"""Read saved CAD graphics and native pin snapshots; never modify any CAD file.

PNGs are saved-geometry reconstructions, NOT native Altium screenshots.
Pin-text placement follows a documented approximation; binary pin records are
not rewritten or interpreted. This is independent visual QA, not CAD/ERC.
"""
from pathlib import Path
import sys, json, math, hashlib, itertools

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.append(str(ROOT/'tools/altium/.venv/Lib/site-packages'))
from read_native_inventory import inspect
from PIL import Image, ImageDraw, ImageFont

EVIDENCE = OUT/'evidence'
PREVIEWS = EVIDENCE/'previews'
FONT_PATH = Path('C:/Windows/Fonts/GOST Common.ttf')
COORD_MM = 0.00000254
SCALE = 16
FONT_PX = round(10*25.4/72*SCALE)
FONT = ImageFont.truetype(str(FONT_PATH), FONT_PX)
SMALL = ImageFont.truetype(str(FONT_PATH), 24)


def mm(record, key):
    # Saved SchLib ASCII coordinate fields use units of 10 mil,
    # with a signed decimal fractional part in 1/100000 units.
    return (float(record.get(key, 0)) + float(record.get(key+'_Frac', 0))/100000)*0.254


def ink_box(text):
    return FONT.getbbox(text)


def render_component(key, path):
    native=json.loads((EVIDENCE/f'{key}-after.json').read_text(encoding='utf-8'))['result']
    saved=inspect(path)
    records=next(v for k,v in saved['records'].items() if k.endswith('/Data'))
    report={'component':native['component'], 'library':str(path), 'saved_sha256':saved['sha256'],
            'native_snapshot':f'{key}-after.json', 'parts':[], 'limitations':[
                'Saved graphical primitives and native pin positions used together.',
                'Pin name/number offsets are reconstruction approximations; native UI not captured.',
                'No compiler, electrical or model validation is performed by this script.']}
    for part in range(1,native['part_count']+1):
        pins=[p for p in native['pins'] if p['part']==part]
        graphic=[r for r in records if (int(r.get('OwnerPartId',-1))==part and r.get('RECORD') in {'4','13','14'})
                 or (r.get('RECORD')=='34' and r.get('IsHidden')!='T')]
        rectangles=[r for r in graphic if r.get('RECORD')=='14']
        xs=[mm(r,k) for r in graphic for k in ['Location.X','Corner.X']]
        ys=[mm(r,k) for r in graphic for k in ['Location.Y','Corner.Y']]
        for p in pins:
            x,y=p['x_coord']*COORD_MM,p['y_coord']*COORD_MM
            length=p['length_coord']*COORD_MM
            xs.extend([x,x+length if p['orientation']==0 else x-length])
            ys.append(y)
        minx,maxx=min(xs)-14,max(xs)+14
        miny,maxy=min(ys)-8,max(ys)+15
        width=math.ceil((maxx-minx)*SCALE)
        height=math.ceil((maxy-miny)*SCALE)
        image=Image.new('RGB',(width,height),'white')
        draw=ImageDraw.Draw(image)
        xy=lambda x,y: ((x-minx)*SCALE,(maxy-y)*SCALE)
        draw.text((18,12),f'{key.upper()} / part {part}: SAVED-GEOMETRY RECONSTRUCTION',font=SMALL,fill='#36516c')
        # Main and auxiliary millimetre grids as dots rather than an obscuring mesh.
        for x in range(math.ceil(minx),math.floor(maxx)+1):
            for y in range(math.ceil(miny),math.floor(maxy)+1):
                if x%5==0 and y%5==0:
                    px,py=xy(x,y)
                    draw.point((px,py),fill='#d2d8dd')
        for r in graphic:
            rtype=r.get('RECORD')
            x1,y1=mm(r,'Location.X'),mm(r,'Location.Y')
            if rtype in {'13','14'}:
                x2,y2=mm(r,'Corner.X'),mm(r,'Corner.Y')
                box=[xy(min(x1,x2),max(y1,y2)),xy(max(x1,x2),min(y1,y2))]
                if rtype=='14': draw.rectangle(box,outline='black',width=2)
                else: draw.line([xy(x1,y1),xy(x2,y2)],fill=globals().get('LINE_COLOR','#a02b22'),width=2)
            elif rtype in {'4','34'}:
                text=r.get('Text','')
                bx=ink_box(text)
                px,py=xy(x1,y1)
                if rtype=='4':
                    draw.text((px-(bx[2]-bx[0])/2,py-(bx[3]-bx[1])/2),text,font=FONT,fill='black')
                else:
                    draw.text((px-bx[0],py-bx[3]),text,font=FONT,fill='black')
        text_boxes=[]
        for p in pins:
            x,y=p['x_coord']*COORD_MM,p['y_coord']*COORD_MM
            length=p['length_coord']*COORD_MM
            orient=p['orientation']
            direction=1 if orient==0 else -1
            external=x+direction*length
            draw.line([xy(x,y),xy(external,y)],fill='black',width=2)
            px,py=xy(external,y)
            draw.ellipse((px-3,py-3,px+3,py+3),outline='#3867b1')
            # Pin name inside the body, number above the external 5-mm stem.
            name=p['name']; bx=ink_box(name)
            tx,ty=xy(x-direction*0.8,y)
            w,h=bx[2]-bx[0],bx[3]-bx[1]
            left=tx-w if orient==0 else tx
            top=ty-h/2
            if p.get('show_name',True):
                draw.text((left-bx[0],top-bx[1]),name,font=FONT,fill='black')
                text_boxes.append({'designator':p['designator'],'kind':'name','bbox_px':[left,top,left+w,top+h]})
            number=p['designator']; bx=ink_box(number); w,h=bx[2]-bx[0],bx[3]-bx[1]
            tx,ty=xy((x+external)/2,y)
            left,top=tx-w/2,ty-h-0.3*SCALE
            draw.text((left-bx[0],top-bx[1]),number,font=FONT,fill='black')
            text_boxes.append({'designator':p['designator'],'kind':'number','bbox_px':[left,top,left+w,top+h]})
        overlaps=[]
        # Name/name bounding boxes flag crowded rows independently from number offset approximation.
        for a,b in itertools.combinations([t for t in text_boxes if t['kind']=='name'],2):
            A,B=a['bbox_px'],b['bbox_px']
            wx,hy=min(A[2],B[2])-max(A[0],B[0]),min(A[3],B[3])-max(A[1],B[1])
            if wx>0 and hy>0:
                overlaps.append({'a':a['designator'],'b':b['designator'],'bbox_overlap_mm':[wx/SCALE,hy/SCALE]})
        name_heights=[(t['bbox_px'][3]-t['bbox_px'][1])/SCALE for t in text_boxes if t['kind']=='name']
        filename=f'{key}-part-{part:02d}.png'
        image.save(PREVIEWS/filename)
        report['parts'].append({'part':part,'pins':len(pins),'preview':filename,
            'rectangle_count':len(rectangles),'line_count':sum(r.get('RECORD')=='13' for r in graphic),
            'graphic_bounds_mm':[min(xs),min(ys),max(xs),max(ys)],
            'max_name_ink_height_mm':max(name_heights,default=0),'approximate_name_bbox_overlaps':overlaps})
    return report


