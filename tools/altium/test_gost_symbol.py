"""Offline acceptance checks for layout identity and native readback verification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import gost_symbol as g

MANIFEST=Path(__file__).parent/'manifests/gost-tps563210a-approved.json'

def after_for(layout):
    """Native-result-shaped fixture. Only offline checks; not CAD execution."""
    pins=[]; graphics=[]
    for p in layout['pins']:
        pins.append({'designator':p['designator'],'name':p['name'],'part':p['part'],'orientation':p['orientation'],
            'x_coord':g.coord(p['x_mm']),'y_coord':g.coord(p['y_mm']),'electrical':p['electrical'],
            'length_coord':g.coord(layout['pin_length_mm']),'name_font':layout['font_name'],'designator_font':layout['font_name'],
            'name_size':layout['font_size_pt'],'designator_size':layout['font_size_pt'],'name_font_mode':1,'designator_font_mode':1})
    for part in layout['parts']:
        graphics.append({'kind':'rectangle','part':part['id'],'color':0,'x':0,'y':g.coord(-part['height_mm']),'cx':g.coord(part['width_mm']),'cy':0})
        for x in part['dividers_mm']:
            graphics.append({'kind':'line','part':part['id'],'color':0,'x':g.coord(x),'y':0,'cx':g.coord(x),'cy':g.coord(-part['height_mm'])})
        graphics.append({'kind':'label','part':part['id'],'color':0,'text':part['function'],'x':g.coord(part['label_mm'][0]),'y':g.coord(part['label_mm'][1]),'font':layout['font_name'],'size':layout['font_size_pt']})
    return {'component':layout['component'],'part_count':len(layout['parts']),'pins':pins,'graphics':graphics,
        'pin_colors':[{'designator':p['designator'],'color':0} for p in pins],'designator_color':0,'comment_color':0,
        'models':[{'name':'TEST','type':'PCBLIB','map':','.join(f'({p["designator"]}:{p["designator"]})' for p in reversed(pins)),'links':[]}],
        'snap_grid_coord':g.coord(1),'visible_grid_coord':g.coord(.5)}

class GostTests(unittest.TestCase):
    def setUp(self): self.data=g.load(MANIFEST)

    def test_approved_geometry_and_grid(self):
        layout=g.normalize(self.data,'create'); part=layout['parts'][0]
        self.assertEqual((part['width_mm'],part['height_mm'],part['dividers_mm'],part['label_mm']),(35,30,[12,23],[17.5,-3]))
        self.assertEqual({p['electrical'] for p in layout['pins']},{7})
        self.assertTrue(all(abs(g.coord(p['y_mm'])*g.STEP_MM-p['y_mm'])<=g.STEP_MM for p in layout['pins']))

    def test_preserve_types_from_live_snapshot(self):
        old=after_for(g.normalize(self.data,'create'))
        for i,p in enumerate(old['pins']): p['electrical']=i
        self.data['electrical_policy']='preserve'
        layout=g.normalize(self.data,'redraw',old)
        self.assertEqual([p['electrical'] for p in layout['pins']],list(range(8)))

    def test_create_cannot_invent_preserved_types(self):
        self.data.pop('electrical_policy')
        with self.assertRaises(ValueError): g.normalize(self.data,'create')

    def test_missing_pin_rejected(self):
        before=after_for(g.normalize(self.data,'create')); self.data['parts'][0]['pins'].pop()
        with self.assertRaises(ValueError): g.normalize(self.data,'redraw',before)

    def test_renaming_physical_pin_rejected(self):
        before=after_for(g.normalize(self.data,'create')); self.data['parts'][0]['pins'][0]['name']='WRONG'
        with self.assertRaises(ValueError): g.normalize(self.data,'redraw',before)

    def test_duplicate_designator_rejected(self):
        self.data['parts'][0]['pins'][1]['designator']='3'
        with self.assertRaises(ValueError): g.normalize(self.data,'create')

    def test_fractional_grid_nan_and_overflow_rejected(self):
        for change in [('pitch_mm',3),('pitch_mm',6.5),('pitch_mm',float('nan'))]:
            d=copy.deepcopy(self.data); d['parts'][0][change[0]]=change[1]
            with self.assertRaises(ValueError): g.normalize(d,'create')
        d=copy.deepcopy(self.data); d['parts'][0]['pitch_mm']=1000
        d['parts'][0]['pins']=[{'designator':str(i),'name':'P','side':'left'} for i in range(6000)]
        with self.assertRaises(ValueError): g.normalize(d,'create')

    def test_native_result_and_reordered_map_verified(self):
        self.assertTrue(self.check_result()['success'])

    def test_wrong_map_not_accepted(self):
        def corrupt(a): a['models'][0]['map']='(3:7),(7:3)'
        self.assertFalse(self.check_result(corrupt)['success'])

    def test_missing_divider_and_wrong_color_rejected(self):
        self.assertFalse(self.check_result(lambda a:a['graphics'].pop(1))['success'])
        self.assertFalse(self.check_result(lambda a:a['graphics'][0].update(color=8388608))['success'])

    def test_wrong_pin_type_font_and_coordinate_rejected(self):
        for changes in [{'electrical':0},{'name_font':'Arial'},{'x_coord':12345}]:
            self.assertFalse(self.check_result(lambda a,c=changes:a['pins'][0].update(c))['success'])

    def test_false_success_or_missing_color_data_rejected(self):
        with self.assertRaises(ValueError): g.payload({'success':True,'result':{'error':'SAVE_FAILED'}})
        self.assertFalse(self.check_result(lambda a:a.update(pin_colors=[]))['success'])

    def check_result(self,modify=None):
        layout=g.normalize(self.data,'create'); result=after_for(layout)
        if modify: modify(result)
        # Temporary directory contains JSON and non-CAD text only.
        with tempfile.TemporaryDirectory(prefix='gost-offline-') as name:
            out=Path(name).resolve(); target=out/'audit.txt'; target.write_text('non-CAD hashing fixture',encoding='utf-8')
            g.write_json(out/'state.json',{'layout':layout,'path':str(target),'pcblib':None,'footprint':'TEST','checkpoint_captured':True})
            g.write_json(out/'result.json',{'success':True,'result':result})
            return g.verify(out,out/'result.json')

if __name__=='__main__': unittest.main()
