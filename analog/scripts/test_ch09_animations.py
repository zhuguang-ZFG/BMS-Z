import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals import regulator_models as m, regulator_scenes as s


class RegulatorModels(unittest.TestCase):
    def test_bandgap_compensates_both_density_ratio_and_temperature(self):
        for n in [2,8,16]:
            for temperature in [-40,25,85]:
                ct,pt,total=m.bandgap(temperature,n)
                self.assertAlmostEqual(total,1.2463,places=10)
                self.assertAlmostEqual(ct+pt,total)
        self.assertAlmostEqual(m.bandgap(26)[0]-m.bandgap(25)[0],-.002)

    def test_shunt_current_and_energy_conservation_at_corners(self):
        for vin in [10.8,12,13.2]:
            for il in [0,.01]:
                iz,pz,pr=m.shunt(vin,il)
                feed=(vin-5.1)/360
                self.assertAlmostEqual(feed,iz+il)
                self.assertAlmostEqual(vin*feed,pr+pz+5.1*il)
                self.assertGreaterEqual(iz,.005)
        self.assertAlmostEqual(m.shunt(13.2,0)[0],.0225)

    def test_tl431_bias_flows_into_ref(self):
        for top,bottom in [(1e4,1e4),(1e5,1e5),(8.6e4,1e4)]:
            output=m.tl431_output(top,bottom)
            self.assertAlmostEqual((output-2.5)/top,2.5/bottom+2e-6)
        self.assertAlmostEqual(m.tl431_output(1e4,1e4),5.02)
        self.assertAlmostEqual(m.tl431_output(1e5,1e5),5.2)

    def test_dropout_valley_follows_pass_resistance(self):
        vin,vout=m.dropout(.00075)
        self.assertAlmostEqual(vin,3.3)
        self.assertAlmostEqual(vout,3.15)
        self.assertAlmostEqual(m.dropout(.00025)[1],3.3)

    def test_thermal_boundary_and_input_power(self):
        for theta in [21,50]:
            self.assertAlmostEqual(m.junction(m.thermal_current(theta),theta),125)
        self.assertAlmostEqual(m.junction(.3),153)
        self.assertAlmostEqual(m.power(.3)+5*.3,12*(.3+.005))

    def test_efficiency_limits(self):
        self.assertAlmostEqual(m.efficiency(.01),.44)
        self.assertAlmostEqual(m.efficiency(.3),.6491803279)
        self.assertEqual(m.efficiency(0),0)
        self.assertAlmostEqual(m.efficiency(1,iq=0),.66)

    def test_transient_conserves_charge_and_has_continuous_handoff(self):
        dt=1e-10
        for t in [1e-6,4e-6,6e-6,10e-6,20e-6]:
            e,ic,out=m.transient(t)
            derivative=(m.transient(t+dt)[0]-m.transient(t-dt)[0])/(2*dt)
            self.assertAlmostEqual(derivative*10e-6,ic,places=8)
            self.assertAlmostEqual(out,e+.05*ic)
            self.assertAlmostEqual(m.transient(t,delta=-.49)[2],-out)
        for column in range(3):
            self.assertAlmostEqual(m.transient(5e-6-1e-12)[column],m.transient(5e-6+1e-12)[column],delta=1e-6)
        self.assertAlmostEqual(m.transient(5e-6)[2],-.2695)
        self.assertLess(m.transient(7e-6)[2],-.2695)
        self.assertAlmostEqual(m.transient(.001)[2],0)

    def test_periodic_charge_draw_reaches_energy_balanced_cycle(self):
        peak,trough=m.pulse_steady()
        self.assertAlmostEqual(peak-trough,.001)
        self.assertAlmostEqual(trough,peak*math.exp(-1))
        self.assertAlmostEqual(peak,.0015819767068693265)
        self.assertAlmostEqual(m.pulse_deficit(.001),peak,places=12)
        # Average recharge current must equal withdrawn charge per period.
        average=peak*(10*1e-6)/10e-6*(1-math.exp(-1))
        self.assertAlmostEqual(average/10,1e-9/10e-6)

    def test_transient_minimum_is_stationary_and_after_handoff(self):
        t=m.transient_minimum_time()
        self.assertAlmostEqual(t*1e6,6.9444444444)
        self.assertGreater(t,5e-6)
        dt=1e-10
        derivative=(m.transient(t+dt)[2]-m.transient(t-dt)[2])/(2*dt)
        self.assertAlmostEqual(derivative,0,delta=1e-4)
        self.assertLess(m.transient(t)[2],m.transient(t-1e-6)[2])
        self.assertLess(m.transient(t)[2],m.transient(t+1e-6)[2])

    def test_print_frames_preserve_all_beats_with_legible_static_text(self):
        for key in s.SPECS:
            root=ET.fromstring(s.storyboard(key))
            self.assertEqual(4,len([n for n in root.iter() if n.get('data-storyboard-beat')]))
            for node in root.iter():
                self.assertFalse(node.tag.rsplit('}',1)[-1].startswith('animate'))
                if node.tag.endswith('}text'):
                    self.assertGreaterEqual(float(node.get('font-size'))*138/25.4*72/720,8.5)
