"""16K 十页样张：证明版心、镜像边距回退与完整视觉系统。"""
from __future__ import annotations

import html
import json
from pathlib import Path

from . import config
from .fonts import font_css

SAMPLE_SECTIONS = ["篇首页样张", "章首页样张", "正文样张", "插图样张",
                   "表格样张", "代码样张", "公式样张", "脚注样张",
                   "目录样张", "索引样张"]

MM = 72 / 25.4
TEXT_WIDTH_LIMIT_MM = 145.5
SIZE_TOLERANCE_MM = 0.5


class SampleError(RuntimeError):
    """样张没有达到 16K 版式门槛。"""


def inspect_sample(pdf_path):
    """测量页面尺寸与每页文字块的左右边界（mm）。"""
    import fitz

    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        size = (page.rect.width / MM, page.rect.height / MM)
        sections = []
        for pno, page in enumerate(doc):
            blocks = [b for b in page.get_text("blocks") if b[4].strip()]
            xs0 = min(b[0] for b in blocks) / MM
            xs1 = max(b[2] for b in blocks) / MM
            sections.append({"page": pno + 1, "left": round(xs0, 2),
                             "right": round(xs1, 2),
                             "width": round(xs1 - xs0, 2)})
        mirrored = abs(sections[1]["left"] - sections[2]["left"]) > 2.0
        report = {
            "page_size_mm": [round(x, 2) for x in size],
            "text_width_mm": max(s["width"] for s in sections),
            "margins_mm": {"top": 20, "bottom": 22},
            "mirrored": mirrored,
            "fallback": "mirrored" if mirrored else "uniform-20mm",
            "sections": sections,
        }
    finally:
        doc.close()
    return report


def build_sample(out_dir, fonts_dir=config.FONTS_DIR, browser_override=None):
    """生成 sample.html / sample.pdf / sample-report.json。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    html_path = out / config.SAMPLE_HTML_NAME
    pdf_path = out / config.SAMPLE_PDF_NAME
    report_path = out / config.SAMPLE_REPORT_NAME
    html_path.write_text(sample_html(font_css(fonts_dir)), encoding="utf-8")
    _print_pdf(html_path, pdf_path, browser_override)
    report = inspect_sample(pdf_path)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    width, height = report["page_size_mm"]
    if (abs(width - config.TRIM_WIDTH_MM) > SIZE_TOLERANCE_MM
            or abs(height - config.TRIM_HEIGHT_MM) > SIZE_TOLERANCE_MM):
        raise SampleError(f"样张页面不是 16K：{width}×{height} mm")
    if report["text_width_mm"] > TEXT_WIDTH_LIMIT_MM:
        raise SampleError(
            f"样张版心 {report['text_width_mm']} mm 超过 "
            f"{TEXT_WIDTH_LIMIT_MM} mm")
    return html_path, pdf_path, report


def _print_pdf(html_path, pdf_path, browser_override=None):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise SampleError(
            "样张 PDF 需要 Playwright：pip install -r analog-book/requirements.txt"
        ) from exc
    launch = {"headless": True}
    if browser_override:
        executable = Path(browser_override).expanduser()
        if not executable.is_file():
            raise SampleError(f"浏览器不存在: {browser_override}")
        launch["executable_path"] = str(executable)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**launch)
        try:
            page = browser.new_page()
            page.set_default_timeout(180000)
            page.goto(Path(html_path).resolve().as_uri(), wait_until="load")
            page.evaluate(
                "async () => { if (document.fonts) await document.fonts.ready; }")
            page.pdf(path=str(pdf_path), print_background=True,
                     prefer_css_page_size=True)
        finally:
            browser.close()


def sample_html(fonts_css, manifest=None):
    """返回内联字体与 print.css 的独立十页样张 HTML。"""
    print_css = (config.STYLES_DIR / "print.css").read_text(encoding="utf-8")
    metadata = manifest or {}
    title = str(metadata.get("title") or "通往模拟电路之路")
    author = str(metadata.get("author") or "zhuguang-ZFG 与贡献者")
    sections = "\n".join([
        _part_section(),
        _chapter_section(),
        _body_section(),
        _figure_section(),
        _table_section(),
        _code_section(),
        _formula_section(),
        _footnote_section(),
        _toc_section(),
        _index_section(),
    ])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="author" content="{html.escape(author)}">
<title>{html.escape(title)} · 16K 样张</title>
<style>
{fonts_css}
</style>
<style>
{print_css}
</style>
</head>
<body>
<main class="book">
<div class="md-typeset">
{sections}
</div>
</main>
</body>
</html>
"""


