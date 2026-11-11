"""Explicit comparator state and RC models; SI units throughout."""
import math


def release_voltage(time,resistance=4700,capacitance=50e-12,supply=5,release=1e-6):
    return 0 if time<release else supply*(-math.expm1(-(time-release)/(resistance*capacitance)))


def release_crossing(voltage,resistance=4700,capacitance=50e-12,supply=5,release=1e-6):
    return release-resistance*capacitance*math.log1p(-voltage/supply)


def divider(top,bottom,supply=5):
    return supply*bottom/(top+bottom)


def opposing_error(fraction):
    return divider(1e5*(1-fraction),1e5*(1+fraction))-2.5


def window_state(battery,low=3,high=3.6):
    """None at equality: no deterministic state asserted at the threshold."""
    if battery in (low,high):
        return None
    undervoltage=battery/2<low/2  # sensed + input is below reference - input
    overvoltage=high/2<battery/2  # reference + input is below sensed - input
    return undervoltage,overvoltage,not(undervoltage or overvoltage)


def inverting_threshold(output,reference=2.5,rref=1e4,rfeedback=1e5):
    return (rfeedback*reference+rref*output)/(rref+rfeedback)


def noninverting_threshold(output,reference=2.5,rin=1e4,rfeedback=1e5):
    return reference*(1+rin/rfeedback)-output*rin/rfeedback


def loaded_thresholds(pullup,supply=5,reference=2.5,rref=1e4,rfeedback=1e5,low=.2):
    voh=(supply/pullup+reference/(rref+rfeedback))/(1/pullup+1/(rref+rfeedback))
    return voh,inverting_threshold(voh,reference,rref,rfeedback),inverting_threshold(low,reference,rref,rfeedback)


def oscillator_period(tau=10e-6,delay=1.3e-6):
    # Thresholds are 1/4 and 3/4 of ideal output rails. Capacitor continues during delay.
    return 2*(delay+tau*math.log(4-math.exp(-delay/tau)))


def oscillator_voltage(time,tau=10e-6,delay=1.3e-6):
    half=oscillator_period(tau,delay)/2
    vmin=.25*math.exp(-delay/tau)
    phase=max(0,time)%(2*half)
    return (1-(1-vmin)*math.exp(-phase/tau)) if phase<half else ((1-vmin)*math.exp(-(phase-half)/tau))


def disturbance(time_ms):
    baseline=2.4 if time_ms<=10 else max(2.2,2.4-.2*(time_ms-10))
    return baseline+sum(a*max(0,1-abs(time_ms-t)/.4) for t,a in [(2,.2),(5,.3),(8,.4)])


def hysteresis_trace(samples,upper=30/11,lower=25/11,initial_high=True):
    high=initial_high
    states=[]
    for value in samples:
        if high and value>upper: high=False
        elif not high and value<lower: high=True
        states.append(high)
    return states


def ramp_crossing(threshold,start=2.3,slope=.001):
    return (threshold-start)/slope
