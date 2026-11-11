#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视觉资产 manifest 闸：登记齐全、来源可回对、prompt 可追溯、
纸雕类定量图四条规矩逐项申报。

`--bootstrap-legacy`：把磁盘上尚未登记的 svg/图形/照片补成
`legacy-unreviewed` 条目（幂等，只增不改）。
默认模式：校验全部条目；任何违规退出码 1。
"""
from __future__ import annotations

import argparse
import copy
import math
import re
import sys
from pathlib import Path

import yaml

from visual_fidelity import number_gaps, source_excerpt, visible_text, visible_number_gaps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "superpowers" / "visual" / "visual-manifest.yml"
LOCK = ROOT / "docs" / "superpowers" / "visual" / "handraw-style-lock.md"

KINDS = {"figure", "animation", "photo"}
TYPES = {f"V{n}" for n in range(1, 7)} | {f"A{n}" for n in range(1, 6)}
STATUSES = ["legacy-unreviewed", "planned", "generated", "reviewed",
            "accepted", "published"]
REVIEWED = {"reviewed", "accepted", "published"}
SCORE_DIMS = ["教学必要性", "事实精度", "构图层级", "风格一致性", "印刷可读性"]
ANIM_DIMS = ["运动叙事", "交互节奏"]
ANIM_TOTAL_FLOOR = 30          # 规格 §评分：动画七项总分至少 30/35
NUMBER = re.compile(r"\d")

# 定量图四条规矩（2026-11-05 FF-015 试片失分换来，见 reviews/pilot-decision.md）。
# 灰度实测：纸↔墨 10.42、纸↔石板灰 5.45、纸↔柿子橙 4.40、墨↔柿子橙 2.37、
# 石板灰↔柿子橙 1.24——所以重点色只能落在纸上，多曲线不能只靠颜色。
QUANT_TYPES = {"V3", "V5"}
# 四条规矩是**纸雕类画风**才有的毛病：层高是一叠纸的物理厚度，读者会把它当成
# 纵轴读，量值一放上去就两套语义打架；FA-029 那批平面线稿没有这层错觉，不在此闸内。
PAPERCUT_STYLES = {"FF-015"}
NONCOLOR_CHANNELS = {"lineweight", "dash", "marker", "order", "label"}
QUANT_RULES = {
    "layer_encodes_value": "规则①层高不得编码数值：必须显式写 false",
    "value_channel": "规则①量值只由 SVG overlay 的坐标轴与标签编码：须为 overlay-axis",
    "leader_route": "规则②标注引线不得跨过主体：须为 margin 或 outside",
    "accent_on": "规则③重点色只落纸白区：须为 paper（压石板灰只有 1.24:1）",
    "series_distinguisher": "规则④多条曲线不得只靠颜色：须含 "
                             + "/".join(sorted(NONCOLOR_CHANNELS)) + " 之一",
}


def quant_rule_gaps(tag: str, asset: dict) -> list[str]:
    """纸雕类画风的 V3 定量图与 V5 流程／决策图，出厂前必须逐项申报四条规矩。"""
    rules = asset.get("quant_rules")
    if not isinstance(rules, dict):
        return [f"{tag}: 缺 quant_rules（{QUANT_TYPES} 必须逐项申报四条规矩）"]
    bad = []
    if rules.get("layer_encodes_value") is not False:
        bad.append(f"{tag}: {QUANT_RULES['layer_encodes_value']}")
    if rules.get("value_channel") != "overlay-axis":
        bad.append(f"{tag}: {QUANT_RULES['value_channel']}")
    if rules.get("leader_route") not in ("margin", "outside"):
        bad.append(f"{tag}: {QUANT_RULES['leader_route']}")
    if rules.get("accent_on") != "paper":
        bad.append(f"{tag}: {QUANT_RULES['accent_on']}")
    channels = rules.get("series_distinguisher") or []
    if isinstance(channels, str):
        channels = [channels]
    if not set(channels) & NONCOLOR_CHANNELS:
        bad.append(f"{tag}: {QUANT_RULES['series_distinguisher']}")
    return bad

DISK_GLOBS = [
    ("assets/svg", "*.svg", "animation"),
    ("assets/figures", "*.svg", "figure"),
    ("assets/photos", "**/*.jpg", "photo"),
    ("assets/photos", "**/*.png", "photo"),
    ("assets/figures-v2", "*.svg", "figure"),
    ("assets/figures-v2", "*.webp", "figure"),
    ("assets/svg-v2", "*.svg", "animation"),
]


def load(path: Path = MANIFEST) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def dump(data: dict, path: Path = MANIFEST) -> None:
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8")


def disk_assets() -> list[tuple[Path, str]]:
    """调用期拼路径，保证测试替换 ROOT 后仍指向夹具目录。"""
    found = []
    for rel, pattern, kind in DISK_GLOBS:
        found += [(p, kind) for p in sorted((ROOT / rel).glob(pattern))]
    return found


def chapter_of(asset: Path) -> int:
    """正文里哪个章节引用了这个资产。"""
    rel = asset.relative_to(ROOT).as_posix()
    for doc in sorted((ROOT / "docs").glob("p*-ch*.md")):
        m = re.search(r"-ch(\d+)\.md$", doc.name)
        if m and rel in doc.read_text(encoding="utf-8"):
            return int(m.group(1))
    return -1


def legacy_id(asset: Path) -> str:
    stem = asset.stem.replace("_", "-")
    return f"legacy-{asset.parent.name}-{stem}"


def bootstrap(data: dict) -> int:
    data.setdefault("meta", {})
    data["meta"]["lock"] = LOCK.relative_to(
        Path(__file__).resolve().parents[1]).as_posix()
    data["meta"]["statuses"] = STATUSES
    assets = data.setdefault("assets", [])
    known = {a.get("output") for a in assets}
    added = 0
    for asset, kind in disk_assets():
        rel = asset.relative_to(ROOT).as_posix()
        if rel in known:
            continue
        n = chapter_of(asset)
        assets.append({
            "id": legacy_id(asset),
            "chapter": n if n >= 0 else 0,
            "kind": kind,
            "type": "A1" if kind == "animation" else "V6" if kind == "photo" else "V2",
            "anchor": "",
            "purpose": "改造前存量资产，待逐张审查（Rebuild/Retire/Keep）",
            "source_facts": [],
            "prompt_file": "",
            "output": rel,
            "print_fallback": "",
            "status": "legacy-unreviewed",
        })
        known.add(rel)
        added += 1
    return added


def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def history_gaps(asset: dict, previous: dict | None = None) -> list[str]:
    tag = asset.get("id", "<无 id>")
    history = asset.get("status_history") or []
    status = asset.get("status")
    stages = STATUSES[1:]
    if status not in stages:
        return []
    expected = stages[:stages.index(status) + 1]
    bad = []
    if history != expected:
        bad.append(f"{tag}: status_history 必须逐级迁移至 {status}: {expected}")
    if previous and previous.get("status") in stages:
        before = stages.index(previous["status"])
        after = stages.index(status)
        if after not in (before, before + 1):
            bad.append(f"{tag}: 禁止越级或回退 {previous['status']} → {status}")
    return bad


def transition(asset: dict, status: str) -> dict:
    """一次只走一个相邻阶段；评分与文件检查由调用者写盘前执行。"""
    current = asset.get("status")
    if current not in STATUSES or status not in STATUSES:
        raise ValueError("非法状态")
    if STATUSES.index(status) != STATUSES.index(current) + 1:
        raise ValueError(f"禁止越级或回退 {current} → {status}")
    result = copy.deepcopy(asset)
    result["status"] = status
    result["status_history"] = (asset.get("status_history") or []) + [status]
    return result


def animation_gaps(asset: dict) -> list[str]:
    tag = asset["id"]
    bad = []
    for field in ("beats", "duration", "conclusion_frame", "reduced_motion", "storyboard"):
        if not asset.get(field):
            bad.append(f"{tag}: 动画缺 {field}")
    parameters = asset.get("parameters")
    if not isinstance(parameters, list):
        bad.append(f"{tag}: 动画缺 parameters 列表（无扫描时显式 []）")
    elif asset.get("type") == "A3" and not parameters:
        bad.append(f"{tag}: A3 参数扫描须声明 parameters")
    else:
        for p in parameters:
            if not isinstance(p, dict) or not all(p.get(k) for k in ("name", "values", "unit")):
                bad.append(f"{tag}: parameters 须含 name、values、unit")
    try:
        duration = float(str(asset.get("duration", "")).removesuffix("s"))
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError
    except ValueError:
        bad.append(f"{tag}: duration 必须为正数秒")
        duration = 0
    beats = asset.get("beats")
    if not isinstance(beats, list) or not beats:
        bad.append(f"{tag}: beats 必须是具名时间轴")
    else:
        names = []
        end = 0
        for beat in beats:
            try:
                start, stop = float(beat["start"]), float(beat["end"])
                name = beat["name"]
                if not name or name in names or start != end or not start < stop <= duration:
                    raise ValueError
                names.append(name)
                end = stop
            except (KeyError, TypeError, ValueError):
                bad.append(f"{tag}: beats 名称须唯一且时间连续、落在 duration 内")
        if end != duration:
            bad.append(f"{tag}: beats 必须覆盖完整 duration")
        conclusion = asset.get("conclusion_frame")
        if (not isinstance(conclusion, dict) or not names
                or conclusion.get("beat") != names[-1]
                or conclusion.get("output") != asset.get("reduced_motion")):
            bad.append(f"{tag}: conclusion_frame 须指向末拍及 reduced_motion 文件")
    return bad


def animation_index(data: dict) -> dict:
    """动画表是主 manifest 的派生视图，避免两份状态源互相漂移。"""
    return {"meta": {"source": "visual-manifest.yml", "schema_version": 1},
            "assets": [copy.deepcopy(a) for a in data.get("assets", [])
                       if a.get("kind") == "animation"]}


def check(data: dict, previous: dict | None = None) -> list[str]:
    bad: list[str] = []
    assets = data.get("assets") or []
    ids = [a.get("id") for a in assets]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        bad.append(f"ID 重复: {sorted(dupes)}")
    if data.get("meta", {}).get("statuses") != STATUSES:
        bad.append("meta.statuses 与状态机不一致")
    for a in assets:
        tag = a.get("id") or "<无 id>"
        if a.get("status") not in STATUSES:
            bad.append(f"{tag}: 非法状态 {a.get('status')!r}")
        if a.get("kind") not in KINDS:
            bad.append(f"{tag}: 非法 kind {a.get('kind')!r}")
        if a.get("type") not in TYPES:
            bad.append(f"{tag}: 非法 type {a.get('type')!r}")
        ch = a.get("chapter")
        if not isinstance(ch, int) or not 0 <= ch <= 18:
            bad.append(f"{tag}: chapter {ch!r} 不在 0..18")
        output = a.get("output") or ""
        if output and a.get("status") != "planned" and not (ROOT / output).exists():
            bad.append(f"{tag}: output 不存在 {output}")
        if a.get("status") == "legacy-unreviewed":
            continue
        old = next((p for p in (previous or {}).get("assets", []) if p.get("id") == tag), None)
        bad += history_gaps(a, old)
        for field in ("anchor", "purpose", "style_id", "layout_id",
                      "color_ids", "source_facts", "prompt_file",
                      "print_fallback", "alt", "output"):
            if not a.get(field):
                bad.append(f"{tag}: 缺 {field}")
        if a.get("kind") == "animation":
            bad += animation_gaps(a)
        if a.get("status") != "planned":
            for field in ("print_fallback", "reduced_motion", "storyboard", "preview"):
                if a.get(field) and not (ROOT / a[field]).is_file():
                    bad.append(f"{tag}: {field} 不存在 {a[field]}")
            if a.get("kind") == "figure" and output.startswith("assets/figures-v2/"):
                fallback = a.get("print_fallback", "")
                if fallback == output or not fallback.endswith(".svg"):
                    bad.append(f"{tag}: V2 静态图须有独立纯 SVG print_fallback")
                elif (ROOT / fallback).is_file() and re.search(
                        r"<(?:[\w]+:)?image\b", (ROOT / fallback).read_text(encoding="utf-8")):
                    bad.append(f"{tag}: V2 print_fallback 不得包含位图 image")
        excerpts = []
        for reference in a.get("source_facts") or []:
            try:
                excerpts.append(source_excerpt(ROOT, reference))
            except ValueError as exc:
                bad.append(f"{tag}: {exc}")
        if a.get("anchor") and not any(str(a["anchor"]) in text for text in excerpts):
            bad.append(f"{tag}: anchor 未落在 source_facts 小节内")
        if (a.get("type") in QUANT_TYPES
                and a.get("style_id") in PAPERCUT_STYLES):
            bad += quant_rule_gaps(tag, a)
        prompt = a.get("prompt_file")
        if prompt:
            path = ROOT / prompt
            if not path.exists():
                bad.append(f"{tag}: prompt 记录不存在 {prompt}")
            else:
                record = front_matter(path)
                if record.get("id") != a.get("id"):
                    bad.append(f"{tag}: prompt 记录 id 不匹配")
                if not record.get("zh_prompt") or not record.get("en_prompt"):
                    bad.append(f"{tag}: prompt 缺中/英文本")
                bad += number_gaps(tag, record.get("numbers") or [],
                                   "\n".join(excerpts), visible_text(ROOT / output))
                bad += visible_number_gaps(tag, visible_text(ROOT / output),
                                           "\n".join(excerpts), record.get("numbers") or [])
        if a.get("status") in REVIEWED:
            scores = a.get("review_scores") or {}
            dims = SCORE_DIMS + (ANIM_DIMS if a.get("kind") == "animation" else [])
            for dim in dims:
                val = scores.get(dim)
                if type(val) not in (int, float) or not math.isfinite(val) or not 4 <= val <= 5:
                    bad.append(f"{tag}: 评分「{dim}」须在 4..5 内")
            if a.get("kind") == "animation" and all(type(scores.get(d)) in (int, float) for d in dims):
                total = sum(scores[dim] for dim in dims)
                if total < ANIM_TOTAL_FLOOR:
                    bad.append(f"{tag}: 动画七项合计 {total}/35 < {ANIM_TOTAL_FLOOR}")
    registered = {a.get(field) for a in assets
                  for field in ("output", "print_fallback", "reduced_motion", "storyboard", "preview")}
    for asset, _kind in disk_assets():
        rel = asset.relative_to(ROOT).as_posix()
        if rel not in registered:
            bad.append(f"磁盘资产未登记: {rel}")
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bootstrap-legacy", action="store_true")
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--previous", type=Path, help="对照旧 manifest，禁止一次跳过多个阶段")
    ap.add_argument("--transition", nargs=2, metavar=("ID", "STATUS"))
    ap.add_argument("--write-animation-index", action="store_true")
    args = ap.parse_args(argv)
    data = load(args.manifest) if args.manifest.exists() else {}
    if args.bootstrap_legacy:
        added = bootstrap(data)
        if added:
            dump(data, args.manifest)
        dump(animation_index(data), args.manifest.with_name("animation-v2-manifest.yml"))
        print(f"bootstrap: 新增 {added} 条 legacy-unreviewed，"
              f"共 {len(data.get('assets') or [])} 条")
        return 0
    if args.transition:
        tag, status = args.transition
        matches = [a for a in data.get("assets", []) if a.get("id") == tag]
        if len(matches) != 1:
            ap.error(f"ID 必须唯一存在: {tag}")
        try:
            replacement = transition(matches[0], status)
        except ValueError as exc:
            ap.error(str(exc))
        data["assets"][data["assets"].index(matches[0])] = replacement
    bad = check(data, load(args.previous) if args.previous else None)
    index_path = args.manifest.with_name("animation-v2-manifest.yml")
    if not bad and args.transition:
        dump(data, args.manifest)
    if not bad and (args.write_animation_index or args.transition):
        dump(animation_index(data), index_path)
    elif index_path.exists() and load(index_path) != animation_index(data):
        bad.append("animation-v2-manifest.yml 已漂移，请运行 --write-animation-index")
    elif not index_path.exists():
        bad.append("缺 animation-v2-manifest.yml，请运行 --write-animation-index")
    for line in bad:
        print("FAIL " + line)
    print(f"manifest: {'FAIL' if bad else 'PASS'}（{len(bad)} 项）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