def _part_section():
    def ladder_row(level, title, detail):
        return (f'<div class="ladder-row"><span class="lnode"></span>'
                f'<span class="lv">{level}</span>'
                f'<div class="ladder-text"><strong>{title}</strong>'
                f'<span>{detail}</span></div></div>')

    ladder = "".join((
        ladder_row("L1", "物理", "PN 结 · 沟道"),
        ladder_row("L2", "器件", "二极管 · BJT · MOS"),
        ladder_row("L3", "电路", "运放 · 比较器 · 基准"),
        ladder_row("L4", "系统", "电源 · 定时 · 信号链"),
    ))
    units = "".join(
        f'<li><span class="chno">CH 0{index}</span>'
        f'<span class="chtitle">{title}</span></li>'
        for index, title in enumerate((
            "无源元件：寄生参数的主场",
            "二极管：单向导电与三种模型",
            "稳压与基准：从齐纳到带隙",
        ), start=1))
    units_b = "".join(
        f'<li><span class="chno">CH 0{index}</span>'
        f'<span class="chtitle">{title}</span></li>'
        for index, title in enumerate((
            "BJT：电流控制的放大与开关",
            "MOSFET：电压控制与沟道",
            "输出级：推挽、开漏与上下拉",
        ), start=4))
    return f"""
<section class="book-page" id="sample-part">
  <div class="part-hero">
    <div class="part-hero-top">
      <span>PART SAMPLE / 样张篇</span>
      <span class="sample-id">篇首页样张</span>
    </div>
    <div class="part-hero-main">
      <div>
        <p class="part-kicker">从物理到系统</p>
        <h1 class="part-title">器件与模型</h1>
        <p class="part-sub">电阻 · 电容 · 电感<br>二极管 · BJT · MOSFET</p>
      </div>
      <div class="part-art">
        <div class="ladder">{ladder}</div>
      </div>
    </div>
    <div class="part-hero-foot"><span>6 章 · 2 个单元</span><span>从物理到系统</span></div>
  </div>

  <p class="part-intro"><strong>这一篇把器件放回设计链：</strong>先看物理，再看参数，最后看它在电路里如何失效。每一章都从一张剖面、一条特性曲线或一个失效案例开始，回到可以计算的模型。</p>

  <div class="part-units">
    <div>
      <p class="unit-label">1A · 无源与二极管</p>
      <ul class="unit-list">{units}</ul>
    </div>
    <div>
      <p class="unit-label">1B · 三极管与场效应管</p>
      <ul class="unit-list">{units_b}</ul>
    </div>
  </div>

  <aside class="book-callout book-callout-gem">
    <p class="callout-label">怎么读这一篇</p>
    <p>先通读 L1–L2，建立器件直觉；再用 L3 的电路把参数串起来；最后用 L4 的系统案例检验模型边界。每章末的“模型边界”提示，是从公式回到现实的入口。</p>
  </aside>

  <div class="part-epigraph">
    <p class="epi-label">篇首语 / BEFORE YOU BEGIN</p>
    <p>“器件不是理想元件，而是有脾气的东西。读数据手册，就是读它们的脾气。”</p>
    <cite>—— 本书导读</cite>
  </div>
</section>
"""


def _chapter_section():
    goals = "".join(
        f"<li>{item}</li>" for item in (
            "说出 1 kΩ 电阻从哪个频率开始“不再是电阻”；",
            "用戴维南等效算出分压器带载后的真实输出；",
            "判断 ESR 与 ESL 谁在目标频段说了算。",
        ))
    plans = "".join(
        f'<li><span class="plan-no">{no}</span>'
        f'<span class="plan-title">{title}</span>'
        f'<span class="plan-page">{page}</span></li>'
        for no, title, page in (
            ("1.1", "真实电阻的等效模型", "P.012 · 3 个算例"),
            ("1.2", "真实电容：ESR 与 ESL", "P.018 · 阻抗曲线"),
            ("1.3", "真实电感与自谐振", "P.024 · 选型清单"),
        ))
    return f"""
<section class="book-page" id="sample-chapter">
  <div class="opener-top">
    <span class="part-tag"><i></i>第一部分 · 器件与模型</span>
    <span class="chapter-tag"><b>01</b>CHAPTER / 19
      <span class="sample-id">章首页样张</span></span>
  </div>

  <div class="opener-hero">
    <div>
      <p class="eyebrow">第 1 章 · 无源元件</p>
      <h1 class="opener-title">无源元件的<br><span>真实面目</span></h1>
      <p class="deck">理想元件并不存在。理解寄生参数，是区分“会背公式的人”和“能设计电路的人”的第一道门槛。本章从电阻、电容、电感三件无源元件出发，把数据手册上的数字还原成可以计算的模型。</p>
    </div>
    <figure class="opener-art">
      <span class="corner tl"></span><span class="corner tr"></span>
      <span class="corner bl"></span><span class="corner br"></span>
      <div class="plot">
        <svg viewBox="0 0 320 250" role="img" aria-label="示意图：真实电阻的阻抗随频率变化，低频平坦，经过拐点后下降，在谐振谷底后重新上升">
          <defs>
            <pattern id="sample-grid-a" width="16" height="16" patternUnits="userSpaceOnUse">
              <path d="M16 0H0V16" fill="none" stroke="#e4e7ec" stroke-width="0.6"/>
            </pattern>
            <marker id="sample-arrow-a" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
              <path d="M0 0L7 3.5L0 7Z" fill="#14213d"/>
            </marker>
          </defs>
          <rect x="8" y="8" width="304" height="226" fill="url(#sample-grid-a)"/>
          <path d="M30 22 V222 H306" fill="none" stroke="#14213d" stroke-width="1.5" marker-end="url(#sample-arrow-a)"/>
          <path d="M30 120 H262" fill="none" stroke="#98a2b3" stroke-width="1.2" stroke-dasharray="4 4"/>
          <text x="36" y="113" font-family="Book Mono, monospace" font-size="10.5" fill="#98a2b3">IDEAL R</text>
          <path d="M30 120 H150 C185 120 196 200 222 200 C250 200 276 72 302 60"
                fill="none" stroke="#0f766e" stroke-width="2.4"/>
          <path d="M150 120 V222" fill="none" stroke="#0f766e" stroke-width="0.9" stroke-dasharray="3 3"/>
          <text x="143" y="238" font-family="Book Mono, monospace" font-size="10.5" fill="#0f766e">f1</text>
          <circle cx="222" cy="200" r="3.4" fill="#b45309"/>
          <path d="M225 201 L246 214" fill="none" stroke="#b45309" stroke-width="0.8"/>
          <text x="248" y="218" font-family="Book Sans, sans-serif" font-size="10.5" fill="#b45309">Z<tspan dy="3" font-size="7">min</tspan></text>
          <text x="160" y="160" font-family="Book Sans, sans-serif" font-size="10.5" fill="#b45309" transform="rotate(-28 160 160)">−20 dB/dec</text>
          <text x="14" y="34" font-family="Book Mono, monospace" font-size="12" fill="#14213d">|Z|</text>
          <text x="292" y="242" font-family="Book Mono, monospace" font-size="12" fill="#14213d">f</text>
          <text x="44" y="240" font-family="Book Mono, monospace" font-size="9" fill="#52606d">100M</text>
          <text x="140" y="240" font-family="Book Mono, monospace" font-size="9" fill="#52606d">1G</text>
          <text x="238" y="240" font-family="Book Mono, monospace" font-size="9" fill="#52606d">10G</text>
          <path d="M60 222 V217 M140 222 V217 M238 222 V217" stroke="#14213d" stroke-width="0.8"/>
        </svg>
      </div>
      <div class="art-foot"><span>FIG. 1-1 · 示意</span><span>Z(f) · 1 kΩ</span></div>
    </figure>
  </div>

  <div class="stat-strip"><span>3 节</span><span>1 个算例</span><span>3 个模型边界</span></div>

  <aside class="book-callout book-callout-goal">
    <p class="callout-label">学完你应能</p>
    <ul>{goals}</ul>
  </aside>

  <blockquote><p><strong>先修：</strong>第 0 章的水路比喻。本章告诉你“水池也会漏、水管也有惯性”——这就是寄生参数。</p></blockquote>

  <div class="chapter-plan">
    <p class="plan-label"><span>本章路线</span><span class="en">IN THIS CHAPTER</span></p>
    <ol>{plans}</ol>
  </div>
</section>
"""


