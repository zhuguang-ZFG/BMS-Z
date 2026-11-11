"""16K 内文 PDF：Chromium 打印、补白、页码标签、书签、回填、天头地脚。"""
from __future__ import annotations

import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path

from . import config, fonts
from .manifest import BookError

MM = 72 / 25.4
SKIP_KINDS = {"half_title", "title_page", "copyright", "part", "chapter",
              "appendix_opener"}
FRONT_KINDS = {"half_title", "title_page", "copyright", "toc",
               "list_of_figures", "list_of_tables"}
MUTED = (0.32, 0.38, 0.44)
RULE = (0.78, 0.82, 0.86)
TAG_RE = re.compile(r"<[^>]+>")


def _roman(number: int) -> str:
    values = ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"),
              (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"),
              (5, "v"), (4, "iv"), (1, "i"))
    out = []
    for value, glyph in values:
        while number >= value:
            out.append(glyph)
            number -= value
    return "".join(out)


def _group(page: dict) -> str:
    if page.get("group"):
        return page["group"]
    kind = page["kind"]
    if kind in FRONT_KINDS:
        return "front"
    if kind in {"part", "chapter"}:
        return "body"
    if kind.startswith("appendix"):
        return "appendix"
    return "back"


def _browser_candidates(override: str | None) -> list[Path]:
    candidates = [Path(override)] if override else []
    for command in ("msedge", "chrome", "chromium"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    for raw in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ):
        candidates.append(Path(raw))
    result, seen = [], set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved not in seen and resolved.is_file():
            result.append(resolved)
            seen.add(resolved)
    return result


def print_pdf(html_path: Path, output_pdf: Path,
              browser_override: str | None = None) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BookError(
            "PDF 需要 Playwright：pip install -r analog-book/requirements.txt") from exc
    executables = _browser_candidates(browser_override)
    if browser_override and not executables:
        raise BookError(f"浏览器不存在: {browser_override}")
    launch = {"headless": True}
    if executables:
        launch["executable_path"] = str(executables[0])
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(**launch)
            try:
                context = browser.new_context(reduced_motion="reduce")
                page = context.new_page()
                page.set_default_timeout(300000)
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                page.emulate_media(media="print")
                page.evaluate(
                    "async () => {"
                    " const wait = ms => new Promise((_, reject) =>"
                    " setTimeout(() => reject(new Error('font timeout')), ms));"
                    " if (document.fonts) await Promise.race(["
                    " document.fonts.ready, wait(180000)]); }")
                if page.evaluate("() => !!window.MathJax"):
                    page.evaluate(
                        "async () => {"
                        " const wait = ms => new Promise((_, reject) =>"
                        " setTimeout(() => reject(new Error('mathjax timeout')), ms));"
                        " await Promise.race([MathJax.startup.promise, wait(120000)]); }")
                page.wait_for_function(
                    "() => Array.from(document.querySelectorAll('.arithmatex'))"
                    ".every(el => el.querySelector('mjx-container svg'))",
                    timeout=120000)
                page.wait_for_function(
                    "() => Array.from(document.images).every("
                    "img => img.complete && img.naturalWidth > 0)",
                    timeout=60000)
                page.pdf(path=str(output_pdf), print_background=True,
                         prefer_css_page_size=True, outline=True, tagged=True)
            finally:
                browser.close()
    except BookError:
        raise
    except Exception as exc:
        raise BookError(f"PDF 构建失败: {exc}") from exc
    return output_pdf


def pad_to_multiple(document, multiple: int = 4) -> list[int]:
    if document.page_count == 0:
        raise BookError("PDF 没有页面")
    remainder = document.page_count % multiple
    if remainder == 0:
        return []
    first = document.page_count
    width = document[0].rect.width
    height = document[0].rect.height
    for _ in range(multiple - remainder):
        document.new_page(width=width, height=height)
    return list(range(first, document.page_count))


def _is_blank(page) -> bool:
    return not page.get_text().strip() and not page.get_images()


def _normalize_title(text: str) -> str:
    text = html.unescape(TAG_RE.sub("", text))
    return re.sub(r"\s+", " ", text).strip()


