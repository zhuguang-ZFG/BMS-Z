"""Independent physical checks for chapter 11 teaching models and rendered samples."""
import math
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.visuals import topology_models as m
from scripts.visuals import topology_scenes as scenes


class TopologyModels(unittest.TestCase):
    def test_differential_current_conservation_and_exponential_ratio(self):
        for vd in [-.06,-.02,0,.02,.06]:
            a,b=m.differential(vd)
            self.assertAlmostEqual(a+b,.001)
            self.assertAlmostEqual(a/b,math.exp(vd/m.VT))
        dv=1e-7
        slope=(m.differential(dv)[0]-m.differential(-dv)[0])/(2*dv)
        self.assertAlmostEqual(slope,.0005/m.VT/2,places=9)

    def test_cmrr_respects_output_reference_and_load_mismatch(self):
        ad,ac,dd,dc=m.cmrr(1e6)
        self.assertAlmostEqual(dd,-2*ad)
        self.assertAlmostEqual(dc,-.02*ac)
        self.assertEqual(m.cmrr(1e6,0)[3],0)
        self.assertAlmostEqual(20*math.log10(abs(ad/ac)),85.6799,places=3)

    def test_mirror_reference_kcl_with_early_effect(self):
        for beta in [20,100,300]:
            for voltage in [.65,5,10]:
                ratio=(1+voltage/100)/(1+.65/100)
                out=m.mirror(beta,voltage,100)
                first=out/ratio
                self.assertAlmostEqual(first+first/beta+out/beta,1)

    def test_damping_from_actual_unity_crossing_and_step_peak(self):
        for pm in [30,45,60,65]:
            z=m.damping(pm)
            w=math.sqrt(math.sqrt(1+4*z**4)-2*z*z)
            loop=1/(1j*w*(1j*w+2*z))
            self.assertAlmostEqual(abs(loop),1)
            self.assertAlmostEqual(180+math.degrees(math.atan2(loop.imag,loop.real)),pm)
            peak=math.pi/math.sqrt(1-z*z)
            self.assertAlmostEqual(m.step(peak,z)-1,m.overshoot(pm))

    def test_compensated_roots_recover_uncompensated_rc_and_polynomial(self):
        self.assertTrue(np.allclose(m.compensated(0),sorted([1/(2*math.pi*1e5*c) for c in [1e-11,1e-10]])))
        for cc in [1e-12,1e-11,3e-11]:
            a=1e-21+cc*1.1e-10
            b=1.1e-15+cc*(2e-5+.001)
            c=1e-10
            for f in m.compensated(cc):
                s=-2*math.pi*f
                self.assertAlmostEqual((a*s*s+b*s+c)/(abs(a*s*s)+abs(b*s)+c),0,places=10)

    def test_noise_integral_matches_quadrature_and_rss(self):
        f=np.geomspace(1,1e5,10001)
        psd=np.array([m.noise_density(x)**2 for x in f])
        variance=np.sum((psd[1:]+psd[:-1])/2*np.diff(f))
        self.assertAlmostEqual(variance/m.noise_integral(1,1e5)**2,1,places=6)
        with self.assertRaises(ValueError):m.noise_integral(0,100)
        terms,total=m.noise_budget()
        self.assertAlmostEqual(total**2,sum(t*t for t in terms))
        self.assertGreater((terms[0]/total)**2,.99)

    def test_cascode_output_resistance_from_node_kcl(self):
        gm=.04;ro=1e5;beta=200;rp=beta/gm
        # Apply 1 V at the upper collector; solve the shared emitter voltage.
        ve=(1/ro)/(2/ro+1/rp+gm)
        output_current=(1-ve)/ro-gm*ve
        self.assertAlmostEqual(1/output_current,m.cascode_r(),places=4)

    def test_old_design_fails_with_real_output_load(self):
        a1,a2,a3,total,rin=m.old_cascade()
        self.assertAlmostEqual(total,806.6915996,places=5)
        self.assertLess(a3,.8)
        self.assertLess(total,1000)
        self.assertGreater(m.old_cascade(load=1e9)[3],1000)

    def test_revised_bias_has_current_balance_and_headroom(self):
        for beta in [100,200,300]:
            d=m.design_dc(beta)
            vb1=d['ve1']+.65;vb2=d['ve2']+.65
            self.assertAlmostEqual((12-vb1)/1e6-vb1/130000,d['ic1']/beta)
            self.assertAlmostEqual((12-vb2)/60000-vb2/12000,d['ic2']/beta)
            self.assertAlmostEqual((12-d['vc2'])/2200,d['ic2']+d['ic3']/beta)
            self.assertGreater(d['vx']-d['ve1'],1)
            self.assertGreater(d['vc1']-d['vx'],5)
            self.assertGreater((d['ve3']-1)/470-.01,0)
            self.assertLess(d['ve3']+1,11)

    def test_ac_matches_low_frequency_hybrid_pi_kcl(self):
        for beta in [100,200,300]:
            d=m.design_dc(beta);v=m.design_ac(0,beta).real
            b,x,c,b3,e=v
            gm1=d['ic1']/m.VT;gmu=d['ic_upper']/m.VT
            gm2=d['ic2']/m.VT;gm3=d['ic3']/m.VT
            # Follower emitter and second collector equations independently.
            self.assertAlmostEqual(e/470+e/100+(e-b3)*gm3/beta+e*d['ic3']/100-gm3*(b3-e),0)
            self.assertAlmostEqual(b3/2200+b3*d['ic2']/100+gm2*c+(b3-e)*gm3/beta,0)
            self.assertAlmostEqual((b-1)/10000+b/m.parallel(1e6,130000)+b*gm1/beta,0)
            self.assertAlmostEqual(x*d['ic1']/100+gm1*b+(x-c)*d['ic_upper']/100+x*gmu/beta+gmu*x,0)

    def test_nominal_bandwidth_and_failed_beta_corner_are_visible(self):
        nominal=m.design_ac(0)
        self.assertGreater(abs(nominal[4]/nominal[0]),1000)
        self.assertLess(m.design_ac(0,test_output=True)[4].real,100)
        bw=m.design_bandwidth()
        self.assertGreater(bw,100000)
        self.assertAlmostEqual(abs(m.design_ac(bw)[4]/nominal[4]),1/math.sqrt(2))
        v=m.design_ac(0,100)[0].real
        self.assertLess(10000*v/(1-v),10000)

    def test_all_scene_curves_are_finite_and_print_has_four_frames(self):
        for key,s in scenes.SPECS.items():
            for stage in range(4):
                for fn,_,_ in scenes.functions(key,stage):
                    for x in np.linspace(*s['xlim'],81):
                        self.assertTrue(math.isfinite(fn(x)),(key,stage,x))
            tree=ET.fromstring(scenes.storyboard(key))
            self.assertEqual(len([e for e in tree.iter() if 'data-storyboard-beat' in e.attrib]),4)
            self.assertFalse(any(e.tag.endswith(('animate','animateMotion')) for e in tree.iter()))


if __name__=='__main__':unittest.main()
