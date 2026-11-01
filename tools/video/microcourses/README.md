# BMS 核心问题微课

微课不是把八集总课随便截短，而是重新围绕一个问题编排：一个现场、一个贯穿输入、一张逐步生长的图和一次取回练习。总课负责全景，微课负责讲透。

## 目录约定

- `mNN-*.STORYLINES.md`：三种真正不同的故事线，推荐方案排第一。
- `mNN-*.SPEC.md`：数字化导演规格，明确目标、画面、运动、禁用默认和 QA 帧。
- `mNN-*.FACTS.json`：逐条事实、教学示意与出处；每个 beat 用 `facts` 指回这里。
- `mNN-*.json`：现有 Python 出片流水线读取的唯一分镜真源。

微课 JSON 写 `"kind": "microcourse"`。`spec.py` 仍检查它使用的动画必须来自 `stage_doc`，但不会强迫一条微课把该阶段所有动画全部塞进去。主系列 JSON 默认 `kind=series`，继续执行“阶段动画必须完整覆盖”的旧契约。

## 七段流程与三次确认

项目内的 Claude Code skill 在 [`.claude/skills/bms-knowledge-video/SKILL.md`](../../../.claude/skills/bms-knowledge-video/SKILL.md)。它把一条微课拆成选题、查证、写稿、配音、代码成片、质检和发布包；中间停三次：先定问题与时长，再审事实／旁白／分镜，最后看成片后才出发布包。

这层流程参考了 MIT 项目 `andyhuo520/vibe-knowledge` 的单知识点工作流（审阅提交 `c3a13a85f7cc560e5d396f063baecea4b2748e1e`），但没有复制 cine、MiMo、Renoise 或 OCR 引擎。BMS-Z 继续使用自己的 SVG 与 Python 出片链；吸收的是事实台账、确认点和“发布前量成品”的做法。

## 第一条样板

`m01-load-voltage-drop` 回答“满电一拧把为什么掉两格”：

- 同一个 20 A 输入贯穿全片；
- 20 mΩ 得到 0.40 V，低温教学值 120 mΩ 得到 2.40 V；
- 撤载回弹用来区分端电压变化与 SOC 瞬时变化；
- 只使用阶段 0 已有的 `internal-resistance.svg` 与 `rint-arrhenius.svg`。

检查与离线出片：

```powershell
python tools/video/spec.py --check m01-load-voltage-drop
python tools/video/narrate.py --episode m01-load-voltage-drop --engine sapi
python tools/video/capture.py --episode m01-load-voltage-drop
python tools/video/compose.py --episode m01-load-voltage-drop --both
python tools/video/assemble.py --episode m01-load-voltage-drop --both
python tools/video/audit.py --episode m01-load-voltage-drop --contact-sheet --both
```

在线 MiMo 配音先运行 `python tools/video/set_mimo_key.py`，再把旁白命令换成：

```powershell
python tools/video/narrate.py --episode m03-protection-line --engine mimo
```

先用 `python tools/video/narrate.py --probe-mimo` 生成 `.local/mimo-probe.wav`，确认鉴权与内置音色。密钥只落 `.local/mimo.env`（已忽略），不得写进分镜、文档或 shell 命令。断网时继续用 `--engine sapi`。

成片和中间产物仍落在 `media/`，不入库；JSON、故事线与导演规格入库。

## 第二条样板

`m02-ocv-trust` 回答“电压什么时候能当 SOC 的尺子”：

- 同一个刚撤流样本从 3.450 V、3.490 V 走向 3.620 V；
- 3.660 V 充电支只用来说明滞回不会靠等待消失；
- 结尾固定复答四道资格门：电流、变化率、温度、历史；
- LFP 平台用 `5 mV → 约 6.7 pp` 说明参考合格不等于信息充足。

## 第三条样板

`m03-protection-line` 回答“保护点为什么不是危险点”：

- 同一条证据链分开正常充电截止、保护动作线与化学边界；
- tick 46 首次越线、tick 48 发命令、tick 49 反馈归零，三拍不互相冒充；
- 20 ms、3 拍、2 ms、15 ms 复算 57/77 ms 与 23 ms 余量；
- 用短路硬件快路径作反例，避免把连续确认讲成所有故障的固定规则。
