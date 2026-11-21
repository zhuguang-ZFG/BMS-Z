"""Reuse verified, unchanged body editions for a collection-only publication."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    ".github/scripts/check_search.mjs",
    ".github/workflows/deploy-pages.yml", "book/refresh_collection.py",
    "book/build_combined.py", "book/combined_epub.py", "book/combined_pdf.py",
    "book/combined_front.py", "book/reading_lab.py", "book/download_page.py",
    "book/assets/download.css", "book/assets/download.js", "book/assets/epub-reader.css",
    "book/downloads.py", "book/epub_standard.py", "book/check_compatibility.py",
    "book/README.md", "book/REFERENCE_REVIEW.md",
}


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8").strip()


def validate_changes(paths):
    invalid = [p for p in paths if p not in ALLOWED and not p.startswith("book/tests/")]
    if invalid:
        raise ValueError("正文或站点输入变化，必须全量构建：" + ", ".join(invalid))


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    run_id = os.environ.get("COLLECTION_BASE_RUN", "")
    if not run_id.isdecimal():
        raise ValueError("collection_base_run must be a numeric run ID")
    repo = os.environ["GITHUB_REPOSITORY"]
    base = json.loads(run("gh", "api", f"repos/{repo}/actions/runs/{run_id}"))
    if base["conclusion"] != "success" or base["path"] != ".github/workflows/deploy-pages.yml":
        raise ValueError("只接受成功的 deploy-pages 全量发布")
    sha = base["head_sha"]
    # Only this optional reuse path needs commit ancestry. Keep ordinary Pages
    # checkouts shallow and do not fetch release tags for this comparison.
    if run("git", "rev-parse", "--is-shallow-repository") == "true":
        run("git", "fetch", "--no-tags", "--unshallow", "origin")
    run("git", "merge-base", "--is-ancestor", sha, "HEAD")
    validate_changes(run("git", "diff", "--name-only", sha, "HEAD").splitlines())
    temp = Path(os.environ["RUNNER_TEMP"]) / f"collection-base-{run_id}"
    temp.mkdir()
    run("gh", "run", "download", run_id, "--repo", repo, "--name", "github-pages", "--dir", str(temp))
    site = ROOT / "book/dist/site"
    site.mkdir(parents=True, exist_ok=True)
    with tarfile.open(temp / "artifact.tar") as archive:
        archive.extractall(site, filter="data")
    downloads = site / "downloads"
    manifest = json.loads((downloads / "downloads.json").read_text(encoding="utf-8"))
    old_report = downloads / "combined-build-report.json"
    if digest(old_report) != manifest["combined_build_report"]["sha256"]:
        raise ValueError("基线构建记录哈希不匹配")
    baseline = json.loads(old_report.read_text(encoding="utf-8"))
    if baseline["git_commit"] != sha or baseline.get("source_release"):
        raise ValueError("基线必须是该提交的全量构建，不能串接增量发布")
    restored = []
    names = {"html": "book.html", "a4": "book-a4.pdf", "epub": "book.epub"}
    for item in manifest["files"]:
        if item["volume"] not in {"volume-1", "volume-2"}:
            continue
        source = downloads / item["latest"]
        if source.parent != downloads or digest(source) != item["sha256"]:
            raise ValueError("基线分卷文件哈希不匹配")
        dest = ROOT / "book/dist" / item["volume"] / names[item["kind"]]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        restored.append(dest.relative_to(ROOT).as_posix())
    if len(set(restored)) != 6:
        raise ValueError("必须恢复两卷全部六份文件")
    run(sys.executable, "book/build_combined.py")
    report_path = ROOT / "book/dist/combined/combined-build-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["source_release"] = {"run_id": run_id, "git_commit": sha,
                                "report_sha256": digest(old_report),
                                "unchanged_volume_files": restored}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run(sys.executable, "book/downloads.py", "--site-dir", str(site))
    # Search checks compare the published index with generated source pages.
    # A fresh checkout has none of these ignored pages; restore them from the
    # unchanged inputs rather than silently omitting them from the audit.
    for script in ("prepare-stage0", "prepare-stage2", "prepare-stage3",
                   "prepare-stage4", "prepare-stage5", "prepare-stage6",
                   "prepare-volume-1", "prepare-book"):
        run("node", f"docs/.vitepress/{script}.mjs")
    print(f"PASS: collection rebuilt; six unchanged body files verified against run {run_id}")


if __name__ == "__main__":
    main()
