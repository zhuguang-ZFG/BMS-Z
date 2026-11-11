"""构建报告与印刷规格：只读已有产物，不重复构建。"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import config
from .manifest import BookError

REPORT_NAME = "build-report.json"
PRINT_SPEC_NAME = "PRINT-SPEC.md"
FONT_LICENSE = "SIL OFL 1.1"
PAPER = "80g 纯质纸"
COVER_STOCK = "250g 铜版纸覆哑膜"
BINDING = "胶装"
COLOR = "sRGB"
DEFERRED = [
    "19 章正文扩写与统稿（目标 320,000 字）",
    "图表、动画与视频配套补齐",
    "19 章 SPICE 仿真与三套实测复核",
    "索引、参考文献与外部审读",
    "封面打样、纸张与印厂参数确认",
    "印前全检（字体嵌入、缺字、公式图形、版心溢出、图表跨页与 PDF <100MB）",
    "ISBN 与条码（尚未申请）",
]


def _require(path: Path) -> Path:
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise BookError(f"报告所需产物不存在或为空: {path}")
    return path


def _pdf_version(pdf_path: Path) -> str:
    with Path(pdf_path).open("rb") as handle:
        head = handle.read(8).decode("latin-1", "replace")
    if head.startswith("%PDF-"):
        return "PDF " + head[5:].strip()
    return "PDF"


def _fonts(fonts_dir=config.FONTS_DIR) -> list[dict]:
    data = json.loads(
        (Path(fonts_dir) / "sources.json").read_text(encoding="utf-8"))
    fonts = [{"family": item["family"], "weight": item["weight"],
              "file": item["name"], "license": FONT_LICENSE}
             for item in data["subsets"]]
    stamp = data.get("stamp") or {}
    if stamp:
        fonts.append({"family": stamp["family"], "weight": stamp["weight"],
                      "file": stamp["name"], "license": FONT_LICENSE})
    return fonts


def _sample(out_dir: Path) -> dict | None:
    path = Path(out_dir) / "sample" / config.SAMPLE_REPORT_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(out_dir, model, manifest, pdf_report, cover_report,
                 sample_report=None, pdf_path=None, cover_path=None) -> dict:
    if pdf_report.get("problems"):
        raise BookError("PDF 结构问题: " + "; ".join(pdf_report["problems"]))
    if cover_report.get("problems"):
        raise BookError("封面结构问题: " + "; ".join(cover_report["problems"]))
    out_dir = Path(out_dir)
    html_path = _require(out_dir / config.OUTPUT_NAME)
    pdf_path = _require(pdf_path or out_dir / config.PDF_NAME)
    cover_path = _require(cover_path or out_dir / config.COVER_PDF_NAME)
    preview = out_dir / config.COVER_PREVIEW_NAME
    sample = sample_report if sample_report is not None else _sample(out_dir)
    stats = model["stats"]
    cover_cfg = manifest["cover"]
    endnotes = model.get("endnotes", 0)
    if isinstance(endnotes, list):
        endnotes = len(endnotes)
    return {
        "schema": 1,
        "generated": dt.datetime.now(
            dt.timezone.utc).isoformat(timespec="seconds"),
        "edition_status": manifest["release"]["edition_status"],
        "title": manifest["title"],
        "edition": manifest["edition"],
        "version": manifest["version"],
        "source_version": manifest.get("source_version", ""),
        "date": manifest["date"],
        "logical_pages": len(model["pages"]),
        "parts": len(manifest["parts"]),
        "chapters": sum(len(unit["chapters"]) for part in manifest["parts"]
                        for unit in part["units"]),
        "pdf_pages": pdf_report["pages"],
        "body_start": pdf_report["body_start"],
        "bookmarks": pdf_report["bookmarks"],
        "pdf_warnings": list(pdf_report.get("warnings", [])),
        "preflight": "未执行（Phase 5 印前门禁）",
        "figures": stats.get("figures", 0),
        "tables": stats.get("tables", 0),
        "formulas": stats.get("formulas", 0),
        "images": stats.get("images", 0),
        "endnotes": endnotes,
        "html_bytes": html_path.stat().st_size,
        "pdf_bytes": pdf_path.stat().st_size,
        "cover_bytes": cover_path.stat().st_size,
        "preview_bytes": preview.stat().st_size if preview.is_file() else 0,
        "trim_mm": [manifest["trim"]["width_mm"],
                    manifest["trim"]["height_mm"]],
        "interior_size_mm": list(pdf_report.get("size_mm") or []),
        "text_block_mm": [config.TEXT_WIDTH_MM, config.TEXT_HEIGHT_MM],
        "margins_mm": {"top": 20, "bottom": 22,
                       "inside": 22, "outside": 18},
        "mirrored": (sample or {}).get("fallback", "not-sampled"),
        "bleed_mm": cover_cfg["bleed_mm"],
        "cover": {
            # inspect_cover 的 pages 是封面 PDF 自身页数（恒为 1）；
            # 报告要记的是书脊所依据的内文页数。
            "pages": pdf_report["pages"],
            "size_mm": cover_report["size_mm"],
            "spine_mm": cover_report["spine_mm"],
            "paper_caliper_mm": cover_cfg["paper_caliper_mm"],
            "spine_allowance_mm": cover_cfg["spine_allowance_mm"],
        },
        "fonts": _fonts(),
        "paper": PAPER,
        "cover_stock": COVER_STOCK,
        "binding": BINDING,
        "color": COLOR,
        "pdf_version": _pdf_version(pdf_path),
        "audit": {"errors": model["audit"]["errors"],
                  "warnings": model["audit"]["warnings"]},
        "deferred": (
            [] if manifest["release"]["edition_status"] == "final"
            else list(DEFERRED)),
    }


def _human(size: int) -> str:
    if size >= 1024 * 1024:
        return "%.1f MB" % (size / (1024 * 1024))
    return "%d KB" % max(1, round(size / 1024))


def print_spec_markdown(report: dict, manifest: dict) -> str:
    cover = report["cover"]
    spine = cover["spine_mm"]
    caliper = cover["paper_caliper_mm"]
    allowance = cover["spine_allowance_mm"]
    width, height = cover["size_mm"]
    trim_w, trim_h = report["trim_mm"]
    bleed = report["bleed_mm"]
    size_mm = report.get("interior_size_mm") or []
    interior = (f"{size_mm[0]:.2f} × {size_mm[1]:.2f} mm"
                if len(size_mm) == 2 else "未记录")
    multiple = "是" if report["pdf_pages"] % 4 == 0 else "否"
    pdf_warnings = report.get("pdf_warnings") or []
    warning_lines = ("\n".join(f"- {item}" for item in pdf_warnings)
                     if pdf_warnings else "- 无")
    formula = (f"{report['pdf_pages']} / 2 × {caliper:.2f} + "
               f"{allowance:.1f} = {spine:.2f} mm")
    nominal_width = 2 * trim_w + spine + 2 * bleed
    nominal_height = trim_h + 2 * bleed
    cover_formula = (
        f"2 × {trim_w:g} + {spine:.2f} + 2 × {bleed:g} = "
        f"{nominal_width:.2f} mm（标称）；"
        f"{trim_h:g} + 2 × {bleed:g} = {nominal_height:.2f} mm（标称）；"
        f"实际 MediaBox {width:.2f} × {height:.2f} mm")
    fonts = "\n".join(
        f"| {item['family']} | {item['weight']} | `{item['file']}` | "
        f"{item['license']} |" for item in report["fonts"])
    deferred = ("\n".join(f"- {item}" for item in report["deferred"])
                if report["deferred"] else "- 无（本版为稳定版）")
    status = "草稿" if report["edition_status"] == "draft" else "稳定版"
    return f"""# 印刷规格：{report['title']} {report['edition']}