def _body_section():
    return """
<section class="book-page body-page" id="sample-body">
  <div class="runline">
    <span class="sq"></span><span>第 2 章 · 小信号模型</span>
    <span class="rule"></span><span class="folio">P.018</span>
  </div>

  <h2><span class="secno">2.1</span>正文样张：小信号增益的三条路</h2>

  <p class="lead">同一个共源放大器，可以从三条路算出同一个电压增益：画负载线、列节点方程，或者直接套用小信号模型。三条路得到的表达式必须一致，这是检查代数错误最便宜的办法。</p>

  <p>先用大信号负载线确定工作点，再把工作点附近的斜率读成跨导。只要信号幅度远小于热电压，这条切线就足够准确；一旦摆幅逼近电源轨，负载线本身开始弯曲，小信号模型也就失效了。</p>

  <h3>2.1.1 三条路的适用边界</h3>
  <ul>
    <li><strong>负载线：</strong>看直流工作点与输出摆幅，最直观。</li>
    <li><strong>节点方程：</strong>适合多管级联，便于交给仿真器。</li>
    <li><strong>小信号模型：</strong>手算增益与阻抗，速度最快。</li>
  </ul>

  <blockquote><p>经验法则：先画工作点，再谈增益。工作点错了，增益公式再漂亮也没有意义。</p></blockquote>

  <aside class="book-callout book-callout-calc">
    <p class="callout-label">算一笔</p>
    <p>若 <em>g</em><sub>m</sub> = 2 mS、<em>R</em><sub>D</sub> = 10 kΩ、<em>r</em><sub>o</sub> = 100 kΩ，则 <em>A</em><sub>v</sub> ≈ −2 mS × (10 kΩ ∥ 100 kΩ) ≈ −18.2。把 <em>R</em><sub>D</sub> 换成 1 kΩ，增益掉到约 −2，但带宽会按比例变宽。</p>
  </aside>

  <aside class="book-callout book-callout-limit">
    <p class="callout-label">模型边界</p>
    <p>以上忽略体效应、栅极电阻与封装寄生。频率超过 <em>f</em><sub>T</sub>/10 时，单极点模型不再够用，必须把 <em>C</em><sub>gd</sub> 的米勒反馈拆成输入、输出两个结点分别计算。</p>
  </aside>

  <figure class="equation-strip">
    <div class="eq-head"><span class="n">式 2-1</span><span>增益与特征频率 · GAIN &amp; f<sub>T</sub></span></div>
    <p class="eq-line"><i>A</i><sub>v</sub><span class="upr"> = −</span><i>g</i><sub>m</sub><span class="upr">(</span><i>R</i><sub>D</sub><span class="upr"> ∥ </span><i>r</i><sub>o</sub><span class="upr">)　　</span><i>f</i><sub>T</sub><span class="upr"> ≈ </span><i>g</i><sub>m</sub><span class="upr"> / (2π(</span><i>C</i><sub>gs</sub><span class="upr"> + </span><i>C</i><sub>gd</sub><span class="upr">))</span></p>
    <figcaption>增益由跨导与输出电阻共同决定；特征频率只看跨导与输入电容。</figcaption>
  </figure>
</section>
"""


