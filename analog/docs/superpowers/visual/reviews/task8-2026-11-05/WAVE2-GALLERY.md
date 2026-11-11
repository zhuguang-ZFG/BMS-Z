# Wave 2 图库（45 张，待审）

评分入口：[`contact-wave2.html`](contact-wave2.html)（本地打开）。
本页图片路径相对仓库根，GitHub 可直接预览。

## ch13（3 张）

### H 桥四拍
`ch13-h-bridge-states` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch13-h-bridge-states.webp" width="640" alt="左右两栏：左栏四拍是正转 Q1 与 Q4 导通、反转 Q2 与 Q3 导通、全关滑行时电感电流经体二极管回电源、同臂 Q1 与 Q2 齐开会毫秒级烧管；右栏是 1 到 2 微秒死区、体二极管兜底、高侧自举、DRV8833 或 L298 集成驱动。">

### 低侧与高侧电流检测
`ch13-current-sense-sides` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch13-current-sense-sides.webp" width="640" alt="左右两栏：低侧检测共模接近 0 V、会把负载地抬高 100 mV、测不到对地短路，适合精度优先的单路负载；高侧检测共模为 12 或 24 或 48 V、地完整、能测对地短路，适合保护优先的多路共地负载。">

### 隔离三条路线与 CTR
`ch13-opto-ctr` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch13-opto-ctr.webp" width="640" alt="左右两栏：左栏三条隔离路线是光耦、数字隔离器、隔离放大器，共同点是没有欧姆通路；右栏 CTR 三个坑是分档 50% 到 600% 要按最小值、100 摄氏度与 20 毫安下十年可能掉一半、驱动至少留 2 倍余量，设计式为集电极电流等于正向电流乘 CTR。">

## ch14（6 张）

### LDO 的热阻预算
`ch14-thermal-budget` · V3 · `IG-015`

<img src="../../../../../assets/figures-v2/ch14-thermal-budget.webp" width="640" alt="热量账：12 V 转 5 V、1 A 的 LDO 耗散 7 W；允许总结温 125−40 除以 7 得 12.1 °C/W；扣掉 TO-220 的 θJC 2 与硅脂云母的 θCS 1，散热器配额只剩 9.1 °C/W。">

### LTspice 五种分析
`ch14-ltspice-five` · V5 · `IG-008`

<img src="../../../../../assets/figures-v2/ch14-ltspice-five.webp" width="640" alt="五步卡：.op 先看直流工作点，.dc 扫传输特性，.tran 看时域波形，.ac 量频域裕度，.step 扫参数与温度极限；顺序是先工作点后动态、先理想后真实。">

### WC、RSS 与 3σ
`ch14-tolerance-three` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch14-tolerance-three.webp" width="640" alt="左右两栏：WC 把三个 ±1% 同向相加得 3%，适合车规医疗；RSS 把 ±1% 按均匀分布折成 σ=0.577%，三项合成 1σ=1.0%、3σ=3.0%，适合消费类良率。">

### 测试点与量产测试
`ch14-dft-testpoints` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch14-dft-testpoints.webp" width="640" alt="左右两栏：左栏列应留测试点的位置与机械要求（TP 直径至少 1 mm、间距至少 2.54 mm、沉金）；右栏区分 ICT 抓连接、FCT 抓功能，高速节点改用测试过孔，量产用 50 到 100 块小批看分布。">

### 常用降额线
`ch14-derating-margin` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch14-derating-margin.webp" width="640" alt="手绘横向条形图：以额定值百分比为横轴，电阻功率 50 到 60%、陶瓷电容 50 到 80%、电解电容不超过 80%、二极管 70 到 80%、MOSFET 60 到 80%、连接器 50 到 70%；绿色条表示建议工作区，红色竖线标出上限。">

### 结温与失效率
`ch14-arrhenius-ten-degree` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch14-arrhenius-ten-degree.webp" width="640" alt="手绘结温账：工作结温再升 10 摄氏度，失效率约翻倍；右侧是从允许结温倒推热阻、功耗与散热面积的链条，底部写温度是寿命的乘数。">

## ch15（14 张）

### 电源走线的压降账
`ch15-trace-drop` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch15-trace-drop.webp" width="640" alt="手绘走线示意：8 cm 长、0.5 mm 宽、1 oz 铜的路径按 1 mΩ/cm 记共 8 mΩ；静态 300 mA 压降 2.4 mV，瞬态 1 A 压降 8 mV，提示按瞬态电流定线宽。">

