# 正文语言规范：把硬核内容写成人话

本书的内容密度不降，**句子结构降**。读者卡住的地方几乎从不是物理，而是
一句话里塞了四件事。本文给出可执行的改写规则与阈值，并标注每条的出处。

度量工具：`python scripts/audit_readability.py`
安全闸：`python scripts/check_prose_safety.py`（确认改写没弄丢插图依赖的数字）

## 为什么改：读者真正卡住的位置

调研社区反馈，读者卡点集中在六类，全部是**表述问题**，不是内容深度问题：

1. 符号或缩写未定义就使用；
2. 「假设……」跳步，不说假设从哪来；
3. 推导缺中间步骤；
4. 只给公式，不给物理直觉；
5. 缺量级感——读者不知道「正常值」该是多少；
6. 一段里堆叠多个新术语。

出处：EEVblog
[A learner's rant](https://www.eevblog.com/forum/beginners/a-learner_s-rant/)；
EET-China
[为什么我努力学模电还是学不好](https://www.eet-china.com/mp/a34912.html)。
（这两条是零散论坛反馈的归纳，不是系统研究。）

## 硬阈值（可机械检查）

| 指标 | 阈值 | 出处 |
|---|---|---|
| 无标点单句 | ≤20 字最佳；30–39 字须语义明确；>40 字拆 | [ruanyf/document-style-guide](https://github.com/ruanyf/document-style-guide) `text.md` |
| 含逗号长句总长 | ≤100 字 | 同上 |
| 段落行数 | ≤4 行最佳，≤7 行硬限 | 同上 `paragraph.md` |
| 段落句数 | >5–6 句视为超载，必须拆 | [Google style](https://developers.google.com/style/paragraph-structure) |
| 每句想法数 | 1 | [plainlanguage.gov](https://digital.gov/guides/plain-language/writing/clear-short) |
| 术语首现定义率 | 100% | ruanyf `text.md` |
| 中英文/数字间空格 | 0 违规 | [chinese-copywriting-guidelines](https://github.com/sparanoid/chinese-copywriting-guidelines) |

本书作为硬核教材，`audit_readability.py` 的告警线设在 60 字（长）与 90 字
（很长），比上表宽松——**这是分流用的工作线，不是放宽标准**。排行榜上分数
高的小节仍按上表 100 字硬限改。

## 改写规则

### 结构

1. **结论先行**：每节、每段的第一句给结论或可用结果，推导跟在后面。
   出处：Google style「critical information first」。
2. **一段一个主题**，中心句放段首。出处：ruanyf `paragraph.md`。
3. **并列项拉成列表**。一句话里出现「①②③」或三个以上分号并列，一律改
   列表。这是本书最高频的缺陷形态。
4. **先失败，再理论，再可用电路**。Jim Williams
   [AN47](https://www.mit.edu/~6.331/an47fa.pdf) 的结构：Murphy 失败画廊 →
   Tutorial → Applications。本书的「故障图谱」「算一笔」已是同构，继续保持。

### 句子

5. **一句一个想法**。出现「……，而且……，但……，所以……」四段挂车，拆。
6. **主动语态**。
7. **主谓宾靠近**，别在主语和谓语之间插入长定语。
8. **代词指代唯一**。「它」在一段里不得指两个不同对象——这是本书硬核段落
   里最隐蔽的卡点。

### 术语与量级

9. **术语首现给定义**，哪怕只有半句。后文才可用缩写。
10. **给量级感**。只说「阻抗高」没用，要给「几十 kΩ 以上」。读者缺的往往
    是正常值范围，不是公式。
11. **先量级，后精确**。经验法则（rule of thumb）显式写出来。出处：AoE3
    与 Camenzind
    [Designing Analog Chips](http://designinganalogchips.com/)（作者明确
    反对数学堆砌，主张先懂原理再计算）。
12. **数字必须可溯源**。正文数字是插图的事实来源，改写时一个都不能丢，由
    `check_prose_safety.py` 把关。

### 不做的事

13. 不降低内容密度，不删算例，不删故障案例。
14. 不把硬核推导删掉换成比喻——推导可以移到小节末或脚注，但不能消失。
15. 不为了凑短句把一句话切成语义不完整的碎片。「概括不是压缩」。

## 改写流程

```
python scripts/audit_readability.py --top 15     # 找最差的节
python scripts/audit_readability.py --section N  # 看该节的超长句
# 改写：拆长句、并列转列表、结论提到段首
python scripts/check_prose_safety.py             # 确认数字没丢
python scripts/audit_readability.py --section N  # 复测分数
```

全书基线（2026-11-06，改写前）：246 小节、7134 句，长句（>60 字）11.7%、
很长句（>90 字）2.3%、多从句句 9.7%。

## 参考来源

- [ruanyf/document-style-guide](https://github.com/ruanyf/document-style-guide)：中文技术文档写作规范，句长与段落阈值的主要出处。
- [Google developer documentation style guide](https://developers.google.com/style/paragraph-structure)：结论先行、段落句数上限。
- [plainlanguage.gov / digital.gov](https://digital.gov/guides/plain-language/writing/clear-short)：一句一个想法、段落长度。
- [sparanoid/chinese-copywriting-guidelines](https://github.com/sparanoid/chinese-copywriting-guidelines)：中英混排排版。
- [Jim Williams AN47](https://www.mit.edu/~6.331/an47fa.pdf)：失败案例先行的章节结构。
- [Designing Analog Chips (Camenzind)](http://designinganalogchips.com/)：反数学堆砌、先原理后计算。
- [The Art of Electronics 书评](https://tangentsoft.com/elec/reviews/aoe2.html)：插图密度与「真实电路而非玩具电路」。
- [Crafting Interpreters 导言拆解](https://refactoringenglish.com/blog/crafting-interpreters-intro/)：导言前四句回答「学什么／为何学／面向谁」。