> 本文件由 `analog-book/book/report.py` 从实际 HTML、PDF、封面与样张生成。与任何手写数字冲突时，以本文件为准。

## 1 版本与状态

| 项目 | 值 |
|---|---|
| 版本 | {report['version']} |
| 状态 | {status} |
| 内容源版本 | {report['source_version']} |
| 构建日期 | {report['date']} |
| 生成时间 | {report['generated']} |

## 2 开本与版心

| 项目 | 数值 |
|---|---|
| 成品尺寸 | {trim_w:g} × {trim_h:g} mm（16K，标称） |
| 内文实际 MediaBox | {interior}（Chromium 渲染，允许 ±0.5 mm） |
| 版心 | {report['text_block_mm'][0]:g} × {report['text_block_mm'][1]:g} mm |
| 页边距 | 上 {report['margins_mm']['top']} mm / 下 {report['margins_mm']['bottom']} mm / 订口 {report['margins_mm']['inside']} mm / 切口 {report['margins_mm']['outside']} mm |
| 镜像边距 | {report['mirrored']} |

## 3 页数、书脊与封面

| 项目 | 数值 |
|---|---|
| 内文页数 | {report['pdf_pages']}（4 的倍数：{multiple}） |
| 书脊公式 | {formula} |
| 封面展开（含出血） | {width:.2f} × {height:.2f} mm |
| 封面尺寸推导 | {cover_formula} |
| 出血 | {bleed} mm |
| 内文 PDF | {_human(report['pdf_bytes'])} |
| 封面 PDF | {_human(report['cover_bytes'])} |

