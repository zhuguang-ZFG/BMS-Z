---
search: false
slug: pybamm-scales
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: hppc-identification
source_svg: null
---

# 观察题

同一个电芯，1C 放电时 SPM 够用，10C 就不够了——差别不在方程，在哪个时间尺度还「小」。

# 帧大纲

1. 版式立起：一条对数时间轴（10² s → 10⁴ s），先不标任何点——格式先于答案。
2. τ_e ≈ 100 s：电解液扩散的松弛尺度（L=80 µm、D_e=2.5×10⁻¹⁰、Bruggeman 1.5 → D_eff≈6.3×10⁻¹¹）。
3. 1C：t_d=3600 s，比 τ_e 长 36 倍；写成判据就是 τ_e/t_d ≈ 0.03——电解液近似瞬时平衡，SPM 敢省掉电解液项。
4. 10C：t_d 缩到 360 s，与 τ_e 同量级（360/100 ≈ 3.6）——梯度跟不上，SPM 假设破了，至少 SPMe。
5. τ_s ≈ 2500 s（约 42 min）与放电时间同量级甚至更慢——同样的电流、不同历史，端电压不同；RC 尾巴、HPPC 时间窗量的都是这条时间尺度。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03 only; zero use of C-15 in this figure. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames of one logarithmic time axis (10² s to 10⁴ s), same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — the axis is ruled with decade ticks 10² s / 10³ s / 10⁴ s; nothing plotted yet.
Frame 2 — one marker at τ_e ≈ 100 s: the electrolyte diffusion relaxation scale (L=80 µm, D_e=2.5e-10, Bruggeman 1.5 → D_eff≈6.3e-11).
Frame 3 — at 1C: t_d=3600 s on the axis; a note block reads τ_e/t_d ≈ 0.03 — electrolyte near instantaneous equilibrium, so SPM may drop the electrolyte term.
Frame 4 — at 10C: t_d falls to 360 s, same order as τ_e (360/100 ≈ 3.6) — gradients lag, SPM's assumption breaks, at least SPMe.
Frame 5 — τ_s ≈ 2500 s (about 42 min) sits at the same order as the discharge time: same current, different history, different terminal voltage — the RC tail and the HPPC time window measure this scale.

# Prompt（ZH）

手绘教学信息结构图，FA-029 Chris Ware 几何叙事风格：平直几何分栏、精确直线框架、克制冷面构图、纸纹质感。结构线与标注只用 C-03 普鲁士蓝，本图零红。数字只用小手写标注，全部标「示意」。图注：原理示意 / 非实拍。

同一条对数时间轴（10² s → 10⁴ s）的五个帧、同一视角，无人、无卡通吉祥物、无品牌 Logo、纯示意：

1. 版式划好：一条对数时间轴，十进刻度 10² s / 10³ s / 10⁴ s，暂不标点。
2. 一个标记 τ_e ≈ 100 s：电解液扩散的松弛尺度（L=80 µm、D_e=2.5×10⁻¹⁰、Bruggeman 1.5 → D_eff≈6.3×10⁻¹¹）。
3. 1C：t_d=3600 s 落在轴上；判据块写 τ_e/t_d ≈ 0.03——电解液近似瞬时平衡，SPM 敢省掉电解液项。
4. 10C：t_d 缩到 360 s，与 τ_e 同量级（360/100 ≈ 3.6）——梯度跟不上，SPM 假设破了，至少 SPMe。
5. τ_s ≈ 2500 s（约 42 min）与放电时间同量级甚至更慢：同样的电流、不同历史，端电压不同——RC 尾巴、HPPC 时间窗量的是它。

# 验收自检

- [ ] 无人、无卡通、无实拍口吻
- [ ] 全图零红（C-15 不出现）
- [ ] 四条标注错行不压字（τ_e/t_d 1C 在高行，10C/τ_s 在低行）
- [ ] 数字与表 23-2 逐字一致：τ_e≈100 s / τ_s≈2500 s（约 42 min）/ t_d 1C=3600 s / 10C=360 s；判据 τ_e/t_d≈0.03、360/100≈3.6
