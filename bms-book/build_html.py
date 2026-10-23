#!/usr/bin/env python3
"""Build the single-file HTML/PDF edition of the BMS book.

Usage: python build_html.py [--pdf]      # --pdf 额外打印带书签、带页码的 PDF
"""

from pathlib import Path
import html
import json
import shutil
import subprocess
import tempfile
import argparse


ROOT = Path(__file__).resolve().parent
BOOK = ROOT / "book"
DIST = ROOT / "dist"

MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
PARTS = [(p["id"], p["title"], p["description"], p["files"]) for p in MANIFEST["parts"]]


CSS = """
:root {
  --ink:#0f172a; --muted:#475569; --border:#d8dee9; --paper:#ffffff;
  --accent:#0f766e; --soft:#f1f5f9;
}
* { box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
body { margin:0 auto; max-width:920px; padding:44px 26px 96px;
       font-family:"Noto Serif SC","Source Han Serif SC",Georgia,serif;
       color:var(--ink); line-height:1.8; font-size:16px; background:var(--paper); }
h2 { font-size:2rem; margin:2.6rem 0 1rem; padding-bottom:.45rem;
     border-bottom:2px solid var(--accent); color:var(--accent); }
h3 { font-size:1.4rem; margin:2rem 0 .7rem; color:#111827; }
h4 { font-size:1.15rem; margin:1.5rem 0 .5rem; color:#1f2937; }
h1, h2, h3, h4 { break-after:avoid; page-break-after:avoid; }
p, li { text-align:justify; orphans:3; widows:3; }
ul, ol { padding-left:1.4rem; }
code { font-family:"JetBrains Mono",Consolas,monospace; font-size:.9em;
       background:#eef2f7; padding:.1em .35em; border-radius:4px; }
pre { background:#0f172a; color:#e2e8f0; padding:1rem 1.1rem; overflow:auto;
      border-radius:10px; border:1px solid #1e293b; line-height:1.55; }
pre code { background:none; color:inherit; padding:0; }
table { border-collapse:collapse; width:100%; margin:1rem 0; font-size:.94em;
        break-inside:avoid; }
th, td { border:1px solid var(--border); padding:.45rem .6rem; vertical-align:top; }
th { background:#eef2f7; text-align:left; }
tbody tr:nth-child(even) { background:#fafbfc; }
blockquote { margin:1rem 0; padding:.6rem 1rem; color:var(--muted);
             border-left:4px solid var(--border); background:#f8fafc; }
a { color:#1d4ed8; text-decoration:none; }
a:hover { text-decoration:underline; }
mark { background:#fef08a; padding:0 .15em; border-radius:3px; }
figure { margin:1.4rem 0; break-inside:avoid; }
figure img { width:100%; border:1px solid var(--border); border-radius:10px; display:block; }
figcaption { margin-top:.45rem; color:var(--muted); font-size:.88em; text-align:center; }

.chapter { break-before:page; page-break-before:always;
           border-top:6px solid var(--accent); padding-top:1.1rem; }
.chapter[data-part="p1"] { --accent:#0f766e; }
.chapter[data-part="p2"] { --accent:#be123c; }
.chapter[data-part="p3"] { --accent:#1d4ed8; }
.chapter[data-part="p4"] { --accent:#6d28d9; }
.chapter[data-part="p5"] { --accent:#b45309; }
.chapter[data-part="p6"] { --accent:#0891b2; }
.chapter[data-part="p7"] { --accent:#15803d; }
.chapter[data-part="p8"] { --accent:#475569; }

.part-divider { break-before:page; page-break-before:always;
                min-height:70vh; display:flex; flex-direction:column; justify-content:center;
                padding:2rem; border-radius:16px; color:#fff;
                background:linear-gradient(135deg,#0f172a 0%,#1e293b 60%,#334155 100%); }
.part-divider h1 { font-size:2.1rem; margin:0 0 .6rem; color:#fff; border:none; }
.part-divider p { color:#cbd5e1; font-size:1rem; margin:0; }
.part-divider[data-part="p2"] { background:linear-gradient(135deg,#4c0519,#9f1239 70%,#be123c); }
.part-divider[data-part="p3"] { background:linear-gradient(135deg,#172554,#1e3a8a 70%,#1d4ed8); }
.part-divider[data-part="p4"] { background:linear-gradient(135deg,#2e1065,#5b21b6 70%,#6d28d9); }
.part-divider[data-part="p5"] { background:linear-gradient(135deg,#451a03,#92400e 70%,#b45309); }
.part-divider[data-part="p7"] { background:linear-gradient(135deg,#052e16,#15803d 70%,#16a34a); }
.part-divider[data-part="p8"] { background:linear-gradient(135deg,#1e293b,#475569); }
.part-divider[data-part="p6"] { background:linear-gradient(135deg,#164e63,#0e7490 70%,#0891b2); }
.part-divider[data-part="p1"] { background:linear-gradient(135deg,#042f2e,#0f766e 70%,#0d9488); }

.callout { margin:1.2rem 0; padding:.85rem 1.05rem; border-radius:10px;
           border-left:5px solid var(--c); background:var(--bg); break-inside:avoid; }
.callout .callout-title { font-weight:700; color:var(--c); margin-bottom:.25rem;
                          font-family:"Noto Sans SC","Microsoft YaHei",sans-serif; }
.callout p:last-child { margin-bottom:0; }
.callout.story { --c:#b45309; --bg:#fffbeb; }
.callout.principle { --c:#1d4ed8; --bg:#eff6ff; }
.callout.trap { --c:#be123c; --bg:#fff1f2; }
.callout.lab { --c:#047857; --bg:#ecfdf5; }

.toc { background:#f8fafc; border:1px solid var(--border); border-radius:12px;
       padding:1rem 1.4rem; margin:2rem 0; }
.toc ul { margin:.25rem 0; padding-left:0; list-style:none; }
.toc li { margin:.08rem 0; }
.toc { font-size:.92em; }
.toc .toc-part { list-style:none; margin:.55rem 0 .15rem; font-weight:700;
                 color:#0f172a; font-family:"Noto Sans SC","Microsoft YaHei",sans-serif; }
.toc a { color:#1f2937; }

.cover { min-height:92vh; display:flex; flex-direction:column; justify-content:center;
         padding:3rem 2rem; margin:-44px -26px 0; color:#e2e8f0;
         background:radial-gradient(circle at 80% 10%,#1e3a8a 0%,transparent 45%),
                    radial-gradient(circle at 10% 90%,#0f766e 0%,transparent 40%),
                    linear-gradient(160deg,#020617,#0f172a 70%); }
.cover .eyebrow { color:#7dd3fc; letter-spacing:.2em; font-size:.85rem; }
.cover h1 { border:none; color:#fff; font-size:3rem; line-height:1.15; margin:.6rem 0 1rem; }
.cover .sub { color:#cbd5e1; font-size:1.1rem; max-width:640px; }
.cover .chips { margin-top:1.6rem; display:flex; flex-wrap:wrap; gap:.5rem; }
.cover .chip { border:1px solid #334155; background:#0b1220; color:#93c5fd;
               padding:.3rem .7rem; border-radius:999px; font-size:.82rem; }
.cover .meta { margin-top:2rem; color:#94a3b8; font-size:.9rem; }

.back-to-toc { position:fixed; right:1rem; bottom:1rem; padding:.5rem .8rem;
  background:var(--paper); border:1px solid var(--border); border-radius:8px; }
mjx-container { max-width:100%; overflow-x:auto; overflow-y:hidden; }
@media (max-width:600px) {
  body { padding:20px 16px 80px; }
  .cover { margin:-20px -16px 0; padding:2rem 1rem; min-height:75vh; }
  .cover h1 { font-size:2rem; }
  .part-divider { min-height:35vh; padding:1.2rem; }
  h2 { font-size:1.6rem; }
  table { display:block; overflow-x:auto; }
  p, li { text-align:left; }
}
@media (prefers-color-scheme:dark) {
  :root { --ink:#e2e8f0; --muted:#a8b4c5; --border:#475569; --paper:#0f172a; --accent:#5eead4; }
  h3, h4, .toc .toc-part, .toc a { color:var(--ink); }
  a { color:#93c5fd; }
  code, th, .toc { background:#1e293b; }
  blockquote, tbody tr:nth-child(even) { background:#172033; }
  .callout { background:#172033; }
  .callout.story { --c:#fbbf24; }
  .callout.principle { --c:#93c5fd; }
  .callout.trap { --c:#fda4af; }
  .callout.lab { --c:#6ee7b7; }
}
@media print {
  :root { --ink:#0f172a; --muted:#475569; --border:#d8dee9; --paper:#ffffff; --accent:#0f766e; }
  .back-to-toc { display:none; }
  code, th, .toc { background:#eef2f7; }
  h3, h4, .toc a, .toc .toc-part { color:#0f172a; }
  blockquote, tbody tr:nth-child(even) { background:#f8fafc; }
  .callout { background:#f1f5f9; }
  @page { size:A4; margin:17mm 16mm; }
  body { max-width:none; padding:0; font-size:11pt; line-height:1.72; }
  .cover { min-height:245mm; margin:0; padding:2.5rem 1.5rem; page-break-after:always; }
  .part-divider { min-height:243mm; padding:2.4rem; border-radius:0; }
  pre { white-space:pre-wrap; overflow:visible; overflow-wrap:anywhere; }
  a { color:var(--ink); }
}
"""