def _page_heading(page: dict) -> tuple[int, str]:
    level = 2 if page.get("source") and page.get("group") == "appendix" else 1
    match = re.search(
        rf"<h{level}\b[^>]*>(.*?)</h{level}>", page.get("html") or "",
        re.S | re.I)
    if match is None:
        raise BookError(f"{page['id']}: 找不到 h{level} 标题")
    return level, _normalize_title(match.group(1))


def _title_key(text: str) -> str:
    """Chromium 折行会吞掉断点处的空格（「BJT 三极管」→「BJT三极管」），
    因此比对大纲时忽略全部空白。成书书签由书模型重建，不受影响。"""
    return re.sub(r"\s+", "", text)


def _page_starts(document, model: dict) -> list[int]:
    outline = [(int(level), _title_key(_normalize_title(title)), page - 1)
               for level, title, page in document.get_toc()]
    starts: list[int] = []
    cursor = 0
    for page in model["pages"]:
        level, title = _page_heading(page)
        key = _title_key(title)
        match = next(
            (index for index in range(cursor, len(outline))
             if outline[index][0] == level and outline[index][1] == key),
            None)
        if match is None:
            raise BookError(
                f"PDF 大纲缺少 {page['id']} 的 h{level} 标题「{title}」")
        starts.append(outline[match][2])
        cursor = match + 1
    if not starts or starts[0] != 0:
        raise BookError(f"PDF 第一页标题不在第 1 物理页: {starts[:1]}")
    if any(b <= a for a, b in zip(starts, starts[1:])):
        raise BookError("PDF 标题页序与书模型页序不一致")
    return starts


PAGE_NUMBER_RE = re.compile(r"(?<!\d)000(?!\d)")


def _page_number_runs(page) -> list:
    """返回本页所有 000 占位的字符包围盒。

    不用 get_text("words", clip=...)：行末零宽字符会被剪进词里（"000f"），
    紧贴正文的 000 会粘成一个词（"测试术语000"），clip 还会把词框夹到链接框上；
    字符级 run 只覆盖三个零本身，红条不会压到相邻术语。
    """
    import fitz
    runs = []
    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            chars = [char for span in line["spans"]
                     for char in span.get("chars", [])]
            text = "".join(char["c"] for char in chars)
            for match in PAGE_NUMBER_RE.finditer(text):
                picked = chars[match.start():match.end()]
                rect = fitz.Rect(picked[0]["bbox"])
                for char in picked[1:]:
                    rect |= fitz.Rect(char["bbox"])
                runs.append(rect)
    return runs


def _region_links(document, start: int, end: int, body_start: int):
    import fitz
    links = []
    for pno in range(start, end):
        page = document[pno]
        # Chromium 双栏 PDF 的链接注记顺序即 DOM/阅读顺序；坐标排序会交错两栏。
        raw_links = page.get_links()
        if not any(isinstance(link.get("page"), int)
                   and link["page"] >= body_start for link in raw_links):
            continue
        runs = [(rect, fitz.Point((rect.x0 + rect.x1) / 2,
                                  (rect.y0 + rect.y1) / 2))
                for rect in _page_number_runs(page)]
        for link in raw_links:
            target = link.get("page")
            if not isinstance(target, int) or target < body_start:
                continue
            rect = fitz.Rect(link["from"])
            # 只认“000 字符 run 的中心落在链接矩形内”的注记：术语链接的
            # 矩形不含页码中心，行末折行的页码若注记错位也不会误判。
            inside = [run for run, center in runs if rect.contains(center)]
            if not inside:
                continue
            run = min(inside, key=lambda item: abs(item.y0 - rect.y0)
                      + abs(item.x0 - rect.x0))
            links.append({"page": pno, "target": target, "rect": rect,
                          "run": run})
    return links


def _link_key(link: dict) -> tuple:
    rect = link["from"]
    target = link.get("to")
    point = None if target is None else (round(target.x, 2), round(target.y, 2))
    return (link.get("kind"), round(rect.x0, 2), round(rect.y0, 2),
            round(rect.x1, 2), round(rect.y1, 2), link.get("page"), point,
            link.get("uri"), link.get("file"), link.get("nameddest"))


