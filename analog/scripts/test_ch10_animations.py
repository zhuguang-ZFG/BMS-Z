import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals import timer_models as m


class TimerModels(unittest.TestCase):
    def test_steady_cycle_crossings_and_rc_differential_equation(self):
        th,tl=m.astable()
        self.assertAlmostEqual(th,.0005406548008367573)
        self.assertAlmostEqual(tl,.0004713400827807628)
        self.assertAlmostEqual(m.cycle(th)[0],6)
        self.assertAlmostEqual(m.cycle(th+tl)[0],3)
        for t in [th/2,th+tl/2]:
            v,on=m.cycle(t);dt=1e-10
            dv=(m.cycle(t+dt)[0]-m.cycle(t-dt)[0])/(2*dt)
            current=(9-v)/7800 if on else -v/6800
            self.assertAlmostEqual(100e-9*dv,current,places=9)

    def test_state_priorities_and_deadband_memory(self):
        self.assertEqual(m.logic(False,0,9,1),0)
        self.assertEqual(m.logic(True,0,9,0),1)
        self.assertEqual(m.logic(True,9,9,1),0)
        for old in [0,1]:self.assertEqual(m.logic(True,9,0,old),old)

    def test_first_pulse_depends_on_initial_charge(self):
        th,_=m.astable()
        first=7800*100e-9*math.log(3)
        self.assertAlmostEqual(m.first_charge(first),6)
        self.assertAlmostEqual(m.first_charge(th,3),6)
        self.assertAlmostEqual(first/th,math.log(3)/math.log(2))

    def test_discharge_floor_slows_discharge_and_current_accounts(self):
        th,tl=m.astable(floor=.15)
        self.assertGreater(tl,m.astable()[1])
        self.assertAlmostEqual(.15+(6-.15)*math.exp(-tl/.00068),3)
        supply,cap=m.discharge_current(6)
        self.assertAlmostEqual(supply,.00885)
        self.assertAlmostEqual(cap,5.85/6800)
        self.assertAlmostEqual(supply+cap,(9-.15)/1000+(6-.15)/6800)

    def test_diode_drop_keeps_thresholds_but_delays_charge(self):
        th0,tl0=m.diode_times(0)
        self.assertAlmostEqual(th0,tl0)
        for vf in [.3,.6,.8]:
            th,tl=m.diode_times(vf)
            self.assertGreater(th,th0)
            self.assertEqual(tl,tl0)
            self.assertAlmostEqual(5-vf-(5-vf-5/3)*math.exp(-th/.001),10/3)
        with self.assertRaises(ValueError):m.diode_times(.9)

    def test_output_loading_lengthens_pulse_until_unreachable(self):
        t1,_=m.output_feedback(5)
        t2,_=m.output_feedback(3.6)
        self.assertGreater(t2,t1)
        self.assertEqual(m.output_feedback(3.3)[0],math.inf)
        high,low=m.output_feedback(5,vol=0)
        self.assertAlmostEqual(high,low)

    def test_control_changes_charge_time_but_ideal_low_time_is_constant(self):
        last=0
        for control in [3,4,6,8]:
            th,tl=m.astable(control=control)
            self.assertGreater(th,last);last=th
            self.assertAlmostEqual(tl,6800*100e-9*math.log(2))
            self.assertAlmostEqual(9-(9-control/2)*math.exp(-th/.00078),control)

    def test_leakage_kcl_and_unreachable_threshold(self):
        duration=m.monostable(1e-6)
        target=9-1e-6*560000
        self.assertAlmostEqual(target*(1-math.exp(-duration/(560000*47e-6))),6)
        self.assertGreater(duration,m.monostable())
        self.assertEqual(m.monostable(6e-6),math.inf)

    def test_recovery_retains_supply_feed_and_residual_charge(self):
        self.assertEqual(m.recovery(0)[1],0)
        for gap in [1e-5,1e-3,.005]:
            v,duration=m.recovery(gap)
            self.assertAlmostEqual(5-(5-v)*math.exp(-duration),10/3)
            dt=1e-8
            derivative=(m.recovery(gap+dt)[0]-m.recovery(gap-dt)[0])/(2*dt)
            self.assertAlmostEqual(10e-6*derivative,(5-v)/1e5-v/100,places=8)
        v,_=m.recovery(.1)
        self.assertAlmostEqual(v,5*100/100100)

    def test_all_plotted_points_are_finite_including_recovery_origin(self):
        from scripts.visuals import timer_scenes as s
        for key,spec in s.SPECS.items():
            if key=='threshold_memory':continue
            lo,hi=spec['xlim']
            for stage in range(4):
                for fn,_,_ in s.functions(key,stage):
                    for i in range(101):
                        self.assertTrue(math.isfinite(fn(lo+(hi-lo)*i/100)),(key,stage,i))

    def test_print_frames_and_minimum_text_size(self):
        from scripts.visuals import timer_scenes as s
        for key in s.SPECS:
            root=ET.fromstring(s.storyboard(key))
            self.assertEqual(sum(bool(n.get('data-storyboard-beat')) for n in root.iter()),4)
            for n in root.iter():
                self.assertFalse(n.tag.rsplit('}',1)[-1].startswith('animate'))
                if n.tag.endswith('}text'):
                    self.assertGreaterEqual(float(n.get('font-size'))*138/25.4*72/720,8.5)

    def test_low_reset_threshold_crosses_before_one_rc(self):
        for voltage in [.3,.7,1]:
            t=m.crossing(0,12,voltage,.47)
            self.assertAlmostEqual(m.reset_ramp(t),voltage)
            self.assertLess(t,.047)

    def test_timing_tolerances_multiply_and_resistors_are_weighted(self):
        lo,hi=m.tolerance_corners()
        corners=[r*c*(-math.log(1-alpha))/math.log(3)
                 for r in [.99,1.01] for c in [.95,1.05] for alpha in [.65,.68]]
        self.assertEqual(lo,min(corners));self.assertEqual(hi,max(corners))
        for a,b in [(.99,1.01),(1.01,.99),(.99,.99),(1.01,1.01)]:
            self.assertLessEqual(abs((a*1000+2*b*6800)/14600-1),.010000001)