def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    renderer = shutil.which("node")
    if renderer is None:
        raise RuntimeError("HTML 构建需要 Node.js 24+；请先在仓库根运行 npm ci")
    rendered = subprocess.run(
        [renderer, str(ROOT / "render.mjs")], check=True, capture_output=True,
        encoding="utf-8", timeout=120,
    )
    chapters = json.loads(rendered.stdout)
    toc, combined, body_parts = [], [], []
    index = 0
    for part_id, part_title, part_desc, files in PARTS:
        label = f"{part_title} · {part_desc}"
        toc.append(f'<li class="toc-part">{html.escape(label)}</li>')
        body_parts.append(
            f'<section class="part-divider" data-part="{part_id}">'
            f'<h1>{html.escape(label)}</h1>'
            '<p>BMS 实战 · 从一颗电芯到一套证据链</p></section>'
        )
        for name in files:
            chapter = chapters[index]
            combined.append((BOOK / name).read_text(encoding="utf-8"))
            index += 1
            toc.append(f'<li><a href="#{chapter["prefix"]}">{html.escape(chapter["title"])}</a></li>')
            body_parts.append(f'<section class="chapter" data-part="{part_id}">{chapter["body"]}</section>')
    (DIST / "bms-book.md").write_text("\n\n---\n\n".join(combined), encoding="utf-8")

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMS 实战：从一颗电芯到一套证据链</title>
<style>{CSS}</style>
</head>
<body>
<header class="cover">
  <div class="eyebrow">BMS IN PRACTICE · v{MANIFEST["version"]}</div>
  <h1>BMS 实战<br>从一颗电芯到一套证据链</h1>
  <p class="sub">参考 BMS-Z 开源教程、foxBMS、PyBaMM 与社区实践：把“为什么”讲到能复现，把“谁签字”写进流程。</p>
  <div class="chips">
    <span class="chip">BMS-Z 实验数据</span>
    <span class="chip">154 张动画</span>
    <span class="chip">{len(MANIFEST['demos'])} 份可跑代码</span>
    <span class="chip">无真值诊断</span>
    <span class="chip">证据链</span>
    <span class="chip">UDS 诊断</span>
    <span class="chip">高压安全</span>
  </div>
  <p class="meta">2026-10 · 中文 · CC BY-SA 4.0（正文） / MIT（代码）</p>
