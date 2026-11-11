# 手绘纸墨视觉规范

本文件是**视觉层**的唯一规范：108 张原理动画（`assets/svg/`）、在线站点外壳、
16K 印刷内文都以它为准。写作、标记、编号规则见 `STYLE.md`；本文件只管
「长什么样」，不管「写什么」。

## 1 选型与依据

| 维度 | 选择 | 为什么 |
|---|---|---|
| 画风 | **FA-029 Geometric Diagrammatic Narrative** | 几何精密线条 + 信息图式留白 + 克制色彩。原理图最怕「画得像插画」，FA-029 的手绘感来自线条与留白，不靠夸张涂鸦，元件符号该直的地方仍然直 |
| 纸 | **C-30 象牙白** `#fdf8ea` | 比纯白暖一档，长时间读不刺眼；印刷时同等网点下比冷白更接近书纸 |
| 墨 | **C-31 佩恩灰** `#16202b` | 近黑但带蓝灰，比纯黑 `#000` 柔和；与纸的对比 15.5:1，远超 3:1 门槛 |
| 标记 | **C-29 赭石** `#a4630f` | 标题下的马克笔线、章号、`h3` 前的点。暖色只用来「指路」，不用来填充 |

深色模式不是另画一套图，而是同一组 token 换第二档值（`scripts/handraw.py`
里每个 token 都是 `(浅色, 深色)` 二元组）：纸 → 焦墨 `#141310`，墨 → 米白
`#ece4d3`，语义色各自提亮。

## 2 不用抖线滤镜

常见「手绘滤镜」是 `feTurbulence` + `feDisplacementMap`。这里**不用**：

- 108 张图、每张几百个图元、绝大多数还带 SMIL 动画，逐元素滤镜会让移动端
  掉到个位数帧率；印刷管线 `book/svg_refine.py` 还会再处理一遍，滤镜一旦
  被展开成位图就不可逆。
- 手绘感改由四件低成本的东西承载：**几何微弯**（`bow_lines()`：把长直线换成
  一条幅度 `min(1.5, 长度×0.0045)` 的二次曲线，短于 14px 不弯）、**纸纹**
  （一张 12px 的平铺纹理）、**楷体标题 + 赭石马克笔划线**、**纸墨配色**。

## 3 token 表

中性色（明 / 暗）：

| token | 浅色 | 深色 | 用途 |
|---|---|---|---|
| `paper` | `#fdf8ea` | `#141310` | 画布 |
| `paper2` | `#f6eedb` | `#1d1a14` | 卡片、面板底 |
| `edge` | `#e0d3b8` | `#3b3529` | 纸边、分隔线 |
| `rule` | `#c9bb9d` | `#4a4436` | 网格、坐标轴发丝线 |
| `ink` | `#16202b` | `#ece4d3` | 正文与主线条 |
| `ink2` | `#37424e` | `#cfc6b4` | 次级文字 |
| `muted` | `#5b666f` | `#a79e8b` | 弱化文字（图注、单位） |
| `faint` | `#8b8272` | `#857c6c` | 装饰性文字 |

语义色每个都有 **四档**，因为同一个色要同时当「字」「块」「线」：

| 族 | 浅色（文字/线） | 深色·文字 | 深色·色块 | 深色·描边 | 淡染（浅/深） |
|---|---|---|---|---|---|
| blue | `#1f5d7a` | `#7fb7cf` | `#2b4d5f` | `#6fa3b9` | `#e6eff3` / `#17262e` |
| sky | `#2f7f96` | `#8ac9d8` | `#2b5660` | `#77b2c1` | `#e4f1f3` / `#15262a` |
| green | `#3d6b4a` | `#98c096` | `#2f4a33` | `#7aa87c` | `#e8efe6` / `#182418` |
| red | `#a8321f` | `#e0907a` | `#55231b` | `#c07a63` | `#f6e7e1` / `#281a16` |
| amber | `#a4630f` | `#dcab63` | `#553a17` | `#c08a45` | `#f7eedb` / `#292114` |
| purple | `#6b3f63` | `#c4a2bf` | `#452c40` | `#a17c9b` | `#efe8ee` / `#241c22` |

**分工是硬规则**：`<text>` 用深档文字色；形状 `fill` 用淡染；`stroke` 用深档。
只有一个深色值会出现「深底上字看不见」或「浅底上色块糊成一片」——两种坏法
各自都验证过。