def _figure_section():
    return """
<section class="book-page body-page" id="sample-figure">
  <div class="runline">
    <span class="sq"></span><span>第 11 章 · 放大电路拓扑</span>
    <span class="rule"></span><span class="folio">P.247</span>
  </div>

  <h2><span class="secno">11.1</span>插图样张：共源级的读图顺序</h2>

  <p><strong>问题：</strong>同一张原理图，为什么有人三秒看出增益，有人十分钟还在找地线？读图不是认符号，而是沿三条线走一遍。</p>

  <figure class="book-figure figure-panel">
    <span class="corner tl"></span><span class="corner tr"></span>
    <span class="corner bl"></span><span class="corner br"></span>
    <div class="panel-labels"><span>FIG. 11-1</span><span class="panel-note">作者重绘 / SCHEMATIC</span></div>
    <div class="plot">
      <svg viewBox="0 0 560 280" role="img" aria-label="共射放大器：VCC 经 RC 接集电极，基极经 RB 偏置并串入耦合电容 C1，发射极接地">
        <g fill="none" stroke="#14213d" stroke-width="2">
          <path d="M120 34 H430"/>
          <path d="M330 34 V48 L322 56 L338 64 L322 72 L338 80 L322 88 L330 96 V120"/>
          <path d="M240 34 V48 L232 56 L248 64 L232 72 L248 80 L232 88 L240 96 V158"/>
          <path d="M330 120 H470"/>
          <path d="M330 120 V134 L304 150"/>
          <path d="M304 168 L330 186 V214"/>
          <path d="M239 158 H300"/>
          <path d="M205 158 H214 M221 158 H240"/>
          <path d="M214 143 V173 M221 143 V173" stroke-width="2.6"/>
          <path d="M160 158 H175"/>
          <path d="M190 173 V214"/>
          <path d="M120 214 H350"/>
        </g>
        <g fill="none" stroke="#14213d" stroke-width="3.4">
          <path d="M300 128 V186"/>
        </g>
        <circle cx="190" cy="158" r="15" fill="none" stroke="#14213d" stroke-width="2"/>
        <path d="M182 158 Q186 148 190 158 T198 158" fill="none" stroke="#14213d" stroke-width="1.6"/>
        <g stroke="#14213d" stroke-width="2">
          <path d="M262 214 V224 M252 224 H272 M256 230 H268 M260 236 H264"/>
        </g>
        <path d="M313 169 L325 181 L311 184 Z" fill="#14213d"/>
        <g fill="#0f766e">
          <circle cx="240" cy="34" r="4"/>
          <circle cx="330" cy="34" r="4"/>
          <circle cx="330" cy="120" r="4"/>
          <circle cx="240" cy="158" r="4"/>
          <circle cx="190" cy="214" r="4"/>
        </g>
        <g fill="#14213d" font-family="Book Sans, sans-serif" font-size="15">
          <text x="275" y="24" text-anchor="middle">V<tspan dy="5" font-size="11">CC</tspan></text>
          <text x="346" y="76">R<tspan dy="5" font-size="11">C</tspan></text>
          <text x="226" y="76" text-anchor="end">R<tspan dy="5" font-size="11">B</tspan></text>
          <text x="217" y="136" text-anchor="middle">C<tspan dy="5" font-size="11">1</tspan></text>
          <text x="154" y="163" text-anchor="end">v<tspan dy="5" font-size="11">in</tspan></text>
          <text x="482" y="126">v<tspan dy="5" font-size="11">out</tspan></text>
          <text x="346" y="176">Q<tspan dy="5" font-size="11">1</tspan></text>
          <text x="262" y="252" text-anchor="middle" font-size="12">GND</text>
        </g>
      </svg>
    </div>
    <figcaption class="figure-caption">
      <span class="fno">图 11-1</span>
      <span>共射放大器：偏置网络与信号通路（示意图）</span>
    </figcaption>
  </figure>

  <div class="reading-notes">
    <p class="rn-label"><span>判读要点</span><span class="en">HOW TO READ · 3 STEPS</span></p>
    <div class="rn-grid">
      <div class="rn-item">
        <span class="rn-no">01</span>
        <div><strong>先找公共端</strong><p>交流接地的那一极，决定组态的名字与性格。</p></div>
      </div>
      <div class="rn-item">
        <span class="rn-no">02</span>
        <div><strong>再看增益符号</strong><p>共射反相，共集同相且略小于 1，共基同相。</p></div>
      </div>
      <div class="rn-item">
        <span class="rn-no">03</span>
        <div><strong>最后看阻抗</strong><p>输入与输出阻抗，决定它该放在信号链的哪一级。</p></div>
      </div>
    </div>
  </div>

  <div class="selection-deck">
    <p class="sel-label"><span>三条读图路径</span><span>READING PATHS</span></p>
    <div class="sel-grid">
      <div class="sel-card">
        <span class="sel-name">直流路径</span>
        <span class="sel-spec">VCC → RC → C-E → GND</span>
        <p>先算静态电流，确认管子工作在放大区。</p>
      </div>
      <div class="sel-card">
        <span class="sel-name">交流路径</span>
        <span class="sel-spec">vin → C1 → B → C → vout</span>
        <p>耦合电容短路、电源接地，再看信号往哪走。</p>
      </div>
      <div class="sel-card">
        <span class="sel-name">失效路径</span>
        <span class="sel-spec">开路 / 短路 / 饱和</span>
        <p>假设每个元件失效一次，输出会怎样变化。</p>
      </div>
    </div>
  </div>
</section>
"""


