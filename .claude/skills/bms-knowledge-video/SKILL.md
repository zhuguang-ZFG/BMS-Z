---
name: bms-knowledge-video
description: 把一个 BMS 知识点做成可发布的单问题短片，串起选题、事实台账、旁白、配音、现有 Python 出片、质检与发布包；适用于 tools/video/microcourses，不用于八集系统总课或无出处的泛科普。
---

# BMS 知识短片

一次只讲透一个问题，复用仓库现有 `tools/video/` 引擎。不要复制另一套渲染器，也不要先写满屏卡片再补旁白。

## 开始前

1. 读 `tools/video/microcourses/README.md`、对应阶段正文和同主题书章。
2. 若是新选题，先给 2–4 个候选；每个候选写清现场、贯穿输入、反直觉点和预计时长。
3. 视觉沿用 BMS-Z 的课本边角手绘：象牙纸、孔雀蓝、那不勒斯黄与赭石；技术曲线、标签和数字优先，装饰不能改变量义。
4. 需要完整步骤时读 [references/workflow.md](references/workflow.md)。需要核对借鉴来源时读 [references/provenance.md](references/provenance.md)。

## 三个确认点

- **确认 1：选题。** 用户确认问题、讲法、时长、画幅和基础／增强档。未确认前不写完整分镜。
- **确认 2：内容。** 用户确认 `FACTS.json`、旁白和逐拍分镜。未确认前不配音、不批量捕获、不调用任何付费生成服务。
- **确认 3：成片。** 用户看接触表或成片后再生成发布包。修改先落回分镜或事实台账，不直接修派生视频。

## 硬契约

- `FACTS.json` 是事实真源。数字、年份、阈值、专名、外部结论和教学示意都要有 ID；每个 beat 用 `facts` 引用。
- 教学数字写 `demo`，同时写明算式或仓库来源。它不能冒充手册参数。
- 原始资料优先；二手资料只作解释，社区资料只作线索。存在分歧时并列，不替读者选一个顺耳的版本。
- 旁白说因果，屏幕放对象、步骤、数字和出处。不要逐字搬运旁白。
- 默认使用仓库现有 30 fps 流水线，不宣称 60 fps。要升到 60 fps，先单独改引擎和审计阈值，再出样片。
- 外部图片、配音克隆、在线生图和付费服务都需要单独授权；没有授权时只用仓库已有 SVG、照片、代码图形和 SAPI 离线配音。

## 交付

至少保留这些可复算源文件：

- `mNN-*.STORYLINES.md`
- `mNN-*.SPEC.md`
- `mNN-*.FACTS.json`
- `mNN-*.json`

派生音频、帧和 MP4 留在 `media/`，不入库。结束前运行：

```powershell
python tools/video/spec.py --check <slug>
python tools/video/narrate.py --episode <slug> --engine sapi
python tools/video/capture.py --episode <slug>
python tools/video/compose.py --episode <slug> --both
python tools/video/assemble.py --episode <slug> --both
python tools/video/audit.py --episode <slug> --contact-sheet --both
python tools/video/publish.py --episode <slug> --selftest
```

只改文案或事实台账时，至少跑 `spec.py --check` 和相关 pytest。
