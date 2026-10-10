"""单粒子模型（SPM）里的固相扩散：一条闭式级数与一台隐式有限体积互相钉。

对应教程：阶段 4 §4.4 说「一阶 RC 只有一条支路，前段怎么调参都拟合不上；二阶 RC
用快、慢两条支路各管一段才能贴合」，又说更慢那一路是「锂离子在电极内部的扩散」。
那两句是**断言**。本脚本把它算出来：把活性颗粒当成半径 R 的球、表面加恒定摩尔通量
J，端部浓度响应有闭式级数解，于是「一阶差多少、二阶差多少、要几阶才够」逐个数得清。
共学 09 那颗真值电芯只有 R0 + 一个 RC，缺的正是这一段。

全部无量纲——这是本脚本最重要的一条纪律：
    ξ = r/R      t* = D·t/R²      u = (c − c₀)·D/(J·R)
R、D、J 在方程里全部消掉，只剩 ∂u/∂t* = ∇²_ξ u，边界 ∂u/∂ξ|₁ = 1，初值 u(·,0) = 0。
要还原成秒只需 τ_d = R²/D（末尾给 5 µm / 1e-14 m²/s 那一档的量级）。

四条解析锚点，一条都不靠拟合：
  1) ⟨u⟩ = 3t*            有限体积望远镜求和的恒等式，不是近似（脚本里验到 1e-12）
  2) u_s − ⟨u⟩ → 1/5      定常态形状 u = ξ²/2 − 3/10，于是中心−均值 → −3/10
  3) 谱 = tan x = x 的正根  球 + 表面零通量的本征值；τ*₁ = 1/x₁² = 0.04953。
     常见错误是写成 1/π²——那是「平板」的数，会把弛豫时间说成 2.05 倍。
  4) S(t*) = Σₖ (2/xₖ²)(1 − e^{−xₖ²t*})   表面−均值的闭式级数。特征函数是球坐下的
     φₖ = sin(xₖξ)/ξ（中心正则，φₖ'(1)=0 展开就是 tan x = x）。权重全靠三条闭式积分：
     模长 ∫₀¹ξ²φₖ²dξ = xₖ²/(2(1+xₖ²))，投影 ∫₀¹ξ(ξ²/2−3/10)sin(xₖξ)dξ = cos xₖ/xₖ，
     两相除得 Bₖ，再乘 φₖ(1) = sin xₖ、用 sin xₖ = xₖcos xₖ 与 cos²xₖ = 1/(1+xₖ²) 化简
     就是 2/xₖ²。第三条更要紧：⟨φₖ⟩ = 3∫₀¹ξ sin(xₖξ)dξ = 3(sin xₖ − xₖcos xₖ)/xₖ² = 0
     ——**每个衰减模态都不搬动总锂**，均值只能跟着外加通量走。所以停流之后能掉的只有
     「表面−均值」（[7] 节），Σₖ 2/xₖ² = 1/5 也就只是锚点 2 的另一种写法。

最想让你记住的一条来自对锚点 4 逐项求导：
    S'(t*) = Σₖ 2 e^{−xₖ²t*}   ——权重正好抵消，t*→0 时发散，于是 S ~ 2√(t*/π)
任何有限个 RC 并联的阶跃响应，原点斜率都是**有限**值（Σg/τ）。所以「一阶拟合不上
前段」不是参数没调好，是结构上不可能：扩散的起点是 √t，不是一次方。

最后一节顺带纠正本仓库自己的一句话说法：eis-nyquist.svg 标着「尾巴斜率约 0.94」。
那个 0.94 既不是元件值、也不是理想 Warburg 的 45°，而是**你扫到多低**的读数——
同一条 Randles 曲线，尾巴只画一个十倍频程时割线斜率是 0.78，往下多扫 10 倍就变
0.94，多扫 1000 倍是 0.994。所以「斜率不到 1」不能当常相位元件（CPE）的证据：
真 α≠0.5 的签名是斜率**封顶**在 tan(απ/2)、再宽也回不到 1。判据只有一条。

运行：cd code/soc && python3 spm_demo.py
退出码 0 = 全部锚点在容差内；1 = 有锚点超差（打印超差项）。约 50 秒（隐式 marching 占大头）。
"""
from __future__ import annotations

import sys

import numpy as np

# ---- 把 t* 换成秒用的量级（文献常见范围，只为给个尺子，不是某颗电芯的规格）------
R_M = 5e-6          # 活性颗粒半径 5 µm：18650 里石墨/NMC 一次颗粒的典型档
D_M2S = 1e-14       # 固相扩散系数 m²/s：石墨 1e-14~1e-13，正极 1e-15~1e-14
TAU_D = R_M * R_M / D_M2S          # = 2500 s ≈ 42 min，整个颗粒换一遍血的时间

