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
import json
import re
import shutil
from pathlib import Path
from uuid import uuid4

from assemble import BOOK, DIST, VOLUME_DIR, BuildError
from combined_front import cover_png
from download_page import ASSETS, landing_page

FORMATS = [
    ("html", "book.html", "单文件 HTML", "离线单文件，内嵌目录、公式与交互，双击即开"),
    ("a4", "book-a4.pdf", "出版 PDF（A4）", "A4 出版版式，书签、目录页码与页眉完整"),
    ("epub", "book.epub", "EPUB", "可调字号，随屏幕宽度重排，含章节目录"),
]

COMBINED_FORMATS = [
    ("epub", "from-analog-to-bms.epub", "合集 EPUB", "两卷合一，统一总目录与跨卷跳转，可随字号重排"),
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
        report_path = COMBINED_DIR / "combined-build-report.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            recorded = {Path(item["path"]).name: item["sha256"] for item in report["outputs"]}
            for item in files:
                if item["volume"] == "combined" and recorded.get(item["source"].name) != item["sha256"]:
                    raise DownloadError("合集构建记录与下载文件不匹配，请重新构建合集")
            shutil.copyfile(report_path, staging_dir / report_path.name)
            digest = _sha256(report_path)
            sums.append(f"{digest} *{report_path.name}")
            metadata["combined_build_report"] = {"file": report_path.name, "sha256": digest,
                                                 "generated_at": report["generated_at"]}
            release["combined_report"] = True
        (staging_dir / "downloads.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        (staging_dir / "SHA256SUMS.txt").write_text(
            "\n".join(sums) + "\n", encoding="utf-8", newline="\n")
        (staging_dir / "index.html").write_text(
            landing_page(release, files), encoding="utf-8", newline="\n")

        for name in ("download.css", "download.js"):
            shutil.copyfile(ASSETS / name, staging_dir / name)
        (staging_dir / "collection-cover.png").write_bytes(cover_png())

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
