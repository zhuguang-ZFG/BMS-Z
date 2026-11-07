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
sys.path.insert(0, str(ROOT / "tools"))

import check_curriculum  # noqa: E402
SOURCE = ROOT / "curriculum" / "concepts.json"
OUTPUT = ROOT / "docs" / "核心问题地图.md"
INDEX_OUTPUT = ROOT / "docs" / "知识点索引.md"
STATUS_LABELS = {"planned": "草案", "active": "已发布", "gap": "缺口"}
_SLUG_KEEP = re.compile(r"[^\w\s\-\u4e00-\u9fff\u0300-\u036f]", re.UNICODE)


def docs_link(path_text: str) -> str:
    path = Path(path_text)
    if path.parts and path.parts[0] == "docs":
        return Path(*path.parts[1:]).as_posix()
    return "../" + path.as_posix()


def asset_title(path_text: str) -> str:
    path = ROOT / path_text
    # 逐帧手绘导出没有可读标题：回落到同名的归档矢量源，保持图说文字不变。
    candidates = [path]
    if path.suffix.lower() != ".svg":
        candidates.append(ROOT / "docs/circuits/assets/archive" / f"{path.stem}.svg")
    path = next((c for c in candidates if c.suffix.lower() == ".svg" and c.is_file()), None)
    if path is None:
        return Path(path_text).stem
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<title>(.*?)</title>", text, re.S)
    if not match:
        return path.stem
    title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title.removesuffix("动画") or path.stem


def slugify(heading: str) -> str:
    text = unicodedata.normalize("NFC", heading).strip().lower()
    return _SLUG_KEEP.sub("", text).replace(" ", "-")


def media_label(path_text: str) -> str:
    """表里只放短名：SVG 的 <title> 常常是一整句图说，塞进单元格会把表撑爆。"""
    path = Path(path_text)
    return path.stem if path.suffix.lower() in (".svg", ".webp") else path.name


def entry_label(path_text: str) -> str:
    stem = Path(path_text).stem
    if stem.startswith("stage-"):
        stem = re.sub(r"^stage-(\d)-主线-", r"阶段 \1 · ", stem)
        stem = re.sub(r"^stage-(\d)-", r"阶段 \1 · ", stem)
    return stem


def cell(text: str) -> str:
    return re.sub(r"\s*\n\s*", " ", str(text)).replace("|", "\\|").strip()


