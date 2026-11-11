#!/usr/bin/env python3
"""引用库校验：schema、唯一 id、chapters 范围、OSS/官方源扩量要求。

CLI:
  python scripts/check_references.py analog-book/data/references.yml analog-book/data/sources.yml [--only a.md,b.md]
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

REQUIRED_FIELDS = ("id", "title", "isbn_or_url", "chapters")
OSS_URLS = [
    "https://github.com/yang0/handraw-style",
    "https://github.com/ningzimu/handdrawn-tech-illustrations",
    "https://github.com/overegneered/manim-eng",
    "https://github.com/Mr-FuzzyPenguin/manim-circuit",
    "https://github.com/milkway/rpic-lang",
    "https://github.com/wijnen/edraw",
]


def _load(path: Path):
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(text)
    raise SystemExit("PyYAML 不可用：请安装 pyyaml 后重试")


def validate(ref_path: Path, src_path: Path) -> list[str]:
    errors: list[str] = []
    refs = _load(ref_path)
    if not isinstance(refs, list):
        return [f"{ref_path}: 顶层应为 list"]
    seen = set()
    blob = ""
    for item in refs:
        if not isinstance(item, dict):
            errors.append(f"{ref_path}: 条目应为 dict")
            continue
        rid = str(item.get("id", ""))
        for f in REQUIRED_FIELDS:
            if f not in item:
                errors.append(f"{rid}: 缺字段 {f}")
        if rid in seen:
            errors.append(f"{rid}: id 重复")
        seen.add(rid)
        chs = item.get("chapters") or []
        if not isinstance(chs, list) or any(not isinstance(c, int) or not 0 <= c <= 18 for c in chs):
            errors.append(f"{rid}: chapters 须为 0-18 整数列表")
        notes = str(item.get("notes", ""))
        if "github.com" in str(item.get("isbn_or_url", "")) and not notes:
            errors.append(f"{rid}: OSS 条目须写 notes（用途/许可立场）")
        blob += str(item.get("isbn_or_url", "")) + " " + str(item.get("title", ""))

    for url in OSS_URLS:
        if url not in blob:
            errors.append(f"缺少 OSS 条目 URL：{url}")

    for vendor, domain, floor in (("ADI", "analog.com", 3), ("TI", "ti.com", 3)):
        n = sum(1 for item in refs
                if isinstance(item, dict) and domain in str(item.get("isbn_or_url", "")))
        if n < floor:
            errors.append(f"{vendor} 官方域名条目仅 {n} 条（须 ≥{floor}）")

    if not any("新概念模拟电路" in str(i.get("title", "")) for i in refs if isinstance(i, dict)):
        errors.append("缺少《新概念模拟电路》条目")
    else:
        for item in refs:
            if isinstance(item, dict) and "新概念模拟电路" in str(item.get("title", "")):
                tag = str(item.get("edition", "")) + str(item.get("notes", ""))
                if "optional-deep-read" not in tag:
                    errors.append("《新概念模拟电路》必须标 optional-deep-read")

    srcs = _load(src_path)
    if not isinstance(srcs, list):
        errors.append(f"{src_path}: 顶层应为 list")
    elif len(srcs) < 20:
        errors.append(f"{src_path}: 条目数 {len(srcs)} < 20（Task 11c 出口闸）")
    return errors


def scan_chapters(paths: list[Path]) -> list[str]:
    errors = []
    for p in paths:
        text = p.read_text(encoding="utf-8")
        ok = ("<!-- slot:citations -->" in text) or ("### 参考与出处" in text)
        if not ok:
            errors.append(f"{p}: 缺少引用清单（<!-- slot:citations --> 或 ### 参考与出处）")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ref")
    ap.add_argument("sources")
    ap.add_argument("--only", default="", help="仅扫描逗号分隔的章文件（样板阶段用）")
    args = ap.parse_args()
    errors = validate(Path(args.ref), Path(args.sources))
    if args.only:
        files = [Path(x) for x in args.only.split(",") if x.strip()]
        errors += scan_chapters(files)
    else:
        files = sorted(p for p in Path("docs").glob("p*-ch*.md")
                       if re.fullmatch(r"p\d+-\d+-ch\d+\.md", p.name))
        errors += scan_chapters(files)
    for e in errors:
        print(e)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
