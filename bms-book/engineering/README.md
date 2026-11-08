# 深研样章（P1）

这里是 BMS v3 深度改造的 P1 样章工作区。正文暂时独立存放，**不进入** `bms-book/book/` 的 32 章清单：书稿章数与导航由 `docs/.vitepress/book-sources.mjs` 枚举，提前塞入会破坏构建门。P2 装配时再决定章节编号、导航与页面组件。

## 当前状态

| 单元 | 正文 | 图 | 参考实现 + 测试 | 状态 |
|---|---|---|---|---|
| S2 一条电压曲线能识别出多少东西 | [S2-一条电压曲线能识别出多少东西.md](S2-一条电压曲线能识别出多少东西.md) | 5 张（`assets/engineering/s2-model/`） | `code/engineering/identification/`（15 项测试） | 本地完成 |
| S1 测量链 | 未开始 | — | — | 未开工 |
| S3 预充时序 | 未开始 | — | — | 未开工 |

S2 的"本地完成"指：正文、图、参考实现、窄测试、留出验证与反例都可复算。它**不**包含：

- 硬件或台架证据（全部数值为合成真值）；
- 真人读者试读与独立作答记录；
- 窄屏（390/820 px）、A4、离线包验收——这些依赖 P2 装配后的站点与出版链。

## S2 的复算入口

```text
python code/engineering/identification/s2_identification.py --out <新目录>
python code/engineering/identification/s2_identification.py --out <新目录> --mode student
python code/engineering/identification/make_s2_figures.py
python -m pytest code/engineering/identification -q --basetemp=".tmp-s2"
```

- `--mode reference` 写 `config.json`、`observations.csv`、`report.json`；
- `--mode student` 不生成 `report.json`，只写配置、观测与问题；合成真值保留在配置里供自查，交付物是过程与结论；
- 生成图的每个数字都读自 `s2_identification.py`，图与报告不会各自漂移。

S2 的三个场景 ID：`S2-pulse-identification`（主场景）、`S2-flat-ocv`（偏置反例）、`S2-short-window-ambiguity`（短窗混淆的独立曲线）。改动任一配置字段都必须登记新 ID。

## 图

| 图 | 回答的问题 |
|---|---|
| `S2-F1-rc-polarity.svg` | 三项电压归谁所有、极性怎么定、状态在区间两端如何跳变 |
| `S2-F2-common-time-axis.svg` | 电流、OCV、欧姆项、极化项、端电压在同一时间轴上的先后 |
| `S2-F3-window-and-tau-profile.svg` | 短窗与长窗的拟合，以及 τ 目标函数剖面和边界解 |
| `S2-F4-slope-sensitivity.svg` | 同一个电压误差在不同 OCV 斜率上换算成多少 SOC |
| `S2-F5-bias-counterexample.svg` | 电压完全重合、SOC 相差 10 pp 的严格反例 |

图按 `docs/circuits/assets/*.svg` 的硬门规格编写（800 宽、`role="img"`、非空 `<title>/<desc>`、`<style>` 类、字号 ≥12、无内联填色），但目录不在该门禁的扫描范围内；P2 上站时无需返工。

## 合同

符号、时钟与数据口径以 [engineering-conventions.md](../engineering-conventions.md) 为准：新深研侧放电为正（`I > 0` 放电），旧 `code/soc` 保留充电为正（`I_legacy = -I`，`u_rc = -v_p`），SOC 为 0–1 比例。

## 未验证项

- 无电芯数据表、测量链或硬件结果；所有参数为教学合成值。
- 无真人读者试读、无独立作答记录、无具资质工程审读签字。
- 窄屏、A4、离线包与全文检索验收留待 P2 装配。
