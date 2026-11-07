"""Reproducible stdlib + Icarus tests, no network or third-party Python needed."""
from pathlib import Path
import argparse, hashlib, json, shutil, socket, struct, subprocess, zlib
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'vivado/codex_sources'
VENDOR=ROOT/'vivado/third_party/verilog-ethernet'
PC_MAC=bytes.fromhex('020000000001'); FPGA_MAC=bytes.fromhex('020000000050')
PC_IP=socket.inet_aton('192.168.1.10'); FPGA_IP=socket.inet_aton('192.168.1.128')
def checksum(data):
    if len(data)%2: data+=b'\0'
    total=sum(struct.unpack('!%dH'%(len(data)//2),data))
    while total>>16: total=(total&65535)+(total>>16)
    return (~total)&65535
def wire_frame(body,bad_fcs=False):
    body=body.ljust(60,b'\0')
    crc=zlib.crc32(body) ^ int(bad_fcs)
    return b'\x55'*7+b'\xd5'+body+struct.pack('<I',crc)
def arp():
    return wire_frame(b'\xff'*6+PC_MAC+b'\x08\x06'+struct.pack('!HHBBH',1,0x800,6,4,1)+PC_MAC+PC_IP+b'\0'*6+FPGA_IP)
def udp(payload,*,dip=FPGA_IP,dmac=FPGA_MAC,port=1234,flags=0,corrupt_udp=False,corrupt_ip=False,bad_fcs=False,zero_checksum=False,declared=None):
    size=8+len(payload) if declared is None else declared
    h=struct.pack('!HHHH',40000,port,size,0)
    c=checksum(PC_IP+dip+struct.pack('!BBH',0,17,size)+h+payload) or 65535
    if corrupt_udp: c^=1
    h=h[:6]+struct.pack('!H',0 if zero_checksum else c)
    ip=struct.pack('!BBHHHBBH',0x45,0,20+len(h)+len(payload),1,flags,64,17,0)+PC_IP+dip
    ic=checksum(ip) ^ int(corrupt_ip)
    ip=ip[:10]+struct.pack('!H',ic)+ip[12:]
    return wire_frame(dmac+PC_MAC+b'\x08\x00'+ip+h+payload,bad_fcs)
def generate(out):
    memory=bytearray(); code=[]; n=0
    def send(f):
        code.append(f'send_frame({len(memory)},{len(f)});');memory.extend(f)
    def command(ch,mode,**kw):
        nonlocal n
        send(udp(bytes([ch,mode]),**kw));n+=1
        code.append(f'settle;check_requests({n});')
    send(arp());code.append('settle;')
    for ch in range(1,4):
        for mode in range(4): command(ch,mode)
    for ch in range(1,4): command(ch,128)
    bad=[udp(b'\0\1'),udp(b'\4\1'),udp(b'\1\4'),udp(b'\1'),udp(b'\1\2\3'),
         udp(b'\1\2',dip=PC_IP),udp(b'\1\2',dmac=PC_MAC),udp(b'\1\2',port=9999),
         udp(b'\1\2',flags=0x2000),udp(b'\1\2',flags=1),udp(b'\1\2',corrupt_udp=True),
         udp(b'\1\2',corrupt_ip=True),udp(b'\1\2',bad_fcs=True),udp(b'\1\2',declared=12)]
    for f in bad:
        send(f);code.append(f'settle;check_requests({n});')
    command(1,2,zero_checksum=True)
    command(1,2) # duplicate restarts addressed channel; no transaction ID dedup
    # Stall source domain after request has been launched: response must survive.
    send(udp(b'\1\3'));n+=1
    code.append('wait(cv);@(negedge clk);@(negedge clk);run_net=0;#2000;run_net=1;settle;')
    code.append(f'check_requests({n});if(mailbox.modes[0]!=3) $fatal(1,"net-clock stop corrupted command");')
    code.append('@(negedge refclk);run_ref=0;')
    send(udp(b'\2\1'));n+=1;code.append(f'settle;check_requests({n});if(cr) $fatal(1,"mailbox did not stay full");')
    send(udp(b'\3\0'));code.append(f'settle;check_requests({n});if(overflow!=1) $fatal(1,"overflow missing");')
    code.append('run_ref=1;settle;if(mailbox.modes[1]!=1 || mailbox.modes[2]!=3) $fatal(1,"stalled command corrupted");')
    code.append('@(negedge refclk);run_ref=0;')
    send(udp(b'\1\3'));n+=1
    code.append(f'settle;check_requests({n});arst=1;repeat(20) @(negedge clk);arst=0;run_ref=1;settle;')
    code.append('if(mailbox.modes[0]!=0 || mailbox.modes[1]!=0 || mailbox.modes[2]!=0) $fatal(1,"reset replay");')
    code.append("repeat(2000) @(negedge clk);")
    send(arp());code.append("settle;")
    command(3,1)
    code.append('if(mailbox.modes[2]!=1) $fatal(1,"post-reset command");')
    (out/'frames.hex').write_text('\n'.join(f'{b:02x}' for b in memory)+'\n')
    (out/'vector_size.vh').write_text(f'localparam integer VECTOR_BYTES={len(memory)};\n')
    (out/'stimulus.vh').write_text('\n'.join(code)+'\n')
def verify_tx(out):
    frames=[];frame=bytearray();lo=None
    for line in (out/'tx_nibbles.txt').read_text().splitlines():
        if line=='-':
            if frame: frames.append(bytes(frame));frame.clear()
            lo=None
        elif line[0]=='L':lo=int(line[1],16)
        elif lo is not None:frame.append(lo | (int(line[1],16)<<4));lo=None
    arp_count=0; replies=[]
    for frame in frames:
        assert frame[:8]==b'\x55'*7+b'\xd5',frame[:8].hex()
        body=frame[8:-4]
        assert struct.unpack('<I',frame[-4:])[0]==zlib.crc32(body),'TX FCS'
        assert body[:6]==PC_MAC and body[6:12]==FPGA_MAC,'reply MAC'
        if body[12:14]==b'\x08\x06':
            assert body[20:22]==b'\0\2' and body[28:32]==FPGA_IP and body[38:42]==PC_IP
            arp_count+=1
        else:
            assert body[12:14]==b'\x08\x00'
            ip=body[14:34];assert checksum(ip)==0,'TX IP checksum'
            assert ip[12:16]==FPGA_IP and ip[16:20]==PC_IP
            u=body[34:46]
            assert struct.unpack('!HHH',u[:6])==(1234,40000,12)
            assert checksum(FPGA_IP+PC_IP+struct.pack('!BBH',0,17,12)+u)==0,'TX UDP checksum'
            assert u[8]==0 and u[11]==1
            replies.append(u[8:])
    expected=[bytes([0,ch,mode,1]) for ch in range(1,4) for mode in range(4)]
    expected += [bytes([0,ch,3,1]) for ch in range(1,4)]
    expected += [b'\0\1\2\1']*2+[b'\0\1\3\1',b'\0\2\1\1',b'\0\3\1\1']
    assert arp_count==2,(arp_count,'ARP replies')
    assert replies==expected,([r.hex() for r in replies],[e.hex() for e in expected])
    print(f'PASS TX: {arp_count} ARP + {len(replies)} applied/read replies; MAC/FCS/IP/UDP checksums and payloads')
def run(args,cwd):
    p=subprocess.run([str(x) for x in args],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (cwd/(Path(str(args[0])).stem+'.log')).open('a').write(p.stdout)
    if p.returncode: raise RuntimeError(p.stdout)
    if 'FATAL:' in p.stdout or 'Fatal:' in p.stdout: raise RuntimeError(p.stdout)
    print(p.stdout.strip() if Path(str(args[0])).stem in ('vvp','xsim') else f'PASS {Path(str(args[0])).name}')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--quick',action='store_true');parser.add_argument('--xsim-bin',type=Path);parser.add_argument('--top-only',action='store_true');args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((VENDOR/'manifest.json').read_text())
    for f,h in manifest['files'].items():assert hashlib.sha256((VENDOR/f).read_bytes()).hexdigest()==h,f
    print('PASS vendor checksums')
    generate(out)
    vendor=sorted((VENDOR/'rtl').glob('*.v'))+sorted((VENDOR/'lib/axis/rtl').glob('*.v'))
    design=[SRC/(n+'.v') for n in ['pps_generator','command_mailbox','udp_pps_control','ethernet_core']]
    tests=[('udp_backpressure_tb',[SRC/'udp_pps_control.v',ROOT/'vivado/tests/udp_backpressure_tb.v']),
           ('rtl8211e_init_tb',[SRC/'rtl8211e_init.v',ROOT/'vivado/tests/rtl8211e_init_tb.v']),
           ('pps_generator_tb',[SRC/'pps_generator.v',SRC/'pps_generator_tb.v']),
           ('pps_real_period_tb',[SRC/'pps_generator.v',SRC/'pps_real_period_tb.v']),
           ('ethernet_integration_tb',design+vendor+[ROOT/'vivado/tests/ethernet_integration_tb.v'])]
    if args.top_only:
        if not args.xsim_bin:parser.error('--top-only requires --xsim-bin for UNISIM')
        tests=[('smart_artix_top_tb',design+vendor+[SRC/'rtl8211e_init.v',SRC/'smart_artix_top.v',SRC/'smart_artix_top_tb.v',args.xsim_bin.parent/'data/verilog/src/glbl.v'])]
    for top,files in tests:
        if args.quick and top=='pps_real_period_tb':continue
        if args.xsim_bin:
            run([args.xsim_bin/'xvlog.bat','--sv','-i',out,*files],out)
            run([args.xsim_bin/'xelab.bat',top,*(['glbl'] if args.top_only else []),'-s',top+'_sim','--debug','typical','-L','unisims_ver'],out)
            run([args.xsim_bin/'xsim.bat',top+'_sim','-runall'],out)
        else:
            exe=out/(top+'.vvp')
            run(['iverilog','-g2012','-I',out,'-s',top,'-o',exe,*files],out)
            run(['vvp',exe],out)
    if not args.top_only:verify_tx(out)
if __name__=='__main__':main()
