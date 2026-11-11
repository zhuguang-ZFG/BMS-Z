"""Explicit linear teaching models for op-amp applications, in SI units.

No rail, slew-rate, vendor, or temperature guarantees are implied.
"""
import cmath
import math
import numpy as np


def difference_gains(r1, r2, r3, r4):
    """Vout=Ad*(V2-V1)+Ac*(V1+V2)/2; ideal amplifier."""
    k1, k2 = r2/r1, r4/r3
    positive = (1+k1)*k2/(1+k2)
    return (positive+k1)/2, positive-k1


def leaky(f, rin=1e4, rf=1e6, capacitance=1e-8):
    return -rf/rin/(1+2j*math.pi*f*rf*capacitance)


def differentiator(f, rin=1e3, rf=1e4, ci=1e-8, cf=1e-9):
    s = 2j*math.pi*f
    return -s*rf*ci/((1+s*rin*ci)*(1+s*rf*cf))


def sallen_key(r1, r2, c1, c2, gain=1):
    """C1: resistor junction to output; C2: noninverting input to ground."""
    root = math.sqrt(r1*r2*c1*c2)
    return 1/(2*math.pi*root), root/(c2*(r1+r2)+r1*c1*(1-gain))


def lowpass(ratio, q):
    return 1/(1-ratio**2+1j*ratio/q)


def f3_ratio(q):
    b = 1/q**2-2
    return math.sqrt((-b+math.sqrt(b*b+4))/2)


def second_step(t, q):
    z = 1/(2*q)
    if abs(z-1) < 1e-10:
        return 1-(1+t)*math.exp(-t)
    if z < 1:
        w = math.sqrt(1-z*z)
        return 1-math.exp(-z*t)*(math.cos(w*t)+z/w*math.sin(w*t))
    w = math.sqrt(z*z-1)
    return 1-math.exp(-z*t)*(math.cosh(w*t)+z/w*math.sinh(w*t))


def peak_hold(t, initial=1, capacitance=1e-7, resistance=1e7, leakage=1e-7):
    """Constant outward leakage plus a shunt resistor, while diode is off."""
    return (initial+leakage*resistance)*math.exp(-t/(resistance*capacitance))-leakage*resistance


def crossing(loop, lo=1, hi=1e9):
    """One downward unity crossing, bracket checked (not a Nyquist solver)."""
    if not (abs(loop(lo)) > 1 and abs(loop(hi)) < 1):
        raise ValueError('unity crossing is not bracketed')
    for _ in range(90):
        mid = math.sqrt(lo*hi)
        if abs(loop(mid)) > 1:
            lo = mid
        else:
            hi = mid
    f = math.sqrt(lo*hi)
    return f, 180+math.degrees(cmath.phase(loop(f)))


def capacitive_loop(f, isolation=0, feedback='A', a0=1e5, fp=10, ro=50, cl=1e-7):
    s = 2j*math.pi*f
    load = (1+s*isolation*cl if feedback=='A' else 1)/(1+s*(ro+isolation)*cl)
    return a0/(1+s/(2*math.pi*fp))*load


def rational_step(t, numerator, denominator):
    """Unit step from distinct stable quadratic poles using residues."""
    if t <= 0:
        return 0.0
    poles = np.roots(denominator)
    if any(p.real >= 0 for p in poles):
        raise ValueError('step model must have stable poles')
    derivative = np.polyder(denominator)
    value = complex(numerator[-1]/denominator[-1])
    for p in poles:
        value += np.polyval(numerator,p)/(p*np.polyval(derivative,p))*cmath.exp(p*t)
    return value.real


def capacitive_step(t, isolation=0, feedback='A', at='load'):
    a0, wp, cl, ro = 1e5, 2*math.pi*10, 1e-7, 50
    tau = (ro+isolation)*cl
    den = [tau/wp, 1/wp+tau+(a0*isolation*cl if feedback=='A' else 0), 1+a0]
    num = [a0*isolation*cl, a0] if at=='amp' else [a0]
    return rational_step(t,num,den)


def tia_ng(f, cf, rf=1e6, cin=1e-11):
    s = 2j*math.pi*f
    return (1+s*rf*(cin+cf))/(1+s*rf*cf)


def tia_loop(f, cf, rf=1e6, cin=1e-11, a0=1e5, fp=100):
    return a0/(1+1j*f/fp)/tia_ng(f,cf,rf,cin)


def tia_transimpedance(f, cf, rf=1e6, cin=1e-11, a0=1e5, fp=100):
    s = 2j*math.pi*f
    amp = a0/(1+s/(2*math.pi*fp))
    zf = rf/(1+s*rf*cf)
    return -amp*zf/(1+amp+s*cin*zf)


def tia_step(t, cf, rf=1e6, cin=1e-11):
    a0, wp = 1e5, 2*math.pi*100
    den = [rf*(cin+cf)/wp, 1/wp+rf*(cin+cf)+a0*rf*cf, 1+a0]
    return rational_step(t,[a0],den)


def triangle(t, rc=1e-4, period=1e-3, amplitude=1):
    phase = t % period
    return -amplitude/rc*(phase if phase <= period/2 else period-phase)


def source_noise(rs, en, inoise, temperature=300):
    return math.sqrt(4*1.380649e-23*temperature*rs+en*en+(inoise*rs)**2)


def settling_tau(bits, half_lsb=True):
    return (bits+int(half_lsb))*math.log(2)
