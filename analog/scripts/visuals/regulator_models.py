"""Reference and regulator teaching models; SI units, explicit idealizations."""
import math

KT_Q=1.380649e-23/1.602176634e-19


def bandgap(temperature,n=8,vbe25=.65,slope=-.002):
    ptat=KT_Q*(temperature+273.15)*math.log(n)
    k=-slope/(KT_Q*math.log(n))
    ct=vbe25+slope*(temperature-25)
    return ct,k*ptat,ct+k*ptat


def shunt(supply,load,resistance=360,voltage=5.1):
    feed=(supply-voltage)/resistance
    current=feed-load
    return current,voltage*current,(supply-voltage)*feed


def tl431_output(top,bottom,reference=2.5,bias=2e-6):
    return reference*(1+top/bottom)+bias*top


def dropout(time,average=3.5,amplitude=.2,frequency=1000,target=3.3,current=.5,ron=.3):
    vin=average+amplitude*math.sin(2*math.pi*frequency*time)
    return vin,min(target,vin-current*ron)


def power(current,vin=12,vout=5,iq=.005):
    return (vin-vout)*current+vin*iq


def junction(current,theta=50,ambient=45):
    return ambient+theta*power(current)


def thermal_current(theta=50,ambient=45,limit=125):
    return ((limit-ambient)/theta-12*.005)/7


def efficiency(current,iq=.005,vin=5,vout=3.3):
    return vout*current/(vin*(current+iq))


def transient(time,delta=.49,capacitance=10e-6,esr=.05,delay=5e-6,tau=5e-6):
    """Returns capacitor error, capacitor current, output error.

    For t>=delay, capacitor error obeys e''+2e'/tau+e/tau²=0,
    with continuous voltage/current at the handoff. ESR uses actual capacitor current.
    """
    if time<0:return 0,0,0
    if time<delay:
        error=-delta*time/capacitance
        ic=-delta
    else:
        u=time-delay
        decay=math.exp(-u/tau)
        error=-delta/capacitance*(delay+(1+delay/tau)*u)*decay
        ic=-delta*(1-(1+delay/tau)*u/tau)*decay
    return error,ic,error+esr*ic


def transient_minimum_time(capacitance=10e-6,esr=.05,delay=5e-6,tau=5e-6):
    """Minimum output time for a positive step under this recovery model."""
    slope=(1+delay/tau)*(1-esr*capacitance/tau)
    if slope<=0:return delay
    return delay+max(0,tau-(delay+esr*capacitance)/slope)


def pulse_deficit(time,charge=1e-9,capacitance=1e-6,resistance=10,period=10e-6):
    if time<0:return 0
    # Include the pulse at t=0 and at each following period.
    count=int(math.floor(time/period+1e-10))+1
    remainder=max(0,time-(count-1)*period)
    ratio=math.exp(-period/(resistance*capacitance))
    return charge/capacitance*(-math.expm1(-count*period/(resistance*capacitance)))/(1-ratio)*math.exp(-remainder/(resistance*capacitance))


def pulse_steady(charge=1e-9,capacitance=1e-6,resistance=10,period=10e-6):
    peak=charge/capacitance/(-math.expm1(-period/(resistance*capacitance)))
    return peak,peak-charge/capacitance
