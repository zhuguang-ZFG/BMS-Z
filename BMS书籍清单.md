# BMS（电池管理系统）相关书籍清单

> 整理日期：2026-10-04。书目信息（作者/出版社/年份/ISBN）均经公开来源核实，来源链接附于各条。

## 一、BMS 核心专著（必读）

1. **Battery Management Systems, Volume I: Battery Modeling**
   - Gregory L. Plett，Artech House，2015，ISBN 978-1-63081-024-5，336 页
   - 电芯建模（等效电路 + 物理模型基础），是整套 BMS 算法（SOC/SOH 估计）的地基。
   - 来源：[Artech House](https://us.artechhouse.com/Battery-Management-Systems-Volume-1-Battery-Modeling-P1752.aspx) / [Google Books](https://books.google.com/books/about/Battery_Management_Systems_Volume_I_Batt.html?id=suLRCgAAQBAJ)

2. **Battery Management Systems, Volume II: Equivalent-Circuit Methods**
   - Gregory L. Plett，Artech House，2015
   - 基于等效电路模型的 SOC/SOH 估计：Kalman 滤波族（EKF/SPKF/Sigma-point）、联合/对偶估计、均衡、功率/寿命预测。**与本仓库 SOC 校准/EKF 工作最直接对口的一本。**
   - 来源：[Artech House](https://us.artechhouse.com/Battery-Management-Systems-Volume-II-Equivalent-Circuit-Methods-P2192.aspx)

3. **Battery Management Systems, Volume III: Physics-Based Methods**
   - Gregory L. Plett, M. Scott Trimboli，Artech House，2024，ISBN 978-1-63081-904-0
   - 基于电化学物理模型（P2D/SPMe 降阶）的估计与最优控制，系列收官卷。
   - 来源：[Artech House](https://us.artechhouse.com/Battery-Management-Systems-Volume-III-Physics-Based-Methods-P2308.aspx) / [IEEE](https://ieeexplore.ieee.org/document/10418249)

4. **Battery Management Systems for Large Lithium-Ion Battery Packs**
   - Davide Andrea，Artech House，2010，290 页（ISBN 存在 978-1-60807-104-3 / 978-1-60807-105-0 两个变体，版本对应关系未核实，故不标注）
   - 工程实践视角：BMS 拓扑（集中/分布）、采样前端、均衡、保护、通讯。被引 800+ 的经典工程参考书。
   - 来源：[Artech House](https://us.artechhouse.com/Battery-Management-Systems-for-Large-Lithium-Ion-Battery-Packs-P1891.aspx) / [Google Books](https://books.google.com/books/about/Battery_Management_Systems_for_Large_Lit.html?id=o-QpFOR0PTcC)

5. **Lithium-Ion Batteries and Applications, Volume 1: Batteries**
   - Davide Andrea，Artech House，2020，ISBN 978-1-63081-767-1
   - 从消费级到电网级的锂电池与电池组实用指南（"from Toys to Towns"），BMS 背景的电池本体知识。
   - 来源：[作者站点 book.liionbms.com](https://book.liionbms.com/)

6. **A Systems Approach to Lithium-Ion Battery Management**
   - Phillip Weicker，Artech House，2013
   - 系统工程视角：需求、架构、BMS 功能分解，适合搭建整体设计框架。
   - 来源：[Artech House](https://us.artechhouse.com/A-Systems-Approach-to-Lithium-Ion-Battery-Management-P1628.aspx) / [Vanderbilt 馆藏](https://catalog.library.vanderbilt.edu/discovery/fulldisplay/alma991043278917803276/01VAN_INST:vanui)

## 二、SOC/SOH 估计与算法

7. **Battery Management Systems: Accurate State-of-Charge Indication for Battery-Powered Applications**
   - Valer Pop, Henk Jan Bergveld, Dmitry Danilov, Paul P.L. Regtien, Peter H.L. Notten，Springer，2008
   - 专注 SOC 指示精度：库仑计量 + EMF/OCV 方法 + 自适应，Philips 研究体系。
   - 来源：[Springer](https://link.springer.com/book/10.1007/978-1-4020-6945-1) / [University of Twente](https://research.utwente.nl/en/publications/battery-management-systems-accurate-state-of-charge-indication-fo)

8. **Battery Management Systems: Design by Modelling**
   - Henk Jan Bergveld, Wanda S. Kruijt, Peter H.L. Notten，Kluwer Academic，2002
   - 上述体系的源头专著：以建模驱动 BMS 设计（EMF、过电位、可用容量建模）。
   - 来源：[Internet Archive](https://archive.org/details/batterymanagemen0000berg)

9. **Advanced Battery Management Technologies for Electric Vehicles**
   - Rui Xiong（熊瑞）, Weixiang Shen，Wiley，2019
   - 电池建模、SOC/SOH/SOP/SOE 联合估计、云-端协同管理等，偏研究前沿。
   - 来源：[北理工作者页](https://pure.bit.edu.cn/zh/persons/rui-xiong)

10. **Battery Management Algorithm for Electric Vehicles**
    - Rui Xiong，Springer，2020
    - 算法向专著：分数阶/数据驱动状态估计、剩余寿命与故障诊断。
    - 来源：[Springer](https://link.springer.com/book/10.1007/978-981-15-0248-4)

## 三、建模与系统工程

11. **Battery Systems Engineering**
    - Christopher D. Rahn, Chao-Yang Wang（王朝阳），Wiley，2013，ISBN 978-1-119-97950-0
    - 电化学—降阶模型—估计与控制—热管理的完整链条，学术与工程兼顾。
    - 来源：[Wiley](https://onlinelibrary.wiley.com/doi/book/10.1002/9781118517048) / [MRS Bulletin 书评](https://www.cambridge.org/core/journals/mrs-bulletin/article/battery-systems-engineering-christopher-d-rahn-and-chaoyang-wang/E673F69CEF437374103CA4D8F6870BE0)

12. **Design and Analysis of Large Lithium-Ion Battery Systems**
    - Shriram Santhanagopalan, Matthew Keyser, Gi-Heon Kim, Jeremy Neubauer, Ahmad Pesaran, Kandler Smith（NREL），Artech House
    - 大容量电池系统的设计与分析方法，储能/车用均适用。
    - 来源：[Artech House 书目页](https://us.artechhouse.com/Assets/Email/09_20/profcat/power.html)

## 四、中文书籍

13. **动力电池管理系统核心算法（第 2 版）**
    - 熊瑞，机械工业出版社（第 1 版 2018）
    - 中文里最系统的 BMS 算法书：建模、SOC/SOH 估计、均衡与安全管理。
    - 来源：[北理工作者页](https://pure.bit.edu.cn/zh/persons/rui-xiong) / [得到电子书](https://www.dedao.cn/ebook/detail?id=XOnaYG1qlM7amvGYerDZOy9JVnXL40BjyJ0Bkp1NKxoRdb86P2Q5AzgEj9vE5rDo)

14. **电动汽车动力电池管理系统设计**
    - 谭晓军，中山大学出版社，ISBN 978-7-306-04061-9
    - 特性测试、建模仿真、SOC 估算、均衡控制的设计要点。
    - 来源：[当当](https://product.dangdang.com/22538218.html) / [深圳图书馆馆藏](https://www.szlib.org.cn/opac/searchDetail?library=all&recordid=2096259&tablename=bibliosm)

15. **电动汽车动力电池系统安全分析与设计**
    - 王芳、夏军 等，科学出版社
    - 电池系统（Pack）安全分析与安全设计，中汽中心经验。
    - 来源：[大连理工大学图书馆](https://opac.lib.dlut.edu.cn/mspace/searchDetailLocal/meab7c654c020a997c2a4ee30b1a0ce7c)

16. **电动汽车动力电池系统设计与制造技术**
    - 王芳、夏军 等，科学出版社
    - Pack 级设计与制造的系统化梳理，立足国内产业实践。
    - 来源：[宁波职业技术学院图书馆](https://opac.app.nbpu.edu.cn/mspace/searchDetailLocal/m1877b8d794e5a459374dd4fa6a2659f9)

17. **电池管理系统（BMS）设计与制造技术**
    - 许铀、魏亮亮、刘鲁新 等，机械工业出版社，ISBN 978-7-111-73859-6
    - 面向工程落地的 BMS 设计与制造全流程。
    - 来源：[机工社工程科技数字图书馆](https://ebooks.cmpbook.com/detail?id=25480)

18. **锂光：动力电池硬核入门**
    - 刘冠伟，清华大学出版社，2024.5（2025.6 重印），ISBN 978-7-302-66072-9，208 千字
    - 行业入门科普：材料→电芯结构→系统集成→性能应用→技术挑战→新型电池→职场建议（8 章）。零算法深度，建立行业全貌用。
    - 来源：书目信息经本书 CIP 页（2024 第 072578 号）核实

19. **动力电池系统设计**
    - 徐晓明、胡东海 编著，机械工业出版社，2018.12（"十三五"汽车类规划教材），ISBN 978-7-111-61485-2，366 千字
    - Pack 级工程设计：方案/机械结构/高压电连接/热管理/仿真/安全测试/制造，BMS 占一章。补 Pack 结构与高压设计空位。
    - 来源：书目信息经本书 CIP 页（2018 第 265991 号）核实

## 五、电池基础参考（非 BMS 专著，作背景用）

20. **Linden's Handbook of Batteries**
    - David Linden, Thomas B. Reddy（编），McGraw-Hill；第 4 版 2010（ISBN 978-0-07-162419-0）；最新为第 5 版（ISBN 978-1-260-11592-5）
    - 各类电池体系的权威手册，查参数、查特性用。
    - 来源：[McGraw-Hill](https://www.mheducation.com/highered/mhp/product/linden-s-handbook-batteries-4th-edition.html)

21. **Lithium-Ion Batteries: Basics and Applications**
    - Reiner Korthauer（编），Springer，2018
    - 锂电池基础与应用的章节式综述（含 BMS/安全章节），中译本《锂离子电池：基础与应用》。
    - 来源：[Springer](https://link.springer.com/book/10.1007/978-3-662-53071-9)

22. **Electric Vehicle Battery Systems**
    - Sandeep Dhameja，Newnes / Butterworth-Heinemann，2002
    - 较早但完整的 EV 电池系统工程书（电池选型、BMS、充电基础设施）。
    - 来源：[USPTO 存档版权页](https://ptacts.uspto.gov/ptacts/public-informations/petitions/1556914/download-documents?artifactId=VSZskQkdr5EzqAWfNqyCsm3gfuvHwXVzYBAeRK3gOijVAVoqc1jW6Vg)

## 六、免费资源

- **Plett 的 UCCS BMS 课程站**：http://mocha-java.uccs.edu/BMS1 —— 卷 I 官方配套页（卷 II/III 为 /BMS2、/BMS3 同款路径）。
  - **已下载到本仓库**（`books/uccs-ece5710/`，官方免费公开）：ECE5710《Modeling, Simulation, and Identification of Battery Dynamics》全套讲义 Notes00–07，对应卷 I 全部 7 章（Battery Boot Camp、等效电路模型、微观/连续介质模型、状态空间与 DRA、降阶模型、热建模）＋ 卷 I 官方勘误表 `BMS1_errata.pdf`；**Notes02 中文导读见 `docs/ece5710-notes02-中文导读.md`**。页面上另有 1.2 GB 的 ESC 模型 MATLAB/Python 工具箱（[GitHub 开源版](https://github.com/batterysim/esctoolbox-python)）与 180 MB 降阶模型工具箱，体积大未镜像，需要时按页面链接自取。
  - **已下载到本仓库**（`books/uccs-ece5720/`，官方免费公开）：ECE5720《Battery Management and Control》全套讲义 Notes00–07，对应卷 II（BMS 需求、电池包仿真、**SOC 估计 KF/EKF/SPKF/bar-delta**、SOH 估计与参数辨识、均衡、功率限制、物理最优控制）＋ 卷 II 官方勘误表 `BMS2_errata.pdf`；**Notes03 中文导读见 `docs/ece5720-notes03-中文导读.md`**。
  - 版权 © University of Colorado Colorado Springs（课程页声明），仅供个人学习使用，勿二次分发。
- **TI BMS 白皮书**：《设计更安全、更智能、互联程度更高的电池管理系统》（zhcy204）——**已下载** `books/vendor/TI-BMS-whitepaper-zhcy204.pdf`。
- **Davide Andrea 的 BMS 站**：https://book.liionbms.com/ —— 书中概念的白皮书与 BMS 设计文章。
- **GB/T 标准**（非书籍，工程必读）：《电动汽车用电池管理系统技术条件》（CATARC 官网征求意见稿：[catarc.org.cn](https://www.catarc.org.cn/upload/201810/12/201810121446048718.pdf)；2026-10-04 该站全站 502 宕机，未能镜像，恢复后可自行下载）。

## 七、视频资源

> 可内嵌播放版：仓库内 `BMS学习路径.html`（本地双击打开，需联网）。

**入门科普**

- [GreatScott! — BMS || DIY or Buy（YouTube，160 万+ 播放）](https://www.youtube.com/watch?v=rT-1gvkFj60)
  [![GreatScott BMS](https://img.youtube.com/vi/rT-1gvkFj60/mqdefault.jpg)](https://www.youtube.com/watch?v=rT-1gvkFj60)
- [How does a BMS work? Passive & Active cell balancing Explained（YouTube）](https://www.youtube.com/watch?v=q4wDa_m9-8E)
  [![How does a BMS work](https://img.youtube.com/vi/q4wDa_m9-8E/mqdefault.jpg)](https://www.youtube.com/watch?v=q4wDa_m9-8E)
- [达尔闻《1 小时讲透 BMS 设计：从系统原理到项目实战》（B 站）](https://www.bilibili.com/video/BV1NwnRzAEb3)

**系统课程**

- Plett 的 Coursera 专项课 *Algorithms for Battery Management Systems*（Plett 授课；ECEA 5730 为首门、与卷 I 内容对应；完整课程/作业/证书需注册，可旁听）：[Coursera 专项课主页](https://www.coursera.org/specializations/algorithms-for-battery-management-systems) / [CU Boulder 课程页](https://www.colorado.edu/ecee/academics/online-programs/ms-ee-coursera/curriculum/power-electronics/ecea-5730-introduction-battery)
- [Coursera 样例课：Equivalent Circuit Cell Model Simulation 欢迎课（YouTube，公开预览片段；正课需注册旁听）](https://www.youtube.com/watch?v=fRgre6Tn3mw)
- [《BMS 电池管理系统从 0 到 1 完整教程》70 集合集（B 站 UP 主"慧识学堂"，约 49 小时，疑似付费课程二次搬运，仅作中文补充材料、注意甄别）](https://www.bilibili.com/video/BV1ptME6LEb9)

## 推荐阅读路径（按 SOC 估计方向）

1. 建模基础 → Plett 卷 I（条目 1）
2. 状态估计算法 → Plett 卷 II（条目 2）＋ 熊瑞《核心算法》（条目 13）
3. SOC 指示经典方法 → Pop/Notten Springer 2008（条目 7）
4. 工程实现 → Davide Andrea 2010（条目 4）
5. 物理模型进阶 → Plett 卷 III（条目 3）＋ Rahn & Wang（条目 11）
