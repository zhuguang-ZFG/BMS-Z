#!/usr/bin/env python3
"""统一成书入口（设计 §7）。装配调度在 assemble/pdf/epub，本文件只留 CLI 与审计。

子命令：
  site                          VitePress 站点（P3 前只承载卷二现有站点）
  html   --volume I|II|all      单文件 HTML
  pdf    --format a4|16k --volume I|II|all
  epub   --volume I|II|all
  check                         只审计已有产物并写构建报告
  all                           全链路 + 全审计
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from assemble import (BOOK, DIST, EXPECTED, HTML_LIMITS_BYTES, MAX_PRINT_PAGES, PY,
                      ROOT, VOLUME_DIR, BuildError, build_html, build_site,
                      ensure_dir, volumes)
from downloads import build_downloads
from epub import build_epub
from pdf import build_pdf


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int | None:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None
    with fitz.open(path) as doc:
        return doc.page_count


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def check_manifest() -> list[dict]:
    root = json.loads((BOOK / "manifest.json").read_text(encoding="utf-8"))
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "status": "ok" if ok else "fail", "detail": detail})

    record("总 manifest schema", root.get("schema") == 3,
           f"schema={root.get('schema')}")
    ids = [volume["id"] for volume in root.get("volumes", [])]
    record("卷清单", ids == ["I", "II"], f"volumes={ids}")
    for volume in root.get("volumes", []):
        manifest_path = ROOT / volume["manifest"]
        record(f"卷 {volume['id']} manifest 存在", manifest_path.is_file(),
               str(manifest_path.relative_to(ROOT)))

    sys.path.insert(0, str(BOOK))
    from manifests.convert_bms import convert, ManifestError

    try:
        converted = convert(print_spec=root["volumes"][1].get("print"))
        record("BMS manifest 转换与契约校验", True,
               f"{len(converted['parts'])} parts, {len(converted['index_terms'])} terms")
        out = ensure_dir(DIST / "manifests") / "volume-2.json"
        out.write_text(json.dumps(converted, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    except ManifestError as exc:
        record("BMS manifest 转换与契约校验", False, str(exc))

    from references import ReferenceIndex

    problems = ReferenceIndex().audit()
    record("跨卷引用审计", not problems,
           f"{len(problems)} 个问题" + (f"；首个：{problems[0]}" if problems else ""))

    from build_glossary import OUTPUT as GLOSSARY_OUTPUT, build as build_glossary
    from glossary_lint import lint as glossary_lint_issues

    expected = build_glossary()
    current = (GLOSSARY_OUTPUT.read_text(encoding="utf-8")
               if GLOSSARY_OUTPUT.is_file() else "")
    record("共享术语表同步", current == expected,
           "与源术语表一致" if current == expected else "请运行 python book/build_glossary.py")
    problems = glossary_lint_issues()
    record("术语 lint", not problems,
           f"{len(problems)} 个问题" + (f"；首个：{problems[0]}" if problems else ""))

    from build_shared import check as shared_front_issues

    problems = shared_front_issues()
    record("共享卷首", not problems,
           f"{len(problems)} 个问题" + (f"；首个：{problems[0]}" if problems else ""))
    return checks


def check_artifacts() -> tuple[list[dict], list[dict]]:
    checks: list[dict] = []
    artifacts: list[dict] = []
    for volume, names in EXPECTED.items():
        for name in names:
            path = VOLUME_DIR[volume] / name
            if not path.is_file():
                checks.append({"name": f"产物 {volume}/{name}", "status": "fail",
                               "detail": "缺失"})
                continue
            entry = {"volume": volume, "name": name, "bytes": path.stat().st_size,
                     "sha256": sha256(path)}
            artifacts.append(entry)
            ok = True
            detail = f"{entry['bytes']} bytes"
            if name == "book.html":
                limit = HTML_LIMITS_BYTES[volume]
                ok = entry["bytes"] <= limit
                detail += f"（上限 {limit}）"
            if "16k" in name and name.endswith(".pdf"):
                pages = pdf_pages(path)
                if pages is not None:
                    entry["pages"] = pages
                    ok = ok and pages <= MAX_PRINT_PAGES
                    detail += f"，{pages} 页（上限 {MAX_PRINT_PAGES}）"
                else:
                    detail += "，未装 PyMuPDF，跳过页数"
            checks.append({"name": f"产物 {volume}/{name}", "status": "ok" if ok else "fail",
                           "detail": detail})
    return checks, artifacts


def check_external() -> list[dict]:
    checks: list[dict] = []

    def run_check(name: str, cmd: list[str], cwd: Path, required: Path) -> None:
        if not required.exists():
            checks.append({"name": name, "status": "skip", "detail": f"缺 {required}"})
            return
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        ok = result.returncode == 0
        tail = (result.stdout or result.stderr).strip().splitlines()
        checks.append({"name": name, "status": "ok" if ok else "fail",
                       "detail": tail[-1] if tail else f"exit {result.returncode}"})

    analog = ROOT / "analog"
    run_check("卷 I 单文件 HTML 审计",
              [PY, "analog-book/build_book.py", "--check", "--no-build"], analog,
              analog / "analog-book/dist/analog-circuit-book.html")
    run_check("卷 I 16K 审计",
              [PY, "analog-book/build_print_book.py", "--check", "--no-build"], analog,
              analog / "analog-book/dist/print/analog-circuit-book.html")
    run_check("卷 II PDF 审计",
              [PY, "check_pdf.py", str(VOLUME_DIR["II"] / "book-a4.pdf")],
              ROOT / "bms-book", VOLUME_DIR["II"] / "book-a4.pdf")
    return checks


def build_check() -> int:
    checks = check_manifest()
    artifact_checks, artifacts = check_artifacts()
    checks.extend(artifact_checks)
    checks.extend(check_external())
    report = {
        "schema": 3,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "checks": checks,
        "artifacts": artifacts,
    }
    ensure_dir(DIST)
    (DIST / "build-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [item for item in checks if item["status"] == "fail"]
    for item in checks:
        print(f"[{item['status']}] {item['name']}: {item['detail']}")
    print(f"报告 -> {DIST / 'build-report.json'}（{len(checks)} 项，{len(failed)} 项失败）")
    return 0 if not failed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="两卷统一成书入口")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--no-build", action="store_true",
                        help="复用已有站点/中间产物")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("site", parents=[common], help="站点构建与汇总")
    html = sub.add_parser("html", parents=[common], help="单文件 HTML")
    html.add_argument("--volume", choices=["I", "II", "all"], default="all")
    pdf = sub.add_parser("pdf", parents=[common], help="PDF")
    pdf.add_argument("--format", choices=["a4", "16k"], default="a4")
    pdf.add_argument("--volume", choices=["I", "II", "all"], default="all")
    epub = sub.add_parser("epub", parents=[common], help="EPUB")
    epub.add_argument("--volume", choices=["I", "II", "all"], default="all")
    sub.add_parser("check", help="只审计已有产物")
    downloads = sub.add_parser("downloads", help="两卷下载目录（HTML/PDF/EPUB + 校验）")
    downloads.add_argument("--site-dir", type=Path, default=DIST / "site")
    all_cmd = sub.add_parser("all", parents=[common], help="全链路 + 全审计")
    all_cmd.add_argument("--volume", choices=["I", "II", "all"], default="all")

    args = parser.parse_args(argv)
    try:
        if args.command == "site":
            build_site(args.no_build)
        elif args.command == "html":
            for volume in volumes(args.volume):
                build_html(volume, args.no_build)
        elif args.command == "pdf":
            for volume in volumes(args.volume):
                build_pdf(volume, args.format, args.no_build)
        elif args.command == "epub":
            for volume in volumes(args.volume):
                build_epub(volume, args.no_build)
        elif args.command == "check":
            return build_check()
        elif args.command == "downloads":
            build_downloads(args.site_dir)
        elif args.command == "all":
            build_site(args.no_build)
            for volume in volumes(args.volume):
                build_html(volume, args.no_build)
                build_pdf(volume, "a4", True)
                build_pdf(volume, "16k", True)
                build_epub(volume, True)
            if args.volume == "all":
                build_downloads(DIST / "site")
            return build_check()
    except BuildError as exc:
        print(f"build error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
