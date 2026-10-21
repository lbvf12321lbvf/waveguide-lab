import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
import numpy as np
from scipy.special import jn_zeros, jv
import web_engine as engine


class AutomaticSelectionTests(unittest.TestCase):
    def test_default_grows_to_target_and_ignores_inactive_manual_limit(self):
        a = engine.simulate({'mode_selection': 'auto', 'max_modes': 1})
        b = engine.simulate({'mode_selection': 'auto', 'max_modes': 6000})
        self.assertTrue(a['selection']['target_met'])
        self.assertLessEqual(a['metrics']['residual'], .001)
        self.assertGreater(len(a['selection']['passes']), 1)
        self.assertEqual(a['metrics']['physical_modes'], b['metrics']['physical_modes'])
        np.testing.assert_allclose(a['power']['fraction'], b['power']['fraction'], atol=1e-12)

    def test_manual_count_is_honoured_and_legacy_settings_stay_manual(self):
        a = engine.simulate({'mode_selection': 'manual', 'max_modes': 2})
        self.assertEqual(a['metrics']['physical_modes'], 2)
        self.assertGreater(a['metrics']['residual'], .001)
        self.assertEqual(a['selection']['method'], 'manual')
        self.assertEqual(engine.validate({'max_modes': 64})['mode_selection'], 'manual')
        self.assertEqual(engine.validate({})['mode_selection'], 'auto')

    def test_memory_guard_uses_actual_basis_not_the_requested_upper_limit(self):
        r = engine.simulate({'mode_selection': 'manual', 'max_modes': 6000, 'samples': 256})
        self.assertLess(r['metrics']['physical_modes'], 10)
        self.assertLess(r['selection']['estimated_memory_mb'], engine.WORKING_MEMORY_MB)

    def test_auto_reports_resource_stop_instead_of_claiming_target(self):
        with patch.object(engine, 'WORKING_MEMORY_MB', 40):
            r = engine.simulate({})
        self.assertFalse(r['selection']['target_met'])
        self.assertEqual(r['selection']['stop_reason'], 'memory_limit')
        self.assertTrue(any('working-memory budget' in w for w in r['warnings']))

    def test_manual_resource_overflow_is_rejected(self):
        with patch.object(engine, 'WORKING_MEMORY_MB', 40), self.assertRaisesRegex(ValueError, 'working-memory'):
            engine.simulate({'mode_selection': 'manual', 'max_modes': 5})

    def test_launch_parameters_change_automatic_basis(self):
        centred = engine.simulate({})
        tilted = engine.simulate({'theta_deg': 1, 'offset_um': 30})
        self.assertGreater(tilted['metrics']['physical_modes'], centred['metrics']['physical_modes'])
        self.assertTrue(tilted['selection']['target_met'])


class SlitAndSelectedFitTests(unittest.TestCase):
    def setUp(self):
        self.image = engine.demo_image()
        self.roi = self.image['roi']

    def slit(self, angle=0, width=30):
        return {**self.roi, 'catalogue': 100, 'slit_enabled': True, 'slit_width': width,
                'slit_angle': angle, 'slit_x': self.roi['center_x'], 'slit_y': self.roi['center_y']}

    def test_horizontal_vertical_and_oblique_slits_recover_known_mode(self):
        for angle in (0, 90, 37):
            with self.subTest(angle=angle):
                r = engine.analyse_image(self.slit(angle))
                self.assertEqual(r['rows'][0]['name'], 'HE_1,3')
                self.assertGreater(r['rows'][0]['correlation_2d'], .99)
                self.assertGreater(r['coverage'], .05)
                self.assertLess(r['coverage'], .3)
                self.assertTrue(np.isnan(r['predicted']).any())

    def test_outside_slit_cannot_change_preprocessing_or_ranking(self):
        config = {**self.slit(31), 'background': 10}
        reference = engine.analyse_image(config)
        mask, _ = engine.slit_mask(config, self.roi)
        engine._image[~mask] = 1e9
        changed = engine.analyse_image(config)
        np.testing.assert_allclose(reference['observed'], changed['observed'], atol=0, equal_nan=True)
        self.assertEqual(reference['rows'], changed['rows'])
        np.testing.assert_allclose(reference['radial']['observed'], changed['radial']['observed'], atol=0, equal_nan=True)

    def test_selected_two_mode_mixture_is_fitted_only_inside_slit(self):
        yy, xx = np.indices(engine._image.shape)
        rho = np.hypot(xx-self.roi['center_x'], yy-self.roi['center_y'])/self.roi['radius_px']
        u = jn_zeros(0, 4)
        field = jv(0, u[1]*rho) + .55*np.exp(.6j)*jv(0, u[3]*rho)
        engine._image = np.where(rho<=1, abs(field)**2, 0)
        config = {**self.slit(27, 45), 'fit_mode': 'selected', 'fit_terms': [
            dict(family='HE', n=1, m=2, orientation='c'),
            dict(family='HE', n=1, m=4, orientation='c')]}
        mask, _ = engine.slit_mask(config, self.roi)
        engine._image[~mask] = 1e8
        r = engine.analyse_image(config)
        self.assertEqual(r['fit']['modes'], ['HE_1,2', 'HE_1,4'])
        self.assertEqual(r['fit']['profiles'], ['HE_1,2c', 'HE_1,4c'])
        self.assertLess(r['fit']['residual'], .01)
        self.assertGreater(r['fit']['correlation'], .999)
        self.assertEqual(len(r['fit']['coefficients']), 2)
        coefficients = [complex(c['real'], c['imaginary'])/c['profile_rms']
                        for c in r['fit']['coefficients']]
        self.assertAlmostEqual(abs(coefficients[1]/coefficients[0]), .55, delta=.02)
        self.assertTrue(np.isnan(r['observed']).any())
        self.assertTrue(np.isfinite(r['fit']['restart_residuals']).all())

    def test_invalid_or_empty_slits_and_invalid_basis_rejected(self):
        cases = [{**self.slit(), 'slit_width': 0}, {**self.slit(), 'slit_angle': float('nan')},
                 {**self.slit(width=1), 'slit_y': 0},
                 {**self.roi, 'fit_mode': 'selected', 'fit_terms': []},
                 {**self.roi, 'fit_mode': 'selected', 'fit_terms': [dict(family='TE', n=1, m=1)]}]
        for config in cases:
            with self.subTest(config=config), self.assertRaises(ValueError):
                engine.analyse_image(config)

if __name__ == '__main__':
    unittest.main()
