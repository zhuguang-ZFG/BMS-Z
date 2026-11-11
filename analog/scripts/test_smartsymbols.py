"""pymdownx.smartsymbols 的护栏。

它把 ASCII 换成排版符号，好处是把「1/3 Vcc」自动排成「⅓ Vcc」、「3rd」自动带上标；
坏处是**同一条规则分不清分数和区间**——「第 3/4 章」会被排成「第 ¾ 章」，
意思直接变了。这类错误不会报错、不会构建失败，只有人肉读才发现。

触发规则**直接取自 pymdownx.smartsymbols.REPL**，不在本文件里重抄一遍：
抄一遍就会漂移，而「护栏和被测对象用两套规则」正是最容易假绿的地方。
pymdownx 的真实触发表（本文件末尾的 test 会打印实际命中）：

  分数  (?<!\\d)(1/4|1/2|3/4|1/3|2/3|1/5|2/5|3/5|4/5|1/6|5/6|1/8|3/8|5/8|7/8)(?!\\d)
        → ½ ¼ ¾ ⅓ ⅔ …（1/7 不在表里；分子分母被数字夹住的也不动）
  序数  \\b([1-9][0-9]*)?(11th|12th|13th|1st|2nd|3rd|[04-9]th)\\b → 3<sup>rd</sup>
  其他  (c) (r) → © ® ；+/- → ± ；=/= → ≠ ；\\bc/o\\b → ℅ ；--> <-- <--> → → ← ↔
        注意：`...`、`(C)`/`(TM)` 大写、`(tm)`（小写！在表里）以外的大写形式**不在**表里。

保护范围（实测，靠上游处理器而不是 smartsymbols 自觉）：
  `$…$` / `$$…$$` 的数学、反引号行内代码、围栏代码块、**HTML 注释**、
  **HTML 标签的属性值**（`<img src="…/7/73/400_….jpg">` 里的 3/4 不会被改，
  因为整块被 Python-Markdown 存进了 stash）**都不会被改写**。
  所以分数写在公式里是安全的，只有**正文里**的才危险。

Run: python -B -m unittest discover -s scripts -p test_smartsymbols.py -v
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402
from pymdownx import smartsymbols as _ss  # noqa: E402

DOCS = ROOT / "docs"

FENCE = re.compile(r"^[ \t]*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
MATH_BLOCK = re.compile(r"\$\$.*?\$\$", re.S)
MATH_INLINE = re.compile(r"\$[^$\n]+\$")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
# 只剥「长得像标签」的：`Rs < 30 kΩ` 这种正文里的裸尖括号不能被误删
HTML_TAG = re.compile(r"</?[a-zA-Z][a-zA-Z0-9-]*(?:\s[^<>]*)?/?>")
# 链接目标会被 Python-Markdown 存进 stash，和标签属性一样受保护
MD_DEST = re.compile(r"\]\([^)\s]*\)")

# 已逐条复核、确认在原意上就是「分数 / 序数」的触发串。
# 出现新的触发串 → 红灯，逼作者看一眼：是新写的分数（那就加进来），
# 还是把「第 5/6 章」这种区间写成了斜杠（那就改写成「第 5、6 章」）。
REVIEWED = {"1/2", "1/3", "1/4", "1/5", "1/6", "1/8", "2/3", "3/4", "3rd"}

# 「X/Y」贴着这些字时一定是**区间**，不是分数。
# 两类都拦：阿拉伯数字（「第 14/15 章」）与中文数字（「第一/二/三篇」）——
# 同一条编辑规则只拦一半，等于没拦。
RANGE = re.compile(
    r"(?:第|§|章|节|页|图|表|题|卷|篇)\s*\d+(?:\s*/\s*\d+)+"
    r"|\d+(?:\s*/\s*\d+)+\s*(?:章|节|页|图|表|题|卷|篇)"
    r"|第[一二三四五六七八九十]+(?:/[一二三四五六七八九十]+)+[篇章节页]"
)

# 与 build_site.MKDOCS_YML 的 markdown_extensions 对齐（见 test_the_extension_is_enabled）
PIPELINE = ["pymdownx.smartsymbols", "pymdownx.arithmatex", "pymdownx.superfences",
            "pymdownx.highlight", "pymdownx.inlinehilite", "pymdownx.tabbed",
            "pymdownx.details", "md_in_html", "tables", "attr_list",
            "footnotes", "abbr", "def_list", "admonition"]
PIPELINE_CFG = {"pymdownx.arithmatex": {"generic": True},
                "pymdownx.tabbed": {"alternate_style": True}}


def triggers(text):
    """正文里会被 smartsymbols 改写的片段——直接用 pymdownx 自己的正则。"""
    hits = set()
    for _name, pattern, _repl in _ss.REPL.values():
        for m in re.finditer(pattern, text):
            hits.add(m.group(0))
    return hits


def prose(text):
    """剥掉受保护的区域，只留会被 smartsymbols 改写的正文。"""
    kept, fence = [], None
    for line in text.split("\n"):
        f = FENCE.match(line)
        if f:
            ch = f.group(1)[0]
            if fence is None:
                fence = ch
            elif fence == ch:
                fence = None
            continue
        if fence:
            continue
        kept.append(line)
    body = "\n".join(kept)
    body = HTML_COMMENT.sub(" ", body)
    body = MATH_BLOCK.sub(" ", body)
    body = MATH_INLINE.sub(" ", body)
    body = INLINE_CODE.sub(" ", body)
    body = MD_DEST.sub("]()", body)
    return HTML_TAG.sub(" ", body)


class SmartsymbolsTests(unittest.TestCase):
    def test_the_extension_is_enabled(self):
        """护栏在、功能却被删掉——最常见的假绿，先钉死这一条。

        **要匹配「列表项那一行」，不能只 assertIn 名字**：把 `- pymdownx.smartsymbols`
        注释掉之后，名字仍然作为注释文字留在配置里，`assertIn` 照样为真
        （变异验证时踩过这个坑）。
        """
        for name in ("pymdownx.smartsymbols", "pymdownx.arithmatex",
                     "pymdownx.superfences", "md_in_html", "tables"):
            with self.subTest(extension=name):
                # 末尾允许一个 `:`（`- pymdownx.arithmatex:` 这种带配置的写法）
                self.assertRegex(
                    build_site.MKDOCS_YML,
                    re.compile(rf"^[ \t]*-[ \t]*{re.escape(name)}[ \t]*:?[ \t]*$", re.M),
                    f"{name} 没有被真正启用（注释里的名字不算）")

    def test_the_scanner_actually_finds_triggers(self):
        """扫描器自己的自检：正则 / 剥离逻辑坏掉时后面几条会静默全绿。"""
        self.assertEqual({"1/2"}, triggers(prose("一杯的 1/2 就行")))
        self.assertEqual({"3/4"}, triggers(prose("第 3/4 章")))
        self.assertEqual({"23rd"}, triggers(prose("23rd 版")))
        # 受保护的四类，一个都不该命中
        self.assertEqual(set(), triggers(prose("$1/2$ 与 `1/2` 都安全")))
        self.assertEqual(set(), triggers(prose("<!-- 3/4 -->\n\n正文")))
        self.assertEqual(set(), triggers(prose('<img src="https://x/7/73/400_1/2.jpg">')))
        self.assertEqual(set(), triggers(prose("[看这里](https://x/1/2/3.md)")))
        self.assertEqual(set(), triggers(prose("```\n1/2 --> 3/4\n```")))
        # 边界规则照抄 pymdownx：被数字夹住的不算
        self.assertEqual(set(), triggers(prose("型号 7/73/400")))
        # RANGE 的两类
        self.assertEqual(["第 14/15"], RANGE.findall(prose("见第 14/15 章")))
        self.assertEqual(["第一/二篇"], RANGE.findall(prose("第一/二篇都讲了")))
        self.assertEqual([], RANGE.findall(prose("衰减 1/3，见 13.4 节")))

    def test_math_code_comments_and_tag_attributes_survive_the_rewrite(self):
        """证明保护来自上游处理器，而不是「碰巧没写」。"""
        import markdown

        src = ("正文写 1/3 会被改；$1/2$ 不该被改；`1/2` 不该被改。\n\n"
               "<!-- 3/4 注释里的不该被改 -->\n\n"
               '<img src="https://x/7/73/400_1/2.jpg" alt="1/3">\n\n'
               "```text\n1/2 --> 1/3\n```\n")
        html = markdown.markdown(src, extensions=PIPELINE, extension_configs=PIPELINE_CFG)
        self.assertIn("&#8531;", html, "正文里的 1/3 应当被排成 ⅓")
        self.assertIn(r"\(1/2\)", html, "数学里的 1/2 被改写了——arithmatex 没抢在 smartsymbols 前面")
        self.assertIn("<code>1/2</code>", html, "行内代码里的 1/2 被改写了")
        self.assertIn("<!-- 3/4 注释里的不该被改 -->", html, "HTML 注释里的 3/4 被改写了")
        self.assertIn("400_1/2.jpg", html, "标签属性里的 1/2 被改写了")
        self.assertIn("1/2 --&gt; 1/3", html, "围栏代码块里的内容被改写了")

    def test_prose_never_uses_a_slash_for_a_range(self):
        """「第 3/4 章」这类区间必须写成「第 3、4 章」——斜杠会被排成 ¾。"""
        offenders = []
        for page in sorted(DOCS.glob("*.md")):
            for num, line in enumerate(prose(page.read_text(encoding="utf-8")).split("\n"), 1):
                m = RANGE.search(line)
                if m:
                    offenders.append(f"{page.name}:{num} {m.group(0)!r}")
        self.assertEqual([], offenders,
                         "把区间写成了斜杠：读起来像分数，且一旦分子分母落在 "
                         "pymdownx 的分数表里就会被排成分数（如「第 3/4 章」→「第 ¾ 章」）：\n  "
                         + "\n  ".join(offenders))

    def test_every_rewrite_trigger_in_the_prose_has_been_reviewed(self):
        """正文里出现的每个触发串都必须是「已复核的分数 / 序数」。

        出现新串就红灯：要么它确实是分数（把串加进 REVIEWED），
        要么它是个区间 / 代码味的东西（改写成中文标点）。
        """
        found = {}
        for page in sorted(DOCS.glob("*.md")):
            text = prose(page.read_text(encoding="utf-8"))
            for hit in triggers(text):
                found.setdefault(hit, []).append(page.name)
        unreviewed = {k: sorted(set(v)) for k, v in found.items() if k not in REVIEWED}
        self.assertEqual({}, unreviewed,
                         "出现了没复核过的 smartsymbols 触发串（会被改写成排版符号）：\n  "
                         + "\n  ".join(f"{k!r}  ← {v}" for k, v in sorted(unreviewed.items())))


if __name__ == "__main__":
    unittest.main()
