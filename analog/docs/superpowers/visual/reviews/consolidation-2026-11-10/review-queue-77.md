# C 组：内容漂移待重审 8 张（papercut，签名版与当前版文本有实质差异）

**更新**：原 77 张中 69 张 python-handraw-v1 经 `label_handraw_figures.label()` 精确变换测试
（当前字节 == label(签名版)），已按 `preserve_review_for_labels` 规则依法继承原签核
（review_record 附 metadata_amendments 记录 before/after sha）。**本队列只剩 8 张真内容变更**，
字节与签核不符，维持 status=generated，需人工目审。

> 签核方式：回列 accepted id，代理翻转 status 并补 review_record（新 sha256 + 评分）。

## 待审清单（8 张，按章序）

| # | id | 章·锚 | numΔ 摘要 | 签核 |
|---|---|---|---|---|
| 1 | ch13-current-sense-sides | 13·13.8 | 图内文本有变 | ✅ 已签 2026-11-10 |
| 2 | ch13-h-bridge-states | 13·13.7 | 图内文本有变 | ✅ 已签 2026-11-10 |
| 3 | ch13-opto-ctr | 13·13.11 | 图内文本有变（0.5/50/100 等；source_facts 已补 13.11a） | ✅ 已签 2026-11-10 |
| 4 | ch14-dft-testpoints | 14·14.8 | 图内文本有变 | ✅ 已签 2026-11-10 |
| 5 | ch14-ltspice-five | 14·14.6 | 底行结论句改写（「仿真不过一定不能工作」→「仿真异常先区分模型、数值与电路」） | ✅ 已签 2026-11-10 |
| 6 | ch14-tolerance-three | 14·14.10 | 图内文本有变 | ✅ 已签 2026-11-10 |
| 7 | ch15-crosstalk-3w | 15·15.3 | 图内文本有变 | ✅ 已签 2026-11-10 |
| 8 | ch15-via-parallel | 15·15.3 | 图内文本有变 | ✅ 已签 2026-11-10 |

逐张预览与签名版对照见同目录 `<id>.webp` / `<id>.prev.webp`。