# 级数截断的误差不是「t* 越小要越多模态」这么简单：切在第 K 项，漏掉的是
# Σ_{k>K}2/x_k² ≈ 2/(π²K)，与 t* 几乎无关。要 0.1% 就得 2 万个模态——好在模态是
# 一次向量化求根 + 一次 outer，20 万个也就半秒。[1] 节把「预测的截断误差」与
# 「实测的截断误差」并排打出来，不让它当一个隐藏常数——[3] 节差点被它骗过去：
# 2 万项时参考值自己带 1.0e-5 的尾，把有限体积的二阶收敛信号整个盖掉了。
N_MODES = 200_000
N_GRID = 400        # 有限体积格数（[3] 节还会跑 100/200/400 看收敛率）
DT_STAR = 2e-3      # 长跑（t*=8、20）的步长：隐式不挑步长，慢模态 x₁²dt*=0.04 足够分辨
DT_STUDY = 5e-5     # 网格收敛研究专用：粗到能跑、细到时间误差压到空间误差的 1/10 以下


def tan_roots(n: int) -> np.ndarray:
    """tan x = x 的前 n 个正根，向每个区间里并行二分。

    区间必须停在 (mπ, mπ+π/2)：跨过 π/2 那个极点，二分会收敛到渐近线上的一堆假根。
    f(x)=tan x−x 在区间内单调（f'=tan²x≥0），所以 lo/hi 可以整片数组一起推。
    第一个非零根 x₁ = 4.4934094579…，常被误当成 π（3.1416）。
    """
    m = np.arange(1, n + 1, dtype=float)
    lo, hi = m * np.pi + 1e-6, m * np.pi + np.pi / 2 - 1e-6
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        neg = np.tan(mid) - mid < 0.0
        lo = np.where(neg, mid, lo)
        hi = np.where(neg, hi, mid)
    return 0.5 * (lo + hi)


XS = tan_roots(N_MODES)
X2 = XS * XS
W = 2.0 / X2                      # 闭式权重；ΣW = 1/5 就是「表面−均值」的定常态


def surface_rise(tstar: float | np.ndarray):
    """定流充电下 u_s − ⟨u⟩ 的精确值（截到 N_MODES 项）。单位 JR/D。"""
    t = np.atleast_1d(np.asarray(tstar, dtype=float))
    out = np.sum(W * (1.0 - np.exp(-np.outer(t, X2))), axis=1)
    return float(out[0]) if np.ndim(tstar) == 0 else out


def surface_slope(tstar: float) -> float:
    """S 对 t* 的导数：逐项求导后权重抵消，只剩 Σ2e^{−x²t*}。"""
    return float(np.sum(2.0 * np.exp(-X2 * tstar)))


def sphere_operator(n: int, surface_grad: float | None):
    """球坐标有限体积算子，用**精确**格体积（不是 rc²·dξ 那种近似）。

    dξ = 1/n，格心 ξᵢ = (i+½)dξ，面面积 Âⱼ = ξⱼ²（4π 约掉），
    体积 V̂ᵢ = ((i+1)³ − i³)dξ³/3。最内面 Â₀ = 0 —— 中心正则性自动满足，
    不需要给 r=0 单写边界条件。surface_grad=None 就是两面都零通量（停流弛豫）。
    """
    d = 1.0 / n
    af = (np.arange(n + 1) * d) ** 2
    vol = np.diff((np.arange(n + 1) * d) ** 3) / 3.0
    dg = -(af[:-1] + af[1:]) / (d * vol)
    up = af[1:n] / (d * vol[: n - 1])                 # 行 i 里 u_{i+1} 的系数
    lo = af[1:n] / (d * vol[1:])                      # 行 i+1 里 u_i 的系数
    # 表面那一面永远是**通量面**（给定的，可能是 0），不连幽灵格：所以末格对角里
    # 不能有 Â_N·u_{N−1} 这一项。上一版把 Â_N 留在对角上，等于凭空加了个漏项，
    # 停流弛豫直接奔 −∞（首项误差 −100%）。
    dg[-1] = -af[-2] / (d * vol[-1])
    src = np.zeros(n)
    if surface_grad is not None:
        src[-1] = af[-1] * surface_grad / vol[-1]     # 换成 prescribed gradient
    return dg, up, lo, src, vol


def thomas_factor(dd: np.ndarray, uu: np.ndarray, ll: np.ndarray):
    """把三对角矩阵的前向消元系数与主元倒数提出来，返回 (乘数, 下次对角, 主元倒数)。

    每一步的矩阵都一模一样，所以分解不该放在步循环里——上一版每步重算前向消元，白花一倍工。
    uu[i] = A[i,i+1]（末元素 0），ll[i] = A[i,i-1]（首元素 0）。

    这里差一点写错成「前向消元也带除法」：把 x 在前向就除以主元，乘数就得退回原始 a_i；
    两者混用会有 ~1e-5 的相对误差，单步看不出，2000 步之后硬模态把它放大到 1e140。
    下面按「前向不归一化、回代才除」的写法，和对拍 numpy 稠密解差 2e-16。
    """
    n = dd.size
    lm = np.zeros(n)
    inv_b = np.empty(n)
    inv_b[0] = 1.0 / dd[0]
    for i in range(1, n):
        lm[i] = ll[i] * inv_b[i - 1]
        inv_b[i] = 1.0 / (dd[i] - lm[i] * uu[i - 1])      # 注意是 uu[i-1] = A[i-1,i]
    return lm, uu, inv_b


