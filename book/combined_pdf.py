"""合集 PDF：独立卷首、实际章节目录、卷号页码及完整链接映射。"""

from __future__ import annotations

import re
from pathlib import Path

import fitz

from combined_front import (
    TITLE,
    VOL1_TITLE,
    VOL2_TITLE,
    GUIDE,
    colophon_sections,
    cover,
    prose_page,
    text,
)

ROWS_PER_PAGE = 22


def flat(page):
    return re.sub(r"\s+", "", page.get_text())


def shared_pages(doc):
    start = next(
        (
            i
            for i in range(1, min(len(doc), 15))
            if flat(doc[i]).startswith("从模拟电路到BMS")
        ),
        None,
    )
    if start is None:
        raise ValueError("未找到共享卷首起点，停止合并以免误删正文")
    end = next(
        (
            i
            for i in range(start + 1, min(len(doc), start + 12))
            if flat(doc[i]).startswith("版本、许可与勘误")
        ),
        None,
    )
    if end is None:
        raise ValueError("未找到共享卷首终点")
    return set(range(start, end + 1))


def source_label(doc, index, volume):
    if index == 0:
        return f"{volume}-cover"
    page = doc[index]
    footer = page.get_text(
        clip=fitz.Rect(0, page.rect.height - 70, page.rect.width, page.rect.height)
    )
    matches = re.findall(r"(?<!\d)(\d+)\s*/\s*\d+", footer)
    return f"{volume}-{matches[-1]}" if matches else f"{volume}-front-{index + 1}"


def toc_rows(doc, skipped, volume):
    rows = []
    for level, title, page in doc.get_toc():
        if page - 1 in skipped or page == 1:
            continue
        chapter = re.match(r"第\s*\d+\s*章|附录\s*[A-E]", title)
        useful = title.startswith(
            ("公式速查", "模型边界速查", "共享术语表", "索引", "前言：")
        )
        if level == 1 or (level == 2 and (chapter or useful)):
            rows.append(
                {
                    "volume": volume,
                    "title": title.strip(),
                    "source": page - 1,
                    "label": source_label(doc, page - 1, volume),
                    "level": level,
                }
            )
    return rows


def layout(docs):
    skips = [shared_pages(d) for d in docs]
    groups = [
        toc_rows(d, s, v) for d, s, v in zip(docs, skips, ("I", "II"), strict=True)
    ]
    chunks = []
    for volume, rows in zip(("I", "II"), groups, strict=True):
        chunks.extend(
            (volume, rows[i : i + ROWS_PER_PAGE])
            for i in range(0, len(rows), ROWS_PER_PAGE)
        )
    front = 3 + len(chunks)
    mappings = []
    cursor = front
    for doc, skip in zip(docs, skips, strict=True):
        mapping = {}
        for i in range(len(doc)):
            if i not in skip:
                mapping[i] = cursor
                cursor += 1
        mappings.append(mapping)
    aliases = []
    for doc, skip in zip(docs, skips, strict=True):
        aliases.append(
            {
                i: (
                    0
                    if flat(doc[i]).startswith("从模拟电路到BMS")
                    else 1
                    if flat(doc[i]).startswith("两卷怎么读")
                    else 2
                    if flat(doc[i]).startswith("版本、许可与勘误")
                    else 3
                )
                for i in skip
            }
        )
    return skips, chunks, front, mappings, aliases


def page_label_rules(labels):
    rules = []
    previous = None
    for i, label in enumerate(labels):
        match = re.fullmatch(r"(.*-)(\d+)", label)
        if match:
            prefix, num = match[1], int(match[2])
            if previous and previous[0] == prefix and previous[1] + 1 == num:
                previous = (prefix, num)
                continue
            rules.append(
                {"startpage": i, "prefix": prefix, "style": "D", "firstpagenum": num}
            )
            previous = (prefix, num)
        else:
            rules.append({"startpage": i, "prefix": label, "style": ""})
            previous = None
    return rules