def _restore_links(page, snapshot: list[dict]) -> None:
    # apply_redactions 会连带删除与红条相交的链接注记；按原矩形/目标补回，
    # 对外可见的链接数量与目标保持不变。
    surviving = Counter(_link_key(link) for link in page.get_links())
    for link in snapshot:
        key = _link_key(link)
        if surviving[key]:
            surviving[key] -= 1
        else:
            page.insert_link(link)


def _backfill(document, start: int, end: int, body_start: int,
              expected: int | None = None,
              fonts_dir: Path = config.FONTS_DIR):
    import fitz
    stamp_path = fonts.stamp_font_path(fonts_dir)
    if not stamp_path.is_file():
        raise BookError(f"缺少印章字体: {stamp_path}")
    stamp = fitz.Font(fontfile=str(stamp_path))
    links = _region_links(document, start, end, body_start)
    if expected is not None and len(links) != expected:
        raise BookError(
            f"页码占位 {len(links)} 个，目录项 {expected} 个；"
            "每个目录行必须恰好一个链接且包含 000")
    # 索引页的每个页码在 Chromium 里会生成多条完全重合的链接注记；
    # 红字与补字只做一次，链接注记仍按 snapshot 全量恢复。
    by_page: dict[int, list[dict]] = {}
    seen: set[tuple] = set()
    for item in links:
        key = (item["page"], round(item["run"].x0, 1),
               round(item["run"].y0, 1), item["target"])
        if key in seen:
            continue
        seen.add(key)
        by_page.setdefault(item["page"], []).append(item)
    for pno, items in by_page.items():
        page = document[pno]
        snapshot = page.get_links()
        for item in items:
            run = item["run"]
            # 红条严格等于三个零的字形框，不向外扩：相邻术语共用一个词框时
            # 也不会被 apply_redactions 连带删除。
            page.add_redact_annot(run, fill=(1, 1, 1), cross_out=False)
        # 白色矩形只是覆盖，get_text() 仍会读到 000；必须真正删字。
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                              graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        _restore_links(page, snapshot)
        page.insert_font(fontname="bookstamp", fontfile=str(stamp_path))
        for item in items:
            run = item["run"]
            label = str(item["target"] - body_start + 1)
            width = stamp.text_length(label, 9)
            page.insert_text((run.x1 - width, run.y1 - 1.2),
                             label, fontname="bookstamp", fontsize=9,
                             color=MUTED)
    remaining = [pno + 1 for pno in range(start, end)
                 if "000" in document[pno].get_text()]
    if remaining:
        raise BookError(f"页码回填后仍有 000：物理页 {remaining[:5]}")
    return links


def _section_for(pno: int, starts: list[int], model: dict) -> dict:
    pages = model["pages"]
    chosen = 0
    for index, start in enumerate(starts[:len(pages)]):
        if start <= pno:
            chosen = index
        else:
            break
    return pages[chosen]


def _stamp_running(document, model: dict, starts: list[int], body_start: int,
                   manifest: dict, padding: list[int], fonts_dir: Path) -> None:
    import fitz
    stamp_path = fonts.stamp_font_path(fonts_dir)
    if not stamp_path.is_file():
        raise BookError(f"缺少印章字体: {stamp_path}")
    stamp = fitz.Font(fontfile=str(stamp_path))
    skip = set(padding)
    for index, page in enumerate(model["pages"]):
        if page["kind"] in SKIP_KINDS:
            skip.add(starts[index])
    width_page = document[0].rect.width
    height_page = document[0].rect.height
    outside = 18 * MM
    inside = 22 * MM
    for pno in range(document.page_count):
        page = document[pno]
        if pno in skip or _is_blank(page):
            continue
        page.insert_font(fontname="bookstamp", fontfile=str(stamp_path))
        is_right = pno % 2 == 0
        info = _section_for(pno, starts, model)
        label = _roman(pno + 1) if pno < body_start else str(pno - body_start + 1)
        if info["kind"] == "chapter":
            heading = info["title"]
        else:
            heading = info.get("header") or info["title"]
        if is_right:
            header = heading
            header_x = width_page - outside - stamp.text_length(header, 8)
            folio_x = width_page - outside - stamp.text_length(label, 8)
            rule_start, rule_end = inside, width_page - outside
        else:
            header = manifest["title"]
            header_x = outside
            folio_x = outside
            rule_start, rule_end = outside, width_page - inside
        page.insert_text((header_x, 12 * MM), header, fontname="bookstamp",
                         fontsize=8, color=MUTED)
        page.draw_line(fitz.Point(rule_start, 14.2 * MM),
                       fitz.Point(rule_end, 14.2 * MM),
                       color=RULE, width=0.3)
        page.insert_text((folio_x, height_page - 9 * MM), label,
                         fontname="bookstamp", fontsize=8, color=MUTED)