def render(data: dict) -> str:
    concepts = sorted(data["concepts"], key=lambda row: row["order"])
    by_id = {row["id"]: row for row in concepts}
    anchors = {
        row["id"]: slugify(f"{index}. {row['question']}")
        for index, row in enumerate(concepts, 1)
    }
    lines = [
        # 本页 78 条知识点全量展开，进本地搜索索引要多 400+ KiB；站内检索改由
        # 同目录的《知识点索引》（一条一行）承担，本页排除出索引（见 BUNDLE 预算门）。
        "---",
        "search: false",
        "---",
        "",
        "# 核心问题地图：先解决一个问题，再扩成完整能力",
        "",
        f"> **本篇你会学到**　{len(concepts)} 个知识点的五级任务。先选阶段，再选一个问题；完成取回任务后核对通过标准，不用一次读完本页。",
        ">",
        "> **怎么用**　不要先把资源从头扫一遍。选一个现在最想解决的问题，先押答案，再按“先懂 → 会算 → 会做”走完，最后回到同一道题复答。",
        ">",
        "> **站内搜索**　本页不进退首页的检索索引（篇幅太大）。按关键词找题请用[知识点索引](知识点索引.md)，再点回这里的锚点。",
        "",
        "<!-- 本页由 curriculum/concepts.json 生成；请运行 python tools/gen_curriculum_pages.py，不要手改正文。 -->",
        "",
        f"课程图版本 **v{data['version']}**，更新于 **{data['updated']}**。每题明确难度、先修、预计时间和交付物；`python tools/check_curriculum.py` 同时检查课程数据、跨媒介文件、视频段、先修环路与本页是否漂移。",
        "",
    ]
    lines += ["## 按阶段找问题", "", "| 阶段 | 知识点 |", "|---|---|"]
    for stage_no in sorted({row["stage_no"] for row in concepts}):
        links = " · ".join(
            f"[{row['title']}](#kp-{row['id']})"
            for row in concepts if row["stage_no"] == stage_no
        )
        lines.append(f"| {stage_no} | {links} |")
    lines += ["", "已发布表示学习任务和证据入口已备齐，不表示已经通过陌生读者试读或产品验证。", ""]
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
            f'<a id="kp-{concept["id"]}"></a>',
            "",
            f"### {number}. {concept['question']}",
            "",
            f"`{concept['title']}` · `阶段 {concept['stage_no']}` · `{concept['level']}` · `难度 {difficulty}` · `约 {concept['estimated_minutes']} 分钟` · `{status}`",
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
        if explanation := concept.get("explanation"):
            lines += ["", "**把原因讲清楚**", "", explanation["mechanism"], "",
                      "**跟着这组输入算一遍**", ""]
            lines += [f"{i}. {step}" for i, step in enumerate(explanation["worked_steps"], 1)]
            lines += ["", f"**什么时候不能套用**　{explanation['boundary']}", "",
                      f"**看图盯这里**　{explanation['watch_for']}", ""]
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
            lines += ["- **动手**：完成本题纸笔或证据审查任务；无需硬件，不以模拟替代实测。"]
        lines += [
            f"- [ ] **交付**　{concept['deliverable']}",
            f"- **知识点 ID**：`{concept['id']}`",
            f"- **课后复答**：{concept['checkpoint']}",
        ]
        if ladder := concept.get("ladder"):
            evidence = " / ".join(concept["mastery_evidence"])
            lines += [
                "",
                f"**五级梯子**　主线承诺到 `{concept['bloom_ceiling']}`；L4/L5 用于判断与交付。精通证据：{evidence}。先作答，再核对通过标准。",
                "",
                "| 级 | 目标 | 入口 | 取回任务 | 通过标准 | 媒介 |",
                "|---|---|---|---|---|---|",
            ]
            for level in ("L1", "L2", "L3", "L4", "L5"):
                node = ladder[level]
                path_text, _, anchor = node["entry_path"].partition("#")
                entry = f"[{entry_label(path_text)}]({docs_link(path_text)}{f'#{anchor}' if anchor else ''})"
                media = " · ".join(
                    f"[{media_label(item)}]({docs_link(item)})" for item in node["media"]
                )
                lines.append(
                    f'| <a id="kp-{concept["id"]}-{level.lower()}"></a>{level} | {cell(node["goal"])} | {entry} | {cell(node["retrieve_task"])} '
                    f"| {cell(node['pass_check'])} | {media} |"
                )
        if next_ids := concept.get("next"):
            next_links = " · ".join(
                f"[{by_id[item]['title']}](#kp-{item})" for item in next_ids
            )
            lines += ["", f"**下一知识点**：{next_links}"]
        lines += ["", ""]
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


ROUTES = {
    "A": "做一块 3–4 串保护板，并实测保护动作",
    "B": "把商用 BMS 的数据读到手机 / Home Assistant",
    "C": "只做 SOC/SOH 算法，全程不碰硬件",
    "D": "逆向一台不开放协议的商用 BMS",
    "E": "自己做一块 8–16 串智能 BMS（AFE + MCU）",
    "F": "往产品级 / 车规靠：功能安全与量产",
}
# 能力地图的六层与梯子级的映射：评价并入 L4，创造 = L5（SPEC §9.4）。
BLOOM_TO_LADDER = (
    ("记忆", "L1"),
    ("理解", "L2"),
    ("应用", "L3"),
    ("分析 / 评价", "L4"),
    ("创造", "L5"),
)
# 每类生成块在目标文件里缺标记时用的二级标题。
HEADINGS = {
    "kp-routes": "每条路线的知识点序列",
    "kp-bloom": "知识点梯子入口",
    "kp-backlink": "本讲服务知识点",
    "kp-audit": "现库知识点清单与配额（自动生成）",
}


def kp_link(concept_id: str, prefix: str) -> str:
    return f"{prefix}核心问题地图.md#kp-{concept_id}"


