# code/ — 教程配套参考实现

> 教程里每个"动手任务"在这里都有一个**能跑、有测试**的最小实现。
> 三个包都是纯 PC 环境可运行，不需要任何硬件。

| 目录 | 内容 | 对应教程 | 运行 |
|---|---|---|---|
| `soc/` | Thevenin 电池模型 + 三种 SOC 估算器（纯安时积分 / 积分+校准点 / EKF）对比实验 | [阶段 4](../docs/stages/stage-4-SOC-SOH算法.md) §4.10 任务 1 | `cd soc && python3 compare.py --plot` |
| `protocol/` | CRC-8/16 校验 + UART 帧状态机解析器（坏帧丢弃并计数、垃圾前缀重同步） | [阶段 5](../docs/stages/stage-5-通信与集成.md) §5.2 / §5.6 | `cd protocol && python3 -m pytest tests/ -q` |
| `firmware/` | BMS 主状态机骨架（保护去抖 / 故障分级 / 快照 / 锁存 / 均衡 / 休眠），纯 C99 | [阶段 3](../docs/stages/stage-3-AFE-MCU智能BMS.md) §3.4、[阶段 6](../docs/stages/stage-6-精通与毕业项目.md) §6.2 | `cd firmware && gcc -std=c99 -Wall -Wextra -Werror -o test_bms bms.c test_bms.c && ./test_bms` |

## 环境

```bash
pip install -r requirements.txt   # numpy / matplotlib / pytest
```

- Python 3.10+；C 代码需要任意 C99 编译器（gcc/clang/MSVC 均可）。
- 全部测试在 CI 运行（`.github/workflows/tests.yml`）。

## 设计约定（与教程全文一致）

- **电流符号：充电为正**（I > 0 充、I < 0 放）；
- SOC 在代码里用 `[0, 1]`，显示时 ×100；
- 所有阈值均为**示例值**——真实产品以电芯 datasheet 与保护 IC 料号为准；
- 这些代码是**教学骨架**：刻意保持短小、每条纪律可直接对应教程章节。
  量产级参考请研究 [LibreSolar](https://github.com/LibreSolar/bms-firmware)
  与 [foxBMS](https://github.com/foxBMS/foxbms-2)。

## 给自学者的使用建议

1. **先跑后读**：跑通 `compare.py --plot`，再带着"为什么 EKF 贴得住"的问题去读 `estimators.py`；
2. **动手改**：把电流零漂改大、把 EKF 的 R 调大，看曲线怎么变——教程 §4.5 的调参直觉就是这么来的；
3. **逆向练习**：`protocol/frames.py` 的帧格式是教学抽象；学完去对照 [esphome-jk-bms](https://github.com/syssi/esphome-jk-bms) 源码读真实协议；
4. **扩展状态机**：给 `firmware/bms.c` 加"预充"状态（教程 6.1.2）或充电过流保护，并把场景测试补上。