def _bookmarks(model: dict, starts: list[int], toc_targets: dict[str, int]):
    page_targets = {page["id"]: starts[index]
                    for index, page in enumerate(model["pages"])}
    entries, previous_level = [], 0
    for entry in model["toc"]:
        anchor = entry["anchor"]
        target = page_targets.get(anchor, toc_targets.get(anchor))
        if target is None:
            raise BookError(f"书签锚点没有目标页: {anchor}")
        level = int(entry["level"])
        if level < 1 or level > 3 or level > previous_level + 1:
            raise BookError(f"书签层级非法: {entry}")
        entries.append([level, entry["title"], target + 1])
        previous_level = level
    return entries


def stamp_pdf(raw_pdf: Path, output_pdf: Path, model: dict, manifest: dict,
              fonts_dir: Path = config.FONTS_DIR) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise BookError(
            "PDF 需要 PyMuPDF：pip install -r analog-book/requirements.txt") from exc
    if model.get("edition_status") != manifest["release"]["edition_status"]:
        raise BookError("PDF 模型与 manifest 的版本状态不一致，请重建 HTML")
    document = fitz.open(raw_pdf)
    try:
        original_pages = document.page_count
        padding = pad_to_multiple(document)
        starts = _page_starts(document, model)
        body_start = starts[next(
            index for index, page in enumerate(model["pages"])
            if _group(page) != "front")]
        kinds = [page["kind"] for page in model["pages"]]
        toc_index = kinds.index("toc")
        lof_index = kinds.index("list_of_figures")
        lot_index = kinds.index("list_of_tables")
        # assemble 把索引起页建模为 kind="back"，只能按固定 id 定位。
        index_index = next(
            (index for index, page in enumerate(model["pages"])
             if page["id"] == "book-index"), None)
        if index_index is None:
            raise BookError("书模型缺少 book-index 索引页")
        toc_start, toc_end = starts[toc_index], starts[toc_index + 1]
        lof_start, lof_end = starts[lof_index], starts[lof_index + 1]
        lot_start, lot_end = starts[lot_index], starts[lot_index + 1]
        index_start = starts[index_index]
        index_end = (starts[index_index + 1]
                     if index_index + 1 < len(starts) else document.page_count)
        toc_links = _backfill(document, toc_start, toc_end, body_start,
                              expected=len(model["toc"]), fonts_dir=fonts_dir)
        toc_targets = {entry["anchor"]: link["target"]
                       for entry, link in zip(model["toc"], toc_links)}
        filled = len(toc_links)
        filled += len(_backfill(document, lof_start, lof_end, body_start,
                                expected=len(model["lof"]),
                                fonts_dir=fonts_dir))
        filled += len(_backfill(document, lot_start, lot_end, body_start,
                                expected=len(model["lot"]),
                                fonts_dir=fonts_dir))
        filled += len(_backfill(document, index_start, index_end, body_start,
                                fonts_dir=fonts_dir))
        _stamp_running(document, model, starts, body_start, manifest,
                       padding, fonts_dir)
        document.set_toc(_bookmarks(model, starts, toc_targets))
        document.set_page_labels([
            {"startpage": 0, "prefix": "", "style": "r", "firstpagenum": 1},
            {"startpage": body_start, "prefix": "", "style": "D",
             "firstpagenum": 1},
        ])
        document.set_metadata({
            "title": manifest["title"],
            "author": manifest["author"],
            "subject": manifest["subtitle"],
            "keywords": "模拟电路, 电子, 16K, " + manifest["license"],
            "creator": "analog-circuit-roadmap/book",
        })
        # 索引页有 1700+ 条页码链接注记；garbage=3 的对象重编号在 672 页
        # 文档上实测 323 s，只换回 0.3% 体积；garbage=1 时整次 --pdf 构建
        # 73 s、PDF 30.9 MB。印前体积由 100 MB 上限兜底。
        document.save(output_pdf, garbage=1, deflate=True)
        return {
            "pages": document.page_count,
            "original_pages": original_pages,
            "body_start": body_start,
            "starts": starts,
            "padded": padding,
            "backfilled": filled,
            "bookmarks": len(model["toc"]),
            "labels": ["i", _roman(body_start), "1"],
        }
    finally:
        document.close()


