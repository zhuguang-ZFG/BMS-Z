---
search: false
---

# yuyu 格式改造基线（M0 冻结，2026-11-13）

## 目标与范围（用户已确认）
参考 D:\Users\claude 的 yuyu 合集格式改造本仓：卷 II 38 枚章徽 + 9 枚篇题全做；两卷 57 章六要素全审计并分片补齐；卷 I 对拍核查补缺。SPEC：docs/YUYU-FORMAT-OVERHAUL-SPEC.md。

## 结构事实（已核实）
- 卷 I = analog/analog-book/（19 章 ch0–ch18，篇 I–V，附录 A–G）。**章源 = analog/docs/p*-*.md**（精修提交 1306a1c 改的是这里；analog/build/docs/ 是站点侧副本，与源全文件分叉，勿当源改）。
- 卷 I 插画层已存在：analog/analog-book/static/illustrations/（ch00–ch18.svg 19 枚章徽 + part-i–v.svg 5 枚篇题 + static/cover-art.svg）。契约在 analog-book/book/illustrations.py（part_art()：SAFE_NAME_RE、token 黑名单、无 href/url()/CJK）。
- **卷 I 章徽消费链**：grep 未见 assemble/content/frontmatter 消费 ch*.svg——章徽文件当前未被书构建内联（站点侧也未引用），接线属 M3 对拍内容。
- 卷 II = bms-book/（38 章 = p0 导读 1 + p1 5 + p2 4 + p3 8 + p4 4 + p5 5 + p6 4 + p7 2 + p8 附录 5）。章源 = bms-book/book/*.md（00-前言.md … 37-*.md，按文件名前缀编号）。
- 卷 II 封面已有：build_html.py:969 内嵌 base64 手绘 SVG（cover_src）。章首有 chapter-ribbon + chapter-compass；part-divider 有 data-part 配色 CSS（build_html.py:363-371）；无章徽/篇题机制（无 emblem 装载）。
- 卷 II 其他图：assets/*.svg 技术图（按章编号）、illustrations/handdraw/ AI 位图（manifest 门 tools/check_handraw_manifest.py，不动）。
- 顶层 book/：两卷 orchestrator（《从模拟电路到 BMS》，卷 I/II 各 ≤700 页）。

## 门禁基线（2026-11-13 本地实测）
- **修复前**：CI tests workflow（64f744e, run 43416431931）红——visual-check 的 test_records_match_published_text：12 条 text-replacements 记录与精修后正文漂移（破折号收口 + 「真正」清理所致）。
- **已修复**：12 条记录（insertion-ch01 ×6、insertion-ch02 ×2、insertion-ch03 ×2、insertion-ch07 ×1、python-papercut-2026-11-05 ×1）的 after 文本与 removed_prose_chars 已同步为当前正文。**待提交**（执行期不 commit，等用户下令）。
- 修复后实测：test_visual_text_replacement.py 17 passed；check_visual_manifest.py PASS（0 项）；test_visual_release/calculations/density/distribution/manifest/fidelity 全 OK；test_pcb_visual_units + test_design_visual_models 11 passed。
- 其余门禁（64f744e 时全绿）：gen_curriculum_pages --check、glossary lint 0、pytest book/tests 16、check_docs PASS（6208 链接/24 草图契约）、docs-sync 5 OK、build.py check 21/21、verify_polish FAIL 0。
- CI 环境怪癖：deploy-pages 并发组 bms-z-pages 会被旧 run 卡队列；links 曾外链超时 rerun 即绿。

- 卷 II 接线挂点（M1/M2 工具 worker 用）
- 章首：build_html.py chapter-ribbon（示例 :244）+ chapter-compass（:88-98）——章徽插 ribbon 旁/章首区。
- 篇首：.part-divider（:375 起，data-part 配色 :363-371）——篇题插画插 divider 区。
- 内联方式：与封面一致走 data URI（base64）内联，保持单文件 HTML 自包含。
- 缺文件策略：过渡期 warnings 不 fail；终态全部就位后 --strict  fail（与卷 I opener_art 行为对齐）。

## 章徽命名映射（已核实 book/ 全部 38 文件）
- 数字章 00-*.md … 32-*.md（33 章）→ ch00.svg … ch32.svg（NN=文件名数字前缀，两位零填充）。
- 附录 附录A…E（按 A→E 顺序）→ ch33.svg … ch37.svg。
- 篇题：part-p0.svg … part-p8.svg（对应 manifest parts[].id）。
- 38 枚章徽已全部交付（assets/emblems/）并通过统一契约自检（ALL OK）。