TABLE_ROWS = (
    ("电阻", "R = V/I", "串联 L、并联 C", "1/(2πRC)", "0.1–1 GHz", "高频用贴片"),
    ("电容", "C = Q/V", "ESR、ESL", "1/(2π√LC)", "1–100 MHz", "去耦看 ESR"),
    ("电感", "L = Φ/I", "绕组电容、DCR", "1/(2π√LC)", "1–50 MHz", "防止磁饱和"),
    ("二极管", "指数 I–V", "结电容、反向恢复", "1/(2πRCj)", "pF 与 ns", "开关损耗"),
    ("BJT", "β 视为常数", "Cπ、Cμ、rbb'", "gm/(2πCπ)", "0.1–10 GHz", "核对 fT"),
    ("MOS", "平方律", "Cgs、Cgd、Cdb", "gm/(2πCgs)", "1–100 GHz", "沟长调制"),
    ("运放", "增益无穷大", "输入电容、输出阻抗", "GBW", "1–100 MHz", "看相位裕度"),
    ("基准", "零温漂", "噪声、PSRR", "—", "ppm/°C", "长期漂移"),
)
TABLE_HEADER = ("元件", "理想模型", "主要寄生", "拐点频率", "典型量级", "设计提醒")


def _table_section():
    head = "".join(f"<th>{cell}</th>" for cell in TABLE_HEADER)
    body = "".join(
        "<tr>" + "".join(
            f"<td><strong>{cell}</strong></td>" if index == 0 else f"<td>{cell}</td>"
            for index, cell in enumerate(row)) + "</tr>"
        for row in TABLE_ROWS)
    return f"""
<section class="book-page body-page" id="sample-table">
  <div class="runline">
    <span class="sq"></span><span>第 11 章 · 元件的模型边界</span>
    <span class="rule"></span><span class="folio">P.254</span>
  </div>

  <h2><span class="secno">11.2</span>表格样张：元件的理想模型与寄生</h2>

  <p>表 11-1 把常用元件的理想模型、主要寄生和失效拐点放在同一张六列表里。阅读时先横向比较同一列的典型量级，再回到具体元件核对设计提醒。</p>

  <figure class="book-table">
    <figcaption class="table-caption">
      <span class="tno">表 11-1</span>
      <span>常用元件的理想模型与主要寄生（样张数据）</span>
    </figcaption>
    <table>
      <colgroup>
        <col style="width:12%"><col style="width:15%"><col style="width:22%">
        <col style="width:19%"><col style="width:14%"><col style="width:18%">
      </colgroup>
      <thead><tr>{head}</tr></thead>
      <tbody>{body}</tbody>
    </table>
  </figure>

  <aside class="book-callout book-callout-gem">
    <p class="callout-label">读表方法</p>
    <p>先看“主要寄生”一列，找到最可能在目标频段夺权的参数；再用“拐点频率”估算它何时生效；最后回到数据手册核对封装与偏压。</p>
  </aside>

  <p>注意：拐点频率一列只是数量级提示，实际值取决于封装、偏压和温度。任何一张表都不能替代数据手册，但它能告诉你应该先翻到手册的哪一页。</p>

  <aside class="book-callout book-callout-calc">
    <p class="callout-label">数量级速算</p>
    <p>拐点频率先记 <em>1/(2π)</em> ≈ 0.159：1 kΩ × 1 pF → 159 MHz，1 kΩ × 1 μF → 159 Hz；1 μH × 1 pF 也落在 159 MHz 附近。同样数量级，一个是 RC 拐点，一个是 LC 谐振，失效机制并不相同。</p>
  </aside>
</section>
"""


CODE_LINES = (
    "* CS amplifier: 1.8 V, 65 nm, gain and bandwidth",
    ".param vsup=1.8 vbias=0.65",
    "VDD  vdd 0 {vsup}",
    "VIN  in  0 dc {vbias} ac 1",
    "RD   vdd out 2k",
    "M1   out in 0 0 nmos W=10u L=65n",
    ".model nmos nmos level=1 vto=0.45 kp=200u lambda=0.05",
    ".op",
    ".ac dec 10 1 1G",
    ".tran 1n 20u",
    ".meas ac gain max vdb(out)",
    ".end",
)


