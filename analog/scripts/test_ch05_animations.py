"""Check conservation and limiting cases independently of chapter 5 drawings."""
import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals import interface_models as m
from scripts.visuals.scenes import ch05_ground_bounce_v2 as bounce
from scripts.visuals.scenes import ch05_tristate_timing_v2 as timing
from scripts.visuals.scenes import ch05_reference_figures as figures


class InterfaceModelTests(unittest.TestCase):
    def test_charging_energy_conservation_and_resistor_integral(self):
        for t in [.1,1,3,6]:
            supply,stored,heat=m.charging_accounts(t)
            self.assertAlmostEqual(supply,stored+heat,places=18)
            # Integral R i(t)^2 dt = CV²/2 (1-exp(-2t/RC)).
            expected=.5*20e-12*25*(-math.expm1(-2*t))
            self.assertAlmostEqual(expected,heat,places=18)
        source,stored,heat=m.charging_accounts(100)
        self.assertAlmostEqual(source*10e6,.005)
        self.assertAlmostEqual(stored,heat,places=18)

    def test_pullup_interval_obeys_both_guaranteed_constraints(self):
        lower,upper=m.pullup_bounds(100e-12)
        self.assertAlmostEqual(.003,(3.3-.4)/lower)
        time30=-upper*100e-12*math.log(.7)
        time70=-upper*100e-12*math.log(.3)
        self.assertAlmostEqual(300e-9,time70-time30,places=15)
        self.assertLess(lower,2200)
        self.assertGreater(upper,2200)
        lower,upper=m.pullup_bounds(400e-12)
        self.assertGreater(lower,upper)

    def test_shared_pullup_current_satisfies_kcl_and_kvl(self):
        for sinks in [1,2,8]:
            for pullups in [1,2]:
                voltage,total,each=m.sink_accounts(sinks,pullups)
                self.assertAlmostEqual(total,sinks*each)
                self.assertAlmostEqual(total,(3.3-voltage)/(1000/pullups))
                self.assertAlmostEqual(voltage,25*each)
        self.assertLess(m.sink_accounts(2)[1]/m.sink_accounts(1)[1],1.02)
        self.assertAlmostEqual(.006439,m.sink_accounts(2,2)[1],places=6)

    def test_unpowered_rail_satisfies_kcl_and_boundary_conditions(self):
        self.assertEqual(0,m.unpowered_rail(0))
        self.assertAlmostEqual(1.5,m.unpowered_rail(1))
        for t in [.001,.005,.02]:
            dt=1e-7
            slope=(m.unpowered_rail(t+dt)-m.unpowered_rail(t-dt))/(2*dt)
            voltage=m.unpowered_rail(t)
            self.assertAlmostEqual((3-voltage)/1e4,1e-6*slope+voltage/1e4,places=10)

    def test_bounce_matches_derivative_and_returns_to_zero(self):
        for n in [1,8]:
            slope=(bounce.current(1.001,n)-bounce.current(.999,n))/(.002e-9)
            self.assertAlmostEqual(5e-9*slope,bounce.bounce(1,n))
            self.assertEqual(0,bounce.bounce(3,n))
        self.assertAlmostEqual(.4,bounce.bounce(1,8))

    def test_actual_drive_overlap_not_just_command_gap(self):
        self.assertEqual(-15,timing.interval(5))
        self.assertEqual(10,timing.interval(30))
        self.assertEqual(0,timing.interval(20))

    def test_rc_rise_figure_marks_threshold_crossings_not_absolute_deadlines(self):
        for resistance,expected in [(1000,84.73),(2200,186.41),(4700,398.23)]:
            low=figures.crossing(.3,resistance)
            high=figures.crossing(.7,resistance)
            self.assertAlmostEqual(.3*3.3,figures.charge(low,resistance))
            self.assertAlmostEqual(.7*3.3,figures.charge(high,resistance))
            self.assertAlmostEqual(expected,high-low,delta=.01)
            self.assertGreater(high,high-low)

    def test_class_b_heat_matches_half_cycle_integral(self):
        for peak in [1,7.64,12]:
            n=10000
            heat=sum((12-peak*math.sin((i+.5)*math.pi/n))*peak*math.sin((i+.5)*math.pi/n)/8 for i in range(n))/(2*n)
            output,per_device=m.class_b(peak)
            self.assertAlmostEqual(heat,per_device,places=7)
            self.assertAlmostEqual(output+2*per_device,2*12*peak/(math.pi*8))
        peak=24/math.pi
        h=.001
        self.assertGreater(m.class_b(peak)[1],m.class_b(peak-h)[1])
        self.assertGreater(m.class_b(peak)[1],m.class_b(peak+h)[1])
        self.assertAlmostEqual(144/(8*math.pi**2),m.class_b(peak)[1])

    def test_print_text_is_readable_and_static(self):
        import importlib
        for name in ['capacitive_energy','ground_bounce','pullup_window','open_drain_sharing','backpower','tristate_timing','class_b_dissipation']:
            module=importlib.import_module('scripts.visuals.scenes.ch05_'+name+'_v2')
            for node in ET.fromstring(module.storyboard()).iter():
                self.assertFalse(node.tag.rsplit('}',1)[-1].startswith('animate'))
                self.assertNotIn('scale(',node.get('transform',''))
                if node.tag.endswith('}text'):
                    self.assertGreaterEqual(float(node.get('font-size'))*138/25.4*72/720,8.5)
