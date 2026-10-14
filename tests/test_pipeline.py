import copy
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_turret import build, export, pixel_to_spine, radius_px, recoil_at, validate_skeleton
from split_character import split_sheet
from make_atlas import pack, write_atlas
from build_spine_json import build_spine_json, _convert_timeline
from generate_spine_player import generate_html, find_atlas_images


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        for name,size in [('base',(12,12)),('body',(10,10)),('barrel',(16,4))]:
            Image.new('RGBA',size,(255,255,255,255)).save(self.root/(name+'.png'))
        self.config={'name':'fixture','spine_version':'4.3.26','canvas_size_px':[64,64],
                     'pivot_px':[32,32],'display_size_px':64,'cell_size_px':72,'forward_px':[1,0],
                     'parts':[{'name':'base','role':'base','file':'base.png','position_px':[26,26]},
                              {'name':'body','role':'aim','file':'body.png','position_px':[27,27]},
                              {'name':'barrel','role':'recoil','file':'barrel.png','position_px':[30,30]}],
                     'muzzles':[{'name':'main','position_px':[46,32]}]}

    def tearDown(self):
        self.temp.cleanup()

    def test_named_crop_preserves_white_and_faint_alpha(self):
        image=Image.new('RGBA',(20,20))
        image.putpixel((4,5),(255,255,255,255))
        image.putpixel((7,5),(35,20,60,1))
        source=self.root/'sheet.png';image.save(source)
        result=split_sheet(source,self.root/'parts',{'parts':[{'name':'white','rect':[3,4,6,5]}]})
        crop=Image.open(self.root/'parts/white.png')
        self.assertEqual(crop.getpixel((1,1)),(255,255,255,255))
        self.assertEqual(crop.getpixel((4,1)),(35,20,60,1))
        self.assertEqual(result['parts'][0]['rect_px'],[3,4,6,5])

    def test_crop_rejects_opaque_inputs_and_bad_regions_without_writes(self):
        with self.assertRaises(ValueError):
            split_sheet(self.root/'base.png',self.root/'bad',{'parts':[{'name':'base','rect':[0,0,12,12]}]})
        self.assertFalse((self.root/'bad').exists())
        im=Image.new('RGBA',(20,20));im.putpixel((1,1),(0,0,0,255));im.save(self.root/'sheet.png')
        with self.assertRaises(ValueError):
            split_sheet(self.root/'sheet.png',self.root/'bad',{'parts':[{'name':'../escape','rect':[0,0,12,12]}]})
        self.assertFalse((self.root/'bad').exists())

    def test_auto_components_preserve_faint_parts_and_sort(self):
        try:
            import cv2
        except ImportError:
            self.skipTest('optional OpenCV unavailable')
        image=Image.new('RGBA',(20,20))
        for x in range(2,5):
            for y in range(3,6):
                image.putpixel((x,y),(255,255,255,1))
        for x in range(12,15):
            for y in range(12,15):
                image.putpixel((x,y),(40,20,10,255))
        source=self.root/'sheet.png';image.save(source)
        result=split_sheet(source,self.root/'components',auto=True,min_area=4,padding=1)
        self.assertEqual(len(result['parts']),2)
        self.assertEqual(result['parts'][0]['rect_px'],[1,2,5,5])
        self.assertEqual(Image.open(self.root/'components/part_00.png').getpixel((1,1))[3],1)

    def test_atlas_keeps_pixel_alpha_and_regions_do_not_overlap(self):
        images={'large':Image.new('RGBA',(90,2),(10,30,50,17)),
                'small':Image.new('RGBA',(3,5),(250,220,90,255))}
        placements=write_atlas(images,self.root/'atlas','fixture')
        atlas=Image.open(self.root/'atlas/fixture.png')
        for name,(x,y,w,h) in placements.items():
            self.assertTrue(np.array_equal(np.array(atlas.crop((x,y,x+w,y+h))),np.array(images[name])))
        self.assertGreaterEqual(atlas.width,94)
        self.assertEqual(placements,pack(dict(reversed(list(images.items()))))[2])
        with self.assertRaises(ValueError):
            write_atlas(images,self.root/'atlas','fixture')

    def test_turret_fixed_root_procedural_aim_and_two_clips(self):
        original=copy.deepcopy(self.config)
        skeleton,_,manifest,_=build(self.config,self.root)
        validate_skeleton(skeleton)
        self.assertEqual(original,self.config)
        self.assertEqual(set(skeleton['animations']),{'idle','fire'})
        self.assertEqual(skeleton['bones'][0],{'name':'root'})
        self.assertEqual(skeleton['bones'][-1]['parent'],'recoil')
        self.assertEqual(manifest['muzzles'][0]['setup_spine'],[14,0])
        self.assertEqual(set(skeleton['animations']['fire']['bones']),{'recoil'})

    def test_diagonal_recoil_has_correct_spine_sign_at_every_yaw(self):
        self.config['forward_px']=[3,4]
        skeleton,_,manifest,_=build(self.config,self.root)
        displacement=skeleton['animations']['fire']['bones']['recoil']['translate'][1]
        depth=manifest['fire']['recoil_source_px']
        self.assertAlmostEqual(displacement['x'],-.6*depth)
        self.assertAlmostEqual(displacement['y'],.8*depth)
        # Spine rotation is negative screen yaw; compare resulting Y-down displacement.
        for degrees in range(0,360,7):
            theta=math.radians(degrees)
            x=math.cos(-theta)*displacement['x']-math.sin(-theta)*displacement['y']
            y=-(math.sin(-theta)*displacement['x']+math.cos(-theta)*displacement['y'])
            self.assertAlmostEqual(x,-depth*(.6*math.cos(theta)-.8*math.sin(theta)))
            self.assertAlmostEqual(y,-depth*(.6*math.sin(theta)+.8*math.cos(theta)))

    def test_faint_pixel_corners_enforce_full_rotation_envelope(self):
        image=Image.new('RGBA',(64,64));image.putpixel((63,63),(0,0,0,1));image.save(self.root/'body.png')
        self.config['parts'][1]['position_px']=[0,0]
        with self.assertRaisesRegex(ValueError,'alpha envelope'):
            build(self.config,self.root)
        self.assertAlmostEqual(radius_px(image,(0,0),(32,32)),math.sqrt(32**2+32**2))

    def test_exact_endpoint_bound_covers_continuous_recoil(self):
        image=Image.open(self.root/'barrel.png')
        limit=max(radius_px(image,(30,30),(32,32)),radius_px(image,(30,30),(32,32),(-2,0)))
        for step in range(101):
            self.assertLessEqual(radius_px(image,(30,30),(32,32),(-2*step/100,0)),limit+1e-12)
        self.assertEqual(recoil_at(.18,.18,.03,.18,2),0)
        self.assertEqual(recoil_at(.03,.18,.03,.18,2),2)

    def test_budget_rejects_global_toywatch_relaxation(self):
        for field,value in [('head_max_radius_cell',.55),('fire',{'recoil_cell':.02})]:
            candidate=copy.deepcopy(self.config);candidate[field]=value
            with self.assertRaises(ValueError):
                build(candidate,self.root)

    def test_invalid_geometry_does_not_make_partial_output(self):
        self.config['forward_px']=[0,0]
        config=self.root/'config.json';config.write_text(json.dumps(self.config))
        with self.assertRaises(ValueError):
            export(config,self.root/'out')
        self.assertFalse((self.root/'out').exists())

    def test_portable_export_reproduces_core_artifacts(self):
        config=self.root/'config.json';config.write_text(json.dumps(self.config))
        first=export(config,self.root/'first')
        second=export(self.root/'first/rig.config.json',self.root/'second')
        self.assertEqual(first['outputs'],second['outputs'])
        self.assertIn('data:image/png;base64', (self.root/'first/preview.html').read_text())
        self.assertNotIn('https://',(self.root/'first/preview.html').read_text())
        with self.assertRaises(ValueError):
            export(config,self.root/'first')

    def test_wire_custom_curves_preserved_and_input_not_mutated(self):
        curve=[0.1,2,0.2,4]
        config={'bones':[{'name':'root'},{'name':'head','parent':'root'}], 'animations':[],
                'custom_animations':{'turn':{'bones':{'head':{'rotate':[{'time':0,'value':1,'curve':curve},{'time':1,'value':5}]}}}}}
        original=copy.deepcopy(config)
        result=build_spine_json(config)
        self.assertEqual(result['animations']['turn'],config['custom_animations']['turn'])
        self.assertEqual(original,config)
        frames=[{'time':0,'angle':30,'curve':[.25,0,.75,1]}]
        _convert_timeline('rotate',frames)
        self.assertEqual(frames,[{'time':0,'value':30}])

    def test_player_aliases_godot_json_and_enforces_runtime_version(self):
        config=self.root/'config.json';config.write_text(json.dumps(self.config));export(config,self.root/'out')
        out=self.root/'out';images=find_atlas_images(out/'fixture.atlas')
        page=generate_html(out/'fixture.spine-json',out/'fixture.atlas',images,title='</script>')
        self.assertIn('spine-player@4.3.*',page)
        self.assertIn('"skeleton": "fixture.json"',page)
        self.assertIn('&lt;/script&gt;',page)
        with self.assertRaises(ValueError):
            generate_html(out/'fixture.spine-json',out/'fixture.atlas',images,runtime_version='4.2.9')


if __name__=='__main__':
    unittest.main()