def _code_section():
    code = html.escape("\n".join(CODE_LINES))
    return f"""
<section class="book-page body-page" id="sample-code">
  <div class="runline">
    <span class="sq"></span><span>第 12 章 · 从手算到仿真</span>
    <span class="rule"></span><span class="folio">P.266</span>
  </div>

  <h2><span class="secno">12.1</span>代码样张：共源级的 SPICE 网表</h2>

  <p>网表按“标题行、参数、电源、器件、分析、结束”的顺序组织。每一行都以元件名开头，续行用 <code>+</code>，注释用 <code>*</code>——这些规则在所有 SPICE 方言里都一样。</p>

  <figure class="book-figure">
    <pre><code>{code}</code></pre>
    <figcaption class="figure-caption">
      <span class="fno">清单 12-1</span>
      <span>共源放大器的 ngspice 网表（12 行）</span>
    </figcaption>
  </figure>

  <p>运行后用 <code>meas</code> 语句直接读出增益。注意 <code>vdb(out)</code> 给出的是 dB 值：先除以 20 再取 10 的幂，才得到 |<em>A</em><sub>v</sub>|；若与手算的 <em>g</em><sub>m</sub>·(<em>R</em><sub>D</sub> ∥ <em>r</em><sub>o</sub>) 相差超过 20%，先检查模型参数的单位，再检查工作点是否落在饱和区。</p>

  <aside class="book-callout book-callout-calc">
    <p class="callout-label">手算对照</p>
    <p>按 level=1 模型：<em>V</em><sub>OV</sub> = 0.20 V，<em>I</em><sub>D</sub> ≈ 0.62 mA，<em>V</em><sub>DS</sub> ≈ 0.57 V；<em>g</em><sub>m</sub> ≈ 6.2 mS，<em>r</em><sub>o</sub> ≈ 32.5 kΩ，故 |<em>A</em><sub>v</sub>| ≈ 11.6（忽略 <em>r</em><sub>o</sub> 约 12.3）。这组数字应与 <code>.op</code> 和 <code>.ac</code> 的输出同量级；若相差很远，先回查偏置。</p>
  </aside>

  <div class="reading-notes">
    <p class="rn-label"><span>网表三查</span><span class="en">BEFORE YOU RUN</span></p>
    <div class="rn-grid">
      <div class="rn-item">
        <span class="rn-no">01</span>
        <div><strong>查单位</strong><p>u、n、meg 大小写敏感，1meg 不是 1m。</p></div>
      </div>
      <div class="rn-item">
        <span class="rn-no">02</span>
        <div><strong>查模型</strong><p>level=1 只适合练手，真实设计要换成工艺模型卡。</p></div>
      </div>
      <div class="rn-item">
        <span class="rn-no">03</span>
        <div><strong>查工作点</strong><p>先看 .op 的 Vds 与 Vgs，确认管子真的在饱和区。</p></div>
      </div>
    </div>
  </div>
</section>
"""


def _formula_section():
    return """
<section class="book-page body-page" id="sample-formula">
  <div class="runline">
    <span class="sq"></span><span>第 12 章 · 小信号参数</span>
    <span class="rule"></span><span class="folio">P.271</span>
  </div>

  <h2><span class="secno">12.2</span>公式样张：增益、输出电阻与特征频率</h2>

  <p>公式用本地内联 SVG 排版，不依赖 MathJax 初始化。下面的共源级增益同时写出“电导形式”与“电阻形式”，两者只差一个倒数关系。</p>

  <figure class="book-figure equation-strip">
    <div class="eq-head"><span class="n">式 12-1</span><span>小信号参数 · SMALL-SIGNAL</span></div>
    <div class="eq-body">
      <div class="arithmatex">
        <svg viewBox="0 0 560 150" width="140mm" role="img" aria-label="共源级小信号增益、输出电阻与特征频率公式">
          <g fill="#14213d" font-family="Book Serif, serif" font-size="21">
            <text x="280" y="40" text-anchor="middle">
              <tspan font-style="italic">A</tspan><tspan dy="7" font-size="14">v</tspan><tspan dy="-7"> = −</tspan><tspan font-style="italic">g</tspan><tspan dy="7" font-size="14">m</tspan><tspan dy="-7"> (</tspan><tspan font-style="italic">R</tspan><tspan dy="7" font-size="14">D</tspan><tspan dy="-7"> ∥ </tspan><tspan font-style="italic">r</tspan><tspan dy="7" font-size="14">o</tspan><tspan dy="-7">)</tspan>
            </text>
            <text x="280" y="92" text-anchor="middle">
              <tspan font-style="italic">R</tspan><tspan dy="7" font-size="14">out</tspan><tspan dy="-7"> = </tspan><tspan font-style="italic">R</tspan><tspan dy="7" font-size="14">D</tspan><tspan dy="-7"> ∥ </tspan><tspan font-style="italic">r</tspan><tspan dy="7" font-size="14">o</tspan><tspan dy="-7"> ≈ </tspan><tspan font-style="italic">R</tspan><tspan dy="7" font-size="14">D</tspan>
            </text>
            <text x="280" y="136" text-anchor="middle">
              <tspan font-style="italic">f</tspan><tspan dy="7" font-size="14">T</tspan><tspan dy="-7"> ≈ </tspan><tspan font-style="italic">g</tspan><tspan dy="7" font-size="14">m</tspan><tspan dy="-7"> / (2π(</tspan><tspan font-style="italic">C</tspan><tspan dy="7" font-size="14">gs</tspan><tspan dy="-7"> + </tspan><tspan font-style="italic">C</tspan><tspan dy="7" font-size="14">gd</tspan><tspan dy="-7">))</tspan>
            </text>
          </g>
        </svg>
      </div>
    </div>
    <figcaption>式 12-1　共源级的小信号增益、输出电阻与特征频率</figcaption>
  </figure>

  <ul>
    <li><em>g</em><sub>m</sub>：工作点处的跨导，单位 A/V；</li>
    <li><em>R</em><sub>D</sub>：漏极负载电阻，单位 Ω；</li>
    <li><em>r</em><sub>o</sub>：沟道长度调制引入的输出电阻。</li>
  </ul>

  <p>当 <em>r</em><sub>o</sub> ≫ <em>R</em><sub>D</sub> 时，输出电阻近似等于 <em>R</em><sub>D</sub>，增益化简为 <em>A</em><sub>v</sub> ≈ −<em>g</em><sub>m</sub>·<em>R</em><sub>D</sub>。若 <em>R</em><sub>D</sub> 换成电流源负载，<em>r</em><sub>o</sub> 就不能再被忽略——这也是电流源负载增益更高的原因。</p>

  <div class="book-reveal">
    <p class="book-reveal-title">展开推导</p>
    <p>在漏极节点列 KCL：<em>g</em><sub>m</sub><em>v</em><sub>in</sub> + <em>v</em><sub>out</sub>/<em>R</em><sub>D</sub> + <em>v</em><sub>out</sub>/<em>r</em><sub>o</sub> = 0，两边同乘 <em>R</em><sub>D</sub>·<em>r</em><sub>o</sub> 即得 <em>v</em><sub>out</sub>/<em>v</em><sub>in</sub> = −<em>g</em><sub>m</sub>(<em>R</em><sub>D</sub> ∥ <em>r</em><sub>o</sub>)。</p>
  </div>

  <p>做一次纯代数练习：若 <em>g</em><sub>m</sub> = 6.2 mS、<em>C</em><sub>gs</sub> + <em>C</em><sub>gd</sub> = 25 fF，则 <em>f</em><sub>T</sub> ≈ 39.5 GHz。这个数值只用于核对单位与数量级，不代表任何具体工艺。</p>

  <aside class="book-callout book-callout-limit">
    <p class="callout-label">量纲自检</p>
    <p><em>g</em><sub>m</sub>/<em>C</em> 的单位是 (A/V)/F = 1/s，所以 <em>ω</em><sub>T</sub> = <em>g</em><sub>m</sub>/(<em>C</em><sub>gs</sub> + <em>C</em><sub>gd</sub>) 是角频率；少除以 2π 会把 <em>f</em><sub>T</sub> 高估 6.28 倍。先写 <em>ω</em><sub>T</sub>，再写 <em>f</em><sub>T</sub>，可以避免这类错误。</p>
  </aside>
</section>
"""