class Diffuser:
    """隐式 Crank–Nicolson 推进器。

    显式格式在这里要求 dt* ≲ dξ²/2（N=400 时是 3e-7），跑不到 t*=8；隐式不挑步长，
    所以下面敢用 2e-3。上一版就是因为把「dt 放大」当成「少跑几步」而直接炸到 1e69。

    advance 接受 (n,) 或 (m, n)：一行一个时刻/一组参数，逐行独立（线性格式），
    这样「三个时刻的误差」只走一遍步循环，而不是三遍。
    """

    def __init__(self, n: int, dt: float, surface_grad: float | None, theta: float = 0.5):
        dg, up, lo, src, vol = sphere_operator(n, surface_grad)
        self.src, self.dt, self.vol, self.n = src, dt, vol, n
        self.band = 1.0 + dt * (1.0 - theta) * dg
        self.bu = dt * (1.0 - theta) * up
        self.bl = dt * (1.0 - theta) * lo
        dd = 1.0 - theta * dt * dg
        uu = np.zeros(n)
        uu[: n - 1] = -theta * dt * up                    # uu[i] = A[i, i+1]，末行无上邻
        ll = np.zeros(n)
        ll[1:] = -theta * dt * lo                         # ll[i] = A[i, i-1]，首行无下邻
        self.lu = thomas_factor(dd, uu, ll)

    def advance(self, u: np.ndarray, secs: int) -> np.ndarray:
        lm, uu, inv_b = self.lu
        for _ in range(secs):
            rhs = self.band * u + self.dt * self.src
            rhs[..., :-1] += self.bu * u[..., 1:]
            rhs[..., 1:] += self.bl * u[..., :-1]
            u = rhs
            for i in range(1, self.n):
                u[..., i] -= lm[i] * u[..., i - 1]
            u[..., self.n - 1] *= inv_b[self.n - 1]
            for i in range(self.n - 2, -1, -1):
                u[..., i] = (u[..., i] - uu[i] * u[..., i + 1]) * inv_b[i]
        return u

    @staticmethod
    def mean(u: np.ndarray, vol: np.ndarray) -> float:
        return float(np.dot(u, vol) / vol.sum())


def march(n: int, tstar: float, flux: float | None = 1.0, dt: float = DT_STAR):
    """从均匀初值推进到**恰好** tstar：步数取整后回头修 dt，不 overshoot。"""
    steps = max(1, int(round(tstar / dt)))
    m = Diffuser(n, tstar / steps, flux)
    return m.advance(np.zeros(n), steps), m.vol, m.dt


def march_marks(n: int, marks: tuple[float, ...], dt: float, flux: float | None = 1.0):
    """一次推进、多个时刻同时取「表面−均值」：一行一个时刻，共用同一遍步循环。

    marks 必须都是 dt 的整数倍，否则共用的步网格会把时刻读歪——这条不是防呆，是
    上一版 overshoot 小时刻留下的疤。
    """
    steps = [int(round(w / dt)) for w in marks]
    for s, w in zip(steps, marks, strict=True):
        if abs(s * dt - w) > 1e-9 * w:
            raise ValueError(f"t*={w} 不是 dt={dt} 的整数倍（{s} 步差 {abs(s * dt - w):.1e}）")
    m = Diffuser(n, dt, flux)
    u = np.zeros((len(marks), n))
    out, done = {}, 0
    for i in sorted(range(len(marks)), key=lambda k: steps[k]):
        u = m.advance(u, steps[i] - done)
        done = steps[i]
        row = u[i]
        out[marks[i]] = surface_of(row, n, flux) - float(np.dot(row, m.vol) / m.vol.sum())
    return out


def surface_of(u: np.ndarray, n: int, flux: float | None) -> float:
    """把格心读数换算到边界面上。

    有限体积存的是**格心**（最后一格在 ξ=1−dξ/2），不是边界。定通量面那一面的
    ∂u/∂ξ 恰好等于 imposed flux，所以面值 = 格心 + (dξ/2)·flux；零通量时不用补。
    少了这一步，表面−均值会系统性低 (dξ/2)，N=200 时是 2.5e-3——比格式本身的
    误差大两个数量级，看起来像解析解错了，其实是读错位置。
    """
    return float(u[-1] + (0.5 / n) * (flux if flux is not None else 0.0))


def integral(y: np.ndarray, h: float) -> float:
    """等距梯形积分。不叫 np.trapz：numpy 2 把它改名成 trapezoid，仓库要 1.24~2.x 通吃。"""
    return float(h * (y.sum() - 0.5 * (y[0] + y[-1])))


