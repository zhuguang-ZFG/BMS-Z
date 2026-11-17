# 四组对照实验：只改一个条件，先猜再跑

读过公式，再换个数字往往就会犹豫：电流翻倍，发热也翻倍吗？两次低压读数，够不够确认欠压？这里每次只改一个条件，先把 A、B 两组的预测写在纸上，再让程序算给你看。

这些是可选练习，穿插在原来的 24 课中。学完[第 4 课](04-first-run.md)、准备好 Python 后即可运行，只用标准库，无需电池、板卡或额外软件包。先做 `load`，其他题按下表中的先修进度选。

| 练习 | 先学哪课 | 两组之间只改什么 | 你要预测什么 |
|---|---|---|---|
| `load` 电流翻倍 | [第 3 课](03-load.md) | 放电电流 | 压降和发热功率各变几倍 |
| `pulse` 两个低样本 | [第 8 课](08-time.md) | 短暂欠压改成持续欠压 | 是否动作，首次确认在何时 |
| `capacity` 同一笔电量 | [第 10 课](10-counting.md) | 容量 2.0 Ah 改成 1.6 Ah | 放出 Ah 和 SOC 降幅是否都变化 |
| `stale` 看似正常的旧数据 | [第 19–20 课](19-loop.md) | 本拍采样时间改成已经接收过的旧时间 | 单行检查和完整控制循环为何不同 |

## 先运行一题

在仓库根目录运行：

```sh
python code/course/practice.py --case load --seed 7
```

屏幕只给条件和问题。`--case` 选择题型，`--seed` 固定这次的数字。同一份代码、相同题型和种子会给出相同条件，适合隔天重做或让同学复算。换一个种子可能碰巧抽到同一组数；它只控制选题，不代表新的真实测量。

先写下 A、B 的结果和单位，再运行：

```sh
python code/course/practice.py --case load --seed 7 --solve
```

`--solve` 显示参考推演，使用配套实现，不会读取或评分 `my_bms.py`。做对后换一个种子，再解释为什么压降与功率的倍数不同。只记住上一次的数值，换题后很容易露出问题。

## 卡住时只看一级提示

以 `pulse` 为例，先给自己画时间线的机会。确实接不上时，再依次运行：

```sh
python code/course/practice.py --case pulse --seed 7 --hint 1
python code/course/practice.py --case pulse --seed 7 --hint 2
```

第一级指向要观察的量，第二级补上计算关系，均不公布结果。写出自己的推演后，才用同一题型、同一种子的 `--solve` 核对。四题都能按这套方式做，不需要一次全部完成。

<details>
<summary>没有电脑也能先猜一题</summary>

沿用第 3 课的 4S 教学包：OCV 为 14.80 V，总电阻 0.12 Ω。A 组放电 2 A；B 组只把电流改为 4 A，暂时假定 OCV 和电阻不变。先分别计算端电压及电阻发热功率，再展开下一项。

</details>

<details>
<summary>写完后核对这道纸笔题</summary>

A 组压降 2 × 0.12 = 0.24 V，端电压 14.56 V，发热功率 2² × 0.12 = 0.48 W。B 组压降 0.48 V，端电压 14.32 V，发热功率 1.92 W。电流翻倍，压降翻倍，发热功率变为四倍。这里计算的是电阻耗散功率，温度上升多少还要看热容量、散热及时间。

</details>

## 把一个预测交给同学检查

一人只看题目写预测，另一人独立计算，再一起核对推演。交换角色时换题型或种子。结论不一致时，先比较输入和单位，再找最早不同的一步；不要先修改通过标准。

求助时可以直接填这张小记录：

```text
我在做：pulse，seed=7；仓库版本或下载日期：……
我运行的完整命令：……
程序给出的条件：……
我的预测与理由：……
实际输出或完整报错：……
我卡在：哪两个时刻之间算时长，而不是只问“为什么不对”
```

在[本项目讨论区](https://github.com/zhuguang-ZFG/BMS-Z/discussions)提问时附题目条件和文字输出。做第 19–21 课项目时再补 `input.json`、相关日志行和配置版本。截图可辅助说明，复制的命令和文字更方便别人复现。

## 做完后再看 GitHub 与社区

下面是本次核对过的公开入口（2026-11-16）。先带一个问题进去，选一份示例或一段讨论；无需为了完成本课同时安装这些项目。

| 资源 | 本项目借鉴或建议观察的做法 | 适合何时打开 | 难度／初读建议／语言／获取条件 |
|---|---|---|---|
| [OSTEP homework](https://github.com/remzi-arpacidusseau/ostep-homework) | 模拟器用固定随机种子出题，默认隐藏解答，另用参数计算答案；本页借鉴了先预测、再核对的过程 | 想给自己换一题时，先读仓库 README | 进阶／15–20 分钟／英文／源码与说明公开；运行示例需相应环境 |
| [Exercism Python](https://github.com/exercism/python) | 将概念练习和实践练习分开；[提示示例](https://github.com/exercism/python/blob/main/exercises/concept/currency-exchange/.docs/hints.md)按任务提供线索 | 第 4 课后想补 Python 小练习时 | 入门／15–30 分钟／英文／题面与测试公开；在线使用条件以平台为准 |
| [Rustlings](https://github.com/rust-lang/rustlings) | 小练习与语言书并行，读过后立即动手；适合观察练习粒度 | 对照练习方式即可，当前 BMS 主线不要求学习 Rust | 进阶／10–15 分钟／英文／源码公开；实际做题需要 Rust 环境 |
| [PyBaMM 入门示例](https://github.com/pybamm-team/PyBaMM/tree/main/docs/source/examples/notebooks/getting_started) | 从简单模型和工况开始，再改变模型假设或参数；记录版本、模型、参数集和实验条件 | [第 24 课模型路线](24-mastery.md#模型与估算路线)之后 | 进阶／30–60 分钟／英文／公开笔记本；本地与在线运行条件见项目说明 |
| [PyBaMM Discussions](https://github.com/pybamm-team/PyBaMM/discussions) | 查已有的模型与使用问题，先比较提问者的输入条件和版本；个别回答仍需自己验证 | 同一最小示例能够复现问题后 | 进阶／15–30 分钟／英文／公开阅读，发言需 GitHub 账号 |

本页的题面、数值和代码围绕本项目重新设计。外部项目各有自己的学习目标；例如 [Exercism 社区指南](https://github.com/exercism/docs/blob/main/community/good-member/suggesting-exercise-improvements.md)强调概念练习应集中教学，避免增加与目标无关的负担。本项目也把这四组小练习与工程验证分开：需要核查真实保护行为时，仍按[第 23 课的验证矩阵](23-validation.md)补正常、临界和失败输入。

回到[课程目录](index.md)继续下一课，或按[项目说明](project.md)检查自己的学员实现。
