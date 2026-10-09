# firmware：BMS 主状态机骨架 [应用]

主层级是 **应用**：保护去抖、故障快照、均衡和休眠怎样落成一次 `bms_tick`。高边还是低边、功能安全定级，是 [评价]，不在这几份 C 文件里做决定。

> **先读/后读**：先 `gcc` 编过并跑 `./test_bms`（应用），再跑快照回放，然后读 [逐行走读](../README.md#firmware五条纪律的代码落点对应阶段-3--6-应用)。预充、充电过流、欠温没有实现，见 `bms.h` 顶部，不要把骨架当成量产固件。

```bash
gcc -std=c99 -Wall -Wextra -Werror -o test_bms bms.c test_bms.c && ./test_bms
gcc -std=c99 -Wall -Wextra -Werror -o hil_replay bms.c hil_replay.c && ./hil_replay
```

`hil_replay` 不改 `bms.c`。它演示过充快照不被随后的短路覆盖，以及 0 mV 在这个骨架里会变成欠压。开线检测不在这里。讲解在 [阶段 6 §6.2.5](../../docs/stages/stage-6-精通与毕业项目.md#625-故障注入与快照回放-应用)。

> **原理**　每一拍都先评估全部保护，再合并断口。故障态不能跳过评估，否则后出现的过温或过放会被先出现的故障挡住。去抖是为了放过正常尖峰，不是为了把短路拖慢。
> **证据**　可核验实验：`test_bms`（CI 用 `gcc -Wall -Wextra -Werror` 编译并运行）。状态机对照 [阶段 3 §3.4](../../docs/stages/stage-3-AFE-MCU智能BMS.md) 与 [阶段 6 §6.2](../../docs/stages/stage-6-精通与毕业项目.md)。
> **延伸阅读**　[LibreSolar bms-firmware](https://github.com/LibreSolar/bms-firmware)（英文，可选）。五天跟着做见 [共学 · 固件](../../docs/共学/03-固件五天.md)。

这份代码不接电芯、不驱动 MOS。锂电池实验的安全纪律仍在阶段 2。

进阶：[PC 综合实验](../../docs/PC综合实验专题.md)。在仓库根运行 `python code/firmware/pc_demo.py`，自动编译本目录的状态机，连接电芯模型、SOC 估算、遥测组帧与接收日志。需要 Python 依赖和 gcc，产物包含 `samples.csv`、`wire.bin`、`telemetry.csv`、`events.json`、`report.json`。那份日志怎么逐拍读，见 [共学 · PC 全链路](../../docs/共学/08-pc全链路五天.md)。