def check_pdf(pdf_path: Path, model: dict, manifest: dict) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise BookError(
            "PDF 需要 PyMuPDF：pip install -r analog-book/requirements.txt") from exc
    document = fitz.open(pdf_path)
    try:
        problems, warnings = [], []
        pages = document.page_count
        size_mm = [round(document[0].rect.width / MM, 2),
                   round(document[0].rect.height / MM, 2)]
        final = manifest["release"]["edition_status"] == "final"
        for page in document:
            width = page.rect.width / MM
            height = page.rect.height / MM
            if abs(width - 185) > 0.5 or abs(height - 260) > 0.5:
                problems.append(f"页面尺寸 {width:.1f}×{height:.1f}mm 不是 16K")
                break
        if pages % 4:
            problems.append(f"页数 {pages} 不是 4 的倍数")
        labels = [page.get_label() for page in document]
        if not labels or labels[0] != "i":
            problems.append("第 1 页页码标签不是 i")
        try:
            body_start = labels.index("1")
        except ValueError:
            body_start = -1
            problems.append("找不到页码 1 的起始页")
        toc = document.get_toc()
        if len(toc) != len(model["toc"]):
            problems.append(f"书签 {len(toc)} 条，模型 {len(model['toc'])} 条")
        if any(entry[0] > 3 for entry in toc):
            problems.append("书签超过三级")
        # 450–700/535–653 是整书一册的装订区间；分卷后每卷独立成册，
        # 只有 700 页硬上限对单册仍然成立。
        whole_book = not model.get("volume")
        if whole_book and pages < 450:
            if final:
                problems.append(f"页数 {pages} 低于硬区间下限 450")
            else:
                warnings.append(f"草稿页数 {pages}，低于目标区间 450–700")
        if pages > 700:
            problems.append(f"页数 {pages} 超过硬上限 700")
        if whole_book and final and pages < 535:
            warnings.append(f"页数 {pages} 低于目标区间下限 535")
        if whole_book and final and pages > 653:
            warnings.append(f"页数 {pages} 高于目标区间上限 653")
        if not final:
            warnings.append(
                "草稿只检查 16K 结构项；字体嵌入、缺字、公式图形、版心溢出、"
                "图表跨页与 PDF <100MB 等印前全检在 Phase 5 执行")
        return {"pages": pages, "body_start": body_start, "labels": labels[:12],
                "bookmarks": len(toc), "size_mm": size_mm,
                "max_level": max((entry[0] for entry in toc), default=0),
                "problems": problems, "warnings": warnings}
    finally:
        document.close()


def build_pdf(html_path: Path, out_dir: Path, manifest: dict,
              browser_override: str | None = None) -> Path:
    model_path = out_dir / config.MODEL_NAME
    if not model_path.is_file():
        raise BookError(f"缺少书模型: {model_path}")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    raw = out_dir / ".analog-book.raw.pdf"
    output = out_dir / config.PDF_NAME
    try:
        print_pdf(html_path, raw, browser_override)
        report = stamp_pdf(raw, output, model, manifest)
        pdf_report = check_pdf(output, model, manifest)
    finally:
        raw.unlink(missing_ok=True)
    if pdf_report["problems"]:
        raise BookError("PDF 审计失败:\n" + "\n".join(pdf_report["problems"]))
    for warning in pdf_report["warnings"]:
        print(f"pdf warning: {warning}")
    print(f"pdf   {output} ({output.stat().st_size} bytes, {report['pages']} pages)")
    return output
