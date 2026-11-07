"""Send exactly one PPS command over UDP; Python standard library only."""
import argparse
import socket
import sys

MODES={'off':0,'1':1,'10':2,'100':3,'get':128}
NAMES={0:'OFF',1:'1 PPS',2:'10 PPS',3:'100 PPS'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('channel',type=int,choices=[1,2,3])
    p.add_argument('mode',choices=MODES)
    p.add_argument('--ip',default='192.168.1.128')
    p.add_argument('--port',type=int,default=1234)
    p.add_argument('--bind',help='Local wired IPv4 address (optional)')
    p.add_argument('--timeout',type=float,default=2.0)
    args=p.parse_args()
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        if args.bind:s.bind((args.bind,0))
        s.settimeout(args.timeout)
        s.connect((args.ip,args.port))
        s.send(bytes([args.channel,MODES[args.mode]]))
        try:reply=s.recv(256)
        except (TimeoutError,OSError) as exc:
            print(f'No application acknowledgement: {exc}. Command may have applied; read state before retrying.',file=sys.stderr)
            return 1
    if len(reply)!=4 or reply[0]!=0 or reply[1]!=args.channel or reply[2]>3 or reply[3]!=1:
        print(f'Invalid reply: {reply.hex(" ")}',file=sys.stderr);return 1
    if args.mode!='get' and reply[2]!=MODES[args.mode]:
        print(f'Unexpected applied mode: {reply.hex(" ")}',file=sys.stderr);return 1
    print(f'Channel {reply[1]}: {NAMES[reply[2]]} (PPS-domain acknowledgement)')
    return 0

if __name__=='__main__':sys.exit(main())
