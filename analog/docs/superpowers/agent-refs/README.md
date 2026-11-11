# Agent 引用清单（整包重做 2026-11-03）

实施 agent 用到的外部 / 本机资源索引。**只登记路径与用法，不把大 skill 原文复制进仓。**

| 资源 | 位置 | 用途 |
|---|---|---|
| humanizer-zh 主技能 | `D:\Users\monidianlu\humanizer-zh.md`（本机，仓库外） | 全书口吻重写的权威规则；每章重写前后通读 |
| yang0/handraw-style | https://github.com/yang0/handraw-style | 封面 / EP 缩略图 / 社媒主视觉提示词与风格编号（FA-029） |
| FA-029 DNA 规范 | `analog-book/HANDRAW-STYLE.md` | 纸 C-30 `#fdf8ea`、墨 C-31 `#16202b`、标记 C-29 `#a4630f` 与线宽 / 语义色规则 |
| 手绘生成器 | `scripts/handraw.py` | 正文 / 印刷 / SVG 共用的纸墨外壳（`handraw.apply` 等）；改气质只改这里 |
| humanizer 白名单 | `docs/superpowers/templates/humanizer-whitelist.md` | 允许保留的工程对比整行条目，供 `check_ai_slop.load_whitelist` 读取 |

使用规则：

1. 章节正文重写前先读 humanizer-zh，再读白名单；新增真工程对比必须**先改白名单再写正文**。
2. 任何视觉产物（hero / 动画 / 封面）动手前先核对本表两份 DNA 文档；禁止凭印象调色。
3. 本文件路径若失效（换机器 / 迁移），只改本表，不在章内散落硬路径。