</header>
<nav class="toc" id="contents" aria-label="全书目录"><strong>目录</strong><ul>{''.join(toc)}</ul></nav>
{''.join(body_parts)}
<a class="back-to-toc" href="#contents">返回目录</a>
</body>
</html>
"""
    out = DIST / "bms-book.html"
    out.write_text(doc, encoding="utf-8")
    print(f"built {out} ({out.stat().st_size} bytes, {index} chapters)")

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def build_pdf(browser_override: str | None = None) -> None:
    """Chrome/Edge headless 打印带书签 PDF；再给除封面外的页面盖页脚页码。"""
    browser = browser_override or next((p for p in BROWSERS if Path(p).exists()), None)
    if browser is None:
        browser = next((shutil.which(p) for p in ("google-chrome", "chromium", "chromium-browser", "msedge") if shutil.which(p)), None)
    if browser is None:
        raise RuntimeError("PDF 构建需要 Chrome/Edge；可用 --browser 指定可执行文件")
    html_path, out_pdf = DIST / "bms-book.html", DIST / "bms-book.pdf"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--generate-pdf-document-outline", f"--user-data-dir={profile}",
             f"--print-to-pdf={out_pdf}", html_path.resolve().as_uri()],
            check=True, capture_output=True, timeout=120)
    try:
        import fitz  # PyMuPDF，仅页码盖章需要
    except ImportError:
        print(f"pdf   {out_pdf} ({out_pdf.stat().st_size} bytes, outline; 未装 pymupdf，跳过页码)")
        return
    doc = fitz.open(out_pdf)
    for page in doc:
        if page.number == 0:
            continue  # 封面不编号
        num = str(page.number + 1)
        width = fitz.get_text_length(num, fontname="helv", fontsize=8.5)
        page.insert_text(((page.rect.width - width) / 2, page.rect.height - 22),
                         num, fontsize=8.5, fontname="helv", color=(0.28, 0.33, 0.41))
    stamped = out_pdf.with_suffix(".stamped.pdf")
    doc.save(stamped, garbage=3, deflate=True)
    doc.close()
    stamped.replace(out_pdf)
    print(f"pdf   {out_pdf} ({out_pdf.stat().st_size} bytes, outline + page numbers)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", action="store_true", help="额外生成 PDF")
    parser.add_argument("--out-dir", type=Path, default=DIST, help="构建输出目录")
    parser.add_argument("--browser", help="Chrome/Edge 可执行文件")
    options = parser.parse_args()
    DIST = options.out_dir.resolve()
    main()
    if options.pdf:
        build_pdf(options.browser)
