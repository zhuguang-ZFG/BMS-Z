# 机制动画生成

`gen_mechanism_svgs.py` 重画下面表里的机制图。曲线点来自脚本里的公式，或来自 `code/soc/compare.py` 的 `run(seed=42)`。不改 `code/` 里的算法。色和版式见 [动画画风规范](../docs/circuits/动画画风规范.md)。

```bash
python3 tools/gen_mechanism_svgs.py
```

会覆盖：

| 文件 | 曲线从哪来 |
|---|---|
| `docs/circuits/assets/ocv-hysteresis.svg` | 平均开路电压 ± 20 mV。SOC 0.50 锚在 3.300 V，平台斜率 0.075 V/单位荷电 |
| `docs/circuits/assets/ocv-plateau-distrust.svg` | 同一条平均支，锚改到 3.295 V。底栏的 dV/dSOC 和「5 mV 盖住多少个百分点」是这条导数算的 |
| `docs/circuits/assets/sop-derating.svg` | 温度分段线性、荷电分段线性、电压墙 `(OCV−3.00)/0.015/40 A`，取最小后再限斜率 |
| `docs/circuits/assets/kalman-gain.svg` | `P←P+Q`，`K=P/(P+R)`，`P←(1−K)P`。P0=0.04，Q=0.0004，R 取 0.001 和 0.020。绿线把 Q 提到 0.0016 |
| `docs/circuits/assets/ekf-estimation.svg` | `compare.py` 全部 17000 步的 RMSE；折线等距抽点 |
| `docs/circuits/assets/second-order-rc.svg` | `U = 3.700 − 20·(0.002 + 0.004·(1−e^{−t/1}) + 0.006·(1−e^{−t/30}))`。一阶对照把 10 mΩ 合成 τ=12 s |
| `docs/circuits/assets/soh-aging.svg` | 容量 `100 − 20·(n/3000)^1.5`，内阻 `20 + 25·(n/3000)^0.45` mΩ。新电池按 5.0 Ah 起算 |
| `docs/circuits/assets/error-budget-waterfall.svg` | 2.0、1.5、0.8、0.3、0.9 mV 逐截累加。预算线在 5 mV，标定后剩约 1.8 mV |

数字是示意或仿真，不是电芯实测。单文件控制在大约 20 KB 以内。

## 再生成对账（本地门禁里的「生成图对账」）

`scripts/local-gates.sh` / `.ps1` 有一道 CI 没有的门：用 `--out` 把生成脚本的输出写到临时目录，再与 assets 里的入库版本逐字节比对。过了它，意味着入库的生成图和当前生成器输出一致。它会拦住两类事故：

- **手改生成产物**。`ekf-estimation.svg` 这类文件属于生成器，发现图上的数字错了要改生成器再生成，不是直接改 SVG；
- **改了生成器忘了重新生成**。样式块加过 `.boxy/.boxr` 但 7 张旧产物没跟着重生成，这种过期产物在 2026-10 之前没有任何门能发现。

为什么 CI 不跑这道门：`ekf-estimation` 的坐标来自 `compare.run(seed=42)` 的仿真，`requirements.txt` 故意只锁 numpy 区间（≥1.24,<3）。哪天 numpy 出新版让浮点差到最后一位，CI 会在所有无关 PR 上变红。本地门跑在你提交前的那台机器上，没有这个问题。真要跨机器复现，按 `code/requirements.txt` 注释里的版本对齐 numpy。

对账失败时先跑 `python3 tools/gen_mechanism_svgs.py` 覆盖 assets（不加 `--out` 就是直接写库），再 `git diff docs/circuits/assets` 过目提交。

## 社交卡（本地门禁里的「社交卡对账」）

`docs/circuits/assets/bms-roadmap-social.png` 是仓库的社交预览图，图上有三个数：教程篇数、动画张数、配套包数。它原先是手工做的位图，仓库里没有源，所以 147→148 那轮 README、门户 HTML、路线图动画都跟着改了，只有它没改——而这张是链接分享出去最先被看到的东西。

