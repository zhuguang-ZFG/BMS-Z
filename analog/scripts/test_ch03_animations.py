"""Validate current laws and the teaching model against independent calculations."""
import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.visuals.scenes import ch03_bias_sweep_v2 as bias
from scripts.visuals.scenes import ch03_forced_beta_v2 as forced
from scripts.visuals.scenes import ch03_ce_linearity_v2 as ce


class Ch03AnimationTests(unittest.TestCase):
    def test_divider_currents_satisfy_kcl_including_base_loading(self):
        for beta in [100, 300, 600]:
            ic = bias.collector_ma(beta, 'divider') / 1000
            ib = ic / beta
            ve = (ic + ib) * bias.RE
            vb = ve + bias.VBE
            self.assertAlmostEqual((bias.VCC-vb)/bias.R1, vb/bias.R2+ib)
        ratio=bias.collector_ma(300,'divider')/bias.collector_ma(100,'divider')-1
        self.assertAlmostEqual(.04837,ratio,places=4)

    def test_fixed_bias_clips_at_the_load_limit(self):
        self.assertAlmostEqual(1,bias.collector_ma(100,'fixed'))
        self.assertAlmostEqual(5.9,bias.collector_ma(600,'fixed'))
        self.assertAlmostEqual(bias.VSAT,bias.VCC-bias.collector_ma(600,'fixed')/1000*bias.RC)

    def test_drawn_bias_curves_recover_the_computed_currents(self):
        for mode in ['fixed','divider']:
            node=ET.fromstring(bias.trace(mode))
            for pair in node.get('points').split():
                x,y=map(float,pair.split(','))
                self.assertAlmostEqual((350-y)/36,bias.collector_ma(x,mode),places=4)

    def test_forced_beta_bars_preserve_inverse_current_ratio(self):
        for beta in [2,10,50]:
            node=ET.fromstring(forced.bar(beta,100,forced.BLUE))
            current=float(node.get('width'))/12
            self.assertAlmostEqual(forced.LOAD_MA,current*beta)
        self.assertAlmostEqual(5,forced.base_ma(2)/forced.base_ma(10))
        with self.assertRaises(ValueError):
            forced.base_ma(0)

    def test_exponential_model_has_correct_small_signal_slope_and_saturation(self):
        epsilon=.001  # mVpp
        a=ce.output_v(math.pi/2,epsilon,'exponential')
        b=ce.output_v(3*math.pi/2,epsilon,'exponential')
        self.assertAlmostEqual(-ce.ICQ*ce.RC/ce.VT,(a-b)/(epsilon/1000),places=5)
        self.assertAlmostEqual(2,ce.output_v(math.pi/2,35,'exponential'))
        self.assertGreater(ce.output_v(math.pi/2,30,'linear'),2)
        self.assertAlmostEqual(2,ce.output_v(math.pi/2,30,'exponential'))
        # Already asymmetric before clipping: the positive current excursion is larger.
        low=6-ce.output_v(math.pi/2,10,'exponential')
        high=ce.output_v(3*math.pi/2,10,'exponential')-6
        self.assertGreater(low,high)

    def test_print_layouts_are_static_and_readable_at_138mm(self):
        for module in [bias,forced,ce]:
            for node in ET.fromstring(module.storyboard()).iter():
                self.assertNotIn('scale(',node.get('transform',''))
                self.assertFalse(node.tag.rsplit('}',1)[-1].startswith('animate'))
                if node.tag.endswith('}text'):
                    self.assertGreaterEqual(float(node.get('font-size'))*138/25.4*72/720,8.5)