def check(name: str, ok: bool, detail: str) -> dict:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}　{detail}")
    return {name: ok}


def trunc_surface(n: int, tstar: float | np.ndarray):
    """只留前 n 个模态时 t* 处的表面−均值——这就是「n 阶 RC」的曲线。"""
    t = np.atleast_1d(np.asarray(tstar, dtype=float))
    out = np.sum(W[:n] * (1.0 - np.exp(-np.outer(t, X2[:n]))), axis=1)
    return float(out[0]) if np.ndim(tstar) == 0 else out


# —— 奈奎斯特那一节的元件值：照抄 docs/circuits/assets/eis-nyquist.svg 的注释行 ——
EIS_R0, EIS_RCT, EIS_CDL, EIS_SIGMA = 20e-3, 40e-3, 0.80, 0.006


def randles(f: float, alpha: float = 0.5) -> complex:
    """Randles 单元的阻抗，扩散支路写成 (jω)^−α。

    α=0.5 时 A( jω)^−1/2 = A(1−i)/(√2·√ω)，取 A=σ√2 就**精确**回到图上那行
    Zw=σ(1−i)/√ω。绕这一圈是为了让 α 成为唯一的自由参数：[8] 要问的是「斜率
    不到 1」到底来自 α（真分布时间常数）还是来自测量窗，两种解释必须能同框对比。
    """
    w = 2 * np.pi * f
    zw = EIS_SIGMA * np.sqrt(2.0) * (1j * w) ** (-alpha)
    return EIS_R0 + 1.0 / (1.0 / (EIS_RCT + zw) + 1j * w * EIS_CDL)


def tail_slope(f_a: float, f_b: float, alpha: float = 0.5) -> float:
    """奈奎斯特图上两点间的割线斜率 Δ(−Im)/ΔRe。用差值而不是绝对高度：
    R0+Rct 那段实轴偏移在差里自己消掉，所以这个数与「原点取在哪」无关。"""
    za, zb = randles(f_a, alpha), randles(f_b, alpha)
    return float((-zb.imag + za.imag) / (zb.real - za.real))


