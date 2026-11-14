# BMS-Z yuyu 式改造 · 验收报告（2026-11-14）

参照 `D:\Users\claude`「yuyu 合集」格式，对 BMS-Z 两卷（插图 + 文字）的彻底改造。
原则：结构行不动、kp-backlink 块禁改、表格单元格不改、历史段不改；六要素只增不改。

## 1. 插图（47 枚新 SVG）

| 类别 | 数量 | 文件 | 契约 |
|---|---|---|---|
| 卷 II 章徽 | 38 | `bms-book/assets/emblems/ch00–ch37.svg` | 严契约：单根 svg+viewBox、仅 currentColor、无 `<text>`、≤6000B |
| 卷 II 篇题 | 9 | `bms-book/assets/emblems/part-p0–p8.svg` | 放宽：纸底 `#fffdf8` + `#14213d` 主结构 + `#f2b84b` 琥珀 + `#176b73` 青 + `#94a3b8` 辅助，拉丁标签 `<text>`，禁 CJK，≤6000B |

- 接线：卷 II `bms-book/book_art.py`（EmblemLibrary、双层校验、data URI 内联、`--strict-emblems`），`build_html.py` 章首/篇题插入；卷 I `book/illustrations.py chapter_art()` + `assemble.py` 幂等守卫（与 `build_site.py:332` 共处，两世界都恰好 19 枚）。
- 篇题风格对齐卷 I（纸底+三色+拉丁标签）；章徽两卷统一严格单色。深色反色只作用于单色章徽。
- 测试：`tests/test_book_art.py` 19 例、卷 I `test_book_emblems.py` 8 例。

### 迭代记录（2 轮）
- 第 1 轮：子代理 QA 渲染 71 PNG 目检 → 高 1（ch27 出界裁切）、中 5（ch03/14/17/25/35）、低 15、OK 17；篇题 p7/p8 中、p0/p4/p6 低。
- 返工：IllEmblemA/B/C 修 21 枚；IllPlates 全部重涂为卷 I 纸底语言（首版误用深底，已纠正；青色用 `#176b73` 替代 `#5eead4`，纸底对比 1.3:1 → 6.1:1）。
- 第 2 轮：重渲染复检——ch27/14/35/03/17/25 全部目检通过，高/中缺陷清零；篇题 9 枚目检通过（构图、标签、基线、格线几何经 getBBox 实测）。

## 2. 文字（六要素补齐 + 去 AI 味）

- 六要素审计：`tools/audit_structure.py` → 卷 I **19/19**、卷 II **37/38**（唯一缺：附录 D e5，无真实跨卷同构，记 Deferred；附录 A–E 的 e2/e3/e4 按 N/A 不计）。e5 判据从严：只认明确另一卷目标（「参见卷/卷 I/卷 II」），裸「同构」不算——据此为卷 II 第 19 章补 19.9（CAN 仲裁 ↔ 卷 I ch5 开漏线与）、第 28 章补 28.9（HPPC 脉冲辨识 ↔ 卷 I ch1 一阶 RC 零输入响应），均为真实跨卷对应。
- 去 AI 味：`.local/polish-tools/verify_polish.py`（含 ALLOW_ADDED_STRUCT 批次机制）最终 **FAIL files: 0**。