实测对比度（对 `paper` / 对深色 `paper`）：ink 15.52 / 14.69、muted 5.54 / 6.99、
faint 3.58 / 4.51、blue 6.81 / 8.47、green 5.82 / 9.13、red 6.30 / 7.47、
amber 4.53 / 8.89、purple 7.87 / 8.20。

## 4 字体

- 标题与卡片标签：`"KaiTi", "STKaiti", "Kaiti SC", "LXGW WenKai", "Hand Serif", "Noto Serif SC", serif`，
  **`font-weight: 400`**。楷体没有真粗体，加粗走的是合成的假粗，笔画会糊成
  黑体观感，手写笔锋全丢。
- 正文：正文栈不动（屏幕用系统 UI 字体）。手写体只做「标题承担风格」，正文
  保证可读性与中西文混排行高。
- **楷体不能当唯一依赖**：Linux/Android 上没有 KaiTi，整栈掉到通用 `serif` 后
  CJK 字形一个都不画——CI 实测顶栏标题是整块纯底色（几何框还在，颜色计算还全部
  "合规"）。站点因此随包发 Noto Serif SC 子集（`assets/fonts/`，两档字重 685 KB）
  作为 `Hand Serif`；SVG 内的栈补 `Noto Serif CJK SC / Source Han Serif SC /
  Songti SC / SimSun`，这些机器上至少落到系统衬线而不是空白。
- **正文标签是另一套栈**：`SANS_FONT` 管 108 张图里 11~13px 的标签，它同样只能
  写系统字体名（`<img>` 载入的 SVG 吃不到页面 `@font-face`），所以也补了
  `Noto Sans CJK SC / Source Han Sans SC / Noto Sans SC`。改任何一套栈后都要重生成
  SVG 并跑 `test_svg_layout`（它按渲染文本框量压字，缺字形的机器上量的是方框）。
- **子集范围要覆盖「站内独有字」**：`book/fonts.py::required_text()` 除 docs 与
  book 源码，还扫根目录 Markdown、`scripts/build_site.py` 与 `scripts/site_media/*`。
  只扫 docs 会漏掉 CONTRIBUTING 等页面与硬写的 UI 文案（实测 5 个字落在子集外），
  而覆盖率护栏本身只校验 `required_text()`，漏掉的字它查不出来。
- SVG 内部的字体栈写在 `<style>` 里；标题的手写体用 **inline `style`** 覆盖，
  否则会被 `text{font-family:…}` 的组选择器压掉。

## 5 形状与装饰

- **不等圆角**：卡片四角半径故意不同（站点 `--hand-radius: 14px 11px 15px 10px`），
  像随手画的框；等半径是"软件画的"，不等半径才是"手画的"。
- **马克笔划线**：标题下方一条赭石色、两端略收的粗线；如果标题带居中副标题
  （`y ∈ [31,65)`），划线会压住副标题，此时自动跳过。
- **纸纹**：一张内联 SVG 噪声平铺（横向 12px 级），不请求外部资源；站点上铺在
  `body` 的 `background-image`，不能用 `z-index:-1` 的伪元素（会被 body 自己的
  底色盖住，屏幕上看不到颗粒）。
- **描边-only 形状必须 `fill="none"`**：`<line>` 转成 `<path>` 后默认填充黑色，
  会在拐角漏出 1px 黑月牙；印刷管线去掉滤镜后尤其明显（`stroke_only()` 一次性
  补齐 1593 处）。
- **颜色只做装饰，不做文字**：首页「四层难度阶梯」原本用四种品牌色当 `h3` 文字色，
  明色下余量只剩 4.4，深色下因为卡片底色是「浅纸混深底」掉到 3.2。现在 `h3` 一律
  墨色，层次靠四条不同颜色的**虚线顶带**表达 —— 装饰可以低对比，文字不行。
- **卡片底色要按主题显式给**：`--hand-paper-2`（`#f7efdd`）在 slate 下没有覆盖，
  `color-mix(浅纸 62%, 深底)` 会算出**中灰**，浅字压上去只有 3.2:1。深色模式下
  这些卡片必须整体换成深纸 `#1e1b16` + 浅墨字，而不是继续混色。
- **装饰线别压进文字的行框**：虚线顶带贴在卡片顶端 0.38rem 处时会落进 `h3` 的
  行框，截图取样「离底色最远的像素」先取到赭石带，对比度被误判成 4.4。卡片
  `padding-top` 要让开带子高度（本规范取 1rem）。

