"""Independent conservation, boundary and dimensional checks for chapter 13."""
import math
import unittest
from scripts.visuals import power_signal_models as m


class PowerSignalModels(unittest.TestCase):
    def test_buck_voltage_seconds_and_charge(self):
        d=5/12;t=1/150e3
        self.assertAlmostEqual(7*d-5*(1-d),0)
        self.assertAlmostEqual(m.buck_current(d)-m.buck_current(0),7*d*t/22e-6)
        self.assertAlmostEqual(m.buck_charge(1),0)
        self.assertAlmostEqual(m.buck_charge((1+d)/2)-m.buck_charge(d/2),m.buck_ripple()*t/8)
        self.assertAlmostEqual((m.buck_charge((1+d)/2)-m.buck_charge(d/2))/100e-6, .007365319865319865)

    def test_dcm_from_peak_current_and_discharge_duration(self):
        for r in (12,50,100):
            ratio=m.buck_dcm_ratio(r);d=5/12
            peak=(12-12*ratio)*d/(22e-6*150e3)
            discharge=(1-ratio)*d/ratio
            self.assertLessEqual(d+discharge,1)
            self.assertAlmostEqual(.5*peak*(d+discharge),12*ratio/r)
        self.assertAlmostEqual(m.buck_dcm_ratio(5/m.buck_ripple()*2),5/12)
        self.assertAlmostEqual(m.buck_dcm_ratio(5),5/12)

    def test_zener_node_current_balance(self):
        load=.2;ib=load/51
        self.assertAlmostEqual(m.zener_current(9,load)+ib,(9-5.6)/330)
        self.assertLess(m.zener_current(7,.5),0)

    def test_boost_input_power_and_slopes(self):
        d=1-5/12
        avg=(m.boost_current(0)+m.boost_current(d))/2
        self.assertAlmostEqual(5*avg,12*.2)
        self.assertAlmostEqual((m.boost_current(d)-m.boost_current(0))/(d/1e5),5/47e-6)

    def test_wien_and_amplitude_boundaries(self):
        self.assertAlmostEqual(m.wien(1).real,1/3)
        self.assertAlmostEqual(m.wien(1).imag,0)
        self.assertAlmostEqual(m.wien(.1).real,m.wien(10).real)
        self.assertAlmostEqual(m.wien(.1).imag,-m.wien(10).imag)
        self.assertAlmostEqual(m.amplitude(0),.02)
        self.assertLess(m.amplitude(20),1)
        self.assertGreater(m.amplitude(20),.999)

    def test_sar_binary_search_all_bins(self):
        for code in range(16):
            rows=m.sar_trials((code+.25)/16)
            self.assertEqual(rows[-1][2],code)
        self.assertEqual([r[:2] for r in m.sar_trials()],[(.5,True),(.75,False),(.625,True),(.6875,False)])

    def test_jitter_and_half_lsb(self):
        self.assertAlmostEqual(m.jitter_snr(1e6),84.0364026328377)
        self.assertAlmostEqual(m.jitter_snr(1e6)-m.jitter_snr(1e7),20)
        resistance=500e-9/(20e-12*13*math.log(2))
        self.assertAlmostEqual(resistance,2774.4135401710834)
        self.assertAlmostEqual(m.acquisition_error(resistance),1/8192)

    def test_bridge_current_continuity_and_energy(self):
        self.assertEqual(m.bridge_current(0),2)
        self.assertAlmostEqual(m.bridge_current(.005*math.log(4/3)),0)
        self.assertGreater(m.bridge_current(.001),0)
        # v*i = d(1/2 L i²)/dt + R i², with zero back EMF.
        t=.002;dt=1e-8;i=m.bridge_current(t)
        derivative=(m.bridge_current(t+dt)-m.bridge_current(t-dt))/(2*dt)
        self.assertAlmostEqual(-12*i,.01*i*derivative+2*i*i,places=6)

    def test_class_b_full_swing_limit(self):
        p=15**2/(2*8);dc,heat=m.class_b_power(p)
        self.assertAlmostEqual(p/dc,math.pi/4)
        self.assertAlmostEqual(dc,heat+p)
        self.assertAlmostEqual(m.class_b_power(10)[1],5.09876363134611)

    def test_crystal_load_equivalent_and_frequency_direction(self):
        cl=22*22/(22+22)+4
        self.assertEqual(cl,15)
        ppm=m.crystal_pull_ppm(cl)
        self.assertGreater(ppm,-68)
        self.assertLess(ppm,-67)
        # At the lossless parallel resonance, motional and shunt susceptances cancel.
        cm=10e-15;c0=1.5e-12;fs=32768;lm=1/((2*math.pi*fs)**2*cm)
        w=2*math.pi*m.crystal_frequency(15e-12)
        self.assertAlmostEqual(w*(c0+15e-12)-1/(w*lm-1/(w*cm)),0,places=12)
        self.assertAlmostEqual(m.crystal_gm_critical(8e6,80,3e-12,15e-12)*1000,.26195982958206576)

    def test_crystal_startup_uses_net_negative_resistance(self):
        self.assertEqual(m.crystal_envelope(1,50e3),1e-6)
        self.assertLess(m.crystal_envelope(.1,25e3),1e-6)
        self.assertGreater(m.crystal_envelope(.1,100e3),1e-6)

    def test_opto_current_headroom_and_compliance(self):
        needed=(3.3-.3)/4700
        self.assertGreater(m.opto_available(1000,.5),needed)
        self.assertLess(m.opto_available(1000,.25),needed)
        self.assertGreater(m.opto_available(470,.25),needed)
        for supply,ceiling in [(2.8,2000),(5,4200),(12,11200)]:
            self.assertAlmostEqual(m.compliance_current(ceiling,supply),.001)
            self.assertLess(m.compliance_current(ceiling+100,supply),.001)


if __name__=='__main__':unittest.main()
