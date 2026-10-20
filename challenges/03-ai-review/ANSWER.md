# 参考答案：五类问题，六个检查

> 先写自己的审查记录，再看这一页。行号以 `project/` 当前文件为准；以后改夹具时行号会漂，以代码内容为准。

| # | 类别 | 位置 | 一句话 |
| --- | --- | --- | --- |
| 1 | 测试 | `project/test_frame_gate.py:19` | 断言从 `== 1` 放宽成 `>= 0`，两条边界用例被删 |
| 2 | 异常 | `project/frame_gate.py:56-60` | ASCII 解码失败被吞，二进制载荷整帧消失 |
| 3 | 行为 | `project/frame_gate.py:53-55` | 坏 CRC 不再重扫、也不再计数 |
| 4 | 行为 | `project/frame_gate.py:46` | `>` 改成 `>=`，64 字节载荷被当成非法 |
| 5 | 依赖 | `project/frame_gate.py:66-70` | 协议模块里新增 `pandas`，没声明也没测试 |
| 6 | 生成物 | `project/gates_report.txt:2-3` | 手改输出并加了一行生成器不会打印的「结论」 |

---

## 1. 测试：断言被放宽，边界用例被删

`project/test_frame_gate.py:19`：

```python
assert gate.bad_crc >= 0
```

计数器永远 `>= 0`，所以这条断言即使坏帧计数是 0 也会绿。它证明不了「坏 CRC 被计数」，只证明变量存在。

diff 里还删了两条用例：

- `test_good_frame_inside_bad_outer_frame_is_recovered`
- `test_payload_at_limit_is_delivered`

它们正好是第 3、4 条行为变化的唯一守卫。删掉之后，可见测试当然全绿。

同一份 diff 还把 `test_good_frame_is_delivered` 的期望从 `b"ok"` 改成 `"ok"`，跟着实现把载荷类型从 `bytes` 换成了 `str`。这是改契约，不是更新测试。

**判定：打回。** 恢复 `== 1`，恢复两条用例，再补一条二进制载荷用例。

## 2. 异常：解码失败被吞，帧静默消失

`project/frame_gate.py:56-60`：

```python
try:
    payload = bytes(buf[5:total - 1]).decode("ascii")
except UnicodeDecodeError:
    del buf[:total]
    continue
```

帧格式的载荷是任意字节，不是 ASCII 文本。一个 CRC 正确、载荷含 `0xff` 的帧，在 `feed()` 里被解码失败后直接丢掉：不计坏帧、不计坏长度、不留日志。对调用方来说，「没有帧」和「我扔了一帧」看起来一模一样。

**判定：打回。** `feed()` 保持返回 `bytes`；要显示再在解析之外解码，并且把解码失败计数，不要吞。

## 3. 行为：坏 CRC 不再重扫，计数也没有了

`project/frame_gate.py:53-55`：

```python
if crc8_atm(bytes(buf[2:total - 1])) != buf[total - 1]:
    del buf[:total]
    continue
```

基线是 `self.bad_crc += 1` 加 `del buf[0]`：坏帧计数加一，然后逐字节重扫，因此藏在坏帧载荷里的好帧还有机会被找到。现在计数那一行没了，跳过也从一字节变成整帧。

两个后果：

- 一个坏 CRC 的外层帧里嵌着好帧时，好帧救不回来。
- `bad_crc` 永远是 0，后面再拿这个计数做诊断就是假的。

这正是 [AI 陪练卡](../../docs/AI陪练卡.md#写代码的五个关卡)返工现场里那段：把测试改宽让它变绿，而不是修计数。

**判定：打回。** 恢复计数和逐字节重扫；补一条同时检查「计数为 1」和「后续好帧仍能解析」的测试。

## 4. 行为：64 字节载荷被当成非法

`project/frame_gate.py:46`：

```python
if size >= MAX_PAYLOAD:
```

基线是 `>`，常量是 `MAX_PAYLOAD = 64`。改成 `>=` 后，合法的 64 字节载荷会被计入 `bad_len` 并丢掉；65 字节本来就该拒。可见测试最大只测到 63 字节，所以全绿。

**判定：拆成单独改动。** 恢复 `>`；补 64 和 65 两个边界测试，别只测一个 63。

## 5. 依赖：协议模块里塞进 pandas

`project/frame_gate.py:66-70`：

```python
def summary(self) -> str:
    import pandas as pd

    rows = pd.DataFrame(self.frames, columns=["addr", "cmd", "payload"])
    return rows.to_string(index=False)
```

解析模块本来只用标准库。`summary()` 没有被任何测试或调用方使用，但新依赖已经写进代码；换一台没装 pandas 的机器，这个方法就是 `ImportError`。即使本机装了，也不代表仓库声明过这个依赖。

**判定：先讨论。** 这次任务不碰依赖。`summary()` 若真需要，用标准库拼字符串，或单独走依赖评审。

## 6. 生成物：报告被手改，还加了一行「结论」

`project/gates_report.txt:2-3`：

```text
frames=1 bad_crc=0 bad_len=0
note=回归已确认
```

`make_report.py` 没有改。用当前代码重跑生成器，输出只有两行，且 `bad_crc=0`。这意味着两件事：

- `bad_crc=0` 是坏帧计数回归的直接证据：这段流里明明有一个坏帧。它本来应该在审查时被看见，而不是被提交。
- `note=回归已确认` 生成器根本不会打印，是手写进去的。

**判定：打回。** 把输出文件退回生成器版本；先修代码，再重跑 `make_report.py`，不要手改生成物。

---

## 最小修复顺序

1. 恢复测试断言和两条被删用例，再补二进制载荷、64/65 字节边界用例；先让它们红。
2. 恢复 `bad_crc += 1` 和逐字节重扫；让坏 CRC 计数与嵌套好帧两条检查转绿。
3. 恢复 `size > MAX_PAYLOAD`；让边界检查转绿。
4. `feed()` 保持返回 `bytes`；把显示解码移出解析路径，失败要计数。
5. 去掉 `pandas`，除非单独走依赖评审。
6. 重跑 `python project/make_report.py > project/gates_report.txt` 这一类生成命令；再跑完整门禁。

## 这道题证明不了什么

- 它是静态 diff 审查练习，不是产品协议实现，也不是 `code/protocol` 的替代。
- 隐藏检查是夹具的答案，不是产品验收标准；真实项目要按自己的契约补测试。
- 没有真实电芯、阈值、寄存器或硬件。审查动作可以迁移，数字不能。
