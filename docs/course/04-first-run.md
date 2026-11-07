# 04 · 把第一行采样读进电脑

先修：[第 3 课](03-load.md)。本课第一次用电脑，不要求你已经会编程。完成后，你能运行一个小函数，并知道输入、代码和输出分别在哪里。

## 先让已知正确的一步成功

按 [项目说明](project.md)下载仓库，在仓库根打开终端，运行环境自检和 `init`。终端是输入命令、查看文字结果的窗口；它的当前目录决定相对路径从哪里找。命令找不到文件时，先检查位置，不要先重装 Python。

```sh
python code/course/learn.py doctor
python code/course/learn.py init --work .tmp-my-bms.py
python code/course/learn.py check --work .tmp-my-bms.py --through 4
```

## 读懂六行 Python

用文本编辑器打开 `.tmp-my-bms.py`，开头已经提供：

```python
def pack_voltage(cells):
    return sum(cells)
```

`def` 定义一个函数，相当于给一小段计算起名字。`cells` 是传进来的四个数，写成列表 `[3.70, 3.72, 3.68, 3.71]`；`sum` 将它们相加；`return` 把结果交回调用者。缩进表示函数内部的语句，中文说明可以写在 `#` 后。

检查器会调用这个函数，把结果与 **14.81 V** 对照，再换一组数检查。它不是只打印你想看到的结果。可以暂时把 `return sum(cells)` 改成 `return 14.81` 再运行：第二组会失败。观察后改回来，保留这次失败记录。

## 一行数据需要哪些字段

采样是某一时刻取得的一组读数。CSV 是用逗号分隔的文本表格，第一行写字段名：

```csv
sampled_s,cell1_v,cell2_v,cell3_v,cell4_v,current_a,temp_c
0.0,3.70,3.72,3.68,3.71,1.0,25.0
```

`sampled_s` 是取得数据的时间，单位秒；`current_a` 约定放电为正、充电为负；`temp_c` 是摄氏温度。列名把单位写出来，能减少把 3700 mV 当作 3700 V 的错误。

现阶段只读懂这行，不必写完整 CSV 解析器。项目会在第 19 课把完整输入和结果分别保存为 JSON 与 CSV。JSON 是另一种带字段名的数据文本，适合保存四节电压这样的列表。

## 合上例子再做

给 `pack_voltage` 输入 `[3.10, 3.20, 3.30, 3.40]`，先手算再运行。解释为什么把答案直接写死，第一组通过仍不表示函数正确。再说明 `current_a=-0.5` 在本课程中表示什么。

<details class="course-check">
<summary>做完后核对</summary>

总电压 **13.0 V**。函数应随输入改变；固定返回 14.81 会被第二组拒绝。−0.5 A 表示 **0.5 A 充电**。浮点计算可能出现 14.809999…，检查器允许很小的舍入差，不能因此放宽到毫伏级测量误差。

</details>

下一课：[读数离真值有多远](05-calibration.md)。
