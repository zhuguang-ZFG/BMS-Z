#!/usr/bin/env python3
"""两卷与合集下载发布：把 book/dist 的成品打成站点 downloads 目录。

《从模拟电路到 BMS》每个卷提供三种介质：单文件 HTML、出版 A4 PDF、EPUB；
另有一本两卷合订的 A4 PDF 与 EPUB（book/dist/combined）。
本模块读取 book/manifest.json 的丛书信息与版本号，把两卷 6 件与合集 2 件
复制成稳定文件名 + 版本化副本，并生成 SHA256SUMS.txt、downloads.json 与着陆页。
全部写入在同级临时目录完成后才整体替换输出目录；任何一件产物缺失都会
在写盘前整体失败，不留半成品。
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from uuid import uuid4

from assemble import BOOK, DIST, VOLUME_DIR, BuildError

FORMATS = [
    ("html", "book.html", "单文件 HTML", "离线单文件，内嵌目录、公式与交互，双击即开"),
    ("a4", "book-a4.pdf", "出版 PDF（A4）", "A4 出版版式，书签、目录页码与页眉完整"),
    ("epub", "book.epub", "EPUB", "电子书阅读器适用，spine 与目录完整"),
]

COMBINED_FORMATS = [
    ("epub", "from-analog-to-bms.epub", "合集 EPUB", "两卷合一，合集目录与 spine 完整"),
    ("pdf", "from-analog-to-bms.pdf", "合集 PDF（A4）", "两卷按卷序合一，A4 版式、页内链接与两卷书签"),
]

COMBINED_DIR = DIST / "combined"
COMBINED_TITLE = "两卷合集：从模拟电路到 BMS"

VOLUME_SLUG = {"I": "volume-1", "II": "volume-2"}


class DownloadError(BuildError):
    """下载发布失败。"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MiB"
    if size >= 1024:
        return f"{size / 1024:.1f} KiB"
    return f"{size} B"


def _make_sibling_dir(parent: Path, prefix: str) -> Path:
    """在同级分配一个继承父目录 Windows ACL 的临时目录。"""
    for _ in range(8):
        candidate = parent / f"{prefix}{uuid4().hex}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise DownloadError(f"无法在 {parent} 下分配临时目录")


def load_release() -> dict:
    manifest = json.loads((BOOK / "manifest.json").read_text(encoding="utf-8"))
    title = manifest.get("title")
    subtitle = manifest.get("subtitle")
    version = manifest.get("version")
    volumes = manifest.get("volumes")
    if not isinstance(title, str) or not title.strip():
        raise DownloadError("book/manifest.json 缺丛书 title")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise DownloadError(f"book/manifest.json 的 version 非法：{version!r}")
    if not isinstance(volumes, list) or not volumes:
        raise DownloadError("book/manifest.json 缺 volumes")
    for volume in volumes:
        if volume.get("id") not in VOLUME_SLUG or not volume.get("title"):
            raise DownloadError(f"book/manifest.json 的卷登记非法：{volume!r}")
    return {"title": title, "subtitle": subtitle or "", "version": version,
            "volumes": volumes}


def collect_files(release: dict) -> list[dict]:
    """核对 6 件分卷产物 + 2 件合集产物齐全，缺失时整体失败。"""
    missing: list[str] = []
    files: list[dict] = []
    for volume in release["volumes"]:
        slug = VOLUME_SLUG[volume["id"]]
        for kind, artifact, label, description in FORMATS:
            source = VOLUME_DIR[volume["id"]] / artifact
            if not source.is_file():
                missing.append(f"{slug}/{artifact}")
                continue
            latest = f"{slug}{Path(artifact).suffix}"
            versioned = f"{slug}-v{release['version']}{Path(artifact).suffix}"
            files.append({
                "volume": slug, "volume_id": volume["id"],
                "volume_title": volume["title"],
                "kind": kind, "label": label, "description": description,
                "source": source, "latest": latest, "versioned": versioned,
            })
    for kind, artifact, label, description in COMBINED_FORMATS:
        source = COMBINED_DIR / artifact
        if not source.is_file():
            missing.append(f"combined/{artifact}")
            continue
        versioned = f"{Path(artifact).stem}-v{release['version']}{Path(artifact).suffix}"
        files.append({
            "volume": "combined", "volume_id": "combined",
            "volume_title": COMBINED_TITLE,
            "kind": kind, "label": label, "description": description,
            "source": source, "latest": artifact, "versioned": versioned,
        })
    if missing:
        raise DownloadError("产物缺失，无法生成下载页：" + "、".join(missing))
    return files