### 布局十问
`ch15-layout-ten-questions` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch15-layout-ten-questions.webp" width="640" alt="左右两栏列布局十问：摆放四问是 100 nF 贴脸且过孔就近、储能靠近负载、晶振环路最小且下方无走线、四区分团；收尾六问是发热件远离温敏件、结构图叠图核对、芯片朝向顺走线、测试点丝印与板边 5 mm 禁布。">

### 晶振布局三不
`ch15-crystal-three-no` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch15-crystal-three-no.webp" width="640" alt="左右两栏：左栏三不是不穿晶振下方、不贴板边、外壳不悬空、XI/XO 不走板边；右栏要求负载电容贴晶振且总距离小于 10 mm、不与高速线平行超过 5 mm、不用探头直量、先保负阻裕度。">

### 四区分团的三条约定
`ch15-four-zones` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch15-four-zones.webp" width="640" alt="左右两栏：左栏三条约定是供电分界、元件归属、走线过境管制，并说明 ADC 模拟脚与数字脚分侧骑跨；右栏审查动作是打印各层用记号笔沿穿区走线打叉、问回流路径、保持地平面完整、确认数字回流不经过模拟脚下方。">

### 热焊盘的两难
`ch15-thermal-relief` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch15-thermal-relief.webp" width="640" alt="手绘两种焊盘：花孔用四条细桥连接铺铜，限制散热，手工烙铁 350 摄氏度才焊得动；直连焊盘整片铜相连，适合大电流与电源入口。底部要求同一封装库把两类焊盘分开命名。">

### 过孔并联与电感
`ch15-via-parallel` · V3 · `IG-007`

<img src="../../../../../assets/figures-v2/ch15-via-parallel.webp" width="640" alt="纸层量级图：单个 0.3 毫米过孔约 1.3 纳亨，四个并联约 0.25 纳亨，3 安培换层至少 3 只；信号过孔每孔都带寄生，应少打并成对打。">

### 串扰三招与包地边界
`ch15-crosstalk-3w` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch15-crosstalk-3w.webp" width="640" alt="左右两栏：左栏三招是拉开间距使容性耦合减半、3W 规则把串扰压到 5% 以下、缩短平行长度并用 5 到 10 毫米间距的地孔栅栏包地；右栏边界是地线必须低阻、线宽至少为被保护线两倍、包地只防电场耦合，磁场耦合要靠缩环路或拉距离。">

### 测试点三条规矩
`ch15-testpoint-rules` · V5 · `IG-001`

<img src="../../../../../assets/figures-v2/ch15-testpoint-rules.webp" width="640" alt="四步流程：每个网络至少一个测试点，测试点直径至少 1.0 毫米，放在元件面并避开散热器与屏蔽罩阴影，每片区域至少两个地测试点让回流就近走。">

### V-cut 与邮票孔
`ch15-panelization` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch15-panelization.webp" width="640" alt="左右两栏：V-cut 两侧各切三分之一板厚、槽边 0.5 毫米无铜无件、分板应力大，适合矩形小板；邮票孔用窄桥小孔拼异形边、应力小但要打磨毛刺，适合贴板边 3 毫米内有陶瓷电容或要过跌落的板。">

### DFM 四个数
`ch15-dfm-limits` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch15-dfm-limits.webp" width="640" alt="左右两栏：左栏几何下限是线宽间距常规 0.15 毫米、机械钻孔 0.3 毫米起步、丝印字高至少 1.0 毫米、铜到板边 V-cut 至少 0.5 毫米；右栏设计动作是过孔配 0.6 毫米焊盘、细间距器件集中放并逐颗查阻焊开窗、底层丝印镜像查看、钻孔文件与外形层对齐。">

### 翻车案例分诊
`ch15-failure-signatures` · V5 · `IG-006`

<img src="../../../../../assets/figures-v2/ch15-failure-signatures.webp" width="640" alt="分诊图：板子不对时先看症状，再分四支——ADC 读数跳查数字回流与去耦距离，无线距离短查天线净空区铺铜，上电发烫查电源地接反并先限流，EMC 辐射超标查地平面开槽、晶振贴边与电缆。">

### ADC 骑跨分区线
`ch15-adc-straddle` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch15-adc-straddle.webp" width="640" alt="手绘 ADC 骑跨：芯片本体跨在模拟区与数字区的分区线上，AIN、REF、AVDD 在左，SPI、CLK、DVDD 在右；AGND 与 DGND 就近下过孔进完整地平面，数字回流不经过模拟脚下方。">

