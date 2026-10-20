# 机制动画生成

`gen_mechanism_svgs.py` 重画下面表里的机制图。曲线点来自脚本里的公式，或来自 `code/soc/compare.py` 的 `run(seed=42)`。不改 `code/` 里的算法。色和版式见 [动画画风规范](../docs/circuits/动画画风规范.md)。

> **让模型改图**　改生成器，不改 assets 里的产物。动代码前先过 [写代码的五个关卡](../docs/AI陪练卡.md#写代码的五个关卡)，用本页的再生成对账收口。

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

七个模块按依赖顺序跑，**跳步的报错都指得回具体模块**：

```bash
python tools/video/spec.py     --check  ep02-recognize-bms          # 分镜静态检查：字段、图名、口径
python tools/video/narrate.py  --episode ep02-recognize-bms          # 旁白 → wav + 实测时长表
python tools/video/capture.py  --episode ep02-recognize-bms --list   # 看要截哪些 clip，去掉 --list 就截
python tools/video/compose.py  --episode ep02-recognize-bms --selftest # 内容框、字幕安全区、六种布局、静态回退、字幕高亮、清单折行
python tools/video/compose.py  --episode ep02-recognize-bms --both     # 版面 + 烧字 → 无声底板 + srt
python tools/video/assemble.py --episode ep02-recognize-bms --both     # numpy 混音 + 母带 + 封装 → 成片
python tools/video/bgm.py      --selftest                               # BGM/SFX 自验（可单独跑）
python tools/video/assemble.py --episode ep02-recognize-bms --selftest  # 摆位、ducking、成片响度/真峰值/帧数
python tools/video/audit.py    --episode ep02-recognize-bms --both      # 全片审计：闪切、黑白帧、转场（交叉淡化摊开/过场后文字不倒退）、削波、静音、口型、来源（成片 vs 底板/混音原件）
python tools/video/publish.py  --episode ep02-recognize-bms --selftest  # 发布包自验：封面（黑帧块、强调色占比、徽章实心、文字不压吉祥物）与文案预算
python tools/video/publish.py  --episode ep02-recognize-bms             # 封面三张 + 四平台文案 → media/video/out/publish/（不入库）
python tools/video/publish.py  --episode ep02-recognize-bms --kit       # 再写投稿页用的复制粘贴件 → publish/kit/（含 B 站分区/10 标签/分段章节）
python tools/video/publish.py  --episode ep02-recognize-bms --cover-variant q  # 另出一套问句版封面（-q 后缀），小红书封面 PK 当备选用
python tools/video/clip.py     --episode ep02-recognize-bms --selftest  # 切片自验：取段 60–90 s、帧账、片尾卡文字不压水印、文案预算
python tools/video/clip.py     --episode ep02-recognize-bms             # 抖音 9x16 切片（60–90 s + 4 s 片尾卡）+ 文案 → publish/douyin/（不入库）
python tools/video/clip.py     --all                                    # 八集批量切片（同一条流水线）
```

这些不变量值得单独说，因为它们错了都不会报错、只会不好看、难听或对不上口型：

- **时间轴只用实测时长**。`spec.timeline()` 缺 `durations.json` 直接报错，不用估计时长把后面全蒙一遍；改一个字的旁白，narrate 的缓存键跟着变，assemble 按新键找不到旧 wav 会当场报缺文件，而不是拿旧音频配新字幕。
- **帧数按全局边界摊**。compose 按每个 beat 的 `[start, end)` 边界取帧，74 个 beat 首尾相接，总数恒等于 `round(总时长 × 30)`。曾经逐 beat 各自 `round(dur×fps)` 再求和，与总数差出 4 帧——assemble 的帧数门直接拦下整轮封装。assemble 另两道门继续守音画差不超过一帧、混音与时间轴同源。
- **成片的帧数要数，不能只读元数据**。混音补齐到整帧边界（`round(帧数/30×48000)` 个样本），mux 不用 `-shortest`；assemble 与 audit 都对**封装后的文件**数帧。曾经 `-shortest` 按短流截视频，元数据三帧门全绿、成片却少 3 帧——结尾整张 CTA 卡静默消失，这件事只有“量成品”能发现。
- **成片得是自己流水线造出来的东西**。帧数、响度、闪切、黑白帧、削波门都只看成品自己：mux 换错底板、拿错音轨、母带增益失准，它们照样全绿。audit 因此比两条**构造恒等式**——`-c:v copy` 让成片画面逐像素等于 compose 刚跑出来的无声底板（竖屏底板当横屏 mux 实测差 123.0 即红）；音频直送 AAC 让音轨逐样本等于 `-mix.wav`（增益按最佳拟合实测，随母带意图走：白噪音轨 0.0 dB、截短 4.167 s、增益偏 0.8 dB 都红，正品 −0.825 dB / 尾差 +15 ms 稳定过）。恒等式之外还有一道按中点取阈值的：残差相对**同位置 10 ms 局部电平**——一个 0.5 的单样本毛刺不改峰值、不改整段信噪比（27.89 → 27.89）、不改直流，前几道门全放行，而正常 AAC 陡沿余振最大只有 4.77 倍、毛刺是 250–514 倍，取几何中点 50。孤立爆音**不作为门**：AAC 把陡沿抹平（音源 4790 → 成品 215），“超过音源两倍加 200”基本不可能触及；“音源里没有的新增断点”实测 49 处但全是编码陡沿余振，上限只能拍倍数——两者都降为诊断数字，守卫交给残差比门。
- **一集只用一套皮肤**。成片统一深色，Chromium 以 `prefers-color-scheme: dark` 捕获 SVG；主题进入 clip 缓存键（例如 `…-dark.mp4`），不能让改过皮肤的 compose 静默吃到旧浅色帧。capture 中途崩溃会在 `finally` 清掉临时 PNG，异常仍原样上抛。
- **clip 按 2× 超采样捕获**（`CLIP_SS`）。暗底细字行在 yuv420p 4:2:0 下会产生贯穿文字宽度的色度泄漏带（文字行下方一行，chroma bleed）——编码参数、yuv444p、full-range 全无效（已逐一实验），因为 bleed 宽度固定为 1 个 chroma 行。capture 按图区 2× 截图编码，compose 贴入前 LANCZOS 缩回：缩回让线宽减半、对比度摊薄，SVG 细线也更锐。代价是捕获时长约 ×4、clip 体积 ×4，以及 compose 每帧一次 resize；缓存键自带尺寸，改倍数后旧 clip 自然作废重捕。这道门任何工具都量不出来，只有抽帧人检看得见，所以写在这里而不写进 selftest。
- **字幕与主画面不抢位置**。竖屏字幕基线距底 290 px、左右各守 10% 侧边危险带（右为动作栏、左下为评论框），字幕带以画幅为心；长字幕按真实像素宽度缩到不低于 40 px（放不下就折行，折行只断在标点）。横屏距底 88 px（墨迹实测距底 36 px）不为"避开播放器控件"再动：2026-10-17 在 B 站真实播放器上量过，控件层是 CSS 定尺而视频随窗口缩放——同一根 4 px 进度条换算到视频坐标，内嵌窗口（视频 668×376）是距底 144 px、1136×828 全屏 96 px、1:1 全屏 74 px，**会随窗口尺寸扫过整条字幕带**，没有哪个固定位置能同时避开（往上抬只是把遮挡发生的那档尺寸换一档）；控件层又在光标静止时整体隐藏（实测 bottom/mask `opacity: 0`、progress `visibility: hidden`），播放中不遮挡。实测几何与判决写在 `Layout.caption_from_bottom` 旁。card / number / checklist / quiz 的主画面已经说过的话不再抄到底带，只有 figure 额外保留一行结论。`compose.py --selftest` 守的构图契约量的都是**渲染出来的画面**，不读版面函数——读函数就是门在测自己。四类版面的实测病都已修：竖屏 checklist 旧实现把行高死顶在 64 px，上空 385 / 下空 449、内容只占面板 21%；数字版面旧实现把大字中心钉在内容框 42% 处，整块偏上且偏移量随文案行数而变；split 旧实现从文字区顶部起排，横屏三行只占 22%、下部空 76%；quiz 旧实现把进度条钉在面板底，横屏中段空 53%、竖屏空 71%，修后面板贴内容走、选项块末项整步不再重复计入内容高（旧式多垫 ~91/~101 px 底空），进度条与末项圆圈净距 0.5 行。后两类的"居中"还要按 **墨迹**而不是 em 盒算——`anchor="mm"` 的锚点在 em 盒中心，而 190 px 中文粗体的墨迹心比它低 9 px，只按盒子居中"看起来仍偏低"；四组（number/split × 横/竖）实测偏离现已全部 ≤0.3%。
- **响度量最终文件**。旁白在的时候 BGM 从满电平 −14 dB 压到 −26 dB；混音原件不压缩，最终 AAC 统一衰减 0.8 dB。assemble 用 ffmpeg loudnorm 对**封装后的 MP4**量 EBU R128，要求 −18…−16 LUFS、true peak ≤ −1 dBTP；ep02 两个画幅实测均为 −17.31 LUFS / −1.16 dBTP / LRA 2.10 LU。
- **发布包从分镜与时间轴里长出来，不手抄**（`publish.py`）。一集三张封面——16:9（B 站、知乎、抖音横版）、3:4（小红书）、9:16（抖音竖版）——封面走独立皮肤 `cover_art.py`（只给封面用，PIL + numpy）：横向渐变暗蓝底（#071A24→#101826→#1B1924）+ 右侧青色径向光 + 左下方暖光 + 120 px 斜细线 + 暗角，亮度地板 ≥10；左侧文字栈是系列胶囊、琥珀集号徽章、双行标题（第一行 TXT、第二行青）、暖紫问句条（左青细杠，右侧「本集尺子」取该集最后一条 number beat 的 `big`，没有就不画；问句版这里写「答案在片尾」）、三个步骤 chips（navy 底青描边，上行白下行琥珀，chip 间琥珀箭头），左下弱化 CTA；右侧电池吉祥物（navy 电芯身、青描边、琥珀极柱与电量条、粉脸颊，`happy/thinking/guard` 三种表情按集指定）加对话气泡、四角星与背后低透明大集号。文案优先取 spec 新字段：`cover_title`（缺省回退 stage/hook）、`cover_question`（缺省回退首条 question beat）、`cover_chips`（缺省取前三个段名）、`cover_bubble`/`cover_mood`（缺省不生气泡）；四画幅按 zone 宽自动降字号（有下限），并与吉祥物/气泡矩形做碰撞检查。视频成片的皮肤三件套不变（见下一条）——封面是同一色系的更亮皮肤，不是另一套视觉语言。四平台标题/正文/话题由 spec 现算：章节时间点是 `spec.timeline()` 的**实测**起点（B 站/知乎按 `mm:ss 标题` 建章节），验收清单逐字来自 `spec.checklist`。平台的字数预算写在 `PLATFORMS` 常量里，以平台当期规则为准；超预算会截断并在 JSON 里标 `title_trimmed`/`body_trimmed`，不静默丢字。`--kit` 再把投稿页真正要的字段落成复制粘贴件：`publish/kit/<平台>/<集>.txt` 一集一份（标题、正文、话题、素材路径），B 站那份另写**分区候选**（科技 · 极客DIY / 知识 · 科学科普，明确标注未经投稿页核实——本轮 upos 上传阶段就失败、投稿表单没出现过，分区选择器没读到）与 10 个标签，分段章节单独成 `<集>-chapters.txt`——投稿页的章节是独立输入框，粘在简介里不算；章节时间与简介里那份同源（同一个 `ts()`），六集实测两处逐行一致。`--selftest` 同时量 kit：B 站标签必须是 10 个、章节文件行数等于段数、首行 00:00，另外**正文不许出现外链**——照投稿要求不写 GitHub，命中 `github`/`http` 即报红（封面只画标题/尺子/阶段，本来就不含链接）。平台边界按**实测**记：小红书发布页 2026-10-18 自己写着「支持时长 4 小时以内、最大 20GB 的视频文件」，六集 675–924 s / 30–44 MB 全在限内——上一轮引的「15 分钟上限」来自 2023 年第三方资料，已过时，`XHS_LIMIT` 常量与 selftest 都按页面测得的值来（超限才在 kit 里出「时长提醒」）。`--selftest` 量的是**渲染出来的封面**（最暗 64×64 块 ≥ 8 同黑帧门精神、全图块对比 ≥ 12、青+琥珀像素占比 1.5%–20%、徽章矩形内琥珀填充 ≥ 40%、标题/问句/chips 按像素宽放得下且标题不小于该画幅下限、文字 zone 与吉祥物/气泡矩形外扩 12 px 零相交，另校验字段格数：标题每行 ≤12、问题 ≤24、chip ≤10、气泡 ≤10）与文案侧（不超预算、章节首条 00:00 且严格递增、章节数 = 段数），量的是内存图，不读版面函数；meta 里的 `zones` 只给复量用。`--cover-variant q` 另出**问句版**（同名加 `-q`）：大字换成该集**开场那道题**（`cover_question`，缺省回退 `question` beat），徽章角上标 `Q`，问句条右侧写「答案在片尾」——小红书给这个号开了「封面PK」内测（笔记编辑页「PK封面」开关 + 最多 3 张备选，页面文案：72 小时后点击率最高的自动设为主封面），主封面 + 备选才是 A/B，一张图没得比，所以问句版就是备选；同一套皮肤、只换标题/徽章/问句条三处，四画幅 × 两变体逐张进 `--selftest`。
- **抖音切片按 beat 边界取段，不手填秒数**（`clip.py`）。跳过开场题与「答案片尾给」的铺垫 beat，从第一个内容 beat 起算；终点优先取 90 秒内最靠后的**段边界**，没有段边界就取最靠后的 beat 边界，保证 60–90 秒。起帧 `ceil(start×30)`、止帧 `round(end×30)`（排除边界帧，避免把下一段的淡入首帧带进来），成片帧数 = 止−起；音频按同一帧数截、末 0.3 s 淡出，片尾卡固定 4 s / 120 帧，封装后重新数帧、量时长与响度，不符即红。片尾卡的大集号水印画在 RGBA 层上再合成——RGB 图上 PIL 会忽略 alpha，半透明大字会变成纯白实心压住 CTA（封面改版时踩过同一个坑）。`--selftest` 对八集逐张验：取段 60–90 s、从 quiz 起算即红、标题 ≤30 字、正文 ≤1000 字且无外链、文字框不出安全区且不压水印、卡片均值亮度 ≥10。
- **动效词汇：缓动三条曲线，别的不要发明**（`docs/circuits/assets/*.svg` 的 SMIL）。2026-10-18 全库体检：150 张图、1600 个 `animate`，`keySplines` **一个都没有**——1433 个 linear（匀速机械）、167 个 discrete（硬切），而 1114 个动画盯的是 `opacity`（元素闪进闪出、没有运动）。观感粗糙的根在这一层，不在采样：Chromium `setCurrentTime` 逐帧钉住时间轴、30 fps、2× 超采样本来就是对的。规矩定成：非 discrete 的 animate 要么带 `keySplines`，要么显式 `data-ease="linear"`；三条曲线——进场 `0.16 1 0.3 1`（out）、退场 `0.7 0 0.84 0`（in）、位移/扫掠 `0.42 0 0.58 1`（in-out）；`opacity` 按「值变大用 out、变小用 in、保持不变用 in-out」**逐段**挑，所以「亮起—保持—淡出」这种三段高亮各自合适。时间轴上的匀速是**语义正确**的（图里沿横轴走的点代表时间在流），这类保留 linear 但必须自己声明 `data-ease="linear"`——默认不再是「随便」。硬切只留给真要断的地方（步进计数、状态切换），全库还剩 9 处 discrete 的几何量属于这类。这一轮 codemod 补齐 **1523 处缓动**、156 个 `opacity` 硬闪改淡入淡出、5 个 `animateTransform` 补曲线，并且**幂等**（第二次跑零改动；不幂等会把 `data-ease` 插两遍——属性重复直接坏 XML，本轮真踩过，所以校验里加了「重复属性 = 0」）。`spec.py --check` 新增这条硬契约：这集的图里有 animate 没交代时间曲线就报红，另有一条提示——整张图 ≥6 个 animate 却一个位移/变换都没有（＝只剩闪进闪出）。验证是同刻对照：同一张图改造前后在相同 `setCurrentTime` 上逐帧渲染比对，**静止态逐像素一致**（can-arbitration t=9.0 s 差 56 像素、最大差 3），差异只落在过渡窗口（t=3.0 s 那处高亮正在滑行）——缓动只改时间，不改几何。
- **图改过就必须重捕 clip**。clip 缓存键只有 图名/尺寸/帧率/主题，**不含内容**：改完 SMIL 若不复检，`capture.py` 会静默复用旧帧，看上去「动画没变」其实是缓存。现在 `ensure_clip` 比 mtime——图比 clip 新就重捕。同理，动效改完要重跑 `capture → compose → assemble` 才看得到效果，改了图只看文档站预览会以为没生效。
- **皮肤三件套：环境光、立层面板、光晕**（common.video_bg / compose._paint_panel / _num_glow）。帧背景不是平板 INK：内容区上方一盏峰值 +10 的蓝冷光 + 四角 0.86 暗角（守住 L≥9 黑帧门）；card/quiz/checklist 面板是纵向渐变 + 底缘软投影 + 顶缘 1px 灯，描边仍用 EDGE（selftest 面板扫描的锚）；number 大字背后一圈 alpha 30 的蓝色径向光。clip 画布是 flat INK，贴入用 2px 羽化蒙版融进带光的背景，硬贴会露一条 10/255 的暗框。精灵全部按画幅缓存，quiz/checklist 每帧只 paste 一次。第二盏极弱暖光（峰值 +5/+2）打在内容区右下角，双色调破单色；面板顶部 alpha 10 的 sheen；顶栏蓝分割线下一晕灯光（alpha 26→0）；全部文字走 _sh_text 画一层暗色偏移副本——字从面板浮起半层，是细腻度的最大来源。淡化/过场 alpha 曲线走 _ease（smoothstep）缓入缓出，线性起停生硬。并发纪律：一时刻最多两个重型任务——compose 双画幅并行可以，再叠第三个（assemble/audit）会把 ffmpeg 管道干死（OSError 22，moov 不写盘，且 `| tail` 会吞掉非零退出码装成成功）。
- **克制的电影感动效与字幕高亮**（`compose.py`）。文字按行错开 3 帧、8–14 帧内 alpha 0→1 并上浮 8 px（card / split / on-screen 结论共用；`p == 1` 时走原路径，逐字节等于旧渲染）；数字前 8 帧 0.94→1.0 punch-in、光晕同步淡入；图表 Ken Burns 4% 缓推、相邻 figure beat 交替 in/out（避免边界从 1.04 跳回 1.0），先裁再 LANCZOS 缩回目标框，不碰 clip 捕获与缓存；字幕前 5 帧 alpha 0→1、上浮 2 px；顶栏 5 px 蓝线改成轨道 + 青色进度填充（宽 = 进度 × 画幅）。字幕关键词高亮只处理底部字幕（figure 底带结论不重复着色）：数字/单位（`\d+(\.\d+)?` 加 V/A/Ah/%/°C 等，中文数词只认「数词 + 单位」，避免「一致」「一起」被误伤）用琥珀，术语白名单（AFE/MCU/SOC/热失控/安时积分…）用青；每行最多 2 段、数字优先、单段超行宽 60% 不着色；整行先画一次投影，再按 `font.getlength(prefix)` 从左到右分段画，字号/折行/宽度全部不变。字节复用加两条硬条件：静态 beat 必须 `p == 1 and cap_p == 1`，进度条按 600 桶分宽且桶不变——少一条就会把动画首帧复用成旧图或让进度条冻住。
- **过场与入场动效只叠一层**（`compose.py` / `audit.py`）。片头淡入、段间过场（6 帧）或内容交叉淡化（8 帧）发生时，PIL 文字揭示（card/number/split）整体压到 `p=1.0` 并**让满整个 REVEAL 窗**——只压过场那几帧，过场一结束 `p` 会从 1.0 跌回 `i/REVEAL_FRAMES`，已显形的行退回半透明再重放（ep01 旧片 8 个段边界实测内容区亮度回跌 2.3–13.0，帧 4663 是 30.9→27.1）；交叉淡化期间边淡边显形也会把跳变顶出 8 帧窗（ep04 帧 17014/7851 被判退化硬切）。`audit.py` 新增「过场后入场文字不得倒退」门：入场为 card/number 的段过场/交叉淡化边界，过场末帧后 7 帧内容区亮度跌幅 >1.5 即红；旧 ep01 成片跑新门 8 条红，重渲后全绿。

三个环境事实：`narrate` 默认走 edge-tts（在线神经语音），**断网时 `--engine sapi`** 用 Windows 离线语音兜底，音质降级但系列不断更；系统没有 ffmpeg 时回落到 imageio-ffmpeg 自带的那一个。Chromium 必须是 Playwright 那份（SMIL 动画只有它能忠实渲染），路径与版本按 `capture.py` 顶部的 `CHROMIUM` 找。

这套不进 CI，也不进本地门禁清单：它要网（TTS）、要 Playwright 的 Chromium、要几 GB 临时盘，而 runner 上一个都不占；本地门禁清单还要在 CI 与四处文档副本之间逐字对账，加一项就得同步五处，为一个本地工具改这份契约不划算。CI 今日守得住的是它的上游文本产物——口诀页逐字同步、社交卡三个数在 `check_docs.py` 里现算——这些都在；跑片这条链留在维护者机器上，由 `spec --check`、`compose --selftest`、`bgm --selftest`、`assemble --selftest` 四道窄门守，成片落地后另由 `audit --both` 全片审计量成品本身。出片后仍要人工过目每个 beat：`python tools/video/audit.py --episode <slug> --contact-sheet --both` 按中点抽帧拼审片格（横屏 4×5、竖屏 5×5，ep02 每画幅 74 beat 各 4/3 页），不能只挑几个漂亮画面截图——断行断在词中间、chroma bleed 色带这两类 defect 就是靠全量格图才发现的，它们 audit 全绿。
