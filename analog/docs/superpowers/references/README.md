# 策展引用库说明

> 正文引用的**唯一数据源**是 `analog-book/data/references.yml`（书籍/论文/datasheet/OSS 条目）与 `analog-book/data/sources.yml`（事实源追溯表）。本目录只放评估笔记，不放正文数据，避免双源。

- 仓库条目规则：`id` 唯一（`ref-NNN` 只追加不重编号）；`chapters` 为 0–18 整数；OSS 条目注明用途与许可立场。
- OSS 候选评估表：`oss-animation-candidates.md`（Task 11b 决策记录）。
- 闸：`python scripts/check_references.py analog-book/data/references.yml analog-book/data/sources.yml`；测试 `scripts/test_references.py`。
