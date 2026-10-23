#!/usr/bin/env python3
"""BMS 书稿质量门：结构契约校验 + 清单内 demo 全跑。

用法：python check.py
全部通过 exit 0；任何失败 exit 1 并逐条列出。
"""

from pathlib import Path
import re
import subprocess
import sys
import json
import os

from build_html import PARTS, MANIFEST

ROOT = Path(__file__).resolve().parent
BOOK = ROOT / "book"
ASSETS = ROOT / "assets"

# v0.3 扩写与 v0.4 升级版章节，执行完整契约检查；更早的章节只查普适不变量。
NEW_CHAPTERS = {"03", "04", "06", "08", "09", "11", "15", "16", "19",
                "20", "21", "22", "23", "24", "25", "26", "31", "32"}

EXPECTED_FILES = [name for _, _, _, files in PARTS for name in files]
CHAPTER_NUMBERS = {int(name[:2]) for name in EXPECTED_FILES if name[:2].isdigit() and name[:2] != "00"}
CHAPTER_RE = re.compile(r"^# 第 (\d{1,2}) 章 ")
OPEN_RE = re.compile(r"^::: (story|principle|trap|lab)")
CLOSE_RE = re.compile(r"^:::\s*$")
FIG_RE = re.compile(r"<figure>.*?</figure>", re.S)
FIGCAP_RE = re.compile(r"图 (\d+)-(\d+)")
IMG_SRC_RE = re.compile(r'<img src="assets/([^"]+)"')
REF_RE = re.compile(r"第\s*([0-9、，,\s–\-]+?)\s*章")

# 书中引用、demo 输出必须钉死的数字：stdout 必须出现这些子串。
# 实现改了、数字 legitimately 变了，就要同步改这里与正文（书 ↔ demo 不许多头漂移）。
DEMO_ASSERTIONS = {
    "soc_coulomb_ocv.py": ["51.90%", "46.15%"],
    "ekf_soc.py": ["9.4605%", "0.1382%"],
    "hppc_fit.py": ["0.47%", "17.5%"],
    "frame_parser.py": ["2 1 0 1 5"],
    "thermal_lump.py": ["31.117", "2.424"],
    "cccv_charge.py": ["48 min", "29 min"],
    "ic_dv.py": ["SOH 90%"],
    "balancing_energy.py": ["25.0", "0.5"],
    "data_audit.py": ["3/3 defects caught"],
    "insulation_bridge.py": ["11/11 checks"],
    "pybamm_fit.py": ["30.20", "14.32", "19.87"],
    "uds_demo.py": ["67 02", "7F 27 35"],
}

failures = []


def fail(msg: str) -> None:
    failures.append(msg)


def check_fileset() -> None:
    actual = sorted(p.name for p in BOOK.glob("*.md"))
    expected = sorted(EXPECTED_FILES)
    for extra in set(actual) - set(expected):
        fail(f"文件集：book/ 中多余文件 {extra}")
    for missing in set(expected) - set(actual):
        fail(f"文件集：book/ 缺少 {missing}")


def check_chapter(name: str, text: str) -> None:
    stem = name.split("-")[0]
    lines = text.splitlines()
    m = CHAPTER_RE.match(lines[0]) if lines else None
    if not m:
        fail(f"{name}：首行不是『# 第 N 章 …』格式：{lines[0] if lines else '(空)'}")
        return
    if int(m.group(1)) != int(stem):
        fail(f"{name}：首行章号 {m.group(1)} 与文件名前缀 {stem} 不一致")

    opens = [m.group(1) for line in lines if (m := OPEN_RE.match(line))]
    closes = sum(1 for line in lines if CLOSE_RE.match(line))
    if len(opens) != closes:
        fail(f"{name}：callout 围栏不配对（开 {len(opens)} / 闭 {closes}）")
    if "story" not in opens:
        fail(f"{name}：缺少 story 开篇 callout")

    if stem in NEW_CHAPTERS:
        if not 85 <= len(lines) <= 115:
            fail(f"{name}：行数 {len(lines)} 超出 85–115 契约带")
        sections = [line[3:] for line in lines if line.startswith("## ")]
        for k in range(1, 7):
            want = f"{int(stem)}.{k}"
            if not any(s == want or s.startswith(want + " ") for s in sections):
                fail(f"{name}：缺少小节 ## {want}")
        if len(sections) < 8 or sections[-2] != "练习" or sections[-1] != "参考资料":
            fail(f"{name}：小节结构异常（{len(sections)} 个 ##，末两个 {sections[-2:]}）")
        if not 4 <= len(opens) <= 5:
            fail(f"{name}：callout 总数 {len(opens)} 不在 4–5")
        if "$" in text:
            fail(f"{name}：新章不允许出现 $（MathJax 会吞掉）")
        if "![" in text:
            fail(f"{name}：新章不允许 markdown 图片语法，图用 raw HTML figure")
        ex = re.search(r"## 练习\n(.*?)\n## ", text, re.S)
        n_ex = len(re.findall(r"^\d+\. ", ex.group(1), re.M)) if ex else 0
        if n_ex != 3:
            fail(f"{name}：练习 {n_ex} 题，应为 3")
        ref = re.search(r"## 参考资料\n(.*?)$", text, re.S)
        n_ref = len(re.findall(r"^- ", ref.group(1), re.M)) if ref else 0
        if not 2 <= n_ref <= 4:
            fail(f"{name}：参考资料 {n_ref} 条，应为 2–4")


