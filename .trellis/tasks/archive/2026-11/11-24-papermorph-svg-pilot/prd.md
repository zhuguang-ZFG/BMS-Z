# 用生成 SVG 制作被动均衡互动课试点

## Goal

制作一节被动均衡互动课原型，使用程序生成 SVG 表现电路与计算结果，并评估 Papermorph 是否适合后续课程。

## Requirements

- Place a short interactive passive-balancing lesson in §9.2, following the chapter's existing 4 V / 100 Ω / 1 Ah worked example.
- Hold cell voltage at 4 V and discharged imbalance at 1 Ah. Let the reader adjust resistance from 50 Ω to 200 Ω in 10 Ω steps.
- Update one generated inline SVG diagram and the current, resistor power, and ideal time from the same input state.
- Ask one multiple-choice prediction question; grade it immediately and explain each wrong choice.
- Keep the complete 100 Ω static diagram and 40 mA / 0.16 W / 25 h outputs readable when JavaScript is disabled. Include meaningful SVG accessible text and keyboard-operable native controls with announced readouts.
- Make the lab available in the VitePress chapter and offline single-file HTML. Keep the printed lesson understandable through a static default example.
- Assess Papermorph for future lessons, but do not install it or add packages during this pilot.
- Make no claim of thermal simulation: heat marks encode dissipated power only; ideal balancing time excludes duty cycle, thermal derating, and controller limits.

## Acceptance Criteria

- [x] At the default state, show 4 V, 100 Ω, 1 Ah, 40 mA, 0.16 W, and 25 h. At the 50 Ω and 200 Ω boundaries show 80 mA / 0.32 W / 12.5 h and 20 mA / 0.08 W / 50 h.
- [x] At 375 px there is no page-level horizontal overflow; slider and answer buttons work with keyboard input, and reset works.
- [x] Correct and incorrect answers produce specific, accurate feedback; changing the slider updates SVG and all results together.
- [x] Online and offline HTML both run the interaction without a network or new runtime dependency; no-script and printed versions retain the static example.
- [x] Reader tests, BMS book tests, the book quality gate, and VitePress build/test pass.
- [x] Record a dated Papermorph fit assessment with the official repository revision, workflow/offline/feature/dependency tradeoffs, and a clear install recommendation.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
# 被动均衡互动课 SVG 试点

在 BMS 深读书第 9 章做一节短互动课，用程序生成的 SVG 把被动均衡的电阻、电流、功耗和理想均衡时间连起来。读者改变电阻后能马上看到图和数字同步变化，并完成一道即时判分的预测题。试点完成后，再根据实际制作与阅读效果评估是否值得安装 Papermorph。

## 读者需求

第一次读到“被动均衡是用时间换少量发热”的读者，可以亲自改变一个参数，观察它如何同时影响三笔账，而不是只看一幅固定示意图。

## 范围

- 放在 `bms-book/book/09-均衡.md` 的 §9.2，承接现有的 4 V、100 Ω、1 Ah 教学算例。
- 以均衡电阻为唯一可调输入；电压与需要补回的电量固定，让读者看清一个变量造成的连锁变化。
- 显示电阻支路、均衡电流、热功率与理想时间；提供一道“电阻减半会怎样”的选择题和即时反馈。
- 同时供站点章节和可断网的整书 HTML 使用。打印状态保留默认示意图与三笔账。
- 试点本身用项目内代码和原生 SVG 实现。先不安装 Papermorph、不增加第三方依赖、不制作旁白视频或整章改编。

## 验收标准

1. 默认输入为 `U=4 V`、`R=100 Ω`、`ΔQ=1 Ah`，显示 `I=40 mA`、`P=0.16 W`、`t=25 h`；与现有第 9 章和 `bms-book/code/balancing_energy.py` 的算例一致。
2. 电阻范围为 `50–200 Ω`，每 `10 Ω` 一档。拖动后，SVG 与所有数值由同一状态即时更新。边界值 `50 Ω` 得到 `80 mA / 0.32 W / 12.5 h`；`200 Ω` 得到 `20 mA / 0.08 W / 50 h`。
3. 图明确表示并联泄放支路和电阻上耗散的功率；热强弱仅作功率示意，不伪装成温度或热仿真。
4. 选择题能判定“电阻减半，电流和功率加倍，理想时间减半”，错误答案给针对性解释；可键盘操作，并有可读的状态反馈。
5. JavaScript 未运行时仍能读到完整默认示意和默认数值；站点与离线 HTML 中控件正常，窄屏不造成整页横向溢出，打印保留静态算例。
6. 用测试锁住公式、边界值、判题反馈、重置与静态回退；通过 BMS 书测试、书稿质量门和站点构建。
7. 写出 Papermorph 的试点评估结论，至少比较互动/判分价值、旁白或分拍能力、Codex 工作流适配、离线构建适配、依赖和费用；明确给出“暂不安装 / 再试装”的建议与依据。

## 不在范围内

- 把全书或其他章节迁移到 Papermorph。
- 依赖云端模型、账号、外部运行时服务或付费语音/图片生成。
- 把理想电阻模型描述为产品热设计、闭环均衡或电芯仿真的依据。
- 要求纸面 PDF 或 EPUB 具备交互功能；它们保留经过核对的静态默认算例即可。

## 保留约束

- 保留第 9 章已有静态图文和来源边界；交互是补充，不改写能修复容量差的事实边界。
- 不覆盖用户已有的 `package-lock.json` 修改。
- 后续实现应从已包含 PR #114 的最新 `main` 开始；不在本次规划中切换工作分支。
