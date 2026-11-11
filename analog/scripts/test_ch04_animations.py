"""Independent dimensional, differential and energy checks for MOSFET diagrams."""
import math
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals.scenes import ch04_transconductance_v2 as gm
from scripts.visuals.scenes import ch04_gate_transient_v2 as gate
from scripts.visuals.scenes import ch04_deadtime_energy_v2 as dead
from scripts.visuals.scenes import ch04_thermal_pulse_v2 as thermal
from scripts.visuals.scenes import ch04_gate_power_v2 as drive
from scripts.visuals.scenes import ch04_reference_figures as figures
from scripts.visuals.scenes.handdrawn_wave8 import deadtime_ledger


class Ch04ModelTests(unittest.TestCase):
    def test_local_transconductance_and_threshold_secant_differ(self):
        dv=1e-5
        slope=(gm.current(3+dv)-gm.current(3-dv))/(2*dv)
        self.assertAlmostEqual(10,slope)
        self.assertAlmostEqual(1,2*gm.current(3)/slope)
        self.assertEqual(0,gm.tangent(2.5))
        self.assertGreater(gm.current(2.5),0)

    def test_gate_response_satisfies_kcl_on_both_sides_of_the_ramp(self):
        for resistance in [1,10]:
            for time in [1,5,19,21,25,40]:
                dt=.0001
                deriv=(gate.gate_v(time+dt,resistance)-gate.gate_v(time-dt,resistance))/(2*dt*1e-9)
                injection=gate.CGD*gate.SLOPE if time<gate.RAMP_NS else 0
                self.assertAlmostEqual(injection,(gate.CGD+gate.CGS)*deriv+gate.gate_v(time,resistance)/resistance,places=6)
        self.assertAlmostEqual(8.5114,gate.gate_v(20,10),places=4)
        self.assertAlmostEqual(1,gate.gate_v(20,1),places=6)

    def test_deadtime_energy_and_static_label_have_correct_units(self):
        self.assertAlmostEqual(.4e-6,dead.energy_j())
        power=dead.energy_j()*dead.FREQUENCY
        self.assertAlmostEqual(.04,power)
        visible=' '.join(re.sub('<[^>]+>','',p) for p in deadtime_ledger())
        label=float(re.search(r'≈ ([\d.]+) W',visible)[1])
        self.assertAlmostEqual(power,label)

    def test_thermal_response_is_continuous_cools_and_accumulates(self):
        for t in [.5,2,2.5,4,4.5]:
            self.assertAlmostEqual(thermal.rise(t-1e-7,[0,2,4]),thermal.rise(t+1e-7,[0,2,4]),places=6)
        self.assertGreater(thermal.rise(.5,[0]),thermal.rise(1,[0]))
        self.assertGreater(thermal.rise(2.5,[0,2]),thermal.rise(.5,[0]))
        self.assertLess(thermal.rise(4.5,[0,2,4]),thermal.step(4.5))
        # For a long repeating train, average heat equals duty times steady rise.
        starts=[2*i for i in range(100)]
        mean=sum(thermal.rise(198+(i+.5)*2/1000,starts) for i in range(1000))/1000
        self.assertAlmostEqual(.25,mean,places=5)

    def test_driver_average_and_peak_currents_are_distinct(self):
        a=drive.accounts()
        self.assertAlmostEqual(.0007,a['average_a'])
        self.assertAlmostEqual(.007,a['power_w'])
        self.assertAlmostEqual(1,a['initial_a'])

    def test_output_curves_join_continuously_with_zero_saturation_slope(self):
        for od in [1,2,3]:
            self.assertAlmostEqual(figures.drain_current(od-1e-5,od),figures.drain_current(od+1e-5,od))
            self.assertAlmostEqual(od**2,figures.drain_current(5,od))
        self.assertAlmostEqual(1/6,1/(figures.drain_current(1e-6,3)/1e-6),places=5)

    def test_four_axes_power_is_always_voltage_times_current(self):
        for t in range(701):
            vg,vd,current,power=figures.switching_values(t)
            self.assertAlmostEqual(vd*current,power)
        energy=sum((figures.switching_values(t)[3]+figures.switching_values(t+1)[3])/2*1e-9 for t in range(150,560))
        self.assertAlmostEqual(20.56e-6,energy,places=10)
        self.assertAlmostEqual(.75,figures.switching_values(700)[3])

    def test_print_text_is_readable_without_scaled_miniature_frames(self):
        for module in [gm,gate,dead,thermal,drive]:
            for node in ET.fromstring(module.storyboard()).iter():
                self.assertNotIn('scale(',node.get('transform',''))
                self.assertFalse(node.tag.rsplit('}',1)[-1].startswith('animate'))
                if node.tag.endswith('}text'):
                    self.assertGreaterEqual(float(node.get('font-size'))*138/25.4*72/720,8.5)
