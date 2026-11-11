"""Explicit teaching models, in SI units except documented plot coordinates."""
import math


def compensation(capacitance, gm=2*math.pi*30e-12*1e6, current=15e-6):
    return gm/(2*math.pi*capacitance), current/capacitance


def follower_error(resistance, offset=.003, bias=20e-9, signal=1, gain=1e5):
    """Signed model: positive offset; bias current flows into the + input."""
    return (offset-bias*resistance-signal/gain)/(1+1/gain)


def balanced_error(balance, minus=20e-9, plus=20e-9, rin=1e4, rf=9e4):
    return rf*minus-(1+rf/rin)*balance*plus


def closed_gain(frequency, noise_gain=100, gbw=.7e6):
    return noise_gain/math.hypot(1,frequency/(gbw/noise_gain))


def sine_slope(frequency, peak=5):
    return 2*math.pi*frequency*peak


def rejection_error(disturbance, db=40, noise_gain=1):
    return disturbance*10**(-db/20)*noise_gain


def noise_rms(cutoff, density=40e-9, first_order=True):
    return density*math.sqrt(cutoff*(math.pi/2 if first_order else 1))


def settling_handoff(step=1, pole=1e6, slew=.5e6):
    tau=1/(2*math.pi*pole)
    return max(0,(step-slew*tau)/slew), min(step,slew*tau), tau


def step_response(time, step=1, pole=1e6, slew=.5e6):
    handoff,error,tau=settling_handoff(step,pole,slew)
    time=max(0,time)
    return slew*time if time<handoff else step-error*math.exp(-(time-handoff)/tau)


def settling_time(tolerance=.001, step=1, pole=1e6, slew=.5e6):
    handoff,error,tau=settling_handoff(step,pole,slew)
    target=abs(step)*tolerance
    if target>=error:
        return max(0,(step-target)/slew)
    return handoff+tau*math.log(error/target)
