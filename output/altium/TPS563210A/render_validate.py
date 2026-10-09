"""Read-only saved geometry QA; no native CAD editing or scripting."""
from pathlib import Path
import sys,json,hashlib,math
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'output/altium/component-preparation'))
import render_native_previews as renderer
sys.path.insert(0,str(OUT)); from build_requests import PINS,LIB,PCB,COMP,MODEL,coord

def main():
    snapshot=json.loads((OUT/'native-save-reopen.json').read_text(encoding='utf-8'))
    (OUT/'tps-after.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
    renderer.EVIDENCE=OUT; renderer.PREVIEWS=OUT; renderer.LINE_COLOR='black'
    visual=renderer.render_component('tps',LIB)
    # Include the visible Comment parameter, which the generic renderer omitted.
    from PIL import Image,ImageDraw
    im=Image.open(OUT/'tps-part-01.png'); draw=ImageDraw.Draw(im)
    # Bounds produced by generic renderer: -19..54mm X, -38..20mm Y.
    for rows in renderer.inspect(LIB)['records'].values():
        for rec in rows:
            if rec.get('RECORD')=='41' and rec.get('Name')=='Comment' and rec.get('IsHidden')!='T':
                x,y=renderer.mm(rec,'Location.X'),renderer.mm(rec,'Location.Y'); box=renderer.ink_box(rec['Text'])
                draw.text(((x+19)*renderer.SCALE-box[0],(20-y)*renderer.SCALE-box[3]),rec['Text'],font=renderer.FONT,fill='black')
    im.save(OUT/'symbol-preview.png')
    a={p['designator']:p for p in snapshot['result']['pins']}; checks=[]
    for e in PINS:
        p=a[e['designator']]; dx={0:1,2:-1}[p['orientation']]
        endx=(p['x_coord']+dx*p['length_coord'])*0.00000254; endy=p['y_coord']*0.00000254
        err=max(abs(endx-round(endx)),abs(endy-round(endy)))
        checks.append({'pin':p['designator'],'name':p['name'],'name_type_match':(p['name'],p['electrical'])==(e['name'],e['electrical']),'layout_match':(p['x_coord'],p['y_coord'],p['orientation'])==(coord(e['x_mm']),coord(e['y_mm']),e['orientation']),'length_mm':p['length_coord']*0.00000254,'endpoint_mm':[endx,endy],'grid_error_mm':err,'grid_pass':err<=0.00000254+1e-10,'font_pass':p['name_font']==p['designator_font']=='GOST Common' and p['name_size']==p['designator_size']==10 and p['name_font_mode']==p['designator_font_mode']==1})
    backup=json.loads((OUT/'backups.json').read_text(encoding='utf-8'))[0]
    report={'component':COMP,'pins':8,'parts':1,'native_saved_reopened':snapshot['success'],'schlib_sha256':hashlib.sha256(LIB.read_bytes()).hexdigest(),'pcblib_sha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'existing_pcblib_unchanged':hashlib.sha256(PCB.read_bytes()).hexdigest()==backup['sha256'],'checks':checks,'visual_reconstruction':visual,'visual_method':'Saved graphical records and native snapshot rendered using GOST Common; not Altium screenshot','source_datasheet_sha256':hashlib.sha256((ROOT/'datasheets/Datasheets/POWER/TPS563210A.pdf').read_bytes()).hexdigest()}
    report['symbol_numeric_pass']=set(a)==set(str(n) for n in range(1,9)) and all(p['name_type_match'] and p['layout_match'] and p['grid_pass'] and p['font_pass'] for p in checks)
    report['visual_overlap_count']=len(visual['parts'][0]['approximate_name_bbox_overlaps'])
    if (OUT/'model-resolution.json').exists():
        model=json.loads((OUT/'model-resolution.json').read_text(encoding='utf-8'))
        mapping=json.loads((OUT/'model-native-map.json').read_text(encoding='utf-8'))
        before=json.loads((OUT/'footprint-native-before.json').read_text(encoding='utf-8'))
        after=json.loads((OUT/'footprint-native-after.json').read_text(encoding='utf-8'))
        report['model_resolution']=model
        report['model_native_map']=mapping
        import re
        pairs=re.findall(r'\((\d+):(\d+)\)',mapping['result']['map'])
        report['identity_map_pass']=len(pairs)==8 and set(pairs)=={(str(n),str(n)) for n in range(1,9)}
        report['footprint_native_reopen_pad_invariants']=before['result']==after['result']
        report['resolution_exact_project_pcblib']=Path(model['result']['resolved']).resolve()==PCB.resolve()
        report['pad_number_set_pass']={p['name'] for p in after['result']['footprints'][0]['pads']}==set(str(n) for n in range(1,9))
        import configparser
        def references(path):
            cp=configparser.ConfigParser(interpolation=None,strict=False); cp.read(path,encoding='utf-8-sig')
            return [cp.get(s,'DocumentPath') for s in cp.sections() if s.startswith('Document') and cp.has_option(s,'DocumentPath')]
        project=ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb'
        old=references(OUT/'backups/ARTIX.live-checkpoint.PrjPcb'); new=references(project)
        added=[x for x in new if x not in old]
        report['project']={'path':str(project),'sha256':hashlib.sha256(project.read_bytes()).hexdigest(),'all_prior_live_refs_preserved':set(old)<=set(new),'added_references':added,'source_document_count':len(new),'duplicate_references':len(new)!=len(set(new))}
        report['project_connection_pass']=set(added)=={'libraries\\TPS563210A\\TPS563210A.PcbLib','libraries\\TPS563210A\\TPS563210A.SchLib'} and report['project']['all_prior_live_refs_preserved'] and not report['project']['duplicate_references']
        report['ready_for_placement']=report['symbol_numeric_pass'] and report['identity_map_pass'] and report['pad_number_set_pass'] and report['resolution_exact_project_pcblib'] and report['project_connection_pass'] and report['footprint_native_reopen_pad_invariants']
        report['placed_circuit_erc']='Not applicable: this request created/connected libraries; no TPS component placed on user sheets.'
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert report['symbol_numeric_pass'] and report['existing_pcblib_unchanged'] and report['visual_overlap_count']==0
    if 'ready_for_placement' in report: assert report['ready_for_placement']
    print(json.dumps({'symbol_numeric_pass':True,'pins':8,'existing_pcblib_unchanged':True,'visual_overlap_count':0}))
if __name__=='__main__': main()
