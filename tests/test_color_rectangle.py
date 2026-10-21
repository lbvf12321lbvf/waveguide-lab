import io
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
import numpy as np
from PIL import Image
from scipy.special import jv,jn_zeros
import web_engine as e
from image_color import decode_intensity,color_config,palette_table

def png(rgb):
    f=io.BytesIO();Image.fromarray(rgb).save(f,format='PNG');return f.getvalue()

class ColorScaleTests(unittest.TestCase):
    def test_white_background_and_palette_endpoints(self):
        rgb=np.array([[[255,255,255],[255,0,0],[255,255,0],[0,255,0],[0,0,255]]],dtype=np.uint8)
        decoded,dist,_=decode_intensity(rgb,{'source_palette':'figure'})
        np.testing.assert_allclose(decoded,[[0,.25,.5,.75,1]],atol=1e-7)
        np.testing.assert_allclose(dist,0,atol=1e-7)
        reversed_,_,_=decode_intensity(rgb,{'source_palette':'figure','palette_reverse':True})
        np.testing.assert_allclose(reversed_,1-decoded,atol=1e-7)
    def test_custom_nonuniform_levels_and_interpolation(self):
        config={'source_palette':'custom','palette_stops':[{'color':'#ffffff','intensity':0},
            {'color':'#ff0000','intensity':.2},{'color':'#000000','intensity':1}]}
        rgb=np.array([[[255,255,255],[255,128,128],[255,0,0],[0,0,0]]],dtype=np.uint8)
        result,_,_=decode_intensity(rgb,config)
        np.testing.assert_allclose(result,[[0,.1,.2,1]],atol=.001)
        nearest,_,_=decode_intensity(rgb,{**config,'palette_interpolation':'nearest'})
        self.assertEqual(nearest[0,2],np.float32(.2))
    def test_native_scientific_data_are_not_palette_mapped(self):
        values=np.arange(400,dtype=np.uint16).reshape(20,20)*100
        mapped,dist,cfg=decode_intensity(values,{'source_palette':'figure','palette_reverse':True})
        np.testing.assert_array_equal(mapped,values)
        self.assertIsNone(dist)
        self.assertEqual(cfg['source_palette'],'native')
    def test_builtin_lookup_roundtrip(self):
        for name in ('inferno','viridis','plasma','magma','turbo'):
            config=color_config({'source_palette':name})
            rgb,levels=palette_table(config)
            result,_,_=decode_intensity(np.round(rgb*255).astype(np.uint8)[None,:,:],config)
            np.testing.assert_allclose(result[0],levels,atol=.005)
    def test_palette_changes_keep_original_colors_and_geometry(self):
        rgb=np.full((20,20,3),255,dtype=np.uint8);rgb[4:16,4:16]=[255,0,0]
        first=e.load_image({'name':'colors.png'},png(rgb))
        before=e._source_image.copy()
        self.assertGreater(e._image[0,0],e._image[10,10])
        changed=e.decode_image({'source_palette':'figure'})
        self.assertEqual(e._image[0,0],0);self.assertAlmostEqual(float(e._image[10,10]),.25)
        np.testing.assert_array_equal(e._source_image,before)
        self.assertEqual(first['meta'],changed['meta'])
        self.assertTrue(first['source_rgb'])
    def test_decode_precedes_downsampling(self):
        rgb=np.zeros((16,2048,3),dtype=np.uint8);rgb[:,::2]=[255,0,0];rgb[:,1::2]=[0,255,0]
        rgb[:,:2]=255
        e.load_image({'name':'large.png','source_palette':'figure'},png(rgb))
        self.assertAlmostEqual(e._image[0,3],.5,places=6)
        self.assertEqual(e._image[0,0],0)
    def test_invalid_scales_are_rejected(self):
        bad=[{'source_palette':'unknown'},
             {'source_palette':'custom','palette_stops':[]},
             {'source_palette':'custom','palette_stops':[{'color':'bad','intensity':0},{'color':'#ffffff','intensity':1}]},
             {'source_palette':'custom','palette_stops':[{'color':'#000000','intensity':float('nan')},{'color':'#ffffff','intensity':1}]},
             {'source_palette':'custom','palette_stops':[{'color':'#ffffff','intensity':0},{'color':'#ffffff','intensity':1}]}]
        for data in bad:
            with self.subTest(data=data),self.assertRaises(ValueError):color_config(data)

class RectangularSelectionTests(unittest.TestCase):
    def setUp(self):self.roi=e.demo_image()['roi']
    def config(self,angle=0):
        return {**self.roi,'catalogue':100,'region_enabled':True,'region_x':127.5,'region_y':127.5,
                'region_width':180,'region_height':50,'region_angle':angle}
    def test_both_dimensions_and_rotation(self):
        for angle in (0,90,37):
            config=self.config(angle);mask,_=e.analysis_mask(config,self.roi)
            self.assertTrue(mask[127,127]);self.assertLess(mask.sum(),180*52)
            r=e.analyse_image(config)
            self.assertEqual(r['rows'][0]['name'],'HE_1,3')
            self.assertGreater(r['rows'][0]['correlation_2d'],.99)
    def test_excluded_endpoints_cannot_affect_result(self):
        config=self.config();mask,_=e.analysis_mask(config,self.roi)
        self.assertFalse(mask[127,240])
        before=e.analyse_image(config);e._image[~mask]=1e9;after=e.analyse_image(config)
        np.testing.assert_allclose(before['observed'],after['observed'],atol=0,equal_nan=True)
        self.assertEqual(before['rows'],after['rows'])
    def test_colored_known_mode_recovered_through_rectangle(self):
        y,x=np.indices((256,256));rho=np.hypot(x-127.5,y-127.5)/112
        intensity=np.where(rho<=1,jv(0,jn_zeros(0,3)[-1]*rho)**2,0)
        rgb=np.full((256,256,3),255,dtype=np.uint8)
        rgb[:,:,1]=rgb[:,:,2]=np.round(255*(1-intensity))
        color={'source_palette':'custom','palette_stops':[{'color':'#ffffff','intensity':0},{'color':'#ff0000','intensity':1}]}
        e.load_image({'name':'encoded.png',**color},png(rgb))
        r=e.analyse_image({**self.config(21),**color})
        self.assertEqual(r['rows'][0]['name'],'HE_1,3')
        self.assertGreater(r['rows'][0]['correlation_2d'],.999)
        self.assertEqual(r['config']['palette_stops'][0]['intensity'],0)

if __name__=='__main__':unittest.main()
