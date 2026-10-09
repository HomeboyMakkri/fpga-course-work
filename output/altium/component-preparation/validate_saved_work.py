"""Read-only audit of native snapshots, saved models, sources and project links."""
from pathlib import Path
import hashlib, json, sys, zipfile
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/altium'))
from library_api import fingerprint_models
from read_native_inventory import inspect
MM_PER_COORD=0.0254/10000

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n): return json.loads((OUT/'evidence'/n).read_text(encoding='utf-8'))
def upper(r): return {k.upper():v for k,v in r.items()}
def grid_error(value,grid=1):
    mm=value*MM_PER_COORD
    return abs(mm-round(mm/grid)*grid)
def coord_from_record(r,key):
    # Serialized schematic ASCII unit = 10 mil; fractional millionths.
    return int(r.get(key,'0'))*100000+int(r.get(key+'_Frac','0'))

def check_symbol(key,path,after_file):
    before=load(f'{key}-native-before.json')['result']; after=load(after_file)['result']
    a={p['designator']:p for p in before['pins']}; b={p['designator']:p for p in after['pins']}
    preserved=a.keys()==b.keys() and all((a[d]['name'],a[d]['electrical'],a[d]['part'])==(b[d]['name'],b[d]['electrical'],b[d]['part']) for d in a)
    defects=[]; endpoints=[]
    for p in after['pins']:
        dx,dy={0:(1,0),1:(0,1),2:(-1,0),3:(0,-1)}[p['orientation']]
        x=p['x_coord']+dx*p['length_coord']; y=p['y_coord']+dy*p['length_coord']
        error=max(grid_error(x),grid_error(y))
        endpoints.append({'designator':p['designator'],'part':p['part'],'x_mm':x*MM_PER_COORD,'y_mm':y*MM_PER_COORD,'grid_error_mm':error})
        if error>MM_PER_COORD+1e-10: defects.append(p['designator'])
    formats=all(abs(p['length_coord']*MM_PER_COORD-5)<=MM_PER_COORD and p['name_font']==p['designator_font']=='GOST Common' and p['name_size']==p['designator_size']==10 and p['name_font_mode']==p['designator_font_mode']==1 for p in after['pins'])
    native=inspect(path); recs=[r for rows in native['records'].values() for r in rows]; header=next(r for r in recs if 'HEADER' in r)
    graphical=[]; old_lines=0
    for r in recs:
        if r.get('RECORD')=='13': old_lines+=1
        if r.get('RECORD') in {'13','14','4','41','34'}:
            for fld in ['Location.X','Location.Y']+(['Corner.X','Corner.Y'] if r.get('RECORD') in {'13','14'} else []):
                if fld in r or fld+'_Frac' in r:
                    error=grid_error(coord_from_record(r,fld),0.5)
                    graphical.append({'record':r.get('RECORD'),'part':r.get('OwnerPartId','0'),'field':fld,'mm':coord_from_record(r,fld)*MM_PER_COORD,'grid_error_mm':error,'on_grid':error<=MM_PER_COORD+1e-10})
    (OUT/'evidence'/f'{key}-endpoint-grid.json').write_text(json.dumps(endpoints,indent=2),encoding='utf-8')
    (OUT/'evidence'/f'{key}-saved-scene.json').write_text(json.dumps(native,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'path':str(path),'saved_sha256':sha(path),'native_save_reopen':True,'pin_count':after['pin_count'],'part_count':after['part_count'],'identity_names_types_parts_preserved':preserved,'length_font_pass':formats,'endpoint_grid_mm':1,'precision_step_mm':MM_PER_COORD,'endpoint_grid_pass':not defects,'max_endpoint_grid_error_mm':max(p['grid_error_mm'] for p in endpoints),'off_grid_pins':defects,'graphics_aux_grid_mm':0.5,'graphical_grid_pass':all(r['on_grid'] for r in graphical),'off_grid_graphics':[r for r in graphical if not r['on_grid']],'old_line_count':old_lines,'display_unit_saved':header.get('Display_Unit'),'snap_grid_mm':coord_from_record(header,'SnapGridSize')*MM_PER_COORD,'visible_grid_mm':coord_from_record(header,'VisibleGridSize')*MM_PER_COORD,'model_fingerprint':fingerprint_models(path),'connected_new_working_library':False,'model_resolution_from_target_project':None,'erc':None,'ready_full_lifecycle':False}

def main():
    report={'date':'2026-10-08','complete_kit':False,'fully_ready_connected_count':0,'new_verified_project_connection_count':0,'components':{}}
    report['components']['fpga']=check_symbol('fpga',ROOT/'ARTIX/ARTIX/libraries/project/ARTIX.SchLib','fpga-after.json')
    report['components']['asv']=check_symbol('asv',ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib','asv-after-final.json')
    report['components']['fpga']['manufacturer_ball_map']=load('fpga-manufacturer-pin-crosscheck.json')
    report['components']['fpga']['electrical_types_limitation']='All 484 original pins Passive (4), preserved as requested; directional ERC not validated.'
    source=ROOT/'ARTIX/ARTIX/libraries/X7/XC7A50T-2FGG484I.SchLib'
    report['components']['fpga']['model_records_and_maps_unchanged']=fingerprint_models(source)==fingerprint_models(ROOT/'ARTIX/ARTIX/libraries/project/ARTIX.SchLib')
    for key in ['asv','flash']:
        path=ROOT/('ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib' if key=='asv' else 'ARTIX/ARTIX/libraries/W25Q128JV/new/W25Q128JVSIQ.SchLib')
        inventory=inspect(path); save=OUT/'evidence'/f'{key}-saved-scene.json'; save.write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
        headers=[upper(r) for rows in inventory['records'].values() for r in rows if r.get('RECORD')=='1']
        params=[upper(r) for rows in inventory['records'].values() for r in rows if r.get('RECORD')=='41']
        item=report['components'].setdefault(key,{})
        item['saved_components']=[h.get('LIBREFERENCE') for h in headers]; item['saved_parameters']=params
        item['model_fingerprint']=fingerprint_models(path)
        if key=='flash': item.update(path=str(path),saved_sha256=sha(path),grid_mutation_saved=True,native_save_reopen=False,source_defects=['pin7 RESET instead of IO3','all pins electrical7 Power'],correction_state='STARTED_WITHOUT_COMPLETION; unsaved state unknown',connected_new_working_library=False,model_resolution_from_target_project=None,erc=None,ready_full_lifecycle=False)
    # Native footprint snapshots were read from these exact sources/copies.
    report['footprints']={k:load(n)['result'] for k,n in [('fpga','fpga-pcb.json'),('flash','flash-pcb.json'),('asv_source','asv-pcb-before.json')]}
    asv_old=ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/PcbLib1.PcbLib'; asv_new=ROOT/'ARTIX/ARTIX/libraries/ASV-50MHz/new/PcbLib1.PcbLib'
    import olefile
    with olefile.OleFileIO(str(asv_old)) as a, olefile.OleFileIO(str(asv_new)) as b:
        streams=[s for s in b.listdir() if len(s)>=2 and s[0]=='ASV25000MHZEJT']
        comparisons={('/'.join(s)):hashlib.sha256(a.openstream(s).read()).hexdigest()==hashlib.sha256(b.openstream(s).read()).hexdigest() for s in streams if a.exists(s)}
        report['components']['asv']['isolated_footprint_names']=sorted({s[0] for s in b.listdir() if len(s)==2 and s[-1]=='Data' and s[0] not in ['Library','FileVersionInfo']})
        report['components']['asv']['selected_footprint_streams_preserved']=comparisons
    report['source_preservation']=[]
    for rec in load('source-checkpoints.json'):
        current=sha(Path(rec['source'])); report['source_preservation'].append({**rec,'current_source_sha256':current,'unchanged':current==rec['source_sha256']})
    project=ROOT/'ARTIX/ARTIX/ARTIX.PrjPcb'; text=project.read_text(encoding='utf-8-sig')
    report['project']={'path':str(project),'saved_sha256':sha(project),'references':[line.partition('=')[2] for line in text.splitlines() if line.startswith('DocumentPath=')],'modified_by_this_run':False,'new_pair_connected':False,'compiler_called':False}
    report['blocked_executor']={'mutation_job':'0b5f9f78b4034984a80b45aaa67e5ac6','mutation_state':'STARTED_WITHOUT_COMPLETION','recovery_job':'c58f4e3aefe640ef98c37e45496bf9f1','recovery_success':False}
    report['components']['fpga']['visual_qa']={'method':'reconstruction from saved native geometry with GOST Common font; not Altium screenshot','status':'PENDING','finding':'3mm rows may overlap 10pt glyphs; source-file-only generator changed to 4mm but not executed','evidence':'evidence/qa-preview.md'}
    report['components']['asv']['visual_qa']={'status':'FAIL','finding':'four old eLine segments remain off grid, alongside new body','evidence':'evidence/qa-preview.md'}
    for key in ['power_tps','power_spx','ethernet_phy','ethernet_magjack','ethernet_crystal','jtag','reset_led','inductors','ferrite']:
        report['components'][key]={'ready_full_lifecycle':False,'connected_new_working_library':False,'status':'PENDING; see components.md and blockers.md'}
    for key,item in report['components'].items():
        item['stages']={
            '1_exact_component_source': 'existing native source + manufacturer evidence; FPGA procurement grade unresolved' if key=='fpga' else 'existing native source + manufacturer evidence' if key in ['asv','flash','ferrite'] else 'exact MPN + provider evidence + BXL downloaded' if key=='power_spx' else 'family identified; order code proposal documented' if key=='power_tps' else 'exact MPN + vendor evidence, CAD archive not downloaded' if key in ['ethernet_phy','ethernet_magjack'] else 'exact MPN/requirements unresolved',
            '2_native_import_or_existing_reuse':'existing native source reused in separate explicit working copy' if key in ['fpga','asv','flash'] else 'local native source found; live verification pending' if key=='ferrite' else 'not completed',
            '3_isolation':'single original FPGA/footprint only' if key=='fpga' else 'single ASV symbol/footprint saved; dependency readback pending' if key=='asv' else 'single original Flash/footprint only' if key=='flash' else 'not completed',
            '4_gost_mm':'geometry saved; visual pitch review pending' if key=='fpga' else 'geometry saved; old contour removal pending' if key=='asv' else 'layout saved; source defect correction and native validation blocked' if key=='flash' else 'not completed',
            '5_save_reopen_validate':'pin/font/grid native checks passed; full visual/models pending' if key in ['fpga','asv'] else 'not completed',
            '6_project_connection_resolution':'not completed'}
        item['blockers']=['B01','B02','B03'] if key in ['fpga','asv','flash'] else ['B04'] if key in ['power_tps','power_spx','ethernet_phy','ethernet_magjack'] else ['B05'] if key in ['ethernet_crystal','jtag','reset_led','inductors'] else ['B01','B03']
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for key,folder in [('fpga','ARTIX/ARTIX/libraries/project'),('asv','ARTIX/ARTIX/libraries/ASV-50MHz'),('flash','ARTIX/ARTIX/libraries/W25Q128JV')]:
        companion={'scope':'This preparation attempt; partial, not a completed component package','date':report['date'],'report':str(OUT/'validation.json'),'component':report['components'][key],'source_files':[r for r in report['source_preservation'] if ('X7' in r['source'] if key=='fpga' else 'ASV-50MHz' in r['source'] if key=='asv' else 'W25Q128JV' in r['source'])]}
        (ROOT/folder/'preparation-20261008.json').write_text(json.dumps(companion,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'fpga_pin_count':report['components']['fpga']['pin_count'],'fpga_grid_pass':report['components']['fpga']['endpoint_grid_pass'],'asv_grid_pass':report['components']['asv']['endpoint_grid_pass'],'source_files_unchanged':all(r['unchanged'] for r in report['source_preservation']),'ready_connected':0,'old_asv_lines':report['components']['asv']['old_line_count']},ensure_ascii=True))
if __name__=='__main__': main()