def render_index(data: dict) -> str:
    """站内检索入口：一条一行，进本地搜索索引；详情仍在核心问题地图的锚点上。"""
    concepts = sorted(data["concepts"], key=lambda row: row["order"])
    lines = [
        f"# 知识点索引：{len(concepts)} 条知识点的稳定入口",
        "",
        "> **这是什么**　[核心问题地图](核心问题地图.md)篇幅太大，不进站内检索索引；"
        "这一页一条一行，专门给搜索和深链用。点 ID 直接落到该知识点的五级梯子。",
        "",
        "| # | 阶段 | 知识点 ID | 问题 | 梯子到 |",
        "|---:|---:|---|---|---|",
    ]
    for number, row in enumerate(concepts, 1):
        lines.append(
            f"| {number} | {row['stage_no']} | [`{row['id']}`](核心问题地图.md#kp-{row['id']}) "
            f"| {cell(row['question'])} | {row['bloom_ceiling']} |"
        )
    lines += [
        "",
        "## 从哪条路线走",
        "",
        "- 六条任务导向捷径：[按目标选路线](stages/按目标选路线.md)",
        "- 六层能力地图：[bloom-map](stages/bloom-map.md)",
        "- 配额与缺口现状：[KP 缺口审计](kp_gap_audit.md)",
        "",
        "<!-- 本页由 curriculum/concepts.json 生成；请运行 python tools/gen_curriculum_pages.py，不要手改。 -->",
        "",
    ]
    return "\n".join(lines)


def block_routes(concepts: list[dict]) -> str:
    """六条捷径 = KP 子集路径；每条列出 id 序列（SPEC §9.4）。"""
    unknown = sorted(
        {letter for row in concepts for letter in row.get("routes", []) if letter not in ROUTES}
    )
    if unknown:
        raise SystemExit(f"routes 里出现未知路线代号：{unknown}；只允许 {sorted(ROUTES)}")
    lines = [
        "以下序列由 `curriculum/concepts.json` 的 `routes` 字段生成，"
        "与[核心问题地图](../核心问题地图.md)逐条对应；改课程图只改 JSON，不要手改这一节。",
        "",
    ]
    for letter, title in ROUTES.items():
        members = [row for row in concepts if letter in row.get("routes", [])]
        if not members:
            raise SystemExit(f"路线 {letter} 没有任何知识点；先补 curriculum/concepts.json 的 routes")
        lines += [
            f"### 路线 {letter}：{title}",
            "",
            "| # | 知识点 ID | 标题 | 阶段 | 梯子到 |",
            "|---:|---|---|---:|---|",
        ]
        for number, row in enumerate(members, 1):
            lines.append(
                f"| {number} | [`{row['id']}`]({kp_link(row['id'], '../')}) | {cell(row['title'])} "
                f"| {row['stage_no']} | {row['bloom_ceiling']} |"
            )
        lines += ["", f"共 {len(members)} 个知识点。", ""]
    return "\n".join(lines).rstrip() + "\n"


