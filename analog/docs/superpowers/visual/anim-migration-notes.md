# 动画气质迁移备忘（SVG → 纸墨手绘）

> Task 11（气质批迁移）与 Task 11b（扩量）共用本备忘。铁律：`assets/svg/*.svg` 是 `scripts/generate_svgs.py` 的产物，**禁止手改产物、禁止只改 SVG 不回灌脚本**。

## 改什么

- **外壳**：所有气质改动只经 `scripts/handraw.py` 的既有入口（`apply` / `retint` / `bow_lines` / `title_decor`）落到生成器输出上；纸纹、线型、色板迁到 FA-029 纸墨。
- **caption 字符串**：与新口诀冲突的节拍字幕，只改 `scripts/generate_svgs.py` 里的 caption 文本，与重写后 docs 口径一致。
- **标题装饰**：`title_decor` 的楷体标题栈按 `HANDRAW-STYLE.md` 核对，缺字走字体子集流程。

## 不改什么

- **教学数值**：电路参数常量（电阻/电容/电压/频率）不改；要改必须 docs 同步改且有出处。
- **封装与电流路径语义**：封装轮廓、引脚号、电流走向箭头的物理含义不动。
- **SMIL 时序语义**：教学节拍（先充后放、先开后关）不动；只许调外壳观感。
- **产物直改**：一律改脚本 → `python scripts/generate_svgs.py` 重生。
- **reduced-motion**：不在 SVG 内写 media query 回退；无障碍回退归站点层管（既有 `test_reduced_motion.py` 口径）。

## 回归闸

```bash
python scripts/generate_svgs.py
python -B -m unittest discover -s scripts -p 'test_svg_assets.py' -v
python -B -m unittest discover -s scripts -p 'test_a11y.py' -v
# 有浏览器环境时再跑：
python -B -m unittest discover -s scripts -p 'test_svg_contrast.py' -v
```

迁移与扩量分开验收（Task 11 / Task 11b），避免「气质改动」与「数量达标」互相糊弄。
