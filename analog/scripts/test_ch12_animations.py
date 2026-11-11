"""Physical checks independent of chapter 12 scene labels and interpolation."""
import itertools
import math
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals import application_models as m
from scripts.visuals import application_scenes as scenes


class ApplicationModels(unittest.TestCase):
    def test_difference_amplifier_kcl_and_all_tolerance_corners(self):
        for t in [.001,.01]:
            ratios=[]
            for signs in itertools.product([-1,1],repeat=4):
                r1,r2,r3,r4=[1+t*s for s in signs]
                ad,ac=m.difference_gains(r1,r2,r3,r4)
                for vd,cm in [(.001,2),(-.02,1),(0,3)]:
                    v1,v2=cm-vd/2,cm+vd/2
                    vp=v2*r4/(r3+r4)
                    vo=ad*vd+ac*cm
                    self.assertAlmostEqual((v1-vp)/r1+(vo-vp)/r2,0)
                if abs(ac)>1e-12:ratios.append(abs(ad/ac))
            self.assertAlmostEqual(min(ratios),1/(2*t))

    def test_integrator_and_differentiator_from_complex_impedances(self):
        for f in [1,100,10000,1e6]:
            s=2j*math.pi*f
            self.assertAlmostEqual(m.leaky(f),-1/(1e-6+s*1e-8)/1e4)
            self.assertAlmostEqual(m.differentiator(f),-1/(1e-4+s*1e-9)/(1e3+1/(s*1e-8)))
        self.assertAlmostEqual(abs(m.differentiator(1/(2*math.pi*1e-5))),5)

    def test_sallen_key_two_node_kcl_for_general_gain(self):
        r1,r2,c1,c2=2200,2700,1e-8,5e-9
        for k in [1,1.4,2]:
            f0,q=m.sallen_key(r1,r2,c1,c2,k)
            for f in [100,10000,1e5]:
                s=2j*math.pi*f
                # X and Y nodes, Vout=K*Y; independent nodal equations.
                matrix=[[1/r1+1/r2+s*c1,-1/r2-s*c1*k],[-1/r2,1/r2+s*c2]]
                x,y=np.linalg.solve(np.array(matrix),[1/r1,0])
                self.assertAlmostEqual(k*y,k*m.lowpass(f/f0,q))

    def test_cutoff_and_step_damping_are_not_interchangeable(self):
        for q in [.5,1/math.sqrt(3),1/math.sqrt(2),.864]:
            self.assertAlmostEqual(abs(m.lowpass(m.f3_ratio(q),q)),1/math.sqrt(2))
        self.assertAlmostEqual(m.f3_ratio(.5),math.sqrt(math.sqrt(2)-1))
        self.assertAlmostEqual(m.second_step(math.pi*math.sqrt(2),1/math.sqrt(2))-1,math.exp(-math.pi))

    def test_hold_capacitor_obeys_charge_balance(self):
        dt=1e-6
        for t in [0,.01,.1]:
            center=m.peak_hold(t)
            derivative=(m.peak_hold(t+dt)-m.peak_hold(t-dt))/(2*dt)
            self.assertAlmostEqual(derivative,(-center/1e7-1e-7)/1e-7,places=8)

    def test_riso_returns_actual_unity_crossings(self):
        expected=[10.195,88.185,7.220]
        for (iso,feedback),pm in zip([(0,'A'),(50,'A'),(50,'B')],expected):
            f,phase=m.crossing(lambda f:m.capacitive_loop(f,iso,feedback))
            self.assertAlmostEqual(abs(m.capacitive_loop(f,iso,feedback)),1)
            self.assertAlmostEqual(phase,pm,delta=.015)
        for iso,fb,at in [(0,'A','load'),(50,'A','amp'),(50,'A','load'),(50,'B','load')]:
            self.assertAlmostEqual(m.capacitive_step(.002,iso,fb,at),1e5/(1e5+1))
        self.assertGreater(max(m.capacitive_step(t) for t in np.linspace(0,20e-6,501)),1.7)
        for at in ['amp','load']:
            self.assertLess(max(m.capacitive_step(t,50,'A',at) for t in np.linspace(0,80e-6,501)),1.05)

    def test_tia_kcl_includes_input_capacitance_and_finite_gain(self):
        for cf in [0,.4e-12,1e-12]:
            for f in [0,1e4,4e5,1e7]:
                s=2j*math.pi*f;vo=m.tia_transimpedance(f,cf)
                a=1e5/(1+1j*f/100);vn=-vo/a
                feedback=(vn-vo)*(1e-6+s*cf)
                self.assertAlmostEqual(s*1e-11*vn+feedback,1)
                self.assertAlmostEqual(m.tia_ng(f,cf),1+s*1e-11/(1e-6+s*cf))
        crossing,pm=m.crossing(lambda f:m.tia_loop(f,0))
        self.assertAlmostEqual(crossing/1000,398.783,delta=.01)
        self.assertLess(pm,3)

    def test_tia_step_obeys_second_order_ode(self):
        dt=1e-10;wp=2*math.pi*100;a0=1e5
        for cf in [0,.4e-12,1e-12]:
            a=1e6*(1e-11+cf)/wp;b=1/wp+1e6*(1e-11+cf)+a0*1e6*cf;c=1+a0
            for t in [.5e-6,2e-6,5e-6]:
                y=m.tia_step(t,cf);lo=m.tia_step(t-dt,cf);hi=m.tia_step(t+dt,cf)
                residual=a*(hi-2*y+lo)/dt**2+b*(hi-lo)/(2*dt)+c*y-a0
                self.assertLess(abs(residual/a0),1e-5)

    def test_integrator_slopes_and_peak_to_peak(self):
        for rc,pp in [(1e-4,5),(1.25e-4,4),(2.5e-4,2)]:
            self.assertAlmostEqual(m.triangle(.0005,rc),-pp)
            self.assertAlmostEqual(m.triangle(.001,rc),0)
            self.assertAlmostEqual((m.triangle(.0002+1e-7,rc)-m.triangle(.0002,rc))/1e-7,-1/rc)

    def test_half_lsb_and_noise_power(self):
        for n in [8,12,16]:
            self.assertAlmostEqual(math.exp(-m.settling_tau(n)),2**(-n-1))
            self.assertAlmostEqual(m.settling_tau(n)-m.settling_tau(n,False),math.log(2))
        self.assertAlmostEqual(m.source_noise(1e6,0,0)**2,4*1.380649e-23*300*1e6)
        self.assertGreater(m.source_noise(1e6,5e-9,1e-12),m.source_noise(1e6,20e-9,1e-15))

    def test_scene_samples_stay_inside_physical_axes(self):
        for key,spec in scenes.SPECS.items():
            for stage in range(4):
                for fn,_color,_dash in scenes.functions(key,stage):
                    for x in np.linspace(*spec['xlim'],241):
                        y=fn(x)
                        self.assertTrue(math.isfinite(y),(key,x,y))
                        self.assertGreaterEqual(y,spec['ylim'][0]-1e-8,(key,x,y))
                        self.assertLessEqual(y,spec['ylim'][1]+1e-8,(key,x,y))


if __name__=='__main__':unittest.main()
