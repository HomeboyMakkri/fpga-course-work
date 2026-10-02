"""Real roundtrip on our generated sheet, including a parameter change/restoration."""
import json
import sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
import cad_bridge

path=str(BASE.parents[1]/'ARTIX/ARTIX/CodexGenerated/Clock_Flash_Verified.SchDoc')
manifest=json.loads((Path(__file__).parent/'manifests/clock_flash.json').read_text())
report={}
first=cad_bridge.inspect_schematic(path)
if not first['success']: raise RuntimeError(first)
report['before']=first
changed=cad_bridge.set_component_parameter(path,'J2','Comment','CODEX_ROUNDTRIP_TEST')
if not changed['success']: raise RuntimeError(changed)
after=cad_bridge.inspect_schematic(path)
if not after['success']: raise RuntimeError(after)
assert next(c for c in after['result']['components'] if c['ref']=='J2')['value']=='CODEX_ROUNDTRIP_TEST'
restored=cad_bridge.set_component_parameter(path,'J2','Comment','W25Q128JVSIQTR')
if not restored['success']: raise RuntimeError(restored)
final=cad_bridge.inspect_schematic(path)
if not final['success']: raise RuntimeError(final)
actual=final['result']
comps={c['ref']:c for c in actual['components']}
labels={(n['x'],n['y']):n['net'] for n in actual['net_labels']}
adj={}
for w in actual['wires']:
    a=(w['x1'],w['y1']);b=(w['x2'],w['y2'])
    adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
checks=[]
for c in manifest['components']:
    saved=comps[c['ref']]
    assert saved['value']==c['value']
    pins={p['number']:p for p in saved['pins']}
    for p in c['pins']:
        real=pins[str(p['number'])]
        dx,dy=[(1,0),(0,1),(-1,0),(0,-1)][real['orientation']]
        hot=(real['x']+dx*real['length'],real['y']+dy*real['length'])
        connected={labels[q] for q in adj.get(hot,[]) if q in labels}
        expected={p['net']} if p.get('net') else set()
        checks.append({'ref':c['ref'],'pin':str(p['number']),'expected':p.get('net'),'actual':sorted(connected),'pass':connected==expected})
report.update({'change':changed,'changed_readback':after['job_dir'],'restore':restored,'final':final,'pin_net_checks':checks,
               'all_geometry_checks_pass':all(x['pass'] for x in checks),
               'note':'API geometry verification; compiler connectivity and ERC are separate checks'})
(BASE/'runtime/live-roundtrip-test.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'components':len(comps),'pins_checked':len(checks),'pass':report['all_geometry_checks_pass'],'parameter_roundtrip':True,'report':str(BASE/'runtime/live-roundtrip-test.json')},indent=2))
