# 贯穿项目：虚拟 4S 电池包

你会在电脑上做一个虚拟电池包：输入四节电压，写下自己的判断，再看程序有没有按预期动作。项目只用 Python 自带的工具，不需要另外安装代码包。前三课用纸笔或计算器即可；学到第 4 课时再完成下面的准备。

## 先验证环境

1. 下载[包含本课程代码的 ZIP 快照](https://github.com/zhuguang-ZFG/BMS-Z/archive/c0a3ef63452b1c1340012fa6ea448413195909be.zip)，先解压，再打开解压后的文件夹。你应能同时看到 `README.md` 文件和 `code` 文件夹；这个位置就是后文说的**仓库根目录**。不要在 ZIP 压缩包里面直接运行。
2. 如果还没有 Python，从 [Python 官网](https://www.python.org/downloads/)安装 3.12 或更新版本。Python 是运行这些 `.py` 文件的程序；无需为了本课安装其他开发工具套装。
3. 在仓库根目录打开终端。Windows 可以点资源管理器的地址栏，输入 `powershell` 后回车；macOS/Linux 可以在终端输入 `cd` 和一个空格，把解压目录拖入窗口，再回车。终端当前所在的位置决定下面的相对路径从哪里找。
4. 先输入下面第一行，按回车。确认出现 Python 版本号，再逐行运行后面的命令。如果 `python` 不可用，Windows 将它换成 `py -3`，macOS/Linux 换成 `python3`；后面的参数照抄。

后文较长的命令可能因页面宽度自动折行；从 `python` 到最后一个参数仍是一条命令，输完整后再按回车。

```sh
python --version
python code/course/learn.py doctor
python code/course/learn.py init --work my_bms.py
python code/course/learn.py check --work my_bms.py --through 4
```

`doctor` 的输出应含 `PASS`，表示基础环境可用；`init` 应显示 `created my_bms.py`，表示已经创建作业；最后一条应显示 `LEARNER: 2 passed, 0 failed, through lesson 04`，表示第 4 课的两项检查通过。

以后用文本编辑器打开并修改 **`my_bms.py`**，每次保存后再运行 `check`。`--work` 指定检查哪个文件，`--through 4` 表示检查到第 4 课；学到第 5 课时改成 `--through 5`，前面的作业也会一起重查。每次只替换当前函数中的待完成行，保留文件里其他函数。

`init` 只在首次准备时运行，已有文件不会覆盖。请定期备份自己的 `my_bms.py`。早先使用 `--work .tmp-my-bms.py` 的读者可以继续沿用原文件，只需把本页命令中的文件名换回自己的。

| 出现什么 | 先检查什么 |
|---|---|
| `python` 找不到或打开应用商店 | 确认已安装；按上面的系统选择尝试 `py -3` 或 `python3` |
| 找不到 `code/course/learn.py` | 当前目录是否是仓库根；确认下载的是含本课程的版本 |
| `work file already exists` | 作业已经创建，直接编辑并运行 `check`，不用再 `init` |
| 运行 `python my_bms.py` 后没有显示 | 该文件主要定义函数；用 `check` 检查，或按第 4 课用 `python -i my_bms.py` 亲自调用函数 |
| 窗口里是 `>>>`，命令却报错 | 你还在 Python 交互窗口；先输入 `exit()` 回到终端，再运行整条命令 |
| `NotImplementedError: 05...` | 只完成了第 4 课，却检查了后续课；或对应函数还没写 |
| `SyntaxError` / `IndentationError` | 对照报错行，检查英文标点及行首空格；保存的是 `.py`，不是 `.py.txt` |
| `FAIL ... expected ... got ...` | `expected` 是应得结果，`got` 是实际结果；保留原输出，核对单位、符号、边界，再修改函数 |
| 输出目录已存在 | 为这次运行换一个新目录，例如 `my-run/run-02`；不要删除旧结果来消除提示 |

本项目不需要串口、驱动、Zephyr、Conda 或真实板卡。它们放在工程进阶任务，避免环境问题与电池问题混在一起。

## 学员实现与参考实现

`workbook.py` 是用来复制的作业模板，`my_bms.py` 才是你正在修改的文件。`reference.py` 是供核对的完成版本。检查自己时必须带 `--work`；以下命令检查配套参考答案，输出会明确标为 `REFERENCE`，通过它不代表你自己的作业已经通过：

```sh
python code/course/learn.py check --reference --through 18
```

检查包含题面外的变式，但不是完整安全验证。第 19 课的控制器只接入学员的加总、采样质量、电量更新和使能函数；`violations`、`trip_at` 等单项作业由检查器单独测试。不要把“控制器能运行”当作全部作业已经完成。

## 第 19 课起运行整合项目

```sh
python code/course/project.py --scenario nominal --work my_bms.py --out my-run/nominal
python code/course/project.py --scenario undervoltage --work my_bms.py --out my-run/uv
```

`--scenario` 选择内置场景，`--out` 指定一个尚不存在的结果文件夹。再次运行时换新名字，例如 `my-run/nominal-02`，保留第一次的输出。未带 `--work` 时运行配套参考实现，报告也会标明。每次输出三份文件：`input.json` 保存配置和逐拍输入，`trace.csv` 每一行记录一次控制循环，`report.json` 汇总结果。CSV 是可用表格软件打开的逗号分隔表格；JSON 是用字段名组织的文本，可以用编辑器查看。

报告还记录输入与实现的 SHA-256 摘要，相当于核对文件有没有变化的一串指纹，帮助别人重跑同一份内容。摘要相同不证明输入来自真实测量。

可用场景：`nominal` 正常、`spike` 短暂欠压、`undervoltage` 持续欠压、`stale` 重复旧采样、`feedback` 断开后反馈仍闭合、`timeout` 远程通信过期、`transfer` 改容量和周期的迁移任务。

整合项目输入的远程请求已经解码，独立记录 `remote_received_s`，超过 0.30 s 未更新时锁存 `COMM_TIMEOUT`。第 16–17 课的字节解析与序号练习另由检查器测试；本项目没有连接真实 CAN 总线。

## 用保存的输入重跑

完成第一次正常回放后，在终端运行：

```sh
python code/course/project.py --input my-run/nominal/input.json --work my_bms.py --out my-run/nominal-replay
```

`--input` 表示逐行使用这份文件，不再生成内置场景；不能同时指定 `--scenario`。输入和学员实现未变时，两次的 `trace.csv` 应相同。报告中的来源与命令不同，因此不要求整份 `report.json` 相同。

打开 `input.json`，先认清三层：`schema` 标明文件格式；`config` 保存容量 `capacity_ah`（Ah）和采样周期 `period_s`（s）；`samples` 是按时间排列的输入记录。迁移场景的 1.6 Ah 与 0.05 s 也在文件里，按文件重跑时会继续使用。初始 SOC 为 1，保护阈值与延时沿用课程配置，不能在文件里另加一个字段就当作已经改了规则。

要做自己的变式，用编辑器将它**另存为** `my-run/my-input.json`，只改自己选定的一项，保存后把命令中的输入路径换成这个文件，输出改成 `my-run/my-case-01`。保留原文件和修改理由。JSON 的字段名用英文双引号，布尔值写 `true` / `false`；格式错误、缺字段或本地时间倒退会停止运行，并指出出错位置。电压超范围、节数不足、重复采样时间等可作为故障输入，由质量层记录，不会被补成正常数据。

电流、开关反馈都是文件里给定的记录。只修改电流不会自动生成新的开关动作，修改配置周期也不会重采样文件中的时间点；比较结果时，要说明哪些输入是自己设定的。旧版本只有数组的输入文件不含容量与周期，应先用本版重新导出内置场景，再迁移自己的改动。

## 报告保留什么

记录仓库提交号、Python 版本、学员文件、输入、实际命令、输出目录、第一次异常/断开时间、判断依据和未验证项。报告自动保存本次配置、命令、Python 版本和文件摘要；自己另存学员文件与预测，不能只留下摘要。将“我预计”与“我实际得到”分成两列。真实读者作答与卡住的原话需另外收集，不能由参考程序生成。