### 回流审查五步
`ch15-return-review` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch15-return-review.webp" width="640" alt="手绘回流审查单：高亮网络、沿走线想象正下方回流、到换层过孔查伴生地孔、遇槽或隔离带查回流是否被挤开、不许用“应该能绕”含糊过去；右侧对比紧贴回流与绕远形成天线。">

### 双层板地网
`ch15-ground-grid` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch15-ground-grid.webp" width="640" alt="手绘两种地：四层板完整平面，信号回流贴着正下方约 1 毫米介质；双层板用 20 毫米以内的地网加铺铜与过孔缝合，环路电感差一个数量级，辐射差约 20 dB。">

## ch16（7 张）

### 信号注入与二分
`ch16-bisect-injection` · V3 · `IG-001`

<img src="../../../../../assets/figures-v2/ch16-bisect-injection.webp" width="640" alt="五步流程：在链路中点注入已知好信号；看输出正常或异常，分别把故障缩小到前半或后半；每轮只改一个变量并对半再分；逼近最小电路；最后解剖复制件，原系统留对照。">

### 三个案例的分诊
`ch16-case-triage` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch16-case-triage.webp" width="640" alt="左右两栏：左栏三个案例是低温 150 kHz 自激因换低 ESR 电容、装壳后 68 摄氏度复位因晶振线与开关节点平行 6 毫米、2% 批次随机复位因 BGA 虚焊；右栏对应先问最近改过什么、开盖与关盖差在哪、拍桌子能否复现。">

### 仪器信任链
`ch16-instrument-trust` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch16-instrument-trust.webp" width="640" alt="手绘仪器检查单：探头负载先用乘十档、测完电流立刻插回电压孔、首次上电串限流灯泡或限 50 毫安、地夹最后接；右侧两个坑是自动量程在跳变信号上反复换档，以及微安档约 100 欧姆、毫安档约 2 欧姆的 burden 压降。">

### 根因与触发条件
`ch16-postmortem-split` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch16-postmortem-split.webp" width="640" alt="手绘复盘分栏：左栏根因分别是环路相位裕度不足、晶振线与开关节点平行 6 毫米、BGA 焊球虚焊；右栏触发条件分别是低温让 MLCC 容值再降、关盖温升 23 摄氏度与高 dV/dt、热循环振动与拍桌子。">

### 排故第一问
`ch16-first-question` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch16-first-question.webp" width="640" alt="手绘第一问：这块板最近动过哪里；三条分支是换料换厂、改版改参数、环境负载；案例 A 的答案是降成本把钽电容换成 MLCC，一问就命中。">

### 探头补偿三种方波
`ch16-probe-compensation` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch16-probe-compensation.webp" width="640" alt="手绘三种校准方波：过补偿顶角过冲、欠补偿顶角圆塌、正确方角平顶；提示补偿没调对时，看到的过冲或塌陷可能来自探头而不是电路。">

### 示波器带宽五倍规则
`ch16-bandwidth-five` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch16-bandwidth-five.webp" width="640" alt="手绘两种边沿：带宽不足时边沿变圆、振铃被吃掉；五倍带宽时边沿与过冲保得住。底部写先算最高频率分量乘五，再看电源纹波可先开 20 兆赫限制，读数前先报档位。">

## ch18（15 张）

### 先量电源的三处触点
`ch18-power-three-touchpoints` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch18-power-three-touchpoints.webp" width="640" alt="左右两栏：左栏依次量稳压器输出脚 5.02 V、芯片电源引脚 4.86 V、去耦电容两端，判据是三点只在毫伏级有差；右栏算 160 mV 除以 120 mA 约 1.3 Ω，并给出 1 oz 铜 0.5 mΩ/方、0.2 mm 宽 200 mm 长约 1000 方的路径账。">

### 万用表的平均滤镜
`ch18-dmm-averaging` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch18-dmm-averaging.webp" width="640" alt="左右两栏对比：左栏 DC 档把 2.5 V 上的 1 MHz 正负摆动平均成稳定 2.5 V，AC 档因带宽不足读约 0 V；右栏示波器用 AC 耦合与毫伏档摊开时间，看到峰峰值 4 V 的振荡。">

### 探头电容把拐点拉低
`ch18-probe-loading` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch18-probe-loading.webp" width="640" alt="左右两栏对比 100 kΩ 节点的探头负载：×1 档约 100 pF，拐点约 16 kHz，20 kHz 幅度掉近四成、相位落后约 50 度；×10 档约 10 到 15 pF，拐点约 160 kHz，20 kHz 接近真实。">