现在由 `tools/gen_social_card.py` 画。三个数从仓库现算（`docs/stages/stage-*.md` 的篇数、`docs/circuits/assets/*.svg` 的张数、`code/` 下的包目录数），和 [check_docs.py](../.github/scripts/check_docs.py) 数的是同一批文件；版式是照上一版逐像素量出来的，不是新设计。

```bash
python3 tools/gen_social_card.py            # 覆盖入库的社交卡
python3 tools/gen_social_card.py --out DIR  # 只写到 DIR，供本地对账
```

为什么这道门也留在本地：中文字体走系统字体目录里的 Noto Sans SC，runner 上没有，缺字会画成方框。文本类的张数对账（README、门户 HTML、动画索引的中文数字标题、路线图 SVG 的 `desc` 与底栏）在 CI 里由 `check_docs.py` 守；社交卡是位图，查不了字，只能比对再生成的哈希。

## 发版计数（`release_stats.py`）

`python3 tools/release_stats.py --from v1.2.0 --to v1.3.0` 一条命令数出 CHANGELOG 版本节首那句：条目数取那一节 `- ` 开头的行数，提交数取 `git rev-list --count`，PR 区间与个数取 `git log --format=%s` 末尾的 `(#N)`，直接提交数 = 提交数 − 带 PR 号的提交数。`--to` 默认 HEAD（起草下一版时用），`--section` 可点名小节，小节找不到就退回 `## [Unreleased]`。

```bash
python3 tools/release_stats.py --from v1.2.0 --to v1.3.0   # 数已发布的那一版
python3 tools/release_stats.py --from v1.3.0               # 数到 HEAD，起草下一版用
```

```text
CHANGELOG 小节：## [1.3.0]
共 44 条，覆盖 `v1.2.0` 之后 33 个提交（PR #25–#42 共 18 个，加 15 个直接提交）
```

第二行正是 1.3.0 节首定版那一句，一字不差。带 PR 号的提交数与去重后的 PR 号个数不等时（同一个 PR squash 过两次）会多打一行提示；区间里没有带 PR 号的提交时改说「没有带 PR 号的提交，加 M 个直接提交」；本地找不到 `--from` 或 `--to` 时退出码 2 并让你先 `git fetch --tags`，不猜数。

对账门在 `check_docs.py --release-truth` 里的 `check_release_counts()`，工具和门各数一遍再比。它留在本地而不进 CI，理由与发布记录真值门同一条：`actions/checkout` 默认不抓 tag，runner 上连区间都框不出来。详见 [维护说明](../docs/维护说明.md) 的「发布记录」。

## 口诀速查页（CI 会守同步）

`tools/gen_koujue_index.py` 把全库口诀（`> **口诀**` 引用块，句数写在生成页的页首，不在这份文档里手抄一遍）汇总成 [docs/口诀速查.md](../docs/口诀速查.md)，按阶段教程 → 电路详解 → 专题与工具页 → 中文导读分组，每句钉着出处小节的锚点。

生成逻辑 `build_koujue_page()` 在 `.github/scripts/check_docs.py` 里：检查器每次跑都重算一遍并与入库版本逐字比对，**正文里口诀改了、加了、删了而没重新生成，CI 的 docs-consistency 直接红灯**，报错会指出第一处差异。所以：

```bash
python3 tools/gen_koujue_index.py            # 改完口诀后重新生成
python3 tools/gen_koujue_index.py --check    # 只比对，不同步退出码 1
```

这和生成图对账不同：口诀页是纯文本、零依赖，同步检查可以直接进 CI，不需要留在本地门。

另外几张示意图（DW01、短路时间轴等）是在原文件上加了移动的点或游标，不由这个脚本覆盖。DW01 底栏的检流直线是 `V = 0.40 + 1.20 t`（t 从 0 到 1），1.2 V 是这条直线上的阈值。

底栏横轴标题用 `axis_title_xy`：放在最后一个刻度的右侧，不要和刻度写在同一个点上。`tools/reskin_legacy_svgs.py` 按画风规范换旧图的色和字体时，也调用这个函数挪开已经叠住的标题。

`batch3_scenes.py` 由上面同一个入口覆盖。第 3 批的曲线也标示意。和正文对得上的数如下，没有新编 datasheet：