def _footnote_section():
    return """
<section class="book-page body-page" id="sample-footnote">
  <div class="runline">
    <span class="sq"></span><span>第 13 章 · 精度与噪声</span>
    <span class="rule"></span><span class="folio">P.284</span>
  </div>

  <h2><span class="secno">13.1</span>脚注样张：章末注释与上标</h2>

  <p>正文里的上标数字指向页末或章末的注释，读者不必翻到全书末尾。<sup>1</sup> 本书把短注释排在章末，把数据来源与延伸阅读放到书末的参考文献。<sup>2</sup></p>

  <p>注释的编号以章为单位重新开始，避免出现四位数页码式的编号。<sup>3</sup> 同一页出现多个注释时，按正文出现顺序排列，并与正文中的上标一一对应。</p>

  <h3>关于样张数据的说明</h3>
  <p>本页的数值用于演示版式，不代表任何具体工艺。<sup>4</sup> 需要复现实验时，请以对应章节给出的网表和模型卡为准。</p>

  <aside class="book-callout book-callout-gem">
    <p class="callout-label">排版约定</p>
    <p>短注释排章末，数据来源与延伸阅读放书末参考文献；上标只标一次，同一页重复引用沿用原编号。注释编号与参考文献编号互不干扰。</p>
  </aside>

  <figure class="book-table">
    <figcaption class="table-caption">
      <span class="tno">表 13-1</span>
      <span>注释、来源与延伸阅读的分工</span>
    </figcaption>
    <table>
      <colgroup><col style="width:22%"><col style="width:32%"><col style="width:46%"></colgroup>
      <thead><tr><th>内容</th><th>位置</th><th>适合放什么</th></tr></thead>
      <tbody>
        <tr><td><strong>短注释</strong></td><td>章末注释</td><td>推导跳步、术语解释、同一页放不下的补充</td></tr>
        <tr><td><strong>数据来源</strong></td><td>书末参考文献</td><td>手册编号、论文、数据表版本与访问日期</td></tr>
        <tr><td><strong>延伸阅读</strong></td><td>书末资源页</td><td>教材章节、应用笔记与可复现的实验工程</td></tr>
      </tbody>
    </table>
  </figure>

  <aside class="book-endnotes">
    <h2>注释</h2>
    <ol>
      <li>上标与注释之间的对应关系由排版阶段自动生成，样张使用固定编号。</li>
      <li>参考文献按作者排序，中文文献按拼音排序。</li>
      <li>章末注释与书末参考文献使用两套独立编号，互不干扰。</li>
      <li>样张中的 65 nm、1.8 V 等参数仅用于演示，不构成设计建议。</li>
    </ol>
  </aside>
</section>
"""