def find_freq_by_re(target_ohm: float) -> float:
    """按实部反查频率（低频支路单调，二分即可）：用来验证图上那个坐标确实是这条公式画的。"""
    lo, hi = 1e-6, 1e4
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if randles(mid).real * 1e3 > target_ohm:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main() -> int:
    print(f"球扩散（SPM 缺的那一中段）：{N_MODES} 个模态的闭式级数 vs {N_GRID} 格隐式有限体积")
    print(f"无量纲变量 ξ=r/R、t*=Dt/R²、u=(c−c₀)D/(JR)；"
          f"R={R_M*1e6:.0f} µm、D={D_M2S:.0e} m²/s → τ_d=R²/D={TAU_D:.0f} s={TAU_D/60:.1f} min")
    checks: dict[str, bool] = {}

    # —— 1) 谱与权重 ——
    print("\n[1] 谱：tan x = x 的正根，不是 π")
    print(f"    前 5 根 {np.round(XS[:5], 4)}（π=3.1416、2π=6.2832 都不是根）")
    print(f"    τ*₁ = 1/x₁² = {1 / X2[0]:.5f}；错用 1/π² = {1 / np.pi ** 2:.5f} "
          f"→ 把弛豫时间说成 {X2[0] / np.pi ** 2:.2f} 倍")
    checks.update(check("x₁ = 4.4934（不是 π）", abs(XS[0] - 4.4934094579) < 1e-6, f"x₁={XS[0]:.10f}"))
    tail = 2.0 / (np.pi ** 2 * (N_MODES + 0.5))      # Σ_{k>N}2/x_k² 的积分上界
    print(f"    ΣWₖ（{N_MODES} 项）= {W.sum():.6f}，加上界 {tail:.6f} → {W.sum() + tail:.6f}"
          f"（应 = 1/5 = 0.200000）")
    checks.update(check("Σ 2/xₖ² = 1/5", abs(W.sum() + tail - 0.2) < 2e-4, f"残差 {W.sum() + tail - 0.2:+.2e}"))
    print("    权重不是抄来的：特征函数 φₖ=sin(xₖξ)/ξ，三条积分各自积出来对闭式（20 万点梯形）")
    xi = np.linspace(0.0, 1.0, 200_001)
    step = xi[1] - xi[0]
    dev = xi ** 2 / 2 - 0.3                      # 定常态形状（已经减过均值）
    worst = {"norm": 0.0, "proj": 0.0, "mean": 0.0, "weight": 0.0}
    for k in (0, 1, 2, 5, 20, 99):
        x = XS[k]
        s = np.sin(x * xi)                       # ξ²φ² = sin²，处处不带 1/ξ
        norm = integral(s * s, step)             # = ∫ξ²φ²
        proj = integral(xi * dev * s, step)      # = ⟨v, φ⟩（权重 ξ² 吸收掉一个 ξ）
        mean = 3.0 * integral(xi * s, step)      # = ⟨φ⟩
        weight = proj / norm * np.sin(x)         # = Aₖ·sin(xₖ)，应当就是 2/xₖ²
        worst["norm"] = max(worst["norm"], abs(norm / (x * x / (2 * (1 + x * x))) - 1))
        worst["proj"] = max(worst["proj"], abs(proj / (np.cos(x) / x) - 1))
        worst["mean"] = max(worst["mean"], abs(mean))
        worst["weight"] = max(worst["weight"], abs(weight / W[k] - 1))
        if k < 3:
            print(f"      k={k + 1}: 模长 {norm:.9f} vs {x * x / (2 * (1 + x * x)):.9f}　"
                  f"投影 {proj:+.8f} vs {np.cos(x) / x:+.8f}　⟨φ⟩={mean:+.1e}　"
                  f"权重 {weight:.8f} vs {W[k]:.8f}")
    print("      六个模态（k=1,2,3,6,21,100）最大偏差："
          + " ".join(f"{lab} {worst[key]:.1e}" for key, lab in
                     (("norm", "模长"), ("proj", "投影"), ("mean", "均值"), ("weight", "权重"))))
    print("      ⟨φₖ⟩=0 这条不是凑数：它说的是每个衰减模态都不搬动总锂，"
          "所以停流后能掉的只有表面−均值——[7] 节测的正是这个差")
    checks.update(check("权重 2/xₖ² 由三条闭式积分独立复现",
                        worst["norm"] < 1e-6 and worst["proj"] < 1e-6
                        and worst["mean"] < 1e-10 and worst["weight"] < 1e-6,
                        f"模长 {worst['norm']:.1e} 投影 {worst['proj']:.1e} "
                        f"均值 {worst['mean']:.1e} 权重 {worst['weight']:.1e}"))
    print("    截断误差可预测：切在第 K 项就漏 2/(π²K)（与 t* 几乎无关），实测对账")
    worst = 0.0
    for k in (200, 1000, 5000):
        got = trunc_surface(k, 1e-4)
        pred = 2.0 / (np.pi ** 2 * k)
        meas = surface_rise(1e-4) - got
        worst = max(worst, abs(meas / pred - 1))
        print(f"      K={k:5d}  S={got:.7f}  预测漏 {pred:.2e}  实测漏 {meas:.2e} "
              f"→ 比值 {meas / pred:.3f}")
    checks.update(check("截断误差 = 2/(π²K)", worst < 0.06, f"预测与实测最大偏 {100 * worst:.1f}%"))

    # —— 2) 望远镜恒等式：定流的总锂上升率恰为 3 ——
    print("\n[2] 恒等式 d⟨u⟩/dt* = 3（不靠跑，靠在算子上做望远镜求和）")
    for n in (20, N_GRID):
        dg, up, lo, src, vol = sphere_operator(n, 1.0)
        probe = np.linspace(0.1, 1.0, n)
        L = np.diag(dg) + np.diag(up, 1) + np.diag(lo, -1)
        net = float(np.dot(vol, L @ probe + src))
        print(f"    N={n:4d}  ΣV̂(Lu+src)/ΣV̂ = {net / vol.sum():.12f}（应 3.000000000000）"
              f"  ΣV̂ = {vol.sum():.10f}（应 0.3333333333）")
        if n == N_GRID:
            checks.update(check("d⟨u⟩/dt* 恰为 3", abs(net / vol.sum() - 3.0) < 1e-10,
                                f"{net / vol.sum():.12f}"))

    # —— 3) 数值 vs 级数：网格收敛 ——
    print("\n[3] 隐式有限体积 vs 闭式级数：误差应按 1/N² 收（二阶格式）")
    marks = (5e-3, 2e-2, 1e-1)
    ref = {w: surface_rise(w) for w in marks}
    print("    先在网格最细处把 dt 砍一半，确认时间误差不参与——隐式管稳定性不管精度：\n"
          "    CN 对没分辨出的硬模态给出 g→−1（振动而非衰减），而 |λ_max| ~ 4/dξ² 随 N² 涨，\n"
          "    所以 dt 只能在最细的网格上重查；粗网格上「看着还行」不算数。")
    ladder = {}
    for d in (DT_STUDY, DT_STUDY / 2):
        got = march_marks(400, marks, dt=d)
        ladder[d] = max(abs(got[w] - ref[w]) for w in marks)
    trap = march_marks(400, marks, dt=2e-4)
    print("      dt = " + " / ".join(f"{d:.2e}" for d in ladder) + " → 最大误差 "
          + " / ".join(f"{e:.2e}" for e in ladder.values())
          + f"（{max(ladder.values()) / min(ladder.values()):.3f}×，不动）")
    print(f"      但 dt=2e-4 在同一网格上是 {abs(trap[5e-3] - ref[5e-3]):.2e}——比 N=100 的"
          f"全部误差还大，看着像格式在退化。上一版量到「N=200→400 只有 0.3×」就是踩在这上面。")
    checks.update(check("dt 不是误差来源（最细网格上最大/最小 <1.15）",
                        max(ladder.values()) / min(ladder.values()) < 1.15,
                        f"{max(ladder.values()) / min(ladder.values()):.3f}×"))
    prev = None
    for n in (100, 200, 400):
        got = march_marks(n, marks, dt=DT_STUDY)
        errs = [abs(got[w] - ref[w]) for w in marks]
        ratio = f"  收敛 {prev[0] / max(errs):.1f}×（理论 4×）" if prev else ""
        print(f"    N={n:4d}  最大差 {max(errs):.2e}{ratio}   逐点 "
              + " ".join(f"{e:.1e}" for e in errs))
        if prev:
            checks.update(check(f"N={prev[1]}→{n} 二阶收敛",
                                2.5 < prev[0] / max(errs) < 6.5, f"{prev[0] / max(errs):.2f}×"))
        prev = (max(errs), n)
    print(f"    这张表有自己的下限：级数截到 {N_MODES} 项，参考值自带 2/(π²K)={tail:.1e} 的尾。"
          f"N=400 的 {prev[0]:.1e} 只比它高一个数量级——再往细一格量的就不是格式误差了。")

    # —— 4) 定常态形状：1/5 与 −3/10 ——
    print("\n[4] 定常态形状 u = ξ²/2 − 3/10（t*=8 ≈ 162 个 τ*₁，形状早该收敛）")
    u, vol, _ = march(200, 8.0)
    cbar = Diffuser.mean(u, vol)
    surf = surface_of(u, 200, 1.0)
    print(f"    表面−均值 {surf - cbar:+.6f}（应 → +1/5）  中心−均值 {u[0] - cbar:+.6f}（应 → −3/10）")
    print(f"    （面值 = 格心 + dξ/2：不补这半格会读到 {u[-1] - cbar:+.6f}，"
          f"差 {0.5 / 200:.4f}——比格式误差大两个数量级，看着像解析解错了）")
    print(f"    均值 {cbar:.6f}（应 = 3t* = 24）—— 通量归一化也一并钉住了")
    print(f"    级数同一时刻 {surface_rise(8.0):+.6f}（{N_MODES} 项，尾部还差 {tail:.1e}）")
    checks.update(check("定常态表面超额 = 1/5", abs(surf - cbar - 0.2) < 2e-5, f"{surf - cbar - 0.2:+.2e}"))
    checks.update(check("定常态中心超额 = −3/10", abs(u[0] - cbar + 0.3) < 2e-3, f"{u[0] - cbar + 0.3:+.2e}"))
    checks.update(check("总锂 = 3t*", abs(cbar - 24.0) < 1e-9, f"{cbar - 24.0:+.2e}"))

    # —— 5) 短时 √t：这就是「一阶拟合不上前段」的那一段 ——
    print("\n[5] 短时渐近 S ~ 2√(t*/π) − 3t*：起点是 √t，不是一次方")
    for w in (2e-3, 5e-4, 1e-4):
        s = surface_rise(w)
        a = 2 * np.sqrt(w / np.pi)
        print(f"    t*={w:.0e}  S={s:.7f}  2√(t*/π)={a:.7f}  (S+3t*)/2√(t*/π)={(s + 3 * w) / a:.5f}"
              f"   S'={surface_slope(w):6.2f}（×√(πt*)={surface_slope(w) * np.sqrt(np.pi * w):.3f}）")
    r1 = (surface_rise(2e-3) + 6e-3) / (2 * np.sqrt(2e-3 / np.pi))
    r3 = (surface_rise(1e-4) + 3e-4) / (2 * np.sqrt(1e-4 / np.pi))
    checks.update(check("t*→0 时 (S+3t*)/(2√(t*/π)) → 1",
                        r1 > r3 and abs(r3 - 1) < 0.012 and abs(r3 - 1) < abs(r1 - 1),
                        f"t*=2e-3 偏 {100*(r1-1):+.2f}% → t*=1e-4 偏 {100*(r3-1):+.2f}%"))
    print(f"    原点斜率发散：S'(2e-3)={surface_slope(2e-3):.1f} → S'(1e-4)={surface_slope(1e-4):.1f}；"
          f"而任何有限 RC 网络的原点斜率是 Σg/τ（有限）——前段不是调参能救的。")

    # —— 6) 截断：只留前 n 个指数（= n 阶 RC）差多少 ——
    print("\n[6] 留前 n 个模态（等效 n 阶 RC：时间常数与权重都取物理值，不再拟合）")
    probe = 5e-3
    exact = surface_rise(probe)
    window = np.logspace(-3, -1, 41)          # 脉冲前段横跨的那 2 个数量级
    ref = surface_rise(window)
    print(f"    窗口 = {window[0]:.0e}…{window[-1]:.0e} 等比 41 点；RMS 是整段前段的差别，不只看一个点")
    for n in (1, 2, 4, 8, 16, 32):
        at_probe = trunc_surface(n, probe)
        rms = float(np.sqrt(np.mean((trunc_surface(n, window) - ref) ** 2)))
        print(f"    n={n:2d}：t*={probe:.0e} 处 {at_probe:.5f} vs 精确 {exact:.5f}"
              f" → 只有 {100 * at_probe / exact:5.1f}%；窗口 RMS {rms:.2e}（单位 JR/D）")
    n90 = next(k for k in range(1, 400) if trunc_surface(k, probe) > 0.9 * exact)
    n99 = next(k for k in range(1, 400) if trunc_surface(k, probe) > 0.99 * exact)
    print(f"    要在「前 {100*probe/0.2:.1f}% 时间」里对到 90% 要 {n90} 条支路，对到 99% 要 {n99} 条。")
    checks.update(check("阶数越高、前段越贴（单调）",
                        all(trunc_surface(k, probe) < trunc_surface(k + 1, probe)
                            for k in (1, 2, 4, 8, 16)), "n=1,2,4,8,16 递增"))
    checks.update(check("一阶只有半成以下", trunc_surface(1, probe) / exact < 0.35,
                        f"{100 * trunc_surface(1, probe) / exact:.1f}%"))

    # —— 7) 停流弛豫：掉的是「表面−均值」，速率是 x₁² ——
    print("\n[7] 停流弛豫：闭合颗粒总锂没处去，所以可观测量必须是表面−均值")
    u, vol, _ = march(200, 20.0)
    cbar = Diffuser.mean(u, vol)
    s0 = surface_of(u, 200, 1.0) - cbar
    print(f"    停流瞬间：表面−均值 {s0:.6f}；表面绝对值 {u[-1]:.4f}，均值 {cbar:.4f}"
          f"（=3t*=60）—— 表面浓度本身几乎不掉，别拿它当回弹曲线")
    relax = Diffuser(200, 4e-4, None)
    uu, tacc = u.copy(), 0.0
    a1 = W[0] / W.sum()          # 首模态只占停流瞬间表面超额的这一份
    print("     Δt*        数值      首项+幅值      纯 e^(−x₁²Δt*)    "
          "e^(−π²Δt*)      幅值修正后误差")
    hist = []
    for want in (0.02, 0.05, 0.1, 0.2, 0.4, 0.8):
        uu = relax.advance(uu, int(round((want - tacc) / relax.dt)))
        tacc = want
        num = (surface_of(uu, 200, None) - Diffuser.mean(uu, relax.vol)) / s0
        hist.append((want, num))
        amp = a1 * np.exp(-X2[0] * want)
        print(f"    {want:5.2f}  {num:10.6f}  {amp:11.6f}  {np.exp(-X2[0]*want):12.6f}  "
              f"{np.exp(-np.pi ** 2 * want):11.6f}   {100 * (amp / num - 1):+7.1f}%")
    (t_lo, n_lo), (t_hi, n_hi) = hist[-2], hist[-1]
    slope = np.log(n_lo / n_hi) / (t_hi - t_lo)
    print(f"    末两段对数斜率 = {slope:.2f}；x₁² = {X2[0]:.2f}，π² = {np.pi ** 2:.2f}"
          f" → 偏差 {100 * (slope / X2[0] - 1):+.1f}% / {100 * (slope / np.pi ** 2 - 1):+.0f}%")
    checks.update(check("弛豫速率是 x₁²，不是 π²",
                        abs(slope / X2[0] - 1) < 0.02 and abs(slope / np.pi ** 2 - 1) > 0.9,
                        f"斜率 {slope:.2f} vs x₁² {X2[0]:.2f}（π² 差 {100*(slope/np.pi**2-1):+.0f}%）"))
    print(f"    首模态只带 {100 * a1:.1f}% 的幅度：即使速率对了，一条 RC 也只能解释回弹的一半，"
          f"剩下 {100 * (1 - a1):.1f}% 走得更早——这就是回弹曲线拟合不出单一 τ 的原因。")
    print(f"    换成秒：τ₁ = R²/(D·x₁²) = {TAU_D / X2[0]:.1f} s；错用 R²/(D·π²) = {TAU_D / np.pi ** 2:.1f} s。"
          f"静置窗长按哪个开，差一倍。")

    # —— 8) 奈奎斯特尾巴的斜率：那是窗口的读数，不是元件的 ——
    print("\n[8] EIS 尾巴：图上「斜率约 0.94」是谁的数——扫描窗口的，不是元件的")
    f_hi, f_dome = 2000.0, find_freq_by_re(41.2)
    f_leave, f_end = find_freq_by_re(63.94), find_freq_by_re(76.73)
    beats = ((f_hi, "① 高频截距"), (f_dome, "② 半圆顶"), (f_leave, "③ 离圆"), (f_end, "④ 末端"))
    print("    先把动画那四拍逐条重算（元件值照抄 SVG 注释行，一点没调）：")
    for f, lab in beats:
        z = randles(f)
        print(f"      {lab}　f={f:8.4f} Hz → Re {z.real * 1e3:6.2f} mΩ　−Im {-z.imag * 1e3:5.2f} mΩ")
    dome = max(np.geomspace(2000.0, f_leave, 20000), key=lambda f: -randles(f).imag)
    print(f"      半圆顶是局部极大：f={dome:.2f} Hz，−Im={-randles(dome).imag * 1e3:.2f} mΩ；"
          f"纯 RC 会给出 1/(2πRctCdl)={1 / (2 * np.pi * EIS_RCT * EIS_CDL):.2f} Hz、Rct/2={EIS_RCT / 2 * 1e3:.1f} mΩ")
    checks.update(check("图上四拍由 SVG 自己那行公式复现",
                        abs(randles(f_hi).real * 1e3 - 20.0) < 0.05
                        and abs(-randles(dome).imag * 1e3 - 20.6) < 0.1
                        and abs(randles(f_end).real * 1e3 - 76.7) < 0.05
                        and abs(-randles(f_end).imag * 1e3 - 17.2) < 0.1,
                        f"截距 {randles(f_hi).real * 1e3:.2f}　圆顶 {-randles(dome).imag * 1e3:.2f}"
                        f"　末端 {randles(f_end).real * 1e3:.2f}/{-randles(f_end).imag * 1e3:.2f}"))
    print(f"    尾巴就是 {f_leave:.4f}→{f_end:.4f} Hz 这一个十倍频程（图只画到这儿）：")
    seg = [tail_slope(f, f / 1.1369) for f in
           (f_leave, f_leave / 3, f_leave / 10, f_end)]
    print(f"      割线斜率 {tail_slope(f_leave, f_end):.4f}；逐段 " +
          " → ".join(f"{s:.3f}" for s in seg) + "（越往低频越接近 1）")
    print("      把扫描往低频延长，同一条曲线、同一个元件，读出来的斜率一路改口：")
    wid = {}
    for m in (1, 3, 10, 30, 100, 300, 1000):
        wid[m] = tail_slope(f_leave, f_end / m)
        print(f"        多扫 {m:5d}×　→ 斜率 {wid[m]:.4f}　末端实部 {randles(f_end / m).real * 1e3:7.1f} mΩ")
    checks.update(check("理想扩散：窗口放宽，斜率单调趋近 1",
                        all(wid[a] < wid[b] for a, b in zip(sorted(wid)[:-1], sorted(wid)[1:], strict=True))
                        and wid[1000] > 0.99, f"1× {wid[1]:.3f} → 100× {wid[100]:.3f} → 1000× {wid[1000]:.3f}"))
    print("    所以「0.94」= 比图里那段多扫约 10 倍频宽。它不是新元件，是窗口。")
    print("    反过来才是要紧的：把不到 1 的斜率当成常相位元件（CPE）的证据，会「测」出一个假 α")
    for s in (wid[1], 0.94, wid[1000]):
        print(f"      读数 {s:.3f} → α=(2/π)arctan(s)={2 / np.pi * np.arctan(s):.3f}（理想扩散该是 0.500）")
    print("    真分布时间常数（α<0.5）的签名是封顶：窗口再宽也回不到 1，停在 tan(απ/2)")
    for alpha in (0.45, 0.40):
        row = [tail_slope(f_leave, f_end / m, alpha) for m in (1, 10, 100, 1000)]
        print(f"      α={alpha:.2f}：{' → '.join(f'{s:.3f}' for s in row)}"
              f"　渐近 tan(απ/2)={np.tan(alpha * np.pi / 2):.3f}")
    cap45 = tail_slope(f_leave, f_end / 1000, 0.45)
    checks.update(check("分数阶支路的斜率封顶在 tan(απ/2)，不随窗口趋近 1",
                        abs(cap45 / np.tan(0.45 * np.pi / 2) - 1) < 0.02 and cap45 < 0.9,
                        f"α=0.45 扫到 1000× 仍是 {cap45:.3f}（{100 * cap45 / np.tan(0.45 * np.pi / 2) - 100:+.1f}% 于渐近值）"))
    print("    判别只有一条：把低频端往下扩。斜率走向 1 就是理想 Warburg + 窗不够宽；"
          "走向一个低于 1 的平台才是 α≠0.5。差 6% 的斜率自己什么都不能说明。")

    print()
    bad = [k for k, v in checks.items() if not v]
    if bad:
        print(f"FAIL：{len(bad)} 项超差 → {bad}")
        return 1
    print(f"PASS：{len(checks)} 项锚点全过——扩散这一段的每条时间常数、每阶 RC 的误差，"
          f"都是算出来的，不是示意图里的示意数")
    return 0


if __name__ == "__main__":
    sys.exit(main())
