"""章徽与篇题插画装载：读 assets/emblems/*.svg，校验 yuyu 契约后以 data URI 内联。

两套契约（章徽从严、篇题从卷 I part-art 语言，均违者即报错）：

章徽 chNN.svg —— 单色线描（与卷 I 章徽同一语言）：
- 单根 <svg> 且带 viewBox；线条/填充只用 currentColor，不许任何 #hex 颜色字面量；
- 禁 id=、href=、url(、<style>、<script>、<iframe>、<image>、foreignObject、
  object、embed、xlink:、data:、@import、on*= 事件属性；纯几何线描，不用 <text>；
- 不加 role=/aria-label（可访问性由包装层统一处理）；每枚 ≤6000 字节（UTF-8）。

篇题 part-pN.svg —— 卷 I 篇题语言（analog-book/book/illustrations.py 的 part_art 标准）：
- 单根 <svg> 且带 viewBox；允许 #hex 纸底/三色配色与 <text> 拉丁标签；
- <text> 只许拉丁文字（全文禁 CJK，与卷 I 一致）；仍禁 id=/href=/url( 等共用标签黑名单；
  允许 role=/aria-label（卷 I 篇题自带 role="presentation"）；
- 每枚 ≤6000 字节（UTF-8）。

文件名映射（Main 已核定的 38 枚连续编号）：
- 数字前缀章 00-*.md … 32-*.md → ch00.svg … ch32.svg（NN = 文件名数字前缀）；
- 附录 A–E（按 A、B、C、D、E 顺序）→ ch33.svg … ch37.svg；
- 篇题 part-pN.svg（N = manifest parts[].id，p0–p8）。

缺文件策略：默认收集 warnings 不 fail（过渡期插画分批交付）；
--strict-emblems 开启时缺一枚即 fail。契约违例在两种模式下都直接报错——
缺是进度问题，违例是质量问题。
"""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EMBLEM_DIR = ROOT / "assets" / "emblems"
MAX_EMBLEM_BYTES = 6000

# 附录 A–E → ch33–ch37。
_APPENDIX_ORDER = "ABCDE"
_APPENDIX_FIRST_NO = 33

# 两套契约共用的标签/属性黑名单。
_BANNED_RE = re.compile(
    r"<\s*(script|style|image|foreignObject|iframe|object|embed)\b"
    r"|xlink:|data:|@import|\bid\s*=|\bhref\s*=|url\s*\(|on[a-z]+\s*=",
    re.I,
)
# 章徽不加 role=/aria-label（可访问性由 <img alt> 包装层统一处理）；
# 篇题放行——卷 I 篇题自带 role="presentation"，<img> 内嵌文档的标注不外露。
_A11Y_ATTR_RE = re.compile(r"\brole\s*=|aria-label\s*=", re.I)
# 章徽只许 currentColor：任何 #hex 颜色字面量都是违例（负向先行排除 &#123; 实体）。
_HEX_COLOR_RE = re.compile(r"(?<![&\w])#[0-9a-fA-F]{3,8}\b")
_TEXT_RE = re.compile(r"<\s*text\b", re.I)
# 篇题允许 <text>，但只许拉丁标签（卷 I part_art 同一禁令）。
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_CHAPTER_NO_RE = re.compile(r"^(\d{2})-")
_APPENDIX_RE = re.compile(r"^附录([A-E])-")


class EmblemError(RuntimeError):
    """章徽/篇题插画契约违例，或 strict 模式下缺文件。"""


def chapter_stem(name: str) -> str | None:
    """章文件名 → 章徽文件干（chNN.svg 的 NN）；无映射（未知形态）返回 None。"""
    match = _CHAPTER_NO_RE.match(name)
    if match:
        return f"ch{match.group(1)}"
    match = _APPENDIX_RE.match(name)
    if match:
        return f"ch{_APPENDIX_FIRST_NO + _APPENDIX_ORDER.index(match.group(1))}"
    return None


def part_stem(part_id: str) -> str:
    """分部 id（p0–p8）→ 篇题文件干（part-pN.svg 的 part-pN）。"""
    return f"part-{part_id}"