### 不启动的三板斧
`ch18-reset-clock-enable` · V5 · `IG-008`

<img src="../../../../../assets/figures-v2/ch18-reset-clock-enable.webp" width="640" alt="四步顺序卡：先查复位脚是否释放，再查时钟是否起振（×10 探头避免 100 pF 压停晶振），再查使能脚电平与上拉，最后才读数据手册；顺序为复位、时钟、使能。">

### 源头放大锁住信噪比
`ch18-measurement-snr` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch18-measurement-snr.webp" width="640" alt="左右两栏对比：20 µV 信号直接进示波器，被 200 µV 环境拾取淹没，信噪比 0.1；在源头先放大 100 倍变成 2 mV，同样拾取下信噪比 10，前级自身噪声需小于 2 µV。">

### 探头地线的假振铃
`ch18-ground-lead-inductance` · V4 · `IG-004`

<img src="../../../../../assets/figures-v2/ch18-ground-lead-inductance.webp" width="640" alt="左右两栏对比探头地线：15 cm 地夹约 150 nH，50 mA 在 2 ns 内变化给出约 3.8 V 假尖峰；1 cm 弹簧地针约 10 nH，同一边沿的假尖峰降到约 0.25 V。">

### 假设树与互斥分支
`ch18-assumption-tree` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-assumption-tree.webp" width="640" alt="手绘假设树：现象是输出缓慢漂移，分成电源轨在动与测量链在漂两条互斥分支；每条都写预测、实验与判据，底部写明结果为 A 则排除 B、结果为 B 则排除 A。">

### 可复用的故障档案字段
`ch18-fault-record` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-fault-record.webp" width="640" alt="手绘故障档案卡：日期与批次、用户语言的现象、复现条件、带预测的假设、一次只改一个变量的实验记录、证据链根因、修复动作、原条件加边界拉偏的反向回归；每行右侧一个待勾选圆圈。">

### 正向、反向与边界验证
`ch18-two-way-validation` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-two-way-validation.webp" width="640" alt="手绘三栏：正向验证换好件后故障消失，反向验证装回坏件后故障复现，边界拉偏覆盖供电正负 10%、全温区与至少一天老化；三条都过才允许关闭故障单。">

### 下探头前先预测
`ch18-predict-before-probe` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-predict-before-probe.webp" width="640" alt="手绘对账本：左栏预测直流 2.5 V、交流正负 2 V、时间尺度 69 ms、波形先陡后缓；右栏实测 140 ms，偏差超过 20% 就停手改模型，嫌犯收窄到电容翻倍或漏电阻。">

### 60 秒目检
`ch18-first-minute` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-first-minute.webp" width="640" alt="手绘 60 秒目检单：保险丝、插座、开关、线序、芯片方向、跳线帽六项打勾；右侧写保险丝烧断先查下游短路，触点 1 欧姆在 1 安培下吃掉 1 伏，让 5 伏后级只剩 4 伏。">

### 两线法与四线法
`ch18-four-wire` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-four-wire.webp" width="640" alt="手绘测量对照：两线法表笔底数 0.3 欧姆，量地线读到 0.8 欧姆，扣底数后真实约 0.5 欧姆；四线法用独立回路强制电流、单独测电阻两端电压，让表笔压降不进入读数。">

### 交换法三条纪律
`ch18-swap-discipline` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-swap-discipline.webp" width="640" alt="手绘交换法：好板 A 与坏板 B 之间只交换一个可疑部件；如果故障跟件走就是部件坏，跟板走就是板级设计或工艺问题；三条纪律是交换前拍照、戴防静电腕带、一次只换一个部件。">

### 元件失效签名
`ch18-component-signatures` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-component-signatures.webp" width="640" alt="手绘四张失效签名卡：电阻过流烧毁开路、电容短路或漏电、半导体过压击穿、MLCC 在直流偏压下容量缩水；底部提示参数漂移型失效要带实际偏压核对容量。">

### 温度手段与安全边界
`ch18-temp-spray` · V4 · `IG-013`

<img src="../../../../../assets/figures-v2/ch18-temp-spray.webp" width="640" alt="手绘三步温度定位：手背感知只限低压或电池供电，冷却喷剂逐片降温看故障是否回来，锁定温敏件并记录边界；下方强调市电与高压电容附近只用喷剂和红外测温，绝不伸手。">
