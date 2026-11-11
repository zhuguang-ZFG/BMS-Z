#!/usr/bin/env python3
"""统一成书入口（设计 §7）。P2 进行中：卷 I 四类介质已接通，卷 II 16K 待补。

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
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
DIST = BOOK / "dist"
PY = sys.executable

HTML_LIMITS_BYTES = {"I": 24 * 1024 * 1024, "II": 32 * 1024 * 1024}
MAX_PRINT_PAGES = 700

EXPECTED = {
    "I": ["book.html", "book-a4.pdf", "book-16k-1.pdf", "book-16k-2.pdf", "book.epub"],
    "II": ["book.html", "book-a4.pdf", "book-16k-1.pdf", "book.epub"],
}
VOLUME_DIR = {"I": DIST / "volume-1", "II": DIST / "volume-2"}


class BuildError(RuntimeError):
    """构建或审计失败。"""


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(cmd), f"(cwd={cwd.relative_to(ROOT)})")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise BuildError(f"命令失败（exit {result.returncode}）：{' '.join(cmd)}")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_artifact(src: Path, dst: Path) -> Path:
    if not src.is_file():
        raise BuildError(f"构建器没有产出预期文件：{src}")
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)
    return dst


def volumes(choice: str) -> list[str]:
    return ["I", "II"] if choice == "all" else [choice]


def build_html(volume: str, no_build: bool) -> None:
    out = VOLUME_DIR[volume]
    if volume == "I":
        cmd = [PY, "analog-book/build_book.py"]
        if no_build:
            cmd.append("--no-build")
        run(cmd, cwd=ROOT / "analog")
        copy_artifact(ROOT / "analog/analog-book/dist/analog-circuit-book.html",
                      out / "book.html")
        return
    ensure_dir(out)
    run([PY, "bms-book/build_html.py", "--out-dir", str(out)])
    produced = out / "bms-book.html"
    if not produced.is_file():
        raise BuildError(f"构建器没有产出预期文件：{produced}")
    produced.replace(out / "book.html")


def build_pdf(volume: str, fmt: str, no_build: bool) -> None:
    out = VOLUME_DIR[volume]
    if fmt == "a4":
        if volume == "I":
            cmd = [PY, "analog-book/build_book.py", "--pdf"]
            if no_build:
                cmd.append("--no-build")
            run(cmd, cwd=ROOT / "analog")
            copy_artifact(ROOT / "analog/analog-book/dist/analog-circuit-book.pdf",
                          out / "book-a4.pdf")
            return
        ensure_dir(out)
        run([PY, "bms-book/build_html.py", "--pdf", "--out-dir", str(out)])
        produced = out / "bms-book.pdf"
        if not produced.is_file():
            raise BuildError(f"构建器没有产出预期文件：{produced}")
        produced.replace(out / "book-a4.pdf")
        rebuilt_html = out / "bms-book.html"
        if rebuilt_html.is_file():
            rebuilt_html.replace(out / "book.html")
        return

    if volume == "II":
        ensure_dir(out)
        run([PY, "bms-book/build_print_book.py", "--out-dir", str(out)])
        produced = out / "bms-book.pdf"
        if not produced.is_file():
            raise BuildError(f"构建器没有产出预期文件：{produced}")
        produced.replace(out / "book-16k-1.pdf")
        for extra in ("bms-book.html", "bms-book.md"):
            (out / extra).unlink(missing_ok=True)
        return
    run([PY, "analog-book/build_print_book.py", *(["--no-build"] if no_build else [])],
        cwd=ROOT / "analog")
    run([PY, "analog-book/build_print_book.py", "--volumes", "--pdf",
         *(["--no-build"] if no_build else [])], cwd=ROOT / "analog")
    print_dir = ROOT / "analog/analog-book/dist/print"
    for index, name in ((1, "volume-1"), (2, "volume-2")):
        copy_artifact(print_dir / name / "analog-circuit-book.pdf",
                      out / f"book-16k-{index}.pdf")


def build_epub(volume: str, no_build: bool) -> None:
    out = VOLUME_DIR[volume]
    if volume == "I":
        run([PY, "scripts/build_epub.py"], cwd=ROOT / "analog")
        copy_artifact(ROOT / "analog/analog-book/dist/analog-circuit-book.epub",
                      out / "book.epub")
        return
    ensure_dir(out)
    run([PY, "bms-book/build_epub.py", "--out-dir", str(out)])
    produced = out / "bms-book.epub"
    if not produced.is_file():
        raise BuildError(f"构建器没有产出预期文件：{produced}")
    produced.replace(out / "book.epub")


def build_site(no_build: bool) -> None:
    if not no_build:
        npm = shutil.which("npm") or "npm"
        run([npm, "run", "docs:build"], cwd=ROOT)
    src = ROOT / "docs/.vitepress/dist"
    if not src.is_dir():
        raise BuildError(f"站点产物不存在：{src}（先跑 python book/build.py site）")
    dst = DIST / "site"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"site -> {dst} ({sum(p.stat().st_size for p in dst.rglob('*') if p.is_file())} bytes)")


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
        elif args.command == "all":
            build_site(args.no_build)
            for volume in volumes(args.volume):
                build_html(volume, args.no_build)
                build_pdf(volume, "a4", True)
                build_pdf(volume, "16k", True)
                build_epub(volume, True)
            return build_check()
    except BuildError as exc:
        print(f"build error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
