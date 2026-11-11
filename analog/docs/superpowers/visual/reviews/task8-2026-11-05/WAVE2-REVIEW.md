# Wave 2 视觉复核包（45 张，待人工审图）

本包新增 45 张静态图：24 张纸层（V3/V4/V5）与 21 张手绘纸墨（V4）。
全部 `status: generated`，未插入正文，未回填评分；没有伪造人工签核。

## 怎么看

1. 打开 [`contact-wave2.html`](contact-wave2.html)，逐张看大图。
   也可在 GitHub 直接看 [`WAVE2-GALLERY.md`](WAVE2-GALLERY.md)。
2. 按五项各打 1–5 分：教学必要性、事实精度、构图层级、风格一致性、印刷可读性。
3. 任一维度 <4 记具体返工点；5 分才可写 `accepted`。
4. 回复“第 X 张：5/5/5/5/5”或“全部 5 分通过”即可回填；模型不会代签。

## 优先看这六张

| 图 | 为什么先看 |
|---|---|
| `ch15-adc-straddle` | 分区线 ≠ 地平面分割线，最容易被误读 |
| `ch15-return-review` | 五步回流审查，直接能贴进检查单 |
| `ch18-predict-before-probe` | “先预测再测量”的方法核心 |
| `ch18-first-minute` | 60 秒目检，最像真实排故现场 |
| `ch16-first-question` | 把“最近改过什么”做成第一动作 |
| `ch13-h-bridge-states` | 四拍与死区，功率章的门面 |

其余按章看：ch15 布线与 DFM → ch18 测量与排故 → ch16 流程 → ch13 功率 → ch14 热与降额。

## 清单

### ch13（3 张）

| id | 标题 | 类型 | 布局 |
|---|---|---|---|
| `ch13-h-bridge-states` | H 桥四拍 | V4 | IG-004 |
| `ch13-current-sense-sides` | 低侧与高侧电流检测 | V4 | IG-004 |
| `ch13-opto-ctr` | 隔离三条路线与 CTR | V4 | IG-004 |

### ch14（6 张）

| id | 标题 | 类型 | 布局 |
|---|---|---|---|
| `ch14-thermal-budget` | LDO 的热阻预算 | V3 | IG-015 |
| `ch14-ltspice-five` | LTspice 五种分析 | V5 | IG-008 |
| `ch14-tolerance-three` | WC、RSS 与 3σ | V4 | IG-004 |
| `ch14-dft-testpoints` | 测试点与量产测试 | V4 | IG-004 |
| `ch14-derating-margin` | 常用降额线 | V4 | IG-013 |
| `ch14-arrhenius-ten-degree` | 结温与失效率 | V4 | IG-013 |

### ch15（14 张）

| id | 标题 | 类型 | 布局 |
|---|---|---|---|
| `ch15-trace-drop` | 电源走线的压降账 | V4 | IG-013 |
| `ch15-layout-ten-questions` | 布局十问 | V4 | IG-004 |
| `ch15-crystal-three-no` | 晶振布局三不 | V4 | IG-004 |
| `ch15-four-zones` | 四区分团的三条约定 | V4 | IG-004 |
| `ch15-thermal-relief` | 热焊盘的两难 | V4 | IG-013 |
| `ch15-via-parallel` | 过孔并联与电感 | V3 | IG-007 |
| `ch15-crosstalk-3w` | 串扰三招与包地边界 | V4 | IG-004 |
| `ch15-testpoint-rules` | 测试点三条规矩 | V5 | IG-001 |
| `ch15-panelization` | V-cut 与邮票孔 | V4 | IG-004 |
| `ch15-dfm-limits` | DFM 四个数 | V4 | IG-004 |
| `ch15-failure-signatures` | 翻车案例分诊 | V5 | IG-006 |
| `ch15-adc-straddle` | ADC 骑跨分区线 | V4 | IG-013 |
| `ch15-return-review` | 回流审查五步 | V4 | IG-013 |
| `ch15-ground-grid` | 双层板地网 | V4 | IG-013 |

### ch16（7 张）

| id | 标题 | 类型 | 布局 |
|---|---|---|---|
| `ch16-bisect-injection` | 信号注入与二分 | V3 | IG-001 |
| `ch16-case-triage` | 三个案例的分诊 | V4 | IG-004 |
| `ch16-instrument-trust` | 仪器信任链 | V4 | IG-013 |
| `ch16-postmortem-split` | 根因与触发条件 | V4 | IG-013 |
| `ch16-first-question` | 排故第一问 | V4 | IG-013 |
| `ch16-probe-compensation` | 探头补偿三种方波 | V4 | IG-013 |
| `ch16-bandwidth-five` | 示波器带宽五倍规则 | V4 | IG-013 |

### ch18（15 张）

| id | 标题 | 类型 | 布局 |
|---|---|---|---|
| `ch18-power-three-touchpoints` | 先量电源的三处触点 | V4 | IG-004 |
| `ch18-dmm-averaging` | 万用表的平均滤镜 | V4 | IG-004 |
| `ch18-probe-loading` | 探头电容把拐点拉低 | V4 | IG-004 |
| `ch18-reset-clock-enable` | 不启动的三板斧 | V5 | IG-008 |
| `ch18-measurement-snr` | 源头放大锁住信噪比 | V4 | IG-004 |
| `ch18-ground-lead-inductance` | 探头地线的假振铃 | V4 | IG-004 |
| `ch18-assumption-tree` | 假设树与互斥分支 | V4 | IG-013 |
| `ch18-fault-record` | 可复用的故障档案字段 | V4 | IG-013 |
| `ch18-two-way-validation` | 正向、反向与边界验证 | V4 | IG-013 |
| `ch18-predict-before-probe` | 下探头前先预测 | V4 | IG-013 |
| `ch18-first-minute` | 60 秒目检 | V4 | IG-013 |
| `ch18-four-wire` | 两线法与四线法 | V4 | IG-013 |
| `ch18-swap-discipline` | 交换法三条纪律 | V4 | IG-013 |
| `ch18-component-signatures` | 元件失效签名 | V4 | IG-013 |
| `ch18-temp-spray` | 温度手段与安全边界 | V4 | IG-013 |

## 已过的自动闸

- `python scripts/check_visual_manifest.py` → PASS（0 项）
- 每张 `bounds: pass`，最小印刷字号 8.6 pt（≥8.5 pt）
- manifest/纸层/动画测试（本轮结束前重跑）
- 数字均由脚本对 anchor 原文核查；图内不编码正文没有的量值

## 合入条件

- 人工评分回填且全部 ≥4；
- 插入对应章节 anchor，正文有引用与读图指引；
- 重建 BOOK.md 与站点后，`test_book_real`、`check_visual_manifest`、`test_papercut_figures` 全过；
- PR 合并后 main CI 全绿。