def verify_bga():
    f=json.loads((EVIDENCE/'fpga-pcb.json').read_text(encoding='utf-8'))['result']['footprints'][0]
    pads=f['pads']; rows='A B C D E F G H J K L M N P R T U V W Y AA AB'.split()
    expected={f'{r}{c}' for r in rows for c in range(1,23)}
    names=[p['name'] for p in pads]
    xs=sorted(set(p['x_coord'] for p in pads)); ys=sorted(set(p['y_coord'] for p in pads),reverse=True)
    tolerance=COORD_MM
    x0=(min(xs)+max(xs))/2; y0=(min(ys)+max(ys))/2
    map_errors=[]
    for i,row in enumerate(rows):
        for j in range(22):
            name=f'{row}{j+1}'; found=[p for p in pads if p['name']==name]
            if len(found)!=1:
                map_errors.append({'name':name,'count':len(found)}); continue
            p=found[0]
            expected_x=(j-10.5); expected_y=(10.5-i)
            actual_x=(p['x_coord']-x0)*COORD_MM; actual_y=(p['y_coord']-y0)*COORD_MM
            if max(abs(actual_x-expected_x),abs(actual_y-expected_y))>tolerance+1e-10:
                map_errors.append({'name':name,'expected_mm':[expected_x,expected_y],'actual_mm':[actual_x,actual_y]})
    pitch_x=[(b-a)*COORD_MM for a,b in zip(xs,xs[1:])]
    pitch_y=[(a-b)*COORD_MM for a,b in zip(ys,ys[1:])]
    result={'footprint':f['name'],'pad_count':len(pads),'unique_names':len(set(names)),
        'name_set_matches_22x22':set(names)==expected,'row_sequence':rows,
        'x_columns':len(xs),'y_rows':len(ys),'pitch_x_range_mm':[min(pitch_x),max(pitch_x)],
        'pitch_y_range_mm':[min(pitch_y),max(pitch_y)],
        'matrix_extent_mm':[(max(xs)-min(xs))*COORD_MM,(max(ys)-min(ys))*COORD_MM],
        'position_tolerance_mm':tolerance,'map_errors':map_errors,
        'pad_size_ranges_mm':{'x':[min(p['x_size_coord'] for p in pads)*COORD_MM,max(p['x_size_coord'] for p in pads)*COORD_MM],
                              'y':[min(p['y_size_coord'] for p in pads)*COORD_MM,max(p['y_size_coord'] for p in pads)*COORD_MM]},
        'hole_sizes_mm':sorted(set(p['hole_coord']*COORD_MM for p in pads)),
        'rotations_deg':sorted(set(p['rotation'] for p in pads)),
        'limitation':'Pad matrix/labels checked; copper pad diameter is not an AMD-recommended land pattern proof.'}
    result['matrix_pass']=len(pads)==484 and len(set(names))==484 and set(names)==expected and len(xs)==22 and len(ys)==22 and not map_errors
    return result


def main():
    PREVIEWS.mkdir(exist_ok=True)
    report={'preview_type':'saved-geometry reconstruction, NOT native Altium screenshot',
        'font':{'path':str(FONT_PATH),'sha256':hashlib.sha256(FONT_PATH.read_bytes()).hexdigest(),'size_pt':10,'pixel_scale_px_per_mm':SCALE},
        'components':[],'fpga_bga_matrix':verify_bga(),
        'flash_preview':'SKIPPED: no reliable post-correction native pin snapshot; CAD executor blocked after incomplete correction job.'}
    for key,path in [('fpga','ARTIX/ARTIX/libraries/project/ARTIX.SchLib'),('asv','ARTIX/ARTIX/libraries/ASV-50MHz/new/Schlib1.SchLib')]:
        report['components'].append(render_component(key,ROOT/path))
    (PREVIEWS/'preview-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'rendered_parts':sum(len(c['parts']) for c in report['components']),
        'bga_matrix_pass':report['fpga_bga_matrix']['matrix_pass'],
        'approximate_name_bbox_overlap_counts':{c['component']:sum(len(p['approximate_name_bbox_overlaps']) for p in c['parts']) for c in report['components']}},ensure_ascii=True))


if __name__=='__main__': main()
