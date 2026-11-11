"""19 章「先建立直觉」导读。"""
from __future__ import annotations

import html
import re

from .manifest import BookError

SCENE_RE = re.compile(
    r'<aside class="book-callout book-callout-scene"[^>]*>.*?</aside>', re.S)
# docs 侧每个章首已经有「白话」卡（scripts/curriculum.py 维护），
# 它讲的正是 CHAPTER_LEADS 那句话。印刷时若再插一条 chapter-intuition，
# 同一段白话会在同页出现两次。
LEAD_CARD_RE = re.compile(r'<aside class="book-callout book-callout-lead"')

CHAPTER_LEADS: dict[int, str] = {
    0: "先把电路想成水路：电压是水位差，电流是水流，电阻是管道变窄的地方。"
       "先学会看回路，再谈公式。",
    1: "电阻、电容、电感都有“理想值”和“真实脾气”。"
       "先看清寄生参数从哪个频率开始说话，再去算它。",
    2: "二极管像一扇单向阀：正向开、反向关。但开启电压和反向击穿是两条边界，"
       "越过去就不是理想模型了。",
    3: "BJT 是电流控制的三端器件。先分清截止、放大、饱和三个区域，再谈放大倍数。",
    4: "MOSFET 靠栅极电压控制沟道。先把它当开关看，"
       "再补上导通电阻、栅极电荷和寄生电容。",
    5: "输出级决定谁来“推”负载。推挽、开漏、上拉下拉，先问电流从哪来、往哪去。",
    6: "运放不是“永远虚短”。先看内部结构，再记参数，最后确认负反馈到底成不成立。",
    7: "比较器把输入电压差放大成两种输出状态。加一点迟滞，才能让输出在噪声里不发抖。",
    8: "模拟开关是 CMOS 传输门。导通电阻、电荷注入和关断隔离，"
       "决定它能不能放进你的信号链。",
    9: "基准和稳压器是系统的“定盘星”。把初始误差、温漂、噪声、负载与动态条件分别算清。",
    10: "电容决定电压变化有多快，比较器判断何时跨门限，锁存器决定此刻充电还是放电。",
    11: "共射、共集、共基是分析晶体管放大的起点。先确定端口和偏置，再算负载、带宽与噪声。",
    12: "虚短与虚断是两项不同的近似，写出电流路径后，还要检查各自的误差。",
    13: "电源负责供能，振荡器负责造波形；两者都要在损耗、反馈和器件极限之间找到可工作的范围。",
    14: "设计不是找唯一答案。把指标翻译成拓扑，再把假设、余量和验证记录清楚。",
    15: "PCB 上的走线也是电路。地回流、去耦和敏感信号路径，"
        "往往比原理图更早决定成败。",
    16: "排故五步：先观察现象，再分割电路，提出假设，用测量验证，最后回到根因。",
    17: "故障速查表是索引，不是答案。从症状找到可疑原因，再用测量逐条排除。",
    18: "大师的排故智慧：控制变量、选对参考点、别把假象当结论。"
        "最后用设计评审把故障挡在画板前。",
}


def insert_lead(fragment: str, lead: str) -> str:
    """导读放在场景卡之后；没有场景卡时退回标题之后。

    源文档已经带「白话」卡时原样返回：那张卡就是这条导读，插第二次只会重复。
    """
    if LEAD_CARD_RE.search(fragment):
        return fragment
    scene = SCENE_RE.search(fragment)
    if scene is not None:
        return fragment[:scene.end()] + "\n" + lead + fragment[scene.end():]
    fragment, inserted = re.subn(
        r"</h1>", "</h1>\n" + lead, fragment, count=1, flags=re.I)
    if inserted != 1:
        raise BookError("缺少章标题 h1，无法插入导读")
    return fragment


def chapter_lead(chapter: int) -> str:
    """返回插入章首的 <aside>；未知章号抛 BookError。"""
    try:
        text = CHAPTER_LEADS[chapter]
    except (KeyError, TypeError):
        raise BookError(f"未知章号: {chapter}") from None
    return (
        '<aside class="chapter-intuition">\n'
        f'<span class="ci-no" aria-hidden="true">{chapter:02d}</span>\n'
        '<div class="ci-body">\n'
        '<p class="ci-label">先建立直觉</p>\n'
        f'<p class="ci-text">{html.escape(text)}</p>\n'
        '</div>\n'
        '</aside>')
