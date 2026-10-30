#!/usr/bin/env python3
"""Generate the human-facing core-question map from curriculum/concepts.json."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "curriculum" / "concepts.json"
OUTPUT = ROOT / "docs" / "核心问题地图.md"
STATUS_LABELS = {"active": "已发布", "pilot": "试点", "retired": "已归档"}
_SLUG_KEEP = re.compile(r"[^\w\s\-\u4e00-\u9fff\u0300-\u036f]", re.UNICODE)


def docs_link(path_text: str) -> str:
    path = Path(path_text)
    if path.parts and path.parts[0] == "docs":
        return Path(*path.parts[1:]).as_posix()
    return "../" + path.as_posix()


def asset_title(path_text: str) -> str:
    path = ROOT / path_text
    if path.suffix.lower() != ".svg" or not path.is_file():
        return path.stem
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<title>(.*?)</title>", text, re.S)
    if not match:
        return path.stem
    title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title.removesuffix("动画") or path.stem


def slugify(heading: str) -> str:
    text = unicodedata.normalize("NFC", heading).strip().lower()
    return _SLUG_KEEP.sub("", text).replace(" ", "-")


def render(data: dict) -> str:
    concepts = sorted(data["concepts"], key=lambda row: row["order"])
    by_id = {row["id"]: row for row in concepts}
    anchors = {
        row["id"]: slugify(f"{index}. {row['question']}")
        for index, row in enumerate(concepts, 1)
    }
    lines = [
        "# 核心问题地图：先解决一个问题，再扩成完整能力",
        "",
        "> **本篇你会学到**　BMS-Z 最核心的十三个问题，以及每个问题对应的短解释、深读、动画、视频和练习。",
        ">",
        "> **怎么用**　不要先把资源从头扫一遍。选一个现在最想解决的问题，先押答案，再按“先懂 → 会算 → 会做”走完，最后回到同一道题复答。",
        "",
        "<!-- 本页由 curriculum/concepts.json 生成；请运行 python tools/gen_curriculum_pages.py，不要手改正文。 -->",
        "",
        f"课程图版本 **v{data['version']}**，更新于 **{data['updated']}**。每题明确难度、先修、预计时间和交付物；`python tools/check_curriculum.py` 同时检查课程数据、跨媒介文件、视频段、先修环路与本页是否漂移。",
        "",
    ]
    current_domain = None
    number = 0
    for concept in concepts:
        if concept["domain"] != current_domain:
            current_domain = concept["domain"]
            lines += [f"## {current_domain}", ""]
        number += 1
        difficulty = "★" * concept["difficulty"] + "☆" * (3 - concept["difficulty"])
        status = STATUS_LABELS[concept["status"]]
        lines += [
            f"### {number}. {concept['question']}",
            "",
            f"`阶段 {concept['stage_no']}` · `{concept['level']}` · `难度 {difficulty}` · `约 {concept['estimated_minutes']} 分钟` · `{status}`",
            "",
            f"> **课前押注**　{concept['precheck']}",
            "",
            f"**形象入口**　{concept['teaching']['hook']}",
            "",
            f"**一句话**　{concept['answer']}",
            "",
            f"- **贯穿算例**：{concept['teaching']['worked_example']}",
            f"- **最容易误解**：{concept['teaching']['misconception']}",
        ]
        prerequisites = concept["prerequisites"]
        if prerequisites:
            prereq_links = " · ".join(
                f"[{by_id[item]['question']}](#{anchors[item]})" for item in prerequisites
            )
            lines += [f"- **先修**：{prereq_links}"]
        else:
            lines += ["- **先修**：无，可直接开始"]
        lines += [
            f"- **先懂**：[{concept['stage']['label']}]({docs_link(concept['stage']['path'])})",
            f"- **深读**：[{concept['book']['label']}]({docs_link(concept['book']['path'])})",
        ]
        animation_links = " · ".join(
            f"[{asset_title(path)}]({docs_link(path)})" for path in concept["animations"]
        )
        lines += [f"- **看图**：{animation_links}"]
        video_spec = json.loads((ROOT / concept["video"]["spec"]).read_text(encoding="utf-8"))
        segment = next(
            segment for segment in video_spec["segments"] if segment["id"] == concept["video"]["segment"]
        )
        kind = "微课" if video_spec.get("kind") == "microcourse" else "视频段"
        lines += [
            f"- **{kind}**：`{concept['video']['spec']}#{segment['id']}` · {segment['title']}",
        ]
        if practice := concept.get("practice"):
            lines += [
                f"- **动手**：`{practice['command']}`",
                f"- **练习证据**：{practice['proof']}",
            ]
        else:
            lines += ["- **动手**：当前先完成纸笔或口述任务；可运行练习待补"]
        lines += [
            f"- [ ] **交付**　{concept['deliverable']}",
            f"- **课后复答**：{concept['checkpoint']}",
            "",
        ]
    lines += [
        "## 下一步",
        "",
        "- 完全零基础：从[30 分钟小实验](stages/getting-started.md)开始。",
        "- 已有明确任务：去[按目标选路线](stages/按目标选路线.md)。",
        "- 想完整走一遍：回[学习路线总纲](bms-resources.md)。",
        "- 维护课程图：只改 `curriculum/concepts.json`，再运行 `python tools/gen_curriculum_pages.py` 与 `python tools/check_curriculum.py`。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    expected = render(data)
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if actual != expected:
            print("FAIL：docs/核心问题地图.md 与 curriculum/concepts.json 不一致")
            return 1
        print(f"PASS：核心问题地图由 {len(data['concepts'])} 个概念生成且无漂移")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
