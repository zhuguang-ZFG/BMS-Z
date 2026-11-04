# handraw 扩面 runbook（阶段 0 → 7）

> 用途：第一批 20 张过门后，按同一流水线扩面；本 runbook 不要求一次跑完全库。
> 合同：`docs/visual-style-pack.md` + `docs/superpowers/specs/2026-11-04-handraw-visual-overhaul-design.md`。

## 基线快照（2026-11-04）

| 项 | 数量 |
|----|------|
| `docs/circuits/assets/*.svg`（未 handraw 化） | 167 |
| `docs/circuits/assets/archive/*.svg` | 0 |
| `bms-book/assets/*.svg` | 56（`hppc-pulse.svg` 属第一批，归档到 `bms-book/assets/archive/`） |
| 第一批登记 | 20（`docs/circuits/handraw/manifest.json`） |

## 1. 列未迁移清单

```powershell
Get-ChildItem docs/circuits/assets -Filter *.svg |
  Where-Object { -not (Test-Path (Join-Path 'docs/circuits/assets/archive' $_.Name)) } |
  Select-Object -ExpandProperty Name
```

先剔除已在 `manifest.json` 登记的 slug，剩余即未迁移集合。

## 2. 按阶段分批（0 → 7）

1. 用 `rg -l "<slug>\.svg" docs/stages` 找到引用该图的阶段页，读文件名前缀得到 `stage_no`。
2. 每批 **≤20 条**，同一阶段优先、同一 KP 相邻的图放同一批，便于统一观察题措辞。
3. 每批先写清单（slug + source_svg + kp_id + 画风），再进流水线；不要边写边扩。

## 3. 单条流水线

1. **抽因果**：读源 SVG 的 `<text>` / `<title>`，写 3–8 步「什么在变」。数字只用源图已有值并保留「示意」。
2. **prompt**：按 `docs/visual-style-pack.md` 模板写 `docs/circuits/handraw/prompts/<slug>.md`；FA-002 机制 / FA-029 信息结构。
3. **（需授权）出帧**：仅当用户明确说「出图」后渲染 `storyboard/<slug>/frame-01.webp …`；3–8 帧。
4. **export**：`python tools/export_handraw_animation.py` 生成 `exports/<slug>.webp` 与 `-start` / `-end` 静态帧。
5. **换链**：正文图片路径改指 exports，补观察题，图注写「原理示意 / 非实拍」；不得双源并存。
6. **archive**：旧 SVG 移到 `archive/`（`hppc-pulse` 走 `bms-book/assets/archive/`），不留 stub。
7. **manifest**：`frames`、`export`、`caption_ok`、`bans_ok`、`status` 同步（`rendered` → `exported` → `linked` → `archived`）。

## 4. 门禁命令

```powershell
python tools/check_handraw_manifest.py
python -m pytest bms-book/tests/test_handraw_manifest.py -q --basetemp=.tmp-pytest-hw -p no:cacheprovider
# 抽检（Task 5 落地后）
python -m pytest bms-book/tests/test_handraw_spotcheck.py -q --basetemp=.tmp-pytest-hw -p no:cacheprovider
```

任一条 FAIL：不得标完成，先进缺口表。

## 5. 失败进缺口表（`docs/视觉缺口表.md`）

行模板：

```markdown
| <日期> | <页面 / slug> | <现象：如「帧 3 出现卡通电芯脸」> | <结论：退回重出 / 降级为静态 / 待授权> |
```

## 6. 授权边界

- **未说「出图」只交 prompts**：不渲染、不调用图像生成、不提交位图。
- 已授权出图也不得把静态帧伪装成 SMIL 动画；导出物必须可暂停、首末帧可单独阅读。
- 本 runbook 不覆盖「全库 167 张一次跑完」——按批次推进，每批过门后再开下一批。