def validate_svg(svg: str, source: str, kind: str = "chapter") -> None:
    """按契约校验一份章徽（kind="chapter"）或篇题（kind="part"）SVG 源文本。"""
    if kind not in {"chapter", "part"}:
        raise ValueError(f"未知插画类型: {kind!r}")
    name = Path(source).name
    head = svg.split(">", 1)[0]
    if not svg.startswith("<svg") or "viewBox" not in head or svg.count("<svg") != 1:
        raise EmblemError(f"{name}: 必须是带 viewBox 的单根 <svg>")
    if len(svg.encode("utf-8")) > MAX_EMBLEM_BYTES:
        raise EmblemError(f"{name}: 超过 {MAX_EMBLEM_BYTES} 字节上限")
    banned = _BANNED_RE.search(svg)
    if banned:
        raise EmblemError(f"{name}: 含禁用内容 {banned.group(0)!r}")
    if kind == "chapter":
        if "currentColor" not in svg:
            raise EmblemError(f"{name}: 线条与填充必须只用 currentColor")
        color = _HEX_COLOR_RE.search(svg)
        if color:
            raise EmblemError(f"{name}: 章徽只许 currentColor，出现颜色字面量 {color.group(0)!r}")
        text = _TEXT_RE.search(svg)
        if text:
            raise EmblemError(f"{name}: 章徽是纯几何线描，不许 <text>")
        a11y = _A11Y_ATTR_RE.search(svg)
        if a11y:
            raise EmblemError(f"{name}: 章徽不加 role=/aria-label（由 <img alt> 统一处理）")
    else:
        cjk = _CJK_RE.search(svg)
        if cjk:
            raise EmblemError(f"{name}: 篇题只许拉丁文字，出现 CJK {cjk.group(0)!r}")


def _data_uri(svg: str) -> str:
    """SVG 源文本 → base64 data URI（与封面同一内联方式，保持单文件 HTML 自包含）。"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


_VIEWBOX_RE = re.compile(r'viewBox\s*=\s*"([^"]+)"')


def _viewbox_size(svg: str) -> tuple[str, str]:
    """viewBox 宽高 → <img> 的 width/height 属性（CI 契约：全书每张 img 必须带尺寸）。"""
    match = _VIEWBOX_RE.search(svg)
    if match:
        parts = match.group(1).replace(",", " ").split()
        if len(parts) >= 4:
            try:
                width, height = float(parts[-2]), float(parts[-1])
            except ValueError:
                width = height = 48.0

            def fmt(value: float) -> str:
                return str(int(value)) if value.is_integer() else str(value)

            return fmt(width), fmt(height)
    return "48", "48"


class EmblemLibrary:
    """一次构建的插画装载器：读文件、校验契约、内联为 data URI、收集缺文件告警。"""

    def __init__(self, root: Path = EMBLEM_DIR, strict: bool = False) -> None:
        self.root = Path(root)
        self.strict = strict
        self.warnings: list[str] = []

    def _svg(self, stem: str, label: str, kind: str) -> str | None:
        path = self.root / f"{stem}.svg"
        if not path.is_file():
            message = f"{label}插画缺失：{path}"
            if self.strict:
                raise EmblemError(f"{message}（--strict-emblems）")
            self.warnings.append(message)
            return None
        svg = path.read_text(encoding="utf-8").strip()
        validate_svg(svg, path.name, kind)
        return svg

    def chapter_html(self, name: str, title: str) -> str:
        """章首徽章 <img>；缺文件返回空串（告警已记录），章首结构保持原样。"""
        stem = chapter_stem(name)
        if stem is None:
            return ""
        svg = self._svg(stem, f"章徽 {stem}.svg（{name}）", "chapter")
        if svg is None:
            return ""
        alt = html.escape(f"章徽线描：{title}", quote=True)
        width, height = _viewbox_size(svg)
        return (f'<img class="chapter-emblem" src="{_data_uri(svg)}"'
                f' width="{width}" height="{height}" alt="{alt}"'
                f' loading="lazy">')

    def part_html(self, part_id: str, title: str) -> str:
        """篇题插画 <img>；缺文件返回空串（告警已记录），分部页结构保持原样。"""
        stem = part_stem(part_id)
        svg = self._svg(stem, f"篇题插画 {stem}.svg", "part")
        if svg is None:
            return ""
        alt = html.escape(f"篇题线描：{title}", quote=True)
        width, height = _viewbox_size(svg)
        return (f'<img class="part-art" src="{_data_uri(svg)}"'
                f' width="{width}" height="{height}" alt="{alt}"'
                f' loading="lazy">')
