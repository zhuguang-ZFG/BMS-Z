"""Chapter 11 teaching models. SI units, explicitly bounded approximations."""
import math
import numpy as np

VT = .026
K = 1.380649e-23
Q = 1.602176634e-19


def parallel(*values):
    return 1 / sum(1 / v for v in values)


def differential(vd, tail=.001):
    d = math.tanh(vd / (2 * VT))
    return tail * (1 + d) / 2, tail * (1 - d) / 2


def cmrr(tail_r, delta=.01):
    gm = .0005 / VT
    ad_se = -gm * 10000 / 2
    ac_se = -10000 / (2 * tail_r + 1 / gm)
    ad_diff = gm * 10000
    ac_diff = 2 * delta * 10000 / (2 * tail_r + 1 / gm)
    return ad_se, ac_se, ad_diff, ac_diff


def mirror(beta, vout=.65, early=math.inf):
    ratio = (1 + vout / early) / (1 + .65 / early)
    # Reference source supplies IC1 + IB1 + IB2.
    return ratio / (1 + (1 + ratio) / beta)


def crossover(x, bias=0, vbe=.65):
    dead = max(0, vbe - bias / 2)
    return math.copysign(max(0, abs(x) - dead), x)


def damping(pm_degrees):
    p = math.radians(pm_degrees)
    # L(s)=wn²/[s(s+2*zeta*wn)], unity feedback.
    return math.sin(p) / (2 * math.sqrt(math.cos(p)))


def step(t, zeta):
    wd = math.sqrt(1 - zeta * zeta)
    return 1 - math.exp(-zeta * t) * (math.cos(wd * t) + zeta / wd * math.sin(wd * t))


def overshoot(pm):
    z = damping(pm)
    return math.exp(-math.pi * z / math.sqrt(1 - z * z))


def compensated(cc, r1=1e5, r2=1e5, c1=10e-12, c2=100e-12, gm2=.001):
    # Exact roots of a*s²+b*s+c for the unilateral two-node model.
    a = c1 * c2 + cc * (c1 + c2)
    b = c1 / r2 + c2 / r1 + cc * (1 / r1 + 1 / r2 + gm2)
    c = 1 / (r1 * r2)
    disc = math.sqrt(b * b - 4 * a * c)
    slow = 2 * c / (b + disc)
    fast = (b + disc) / (2 * a)
    return slow / (2 * math.pi), fast / (2 * math.pi)


def noise_density(f, corner=100, white=10e-9):
    return white * math.sqrt(1 + corner / f)


def noise_integral(low, high, corner=100, white=10e-9):
    if not 0 < low < high:
        raise ValueError('Positive, ordered integration limits are required')
    return white * math.sqrt(high - low + corner * math.log(high / low))


def noise_budget(rs=1e6, en=10e-9, inoise=1e-15, bandwidth=math.pi / 2 * 1e4):
    terms = [math.sqrt(4 * K * 300 * rs * bandwidth), en * math.sqrt(bandwidth), inoise * rs * math.sqrt(bandwidth)]
    return terms, math.sqrt(sum(t * t for t in terms))


def cascode_r(ro=1e5, gm=.04, beta=200):
    return ro + (1 + gm * ro) * parallel(ro, beta / gm)


def old_cascade(beta=200, load=100):
    gm1, gm2, gm3 = [.0004 / VT, .001 / VT, .001 / VT]
    rp1, rp2, rp3 = [beta / gm for gm in [gm1, gm2, gm3]]
    re = parallel(1000, load)
    rin3 = rp3 + (beta + 1) * re
    a1 = gm1 * parallel(5600, rp2, 250000)
    a2 = gm2 * parallel(680, 100000, rin3)
    a3 = (beta + 1) * re / rin3
    return a1, a2, a3, a1 * a2 * a3, parallel(rp1, 110000)


def design_dc(beta=200):
    """Nominal fixed-VBE bias model, AC coupling, upper cascode base at 2.5 V."""
    alpha = beta / (beta + 1)
    ic1 = (12 * 130000 / 1130000 - .65) / (1500 / alpha + parallel(1e6, 130000) / beta)
    ic2 = (2 - .65) / (1200 / alpha + 10000 / beta)
    ve3 = (12 - .65 - 2200 * ic2) / (1 + 2200 / (470 * (beta + 1)))
    ic3 = alpha * ve3 / 470
    return dict(beta=beta, ic1=ic1, ic_upper=alpha*ic1, ic2=ic2, ic3=ic3,
                ve1=ic1/alpha*1500, vx=1.85, vc1=12-alpha*ic1*12000,
                ve2=ic2/alpha*1200, vc2=ve3+.65, ve3=ve3)


def design_ac(frequency, beta=200, source=10000, test_output=False):
    """Six-node hybrid-pi model; coupling/bypass capacitors ideal in passband.

    Nodes: input, lower collector, first output/second base, second output/
    follower base, follower emitter, unused ground-free slot omitted. Each BJT
    has explicit rpi, ro, gm, Cpi=25 pF, Cmu=5 pF (illustrative, not a part spec).
    """
    dc = design_dc(beta)
    y = np.zeros((5, 5), dtype=complex)
    rhs = np.zeros(5, dtype=complex)
    s = 2j * math.pi * frequency

    def adm(a, b, value):
        if a >= 0: y[a, a] += value
        if b >= 0: y[b, b] += value
        if a >= 0 and b >= 0: y[a, b] -= value; y[b, a] -= value

    def bjt(base, collector, emitter, ic):
        gm = ic / VT
        adm(base, emitter, gm / beta + s * 25e-12)
        adm(base, collector, s * 5e-12)
        adm(collector, emitter, ic / 100)
        for row, sign in [(collector, 1), (emitter, -1)]:
            if row < 0: continue
            if base >= 0: y[row, base] += sign * gm
            if emitter >= 0: y[row, emitter] -= sign * gm

    for node, resistance in [(0, parallel(1e6, 130000)), (0, source), (2, 12000), (2, 10000), (3, 2200), (4, 470)]:
        adm(node, -1, 1 / resistance)
    if not test_output: adm(4, -1, 1 / 100)
    bjt(0, 1, -1, dc['ic1'])
    bjt(-1, 2, 1, dc['ic_upper'])
    bjt(2, 3, -1, dc['ic2'])
    bjt(3, -1, 4, dc['ic3'])
    rhs[4 if test_output else 0] = 1 if test_output else 1 / source
    return np.linalg.solve(y, rhs)


def design_bandwidth(beta=200):
    reference = abs(design_ac(0, beta)[4]) / math.sqrt(2)
    lo, hi = 0, 1e7
    for _ in range(50):
        mid = (lo + hi) / 2
        if abs(design_ac(mid, beta)[4]) > reference: lo = mid
        else: hi = mid
    return (lo + hi) / 2