def block_bloom(concepts: list[dict]) -> str:
    """能力地图每层入口指向 KP 梯子对应级（SPEC §9.4）。"""
    lines = [
        "下面的入口由 `curriculum/concepts.json` 的 `ladder` 生成："
        "每层落到知识点的同名梯子级，不再只是散落的小节目录。"
        "`分析 / 评价` 合并到 L4，`创造` 对应 L5。",
        "",
    ]
    for bloom, level in BLOOM_TO_LADDER:
        lines += [
            f"### {bloom}（梯子 {level}）",
            "",
            "| 阶段 | 知识点 |",
            "|---:|---|",
        ]
        for stage_no in sorted({row["stage_no"] for row in concepts}):
            members = [row for row in concepts if row["stage_no"] == stage_no]
            if not members:
                continue
            links = " · ".join(
                f"[{cell(row['title'])}]({kp_link(row['id'], '../')}-{level.lower()})"
                for row in members
            )
            lines.append(f"| {stage_no} | {links} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def block_backlinks(concepts: list[dict]) -> dict[str, list[dict]]:
    """伴读书章节要回链的 KP，按章节分组（SPEC §9.4）。"""
    grouped: dict[str, list[dict]] = {}
    for row in concepts:
        grouped.setdefault(row["book"]["path"], []).append(row)
    return {path: sorted(members, key=lambda row: row["order"]) for path, members in grouped.items()}


def book_block(members: list[dict], table_no: str | None, figure_start: int = 1) -> str:
    """章节尾部的回链表。

    `table_no` 是本章的表格序号：`bms-book/check.py` 要求每张表都带 `**表 N-k**`
    标题且按出现顺序连续编号，所以生成时把序号算准（None 表示该章不吃这条规则）。
    """
    lines = [
        f"本章服务 {len(members)} 个知识点；每条都能回到"
        "[核心问题地图](../../docs/核心问题地图.md)的 L1–L5 五级入口。"
        "这一节由 `curriculum/concepts.json` 的 `book` 字段生成。",
        "",
    ]
    if table_no is not None:
        lines.append(f"**表 {table_no}**　本章服务的知识点与其梯子入口")
        lines.append("")
    lines += [
        "| 知识点 ID | 标题 | 阶段 | 梯子到 | 握证 |",
        "|---|---|---:|---|---|",
    ]
    for row in members:
        lines.append(
            f"| [`{row['id']}`]({kp_link(row['id'], '../../docs/')}) | {cell(row['title'])} "
            f"| {row['stage_no']} | {row['bloom_ceiling']} | {' / '.join(row['mastery_evidence'])} |"
        )
    figure_no = figure_start
    for row in members:
        if not (explanation := row.get("explanation")):
            continue
        lines += ["", f"**{row['title']}：{row['question']}**", "", explanation["mechanism"], "",
                  "**沿着这组输入做一遍**", ""]
        lines += [f"{i}. {step}" for i, step in enumerate(explanation["worked_steps"], 1)]
        lines += ["", f"**边界与反例**　{explanation['boundary']}", "",
                  f"**看图任务**　{explanation['watch_for']}", ""]
        lines += ["**对应图解**　" + " · ".join(
            f"[{media_label(path)}](../../{path})"
            for path in row["animations"]
        ), ""]
        if illustration := explanation.get("illustration"):
            chapter = str(int(Path(row["book"]["path"]).name[:2]))
            lines += ["<figure>", f'<img src="../assets/{illustration}" alt="手绘原理示意：{row["title"]}" width="960" height="560">',
                      f"<figcaption>图 {chapter}-{figure_no}　{row['title']}。原理示意 / 非实拍；数字沿用本节教学条件，不作产品参数。</figcaption>",
                      "</figure>", ""]
            figure_no += 1
    return "\n".join(lines) + "\n"


def block_audit(concepts: list[dict]) -> str:
    """§9.7 的落盘表：逐条 KP 的锚点、梯子与媒体现状，全部由 concepts.json 推导。"""
    backbone = cc_backbone_ids()
    lines = [
        "本表由 `curriculum/concepts.json` 生成，字段按 SPEC §9.7："
        "`kp_id | stage_no | title | 现正文锚点 | ladder缺级 | 缺媒体 | 优先级 | status | 备注`。"
        "`ladder缺级` / `缺媒体` 由 `concepts.json` 实算：生成器与 `--check` 对全部 `active` 行"
        "复用 `check_curriculum.check_ladder`（缺级、空字段、坏锚点、缺媒介、L3 不在主线页即 FAIL），"
        "所以 `无 / 无` 是校验过的事实，不是占位；非 `active` 行在此表显示实际缺口；"
        "优先级规则：骨干 `P0`、到 L5 的 `P1`、其余 `P2`。"
        "真实的实物缺口（HIL 机架、认证现场、授权照片）与真人试读仍按 §9.5 记为未验证。",
        "",
        "| kp_id | stage | title | 现正文锚点（L3） | ladder缺级 | 缺媒体 | 优先级 | status | 备注 |",
        "|---|---:|---|---|---|---|---|---|---|",
    ]
    for row in concepts:
        entry = row["ladder"]["L3"]["entry_path"]
        path_text, _, anchor = entry.partition("#")
        link = f"[`{path_text.rsplit('/', 1)[-1]}`]({docs_link(path_text)}{f'#{anchor}' if anchor else ''})"
        priority = "P0" if row["id"] in backbone else ("P1" if row["bloom_ceiling"] == "L5" else "P2")
        note = "骨干 id 冻结" if row["id"] in backbone else f"draft {'/'.join(row.get('draft_ids', [])) or '—'}"
        missing_levels, no_media = ladder_gaps(row)
        gap_cell = " / ".join(missing_levels) if missing_levels else "无"
        media_cell = " / ".join(no_media) if no_media else "无"
        lines.append(
            f"| [`{row['id']}`]({kp_link(row['id'], '')}) | {row['stage_no']} | {cell(row['title'])} "
            f"| {link} | {gap_cell} | {media_cell} | {priority} | {row['status']} | {note} |"
        )
    stage_counts = {}
    for row in concepts:
        stage_counts[row["stage_no"]] = stage_counts.get(row["stage_no"], 0) + 1
    floors = {stage: 8 for stage in range(7)} | {7: 4}
    lines += ["", "### 阶段配额（§9.2）", "", "| 阶段 | 已入库 | 下限 | 判定 |", "|---:|---:|---:|---|"]
    for stage in sorted(stage_counts):
        count = stage_counts[stage]
        floor = floors[stage]
        lines.append(f"| {stage} | {count} | {floor} | {'达标' if count >= floor else '不足'} |")
    total = len(concepts)
    lines.append(f"| 合计 | {total} | ≥60 | {'达标' if total >= 60 else '不足'} |")
    return "\n".join(lines) + "\n"


def ladder_gaps(concept: dict) -> tuple[list[str], list[str]]:
    """按数据算「缺级 / 缺媒体」，审计表不写死「无」。"""
    ladder = concept.get("ladder")
    if not isinstance(ladder, dict):
        return list(check_curriculum.LADDER_LEVELS), []
    missing = [level for level in check_curriculum.LADDER_LEVELS if level not in ladder]
    no_media = [
        level
        for level in check_curriculum.LADDER_LEVELS
        if isinstance(ladder.get(level), dict) and not ladder[level].get("media")
    ]
    return missing, no_media


def verify_ladders(data: dict) -> list[str]:
    """把课程图校验器对骨干的梯子硬门复用到全部 active 行（SPEC §9.2）。

    生成器与 `--check` 都先过这一关：缺级、空字段、坏锚点、缺媒介、L3 不在主线页
    都会在写出任何生成物之前 FAIL，避免审计表把未校验的行报成绿。
    """
    docs = check_curriculum._load_docs_module()
    errors: list[str] = []
    for concept in data["concepts"]:
        if concept.get("status") != "active":
            continue
        local: list[str] = []
        check_curriculum.check_ladder(local, concept, docs)
        errors += [message.replace("骨干 KP", "KP") for message in local]
    return errors


def cc_backbone_ids() -> set[str]:
    """复用课程图校验器的冻结名单，避免第二份骨干清单漂移。"""
    return set(check_curriculum.BACKBONE_IDS)


def inject(path: Path, kind: str, block: str, heading: str) -> str:
    """把生成块写进目标文件的 markdown 注释标记之间；缺标记时按固定样式追加。"""
    text = path.read_text(encoding="utf-8")
    start, end = f"<!-- {kind}:start -->", f"<!-- {kind}:end -->"
    if start in text and end in text:
        head, _, rest = text.partition(start)
        _, _, tail = rest.partition(end)
        return f"{head}{start}\n{block}{end}{tail}"
    return f"{text.rstrip()}\n\n## {heading}\n\n{start}\n{block}{end}\n"


BOOK_BLOCK_RE = re.compile(
    r"\n*## 本讲服务知识点\n\n<!-- kp-backlink:start -->.*?<!-- kp-backlink:end -->\n?",
    re.S,
)
_TABLE_ROW = re.compile(r"^\|[-: |]+\|\s*$")


def table_prefix(path: Path) -> str | None:
    """章号前缀：与 `bms-book/check.py` 的表标题规则一致（07 → 7、附录A → A）。"""
    name = path.name
    if len(name) > 2 and name[:2].isdigit() and name[:2] != "00":
        return str(int(name[:2]))
    if name.startswith("附录"):
        return name[2]
    return None


def count_tables(text: str) -> int:
    """按 check.py 的口径数表：一行 `|---|` 且上一行以 `|` 开头算一张表。"""
    lines = text.splitlines()
    total = 0
    for index, line in enumerate(lines):
        if index == 0 or not _TABLE_ROW.match(line):
            continue
        if lines[index - 1].strip().startswith("|"):
            total += 1
    return total


def render_book_page(path: Path, members: list[dict]) -> str:
    """书稿回链块写在 `## 练习` 之前。

    `check.py` 要求新章以 `练习`、`参考资料` 收尾，且每张表都带连续编号的
    `**表 N-k**` 标题；所以块不能追加到文末，表格序号按本章已有表数推出来。
    """
    text = path.read_text(encoding="utf-8")
    if "kp-backlink:start" in text:
        text = BOOK_BLOCK_RE.sub("\n", text)
    marker = "\n## 练习\n"
    if marker not in text:
        raise SystemExit(f"{path.relative_to(ROOT).as_posix()}：找不到 `## 练习`，无法定位回链块")
    index = text.index(marker)
    head, tail = text[:index].rstrip("\n"), text[index + 1:]
    tables_after = count_tables(tail)
    if tables_after:
        raise SystemExit(f"{path.relative_to(ROOT).as_posix()}：练习/参考资料里有 {tables_after} 张表，表序号无法从正文推算")
    prefix = table_prefix(path)
    number = count_tables(head) + 1 if prefix else None
    figure_start = len(re.findall(r"<figcaption>\s*图 \d+-\d+", head)) + 1
    block = book_block(members, f"{prefix}-{number}" if prefix else None, figure_start)
    injected = f"## 本讲服务知识点\n\n<!-- kp-backlink:start -->\n{block}<!-- kp-backlink:end -->\n"
    return f"{head}\n\n{injected}\n{tail}"


def build_targets(data: dict) -> list[tuple[Path, str, str | list[dict]]]:
    concepts = sorted(data["concepts"], key=lambda row: row["order"])
    targets: list[tuple[Path, str, str | list[dict]]] = [
        (ROOT / "docs" / "stages" / "按目标选路线.md", "kp-routes", block_routes(concepts)),
        (ROOT / "docs" / "stages" / "bloom-map.md", "kp-bloom", block_bloom(concepts)),
    ]
    for path_text, members in sorted(block_backlinks(concepts).items()):
        targets.append((ROOT / path_text, "kp-backlink", members))
    targets.append((ROOT / "docs" / "kp_gap_audit.md", "kp-audit", block_audit(concepts)))
    return targets


def render_target(path: Path, kind: str, payload: str | list[dict]) -> str:
    """目标文件的完整期望文本：书稿走专属排版，其余走标记块注入。"""
    if kind == "kp-backlink":
        return render_book_page(path, payload)  # type: ignore[arg-type]
    return inject(path, kind, payload, HEADINGS[kind])  # type: ignore[arg-type]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    ladder_errors = verify_ladders(data)
    if ladder_errors:
        print("FAIL：知识点梯子未过门（全部 active 行；生成物未写出）")
        for problem in ladder_errors:
            print(f"  - {problem}")
        return 1
    expected = render(data)
    expected_index = render_index(data)
    targets = build_targets(data)
    for path, _, _ in targets:
        if not path.is_file():
            raise SystemExit(f"生成目标不存在：{path.relative_to(ROOT)}")
    if args.check:
        problems = []
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if actual != expected:
            problems.append("docs/核心问题地图.md 与 curriculum/concepts.json 不一致")
        index_actual = INDEX_OUTPUT.read_text(encoding="utf-8") if INDEX_OUTPUT.is_file() else ""
        if index_actual != expected_index:
            problems.append("docs/知识点索引.md 与 curriculum/concepts.json 不一致")
        for path, kind, payload in targets:
            want = render_target(path, kind, payload)
            if path.read_text(encoding="utf-8") != want:
                problems.append(f"{path.relative_to(ROOT).as_posix()} 的 {kind} 块与 concepts.json 不一致")
        if problems:
            print("FAIL：课程图与生成物不一致；运行 python tools/gen_curriculum_pages.py")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print(
            f"PASS：核心问题地图由 {len(data['concepts'])} 个概念生成且无漂移；"
            f"{len(ROUTES)} 条路线、{len(BLOOM_TO_LADDER)} 层能力地图、{len(targets) - 3} 章书稿回链、配额表与知识点索引同步"
        )
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    INDEX_OUTPUT.write_text(expected_index, encoding="utf-8")
    for path, kind, payload in targets:
        path.write_text(render_target(path, kind, payload), encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)}、{INDEX_OUTPUT.relative_to(ROOT)} and {len(targets)} 个导航块 from {SOURCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