> 表中“封面展开”是 `cover.pdf` 的实际 MediaBox；推导公式是按页数与纸张参数计算的标称尺寸。Chromium 渲染允许 0.5 mm 内的取整误差，印刷以实际 MediaBox 与打样为准。

> 书脊按 `页数 / 2 × 纸张厚度 + 装订余量` 计算。上机前必须用实际纸张打样复核；不同批次纸张厚度会让书脊相差 1–2 mm。

## 4 纸张与装订

| 项目 | 规格 |
|---|---|
| 正文 | {report['paper']} |
| 封面 | {report['cover_stock']} |
| 装订 | {report['binding']} |
| ISBN | 未申请 ISBN；封面不含 ISBN 与条码 |

## 5 字体与许可

| 字族 | 字重 | 文件 | 许可 |
|---|---:|---|---|
{fonts}

## 6 色彩与文件

| 项目 | 值 |
|---|---|
| 色彩空间 | {report['color']} |
| PDF 版本 | {report['pdf_version']} |
| 单文件 HTML | {_human(report['html_bytes'])} |
| 封面预览 | {_human(report['preview_bytes']) if report['preview_bytes'] else '未生成'} |
| 书签数 | {report['bookmarks']} |
| 图表数 | {report['figures']} 图 / {report['tables']} 表 |
| 公式数 | {report['formulas']} |
| 尾注数 | {report['endnotes']} |

## 7 打样与校对页

- 章首页：确认章号、学习目标与页眉不冲突。
- 跨页表：确认表头重复、单元格不被裁切。
- 长公式：确认不越出版心、不被分页截断。
- 图与图注：确认图注同页、灰阶可辨。
- 目录/索引：确认 `000` 已全部回填，页码与正文一致。
- 封面：确认书脊文字、裁切线、二维码与出血。

## 8 尚未关闭的质量门

**印前全检：{report['preflight']}。** 下表列出尚未关闭的门；第 3 节的书脊与封面仍须打样复核。

{deferred}

## 9 PDF 结构检查警告

{warning_lines}
"""


def write_report(out_dir, model, manifest, pdf_report, cover_report,
                 sample_report=None, pdf_path=None, cover_path=None) -> dict:
    out_dir = Path(out_dir)
    report = build_report(
        out_dir, model, manifest, pdf_report, cover_report,
        sample_report=sample_report, pdf_path=pdf_path,
        cover_path=cover_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / REPORT_NAME).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (out_dir / PRINT_SPEC_NAME).write_text(
        print_spec_markdown(report, manifest), encoding="utf-8")
    return report
