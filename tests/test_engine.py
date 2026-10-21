"""Scientific and input-boundary regression tests, runnable with stdlib unittest."""
import io
import json
import math
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
import numpy as np
from PIL import Image
import web_engine as engine
from waveguide_core.projection import decompose_gaussian, make_grid, field_power
from waveguide_core.cylindrical_modes import solve_mode


class SimulationTests(unittest.TestCase):
    def test_reproduces_independent_core_pipeline(self):
        output = engine.simulate({})
        cfg, beam = engine.physics(engine.validate({}))
        names = sorted({(r['family'], r['n'], r['m']) for r in output['rows']})
        modes = [solve_mode(*name, cfg) for name in names]
        direct = decompose_gaussian(modes, cfg, beam, samples=96)
        self.assertAlmostEqual(output['metrics']['coupled'], direct.coupled_power / direct.input_power, places=11)
        self.assertAlmostEqual(output['metrics']['transmission'], direct.power_at(.4) / direct.input_power, places=10)
        self.assertEqual(output['metrics']['fallback_count'], 0)
        self.assertGreater(output['metrics']['coupled'], .999)

    def test_power_at_zero_and_coefficients(self):
        output = engine.simulate({'theta_deg': .6, 'offset_um': 12})
        zero = engine.slice_field({'z_cm': 0})
        self.assertAlmostEqual(zero['power_fraction'], output['metrics']['coupled'], places=10)
        self.assertAlmostEqual(sum(r['weight'] for r in output['rows']), 1, places=12)
        self.assertTrue(all(r['alpha_power_per_m'] >= 0 for r in output['rows']))
        self.assertTrue(np.isfinite(output['power']['fraction']).all())

    def test_rotational_symmetry(self):
        x = engine.simulate({'polarization': 'x'})
        y = engine.simulate({'polarization': 'y'})
        self.assertAlmostEqual(x['metrics']['transmission'], y['metrics']['transmission'], places=9)
        np.testing.assert_allclose(x['field']['intensity'], y['field']['intensity'], atol=1e-7, equal_nan=True)

    def test_inadequate_sampling_is_rejected(self):
        for config in ({'theta_deg': 15}, {'waist_um': 1}, {'samples': 256, 'max_modes': 128}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                engine.validate(config)

    def test_nonfinite_out_of_range_and_fractional_inputs(self):
        for config in ({'wavelength_nm': float('nan')}, {'length_cm': float('inf')},
                       {'samples': 64.5}, {'max_modes': True}, {'offset_um': 160},
                       {'epsilon_imag': -1}, {'polarization': 'unsupported'}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                engine.validate(config)

    def test_json_is_finite_and_contains_units(self):
        text = engine.dispatch('simulate')
        self.assertNotIn('NaN', text)
        self.assertNotIn('Infinity', text)
        output = json.loads(text)
        self.assertEqual(len(output['field']['intensity']), 96**2)
        self.assertEqual(output['config']['length_cm'], 40)


class ImageTests(unittest.TestCase):
    @staticmethod
    def spe(width=20, height=20, frames=1, version=2.):
        header = bytearray(4100)
        for offset, kind, value in ((42, '<H', width), (656, '<H', height),
                                    (108, '<h', 3), (1446, '<i', frames), (1992, '<f', version)):
            struct.pack_into(kind, header, offset, value)
        data = np.arange(width*height*frames, dtype='<u2')
        return bytes(header) + data.tobytes()

    def test_spe_orientation_and_stack(self):
        result, meta = engine.read_spe(self.spe(20, 1, 25))
        self.assertEqual(result.shape, (25,20))
        self.assertEqual(result[1,0], 20)
        self.assertEqual(meta['spe_mode'], 'stack')
        result, _ = engine.read_spe(self.spe(20,20,2), 'mean')
        self.assertEqual(result[0,0], 200)

    def test_corrupt_and_unsupported_spe(self):
        for raw in (b'bad', self.spe()[:-10], self.spe(version=3), self.spe(width=0)):
            with self.assertRaises(ValueError): engine.read_spe(raw)

    def test_16bit_png_keeps_scientific_range(self):
        values = np.arange(400, dtype=np.uint16).reshape(20,20)*100
        stream=io.BytesIO();Image.fromarray(values).save(stream,format='PNG')
        engine.load_image({'name':'test.png'}, stream.getvalue())
        self.assertEqual(engine._image.max(), values.max())
        np.testing.assert_array_equal(engine._image, values)

    def test_known_mode_is_recovered_from_synthetic_image(self):
        image = engine.demo_image()
        output = engine.analyse_image({**image['roi'], 'catalogue':100})
        self.assertEqual(output['rows'][0]['name'], 'HE_1,3')
        self.assertGreater(output['rows'][0]['similarity_score'], .99)
        self.assertGreater(output['rows'][0]['correlation_2d'], .99)

    def test_invisible_roi_rejected(self):
        engine.demo_image()
        with self.assertRaises(ValueError):
            engine.analyse_image({'center_x':500, 'center_y':500, 'radius_px':20})

    def test_empty_image_is_rejected(self):
        engine.demo_image()
        previous=engine._image.copy()
        stream=io.BytesIO();Image.fromarray(np.zeros((20,20), dtype='uint8')).save(stream,format='PNG')
        with self.assertRaises(ValueError): engine.load_image({'name':'black.png'},stream.getvalue())
        np.testing.assert_array_equal(engine._image,previous)

    def test_unknown_action_never_executes_code(self):
        with self.assertRaises(ValueError): engine.dispatch('__import__("os")')


class ModeLabTests(unittest.TestCase):
    term=dict(family='HE',n=1,m=1,orientation='c',amplitude=1,phase_deg=0)

    def test_unit_power_and_constructive_destructive_interference(self):
        single=json.loads(engine.dispatch('mode_lab',{'terms':[self.term]}))
        self.assertAlmostEqual(single['power'],1,places=12)
        doubled=engine.mode_lab({'terms':[self.term,self.term]})
        self.assertAlmostEqual(doubled['power'],4,places=12)
        cancelled=engine.mode_lab({'terms':[self.term,{**self.term,'phase_deg':180}]})
        self.assertTrue(cancelled['cancelled'])
        self.assertEqual(cancelled['power'],0)
        self.assertEqual(np.nanmax(cancelled['field']['intensity']),0)

    def test_orthogonal_polarizations_add_without_interference(self):
        mixed=engine.mode_lab({'terms':[self.term,{**self.term,'orientation':'s','phase_deg':90}]})
        self.assertAlmostEqual(mixed['power'],2,places=12)

    def test_all_families_and_propagation(self):
        for family,n in [('HE',2),('EH',1),('TE',0),('TM',0)]:
            with self.subTest(family=family):
                result=engine.mode_lab({'terms':[{**self.term,'family':family,'n':n}], 'z_cm':40})
                expected=math.exp(-result['rows'][0]['alpha_power_per_m']*.4)
                self.assertAlmostEqual(result['power_ratio'],expected,places=11)

    def test_invalid_and_underresolved_modes_are_rejected(self):
        cases=[[],[dict(self.term,n=0)],[dict(self.term,m=0)],[dict(self.term,n=1.2)],
               [dict(self.term,family='TE',n=1)],[dict(self.term,amplitude=0)],
               [dict(self.term,m=60)],[dict(self.term,phase_deg=float('nan'))], [self.term]*13]
        for terms in cases:
            with self.subTest(terms=terms),self.assertRaises(ValueError):engine.mode_lab({'terms':terms})

    def test_mode_inspection_preserves_simulation_state(self):
        engine.simulate({})
        before=engine.slice_field({'z_cm':20})
        engine.mode_lab({'terms':[self.term]})
        after=engine.slice_field({'z_cm':20})
        np.testing.assert_allclose(before['intensity'],after['intensity'],equal_nan=True)


if __name__ == '__main__': unittest.main(verbosity=2)
