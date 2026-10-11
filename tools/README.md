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

第一行打印的是**实际用了哪一节**，这行不是装饰：`--section` 点名的小节找不到时，工具退回 `## [Unreleased]`（起草下一版要的就是这个行为），而那半句提交数照样来自同一个 git 区间——条目数张冠李戴之后看上去仍是一次正常输出。所以 `check_docs.py --release-truth` 把这行一起取回对账，数了别的小节就报红。小节名认开头可选的 `v`（1.0.0 那一节当年就写成 `## [v1.0.0]`），与门那边四处读小节名的正则同一口径，分家由 `check_changelog_enum()` 盯着。

那五个数（44 条、33 个提交、PR #25–#42、共 18 个、加 15 个直接提交）与 1.3.0 节首定版那一句逐个相等；措辞上工具打的是主干，定版那句多一个「的」和前置分句（「……这一批，共 44 条，覆盖 `v1.2.0` 之后**的** 33 个提交……」），门的正则用 `之后的?` 把两种都认。带 PR 号的提交数与去重后的 PR 号个数不等时（同一个 PR squash 过两次）会多打一行提示；区间里没有带 PR 号的提交时改说「没有带 PR 号的提交，加 M 个直接提交」；本地找不到 `--from` 或 `--to` 时退出码 2 并让你先 `git fetch --tags`，不猜数。

对账门在 `check_docs.py --release-truth` 里的 `check_release_counts()`，工具和门各数一遍再比。它留在本地而不进 CI，理由与发布记录真值门同一条：`actions/checkout` 默认不抓 tag，runner 上连区间都框不出来。

`sentence()` 是那句的**唯一拼法**，不要在别处再抄一遍模板：CI 里的 `check_release_wording()` 把这个函数拼出的两种句式回灌 `check_docs.py` 的 `CL_COUNT` / `CL_COUNT_NOPR`，要求命中、五个数原样读回、两种句式互不认领。改这里的措辞就得同步改正则——两边分家时真值门不会对工具的句子报错，而是静默不判，那道措辞门正是为这个而存在。详见 [维护说明](../docs/维护说明.md) 的「发布记录」。

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
| `cloud-vs-pack-protocol.svg` | 对数时间上的阶梯：短路示例 10 μs、过充 80–200 ms、正常存储最多 30 s |

## 视频系列（`tools/video/`）

把站点自己的机制动画（`docs/circuits/assets/*.svg` 的 SMIL）和阶段正文的口头稿做成成片：横屏 1920×1080 与竖屏 1080×1920 两个画幅各一条。**分镜（`specs/*.json`）是唯一真源**——旁白、图、布局、音效、BGM 曲目都写在那里；正文与动画只被引用，不被复制。产物全在 `media/` 下（`.gitignore` 已排除）：MP4 与 PNG 帧是可重算的派生物，入库会把仓库压垮，`media/video/work/` 是流水线中间件，成片落 `media/video/out/<slug>-<aspect>.mp4`，旁边一份同名 `.json` 分开记两本账：`mix` 是封装前的语音/BGM/SFX 电平，`output_loudness` 是 AAC 成片实测的 LUFS / true peak / LRA。

六个模块按依赖顺序跑，**跳步的报错都指得回具体模块**：

```bash
python tools/video/spec.py     --check  ep02-recognize-bms          # 分镜静态检查：字段、图名、口径
python tools/video/narrate.py  --episode ep02-recognize-bms          # 旁白 → wav + 实测时长表
python tools/video/capture.py  --episode ep02-recognize-bms --list   # 看要截哪些 clip，去掉 --list 就截
python tools/video/compose.py  --episode ep02-recognize-bms --selftest # 内容框、字幕安全区、六种布局
python tools/video/compose.py  --episode ep02-recognize-bms --both     # 版面 + 烧字 → 无声底板 + srt
python tools/video/assemble.py --episode ep02-recognize-bms --both     # numpy 混音 + 母带 + 封装 → 成片
python tools/video/bgm.py      --selftest                               # BGM/SFX 自验（可单独跑）
python tools/video/assemble.py --episode ep02-recognize-bms --selftest  # 摆位、ducking、成片响度/真峰值/帧数
python tools/video/audit.py    --episode ep02-recognize-bms --both      # 全片审计：闪切、黑白帧、削波、爆音、静音、口型、来源（成片 vs 底板/混音原件）
```

