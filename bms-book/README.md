# BMS 实战：从一颗电芯到一套证据链

> 参考 BMS-Z 开源教程（上游 [GitHub](https://github.com/zhuguang-ZFG/BMS-Z)）、foxBMS、PyBaMM 与社区实践<br>
> 版本：v0.5.0 · 2026-10-23 · 中文<br>
> 在线阅读：[站点伴读书入口](https://zhuguang-zfg.github.io/BMS-Z/reading.html)（含上一章/下一章导航与全文搜索）

## 这本书想干什么

市面上讲 BMS 的书，大多在“讲知识”；这本书想讲的是**知识怎样变成证据**。

一颗电芯为什么在这个 tick 被判过压？一条 SOC 曲线凭什么说自己是准的？一个模型参数错了，残差会怎么告状？——BMS 的日常不是背公式，而是不断地回答：**谁量的、量了几次、拿什么对照、谁签字**。

这本书用 BMS-Z 的真实实验数据、可运行代码和 154 张动画做骨架，把“原理”落到“能复现的数字”上：

- 同一个 15 mV 新息，在 SOC 0.05 处只值 0.2%，在平台区却值 1.9%；
- R0 写大 10 倍，SOC RMSE 冲到 41.51%；C1 写大 10 倍，只有 1.00%；
- 100 拍里故意弄坏 1 帧，解析器仍收全 99 帧；
- 25,461 行外部数据，改 1 个字节就被 SHA-256 拦下；
- 被动均衡补 1 Ah 要 25 小时烧掉 4 Wh，主动均衡 0.5 小时只损 0.7 Wh；
- 400 V 系统按 100 Ω/V 算，绝缘低于 40 kΩ 就不许上高压。

这些不是“结论”，是**可以被你再跑一遍的实验**。

第 13、17、27 章的科学曲线可用 `python bms-book/generate_figures.py` 重算（另外需要 matplotlib；阅读和构建不需要）。指数辨识、新息时序与观测权重图给出全部合成条件。

## 读者

- 有 Python 基础、想进入储能/电动车 BMS 的软件工程师
- 做过嵌入式、需要补齐系统与安全视角的硬件工程师
- 电子/车辆/能源专业，想做课程设计或毕业设计的学生
- 已经在看 BMS-Z，想要一本“把为什么讲透”的伴读书

不要求电化学背景；第 1 章从“离子走里面，电子走外面”讲起。

## 目录

**导读**

0. 前言：把 BMS 当证据学

**第一部分 物理与系统**

1. 一块电池里在发生什么
2. BMS 的六件事与三种形态
3. 电芯化学家族
4. 保护板解剖
5. 测量链：误差预算不是表格，是站位

**第二部分 保护与均衡**

6. AFE：模拟前端
7. 保护：tick 48 的那两拍
8. 硬件失效与二次保护
9. 均衡：平均是安慰值

**第三部分 模型与算法**

10. 模型：一条 OCV 曲线的四项
11. CC-CV：恒流恒压
12. SOC：三条路与三个锚点
13. HPPC：40 秒窗为什么会骗人
14. SOP 与热：三约束取最小，温度慢半拍
15. SOH 的两张脸
16. 老化物理
17. 无真值诊断：没有答案时怎么听诊

**第四部分 数据与通信**

18. 通信：一帧正确，不等于数据可信
19. 总线全景
20. 上位机与数据链
21. 数据准备：先验身份，再用数据

**第五部分 工程与生态**

22. 开源架构：foxBMS 2 与 DIY 三条路线
23. PyBaMM：模型不是答案
24. BMS × AI：能解释，不能签字
25. 功能安全与量产
26. 从原型到产品：证据链与 12 周

**第六部分 深读**

27. EKF 的六个矩阵
28. 一条 HPPC 曲线的解剖
29. 帧状态机的八个边界
30. 热的一阶账本

**第七部分 诊断与高压：两张量产准考证**

31. UDS 诊断与刷写
32. 高压安全与绝缘检测

**附录**

A. BMS-Z 使用地图　B. 项目清单　C. 术语表　D. 参考资料　E. 习题参考答案

## 怎么读

- 想建立全局观：0、1、2、7、22、26。
- 想做算法：10–17，配 `code/` 与 BMS-Z 的 `code/soc/`。
- 想吃透热这本账：14、30，配 `code/thermal_lump.py`。
- 想做通信/数据：18–21；想做诊断刷写与高压量产：25、31、32。
- 想用 AI 加速但不踩坑：24。
- 自测：每章练习先自己做，再对附录 E 参考答案；数值题附录给了关键步骤。

每章结构固定：**一个现场 → 原理 → 可复现数字 → 坑 → 练习**。

## 图解与交互怎么读

32 章正文现在每章都有图：全书 58 个图解位置，其中 33 个可以点击“播放动画”，每个配“先看哪里”和“看完追问”。默认显示矢量静态快照，停止播放后回到静态图；PDF 使用同一快照，保留图注与读图问题。

第 10 章提供 **OCV 四项实验**：拖动 SOC 和斜率，看曲线、四项贡献与 5 mV 的局部换算。第 14 章提供 **SOP 三约束实验**：拖动 OCV、内阻、SOC 和预测窗，看主导约束、端口功率与欧姆生热怎样一起变化。全部是明确标注条件的教学模型。

动画复用教程中的 SVG 真源；打印快照在 `assets/print/`，时刻清单在 `visuals.json`。重生成快照需 Playwright 与 Edge：`python bms-book/snapshot_visuals.py`；普通阅读和构建无需安装它们。离线 HTML 将静态图、动画与交互脚本全部内嵌。

## 与 BMS-Z 的关系

BMS-Z 是这套书的“实验台”：七篇阶段教程、154 张动画、三份可运行代码、十一期共学。本书是它的“深读本”，把其中的数字、失败与取舍展开讲。

- 上游：https://github.com/zhuguang-ZFG/BMS-Z
- 在线站：https://zhuguang-zfg.github.io/BMS-Z/
- 引用均注明出处；本书正文采用 **CC BY-SA 4.0**，与 BMS-Z 文档许可一致。
- 引用本书请用 `CITATION.cff` 中的格式。

## 代码

从仓库根准备环境（Python 3.10+、Node.js 24+）：

```bash
npm ci
python -m pip install -r bms-book/requirements.txt
python bms-book/build_html.py     # 生成 dist/bms-book.html（公式构建期渲染，插图内嵌，可断网阅读）
python bms-book/check.py          # 质量门：结构契约 + 14 份 demo 全跑 + 书↔demo 钉死数字对账
```

HTML 提供四条阅读路线、分部学习目标、章节标识，支持手机排版、随系统切换深色模式、返回目录；`--out-dir` 指定输出目录；加 `--pdf` 额外生成带书签带页码的 PDF（需 Chrome/Edge，`--browser` 可指定路径）。章节、版本与实验清单统一维护在 `manifest.json`；以下单独实验命令从 `bms-book/` 目录运行。

```bash
python code/soc_coulomb_ocv.py   # SOC 三条路的迷你对照
python code/ekf_soc.py           # 两状态 EKF vs 纯库仑
python code/hppc_fit.py          # 脉冲反推 R0/R1/C1；40 s 窗的偏差
python code/frame_parser.py      # CRC、坏帧、重同步
python code/thermal_lump.py      # 集总热模型：稳态、τ、熵热、低通
python code/cccv_charge.py       # CC-CV：恒流恒压的安时账
python code/ic_dv.py             # dQ/dV：两座峰的老化指纹
python code/balancing_energy.py  # 均衡：被动 25 h/4 Wh vs 主动 0.5 h/0.7 Wh
python code/data_audit.py        # 行级体检：8 项检查抓 3 类注入瑕疵
python code/insulation_bridge.py # 不平衡桥解绝缘电阻；平衡桥漏检对称退化
python code/pybamm_fit.py        # 仿真当裁判：平台标定 ECM，两端露馅
python code/uds_demo.py          # 迷你 UDS：会话、seed-key 解锁、DID、NRC
python code/measurement_budget.py # 测量：绝对上界、随机噪声、漂移、时序与保护裕量
python code/estimator_evidence.py # 估计证据：观测权重、NIS 时序、SOH 端点不确定度
```

书中数字来自 BMS-Z 2026-10-09 的实测/合成记录；你的环境不同，结果可能有小数位差异（`check.py` 会把漂移当成失败提示你）。

## 许可

- 正文：CC BY-SA 4.0
- 代码：MIT

## 安全声明

锂电池滥用可能起火或爆炸。本书与 BMS-Z 的 DIY 内容仅用于学习与低压实验，**不得用于生命安全、并网、车用或无人值守场景**。高压操作必须由具备资质的人员按当地法规进行。