def check_figures(name: str, text: str) -> None:
    stem = int(name.split("-")[0])
    seq = 0
    for fig in FIG_RE.findall(text):
        cap = FIGCAP_RE.search(fig)
        if cap:
            seq += 1
            ch, idx = int(cap.group(1)), int(cap.group(2))
            if ch != stem:
                fail(f"{name}：图号 图 {ch}-{idx} 与章号 {stem} 不符")
            if idx != seq:
                fail(f"{name}：图号 图 {ch}-{idx} 序号应为 {seq}")
        for src in IMG_SRC_RE.findall(fig):
            if not (ASSETS / src).exists():
                fail(f"{name}：引用资产 assets/{src} 不存在")


def check_refs(name: str, text: str) -> None:
    for m in REF_RE.finditer(text):
        for tok in re.split(r"[、，,\s–\-]+", m.group(1)):
            if not tok:
                continue
            if int(tok) not in CHAPTER_NUMBERS:
                fail(f"{name}：交叉引用『第 {m.group(1).strip()} 章』含越界章号 {tok}")


def check_assets() -> None:
    svgs = sorted(p.name for p in ASSETS.glob("*.svg"))
    referenced = set()
    for name in EXPECTED_FILES:
        if not (BOOK / name).is_file():
            continue
        referenced.update(IMG_SRC_RE.findall((BOOK / name).read_text(encoding="utf-8")))
    for orphan in set(svgs) - referenced:
        fail(f"资产：assets/{orphan} 未被任何章节引用")
    for missing in referenced - set(svgs):
        fail(f"资产：章节引用的 assets/{missing} 不存在")


def check_demos() -> None:
    scripts = sorted((ROOT / "code").glob("*.py"))
    expected = set(MANIFEST["demos"])
    actual = {script.name for script in scripts}
    for missing in sorted(expected - actual):
        fail(f"demo：缺少 {missing}")
    for extra in sorted(actual - expected):
        fail(f"demo：{extra} 未登记到 manifest.json")
    for s in scripts:
        r = subprocess.run(
            [sys.executable, str(s)], capture_output=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=60,
        )
        if r.returncode != 0:
            fail(f"demo：{s.name} 退出码 {r.returncode}\n{r.stdout[-1200:]}{r.stderr[-1200:]}")
            continue
        out = r.stdout or ""
        for needle in DEMO_ASSERTIONS.get(s.name, []):
            if needle not in out:
                fail(f"demo：{s.name} 输出缺少钉死数字 {needle!r}（书中引用了它，改实现就要一起改）")


def check_version() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    rv = re.search(r"版本：v([\d.]+)", readme)
    if not rv or rv.group(1) != manifest["version"]:
        fail("版本：README 与 manifest.json 不一致")


def main() -> None:
    failures.clear()
    check_fileset()
    for name in EXPECTED_FILES:
        if not (BOOK / name).is_file():
            continue
        text = (BOOK / name).read_text(encoding="utf-8")
        if name[:2].isdigit() and name[:2] != "00":
            check_chapter(name, text)
        if name[:2].isdigit():
            check_figures(name, text)
        check_refs(name, text)
    check_assets()
    check_demos()
    check_version()

    if failures:
        print(f"FAIL ({len(failures)}):")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"PASS：文件集 / 章结构 / 围栏 / 图号 / 交叉引用 / 资产 / {len(MANIFEST['demos'])} demo / 版本 一致")


if __name__ == "__main__":
    main()