## 6 正例 / 反例

| 正 | 反 | 原因 |
|---|---|---|
| 直线带宽 1.5–2px，转角微弯 | 每条线加 `filter="url(#roughen)"` | 108 张图 × SMIL，滤镜会拖垮帧率 |
| 色块用 `*_t` 淡染 | 色块直接用 `#1f5d7a` | 深块压住墨色文字，读不出来 |
| 深色模式换 token 第二档 | 深色模式再导出一套 `<style>` | 两套规则必然分叉 |
| 标题楷体 400 | 楷体 + `font-weight:800` | 合成假粗，失去手写笔锋 |
| 圆角 `14px 11px 15px 10px` | 统一 `border-radius:12px` | 等半径是软件感 |

## 7 落地位置与校验

| 位置 | 内容 |
|---|---|
| `scripts/handraw.py` | 唯一 token 源：调色板、`retint()`、`bow_lines()`、`stroke_only()`、`token_css()`、`svg_defs()`、`title_decor()` |
| `scripts/generate_svgs.py` | 唯一图源；`save()` 末尾调用 `handraw.apply()` |
| `scripts/site_media/handraw.css` | 站点外壳：纸底/纸纹、墨边、楷体标题、手绘圆角、19 种提示卡配色 |
| `analog-book/styles/print.css` | 16K 内文（纸色/墨色/赭石标记/虚线分隔） |
| `analog-book/styles/book.css` | A4 1.0 遗留管线（Phase 5 删除） |

校验（任何视觉改动都要跑）：

```
python -B -m unittest discover -s scripts -p "test_svg_contrast.py" -v   # 明暗双模逐字测对比度
python -B -m unittest discover -s scripts -p "test_svg_assets.py" -v     # 调色板残留
python -B -m unittest discover -s scripts -p "test_curriculum.py" -v     # 章首块与接线
python scripts/build_site.py --build                                     # 站点
python analog-book/build_print_book.py --check                           # 16K 内文
```

`test_svg_contrast.py` 是硬护栏：它在 Chromium 里量**每一个** `<text>` 的实际
渲染色，明暗两套都量，任一低于 3:1 直接失败。改配色后不要靠肉眼判断。

## 8 这轮改到的护栏（待评审）

视觉换皮会碰到一批「钉住旧配色/旧取样方式」的断言。逐条列出改法，评审时按
「改的是测量方式还是削弱了门槛」来判：

| 测试 | 原断言 | 现断言 | 判定 |
|---|---|---|---|
| `scripts/test_svg_assets.py` | 临时目录里只有生成器 | 额外拷 `handraw.py` | 生成器新增依赖，不改判据 |
| `scripts/test_noise_budget.py` | `CURVES` 写死十六进制 | 取 `handraw.LIGHT["green"/"red"]` | 单一 token 源，判据不变 |
| `scripts/test_waveform_timing.py` | 同上 | `handraw.LIGHT["blue"/…]` | 同上 |
| `scripts/test_learning_interactions.py` | 选 `circle[r="4.2"][fill="#2563eb"]` | 选 `circle.cursor-dot`（生成器新增 class） | 位置判据不变，去掉调色板耦合 |
| `scripts/test_first_screen.py`（logo） | 数「接近白色」的像素 | 数「偏离众数底色」的像素 | 顶栏由深底改纸底，原口径会量到 0.69 背景 |
| `analog-book/tests/test_book_sample.py` | 钉 `--navy: #14213d` 等五个字面值 | 解析 token 并断言墨/灰/赭对纸底 ≥12/4.5/4.5 | 换成对比度下限，比字面值更严 |
| `analog-book/tests/test_book_fonts.py` | `assertNotIn("http", css)` 查远程字体 | 只查 `url(http`/`@import` | 子集重切后 base64 载荷里偶然出现 `http`，原断言变成误报；判据仍是「无远程字体源」 |
| `analog-book/tests/test_wave1_chapters.py` | ch11 表题数 `tables: 5` | `tables: 6` | ch11 实际有 6 张表，此前 2 张无表注、3 张表号跳号（11-3…11-5）；补注后表格数与表题数同为 6，契约改为钉真实数量 |
| `analog-book/tests/test_wave1_chapters.py` | ch14 `tables: 6`、ch16 `tables: 6` | `11` / `12` | 两章分别有 11 / 12 张表，旧契约只数到已有表注；补注后按真实表数钉住（ch14 顺移 6→11、ch16 6→12） |
