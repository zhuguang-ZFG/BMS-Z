#!/usr/bin/env python3
"""P2 parity 对账：统一入口产物 vs 两边旧构建器产物（设计 §11 P2 验收）。

对每个可对照产物比较字节与 sha256，并汇总页数、章数、图数、链接数、书签数。
旧产物缺失时记 skip；存在但不一致时退出码 1。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "book/dist"
ANALOG_DIST = ROOT / "analog/analog-book/dist"
BMS_DIST = ROOT / "bms-book/dist"

IMG_RE = re.compile(r"<img\b", re.I)
SVG_RE = re.compile(r"<svg\b", re.I)
LINK_RE = re.compile(r"<a\s[^>]*href\s*=", re.I)
CHAPTER_FILE_RE = re.compile(r"^\d{2}-.+\.md$")

REFERENCES = {
    "I": {
        "book.html": ANALOG_DIST / "analog-circuit-book.html",
        "book-a4.pdf": ANALOG_DIST / "analog-circuit-book.pdf",
        "book-16k-1.pdf": ANALOG_DIST / "print/volume-1/analog-circuit-book.pdf",
        "book-16k-2.pdf": ANALOG_DIST / "print/volume-2/analog-circuit-book.pdf",
        "book.epub": ANALOG_DIST / "analog-circuit-book.epub",
    },
    "II": {
        "book.html": BMS_DIST / "bms-book.html",
        "book-a4.pdf": BMS_DIST / "bms-book.pdf",
        "book.epub": BMS_DIST / "bms-book.epub",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def html_metrics(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "figures": len(IMG_RE.findall(text)) + len(SVG_RE.findall(text)),
        "links": len(LINK_RE.findall(text)),
    }


def pdf_metrics(path: Path) -> dict:
    try:
        import fitz
    except ImportError:
        return {}
    with fitz.open(path) as doc:
        return {"pages": doc.page_count, "bookmarks": len(doc.get_toc())}


def epub_metrics(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        return {"entries": len(entries), "uncompressed": sum(item.file_size for item in entries)}


def metrics(path: Path) -> dict:
    if path.suffix == ".html":
        data = html_metrics(path)
    elif path.suffix == ".pdf":
        data = pdf_metrics(path)
    elif path.suffix == ".epub":
        data = epub_metrics(path)
    else:
        data = {}
    data["bytes"] = path.stat().st_size
    return data


def chapter_counts() -> dict:
    analog = json.loads((ROOT / "analog/analog-book/manifest.json").read_text(encoding="utf-8"))
    volume_i = sum(len(unit.get("chapters", []))
                   for part in analog.get("parts", [])
                   for unit in part.get("units", []))
    bms = json.loads((ROOT / "bms-book/manifest.json").read_text(encoding="utf-8"))
    volume_ii = sum(1 for part in bms.get("parts", []) for name in part.get("files", [])
                    if CHAPTER_FILE_RE.match(name) and not name.startswith("00-"))
    return {"I": volume_i, "II": volume_ii}


def main() -> int:
    rows = []
    for volume, mapping in REFERENCES.items():
        for name, reference in mapping.items():
            artifact = DIST / f"volume-{1 if volume == 'I' else 2}" / name
            row = {"volume": volume, "name": name, "artifact": str(artifact.relative_to(ROOT)),
                   "reference": str(reference.relative_to(ROOT))}
            if not artifact.is_file():
                row["status"] = "missing-artifact"
            elif not reference.is_file():
                row["status"] = "skip-reference-missing"
                row["new"] = metrics(artifact)
            else:
                row["new"] = metrics(artifact)
                row["old"] = metrics(reference)
                row["identical"] = sha256(artifact) == sha256(reference)
                if row["identical"]:
                    row["status"] = "identical"
                elif row["new"] == row["old"]:
                    row["status"] = "metrics-match"
                else:
                    row["status"] = "different"
            rows.append(row)

    volume_ii_16k = DIST / "volume-2/book-16k-1.pdf"
    rows.append({
        "volume": "II", "name": "book-16k-1.pdf", "artifact": str(volume_ii_16k.relative_to(ROOT)),
        "reference": "无旧产物（P2 新增）",
        "status": "new-only" if volume_ii_16k.is_file() else "missing-artifact",
        "new": metrics(volume_ii_16k) if volume_ii_16k.is_file() else {},
    })

    report = {
        "schema": 3,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "chapters": chapter_counts(),
        "rows": rows,
    }
    (DIST / "parity-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failed = [row for row in rows if row["status"] in {"different", "missing-artifact"}]
    for row in rows:
        print(f"[{row['status']}] {row['volume']}/{row['name']}: {row.get('new', {})} "
              f"vs {row.get('old', '-')}")
    print(f"章节数 {report['chapters']}；报告 -> {DIST / 'parity-report.json'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
