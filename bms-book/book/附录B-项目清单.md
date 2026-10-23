# 附录 B 项目与资料清单

> 星数为 2026-10-23 GitHub API 实测，仅反映传播度，不代表质量、稳定 release 或适配性。

## B.1 BMS 项目

| 项目 | Stars | 许可（以仓库为准） | 定位 |
|---|---:|---|---|
| `foxBMS/foxbms-2` | 491 | 软件 BSD-3；硬件/文档 CC BY 4.0 | 工业级模块化 BMS 开发平台 |
| `Green-bms/SmartBMS` | 756 | CC BY-SA 4.0 | 低成本四件套 BMS |
| `stuartpittaway/diyBMS` | 676 | 见仓库 | 电源墙 DIY BMS（已被 v4 取代） |
| `syssi/esphome-jk-bms` | 1,040 | 见仓库 | JK-BMS 接入 ESPHome |
| `pybamm-team/PyBaMM` | 1,702 | 见仓库 | 锂电物理模型与实验仿真 |
| `LibreSolar/bms-firmware` | 270 | Apache-2.0 | Zephyr BMS 固件；区分持续开发的 `main` 与多板测试后的 release |

第 22 章的源码级对照固定在 foxBMS 2 `v1.12.0`／`73dbde670f7e…` 与 LibreSolar `779d20199bff…`。Stars 用来发现项目；tag、commit、工具链和测试证据才进入复用记录。

## B.2 教程与课程

| 资料 | 类型 | 链接 |
|---|---|---|
| BMS-Z | 中文阶段教程 + 代码 + 动画 | https://github.com/zhuguang-ZFG/BMS-Z |
| BMS-Z 在线站 | VitePress | https://zhuguang-zfg.github.io/BMS-Z/ |
| ECE5710/5720 | Plett 课程讲义（英文，免费） | http://mocha-java.uccs.edu/ECE5720/index.html |
| IntechOpen BMS 章节 | 开放获取 | https://www.intechopen.com/chapters/49272 |
| Battery University | 免费科普 | https://batteryuniversity.com/ |
| TI BMS 白皮书 | 厂商文档 | https://www.ti.com/ |

## B.3 商业教材

- G. L. Plett, *Battery Management Systems*, Vol. I–III, Artech House.
- D. Andrea, *Battery Management Systems for Large Lithium-Ion Battery Packs*, Artech House.
- H. J. Bergveld et al., *Battery Management Systems: Design by Modelling*, Springer.
- R. Xiong（熊瑞）, *Advanced Battery Management Technologies for Electric Vehicles*, Wiley.
- 熊瑞，《动力电池管理系统核心算法》，机械工业出版社。

## B.4 标准（按最新版本查阅）

- UN 38.3：锂电池运输测试
- IEC 62619：工业用锂二次电池安全
- UL 1973：固定式储能电池系统
- ISO 26262：道路车辆功能安全
- IEC 61508：通用功能安全
- ISO/SAE 21434：道路车辆网络安全
- IEC 62443：工业自动化信息安全

## B.5 选型建议

- 想系统读架构：foxBMS 2 + 本书第 2、5、22 章。
- 想动手做板：SmartBMS + BMS-Z 阶段 2/3。
- 想做算法：BMS-Z `code/soc/` + 本书第 10–17 章。
- 想做通信：BMS-Z `code/protocol/` + 本书第 18、19 章。
- 想用 AI：本书第 24 章 + BMS-Z 阶段 7。