def build(vol1: Path, vol2: Path, output: Path) -> dict:
    with fitz.open(vol1) as d1, fitz.open(vol2) as d2, fitz.open() as out:
        docs = [d1, d2]
        skips, chunks, front, maps, aliases = layout(docs)
        cover(out)
        prose_page(out, "两卷怎么读", GUIDE)
        prose_page(out, "版本、许可与勘误", colophon_sections())
        toc_links = []
        for volume, rows in chunks:
            page = out.new_page(width=595.28, height=841.89)
            text(page, "两卷总目录", 48, 60, 24)
            text(page, VOL1_TITLE if volume == "I" else VOL2_TITLE, 48, 94, 12)
            text(page, "章节 / 篇目", 48, 132, 10)
            text(page, "卷内页", 425, 132, 10)
            text(page, "文件页", 501, 132, 10)
            page.draw_line((48, 144), (548, 144), color=(0.09, 0.42, 0.4), width=1)
            for row_index, row in enumerate(rows):
                y = 169 + row_index * 27
                size = min(10.3, 355 / max(1, len(row["title"])))
                text(page, row["title"], 48, y, size, width=363)
                text(page, row["label"], 425, y, 9, width=72)
                dest = maps[0 if volume == "I" else 1][row["source"]]
                text(page, str(dest + 1), 511, y, 10, width=40)
                toc_links.append((page.number, fitz.Rect(46, y - 17, 550, y + 5), dest))
            text(
                page,
                "点击条目跳转。卷内页对应原书页脚；文件页从合集封面起计。",
                48,
                798,
                9,
            )
        # 只子集化新卷首使用的字体，不重压缩已有千页正文。
        out.subset_fonts()
        for volume, (doc, skip) in enumerate(zip(docs, skips, strict=True), 1):
            with fitz.open() as divider:
                cover(divider, volume)
                divider.subset_fonts()
                out.insert_pdf(divider, links=False)
            kept = [i for i in range(1, len(doc)) if i not in skip]
            start = last = kept[0]
            for index in kept[1:] + [len(doc) + 1]:
                if index == last + 1:
                    last = index
                    continue
                out.insert_pdf(doc, from_page=start, to_page=last, links=False)
                start = last = index
        copied = 0
        for doc, mapping, alias in zip(docs, maps, aliases, strict=True):
            for source, dest_page in mapping.items():
                if source == 0:
                    continue
                for link in doc[source].get_links():
                    if link.get("kind") == fitz.LINK_URI and link.get("uri"):
                        out[dest_page].insert_link(
                            {
                                "kind": fitz.LINK_URI,
                                "from": link["from"],
                                "uri": link["uri"],
                            }
                        )
                    elif link.get("page", -1) >= 0:
                        target = link["page"]
                        dest = mapping.get(target, alias.get(target))
                        if dest is None:
                            raise ValueError(f"未映射的 PDF 目标页 {target}")
                        out[dest_page].insert_link(
                            {
                                "kind": fitz.LINK_GOTO,
                                "from": link["from"],
                                "page": dest,
                                "to": link.get("to", fitz.Point(0, 0))
                                if target not in alias
                                else fitz.Point(0, 0),
                            }
                        )
                    else:
                        continue
                    copied += 1
        for source, rect, target in toc_links:
            out[source].insert_link(
                {
                    "kind": fitz.LINK_GOTO,
                    "from": rect,
                    "page": target,
                    "to": fitz.Point(0, 0),
                }
            )
        outline = [
            [1, "合集封面", 1],
            [1, "两卷怎么读", 2],
            [1, "版本、许可与勘误", 3],
            [1, "两卷总目录", 4],
        ]
        labels = [f"Front-{i + 1}" for i in range(front)]
        for volume, doc, mapping, skip, title in zip(
            ("I", "II"), docs, maps, skips, (VOL1_TITLE, VOL2_TITLE), strict=True
        ):
            outline.append([1, title, mapping[0] + 1])
            previous = 1
            for level, label, page in doc.get_toc():
                if page - 1 in skip or page == 1:
                    continue
                level = min(level + 1, previous + 1, 6)
                outline.append([level, label, mapping[page - 1] + 1])
                previous = level
            labels.extend(source_label(doc, i, volume) for i in mapping)
        out.set_toc(outline)
        out.set_page_labels(page_label_rules(labels))
        out.set_metadata(
            {
                "title": TITLE,
                "author": "zhuguang-ZFG 与贡献者",
                "subject": "两卷合集；原卷页码保留，目录列出卷内页与文件页",
                "creator": "book/build_combined.py",
            }
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        out.save(output, garbage=0, deflate=False)
        return {
            "pages": len(out),
            "front_pages": front,
            "removed_shared_pages": [len(s) for s in skips],
            "preserved_links": copied,
            "toc_links": len(toc_links),
            "bookmarks": len(outline),
            "volume_starts": [m[0] + 1 for m in maps],
        }


def validate(path: Path, vol1: Path, vol2: Path) -> dict:
    with fitz.open(vol1) as d1, fitz.open(vol2) as d2, fitz.open(path) as doc:
        sources = [d1, d2]
        skips, chunks, front, maps, aliases = layout(sources)
        expected = front + sum(len(m) for m in maps)
        if len(doc) != expected:
            raise ValueError(f"PDF 页数 {len(doc)} != {expected}")
        if doc.metadata.get("title") != TITLE:
            raise ValueError("PDF 书名错误")
        if not doc.get_page_labels():
            raise ValueError("PDF 缺少卷号页码标签")
        if (
            not flat(doc[0]).startswith("BMS-Z/")
            or "从模拟电路" not in doc[0].get_text()
        ):
            raise ValueError("PDF 合集封面错误")
        # 每个保留页逐一比较正文文本；每条原有链接比较类型、区域、目标、落点。
        checked = 0
        for volume, source, mapping, alias in zip(
            ("I", "II"), sources, maps, aliases, strict=True
        ):
            for src, dest in mapping.items():
                if doc[dest].get_label() != source_label(source, src, volume):
                    raise ValueError(f"PDF 页码标签错误: {dest + 1}")
                if src == 0:
                    continue  # 分卷封面已统一重绘。
                if flat(source[src]) != flat(doc[dest]):
                    raise ValueError(f"正文页变化: {volume}/{src + 1}")
                actual = list(doc[dest].get_links())
                for link in source[src].get_links():
                    kind = link.get("kind")
                    if kind == fitz.LINK_URI:
                        payload = link.get("uri")
                        key = "uri"
                    elif link.get("page", -1) >= 0:
                        kind = fitz.LINK_GOTO
                        payload = mapping.get(link["page"], alias.get(link["page"]))
                        key = "page"
                    else:
                        continue
                    same = next(
                        (
                            a
                            for a in actual
                            if a.get("kind") == kind
                            and a.get(key) == payload
                            and all(
                                abs(x - y) < 1
                                for x, y in zip(a["from"], link["from"], strict=True)
                            )
                        ),
                        None,
                    )
                    if same is None:
                        raise ValueError(
                            f"PDF 链接丢失: {volume}/{src + 1} -> {payload}"
                        )
                    if kind == fitz.LINK_GOTO and link["page"] not in alias:
                        want = link.get("to", fitz.Point(0, 0))
                        got = same.get("to", fitz.Point(0, 0))
                        if abs(want.x - got.x) > 1 or abs(want.y - got.y) > 1:
                            raise ValueError("PDF 链接落点偏移")
                    actual.remove(same)
                    checked += 1
                if actual:
                    raise ValueError(f"正文页出现额外链接: {dest + 1}")
        total_toc = 0
        for i, (volume, rows) in enumerate(chunks, 3):
            links = doc[i].get_links()
            targets = [maps[0 if volume == "I" else 1][row["source"]] for row in rows]
            if [link.get("page") for link in links] != targets:
                raise ValueError(f"总目录链接错误: {i + 1}")
            total_toc += len(links)
        return {
            "pages": len(doc),
            "preserved_links_checked": checked,
            "toc_links_checked": total_toc,
            "retained_text_pages_checked": sum(len(m) - 1 for m in maps),
            "page_labels": True,
        }
