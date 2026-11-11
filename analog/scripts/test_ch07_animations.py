import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals import comparator_models as m, comparator_scenes as s


class ComparatorModelTests(unittest.TestCase):
    def test_rc_release_crossings_have_one_time_origin(self):
        tau=4700*50e-12
        self.assertAlmostEqual(m.release_crossing(1.4)*1e6,1.077,delta=.001)
        self.assertAlmostEqual(m.release_crossing(2.5)*1e6,1.0+tau*math.log(2)*1e6,delta=.001)
        self.assertAlmostEqual((m.release_crossing(4.5)-m.release_crossing(.5))/tau,math.log(9),places=12)
        self.assertEqual(m.release_voltage(0),0)

    def test_divider_opposed_tolerance_is_twenty_five_mv(self):
        self.assertAlmostEqual(m.divider(99e3,101e3),2.525)
        self.assertAlmostEqual(m.divider(101e3,99e3),2.475)
        self.assertAlmostEqual(m.opposing_error(.01),.025)
        self.assertAlmostEqual(m.opposing_error(-.01),-.025)

    def test_window_polarity_and_equality_boundary(self):
        self.assertEqual(m.window_state(2.8),(True,False,False))
        self.assertEqual(m.window_state(3.2),(False,False,True))
        self.assertEqual(m.window_state(3.8),(False,True,False))
        self.assertIsNone(m.window_state(3.0))

    def test_feedback_loading_changes_high_threshold(self):
        strong=m.loaded_thresholds(4700)[1]
        weak=m.loaded_thresholds(47000)[1]
        self.assertAlmostEqual(strong,2.718,delta=.002)
        self.assertAlmostEqual(weak,2.659,delta=.002)
        self.assertLess(weak,strong)
        self.assertAlmostEqual(m.loaded_thresholds(4700)[2],2.291,delta=.002)

    def test_delay_period_is_not_ideal_period_plus_two_delays(self):
        ideal=2*10e-6*math.log(3)
        delayed=m.oscillator_period()
        self.assertGreater(delayed,ideal)
        self.assertGreater(delayed,ideal+2*1.3e-6)
        self.assertAlmostEqual(delayed*1e6,25.369,delta=.02)

    def test_loaded_network_satisfies_both_node_current_balances(self):
        for rp in [1000,4700,47000,1000000]:
            voh,upper,lower=m.loaded_thresholds(rp)
            self.assertAlmostEqual((5-voh)/rp,(voh-upper)/1e5,places=13)
            self.assertAlmostEqual((voh-upper)/1e5,(upper-2.5)/1e4,places=13)
            self.assertAlmostEqual((2.5-lower)/1e4,(lower-.2)/1e5,places=13)

    def test_oscillator_obeys_rc_dynamics_and_delayed_threshold_switching(self):
        for tau,delay in [(10e-6,0),(10e-6,1.3e-6),(1e-3,1.3e-6)]:
            period=m.oscillator_period(tau,delay);half=period/2
            value=lambda t:m.oscillator_voltage(t,tau,delay)
            dt=tau*1e-6
            self.assertAlmostEqual(value(half-delay),.75,places=10)
            self.assertAlmostEqual(value(period-delay),.25,places=10)
            for t in [half*.3,half*1.3]:
                rail=1 if t<half else 0
                derivative=(value(t+dt)-value(t-dt))/(2*dt)
                self.assertAlmostEqual(derivative*tau,rail-value(t),places=8)
            for t in [half,period]:
                self.assertAlmostEqual(value(t-dt),value(t+dt),places=5)
            self.assertAlmostEqual(value(period+.2*half),value(.2*half),places=12)

    def test_glitch_memory_uses_prior_output_state(self):
        samples=[2.4,2.6,2.7,2.8,2.4,2.2]
        self.assertEqual(m.hysteresis_trace(samples),[True,True,True,False,False,True])
        self.assertAlmostEqual(m.ramp_crossing(30/11,start=2.3,slope=.001),427.2727,places=3)
        self.assertAlmostEqual(m.ramp_crossing(2.5,start=2.3,slope=.001),200)

    def test_all_storyboards_are_four_static_frames_and_readable(self):
        for key in s.SPECS:
            svg=ET.fromstring(s.storyboard(key))
            self.assertEqual(4,len([n for n in svg.iter() if n.get('data-storyboard-beat')]))
            for node in svg.iter():
                self.assertFalse(node.tag.rsplit('}',1)[-1].startswith('animate'))
                if node.tag.endswith('}text'):
                    self.assertGreaterEqual(float(node.get('font-size'))*138/25.4*72/720,8.5)