### 迭代记录（2 轮）
- 第 1 轮： PolishV1/V2 worker 修完全部标记文件 + 我直修剩余 7 文件 → 门禁绿。
- 第 2 轮：ReviewText2 复审 6 文件（含数值实跑核对），发现 1 高 6 中 若干低，全部处置：
  - **ch24 24.9 边界账代码与判据错误（高）**：`len==64` 在 `>63`/`>=63` 下均通过，演示不出漂移；已改为 `>64`/`>=64`（与 24.5 正文一致）并实跑验证「放/拒」输出；「三笔账」改「四笔账」；注释「第 5 问」改「第 2 问」。
  - **小节位置体系统一（中）**：卷 I ch5/10/11/12/13 与卷 II ch01–15 的新增小节全部移到「自检/练习」之前并续编号（对齐 ch6–9 与 ch16–31 既有体例）；卷 II 新增表全部补 `**表 N-k**` 编号（31 张），章内表号连续。
  - **ch5**：表 5-3 与表 5-2 四行去重（原因栏补区分角度）；「下一章」过渡句移至章末 blockquote；398ns/400ns 表述与低电平读法修正。
  - **ch10**：开篇「两张网表都用受控开关」改为与实物一致；翻车对照表补编号 表 10-1。
  - **低**：ch12 补空行、断电 10 天标「推算」；附录 B 同构改指「卷 I 附录 D《视频资源汇总》」；ch12 套话（不是…而是）改写。
  - **全量 suite 暴露的连带漂移**：卷 I curriculum 章首块节数（19 章 --write 重算写回）、wave1 表数合同（ch14 11→12、ch16 12→13，新增翻车对照表，方向更严）、字体子集重建（新字符「沓」）、figures-v2 74 枚补 data-composition 血统标定（元数据级）。
- 门禁修补：`check.py` 资产孤儿检查排除 `assets/emblems/`（章徽由构建内联，契约由 strict-emblems + test_book_art 把守）；§ 引用豁免加跨卷语境（`卷 I/卷 II`，本节号表只含本卷）；`test_build.py` 夹具 §5.10 → §5.99（5.10 因补齐变为真实节，非弱化）。

## 3. 门禁终态（全部本地实测）

| 门 | 结果 |
|---|---|
| 卷 II pytest（bms-book/tests） | 311 passed |
| 卷 II check.py | PASS（文件集/章结构/图号/表号/交叉引用/资产/demo/版本） |
| 卷 II strict 构建 | 绿（38 章，28.5MB，47 枚全内联） |
| gen_curriculum_pages --check | PASS（80 概念、32 章回链无漂移） |
| glossary_lint | 0 问题 |
| verify_polish | FAIL files: 0（visual-manifest.yml 按记录文件豁免，同 reviews 口径） |
| audit_structure --volume both | 19/19 + 37/38 |
| 卷 I analog-book build --check | exit 0 |
| 卷 I remake-check（ai_slop/chapter_contract unittest） | OK |
| 卷 I check_ai_slop（18 章全量） | exit 0 |
| check_references / svg_floor / book_data / lab_packages | 全绿 |
| 卷 I curriculum 章首块（`curriculum.py --check`） | 16 passed（节数已按补齐后重算并 --write 写回 19 章） |
| 卷 I wave1 合同 + 字体子集 | 12 passed（子集已 `--build` 重建，覆盖新增字符如「沓」） |
| 卷 I figures-v2 血统标定 | 33 passed（74 枚补 data-composition 标定，元数据级变更） |
| docs-sync（README/BOOK.md 再生后） | 5 passed |
| 卷 I analog 全量 pytest | 1002 passed / 10 failed → 修后剩 4 failed，全为本机环境缺件（见已知问题 1） |

## 4. 已知问题 / 遗留

1. **卷 I 全量 pytest 余 4 个环境性失败**：`test_ship_residual`（`video/shots/*.json` 不在仓库，未跟踪、无生成脚本，干净检出必红）；`test_lab_packages`/`test_circuit_examples` 3 例（本机无 ngspice，CI 用 apt 安装）。均与本次改造无关；内容性失败 6 例（curriculum 漂移、wave1 表数合同、字体子集、figures 标定）已全部修复。
2. **附录 D e5 Deferred**：无真实跨卷同构，未硬塞。
3. **A1–A8 审校数值疑点**：遗留未裁决（前轮记录）。
4. **ngspice 网表未实跑**：ch5/ch10 实验节只做了公式侧核对（本机无 ngspice，CI 有）。
5. **全部改动未 commit**，等用户下令；57 个 `.tmp-*` 与 `D:\temp\User\pytest-of-zhugu` 坏 ACL 仍待用户管理员跑 `cleanup-tmp-elevated.cmd`。
