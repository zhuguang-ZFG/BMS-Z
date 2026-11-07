# 贯穿项目：虚拟 4S 电池包

项目源在仓库的 `code/course/`，只用 Python 标准库。建议 Python 3.12 或更新版本。网页和离线书中的所有数值都能先用计算器核对；从第 4 课开始再运行代码。

## 先验证环境

下载 [BMS-Z 仓库](https://github.com/zhuguang-ZFG/BMS-Z)，解压或克隆，在仓库根目录打开终端。若 `python` 命令不可用，Windows 可尝试把下面命令中的 `python` 换成 `py -3`。

```sh
python --version
python code/course/learn.py doctor
python code/course/learn.py init --work .tmp-my-bms.py
python code/course/learn.py check --work .tmp-my-bms.py --through 4
```

最后一条应显示 `LEARNER: 2 passed, 0 failed`。`init` 只复制一份待完成文件，已有文件不会覆盖。后续始终修改这份 `.tmp-my-bms.py`，每课将 `--through` 增加到课号。`.tmp-` 文件被仓库忽略，若要保存到自己的 Git 仓库，另选一个文件名并备份。

| 出现什么 | 先检查什么 |
|---|---|
| 找不到 `code/course/learn.py` | 当前目录是否是仓库根；确认下载的是含本课程的版本 |
| `NotImplementedError: 05...` | 只完成了第 4 课，却检查了后续课；或对应函数还没写 |
| `SyntaxError` | 编辑器是否使用英文标点；缩进是否一致；先看报错行 |
| `FAIL ... expected ... got ...` | 保留原输出，核对单位、符号、边界，再修改函数 |

本项目不需要串口、驱动、Zephyr、Conda 或真实板卡。它们放在工程进阶任务，避免环境问题与电池问题混在一起。

## 学员实现与参考实现

`workbook.py` 是脚手架，`reference.py` 是供核对的完成版本。检查自己时必须带 `--work`；以下命令检查的是配套参考答案，输出会明确标为 `REFERENCE`：

```sh
python code/course/learn.py check --reference --through 18
```

检查包含题面外的变式，但不是完整安全验证。第 19 课的控制器只接入学员的加总、采样质量、电量更新和使能函数；`violations`、`trip_at` 等单项作业由检查器单独测试。不要把“控制器能运行”当作全部作业已经完成。

## 第 19 课起运行整合项目

```sh
python code/course/project.py --scenario nominal --work .tmp-my-bms.py --out .tmp-my-run/nominal
python code/course/project.py --scenario undervoltage --work .tmp-my-bms.py --out .tmp-my-run/uv
```

未带 `--work` 时运行配套参考实现，报告也会标明。输出包括完整 `input.json`、逐拍 `trace.csv` 和 `report.json`。报告记录输入与实现的 SHA-256 摘要，帮助确认别人重跑的是同一份内容；摘要相同不证明输入来自真实测量。

可用场景：`nominal` 正常、`spike` 短暂欠压、`undervoltage` 持续欠压、`stale` 重复旧采样、`feedback` 断开后反馈仍闭合、`timeout` 远程通信过期、`transfer` 改容量和周期的迁移任务。

整合项目输入的远程请求已经解码，独立记录 `remote_received_s`，超过 0.30 s 未更新时锁存 `COMM_TIMEOUT`。第 16–17 课的字节解析与序号练习另由检查器测试；本项目没有连接真实 CAN 总线。

## 报告保留什么

记录仓库提交号、Python 版本、学员文件、输入、实际命令、输出目录、第一次异常/断开时间、判断依据和未验证项。将“我预计”与“我实际得到”分成两列。真实读者作答与卡住的原话需另外收集，不能由参考程序生成。