五条不变量值得单独说，因为它们错了都不会报错、只会不好看、难听或对不上口型：

- **时间轴只用实测时长**。`spec.timeline()` 缺 `durations.json` 直接报错，不用估计时长把后面全蒙一遍；改一个字的旁白，narrate 的缓存键跟着变，assemble 按新键找不到旧 wav 会当场报缺文件，而不是拿旧音频配新字幕。
- **帧数按全局边界摊**。compose 按每个 beat 的 `[start, end)` 边界取帧，74 个 beat 首尾相接，总数恒等于 `round(总时长 × 30)`。曾经逐 beat 各自 `round(dur×fps)` 再求和，与总数差出 4 帧——assemble 的帧数门直接拦下整轮封装。assemble 另两道门继续守音画差不超过一帧、混音与时间轴同源。
- **成片的帧数要数，不能只读元数据**。混音补齐到整帧边界（`round(帧数/30×48000)` 个样本），mux 不用 `-shortest`；assemble 与 audit 都对**封装后的文件**数帧。曾经 `-shortest` 按短流截视频，元数据三帧门全绿、成片却少 3 帧——结尾整张 CTA 卡静默消失，这件事只有“量成品”能发现。
- **成片得是自己流水线造出来的东西**。帧数、响度、闪切、黑白帧、削波门都只看成品自己：mux 换错底板、拿错音轨、母带增益失准，它们照样全绿。audit 因此比两条“构造恒等式”——画面逐像素对 compose 刚跑出来的无声底板（`-c:v copy` 下恒等于 0，竖屏底板当横屏 mux 实测差 123.0 即红）；音轨对齐 `-mix.wav` 比残差（增益按最佳拟合实测，随母带意图走；白噪音轨 0.0 dB、截短 4.167 s、增益偏 0.8 dB 都红，正品 −0.825 dB / 27.9 dB / AAC 尾差 +15 ms 稳定过）。
- **一集只用一套皮肤**。成片统一深色，Chromium 以 `prefers-color-scheme: dark` 捕获 SVG；主题进入 clip 缓存键（例如 `…-dark.mp4`），不能让改过皮肤的 compose 静默吃到旧浅色帧。capture 中途崩溃会在 `finally` 清掉临时 PNG，异常仍原样上抛。
- **字幕与主画面不抢位置**。竖屏字幕基线距底 290 px、右侧给平台按钮留 150 px，长字幕按真实像素宽度缩到不低于 32 px；card / number / checklist / quiz 的主画面已经说过的话不再抄到底带，只有 figure 额外保留一行结论。`compose.py --selftest` 对两个画幅的内容框、字幕宽度、主题缓存键和六种布局逐项守门。
- **响度量最终文件**。旁白在的时候 BGM 从满电平 −14 dB 压到 −26 dB；混音原件不压缩，最终 AAC 统一衰减 0.8 dB。assemble 用 ffmpeg loudnorm 对**封装后的 MP4**量 EBU R128，要求 −18…−16 LUFS、true peak ≤ −1 dBTP；ep02 两个画幅实测均为 −17.31 LUFS / −1.16 dBTP / LRA 2.10 LU。

两个环境事实：`narrate` 默认走 edge-tts（在线神经语音），**断网时 `--engine sapi`** 用 Windows 离线语音兜底，音质降级但系列不断更；系统没有 ffmpeg 时回落到 imageio-ffmpeg 自带的那一个。Chromium 必须是 Playwright 那份（SMIL 动画只有它能忠实渲染），路径与版本按 `capture.py` 顶部的 `CHROMIUM` 找。

这套不进 CI，也不进本地门禁清单：它要网（TTS）、要 Playwright 的 Chromium、要几 GB 临时盘，而 runner 上一个都不占；本地门禁清单还要在 CI 与四处文档副本之间逐字对账，加一项就得同步五处，为一个本地工具改这份契约不划算。CI 今日守得住的是它的上游文本产物——口诀页逐字同步、社交卡三个数在 `check_docs.py` 里现算——这些都在；跑片这条链留在维护者机器上，由 `spec --check`、`compose --selftest`、`bgm --selftest`、`assemble --selftest` 四道窄门守。出片后仍要给每个 beat 抽中点：ep02 是每个画幅 74 帧，横屏排 4×5、竖屏排 5×5 审片格，不能只挑几个漂亮画面截图。