| 文件 | 曲线从哪来 |
|---|---|
| `short-i2t-window.svg` | 对数轴，`I²t = 500² t`。10 μs ≈ 2.5 A²s，1 ms ≈ 250 A²s |
| `gate-return-loop.svg` | `i = 500·max(0, 1−t/tf)`，tf 取 10 μs 与 200 μs。I²t 是这条下降的积分 |
| `hvil-loop.svg` | 对数时间阶梯：环断在 0 ms（轴上标 ≤1），15 ms、30 ms、500 ms |
| `overdischarge-copper.svg` | `V = 3.4 − 0.24·进程`。预充带到约 3.0 V，深放风险 `clip((2.0−V)/0.5, 0, 1)` |
| `afe-register-read.svg` | `(0x12+0x34) & 0xFF = 0x46`。第二字节改 0x35 则和为 0x47。不是芯片 CRC |
| `gbt-27930-handshake.svg` | 示意 0–4.5 s。需求在 2–3 s 为 40 A、3–4 s 为 10 A，跟随滞后 0.25 s。3.8 s 超时则绿线落到 0，红线仍停在 10 A |
| `smbus-sbs-roundtrip.svg` | 高字节到了才是 `0x74 + 0x0E×256 = 3700` mV。不是 SOC |
| `active-discharge-beside-contactor.svg` | `V = 400 e^{−t/0.2}`。到 60 V 的时间是 `−0.2 ln(60/400)`。闸还合着按 800 W |
| `solid-vs-structural-cell.svg` | 1 A。液体 20 mΩ / 1 s，固体界面 80 mΩ / 8 s。不是 LLZO 手册 |
| `isolation-copper-bridge.svg` | `H = (f/f0) / sqrt(1+(f/f0)²)`，f0 = 10 kHz 示意。铜桥增益 1，V = 400 H。不写爬电毫米 |
| `cloud-bms-dashboard.svg` | 存储年龄 `t mod 30`。3 级报警的绿线在 1 s |
| `cert-floor-scene.svg` | 硬件在 t ≥ 10 ms 变为已切断。停掉的软件恒为 0。100 ms 是同一笔示意 FTTI |
| `pack-manual-sampling.svg` | `V = 3.0 + 1.2 s`。红虚线 4.25 V 是阶段 1 的三元示例，阈值格空 |
| `mqtt-pubsub-will.svg` | 静默年龄 = t。教学保活 15 s，不是厂商默认 |
| `parallel-tap-boundary.svg` | 总电流 10 A，`I1 = 10 k/(1+k)`，k = R2/R1。k=2 时约 6.67 A 与 3.33 A |
| `bq769-evb-isospi.svg` | 共模 `n×3.7` V。差分示意恒 2 V |
| `balance-topology-compare.svg` | 被动 `(4.2²/100)·t`。主动输入每秒一拍 20 μJ |
| `balance-efficiency-blank.svg` | 输入 `20 μJ × n`。不画输出，不写 η |
| `precharge-sequence-curve.svg` | `V = 400(1−e^{−t/0.17})`。3τ ≈ 0.51 s ≈ 380 V。I0 ≈ 2.35 A，½CU² = 80 J。故障水平线约 40 V |
| `contactor-weld-check.svg` | `V = 400 e^{−t}`。0.1 s ≈ 362 V，5 s ≈ 2.7 V。粘连恒 400 V |
| `protocol-resync.svg` | 只读调用 `code/protocol` 的教学帧。垃圾 `00 11 22` 之后仍对齐；末字节翻位则坏 CRC |
| `uv-recovery-005c.svg` | 教学 5 Ah 的 0.05C = 0.25 A，只在约 2.0–3.0 V。低于约 2.0 V 允许电流画成 0。红虚线 5 A 标不要 |
| `balance-vs-pack-current.svg` | `t = 0.05/I`，I 从 0.05 A 到 0.20 A。1C = 5 A 时 36 s |
| `cloud-vs-pack-protection.svg` | 对数时间上的阶梯：短路示例 10 μs、过充 80–200 ms、正常存储最多 30 s |
