"""Chapter 10 timer equations; all nonideal values are prescribed teaching models."""
import math


def crossing(start, target, finish, tau):
    """Time for a first-order node to reach finish; unreachable returns infinity."""
    if start == finish:
        return 0.
    if not min(start, target) < finish < max(start, target):
        return math.inf
    return tau * math.log((start-target)/(finish-target))


def astable(ra=1000, rb=6800, c=100e-9, supply=9, control=None, floor=0):
    high = supply*2/3 if control is None else control
    low = high/2
    th = crossing(low, supply, high, (ra+rb)*c)
    tl = crossing(high, floor, low, rb*c)
    return th, tl


def cycle(t, ra=1000, rb=6800, c=100e-9, supply=9):
    th, tl = astable(ra, rb, c, supply)
    u = t % (th+tl)
    if u < th:
        return supply*(1-2/3*math.exp(-u/((ra+rb)*c))), 1
    return supply*2/3*math.exp(-(u-th)/(rb*c)), 0


def logic(reset, trigger, threshold, previous, supply=9):
    """RESET is already resolved to a Boolean enable; analog equality holds here only."""
    if not reset:
        return 0
    if trigger < supply/3:
        return 1
    if threshold > supply*2/3:
        return 0
    return previous


def first_charge(t, initial=0, ra=1000, rb=6800, c=100e-9, supply=9):
    return supply-(supply-initial)*math.exp(-t/((ra+rb)*c))


def diode_times(vf, r=10000, c=100e-9, supply=5):
    # Equal RA/RB, diode across RB, anode at pin 7. Require conduction to upper trip.
    upper, lower = supply*2/3, supply/3
    if supply-upper-vf < vf:
        raise ValueError('Diode stops conducting before the upper threshold')
    return crossing(lower,supply-vf,upper,r*c), crossing(upper,0,lower,r*c)


def output_feedback(voh, vol=.1, r=72000, c=10e-9, supply=5):
    upper,lower = supply*2/3,supply/3
    return crossing(lower,voh,upper,r*c),crossing(upper,vol,lower,r*c)


def monostable(leakage=0, resistance=560000, capacitance=47e-6,
               supply=9, initial=0, fraction=2/3):
    target=supply-leakage*resistance
    return crossing(initial,target,supply*fraction,resistance*capacitance)


def recovery(gap, resistance=100000, discharge=100, capacitance=10e-6, supply=5):
    # Charging resistor remains connected while pin 7 discharges C.
    if gap == 0:
        return supply*(2/3),0.
    final=supply*discharge/(resistance+discharge)
    tau=capacitance/(1/resistance+1/discharge)
    voltage=final+(supply*2/3-final)*math.exp(-gap/tau)
    duration=monostable(resistance=resistance,capacitance=capacitance,supply=supply,initial=voltage)
    return voltage,duration


def reset_ramp(t, resistance=100000, capacitance=4.7e-6, supply=12):
    return supply*(-math.expm1(-t/(resistance*capacitance)))


def discharge_current(vcap, ra=1000, rb=6800, supply=9, floor=.15):
    return (supply-floor)/ra, (vcap-floor)/rb


def tolerance_corners(rtol=.01, ctol=.05, low=.65, high=.68):
    nominal=math.log(3)
    return ((1-rtol)*(1-ctol)*(-math.log1p(-low))/nominal,
            (1+rtol)*(1+ctol)*(-math.log1p(-high))/nominal)
