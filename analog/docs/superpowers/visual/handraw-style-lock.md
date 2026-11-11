# handraw-style 工具链锁定

- **上游**：https://github.com/yang0/handraw-style
- **锁定提交**：`572dff8f8cc1dc16ff9bef1422e90b3dfc42284d`（v1.9.8）
- **本地安装形态**：以 skill 包安装（含 `images/` 画廊与编号参考图）。安装根
  因机器而异，**项目文件与 CI 一律不写绝对路径**；需要核对时在安装根执行：

  ```bash
  git rev-parse HEAD          # 必须等于上面的锁定提交
  ls references               # styles.json / layouts.json / colors.json
  ```

  2026-11-04 验证：本地安装根 HEAD = `572dff8`，与锁定一致。
- **权威数据**：`styles_200_reorganized.md`（367 风格）、
  `skills/handdraw-style-prompter/references/layouts.json`（170 图型）、
  `references/colors.json`（36 主题色）。`*.json` 是生成索引，升级上游后
  须重跑上游 `build_library.py` / `build_layout_gallery.py` / `build_color_gallery.py`。
- **全库校验边界**：上游完整校验含与本项目无关的绝对路径条目，不作为 CI
  前提；本项目只校验**实际使用的条目存在**（见下）。
- **上游索引文件哈希**（2026-11-04 在锁定提交 `572dff8` 的安装根实测）：

  | 文件 | SHA-256 |
  |---|---|
  | `skills/handdraw-style-prompter/references/styles.json` | `5a33f46aba05531f8f024cb9df525374450a9670fcb4df311256d19882e603c0` |
  | `skills/handdraw-style-prompter/references/layouts.json` | `99ae44ec2baa8524f4cb1a763bf68e41edb823c8d63f0be234f9655fd067ceba` |
  | `skills/handraw-style-prompter/references/colors.json` | `bfad81e2635e50e38aa0671d308f56ad49f5b162b3e6198876ee2c949429d3ed` |

  升级上游后必须重跑三个 `build_*.py` 并更新本表；表内哈希与实际使用的
  条目共同构成可复现凭据。

## 已使用的条目

**2026-11-05 拍板**（见 `reviews/pilot-decision.md`）：全书主风格 = **FF-015 纸雕微距**，
全书色族换装为 **C-34 奶油白（纸）+ C-32 炭黑（墨）+ C-35 石板灰（纸层阴影）+ C-26 柿子橙（重点）**
——石板灰的角色由「纸」纠正为「阴影」，理由见下节实测。辅助风格**仍空**——原推荐
「FF-015 限定 V1/V6 每章 1–2 张」的前提是主风格为 FA-029，主风格改为 FF-015 后该答案失效。
换装前 FA-029 仍是既有 61 张静态图与 157 个动画登记条目的现役皮肤，因此下表按
「现役 / 已拍板 / 未采纳」分列，不是一刀替换。

| 类别 | ID | 用途 |
|---|---|---|
| 风格 | FF-015 Paper Sculpture Illustration | **已拍板：全书主风格**（2026-11-05）。V3/V5 定量与流程点位须先通过「层高不编码数值 + 16K 灰度对照」验证才可进入波次 |
| 风格 | FA-029 Geometric Diagrammatic Narrative | **现役**：既有 61 静态图 + 157 动画条目的皮肤，换装（Task 11）前的默认；试片候选 A，25 分制得 20 |
| 风格 | FH-043 Vintage Risograph and Silkscreen Print Illustration | 试片候选 B，得 16，**未采纳**（器件语义漂移 + 蓝↔红灰度同灰） |
| 图型 | IG-002 / IG-004 / IG-008 / IG-009 / IG-011 / IG-012 / IG-014 / IG-015 / IG-019 / IG-024 / IG-026 / IG-027 / IG-028 / IG-032 / IG-033 | 按信息结构选择，见规格 §5.3 |
| 色彩 | C-34 奶油白（纸） / C-32 炭黑（墨） / C-35 石板灰（纸层阴影） / C-26 柿子橙（重点） | **已拍板：全书新色族**（2026-11-05）。石板灰只做阴影，不做纸底 |
| 色彩 | C-30 象牙白（纸） / C-31 佩恩灰（墨） / C-29 赭石（重点） | **现役**基础纸墨，换装完成前仍是正文与旧资产的落地色 |
| 色彩 | C-03 普鲁士蓝 / C-21 珊瑚粉 | 试片候选 B 的限色套印，随 B 未采纳，不入全书 |

## 16K 灰度印刷闸（2026-11-05 实测）

拍板时把 C-35 石板灰标成了「纸」，实测证明该角色不成立，已纠正为「纸层阴影」。
色值不手抄，由 `scripts/make_grayscale_fixture.py` 从上游色卡取中位像素；
「16K 打印」近似为 BT.601 灰度 + 5 档量化。实测对比度：

| 色族 | 纸↔墨 | 纸↔阴影 | 纸↔重点 | 墨↔重点 | 阴影↔重点 | 判定 |
|---|---|---|---|---|---|---|
| 已拍板（C-34/C-32/C-35/C-26） | **10.42:1** | 5.45:1 | **4.40:1** | 2.37:1 | 1.24:1 | PASS |
| 石板灰当纸底（上一题字面写法） | 1.91:1 | 1.00:1 | 1.24:1 | 2.37:1 | 1.24:1 | **FAIL** |
| 现行全书（C-30/C-31/C-29） | 8.36:1 | 8.36:1 | 6.90:1 | 1.21:1 | 1.21:1 | PASS |

