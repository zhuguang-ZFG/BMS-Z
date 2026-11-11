"""Explicit ideal models for chapter 13; SI units unless the name says otherwise."""
import math


def zener_current(vin, load, resistance=330, vz=5.6, beta=50):
    """Available zener current before breakdown regulation is lost."""
    return (vin-vz)/resistance-load/(beta+1)


def buck_ripple(vin=12, vout=5, inductance=22e-6, frequency=150e3):
    return (vin-vout)*(vout/vin)/(inductance*frequency)


def buck_current(phase, load=1):
    d=5/12
    ripple=buck_ripple()
    return load-ripple/2+ripple*(phase/d if phase<=d else (1-phase)/(1-d))


def buck_charge(phase):
    """Integral of capacitor current from phase 0, coulombs; ideal CCM."""
    d=5/12;di=buck_ripple();period=1/150e3
    if phase<=d:
        return period*di*(-phase/2+phase*phase/(2*d))
    u=phase-d
    return period*di*(u/2-u*u/(2*(1-d)))


def buck_dcm_ratio(load_resistance, duty=5/12, inductance=22e-6, frequency=150e3):
    """Fixed duty diode buck, ideal DC output, including its CCM boundary."""
    k=2*inductance*frequency/load_resistance
    return max(duty,2/(1+math.sqrt(1+4*k/duty**2)))


def boost_current(phase, vin=5, vout=12, inductance=47e-6, frequency=100e3, load=.2):
    d=1-vin/vout;di=vin*d/(inductance*frequency);avg=load/(1-d)
    return avg-di/2+di*(phase/d if phase<=d else (1-phase)/(1-d))


def wien(f_normalized):
    s=1j*f_normalized
    return s/(s*s+3*s+1)


def amplitude(time, growth=.8, saturation=1, initial=.02):
    """Slow amplitude model dA/dt=g A(1-A²/As²), not a lamp device model."""
    return saturation/math.sqrt(1+((saturation/initial)**2-1)*math.exp(-2*growth*time))


def compliance_current(load_resistance, supply=5, target=.001, sense=100, headroom=.7):
    """Piecewise ceiling model, not a transistor saturation characteristic."""
    return min(target,max(0,(supply-headroom)/(load_resistance+sense)))


def sar_trials(value=.63, bits=4):
    """Ideal unipolar binary search, normalized full scale, lower-bin code."""
    code=0;result=[]
    for bit in reversed(range(bits)):
        trial=code|(1<<bit)
        accepted=trial/2**bits<=value
        if accepted:code=trial
        result.append((trial/2**bits,accepted,code))
    return result


def quantize_nearest(value, levels=8):
    """Midtread rounding illustration, evaluated away from overload."""
    return math.floor(value*levels+.5)/levels


def jitter_snr(frequency, rms_jitter=10e-12):
    return -20*math.log10(2*math.pi*frequency*rms_jitter)


def acquisition_error(resistance, capacitance=20e-12, time=500e-9):
    return math.exp(-time/(resistance*capacitance))


def bridge_current(time, voltage=-12, initial=2, resistance=2, inductance=.01, back_emf=0):
    final=(voltage-back_emf)/resistance
    return final+(initial-final)*math.exp(-resistance*time/inductance)


def class_b_power(output_power, load=8, rail=15):
    peak_current=math.sqrt(2*output_power/load)
    dc=2*rail*peak_current/math.pi
    return dc,dc-output_power


def crystal_frequency(load_cap, series_frequency=32768, motional_cap=10e-15, shunt_cap=1.5e-12):
    """Lossless parallel load resonance, not complete oscillator phase pulling."""
    return series_frequency*math.sqrt(1+motional_cap/(shunt_cap+load_cap))


def crystal_pull_ppm(load_pf, reference_pf=12):
    return (crystal_frequency(load_pf*1e-12)/crystal_frequency(reference_pf*1e-12)-1)*1e6


def crystal_gm_critical(frequency, esr, shunt_cap, load_cap):
    return 4*esr*(2*math.pi*frequency)**2*(shunt_cap+load_cap)**2


def crystal_envelope(time, negative_resistance, esr=50e3, inductance=2400, initial=1e-6):
    """Linear series motional branch; time seconds, |Rneg| positive, no limiting."""
    return initial*math.exp((negative_resistance-esr)*time/(2*inductance))


def opto_available(input_resistance, ctr_ratio, vin=3.3, vf=1.2):
    """Available active-region current; does not guarantee saturation VOL."""
    return (vin-vf)/input_resistance*ctr_ratio
