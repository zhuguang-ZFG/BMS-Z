# 实物图来源

这些图来自维基共享资源、开源硬件仓库和 CC BY 论文，按原授权转载，用来对照教程里的器件，不是本仓库实拍。缩放过，长边不超过 1400 像素；个别图另裁掉了原图四周的纯白边，在表里注明。原文件以出处页为准。

分压实测台的同框、TI 官方 BQ769 评估板、isoSPI 线束、装在母线旁的主动放电电阻，仍然没有可转载、对得上的照片。被测 BMS 在环的 HIL 同框、功能安全见证现场，同样没有。2026-10-05 又对过一轮近邻文件：电源电容自带泄放（[File:Bleeder.jpg](https://commons.wikimedia.org/wiki/File:Bleeder.jpg)）、实验室里用 100 kΩ 给高压电容放电（[File:HT-PCB-140-08058A-P-V06-main-hv-cap-discharge-resistor.jpg](https://commons.wikimedia.org/wiki/File:HT-PCB-140-08058A-P-V06-main-hv-cap-discharge-resistor.jpg)）、Embedded World 上的 MSP430 实验板（[File:Embedded World 2014 TI Developer Board.jpg](https://commons.wikimedia.org/wiki/File:Embedded_World_2014_TI_Developer_Board.jpg)）。它们分别是电容泄放、另一块开发板，对不上保护板实测台、TI 官方评估板、isoSPI 线束，也不是装在高压接触器旁边的主动放电电阻。isoSPI 的文件名检索落到无关照片。2026-10-05 同日再对过一轮，仍然对不上：预充接线说明 [File:WPEVCContactorCharge2B.png](https://commons.wikimedia.org/wiki/File:WPEVCContactorCharge2B.png)、密封接触器剖视 [File:Contactor cut-away animation with AUX.gif](https://commons.wikimedia.org/wiki/File:Contactor_cut-away_animation_with_AUX.gif)、牵引电池外观 [File:SOR bus EBN 11. Traction batteries. Spielvogel 2014.JPG](https://commons.wikimedia.org/wiki/File:SOR_bus_EBN_11._Traction_batteries._Spielvogel_2014.JPG)。DigiKey 论坛讨论过 BQ76952EVM，页面上没有可转载照片。专利里的主动放电电路也不是实拍。

**2026-10-05 再搜一轮（仍不入库）。** 口诀：对得上画面、又写明可以转载，才进这张表。商品图再清晰，也不改标成实拍。

| 要的镜头 | 看过的页 | 为什么不收 |
|---|---|---|
| 电源、分压链、保护板、万用表同框 | [水果电池配万用表](https://commons.wikimedia.org/wiki/File:Fruit_battery,_apples,_multimeter.jpg)（CC BY 3.0） | 三块苹果和一只表。没有电源，没有分压链，没有保护板 |
| 同上 | 共享资源检索 cell simulator、battery emulator | 落到光伏 I–V 台、飞行模拟器软盘、美国内战炮兵史。不是保护板实测台 |
| 同上 | [LibreSolar BMS C1 手册](https://libre.solar/bms-c1/manual/) 的测试接线（文档 CC BY-SA 4.0） | 那张是 SVG 接线说明，不是照片。仓库里已有的两张测试照仍是板子一张、电源另一张 |
| 同上 | [comemso 电芯模拟器](https://comemso.com/products/battery-cell-simulator/) | 厂商商品页。页面没有写明 CC0 或 CC BY。不转载 |
| TI 官方 BQ769 或 isoSPI 线束 | 共享资源检索 BQ769、BQ76952 | 零条文件 |
| 同上 | 共享资源检索 isoSPI | 文件名落到纽约市夜景一类无关照片，没有线束 |
| 同上 | [BQ76952EVM 用户指南 SLUUC33](https://www.ti.com/lit/ug/sluuc33a/sluuc33a.pdf)、[ADI DC2792B](https://www.analog.com/en/resources/evaluation-hardware-and-software/evaluation-boards-kits/dc2792b.html) | 厂商文件。只外链，不把指南里的图裁进仓库 |
| 接触器旁的主动放电电阻 | 共享资源检索 discharge resistor | 仍是 [Bleeder.jpg](https://commons.wikimedia.org/wiki/File:Bleeder.jpg) 和实验室电容泄放。预充同框已经在表里，身份不变 |
| HIL 同框（可编程电源、故障注入、被测 BMS、上位机） | [1985 年模拟计算机局部](https://commons.wikimedia.org/wiki/File:Analogrechner_HW-in-Loop_Ausschnitt.jpg) | 上一轮已拒。不是电池台 |
| 同上 | 共享资源检索 hardware-in-the-loop | 其余是学位论文 PDF，以及注册号带 HIL 的客机。没有被测 BMS |
| 同上 | Verani 2023 Figure 4、Di Rienzo 2022 Figure 3 | 已在表里。画面是仿真器表征台，没有被测 BMS |
| 功能安全见证（失效注入、硬件比较器、见证记录同框） | [ASIL 计算图](https://commons.wikimedia.org/wiki/File:ISO_26262_ASIL_berechnen.svg) | 上一轮已拒。是算 ASIL 的图，不是现场 |
| 同上 | [HIMA 演讲照片](https://commons.wikimedia.org/wiki/File:Functional_safety_in_a_connected_world_-_HIMA_(40604023743).jpg) | 画面是会议演讲者。不是注入台、比较器和记录本同框 |

**2026-10-07 一轮。** MediaSearch 「battery management system board」找到 MGM COMPRO 的均衡测量单元，收进表尾；同批结果里的 [File:Generic Chinese 6S BMS board 02.jpg](https://commons.wikimedia.org/wiki/File:Generic_Chinese_6S_BMS_board_02.jpg) 是已有 3S/4S/6S 组合照同一上传者的近邻，不重复收。「battery balancer balancing board」落到的全是两轮平衡车（self-balancing scooter），不是电池均衡板。五个坑位仍没有对得上的照片。

还缺的镜头就这五张：同框分压台、TI 官方 BQ769 或 isoSPI 线束、接触器旁主动放电电阻、被测 BMS 在环的 HIL、功能安全见证现场。三处正文里另有标明「示意图·待实拍」的动画，阶段 6 另有 HIL 和见证现场的示意图。还缺的实拍见 [共建任务板](../../../共建任务板.md) T11。

同一天收进本表的是近邻，身份写在「拍的是什么」一列：LibreSolar BMS C1 是开源 BQ76952 台架；kevinxusz 仓库里的板名叫 EvalBoard，是 DIY BQ76940；INL、ORNL 和 DOE 的照片是电池试验或制备环境；Verani 与 Di Rienzo 的图是电芯仿真器表征台，画面里没有被测 BMS；OVMS 是开源车载监控的网页仪表盘。Xu 等 EcoMat 2022 的 Figure 4 是结构电池试样的 TL431 被动均衡电路图。

| 文件 | 拍的是什么 | 作者 | 授权 | 原文件 |
|---|---|---|---|---|
| `18650-21700-cells.jpg` | 18650 与 21700 圆柱电芯 | Sevenethics | CC0 | [File:18650 and 21700 lithium ion battery cell.jpg](https://commons.wikimedia.org/wiki/File:18650_and_21700_lithium_ion_battery_cell.jpg) |
| `18650-charger-four.jpg` | 充电器里的四节 18650，其中一节掉皮 | Retired electrician | CC0 | [File:Four 18650 lithium cells in a Liitokala PL4 charger.jpg](https://commons.wikimedia.org/wiki/File:Four_18650_lithium_cells_in_a_Liitokala_PL4_charger.jpg) |
| `cell-formats.jpg` | 圆柱、方形、软包外形 | CRBAman | CC BY-SA 4.0 | [File:Lithium Ion Battery Cell - Cylindrical Cell, Prismatic Cell, Pouch Cell.png](https://commons.wikimedia.org/wiki/File:Lithium_Ion_Battery_Cell_-_Cylindrical_Cell,_Prismatic_Cell,_Pouch_Cell.png) |
| `laptop-pack-internals.jpg` | 笔记本电池包：电芯、保护电路、温度传感器 | Lead holder | CC BY-SA 3.0 | [File:Lithiumion-laptop-battery-internals.jpg](https://commons.wikimedia.org/wiki/File:Lithiumion-laptop-battery-internals.jpg) |
| `bms-boards-3s4s6s.jpg` | 3S / 4S / 6S 成品保护板 | Retired electrician | CC0 | [File:Generic Chinese 3S, 4S, 6S BMS boards for lithium batteries 01.jpg](https://commons.wikimedia.org/wiki/File:Generic_Chinese_3S,_4S,_6S_BMS_boards_for_lithium_batteries_01.jpg) |
| `bms-board-4s.jpg` | 4S 保护板近看 | Retired electrician | CC0 | [File:Generic Chinese 4S BMS boards for lithium batteries 02.jpg](https://commons.wikimedia.org/wiki/File:Generic_Chinese_4S_BMS_boards_for_lithium_batteries_02.jpg) |
| `balance-xh-plug.jpg` | XH 平衡插头 | Laurenz Wagner | CC BY 3.0 | [File:Balancer Stecker XH.JPG](https://commons.wikimedia.org/wiki/File:Balancer_Stecker_XH.JPG) |
| `digital-multimeter.jpg` | 数字万用表 | André Karwath aka Aka | CC BY-SA 2.5 | [File:Digital Multimeter Aka.jpg](https://commons.wikimedia.org/wiki/File:Digital_Multimeter_Aka.jpg) |
| `esp32-board.jpg` | ESP32 模组开发板 | Ubahnverleih | CC0 | [File:ESP32 on Lolin32 Lite clone board cropped.jpg](https://commons.wikimedia.org/wiki/File:ESP32_on_Lolin32_Lite_clone_board_cropped.jpg) |
| `ntc-thermistor.jpg` | 带引线的 NTC | Soumyapatra13 | CC BY-SA 4.0 | [File:NTC Thermistor.jpg](https://commons.wikimedia.org/wiki/File:NTC_Thermistor.jpg) |
| `smd-shunt.jpg` | 贴片检流电阻 | wdwd | CC BY-SA 4.0 | [File:SMD Shunt Resistors.jpg](https://commons.wikimedia.org/wiki/File:SMD_Shunt_Resistors.jpg) |
| `bench-power-supply.jpg` | 可调直流稳压电源 | Derrick Parker | CC0 | [File:Bench power supply.jpg](https://commons.wikimedia.org/wiki/File:Bench_power_supply.jpg) |
| `kilovac-ev200-contactor.jpg` | 电动车里常见的密封直流接触器。上传者注明型号为 Kilovac EV200 | Leonard G. | CC BY-SA 1.0 | [File:Contactor200AmpSealed.jpg](https://commons.wikimedia.org/wiki/File:Contactor200AmpSealed.jpg) |
| `wirewound-50w-resistor.jpg` | 50 W 线绕功率电阻。用来认识预充 / 放电电阻的一类外形，不是装在母线上的那只 | YoktoBit | CC BY-SA 4.0 | [File:Hochlast Drahtwiderstand 50W 5%.png](https://commons.wikimedia.org/wiki/File:Hochlast_Drahtwiderstand_50W_5%25.png) |
| `bq20z45-pack-controller.jpg` | 笔记本电池上的 TI BQ20Z45（气量计，带保护）。不是 BQ769x 评估板 | Raimond Spekking | CC BY-SA 4.0 | [File:Asus Zenbook UX31E - Lithium-Polymer battery controller - Texas Instruments BQ20Z45-48173.jpg](https://commons.wikimedia.org/wiki/File:Asus_Zenbook_UX31E_-_Lithium-Polymer_battery_controller_-_Texas_Instruments_BQ20Z45-48173.jpg) |
| `sh367103-protection-ic.jpg` | 中颖 SH367103X 锂电保护 IC 特写。不是 DW01 | Raimond Spekking | CC BY-SA 4.0 | [File:Sino Wealth SH367103X-AAE00-0008.jpg](https://commons.wikimedia.org/wiki/File:Sino_Wealth_SH367103X-AAE00-0008.jpg) |
| `tp4056-dw01-8205a.jpg` | 单节充电保护板。上传者说明：右侧是 DW01A 与 8205A，左侧大芯片是 TP4056。自动识别没有稳定抽出完整料号，对印字以原图为准 | -stk | CC BY-SA 4.0 | [File:TP4056 board P1089956.jpg](https://commons.wikimedia.org/wiki/File:TP4056_board_P1089956.jpg) |
| `contactor-precharge-resistor.jpg` | 主接触器与预充电阻、二极管在同一画面。上传者标注 PRECHARGE RESISTOR。不是主动放电电阻 | Criveros0248 | CC BY-SA 3.0 | [File:Main contactor.jpg](https://commons.wikimedia.org/wiki/File:Main_contactor.jpg) |
| `faradion-sodium-ion-museum.jpg` | 伦敦科学博物馆的 Faradion 钠离子电池，藏品号 2023-357。展签写 Sodium-ion battery。展品外形，不是电压窗口，也不是包级手册 | The wub | CC BY-SA 4.0 | [File:Faradion sodium-ion battery - Science Museum, London.jpg](https://commons.wikimedia.org/wiki/File:Faradion_sodium-ion_battery_-_Science_Museum,_London.jpg) |
| `electrode-coater.jpg` | 锂离子电极的卷对卷涂布设备。上传者说明是 Coating Equipment for Electrodes for Lithium-Ion Batteries。不是化成柜，不是 K 值分选，也不是结构电池产线 | RudolfSimon | CC BY 3.0 | [File:Electrode Coater.JPG](https://commons.wikimedia.org/wiki/File:Electrode_Coater.JPG) |
| `libresolar-bms-c1.jpg` | LibreSolar BMS C1 电路板。开源 BQ76952 台架，硬件许可 CERN-OHL-W v2。不是 TI 官方 EVM | LibreSolar | 文档与图 CC BY-SA 4.0 | [bms-c1 `build/bms-c1.jpg`](https://github.com/LibreSolar/bms-c1) |
| `libresolar-test-bms.jpg` | 同一项目的测试布置：板子、电芯和负载。开源 BQ76952 台架。不是分压链、保护板、万用表的同框，也不是 TI 官方 EVM | LibreSolar | 文档与图 CC BY-SA 4.0 | [testing/v0.3/test-setup-bms.jpg](https://github.com/LibreSolar/bms-c1) |
| `libresolar-test-psu.jpg` | 同一项目另拍的直流电源。和上一张不是同一框 | LibreSolar | 文档与图 CC BY-SA 4.0 | [testing/v0.3/test-setup-power-supply.jpg](https://github.com/LibreSolar/bms-c1) |
| `bq76940-diy-evalboard.jpg` | DIY BQ76940 板。仓库文件名叫 EvalBoard。公有领域。不是 TI 官方 EVM | kevinxusz | Public domain | [BMS-bq76940 `Bilder/EvalBoard.png`](https://github.com/kevinxusz/BMS-bq76940) |
| `bq76940-diy-bench.jpg` | 同一仓库的台架照片，2015-06-23。DIY BQ76940，不是 TI 官方 EVM | kevinxusz | Public domain | [Bilder/20150623_114454.jpg](https://github.com/kevinxusz/BMS-bq76940) |
| `ovms-dashboard.jpg` | OVMS 网页仪表盘：这辆车的 SOC、续航、电池电压、电流、温度和 SOH。开源车载监控，许可 MIT。不是商业车队云的后台 | Open Vehicles / OVMS | MIT | [OVMS Dashboard](https://docs.openvehicles.com/en/stable/components/ovms_webserver/docs/dashboard.html) |
| `inl-battery-testing-lab.jpg` | 爱达荷国家实验室的电动车与储能电池测试能力，说明文字写的是过热敏感性。电池试验室。不是功能安全见证现场 | Idaho National Laboratory | CC BY 2.0 | [File:INL battery testing lab (9192409117).jpg](https://commons.wikimedia.org/wiki/File:INL_battery_testing_lab_(9192409117).jpg) |
| `ornl-battery-lab.jpg` | 橡树岭国家实验室的锂离子电芯制备实验环境。电池实验室。不是功能安全见证现场 | Oak Ridge National Laboratory | CC BY 2.0 | [File:Prototype battery testing (5113771331).jpg](https://commons.wikimedia.org/wiki/File:Prototype_battery_testing_(5113771331).jpg) |
| `doe-inl-battery-testing.jpg` | 能源部发布的同一类 INL 电动车与储能电池测试照片。公有领域。电池试验室。不是功能安全见证现场 | U.S. Department of Energy | Public domain | [File:U.S. Department of Energy - Science - 404 075 001 (29595785901).jpg](https://commons.wikimedia.org/wiki/File:U.S._Department_of_Energy_-_Science_-_404_075_001_(29595785901).jpg) |
| `verani-2023-emulator-bench.jpg` | 模块化电池仿真器的表征台：TTi QPX1200SP、仿真器机架、Keithley 2460、笔记本。论文 Figure 4。画面里没有被测 BMS | Verani、Di Rienzo、Baronti、Roncella、Saletti | CC BY 4.0 | [Electronics 2023, 12, 1232](https://doi.org/10.3390/electronics12051232) |
| `dirienzo-2022-emulator-bench.jpg` | 电芯仿真器表征台。论文 Figure 3，图注是 experimental setup used for the cell emulator characterization。画面是仿真器本身 | Di Rienzo、Verani、Baronti、Roncella、Saletti | CC BY 4.0 | [Electronics 2022, 11, 1215](https://doi.org/10.3390/electronics11081215) |
| `ecomat-2022-tl431-balance.jpg` | 三串结构电池试样的电路图。Figure 4B：TL431 被动均衡，R1 = 20 kΩ，R2 = 47 kΩ，单节上限 3.55 V。实验室电路图，不是量产包手册，也不是接触器旁的主动放电电阻 | Xu、Geng、Johansen 等 | CC BY 4.0 | [EcoMat 2022, e12180](https://doi.org/10.1002/eom2.12180) |
| `mgm-bmu-balance-unit.jpg` | 航电厂商 MGM COMPRO 的均衡测量单元：分布式 BMS 的从模块，可见采样线插座、MCU 和三只 TO-220 封装功率管。上传页没写每只元件的功能，正文不指认。裁掉了原图四周的纯白边 | Drazny | CC BY-SA 4.0 | [File:Bms-system-balancujici-a-merici-jednotka.jpg](https://commons.wikimedia.org/wiki/File:Bms-system-balancujici-a-merici-jednotka.jpg) |

CC BY / CC BY-SA 的图保留作者和授权。CC0 和公有领域不要求署名，这里仍记下作者，方便核对原图。MIT 的 OVMS 仪表盘保留项目名。LibreSolar 硬件是 CERN-OHL-W v2，本表这三张图按该仓库文档的 CC BY-SA 4.0 转载。