闸值：`MIN_PAPER_INK_RATIO = 4.0`、`MIN_PAPER_ACCENT_RATIO = 3.0`，由
`scripts/test_grayscale_fixture.py` 4 项锁定（上游未安装时自动跳过）。

由数字得出的两条硬规则，任何 V3/V5 定量与流程图都必须遵守：

1. **柿子橙不得压在石板灰层上**（1.24:1，灰度下等于隐形）；重点色只能落在纸白区。
2. **重点色与墨线只有 2.37:1**，够做单点强调、不够做多曲线分类——多条曲线必须靠
   线宽/虚实/形状区分，不得只靠颜色。附带收益：新色族的墨↔重点（2.37:1）优于现行
   色族（1.21:1），换装在这一点上确实提高了灰度可读性。

复跑：`make visual-gray`（或 `python scripts/make_grayscale_fixture.py --check`），
产物在 `reviews/palette-2026-11-05/`。

每一项视觉资产在 `visual-manifest.yml` 登记 `style_id` / `layout_id` /
`color_ids`；新增 ID 必须先确认存在于上游索引，禁止发明。

## 底图与生成边界（本项目实测约束）

**当前执行路径（2026-11-05 用户调整）**：用户明确允许“自己用 Python 实现插图的绘制”。
三张风险试片已由 `build_papercut_pilot.py` 生成完整纸层矢量图，保留无文字 `base_svg`
与独立技术图层，沿用 FF-015 的纸层语言和已选色族。外部生图服务不再是执行前置。
产物已接入 ch17，记录 `generator: python-svg-papercut-v1`；详见
`reviews/python-papercut-2026-11-05/review.md`。这是 Python 矢量插画，不冒称 AI 生图或真实微距摄影。
以下 11-04 试片与 API 排查记录保留作历史追溯。

**2026-11-04 更正**：此前本节写作「本环境没有可调用的生图模型」，已被 ch17
试片证伪——本机图像生成工具（`generator: imagegen-tool`）可用，FA-029 /
FH-043 / FF-015 三套方向各出了 hero / chart / compare 共 9 张无文字底图，
落在 `reviews/pilot-2026-11-04/`。上游能力判定按库基线模型 `gpt-image-2`
解析，三套候选均判定为**不需垫图**。

但生成边界没有因此放松，规格 §3.3 的硬规则依旧成立：公式、器件参数、引脚名、
波形坐标与中文正文**一律由确定性 SVG/HTML 图层绘制，不交给生图模型**；生图
只产出无文字底图，判读句与数值由 overlay 补。因此两条生产路径当前状态不同：

- **试片路径（本轮，可用）**：生图底图 → `reviews/pilot-2026-11-04/`，
  仅供接触表打分，**不进正文**；overlay 尚未叠加，见 `pilot-decision.md`。
- **正式路径（2026-11-05 管线已接通，等待新底图复评）**：`compose_technical_overlay.py`
  输出底图内嵌的合成 SVG、无位图的 `-print.svg` 与 WebP/灰度预览。三张技术校样在
  `reviews/quant-pilot-2026-11-05/`；当前会话无内置生图工具且未配置 API Key，
  这些校样没有新纸雕底图、没有人工评分，也没有进入正文。已发布静态图仍使用既有资产。

V2 正式图现在可落 `assets/figures-v2/`：字体子集扫描已覆盖该目录，静态图测试和
manifest 磁盘覆盖闸也已接入。书构建按 manifest 选择纯矢量印刷回退，缺回退或
未审图的 V2 静态图会失败。`assets/figures/` 保留已有图以便逐张迁移。

每条 prompt 记录都按上游双语提示词格式落盘（`prompts/<id>.md`）；
`generator` 字段区分来源——确定性 SVG 记 `deterministic-svg-v1`，
生图底图记 `imagegen-tool`，两者受同一套 hard 规则约束。

## 提示词记录契约

`docs/superpowers/visual/prompts/<id>.md`，YAML front matter：

```yaml
---
id: ch17-cause-frequency
generator: deterministic-svg-v1   # 或外部模型名（接入生图后）
reference_policy: none            # none | upstream-relative-path
numbers: ["41%", "23%", "18%", "9%", "6%", "3%"]
zh_prompt: |
  风格名称：几何图式叙事。主题色：象牙白（Ivory）。
  ……画面主题与必须出现的数值……
en_prompt: |
  Style name: Geometric Diagrammatic Narrative. Theme color: Ivory.
  ……
---
```

硬规则（`scripts/check_visual_manifest.py` 强制）：

- `numbers` 里的普通字符串必须能在 `source_facts` 指向的正文小节中找到；
- 示意值须逐项注明 value/label/reason，图内可见文字必须含“示意”；SVG 可见数字也独立扫描；
- 上游相对图路（参考图）只允许记录相对路径与锁定提交，不允许绝对路径；
- 无 prompt 记录的资产不得进入正文。
