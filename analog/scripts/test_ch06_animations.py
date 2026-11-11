"""Conservation, signed DC equations, integration and dynamic boundary tests."""
import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals import opamp_models as m, opamp_scenes as scenes
from scripts.visuals.primitives import directed_arrow


class OpampModelTests(unittest.TestCase):
    def test_arrows_follow_supply_and_signal_direction(self):
        for x,y in [(0,30),(0,-30),(30,0),(-30,0),(-30,40)]:
            markup=ET.fromstring('<svg>'+directed_arrow(0,0,x,y)+'</svg>')
            points=[tuple(map(float,p.split(','))) for p in markup.find('polygon').get('points').split()]
            self.assertEqual(points[0],(x,y))
            center=tuple((points[1][i]+points[2][i])/2 for i in range(2))
            self.assertGreater((x-center[0])*x+(y-center[1])*y,0)
            self.assertAlmostEqual((x-center[0])*y-(y-center[1])*x,0,delta=.001)

    def test_compensation_fixed_charge_and_transconductance(self):
        for c in [30e-12,45e-12,60e-12]:
            gbw,slew=m.compensation(c)
            self.assertAlmostEqual(c*slew,15e-6,places=15)
            self.assertAlmostEqual(2*math.pi*c*gbw,2*math.pi*30e-6,places=15)
        self.assertAlmostEqual(m.compensation(30e-12)[0]/m.compensation(60e-12)[0],2)

    def test_follower_obeys_original_open_loop_equation(self):
        for resistance in [1000,50000,100000]:
            output=1+m.follower_error(resistance)
            plus=1-20e-9*resistance
            self.assertAlmostEqual(output,1e5*(plus+.003-output),places=10)
        # Signed cancellation differs from a sum-of-magnitudes budget.
        self.assertLess(m.follower_error(1e5),.001)

    def test_bias_balance_satisfies_input_node_kcl(self):
        for r in [0,4500,9000]:
            for ip in [20e-9,22e-9]:
                node=-ip*r
                output=m.balanced_error(r,plus=ip)
                self.assertAlmostEqual(node/10000+(node-output)/90000+20e-9,0,places=16)
        self.assertAlmostEqual(m.balanced_error(9000),0)
        self.assertAlmostEqual(m.balanced_error(9000,plus=22e-9),-.00018)

    def test_speed_limits_are_independent(self):
        self.assertAlmostEqual(m.closed_gain(7000),100/math.sqrt(2))
        self.assertAlmostEqual(m.closed_gain(10000),57.3462344,places=6)
        self.assertAlmostEqual(m.sine_slope(.5e6/(2*math.pi*5)),.5e6)

    def test_rejection_is_input_referred_before_noise_gain(self):
        self.assertAlmostEqual(m.rejection_error(1),.01)
        self.assertAlmostEqual(m.rejection_error(.05,noise_gain=10),.005)
        self.assertAlmostEqual(m.rejection_error(1,db=80),.0001)

    def test_noise_matches_integral_not_cutoff_as_bandwidth(self):
        # Substitution u=atan(f/fc) turns integral of |H|² df into fc du.
        cutoff=20000; n=20000; u_max=math.pi/2-1e-5; du=u_max/n
        integral=0
        for i in range(n):
            u=(i+.5)*du
            f=cutoff*math.tan(u)
            integral+=1/(1+(f/cutoff)**2)*cutoff/(math.cos(u)**2)*du
        integral+=cutoff*1e-5
        self.assertAlmostEqual(40e-9*math.sqrt(integral),m.noise_rms(cutoff),places=12)
        self.assertAlmostEqual(m.noise_rms(cutoff,first_order=False)*1e6,5.656854,places=6)

    def test_rate_limited_response_matches_differential_equation(self):
        t1,e,tau=m.settling_handoff()
        self.assertAlmostEqual(m.step_response(t1),1-e)
        for t in [.2e-6,1e-6,t1,2.2e-6,3e-6]:
            dt=1e-12
            slope=(m.step_response(t+dt)-m.step_response(t-dt))/(2*dt)
            expected=min(.5e6,(1-m.step_response(t))/tau)
            self.assertAlmostEqual(slope,expected,delta=1)
        self.assertAlmostEqual(m.settling_time()*1e6,2.537423435,places=8)
        self.assertAlmostEqual(1-m.step_response(m.settling_time()),.001)
        self.assertAlmostEqual(m.step_response(0),0)
        self.assertAlmostEqual(m.step_response(1),1)

    def test_small_step_never_needs_a_slew_segment(self):
        step=.01
        t,e,tau=m.settling_handoff(step)
        self.assertEqual(t,0)
        self.assertAlmostEqual(m.settling_time(step=step),tau*math.log(1000))
        self.assertAlmostEqual(m.step_response(tau,step=step),step*(1-math.exp(-1)))

    def test_print_four_frames_stay_readable_without_scaling(self):
        for key in scenes.SPECS:
            svg=ET.fromstring(scenes.storyboard(key))
            self.assertEqual(4,len([n for n in svg.iter() if n.get('data-storyboard-beat')]))
            for node in svg.iter():
                self.assertFalse(node.tag.rsplit('}',1)[-1].startswith('animate'))
                self.assertNotIn('scale(',node.get('transform',''))
                if node.tag.endswith('}text'):
                    self.assertGreaterEqual(float(node.get('font-size'))*138/25.4*72/720,8.5)
