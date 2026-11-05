---
search: false
---

---
slug: protocol-resync
style: FA-002
colors: [C-03, C-15]
frames: 6
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: protocol-resync
source_svg: docs/circuits/assets/protocol-resync.svg
---

# 观察题

三个垃圾字节挡在前面时，解析器靠什么重新咬住帧头？翻错一位之后，它又为什么要多记一个数而不是把帧吞掉？

# 帧大纲

1. 字节流从左边进来：00 11 22 三个垃圾字节逐个滑进窗口，好帧计数停在 0、坏 CRC 计数停在 0，C-03 实心游标点停在字节 2（值 0x22）。
2. 失步：整窗右移一格，三个垃圾字节被让开——解析器不把它们当帧头，只继续往下找，两个计数都不动。
3. 咬住帧头：AA 55 出现，窗口停住、锁在「帧头」刻度上；紧接着数据段落下——命令 0x03、0x0E74 按大端读成 3700 mV（示意）。
4. 校验通过：CRC-8/ATM 盖住地址到数据，算得上；C-03 好帧计数（实线）在末字节从 0 跳到 1，解析器交还一帧。
5. 翻一位：同一位置的末字节 0x13 翻掉一位，CRC 对不上，帧被拒——坏 CRC 计数从 0 跳到 1（全图唯一 C-15 处）；解析器不崩，继续往下读。
6. 收束：两个计数并排落在同一根字节轴上，都在末字节抬起来（好帧 1 / 坏 CRC 1）；旁注「坏帧要计数，不许静默吞掉」。

# Prompt（EN）

Hand-drawn educational mechanism diagram, FA-002 Saul Steinberg continuous-line style: one unbroken ink contour that threads the whole byte stream, generous white space, deadpan textbook tone, paper grain. Structure lines and labels in Prussian blue C-03 only. The bad-CRC counter is drawn as the same C-03 line, dashed and lighter, because it is a second counter on the same axis and not a hazard; vermilion C-15 appears exactly once, at the single point where the flipped byte is rejected at the last byte position — never as a fill, never as a running series.

Six frames of the same byte stream on one horizontal byte-index axis, same viewpoint, no people, no cartoon mascot, no brand logos, no photorealistic claim, schematic only:

Frame 1 — bytes arrive from the left: three garbage bytes 00 11 22 slide into the window one after another; good-frame count 0, bad-CRC count 0; the solid C-03 cursor sits at byte 2, value 0x22.
Frame 2 — out of step: the window slides one byte to the right and the garbage prefix is stepped over; the parser refuses to read them as a header and keeps hunting, both counters stay at zero.
Frame 3 — header lock: AA 55 appears and the window halts, snapped to the tick labelled 帧头; the data field drops in behind it — command 0x03, payload 0x0E74 read big-endian as 3700 mV (illustrative).
Frame 4 — checksum passes: CRC-8/ATM covers address through data, the arithmetic agrees, and the solid C-03 good-frame count steps from 0 to 1 at the last byte; the parser hands back one frame.
Frame 5 — one bit flips: the last byte 0x13 is inverted in place, the CRC no longer agrees, the frame is refused, and the bad-CRC count steps from 0 to 1 — the only C-15 mark in the picture. The parser does not fall over; it keeps reading.
Frame 6 — closing panel: both counters rest on the same byte axis and both rise at the last byte (good 1, bad 1); a small hand-lettered note reads 坏帧要计数，不许静默吞掉.

Numbers stay as small hand-lettered annotations and are all marked 示意 / illustrative; the frame format is the repository teaching frame, not any vendor's BMS. Caption: 原理示意 / 非实拍.

# Prompt（ZH）

手绘教学机制图，FA-002 Saul Steinberg 连续线风格：一条不断的墨线把整条字节流串起来，大片留白，冷面教科书语气，纸纹质感。结构线与标注只用 C-03 普鲁士蓝。坏 CRC 计数画成同色 C-03 的虚线浅线——它只是同一根轴上的第二个计数，不是危险。C-15 朱砂红全图只出现一次，标在末字节翻位被拒的那一点；不铺面，也不画成一条常驻曲线。

同一条字节流、同一视角的六个帧，无人、无卡通吉祥物、无品牌 Logo、不写实拍，纯示意：

1. 字节从左进来：三个垃圾字节 00 11 22 依次滑进窗口，好帧 0、坏 CRC 0，C-03 实心游标点停在字节 2（值 0x22）。
2. 失步：窗口右移一格，垃圾前缀被让开，解析器不认它们当帧头，只继续往下找，两个计数都不动。
3. 咬住帧头：AA 55 出现，窗口停住并吸到「帧头」刻度上；数据段随后落下——命令 0x03，0x0E74 按大端读成 3700 mV（示意）。
4. 校验通过：CRC-8/ATM 盖住地址到数据，算得上，C-03 好帧计数（实线）在末字节从 0 跳到 1，解析器交还一帧。
5. 翻一位：末字节 0x13 原地翻掉一位，CRC 对不上，帧被拒，坏 CRC 计数从 0 跳到 1——全图唯一 C-15。解析器不崩，继续往下读。
6. 收束：两个计数并排落在同一根字节轴上，同在末字节抬起（好帧 1 / 坏 CRC 1）；手写旁注「坏帧要计数，不许静默吞掉」。

数字只用小手写标注，全部标「示意」；帧格式是仓库教学帧，不假称某家 BMS 的抓包。图注：原理示意 / 非实拍。

# 验收自检

- [ ] 无人、无卡通
- [ ] 危险仅 C-15，且只有一处（末字节的坏 CRC 计数）
- [ ] 第二计数已改为 C-03 虚线，没有被当成危险色
- [ ] 图注将用「原理示意 / 非实拍」
- [ ] 六帧同一字节轴、同一视角，可暂停阅读
- [ ] 首末帧单独成图仍可读（AA 55 与两个计数都能辨认）
- [ ] 不宣称任何厂商帧格式或真实抓包