TOC_ROWS = (
    (1, "第一部分　器件与模型", "1"),
    (2, "第 1 章　无源元件的真实面目", "3"),
    (3, "1.1　真实电阻的等效模型", "3"),
    (3, "1.2　真实电容：ESR 与 ESL", "5"),
    (2, "第 2 章　二极管的三种面孔", "9"),
    (3, "2.1　PN 结的电容", "9"),
    (1, "第二部分　放大与反馈", "15"),
    (2, "第 3 章　共源级", "17"),
    (3, "3.1　小信号模型", "17"),
    (3, "3.2　增益与带宽", "20"),
    (2, "第 4 章　差分对", "24"),
    (3, "4.1　尾电流源", "24"),
    (1, "第三部分　频率与稳定性", "31"),
    (2, "第 5 章　极点与零点", "33"),
    (3, "5.1　米勒近似", "33"),
    (3, "5.2　相位裕度", "36"),
    (2, "第 6 章　反馈网络", "40"),
    (3, "6.1　环路增益", "40"),
    (1, "第四部分　噪声与精度", "47"),
    (2, "第 7 章　噪声入门", "49"),
    (3, "7.1　热噪声", "49"),
    (3, "7.2　闪烁噪声", "52"),
    (2, "第 8 章　失调与温漂", "56"),
    (3, "8.1　斩波稳零", "56"),
    (1, "第五部分　从电路到芯片", "63"),
    (2, "第 9 章　版图与寄生", "65"),
    (3, "9.1　匹配与失配", "65"),
    (3, "9.2　衬底耦合", "68"),
    (2, "第 10 章　基准与电源", "72"),
    (3, "10.1　带隙基准", "72"),
    (3, "10.2　LDO 与 PSRR", "76"),
    (1, "附录 A　公式速查", "81"),
)


def _toc_section():
    rows = "".join(
        f'<li class="toc-row toc-level-{level}"><a href="#">'
        f'<span class="toc-title">{title}</span>'
        f'<span class="toc-dots"></span>'
        f'<span class="toc-page">{page}</span></a></li>'
        for level, title, page in TOC_ROWS)
    return f"""
<section class="book-page" id="sample-toc">
  <div class="book-toc">
    <p class="toc-kicker">CONTENTS / 全书结构</p>
    <h1>目录样张</h1>
    <ul class="book-toc-list">
{rows}
    </ul>
    <div class="reading-notes">
      <p class="rn-label"><span>三种查法</span><span class="en">HOW TO NAVIGATE</span></p>
      <div class="rn-grid">
        <div class="rn-item">
          <span class="rn-no">01</span>
          <div><strong>顺序读</strong><p>从第一篇顺读，先建立器件直觉，再进入放大与反馈。</p></div>
        </div>
        <div class="rn-item">
          <span class="rn-no">02</span>
          <div><strong>按主题查</strong><p>用目录定位章节，用索引回查正文里解释过的术语。</p></div>
        </div>
        <div class="rn-item">
          <span class="rn-no">03</span>
          <div><strong>按公式查</strong><p>先翻附录 A 的公式速查，再回到推导所在章节核对假设。</p></div>
        </div>
      </div>
    </div>
    <p>页码为样张合成数据，仅用于检查双栏目录的对齐与分页；黑体一级条目对应全书五篇与附录。</p>
  </div>
</section>
"""


INDEX_TERMS = (
    "BJT", "CMOS", "ESR", "ESL", "GBW", "MOS", "PSRR", "Q 值", "SPICE",
    "版图", "比较器", "闭环", "带隙基准", "电感", "电容", "电阻", "二极管",
    "反馈", "放大器", "沟道长度调制", "共模抑制比", "极点", "寄生电容",
    "结电容", "跨导", "米勒效应", "偏置", "频率响应", "迁移率", "热噪声",
    "三极管", "闪烁噪声", "失调电压", "输出阻抗", "输入阻抗", "锁相环",
    "体效应", "温漂", "相位裕度", "小信号模型",
)


def _index_section():
    entries = []
    for index, term in enumerate(INDEX_TERMS):
        primary = 3 + (index * 7) % 190
        secondary = primary + 3 + index % 9 if index % 3 == 0 else None
        pages = (f'<span class="book-index-page is-primary">{primary}</span>'
                 + (f', <span class="book-index-page">{secondary}</span>'
                    if secondary else ""))
        entries.append(
            f'<p class="book-index-entry">{term} {pages}</p>')
    body = "\n".join(entries)
    return f"""
<section class="book-page" id="sample-index">
  <div class="runline">
    <span class="sq"></span><span>书末 · 术语索引</span>
    <span class="rule"></span><span class="folio">P.402</span>
  </div>

  <h1>索引样张</h1>
  <p>索引按术语排序，40 条记录分两栏排布；黑体页码表示该术语的定义页。索引只收“值得回查”的词，不重复目录已经给出的章节结构。</p>

  <div class="book-index">
{body}
  </div>

  <p>索引只收在正文中真正解释过、值得回查的术语；图号与表号不进入索引，统一由书末的图目录与表目录承担。样张页码仅用于检查两栏对齐，正式页码在终稿排版后统一核对。</p>
</section>
"""
