---
search: false
slug: structure-vs-trust
style: FA-029
colors: [C-03, C-15]
frames: 5
caption: 原理示意 / 非实拍
bans: [no-people, no-cartoon-IP, no-live-photo-claim]
kp_id: protocol-resync
source_svg: null
---

# 观察题

一帧报文头对上了、长度合法、CRC 也通过了，为什么还不能直接拿去控制？——因为这三道检查只看字节本身，它们读不出这串字节是什么时候采的。

# 帧大纲

1. 版式立起：教学帧的六个字段横成一条——`AA 55 | addr | cmd | len | data[len] | crc8`。图上用的是 §29.3 回放那条好帧 `aa 55 01 03 02 0e a0 31`，CRC `31` 覆盖 `01 03 02 0e a0`，不自造字节。
2. 三道结构检查落位：头对上、长度在 `MAX_LEN=64` 以内、CRC-8 通过。三个「过」字分别压在头、长度、CRC8 三格下方，下面一条虚线写明「结构合法：头、长度、CRC 全过」。
3. 时间轴出现：采样时刻在左，到达时刻在右，中间一段箭头。同一串字节，刚采的和 3 秒前采的，结构上无法区分——这段时间差，帧里没有任何一个字节记着它。
4. 五个语义检查格排开：缩放、端序、固件版本、滚动计数器、信号新鲜度。解析器只证明字节结构成立，不证明语义可信；这五件事一件都还没验。
5. 两章分工收尾：第 29 章把原始字节安全地交上去，第 18 章负责端到端数据身份。红色只落在结论一句——结构检查管不到时间：CRC 正确的一帧，内容可能已经过期。

# Prompt（EN）

Hand-drawn educational information diagram, FA-029 Chris Ware geometric narrative style: flat geometric panels, precise ruled framing, restrained deadpan composition, paper grain. All linework and labels in Prussian blue C-03; vermilion C-15 appears exactly once, on the final frame's concluding line. Numbers stay as small hand-lettered annotations, all marked 示意 / illustrative. Caption: 原理示意 / 非实拍.

Five frames, one fixed layout: a six-cell byte strip across the upper third holding one teaching frame, a dashed structural-validity rule below it, a sampling-to-arrival time arrow in the middle band, a row of five small labelled boxes for the remaining semantic checks, and two wide lanes at the bottom dividing responsibility between two chapters. No people, no cartoon mascot, no brand logos, no photorealistic claim:

Frame 1 — layout only: the six-cell byte strip with hand-lettered hex in each cell and the field name beneath it (header, address, command, length, data, CRC8).
Frame 2 — three structural checks resolve: a small pass mark under the header, length and CRC8 cells, and a dashed rule beneath them declaring the frame structurally valid.
Frame 3 — a horizontal time arrow appears below the rule, ticked at the sampling moment on the left and the arrival moment on the right, annotated that the same byte string is structurally indistinguishable whether sampled now or three seconds earlier.
Frame 4 — five small boxes open in a row: scaling, endianness, firmware version, rolling counter, signal freshness — none of them verified by the structural checks above.
Frame 5 — two wide lanes close the figure, one per chapter responsibility, and a single vermilion line states that structural checks cannot see time: a CRC-correct frame may already be stale.