def _card(item: dict) -> str:
    digest = item["sha256"]
    latest = html.escape(item["latest"])
    versioned = html.escape(item["versioned"])
    return (
        '<article class="download-card">'
        '<div class="card-meta">'
        f'<p class="format">{html.escape(item["label"])}</p>'
        f'<p class="size">{_display_size(item["bytes"])}</p>'
        "</div>"
        f"<h2>{html.escape(item['volume_title'])}</h2>"
        f'<p class="description">{html.escape(item["description"])}</p>'
        f'<a class="primary" href="{latest}">下载 {html.escape(item["volume_title"])}'
        '<span aria-hidden="true">↓</span></a>'
        '<p class="version-copy"><span>固定版本</span>'
        f'<a href="{versioned}">{versioned}</a></p>'
        '<details class="hash"><summary><span>SHA-256</span><span>展开校验值</span></summary>'
        f"<code>{digest}</code></details>"
        "</article>"
    )


def _landing_page(release: dict, files: list[dict]) -> str:
    sections: list[str] = []
    for volume in release["volumes"]:
        slug = VOLUME_SLUG[volume["id"]]
        cards = "".join(_card(item) for item in files if item["volume"] == slug)
        safe_volume = html.escape(volume["title"])
        safe_subtitle = html.escape(volume.get("subtitle", ""))
        sections.append(
            f'<section aria-label="{safe_volume}">'
            f"<h2>{safe_volume}</h2>"
            f'<p class="volume-subtitle">{safe_subtitle}</p>'
            f'<div class="download-grid">{cards}</div>'
            "</section>"
        )

    combined = [item for item in files if item["volume"] == "combined"]
    if combined:
        cards = "".join(_card(item) for item in combined)
        sections.append(
            '<section aria-label="两卷合集">'
            "<h2>两卷合集</h2>"
            '<p class="volume-subtitle">把卷一与卷二装订成一本：A4 PDF 与 EPUB 各一件，'
            "合集目录与两卷书签完整。</p>"
            f'<div class="download-grid">{cards}</div>'
            "</section>"
        )

    safe_title = html.escape(release["title"])
    safe_subtitle = html.escape(release["subtitle"])
    safe_version = html.escape(release["version"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{safe_title} v{safe_version} 两卷离线 HTML、出版 PDF、EPUB 与 SHA-256 校验。">
<title>{safe_title} · 下载</title>
<style>
:root {{ --paper:#fffdf5; --ink:#293b3a; --muted:#626d65; --line:#cfc6b2; --accent:#176b73; --accent-hover:#12545b; --button:#176b73; --button-hover:#12545b; --button-ink:#fff; --panel:#f7f2e5; --code:#fffdf5; --note:#fbefc7; --shadow:#e4f0df; }}
* {{ box-sizing:border-box; }}
html {{ color-scheme:light dark; }}
body {{ margin:0; min-height:100vh; color:var(--ink); background:var(--paper); font:16px/1.7 "Punctuation SC","Inter",ui-sans-serif,system-ui,-apple-system,"Segoe UI","PingFang SC","HarmonyOS Sans SC","Source Han Sans SC","Noto Sans CJK SC","Microsoft YaHei UI","Microsoft YaHei",sans-serif; }}
a {{ color:var(--accent); text-underline-offset:.18em; }}
a:hover {{ color:var(--accent-hover); }}
a:focus-visible,summary:focus-visible {{ outline:3px solid var(--accent); outline-offset:3px; border-radius:5px; }}
.skip {{ position:fixed; z-index:2; top:.75rem; left:.75rem; padding:.45rem .75rem; border-radius:7px; background:var(--paper); transform:translateY(-180%); }}
.skip:focus {{ transform:none; }}
.page {{ width:min(100% - 2.5rem,960px); margin:0 auto; padding:4.5rem 0 3rem; }}
.hero {{ padding-bottom:2rem; border-bottom:1px solid var(--line); }}
.eyebrow,.format {{ margin:0; color:var(--accent); font-size:.75rem; font-weight:800; line-height:1.4; letter-spacing:.14em; }}
h1 {{ max-width:22ch; margin:.45rem 0 .8rem; font-size:clamp(2rem,5vw,3.05rem); line-height:1.16; letter-spacing:-.025em; text-wrap:balance; }}
.lead {{ max-width:50rem; margin:0; color:var(--muted); font-size:1.04rem; }}
.release-facts {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); margin:1.75rem 0 0; border:1px solid var(--line); border-radius:4px 14px 6px 12px; background:var(--note); box-shadow:3px 4px 0 var(--shadow); }}
.release-facts div {{ min-width:0; padding:.9rem 1rem; border-left:1px solid var(--line); }}
.release-facts div:first-child {{ border-left:0; }}
.release-facts dt {{ color:var(--muted); font-size:.76rem; font-weight:700; letter-spacing:.08em; }}
.release-facts dd {{ margin:.12rem 0 0; font-weight:700; }}
section {{ margin-top:2.5rem; }}
section > h2 {{ margin:0; font-size:1.6rem; line-height:1.3; }}
.volume-subtitle {{ margin:.2rem 0 0; color:var(--muted); }}
.download-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1rem; margin:1.25rem 0 1rem; }}
.download-card {{ display:flex; min-width:0; flex-direction:column; padding:1.35rem; border:1px solid var(--line); border-top:3px solid var(--accent); border-radius:5px 18px 7px 14px; background:var(--panel); box-shadow:4px 5px 0 var(--shadow); }}
.card-meta {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; }}
.size {{ margin:0; color:var(--muted); font-size:.8rem; font-variant-numeric:tabular-nums; }}
.download-card h2 {{ margin:.42rem 0 .35rem; font-size:1.2rem; line-height:1.3; }}
.description {{ min-height:3.4em; margin:0 0 1rem; color:var(--muted); font-size:.92rem; }}
.primary {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.72rem .9rem; border:1px solid var(--button); border-radius:9px; color:var(--button-ink); background:var(--button); font-weight:750; text-decoration:none; }}
.primary:hover {{ border-color:var(--button-hover); color:var(--button-ink); background:var(--button-hover); }}
.primary span {{ font-size:1.12rem; }}
.version-copy {{ display:grid; gap:.12rem; margin:1rem 0; color:var(--muted); font-size:.83rem; overflow-wrap:anywhere; }}
.version-copy span {{ font-size:.72rem; font-weight:700; letter-spacing:.06em; }}
.hash {{ margin-top:auto; padding-top:.9rem; border-top:1px solid var(--line); }}
.hash summary {{ display:flex; justify-content:space-between; gap:1rem; color:var(--muted); cursor:pointer; font-size:.76rem; font-weight:700; list-style:none; }}
.hash summary::-webkit-details-marker {{ display:none; }}
.hash summary span:last-child {{ color:var(--accent); font-weight:600; }}
.hash[open] summary {{ margin-bottom:.55rem; }}
.hash code {{ display:block; padding:.65rem .7rem; border:1px solid var(--line); border-radius:7px; color:var(--ink); background:var(--code); font:12px/1.55 "JetBrains Mono",ui-monospace,"SFMono-Regular",Consolas,monospace; overflow-wrap:anywhere; user-select:all; }}
.toolbox {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; margin-top:1rem; }}
.toolbox a {{ display:block; padding:.9rem 1rem; border:1px solid var(--line); border-radius:10px; background:var(--paper); text-decoration:none; }}
.toolbox strong {{ display:block; color:var(--ink); }}
.toolbox span {{ color:var(--muted); font-size:.82rem; }}
.print-note {{ margin-top:1.5rem; padding:.9rem 1rem; border:1px dashed var(--line); border-radius:10px; color:var(--muted); font-size:.88rem; }}
.footer {{ display:flex; justify-content:space-between; gap:1rem; margin-top:2.25rem; padding-top:1.25rem; border-top:1px solid var(--line); color:var(--muted); font-size:.86rem; }}
.footer p {{ margin:0; }}
.footer a {{ font-weight:650; }}
@media (max-width:640px) {{
  .page {{ width:min(100% - 2rem,960px); padding:2rem 0; }}
  h1 {{ font-size:2rem; }}
  .release-facts,.download-grid,.toolbox {{ grid-template-columns:1fr; }}
  .release-facts div {{ padding:.7rem .85rem; border-top:1px solid var(--line); border-left:0; }}
  .release-facts div:first-child {{ border-top:0; }}
  .description {{ min-height:0; }}
  .footer {{ flex-direction:column; }}
}}
@media (prefers-color-scheme:dark) {{
  :root {{ --paper:#192727; --ink:#edf0e5; --muted:#b0beb3; --line:#496160; --accent:#7ec5c5; --accent-hover:#a0dddd; --button:#7ec5c5; --button-hover:#a0dddd; --button-ink:#192727; --panel:#223333; --code:#192727; --note:#453e2b; --shadow:#293f35; }}
}}
@media print {{
  :root {{ color-scheme:light; --paper:#fff; --panel:#fff; --code:#fff; --note:#fff; --ink:#293b3a; --muted:#626d65; --accent:#176b73; --line:#cfc6b2; }}
  .release-facts,.download-card {{ box-shadow:none; break-inside:avoid; }}
}}
</style>
</head>
<body>
<a class="skip" href="#downloads">跳到下载选项</a>
<div class="page">
<header class="hero">
<p class="eyebrow">{safe_title} · OFFLINE BOOKS</p>
<h1>{safe_title}</h1>
<p class="lead">{safe_subtitle}两卷各自提供单文件 HTML、出版 A4 PDF 与 EPUB；另有一本两卷合集（A4 PDF 与 EPUB）。同一次书稿构建，并附版本化副本和可复核摘要。</p>
<dl class="release-facts">
<div><dt>版本</dt><dd>v{safe_version}</dd></div>
<div><dt>构建</dt><dd>同一份丛书构建</dd></div>
<div><dt>门禁</dt><dd>出版契约通过</dd></div>
</dl>
</header>
<main id="downloads">
{''.join(sections)}
<nav class="toolbox" aria-label="校验与机器可读文件">
<a href="SHA256SUMS.txt"><strong>SHA256SUMS.txt</strong><span>批量核对版本化文件</span></a>
<a href="downloads.json"><strong>downloads.json</strong><span>机器可读的版本、大小与摘要</span></a>
</nav>
<p class="print-note">16K 印刷分册（打印店装订版）不随 Pages 分发，随
<a href="https://github.com/zhuguang-ZFG/BMS-Z/releases">GitHub Release</a> 工件提供。</p>
</main>
<footer class="footer">
<p><a href="../reading.html">← 返回书籍与阅读路线</a> · <a href="../volume-1/">卷一在线阅读</a></p>
<p>文档 CC BY-SA 4.0 · 代码 MIT</p>
</footer>
</div>
</body>
</html>
"""


def build_downloads(site_dir: Path) -> dict:
    """把两卷产物发布到 site_dir/downloads，返回机器可读清单。"""
    release = load_release()
    files = collect_files(release)

    output_dir = site_dir / "downloads"
    if output_dir.exists() and (not output_dir.is_dir() or output_dir.is_symlink()):
        raise DownloadError(f"输出路径不是受控目录：{output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = _make_sibling_dir(output_dir.parent, f".{output_dir.name}-staging-")
    backup_dir: Path | None = None
    try:
        payload = []
        sums = []
        for item in files:
            item["sha256"] = _sha256(item["source"])
            item["bytes"] = item["source"].stat().st_size
            shutil.copyfile(item["source"], staging_dir / item["latest"])
            shutil.copyfile(item["source"], staging_dir / item["versioned"])
            digest = item["sha256"]
            payload.append({
                "volume": item["volume"], "volume_title": item["volume_title"],
                "kind": item["kind"], "label": item["label"],
                "latest": item["latest"], "versioned": item["versioned"],
                "bytes": item["bytes"], "sha256": digest,
            })
            sums.append(f"{digest} *{item['versioned']}")

        metadata = {"title": release["title"], "version": release["version"], "files": payload}
        (staging_dir / "downloads.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        (staging_dir / "SHA256SUMS.txt").write_text(
            "\n".join(sums) + "\n", encoding="utf-8", newline="\n")
        (staging_dir / "index.html").write_text(
            _landing_page(release, files), encoding="utf-8", newline="\n")

        if output_dir.exists():
            backup_dir = _make_sibling_dir(output_dir.parent, f".{output_dir.name}-backup-")
            backup_dir.rmdir()
            output_dir.replace(backup_dir)
        try:
            staging_dir.replace(output_dir)
        except OSError:
            if backup_dir is not None and backup_dir.exists():
                backup_dir.replace(output_dir)
            raise
        if backup_dir is not None:
            shutil.rmtree(backup_dir, ignore_errors=True)
        return metadata
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=DIST / "site",
                        help="站点产物根目录（默认 book/dist/site）")
    args = parser.parse_args()
    try:
        result = build_downloads(args.site_dir)
    except (OSError, json.JSONDecodeError, DownloadError) as exc:
        parser.error(str(exc))
    print(f"downloads -> {args.site_dir / 'downloads'} "
          f"（{result['title']} v{result['version']}，{len(result['files'])} 件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
