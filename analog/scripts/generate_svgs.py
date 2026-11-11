# -*- coding: utf-8 -*-
"""
generate_svgs.py — 一键再生成《通往模拟电路之路》全部 108 张 SVG SMIL 动画
用法:  python generate_svgs.py            # 输出到 ../assets/svg/
风格:  参考 BMS-Z 项目 —— 浅色底 + SMIL 节拍字幕 + 深色模式自适应 + 拟人化讲解
所有电路参数经过自洽核算（datasheet 级），详见各函数注释。
"""
import os
import re

import numpy as np

import handraw

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'svg')
os.makedirs(OUT, exist_ok=True)

DARK_CSS = handraw.token_css()

# 注意：「减弱动效」的规则**故意不写在这里**。
#
# SVG 作为 <img> 载入时（本站 108 张动画就是这么嵌的），Chrome 会把
# `prefers-reduced-motion` **恒判为 reduce** —— 页面自己明明是无偏好，图片文档里
# 却是 reduce（有头/无头、data: / http、独立启动的 Chrome 155 均实测一致）。
# 所以写在 SVG 里的 media query 只有两种结局：要么恒不生效，要么恒生效；
# 一旦恒生效，全站动画对**所有人**都是静止的（v3.45 正是踩了这个坑）。
#
# 正确做法是在**页面**上下文里选源：`build_site.py` 生成一份静止版
# `<stem>.reduce.svg`，再把每个动画包进
#   <picture><source srcset="…reduce.svg" media="(prefers-reduced-motion: reduce)">…
# 由 <source media> 决定加载哪一份。因此 SVG 自身必须是「无 media query 的动画版」。
# 详见 scripts/build_site.py 的 REDUCE_CSS / wrap_reduce_picture()。

# 当前这张图的节拍字幕文案（供 <desc> 使用：让读屏用户也能听到"讲了什么"）。
# caption() 追加，save() 落盘后清空。**svg_open() 故意不清空**——见那里的注释。
_BEATS = []

# 当前这张图的 (title, w)——save() 用它给标题配手写体与马克笔划线。
_CURRENT = ('', 800)

# ======================= 模板与元件库 =======================

def svg_open(title, w=800, h=460):
    # 注意：这里**不能**清空 _BEATS。有 8 张图（debug-flow / design-flow /
    # diagnosis-tree / fault-lookup / ground-star / master-wisdom /
    # thinking-toolbox / transformer）是先拼字幕、后调 svg_open 的，
    # 在 svg_open 里清零会把它们的节拍从 <desc> 里抹掉。
    # 清空只放在 save() 落盘之后——每张图恰好 save 一次，因此不会串图。
    #
    # 视觉皮肤（纸墨调色板、纸纹、手写标题）全部来自 handraw.py：这里只保留
    # 结构骨架。印刷管线靠 id="bgL" + .page-* 类名识别旧模板，别改这些标记。
    global _CURRENT
    _CURRENT = (title, w)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="ttl">
<title id="ttl">{title}</title>
<desc>{title}</desc>
{handraw.svg_defs(w, h)}
<rect class="page-bg" width="{w}" height="{h}" fill="url(#bgL)"/>
<rect class="page-grain" width="{w}" height="{h}" fill="url(#dots)"/>
<rect class="page-vig" width="{w}" height="{h}" fill="url(#vig)"/>
<rect class="page-hdr" width="{w}" height="72" fill="url(#hdr)"/>
{DARK_CSS}
<text x="{w//2}" y="29" text-anchor="middle" font-size="19" font-weight="bold" fill="#1e293b">{title}</text>
'''

def flow(path, dur, n=3, color="#f59e0b", r=5.5, stagger=None, keypoints="0;0.3;0.7;1", keytimes="0;0.35;0.65;1"):
    """沿路径的电流粒子；begin 负相位保证静态首帧可见；默认四点 keyPoints 缓入缓出（两端慢、中间快）"""
    stagger = stagger if stagger is not None else dur / n
    kp = f' keyPoints="{keypoints}" keyTimes="{keytimes}" calcMode="linear"' if keypoints else ''
    inner = '\n'.join(
        f'<circle r="{r}" fill="{color}">'
        f'<animateMotion dur="{dur}s" begin="{i*stagger-0.5:.2f}s" repeatCount="indefinite" path="{path}"{kp}/></circle>'
        for i in range(n))
    return f'<g filter="url(#pglow)">{inner}</g>'

def _text_w(s, size):
    """粗略估算文本宽度（CJK/全角/圈号约 1.0em、数字/大写约 0.66em）——用于给字幕配药丸底衬"""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if o >= 0x2E80 or 0x2460 <= o <= 0x24FF or ch in "—–…":
            w += size
        elif ch in "iljI.,:;'|! ":
            w += size * 0.30
        elif ch in "→←↑↓⇒⇔±×÷≈≠≤≥√∑∫∞∝°":
            w += size * 0.95
        elif 0x0370 <= o <= 0x03FF:            # 希腊字母（Ω、µ 等）
            w += size * 0.75
        elif ch.isupper() or ch.isdigit():
            w += size * 0.66
        else:
            w += size * 0.58
    return w * 1.045

def caption(text, color, dur, kt_values, kt_times, y=400, x=400, size=14.5, w=800):
    """节拍字幕：kt_values/kt_times 控制该幕的显隐窗口；配同相显隐的药丸底衬 + 轻微上浮"""
    _BEATS.append(text)
    tw = _text_w(text, size)
    pw, ph = tw + 30, size * 1.66
    pill = ''
    if pw <= w - 24:                       # 过长的字幕不配底衬，免得压到画面边
            pill = (f'<rect x="{x-pw/2:.1f}" y="{y-size*0.9:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{ph/2:.1f}" '
                    f'fill="{color}" fill-opacity="0.09" stroke="{color}" stroke-opacity="0.38" stroke-width="1.3" '
                    f'filter="url(#soft)" opacity="0">'
                f'<animate attributeName="opacity" values="{kt_values}" keyTimes="{kt_times}" dur="{dur}s" repeatCount="indefinite"/></rect>')
    txt = (f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" font-weight="bold" fill="{color}" opacity="0">'
           f'{text}<animate attributeName="opacity" values="{kt_values}" keyTimes="{kt_times}" '
           f'dur="{dur}s" repeatCount="indefinite"/></text>')
    # 上浮量跟着显隐曲线走：入场 6→0px 上浮，退场 0→−4px 上飘；零重叠交接靠运动接力
    slide = ''
    try:
        vals = [float(v) for v in kt_values.split(';')]
        if len(vals) == len(kt_times.split(';')):
            def drift(idx):
                if vals[idx] >= 1:
                    return 0.0
                if idx and vals[idx - 1] >= 1:
                    return -4.0 * (1 - vals[idx])
                return 6.0 * (1 - vals[idx])
            tv = ';'.join(f'0 {drift(i):.1f}' for i in range(len(vals)))
            slide = (f'<animateTransform attributeName="transform" type="translate" values="{tv}" '
                     f'keyTimes="{kt_times}" dur="{dur}s" repeatCount="indefinite"/>')
    except ValueError:
        pass
    return f'<g>{slide}{pill}{txt}</g>'

def beat_captions(beats, dur, y):
    """均分字幕时隙；交接点 b 处旧拍恰好淡完、新拍恰好开始淡入（零重叠接力）。

    两个字幕共用一个 y，任何同窗交叉都会把两行字叠印成糊——所以拼的是
    时间上首尾相衔 + 换场时的上浮/上飘运动，而不是透明度交叉。
    """
    if not beats or dur <= 0:
        raise ValueError('beats must be nonempty and duration must be positive')
    n = len(beats)
    fade = min(0.02, 0.2 / n)
    out = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i / n, (i + 1) / n
        times = ([0] if a else []) + [a, a + fade, b - fade, b] + ([1] if b < 1 else [])
        values = ([0] if a else []) + [0, 1, 1, 0] + ([0] if b < 1 else [])
        out += caption(txt, col, dur, ';'.join(map(str, values)),
                       ';'.join(f'{t:.8g}' for t in times), y=y) + '\n'
    return out

def veil(x, y, w, h, i, n, dur, amount=0.42, fill="#fdf8ea"):
    """强调层的「去亮遮罩」：盖住第 i 块内容，轮到它时淡开。

    为什么不用「内容自身 animate opacity」：印刷管线（book/svg_refine.py）会把
    **任何带直接动画子节点的元素整块删掉**，挂在内容上的 animate 会让算式/卡片
    在纸上凭空消失（实测 derive-divider 23→5 个 text）。所以内容永远静态、
    动效只做在独立的矩形遮罩上——遮罩被印刷删掉是无损的（最多少一层变暗）。
    """
    a = i / n
    fade = min(0.03, 0.25 / n)
    if i == 0:
        return ''                                    # 第一块 t=0 就点亮
    kt = f"0;{a:.6g};{a + fade:.6g};1"
    vals = f"{amount};{amount};0;0"
    # 基础 opacity 写 0（不是 amount）：减弱动效版只停不删 opacity 动画，若基础值
    # 就是 0.5，遮罩会永久压在卡片/算式上；写 0 则任何静止渲染（减弱动效、印刷、
    # README 里的 <img>）看到的都是**完全点亮**的内容，只有真跑动画时才变暗。
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" opacity="0">'
            f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" '
            f'dur="{dur}s" repeatCount="indefinite"/></rect>')

def stage_cards(cards, dur):
    """四拍卡逐拍揭示：每张卡上覆一块纸色遮罩，轮到第 i 拍才淡开。

    卡片本体保持静态——印刷管线只认遮罩上的 animate，卡片文字原样留在纸上；
    遮罩本体 opacity=0，0.5 由 SMIL 的 values[0] 在 t=0 给出：静止渲染（减弱动效、印刷、
    忽略 SMIL 的阅读器）看到的是完全点亮，只有真跑动画才渐暗。
    """
    return [card + veil(20 + 192 * i, 70, 174, 214, i, len(cards), dur, amount=0.5)
            for i, card in enumerate(cards)]

# ======================= 推导阶梯（公式推导图共用） =======================

def derive_ladder(steps, dur, x, y, w=352, gap=58, accent="#b45309"):
    """右栏推导阶梯：steps = [(步骤标签, 算式, 依据), ...]。

    第 i 行在自己的时隙淡入后常驻；一个描边游标按拍离散下跳，始终框住
    「此刻推到哪一行」。第一行 t=0 就在场，静止首帧不空。
    """
    if not steps:
        raise ValueError('steps must be nonempty')
    n = len(steps)
    ys, rows = [], ''
    for i, (tag, expr, why) in enumerate(steps):
        top = y + i * gap
        ys.append(top)
        rows += (f'<text x="{x}" y="{top}" font-size="11.5" font-weight="bold" fill="{accent}">{tag}</text>'
                 f'<text x="{x}" y="{top + 25}" font-size="14.5" font-weight="bold" fill="#1e293b">{expr}</text>'
                 f'<text x="{x}" y="{top + 42}" font-size="10.5" fill="#64748b">{why}</text>'
                 + veil(x - 12, top - 24, w, 58, i, n, dur) + '\n')
    times = ';'.join(f'{i / n:.6g}' for i in range(n)) + ';1'
    pos = ';'.join(str(v) for v in ys) + f';{ys[-1]}'
    cursor = (f'<rect x="{x - 12}" y="{ys[0] - 24}" width="{w}" height="58" rx="7" fill="none" '
              f'stroke="{accent}" stroke-width="1.8" opacity="0.9">'
              f'<animate attributeName="y" values="{pos}" keyTimes="{times}" calcMode="discrete" '
              f'dur="{dur}s" repeatCount="indefinite"/></rect>\n')
    return cursor + rows

def derive_frame(title, steps, left_svg, h=680, dur=16):
    """左图右算式的推导版式：左边电路随拍揭示，右边公式阶梯随拍推进，共用 n、dur。"""
    svg = svg_open(title, h=h)
    svg += (f'<line x1="392" y1="86" x2="392" y2="{h - 44}" stroke="#cbd5e1" '
            f'stroke-width="1" stroke-dasharray="6,5"/>\n')
    svg += left_svg
    svg += derive_ladder(steps, dur, 412, 134, w=352, gap=58)
    return svg

def chip(x, y, text, color="#3d6b4a", size=11.5, fill="#f6eedb"):
    """纸片标签：低位（页底暗带）注释统一承载在这块小纸片上，浅深两主题都可读。"""
    w = _text_w(text, size) + 22
    return (f'<rect x="{x - w/2:.0f}" y="{y - size:.0f}" width="{w:.0f}" height="{size + 12:.0f}" rx="6" '
            f'fill="{fill}" stroke="{color}" stroke-width="1"/>'
            f'<text x="{x}" y="{y + 4:.0f}" text-anchor="middle" font-size="{size}" '
            f'font-weight="bold" fill="{color}">{text}</text>')

def _wrap(text, avail, size, maxlines=3):
    """折行：优先用最少行数，行宽尽量均衡，并倾向在标点后断行"""
    if _text_w(text, size) <= avail or maxlines <= 1:
        return [text]
    for n in range(2, maxlines + 1):               # 先试 2 行，塞不下再 3 行
        target = _text_w(text, size) / n
        best = None
        for i in range(1, len(text)):
            w1 = _text_w(text[:i], size)
            if w1 > avail:
                break
            rest = text[i:]
            if _text_w(rest, size) > avail * (n - 1):
                continue
            score = abs(w1 - target)
            if text[i - 1] in "。；！？，、：）」】":   # 标点后断行更自然
                score *= 0.7
            if best is None or score < best[0]:
                best = (score, i)
        if best is not None:
            i = best[1]
            return [text[:i]] + _wrap(text[i:], avail, size, n - 1)
    return [text]                                  # 实在塞不下，只能溢出

def note_box(text, y, dur, delay_kt="0;0.82;0.86;1", color="#059669", bg="#ecfdf5", x=400, w=560, size=13.5, focus=None):
    """延迟出现的要点注释框（柔和投影 + 左侧色条；文案过长时自动折行，框高随之增长）。

    focus=(fx,fy,fw,fh) 时，注释框登场的同一窗口里对主角图元套一圈
    呼吸高亮框（视线引导，等价 manim 的 Indicate）。
    """
    lines = _wrap(text, w - 34, size)
    n, sp = len(lines), size + 4.5
    h = 34 + (n - 1) * sp
    rects = (f'<rect x="{x-w//2}" y="{y-24}" width="{w}" height="{h}" rx="9" fill="{bg}" stroke="{color}" '
             f'stroke-width="1.5" filter="url(#soft)"/>'
             f'<rect x="{x-w//2+6}" y="{y-17}" width="3" height="{h-14}" rx="1.5" fill="{color}"/>')
    txt = ''.join(f'<text x="{x}" y="{y-2+i*sp:.1f}" text-anchor="middle" font-size="{size}" '
                  f'font-weight="bold" fill="{color}">{ln}</text>' for i, ln in enumerate(lines))
    focus_svg = ''
    if focus:
        fx, fy, fw, fh = focus
        focus_svg = pulse(fx, fy, fw, fh, color=color, dur=1.2)
    if delay_kt is None:          # 印刷安全：整块静态（refine 会删掉带 animate 的元素）
        return f'<g>{focus_svg}{rects}{txt}</g>'
    return (f'<g opacity="0">\n<animate attributeName="opacity" values="0;0;1;1" keyTimes="{delay_kt}" '
            f'dur="{dur}s" repeatCount="indefinite"/>\n{focus_svg}{rects}{txt}\n</g>')

def trace2(path_d, dur, color="#2563eb", width=3.5, kt="0;0.82;0.875;0.93;1", plen=700, ghost=True):
    """描线动画（ghost=True 时附 18% 透明度完整底稿，静态首帧不空）。

    默认 keyTimes 走缓出四点采样（起步快、收尾慢）；调用方显式传 kt 时
    保持旧的「保持→线性到底」两点语义。
    """
    g = f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="1.8" opacity="0.18"/>' if ghost else ''
    if kt == "0;0.82;0.875;0.93;1":
        values = f"{plen};{plen};{plen*0.5:.0f};{plen*0.12:.0f};0"
    else:
        values = f"{plen};{plen};0;0"
    return g + (f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
                f'stroke-dasharray="{plen}" stroke-dashoffset="{plen}">'
                f'<animate attributeName="stroke-dashoffset" values="{values}" keyTimes="{kt}" '
                f'dur="{dur}s" repeatCount="indefinite"/></path>')

def pulse(x, y, w, h, color="#f59e0b", dur=1.2, rx=8):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="none" stroke="{color}" stroke-width="2.5" opacity="0" filter="url(#pglow)">'
            f'<animate attributeName="opacity" values="0.15;0.9;0.15" dur="{dur}s" repeatCount="indefinite"/></rect>')

def gnd_sym(x, y, color="#334155"):
    return (f'<line x1="{x}" y1="{y-14}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="2.5"/>'
            f'<line x1="{x-16}" y1="{y}" x2="{x+16}" y2="{y}" stroke="{color}" stroke-width="3"/>'
            f'<line x1="{x-10}" y1="{y+6}" x2="{x+10}" y2="{y+6}" stroke="{color}" stroke-width="3"/>'
            f'<line x1="{x-4}" y1="{y+12}" x2="{x+4}" y2="{y+12}" stroke="{color}" stroke-width="3"/>')

def resistor_h(x, y, w=56, label='', sub='', color="#334155", lcolor="#b45309"):
    sub_t = f'<text x="{x+w/2}" y="{y+15}" text-anchor="middle" font-size="10.5" fill="#475569">{sub}</text>' if sub else ''
    return f'''<line x1="{x-20}" y1="{y}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="2.5"/>
<rect x="{x}" y="{y-11}" width="{w}" height="22" fill="#f8fafc" stroke="{color}" stroke-width="2.5"/>
<line x1="{x+w}" y1="{y}" x2="{x+w+20}" y2="{y}" stroke="{color}" stroke-width="2.5"/>
<text x="{x+w/2}" y="{y-17}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="{lcolor}">{label}</text>{sub_t}'''

def resistor_v(x, y, h=56, label='', color="#334155", lcolor="#b45309"):
    body = f'''<line x1="{x}" y1="{y-20}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="2.5"/>
<rect x="{x-11}" y="{y}" width="22" height="{h}" fill="#f8fafc" stroke="{color}" stroke-width="2.5"/>
<line x1="{x}" y1="{y+h}" x2="{x}" y2="{y+h+20}" stroke="{color}" stroke-width="2.5"/>'''
    if label:
        body += f'\n<text x="{x+20}" y="{y+h/2+4}" font-size="12.5" font-weight="bold" fill="{lcolor}">{label}</text>'
    return body

def npn_svg(x, y, color="#334155"):
    """NPN：基区棒在(x-35,y)，C 右上、E 右下（发射极箭头向外，沿斜线方向）"""
    return f'''<g stroke="{color}" fill="none" stroke-width="2.5">
<circle cx="{x-12}" cy="{y}" r="34" stroke-width="1.8"/>
<line x1="{x-35}" y1="{y-20}" x2="{x-35}" y2="{y+20}" stroke-width="3.5"/>
<line x1="{x-35}" y1="{y-8}" x2="{x}" y2="{y-35}"/>
<line x1="{x-35}" y1="{y+8}" x2="{x}" y2="{y+35}"/>
<line x1="{x}" y1="{y-35}" x2="{x}" y2="{y-55}"/>
<line x1="{x}" y1="{y+35}" x2="{x}" y2="{y+55}"/>
<line x1="{x-85}" y1="{y}" x2="{x-35}" y2="{y}"/>
<polygon points="{x},{y+35} {x-12.5},{y+31.6} {x-6.5},{y+23.8}" fill="{color}" stroke="none"/>
</g>
<text x="{x-93}" y="{y-8}" font-size="12.5" font-weight="bold" fill="#dc2626">B</text>
<text x="{x+9}" y="{y-48}" font-size="12.5" font-weight="bold" fill="#2563eb">C</text>
<text x="{x+9}" y="{y+60}" font-size="12.5" font-weight="bold" fill="#059669">E</text>'''

def diode_arm(x1, y1, x2, y2, label, dlx, dly):
    """桥臂二极管：正向从 (x1,y1) 指向 (x2,y2)"""
    mx, my = (x1+x2)/2, (y1+y2)/2
    dx, dy = x2-x1, y2-y1
    L = float(np.hypot(dx, dy))
    ux, uy = dx/L, dy/L
    px, py = -uy, ux
    t = 11
    tipx, tipy = mx+ux*t, my+uy*t
    bx1, by1 = mx-ux*t, my-uy*t
    return f'''<line x1="{x1}" y1="{y1}" x2="{bx1:.0f}" y2="{by1:.0f}" stroke="#334155" stroke-width="2.5"/>
<polygon points="{tipx:.0f},{tipy:.0f} {bx1+px*t:.0f},{by1+py*t:.0f} {bx1-px*t:.0f},{by1-py*t:.0f}" fill="#334155"/>
<line x1="{tipx+px*t:.0f}" y1="{tipy+py*t:.0f}" x2="{tipx-px*t:.0f}" y2="{tipy-py*t:.0f}" stroke="#334155" stroke-width="3.5"/>
<line x1="{tipx:.0f}" y1="{tipy:.0f}" x2="{x2}" y2="{y2}" stroke="#334155" stroke-width="2.5"/>
<text x="{dlx}" y="{dly}" font-size="12" font-weight="bold" fill="#475569">{label}</text>'''

def sine_path(x0, x1, ymid, amp, n=48, phase=0.0):
    pts = []
    for i in range(n+1):
        t = i/n*2*np.pi
        x = x0 + (x1-x0)*i/n
        y = ymid + amp*np.sin(t+phase)
        pts.append(f"{x:.0f},{y:.0f}")
    return "M" + " L".join(pts)

def square_path(x0, x1, y_hi, y_lo, periods=2, n=64):
    pts = []
    for i in range(n+1):
        t = i/n*periods
        x = x0 + (x1-x0)*i/n
        y = y_lo if (t % 1) < 0.5 else y_hi
        pts.append(f"{x:.0f},{y:.0f}")
    return "M" + " L".join(pts)

def tri_cap(x0, x1, y13, y23, cycles=2):
    """555 电容三角波：充电 2 份时间、放电 1 份（占空比 2/3 的来源）"""
    pts = []
    T = 3.0
    n = 90
    for i in range(n+1):
        t = i/n*cycles*T
        ph = t % T
        x = x0 + (x1-x0)*i/n
        y = y13+(y23-y13)*(ph/2) if ph < 2 else y23-(y23-y13)*(ph-2)
        pts.append(f"{x:.0f},{y:.0f}")
    return "M" + " L".join(pts)

def sq_out(x0, x1, yhi, ylo, cycles=2):
    pts = []
    T = 3.0
    n = 90
    for i in range(n+1):
        t = i/n*cycles*T
        ph = t % T
        x = x0 + (x1-x0)*i/n
        y = ylo if ph < 2 else yhi
        pts.append(f"{x:.0f},{y:.0f}")
    return "M" + " L".join(pts)

def save(name, svg):
    global _BEATS
    title, width = _CURRENT
    svg = handraw.apply(svg, width, title)
    if _BEATS:
        # 字幕文案在生成器里已经是 XML 转义过的（例如 `距离&lt;3mm`），这里不能再
        # 转义一次，否则 <desc> 会读成字面的 "&lt;"。
        svg = svg.replace('</desc>', '；节拍：' + '；'.join(_BEATS) + '</desc>', 1)
    _BEATS = []
    path = os.path.join(OUT, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg)
    print('saved', name, len(svg), 'bytes')

# ======================= 图 1：RC 充电 =======================
def make_rc_charge():
    DUR = 5
    pts = []
    for i in range(33):
        t = i/32*5
        x = 430 + (750-430)*i/32
        y = 350 - (350-182)*(1-np.exp(-t))
        pts.append(f"{x:.0f},{y:.0f}")
    curve_d = "M" + " L".join(pts)
    hs = [0, .47, .72, .86, .94, .985]          # 指数充电采样 1-e^-t
    kt_h = "0;0.2;0.4;0.6;0.8;1"
    h_vals = ";".join(f"{24*u:.1f}" for u in hs)
    y_vals = ";".join(f"{263-24*u:.1f}" for u in hs)
    svg = svg_open('RC 充电：电容是"水桶"，电阻是"细水管"')
    svg += f'''
<text x="200" y="70" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">电路</text>
<line x1="60" y1="120" x2="60" y2="196" stroke="#334155" stroke-width="2.5"/>
<line x1="60" y1="222" x2="60" y2="300" stroke="#334155" stroke-width="2.5"/>
<line x1="46" y1="196" x2="74" y2="196" stroke="#334155" stroke-width="2"/>
<line x1="52" y1="222" x2="68" y2="222" stroke="#334155" stroke-width="4"/>
<text x="36" y="193" font-size="13" fill="#334155">+</text>
<text x="30" y="216" font-size="13" fill="#334155">−</text>
<text x="18" y="260" font-size="13" font-weight="bold" fill="#b45309">5V</text>
<line x1="60" y1="120" x2="100" y2="120" stroke="#334155" stroke-width="2.5"/>
<circle cx="100" cy="120" r="3.5" fill="#334155"/>
<line x1="100" y1="120" x2="132" y2="106" stroke="#334155" stroke-width="2.5"/>
<circle cx="136" cy="120" r="3.5" fill="#334155"/>
<text x="70" y="97" font-size="11.5" fill="#475569">开关</text>
<line x1="136" y1="120" x2="150" y2="120" stroke="#334155" stroke-width="2.5"/>
<rect x="150" y="108" width="70" height="24" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="185" y="97" text-anchor="middle" font-size="13" font-weight="bold" fill="#b45309">R = 1kΩ</text>
<text x="185" y="124" text-anchor="middle" font-size="11" fill="#475569">水管</text>
<line x1="220" y1="120" x2="320" y2="120" stroke="#334155" stroke-width="2.5"/>
<line x1="320" y1="120" x2="320" y2="235" stroke="#334155" stroke-width="2.5"/>
<line x1="285" y1="235" x2="355" y2="235" stroke="#334155" stroke-width="3"/>
<line x1="285" y1="265" x2="355" y2="265" stroke="#334155" stroke-width="3"/>
<rect x="291" y="263" width="58" height="0" fill="#3b82f6" opacity="0.75">
  <animate attributeName="height" values="{h_vals}" keyTimes="{kt_h}" dur="{DUR}s" repeatCount="indefinite"/>
  <animate attributeName="y" values="{y_vals}" keyTimes="{kt_h}" dur="{DUR}s" repeatCount="indefinite"/>
</rect>
<text x="424" y="252" text-anchor="end" font-size="13" font-weight="bold" fill="#2563eb">C = 10µF</text>
<text x="372" y="270" font-size="11" fill="#475569">水位=电量</text>
<line x1="320" y1="265" x2="320" y2="300" stroke="#334155" stroke-width="2.5"/>
<line x1="320" y1="300" x2="60" y2="300" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(190, 300)}
{flow("M66,112 H314 V228", DUR, n=4, color="#f59e0b", r=5.5, keypoints="0;0.5;0.8;1", keytimes="0;0.2;0.5;1")}
<text x="120" y="152" font-size="11.5" fill="#b45309">电流（先快后慢）</text>
'''
    svg += f'''
<text x="585" y="70" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">电容电压 vC(t)</text>
<line x1="430" y1="350" x2="758" y2="350" stroke="#64748b" stroke-width="2"/>
<line x1="430" y1="350" x2="430" y2="115" stroke="#64748b" stroke-width="2"/>
<text x="752" y="370" text-anchor="end" font-size="12" fill="#475569">t →</text>
<text x="420" y="120" text-anchor="end" font-size="12" fill="#475569">vC</text>
<line x1="430" y1="182" x2="755" y2="182" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="5,4"/>
<text x="425" y="186" text-anchor="end" font-size="12" fill="#475569">5V</text>
<line x1="494" y1="350" x2="494" y2="243" stroke="#b45309" stroke-width="1.5" stroke-dasharray="4,3" opacity="0">
 <animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.62;0.66;1" dur="{DUR}s" repeatCount="indefinite"/></line>
<line x1="430" y1="243" x2="494" y2="243" stroke="#b45309" stroke-width="1.5" stroke-dasharray="4,3" opacity="0">
 <animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.62;0.66;1" dur="{DUR}s" repeatCount="indefinite"/></line>
<text x="494" y="365" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309" opacity="0">τ=10ms
 <animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.62;0.66;1" dur="{DUR}s" repeatCount="indefinite"/></text>
<text x="425" y="247" text-anchor="end" font-size="12" font-weight="bold" fill="#b45309" opacity="0">63.2%
 <animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.62;0.66;1" dur="{DUR}s" repeatCount="indefinite"/></text>
{trace2(curve_d, DUR, color="#2563eb", plen=700)}
'''
    svg += caption("第 1 拍：刚合闸，桶是空的——电流最猛（粒子最密最快）", "#b45309", DUR,
                   "0;1;1;0;0", "0;0.05;0.28;0.32;1", y=400)
    svg += caption("第 2 拍：水位上涨反顶着电流——越充越慢（指数曲线）", "#2563eb", DUR,
                   "0;0;1;1;0;0", "0;0.32;0.36;0.60;0.64;1", y=400)
    svg += caption("第 3 拍：1τ 充到 63%，3τ 到 95%——τ 就是电路的「性格」", "#059669", DUR,
                   "0;0;1;1", "0;0.64;0.68;1", y=400)
    svg += note_box("τ = R×C：电阻大=水管细，电容大=水桶深，都让它更慢", 442, DUR, w=520)
    save('rc-charge.svg', svg + '</svg>')

# ======================= 图 2：桥式全波整流 =======================
def make_bridge_rectifier():
    D4 = 4
    pts = []
    for i in range(97):
        t = i/96*2*np.pi
        x = 60 + 680*i/96
        y = 452 - 42*abs(np.sin(t))
        pts.append(f"{x:.0f},{y:.0f}")
    abs_d = "M" + " L".join(pts)
    svg = svg_open('桥式全波整流：四只二极管接力，负半周也「翻上来」（1N4007）', h=560)
    svg += f'''
<text x="330" y="58" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">桥式整流电路</text>
<circle cx="60" cy="230" r="21" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="M49,230 q5.5,-14 11,0 q5.5,14 11,0" fill="none" stroke="#2563eb" stroke-width="2"/>
<text x="22" y="206" font-size="11.5" font-weight="bold" fill="#2563eb">AC 12V</text>
<line x1="81" y1="230" x2="90" y2="230" stroke="#334155" stroke-width="2.5"/>
<line x1="39" y1="230" x2="24" y2="230" stroke="#334155" stroke-width="2.5"/>
<line x1="24" y1="230" x2="24" y2="366" stroke="#334155" stroke-width="2.5"/>
<line x1="24" y1="366" x2="466" y2="366" stroke="#334155" stroke-width="2.5"/>
<line x1="466" y1="366" x2="466" y2="230" stroke="#334155" stroke-width="2.5"/>
<line x1="466" y1="230" x2="430" y2="230" stroke="#334155" stroke-width="2.5"/>
{diode_arm(90,230,260,120,'D1',140,150)}
{diode_arm(430,230,260,120,'D3',352,150)}
{diode_arm(260,340,90,230,'D2',128,302)}
{diode_arm(260,340,430,230,'D4',356,302)}
<line x1="260" y1="120" x2="260" y2="70" stroke="#334155" stroke-width="2.5"/>
<line x1="260" y1="70" x2="600" y2="70" stroke="#334155" stroke-width="2.5"/>
<line x1="260" y1="340" x2="600" y2="340" stroke="#334155" stroke-width="2.5"/>
<text x="272" y="64" font-size="14" font-weight="bold" fill="#059669">+</text>
<text x="272" y="344" font-size="14" font-weight="bold" fill="#dc2626">−</text>
<line x1="600" y1="70" x2="600" y2="100" stroke="#334155" stroke-width="2.5"/>
{resistor_v(600, 100, 56, '负载')}
<line x1="600" y1="156" x2="600" y2="340" stroke="#334155" stroke-width="2.5"/>
<text x="600" y="56" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#059669">电流方向永远不变！</text>
<line x1="600" y1="70" x2="680" y2="70" stroke="#334155" stroke-width="2.5"/>
<line x1="680" y1="70" x2="680" y2="112" stroke="#334155" stroke-width="2.5"/>
<line x1="650" y1="112" x2="710" y2="112" stroke="#334155" stroke-width="3"/>
<line x1="650" y1="128" x2="710" y2="128" stroke="#334155" stroke-width="3"/>
<line x1="680" y1="128" x2="680" y2="340" stroke="#334155" stroke-width="2.5"/>
<line x1="600" y1="340" x2="680" y2="340" stroke="#334155" stroke-width="2.5"/>
<text x="722" y="124" font-size="11.5" font-weight="bold" fill="#2563eb">C 滤波</text>
<text x="722" y="142" font-size="10" fill="#475569">（可选）</text>
<text x="96" y="190" font-size="14" font-weight="bold" fill="#059669" opacity="0">L +<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.48;0.52;1" dur="{D4}s" repeatCount="indefinite"/></text>
<text x="408" y="190" font-size="14" font-weight="bold" fill="#dc2626" opacity="0">− R<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.48;0.52;1" dur="{D4}s" repeatCount="indefinite"/></text>
<text x="96" y="190" font-size="14" font-weight="bold" fill="#dc2626" opacity="0">L −<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.48;0.52;1" dur="{D4}s" repeatCount="indefinite"/></text>
<text x="408" y="190" font-size="14" font-weight="bold" fill="#059669" opacity="0">+ R<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.48;0.52;1" dur="{D4}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.46;0.5;1" dur="{D4}s" repeatCount="indefinite"/>'
    svg += flow("M96,224 L252,130", D4/2, n=3, color="#059669", r=5)
    svg += flow("M264,66 H592 V334", D4/2, n=6, color="#059669", r=5)
    svg += flow("M264,344 L426,236", D4/2, n=3, color="#059669", r=5)
    svg += flow("M434,234 H462 V362", D4/2, n=3, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.5;0.54;1" dur="{D4}s" repeatCount="indefinite"/>'
    svg += flow("M424,224 L268,130", D4/2, n=3, color="#dc2626", r=5)
    svg += flow("M264,66 H592 V334", D4/2, n=6, color="#dc2626", r=5)
    svg += flow("M256,344 L94,236", D4/2, n=3, color="#dc2626", r=5)
    svg += flow("M86,234 H28 V362", D4/2, n=3, color="#dc2626", r=5) + '</g>'
    svg += f'''
<line x1="60" y1="452" x2="745" y2="452" stroke="#64748b" stroke-width="1.8"/>
<text x="740" y="474" text-anchor="end" font-size="11.5" fill="#475569">t →</text>
<path d="{sine_path(60, 740, 452, 42)}" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="6,4"/>
<text x="64" y="404" font-size="11.5" fill="#64748b">AC 输入（虚线）</text>
<path d="{abs_d}" fill="none" stroke="#2563eb" stroke-width="3.2"/>
<text x="400" y="404" font-size="11.5" font-weight="bold" fill="#2563eb">输出：脉动直流（实线）＝ |输入| − 1.4V</text>
'''
    svg += caption("① 正半周（L+ R−）：D1、D4 导通——绿路走一遍", "#059669", D4,
                   "0;1;1;0;0", "0;0.04;0.44;0.48;1", y=512)
    svg += caption("② 负半周（L− R+）：D2、D3 导通——走红路，负载电流方向不变！", "#dc2626", D4,
                   "0;0;1;1", "0;0.52;0.56;1", y=512)
    svg += note_box("代价：两只管压降 ≈1.4V · 纹波 = 2×市电 = 100Hz · 1N4007 耐压 1000V/1A", 546, D4,
                    "0;0.55;0.6;1", w=680)
    save('bridge-rectifier.svg', svg + '</svg>')

# ======================= 图 3：BJT 共射放大 =======================
# 参数自洽核算（2N2222，β=100 下限设计）：
#   IB = (12−0.7)/390k ≈ 29µA；IC = 100×29µA ≈ 2.9mA；VCE = 12 − 2.9mA×2k ≈ 6.2V
def make_bjt_amplify():
    D6 = 6
    vbe_d = sine_path(450, 750, 150, 15)
    vce_d = sine_path(450, 750, 330, 58, phase=np.pi)
    svg = svg_open('共射放大器：偏置先算准，放大才不翻车（2N2222, β=100）', h=500)
    svg += f'''
<text x="205" y="62" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">电路（固定偏置 · 可实搭）</text>
<text x="36" y="92" font-size="13" font-weight="bold" fill="#b45309">+12V</text>
<line x1="70" y1="86" x2="320" y2="86" stroke="#334155" stroke-width="2.5"/>
<line x1="180" y1="86" x2="180" y2="106" stroke="#334155" stroke-width="2.5"/>
<rect x="169" y="106" width="22" height="56" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="164" y="124" text-anchor="end" font-size="12.5" font-weight="bold" fill="#b45309">R<tspan baseline-shift="sub" font-size="9">B</tspan> 390kΩ</text>
<line x1="180" y1="162" x2="180" y2="210" stroke="#334155" stroke-width="2.5"/>
<circle cx="180" cy="210" r="3" fill="#334155"/>
<line x1="180" y1="210" x2="215" y2="210" stroke="#334155" stroke-width="2.5"/>
<line x1="300" y1="86" x2="300" y2="106" stroke="#334155" stroke-width="2.5"/>
<rect x="289" y="106" width="22" height="50" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="320" y="128" font-size="12.5" font-weight="bold" fill="#b45309">R<tspan baseline-shift="sub" font-size="9">C</tspan> 2kΩ</text>
<line x1="300" y1="156" x2="300" y2="175" stroke="#334155" stroke-width="2.5"/>
{npn_svg(300, 210)}
<line x1="300" y1="265" x2="300" y2="300" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(300, 314)}
<line x1="82" y1="210" x2="108" y2="210" stroke="#334155" stroke-width="2.5"/>
<line x1="108" y1="196" x2="108" y2="224" stroke="#334155" stroke-width="3"/>
<line x1="118" y1="196" x2="118" y2="224" stroke="#334155" stroke-width="3"/>
<line x1="118" y1="210" x2="180" y2="210" stroke="#334155" stroke-width="2.5"/>
<text x="113" y="192" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">C1 10µF</text>
<text x="113" y="240" text-anchor="middle" font-size="10.5" fill="#475569">隔直通交</text>
<circle cx="60" cy="210" r="21" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="M49,210 q5.5,-14 11,0 q5.5,14 11,0" fill="none" stroke="#2563eb" stroke-width="2"/>
<text x="66" y="252" font-size="11" font-weight="bold" fill="#2563eb">信号10mV</text>
<line x1="60" y1="231" x2="60" y2="300" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(60, 314)}
<line x1="300" y1="175" x2="366" y2="175" stroke="#334155" stroke-width="2.5"/>
<text x="322" y="168" font-size="12" font-weight="bold" fill="#2563eb">vCE 输出</text>
<text x="150" y="262" font-size="11.5" font-weight="bold" fill="#dc2626">I_B ≈ 29µA</text>
<text x="296" y="100" text-anchor="end" font-size="11.5" font-weight="bold" fill="#2563eb">I_C ≈ 2.9mA</text>
<text x="322" y="192" font-size="11.5" font-weight="bold" fill="#059669">V_CE ≈ 6.2V</text>
'''
    svg += flow("M74,82 H296 V300", D6, n=9, color="#2563eb", r=6)
    svg += flow("M180,92 V206 H212", D6, n=3, color="#dc2626", r=4.5)
    svg += f'''<g opacity="0"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.2;0.24;1" dur="{D6}s" repeatCount="indefinite"/>
<rect x="163" y="100" width="34" height="68" rx="6" fill="none" stroke="#f59e0b" stroke-width="3">
<animate attributeName="opacity" values="0.2;0.95;0.2" dur="1.1s" repeatCount="indefinite"/></rect></g>
<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.48;0.52;0.78;0.82;1" dur="{D6}s" repeatCount="indefinite"/>
<circle cx="288" cy="210" r="40" fill="none" stroke="#f59e0b" stroke-width="3">
<animate attributeName="opacity" values="0.2;0.95;0.2" dur="1.1s" repeatCount="indefinite"/></circle></g>
'''
    svg += f'''
<text x="600" y="62" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">波形对照（实测值核算）</text>
<text x="448" y="112" font-size="12" font-weight="bold" fill="#dc2626">基极：0.7V ± 10mV（小信号骑在偏置上）</text>
<line x1="440" y1="185" x2="760" y2="185" stroke="#64748b" stroke-width="1.8"/>
<line x1="440" y1="150" x2="760" y2="150" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,4"/>
<text x="755" y="146" text-anchor="end" font-size="10.5" fill="#475569">0.7V 偏置线</text>
<path d="{vbe_d}" fill="none" stroke="#dc2626" stroke-width="3"/>
<circle r="6" fill="#fff" stroke="#dc2626" stroke-width="3"><animateMotion dur="3s" repeatCount="indefinite" path="{vbe_d}"/></circle>
<text x="448" y="252" font-size="12" font-weight="bold" fill="#2563eb">集电极：6.2V ∓ 2V（≈200 倍 · 反相）</text>
<line x1="440" y1="400" x2="760" y2="400" stroke="#64748b" stroke-width="1.8"/>
<path d="{vce_d}" fill="none" stroke="#2563eb" stroke-width="3"/>
<circle r="6" fill="#fff" stroke="#2563eb" stroke-width="3"><animateMotion dur="3s" repeatCount="indefinite" path="{vce_d}"/></circle>
'''
    svg += caption("① 先偏置：R_B 从 12V 喂基流——没有偏置，信号再标准也放不出来", "#b45309", D6,
                   "0;1;1;0;0", "0;0.04;0.18;0.22;1", y=448)
    svg += caption("② 核算：I_B=(12−0.7)÷390k≈29µA → I_C=100×29µA≈2.9mA → V_CE=12−5.8≈6.2V", "#2563eb", D6,
                   "0;0;1;1;0;0", "0;0.22;0.26;0.44;0.48;1", y=448)
    svg += caption("③ 放大：基极 ±10mV → 集电极 ∓2V——约 200 倍，方向相反", "#dc2626", D6,
                   "0;0;1;1;0;0", "0;0.48;0.52;0.78;0.82;1", y=448)
    svg += caption("④ 能量全部来自 12V 电源——三极管是阀门，从不「创造」能量", "#059669", D6,
                   "0;0;1;1", "0;0.82;0.86;1", y=448)
    svg += note_box("2N2222 datasheet：hFE=75~300@10mA，设计时按 β=100 下限留余量", 486, D6, "0;0.9;0.94;1", w=640)
    save('bjt-amplify.svg', svg + '</svg>')

# ======================= 图 4：MOSFET 开关 =======================
# 参数：AO3400 VTH=1.45V(max)，3.3V 驱动可靠；LED 2V/20mA，R=(5−2)/20mA=150Ω
def make_mosfet_switch():
    D4 = 4
    vgs_d = square_path(430, 760, 120, 160)
    id_d = square_path(430, 760, 300, 360)
    svg = svg_open('MOSFET 开关：3.3V 单片机也能控制的「电压阀门」（AO3400）', h=470)
    svg += f'''
<text x="220" y="58" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">低边开关电路</text>
<text x="50" y="86" font-size="13" font-weight="bold" fill="#b45309">+5V</text>
<line x1="84" y1="80" x2="300" y2="80" stroke="#334155" stroke-width="2.5"/>
<line x1="300" y1="80" x2="300" y2="106" stroke="#334155" stroke-width="2.5"/>
<rect x="289" y="106" width="22" height="44" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="320" y="132" font-size="12" font-weight="bold" fill="#b45309">R 150Ω</text>
<line x1="300" y1="150" x2="300" y2="168" stroke="#334155" stroke-width="2.5"/>
<polygon points="300,196 288,172 312,172" fill="#334155"/>
<line x1="288" y1="196" x2="312" y2="196" stroke="#334155" stroke-width="3.5"/>
<line x1="300" y1="196" x2="300" y2="212" stroke="#334155" stroke-width="2.5"/>
<text x="322" y="186" font-size="12" font-weight="bold" fill="#dc2626">LED 2V</text>
<g stroke="#f59e0b" stroke-width="2.5" opacity="0">
<animate attributeName="opacity" values="0;0;0.3;1;1" keyTimes="0;0.5;0.56;0.75;1" dur="{D4}s" repeatCount="indefinite"/>
<line x1="312" y1="168" x2="328" y2="152"/><line x1="320" y1="176" x2="338" y2="162"/>
</g>
<line x1="300" y1="212" x2="300" y2="228" stroke="#334155" stroke-width="2.5"/>
<line x1="300" y1="228" x2="280" y2="228" stroke="#334155" stroke-width="2.5"/>
<line x1="280" y1="228" x2="280" y2="240" stroke="#334155" stroke-width="2.5"/>
<line x1="280" y1="254" x2="280" y2="266" stroke="#334155" stroke-width="2.5"/>
<line x1="280" y1="266" x2="300" y2="266" stroke="#334155" stroke-width="2.5"/>
<line x1="300" y1="266" x2="300" y2="300" stroke="#334155" stroke-width="2.5"/>
<line x1="272" y1="222" x2="272" y2="272" stroke="#94a3b8" stroke-width="3" stroke-dasharray="7,5">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.54;1" dur="{D4}s" repeatCount="indefinite"/></line>
<line x1="272" y1="222" x2="272" y2="272" stroke="#059669" stroke-width="4.5" opacity="0">
<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.5;0.54;1" dur="{D4}s" repeatCount="indefinite"/></line>
<line x1="260" y1="222" x2="260" y2="272" stroke="#334155" stroke-width="3"/>
<line x1="210" y1="247" x2="260" y2="247" stroke="#334155" stroke-width="2.5"/>
<polygon points="279,247 268,241 268,253" fill="#334155"/>
<text x="288" y="222" font-size="12.5" font-weight="bold" fill="#2563eb">D</text>
<text x="288" y="292" font-size="12.5" font-weight="bold" fill="#059669">S</text>
<text x="216" y="240" font-size="12.5" font-weight="bold" fill="#dc2626">G</text>
{gnd_sym(300, 314)}
<text x="312" y="262" font-size="11.5" font-weight="bold" fill="#475569">AO3400</text>
<rect x="90" y="228" width="66" height="38" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="123" y="251" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">MCU</text>
<line x1="156" y1="247" x2="210" y2="247" stroke="#334155" stroke-width="2.5"/>
<line x1="185" y1="247" x2="185" y2="270" stroke="#334155" stroke-width="2.5"/>
<rect x="174" y="270" width="22" height="36" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="146" y="292" font-size="11" font-weight="bold" fill="#b45309">10kΩ</text>
<line x1="185" y1="306" x2="185" y2="314" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(185, 328)}
<text x="120" y="352" font-size="10.5" fill="#475569">下拉防浮空</text>
<text x="360" y="290" font-size="12.5" font-weight="bold" fill="#dc2626" opacity="0">V_GS=0 &lt; V_TH=1.45V：沟道不存在<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.48;0.52;1" dur="{D4}s" repeatCount="indefinite"/></text>
<text x="360" y="290" font-size="12.5" font-weight="bold" fill="#059669" opacity="0">V_GS=3.3V &gt; V_TH：沟道打开，I_D=20mA<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.48;0.52;1" dur="{D4}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.5;0.56;1" dur="{D4}s" repeatCount="indefinite"/>'
    svg += flow("M88,76 H296 V306", D4/2, n=7, color="#2563eb", r=5.5) + '</g>'
    svg += f'''
<text x="595" y="58" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">栅压与漏流（同步）</text>
<text x="442" y="100" font-size="11.5" font-weight="bold" fill="#7c3aed">V_GS：0 / 3.3V</text>
<path d="{vgs_d}" fill="none" stroke="#7c3aed" stroke-width="3"/>
<line x1="430" y1="160" x2="762" y2="160" stroke="#64748b" stroke-width="1.5"/>
<text x="442" y="220" font-size="11.5" font-weight="bold" fill="#2563eb">I_D：0 / 20mA</text>
<path d="{id_d}" fill="none" stroke="#2563eb" stroke-width="3"/>
<line x1="430" y1="360" x2="762" y2="360" stroke="#64748b" stroke-width="1.5"/>
<line x1="430" y1="80" x2="430" y2="380" stroke="#f59e0b" stroke-width="2" opacity="0.8">
<animate attributeName="x1" values="430;760;430" keyTimes="0;0.99;1" dur="{D4}s" repeatCount="indefinite"/>
<animate attributeName="x2" values="430;760;430" keyTimes="0;0.99;1" dur="{D4}s" repeatCount="indefinite"/></line>
'''
    svg += caption("① 栅压 0V：沟道不存在，LED 灭——漏源之间是「断开的开关」", "#dc2626", D4,
                   "0;1;1;0;0", "0;0.04;0.44;0.5;1", y=410)
    svg += caption("② 栅压 3.3V > 阈值 1.45V：沟道形成，LED 亮，I_D=(5−2)÷150≈20mA", "#059669", D4,
                   "0;0;1;1", "0;0.52;0.58;1", y=410)
    svg += note_box("栅极只取 nA 级漏电——电压控制零功耗 · MCU 驱动必须选「逻辑电平」MOS（2N7000 在 3.3V 下不可靠）",
                    452, D4, "0;0.6;0.65;1", w=740, x=400)
    save('mosfet-switch.svg', svg + '</svg>')

# ======================= 图 5：运放反相放大 =======================
# 参数：Rin=1kΩ Rf=10kΩ → 增益 −10；vin ±0.5V → vout ∓5V（±12V 电源内，不饱和）
def make_opamp_inverting():
    D5 = 5
    vin_d = sine_path(60, 390, 350, 30)
    vout_d = sine_path(430, 770, 350, 55, phase=np.pi)
    svg = svg_open('运放反相放大器：「虚短虚断」是怎么回事（增益 = −Rf/Rin）', h=480)
    svg += f'''
<text x="300" y="58" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">反相放大电路（LM358，±12V 供电）</text>
<circle cx="90" cy="180" r="21" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="M79,180 q5.5,-14 11,0 q5.5,14 11,0" fill="none" stroke="#2563eb" stroke-width="2"/>
<text x="42" y="152" font-size="11.5" font-weight="bold" fill="#2563eb">vin ±0.5V</text>
<line x1="111" y1="180" x2="170" y2="180" stroke="#334155" stroke-width="2.5"/>
<line x1="90" y1="201" x2="90" y2="250" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(90, 264)}
{resistor_h(190, 180, 56, 'Rin 1kΩ')}
<line x1="266" y1="180" x2="330" y2="180" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="180" r="4" fill="#334155"/>
<line x1="330" y1="180" x2="480" y2="180" stroke="#334155" stroke-width="2.5"/>
<polygon points="480,158 480,242 566,200" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="492" y="186" font-size="15" font-weight="bold" fill="#dc2626">−</text>
<text x="492" y="228" font-size="15" font-weight="bold" fill="#059669">+</text>
<text x="500" y="262" font-size="11.5" fill="#475569">LM358</text>
<line x1="440" y1="220" x2="480" y2="220" stroke="#334155" stroke-width="2.5"/>
<line x1="440" y1="220" x2="440" y2="252" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(440, 266)}
<line x1="330" y1="180" x2="330" y2="140" stroke="#334155" stroke-width="2.5"/>
{resistor_h(350, 140, 80, 'Rf 10kΩ')}
<line x1="450" y1="140" x2="566" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="566" y1="140" x2="566" y2="200" stroke="#334155" stroke-width="2.5"/>
<line x1="566" y1="200" x2="630" y2="200" stroke="#334155" stroke-width="2.5"/>
<text x="640" y="205" font-size="13" font-weight="bold" fill="#dc2626">vout ∓5V</text>
<circle cx="330" cy="180" r="9" fill="none" stroke="#dc2626" stroke-width="2.5">
<animate attributeName="opacity" values="0.25;1;0.25" dur="1.4s" repeatCount="indefinite"/></circle>
<text x="300" y="216" font-size="12" font-weight="bold" fill="#dc2626">虚地 v− ≈ 0V</text>
<text x="390" y="108" text-anchor="middle" font-size="11.5" fill="#475569">i 全部走 Rf（运放不取流）</text>
'''
    svg += flow("M95,176 H326 V144 H562 V194", D5, n=6, color="#f59e0b", r=5)
    svg += f'''
<line x1="60" y1="350" x2="392" y2="350" stroke="#64748b" stroke-width="1.6"/>
<path d="{vin_d}" fill="none" stroke="#2563eb" stroke-width="3"/>
<text x="64" y="306" font-size="11.5" font-weight="bold" fill="#2563eb">输入 vin = ±0.5V</text>
<circle r="5.5" fill="#fff" stroke="#2563eb" stroke-width="3"><animateMotion dur="2.5s" repeatCount="indefinite" path="{vin_d}"/></circle>
<line x1="430" y1="350" x2="772" y2="350" stroke="#64748b" stroke-width="1.6"/>
<path d="{vout_d}" fill="none" stroke="#dc2626" stroke-width="3"/>
<text x="434" y="286" font-size="11.5" font-weight="bold" fill="#dc2626">输出 vout = ∓5V（反相 ×10）</text>
<circle r="5.5" fill="#fff" stroke="#dc2626" stroke-width="3"><animateMotion dur="2.5s" repeatCount="indefinite" path="{vout_d}"/></circle>
'''
    svg += caption("① 虚断：运放输入端取流≈0——i_in 没地方去，只能全部流向 Rf", "#b45309", D5,
                   "0;1;1;0;0", "0;0.04;0.2;0.24;1", y=418)
    svg += caption("② 虚短：负反馈强迫 v−≈v+=0V——v− 被钉在地上（虚地）", "#dc2626", D5,
                   "0;0;1;1;0;0", "0;0.24;0.28;0.48;0.52;1", y=418)
    svg += caption("③ 增益 = −Rf/Rin = −10k/1k = −10：只看两只电阻，与运放型号几乎无关", "#2563eb", D5,
                   "0;0;1;1;0;0", "0;0.52;0.56;0.76;0.8;1", y=418)
    svg += caption("④ 本质：输出反过来「喂」输入端——负反馈让电路自己纠错", "#059669", D5,
                   "0;0;1;1", "0;0.8;0.84;1", y=418)
    svg += note_box("i = vin/Rin → vout = −i·Rf → vout = −vin·(Rf/Rin)：两条虚字规则推完整个电路", 462, D5,
                    "0;0.86;0.9;1", w=700)
    save('opamp-inverting.svg', svg + '</svg>')

# ======================= 图 6：比较器迟滞 =======================
# 参数：LM393 开集电极+4.7k 上拉；R1=R2=10k 分压 2.5V；R3=1MΩ 正反馈 → 窗口≈1V
def make_comparator_hysteresis():
    D5 = 5
    svg = svg_open('比较器迟滞：正反馈造出 1V「免疫区」（LM393，R1=R2=10k）', h=470)
    svg += f'''
<text x="230" y="58" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">带迟滞的比较器电路</text>
<text x="56" y="86" font-size="13" font-weight="bold" fill="#b45309">+5V</text>
<line x1="90" y1="80" x2="340" y2="80" stroke="#334155" stroke-width="2.5"/>
<line x1="120" y1="80" x2="120" y2="100" stroke="#334155" stroke-width="2.5"/>
{resistor_v(120, 100, 40, 'R1 10k')}
<line x1="120" y1="140" x2="120" y2="166" stroke="#334155" stroke-width="2.5"/>
<circle cx="120" cy="166" r="3.5" fill="#334155"/>
<line x1="120" y1="166" x2="120" y2="186" stroke="#334155" stroke-width="2.5"/>
{resistor_v(120, 186, 40, 'R2 10k')}
<line x1="120" y1="226" x2="120" y2="246" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(120, 260)}
<text x="128" y="158" font-size="11" font-weight="bold" fill="#7c3aed">2.5V</text>
<line x1="120" y1="166" x2="260" y2="166" stroke="#334155" stroke-width="2.5"/>
<polygon points="260,148 260,232 336,190" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="270" y="174" font-size="14" font-weight="bold" fill="#dc2626">−</text>
<text x="270" y="216" font-size="14" font-weight="bold" fill="#059669">+</text>
<text x="272" y="252" font-size="11" fill="#475569">LM393</text>
<circle cx="80" cy="290" r="18" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="M71,290 q4.5,-12 9,0 q4.5,12 9,0" fill="none" stroke="#2563eb" stroke-width="2"/>
<text x="30" y="322" font-size="10.5" font-weight="bold" fill="#2563eb">带噪信号</text>
{resistor_h(110, 290, 56)}
<text x="138" y="322" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">Rin 200k</text>
<line x1="186" y1="290" x2="260" y2="290" stroke="#334155" stroke-width="2.5"/>
<line x1="260" y1="290" x2="260" y2="216" stroke="#334155" stroke-width="2.5"/>
<circle cx="200" cy="290" r="3.5" fill="#334155"/>
<line x1="80" y1="308" x2="80" y2="330" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(80, 344)}
<line x1="310" y1="80" x2="310" y2="100" stroke="#334155" stroke-width="2.5"/>
{resistor_v(310, 100, 36, '4.7k')}
<line x1="310" y1="136" x2="310" y2="190" stroke="#334155" stroke-width="2.5"/>
<circle cx="310" cy="190" r="3.5" fill="#334155"/>
<line x1="310" y1="190" x2="336" y2="190" stroke="#334155" stroke-width="2.5"/>
<line x1="336" y1="190" x2="370" y2="190" stroke="#334155" stroke-width="2.5"/>
<text x="342" y="180" font-size="12" font-weight="bold" fill="#059669">OUT</text>
<line x1="350" y1="190" x2="350" y2="318" stroke="#334155" stroke-width="2.5"/>
<line x1="350" y1="318" x2="296" y2="318" stroke="#334155" stroke-width="2.5"/>
<rect x="240" y="307" width="56" height="22" fill="#f8fafc" stroke="#b45309" stroke-width="2.5"/>
<text x="268" y="301" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">R3 1MΩ</text>
<line x1="240" y1="318" x2="200" y2="318" stroke="#334155" stroke-width="2.5"/>
<line x1="200" y1="318" x2="200" y2="290" stroke="#334155" stroke-width="2.5"/>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{D5}s" begin="-0.2s" repeatCount="indefinite" path="M350,190 L350,318 L296,318"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{D5}s" begin="-0.7s" repeatCount="indefinite" path="M240,318 L200,318 L200,290"/></circle>
<circle r="4" fill="#f59e0b"><animateMotion dur="{D5}s" begin="-1.2s" repeatCount="indefinite" path="M200,290 L260,290 L260,216"/></circle>
<circle cx="622" cy="300" r="5" fill="none" stroke="#059669" stroke-width="2.5">
<animate attributeName="r" values="5;11;5" dur="1.3s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.9;0.2;0.9" dur="1.3s" repeatCount="indefinite"/></circle>
<circle cx="558" cy="130" r="5" fill="none" stroke="#dc2626" stroke-width="2.5">
<animate attributeName="r" values="5;11;5" dur="1.3s" begin="0.65s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.9;0.2;0.9" dur="1.3s" begin="0.65s" repeatCount="indefinite"/></circle>
<text x="252" y="346" font-size="11" fill="#475569">正反馈：输出「拽」输入</text>
<text x="590" y="58" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">传输特性：回滞环</text>
<line x1="440" y1="300" x2="760" y2="300" stroke="#64748b" stroke-width="2"/>
<line x1="440" y1="300" x2="440" y2="110" stroke="#64748b" stroke-width="2"/>
<text x="755" y="342" text-anchor="end" font-size="11.5" fill="#475569">vin →</text>
<text x="434" y="106" text-anchor="end" font-size="11.5" fill="#475569">vout</text>
<text x="433" y="134" text-anchor="end" font-size="11" fill="#475569">5V</text>
<text x="433" y="304" text-anchor="end" font-size="11" fill="#475569">0V</text>
<text x="622" y="318" text-anchor="middle" font-size="11" font-weight="bold" fill="#059669">3V</text>
<text x="558" y="318" text-anchor="middle" font-size="11" font-weight="bold" fill="#dc2626">2V</text>
<text x="744" y="318" text-anchor="middle" font-size="11" fill="#475569">5V</text>
<path d="M440,300 H622" stroke="#2563eb" stroke-width="3.5" fill="none"/>
<path d="M558,130 H755" stroke="#2563eb" stroke-width="3.5" fill="none"/>
<line x1="622" y1="300" x2="622" y2="130" stroke="#059669" stroke-width="3" stroke-dasharray="6,4">
<animate attributeName="opacity" values="0.35;1;0.35" dur="1.3s" repeatCount="indefinite"/></line>
<line x1="558" y1="130" x2="558" y2="300" stroke="#dc2626" stroke-width="3" stroke-dasharray="6,4">
<animate attributeName="opacity" values="0.35;1;0.35" dur="1.3s" begin="0.65s" repeatCount="indefinite"/></line>
<path d="M616,142 L622,130 L628,142" stroke="#059669" stroke-width="2.5" fill="none"/>
<path d="M552,288 L558,300 L564,288" stroke="#dc2626" stroke-width="2.5" fill="none"/>
<text x="636" y="122" font-size="11" font-weight="bold" fill="#059669">升到 3V 才跳高</text>
<text x="452" y="122" font-size="11" font-weight="bold" fill="#dc2626">降到 2V 才跳低</text>
<text x="590" y="245" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#7c3aed">1V 免疫区</text>
<line x1="558" y1="255" x2="622" y2="255" stroke="#7c3aed" stroke-width="1.5"/>
<path d="M558,251 L558,259 M622,251 L622,259" stroke="#7c3aed" stroke-width="1.5"/>
<circle cx="450" cy="330" r="8" fill="#f59e0b" stroke="#b45309" stroke-width="2.5">
<animate attributeName="cx" values="450;745;450" keyTimes="0;0.5;1" dur="{D5}s" repeatCount="indefinite"/></circle>
<circle cx="772" cy="300" r="8" fill="#dc2626">
<animate attributeName="cy" values="300;300;130;130;300;300" keyTimes="0;0.385;0.415;0.885;0.915;1" dur="{D5}s" repeatCount="indefinite"/>
<animate attributeName="fill" values="#dc2626;#dc2626;#059669;#059669;#dc2626;#dc2626" keyTimes="0;0.385;0.415;0.885;0.915;1" dur="{D5}s" repeatCount="indefinite"/></circle>
<text x="764" y="352" font-size="10.5" fill="#475569">OUT</text>
'''
    svg += caption("① 基准 2.5V；R3 把输出状态「拽」回 IN+——阈值随输出而变", "#b45309", D5,
                   "0;1;1;0;0", "0;0.04;0.2;0.24;1", y=400)
    svg += caption("② 输出低时阈值被抬到 3V：输入必须升过 3V 才翻转", "#059669", D5,
                   "0;0;1;1;0;0", "0;0.24;0.28;0.5;0.54;1", y=400)
    svg += caption("③ 输出高时阈值被压到 2V：输入必须跌破 2V 才翻回", "#dc2626", D5,
                   "0;0;1;1;0;0", "0;0.54;0.58;0.78;0.82;1", y=400)
    svg += caption("④ 噪声在 1V 窗口里随便闹——输出纹丝不动", "#2563eb", D5,
                   "0;0;1;1", "0;0.82;0.86;1", y=400)
    svg += note_box("窗口 ≈ (Rin÷R3)·(VOH−VOL) · LM393 开集电极输出必须接上拉电阻 4.7kΩ", 448, D5,
                    "0;0.88;0.92;1", w=620)
    save('comparator-hysteresis.svg', svg + '</svg>')

# ======================= 图 7：555 无稳态振荡 =======================
# 参数：R1=R2=10kΩ, C=10µF → f=1.44/((R1+2R2)C)≈4.8Hz，占空比 66.7%
def make_ne555_astable():
    D6 = 6
    cap_d = tri_cap(60, 380, 440, 400)
    out_d = sq_out(430, 750, 400, 440)
    svg = svg_open('555 无稳态振荡：内部三块拼图，外面三只元件（R1=R2=10k, C=10µF）', h=560)
    svg += f'''
<text x="34" y="66" font-size="13" font-weight="bold" fill="#b45309">+9V</text>
<line x1="70" y1="60" x2="560" y2="60" stroke="#334155" stroke-width="2.5"/>
<rect x="60" y="110" width="280" height="200" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5"/>
<text x="200" y="132" text-anchor="middle" font-size="14" font-weight="bold" fill="#2563eb">NE555</text>
<line x1="100" y1="110" x2="100" y2="140" stroke="#64748b" stroke-width="2"/>
<rect x="92" y="140" width="16" height="40" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>
<rect x="92" y="180" width="16" height="40" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>
<rect x="92" y="220" width="16" height="40" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>
<line x1="100" y1="260" x2="100" y2="290" stroke="#64748b" stroke-width="2"/>
<text x="62" y="152" font-size="9.5" fill="#475569">5k×3</text>
<text x="116" y="184" font-size="10" font-weight="bold" fill="#7c3aed">2/3=6V</text>
<text x="116" y="244" font-size="10" font-weight="bold" fill="#7c3aed">1/3=3V</text>
<polygon points="170,165 170,195 194,180" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<polygon points="170,225 170,255 194,240" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="170" y="158" font-size="9.5" fill="#475569">THRES</text>
<text x="172" y="272" font-size="9.5" fill="#475569">TRIG</text>
<rect x="220" y="185" width="66" height="60" rx="6" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="253" y="220" text-anchor="middle" font-size="11" font-weight="bold" fill="#334155">RS</text>
<line x1="194" y1="180" x2="220" y2="198" stroke="#334155" stroke-width="1.8"/>
<line x1="194" y1="240" x2="220" y2="228" stroke="#334155" stroke-width="1.8"/>
<line x1="320" y1="150" x2="320" y2="290" stroke="#334155" stroke-width="1.8"/>
<line x1="320" y1="220" x2="306" y2="206" stroke="#dc2626" stroke-width="2.5">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.66;0.7;1" dur="{D6}s" repeatCount="indefinite"/></line>
<line x1="320" y1="220" x2="306" y2="220" stroke="#059669" stroke-width="2.5" opacity="0">
<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.66;0.7;1" dur="{D6}s" repeatCount="indefinite"/></line>
<circle cx="320" cy="220" r="3" fill="#334155"/>
<text x="286" y="302" font-size="9.5" fill="#475569">放电管</text>
<line x1="286" y1="215" x2="380" y2="215" stroke="#334155" stroke-width="2.5"/>
<text x="346" y="208" font-size="11" font-weight="bold" fill="#059669">3 OUT</text>
<line x1="200" y1="60" x2="200" y2="110" stroke="#334155" stroke-width="2.5"/>
<text x="208" y="82" font-size="10" fill="#475569">8/4 VCC</text>
<line x1="120" y1="310" x2="120" y2="330" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(120, 344)}
<text x="96" y="326" font-size="10" fill="#475569">1</text>
<line x1="340" y1="150" x2="400" y2="150" stroke="#334155" stroke-width="2.5"/>
<text x="346" y="142" font-size="10" fill="#475569">7 DISCH</text>
<circle cx="400" cy="150" r="4" fill="#334155"/>
<line x1="340" y1="250" x2="400" y2="250" stroke="#334155" stroke-width="2.5"/>
<text x="346" y="242" font-size="10" fill="#475569">6/2</text>
<circle cx="400" cy="250" r="4" fill="#334155"/>
<line x1="400" y1="60" x2="400" y2="80" stroke="#334155" stroke-width="2.5"/>
{resistor_v(400, 80, 56, 'R1 10k')}
<line x1="400" y1="136" x2="400" y2="170" stroke="#334155" stroke-width="2.5"/>
{resistor_v(400, 170, 56, 'R2 10k')}
<line x1="400" y1="226" x2="400" y2="250" stroke="#334155" stroke-width="2.5"/>
<line x1="400" y1="250" x2="460" y2="250" stroke="#334155" stroke-width="2.5"/>
<line x1="460" y1="250" x2="460" y2="270" stroke="#334155" stroke-width="2.5"/>
<line x1="430" y1="270" x2="490" y2="270" stroke="#334155" stroke-width="3"/>
<line x1="430" y1="286" x2="490" y2="286" stroke="#334155" stroke-width="3"/>
<line x1="460" y1="286" x2="460" y2="320" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(460, 334)}
<text x="500" y="284" font-size="12" font-weight="bold" fill="#2563eb">C 10µF</text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.62;0.66;1" dur="{D6}s" repeatCount="indefinite"/>'
    svg += flow("M404,56 V246 H456 V266", D6*0.62, n=5, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.66;0.7;1" dur="{D6}s" repeatCount="indefinite"/>'
    svg += flow("M456,288 H404 V154 H344", D6*0.3, n=4, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="64" y="384" font-size="11" font-weight="bold" fill="#7c3aed">电容电压：3V ↔ 6V 三角波</text>
<path d="{cap_d}" fill="none" stroke="#7c3aed" stroke-width="3"/>
<line x1="60" y1="400" x2="382" y2="400" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="60" y1="440" x2="382" y2="440" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="386" y="404" font-size="10" fill="#7c3aed">6V</text>
<text x="386" y="444" font-size="10" fill="#7c3aed">3V</text>
<text x="434" y="384" font-size="11" font-weight="bold" fill="#059669">OUT 方波（充电=高，放电=低）</text>
<path d="{out_d}" fill="none" stroke="#059669" stroke-width="3"/>
<line x1="430" y1="440" x2="752" y2="440" stroke="#64748b" stroke-width="1.5"/>
'''
    svg += caption("① 充电（绿）：电流经 R1+R2 给电容充值 → 到 6V 时 THRES 比较器翻转", "#059669", D6,
                   "0;1;1;0;0", "0;0.05;0.58;0.64;1", y=486)
    svg += caption("② 放电（红）：放电管导通，电容经 R2 从 7 脚泄放 → 到 3V 时 TRIG 翻转", "#dc2626", D6,
                   "0;0;1;1", "0;0.68;0.74;1", y=486)
    svg += note_box("f = 1.44÷((R1+2R2)·C) ≈ 4.8Hz，占空比 66% · 三个 5kΩ 分压电阻正是「555」名字的由来",
                    534, D6, "0;0.76;0.8;1", w=720)
    save('ne555-astable.svg', svg + '</svg>')

# ======================= 图 8：推挽 vs 开漏 =======================
def make_pushpull_opendrain():
    DP = 4
    rc_pts = []
    for i in range(41):
        u = i/40
        x = 380 + 180*u
        y = 380 - 50*(1-np.exp(-3*u))
        rc_pts.append(f"{x:.0f},{y:.0f}")
    rc_edge = "M" + " L".join(rc_pts)
    svg = svg_open('推挽 vs 开漏：为什么 I2C 偏偏选「慢」的那个？', h=460)
    svg += f'''
<text x="200" y="62" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">推挽：两个开关轮流推</text>
<text x="56" y="76" font-size="12.5" font-weight="bold" fill="#b45309">VDD</text>
<line x1="90" y1="70" x2="200" y2="70" stroke="#334155" stroke-width="2.5"/>
<line x1="200" y1="70" x2="200" y2="92" stroke="#334155" stroke-width="2.5"/>
<circle cx="200" cy="96" r="3.5" fill="#334155"/>
<line x1="200" y1="96" x2="226" y2="122" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0;0;1;1" keyTimes="0;0.22;0.26;0.72;0.76;0.98;1" dur="{DP}s" repeatCount="indefinite"/></line>
<circle cx="200" cy="126" r="3.5" fill="#334155"/>
<text x="232" y="106" font-size="11" font-weight="bold" fill="#059669">上管（推高）</text>
<line x1="200" y1="126" x2="200" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="200" cy="150" r="4" fill="#334155"/>
<line x1="200" y1="150" x2="330" y2="150" stroke="#334155" stroke-width="2.5"/>
<text x="336" y="146" font-size="12" font-weight="bold" fill="#2563eb">OUT</text>
<line x1="200" y1="150" x2="200" y2="174" stroke="#334155" stroke-width="2.5"/>
<circle cx="200" cy="174" r="3.5" fill="#334155"/>
<line x1="200" y1="174" x2="226" y2="200" stroke="#dc2626" stroke-width="3">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.24;0.28;0.7;0.74;1" dur="{DP}s" repeatCount="indefinite"/></line>
<circle cx="200" cy="204" r="3.5" fill="#334155"/>
<text x="232" y="196" font-size="11" font-weight="bold" fill="#dc2626">下管（拉低）</text>
<line x1="200" y1="204" x2="200" y2="230" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(200, 244)}
<text x="120" y="270" font-size="11" fill="#475569">两管交替导通：双向都有劲</text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.22;0.26;1" dur="{DP}s" repeatCount="indefinite"/>'
    svg += flow("M94,66 H196 V146 H326", DP/4, n=6, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.26;0.3;0.68;0.72;1" dur="{DP}s" repeatCount="indefinite"/>'
    svg += flow("M326,146 H204 V236", DP/4, n=6, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="590" y="62" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">开漏：只有下管，靠电阻回高</text>
<text x="446" y="76" font-size="12.5" font-weight="bold" fill="#b45309">VDD</text>
<line x1="480" y1="70" x2="560" y2="70" stroke="#334155" stroke-width="2.5"/>
{resistor_v(560, 90, 50, '上拉 Rp')}
<line x1="560" y1="140" x2="560" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="560" cy="150" r="4" fill="#334155"/>
<line x1="560" y1="150" x2="700" y2="150" stroke="#334155" stroke-width="2.5"/>
<text x="706" y="146" font-size="12" font-weight="bold" fill="#2563eb">OUT</text>
<line x1="560" y1="150" x2="560" y2="174" stroke="#334155" stroke-width="2.5"/>
<circle cx="560" cy="174" r="3.5" fill="#334155"/>
<line x1="560" y1="174" x2="586" y2="200" stroke="#dc2626" stroke-width="3">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.24;0.28;0.7;0.74;1" dur="{DP}s" repeatCount="indefinite"/></line>
<circle cx="560" cy="204" r="3.5" fill="#334155"/>
<text x="592" y="196" font-size="11" font-weight="bold" fill="#dc2626">下管（唯一开关）</text>
<line x1="560" y1="204" x2="560" y2="230" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(560, 244)}
<text x="480" y="270" font-size="11" fill="#475569">下管断开时：Rp 慢慢把总线「充」回高电平</text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.22;0.26;1" dur="{DP}s" repeatCount="indefinite"/>'
    svg += flow("M484,66 H556 V146 H696", DP/2, n=3, color="#b45309", r=5, keypoints="0;0.55;0.82;1", keytimes="0;0.2;0.5;1") + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.26;0.3;0.68;0.72;1" dur="{DP}s" repeatCount="indefinite"/>'
    svg += flow("M696,146 H564 V236", DP/4, n=6, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="64" y="316" font-size="11.5" font-weight="bold" fill="#059669">推挽沿：陡（ns 级）</text>
<path d="M80,380 V330 H180 V380" fill="none" stroke="#059669" stroke-width="3"/>
<line x1="80" y1="380" x2="270" y2="380" stroke="#64748b" stroke-width="1.5"/>
<text x="360" y="316" font-size="11.5" font-weight="bold" fill="#b45309">开漏沿：RC 缓升（上拉×总线电容）</text>
<path d="{rc_edge}" fill="none" stroke="#b45309" stroke-width="3"/>
<line x1="380" y1="380" x2="580" y2="380" stroke="#64748b" stroke-width="1.5"/>
<text x="600" y="355" font-size="11" fill="#475569">I2C 上拉 2.2~4.7kΩ：阻小快但费电</text>
'''
    svg += caption("① 推挽输出高：上管合上，VDD 直推——又快又有劲（粒子密集）", "#059669", DP,
                   "0;1;1;0;0", "0;0.03;0.2;0.24;1", y=410)
    svg += caption("② 开漏输出高：只能靠上拉电阻慢慢充电——沿是 RC 曲线（粒子稀疏）", "#b45309", DP,
                   "0;0;1;1;0;0", "0;0.24;0.28;0.46;0.5;1", y=410)
    svg += caption("③ 那为什么 I2C 还选开漏？——多设备共享总线时，两个推挽互怼=短路烧IO！", "#dc2626", DP,
                   "0;0;1;1", "0;0.52;0.56;1", y=410)
    svg += note_box("开漏+上拉=「线与」：任何一个设备都能拉低总线——仲裁、中断共享、电平转换全靠它", 448, DP, "0;0.6;0.65;1", w=700)
    save('pushpull-opendrain.svg', svg + '</svg>')

# ======================= 图 9：LDO 负反馈 =======================
def make_ldo_feedback():
    DL = 5
    t_pts = []
    for i in range(81):
        u = i/80
        x = 60 + 320*u
        if u < 0.3:
            y = 340
        else:
            du = u - 0.3
            y = 340 + 26*np.exp(-du*6)*np.cos(du*22) - 6*np.exp(-du*4)
        t_pts.append(f"{x:.0f},{y:.1f}")
    fb_d = "M" + " L".join(t_pts)
    ol_pts = []
    for i in range(81):
        u = i/80
        x = 420 + 320*u
        y = 340 if u < 0.3 else 340 + 22*(1-np.exp(-(u-0.3)*9))
        ol_pts.append(f"{x:.0f},{y:.1f}")
    ol_d = "M" + " L".join(ol_pts)
    svg = svg_open('LDO 的本质：一个会「自我调节」的分压器（负反馈环路）', h=470)
    svg += f'''
<text x="330" y="62" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">LDO 内部负反馈环路（AMS1117 同款结构）</text>
<text x="96" y="96" text-anchor="end" font-size="13" font-weight="bold" fill="#b45309">VIN 8V</text>
<line x1="100" y1="90" x2="180" y2="90" stroke="#334155" stroke-width="2.5"/>
<rect x="180" y="78" width="80" height="26" fill="#fffbeb" stroke="#b45309" stroke-width="2.5"/>
<text x="220" y="95" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">调整管</text>
<text x="216" y="118" text-anchor="end" font-size="10" fill="#475569">≈ 自动可变电阻</text>
<line x1="260" y1="90" x2="330" y2="90" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="90" r="4" fill="#334155"/>
<line x1="330" y1="90" x2="400" y2="90" stroke="#334155" stroke-width="2.5"/>
<text x="408" y="95" font-size="13" font-weight="bold" fill="#059669">VOUT 5V</text>
{resistor_v(400, 110, 46, '负载')}
<line x1="400" y1="156" x2="400" y2="186" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(400, 200)}
<line x1="350" y1="90" x2="350" y2="130" stroke="#334155" stroke-width="2" stroke-dasharray="4,3"/>
<circle cx="350" cy="130" r="3" fill="#334155"/>
<line x1="350" y1="130" x2="368" y2="148" stroke="#dc2626" stroke-width="2.5">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.28;0.32;1" dur="{DL}s" repeatCount="indefinite"/></line>
<circle cx="350" cy="152" r="3" fill="#334155"/>
{resistor_v(350, 166, 34, '突加')}
<line x1="350" y1="200" x2="350" y2="214" stroke="#334155" stroke-width="2"/>
{gnd_sym(350, 228)}
<text x="356" y="84" font-size="10" fill="#dc2626" text-anchor="middle">30%处加重</text>
<line x1="330" y1="90" x2="330" y2="130" stroke="#334155" stroke-width="2.5"/>
{resistor_v(330, 130, 34, '')}
<text x="318" y="151" text-anchor="end" font-size="12.5" font-weight="bold" fill="#b45309">R1</text>
<circle cx="330" cy="186" r="3.5" fill="#334155"/>
<line x1="330" y1="164" x2="330" y2="206" stroke="#334155" stroke-width="2.5"/>
{resistor_v(330, 206, 34, '')}
<text x="318" y="227" text-anchor="end" font-size="12.5" font-weight="bold" fill="#b45309">R2</text>
<line x1="330" y1="240" x2="330" y2="252" stroke="#334155" stroke-width="2"/>
{gnd_sym(330, 266)}
<polygon points="180,170 180,222 240,196" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="188" y="196" font-size="13" font-weight="bold" fill="#dc2626">−</text>
<text x="188" y="216" font-size="13" font-weight="bold" fill="#059669">+</text>
<text x="150" y="164" font-size="10.5" fill="#475569">误差放大器</text>
<line x1="296" y1="90" x2="296" y2="112" stroke="#334155" stroke-width="2.5"/>
<line x1="282" y1="118" x2="310" y2="118" stroke="#2563eb" stroke-width="3"/>
<line x1="282" y1="128" x2="310" y2="128" stroke="#2563eb" stroke-width="3"/>
<line x1="296" y1="128" x2="296" y2="150" stroke="#334155" stroke-width="2"/>
{gnd_sym(296, 164)}
<text x="292" y="142" text-anchor="end" font-size="10.5" fill="#2563eb">C_out</text>
<line x1="330" y1="186" x2="300" y2="186" stroke="#334155" stroke-width="2"/>
<line x1="300" y1="186" x2="300" y2="270" stroke="#334155" stroke-width="2"/>
<line x1="300" y1="270" x2="140" y2="270" stroke="#334155" stroke-width="2"/>
<line x1="140" y1="270" x2="140" y2="191" stroke="#334155" stroke-width="2"/>
<line x1="140" y1="191" x2="180" y2="191" stroke="#334155" stroke-width="2"/>
<text x="216" y="283" font-size="10" fill="#7c3aed">采样 1.25V</text>
<rect x="150" y="230" width="70" height="24" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="185" y="246" text-anchor="middle" font-size="11" font-weight="bold" fill="#2563eb">基准 1.25V</text>
<line x1="185" y1="230" x2="185" y2="222" stroke="#334155" stroke-width="2"/>
<line x1="185" y1="222" x2="180" y2="222" stroke="#334155" stroke-width="2"/>
<line x1="240" y1="196" x2="220" y2="196" stroke="#334155" stroke-width="2"/>
<line x1="220" y1="196" x2="220" y2="104" stroke="#334155" stroke-width="2"/>
<text x="226" y="152" font-size="10" fill="#475569">驱动</text>
<path d="M120,240 C80,240 80,120 130,104" fill="none" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,4">
<animate attributeName="opacity" values="0.3;1;0.3" dur="1.6s" repeatCount="indefinite"/></path>
<text x="70" y="180" font-size="10.5" font-weight="bold" fill="#7c3aed">反馈环</text>
'''
    svg += f'''
<text x="64" y="300" font-size="11.5" font-weight="bold" fill="#059669">有反馈：跌落→拉回（振铃后稳定）</text>
<path d="{fb_d}" fill="none" stroke="#059669" stroke-width="3"/>
<circle cx="60" cy="340" r="5.5" fill="#fff" stroke="#059669" stroke-width="3">{linear_x_motion(DL, fb_d)}</circle>
<line x1="60" y1="340" x2="384" y2="340" stroke="#64748b" stroke-width="1.5"/>
<line x1="156" y1="320" x2="156" y2="366" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="424" y="300" font-size="11.5" font-weight="bold" fill="#dc2626">若无反馈：一跌不起（负载调整率灾难）</text>
<path d="{ol_d}" fill="none" stroke="#dc2626" stroke-width="3"/>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DL}s" begin="-0.3s" repeatCount="indefinite" path="M102,90 L178,90"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DL}s" begin="-0.8s" repeatCount="indefinite" path="M332,90 L400,90 L400,108"/></circle>
<circle r="4.5" fill="#059669"><animateMotion dur="{DL}s" begin="-1.3s" repeatCount="indefinite" path="M400,158 L400,174"/></circle>
<circle r="4.5" fill="#059669"><animateMotion dur="{DL}s" begin="-1.8s" repeatCount="indefinite" path="M400,188 L400,198"/></circle>
<circle r="5" fill="#7c3aed">{linear_x_motion(DL, ol_d, begin='-2.3s')}</circle>

<circle cx="420" cy="340" r="5.5" fill="#fff" stroke="#dc2626" stroke-width="3">{linear_x_motion(DL, ol_d)}</circle>
<line x1="420" y1="340" x2="744" y2="340" stroke="#64748b" stroke-width="1.5"/>
<line x1="516" y1="320" x2="516" y2="366" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
'''
    svg += caption("① 分压器 R1/R2 把 VOUT 采样回误差放大器，与 1.25V 基准比", "#7c3aed", DL,
                   "0;1;1;0;0", "0;0.04;0.24;0.28;1", y=410)
    svg += caption("② 负载突然加重 → VOUT 一跌 → 采样低于基准 → 误差放大器喊「不够！」", "#dc2626", DL,
                   "0;0;1;1;0;0", "0;0.28;0.32;0.55;0.6;1", y=410)
    svg += caption("③ 调整管立刻「调小自己的电阻」→ VOUT 拉回 5V——全自动，无需人管", "#059669", DL,
                   "0;0;1;1", "0;0.6;0.65;1", y=410)
    svg += note_box("VOUT = 1.25×(1+R1/R2) · 发热 = (VIN−VOUT)×I 全变成热——LDO 效率低的根因", 452, DL, "0;0.68;0.73;1", w=680)
    save('ldo-feedback.svg', svg + '</svg>')

# ======================= 图 10：模拟开关电荷注入 =======================
def make_analog_switch():
    DA = 6
    sh_pts = []
    per = 160
    x_start = 430
    for seg in range(2):
        hv = None
        for i in range(17):
            u = i/16
            x = x_start + seg*per + 40*u
            t = (x-x_start)/320*4*np.pi
            y = 330 - 42*np.sin(t)
            sh_pts.append(f"{x:.0f},{y:.0f}")
            hv = y
        x0 = x_start + seg*per + 40
        sh_pts.append(f"{x0:.0f},{hv+9:.0f}")
        sh_pts.append(f"{x_start+seg*per+160:.0f},{hv+9:.0f}")
    sh_d = "M" + " L".join(sh_pts)
    sin_d = sine_path(430, 750, 330, 42, n=96)
    svg = svg_open('模拟开关的暗伤：关断瞬间，沟道电荷被「挤」进电容（CD4066）', h=480)
    svg += f'''
<text x="215" y="60" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">采样保持电路（传输门 + 保持电容）</text>
<circle cx="60" cy="160" r="20" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="M50,160 q5,-13 10,0 q5,13 10,0" fill="none" stroke="#2563eb" stroke-width="2"/>
<text x="30" y="196" font-size="11" font-weight="bold" fill="#2563eb">输入</text>
<line x1="80" y1="160" x2="130" y2="160" stroke="#334155" stroke-width="2.5"/>
<circle cx="140" cy="160" r="3.5" fill="#334155"/>
<line x1="140" y1="160" x2="168" y2="136" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.6;0.64;1" dur="{DA}s" repeatCount="indefinite"/></line>
<circle cx="176" cy="160" r="3.5" fill="#334155"/>
<text x="118" y="128" font-size="11" font-weight="bold" fill="#334155">NMOS</text>
<text x="118" y="110" font-size="9.5" fill="#475569">传低电平好手</text>
<line x1="176" y1="160" x2="210" y2="160" stroke="#334155" stroke-width="2.5"/>
<line x1="140" y1="160" x2="140" y2="210" stroke="#334155" stroke-width="2.5"/>
<line x1="210" y1="160" x2="210" y2="210" stroke="#334155" stroke-width="2.5"/>
<circle cx="140" cy="210" r="3.5" fill="#334155"/>
<line x1="140" y1="210" x2="168" y2="186" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.6;0.64;1" dur="{DA}s" repeatCount="indefinite"/></line>
<circle cx="176" cy="210" r="3.5" fill="#334155"/>
<line x1="176" y1="210" x2="210" y2="210" stroke="#334155" stroke-width="2.5"/>
<text x="96" y="240" font-size="11" font-weight="bold" fill="#334155">PMOS</text>
<text x="96" y="252" font-size="9.5" fill="#475569">传高电平好手</text>
<text x="226" y="130" font-size="10.5" fill="#7c3aed">EN/EN̅ 互补控制</text>
<text x="226" y="144" font-size="10" fill="#475569">两管同开同关</text>
<line x1="210" y1="160" x2="280" y2="160" stroke="#334155" stroke-width="2.5"/>
<line x1="210" y1="210" x2="280" y2="210" stroke="#334155" stroke-width="2.5"/>
<line x1="280" y1="160" x2="280" y2="210" stroke="#334155" stroke-width="2.5"/>
<circle cx="280" cy="185" r="4" fill="#334155"/>
<line x1="280" y1="185" x2="330" y2="185" stroke="#334155" stroke-width="2.5"/>
<line x1="330" y1="185" x2="330" y2="205" stroke="#334155" stroke-width="2.5"/>
<line x1="300" y1="205" x2="360" y2="205" stroke="#334155" stroke-width="3"/>
<line x1="300" y1="221" x2="360" y2="221" stroke="#334155" stroke-width="3"/>
<line x1="330" y1="221" x2="330" y2="250" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(330, 264)}
<text x="370" y="217" font-size="12" font-weight="bold" fill="#2563eb">C 保持 100pF</text>
<g fill="#f59e0b" opacity="0">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.3;0.36;0.6;0.66;1" dur="{DA}s" repeatCount="indefinite"/>
<circle cx="150" cy="172" r="2.6"/><circle cx="158" cy="168" r="2.6"/><circle cx="163" cy="174" r="2.6"/>
<circle cx="152" cy="222" r="2.6"/><circle cx="160" cy="218" r="2.6"/><circle cx="165" cy="224" r="2.6"/>
</g>
<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.62;0.66;0.9;0.94;1" dur="{DA}s" repeatCount="indefinite"/>
{flow("M170,166 H272 V181 H324", 1.6, n=4, color="#f59e0b", r=4.5)}
{flow("M170,214 H272 V189 H324", 1.6, n=4, color="#f59e0b", r=4.5)}
</g>
<text x="150" y="285" font-size="11.5" font-weight="bold" fill="#b45309" opacity="0">关断瞬间：沟道电子「无家可归」，被挤进 C！
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.64;0.68;0.9;0.94;1" dur="{DA}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.58;0.62;1" dur="{DA}s" repeatCount="indefinite"/>'
    svg += flow("M84,156 H126 M184,156 H272 V181 H324", DA*0.6, n=6, color="#059669", r=5) + '</g>'
    svg += f'''
<text x="590" y="60" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">采样保持波形（注入跳变放大）</text>
<path d="{sin_d}" fill="none" stroke="#94a3b8" stroke-width="1.8" stroke-dasharray="5,4"/>
<text x="436" y="272" font-size="10.5" fill="#64748b">输入（虚线）</text>
<path d="{sh_d}" fill="none" stroke="#2563eb" stroke-width="2.8"/>
<text x="436" y="252" font-size="10.5" font-weight="bold" fill="#2563eb">保持电容电压（实线）</text>
<line x1="430" y1="330" x2="752" y2="330" stroke="#64748b" stroke-width="1.4"/>
<line x1="470" y1="284" x2="470" y2="300" stroke="#dc2626" stroke-width="2.5" opacity="0">
<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.64;0.68;1" dur="{DA}s" repeatCount="indefinite"/></line>
<text x="478" y="314" font-size="11" font-weight="bold" fill="#dc2626" opacity="0">电子注入→电压下陷 ΔV≈10mV
<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.64;0.68;1" dur="{DA}s" repeatCount="indefinite"/></text>
'''
    svg += caption("① 导通：NMOS+PMOS 互补——低走高走全摆幅无损通过（R_ON≈125Ω）", "#059669", DA,
                   "0;1;1;0;0", "0;0.03;0.28;0.32;1", y=420)
    svg += caption("② 跟随期：电容贴着输入走——采样就是把波形「复印」到电容上", "#2563eb", DA,
                   "0;0;1;1;0;0", "0;0.32;0.36;0.58;0.62;1", y=420)
    svg += caption("③ 关断瞬间：沟道电子 Q≈1pC 涌入 100pF 电容 → 电压下陷 ΔV=Q/C≈10mV！", "#dc2626", DA,
                   "0;0;1;1", "0;0.62;0.66;1", y=420)
    svg += note_box("12 位 ADC 的 1 LSB@3.3V 仅 0.8mV——10mV 注入误差=12 LSB！对策：加大保持电容/低注入开关/差分抵消", 458, DA, "0;0.7;0.75;1", w=740)
    save('analog-switch.svg', svg + '</svg>')

# ======================= 图 12：回流路径 =======================
def make_pcb_return_path():
    DR = 5
    svg = svg_open('回流路径：信号的「回家路」，永远贴着它脚下走', h=490)
    svg += f'''
<text x="210" y="52" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#059669">场景 A：完整地平面——回流紧贴信号正下方</text>
<rect x="50" y="76" width="42" height="26" rx="4" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="71" y="93" text-anchor="middle" font-size="10" fill="#2563eb">驱动</text>
<rect x="330" y="76" width="42" height="26" rx="4" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="351" y="93" text-anchor="middle" font-size="10" fill="#2563eb">负载</text>
<line x1="92" y1="89" x2="330" y2="89" stroke="#dc2626" stroke-width="3.5"/>
<text x="200" y="72" font-size="10.5" font-weight="bold" fill="#dc2626">信号（顶层走线）</text>
<rect x="60" y="140" width="300" height="24" fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"/>
<text x="366" y="156" font-size="10.5" fill="#475569">地平面</text>
<line x1="330" y1="152" x2="92" y2="152" stroke="#059669" stroke-width="2.5" stroke-dasharray="6,4"/>
<text x="120" y="178" font-size="10.5" font-weight="bold" fill="#059669">回流（镜像电流，紧贴脚下）</text>
<rect x="92" y="89" width="238" height="63" fill="#059669" opacity="0.07"/>
<text x="200" y="132" font-size="10" fill="#059669" text-anchor="middle" opacity="0">环路面积≈0
<animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.3;0.36;1" dur="{DR}s" repeatCount="indefinite"/></text>
{flow("M94,86 H328", DR/2, n=5, color="#dc2626", r=4.5)}
<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.12;0.18;0.85;0.92;1" dur="{DR}s" repeatCount="indefinite"/>
{flow("M328,152 H94", DR/2, n=5, color="#059669", r=4.5)}
</g>
'''
    svg += f'''
<text x="590" y="52" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#dc2626">场景 B：地平面开槽——回流被迫绕大圈</text>
<rect x="430" y="76" width="42" height="26" rx="4" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="451" y="93" text-anchor="middle" font-size="10" fill="#2563eb">驱动</text>
<rect x="710" y="76" width="42" height="26" rx="4" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="731" y="93" text-anchor="middle" font-size="10" fill="#2563eb">负载</text>
<line x1="472" y1="89" x2="710" y2="89" stroke="#dc2626" stroke-width="3.5"/>
<rect x="440" y="140" width="120" height="24" fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"/>
<rect x="620" y="140" width="140" height="24" fill="#cbd5e1" stroke="#94a3b8" stroke-width="1.5"/>
<rect x="560" y="138" width="60" height="28" fill="#ffffff" stroke="#dc2626" stroke-width="2" stroke-dasharray="5,3"/>
<text x="590" y="132" font-size="10.5" font-weight="bold" fill="#dc2626" text-anchor="middle">开槽！</text>
<polygon points="472,89 710,89 710,152 620,152 620,232 560,232 560,152 472,152" fill="#7c3aed" opacity="0.08">
<animate attributeName="opacity" values="0.08;0.08;0.22;0.22;0.08;0.08" keyTimes="0;0.42;0.5;0.85;0.92;1" dur="{DR}s" repeatCount="indefinite"/></polygon>
<path d="M710,152 H620 V232 H560 V152 H472" fill="none" stroke="#7c3aed" stroke-width="2.5" stroke-dasharray="6,4"/>
<text x="560" y="258" font-size="10.5" font-weight="bold" fill="#7c3aed" text-anchor="middle">回流绕槽大圈 = 环路面积暴增</text>
{flow("M474,86 H708", DR/2, n=5, color="#dc2626", r=4.5)}
<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.42;0.5;0.9;0.96;1" dur="{DR}s" repeatCount="indefinite"/>
{flow("M708,152 H620 V228 H560 V152 H474", DR/2, n=6, color="#7c3aed", r=4.5)}
</g>
<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.6;0.66;0.9;0.96;1" dur="{DR}s" repeatCount="indefinite"/>
<path d="M590,190 q14,-16 28,0 q14,16 28,0" fill="none" stroke="#dc2626" stroke-width="2" transform="translate(-40,-20)"/>
<path d="M590,190 q14,-16 28,0 q14,16 28,0" fill="none" stroke="#dc2626" stroke-width="1.4" opacity="0.6" transform="translate(-52,-40)"/>
<text x="640" y="200" font-size="10.5" font-weight="bold" fill="#dc2626">辐射 EMI</text>
</g>
'''
    svg += caption("① 高频回流不走「几何最短」，走「电感最小」——永远贴着信号正下方（镜像电流）", "#059669", DR,
                   "0;1;1;0;0", "0;0.03;0.3;0.36;1", y=420)
    svg += caption("② 地平面一开槽：回流被断桥逼得绕大圈，环路面积从≈0 暴增几十倍", "#7c3aed", DR,
                   "0;0;1;1;0;0", "0;0.38;0.44;0.62;0.68;1", y=420)
    svg += caption("③ 环路=环形天线：向外辐射 EMI 认证翻车，向内拾取干扰=莫名串扰", "#dc2626", DR,
                   "0;0;1;1", "0;0.68;0.74;1", y=420)
    svg += note_box("军规：任何信号线不许跨分割/开槽！换层时回流地过孔必须贴着信号过孔——「让回流贴着脚下回家」", 462, DR, "0;0.78;0.84;1", w=730)
    save('pcb-return-path.svg', svg + '</svg>')

# ======================= 图 13：差分对 =======================
def make_diff_pair():
    DD = 6
    svg = svg_open('差分对：只认「差」，不认「同」——运放第一级的灵魂', h=562)
    svg += f'''
<text x="330" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">差分对（长尾对）：2mA 的零和游戏</text>
<text x="56" y="76" font-size="12.5" font-weight="bold" fill="#b45309">VCC</text>
<line x1="90" y1="70" x2="480" y2="70" stroke="#334155" stroke-width="2.5"/>
{resistor_v(220, 90, 34, 'Rc1')}
{resistor_v(420, 90, 34, 'Rc2')}
{npn_svg(220, 200)}
{npn_svg(420, 200)}
<line x1="220" y1="255" x2="220" y2="285" stroke="#334155" stroke-width="2.5"/>
<line x1="420" y1="255" x2="420" y2="285" stroke="#334155" stroke-width="2.5"/>
<line x1="220" y1="285" x2="420" y2="285" stroke="#334155" stroke-width="2.5"/>
<circle cx="320" cy="285" r="4" fill="#334155"/>
<line x1="320" y1="285" x2="320" y2="300" stroke="#334155" stroke-width="2.5"/>
<circle cx="320" cy="318" r="16" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<line x1="320" y1="328" x2="320" y2="310" stroke="#7c3aed" stroke-width="2.5"/>
<polygon points="320,306 315,314 325,314" fill="#7c3aed"/>
<line x1="320" y1="334" x2="320" y2="350" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(320, 364)}
<text x="344" y="322" font-size="11" font-weight="bold" fill="#7c3aed">尾电流源 I_EE=2mA（总量钉死）</text>
<text x="52" y="196" font-size="12.5" font-weight="bold" fill="#059669">IN+</text>
<text x="556" y="196" font-size="12.5" font-weight="bold" fill="#dc2626">IN−</text>
<line x1="90" y1="200" x2="135" y2="200" stroke="#334155" stroke-width="2.5"/>
<line x1="385" y1="200" x2="550" y2="200" stroke="#334155" stroke-width="2.5"/>
<circle cx="220" cy="160" r="3.5" fill="#334155"/>
<circle cx="420" cy="160" r="3.5" fill="#334155"/>
<text x="168" y="158" font-size="10.5" font-weight="bold" fill="#2563eb">vC1</text>
<text x="452" y="158" font-size="10.5" font-weight="bold" fill="#2563eb">vC2</text>
<text x="150" y="130" font-size="11" fill="#059669" opacity="0">↑ 升
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DD}s" repeatCount="indefinite"/></text>
<text x="480" y="130" font-size="11" fill="#dc2626" opacity="0">↓ 降
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DD}s" repeatCount="indefinite"/></text>
<text x="150" y="130" font-size="11" fill="#dc2626" opacity="0">↑ 同升
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DD}s" repeatCount="indefinite"/></text>
<text x="480" y="130" font-size="11" fill="#dc2626" opacity="0">↑ 同升
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DD}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.44;0.5;1" dur="{DD}s" repeatCount="indefinite"/>'
    svg += flow("M320,300 V285 H220 V150 V110 V74", DD/3, n=6, color="#059669", r=5)
    svg += flow("M320,300 V285 H420 V150 V74", DD/3, n=1, color="#94a3b8", r=4) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.9;0.96;1" dur="{DD}s" repeatCount="indefinite"/>'
    svg += flow("M320,300 V285 H220 V150 V74", DD/3, n=3, color="#2563eb", r=5)
    svg += flow("M320,300 V285 H420 V150 V74", DD/3, n=3, color="#2563eb", r=5) + '</g>'
    svg += f'''
<text x="180" y="402" font-size="11" font-weight="bold" fill="#475569">电流分配（Q1 绿 vs Q2 红）</text>
<rect y="414" height="16" fill="#059669" x="100" width="220">
<animate attributeName="x" values="100;100;195;195;100" keyTimes="0;0.45;0.55;0.95;1" dur="{DD}s" repeatCount="indefinite"/>
<animate attributeName="width" values="220;220;125;125;220" keyTimes="0;0.45;0.55;0.95;1" dur="{DD}s" repeatCount="indefinite"/></rect>
<rect x="320" y="414" height="16" fill="#dc2626" width="30">
<animate attributeName="width" values="30;30;125;125;30" keyTimes="0;0.45;0.55;0.95;1" dur="{DD}s" repeatCount="indefinite"/></rect>
<text x="100" y="450" font-size="10.5" fill="#059669" opacity="0">Q1 吃 1.8mA
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DD}s" repeatCount="indefinite"/></text>
<text x="380" y="450" font-size="10.5" fill="#94a3b8" opacity="0">Q2 剩 0.2mA
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DD}s" repeatCount="indefinite"/></text>
<text x="210" y="450" font-size="10.5" fill="#2563eb" opacity="0">各 1mA：谁也多吃不了
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DD}s" repeatCount="indefinite"/></text>
'''
    svg += caption("① 差模（IN+升 IN−降）：尾电流此消彼长——vC1 降 vC2 升，输出拉开差距", "#059669", DD,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=478)
    svg += caption("② 共模（两边同升）：尾源总量钉死，两管谁也多吃不了——输出纹丝不动", "#2563eb", DD,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.48;0.53;1", y=478)
    svg += caption("③ 温度漂移是同向的=共模——被结构天然免疫，这就是运放第一级必选它的原因", "#7c3aed", DD,
                   "0;0;1;1", "0;0.55;0.6;1", y=478)
    svg += note_box("CMRR（共模抑制比）的全部秘密 = 尾电流源的内阻——内阻越大，共模越动弹不得", 532, DD, "0;0.66;0.71;1", w=700)
    save('diff-pair.svg', svg + '</svg>')

# ======================= 图 14：Buck 降压 =======================
def make_buck_converter():
    DB = 6
    il_pts = []
    for i in range(97):
        u = i/96
        x = 430 + 320*u
        seg = (u*3) % 1.0
        y = 372 - (30*seg/0.42 if seg < 0.42 else 30*(1-seg)/0.58)
        il_pts.append(f"{x:.0f},{y:.0f}")
    il_d = "M" + " L".join(il_pts)
    svg = svg_open('Buck 降压：电感是「水车惯性」，把断续水流碾成直流', h=520)
    svg += f'''
<text x="220" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">Buck 变换器（12V → 5V，占空比 42%）</text>
<text x="44" y="102" font-size="12.5" font-weight="bold" fill="#b45309">12V</text>
<line x1="70" y1="96" x2="130" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="140" cy="96" r="3.5" fill="#334155"/>
<line x1="140" y1="96" x2="170" y2="68" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DB}s" repeatCount="indefinite"/></line>
<circle cx="176" cy="96" r="3.5" fill="#334155"/>
<text x="126" y="69" font-size="11" font-weight="bold" fill="#334155">开关 SW</text>
<line x1="176" y1="96" x2="200" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="205" cy="96" r="4" fill="#334155"/>
<text x="166" y="86" font-size="10" fill="#7c3aed">开关节点</text>
<path d="M205,96 q8,-16 16,0 q8,16 16,0 q8,-16 16,0 q8,16 16,0 q8,-16 16,0" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<text x="222" y="70" font-size="12" font-weight="bold" fill="#7c3aed">电感 L</text>
<line x1="285" y1="96" x2="320" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="320" cy="96" r="4" fill="#334155"/>
<line x1="320" y1="96" x2="380" y2="96" stroke="#334155" stroke-width="2.5"/>
<text x="384" y="101" font-size="12.5" font-weight="bold" fill="#059669">5V 输出</text>
<line x1="320" y1="96" x2="320" y2="130" stroke="#334155" stroke-width="2.5"/>
<line x1="304" y1="130" x2="336" y2="130" stroke="#2563eb" stroke-width="3.5"/>
<line x1="304" y1="142" x2="336" y2="142" stroke="#2563eb" stroke-width="3.5"/>
<line x1="320" y1="142" x2="320" y2="160" stroke="#334155" stroke-width="2"/>
{gnd_sym(320, 174)}
<text x="344" y="140" font-size="10.5" fill="#2563eb">C 滤波</text>
<line x1="205" y1="96" x2="205" y2="150" stroke="#334155" stroke-width="2.5"/>
<polygon points="205,146 193,170 217,170" fill="none" stroke="#334155" stroke-width="2.5"/>
<line x1="193" y1="146" x2="217" y2="146" stroke="#334155" stroke-width="3"/>
<line x1="205" y1="170" x2="205" y2="186" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(205, 200)}
<text x="150" y="182" font-size="10.5" fill="#dc2626">续流二极管</text>
<line x1="40" y1="200" x2="40" y2="96" stroke="#334155" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.4"/>
<line x1="40" y1="200" x2="320" y2="200" stroke="#334155" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.4"/>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DB}s" repeatCount="indefinite"/>'
    svg += flow("M74,92 H196 M214,92 H316", DB/3, n=6, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.88;0.94;1" dur="{DB}s" repeatCount="indefinite"/>'
    svg += flow("M205,186 V160 M214,146 V100 M214,92 H316", DB/3, n=5, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="440" y="252" font-size="11.5" font-weight="bold" fill="#7c3aed">开关节点电压（方波）</text>
<path d="M430,300 V268 H475 V300 H537 V268 H582 V300 H644 V268 H689 V300 H750" fill="none" stroke="#7c3aed" stroke-width="2.8"/>
<text x="440" y="332" font-size="11.5" font-weight="bold" fill="#059669">电感电流（三角波：斜坡升/斜坡降）</text>
<path d="{il_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<line x1="430" y1="392" x2="750" y2="392" stroke="#2563eb" stroke-width="2.8"/>
<text x="440" y="412" font-size="11.5" font-weight="bold" fill="#2563eb">输出电压（惯性碾平=直流 5V）</text>
'''
    svg += caption("① 开关闭合：12V 经电感向输出灌能量——电感电流斜坡上升（储 ½LI²）", "#059669", DB,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=460)
    svg += caption("② 开关断开：电感不许电流突变，把节点拉到负压——二极管接住续流", "#dc2626", DB,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.5;0.56;1", y=460)
    svg += caption("③ 伏秒平衡：电感一周期平均电压必须为 0 → Vout = D×Vin = 0.42×12 = 5V", "#7c3aed", DB,
                   "0;0;1;1", "0;0.58;0.64;1", y=460)
    svg += note_box("电感=水车的惯性：开关只管断续送水，惯性把水流碾平——效率 90%+ 的秘密是开关不顶压差", 494, DB, "0;0.7;0.75;1", w=730)
    save('buck-converter.svg', svg + '</svg>')

# ======================= 图 11：去耦电容 =======================
def make_cap_decoupling():
    DC = 5
    def dip_wave(x0, depth, w=0.06):
        pts = []
        for i in range(81):
            u = i/80
            x = x0 + 320*u
            y = 340 + depth*np.exp(-((u-0.5)**2)/(2*w**2))
            pts.append(f"{x:.0f},{y:.1f}")
        return "M" + " L".join(pts)
    a_d = dip_wave(60, 55)
    b_d = dip_wave(420, 10)
    svg = svg_open('去耦电容为什么要「贴脸」放？——走线电感 vs 本地水库', h=480)
    svg += f'''
<text x="200" y="50" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#dc2626">场景 A：电容太远（或没有）</text>
<text x="46" y="102" font-size="12" font-weight="bold" fill="#b45309">5V 源</text>
<line x1="90" y1="96" x2="150" y2="96" stroke="#334155" stroke-width="2.5"/>
<path d="M150,96 q6,-14 12,0 q6,14 12,0 q6,-14 12,0 q6,14 12,0 q6,-14 12,0" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<line x1="210" y1="96" x2="260" y2="96" stroke="#334155" stroke-width="2.5"/>
<text x="148" y="76" font-size="11" font-weight="bold" fill="#7c3aed">走线电感 ~10nH</text>
<text x="148" y="64" font-size="10" fill="#475569">10cm 长走线</text>
<rect x="260" y="76" width="90" height="40" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="305" y="100" text-anchor="middle" font-size="12" font-weight="bold" fill="#2563eb">IC</text>
<line x1="305" y1="116" x2="305" y2="146" stroke="#334155" stroke-width="2"/>
{gnd_sym(305, 160)}
<text x="130" y="136" font-size="11" font-weight="bold" fill="#dc2626" opacity="0">尖峰来了，电感「顶住」不给过！
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.42;0.46;0.62;0.66;1" dur="{DC}s" repeatCount="indefinite"/></text>
<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.4;0.44;0.6;0.64;1" dur="{DC}s" repeatCount="indefinite"/>
{flow("M262,92 H300", 1.0, n=2, color="#dc2626", r=4)}
</g>
<text x="590" y="50" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#059669">场景 B：100nF 贴脸（&lt;3mm）</text>
<text x="436" y="102" font-size="12" font-weight="bold" fill="#b45309">5V 源</text>
<line x1="480" y1="96" x2="540" y2="96" stroke="#334155" stroke-width="2.5"/>
<path d="M540,96 q6,-14 12,0 q6,14 12,0 q6,-14 12,0 q6,14 12,0 q6,-14 12,0" fill="none" stroke="#7c3aed" stroke-width="2.5" opacity="0.45"/>
<line x1="600" y1="96" x2="650" y2="96" stroke="#334155" stroke-width="2.5"/>
<text x="644" y="76" text-anchor="end" font-size="11" fill="#94a3b8">走线电感（远，无所谓）</text>
<rect x="650" y="76" width="90" height="40" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="695" y="100" text-anchor="middle" font-size="12" font-weight="bold" fill="#2563eb">IC</text>
<line x1="695" y1="116" x2="695" y2="146" stroke="#334155" stroke-width="2"/>
{gnd_sym(695, 160)}
<line x1="650" y1="96" x2="630" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="650" cy="96" r="3.5" fill="#334155"/>
<line x1="630" y1="96" x2="630" y2="120" stroke="#334155" stroke-width="2.5"/>
<line x1="612" y1="120" x2="648" y2="120" stroke="#059669" stroke-width="3.5"/>
<line x1="612" y1="132" x2="648" y2="132" stroke="#059669" stroke-width="3.5"/>
<line x1="630" y1="132" x2="630" y2="146" stroke="#334155" stroke-width="2"/>
{gnd_sym(630, 160)}
<text x="584" y="130" font-size="11" font-weight="bold" fill="#059669">100nF</text>
<text x="560" y="146" font-size="9.5" fill="#475569">本地水库</text>
<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.4;0.44;0.6;0.64;1" dur="{DC}s" repeatCount="indefinite"/>
{flow("M634,126 V100 H648 M654,96 H688", 1.0, n=4, color="#059669", r=4.5)}
</g>
<text x="608" y="136" text-anchor="end" font-size="11" font-weight="bold" fill="#059669" opacity="0">本地水库瞬时放水，电压纹丝不动
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.42;0.46;0.62;0.66;1" dur="{DC}s" repeatCount="indefinite"/></text>
'''
    svg += f'''
<text x="64" y="290" font-size="11.5" font-weight="bold" fill="#dc2626">A：电源脚电压塌陷 0.5V+（复位/误触发温床）</text>
<path d="{a_d}" fill="none" stroke="#dc2626" stroke-width="3"/>
<line x1="60" y1="340" x2="384" y2="340" stroke="#64748b" stroke-width="1.5"/>
<text x="424" y="290" font-size="11.5" font-weight="bold" fill="#059669">B：微纹波（&lt;50mV），电路安心工作</text>
<path d="{b_d}" fill="none" stroke="#059669" stroke-width="3"/>
<line x1="420" y1="340" x2="744" y2="340" stroke="#64748b" stroke-width="1.5"/>
'''
    svg += caption("① IC 翻转瞬间要 100mA 尖峰电流，但只持续几 ns", "#b45309", DC,
                   "0;1;1;0;0", "0;0.03;0.2;0.24;1", y=400)
    svg += caption("② 走线电感：直流随便过，ns 尖峰面前=断路（V=L·di/dt）", "#7c3aed", DC,
                   "0;0;1;1;0;0", "0;0.24;0.28;0.42;0.46;1", y=400)
    svg += caption("③ 100nF 贴脸=本地水库：它距离近、电感小，尖峰由它顶上", "#059669", DC,
                   "0;0;1;1;0;0", "0;0.46;0.5;0.68;0.72;1", y=400)
    svg += caption("④ 所以记住：距离&lt;3mm、先过电容再到 IC、电容回路越短越好", "#2563eb", DC,
                   "0;0;1;1", "0;0.72;0.76;1", y=400)
    svg += note_box("100nF 管高频（ns 尖峰）· 10µF 管中频 · 大电解管低频——三级去耦，各司其职", 458, DC, "0;0.8;0.84;1", w=640)
    save('cap-decoupling.svg', svg + '</svg>')

# ======================= 图 15：文氏桥振荡器 =======================
def make_wien_bridge():
    DW = 6
    osc_pts = []
    for i in range(161):
        u = i/160
        x = 420 + 330*u
        A = min(1.0, 0.12*np.exp(2.2*u))
        y = 320 - 44*A*np.sin(u*12*np.pi)
        osc_pts.append(f"{x:.0f},{y:.1f}")
    osc_d = "M" + " L".join(osc_pts)
    env_pts = []
    for i in range(61):
        u = i/60
        x = 420 + 330*u
        A = min(1.0, 0.12*np.exp(2.2*u))
        env_pts.append(f"{x:.0f},{320-44*A:.1f}")
    env_d = "M" + " L".join(env_pts)
    svg = svg_open('文氏桥振荡器：正弦波是怎么「无中生有」的', h=500)
    svg += f'''
<text x="200" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">RC 选频 + 增益=3 的同相放大</text>
<text x="14" y="145" font-size="11" fill="#475569">输入</text>
{resistor_h(60, 140, 40, 'R')}
<line x1="120" y1="140" x2="128" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="128" y1="124" x2="128" y2="156" stroke="#334155" stroke-width="3"/>
<line x1="140" y1="124" x2="140" y2="156" stroke="#334155" stroke-width="3"/>
<text x="134" y="114" font-size="11" font-weight="bold" fill="#b45309">C</text>
<line x1="140" y1="140" x2="165" y2="140" stroke="#334155" stroke-width="2.5"/>
<circle cx="165" cy="140" r="4" fill="#334155"/>
<line x1="165" y1="140" x2="300" y2="140" stroke="#334155" stroke-width="2.5"/>
{resistor_v(165, 160, 30, 'R')}
<circle cx="220" cy="140" r="4" fill="#334155"/>
<line x1="220" y1="140" x2="220" y2="160" stroke="#334155" stroke-width="2.5"/>
<line x1="208" y1="160" x2="232" y2="160" stroke="#334155" stroke-width="3"/>
<line x1="208" y1="172" x2="232" y2="172" stroke="#334155" stroke-width="3"/>
<text x="238" y="170" font-size="11" font-weight="bold" fill="#b45309">C</text>
<line x1="220" y1="172" x2="220" y2="210" stroke="#334155" stroke-width="2.5"/>
<line x1="165" y1="210" x2="220" y2="210" stroke="#334155" stroke-width="2"/>
{gnd_sym(192, 224)}
<polygon points="300,110 300,170 360,140" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="306" y="133" font-size="13" font-weight="bold" fill="#059669">+</text>
<text x="306" y="165" font-size="13" font-weight="bold" fill="#dc2626">−</text>
<line x1="360" y1="140" x2="408" y2="140" stroke="#334155" stroke-width="2.5"/>
<circle cx="390" cy="140" r="4" fill="#334155"/>
<text x="340" y="124" font-size="11" font-weight="bold" fill="#2563eb">输出正弦</text>
<line x1="300" y1="155" x2="300" y2="185" stroke="#334155" stroke-width="2"/>
<circle cx="300" cy="185" r="3.5" fill="#334155"/>
{resistor_h(320, 185, 30)}
<circle cx="378" cy="185" r="7" fill="#fff7ed" stroke="#b45309" stroke-width="2"/>
<path d="M372,185 q2,-4 3,0 q2,4 3,0 q2,-4 3,0" fill="none" stroke="#b45309" stroke-width="1.5"/>
<text x="378" y="212" text-anchor="middle" font-size="10" font-weight="bold" fill="#b45309">灯泡</text>
<text x="335" y="212" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#b45309">Rf=2R</text>
<line x1="385" y1="185" x2="390" y2="185" stroke="#334155" stroke-width="2"/>
<line x1="390" y1="185" x2="390" y2="140" stroke="#334155" stroke-width="2"/>
{resistor_v(300, 205, 30)}
<text x="286" y="224" text-anchor="end" font-size="12.5" font-weight="bold" fill="#b45309">R1=R</text>
<line x1="300" y1="255" x2="300" y2="262" stroke="#334155" stroke-width="2"/>
{gnd_sym(300, 276)}
<text x="296" y="250" text-anchor="end" font-size="10.5" fill="#475569">增益 = 1+Rf/R1 = 3</text>
<text x="40" y="104" font-size="11" fill="#475569">反馈回 +端</text>
<path d="M45,140 C20,140 20,310 200,310 C340,310 380,230 400,150" fill="none" stroke="#7c3aed" stroke-width="1.8" stroke-dasharray="5,4">
<animate attributeName="opacity" values="0.3;1;0.3" dur="1.8s" repeatCount="indefinite"/></path>
'''
    svg += f'''
<text x="585" y="252" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">起振过程：噪声种子 → 指数长大 → 稳幅</text>
<path d="{osc_d}" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="{env_d}" fill="none" stroke="#7c3aed" stroke-width="1.5" stroke-dasharray="5,4"/>
<circle cx="420" cy="320" r="5" fill="#fff" stroke="#2563eb" stroke-width="3">{linear_x_motion(DW, osc_d)}</circle>
<circle cx="45" cy="140" r="5" fill="#fff" stroke="#7c3aed" stroke-width="3"><animateMotion dur="{DW}s" repeatCount="indefinite" path="M45,140 C20,140 20,310 200,310 C340,310 380,230 400,150"/></circle>
<line x1="420" y1="320" x2="750" y2="320" stroke="#64748b" stroke-width="1.4"/>
<line x1="420" y1="276" x2="750" y2="276" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="700" y="270" font-size="10" fill="#7c3aed">灯泡稳幅</text>
<text x="440" y="340" font-size="10.5" fill="#475569">开机噪声里的 f₀ 分量被选中、每圈放大一点</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DW}s" begin="-0.3s" repeatCount="indefinite" path="M42,140 L58,140"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DW}s" begin="-0.9s" repeatCount="indefinite" path="M102,140 L126,140"/></circle>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DW}s" begin="-1.5s" repeatCount="indefinite" path="M167,140 L298,140"/></circle>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DW}s" begin="-2.1s" repeatCount="indefinite" path="M220,142 L220,158"/></circle>

'''
    svg += caption("① RC 串并网络在 f₀=1/(2πRC) 处：相移恰好 0°、衰减恰好 1/3", "#7c3aed", DW,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② 同相放大器增益=3：3 × 1/3 = 1——环路增益=1、相移=0，巴克豪森判据成立", "#059669", DW,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.55;0.61;1", y=430)
    svg += caption("③ 起振靠噪声种子；幅度长大靠增益>1；停在多大？——灯泡发热升阻自动稳幅", "#2563eb", DW,
                   "0;0;1;1", "0;0.61;0.67;1", y=430)
    svg += note_box("惠普第一桶金 HP200A 就是这颗灯泡：幅度大→灯丝热→阻升→增益降，自稳在 3 倍", 474, DW, "0;0.72;0.77;1", w=690)
    save('wien-bridge.svg', svg + '</svg>')

# ======================= 图 16：乙类推挽与交越失真 =======================
def make_class_b():
    DC2 = 6
    sin_d = sine_path(60, 390, 330, 40, n=72)
    xo_pts = []
    for i in range(97):
        u = i/96
        x = 430 + 320*u
        s = np.sin(u*4*np.pi)
        y = 330 - 40*(0 if abs(s) < 0.18 else (s-0.18*np.sign(s))/0.82)
        xo_pts.append(f"{x:.0f},{y:.0f}")
    xo_d = "M" + " L".join(xo_pts)
    sin_d2 = sine_path(430, 750, 330, 40, n=72)
    svg = svg_open('乙类推挽：两个人抬轿子，交接处摔了一跤（交越失真）', h=500)
    svg += '''
<text x="200" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">乙类推挽输出级</text>
<text x="56" y="76" font-size="12.5" font-weight="bold" fill="#b45309">+VCC</text>
<line x1="90" y1="70" x2="140" y2="70" stroke="#334155" stroke-width="2.5"/>
<line x1="140" y1="70" x2="140" y2="86" stroke="#334155" stroke-width="2.5"/>
<rect x="112" y="86" width="56" height="30" rx="5" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="140" y="106" text-anchor="middle" font-size="11" font-weight="bold" fill="#2563eb">NPN</text>
<line x1="140" y1="116" x2="140" y2="185" stroke="#334155" stroke-width="2.5"/>
<circle cx="140" cy="185" r="4" fill="#334155"/>
<line x1="140" y1="185" x2="320" y2="185" stroke="#334155" stroke-width="2.5"/>
<text x="328" y="190" font-size="12" font-weight="bold" fill="#2563eb">输出</text>
<rect x="112" y="200" width="56" height="30" rx="5" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
<text x="140" y="220" text-anchor="middle" font-size="11" font-weight="bold" fill="#dc2626">PNP</text>
<line x1="140" y1="185" x2="140" y2="200" stroke="#334155" stroke-width="2.5"/>
<line x1="140" y1="230" x2="140" y2="250" stroke="#334155" stroke-width="2.5"/>
<text x="56" y="256" font-size="12.5" font-weight="bold" fill="#b45309">−VEE</text>
<line x1="90" y1="250" x2="140" y2="250" stroke="#334155" stroke-width="2.5"/>
<line x1="60" y1="160" x2="112" y2="160" stroke="#334155" stroke-width="2.5"/>
<line x1="112" y1="160" x2="112" y2="101" stroke="#334155" stroke-width="2"/>
<line x1="112" y1="160" x2="112" y2="215" stroke="#334155" stroke-width="2"/>
<text x="30" y="156" font-size="11" fill="#475569">输入</text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0;0;1;1" keyTimes="0;0.22;0.26;0.7;0.74;0.96;1" dur="{DC2}s" repeatCount="indefinite"/>'
    svg += flow("M136,88 V116 V181 H314", DC2/4, n=5, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.26;0.3;0.68;0.72;1" dur="{DC2}s" repeatCount="indefinite"/>'
    svg += flow("M314,181 H144 V228 V246", DC2/4, n=5, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="64" y="290" font-size="11.5" font-weight="bold" fill="#475569">输入正弦</text>
<path d="{sin_d}" fill="none" stroke="#94a3b8" stroke-width="2.2"/>
<text x="434" y="290" font-size="11.5" font-weight="bold" fill="#dc2626">乙类输出：过零豁口（死区 ±0.7V）</text>
<path d="{sin_d2}" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<path d="{xo_d}" fill="none" stroke="#dc2626" stroke-width="2.8"/>
<rect x="504" y="316" width="12" height="28" fill="#dc2626" opacity="0.12">
<animate attributeName="opacity" values="0.12;0.12;0.4;0.4;0.12;0.12" keyTimes="0;0.44;0.5;0.88;0.94;1" dur="{DC2}s" repeatCount="indefinite"/></rect>
<rect x="584" y="316" width="12" height="28" fill="#dc2626" opacity="0.12">
<animate attributeName="opacity" values="0.12;0.12;0.4;0.4;0.12;0.12" keyTimes="0;0.44;0.5;0.88;0.94;1" dur="{DC2}s" repeatCount="indefinite"/></rect>
<rect x="664" y="316" width="12" height="28" fill="#dc2626" opacity="0.12">
<animate attributeName="opacity" values="0.12;0.12;0.4;0.4;0.12;0.12" keyTimes="0;0.44;0.5;0.88;0.94;1" dur="{DC2}s" repeatCount="indefinite"/></rect>
<text x="590" y="356" font-size="10" fill="#dc2626">豁口=两管全关</text>
'''
    svg += caption("① 正半周：NPN 导通往下「推」电流（绿粒子）", "#059669", DC2,
                   "0;1;1;0;0", "0;0.03;0.2;0.24;1", y=430)
    svg += caption("② 负半周：PNP 导通往上「拉」电流（红粒子）", "#dc2626", DC2,
                   "0;0;1;1;0;0", "0;0.24;0.28;0.46;0.5;1", y=430)
    svg += caption("③ 交接区 |输入|&lt;0.7V：两管全关→输出豁口——这就是交越失真", "#b45309", DC2,
                   "0;0;1;1;0;0", "0;0.5;0.54;0.72;0.76;1", y=430)
    svg += caption("④ 甲乙类解法：基极间塞两只二极管预加微偏置——死区消失，功放标配", "#2563eb", DC2,
                   "0;0;1;1", "0;0.76;0.8;1", y=430)
    svg += note_box("偏置管要紧贴功率管安装（热耦合）——否则温度升→电流增→更热：热失控烧管", 474, DC2, "0;0.84;0.88;1", w=660)
    save('class-b-crossover.svg', svg + '</svg>')

# ======================= 图 17：Sallen-Key 滤波器 =======================
def make_sallen_key():
    DS = 7
    freqs = np.linspace(0.05, 4, 121)
    def bode(Q):
        pts = []
        for i, f in enumerate(freqs):
            H = 1/np.sqrt((1-f**2)**2 + (f/Q)**2)
            db = max(-52, 20*np.log10(H))
            x = 420 + (np.log10(f)-np.log10(0.05))/(np.log10(4)-np.log10(0.05))*320
            y = 262 - db*1.9
            pts.append(f"{x:.0f},{y:.0f}")
        return "M" + " L".join(pts)
    flat_d = bode(0.707)
    peak_d = bode(3.0)
    sin_in = sine_path(430, 750, 130, 30, n=72)
    lo_pts = []
    for i in range(73):
        u = i/72
        x = 430 + 320*u
        y = 130 - 30*np.sin(u*4*np.pi)*np.exp(-u*2.2)
        lo_pts.append(f"{x:.0f},{y:.0f}")
    lo_d = "M" + " L".join(lo_pts)
    svg = svg_open('Sallen-Key 二阶低通：滤波器是「受控的谐振」', h=520)
    svg += f'''
<text x="200" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">Sallen-Key 二阶低通（单位增益）</text>
<line x1="40" y1="140" x2="60" y2="140" stroke="#334155" stroke-width="2.5"/>
<text x="18" y="145" font-size="11" fill="#475569">输入</text>
{resistor_h(60, 140, 40, 'R1')}
{resistor_h(140, 140, 40, 'R2')}
<circle cx="216" cy="140" r="4" fill="#334155"/>
<line x1="216" y1="140" x2="250" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="130" y1="140" x2="130" y2="100" stroke="#334155" stroke-width="2"/>
<line x1="118" y1="100" x2="142" y2="100" stroke="#7c3aed" stroke-width="3"/>
<line x1="118" y1="90" x2="142" y2="90" stroke="#7c3aed" stroke-width="3"/>
<line x1="130" y1="90" x2="130" y2="76" stroke="#334155" stroke-width="2"/>
<line x1="130" y1="76" x2="300" y2="76" stroke="#334155" stroke-width="2"/>
<text x="148" y="99" font-size="10.5" fill="#7c3aed">C1（反馈顶帽）</text>
<line x1="216" y1="140" x2="216" y2="180" stroke="#334155" stroke-width="2"/>
<line x1="204" y1="180" x2="228" y2="180" stroke="#7c3aed" stroke-width="3"/>
<line x1="204" y1="192" x2="228" y2="192" stroke="#7c3aed" stroke-width="3"/>
<line x1="216" y1="192" x2="216" y2="210" stroke="#334155" stroke-width="2"/>
{gnd_sym(216, 224)}
<text x="150" y="190" font-size="10.5" fill="#7c3aed">C2 下地</text>
<polygon points="250,110 250,170 310,140" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="256" y="134" font-size="13" font-weight="bold" fill="#059669">+</text>
<text x="256" y="160" font-size="13" font-weight="bold" fill="#dc2626">−</text>
<line x1="250" y1="140" x2="244" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="310" y1="140" x2="380" y2="140" stroke="#334155" stroke-width="2.5"/>
<text x="336" y="126" font-size="11" font-weight="bold" fill="#2563eb">输出</text>
<circle cx="350" cy="140" r="4" fill="#334155"/>
<line x1="350" y1="140" x2="350" y2="195" stroke="#334155" stroke-width="2"/>
<line x1="350" y1="195" x2="244" y2="195" stroke="#334155" stroke-width="2"/>
<line x1="244" y1="195" x2="244" y2="155" stroke="#334155" stroke-width="2"/>
<line x1="244" y1="155" x2="250" y2="155" stroke="#334155" stroke-width="2"/>
<line x1="300" y1="76" x2="310" y2="76" stroke="#334155" stroke-width="2"/>
<line x1="310" y1="76" x2="330" y2="76" stroke="#334155" stroke-width="2"/>
<line x1="330" y1="76" x2="330" y2="140" stroke="#334155" stroke-width="2"/>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DS}s" begin="-0.4s" repeatCount="indefinite" path="M40,140 L180,140"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DS}s" begin="-0.9s" repeatCount="indefinite" path="M180,140 L250,140"/></circle>
<circle r="4" fill="#f59e0b"><animateMotion dur="{DS}s" begin="-1.4s" repeatCount="indefinite" path="M216,140 L216,210"/></circle>
<circle r="4" fill="#7c3aed"><animateMotion dur="{DS}s" begin="-1.9s" repeatCount="indefinite" path="M130,140 L130,76 L310,76 L330,76 L330,140"/></circle>
<circle r="4.5" fill="#059669"><animateMotion dur="{DS}s" begin="-2.4s" repeatCount="indefinite" path="M310,140 L380,140"/></circle>
<circle cx="639" cy="268" r="6" fill="none" stroke="#059669" stroke-width="2.5">
<animate attributeName="cy" values="268;268;244;244;268;268" keyTimes="0;0.23;0.28;0.48;0.53;1" dur="{DS}s" repeatCount="indefinite"/>
<animate attributeName="stroke" values="#059669;#059669;#dc2626;#dc2626;#059669;#059669" keyTimes="0;0.23;0.28;0.48;0.53;1" dur="{DS}s" repeatCount="indefinite"/></circle>
'''
    svg += f'''
<text x="590" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">频响：Q 决定峰化</text>
<path d="{flat_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<path d="{peak_d}" fill="none" stroke="#dc2626" stroke-width="2.2" stroke-dasharray="6,4"/>
<line x1="420" y1="262" x2="750" y2="262" stroke="#64748b" stroke-width="1.4"/>
<line x1="639" y1="230" x2="639" y2="370" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="639" y="384" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#475569">fc</text>
<text x="562" y="246" text-anchor="end" font-size="10.5" fill="#059669">Q=0.707 最平坦（Butterworth）</text>
<text x="580" y="222" font-size="10.5" fill="#dc2626">Q=3 峰化鼓包→再大就振荡</text>
<text x="648" y="330" font-size="10.5" fill="#475569">−40dB/dec</text>
<text x="440" y="86" font-size="11.5" font-weight="bold" fill="#475569">高频输入（实线）→ 输出（衰减）</text>
<path d="{sin_in}" fill="none" stroke="#94a3b8" stroke-width="1.6"/>
<path d="{lo_d}" fill="none" stroke="#059669" stroke-width="2.5"/>
'''
    svg += caption("① 低频：C 开路信号直通——增益=1", "#059669", DS,
                   "0;1;1;0;0", "0;0.03;0.18;0.23;1", y=460)
    svg += caption("② fc 附近：C1 顶帽正反馈「托一把」——Q 值决定这里是平还是鼓包", "#dc2626", DS,
                   "0;0;1;1;0;0", "0;0.23;0.28;0.48;0.53;1", y=460)
    svg += caption("③ 高频：两级 RC 接力衰减，−40dB/十倍频滚降", "#7c3aed", DS,
                   "0;0;1;1;0;0", "0;0.53;0.58;0.78;0.83;1", y=460)
    svg += caption("④ 级数每+1 滚降+20dB——要更陡？多级级联，Q 值按查表分配", "#2563eb", DS,
                   "0;0;1;1", "0;0.83;0.88;1", y=460)
    svg += note_box("fc = 1/(2πRC)（R1=R2、C1=C2 时）· Q 由增益设定——滤波器不是衰减器，是受控的谐振", 494, DS, "0;0.88;0.92;1", w=730)
    save('sallen-key.svg', svg + '</svg>')

# ======================= 图 18：电流镜 =======================
def make_current_mirror():
    DM = 6
    svg = svg_open('电流镜：共用一个 V_BE 的「复印机」', h=500)
    svg += f'''
<text x="300" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">基本电流镜（Q1 二极管接法设基准，Q2 复印输出）</text>
<text x="30" y="76" font-size="12.5" font-weight="bold" fill="#b45309">VCC</text>
<line x1="60" y1="70" x2="560" y2="70" stroke="#334155" stroke-width="2.5"/>
{resistor_v(140, 90, 34, 'R_SET')}
<text x="60" y="150" font-size="11" font-weight="bold" fill="#059669">I_REF=1mA</text>
<line x1="105" y1="200" x2="355" y2="200" stroke="#334155" stroke-width="2.5"/>
{npn_svg(140, 200)}
{npn_svg(440, 200)}
<path d="M140,165 V152 H98 V190 H105" fill="none" stroke="#7c3aed" stroke-width="2" stroke-dasharray="4,3"/>
<text x="220" y="142" font-size="10.5" fill="#7c3aed">C-B 短接=二极管接法</text>
<line x1="140" y1="255" x2="140" y2="285" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(140, 299)}
<line x1="440" y1="255" x2="440" y2="285" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(440, 299)}
<line x1="440" y1="145" x2="440" y2="120" stroke="#334155" stroke-width="2.5"/>
<circle cx="440" cy="120" r="4" fill="#334155"/>
<line x1="440" y1="120" x2="500" y2="120" stroke="#334155" stroke-width="2.5"/>
<rect x="500" y="100" width="60" height="40" rx="5" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="530" y="124" text-anchor="middle" font-size="11" fill="#475569">负载</text>
<line x1="560" y1="120" x2="560" y2="70" stroke="#334155" stroke-width="2.5"/>
<text x="496" y="112" text-anchor="end" font-size="11" font-weight="bold" fill="#2563eb">I_OUT≈1mA</text>
<path d="M200,240 C280,290 360,290 420,240" fill="none" stroke="#7c3aed" stroke-width="1.8" stroke-dasharray="5,4"/>
<polygon points="420,240 410,238 413,248" fill="#7c3aed"/>
<text x="280" y="292" font-size="11" fill="#7c3aed">同一个 V_BE → 同一份 I_C</text>
<text x="120" y="330" font-size="11" fill="#059669" opacity="0">V_BE 自动建立
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DM}s" repeatCount="indefinite"/></text>
<text x="400" y="330" font-size="11" fill="#2563eb" opacity="0">电流被复印
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DM}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.44;0.5;1" dur="{DM}s" repeatCount="indefinite"/>'
    svg += flow("M64,66 H140 V160 V235 V281", DM/3, n=6, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.9;0.96;1" dur="{DM}s" repeatCount="indefinite"/>'
    svg += flow("M556,66 V116 H505 M444,124 V160 V235 V281", DM/3, n=5, color="#2563eb", r=5) + '</g>'
    svg += caption("① R_SET 注入 I_REF——Q1 二极管接法让 V_BE 自动停在「恰好流过 1mA」的值", "#059669", DM,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② 同一根基极线把这只 V_BE 同时喂给 Q2——V_BE 相同，I_C 就相同：电流被复印", "#2563eb", DM,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ Q2 集电极电压随负载怎么变，电流纹丝不动——这就是「电流源」", "#7c3aed", DM,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("误差源头：两只基流都从 I_REF 里扣（β 有限）——Wilson 镜再加一管，把误差再压一个数量级", 474, DM, "0;0.74;0.79;1", w=700)
    save('current-mirror.svg', svg + '</svg>')

# ======================= 图 19：Boost 升压 =======================
def make_boost_converter():
    DB2 = 6
    il_pts = []
    for i in range(97):
        u = i/96
        x = 430 + 320*u
        seg = (u*3) % 1.0
        y = 372 - (30*seg/0.5 if seg < 0.5 else 30*(1-seg)/0.5)
        il_pts.append(f"{x:.0f},{y:.0f}")
    il_d = "M" + " L".join(il_pts)
    svg = svg_open('Boost 升压：电感「叠罗汉」把电压顶上去', h=520)
    svg += f'''
<text x="230" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">Boost 变换器（12V → 24V，占空比 50%）</text>
<text x="14" y="102" font-size="12.5" font-weight="bold" fill="#b45309">12V</text>
<line x1="48" y1="96" x2="90" y2="96" stroke="#334155" stroke-width="2.5"/>
<path d="M90,96 q8,-16 16,0 q8,16 16,0 q8,-16 16,0 q8,16 16,0 q8,-16 16,0" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<text x="106" y="70" font-size="12" font-weight="bold" fill="#7c3aed">电感 L</text>
<line x1="170" y1="96" x2="205" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="205" cy="96" r="4" fill="#334155"/>
<text x="166" y="86" font-size="10" fill="#7c3aed">开关节点</text>
<line x1="205" y1="96" x2="230" y2="96" stroke="#334155" stroke-width="2.5"/>
<polygon points="254,96 230,84 230,108" fill="none" stroke="#334155" stroke-width="2.5"/>
<line x1="254" y1="84" x2="254" y2="108" stroke="#334155" stroke-width="3"/>
<text x="222" y="78" font-size="10.5" fill="#dc2626">二极管</text>
<line x1="254" y1="96" x2="320" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="320" cy="96" r="4" fill="#334155"/>
<line x1="320" y1="96" x2="370" y2="96" stroke="#334155" stroke-width="2.5"/>
<text x="374" y="101" font-size="12.5" font-weight="bold" fill="#059669">24V 输出</text>
<line x1="320" y1="96" x2="320" y2="130" stroke="#334155" stroke-width="2.5"/>
<line x1="304" y1="130" x2="336" y2="130" stroke="#2563eb" stroke-width="3.5"/>
<line x1="304" y1="142" x2="336" y2="142" stroke="#2563eb" stroke-width="3.5"/>
<line x1="320" y1="142" x2="320" y2="160" stroke="#334155" stroke-width="2"/>
{gnd_sym(320, 174)}
<text x="344" y="140" font-size="10.5" fill="#2563eb">C 撑住输出</text>
<line x1="205" y1="96" x2="205" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="205" cy="156" r="3.5" fill="#334155"/>
<line x1="205" y1="156" x2="185" y2="180" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DB2}s" repeatCount="indefinite"/></line>
<circle cx="205" cy="186" r="3.5" fill="#334155"/>
<text x="150" y="176" font-size="11" font-weight="bold" fill="#334155">开关 SW</text>
<line x1="205" y1="186" x2="205" y2="196" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(205, 210)}
<line x1="48" y1="96" x2="48" y2="210" stroke="#334155" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.4"/>
<line x1="48" y1="210" x2="320" y2="210" stroke="#334155" stroke-width="1.5" stroke-dasharray="4,3" opacity="0.4"/>
<text x="100" y="245" font-size="11" fill="#059669" opacity="0">电感储能 ½LI²
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DB2}s" repeatCount="indefinite"/></text>
<text x="240" y="245" font-size="11" fill="#dc2626" opacity="0">Vin+L 叠加=24V 顶上去
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DB2}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DB2}s" repeatCount="indefinite"/>'
    svg += flow("M52,92 H196 M205,110 V150 V196", DB2/3, n=6, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.88;0.94;1" dur="{DB2}s" repeatCount="indefinite"/>'
    svg += flow("M52,92 H196 M214,92 H316 M320,100 V126", DB2/3, n=6, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="440" y="252" font-size="11.5" font-weight="bold" fill="#7c3aed">开关节点（0 / 24V 方波）</text>
<path d="M430,300 V268 H483 V300 H537 V268 H590 V300 H644 V268 H697 V300 H750" fill="none" stroke="#7c3aed" stroke-width="2.8"/>
<text x="440" y="332" font-size="11.5" font-weight="bold" fill="#059669">电感电流（升降各半：D=0.5）</text>
<path d="{il_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<line x1="430" y1="392" x2="750" y2="392" stroke="#2563eb" stroke-width="2.8"/>
<text x="440" y="412" font-size="11.5" font-weight="bold" fill="#2563eb">输出 24V = 12V/(1−0.5)</text>
'''
    svg += caption("① 开关闭合：12V 全加在电感上，电流斜坡上升——能量存进磁场（输出靠电容撑）", "#059669", DB2,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=460)
    svg += caption("② 开关断开：电感不许电流突变，极性翻转与 12V 串联叠加——顶开二极管向 24V 灌能", "#dc2626", DB2,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.5;0.56;1", y=460)
    svg += caption("③ 伏秒平衡：Vin·D = (Vout−Vin)·(1−D) → Vout = Vin/(1−D)——D 越近 1 升得越高", "#7c3aed", DB2,
                   "0;0;1;1", "0;0.58;0.64;1", y=460)
    svg += note_box("升压的秘密 = 电感电压与输入「叠罗汉」；Buck 是电感在后级碾平，Boost 是电感在前级打气", 494, DB2, "0;0.7;0.75;1", w=730)
    save('boost-converter.svg', svg + '</svg>')

# ======================= 图 20：精密整流 =======================
def make_precision_rectifier():
    DP = 6
    sin_in = sine_path(430, 750, 120, 26, n=72)
    half_pts = []
    for i in range(73):
        u = i/72
        x = 430 + 320*u
        s = np.sin(u*4*np.pi)
        half_pts.append(f"{x:.0f},{280 - 40*max(0.0, s):.0f}")
    half_d = "M" + " L".join(half_pts)
    flat_d = "M430,280 L750,280"
    svg = svg_open('精密整流：运放「借增益」消灭二极管压降', h=512)
    svg += f'''
<text x="210" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">精密半波整流器（反相型）</text>
<text x="16" y="145" font-size="11" fill="#475569">输入</text>
<text x="16" y="160" font-size="10" fill="#94a3b8">±100mV</text>
{resistor_h(60, 150, 40, 'R1')}
<circle cx="170" cy="150" r="4" fill="#334155"/>
<polygon points="200,120 200,180 260,150" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="206" y="144" font-size="13" font-weight="bold" fill="#dc2626">−</text>
<text x="206" y="170" font-size="13" font-weight="bold" fill="#059669">+</text>
<line x1="170" y1="150" x2="200" y2="135" stroke="#334155" stroke-width="2"/>
<line x1="200" y1="165" x2="196" y2="190" stroke="#334155" stroke-width="2"/>
{gnd_sym(196, 204)}
<line x1="260" y1="150" x2="284" y2="150" stroke="#334155" stroke-width="2.5"/>
<polygon points="308,150 284,138 284,162" fill="none" stroke="#334155" stroke-width="2.5"/>
<line x1="308" y1="138" x2="308" y2="162" stroke="#334155" stroke-width="3"/>
<text x="272" y="132" font-size="10.5" fill="#dc2626">D</text>
<line x1="308" y1="150" x2="350" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="350" cy="150" r="4" fill="#334155"/>
<line x1="350" y1="150" x2="400" y2="150" stroke="#334155" stroke-width="2.5"/>
<text x="360" y="136" font-size="11" font-weight="bold" fill="#2563eb">输出</text>
{resistor_h(200, 210, 40, 'Rf')}
<line x1="120" y1="150" x2="170" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="260" y1="210" x2="280" y2="210" stroke="#334155" stroke-width="2"/>
<line x1="170" y1="150" x2="170" y2="210" stroke="#334155" stroke-width="2"/>
<line x1="170" y1="210" x2="180" y2="210" stroke="#334155" stroke-width="2"/>
<line x1="280" y1="210" x2="350" y2="210" stroke="#334155" stroke-width="2"/>
<line x1="350" y1="210" x2="350" y2="150" stroke="#334155" stroke-width="2"/>
<text x="120" y="245" font-size="11" fill="#dc2626" opacity="0">运放输出自动多抬 0.7V
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DP}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.44;0.5;1" dur="{DP}s" repeatCount="indefinite"/>'
    svg += flow("M64,146 H160 M170,210 H200 M260,210 H346 V154 H396", DP/3, n=6, color="#059669", r=5) + '</g>'
    svg += f'''
<text x="590" y="66" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">输入 ±100mV（太小，普通整流全丢）</text>
<path d="{sin_in}" fill="none" stroke="#94a3b8" stroke-width="2"/>
<text x="590" y="200" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#dc2626">普通二极管整流：0.7V 死区 → 输出=0</text>
<path d="{flat_d}" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="6,4"/>
<text x="590" y="416" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#059669">精密整流输出：干净半波（基线=0V）</text>
<path d="{half_d}" fill="none" stroke="#059669" stroke-width="2.5" transform="translate(0,80)"/>
<line x1="430" y1="360" x2="750" y2="360" stroke="#64748b" stroke-width="1.2"/>
'''
    svg += caption("① 正半周：运放开环增益 10 万倍——输出只需多抬 0.7V，折算回输入仅 7µV 误差", "#059669", DP,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=440)
    svg += caption("② 负半周：二极管截止、运放饱和也无妨——输出被 Rf 锚在 0", "#dc2626", DP,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=440)
    svg += caption("③ 对比：普通二极管对 100mV 信号输出为零；精密整流分毫毕现——mV 级信号救星", "#2563eb", DP,
                   "0;0;1;1", "0;0.64;0.7;1", y=440)
    svg += note_box("0.7V ÷ 开环增益 = 等效死区 7µV——把非线性元件塞进反馈环，让增益替你买单", 486, DP, "0;0.74;0.79;1", w=680)
    save('precision-rectifier.svg', svg + '</svg>')

# ======================= 图 21：米勒效应 =======================
def make_miller_effect():
    DML = 6
    svg = svg_open('米勒效应：小电容被增益放大 (1+A) 倍', h=500)
    svg += f'''
<text x="220" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">跨接在增益级输入输出之间的电容 C</text>
<text x="20" y="145" font-size="11" fill="#475569">输入源</text>
{resistor_h(60, 150, 40, 'R_sig')}
<circle cx="190" cy="150" r="4" fill="#334155"/>
<text x="182" y="172" font-size="11" font-weight="bold" fill="#2563eb">IN</text>
<rect x="230" y="120" width="90" height="60" rx="6" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="275" y="146" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">增益级</text>
<text x="275" y="166" text-anchor="middle" font-size="12" font-weight="bold" fill="#dc2626">−A = −100</text>
<line x1="190" y1="150" x2="230" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="320" y1="150" x2="360" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="360" cy="150" r="4" fill="#334155"/>
<text x="352" y="172" font-size="11" font-weight="bold" fill="#dc2626">OUT</text>
<line x1="190" y1="150" x2="190" y2="90" stroke="#334155" stroke-width="2"/>
<line x1="190" y1="90" x2="216" y2="90" stroke="#334155" stroke-width="2"/>
<line x1="216" y1="76" x2="216" y2="104" stroke="#7c3aed" stroke-width="3"/>
<line x1="228" y1="76" x2="228" y2="104" stroke="#7c3aed" stroke-width="3"/>
<text x="238" y="82" font-size="11" font-weight="bold" fill="#7c3aed">C=10pF</text>
<line x1="228" y1="90" x2="360" y2="90" stroke="#334155" stroke-width="2"/>
<line x1="360" y1="90" x2="360" y2="150" stroke="#334155" stroke-width="2"/>
<circle r="4" fill="#7c3aed"><animateMotion dur="{DML}s" begin="-0.3s" repeatCount="indefinite" path="M190,150 L190,90 L216,90"/></circle>
<circle r="4" fill="#7c3aed"><animateMotion dur="{DML}s" begin="-0.3s" repeatCount="indefinite" path="M228,90 L360,90 L360,150"/></circle>
<circle r="4" fill="#7c3aed"><animateMotion dur="{DML}s" begin="-0.8s" repeatCount="indefinite" path="M190,150 L190,90 L216,90"/></circle>
<circle r="4" fill="#7c3aed"><animateMotion dur="{DML}s" begin="-0.8s" repeatCount="indefinite" path="M228,90 L360,90 L360,150"/></circle>
<text x="60" y="220" font-size="11" fill="#2563eb" opacity="0">IN 摆 1mV
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DML}s" repeatCount="indefinite"/></text>
<text x="300" y="220" font-size="11" fill="#dc2626" opacity="0">OUT 反相摆 −100mV
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DML}s" repeatCount="indefinite"/></text>
<text x="150" y="290" font-size="11.5" font-weight="bold" fill="#7c3aed" opacity="0">C 两端电压差摆了 101mV——充电电流是「预期」的 101 倍！
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DML}s" repeatCount="indefinite"/></text>
<text x="60" y="330" font-size="12" fill="#334155" opacity="0">⇒ 从输入端看：等效电容 C_eff = (1+A)×C = 101×10pF ≈ <tspan font-weight="bold" fill="#dc2626">1nF</tspan>
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.56;0.6;0.92;0.98;1" dur="{DML}s" repeatCount="indefinite"/></text>
'''
    svg += f'''
<rect x="480" y="90" width="270" height="130" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"/>
<text x="615" y="116" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">输入端看到的「等效世界」</text>
<line x1="500" y1="150" x2="560" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="560" y1="150" x2="560" y2="170" stroke="#334155" stroke-width="2"/>
<line x1="546" y1="170" x2="574" y2="170" stroke="#7c3aed" stroke-width="3"/>
<line x1="546" y1="182" x2="574" y2="182" stroke="#7c3aed" stroke-width="3"/>
<line x1="560" y1="182" x2="560" y2="196" stroke="#334155" stroke-width="2"/>
<text x="586" y="180" font-size="11" font-weight="bold" fill="#dc2626">1nF 到地</text>
<text x="615" y="212" text-anchor="middle" font-size="10.5" fill="#475569">10pF 变身 1nF——高频信号全被它拖慢</text>
<text x="440" y="242" font-size="11" font-weight="bold" fill="#2563eb">IN：±1mV 小摆幅</text>
<path d="{sine_path(440, 740, 268, 7, n=64)}" fill="none" stroke="#2563eb" stroke-width="2.2"/>
<line x1="440" y1="268" x2="740" y2="268" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="3,3"/>
<text x="440" y="312" font-size="11" font-weight="bold" fill="#dc2626">OUT：∓100mV 大摆幅（反相）</text>
<path d="{sine_path(440, 740, 352, 38, n=64, phase=3.14159)}" fill="none" stroke="#dc2626" stroke-width="2.2"/>
<line x1="440" y1="352" x2="740" y2="352" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="3,3"/>
'''
    svg += caption("① IN 只摆 1mV，OUT 反相摆 −100mV——电容两端实际承受 101mV 的摆幅", "#2563eb", DML,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② 充同一份电荷，输入源要供 101 倍电流——仿佛对着 1nF 而不是 10pF", "#7c3aed", DML,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ 坏事变好事：运放人为跨接小补偿电容——用米勒效应低成本获得大电容", "#059669", DML,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("C_eff=(1+A)·C：它是放大器高频滚降的元凶（C_bc 只有几 pF），也是密勒补偿的原理", 474, DML, "0;0.74;0.79;1", w=710)
    save('miller-effect.svg', svg + '</svg>')

# ======================= 图 22：仪表放大器 =======================
def make_instrumentation_amp():
    DI = 7
    cm_in = sine_path(480, 740, 120, 34, n=64)
    diff_out = sine_path(480, 740, 340, 44, n=64)
    svg = svg_open('仪表放大器：三道防线挡住共模', h=520)
    svg += f'''
<text x="240" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">三运放仪放：前级双同相 + 后级减法器</text>
<text x="18" y="128" font-size="11" font-weight="bold" fill="#059669">IN+</text>
<text x="18" y="248" font-size="11" font-weight="bold" fill="#dc2626">IN−</text>
<line x1="46" y1="124" x2="110" y2="124" stroke="#334155" stroke-width="2.5"/>
<line x1="46" y1="244" x2="110" y2="244" stroke="#334155" stroke-width="2.5"/>
<polygon points="110,100 110,160 170,130" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="114" y="126" font-size="12" font-weight="bold" fill="#059669">+</text>
<text x="114" y="156" font-size="12" font-weight="bold" fill="#dc2626">−</text>
<polygon points="110,220 110,280 170,250" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="114" y="246" font-size="12" font-weight="bold" fill="#059669">+</text>
<text x="114" y="276" font-size="12" font-weight="bold" fill="#dc2626">−</text>
<line x1="110" y1="148" x2="110" y2="166" stroke="#334155" stroke-width="2"/>
<circle cx="110" cy="166" r="3.5" fill="#334155"/>
{resistor_v(110, 166, 48, 'R_G')}
<line x1="110" y1="234" x2="110" y2="268" stroke="#334155" stroke-width="2"/>
<line x1="170" y1="130" x2="200" y2="130" stroke="#334155" stroke-width="2.5"/>
<circle cx="200" cy="130" r="3.5" fill="#334155"/>
<line x1="200" y1="130" x2="200" y2="90" stroke="#334155" stroke-width="2"/>
{resistor_h(130, 90, 30, 'R1')}
<line x1="110" y1="90" x2="110" y2="148" stroke="#334155" stroke-width="2"/>
<line x1="180" y1="90" x2="200" y2="90" stroke="#334155" stroke-width="2"/>
<line x1="170" y1="250" x2="200" y2="250" stroke="#334155" stroke-width="2.5"/>
<circle cx="200" cy="250" r="3.5" fill="#334155"/>
<line x1="200" y1="250" x2="200" y2="290" stroke="#334155" stroke-width="2"/>
{resistor_h(130, 290, 30, 'R2')}
<line x1="110" y1="268" x2="110" y2="290" stroke="#334155" stroke-width="2"/>
<line x1="180" y1="290" x2="200" y2="290" stroke="#334155" stroke-width="2"/>
<text x="206" y="120" font-size="10.5" font-weight="bold" fill="#2563eb">v1</text>
<text x="206" y="266" font-size="10.5" font-weight="bold" fill="#2563eb">v2</text>
<line x1="200" y1="130" x2="240" y2="130" stroke="#334155" stroke-width="2"/>
<line x1="240" y1="130" x2="240" y2="186" stroke="#334155" stroke-width="2"/>
{resistor_h(250, 186, 30, 'R')}
<polygon points="310,170 310,230 370,200" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="316" y="198" font-size="12" font-weight="bold" fill="#dc2626">−</text>
<text x="316" y="222" font-size="12" font-weight="bold" fill="#059669">+</text>
<line x1="240" y1="250" x2="240" y2="214" stroke="#334155" stroke-width="2"/>
<line x1="200" y1="250" x2="240" y2="250" stroke="#334155" stroke-width="2"/>
{resistor_h(250, 214, 30, '')}
<text x="265" y="240" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">R</text>
<line x1="370" y1="200" x2="440" y2="200" stroke="#334155" stroke-width="2.5"/>
<text x="400" y="186" font-size="11" font-weight="bold" fill="#2563eb">输出</text>
<line x1="305" y1="214" x2="305" y2="232" stroke="#334155" stroke-width="2"/>
<line x1="305" y1="232" x2="330" y2="232" stroke="#334155" stroke-width="2"/>
{resistor_v(330, 250, 30, 'R')}
{gnd_sym(330, 300)}
<line x1="390" y1="200" x2="390" y2="150" stroke="#334155" stroke-width="2"/>
{resistor_h(340, 150, 30, 'R')}
<line x1="320" y1="150" x2="304" y2="150" stroke="#334155" stroke-width="2"/>
<line x1="304" y1="150" x2="304" y2="186" stroke="#334155" stroke-width="2"/>
<circle cx="304" cy="186" r="3.5" fill="#334155"/>
<line x1="300" y1="186" x2="310" y2="186" stroke="#334155" stroke-width="2"/>
<line x1="300" y1="214" x2="310" y2="214" stroke="#334155" stroke-width="2"/>
<circle cx="305" cy="214" r="3.5" fill="#334155"/>
<text x="100" y="330" font-size="11" fill="#dc2626" opacity="0">差模：R_G 有电流，v1/v2 反向拉大
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.05;0.28;0.33;1" dur="{DI}s" repeatCount="indefinite"/></text>
<text x="100" y="352" font-size="11" fill="#7c3aed" opacity="0">共模：R_G 两端同升同降→无电流→前级增益=1
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.36;0.4;0.62;0.67;1" dur="{DI}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.3;0.35;1" dur="{DI}s" repeatCount="indefinite"/>'
    svg += flow("M110,166 V210", DI/4, n=3, color="#dc2626", r=4.5)
    svg += flow("M204,130 H240 V186 M204,250 H240 V214", DI/4, n=4, color="#059669", r=4.5) + '</g>'
    svg += f'''
<text x="610" y="66" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">输入：毫伏差分 + 大共模干扰</text>
<path d="{cm_in}" fill="none" stroke="#94a3b8" stroke-width="2"/>
<text x="610" y="266" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#059669">输出：差分被放大，共模被扔掉</text>
<path d="{diff_out}" fill="none" stroke="#059669" stroke-width="2.5"/>
<line x1="480" y1="340" x2="740" y2="340" stroke="#64748b" stroke-width="1.2"/>
'''
    svg += caption("① 差模信号：R_G 两端有电位差→电流流过→v1 升 v2 降，前级增益 = 1+2R1/R_G", "#dc2626", DI,
                   "0;1;1;0;0", "0;0.02;0.2;0.25;1", y=460)
    svg += caption("② 共模信号：R_G 两端同升同降→电位差为零→无电流→前级对共模增益=1（不放大）", "#7c3aed", DI,
                   "0;0;1;1;0;0", "0;0.27;0.32;0.5;0.55;1", y=460)
    svg += caption("③ 减法器（A3+四只等值 R）：只认 v1−v2 的差——前级放行的共模在这里被减掉", "#059669", DI,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.78;0.83;1", y=460)
    svg += caption("④ 一只 R_G 调增益：换 R_G 不碰任何匹配网络——产线/现场单手调增益", "#2563eb", DI,
                   "0;0;1;1", "0;0.83;0.88;1", y=460)
    svg += note_box("CMRR>100dB 的三道防线：前级对称结构 · R_G 不吸共模电流 · 减法器四 R 激光修调匹配", 494, DI, "0;0.88;0.92;1", w=700)
    save('instrumentation-amp.svg', svg + '</svg>')

# ======================= 图 23：LC 谐振 =======================
def make_rlc_resonance():
    DR = 6
    f_pts = np.linspace(0.1, 4, 121)
    def resp(Q):
        pts = []
        for f in f_pts:
            H = 1/np.sqrt(1 + (Q*(f-1/f))**2)
            x = 420 + (np.log10(f)-np.log10(0.1))/(np.log10(4)-np.log10(0.1))*320
            pts.append(f"{x:.0f},{330-180*H:.0f}")
        return "M" + " L".join(pts)
    hi_q = resp(5)
    lo_q = resp(1.2)
    svg = svg_open('LC 谐振：电场与磁场的「荡秋千」', h=500)
    svg += '''
<text x="200" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">LC 串联谐振回路</text>
<circle cx="60" cy="150" r="16" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="60" y="155" text-anchor="middle" font-size="12" fill="#334155">~</text>
<line x1="76" y1="150" x2="100" y2="150" stroke="#334155" stroke-width="2.5"/>
<path d="M100,150 q8,-16 16,0 q8,16 16,0 q8,-16 16,0 q8,16 16,0 q8,-16 16,0" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<text x="116" y="124" font-size="12" font-weight="bold" fill="#7c3aed">L</text>
<line x1="180" y1="150" x2="216" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="216" y1="134" x2="216" y2="166" stroke="#2563eb" stroke-width="3"/>
<line x1="228" y1="134" x2="228" y2="166" stroke="#2563eb" stroke-width="3"/>
<text x="238" y="142" font-size="12" font-weight="bold" fill="#2563eb">C</text>
<line x1="228" y1="150" x2="280" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="280" y1="150" x2="280" y2="210" stroke="#334155" stroke-width="2"/>
<line x1="60" y1="166" x2="60" y2="210" stroke="#334155" stroke-width="2"/>
<line x1="60" y1="210" x2="280" y2="210" stroke="#334155" stroke-width="2"/>
<circle cx="170" cy="210" r="4" fill="#334155"/>
<text x="150" y="232" font-size="10.5" fill="#475569">回路电流 I</text>
<rect x="90" y="260" height="14" fill="#7c3aed" width="30">
<animate attributeName="width" values="30;120;30;120;30" dur="2s" repeatCount="indefinite"/></rect>
<text x="90" y="290" font-size="10.5" fill="#7c3aed">磁场能 ½LI²</text>
<rect x="240" y="260" height="14" fill="#2563eb" width="120">
<animate attributeName="width" values="120;30;120;30;120" dur="2s" repeatCount="indefinite"/></rect>
<text x="240" y="290" font-size="10.5" fill="#2563eb">电场能 ½CV²</text>
'''
    svg += flow("M80,146 H176 M232,146 H276 V206 H64 V170", DR/3, n=6, color="#059669", r=4.5)
    svg += f'''
<text x="590" y="66" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">电流-频率曲线：f₀ 处阻抗抵消、电流冲顶</text>
<path d="{hi_q}" fill="none" stroke="#dc2626" stroke-width="2.8"/>
<path d="{lo_q}" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="6,4"/>
<line x1="420" y1="330" x2="740" y2="330" stroke="#64748b" stroke-width="1.4"/>
<line x1="620" y1="150" x2="620" y2="330" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="608" y="344" font-size="10.5" fill="#475569">f₀</text>
<text x="610" y="132" font-size="10.5" fill="#dc2626">Q 高：峰尖（选台准）</text>
<text x="440" y="220" font-size="10.5" fill="#94a3b8">Q 低：峰胖（R 大衰减快）</text>
'''
    svg += caption("① f₀=1/(2π√LC)：感抗与容抗恰好相等、正负抵消——回路只剩 R，电流冲到最大", "#dc2626", DR,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② 能量的秋千：电场能（C）与磁场能（L）每周期来回倒两次——R 只是倒腾途中的摩擦", "#7c3aed", DR,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ Q=ω₀L/R：R 越小 Q 越高、峰越尖——收音机选台、晶振稳频靠的都是高 Q", "#059669", DR,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("谐振不是「放大」——是阻抗抵消后电源只面对 R；峰顶的电压/电流可以远超激励，这就是谐振的危险与价值", 474, DR, "0;0.74;0.79;1", w=730)
    save('rlc-resonance.svg', svg + '</svg>')

# ======================= 图 24：SAR ADC 逐次逼近 =======================
def make_sar_adc():
    DA = 8
    steps_x = [430, 510, 590, 670, 750]
    dac_lv = [8, 4, 6, 5]
    step_d = "M430,300 "
    for i, lv in enumerate(dac_lv):
        y = 300 - lv*12
        step_d += f"V{y} H{steps_x[i+1]} "
    svg = svg_open('SAR ADC：四位天平，四次称出答案', h=520)
    svg += f'''
<text x="240" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">SAR = 二分查找的硬件版（4 位演示：满量程 16，输入 5.3）</text>
<rect x="60" y="100" width="90" height="50" rx="6" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="105" y="122" text-anchor="middle" font-size="11" fill="#334155">采样保持</text>
<text x="105" y="140" text-anchor="middle" font-size="10" fill="#2563eb">5.3V 抓住</text>
<line x1="150" y1="125" x2="190" y2="125" stroke="#334155" stroke-width="2.5"/>
<polygon points="190,100 190,150 240,125" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="196" y="118" font-size="11" font-weight="bold" fill="#059669">+</text>
<text x="196" y="142" font-size="11" font-weight="bold" fill="#dc2626">−</text>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DA}s" begin="-0.5s" repeatCount="indefinite" path="M250,100 L242,100 L242,112"/></circle>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DA}s" begin="-1.3s" repeatCount="indefinite" path="M280,127 L280,188"/></circle>
<circle r="4.5" fill="#059669"><animateMotion dur="{DA}s" begin="-2.1s" repeatCount="indefinite" path="M316,188 L316,62 L318,62"/></circle>
<rect x="270" y="190" width="90" height="44" rx="6" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="315" y="210" text-anchor="middle" font-size="11" fill="#334155">SAR 逻辑</text>
<text x="315" y="226" text-anchor="middle" font-size="10" fill="#475569">留/退裁决</text>
<line x1="240" y1="125" x2="280" y2="125" stroke="#334155" stroke-width="2"/>
<line x1="280" y1="125" x2="280" y2="190" stroke="#334155" stroke-width="2"/>
<rect x="250" y="80" width="70" height="36" rx="6" fill="#f8fafc" stroke="#7c3aed" stroke-width="2"/>
<text x="285" y="102" text-anchor="middle" font-size="11" font-weight="bold" fill="#7c3aed">DAC</text>
<line x1="250" y1="98" x2="240" y2="98" stroke="#334155" stroke-width="2"/>
<line x1="240" y1="98" x2="240" y2="112" stroke="#334155" stroke-width="2"/>
<line x1="320" y1="80" x2="320" y2="60" stroke="#334155" stroke-width="2"/>
<line x1="320" y1="60" x2="315" y2="60" stroke="#334155" stroke-width="2"/>
<line x1="315" y1="60" x2="315" y2="190" stroke="#334155" stroke-width="2" stroke-dasharray="4,3"/>
<text x="330" y="64" font-size="10" fill="#475569">试位码→</text>
<text x="380" y="222" font-size="11" font-weight="bold" fill="#2563eb">结果 0101</text>
<line x1="360" y1="212" x2="380" y2="212" stroke="#334155" stroke-width="2"/>
'''
    svg += f'''
<text x="590" y="142" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">DAC 输出（紫阶）四拍逼近输入线（蓝）</text>
<line x1="430" y1="{300-5.3*12:.0f}" x2="750" y2="{300-5.3*12:.0f}" stroke="#2563eb" stroke-width="2.2"/>
<text x="700" y="{292-5.3*12:.0f}" font-size="10.5" fill="#2563eb">输入 5.3</text>
<path d="{step_d}" fill="none" stroke="#7c3aed" stroke-width="2.8"/>
<line x1="430" y1="300" x2="750" y2="300" stroke="#64748b" stroke-width="1.4"/>
<text x="448" y="330" font-size="10.5" fill="#475569">① 8→退</text>
<text x="528" y="330" font-size="10.5" fill="#475569">② 4→留</text>
<text x="608" y="330" font-size="10.5" fill="#475569">③ 6→退</text>
<text x="688" y="330" font-size="10.5" fill="#475569">④ 5→留</text>
<rect x="430" y="150" width="80" height="150" fill="#7c3aed" opacity="0">
<animate attributeName="opacity" values="0;0.12;0.12;0;0" keyTimes="0;0.03;0.22;0.26;1" dur="{DA}s" repeatCount="indefinite"/></rect>
<rect x="510" y="150" width="80" height="150" fill="#7c3aed" opacity="0">
<animate attributeName="opacity" values="0;0;0.12;0.12;0;0" keyTimes="0;0.27;0.3;0.47;0.51;1" dur="{DA}s" repeatCount="indefinite"/></rect>
<rect x="590" y="150" width="80" height="150" fill="#7c3aed" opacity="0">
<animate attributeName="opacity" values="0;0;0.12;0.12;0;0" keyTimes="0;0.52;0.55;0.72;0.76;1" dur="{DA}s" repeatCount="indefinite"/></rect>
<rect x="670" y="150" width="80" height="150" fill="#7c3aed" opacity="0">
<animate attributeName="opacity" values="0;0;0.12;0.12;0;0" keyTimes="0;0.77;0.8;0.95;0.98;1" dur="{DA}s" repeatCount="indefinite"/></rect>
<circle r="6" fill="#7c3aed" stroke="#ffffff" stroke-width="2">
<animateMotion dur="{DA}s" repeatCount="indefinite" calcMode="linear"
  keyPoints="0;0.352;0.352;0.608;0.608;0.84;0.84;1;1" keyTimes="0;0.05;0.24;0.3;0.48;0.55;0.73;0.79;1"
  path="{step_d}"/></circle>
'''
    svg += caption("① 拍1：先试最高位 8（半天平）——DAC=8 > 5.3，太沉，退掉这一位", "#7c3aed", DA,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=460)
    svg += caption("② 拍2：试次高位 4——DAC=4 &lt; 5.3，太轻，留下（累计 4）", "#059669", DA,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.45;0.51;1", y=460)
    svg += caption("③ 拍3：试 4+2=6——6 &gt; 5.3，退；拍4：试 4+1=5——5 &lt; 5.3，留 → 0101", "#dc2626", DA,
                   "0;0;1;1;0;0", "0;0.53;0.58;0.75;0.81;1", y=460)
    svg += caption("④ N 位只要 N 拍：12 位=12 拍——速度与精度折中里的「中」就是这么来的", "#2563eb", DA,
                   "0;0;1;1", "0;0.81;0.86;1", y=460)
    svg += note_box("比较器是天平的指针，DAC 是砝码，SAR 逻辑是记录员——每拍只问一个问题：「重了还是轻了」", 494, DA, "0;0.88;0.92;1", w=690)
    save('sar-adc.svg', svg + '</svg>')

# ======================= 图 25：带隙基准 =======================
def make_bandgap():
    DBG = 6
    vbe_d = "M430,190 " + " L".join(f"{430+320*i/80:.0f},{190+52*(i/80)**1.15:.0f}" for i in range(81))
    dvbe_d = "M430,262 " + " L".join(f"{430+320*i/80:.0f},{262-52*(i/80):.0f}" for i in range(81))
    svg = svg_open('带隙基准：一正一负，凑出与温度无关的 1.25V', h=520)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">V_REF = V_BE + K·ΔV_BE ≈ 1.25V（硅带隙电压）</text>
<rect x="60" y="80" width="320" height="220" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="220" y="104" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">Brokaw 单元（简化）</text>
<text x="220" y="122" text-anchor="middle" font-size="10.5" fill="#7c3aed">两管电流密度不同 → ΔV_BE=V_T·ln(8)≈54mV 落在 R 上</text>
{npn_svg(150, 206)}
{npn_svg(290, 206)}
<text x="120" y="286" font-size="10.5" fill="#475569">Q1（1×）</text>
<text x="255" y="286" font-size="10.5" font-weight="bold" fill="#dc2626">Q2（8× 面积）</text>
'''
    svg += f'''
<text x="590" y="76" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">随温度（−40°C → 125°C）</text>
<path d="{vbe_d}" fill="none" stroke="#dc2626" stroke-width="2.8"/>
<text x="640" y="238" font-size="10.5" fill="#dc2626">V_BE：−2mV/°C 下坡</text>
<path d="{dvbe_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<text x="440" y="296" font-size="10.5" fill="#059669">K·ΔV_BE：正温漂上坡（V_T 正比绝对温度）</text>
<line x1="430" y1="226" x2="750" y2="226" stroke="#2563eb" stroke-width="3"/>
<text x="590" y="216" font-size="11" font-weight="bold" fill="#2563eb">合成 V_REF=1.25V：一条直线</text>
<line x1="430" y1="270" x2="750" y2="270" stroke="#64748b" stroke-width="1.2"/>
<text x="430" y="284" font-size="10" fill="#475569">−40°C</text>
<text x="724" y="284" font-size="10" fill="#475569">125°C</text>
<circle cx="430" cy="190" r="5.5" fill="#fff" stroke="#dc2626" stroke-width="3"><animateMotion dur="{DBG}s" repeatCount="indefinite" path="{vbe_d}"/></circle>
<circle cx="430" cy="262" r="5.5" fill="#fff" stroke="#059669" stroke-width="3"><animateMotion dur="{DBG}s" repeatCount="indefinite" path="{dvbe_d}"/></circle>
<circle cx="430" cy="226" r="5.5" fill="#fff" stroke="#2563eb" stroke-width="3"><animateMotion dur="{DBG}s" repeatCount="indefinite" path="M430,226 H750"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DBG}s" begin="-0.5s" repeatCount="indefinite" path="M110,300 L110,340 L150,340"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DBG}s" begin="-1.2s" repeatCount="indefinite" path="M150,360 L200,360 L200,400"/></circle>
<circle cx="750" cy="226" r="5" fill="none" stroke="#059669" stroke-width="2.4">
<animate attributeName="r" values="5;13;5" dur="1.8s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.15;0.95" dur="1.8s" repeatCount="indefinite"/></circle>
<circle cx="590" cy="226" r="6" fill="#2563eb">
<animate attributeName="r" values="6;10;6" dur="2.2s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① V_BE 天生负温漂（−2mV/°C）——温度一升它就掉（PN 结特性，见 2.2）", "#dc2626", DBG,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② ΔV_BE 天生正温漂——两管电流密度差产生，V_T=kT/q 与绝对温度严格成正比", "#059669", DBG,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ 给 ΔV_BE 配权重 K，让上坡斜率恰好抵消下坡——合成 1.25V，全温区纹丝不动", "#2563eb", DBG,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("1.25V 不是调出来的，是硅的带隙电压——两条物理曲线的交点写在材料常数里（Widlar 1971 / Brokaw 1974，见 8.9）", 474, DBG, "0;0.74;0.79;1", w=740)
    save('bandgap.svg', svg + '</svg>')

# ======================= 图 26：TL431 可调基准 =======================
def make_tl431():
    DT = 6
    svg = svg_open('TL431：会"变身"的基准——自带 2.5V 标尺的比较器', h=500)
    svg += f'''
<text x="250" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">TL431 内部：基准 + 运放 + 吸入级</text>
<rect x="70" y="80" width="330" height="220" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="235" y="104" text-anchor="middle" font-size="11" fill="#94a3b8">TL431 内部框图</text>
<text x="20" y="196" font-size="11.5" font-weight="bold" fill="#059669">REF</text>
<line x1="52" y1="192" x2="120" y2="192" stroke="#334155" stroke-width="2.5"/>
<polygon points="150,160 150,224 220,192" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="156" y="184" font-size="12" font-weight="bold" fill="#059669">+</text>
<text x="156" y="214" font-size="12" font-weight="bold" fill="#dc2626">−</text>
<line x1="120" y1="192" x2="150" y2="176" stroke="#334155" stroke-width="2"/>
<rect x="110" y="236" width="90" height="30" rx="5" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="155" y="256" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#2563eb">带隙 2.5V</text>
<line x1="155" y1="236" x2="155" y2="208" stroke="#334155" stroke-width="2"/>
{npn_svg(280, 192)}
<line x1="220" y1="192" x2="245" y2="192" stroke="#334155" stroke-width="2"/>
<line x1="280" y1="137" x2="280" y2="110" stroke="#334155" stroke-width="2.5"/>
<text x="292" y="116" font-size="11.5" font-weight="bold" fill="#dc2626">K（阴极吸流）</text>
<line x1="280" y1="247" x2="280" y2="268" stroke="#334155" stroke-width="2"/>
<text x="292" y="266" font-size="11.5" font-weight="bold" fill="#475569">A（阳极）</text>
<line x1="280" y1="268" x2="280" y2="282" stroke="#334155" stroke-width="2"/>
<text x="60" y="330" font-size="11" fill="#dc2626" opacity="0">REF &lt; 2.5V：调整管关，K 不吸流
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DT}s" repeatCount="indefinite"/></text>
<text x="60" y="354" font-size="11" fill="#059669" opacity="0">REF &gt; 2.5V：调整管开，K 猛吸流把电压拽下来
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DT}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.9;0.96;1" dur="{DT}s" repeatCount="indefinite"/>'
    svg += flow("M284,114 V160 V222 V264", DT/3, n=4, color="#dc2626", r=5) + '</g>'
    svg += '''
<rect x="460" y="90" width="290" height="150" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5"/>
<text x="605" y="116" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">变身稳压器：分压采样闭环</text>
<text x="480" y="146" font-size="11" fill="#475569">Vout ──[R1]──┬── REF</text>
<text x="480" y="168" font-size="11" fill="#475569">            [R2]</text>
<text x="480" y="190" font-size="11" fill="#475569">K 串电阻到 Vout，A 接地</text>
<text x="480" y="218" font-size="11.5" font-weight="bold" fill="#2563eb">Vout = 2.5V × (1 + R1/R2)</text>
'''
    svg += caption("① REF 与内部 2.5V 带隙基准比大小——低于基准：运放关断调整管，阴极不吸流（高阻）", "#dc2626", DT,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② REF 高过 2.5V 一点点：运放立刻导通调整管——阴极大力吸流，把采样源头电压拽低", "#059669", DT,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ 分压器把 Vout 按比例送到 REF——闭环自动停在 REF=2.5V：Vout=2.5×(1+R1/R2)，换电阻=换电压", "#2563eb", DT,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("阴极电压永远 ≥2.5V——并联稳压、精密恒流、光耦反馈全用它", 474, DT, "0;0.74;0.79;1", w=730)
    save('tl431.svg', svg + '</svg>')

# ======================= 图 27：采样保持 =======================
def make_sample_hold():
    DH = 7
    sin_d = sine_path(430, 750, 150, 42, n=96)
    hold_pts = []
    for i in range(97):
        u = i/96
        x = 430 + 320*u
        seg = int(u*8)
        v = np.sin(seg/8*2*np.pi*1.5)
        droop = (u*8 - seg)*0.12
        hold_pts.append(f"{x:.0f},{300 - 44*(v - droop):.0f}")
    hold_d = "M" + " L".join(hold_pts)
    svg = svg_open('采样保持：给 SAR 四拍问答按下「暂停键」', h=500)
    svg += f'''
<text x="220" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">开关 + 保持电容 + 缓冲器</text>
<text x="18" y="145" font-size="11" fill="#475569">模拟输入</text>
<line x1="70" y1="140" x2="120" y2="140" stroke="#334155" stroke-width="2.5"/>
<circle cx="130" cy="140" r="3.5" fill="#334155"/>
<line x1="130" y1="140" x2="160" y2="112" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="0;0.2;0.26;0.9;0.94;1" dur="{DH}s" repeatCount="indefinite"/></line>
<circle cx="166" cy="140" r="3.5" fill="#334155"/>
<text x="108" y="106" font-size="11" font-weight="bold" fill="#334155">开关（第 8 章传输门）</text>
<line x1="166" y1="140" x2="220" y2="140" stroke="#334155" stroke-width="2.5"/>
<circle cx="220" cy="140" r="4" fill="#334155"/>
<line x1="220" y1="140" x2="220" y2="180" stroke="#334155" stroke-width="2"/>
<line x1="208" y1="180" x2="232" y2="180" stroke="#2563eb" stroke-width="3"/>
<line x1="208" y1="192" x2="232" y2="192" stroke="#2563eb" stroke-width="3"/>
<line x1="220" y1="192" x2="220" y2="210" stroke="#334155" stroke-width="2"/>
{gnd_sym(220, 224)}
<text x="200" y="190" text-anchor="end" font-size="10.5" fill="#2563eb">C_hold</text>
<polygon points="250,110 250,170 310,140" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="256" y="134" font-size="12" font-weight="bold" fill="#059669">+</text>
<text x="256" y="160" font-size="12" font-weight="bold" fill="#dc2626">−</text>
<line x1="220" y1="140" x2="250" y2="125" stroke="#334155" stroke-width="2"/>
<line x1="310" y1="140" x2="390" y2="140" stroke="#334155" stroke-width="2.5"/>
<text x="330" y="126" font-size="11" font-weight="bold" fill="#2563eb">去 ADC</text>
<circle cx="350" cy="140" r="3.5" fill="#334155"/>
<line x1="350" y1="140" x2="350" y2="185" stroke="#334155" stroke-width="2"/>
<line x1="350" y1="185" x2="244" y2="185" stroke="#334155" stroke-width="2"/>
<line x1="244" y1="185" x2="244" y2="155" stroke="#334155" stroke-width="2"/>
<line x1="244" y1="155" x2="250" y2="155" stroke="#334155" stroke-width="2"/>
<text x="60" y="270" font-size="11" fill="#059669" opacity="0">采样：C 充电跟上输入
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.05;0.22;0.27;1" dur="{DH}s" repeatCount="indefinite"/></text>
<text x="60" y="294" font-size="11" fill="#dc2626" opacity="0">保持：开关断开，C 记住最后一刻——但漏电让它慢慢下垂
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.3;0.34;0.88;0.93;1" dur="{DH}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="0;0.2;0.26;0.9;0.94;1" dur="{DH}s" repeatCount="indefinite"/>'
    svg += flow("M74,136 H126 M170,136 H216", DH/4, n=4, color="#059669", r=5) + '</g>'
    svg += f'''
<text x="590" y="86" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">输入正弦（上）→ 采样保持输出（下）</text>
<path d="{sin_d}" fill="none" stroke="#94a3b8" stroke-width="2"/>
<path d="{hold_d}" fill="none" stroke="#059669" stroke-width="2.5"/>
<line x1="430" y1="300" x2="750" y2="300" stroke="#64748b" stroke-width="1.2"/>
<text x="440" y="352" font-size="10.5" fill="#dc2626">阶梯=记住的值 · 微微下垂=droop（漏电/C）</text>
'''
    svg += caption("① 采样相：开关闭合，C_hold 充电追踪输入——追踪带宽要远大于信号带宽", "#059669", DH,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=430)
    svg += caption("② 保持相：开关断开，电容记住断开瞬间的电压——SAR 四拍问答期间输入被冻结", "#2563eb", DH,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.55;0.61;1", y=430)
    svg += caption("③ 两个非理想：droop（漏电流让电压斜坡下垂）+ 电荷注入（开关断开踢进一份误差电荷）", "#dc2626", DH,
                   "0;0;1;1", "0;0.61;0.67;1", y=430)
    svg += note_box("droop 率 = I_leak / C_hold——电容大下垂慢，但充电也慢；这就是第 8 章电荷注入在 ADC 前端的现身", 474, DH, "0;0.7;0.75;1", w=710)
    save('sample-hold.svg', svg + '</svg>')

# ======================= 图 28：电荷泵 =======================
def make_charge_pump():
    DC3 = 6
    ramp_pts = []
    for i in range(81):
        u = i/80
        x = 430 + 320*u
        ramp_pts.append(f"{x:.0f},{330-120*(1-np.exp(-3*u)):.0f}")
    ramp_d = "M" + " L".join(ramp_pts)
    svg = svg_open('电荷泵：电容当「斗提机」，不用电感也升压', h=522)
    svg += f'''
<text x="230" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">倍压电荷泵（两相时钟， Vin → 2Vin）</text>
<text x="18" y="106" font-size="12.5" font-weight="bold" fill="#b45309">Vin</text>
<line x1="50" y1="100" x2="110" y2="100" stroke="#334155" stroke-width="2.5"/>
<circle cx="120" cy="100" r="3.5" fill="#334155"/>
<line x1="120" y1="100" x2="150" y2="72" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DC3}s" repeatCount="indefinite"/></line>
<circle cx="156" cy="100" r="3.5" fill="#334155"/>
<text x="100" y="66" font-size="10.5" fill="#334155">S1（相1）</text>
<line x1="156" y1="100" x2="190" y2="100" stroke="#334155" stroke-width="2.5"/>
<line x1="192" y1="84" x2="192" y2="116" stroke="#7c3aed" stroke-width="3"/>
<line x1="204" y1="84" x2="204" y2="116" stroke="#7c3aed" stroke-width="3"/>
<text x="212" y="80" font-size="11" font-weight="bold" fill="#7c3aed">C1 飞跨</text>
<line x1="214" y1="100" x2="250" y2="100" stroke="#334155" stroke-width="2.5"/>
<circle cx="256" cy="100" r="3.5" fill="#334155"/>
<line x1="256" y1="100" x2="286" y2="72" stroke="#dc2626" stroke-width="3">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.9;0.96;1" dur="{DC3}s" repeatCount="indefinite"/></line>
<circle cx="292" cy="100" r="3.5" fill="#334155"/>
<text x="242" y="66" font-size="10.5" fill="#334155">S2（相2）</text>
<line x1="292" y1="100" x2="350" y2="100" stroke="#334155" stroke-width="2.5"/>
<circle cx="350" cy="100" r="4" fill="#334155"/>
<line x1="350" y1="100" x2="400" y2="100" stroke="#334155" stroke-width="2.5"/>
<text x="356" y="90" font-size="12" font-weight="bold" fill="#2563eb">2Vin 输出</text>
<line x1="350" y1="100" x2="350" y2="140" stroke="#334155" stroke-width="2"/>
<line x1="338" y1="140" x2="362" y2="140" stroke="#2563eb" stroke-width="3"/>
<line x1="338" y1="152" x2="362" y2="152" stroke="#2563eb" stroke-width="3"/>
<line x1="350" y1="152" x2="350" y2="170" stroke="#334155" stroke-width="2"/>
{gnd_sym(350, 184)}
<text x="368" y="150" font-size="10.5" fill="#2563eb">C2 水库</text>
<line x1="202" y1="112" x2="202" y2="150" stroke="#334155" stroke-width="2"/>
<circle cx="202" cy="150" r="3.5" fill="#334155"/>
<line x1="202" y1="150" x2="176" y2="174" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DC3}s" repeatCount="indefinite"/></line>
<text x="196" y="196" text-anchor="end" font-size="10.5" fill="#334155">S3（相1 接地）</text>
<line x1="202" y1="150" x2="202" y2="196" stroke="#334155" stroke-width="2"/>
<circle cx="202" cy="196" r="3.5" fill="#334155"/>
<line x1="202" y1="196" x2="228" y2="172" stroke="#dc2626" stroke-width="3">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.9;0.96;1" dur="{DC3}s" repeatCount="indefinite"/></line>
<text x="212" y="216" font-size="10.5" fill="#334155">S4（相2 接 Vin）</text>
<line x1="202" y1="196" x2="202" y2="220" stroke="#334155" stroke-width="2"/>
{gnd_sym(202, 234)}
<text x="60" y="280" font-size="11" fill="#059669" opacity="0">相1：C1 下端接地，上端充到 Vin
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DC3}s" repeatCount="indefinite"/></text>
<text x="60" y="304" font-size="11" fill="#dc2626" opacity="0">相2：C1 下端被抬到 Vin——上端=2Vin，向 C2 倒电荷
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DC3}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DC3}s" repeatCount="indefinite"/>'
    svg += flow("M54,96 H150 M160,96 H196 M202,146 V156", DC3/3, n=5, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.9;0.96;1" dur="{DC3}s" repeatCount="indefinite"/>'
    svg += flow("M202,192 V160 M210,96 H250 M296,96 H346 M350,104 V136", DC3/3, n=5, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="590" y="252" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">输出电压：几个周期爬到 2Vin</text>
<path d="{ramp_d}" fill="none" stroke="#2563eb" stroke-width="2.8"/>
<line x1="430" y1="330" x2="750" y2="330" stroke="#64748b" stroke-width="1.4"/>
<line x1="430" y1="210" x2="750" y2="210" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="700" y="204" font-size="10.5" fill="#2563eb">2Vin</text>
<text x="440" y="352" font-size="10.5" fill="#475569">每个周期 C1 倒一勺，C2 水位逐渐涨满</text>
'''
    svg += caption("① 相1：S1/S3 闭合——C1 上端接 Vin、下端接地，充电到 Vin（绿粒子灌满斗）", "#059669", DC3,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② 相2：S2/S4 闭合——C1 下端被抬到 Vin，上端瞬间 2Vin，向 C2 倒电荷（斗提机倒斗）", "#dc2626", DC3,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ 几轮之后 C2 涨到 2Vin——无电感、无反电动势、EMI 小，代价是只供得起小电流", "#2563eb", DC3,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("ICL7660 负压、MAX232 的 ±10V、运放负电源——都是这架斗提机；要电流大？请回 13.3 用电感 Boost", 474, DC3, "0;0.74;0.79;1", w=700)
    save('charge-pump.svg', svg + '</svg>')

# ======================= 图 29：一阶 RC 低通与波特图 =======================
def make_rc_lowpass():
    DLP = 7
    f_pts = np.linspace(0.05, 40, 121)
    mag_pts, pha_pts = [], []
    for f in f_pts:
        x = 430 + (np.log10(f)-np.log10(0.05))/(np.log10(40)-np.log10(0.05))*320
        H = 1/np.sqrt(1+f*f)
        mag_pts.append(f"{x:.0f},{150+90*(1-H):.0f}")
        pha = np.degrees(np.arctan(f))
        pha_pts.append(f"{x:.0f},{295+65*pha/90:.0f}")
    mag_d = "M" + " L".join(mag_pts)
    pha_d = "M" + " L".join(pha_pts)
    hi_in_pts = []
    for i in range(97):
        u = i/96
        x = 430 + 320*u
        y = 416 - 22*np.sin(u*12*np.pi)
        hi_in_pts.append(f"{x:.0f},{y:.0f}")
    sin_hi_in = "M" + " L".join(hi_in_pts)
    hi_pts = []
    for i in range(97):
        u = i/96
        x = 430 + 320*u
        y = 416 - 8*np.sin(u*12*np.pi - 1.2)
        hi_pts.append(f"{x:.0f},{y:.0f}")
    sin_hi_out = "M" + " L".join(hi_pts)
    svg = svg_open('一阶 RC 低通：一颗极点的人生观', h=520)
    svg += f'''
<text x="180" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">R 在前、C 下地 = 低通</text>
<text x="16" y="145" font-size="11" fill="#475569">输入</text>
{resistor_h(60, 150, 40, 'R')}
<line x1="140" y1="150" x2="180" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="180" cy="150" r="4" fill="#334155"/>
<line x1="180" y1="150" x2="240" y2="150" stroke="#334155" stroke-width="2.5"/>
<text x="246" y="155" font-size="11" font-weight="bold" fill="#2563eb">输出</text>
<line x1="180" y1="150" x2="180" y2="190" stroke="#334155" stroke-width="2"/>
<line x1="168" y1="190" x2="192" y2="190" stroke="#2563eb" stroke-width="3"/>
<line x1="168" y1="202" x2="192" y2="202" stroke="#2563eb" stroke-width="3"/>
<line x1="180" y1="202" x2="180" y2="220" stroke="#334155" stroke-width="2"/>
{gnd_sym(180, 234)}
<text x="200" y="200" font-size="10.5" fill="#2563eb">C</text>
<text x="60" y="280" font-size="11" fill="#475569">低频：C 容抗大≈开路 → 全通</text>
<text x="60" y="304" font-size="11" fill="#475569">高频：C 容抗小≈短路 → 被泄放</text>
'''
    svg += f'''
<text x="590" y="76" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">幅度：fc 后 −20dB/十倍频</text>
<path d="{mag_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<line x1="430" y1="150" x2="750" y2="150" stroke="#64748b" stroke-width="1.2"/>
<line x1="573" y1="150" x2="573" y2="258" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="573" y1="276" x2="573" y2="340" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="430" y1="177" x2="750" y2="177" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="3,3"/>
<text x="569" y="254" text-anchor="end" font-size="10.5" fill="#475569">fc</text>
<text x="700" y="170" font-size="10" fill="#dc2626">−3dB</text>
<text x="590" y="270" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">相位：0° → −90°（fc 处恰 −45°）</text>
<path d="{pha_d}" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<line x1="430" y1="300" x2="750" y2="300" stroke="#64748b" stroke-width="1.2"/>
<text x="440" y="384" font-size="10.5" font-weight="bold" fill="#475569">高频输入（灰）→ 输出（绿）：频率不变、幅度缩、相位滞后</text>
<path d="{sin_hi_in}" fill="none" stroke="#94a3b8" stroke-width="1.6"/>
<path d="{sin_hi_out}" fill="none" stroke="#059669" stroke-width="2.5"/>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DLP}s" begin="-0.3s" repeatCount="indefinite" path="M42,150 L58,150"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DLP}s" begin="-0.9s" repeatCount="indefinite" path="M142,150 L238,150"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DLP}s" begin="-1.5s" repeatCount="indefinite" path="M180,152 L180,188"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DLP}s" begin="-2.1s" repeatCount="indefinite" path="M176,240 L184,240 L180,234"/></circle>

<circle cx="430" cy="150" r="5.5" fill="#fff" stroke="#059669" stroke-width="3"><animateMotion dur="{DLP}s" repeatCount="indefinite" path="{mag_d}"/></circle>
<circle cx="430" cy="297" r="5" fill="#fff" stroke="#7c3aed" stroke-width="3"><animateMotion dur="{DLP}s" repeatCount="indefinite" path="{pha_d}"/></circle>
<circle cx="430" cy="424" r="5" fill="#fff" stroke="#059669" stroke-width="3"><animateMotion dur="{DLP}s" repeatCount="indefinite" path="{sin_hi_out}"/></circle>
'''
    svg += caption("① fc=1/(2πRC)：此处容抗=电阻，输出恰好 −3dB（半功率点）、相位 −45°", "#059669", DLP,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=460)
    svg += caption("② 每过十倍频，容抗小十倍、输出小十倍：−20dB/dec 直线——一颗极点的身份证", "#7c3aed", DLP,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.55;0.61;1", y=460)
    svg += caption("③ 相位最多拖到 −90°——一颗极点永远掀不翻反馈（见 12.7 稳定性），两颗就危险", "#dc2626", DLP,
                   "0;0;1;1", "0;0.61;0.67;1", y=460)
    svg += note_box("Sallen-Key、有源滤波、运放主极点——全是这颗种子的繁殖；看懂它，波特图会读一半", 494, DLP, "0;0.7;0.75;1", w=680)
    save('rc-lowpass.svg', svg + '</svg>')

# ======================= 图 30：齐纳稳压 =======================
def make_zener_regulator():
    DZ = 6
    svg = svg_open('齐纳稳压：拿电流换电压的「溢流阀」', h=500)
    svg += f'''
<text x="220" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">12V±波动 → Rs → 齐纳 5.6V</text>
<text x="16" y="94" font-size="12" font-weight="bold" fill="#b45309">12V±</text>
{resistor_h(60, 100, 40, 'Rs')}
<line x1="140" y1="100" x2="180" y2="100" stroke="#334155" stroke-width="2.5"/>
<circle cx="180" cy="100" r="4" fill="#334155"/>
<line x1="180" y1="100" x2="260" y2="100" stroke="#334155" stroke-width="2.5"/>
<text x="266" y="105" font-size="12" font-weight="bold" fill="#2563eb">5.6V 输出</text>
<line x1="180" y1="100" x2="180" y2="150" stroke="#334155" stroke-width="2.5"/>
<polygon points="180,150 168,178 192,178" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<line x1="160" y1="150" x2="168" y2="150" stroke="#7c3aed" stroke-width="3"/>
<line x1="164" y1="144" x2="168" y2="150" stroke="#7c3aed" stroke-width="3"/>
<line x1="168" y1="150" x2="196" y2="150" stroke="#7c3aed" stroke-width="3"/>
<line x1="180" y1="178" x2="180" y2="200" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(180, 214)}
<text x="200" y="168" font-size="10.5" fill="#7c3aed">齐纳（反接）</text>
<text x="60" y="270" font-size="11" fill="#dc2626" opacity="0">Vin 升高 → 齐纳多吸流，余压落在 Rs
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DZ}s" repeatCount="indefinite"/></text>
<text x="60" y="294" font-size="11" fill="#059669" opacity="0">负载加重 → 齐纳少吸流让位——Vout 纹丝不动
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DZ}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0.4;0.4;1;1" keyTimes="0;0.2;0.3;0.9;0.96;1" dur="{DZ}s" repeatCount="indefinite"/>'
    svg += flow("M64,96 H176 M180,104 V146 V196", DZ/3, n=5, color="#dc2626", r=5) + '</g>'
    svg += flow("M64,96 H176 M184,96 H256", DZ/3, n=5, color="#2563eb", r=5)
    svg += f'''
<text x="590" y="86" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">输入抖（灰）→ 输出稳（蓝）</text>
<path d="{sine_path(430, 750, 150, 22, n=96)}" fill="none" stroke="#94a3b8" stroke-width="2"/>
<line x1="430" y1="150" x2="750" y2="150" stroke="#2563eb" stroke-width="2.8"/>
<text x="700" y="140" font-size="10.5" fill="#2563eb">5.6V</text>
<text x="590" y="240" text-anchor="middle" font-size="11" fill="#475569">Rs 的账：Vin 最低时仍供 Iz_min；Vin 最高时齐纳吃掉差额</text>
<text x="590" y="264" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">Rs = (Vin_min − 5.6) / (Iz_min + I_load_max)</text>
'''
    svg += caption("① 齐纳击穿后电压钉在 5.6V——输入再涨，多余的压降全落在 Rs 上（齐纳多吸流）", "#dc2626", DZ,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② 负载加重抢电流，齐纳自动少吸让出份额——总流量恒定，分配自适应", "#059669", DZ,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ 代价全在功耗：负载不用电时齐纳全吃——所以齐纳只做基准/小功率，大功率去 9.3 LDO", "#b45309", DZ,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("水位一到就开闸放水——齐纳是电压的溢流阀；5.6V 附近温度系数最小（两种击穿机制温漂互消）", 474, DZ, "0;0.74;0.79;1", w=700)
    save('zener-regulator.svg', svg + '</svg>')

# ======================= 图 31：恒流源 =======================
def make_constant_current():
    DCC = 6
    svg = svg_open('恒流源：电压随便变，电流我包了', h=500)
    svg += f'''
<text x="220" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">射极负反馈恒流源（I = (V_B−0.7)/R_E，与负载无关）</text>
<text x="30" y="76" font-size="12.5" font-weight="bold" fill="#b45309">VCC</text>
<line x1="60" y1="70" x2="240" y2="70" stroke="#334155" stroke-width="2.5"/>
<rect x="150" y="86" width="80" height="34" rx="5" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="190" y="107" text-anchor="middle" font-size="10.5" fill="#475569">负载（可变）</text>
<line x1="190" y1="70" x2="190" y2="86" stroke="#334155" stroke-width="2.5"/>
<line x1="190" y1="120" x2="190" y2="140" stroke="#334155" stroke-width="2.5"/>
{npn_svg(190, 196)}
<line x1="190" y1="140" x2="190" y2="141" stroke="#334155" stroke-width="2.5"/>
{resistor_v(190, 262, 30, 'R_E')}
<line x1="190" y1="312" x2="190" y2="318" stroke="#334155" stroke-width="2"/>
{gnd_sym(190, 332)}
<rect x="48" y="176" width="46" height="40" rx="5" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="71" y="200" text-anchor="middle" font-size="10" font-weight="bold" fill="#2563eb">基准 V_B</text>
<line x1="94" y1="196" x2="155" y2="196" stroke="#334155" stroke-width="2"/>
<text x="240" y="140" font-size="10.5" fill="#dc2626" opacity="0">V_CE 随负载怎么变
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DCC}s" repeatCount="indefinite"/></text>
<text x="240" y="280" font-size="10.5" fill="#059669" opacity="0">I 被 R_E 钉死：纹丝不动
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DCC}s" repeatCount="indefinite"/></text>
'''
    svg += flow("M194,76 V116 M190,141 V160 V226 V297", DCC/3, n=5, color="#059669", r=5)
    svg += '''
<text x="590" y="86" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">I-V 特性：电压横扫，电流平躺</text>
<line x1="430" y1="210" x2="750" y2="210" stroke="#059669" stroke-width="3"/>
<line x1="430" y1="300" x2="750" y2="300" stroke="#64748b" stroke-width="1.4"/>
<line x1="430" y1="300" x2="430" y2="180" stroke="#64748b" stroke-width="1.4"/>
<text x="700" y="196" font-size="10.5" fill="#059669">I 恒定</text>
<text x="440" y="316" font-size="10" fill="#475569">0</text>
<text x="700" y="316" font-size="10" fill="#475569">V_CE 扫过全程</text>
<text x="446" y="200" font-size="10" fill="#475569">I</text>
<text x="590" y="250" text-anchor="middle" font-size="10.5" fill="#94a3b8">斜率≈0 ⇒ 输出阻抗极高（理想∞）</text>
'''
    svg += caption("① 基准把 V_B 钉死 → V_E=V_B−0.7 钉死 → I=V_E/R_E 钉死：电流与负载脱钩", "#059669", DCC,
                   "0;1;1;0;0", "0;0.03;0.22;0.28;1", y=430)
    svg += caption("② 负载变化只改 V_CE——管子默默吸收全部电压波动，电流纹丝不动", "#2563eb", DCC,
                   "0;0;1;1;0;0", "0;0.3;0.35;0.58;0.64;1", y=430)
    svg += caption("③ 温度捣乱？R_E 负反馈摁住（3.4 偏置同款机制）——这就是 11.2 差分对的「尾巴」", "#7c3aed", DCC,
                   "0;0;1;1", "0;0.64;0.7;1", y=430)
    svg += note_box("恒流源 = 会自适应的电阻：LED 驱动、传感器激励、电流镜负载、差分对长尾——四处都有它", 474, DCC, "0;0.74;0.79;1", w=690)
    save('constant-current.svg', svg + '</svg>')

# ======================= 图 32：峰值检测 =======================
def make_peak_detector():
    DPK = 7
    am_pts = []
    for i in range(121):
        u = i/120
        x = 430 + 320*u
        env = 0.55 + 0.45*np.sin(u*2*np.pi)
        am_pts.append(f"{x:.0f},{170 - 40*env*np.sin(u*14*np.pi):.0f}")
    am_d = "M" + " L".join(am_pts)
    pk_pts = []
    peak = 0.0
    for i in range(121):
        u = i/120
        x = 430 + 320*u
        env = 0.55 + 0.45*np.sin(u*2*np.pi)
        cur = 40*env
        peak = max(cur, peak - 6.0*(1/121)*40)
        pk_pts.append(f"{x:.0f},{170-peak:.0f}")
    pk_d = "M" + " L".join(pk_pts)
    svg = svg_open('峰值检测：只许上、不许下的单向记忆', h=522)
    svg += f'''
<text x="230" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">精密整流 + 保持电容 + 泄放电阻（缓冲级见 12.6）</text>
<text x="16" y="145" font-size="11" fill="#475569">输入</text>
<line x1="46" y1="140" x2="90" y2="140" stroke="#334155" stroke-width="2.5"/>
<polygon points="90,110 90,170 150,140" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="96" y="134" font-size="12" font-weight="bold" fill="#dc2626">−</text>
<text x="96" y="160" font-size="12" font-weight="bold" fill="#059669">+</text>
<line x1="46" y1="140" x2="90" y2="155" stroke="#334155" stroke-width="2"/>
<line x1="240" y1="140" x2="240" y2="100" stroke="#334155" stroke-width="2"/>
<line x1="240" y1="100" x2="90" y2="100" stroke="#334155" stroke-width="2"/>
<line x1="90" y1="100" x2="90" y2="125" stroke="#334155" stroke-width="2"/>
<line x1="150" y1="140" x2="174" y2="140" stroke="#334155" stroke-width="2.5"/>
<polygon points="198,140 174,128 174,152" fill="none" stroke="#334155" stroke-width="2.5"/>
<line x1="198" y1="128" x2="198" y2="152" stroke="#334155" stroke-width="3"/>
<line x1="198" y1="140" x2="240" y2="140" stroke="#334155" stroke-width="2.5"/>
<circle cx="240" cy="140" r="4" fill="#334155"/>
<line x1="240" y1="140" x2="240" y2="180" stroke="#334155" stroke-width="2"/>
<line x1="228" y1="180" x2="252" y2="180" stroke="#2563eb" stroke-width="3"/>
<line x1="228" y1="192" x2="252" y2="192" stroke="#2563eb" stroke-width="3"/>
<line x1="240" y1="192" x2="240" y2="210" stroke="#334155" stroke-width="2"/>
{gnd_sym(240, 224)}
<text x="224" y="190" text-anchor="end" font-size="10.5" fill="#2563eb">C_hold</text>
{resistor_v(300, 160, 30, 'R_bleed')}
<line x1="240" y1="140" x2="300" y2="140" stroke="#334155" stroke-width="2"/>
<line x1="300" y1="210" x2="300" y2="220" stroke="#334155" stroke-width="2"/>
{gnd_sym(300, 234)}
<line x1="300" y1="140" x2="360" y2="140" stroke="#334155" stroke-width="2.5"/>
<text x="366" y="145" font-size="11" font-weight="bold" fill="#2563eb">峰值输出</text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="0;0.3;0.36;0.86;0.92;1" dur="{DPK}s" repeatCount="indefinite"/>'
    svg += flow("M154,136 H194 M202,136 H236 M240,144 V176", DPK/4, n=4, color="#059669", r=4.5) + '</g>'
    svg += f'''
<text x="590" y="86" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">输入（灰，幅度渐变的正弦）vs 峰值输出（绿）</text>
<path d="{am_d}" fill="none" stroke="#94a3b8" stroke-width="1.8"/>
<path d="{pk_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<line x1="430" y1="170" x2="750" y2="170" stroke="#64748b" stroke-width="1"/>
<text x="440" y="290" font-size="10.5" fill="#059669">峰顶充电（跳上）→ 输入回落 → 电容记住（平台缓降=泄放）</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DPK}s" begin="-0.3s" repeatCount="indefinite" path="M48,140 L88,140"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DPK}s" begin="-0.9s" repeatCount="indefinite" path="M152,140 L172,140"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DPK}s" begin="-1.5s" repeatCount="indefinite" path="M200,140 L238,140 L240,104 L92,100"/></circle>
<circle r="5" fill="#059669">{linear_x_motion(DPK, pk_d, begin='-2.1s')}</circle>
<circle cx="560" cy="170" r="5" fill="none" stroke="#059669" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.7s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.2;0.95" dur="1.7s" repeatCount="indefinite"/></circle>

'''
    svg += caption("① 输入创「新高」：运放顶开二极管，C_hold 瞬间充到峰顶——只许上", "#059669", DPK,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=430)
    svg += caption("② 输入回落：二极管反偏关断，电容孤立守住峰值——不许下", "#2563eb", DPK,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.55;0.61;1", y=430)
    svg += caption("③ 泄放电阻决定遗忘速度：τ=R·C——表头要稳（τ≈1s），AGC 要快（τ≈10ms）", "#b45309", DPK,
                   "0;0;1;1", "0;0.61;0.67;1", y=430)
    svg += note_box("峰值表、振幅测量、音频 AGC、包络检波——全是「单向记忆」；二极管压降？运放已按 12.6 精密整流把它除掉了", 474, DPK, "0;0.7;0.75;1", w=720)
    save('peak-detector.svg', svg + '</svg>')

# ======================= 图 33：反相 Buck-Boost =======================
def make_inverting_buckboost():
    DBB = 6
    il_pts = []
    for i in range(97):
        u = i/96
        x = 430 + 320*u
        seg = (u*3) % 1.0
        y = 372 - (30*seg/0.5 if seg < 0.5 else 30*(1-seg)/0.5)
        il_pts.append(f"{x:.0f},{y:.0f}")
    il_d = "M" + " L".join(il_pts)
    svg = svg_open('反相 Buck-Boost：正电压进去，负电压出来', h=542)
    svg += f'''
<text x="230" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">+12V → −12V（占空比 50%）</text>
<text x="18" y="102" font-size="12.5" font-weight="bold" fill="#b45309">+12V</text>
<line x1="50" y1="96" x2="110" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="120" cy="96" r="3.5" fill="#334155"/>
<line x1="120" y1="96" x2="150" y2="68" stroke="#059669" stroke-width="3">
<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DBB}s" repeatCount="indefinite"/></line>
<circle cx="156" cy="96" r="3.5" fill="#334155"/>
<text x="100" y="69" font-size="11" font-weight="bold" fill="#334155">开关 SW</text>
<line x1="156" y1="96" x2="200" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="205" cy="96" r="4" fill="#334155"/>
<text x="166" y="86" font-size="10" fill="#7c3aed">开关节点</text>
<path d="M205,100 q-16,8 0,16 q16,8 0,16 q-16,8 0,16 q16,8 0,16" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<text x="222" y="142" font-size="12" font-weight="bold" fill="#7c3aed">电感 L（下地）</text>
<line x1="205" y1="96" x2="205" y2="100" stroke="#334155" stroke-width="2.5"/>
<line x1="205" y1="164" x2="205" y2="196" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(205, 210)}
<line x1="205" y1="96" x2="260" y2="96" stroke="#334155" stroke-width="2.5"/>
<polygon points="260,96 284,84 284,108" fill="none" stroke="#334155" stroke-width="2.5"/>
<line x1="260" y1="84" x2="260" y2="108" stroke="#334155" stroke-width="3"/>
<text x="248" y="78" font-size="10.5" fill="#dc2626">二极管（朝左吸）</text>
<line x1="284" y1="96" x2="340" y2="96" stroke="#334155" stroke-width="2.5"/>
<circle cx="340" cy="96" r="4" fill="#334155"/>
<line x1="340" y1="96" x2="396" y2="96" stroke="#334155" stroke-width="2.5"/>
<text x="344" y="86" font-size="12" font-weight="bold" fill="#2563eb">−12V 输出</text>
<line x1="340" y1="96" x2="340" y2="140" stroke="#334155" stroke-width="2"/>
<line x1="328" y1="140" x2="352" y2="140" stroke="#2563eb" stroke-width="3.5"/>
<line x1="328" y1="152" x2="352" y2="152" stroke="#2563eb" stroke-width="3.5"/>
<line x1="340" y1="152" x2="340" y2="170" stroke="#334155" stroke-width="2"/>
{gnd_sym(340, 184)}
<text x="358" y="150" font-size="10.5" fill="#2563eb">C（下极板接地，上极板负压）</text>
<text x="60" y="250" font-size="11" fill="#059669" opacity="0">闭合：电感从 +12V 储能
<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.06;0.4;0.46;1" dur="{DBB}s" repeatCount="indefinite"/></text>
<text x="60" y="274" font-size="11" fill="#dc2626" opacity="0">断开：电感经二极管把输出往下拽成负
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.52;0.56;0.9;0.96;1" dur="{DBB}s" repeatCount="indefinite"/></text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.4;0.46;1" dur="{DBB}s" repeatCount="indefinite"/>'
    svg += flow("M54,92 H150 M160,92 H201 M205,100 V188", DBB/3, n=5, color="#059669", r=5) + '</g>'
    svg += f'<g><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.9;0.96;1" dur="{DBB}s" repeatCount="indefinite"/>'
    svg += flow("M340,136 V92 H288 M284,92 H260 M256,92 H210 M205,100 V188", DBB/3, n=5, color="#dc2626", r=5) + '</g>'
    svg += f'''
<text x="440" y="252" font-size="11.5" font-weight="bold" fill="#7c3aed">电感电流（三角波）</text>
<path d="{il_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<line x1="430" y1="392" x2="750" y2="392" stroke="#2563eb" stroke-width="2.8"/>
<line x1="430" y1="300" x2="750" y2="300" stroke="#64748b" stroke-width="1.2"/>
<text x="700" y="388" font-size="10.5" fill="#2563eb">−12V</text>
<text x="440" y="412" font-size="11.5" font-weight="bold" fill="#2563eb">输出 = −D/(1−D) × Vin = −0.5/0.5 × 12 = −12V</text>
'''
    svg += caption("① 开关闭合：+12V 全加在电感上（下端接地），电流斜坡上升——与 Boost 同款储能", "#059669", DBB,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=460)
    svg += caption("② 开关断开：电感不许电流突变，把开关节点拽向负压——二极管接通，能量倒向负输出", "#dc2626", DBB,
                   "0;0;1;1;0;0", "0;0.28;0.33;0.5;0.56;1", y=460)
    svg += caption("③ Vout=−D/(1−D)·Vin：D=0.5 时 −Vin；D>0.5 幅值超过输入——升降压还能反相", "#7c3aed", DBB,
                   "0;0;1;1", "0;0.58;0.64;1", y=460)
    svg += note_box("Buck/Boost/Buck-Boost 一个妈：开关、电感、二极管的三种摆法——运放负电源、RS-232 电平都这么生", 494, DBB, "0;0.7;0.75;1", w=700)
    save('inverting-buckboost.svg', svg + '</svg>')

# ======================= 图 34：555 单稳态 =======================
# 时间自洽核算：RA=100kΩ、C=10µF → RC=1s；t=1.1·RC=1.1s，此刻 Vc=5(1−e^−1.1)≈3.34V≥2Vcc/3 ✓
def make_ne555_monostable():
    DM = 7
    pts = []
    for i in range(25):
        u = i/24
        x = 480 + 120*u
        v = 5*(1-np.exp(-1.1*u))
        pts.append(f"{x:.0f},{340-44*v:.1f}")
    vc_d = "M" + " L".join(pts)
    svg = svg_open('555 单稳态：一触发，亮一拍（t = 1.1·RC）', h=480)
    svg += f'''
<text x="250" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">触发一次 → 输出一个定宽脉冲（宽度只由 RC 决定）</text>
<text x="596" y="108" text-anchor="middle" font-size="10.5" fill="#475569">— OUT（3 脚）　— Vc（6 脚）</text>
<line x1="80" y1="80" x2="330" y2="80" stroke="#334155" stroke-width="2.5"/>
<text x="56" y="86" font-size="12.5" font-weight="bold" fill="#b45309">+5V</text>
<rect x="150" y="150" width="110" height="110" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="205" y="196" text-anchor="middle" font-size="15" font-weight="bold" fill="#334155">555</text>
<text x="205" y="214" text-anchor="middle" font-size="9.5" fill="#64748b">3R 分压 · RS · 放电管</text>
<circle cx="205" cy="80" r="4" fill="#334155"/>
<line x1="205" y1="80" x2="205" y2="150" stroke="#334155" stroke-width="2.5"/>
<text x="218" y="112" font-size="10" fill="#475569">Vcc(8)</text>
<circle cx="205" cy="260" r="4" fill="#334155"/>
<line x1="205" y1="260" x2="205" y2="290" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(205, 304)}
<text x="199" y="280" text-anchor="end" font-size="10" fill="#475569">GND(1)</text>
<line x1="150" y1="180" x2="118" y2="180" stroke="#334155" stroke-width="2.5"/>
<text x="146" y="192" text-anchor="end" font-size="10" fill="#475569">RST(4)</text>
<line x1="118" y1="180" x2="118" y2="80" stroke="#334155" stroke-width="2"/>
<circle cx="118" cy="80" r="3.5" fill="#334155"/>
<line x1="150" y1="230" x2="100" y2="230" stroke="#334155" stroke-width="2.5"/>
<text x="148" y="222" text-anchor="end" font-size="10" fill="#475569">TRIG(2)</text>
{resistor_v(100, 95, 30, '10k')}
<line x1="100" y1="140" x2="100" y2="230" stroke="#334155" stroke-width="2.5"/>
<line x1="100" y1="230" x2="100" y2="290" stroke="#334155" stroke-width="2.5"/>
<circle cx="100" cy="230" r="2.5" fill="#334155"/>
<circle cx="100" cy="290" r="2.5" fill="#334155"/>
<line x1="100" y1="230" x2="114" y2="258" stroke="#334155" stroke-width="2"/>
<text x="60" y="294" font-size="10" fill="#dc2626">按我触发</text>
{gnd_sym(100, 304)}
<line x1="260" y1="170" x2="285" y2="170" stroke="#334155" stroke-width="2"/>
<line x1="260" y1="185" x2="285" y2="185" stroke="#334155" stroke-width="2"/>
<line x1="285" y1="154" x2="285" y2="196" stroke="#334155" stroke-width="2.5"/>
<circle cx="285" cy="170" r="3.5" fill="#334155"/>
<circle cx="285" cy="185" r="3.5" fill="#334155"/>
<text x="297" y="180" font-size="10" fill="#475569">THR(6)+DIS(7)</text>
{resistor_v(285, 95, 44, 'RA 100k')}
<line x1="271" y1="196" x2="299" y2="196" stroke="#2563eb" stroke-width="3"/>
<line x1="271" y1="208" x2="299" y2="208" stroke="#2563eb" stroke-width="3"/>
<line x1="285" y1="208" x2="285" y2="240" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(285, 254)}
<text x="306" y="206" font-size="10" fill="#2563eb">C 10µF</text>
<line x1="240" y1="260" x2="240" y2="272" stroke="#334155" stroke-width="2.5"/>
<line x1="240" y1="272" x2="420" y2="272" stroke="#334155" stroke-width="2.5"/>
<text x="250" y="286" font-size="10" fill="#475569">OUT(3)</text>
<line x1="430" y1="120" x2="430" y2="350" stroke="#64748b" stroke-width="1.4"/>
<line x1="430" y1="350" x2="770" y2="350" stroke="#64748b" stroke-width="1.4"/>
<text x="426" y="124" text-anchor="end" font-size="10.5" fill="#475569">5V</text>
<text x="426" y="354" text-anchor="end" font-size="10.5" fill="#475569">0V</text>
<text x="766" y="364" text-anchor="end" font-size="10" fill="#64748b">t →</text>
<line x1="430" y1="193.5" x2="770" y2="193.5" stroke="#7c3aed" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="430" y1="266.8" x2="770" y2="266.8" stroke="#7c3aed" stroke-width="1" stroke-dasharray="4,3"/>
<text x="766" y="189" text-anchor="end" font-size="10" fill="#7c3aed">2Vcc/3</text>
<text x="766" y="262" text-anchor="end" font-size="10" fill="#7c3aed">Vcc/3</text>
<path d="{vc_d}" fill="none" stroke="#0891b2" stroke-width="2.8"/>
<path d="M440,300 H480 V140 H600 V300 H760" fill="none" stroke="#059669" stroke-width="3"/>
<text x="620" y="160" font-size="10.5" font-weight="bold" fill="#059669">OUT</text>
<text x="620" y="216" font-size="10.5" font-weight="bold" fill="#0891b2">Vc</text>
<line x1="480" y1="130" x2="600" y2="130" stroke="#475569" stroke-width="1.5"/>
<line x1="480" y1="124" x2="480" y2="136" stroke="#475569" stroke-width="1.5"/>
<line x1="600" y1="124" x2="600" y2="136" stroke="#475569" stroke-width="1.5"/>
<text x="540" y="124" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#475569">t = 1.1·RC ≈ 1.1s</text>
<text x="462" y="372" font-size="10" fill="#64748b">触发↓（按下瞬间）</text>
'''
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.26;0.3;0.6;0.66;1" dur="{DM}s" repeatCount="indefinite"/>'
    svg += flow("M285,88 V192", DM, n=4, color="#059669", r=4) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.76;0.8;0.94;1" dur="{DM}s" repeatCount="indefinite"/>'
    svg += flow("M285,212 V244", DM, n=3, color="#dc2626", r=4) + '</g>'
    svg += caption("① 稳态：OUT=低，放电管导通，C 被钉在 0V——它就这么睡着", "#475569", DM,
                   "0;1;1;0;0", "0;0.02;0.22;0.28;1", y=424)
    svg += caption("② 触发！2 脚 &lt; Vcc/3 → RS 翻转：OUT=高，放电管断开，C 开始充电", "#dc2626", DM,
                   "0;0;1;1;0;0", "0;0.24;0.3;0.6;0.66;1", y=424)
    svg += caption("③ 充电全程 OUT 保持高——Vc 沿指数爬升，t = 1.1·RA·C ≈ 1.1s", "#059669", DM,
                   "0;0;1;1;0;0", "0;0.34;0.4;0.7;0.76;1", y=424)
    svg += caption("④ Vc ≥ 2Vcc/3：RS 复位，OUT=低，放电管瞬间把 C 放空——回稳态", "#7c3aed", DM,
                   "0;0;1;1", "0;0.76;0.82;1", y=424)
    svg += note_box("「单稳」= 只有一个稳态。触发多宽都行，输出脉冲宽度只认 RA·C——定时器的本质：RC 定时，芯片在两个阈值之间当裁判。（5 脚接 0.01µF 去耦，别省）", 452, DM, w=680)
    save('ne555-monostable.svg', svg + '</svg>')

# ======================= 图 35：H 桥 =======================
def make_h_bridge():
    DH = 7
    svg = svg_open('H 桥：四只开关让电流「听指挥」掉头', h=480)
    svg += '''
<text x="400" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">两对角线闭合 = 电流方向；同臂直通 = 短路烧管</text>
<line x1="100" y1="80" x2="700" y2="80" stroke="#334155" stroke-width="2.5"/>
<text x="64" y="86" font-size="12.5" font-weight="bold" fill="#b45309">+12V</text>
<line x1="100" y1="340" x2="700" y2="340" stroke="#334155" stroke-width="2.5"/>
<text x="68" y="346" font-size="12.5" font-weight="bold" fill="#334155">GND</text>
<line x1="220" y1="80" x2="220" y2="110" stroke="#334155" stroke-width="2.5"/>
<rect x="212" y="110" width="16" height="60" rx="3" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="208" y="144" text-anchor="end" font-size="11.5" font-weight="bold" fill="#334155">Q1</text>
<line x1="220" y1="170" x2="220" y2="250" stroke="#334155" stroke-width="2.5"/>
<rect x="212" y="250" width="16" height="60" rx="3" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="208" y="284" text-anchor="end" font-size="11.5" font-weight="bold" fill="#334155">Q2</text>
<line x1="220" y1="310" x2="220" y2="340" stroke="#334155" stroke-width="2.5"/>
<line x1="580" y1="80" x2="580" y2="110" stroke="#334155" stroke-width="2.5"/>
<rect x="572" y="110" width="16" height="60" rx="3" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="604" y="144" font-size="11.5" font-weight="bold" fill="#334155">Q3</text>
<line x1="580" y1="170" x2="580" y2="250" stroke="#334155" stroke-width="2.5"/>
<rect x="572" y="250" width="16" height="60" rx="3" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="604" y="284" font-size="11.5" font-weight="bold" fill="#334155">Q4</text>
<line x1="580" y1="310" x2="580" y2="340" stroke="#334155" stroke-width="2.5"/>
<line x1="220" y1="210" x2="378" y2="210" stroke="#334155" stroke-width="2.5"/>
<line x1="422" y1="210" x2="580" y2="210" stroke="#334155" stroke-width="2.5"/>
<circle cx="400" cy="210" r="22" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="400" y="216" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">M</text>
<text x="400" y="180" text-anchor="middle" font-size="10.5" fill="#475569">电机</text>
<circle cx="220" cy="210" r="3.5" fill="#334155"/>
<circle cx="580" cy="210" r="3.5" fill="#334155"/>
<line x1="212" y1="125" x2="192" y2="125" stroke="#334155" stroke-width="1.5"/>
<text x="188" y="129" text-anchor="end" font-size="11" font-weight="bold" fill="#2563eb">A</text>
<line x1="212" y1="265" x2="192" y2="265" stroke="#334155" stroke-width="1.5"/>
<text x="188" y="269" text-anchor="end" font-size="11" font-weight="bold" fill="#dc2626">B</text>
<line x1="588" y1="125" x2="608" y2="125" stroke="#334155" stroke-width="1.5"/>
<text x="612" y="129" font-size="11" font-weight="bold" fill="#dc2626">B</text>
<line x1="588" y1="265" x2="608" y2="265" stroke="#334155" stroke-width="1.5"/>
<text x="612" y="269" font-size="11" font-weight="bold" fill="#2563eb">A</text>
<line x1="220" y1="80" x2="244" y2="80" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<line x1="244" y1="80" x2="244" y2="210" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<polygon points="244,120 238,134 250,134" fill="#94a3b8"/>
<line x1="238" y1="138" x2="250" y2="138" stroke="#94a3b8" stroke-width="2"/>
<line x1="220" y1="340" x2="244" y2="340" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<line x1="244" y1="210" x2="244" y2="340" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<polygon points="244,250 238,264 250,264" fill="#94a3b8"/>
<line x1="238" y1="268" x2="250" y2="268" stroke="#94a3b8" stroke-width="2"/>
<line x1="580" y1="80" x2="556" y2="80" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<line x1="556" y1="80" x2="556" y2="210" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<polygon points="556,120 550,134 562,134" fill="#94a3b8"/>
<line x1="550" y1="138" x2="562" y2="138" stroke="#94a3b8" stroke-width="2"/>
<line x1="580" y1="340" x2="556" y2="340" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<line x1="556" y1="210" x2="556" y2="340" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<polygon points="556,250 550,264 562,264" fill="#94a3b8"/>
<line x1="550" y1="268" x2="562" y2="268" stroke="#94a3b8" stroke-width="2"/>
<line x1="220" y1="210" x2="244" y2="210" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<line x1="580" y1="210" x2="556" y2="210" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,3"/>
<text x="256" y="112" font-size="9.5" fill="#94a3b8">体二极管（每管都有）</text>
'''
    svg += f'<g><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.44;0.5;1" dur="{DH}s" repeatCount="indefinite"/>'
    svg += flow("M220,84 V206 H378", DH/2, n=4, color="#059669", r=5)
    svg += flow("M422,210 H580 V336", DH/2, n=4, color="#059669", r=5) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.46;0.52;0.92;0.98;1" dur="{DH}s" repeatCount="indefinite"/>'
    svg += flow("M580,84 V206 H422", DH/2, n=4, color="#dc2626", r=5)
    svg += flow("M378,210 H220 V336", DH/2, n=4, color="#dc2626", r=5) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;0.9;0;0" keyTimes="0;0.54;0.6;0.7;1" dur="{DH}s" repeatCount="indefinite"/>'
    svg += flow("M220,88 V332", DH/2, n=5, color="#dc2626", r=5) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.72;0.78;0.9;0.96;1" dur="{DH}s" repeatCount="indefinite"/>'
    svg += flow("M422,206 H556 V88", DH, n=3, color="#7c3aed", r=5)
    svg += flow("M244,332 V214 H378", DH, n=3, color="#7c3aed", r=5)
    svg += flow("M378,210 H422", DH, n=2, color="#7c3aed", r=5) + '</g>'
    svg += caption("① 正转：A=1 → Q1+Q4 导通，电流 +12V→Q1→电机→Q4→GND——M 右转", "#059669", DH,
                   "0;1;1;0;0", "0;0.02;0.3;0.36;1", y=424)
    svg += caption("② 反转：B=1 → Q2+Q3 导通，电流整体掉头——换电机两根线就这么干", "#dc2626", DH,
                   "0;0;1;1;0;0", "0;0.36;0.42;0.68;0.74;1", y=424)
    svg += caption("③ 致命错误：同臂齐开 = +12V 直通 GND，毫秒级烧管——换向必须死区 1~2µs", "#b45309", DH,
                   "0;0;1;1;0;0", "0;0.54;0.6;0.78;0.84;1", y=424)
    svg += caption("④ 全关滑行：电感电流没处去，体二极管搭桥流回电源——动能回收，这就是刹车", "#7c3aed", DH,
                   "0;0;1;1", "0;0.84;0.9;1", y=424)
    svg += note_box("四个开关两个状态位——这就是 H 桥。驱动芯片（DRV8833/L298）把死区、自举、过流保护全打包；高侧管源极悬在电机电压上，要靠自举电容「举」着栅极才开得动。", 452, DH, w=700)
    save('h-bridge.svg', svg + '</svg>')

# ======================= 图 36：削波与钳位 =======================
# 波形核算：限幅 ±4V 进、削平在 ±2.7V（基准±2V+0.7）；钳位 ±3V 进、整体垫高 2.3V（峰值 3−0.7）→ −0.7~5.3V
def make_clipper_clamper():
    DC = 6
    inp1, out1 = [], []
    for x in range(70, 331, 5):
        y = 265 - 55*np.sin(2*np.pi*(x-70)/260)
        inp1.append(f"{x},{y:.1f}")
        out1.append(f"{x},{min(max(y, 224.5), 305.5):.1f}")
    inp2, out2 = [], []
    for x in range(430, 761, 5):
        y = 270 - 45*np.sin(2*np.pi*(x-430)/260)
        inp2.append(f"{x},{y:.1f}")
        out2.append(f"{x},{y-34.5:.1f}")
    d1in, d1out = "M" + " L".join(inp1), "M" + " L".join(out1)
    d2in, d2out = "M" + " L".join(inp2), "M" + " L".join(out2)
    svg = svg_open('削波与钳位：同一个 0.7V——一个当闸门，一个当垫脚石', h=460)
    svg += f'''
<text x="400" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">左：限幅（动幅度）　右：钳位（动直流）</text>
<circle cx="70" cy="112" r="14" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="70" y="116" text-anchor="middle" font-size="9" font-weight="bold" fill="#334155">AC</text>
<line x1="84" y1="112" x2="88" y2="112" stroke="#334155" stroke-width="2.5"/>
{resistor_h(108, 112, 44, '1k')}
<line x1="172" y1="112" x2="208" y2="112" stroke="#334155" stroke-width="2.5"/>
<circle cx="208" cy="112" r="3.5" fill="#334155"/>
<line x1="208" y1="112" x2="208" y2="98" stroke="#334155" stroke-width="2"/>
<polygon points="208,86 202,98 214,98" fill="#dc2626"/>
<line x1="202" y1="86" x2="214" y2="86" stroke="#dc2626" stroke-width="2.5"/>
<line x1="208" y1="86" x2="208" y2="60" stroke="#334155" stroke-width="2"/>
<line x1="160" y1="60" x2="256" y2="60" stroke="#334155" stroke-width="2.5"/>
<text x="100" y="66" font-size="11" font-weight="bold" fill="#b45309">基准 +2V</text>
<line x1="208" y1="112" x2="208" y2="138" stroke="#334155" stroke-width="2"/>
<polygon points="208,138 202,150 214,150" fill="#dc2626"/>
<line x1="202" y1="138" x2="214" y2="138" stroke="#dc2626" stroke-width="2.5"/>
<line x1="208" y1="150" x2="208" y2="176" stroke="#334155" stroke-width="2"/>
<line x1="160" y1="176" x2="256" y2="176" stroke="#334155" stroke-width="2.5"/>
<text x="100" y="182" font-size="11" font-weight="bold" fill="#b45309">基准 −2V</text>
<line x1="214" y1="112" x2="280" y2="112" stroke="#334155" stroke-width="2.5"/>
<line x1="60" y1="200" x2="60" y2="330" stroke="#64748b" stroke-width="1.4"/>
<line x1="60" y1="330" x2="340" y2="330" stroke="#64748b" stroke-width="1.4"/>
<line x1="60" y1="265" x2="340" y2="265" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="3,4"/>
<line x1="60" y1="224.5" x2="340" y2="224.5" stroke="#b45309" stroke-width="1" stroke-dasharray="5,4"/>
<line x1="60" y1="305.5" x2="340" y2="305.5" stroke="#b45309" stroke-width="1" stroke-dasharray="5,4"/>
<path d="{d1in}" fill="none" stroke="#94a3b8" stroke-width="2.2"/>
<path d="{d1out}" fill="none" stroke="#059669" stroke-width="2.8"/>
<text x="316" y="205" text-anchor="end" font-size="10" fill="#64748b">输入 ±4V</text>
<text x="98" y="220" text-anchor="end" font-size="10.5" font-weight="bold" fill="#059669">输出</text>
<text x="336" y="238" text-anchor="end" font-size="9.5" fill="#b45309">上限 +2.7V</text>
<text x="250" y="299" font-size="9.5" fill="#b45309">下限 −2.7V</text>
<circle cx="430" cy="112" r="14" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="430" y="116" text-anchor="middle" font-size="9" font-weight="bold" fill="#334155">AC</text>
<line x1="444" y1="112" x2="458" y2="112" stroke="#334155" stroke-width="2.5"/>
<line x1="458" y1="100" x2="458" y2="124" stroke="#2563eb" stroke-width="3"/>
<line x1="466" y1="100" x2="466" y2="124" stroke="#2563eb" stroke-width="3"/>
<text x="462" y="94" text-anchor="middle" font-size="10" fill="#2563eb">C 1µF</text>
<line x1="466" y1="112" x2="560" y2="112" stroke="#334155" stroke-width="2.5"/>
<circle cx="560" cy="112" r="3.5" fill="#334155"/>
<line x1="560" y1="112" x2="560" y2="122" stroke="#334155" stroke-width="2"/>
<line x1="554" y1="122" x2="566" y2="122" stroke="#059669" stroke-width="2.5"/>
<polygon points="560,122 554,134 566,134" fill="#059669"/>
<line x1="560" y1="134" x2="560" y2="158" stroke="#334155" stroke-width="2"/>
{gnd_sym(560, 172)}
<line x1="566" y1="112" x2="660" y2="112" stroke="#334155" stroke-width="2.5"/>
<text x="668" y="116" font-size="10.5" font-weight="bold" fill="#059669">输出</text>
<line x1="420" y1="185" x2="420" y2="335" stroke="#64748b" stroke-width="1.4"/>
<line x1="420" y1="335" x2="780" y2="335" stroke="#64748b" stroke-width="1.4"/>
<line x1="420" y1="270" x2="780" y2="270" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="3,4"/>
<line x1="420" y1="280.5" x2="780" y2="280.5" stroke="#b45309" stroke-width="1" stroke-dasharray="5,4"/>
<path d="{d2in}" fill="none" stroke="#94a3b8" stroke-width="2.2"/>
<path d="{d2out}" fill="none" stroke="#0891b2" stroke-width="2.8"/>
<text x="776" y="328" text-anchor="end" font-size="10" fill="#64748b">输入 ±3V</text>
<text x="600" y="184" font-size="10" fill="#0891b2">输出 −0.7~5.3V</text>
<text x="776" y="294" text-anchor="end" font-size="9.5" fill="#b45309">−0.7V</text>
'''
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.2;0.26;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M88,108 H204 V64", DC, n=4, color="#dc2626", r=4)
    svg += flow("M204,172 V116 H88", DC, n=4, color="#dc2626", r=4) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.56;0.62;0.78;0.84;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M446,116 H552 V158", DC, n=4, color="#059669", r=4) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1" keyTimes="0;0.84;0.9;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M566,108 H656", DC, n=3, color="#0891b2", r=4) + '</g>'
    svg += caption("① 限幅：输出想越过 基准+0.7V，二极管开闸泄流——波形顶部被削平", "#dc2626", DC,
                   "0;1;1;0;0", "0;0.02;0.2;0.26;1", y=400)
    svg += caption("② 双向版就是 ADC 引脚保护：两只二极管把信号锁进 ±0.7V——第一道墙", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.26;0.32;0.5;0.56;1", y=400)
    svg += caption("③ 钳位：负半周瞬间 D 导通，C 充到 ≈2.3V（峰值 3V − 0.7V）——此后 D 常关，C 变成串联电池", "#059669", DC,
                   "0;0;1;1;0;0", "0;0.56;0.62;0.78;0.84;1", y=400)
    svg += caption("④ 输出整体垫高：±3V 进来，−0.7~5.3V 出去——直流分量被恢复了", "#0891b2", DC,
                   "0;0;1;1", "0;0.84;0.9;1", y=400)
    svg += note_box("一句话分清：限幅动「幅度」（削顶），钳位动「直流」（垫高）。同一个 0.7V，闸门还是垫脚石，取决于二极管朝哪边、取样的是哪只。", 430, DC, w=690)
    save('clipper-clamper.svg', svg + '</svg>')

# ======================= 图 37：负反馈纠错 =======================
# 增益核算：1+R2/R1 = 1+5k/1k = 6；±0.5V → ±3V；反馈系数 R1/(R1+R2)=1/6
def make_neg_feedback():
    DC = 6
    vin_d = sine_path(60, 390, 320, 12)
    vout_d = sine_path(430, 772, 320, 72)
    svg = svg_open('负反馈：十万倍的蛮力，被一根线驯成 6 倍', h=506)
    svg += f'''
<circle cx="90" cy="220" r="21" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="M79,220 q5.5,-14 11,0 q5.5,14 11,0" fill="none" stroke="#2563eb" stroke-width="2"/>
<text x="90" y="190" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">vin ±0.5V</text>
<line x1="111" y1="220" x2="480" y2="220" stroke="#334155" stroke-width="2.5"/>
<polygon points="480,158 480,242 566,200" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="492" y="186" font-size="15" font-weight="bold" fill="#dc2626">−</text>
<text x="492" y="228" font-size="15" font-weight="bold" fill="#059669">+</text>
<text x="500" y="262" font-size="11.5" fill="#475569">LM358</text>
<line x1="566" y1="200" x2="566" y2="140" stroke="#334155" stroke-width="2.5"/>
{resistor_h(466, 140, 80, 'R2 5kΩ')}
<line x1="330" y1="140" x2="446" y2="140" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="140" r="4" fill="#334155"/>
<line x1="330" y1="140" x2="330" y2="180" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="180" r="4" fill="#334155"/>
<line x1="330" y1="180" x2="480" y2="180" stroke="#334155" stroke-width="2.5"/>
<line x1="330" y1="140" x2="40" y2="140" stroke="#334155" stroke-width="2.5"/>
{resistor_v(40, 160, 50)}
{gnd_sym(40, 244)}
<text x="64" y="166" font-size="10" font-weight="bold" fill="#b45309">R1 1kΩ</text>
<circle cx="330" cy="180" r="9" fill="none" stroke="#dc2626" stroke-width="2.5">
<animate attributeName="opacity" values="0.25;1;0.25" dur="1.4s" repeatCount="indefinite"/></circle>
<text x="322" y="170" text-anchor="end" font-size="11.5" font-weight="bold" fill="#dc2626">v− ≈ v+</text>
<line x1="566" y1="200" x2="630" y2="200" stroke="#334155" stroke-width="2.5"/>
<text x="640" y="205" font-size="13" font-weight="bold" fill="#dc2626">vout</text>
<line x1="60" y1="320" x2="392" y2="320" stroke="#64748b" stroke-width="1.6"/>
<path d="{vin_d}" fill="none" stroke="#2563eb" stroke-width="3"/>
<text x="64" y="288" font-size="10" font-weight="bold" fill="#2563eb">输入 ±0.5V</text>
<circle r="5.5" fill="#fff" stroke="#2563eb" stroke-width="3">{linear_x_motion(2.5, vin_d)}</circle>
<line x1="430" y1="320" x2="772" y2="320" stroke="#64748b" stroke-width="1.6"/>
<path d="{vout_d}" fill="none" stroke="#dc2626" stroke-width="3"/>
<text x="434" y="290" font-size="10" font-weight="bold" fill="#dc2626">输出 ±3V（同相 ×6）</text>
<circle r="5.5" fill="#fff" stroke="#dc2626" stroke-width="3">{linear_x_motion(2.5, vout_d)}</circle>
'''
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.2;0.26;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M115,224 H476", DC, n=4, color="#2563eb", r=4) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.26;0.32;0.78;0.84;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M562,196 V144 H334 V176", DC, n=5, color="#b45309", r=4) + '</g>'
    svg += caption("① 开环蛮力：放大 10 万倍——输入刚抬 0.1V，输出瞬间撞上电源轨", "#dc2626", DC,
                   "0;1;1;0;0", "0;0.02;0.2;0.26;1", y=418)
    svg += caption("② 反馈线：把输出按 R1:(R1+R2) 切下 1/6，送回反相端 v−", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.26;0.32;0.5;0.56;1", y=418)
    svg += caption("③ 运放继续调 vout，直到 v− = v+——残余误差只有 µV 级", "#059669", DC,
                   "0;0;1;1;0;0", "0;0.5;0.56;0.78;0.84;1", y=418)
    svg += caption("④ 增益 = 1 + R2/R1 = 6：蛮力被驯成电阻的规矩——增益不靠芯片靠电阻", "#7c3aed", DC,
                   "0;0;1;1", "0;0.84;0.9;1", y=418)
    svg += note_box("负反馈的魔法：运放出十万倍的蛮力盯误差，电阻定结果——「增益不靠芯片靠电阻，误差不到调不停」。12.1 的两条公理，全部从这里来。", 462, DC, w=700)
    save('neg-feedback.svg', svg + '</svg>')

# ======================= 图 38：积分器 =======================
# 方波 ±1V 进（周期 165px/半周 82.5px），RC=1ms：半周 ΔVout=−Vin·Δt/RC=±1V → 三角 ±1.75V 视觉夸张
def make_integrator():
    DC = 6
    vin_pts, vout_pts = [], []
    for i in range(65):
        ph = (i / 64 * 2) % 1
        x1 = 60 + 330 * i / 64
        y1 = 330 if ph < 0.5 else 370
        x2 = 430 + 342 * i / 64
        y2 = 315 + 70 * (ph / 0.5) if ph < 0.5 else 385 - 70 * ((ph - 0.5) / 0.5)
        vin_pts.append(f"{x1:.0f},{y1:.0f}")
        vout_pts.append(f"{x2:.0f},{y2:.0f}")
    vin_d = "M" + " L".join(vin_pts)
    vout_d = "M" + " L".join(vout_pts)
    svg = svg_open('积分器：方波进、三角波出——电容在「攒」电压', h=524)
    svg += f'''
<circle cx="90" cy="180" r="21" fill="none" stroke="#2563eb" stroke-width="2.5"/>
<path d="M79,186 h6 v-9 h7 v9 h7 v-9 h8" fill="none" stroke="#2563eb" stroke-width="2"/>
<text x="42" y="152" font-size="11.5" font-weight="bold" fill="#2563eb">vin ±1V 方波</text>
<line x1="111" y1="180" x2="170" y2="180" stroke="#334155" stroke-width="2.5"/>
{resistor_h(190, 180, 56, 'Rin 10kΩ')}
<line x1="266" y1="180" x2="330" y2="180" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="180" r="4" fill="#334155"/>
<line x1="330" y1="180" x2="480" y2="180" stroke="#334155" stroke-width="2.5"/>
<polygon points="480,158 480,242 566,200" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="492" y="186" font-size="15" font-weight="bold" fill="#dc2626">−</text>
<text x="492" y="228" font-size="15" font-weight="bold" fill="#059669">+</text>
<text x="500" y="262" font-size="11.5" fill="#475569">理想运放</text>
<line x1="440" y1="220" x2="480" y2="220" stroke="#334155" stroke-width="2.5"/>
<line x1="440" y1="220" x2="440" y2="252" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(440, 266)}
<line x1="330" y1="180" x2="330" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="330" y1="140" x2="380" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="380" y1="128" x2="380" y2="152" stroke="#2563eb" stroke-width="3"/>
<line x1="388" y1="128" x2="388" y2="152" stroke="#2563eb" stroke-width="3"/>
<text x="384" y="110" text-anchor="middle" font-size="10" fill="#2563eb">C 10nF</text>
<line x1="388" y1="140" x2="566" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="566" y1="140" x2="566" y2="200" stroke="#334155" stroke-width="2.5"/>
<line x1="566" y1="200" x2="630" y2="200" stroke="#334155" stroke-width="2.5"/>
<text x="640" y="205" font-size="13" font-weight="bold" fill="#dc2626">vout</text>
<line x1="60" y1="350" x2="392" y2="350" stroke="#64748b" stroke-width="1.6"/>
<path d="{vin_d}" fill="none" stroke="#2563eb" stroke-width="3"/>
<text x="64" y="300" font-size="10" font-weight="bold" fill="#2563eb">输入 ±1V · 1kHz</text>
<circle r="5.5" fill="#fff" stroke="#2563eb" stroke-width="3">{linear_x_motion(2.5, vin_d)}</circle>
<line x1="430" y1="350" x2="772" y2="350" stroke="#64748b" stroke-width="1.6"/>
<path d="{vout_d}" fill="none" stroke="#dc2626" stroke-width="3"/>
<text x="434" y="290" font-size="10" font-weight="bold" fill="#dc2626">输出 ±2.5V · 5Vpp（零均值示意）</text>
<circle r="5.5" fill="#fff" stroke="#dc2626" stroke-width="3">{linear_x_motion(2.5, vout_d)}</circle>
'''
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.2;0.26;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M115,176 H326 V136 H376", DC, n=4, color="#dc2626", r=4) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.26;0.32;0.5;0.56;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M376,136 H334 V184 H115", DC, n=4, color="#b45309", r=4) + '</g>'
    svg += caption("① 方波 +1V：恒流 i = Vin/Rin 给 C 充电——vout 匀速下滑（斜坡就是「积累」）", "#dc2626", DC,
                   "0;1;1;0;0", "0;0.02;0.2;0.26;1", y=418)
    svg += caption("② 方波翻到 −1V：电流反向，电容匀速放电——vout 匀速上爬", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.26;0.32;0.5;0.56;1", y=418)
    svg += caption("③ 一下一上接成三角波：积分器把「方块的快慢」变成「斜坡的高低」", "#059669", DC,
                   "0;0;1;1;0;0", "0;0.5;0.56;0.78;0.84;1", y=418)
    svg += caption("④ 增益变成斜率 dVout/dt = −Vin/RC：不是放大倍数，是时间整形", "#7c3aed", DC,
                   "0;0;1;1", "0;0.84;0.9;1", y=418)
    svg += note_box("积分器的灵魂：恒流充电容 = 匀速斜坡。实战必记：并在 C 上一只 10MΩ 泄放 V_OS，否则输出慢慢爬向电源轨（漂移饱和）；微分器相反——高频增益无限上升 = 噪声放大器，输入串 R、反馈并 C 摁住它。", 462, DC, w=700)
    save('integrator.svg', svg + '</svg>')

# ======================= 图 39：单电源虚地 =======================
# 0~12V 映射 y=320→130（15.83px/V）；中点 6V→y225；vin ±1.5V→±23.7px
def make_virtual_ground():
    DC = 6
    vin_d = sine_path(424, 760, 320, 23.7)
    vout_d = sine_path(424, 760, 225, 23.7)
    svg = svg_open('单电源运放：两只电阻造出「半个电源」的假地', h=506)
    svg += f'''
<text x="150" y="68" text-anchor="middle" font-size="11" font-weight="bold" fill="#dc2626">+12V</text>
<line x1="90" y1="80" x2="320" y2="80" stroke="#334155" stroke-width="2.5"/>
{resistor_v(150, 100, 50, 'R 10k')}
<line x1="150" y1="170" x2="150" y2="220" stroke="#334155" stroke-width="2.5"/>
<circle cx="150" cy="220" r="4" fill="#334155"/>
{resistor_v(150, 240, 50, 'R 10k')}
<line x1="150" y1="310" x2="150" y2="330" stroke="#334155" stroke-width="2.5"/>
<line x1="90" y1="330" x2="320" y2="330" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(150, 344)}
<text x="60" y="334" font-size="9.5" fill="#64748b">0V</text>
<text x="168" y="212" font-size="11" font-weight="bold" fill="#b45309">6V 虚地</text>
<line x1="150" y1="220" x2="236" y2="220" stroke="#334155" stroke-width="2.5"/>
<circle cx="250" cy="220" r="14" fill="#f8fafc" stroke="#2563eb" stroke-width="2"/>
<path d="M242,220 q4,-10 8,0 q4,10 8,0" fill="none" stroke="#2563eb" stroke-width="1.8"/>
<text x="206" y="196" text-anchor="middle" font-size="10" fill="#2563eb">vin ±1.5V</text>
<line x1="264" y1="220" x2="286" y2="220" stroke="#334155" stroke-width="2.5"/>
<line x1="286" y1="208" x2="286" y2="232" stroke="#2563eb" stroke-width="3"/>
<line x1="294" y1="208" x2="294" y2="232" stroke="#2563eb" stroke-width="3"/>
<text x="290" y="200" text-anchor="middle" font-size="10" fill="#2563eb">C 10µF</text>
<line x1="294" y1="220" x2="380" y2="220" stroke="#334155" stroke-width="2.5"/>
<polygon points="380,158 380,242 466,200" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="392" y="186" font-size="15" font-weight="bold" fill="#dc2626">−</text>
<text x="392" y="228" font-size="15" font-weight="bold" fill="#059669">+</text>
<line x1="466" y1="200" x2="466" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="466" y1="150" x2="350" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="350" y1="150" x2="350" y2="186" stroke="#334155" stroke-width="2.5"/>
<line x1="350" y1="186" x2="380" y2="186" stroke="#334155" stroke-width="2.5"/>
<text x="460" y="142" text-anchor="end" font-size="10" fill="#475569">跟随器：vout = v+</text>
<line x1="466" y1="200" x2="530" y2="200" stroke="#334155" stroke-width="2.5"/>
<text x="546" y="190" font-size="12" font-weight="bold" fill="#059669">vout</text>
<line x1="540" y1="120" x2="540" y2="330" stroke="#64748b" stroke-width="1.4"/>
<line x1="540" y1="130" x2="760" y2="130" stroke="#b45309" stroke-width="1" stroke-dasharray="5,4"/>
<line x1="540" y1="225" x2="760" y2="225" stroke="#2563eb" stroke-width="1" stroke-dasharray="5,4"/>
<line x1="540" y1="320" x2="760" y2="320" stroke="#64748b" stroke-width="1.4"/>
<path d="{vin_d}" fill="none" stroke="#94a3b8" stroke-width="2.2" stroke-dasharray="5,4"/>
<path d="{vout_d}" fill="none" stroke="#059669" stroke-width="2.8"/>
<circle r="5" fill="#fff" stroke="#059669" stroke-width="3"><animateMotion dur="2.5s" repeatCount="indefinite" path="{vout_d}"/></circle>
<text x="544" y="288" font-size="10" fill="#64748b">直接进：负半周撞地</text>
<text x="544" y="166" font-size="10" font-weight="bold" fill="#059669">骑上 6V：全程能走</text>
<text x="780" y="133" text-anchor="end" font-size="9.5" fill="#b45309">12V</text>
<text x="780" y="228" text-anchor="end" font-size="9.5" fill="#2563eb">6V</text>
<text x="780" y="323" text-anchor="end" font-size="9.5" fill="#64748b">0V</text>
'''
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.26;0.32;0.5;0.56;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M146,84 V326", DC, n=4, color="#b45309", r=4) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.78;0.84;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M364,216 H476", DC, n=3, color="#059669", r=4) + '</g>'
    svg += caption("① 单电源 0~12V：运放眼里没有负压——信号贴着 0V，负半周直接撞地被削没", "#dc2626", DC,
                   "0;1;1;0;0", "0;0.02;0.2;0.26;1", y=418)
    svg += caption("② 两只相等电阻分压：中点 = 6V——给信号造一个「假地」（虚地）", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.26;0.32;0.5;0.56;1", y=418)
    svg += caption("③ 交流经 C 骑上 6V：负半周落在 0V 之上，整条波形都能走", "#059669", DC,
                   "0;0;1;1;0;0", "0;0.5;0.56;0.78;0.84;1", y=418)
    svg += caption("④ 虚地不是真地：带载会被拖偏——讲究的场合上专用分压芯片", "#7c3aed", DC,
                   "0;0;1;1", "0;0.84;0.9;1", y=418)
    svg += note_box("口诀：没有负电源，两只电阻造中点；信号骑上虚地走，输出上下都不缺。提醒：虚地是信号基准、不是电源回流——大电流负载会把中点拖偏，讲究的场合用 TLE2426 这类分压芯片。", 462, DC, w=700)
    save('virtual-ground.svg', svg + '</svg>')

# ======================= 图 40：迟滞弛豫振荡器 =======================
# β=R2/(R1+R2)=0.5 → 门槛 ±3V；T=2RC·ln3=2.2ms(RC=1ms)，f≈455Hz；Vc 指数轨迹 10px/V
def make_schmitt_osc():
    DC = 6
    vc_pts = []
    for i in range(167):
        x = 60 + 332 * i / 166
        u = (x - 60) % 166
        if u < 83:
            vc = 6 - 9 * np.exp(-np.log(3) * u / 83)
        else:
            vc = -6 + 9 * np.exp(-np.log(3) * (u - 83) / 83)
        vc_pts.append(f"{x:.0f},{355 - 10 * vc:.1f}")
    vc_d = "M" + " L".join(vc_pts)
    sq_d = square_path(430, 772, 405, 305, periods=2)
    svg = svg_open('迟滞振荡器：方波从两只门槛之间自己「弹」出来', h=506)
    svg += f'''
<polygon points="480,92 480,176 566,134" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="492" y="120" font-size="15" font-weight="bold" fill="#dc2626">−</text>
<text x="492" y="158" font-size="15" font-weight="bold" fill="#059669">+</text>
<line x1="480" y1="120" x2="330" y2="120" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="120" r="4" fill="#334155"/>
<line x1="330" y1="120" x2="330" y2="130" stroke="#334155" stroke-width="2"/>
<line x1="318" y1="130" x2="342" y2="130" stroke="#2563eb" stroke-width="3"/>
<line x1="318" y1="138" x2="342" y2="138" stroke="#2563eb" stroke-width="3"/>
<line x1="330" y1="138" x2="330" y2="154" stroke="#334155" stroke-width="2"/>
{gnd_sym(330, 168)}
<text x="352" y="136" font-size="10" fill="#2563eb">C 100nF</text>
<line x1="450" y1="158" x2="480" y2="158" stroke="#334155" stroke-width="2.5"/>
<circle cx="450" cy="158" r="4" fill="#334155"/>
{resistor_v(450, 178, 32, 'R2 10k')}
{gnd_sym(450, 240)}
{resistor_v(450, 74, 36)}
<text x="428" y="98" text-anchor="end" font-size="12.5" font-weight="bold" fill="#b45309">R1 10k</text>
<line x1="450" y1="130" x2="450" y2="158" stroke="#334155" stroke-width="2.5"/>
<line x1="450" y1="54" x2="566" y2="54" stroke="#334155" stroke-width="2.5"/>
<line x1="566" y1="54" x2="566" y2="134" stroke="#334155" stroke-width="2.5"/>
<line x1="566" y1="134" x2="640" y2="134" stroke="#334155" stroke-width="2.5"/>
<text x="646" y="139" font-size="12" font-weight="bold" fill="#dc2626">vout</text>
<circle cx="610" cy="134" r="4" fill="#334155"/>
<line x1="610" y1="134" x2="610" y2="200" stroke="#334155" stroke-width="2.5"/>
{resistor_v(610, 220, 30, 'R 10k')}
<line x1="610" y1="270" x2="240" y2="270" stroke="#334155" stroke-width="2.5"/>
<line x1="240" y1="270" x2="240" y2="120" stroke="#334155" stroke-width="2.5"/>
<line x1="240" y1="120" x2="330" y2="120" stroke="#334155" stroke-width="2.5"/>
<line x1="60" y1="355" x2="392" y2="355" stroke="#64748b" stroke-width="1.6"/>
<line x1="60" y1="325" x2="392" y2="325" stroke="#b45309" stroke-width="1" stroke-dasharray="5,4"/>
<line x1="60" y1="385" x2="392" y2="385" stroke="#b45309" stroke-width="1" stroke-dasharray="5,4"/>
<path d="{vc_d}" fill="none" stroke="#059669" stroke-width="3"/>
<text x="64" y="301" font-size="10" font-weight="bold" fill="#059669">Vc ±3V 门槛间弹跳</text>
<line x1="430" y1="355" x2="772" y2="355" stroke="#64748b" stroke-width="1.6"/>
<path d="{sq_d}" fill="none" stroke="#dc2626" stroke-width="3"/>
<text x="460" y="291" font-size="10" font-weight="bold" fill="#dc2626">vout ±6V 方波</text>
'''
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.2;0.26;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M566,138 H606 V266 H244 V124 H326", DC, n=6, color="#dc2626", r=4) + '</g>'
    svg += f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.5;0.56;0.78;0.84;1" dur="{DC}s" repeatCount="indefinite"/>'
    svg += flow("M326,124 H244 V266 H606 V138 H566", DC, n=6, color="#059669", r=4) + '</g>'
    svg += caption("① 上电即 +6V：vout 经 R 给 C 充电，Vc 从 −3V 指数爬向 +6V", "#dc2626", DC,
                   "0;1;1;0;0", "0;0.02;0.2;0.26;1", y=418)
    svg += caption("② 爬到上门槛 +3V：比较器翻转，vout 跳到 −6V——门槛被当场搬走", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.26;0.32;0.5;0.56;1", y=418)
    svg += caption("③ Vc 掉头冲向下门槛 −3V：vout 又跳回 +6V——来回弹，停不下来", "#059669", DC,
                   "0;0;1;1;0;0", "0;0.5;0.56;0.78;0.84;1", y=418)
    svg += caption("④ T = 2RC·ln3 ≈ 2.2ms（f≈455Hz）：门槛越宽弹得越慢——555 无稳态的祖师爷", "#7c3aed", DC,
                   "0;0;1;1", "0;0.84;0.9;1", y=418)
    svg += note_box("不用晶振也能造时钟：迟滞管「状态」，RC 管「快慢」。口诀：门槛锁状态，电阻定快慢——窗口越宽弹得越慢，抗噪也越强。", 462, DC, w=700)
    save('schmitt-osc.svg', svg + '</svg>')

# ======================= 图 41：阻抗随频率 =======================
# C=1µF、L=1mH 的 |Z|-f 曲线；交点 f0=1/(2π√(LC))≈5kHz（Z≈32Ω）
def make_impedance_freq():
    DC = 6
    x0, x1, y0, y1 = 100, 760, 90, 360
    def px(f): return x0 + (np.log10(f) - 1) / 5.0 * (x1 - x0)
    def py(z): return y0 + (6 - (np.log10(z) + 1)) * 45.0
    fs = np.logspace(1, 6, 140)
    def cpath(zs):
        pts = [f"{px(f):.0f},{np.clip(py(z), y0, y1):.0f}" for f, z in zip(fs, zs)]
        return "M" + " L".join(pts)
    zc_d = cpath(1 / (2 * np.pi * fs * 1e-6))
    zl_d = cpath(2 * np.pi * fs * 1e-3)
    f0x, f0y = px(5033.0), py(31.6)
    yl = ''
    for k, lab in enumerate(['100kΩ', '10kΩ', '1kΩ', '100Ω', '10Ω', '1Ω', '0.1Ω']):
        yl += f'<text x="{x0-8}" y="{y0+45*k+5}" text-anchor="end" font-size="10.5" fill="#475569">{lab}</text>\n'
    grid = ''
    for k in range(1, 5):
        grid += f'<line x1="{x0+132*k}" y1="{y0}" x2="{x0+132*k}" y2="{y1}" stroke="#e2e8f0" stroke-width="1"/>\n'
    for k in range(1, 6):
        grid += f'<line x1="{x0}" y1="{y0+45*k}" x2="{x1}" y2="{y0+45*k}" stroke="#e2e8f0" stroke-width="1"/>\n'
    svg = svg_open('阻抗随频率：电容降价、电感涨价——寄生在暗处登场', h=480)
    svg += f'''
{grid}<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#334155" stroke-width="2"/>
<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#334155" stroke-width="2"/>
{yl}<text x="{x0+2}" y="{y1+16}" font-size="10.5" fill="#475569">10Hz</text>
<text x="{x0+132}" y="{y1+16}" text-anchor="middle" font-size="10.5" fill="#475569">100Hz</text>
<text x="{x0+264}" y="{y1+16}" text-anchor="middle" font-size="10.5" fill="#475569">1k</text>
<text x="{x0+396}" y="{y1+16}" text-anchor="middle" font-size="10.5" fill="#475569">10k</text>
<text x="{x0+528}" y="{y1+16}" text-anchor="middle" font-size="10.5" fill="#475569">100k</text>
<text x="{x1}" y="{y1+16}" text-anchor="end" font-size="10.5" fill="#475569">1MHz</text>
<text x="{x0-8}" y="{y0-16}" text-anchor="end" font-size="11" fill="#475569">|Z|（对数）</text>
<text x="{x1}" y="{y1+34}" text-anchor="end" font-size="11" fill="#475569">频率 f（对数轴）→</text>
{trace2(zc_d, DC, color="#2563eb", plen=1400)}
{trace2(zl_d, DC, color="#dc2626", plen=1400)}
<text x="{x0+8}" y="84" font-size="11.5" font-weight="bold" fill="#2563eb">Zc = 1/(2πfC)｜C=1µF</text>
<text x="{x1-6}" y="84" text-anchor="end" font-size="11.5" font-weight="bold" fill="#dc2626">Zl = 2πfL｜L=1mH</text>
<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#f59e0b" stroke-width="2" opacity="0.75"><animate attributeName="x1" values="{x0};{x1}" dur="{DC}s" repeatCount="indefinite"/><animate attributeName="x2" values="{x0};{x1}" dur="{DC}s" repeatCount="indefinite"/></line>
<circle cx="100" cy="126" r="6" fill="#fff" stroke="#2563eb" stroke-width="3"><animateMotion dur="{DC}s" repeatCount="indefinite" path="{zc_d}"/></circle>
<circle cx="100" cy="360" r="6" fill="#fff" stroke="#dc2626" stroke-width="3"><animateMotion dur="{DC}s" repeatCount="indefinite" path="{zl_d}"/></circle>
<circle cx="{f0x:.0f}" cy="{f0y:.0f}" r="5" fill="#f59e0b"/>
<line x1="{f0x+4:.0f}" y1="{f0y-6:.0f}" x2="{f0x+20:.0f}" y2="{f0y-34:.0f}" stroke="#b45309" stroke-width="1.5" opacity="0.8"/>
<text x="{f0x-77:.0f}" y="{f0y-36:.0f}" font-size="10.5" font-weight="bold" fill="#b45309">5kHz：Zc=Zl（谐振）</text>
'''
    svg += caption("① 低频区：电容≈断路、电感≈短路——两只元件都「没睡醒」", "#2563eb", DC, "0;1;1;0;0", "0;0.03;0.22;0.25;1", y=418)
    svg += caption("② 高频区全反过来：电容≈短路、电感≈断路——寄生接管电路", "#dc2626", DC, "0;0;1;1;0;0", "0;0.25;0.28;0.47;0.5;1", y=418)
    svg += caption("③ 交点 5kHz：Zc=Zl——LC 谐振，阻抗里只剩电阻（DCR/ESR）", "#b45309", DC, "0;0;1;1;0;0", "0;0.5;0.53;0.72;0.75;1", y=418)
    svg += caption("④ 一切阻抗都是频率的函数——选元件先问「工作在哪个频段」", "#059669", DC, "0;0;1;1", "0;0.75;0.78;1", y=418)
    svg += note_box("口诀：电容高频短路、电感低频短路——同一条线上寄生两头夹击。线≈1nH/mm、电容带 ESL，高频下它们反客为主（1.1-1.3 + 第 15 章去耦军规的物理根）。", 452, DC, x=400, w=690)
    save('impedance-freq.svg', svg + '</svg>')

# ======================= 图 42：运放内部三级流水线 =======================
# 741 框图：①差分输入级 ×100 → ②中间增益级 ×2000（Cc 密勒补偿）→ ③输出级 ×1；④偏置电流镜
def make_opamp_internals():
    DC = 6
    svg = svg_open('运放内部三级流水线：20 万倍增益是怎么攒出来的', h=480)
    svg += f'''
<text x="430" y="100" text-anchor="middle" font-size="13" font-weight="bold" fill="#7c3aed">总增益 = 各级相乘：100 × 2000 × 1 ≈ 20 万倍</text>
<text x="95" y="200" text-anchor="end" font-size="12.5" font-weight="bold" fill="#2563eb">IN+</text>
<text x="95" y="250" text-anchor="end" font-size="12.5" font-weight="bold" fill="#059669">IN−</text>
<line x1="100" y1="205" x2="130" y2="205" stroke="#2563eb" stroke-width="2.5"/>
<line x1="100" y1="245" x2="130" y2="245" stroke="#059669" stroke-width="2.5"/>
<rect x="130" y="175" width="160" height="90" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="210" y="202" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1e293b">① 差分输入级</text>
<text x="210" y="246" text-anchor="middle" font-size="10.5" fill="#475569">只放大差模 V+−V−</text>
<line x1="290" y1="220" x2="333" y2="220" stroke="#334155" stroke-width="2.5"/>
<polygon points="336,220 324,214 324,226" fill="#334155"/>
<rect x="336" y="165" width="180" height="110" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="426" y="197" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1e293b">② 中间增益级</text>
<text x="426" y="241" text-anchor="middle" font-size="10.5" fill="#475569">全部电压增益 ×2000</text>
<line x1="516" y1="220" x2="556" y2="220" stroke="#334155" stroke-width="2.5"/>
<polygon points="559,220 547,214 547,226" fill="#334155"/>
<rect x="559" y="175" width="160" height="90" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="639" y="202" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1e293b">③ 输出级</text>
<text x="639" y="246" text-anchor="middle" font-size="10.5" fill="#475569">推挽跟随 · 低阻输出</text>
<line x1="719" y1="220" x2="756" y2="220" stroke="#334155" stroke-width="2.5"/>
<polygon points="759,220 747,214 747,226" fill="#334155"/>
<text x="766" y="224" font-size="12.5" font-weight="bold" fill="#dc2626">OUT</text>
<line x1="370" y1="165" x2="370" y2="140" stroke="#7c3aed" stroke-width="2"/>
<line x1="370" y1="140" x2="414" y2="140" stroke="#7c3aed" stroke-width="2"/>
<line x1="414" y1="130" x2="414" y2="150" stroke="#7c3aed" stroke-width="3"/>
<line x1="422" y1="130" x2="422" y2="150" stroke="#7c3aed" stroke-width="3"/>
<line x1="422" y1="140" x2="480" y2="140" stroke="#7c3aed" stroke-width="2"/>
<line x1="480" y1="140" x2="480" y2="165" stroke="#7c3aed" stroke-width="2"/>
<text x="418" y="124" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#7c3aed">Cc 30pF 密勒补偿</text>
<rect x="345" y="320" width="175" height="60" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="432" y="346" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1e293b">④ 偏置电流镜</text>
<text x="432" y="367" text-anchor="middle" font-size="10.5" fill="#475569">全芯片的稳定偏流</text>
<line x1="372" y1="320" x2="232" y2="267" stroke="#94a3b8" stroke-width="1.6" stroke-dasharray="5,4"/>
<line x1="432" y1="320" x2="432" y2="267" stroke="#94a3b8" stroke-width="1.6" stroke-dasharray="5,4"/>
<line x1="492" y1="320" x2="621" y2="267" stroke="#94a3b8" stroke-width="1.6" stroke-dasharray="5,4"/>
{flow("M100,220 H755", DC, n=5, color="#2563eb", r=5)}
{flow("M432,318 V272", DC, n=2, color="#b45309", r=4, stagger=1.5)}
'''
    svg += caption("① 输入级只认差模：共模被电流镜「踢」掉——这就是 CMRR 的出生地", "#2563eb", DC, "0;1;1;0;0", "0;0.03;0.22;0.25;1", y=418)
    svg += caption("② 中间级扛下几乎所有增益；Cc 把主极点压到低频——换稳定，代价是压摆率", "#7c3aed", DC, "0;0;1;1;0;0", "0;0.25;0.28;0.47;0.5;1", y=418)
    svg += caption("③ 输出级 ×1 却关键：推挽跟随给低阻，过流保护藏在里面", "#059669", DC, "0;0;1;1;0;0", "0;0.5;0.53;0.72;0.75;1", y=418)
    svg += caption("④ 偏置镜像像自来水厂——每个 datasheet 参数都能对到具体位置", "#b45309", DC, "0;0;1;1", "0;0.75;0.78;1", y=418)
    svg += note_box("看戏指南：Vos/Ib 出生在①；GBW/压摆率由②的 Cc 决定；带载与短路能力看③——看框图比背参数表管事。", 452, DC, x=400, w=680)
    save('opamp-internals.svg', svg + '</svg>')

# ======================= 图 43：排故五步法流程 =======================
# 五步蛇形流程 + 巡游高亮框（10s 一圈，5 拍字幕同步）
def make_debug_flow():
    DC = 10
    boxes = [
        (80, 146, '① 症状确认', '先问后拆：偶发？温度？'),
        (296, 146, '② 二分定位', '对半分：log₂n 次测量'),
        (512, 146, '③ 单变量实验', '一次只改一个变量'),
        (512, 276, '④ 修根因', '别「再换一颗试试」'),
        (296, 276, '⑤ 回归验证', '全温全程全工况＋日志'),
    ]
    bx = ''
    for x, y, t, s in boxes:
        bx += f'<rect x="{x}" y="{y}" width="184" height="66" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>\n'
        bx += f'<text x="{x+92}" y="{y+24}" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">{t}</text>\n'
        bx += f'<text x="{x+92}" y="{y+52}" text-anchor="middle" font-size="10.5" fill="#475569">{s}</text>\n'
    beats = [
        ('① 症状确认：先问五个问题——一直坏还是偶发？温度相关？最近改过什么？', '#dc2626'),
        ('② 二分定位：中线一测去一半——64 个节点最多 6 次测量锁定', '#2563eb'),
        ('③ 单变量实验：一次只改一个变量——「再换一颗试试」是排故头号时间杀手', '#7c3aed'),
        ('④ 修根因不修症状：保险丝烧了，先问「为什么烧」再换', '#b45309'),
        ('⑤ 回归验证：全温、全程、全工况跑过才算修好；写日志给团队攒资产', '#059669'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.2, (i + 1) * 0.2
        if i < 4:
            caps += caption(txt, col, DC, "0;0;1;1;0;0", f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=418) + '\n'
        else:
            caps += caption(txt, col, DC, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=418) + '\n'
    svg = svg_open('排故五步法：把「玄学」拆成实验', h=480)
    svg += f'''
{bx}<line x1="264" y1="179" x2="293" y2="179" stroke="#334155" stroke-width="2.5"/>
<polygon points="296,179 284,173 284,185" fill="#334155"/>
<line x1="480" y1="179" x2="509" y2="179" stroke="#334155" stroke-width="2.5"/>
<polygon points="512,179 500,173 500,185" fill="#334155"/>
<line x1="604" y1="212" x2="604" y2="273" stroke="#334155" stroke-width="2.5"/>
<polygon points="604,276 598,264 610,264" fill="#334155"/>
<line x1="512" y1="309" x2="483" y2="309" stroke="#334155" stroke-width="2.5"/>
<polygon points="480,309 492,303 492,315" fill="#334155"/>
<rect x="74" y="140" width="196" height="78" rx="12" fill="none" stroke="#f59e0b" stroke-width="3" opacity="0.9">
<animate attributeName="x" values="74;290;506;506;290;74" keyTimes="0;0.2;0.4;0.6;0.8;1" dur="{DC}s" repeatCount="indefinite"/>
<animate attributeName="y" values="140;140;140;270;270;140" keyTimes="0;0.2;0.4;0.6;0.8;1" dur="{DC}s" repeatCount="indefinite"/>
</rect>
{flow("M120,179 H604 V309 H380", DC, n=5, color="#2563eb", r=5)}
'''
    svg += caps
    svg += note_box("五步都带「防自欺」设计：先问后拆 / 对数收敛 / 单变量 / 修根因 / 回归——排故不靠灵感，靠流程。", 452, DC, x=400, w=660)
    save('debug-flow.svg', svg + '</svg>')

# ======================= 图 96：故障速查：症状→嫌疑→验证（第 17 章 17.1-17.4） =======================
def make_fault_lookup():
    DF = 12
    rows = [
        ('电源', '#2563eb', '输出为 0', '保险丝/调整管开路', '断电测通断'),
        ('放大', '#dc2626', '高频尖叫（自激）', '容性负载/布局耦合', '输出串 47Ω 试验'),
        ('放大', '#7c3aed', '输出顶到电源轨', '反馈开路/输入超共模', '虚短检验：反相≈同相'),
        ('电源', '#b45309', '芯片反复重启', '电源跌落触发复位', '负载阶跃抓电源波形'),
    ]
    body = ''
    for i, (cat, col, sym, sus, ver) in enumerate(rows):
        y = 105 + i * 78
        cy = y + 28
        body += (f'<rect x="80" y="{y}" width="190" height="56" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2"/>'
                 f'<text x="175" y="{y+24}" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">{sym}</text>'
                 f'<text x="175" y="{y+46}" text-anchor="middle" font-size="10" fill="#64748b">{cat}类</text>')
        body += (f'<rect x="305" y="{y}" width="190" height="56" rx="10" fill="#f8fafc" stroke="{col}" stroke-width="2.5"/>'
                 f'<text x="400" y="{y+24}" text-anchor="middle" font-size="13" font-weight="bold" fill="{col}">{sus}</text>'
                 f'<text x="400" y="{y+46}" text-anchor="middle" font-size="10" fill="#64748b">头号嫌疑</text>')
        body += (f'<rect x="530" y="{y}" width="190" height="56" rx="10" fill="#f8fafc" stroke="#334155" stroke-width="2"/>'
                 f'<text x="625" y="{y+24}" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">{ver}</text>'
                 f'<text x="625" y="{y+46}" text-anchor="middle" font-size="10" fill="#64748b">验证手段</text>')
        body += (f'<line x1="270" y1="{cy}" x2="303" y2="{cy}" stroke="#334155" stroke-width="2"/>'
                 f'<polygon points="305,{cy} 294,{cy-6} 294,{cy+6}" fill="#334155"/>'
                 f'<line x1="495" y1="{cy}" x2="528" y2="{cy}" stroke="#334155" stroke-width="2"/>'
                 f'<polygon points="530,{cy} 519,{cy-6} 519,{cy+6}" fill="#334155"/>')
        p = f'M88,{cy} H712'
        body += flow(p, DF, n=2, color=col, r=5)
        body += (f'<circle cx="625" cy="{cy}" r="4.5" fill="none" stroke="{col}" stroke-width="2">'
                 f'<animate attributeName="r" values="4.5;9;4.5" dur="1.8s" begin="{-0.4*i}s" repeatCount="indefinite"/></circle>')
    oy = 425
    for j, step in enumerate(['电源去耦', '反馈相位裕度', '布线寄生耦合', '接地环路']):
        x = 60 + j * 170
        body += (f'<rect x="{x}" y="{oy}" width="150" height="40" rx="9" fill="#f8fafc" stroke="#7c3aed" stroke-width="2"/>'
                 f'<text x="{x+75}" y="{oy+25}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#7c3aed">{step}</text>')
        if j < 3:
            body += (f'<line x1="{x+150}" y1="{oy+20}" x2="{x+168}" y2="{oy+20}" stroke="#334155" stroke-width="2"/>'
                     f'<polygon points="{x+170},{oy+20} {x+159},{oy+14} {x+159},{oy+26}" fill="#334155"/>')
    body += flow("M68,445 H712", DF, n=2, color="#7c3aed", r=5)
    beats = [
        ('① 电源类：输出为 0/反复重启 → 先查保险丝与电容——断电测通断、负载阶跃抓波形', '#2563eb'),
        ('② 放大类：顶轨/尖叫 → 虚短检验（反相≈同相）与 47Ω 试验', '#dc2626'),
        ('③ 振荡类：先去耦、再查相位裕度、后查布线寄生、最后接地环路——顺序即排查顺序', '#7c3aed'),
        ('④ 先量电源：Bob Pease 的维修记录里，近一半故障藏在这里', '#b45309'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.25, (i + 1) * 0.25
        if i < 3:
            caps += caption(txt, col, DF, "0;0;1;1;0;0", f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=530) + '\n'
        else:
            caps += caption(txt, col, DF, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=530) + '\n'
    svg = svg_open('故障速查：症状 → 头号嫌疑 → 验证手段', h=560)
    svg += f'''
<text x="400" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">查案手册怎么用：三列对号入座，验证手段当场执行——每类故障一条链路</text>
{body}
'''
    svg += caps
    save('fault-lookup.svg', svg + '</svg>')

# ======================= 图 97：大师的排故智慧（第 18 章 18.1-18.3） =======================
def make_master_wisdom():
    DF = 12
    cols = [
        ('Bob Pease · 老中医', '#2563eb', [
            '先量电源——近一半故障藏在这里',
            '怀疑一切，包括你的仪器',
            '数字表测不出振荡 → 示波器复核',
            '记录一切：症状-假设-结果存档']),
        ('Jim Williams · 手术刀', '#dc2626', [
            '先想透，再动手',
            '测量前先在脑子里预测波形',
            '测量链不能改变被测对象',
            '把故障做小：最小可复现电路']),
        ('共通心法', '#7c3aed', [
            '慢观察',
            '快假设',
            '严验证',
            '电路永远是对的，错的是你的模型']),
    ]
    body = ''
    for i, (name, col, lines) in enumerate(cols):
        x = 35 + i * 250
        cx = x + 115
        body += f'<rect x="{x}" y="100" width="230" height="210" rx="12" fill="#f8fafc" stroke="{col}" stroke-width="2.5"/>'
        body += f'<text x="{cx}" y="126" text-anchor="middle" font-size="14.5" font-weight="bold" fill="{col}">{name}</text>'
        body += f'<line x1="{x+14}" y1="138" x2="{x+216}" y2="138" stroke="{col}" stroke-width="1.5" opacity="0.4"/>'
        for j, line in enumerate(lines):
            y = 166 + j * 38
            body += f'<circle cx="{x+20}" cy="{y-5}" r="3.5" fill="{col}"/>'
            body += f'<text x="{x+34}" y="{y}" font-size="11.5" fill="#334155">{line}</text>'
        body += flow(f'M{cx},110 V295', DF, n=2, color=col, r=5)
    oy = 345
    for j, step in enumerate(['先量电源', '预测波形再测量', '最小化复现', '示波器复核']):
        x = 60 + j * 170
        body += (f'<rect x="{x}" y="{oy}" width="150" height="44" rx="9" fill="#f8fafc" stroke="#b45309" stroke-width="2"/>'
                 f'<text x="{x+75}" y="{oy+27}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">{step}</text>')
        if j < 3:
            body += (f'<line x1="{x+150}" y1="{oy+22}" x2="{x+168}" y2="{oy+22}" stroke="#334155" stroke-width="2"/>'
                     f'<polygon points="{x+170},{oy+22} {x+159},{oy+16} {x+159},{oy+28}" fill="#334155"/>')
    body += flow('M68,367 H712', DF, n=2, color='#b45309', r=5)
    beats = [
        ('① Pease：先量电源——他的维修记录里近一半故障藏在这里', '#2563eb'),
        ('② Williams：测量前预测波形，预测与实测不符处就是理解缺口', '#dc2626'),
        ('③ 共通：慢观察、快假设、严验证——观察→假设→实验→结论', '#7c3aed'),
        ('④ 军规：先量电源、预测波形、最小化复现、示波器复核——现场最冷静的人', '#b45309'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.25, (i + 1) * 0.25
        if i < 3:
            caps += caption(txt, col, DF, "0;0;1;1;0;0", f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=440) + '\n'
        else:
            caps += caption(txt, col, DF, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=440) + '\n'
    svg = svg_open('大师的排故智慧：三份心法，一条军规', h=520)
    svg += f'''
<text x="400" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">金句逐条读，粒子替你走流程——军规清单在底部</text>
{body}
<text x="400" y="478" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">排故不是体力活，是科学方法——观察 → 假设 → 实验 → 结论，一次循环逼近真相</text>
'''
    svg += caps
    save('master-wisdom.svg', svg + '</svg>')

# ======================= 图 98：设计流程五部曲（第 14 章 14.1） =======================
def make_design_flow():
    DF = 12
    steps = [
        ('需求指标', '精度/带宽/功耗/温度', '#2563eb'),
        ('拓扑选择', '差分/单端、LDO/DCDC', '#2563eb'),
        ('器件选型', '绝对最大额定→电特性', '#7c3aed'),
        ('仿真验证', 'DC/瞬态/AC/温度', '#7c3aed'),
        ('降额与保护', '电容50-80%、电阻50%', '#b45309'),
        ('打样测试', '指标对照、不过回炉', '#059669'),
    ]
    n = len(steps)
    w, gap = 116, 13
    x0 = (800 - (n * w + (n - 1) * gap)) // 2
    y, h = 105, 120
    body = ''
    cx = []
    for i, (name, sub, col) in enumerate(steps):
        x = x0 + i * (w + gap)
        cx.append(x + w // 2)
        body += (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#f8fafc" stroke="{col}" stroke-width="2.5"/>'
                 f'<circle cx="{x+18}" cy="{y+22}" r="11" fill="{col}"/>'
                 f'<text x="{x+18}" y="{y+26}" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">{i+1}</text>'
                 f'<text x="{x+w//2}" y="{y+50}" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#1e293b">{name}</text>'
                 f'<text x="{x+w//2}" y="{y+74}" text-anchor="middle" font-size="9.5" fill="#475569">{sub}</text>')
        if i < n - 1:
            body += (f'<line x1="{x+w}" y1="{y+h//2}" x2="{x+w+gap}" y2="{y+h//2}" stroke="#334155" stroke-width="2"/>'
                     f'<polygon points="{x+w+gap+3},{y+h//2} {x+w+gap-4},{y+h//2-5} {x+w+gap-4},{y+h//2+5}" fill="#334155"/>')
    body += flow(f'M{x0+10},{y+h//2} H{x0+n*w+(n-1)*gap-10}', DF, n=3, color='#059669', r=5)
    # 迭代回环：仿真验证④ → 器件选型③（回炉）
    m = (cx[3] + cx[2]) / 2
    body += f'<path d="M{cx[3]},{y} Q{m},{y-25} {cx[2]},{y}" fill="none" stroke="#b45309" stroke-width="2" stroke-dasharray="4,3"/>'
    body += flow(f'M{cx[3]},{y} Q{m},{y-25} {cx[2]},{y}', DF, n=1, color='#b45309', r=4.5)
    beats = [
        ('① 需求指标先行：把"好用"翻译成数字——精度 mV？带宽 Hz？功耗 mA？', '#2563eb'),
        ('② 先选架构再选器件：差分还是单端？LDO 还是 DCDC？反馈还是开环？', '#2563eb'),
        ('③ 读 datasheet：绝对最大额定值 → 电特性表 → 典型特性曲线', '#7c3aed'),
        ('④ 降额设计：额定值是"会死的边界"，不是工作点——电容 50~80%、电阻 50%', '#b45309'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.25, (i + 1) * 0.25
        if i < 3:
            caps += caption(txt, col, DF, "0;0;1;1;0;0", f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=330) + '\n'
        else:
            caps += caption(txt, col, DF, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=330) + '\n'
    svg = svg_open('从需求到打样：六步流程', h=430)
    svg += f'''
<text x="400" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">六步一链，粒子从头走到尾——仿真不过，沿橙色回环回炉</text>
{body}
<text x="400" y="400" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">流程是螺旋不是直线：仿真验证不过 → 回炉改选型/降额——指标逐条对照再进下一步</text>
'''
    svg += caps
    save('design-flow.svg', svg + '</svg>')

# ======================= 图 99：思维工具箱四暗器（第 16 章 16.2） =======================
def make_thinking_toolbox():
    DF = 12
    cards = [
        ('内外归因', '#2563eb', '先换"已知好的"电源/线缆', '传感器，把故障域切成板内/板外', '开工第一步——30 秒排除一半嫌疑'),
        ('对比法', '#dc2626', '好板并排同点测量——差异即线索，玄学变科学', None, '量产批次不良、玄学故障'),
        ('极限法', '#b45309', '电压拉偏 ±10%、温度吹风/冷冻', '把偶发故障逼成必现', '偶发不现形就没法测'),
        ('隔离法', '#7c3aed', '断开疑似负载/后级，看前级是否恢复', None, '短路、过载、闩锁定位'),
    ]
    body = ''
    for i, (name, col, how1, how2, when) in enumerate(cards):
        x = 45 + (i % 2) * 370
        y = 100 + (i // 2) * 160
        body += (f'<rect x="{x}" y="{y}" width="340" height="130" rx="14" fill="#f8fafc" stroke="{col}" stroke-width="2.5"/>'
                 f'<text x="{x+24}" y="{y+34}" font-size="15" font-weight="bold" fill="{col}">{name}</text>')
        if how2:
            body += (f'<text x="{x+24}" y="{y+64}" font-size="11" fill="#334155">{how1}</text>'
                     f'<text x="{x+24}" y="{y+84}" font-size="11" fill="#334155">{how2}</text>'
                     f'<text x="{x+24}" y="{y+106}" font-size="10" fill="#64748b">何时用：{when}</text>')
        else:
            body += (f'<text x="{x+24}" y="{y+64}" font-size="11" fill="#334155">{how1}</text>'
                     f'<text x="{x+24}" y="{y+98}" font-size="10" fill="#64748b">何时用：{when}</text>')
    body += flow('M60,105 H740 V385 H60 V105', DF, n=3, color='#059669', r=5)
    beats = [
        ('① 内外归因：先换已知好的电源/线缆/传感器——30 秒排除一半嫌疑', '#2563eb'),
        ('② 对比法：好板并排同点测——差异即线索，玄学变科学', '#dc2626'),
        ('③ 极限法：电压拉偏 ±10%、温度吹风冷冻——把偶发故障逼成必现', '#b45309'),
        ('④ 隔离法：断开疑似负载/后级，看前级恢复——短路、闩锁现形', '#7c3aed'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.25, (i + 1) * 0.25
        if i < 3:
            caps += caption(txt, col, DF, "0;0;1;1;0;0", f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=445) + '\n'
        else:
            caps += caption(txt, col, DF, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=445) + '\n'
    svg = svg_open('思维工具箱：老手的四个暗器', h=500)
    svg += f'''
<text x="400" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">开工先归因 · 坏板找对比 · 偶发用极限 · 短路靠隔离</text>
{body}
<text x="400" y="478" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">四招组合就是老手的节奏——先内外、再对比、极限逼、隔离切</text>
'''
    svg += caps
    save('thinking-toolbox.svg', svg + '</svg>')

# ======================= 图 100：一点接地 vs 共用地线（第 15 章 15.2） =======================
def make_ground_star():
    DF = 12
    # 左卡：共用地线（错误）
    left = f'''
<rect x="30" y="100" width="350" height="270" rx="14" fill="#f8fafc" stroke="#dc2626" stroke-width="2.5"/>
<text x="54" y="132" font-size="15" font-weight="bold" fill="#dc2626">✗ 共用地线：压降踩进信号地</text>
<rect x="60" y="150" width="120" height="26" rx="6" fill="#f1f5f9" stroke="#334155" stroke-width="1.5"/>
<text x="120" y="158" text-anchor="middle" font-size="11" fill="#1e293b">负载 R_L</text>
<rect x="60" y="230" width="120" height="26" rx="6" fill="#f1f5f9" stroke="#334155" stroke-width="1.5"/>
<text x="120" y="247" text-anchor="middle" font-size="11" fill="#1e293b">放大器</text>
<line x1="120" y1="176" x2="120" y2="192" stroke="#dc2626" stroke-width="3"/>
<line x1="120" y1="256" x2="120" y2="192" stroke="#2563eb" stroke-width="1.5"/>
<line x1="120" y1="192" x2="300" y2="192" stroke="#dc2626" stroke-width="3"/>
<text x="210" y="176" text-anchor="middle" font-size="11" font-weight="bold" fill="#dc2626">共用段：R_地 · I×R = 100mV</text>
<text x="108" y="208" font-size="9.5" fill="#475569">A</text>
<text x="296" y="208" font-size="9.5" fill="#475569">B</text>
<line x1="300" y1="192" x2="300" y2="204" stroke="#334155" stroke-width="2"/>
<line x1="290" y1="204" x2="310" y2="204" stroke="#334155" stroke-width="2"/>
<line x1="293" y1="208" x2="307" y2="208" stroke="#334155" stroke-width="2"/>
<line x1="296" y1="212" x2="304" y2="212" stroke="#334155" stroke-width="2"/>
<text x="205" y="352" text-anchor="middle" font-size="10" fill="#64748b">10A × 0.01Ω = 100mV——比 5µV 信号大 4 个数量级</text>
{flow('M120,180 V192 H300', DF, n=2, color='#dc2626', r=5)}
<circle cx="120" cy="192" r="5" fill="none" stroke="#dc2626" stroke-width="2">
<animate attributeName="r" values="5;11;5" dur="1.6s" begin="0s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="1;0;1" dur="1.6s" begin="0s" repeatCount="indefinite"/>
</circle>'''
    # 右卡：星形一点接地（正确）
    right = f'''
<rect x="420" y="100" width="350" height="270" rx="14" fill="#f8fafc" stroke="#059669" stroke-width="2.5"/>
<text x="444" y="132" font-size="15" font-weight="bold" fill="#059669">✓ 星形一点接地：各自到汇点</text>
<rect x="450" y="150" width="120" height="26" rx="6" fill="#f1f5f9" stroke="#334155" stroke-width="1.5"/>
<text x="510" y="167" text-anchor="middle" font-size="11" fill="#1e293b">负载 R_L</text>
<rect x="450" y="230" width="120" height="26" rx="6" fill="#f1f5f9" stroke="#334155" stroke-width="1.5"/>
<text x="510" y="247" text-anchor="middle" font-size="11" fill="#1e293b">放大器</text>
<line x1="570" y1="176" x2="570" y2="188" stroke="#059669" stroke-width="3"/>
<line x1="570" y1="256" x2="570" y2="188" stroke="#2563eb" stroke-width="1.5"/>
<line x1="570" y1="188" x2="592" y2="188" stroke="#059669" stroke-width="3"/>
<line x1="570" y1="188" x2="592" y2="188" stroke="#2563eb" stroke-width="1.5"/>
<circle cx="592" cy="188" r="7" fill="#059669"/>
<text x="592" y="192" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">★</text>
<line x1="592" y1="195" x2="592" y2="204" stroke="#334155" stroke-width="2"/>
<line x1="582" y1="204" x2="602" y2="204" stroke="#334155" stroke-width="2"/>
<line x1="585" y1="208" x2="599" y2="208" stroke="#334155" stroke-width="2"/>
<line x1="588" y1="212" x2="596" y2="212" stroke="#334155" stroke-width="2"/>
<text x="595" y="352" text-anchor="middle" font-size="10" fill="#64748b">没有共用段——压降只落在自己那段，信号基准纹丝不动</text>
{flow('M570,180 V188 H590', DF, n=1, color='#059669', r=5)}
{flow('M570,250 V188 H590', DF, n=1, color='#2563eb', r=3.5)}'''
    beats = [
        ('① 共用地线：负载地与信号地共用一段 AB——大电流压降直接踩进信号基准', '#dc2626'),
        ('② 算账：10A × 0.01Ω 共用段 = 100mV——比 5µV 信号大四个数量级', '#dc2626'),
        ('③ 星形一点接地：大电流走自己的粗线到汇点，小信号单独走——互不污染', '#059669'),
        ('④ 心法：地不是"0V 参考点"，是电流回家的路——别让大电流踩小信号的路', '#059669'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.25, (i + 1) * 0.25
        if i < 3:
            caps += caption(txt, col, DF, "0;0;1;1;0;0", f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=430) + '\n'
        else:
            caps += caption(txt, col, DF, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=430) + '\n'
    svg = svg_open('一点接地：让大电流别踩小信号的路', h=500)
    svg += f'''
<text x="400" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">共用地线 = 压降共享；星形一点接地 = 压降隔离——模拟工程师的终极命题</text>
{left}
{right}
<text x="400" y="478" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">大电流回流与小信号地分开走，汇于星形点——避免大电流压降污染小信号基准</text>
'''
    svg += caps
    save('ground-star.svg', svg + '</svg>')

# ======================= 图 101：变压器：电压换电流（第 1 章 1.3） =======================
def make_transformer():
    DT = 12
    body = ''
    # 磁芯
    body += '<rect x="150" y="142" width="500" height="36" rx="8" fill="#cbd5e1" stroke="#64748b" stroke-width="1.5"/>'
    # 初级线圈（左，N1）
    body += '<rect x="130" y="100" width="26" height="140" rx="4" fill="#f1f5f9" stroke="#2563eb" stroke-width="2.5"/>'
    for k in range(7):
        y = 112 + k * 19
        body += f'<line x1="134" y1="{y}" x2="152" y2="{y}" stroke="#94a3b8" stroke-width="1.2"/>'
    body += '<text x="100" y="90" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#2563eb">V₁ · I₁</text>'
    body += '<text x="143" y="262" text-anchor="middle" font-size="11" font-weight="bold" fill="#2563eb">N₁ = 10T</text>'
    # 次级线圈（右，N2）
    body += '<rect x="644" y="100" width="26" height="140" rx="4" fill="#f1f5f9" stroke="#059669" stroke-width="2.5"/>'
    for k in range(7):
        y = 112 + k * 19
        body += f'<line x1="648" y1="{y}" x2="666" y2="{y}" stroke="#94a3b8" stroke-width="1.2"/>'
    body += '<text x="700" y="90" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#059669">V₂ = 2×V₁</text>'
    body += '<text x="657" y="262" text-anchor="middle" font-size="11" font-weight="bold" fill="#059669">N₂ = 20T</text>'
    # 初次级导线
    body += '<line x1="70" y1="170" x2="130" y2="170" stroke="#334155" stroke-width="2.5"/>'
    body += '<line x1="670" y1="170" x2="730" y2="170" stroke="#334155" stroke-width="2.5"/>'
    body += '<text x="40" y="186" font-size="11" fill="#475569">交流输入</text>'
    body += '<text x="740" y="186" font-size="11" fill="#475569">负载</text>'
    # 磁通箭头（磁芯内）
    body += '<path d="M160,160 L640,160" fill="none" stroke="#7c3aed" stroke-width="2" stroke-dasharray="5,3"/>'
    body += '<text x="400" y="130" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#7c3aed">磁通 Φ —— 连接两边的「无形轴」</text>'
    # 能量守恒条
    body += '<rect x="60" y="300" width="680" height="46" rx="9" fill="#fffbeb" stroke="#b45309" stroke-width="1.8"/>'
    body += '<text x="400" y="328" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">V₁·I₁ = V₂·I₂ —— 电压翻倍的地方电流减半，功率原样过（理想）</text>'
    # 粒子：磁通 + 初/次级电流（同步）
    body += flow('M166,160 H634', DT, n=2, color='#7c3aed', r=4.5)
    body += flow('M75,170 H128', DT, n=2, color='#dc2626', r=5)
    body += flow('M672,170 H728', DT, n=2, color='#059669', r=5)
    beats = [
        ('① 变比是「汇率」：V₂/V₁ = N₂/N₁ —— 匝数翻倍，电压就翻倍（这里 1:2 升压）', '#2563eb'),
        ('② 电流反着来：I₂/I₁ = N₁/N₂ —— 电压升高的地方，电流减半', '#059669'),
        ('③ 能量守恒：V₁·I₁ ≈ V₂·I₂ —— 变压器不产生能量，只换「形态」', '#b45309'),
        ('④ 隔离：初次级只有磁通耦合、没有导线相连——隔离电源与信号的地', '#7c3aed'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.25, (i + 1) * 0.25
        if i < 3:
            caps += caption(txt, col, DT, "0;0;1;1;0;0", f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=430) + '\n'
        else:
            caps += caption(txt, col, DT, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=430) + '\n'
    svg = svg_open('变压器：电压换电流，能量原样过', h=520)
    svg += f'''
<text x="400" y="62" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">变比 N₁:N₂ 决定电压电流的「汇率」——初次级之间没有导线相连</text>
{body}
<text x="400" y="490" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">磁通这根「无形的轴」把能量从初级搬到次级——这是隔离的物理根源</text>
'''
    svg += caps
    save('transformer.svg', svg + '</svg>')

# ======================= 图 44：分压器与带载误差（第 0 章首图） =======================
def make_divider_loading():
    DD = 8
    svg = svg_open('分压器：最容易上手，也最容易翻车的一招', h=600)
    svg += '''
<text x="215" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">空载：R1=R2 → 正好取一半</text>
<line x1="95" y1="150" x2="110" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="160" y1="150" x2="175" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="135" y1="172" x2="135" y2="210" stroke="#334155" stroke-width="2.5"/>
<circle cx="135" cy="172" r="3.5" fill="#334155"/>
<circle cx="135" cy="210" r="3.5" fill="#334155"/>
<line x1="110" y1="172" x2="160" y2="172" stroke="#334155" stroke-width="2.5"/>
<line x1="110" y1="210" x2="160" y2="210" stroke="#334155" stroke-width="2.5"/>
<text x="175" y="150" font-size="12.5" font-weight="bold" fill="#b45309">12V</text>
<text x="144" y="228" font-size="11" fill="#475569">5%</text>
''' + resistor_v(135, 248, 40, 'R1 10k') + '''
<circle cx="135" cy="328" r="3.5" fill="#334155"/>
''' + resistor_v(135, 348, 40, 'R2 10k') + '''
''' + gnd_sym(135, 430) + '''
<line x1="135" y1="328" x2="300" y2="328" stroke="#334155" stroke-width="2.5"/>
<circle cx="300" cy="328" r="3.5" fill="#334155"/>
<text x="306" y="350" font-size="12.5" font-weight="bold" fill="#2563eb">Vout</text>
<line x1="300" y1="328" x2="300" y2="400" stroke="#334155" stroke-width="2.5" stroke-dasharray="5,4"/>
<rect x="270" y="320" width="60" height="16" fill="#0284c7" rx="3"/>
<text x="300" y="332" text-anchor="middle" font-size="11" font-weight="bold" fill="#ffffff">50%</text>
<line x1="60" y1="180" x2="60" y2="372" stroke="#334155" stroke-width="2"/>
<path d="M54,180 L60,170 L66,180 Z" fill="#334155"/>
<path d="M54,372 L60,382 L66,372 Z" fill="#334155"/>
<text x="50" y="265" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#334155" transform="rotate(-90 50 265)">12V</text>
<line x1="64" y1="276" x2="84" y2="276" stroke="#f59e0b" stroke-width="2"/>
<line x1="64" y1="308" x2="84" y2="308" stroke="#dc2626" stroke-width="2"/>
<text x="56" y="280" text-anchor="end" font-size="10.5" font-weight="bold" fill="#f59e0b">6V</text>
<text x="56" y="312" text-anchor="end" font-size="10.5" font-weight="bold" fill="#dc2626">4V</text>
<text x="210" y="280" font-size="11" font-weight="bold" fill="#b45309">空载指针：到中点 = 6V</text>
<text x="210" y="312" font-size="11" font-weight="bold" fill="#dc2626">带载指针：矮一截 = 4V</text>
<path d="M88,180 L88,372" stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="6,4"/>
<path d="M82,186 L88,174 L94,186 Z" fill="#f59e0b"/>
''' + resistor_v(430, 328, 44, '', lcolor='#dc2626') + '''
<text x="398" y="414" text-anchor="end" font-size="12.5" font-weight="bold" fill="#dc2626">RL 10k</text>
<line x1="300" y1="328" x2="430" y2="328" stroke="#dc2626" stroke-width="2.5"/>
<line x1="430" y1="392" x2="430" y2="430" stroke="#dc2626" stroke-width="2.5"/>
''' + gnd_sym(430, 444) + '''
<text x="452" y="342" font-size="11" font-weight="bold" fill="#dc2626">接上负载：突然变矮</text>
<path d="M112,180 L112,308" stroke="#dc2626" stroke-width="3" fill="none" stroke-dasharray="6,5" opacity="0">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.19;0.23;0.4;0.45;1" dur="8s" repeatCount="indefinite"/></path>
<polygon points="106,302 112,310 118,302" fill="#dc2626" opacity="0">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.19;0.23;0.4;0.45;1" dur="8s" repeatCount="indefinite"/></polygon>
<rect x="270" y="320" width="60" height="16" fill="#dc2626" rx="3" opacity="0">
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.19;0.23;0.4;0.45;1" dur="8s" repeatCount="indefinite"/></rect>
<text x="300" y="332" text-anchor="middle" font-size="11" font-weight="bold" fill="#ffffff" opacity="0">33%
<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.19;0.23;0.4;0.45;1" dur="8s" repeatCount="indefinite"/></text>
<text x="245" y="470" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309" opacity="0">Vout = 12 × 5k / (10k + 5k) = 4V
<animate attributeName="opacity" values="0;0;0;1;1;0;0" keyTimes="0;0.21;0.24;0.28;0.4;0.45;1" dur="8s" repeatCount="indefinite"/></text>
<circle r="5.5" fill="#f59e0b">
<animateMotion dur="8s" repeatCount="indefinite" path="M175,150 L135,150 L135,248" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5.5" fill="#f59e0b">
<animateMotion dur="8s" repeatCount="indefinite" path="M135,308 L135,348" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5.5" fill="#f59e0b">
<animateMotion dur="8s" repeatCount="indefinite" path="M135,408 L135,430" keyPoints="0;1" keyTimes="0;1"/></circle>
<line x1="410" y1="70" x2="410" y2="496" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="600" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">算式：Vout = 12 × R2/(R1+R2)</text>
<text x="440" y="100" font-size="13" font-weight="bold" fill="#2563eb">第一步 先算「下面那坨」的总电阻</text>
<text x="456" y="126" font-size="12" fill="#475569">R下 = R2 ∥ RL = 10k ∥ 10k = 5k</text>
<text x="440" y="164" font-size="13" font-weight="bold" fill="#2563eb">第二步 再用分压公式</text>
<text x="456" y="190" font-size="12" fill="#475569">Vout = 12V × 5k / (10k + 5k) = 4V</text>
<line x1="440" y1="212" x2="780" y2="212" stroke="#cbd5e1" stroke-width="1"/>
<rect x="452" y="230" width="96" height="26" fill="#2563eb" rx="4"/>
<text x="500" y="248" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">蓝色 6V</text>
<text x="566" y="249" font-size="12" fill="#475569">按 50% 白算的那份（错）</text>
<line x1="440" y1="282" x2="780" y2="282" stroke="#cbd5e1" stroke-width="1"/>
<rect x="452" y="298" width="55" height="26" fill="#dc2626" rx="4"/>
<text x="479" y="316" text-anchor="middle" font-size="12" font-weight="bold" fill="#ffffff">红色 4V</text>
<text x="520" y="317" font-size="12" fill="#475569">带载后的真实值（少了 33%）</text>
<text x="440" y="358" font-size="12.5" font-weight="bold" fill="#b45309">结论：分压器输出的不是「电压」，是「比值」——</text>
<text x="440" y="380" font-size="12.5" fill="#475569">背后接什么，它就跟着变。要稳，就得把源阻抗压下去。</text>
<text x="440" y="424" font-size="12.5" font-weight="bold" fill="#059669">三条活路：</text>
<text x="456" y="446" font-size="12" fill="#475569">① 后级输入阻抗 ≫ R2（如 1MΩ 的 ADC 输入）</text>
<text x="456" y="468" font-size="12" fill="#475569">② R1/R2 取小（10k→1k）：但静态电流和功耗上去了</text>
<text x="456" y="490" font-size="12" fill="#475569">③ 后面跟一级运放缓冲（第 12 章）——教科书答案</text>
'''
    svg += caption("① 空载：R1、R2 各分一半——Vout = 6V，指针稳稳停在正中", "#2563eb", DD,
                   "0;1;1;0;0", "0;0.04;0.2;0.25;1", y=512)
    svg += caption("② 挂上 RL=10k：R2∥RL 只剩 5k——Vout 塌到 4V，指针矮了三分之一", "#dc2626", DD,
                   "0;0;1;1;0;0", "0;0.42;0.47;0.7;0.76;1", y=512)
    svg += caption("③ 分压比会跟着负载变：要稳，就把源阻抗压到远小于负载阻抗", "#059669", DD,
                   "0;0;1;1", "0;0.78;0.84;1", y=512)
    svg += note_box("分压器是阻抗问题：算之前先问一句「它后面接什么」——Vout = Vin × R下 / (R上 + R下)", 558, DD,
                    "0;0.88;0.92;1", w=770)
    save('divider-loading.svg', svg + '</svg>')

# ======================= 图 45：BJT 三个工作区 =======================
def make_bjt_regions():
    DB = 8
    cur = "M456,214 L460,224 L464,236 L470,250 L476,260 L507,260 L620,260 L700,260 L790,259"
    svg = svg_open('BJT 三个工作区：看两个 PN 结的脸色', h=560)
    svg += f'''
<text x="210" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">判据看两个结，不看心情</text>
{npn_svg(130, 190)}
<line x1="105" y1="140" x2="105" y2="170" stroke="#334155" stroke-width="2.5"/>
<text x="30" y="134" font-size="11.5" font-weight="bold" fill="#b45309">+12V</text>
{resistor_v(105, 140, 40, '')}
<text x="168" y="161" font-size="12.5" font-weight="bold" fill="#b45309">R_C 2k</text>
<line x1="130" y1="135" x2="130" y2="170" stroke="#334155" stroke-width="2.5"/>
<line x1="50" y1="190" x2="95" y2="190" stroke="#334155" stroke-width="2.5"/>
{resistor_v(70, 190, 40, '')}
<text x="70" y="264" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">R_B 300k</text>
<line x1="70" y1="110" x2="70" y2="170" stroke="#334155" stroke-width="2.5"/>
<line x1="70" y1="110" x2="105" y2="110" stroke="#334155" stroke-width="2.5"/>
<text x="18" y="106" font-size="11.5" font-weight="bold" fill="#b45309">+12V</text>
<line x1="130" y1="245" x2="130" y2="285" stroke="#334155" stroke-width="2.5"/>
{resistor_v(130, 285, 40, '')}
<text x="150" y="310" font-size="11" font-weight="bold" fill="#475569">R_E 100</text>
<line x1="130" y1="325" x2="130" y2="350" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(130, 364)}
<text x="140" y="232" font-size="11" fill="#475569">I_B=(12−0.7)/300k</text>
<text x="140" y="268" font-size="11" fill="#dc2626">≈38µA → I_C ≈ 3.8mA</text>
<line x1="286" y1="76" x2="286" y2="388" stroke="#cbd5e1" stroke-width="1"/>
<text x="300" y="88" font-size="12.5" font-weight="bold" fill="#334155">三个工作区</text>
<text x="306" y="122" font-size="12" fill="#475569">发射结</text>
<text x="394" y="122" font-size="12" fill="#475569">集电结</text>
<text x="300" y="152" font-size="12.5" font-weight="bold" fill="#64748b">截止</text>
<text x="306" y="178" font-size="11.5" fill="#dc2626">反偏</text>
<text x="394" y="178" font-size="11.5" fill="#dc2626">反偏</text>
<text x="300" y="208" font-size="12.5" font-weight="bold" fill="#2563eb">放大</text>
<text x="306" y="234" font-size="11.5" fill="#059669">正偏</text>
<text x="394" y="234" font-size="11.5" fill="#dc2626">反偏</text>
<text x="300" y="264" font-size="12.5" font-weight="bold" fill="#dc2626">饱和</text>
<text x="306" y="290" font-size="11.5" fill="#059669">正偏</text>
<text x="394" y="290" font-size="11.5" fill="#059669">正偏</text>
<text x="300" y="332" font-size="12" font-weight="bold" fill="#64748b">≈ 断路（开关打开）</text>
<text x="300" y="356" font-size="12" font-weight="bold" fill="#2563eb">I_C = β·I_B</text>
<text x="300" y="380" font-size="12" font-weight="bold" fill="#dc2626">≈ 闭合开关（β 失效）</text>
<text x="470" y="60" font-size="12.5" font-weight="bold" fill="#334155">输出特性：负载线切过哪里，就是哪个区</text>
<line x1="450" y1="332" x2="790" y2="332" stroke="#64748b" stroke-width="1.6"/>
<line x1="450" y1="332" x2="450" y2="92" stroke="#64748b" stroke-width="1.6"/>
<text x="442" y="86" text-anchor="end" font-size="11" fill="#475569">I_C</text>
<text x="444" y="336" text-anchor="end" font-size="10.5" fill="#475569">0</text>
<text x="444" y="296" text-anchor="end" font-size="10.5" fill="#475569">2mA</text>
<text x="444" y="256" text-anchor="end" font-size="10.5" fill="#475569">4mA</text>
<text x="444" y="218" text-anchor="end" font-size="10.5" font-weight="bold" fill="#dc2626">6mA 饱和</text>
<line x1="450" y1="260" x2="588" y2="260" stroke="#7c3aed" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="588" y1="260" x2="588" y2="332" stroke="#7c3aed" stroke-width="1" stroke-dasharray="3,3"/>
<rect x="450" y="214" width="138" height="118" fill="#dc2626" opacity="0.10"/>
<text x="790" y="352" text-anchor="end" font-size="10.5" font-weight="bold" fill="#64748b">12V 截止</text>
<text x="588" y="352" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#7c3aed">4.4V</text>
<text x="476" y="352" font-size="10.5" fill="#475569">0.2V</text>
<text x="470" y="140" font-size="11" font-weight="bold" fill="#dc2626">饱和区</text>
<text x="470" y="158" font-size="10.5" fill="#475569">负载线压在曲线上方</text>
<text x="470" y="180" font-size="10.5" fill="#475569">膝点：V_CE=0.2V，I_C≈5.9mA</text>
<path d="{cur}" fill="none" stroke="#0ea5e9" stroke-width="2.4"/>
<text x="676" y="214" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#0ea5e9">放大区：I_C=βI_B 拉平在 3.8mA</text>
<text x="760" y="140" text-anchor="end" font-size="10.5" font-weight="bold" fill="#7c3aed">负载线 I_C=(12−V_CE)/2k</text>
<line x1="456" y1="214" x2="790" y2="332" stroke="#7c3aed" stroke-width="2" stroke-dasharray="6,4"/>
<circle r="7" fill="#7c3aed" stroke="#ffffff" stroke-width="2">
<animateMotion dur="{DB}s" repeatCount="indefinite" path="M456,214 L790,332" keyPoints="0;1;0" keyTimes="0;0.5;1"/></circle>
<text x="600" y="254" font-size="11" font-weight="bold" fill="#7c3aed">Q（工作点）</text>
<text x="612" y="374" text-anchor="middle" font-size="10.5" fill="#475569">蓝线=输出特性　紫虚线=负载线　圆点沿负载线来回扫：左端饱和、右端截止</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DB}s" begin="-0.2s" repeatCount="indefinite" path="M105,112 L105,138"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DB}s" begin="-0.9s" repeatCount="indefinite" path="M70,112 L70,168"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DB}s" begin="-1.6s" repeatCount="indefinite" path="M52,190 L93,190"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DB}s" begin="-2.3s" repeatCount="indefinite" path="M130,247 L130,282"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DB}s" begin="-3.0s" repeatCount="indefinite" path="M130,137 L130,168"/></circle>
{pulse(452, 130, 116, 96, '#dc2626', 2.0, 8)}
{pulse(534, 242, 30, 30, '#7c3aed', 1.6, 6)}
'''
    svg += caption("① 截止区：两个结都反偏——CE 之间像断了的开关，I_C≈0", "#64748b", DB,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=406)
    svg += caption("② 放大区：发射结正偏、集电结反偏——I_C=β·I_B，是放大器的家", "#2563eb", DB,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=406)
    svg += caption("③ 饱和区：两个结都正偏——V_CE≈0.2V，像合上的开关，β 说了不算", "#dc2626", DB,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.78;0.83;1", y=406)
    svg += caption("④ 常青坑：设计时不先把「放大区」用负载线框死——信号一摆就削顶", "#b45309", DB,
                   "0;0;1;1", "0;0.83;0.88;1", y=406)
    svg += note_box("口诀：放大靠「发正集反」；开关要「深饱和」（I_B 按 1/10 I_C 给，别按 β 算）", 484, DB,
                    "0;0.9;0.94;1", w=740)
    save('bjt-regions.svg', svg + '</svg>')

# ======================= 图 46：PT100 信号链（第 14 章实例） =======================
def make_signal_chain():
    DSL = 9
    svg = svg_open('信号链设计实例：PT100 温度采集全链复盘', h=600)
    svg += f'''
<circle cx="100" cy="82" r="16" fill="none" stroke="#2563eb" stroke-width="1.6" stroke-dasharray="4,4">
<animateTransform attributeName="transform" type="rotate" values="0 100 82;360 100 82" dur="7s" repeatCount="indefinite"/>
</circle>
<circle cx="100" cy="82" r="5.5" fill="#2563eb"/>
<text x="100" y="114" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">PT100</text>
<text x="100" y="130" text-anchor="middle" font-size="10.5" fill="#475569">1mA 激励 → 385µV/℃</text>
<line x1="130" y1="82" x2="186" y2="82" stroke="#334155" stroke-width="2.5"/>
<circle r="5" fill="#059669">
<animateMotion dur="{DSL}s" repeatCount="indefinite" path="M110,82 H186" keyPoints="0;1" keyTimes="0;1"/></circle>
<text x="158" y="46" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">385µV</text>
<rect x="190" y="52" width="150" height="80" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="265" y="82" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">仪表放大器</text>
<text x="265" y="100" text-anchor="middle" font-size="10.5" fill="#475569">INA333 · G=40</text>
<text x="265" y="122" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">共模 100mV → 差模 1µV</text>
<line x1="340" y1="82" x2="446" y2="82" stroke="#334155" stroke-width="2.5"/>
<circle r="5" fill="#059669">
<animateMotion dur="{DSL}s" repeatCount="indefinite" path="M346,82 H446" keyPoints="0;1" keyTimes="0;1"/></circle>
<text x="392" y="46" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">15.4mV/℃</text>
<rect x="450" y="52" width="130" height="80" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="515" y="82" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">Sallen-Key 低通</text>
<text x="515" y="100" text-anchor="middle" font-size="10.5" fill="#475569">fc=10Hz · Q=0.707</text>
<text x="515" y="122" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">50Hz 工频 −28dB</text>
<line x1="580" y1="82" x2="686" y2="82" stroke="#334155" stroke-width="2.5"/>
<circle r="5" fill="#059669">
<animateMotion dur="{DSL}s" repeatCount="indefinite" path="M586,82 H686" keyPoints="0;1" keyTimes="0;1"/></circle>
<text x="632" y="46" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">1.54V</text>
<rect x="690" y="52" width="86" height="80" rx="8" fill="#f8fafc" stroke="#7c3aed" stroke-width="2.5"/>
<text x="733" y="84" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#7c3aed">ADC</text>
<text x="733" y="102" text-anchor="middle" font-size="10.5" fill="#475569">12 位</text>
<text x="733" y="120" text-anchor="middle" font-size="10.5" fill="#475569">LSB 500µV</text>

<line x1="30" y1="190" x2="30" y2="418" stroke="#94a3b8" stroke-width="1.4"/>
<line x1="30" y1="418" x2="790" y2="418" stroke="#64748b" stroke-width="1.6"/>
<line x1="30" y1="196" x2="37" y2="196" stroke="#94a3b8" stroke-width="1.2"/>
<line x1="30" y1="307" x2="37" y2="307" stroke="#94a3b8" stroke-width="1.2"/>
<text x="42" y="430" font-size="11" fill="#475569">0</text>
<text x="42" y="311" font-size="11" fill="#475569">1.024V</text>
<text x="42" y="200" font-size="11" fill="#475569">2.048V</text>
<text x="96" y="190" font-size="11" font-weight="bold" fill="#475569">ADC 满量程 2.048V（12 位 = 4096 码）</text>
<line x1="340" y1="196" x2="340" y2="418" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="5,4"/>
<line x1="580" y1="196" x2="580" y2="418" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="5,4"/>
<line x1="90" y1="364" x2="760" y2="364" stroke="#0ea5e9" stroke-width="3.5"/>
<circle r="6" fill="#0ea5e9" stroke="#ffffff" stroke-width="2">
<animateMotion dur="{DSL}s" repeatCount="indefinite" path="M90,364 H760" keyPoints="0;1" keyTimes="0;1"/></circle>
<text x="96" y="352" font-size="11.5" font-weight="bold" fill="#0ea5e9">放大后 1.54V（100℃ 满量）＝ 75% 满量程</text>
<line x1="90" y1="417" x2="340" y2="417" stroke="#dc2626" stroke-width="1.8" stroke-dasharray="6,4"/>
<text x="96" y="404" font-size="11.5" font-weight="bold" fill="#dc2626">未放大 38.5mV：真实位置离地 4px，贴地</text>
<text x="96" y="386" font-size="11" fill="#475569">不放大只剩 77 码（≈6.3 位）</text>
<text x="760" y="344" text-anchor="end" font-size="11.5" font-weight="bold" fill="#7c3aed">12.5µV/码 ≈ 0.032℃</text>
<text x="90" y="436" font-size="10.5" font-weight="bold" fill="#475569">PT100 385µV/℃</text>
<text x="340" y="436" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#475569">INA333 ×40</text>
<text x="580" y="436" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#475569">低通 fc=10Hz</text>
<text x="760" y="436" text-anchor="end" font-size="10.5" font-weight="bold" fill="#475569">ADC</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DSL}s" begin="-0.7s" repeatCount="indefinite" path="M348,82 L444,82"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DSL}s" begin="-1.5s" repeatCount="indefinite" path="M92,417 L336,417"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DSL}s" begin="-2.3s" repeatCount="indefinite" path="M588,82 L684,82"/></circle>
{pulse(688, 50, 90, 84, '#7c3aed', 1.9, 8)}
<rect x="446" y="500" width="340" height="60" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.5"/>
<text x="462" y="524" font-size="11.5" font-weight="bold" fill="#b45309">不做前端处理会怎样？</text>
<text x="462" y="548" font-size="11" fill="#475569">不放大：77 码 ≈ 6.3 位　放大后：3080 码 ≈ 11.6 位有效</text>
<text x="452" y="578" font-size="11.5" font-weight="bold" fill="#059669">放大不只是「变大」：把信号顶到接近满量程，才叫没浪费 ADC</text>
'''
    svg += caption("① 反推增益：满量程 2.048V 留 25% 余量 → 目标 1.54V；1.54V ÷ 38.5mV = ×40", "#2563eb", DSL,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=490)
    svg += caption("② 选前端：仪表放大器先扛共模、给高阻；低通 fc=10Hz 再把工频按到 −28dB", "#059669", DSL,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=490)
    svg += caption("③ 逐级验算：每加一级都要回头看「信号还在不在 噪声有没有追上来」", "#dc2626", DSL,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=490)
    svg += caption("④ 收尾：12 位 LSB 折算回输入 = 0.032℃/码，远细于 0.1℃ 的目标分辨率", "#7c3aed", DSL,
                   "0;0;1;1", "0;0.85;0.9;1", y=490)
    save('signal-chain.svg', svg + '</svg>')

# ======================= 图 47：热失控正反馈环 =======================
def make_thermal_runaway():
    DT = 10
    svg = svg_open('热失控：一只 BJT 自己把自己烧了（正反馈环）', h=640)
    svg += f'''
<circle cx="260" cy="230" r="110" fill="none" stroke="#fecaca" stroke-width="14" stroke-dasharray="10 10">
<animateTransform attributeName="transform" type="rotate" values="0 260 230;360 260 230" dur="12s" repeatCount="indefinite"/>
</circle>
<circle cx="260" cy="230" r="20" fill="#fee2e2"/>
<text x="260" y="217" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b91c1c">热失控</text>
<text x="260" y="234" text-anchor="middle" font-size="11" font-weight="bold" fill="#dc2626">Tj ↑</text>
<text x="260" y="250" text-anchor="middle" font-size="10.5" fill="#dc2626">累积</text>
<rect x="170" y="66" width="180" height="48" rx="8" fill="#fff7ed" stroke="#b45309" stroke-width="2"/>
<text x="260" y="88" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">① V_BE 变小</text>
<text x="260" y="106" text-anchor="middle" font-size="10.5" fill="#475569">−2mV/℃（约）</text>
<rect x="378" y="206" width="180" height="48" rx="8" fill="#fff7ed" stroke="#b45309" stroke-width="2"/>
<text x="468" y="228" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">② I_C = β·I_B</text>
<text x="468" y="246" text-anchor="middle" font-size="10.5" fill="#475569">β 也随温度涨</text>
<rect x="170" y="348" width="180" height="48" rx="8" fill="#fff7ed" stroke="#b45309" stroke-width="2"/>
<text x="260" y="370" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">③ P = V_CE·I_C</text>
<text x="260" y="388" text-anchor="middle" font-size="10.5" fill="#475569">自身发热更猛</text>
<rect x="10" y="206" width="128" height="48" rx="8" fill="#fff7ed" stroke="#b45309" stroke-width="2"/>
<text x="74" y="228" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b45309">④ Tj 继续爬</text>
<text x="74" y="246" text-anchor="middle" font-size="10.5" fill="#475569">Ta + P·Rth</text>
<g fill="none" stroke="#b45309" stroke-width="2.5">
<path d="M350,100 A104 104 0 0 1 392,196"/>
<path d="M548,262 A104 104 0 0 1 360,372"/>
<path d="M170,372 A104 104 0 0 1 62,262"/>
<path d="M68,196 A104 104 0 0 1 162,92"/>
</g>
<path d="M392,196 l-12,-13 M392,196 l-17,3" stroke="#b45309" stroke-width="2.5"/>
<path d="M360,372 l-16,-4 M360,372 l1,-16" stroke="#b45309" stroke-width="2.5"/>
<path d="M62,262 l5,-17 M62,262 l17,1" stroke="#b45309" stroke-width="2.5"/>
<path d="M162,92 l17,3 M162,92 l1,16" stroke="#b45309" stroke-width="2.5"/>
<circle r="6" fill="#dc2626">
<animateMotion dur="10s" repeatCount="indefinite" path="M260,68 A162 162 0 1 1 258,68" keyPoints="0;1" keyTimes="0;1"/></circle>
<text x="330" y="128" font-size="10.5" font-weight="bold" fill="#94a3b8">正反馈环</text>
<g>
<animateTransform attributeName="transform" type="scale" values="1 1;2.2 2.2;2.2 2.2;1 1;1 1" keyTimes="0;0.3;0.62;0.94;1" dur="10s" repeatCount="indefinite" additive="sum"/>
<animateTransform attributeName="transform" type="translate" values="0 0;-406 -182;-406 -182;0 0;0 0" keyTimes="0;0.3;0.62;0.94;1" dur="10s" repeatCount="indefinite" additive="sum"/>
<circle cx="338" cy="152" r="7" fill="#dc2626"/>
</g>
<text x="338" y="178" text-anchor="middle" font-size="10.5" fill="#94a3b8">越烧越大的结点</text>
<line x1="566" y1="70" x2="566" y2="496" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="682" y="60" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">可用的偏置 vs 作死的偏置</text>
<line x1="576" y1="92" x2="788" y2="92" stroke="#94a3b8" stroke-width="1.6"/>
<line x1="576" y1="132" x2="788" y2="132" stroke="#cbd5e1" stroke-width="1"/>
<line x1="576" y1="182" x2="788" y2="182" stroke="#cbd5e1" stroke-width="1"/>
<line x1="576" y1="236" x2="788" y2="236" stroke="#cbd5e1" stroke-width="1"/>
<line x1="576" y1="300" x2="788" y2="300" stroke="#cbd5e1" stroke-width="1"/>
<line x1="576" y1="356" x2="788" y2="356" stroke="#cbd5e1" stroke-width="1"/>
<line x1="576" y1="412" x2="788" y2="412" stroke="#cbd5e1" stroke-width="1"/>
<text x="682" y="114" text-anchor="middle" font-size="12" font-weight="bold" fill="#475569">偏置方式</text>
<text x="682" y="158" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#059669">分压 + 射极电阻 Re</text>
<text x="682" y="212" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#dc2626">固定 I_B 偏置</text>
<text x="682" y="272" text-anchor="middle" font-size="11" fill="#475569">温度一升，Re 上压降</text>
<text x="682" y="290" text-anchor="middle" font-size="11" fill="#475569">变大 → V_BE 自己降 → 自动刹车</text>
<text x="682" y="330" text-anchor="middle" font-size="11" fill="#475569">I_C 涨 → 更热 → I_C 再涨</text>
<text x="682" y="348" text-anchor="middle" font-size="11" fill="#475569">没有回路对手，直到烧穿</text>
<text x="682" y="386" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">负反馈 = 刹车</text>
<path d="M682,398 L682,440" stroke="#2563eb" stroke-width="2" stroke-dasharray="5,4"/>
<path d="M676,412 L682,398 L688,412" fill="#2563eb"/>
<text x="682" y="462" text-anchor="middle" font-size="10.5" fill="#475569">I_C ↑ → V_E ↑ → V_BE ↓</text>
<circle r="6" fill="#dc2626">
<animateMotion dur="10s" repeatCount="indefinite" path="M682,462 L682,540" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DT}s" begin="-1.2s" repeatCount="indefinite" path="M350,100 A104 104 0 0 1 392,196" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DT}s" begin="-2.4s" repeatCount="indefinite" path="M548,262 A104 104 0 0 1 360,372" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DT}s" begin="-3.6s" repeatCount="indefinite" path="M170,372 A104 104 0 0 1 62,262" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DT}s" begin="-4.8s" repeatCount="indefinite" path="M68,196 A104 104 0 0 1 162,92" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(236,206,48,48,'#b91c1c',3.0,24)}
<rect x="200" y="548" width="460" height="42" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="2.5"/>
<text x="430" y="574" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#b91c1c">热失控不是「运气差」——是设计里少了一条负反馈</text>
<text x="430" y="538" text-anchor="middle" font-size="11" fill="#475569">前两拍：I_C 慢慢涨（还没觉得烫）　后两拍：P 与温度互相加码，越快越失控</text>
'''
    svg += caption("① 硅的脾气：V_BE 每升 1℃ 就低 2mV——同样的 V_B 会挤出更大的 I_C", "#b45309", DT,
                   "0;1;1;0;0", "0;0.03;0.2;0.26;1", y=520)
    svg += caption("② 恶性循环：更热 → I_C 更大 → 功耗更大 → 更热——自己给自己加速", "#dc2626", DT,
                   "0;0;1;1;0;0", "0;0.26;0.32;0.48;0.54;1", y=520)
    svg += caption("③ 唯一能自己刹住车的是负反馈：Re 把 I_C 的增量变成 V_BE 的减量", "#2563eb", DT,
                   "0;0;1;1;0;0", "0;0.54;0.6;0.78;0.84;1", y=520)
    svg += caption("④ 实战三招：射极电阻、散热片降 Rth、降额使用——别再靠「应该不会那么热」", "#059669", DT,
                   "0;0;1;1", "0;0.84;0.9;1", y=520)
    svg += note_box("对策：射极电阻 Re 负反馈 · 散热片降 Rth · 降额使用——负反馈是唯一能自动稳住的", 616, DT,
                    "0;0.9;0.94;1", w=740)
    save('thermal-runaway.svg', svg + '</svg>')
# ======================= 图 48：真实电容的阻抗频谱（第 1 章 1.2） =======================
def make_cap_parasitics():
    DC = 9
    ML = (100e-9, 0.3, 0.5e-9)
    EL = (10e-6, 1.0, 20e-9)
    def zmag(f, C, esr, esl):
        xc = 1/(2*np.pi*f*C)
        xl = 2*np.pi*f*esl
        return float(np.hypot(esr, xc-xl))
    X0, X1, Y0, Y1 = 400, 772, 104, 404
    def px(f):
        return X0+(np.log10(f)-1)/8*(X1-X0)
    def py(z):
        return Y0+(5-np.log10(max(z, 0.1)))/6*(Y1-Y0)
    def curve(spec, color, wid=2.4):
        fs = np.logspace(1, 9, 300)
        pts = [f"{px(f):.0f},{py(zmag(f, *spec)):.0f}" for f in fs]
        return '<path d="M' + " L".join(pts) + f'" fill="none" stroke="{color}" stroke-width="{wid}"/>'
    srf_ml = 1/(2*np.pi*np.sqrt(ML[0]*ML[2]))
    srf_el = 1/(2*np.pi*np.sqrt(EL[0]*EL[2]))
    svg = svg_open('真实电容的阻抗频谱：谷底有多低，决定它能救多高的频', h=622)
    svg += f'''
<text x="180" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">等效模型：C 串 ESR 串 ESL</text>
<text x="40" y="120" font-size="11.5" fill="#475569">纹波源</text>
<line x1="96" y1="116" x2="120" y2="116" stroke="#334155" stroke-width="2.5"/>
<line x1="120" y1="86" x2="120" y2="146" stroke="#334155" stroke-width="2.5"/>
<path d="M108,92 L120,82 L132,92 Z" fill="#334155"/>
<path d="M108,140 L120,150 L132,140 Z" fill="#334155"/>
<text x="140" y="122" font-size="11.5" font-weight="bold" fill="#334155">~ 噪声</text>
<line x1="180" y1="116" x2="204" y2="116" stroke="#334155" stroke-width="2.5"/>
<line x1="204" y1="96" x2="204" y2="136" stroke="#334155" stroke-width="2.5"/>
<line x1="190" y1="100" x2="218" y2="100" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="190" y1="112" x2="218" y2="112" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="204" y1="112" x2="204" y2="126" stroke="#334155" stroke-width="2"/>
<text x="222" y="110" font-size="12.5" font-weight="bold" fill="#7c3aed">C</text>
<line x1="204" y1="126" x2="204" y2="150" stroke="#334155" stroke-width="2.5"/>
<rect x="190" y="150" width="28" height="34" rx="3" fill="#fffbeb" stroke="#b45309" stroke-width="2"/>
<text x="204" y="172" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">ESR</text>
<line x1="204" y1="184" x2="204" y2="204" stroke="#334155" stroke-width="2.5"/>
<path d="M192,204 q12,14 24,0 q12,-14 24,0" fill="none" stroke="#dc2626" stroke-width="2.5"/>
<line x1="204" y1="204" x2="204" y2="228" stroke="#334155" stroke-width="2.5"/>
<line x1="204" y1="228" x2="204" y2="248" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(204, 262)}
<line x1="204" y1="116" x2="290" y2="116" stroke="#334155" stroke-width="2.5"/>
<circle cx="290" cy="116" r="4" fill="#334155"/>
<text x="296" y="112" font-size="11" font-weight="bold" fill="#2563eb">V 脚</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-0.3s" repeatCount="indefinite" path="M100,116 L120,116"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-0.3s" repeatCount="indefinite" path="M120,116 L180,116 L204,116 L204,150"/></circle>
<circle r="4" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-1.2s" repeatCount="indefinite" path="M204,184 L204,228 L204,248"/></circle>
<text x="60" y="300" font-size="11.5" font-weight="bold" fill="#7c3aed">C 决定低频</text>
<text x="60" y="320" font-size="11.5" font-weight="bold" fill="#b45309">ESR 决定谷底</text>
<text x="60" y="340" font-size="11.5" font-weight="bold" fill="#dc2626">ESL 决定高频</text>
<text x="60" y="368" font-size="11" fill="#475569">三者串联，谁在</text>
<text x="60" y="386" font-size="11" fill="#475569">该频段主导，阻抗就</text>
<text x="60" y="404" font-size="11" fill="#475569">长谁的样。</text>
<text x="240" y="300" font-size="11" fill="#475569">走线 1cm ≈ 5nH：</text>
<text x="240" y="320" font-size="11" fill="#475569">电容离芯片 5cm，</text>
<text x="240" y="340" font-size="11" fill="#475569">ESL 直接 +25nH，</text>
<text x="240" y="360" font-size="11" font-weight="bold" fill="#dc2626">高频救兵变拖油瓶</text>
<text x="586" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">|Z| 随频率：两条曲线差 500 倍</text>
<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<text x="{X1}" y="{Y1+36}" text-anchor="end" font-size="11" fill="#475569">频率 →</text>
<text x="{X0-6}" y="{Y0+10}" text-anchor="end" font-size="10.5" fill="#475569">100kΩ</text>
<text x="{X0-6}" y="{py(100)+4}" text-anchor="end" font-size="10.5" fill="#475569">1kΩ</text>
<text x="{X0-6}" y="{py(1)+4}" text-anchor="end" font-size="10.5" fill="#475569">1Ω</text>
<text x="{X0-6}" y="{Y1+4}" text-anchor="end" font-size="10.5" fill="#475569">0.1Ω</text>
<text x="{px(10):.0f}" y="{Y1+20}" text-anchor="middle" font-size="10" fill="#475569">10Hz</text>
<text x="{px(1e6):.0f}" y="{Y1+20}" text-anchor="middle" font-size="10" fill="#475569">1MHz</text>
<text x="{px(1e9):.0f}" y="{Y1+20}" text-anchor="middle" font-size="10" fill="#475569">1GHz</text>
{curve(EL, '#94a3b8', 2.2)}
{curve(ML, '#2563eb')}
<line x1="{px(srf_ml):.0f}" y1="{Y0}" x2="{px(srf_ml):.0f}" y2="{Y1}" stroke="#2563eb" stroke-width="1.2" stroke-dasharray="4,3"/>
<line x1="{px(srf_el):.0f}" y1="{Y0}" x2="{px(srf_el):.0f}" y2="{Y1}" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="4,3"/>
<circle cx="{px(srf_ml):.0f}" cy="{py(ML[1]):.0f}" r="5" fill="#2563eb"/>
<text x="{px(srf_ml)+7:.0f}" y="{py(ML[1])+4:.0f}" font-size="10.5" font-weight="bold" fill="#2563eb">SRF {srf_ml/1e6:.1f}MHz</text>
<text x="{px(srf_el)-7:.0f}" y="{py(EL[1])+4:.0f}" text-anchor="end" font-size="10.5" font-weight="bold" fill="#64748b">SRF {srf_el/1e3:.0f}kHz</text>
<text x="400" y="76" font-size="11.5" font-weight="bold" fill="#2563eb">100nF MLCC（ESR 0.3Ω / ESL 0.5nH）</text>
<text x="400" y="94" font-size="11.5" font-weight="bold" fill="#64748b">10µF 电解（ESR 1Ω / ESL 20nH）</text>
<text x="{px(srf_el)-7:.0f}" y="{py(zmag(1e8,*EL))-8:.0f}" text-anchor="end" font-size="10.5" font-weight="bold" fill="#dc2626">100MHz 时电解已 {zmag(1e8,*EL):.0f}Ω</text>
<circle r="5" fill="#2563eb">
<animateMotion dur="{DC}s" repeatCount="indefinite" path="M{px(1e3):.0f},{py(zmag(1e3,*ML)):.0f} L{px(1e7):.0f},{py(zmag(1e7,*ML)):.0f}" keyPoints="0;1" keyTimes="0;1"/></circle>
<text x="586" y="486" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">去耦选电容 = 选「谷底低且谷底宽」的那条曲线</text>
<text x="586" y="506" text-anchor="middle" font-size="11" fill="#475569">电解负责储能（低频），100nF 陶瓷负责高频——两者不能互相替代</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-0.4s" repeatCount="indefinite" path="M98,116 L118,116"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-1.0s" repeatCount="indefinite" path="M182,116 L204,116 L204,134"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-1.6s" repeatCount="indefinite" path="M204,186 L204,226"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-2.2s" repeatCount="indefinite" path="M204,230 L204,260"/></circle>
<circle cx="{px(srf_ml):.0f}" cy="{py(ML[1]):.0f}" r="6" fill="none" stroke="#2563eb" stroke-width="2.4">
<animate attributeName="r" values="6;15;6" dur="1.9s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.15;0.95" dur="1.9s" repeatCount="indefinite"/></circle>

'''
    svg += caption("① 低频：容抗 1/2πfC 主导——10µF 在 100Hz 还有 159Ω，随频率一路走低", "#7c3aed", DC,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=548)
    svg += caption("② 中频：ESR 兜底成谷底——MLCC 谷底 0.3Ω@22MHz，电解 1Ω@356kHz", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=548)
    svg += caption(f"③ 高频：ESL 接管，阻抗随频率上升——电解在 100MHz 已涨到 {zmag(1e8,*EL):.0f}Ω（MLCC 才 {zmag(1e8,*ML):.2f}Ω）", "#dc2626", DC,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=548)
    svg += caption("④ 所以「贴脸放」不是迷信：多 5cm 走线 = 多 25nH 串进 ESL", "#2563eb", DC,
                   "0;0;1;1", "0;0.85;0.9;1", y=548)
    svg += note_box("自谐振频率 f_SRF = 1/(2π√(LC))：过了它，电容就变成了电感——所以高频去耦永远要用小封装小容量", 592, DC,
                    "0;0.9;0.94;1", w=760)
    save('capacitor-parasitics.svg', svg + '</svg>')

# ======================= 图 49：米勒平台（MOSFET 开通波形，第 4 章 4.3） =======================
def make_miller_plateau():
    DS = 10
    TX0, TX1 = 90, 760
    def tx(t):
        return TX0 + t/800*670
    # 阶段边界（ns）：延时 150 / 电流上升 400 / 平台 560 / 完全增强 700
    vgs = [(0, 0), (150, 1.4), (400, 2.9), (560, 2.9), (700, 5.0), (800, 5.0)]
    vds = [(0, 20), (400, 20), (560, 0.15), (800, 0.15)]
    idr = [(0, 0), (400, 5), (800, 5)]
    pow_ = []
    for t in range(0, 801, 10):
        def g(tab):
            return np.interp(t, [p[0] for p in tab], [p[1] for p in tab])
        pow_.append((t, g(vds)*g(idr)))
    def path(tab, ytop, ybot, vmax, color, wid=2.6):
        pts = [f"{tx(t):.0f},{ybot-(v/vmax)*(ybot-ytop):.0f}" for t, v in tab]
        return ('<path d="M' + " L".join(pts) + f'" fill="none" stroke="{color}" '
                f'stroke-width="{wid}" stroke-linejoin="round"/>')
    svg = svg_open('米勒平台：V_GS 为什么会在半路「停下来看戏」', h=620)
    vgs_d = (f"M{tx(0):.0f},196 L{tx(150):.0f},175 L{tx(400):.0f},152 "
             f"L{tx(560):.0f},152 L{tx(700):.0f},120 L{tx(800):.0f},120")
    vds_d = f"M{tx(0):.0f},216 L{tx(400):.0f},216 L{tx(560):.0f},291 L{tx(800):.0f},291"
    vgd_d = f"M{tx(0):.0f},84 L{tx(400):.0f},84 L{tx(560):.0f},152 L{tx(800):.0f},152"
    svg += f'''
<text x="425" y="50" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">20V 母线 · 5A 负载 · 10mA 驱动 · AO3400（Q_g≈7nC, Q_gd≈1.6nC）</text>
<rect x="{tx(150):.0f}" y="70" width="{tx(400)-tx(150):.0f}" height="380" fill="#94a3b8" opacity="0.10"/>
<rect x="{tx(400):.0f}" y="70" width="{tx(560)-tx(400):.0f}" height="380" fill="#7c3aed" opacity="0.10"/>
<rect x="{tx(560):.0f}" y="70" width="{tx(700)-tx(560):.0f}" height="380" fill="#059669" opacity="0.10"/>
<text x="{tx(75):.0f}" y="88" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">① 延时区</text>
<text x="{tx(275):.0f}" y="88" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#475569">② 电流上升区</text>
<text x="{tx(480):.0f}" y="88" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#7c3aed">③ 米勒平台</text>
<text x="{tx(630):.0f}" y="88" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#059669">④ 完全增强</text>
<text x="20" y="130" font-size="12" font-weight="bold" fill="#2563eb">V_GS</text>
<text x="20" y="236" font-size="12" font-weight="bold" fill="#dc2626">V_DS</text>
<text x="20" y="342" font-size="12" font-weight="bold" fill="#059669">I_D</text>
<text x="20" y="438" font-size="12" font-weight="bold" fill="#b45309">P=V·I</text>
<line x1="{TX0}" y1="502" x2="{TX1}" y2="502" stroke="#64748b" stroke-width="1.6"/>
{path(vgs, 120, 196, 5, '#2563eb')}
{path(vds, 216, 292, 20, '#dc2626')}
{path(idr, 322, 398, 5, '#059669')}
{path(pow_, 418, 494, 100, '#b45309')}
<line x1="{tx(400):.0f}" y1="120" x2="{tx(400):.0f}" y2="450" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(560):.0f}" y1="120" x2="{tx(560):.0f}" y2="450" stroke="#7c3aed" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(150):.0f}" y1="120" x2="{tx(150):.0f}" y2="200" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{tx(150)+6:.0f}" y="134" font-size="10.5" font-weight="bold" fill="#475569">V_th≈1.4V</text>
<text x="{tx(400)-8:.0f}" y="112" text-anchor="end" font-size="10.5" font-weight="bold" fill="#2563eb">平台电压 ≈V_th+I_D/g_m ≈2.9V</text>
<text x="{tx(700)+6:.0f}" y="308" font-size="10.5" font-weight="bold" fill="#059669">到底 0.15V</text>
<text x="{tx(556):.0f}" y="210" text-anchor="end" font-size="10.5" font-weight="bold" fill="#7c3aed">平台期：V_DS 猛跌</text>
<text x="{tx(275):.0f}" y="314" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">V_DS 还满着 20V，I_D 已经上来了</text>
<text x="{tx(600):.0f}" y="484" font-size="10.5" font-weight="bold" fill="#b45309">损耗 = 阴影面积 × f_sw</text>
<circle r="5" fill="#2563eb">
{linear_x_motion(DS, vgs_d)}</circle>
<circle r="5" fill="#dc2626">
{linear_x_motion(DS, vds_d)}</circle>
<circle r="5" fill="#7c3aed">
{linear_x_motion(DS, vgd_d)}</circle>
<text x="{tx(400):.0f}" y="522" text-anchor="middle" font-size="10.5" fill="#475569">400ns</text>
<text x="{tx(560):.0f}" y="522" text-anchor="middle" font-size="10.5" fill="#475569">560ns</text>
<text x="{TX1}" y="522" text-anchor="end" font-size="10.5" fill="#475569">800ns</text>
<text x="430" y="548" text-anchor="middle" font-size="11" font-weight="bold" fill="#7c3aed">平台时长 = Q_gd ÷ 驱动电流 = 1.6nC ÷ 10mA = 160ns；重叠 410ns → P_sw≈2W（§4.6 按 700ns 保守估 3.5W）</text>
<circle cx="{tx(400):.0f}" cy="152" r="5" fill="none" stroke="#7c3aed" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.6s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.2;0.95" dur="1.6s" repeatCount="indefinite"/></circle>
<circle cx="{tx(400):.0f}" cy="216" r="5" fill="none" stroke="#dc2626" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.6s" begin="-0.8s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.2;0.95" dur="1.6s" begin="-0.8s" repeatCount="indefinite"/></circle>
<circle r="5" fill="#b45309"><animateMotion dur="{DS}s" begin="-0.7s" repeatCount="indefinite" path="M{tx(150):.0f},440 L{tx(560):.0f},440"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DS}s" begin="-1.4s" repeatCount="indefinite" path="M{tx(560):.0f},356 L{tx(800):.0f},356"/></circle>
'''
    svg += caption("① 前 400ns：栅极电流先填 C_GS，I_D 起来时 V_DS 还满着——最疼的一段", "#dc2626", DS,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=584)
    svg += caption("② 平台期：驱动电流全被 C_GD 抽走，V_GS 被钉住，V_DS 快速下降", "#7c3aed", DS,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=584)
    svg += caption("③ 平台结束才是 R_DS(on) 生效的时刻：0.75W 导通损耗此刻才开始", "#059669", DS,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=584)
    svg += caption("④ 记住 Q_gd：它比 C_rss 更直接地告诉你「这管子开关有多肉」", "#2563eb", DS,
                   "0;0;1;1", "0;0.85;0.9;1", y=584)
    save('miller-plateau.svg', svg + '</svg>')

# ======================= 图 50：运放阶跃响应：压摆率与建立时间（6.7） =======================
def make_opamp_slew():
    DW = 9
    X0, X1, Y0, Y1 = 430, 770, 130, 400
    def px(t):
        return X0 + t/3.0*340
    def py(v):
        return Y1 - v/1.15*(Y1-Y0)
    def slew_path(dur_slew, tau, n=120):
        pts = []
        for i in range(n+1):
            t = dur_slew*i/n
            v = min(1.0, 0.5*t)
            if t > dur_slew:
                v = 1.0 - (1.0-v)*(np.exp(-(t-dur_slew)/tau))
            pts.append(f"{px(t):.0f},{py(v):.0f}")
        return "M" + " L".join(pts)
    svg = svg_open('运放阶跃：直线爬坡，不是指数曲线', h=600)
    svg += f'''
<text x="200" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">741 接成跟随器，输入 0 → 1V 阶跃</text>
<line x1="80" y1="150" x2="120" y2="150" stroke="#334155" stroke-width="2.5"/>
<text x="60" y="146" font-size="11" fill="#475569">阶跃</text>
<line x1="120" y1="126" x2="120" y2="174" stroke="#334155" stroke-width="2.5"/>
<path d="M108,132 L120,122 L132,132 Z" fill="#334155"/>
<path d="M108,168 L120,178 L132,168 Z" fill="#334155"/>
<text x="126" y="196" font-size="11.5" font-weight="bold" fill="#334155">1V</text>
<line x1="120" y1="150" x2="160" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="160" cy="150" r="4" fill="#334155"/>
<polygon points="170,118 170,206 240,162" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="178" y="142" font-size="13" font-weight="bold" fill="#059669">+</text>
<text x="178" y="192" font-size="13" font-weight="bold" fill="#dc2626">−</text>
<line x1="160" y1="150" x2="170" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="240" y1="162" x2="290" y2="162" stroke="#334155" stroke-width="2.5"/>
<line x1="290" y1="162" x2="290" y2="240" stroke="#334155" stroke-width="2.5"/>
<line x1="290" y1="240" x2="230" y2="240" stroke="#334155" stroke-width="2.5"/>
<line x1="230" y1="240" x2="230" y2="174" stroke="#334155" stroke-width="2.5"/>
<line x1="230" y1="174" x2="170" y2="174" stroke="#334155" stroke-width="2.5"/>
<line x1="310" y1="162" x2="380" y2="162" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="162" r="4" fill="#334155"/>
<text x="336" y="158" font-size="11.5" font-weight="bold" fill="#2563eb">V_out</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DW}s" begin="-0.3s" repeatCount="indefinite" path="M90,150 L160,150"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DW}s" begin="-0.9s" repeatCount="indefinite" path="M170,174 L230,174 L290,240 L290,162 L380,162"/></circle>
<text x="60" y="290" font-size="11.5" font-weight="bold" fill="#b45309">补偿电容只能靠</text>
<text x="60" y="310" font-size="11.5" font-weight="bold" fill="#b45309">恒定电流充电</text>
<text x="60" y="338" font-size="11" fill="#475569">→ 电流恒定 ⇒ 斜率恒定</text>
<text x="60" y="358" font-size="11" fill="#475569">→ 爬坡段是直线</text>
<text x="60" y="386" font-size="11.5" font-weight="bold" fill="#dc2626">不是指数曲线！</text>
<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<text x="{X1}" y="{Y1+36}" text-anchor="end" font-size="11" fill="#475569">时间 →</text>
<text x="{X0-6}" y="{py(1)+4}" text-anchor="end" font-size="10.5" fill="#475569">1V</text>
<text x="{X0-6}" y="{py(0)+4}" text-anchor="end" font-size="10.5" fill="#475569">0</text>
<text x="{px(1):.0f}" y="{Y1+20}" text-anchor="middle" font-size="10" fill="#475569">1µs</text>
<text x="{px(2):.0f}" y="{Y1+20}" text-anchor="middle" font-size="10" fill="#475569">2µs</text>
<text x="{px(3):.0f}" y="{Y1+20}" text-anchor="end" font-size="10" fill="#475569">3µs</text>
<line x1="{px(2):.0f}" y1="{py(1):.0f}" x2="{px(2):.0f}" y2="{Y1}" stroke="#dc2626" stroke-width="1.2" stroke-dasharray="4,3"/>
<line x1="{X0}" y1="{py(0.999):.0f}" x2="{px(2.75):.0f}" y2="{py(0.999):.0f}" stroke="#059669" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{X1}" y="{py(0.999)-6:.0f}" text-anchor="end" font-size="10.5" font-weight="bold" fill="#059669">0.1% 误差带</text>
<path d="{slew_path(2.0, 0.16)}" fill="none" stroke="#2563eb" stroke-width="3"/>
<path d="{slew_path(0.0, 0.16)}" fill="none" stroke="#64748b" stroke-width="2.4" stroke-dasharray="6,4"/>
<text x="{px(2)-8:.0f}" y="{py(0.35):.0f}" text-anchor="end" font-size="10.5" fill="#64748b">若只有 GBW=1MHz 的小信号速度</text>
<text x="{px(2.02):.0f}" y="{py(0.45):.0f}" font-size="11.5" font-weight="bold" fill="#dc2626">2µs 直线爬坡</text>
<text x="{px(0.15):.0f}" y="{py(0.12):.0f}" font-size="11" fill="#475569">斜率 = 0.5V/µs（SR）</text>
<text x="{px(2.22):.0f}" y="{py(0.86):.0f}" font-size="11" fill="#475569">指数收尾 τ≈0.16µs</text>
<text x="{px(1.35):.0f}" y="{py(0.62):.0f}" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">建立时间≈2.6µs</text>
<circle r="6" fill="#2563eb" stroke="#ffffff" stroke-width="2">
<animateMotion dur="{DW}s" repeatCount="indefinite" path="{slew_path(2.0, 0.16)}" keyPoints="0;1" keyTimes="0;1"/></circle>
<rect x="446" y="470" width="330" height="70" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.5"/>
<text x="462" y="494" font-size="11.5" font-weight="bold" fill="#b45309">全功率带宽（同一个运放）</text>
<text x="452" y="516" font-size="10" fill="#475569">f_max = SR / (2π·V_p) = 0.5 / (2π×0.5) ≈ 159kHz（1Vpp）</text>
<text x="452" y="534" font-size="10" fill="#475569">10Vpp（V_p=5V）时只剩 ≈16kHz——GBW 1MHz 是个纸面数字</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DW}s" begin="-0.4s" repeatCount="indefinite" path="M90,150 L160,150"/></circle>
<circle r="5" fill="#64748b"><animateMotion dur="{DW}s" begin="-1.1s" repeatCount="indefinite" path="{slew_path(0.0, 0.16)}" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle cx="{px(2.0):.0f}" cy="{py(1.0):.0f}" r="5" fill="none" stroke="#dc2626" stroke-width="2.4">
<animate attributeName="r" values="5;13;5" dur="1.8s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.15;0.95" dur="1.8s" repeatCount="indefinite"/></circle>
<circle cx="{px(0.0):.0f}" cy="{py(1.0):.0f}" r="5" fill="none" stroke="#2563eb" stroke-width="2.4">
<animate attributeName="r" values="5;13;5" dur="1.8s" begin="-0.9s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.15;0.95" dur="1.8s" begin="-0.9s" repeatCount="indefinite"/></circle>
{pulse(444, 466, 336, 78, '#b45309', 2.0, 10)}
'''
    svg += caption("① 阶跃瞬间 V_+−V_−=1V：差分对彻底失衡，放大功能直接「宕机」", "#64748b", DW,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=572)
    svg += caption("② 补偿电容被恒定电流充电 → 输出以 SR=0.5V/µs 直线上升（2µs 爬 1V）", "#dc2626", DW,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=572)
    svg += caption("③ 退出饱和后按 GBW 走指数收尾：τ≈0.16µs，可能带过冲振铃", "#2563eb", DW,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=572)
    svg += caption("④ 大信号看 SR、小信号看 GBW：两条曲线谁慢，就决定建立时间", "#b45309", DW,
                   "0;0;1;1", "0;0.85;0.9;1", y=572)
    save('opamp-slew.svg', svg + '</svg>')

# ======================= 图 51：二极管伏安特性（第 2 章 2.2） =======================
def make_diode_iv():
    DI = 10
    IS, VT = 1e-9, 0.026          # n=1 的理想硅结：每 60mV 一个十倍频
    X0, X1, Y0, Y1 = 410, 764, 118, 402
    def px(v):
        return X0 + v/0.8*(X1-X0)
    def py(i):
        return Y0 + (np.log10(100e-3) - np.log10(max(i, 1e-9)))/8*(Y1-Y0)
    def iv(v, dv=0.0):
        return IS*(np.exp((v+dv)/VT)-1)
    def curve(dv, color, wid=2.6):
        pts = []
        for v in np.linspace(0.001, 0.8, 400):
            i = iv(v, dv)
            if i > 100e-3:
                break
            pts.append(f"{px(v):.0f},{py(i):.0f}")
        return '<path d="M' + " L".join(pts) + f'" fill="none" stroke="{color}" stroke-width="{wid}"/>'
    svg = svg_open('二极管伏安特性：一根 60mV 能换来十倍电流', h=600)
    svg += f'''
<text x="185" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">I_D = I_S(e^(V_D/nV_T) − 1)</text>
<text x="40" y="86" font-size="11.5" font-weight="bold" fill="#334155">三条必须记住的账</text>
<text x="40" y="112" font-size="11.5" font-weight="bold" fill="#2563eb">① V_T = kT/q ≈ 26mV</text>
<text x="52" y="132" font-size="11" fill="#475569">→ 电压 +60mV，电流 ×10</text>
<text x="40" y="162" font-size="11.5" font-weight="bold" fill="#dc2626">② −2mV/℃</text>
<text x="52" y="182" font-size="11" fill="#475569">→ 同一电流，温度 +35℃</text>
<text x="52" y="200" font-size="11" fill="#475569">　 V_D 掉 70mV（电流 ×14.7）</text>
<text x="40" y="230" font-size="11.5" font-weight="bold" fill="#059669">③ 动态电阻 r_d</text>
<text x="52" y="250" font-size="11" fill="#475569">= nV_T / I_D = 26mV/1mA = 26Ω</text>
<rect x="36" y="272" width="290" height="120" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.5"/>
<text x="50" y="296" font-size="11.5" font-weight="bold" fill="#b45309">工程近似模型（按精度三选一）</text>
<text x="50" y="318" font-size="11" fill="#475569">理想开关：导通 0V —— 只算损耗时用</text>
<text x="50" y="338" font-size="11" fill="#475569">恒压降 0.7V —— 手算最快，误差最大</text>
<text x="50" y="358" font-size="11" fill="#475569">恒压降 + 体电阻 —— 大电流场合</text>
<text x="50" y="380" font-size="11" font-weight="bold" fill="#dc2626">小电流时 0.7V 假设最骗人：</text>
<text x="50" y="386" font-size="0" fill="none"> </text>
{curve(0.0, '#dc2626')}
{curve(0.07, '#2563eb')}
<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<text x="{X1}" y="{Y1+22}" text-anchor="end" font-size="11" fill="#475569">V_D →</text>
<text x="{X0-6}" y="{py(1e-3)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">1mA</text>
<text x="{X0-6}" y="{py(1e-6)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">1µA</text>
<text x="{X0-6}" y="{py(1e-9)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">1nA</text>
<text x="{X0+4}" y="{Y0+14}" font-size="10.5" fill="#475569">100mA</text>
<text x="{px(0.2):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">0.2V</text>
<text x="{px(0.5):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">0.5V</text>
<circle cx="{px(0.36):.0f}" cy="{py(1e-3):.0f}" r="5" fill="#dc2626"/>
<line x1="{px(0.36):.0f}" y1="{py(1e-3):.0f}" x2="{px(0.36):.0f}" y2="{Y1}" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{px(0.36)+8:.0f}" y="{py(1e-3)+4:.0f}" font-size="10.5" font-weight="bold" fill="#dc2626">25℃ 时 1mA 在 0.36V</text>
<text x="{px(0.36)+8:.0f}" y="{py(1e-3)-10:.0f}" font-size="10.5" font-weight="bold" fill="#2563eb">60℃ 时同一电流只要 0.29V</text>
<text x="560" y="{Y0+40}" font-size="10.5" font-weight="bold" fill="#2563eb">60℃ 曲线：整条左移 70mV（−2mV/℃×35℃）</text>
<text x="{px(0.42):.0f}" y="{py(1e-4)-8:.0f}" font-size="10.5" fill="#475569">↑ 每上升 60mV，电流爬一个十倍</text>
<text x="{px(0.42):.0f}" y="{py(1e-5)-8:.0f}" font-size="10.5" fill="#475569">↑ 指数不是「快」，是「没有拐点」</text>
<circle r="5" fill="#dc2626">
{plain_motion(DI, curve(0.0, '#dc2626'))}</circle>
<text x="587" y="474" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#dc2626">测温二极管、稳压二极管、温度传感器——全靠这条曲线</text>
<text x="587" y="494" text-anchor="middle" font-size="11" fill="#475569">大功率管的「温度升→电流增→更热」正反馈，热失控从这里开始</text>
<circle r="5" fill="#2563eb">{plain_motion(DI, curve(0.07, '#2563eb'))}</circle>
<circle cx="{px(0.36):.0f}" cy="{py(1e-3):.0f}" r="4" fill="#dc2626"><animate attributeName="r" values="5;11;5" dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.9;0.2;0.9" dur="1.6s" repeatCount="indefinite"/></circle>
<circle cx="{px(0.24):.0f}" cy="{py(1e-5):.0f}" r="4" fill="#b45309"><animate attributeName="r" values="3;7;3" dur="2.2s" repeatCount="indefinite"/></circle>
<circle cx="{px(0.3):.0f}" cy="{py(1e-4):.0f}" r="4" fill="#b45309"><animate attributeName="r" values="3;7;3" dur="2.2s" begin="-0.7s" repeatCount="indefinite"/></circle>
<line x1="{px(0.29):.0f}" y1="{py(1e-3)-6:.0f}" x2="{px(0.36):.0f}" y2="{py(1e-3)-6:.0f}" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,3">
<animate attributeName="opacity" values="0;1;1;0;0" dur="{DI}s" repeatCount="indefinite" keyTimes="0;0.3;0.46;0.52;1"/></line>
'''
    svg += caption("① 指数段：每 +60mV 电流 ×10——模拟工程师的十倍频速算法", "#dc2626", DI,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=548)
    svg += caption("② 温度才是那条隐藏的线：+35℃ 让同一电流的 V_D 掉 70mV", "#2563eb", DI,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=548)
    svg += caption("③ 动态电阻不是常数：1mA 处 26Ω，越小电流越「大」", "#059669", DI,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=548)
    svg += caption("④ 所以二极管当不了精密基准——它的曲线只听温度的", "#b45309", DI,
                   "0;0;1;1", "0;0.85;0.9;1", y=548)
    svg += note_box("死记：V_T=26mV、每 60mV 一个十倍、−2mV/℃——三句话能现场推回任何一条硅结曲线", 588, DI,
                    "0;0.9;0.94;1", w=760)
    save('diode-iv.svg', svg + '</svg>')

# ======================= 图 52：比较器 vs 运放（第 7 章 7.1） =======================
def make_comparator_opamp():
    DC = 10
    TX0, TX1 = 430, 764
    def tx(t):
        return TX0 + t/8.0*334
    YTOP, YBOT = 132, 296
    def vy(v):
        return YBOT - v/5.0*(YBOT-YTOP)
    def opamp(t):
        if t <= 4.0:
            return min(2.0, 0.5*t)
        return 2.0 - 2.0*(np.exp(-(t-4.0)/0.16))
    def cmp_(t):
        return 0.0 if t < 1.3 else 4.9
    def curve(fn, color, wid=2.8, dash=''):
        pts = [f"{tx(t):.0f},{vy(fn(t)):.0f}" for t in np.linspace(0, 8, 200)]
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        return ('<path d="M' + " L".join(pts) + f'" fill="none" stroke="{color}" '
                f'stroke-width="{wid}"{d}/>')
    svg = svg_open('运放当比较器、比较器当运放：为什么都不行', h=640)
    svg += f'''
<text x="180" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">同一个 0→2V 阶跃</text>
<line x1="80" y1="170" x2="120" y2="170" stroke="#334155" stroke-width="2.5"/>
<line x1="120" y1="146" x2="120" y2="194" stroke="#334155" stroke-width="2.5"/>
<path d="M108,152 L120,142 L132,152 Z" fill="#334155"/>
<path d="M108,188 L120,198 L132,188 Z" fill="#334155"/>
<line x1="120" y1="170" x2="160" y2="170" stroke="#334155" stroke-width="2.5"/>
<circle cx="160" cy="170" r="4" fill="#334155"/>
<polygon points="170,138 170,226 240,182" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="178" y="162" font-size="13" font-weight="bold" fill="#059669">+</text>
<text x="178" y="212" font-size="13" font-weight="bold" fill="#dc2626">−</text>
<line x1="160" y1="170" x2="170" y2="170" stroke="#334155" stroke-width="2.5"/>
<line x1="240" y1="182" x2="290" y2="182" stroke="#334155" stroke-width="2.5"/>
<line x1="290" y1="182" x2="290" y2="250" stroke="#334155" stroke-width="2.5"/>
<line x1="290" y1="250" x2="230" y2="250" stroke="#334155" stroke-width="2.5"/>
<line x1="230" y1="250" x2="230" y2="194" stroke="#334155" stroke-width="2.5"/>
<line x1="230" y1="194" x2="170" y2="194" stroke="#334155" stroke-width="2.5"/>
<text x="60" y="290" font-size="11.5" font-weight="bold" fill="#2563eb">运放：有补偿</text>
<text x="60" y="308" font-size="11.5" font-weight="bold" fill="#2563eb">SR 限速</text>
<text x="60" y="334" font-size="11" fill="#475569">2V ÷ 0.5V/µs</text>
<text x="60" y="352" font-size="11" fill="#475569">= 4µs 爬坡</text>
<text x="60" y="382" font-size="11.5" font-weight="bold" fill="#059669">比较器：无补偿</text>
<text x="60" y="400" font-size="11.5" font-weight="bold" fill="#059669">1.3µs 后直接跳</text>
<line x1="{TX0}" y1="{YBOT}" x2="{TX1}" y2="{YBOT}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{TX0}" y1="{YTOP}" x2="{TX0}" y2="{YBOT}" stroke="#64748b" stroke-width="1.6"/>
<text x="{TX1}" y="{YBOT+38}" text-anchor="end" font-size="11" fill="#475569">时间 →</text>
<text x="{tx(2):.0f}" y="{YBOT+22}" text-anchor="middle" font-size="10" fill="#475569">2µs</text>
<text x="{tx(4):.0f}" y="{YBOT+22}" text-anchor="middle" font-size="10" fill="#475569">4µs</text>
<text x="{tx(8):.0f}" y="{YBOT+22}" text-anchor="middle" font-size="10" fill="#475569">8µs</text>
<text x="{TX0-6}" y="{vy(5)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">5V</text>
<text x="{TX0-6}" y="{vy(2)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">2V</text>
<text x="{tx(4)+6:.0f}" y="{vy(2)-8:.0f}" font-size="10.5" font-weight="bold" fill="#2563eb">4µs 才爬到 2V</text>
<text x="{tx(1.35):.0f}" y="{vy(4.9)+16:.0f}" font-size="10.5" font-weight="bold" fill="#059669">1.3µs 就跳到 4.9V</text>
{curve(opamp, '#2563eb')}
{curve(cmp_, '#059669')}
<circle r="6" fill="#059669" stroke="#ffffff" stroke-width="2">
{linear_x_motion(DC, curve(cmp_, '#059669'))}</circle>
<text x="400" y="392" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#dc2626">真正的坑不在速度，在输出级</text>
<text x="400" y="414" text-anchor="middle" font-size="11" fill="#475569">LM393 是开集电极：输出只能「拉低」，上电沿要靠外部上拉电阻</text>
<rect x="60" y="436" width="300" height="86" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
<text x="74" y="460" font-size="11.5" font-weight="bold" fill="#b91c1c">开集电极 + 大电容 = 慢到离谱</text>
<text x="74" y="482" font-size="11" fill="#475569">10k 上拉带 100nF：τ = 1ms</text>
<text x="74" y="502" font-size="11" fill="#475569">上升沿 ≈ 2.2τ = 2.2ms——</text>
<text x="74" y="518" font-size="11" fill="#475569">判决再快也被电容拖住</text>
<path d="M400,470 L400,510" stroke="#2563eb" stroke-width="2.5"/>
<path d="M393,503 L400,514 L407,503 Z" fill="#2563eb"/>
<text x="430" y="470" font-size="11.5" font-weight="bold" fill="#2563eb">推挽运放直接驱动电容</text>
<text x="430" y="490" font-size="11" fill="#475569">靠输出级电流「灌」进负载，</text>
<text x="430" y="510" font-size="11" fill="#475569">不受上拉电阻的 RC 拖累</text>
<text x="430" y="536" font-size="11" font-weight="bold" fill="#b45309">所以：判决用比较器，驱动用运放</text>
<circle r="5" fill="#2563eb">{linear_x_motion(DC, curve(opamp, '#2563eb'))}</circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-0.4s" repeatCount="indefinite" path="M92,170 L158,170"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-0.7s" repeatCount="indefinite" path="M82,170 L118,170"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DC}s" begin="-1.5s" repeatCount="indefinite" path="M288,250 L232,250 L232,196 L172,194"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DC}s" begin="-2.3s" repeatCount="indefinite" path="M242,182 L288,182"/></circle>
{pulse(58, 434, 304, 90, '#dc2626', 1.8, 10)}
{pulse(tx(1.35), vy(4.9)+16, 150, 22, '#059669', 1.4, 6)}
{pulse(408, 452, 300, 74, '#2563eb', 2.2, 10)}
'''
    svg += caption("① 速度差：运放被压摆率限死（4µs 爬 2V），比较器 1.3µs 直接跳", "#059669", DC,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=584)
    svg += caption("② 但快不等于能驱动：开集电极输出的上电沿是 RC，不是 MOS 管", "#dc2626", DC,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=584)
    svg += caption("③ 用运放当比较器：翻转慢、饱和恢复拖尾、相位裕度不够还会自激", "#2563eb", DC,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=584)
    svg += caption("④ 用比较器当放大器：开集电极 + 饱和恢复慢，线性增益根本稳不住", "#b45309", DC,
                   "0;0;1;1", "0;0.85;0.9;1", y=584)
    save('comparator-opamp.svg', svg + '</svg>')

# ======================= 图 53：噪声三税种与噪声预算（第 11 章 11.6） =======================
def make_noise_budget():
    DN = 10
    X0, X1, Y0, Y1 = 400, 764, 130, 400
    def fx(f):
        return X0 + np.log10(f/10)/5.0*(X1-X0)
    def ny(db):
        return Y0 + (25-db)/30*(Y1-Y0)
    fig_fs = np.logspace(1, 6, 200)
    thermal_uv = np.sqrt(4 * 1.380649e-23 * 300 * 1e3 * 1e6) * 1e6
    output_mv = thermal_uv * 1000 / 1000
    svg = svg_open('噪声账本：先把每一笔算到同一页', h=640)
    svg += f'''
<text x="185" y="55" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">三笔物理税，先分清来源</text>
<text x="40" y="86" font-size="11.5" font-weight="bold" fill="#2563eb">热噪声：V_n = √(4kTRB)</text>
<text x="40" y="108" font-size="11" fill="#475569">在适用频段近似白噪声</text>
<text x="40" y="126" font-size="11" fill="#475569">高阻读电压；B 是等效噪声带宽</text>
<text x="40" y="156" font-size="11.5" font-weight="bold" fill="#dc2626">1/f 噪声：PSD ∝ 1/f</text>
<text x="40" y="178" font-size="11" fill="#475569">ASD ∝ 1/√f；低频起伏，不靠听感定性</text>
<text x="40" y="196" font-size="11" fill="#475569">宽带「嘶声」常见白噪声，先看频谱</text>
<text x="40" y="226" font-size="11.5" font-weight="bold" fill="#b45309">散粒噪声：I_n = √(2qIB)</text>
<text x="40" y="248" font-size="11" fill="#475569">载流子离散过结；泊松模型</text>
<text x="40" y="266" font-size="11" fill="#475569">降偏置还要核对增益、带宽与失真</text>
<rect x="36" y="290" width="292" height="154" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"/>
<text x="50" y="312" font-size="11.5" font-weight="bold" fill="#059669">算一笔：仅源电阻这一行</text>
<text x="50" y="334" font-size="11" fill="#475569">1kΩ · 300K · 高阻测量</text>
<text x="50" y="355" font-size="11" fill="#475569">B = 1MHz（等效噪声带宽）</text>
<text x="50" y="376" font-size="11" fill="#475569">V_n = {thermal_uv:.3f}µVrms ≈ {thermal_uv:.1f}µVrms</text>
<text x="50" y="397" font-size="10.5" fill="#475569">平坦增益 ×1000；忽略放大器噪声</text>
<text x="50" y="428" font-size="12.5" font-weight="bold" fill="#dc2626">输出 ≈ {output_mv:.1f}mVrms</text>
<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<text x="{X1}" y="{Y1+38}" text-anchor="end" font-size="11" fill="#475569">频率 →</text>
<text x="{X0-6}" y="{ny(0)+4:.3f}" text-anchor="end" font-size="10.5" fill="#475569">0dB</text>
<text x="{X0-6}" y="{ny(10)+4:.3f}" text-anchor="end" font-size="10.5" fill="#475569">10dB</text>
<text x="{X0-6}" y="{ny(20)+4:.3f}" text-anchor="end" font-size="10.5" fill="#475569">20dB</text>
<text x="{fx(10):.3f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">10Hz</text>
<text x="{fx(100):.3f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">100Hz</text>
<text x="{fx(1e4):.3f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">10kHz</text>
<text x="{fx(1e6):.3f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">1MHz</text>
<text x="580" y="55" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#334155">ASD 幅度谱：白噪声 + 1/f</text>
<text x="580" y="78" text-anchor="middle" font-size="11" fill="#475569">纵轴 20log₁₀(e_n/e₀) · 横轴 log f</text>
<text x="580" y="101" text-anchor="middle" font-size="10.5" fill="#475569">BJT / MOSFET 拐角仅示意，不是普遍规格</text>
'''
    # 两条总 ASD 谱共用白噪声地板 e₀，仅示意不同 fc，不代表器件优劣。
    def rel(f, corner):
        # 互不相关的单边 PSD 相加：S/e₀² = 1 + fc/f。
        # ASD/e₀ = sqrt(1 + fc/f)，20log10(ASD/e₀) = 10log10(S/e₀²)。
        # 纯 flicker 的 PSD ∝ 1/f、ASD ∝ 1/sqrt(f)，均为 −10dB/dec。
        white_psd = 1.0
        flicker_psd = corner / f
        return 10 * np.log10(white_psd + flicker_psd)
    dpaths = {}
    for corner, color in ((100.0, '#059669'), (1000.0, '#dc2626')):
        pts = [f"{fx(f):.3f},{ny(rel(f, corner)):.3f}" for f in fig_fs]
        dpaths[corner] = "M" + " L".join(pts)
        svg += (f'<path d="{dpaths[corner]}" fill="none" stroke="{color}" stroke-width="2.4"/>')
    svg += (f'<line x1="{X0}" y1="{ny(0):.3f}" x2="{X1}" y2="{ny(0):.3f}" '
            f'stroke="#64748b" stroke-width="1.2" stroke-dasharray="6,4"/>')
    corner_y = ny(rel(100.0, 100.0))
    svg += f'''
<circle cx="{fx(100):.3f}" cy="{corner_y:.3f}" r="5" fill="#059669"/>
<circle cx="{fx(1000):.3f}" cy="{corner_y:.3f}" r="5" fill="#dc2626"/>
<text x="{fx(100):.3f}" y="{corner_y-24:.3f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">BJT 示例 100Hz</text>
<text x="{fx(1000):.3f}" y="{corner_y+55:.3f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">MOSFET 示例 1kHz</text>
<text x="{X1-4}" y="{ny(0)-20:.3f}" text-anchor="end" font-size="10.5" fill="#475569">白噪声地板 e₀（0dB）</text>
<text x="{X1-4}" y="155" text-anchor="end" font-size="10.5" fill="#475569">f ≪ f_c：渐近 −10dB/dec</text>
<circle r="5" fill="#dc2626">
<animateMotion dur="{DN}s" repeatCount="indefinite" path="{dpaths[1000.0]}"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DN}s" begin="-0.6s" repeatCount="indefinite" path="{dpaths[100.0]}"/></circle>
<circle cx="{fx(100):.3f}" cy="{corner_y:.3f}" r="5" fill="none" stroke="#059669" stroke-width="2.4">
<animate attributeName="r" values="5;13;5" dur="1.8s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.15;0.95" dur="1.8s" repeatCount="indefinite"/></circle>
<circle cx="{fx(1000):.3f}" cy="{corner_y:.3f}" r="5" fill="none" stroke="#dc2626" stroke-width="2.4">
<animate attributeName="r" values="5;13;5" dur="1.8s" begin="-0.9s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.15;0.95" dur="1.8s" begin="-0.9s" repeatCount="indefinite"/></circle>
{pulse(40, 316, 284, 67, '#059669', 2.0, 10)}
<text x="580" y="459" text-anchor="middle" font-size="11" fill="#475569">e_n = e₀√(1 + f_c/f)；f_c 处 +3.01dB</text>
<text x="400" y="486" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">噪声账本：同参考点、同带宽，互不相关各项才做 RSS</text>
<text x="400" y="508" text-anchor="middle" font-size="11" fill="#475569">保住信号带宽和源负载条件，再核对偏置、稳定性与失真</text>
<text x="400" y="530" text-anchor="middle" font-size="11" fill="#475569">前级增益足够且不超载，才可能压低后级折算贡献；不是只看第一级</text>
'''
    svg += caption("① 一阶低通 + 白噪声：B = (π/2)f_H；先保住信号，再谈滤波", "#2563eb", DN,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=568, size=13)
    svg += caption("② 低频看实测谱和源阻抗；BJT / MOS 不能只凭类别排座次", "#059669", DN,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=568, size=13)
    svg += caption("③ 散粒电流噪声随 √I；偏置还会改跨导，必须重算整本账", "#b45309", DN,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=568, size=13)
    svg += caption("④ 同温、同等效阻值、同测量条件：拆成多只电阻不减热噪声", "#7c3aed", DN,
                   "0;0;1;1", "0;0.85;0.9;1", y=568, size=13)
    svg += note_box("四个等量、互不相关项 → 总 RMS 为单项 2 倍；只有一项明显占优，才先抓它", 614, DN,
                    "0;0.9;0.94;1", w=750, size=12)
    save('noise-budget.svg', svg + '</svg>')

# ======================= 图 54：测量本身不破坏电路（第 16 章 16.3） =======================
def make_probe_loading():
    DP = 11
    svg = svg_open('探头是负载：测量的动作本身就会改电路', h=640)
    svg += f'''
<text x="270" y="50" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">① 探头一碰上去，电路就变了</text>
<line x1="60" y1="150" x2="120" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="120" cy="150" r="4" fill="#334155"/>
<text x="44" y="146" font-size="11" fill="#475569">源</text>
<line x1="120" y1="150" x2="150" y2="150" stroke="#334155" stroke-width="2.5"/>
<rect x="150" y="138" width="50" height="24" rx="3" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="175" y="126" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">100k</text>
<line x1="200" y1="150" x2="250" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="250" cy="150" r="4" fill="#334155"/>
<line x1="250" y1="150" x2="250" y2="166" stroke="#334155" stroke-width="2.5"/>
<line x1="222" y1="166" x2="318" y2="166" stroke="#334155" stroke-width="2.5"/>
<line x1="222" y1="166" x2="222" y2="178" stroke="#334155" stroke-width="2.5"/>
<line x1="210" y1="178" x2="234" y2="178" stroke="#dc2626" stroke-width="3.5"/>
<line x1="210" y1="190" x2="234" y2="190" stroke="#dc2626" stroke-width="3.5"/>
<line x1="222" y1="190" x2="222" y2="244" stroke="#334155" stroke-width="2.5"/>
<line x1="318" y1="166" x2="318" y2="178" stroke="#334155" stroke-width="2.5"/>
<rect x="300" y="178" width="36" height="24" rx="3" fill="#f8fafc" stroke="#dc2626" stroke-width="2.5"/>
<line x1="318" y1="202" x2="318" y2="244" stroke="#334155" stroke-width="2.5"/>
<line x1="222" y1="244" x2="318" y2="244" stroke="#334155" stroke-width="2.5"/>
<line x1="270" y1="244" x2="270" y2="258" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(270, 272)}
<text x="204" y="184" text-anchor="end" font-size="11" font-weight="bold" fill="#dc2626">100pF</text>
<text x="344" y="196" font-size="11" font-weight="bold" fill="#dc2626">1MΩ</text>
<text x="352" y="222" font-size="11" font-weight="bold" fill="#b45309">探头</text>
<text x="300" y="140" text-anchor="end" font-size="11" font-weight="bold" fill="#2563eb">读到 V×0.91</text>
<rect x="40" y="296" width="380" height="86" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
<text x="54" y="320" font-size="11.5" font-weight="bold" fill="#b91c1c">×1 档：误差 9%，还想测什么？</text>
<text x="54" y="342" font-size="11" fill="#475569">100kΩ 源阻 + 1MΩ 探头 = 分压到 0.909</text>
<text x="54" y="362" font-size="11" fill="#475569">而且 100k×100pF = 10µs → fc 只剩 16kHz</text>
<text x="54" y="376" font-size="11" font-weight="bold" fill="#dc2626">高频信号直接被探头削圆</text>
<text x="440" y="320" font-size="11.5" font-weight="bold" fill="#059669">×10 档：10MΩ‖10pF</text>
<text x="440" y="342" font-size="11" fill="#475569">分压系数 0.990（误差 1%）</text>
<text x="440" y="362" font-size="11" fill="#475569">时间常数 1µs → fc 提到 159kHz</text>
<text x="440" y="382" font-size="11" font-weight="bold" fill="#059669">代价：探头电容被「等效缩小」10 倍</text>
<text x="270" y="426" text-anchor="middle" font-size="11" fill="#475569">Jim Williams：先问「这个测量会不会改电路」，再按下探头</text>
<line x1="60" y1="470" x2="500" y2="470" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="270" y="502" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">② 另外两个「一按就出事」的动作</text>
<circle cx="90" cy="540" r="26" fill="#fef2f2" stroke="#dc2626" stroke-width="2.5"/>
<text x="90" y="536" text-anchor="middle" font-size="12" font-weight="bold" fill="#b91c1c">A</text>
<text x="90" y="554" text-anchor="middle" font-size="11" font-weight="bold" fill="#b91c1c">表</text>
<text x="132" y="534" font-size="11.5" font-weight="bold" fill="#b91c1c">电流档 = 短路</text>
<text x="132" y="554" font-size="11" fill="#475569">万用表电流档内阻≈0，并到电源上就是放炮</text>
<text x="132" y="574" font-size="11" font-weight="bold" fill="#dc2626">测完立刻把表笔插回电压孔</text>
<text x="420" y="536" font-size="11.5" font-weight="bold" fill="#dc2626">探头地夹 = 市电地</text>
<text x="420" y="556" font-size="11" fill="#475569">示波器地夹与市电共地</text>
<text x="420" y="574" font-size="11" font-weight="bold" fill="#dc2626">隔离变压器 或 差分探头，二选一</text>
<text x="270" y="604" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">上电第一次：串限流灯泡 / 恒流 50mA —— 冒烟的是灯泡，不是芯片</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.3s" repeatCount="indefinite" path="M70,150 L148,150"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.8s" repeatCount="indefinite" path="M202,150 L248,150"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-1.3s" repeatCount="indefinite" path="M250,152 L250,166 L222,166 L222,180"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DP}s" begin="-1.8s" repeatCount="indefinite" path="M318,202 L318,244 L270,244 L270,258"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.6s" repeatCount="indefinite" path="M224,166 L316,166"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DP}s" begin="-1.1s" repeatCount="indefinite" path="M318,168 L318,200"/></circle>
<circle r="4.5" fill="#059669"><animateMotion dur="{DP}s" begin="-1.6s" repeatCount="indefinite" path="M270,246 L270,262"/></circle>
{pulse(216, 126, 90, 22, '#2563eb', 1.9, 6)}
{pulse(52, 500, 96, 78, '#dc2626', 1.6, 12)}
{pulse(52, 296, 300, 86, '#dc2626', 2.0, 10)}
{pulse(400, 512, 380, 74, '#dc2626', 2.4, 10)}
<circle r="5" fill="#dc2626"><animateMotion dur="{DP}s" begin="-0.5s" repeatCount="indefinite" path="M90,514 L90,566 L90,514"/></circle>
'''
    svg += caption("① 探头不是「接上去看看」——它是 1MΩ‖100pF 的负载，会分压也会滤波", "#dc2626", DP,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=628)
    svg += caption("② 测模拟节点一律 ×10 档：误差从 9% 降到 1%，带宽从 16kHz 提到 159kHz", "#059669", DP,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=628)
    svg += caption("③ 电流档并联 = 短路；示波器地夹接市电节点 = 短路——两个都是「一按就出事」", "#b91c1c", DP,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=628)
    svg += caption("④ 新板第一次上电先限流：让最便宜的元件先冒烟", "#b45309", DP,
                   "0;0;1;1", "0;0.85;0.9;1", y=628)
    save('probe-loading.svg', svg + '</svg>')

# ======================= 图 55：CMOS 传输门为什么必须 N+P 并联（第 8 章 8.1） =======================
def make_transfer_gate():
    DG = 10
    VT, R0, VDD = 1.0, 80.0, 5.0
    X0, X1, Y0, Y1 = 400, 760, 132, 402
    def px(v):
        return X0 + v/VDD*(X1-X0)
    def ry(r):
        # 电阻轴按惯例：Ron 越大越靠上（∞ 冲出图顶），所以 1kΩ 在顶、10Ω 在底
        r = min(max(r, 10.0), 1000.0)
        return Y0 + (3-np.log10(r))/2*(Y1-Y0)
    def ron_n(vin):
        d = VDD - vin - VT
        return R0/d if d > 0.06 else 1000.0
    def ron_p(vin):
        d = vin - VT
        return R0/d if d > 0.06 else 1000.0
    def ron_par(vin):
        rn, rp = ron_n(vin), ron_p(vin)
        return 1/(1/rn + 1/rp)
    def curve(fn, color, wid=2.6):
        pts = [f"{px(v):.0f},{ry(fn(v)):.0f}" for v in np.linspace(0, VDD, 240)]
        return '<path d="M' + " L".join(pts) + f'" fill="none" stroke="{color}" stroke-width="{wid}"/>'
    svg = svg_open('CMOS 传输门：一只管子总有一段「使不上劲」', h=640)
    svg += f'''
<text x="190" y="52" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">NMOS + PMOS 并联 = 全程平坦</text>
<text x="40" y="92" font-size="11.5" fill="#475569">Vin 靠近 0V：NMOS 的 V_GS 最大 →</text>
<text x="52" y="110" font-size="11.5" font-weight="bold" fill="#2563eb">NMOS 挑大梁（Ron 20Ω）</text>
<text x="40" y="140" font-size="11.5" fill="#475569">Vin 逼近 VDD：NMOS 的 V_GS→0</text>
<text x="52" y="158" font-size="11.5" font-weight="bold" fill="#dc2626">NMOS 彻底罢工（Ron→∞）</text>
<text x="40" y="188" font-size="11.5" fill="#475569">PMOS 恰好相反：Vin 越低压</text>
<text x="52" y="206" font-size="11.5" font-weight="bold" fill="#dc2626">V_SG 越不够，低端罢工</text>
<text x="40" y="236" font-size="11.5" font-weight="bold" fill="#059669">两只并联：谁行谁上，接力覆盖</text>
<text x="52" y="254" font-size="11.5" fill="#475569">Ron 全程锁在 20~27Ω</text>
<text x="40" y="284" font-size="11" fill="#475569">代价：多一只管子、多一个</text>
<text x="40" y="302" font-size="11" fill="#475569">反相控制信号——CD4066 内部</text>
<text x="40" y="320" font-size="11" fill="#475569">就是这么干的</text>
<polygon points="60,380 60,440 140,410" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="66" y="402" font-size="11" font-weight="bold" fill="#dc2626">N</text>
<text x="66" y="428" font-size="11" font-weight="bold" fill="#2563eb">P</text>
<line x1="140" y1="410" x2="200" y2="410" stroke="#334155" stroke-width="2.5"/>
<line x1="200" y1="410" x2="200" y2="470" stroke="#334155" stroke-width="2.5"/>
{resistor_v(150, 440, 30, '')}
<text x="120" y="500" font-size="11" fill="#475569">导通电阻 Ron</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DG}s" begin="-0.3s" repeatCount="indefinite" path="M20,410 L58,410"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DG}s" begin="-0.9s" repeatCount="indefinite" path="M142,410 L198,410"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DG}s" begin="-1.5s" repeatCount="indefinite" path="M200,412 L200,468"/></circle>
<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<text x="{X1}" y="{Y1+42}" text-anchor="end" font-size="11" fill="#475569">Vin →</text>
<text x="{X0-6}" y="{ry(10)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">10Ω</text>
<text x="{X0-6}" y="{ry(100)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">100Ω</text>
<text x="{X0-6}" y="{ry(1000)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">1kΩ</text>
<text x="{px(1):.0f}" y="{Y1+24}" text-anchor="middle" font-size="10" fill="#475569">1V</text>
<text x="{px(2.5):.0f}" y="{Y1+24}" text-anchor="middle" font-size="10" fill="#475569">2.5V</text>
<text x="{px(5):.0f}" y="{Y1+24}" text-anchor="middle" font-size="10" fill="#475569">5V</text>
<line x1="{px(4):.0f}" y1="{Y0}" x2="{px(4):.0f}" y2="{Y1}" stroke="#dc2626" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="{px(1):.0f}" y1="{Y0}" x2="{px(1):.0f}" y2="{Y1}" stroke="#dc2626" stroke-width="1" stroke-dasharray="4,3"/>
{curve(ron_n, '#dc2626')}
{curve(ron_p, '#2563eb')}
{curve(ron_par, '#059669')}
<text x="{px(3.85):.0f}" y="{Y0-10}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">NMOS 在此罢工</text>
<text x="{px(1.15):.0f}" y="{Y0-10}" text-anchor="start" font-size="10.5" font-weight="bold" fill="#2563eb">PMOS 在此罢工</text>
<text x="{px(2.5):.0f}" y="{ry(26.7)-16:.0f}" text-anchor="middle" font-size="11" font-weight="bold" fill="#059669">并联：20~27Ω 全程平坦</text>
<text x="580" y="500" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">口诀：N 管送低、P 管送高，并联才全都能送</text>
<circle r="5" fill="#dc2626"><animateMotion dur="{DG}s" repeatCount="indefinite" path="M{px(0):.0f},{ry(20):.0f} L{px(3.9):.0f},{ry(970):.0f}" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#059669">
<animateMotion dur="{DG}s" repeatCount="indefinite" path="M{px(0):.0f},{ry(20):.0f} L{px(2.5):.0f},{ry(26.7):.0f} L{px(5):.0f},{ry(20):.0f}" keyPoints="0;1" keyTimes="0;1"/></circle>
'''
    svg += caption("① 低端：NMOS 的 V_GS 最足 → 20Ω；此时 PMOS 的 V_SG 反而最弱", "#2563eb", DG,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=544)
    svg += caption("② 高端：NMOS 的 V_GS→0，Ron→∞ 彻底罢工——这就是「N 管传高电平会掉一个 V_T」", "#dc2626", DG,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=544)
    svg += caption("③ 两只并联：低端 N 扛、高端 P 扛、中间一起扛 → Ron 全程 20~27Ω", "#059669", DG,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=544)
    svg += caption("④ 代价只是多一只管子和一个反相控制——所以模拟开关内部永远是「传输门」", "#b45309", DG,
                   "0;0;1;1", "0;0.85;0.9;1", y=544)
    svg += note_box("单管传的是「有盲区」的电压；传输门传的是「全程达标」的电阻——信号完整性从第一只开关就开始算", 584, DG,
                    "0;0.9;0.94;1", w=750)
    save('transfer-gate.svg', svg + '</svg>')

# ======================= 图 56：三个基本拓扑对比（第 12 章 12.2） =======================
def make_three_topologies():
    DT = 11
    def panel(x, title, color, formula, rows, rin, cmrr, phase):
        p = f'<rect x="{x}" y="60" width="238" height="300" rx="10" fill="#f8fafc" stroke="{color}" stroke-width="1.8"/>'
        p += f'<text x="{x+119}" y="86" text-anchor="middle" font-size="13.5" font-weight="bold" fill="{color}">{title}</text>'
        p += f'<text x="{x+119}" y="110" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">{formula}</text>'
        p += f'<line x1="{x+14}" y1="122" x2="{x+224}" y2="122" stroke="#cbd5e1" stroke-width="1"/>'
        y = 148
        for k, v in rows:
            p += f'<text x="{x+18}" y="{y}" font-size="11.5" fill="#475569">{k}</text>'
            p += f'<text x="{x+220}" y="{y}" text-anchor="end" font-size="11.5" font-weight="bold" fill="#334155">{v}</text>'
            y += 24
        p += f'<line x1="{x+14}" y1="{y-6}" x2="{x+224}" y2="{y-6}" stroke="#e2e8f0" stroke-width="1"/>'
        p += f'<text x="{x+18}" y="{y+16}" font-size="11" fill="#64748b">输入阻抗</text>'
        p += f'<text x="{x+220}" y="{y+16}" text-anchor="end" font-size="11" font-weight="bold" fill="{color}">{rin}</text>'
        p += f'<text x="{x+18}" y="{y+36}" font-size="11" fill="#64748b">共模抑制</text>'
        p += f'<text x="{x+220}" y="{y+36}" text-anchor="end" font-size="11" font-weight="bold" fill="{color}">{cmrr}</text>'
        p += f'<text x="{x+18}" y="{y+56}" font-size="11" fill="#64748b">输出相位</text>'
        p += f'<text x="{x+220}" y="{y+56}" text-anchor="end" font-size="11" font-weight="bold" fill="{color}">{phase}</text>'
        return p
    svg = svg_open('三种基本拓扑：同一只运放，三条推演路径', h=620)
    svg += f'''
<text x="400" y="54" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#64748b">全部从「虚短 + 虚断」推出来——增益都由外接电阻决定，与运放本身无关</text>
{panel(30, '反相放大', '#2563eb', 'A_v = −R_f / R_in = −10', [('R_f', '100k'), ('R_in', '10k')], '≈ R_in = 10k（低）', '无（+端接地）', '反相 180°')}
{panel(281, '同相放大', '#059669', 'A_v = 1 + R_f / R_1 = 10', [('R_f', '90k'), ('R_1', '10k')], '≈ ∞（进 +端）', '无（+端进信号）', '同相 0°')}
{panel(532, '差分放大', '#7c3aed', 'A_v = R_f / R_1 = 10', [('R_f', '100k'), ('R_1', '10k')], '≈ 2×R_1 = 20k', '有，但需四电阻配对', '差模同相')}
<line x1="40" y1="400" x2="760" y2="400" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="428" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309">同一只运放、同一组电阻比例 → 同一份 10 倍增益，差别只在「信号从哪个端进去、哪个端接地」</text>
<text x="400" y="452" text-anchor="middle" font-size="11.5" fill="#475569">反相：虚地把输入阻抗钉在 R_in；同相：信号直接进 +端，输入阻抗接近无穷但共模就是信号本身</text>
<text x="400" y="476" text-anchor="middle" font-size="11.5" fill="#475569">差分：唯一能放大「两个信号之差」的拓扑，代价是四只电阻必须配对，否则共模抑制崩掉</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DT}s" begin="-0.2s" repeatCount="indefinite" path="M150,200 L150,140"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DT}s" begin="-0.9s" repeatCount="indefinite" path="M401,200 L401,140"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DT}s" begin="-1.6s" repeatCount="indefinite" path="M652,200 L652,140"/></circle>
{pulse(38, 128, 222, 30, '#2563eb', 2.0, 8)}
{pulse(289, 128, 222, 30, '#059669', 2.0, 8)}
{pulse(540, 128, 222, 30, '#7c3aed', 2.0, 8)}
<circle cx="149" cy="356" r="5" fill="none" stroke="#2563eb" stroke-width="2.2">
<animate attributeName="r" values="5;11;5" dur="1.7s" repeatCount="indefinite"/></circle>
<circle cx="400" cy="356" r="5" fill="none" stroke="#059669" stroke-width="2.2">
<animate attributeName="r" values="5;11;5" dur="1.7s" begin="-0.6s" repeatCount="indefinite"/></circle>
<circle cx="651" cy="356" r="5" fill="none" stroke="#7c3aed" stroke-width="2.2">
<animate attributeName="r" values="5;11;5" dur="1.7s" begin="-1.2s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① 反相：−端是「虚地」（0V），输入电流全部流过 R_in 与 R_f → 增益 = −R_f/R_in", "#2563eb", DT,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=516)
    svg += caption("② 同相：信号进 +端，−端靠反馈「追平」它 → 增益 = 1 + R_f/R_1，输入阻抗天然极高", "#059669", DT,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=516)
    svg += caption("③ 差分：两个输入各走一条分压，输出只认「差」——共模被两边一起减掉", "#7c3aed", DT,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=516)
    svg += caption("④ 选型口诀：要控阻抗选反相、要高阻缓冲选同相、要抗共模选差分（但电阻必须配对）", "#b45309", DT,
                   "0;0;1;1", "0;0.85;0.9;1", y=516)
    svg += note_box("三种拓扑的增益公式都能从虚短虚断一步推出——真正的差别是输入阻抗、共模范围和电阻配对的代价", 560, DT,
                    "0;0.9;0.94;1", w=760)
    save('three-topologies.svg', svg + '</svg>')

# ======================= 图 57：三态与高阻（第 5 章 5.4） =======================
def make_tristate_bus():
    DZ = 11
    svg = svg_open('三态与高阻：总线上为什么必须有人「闭嘴」', h=620)
    svg += f'''
<text x="200" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">两个驱动器挂在同一根总线上</text>
<line x1="60" y1="96" x2="60" y2="130" stroke="#334155" stroke-width="2.5"/>
<text x="46" y="92" font-size="11.5" font-weight="bold" fill="#b45309">+5V</text>
<rect x="48" y="130" width="24" height="34" rx="3" fill="#fffbeb" stroke="#b45309" stroke-width="2"/>
<text x="86" y="152" font-size="11" font-weight="bold" fill="#b45309">10k 上拉</text>
<line x1="60" y1="164" x2="60" y2="196" stroke="#334155" stroke-width="2.5"/>
<line x1="60" y1="196" x2="330" y2="196" stroke="#334155" stroke-width="2.5"/>
<rect x="90" y="230" width="80" height="52" rx="6" fill="#f8fafc" stroke="#2563eb" stroke-width="2.5"/>
<text x="130" y="252" text-anchor="middle" font-size="12" font-weight="bold" fill="#2563eb">驱动器 A</text>
<text x="130" y="272" text-anchor="middle" font-size="10.5" fill="#475569">EN_A</text>
<line x1="130" y1="230" x2="130" y2="196" stroke="#2563eb" stroke-width="2.5"/>
<rect x="250" y="230" width="80" height="52" rx="6" fill="#f8fafc" stroke="#dc2626" stroke-width="2.5"/>
<text x="290" y="252" text-anchor="middle" font-size="12" font-weight="bold" fill="#dc2626">驱动器 B</text>
<text x="290" y="272" text-anchor="middle" font-size="10.5" fill="#475569">EN_B</text>
<line x1="290" y1="230" x2="290" y2="196" stroke="#dc2626" stroke-width="2.5"/>
<circle cx="210" cy="196" r="5" fill="#334155"/>
<line x1="210" y1="196" x2="210" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="196" y1="150" x2="224" y2="150" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="196" y1="162" x2="224" y2="162" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="210" y1="162" x2="210" y2="130" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(210, 130)}
<text x="228" y="158" font-size="11" font-weight="bold" fill="#7c3aed">总线电容 20pF</text>
<text x="330" y="190" font-size="11" font-weight="bold" fill="#334155">总线</text>
<circle cx="130" cy="196" r="5" fill="#2563eb">
<animate attributeName="opacity" values="1;0.15;1" dur="1.4s" repeatCount="indefinite"/></circle>
<circle cx="290" cy="196" r="5" fill="#dc2626">
<animate attributeName="opacity" values="0.15;1;0.15" dur="1.4s" repeatCount="indefinite"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DZ}s" begin="-0.3s" repeatCount="indefinite" path="M130,228 L130,198"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DZ}s" begin="-0.9s" repeatCount="indefinite" path="M290,228 L290,198"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DZ}s" begin="-1.5s" repeatCount="indefinite" path="M212,198 L212,152"/></circle>
<line x1="420" y1="70" x2="420" y2="492" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="610" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">三种状态：谁在说话，谁必须闭嘴</text>
'''
    rows = [
        ('① A 驱动、B 高阻', '总线 = A 的电平', '正常：一人说话，其他人闭嘴', '#2563eb'),
        ('② B 驱动、A 高阻', '总线 = B 的电平', '正常：换人说话，电平随之改变', '#dc2626'),
        ('③ 两个都高阻', '总线悬空', '只靠 10k 上拉+漏电漂移，τ=10k×20pF=0.2µs', '#7c3aed'),
        ('④ 两个同时驱动', '电平打架', '直通电流！毫安级到安培级，发热甚至烧管', '#b91c1c'),
    ]
    y = 84
    for t, mid, note, col in rows:
        svg += f'<rect x="446" y="{y}" width="330" height="74" rx="8" fill="#f8fafc" stroke="{col}" stroke-width="1.8"/>'
        svg += f'<text x="462" y="{y+26}" font-size="12.5" font-weight="bold" fill="{col}">{t}</text>'
        svg += f'<text x="462" y="{y+48}" font-size="11.5" font-weight="bold" fill="#1e293b">{mid}</text>'
        svg += f'<text x="462" y="{y+66}" font-size="11" fill="#475569">{note}</text>'
        y += 88
    svg += f'''
<text x="400" y="510" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309">高阻态不是「输出低」，是「输出端几乎从电路里消失」——它让总线归别人管</text>
<text x="400" y="534" text-anchor="middle" font-size="11.5" fill="#475569">代价：悬空的总线电平不定（要靠上拉/下拉定住），且悬空输入会让下游 CMOS 输入级两头导通、白耗电</text>
{pulse(446, 336, 330, 74, '#b91c1c', 1.8, 10)}
<circle cx="646" cy="373" r="5" fill="none" stroke="#b91c1c" stroke-width="2.4">
<animate attributeName="r" values="5;13;5" dur="1.6s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.2;0.95" dur="1.6s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① 同一时刻只能有一个驱动器在说话——这就是「三态」存在的全部理由", "#2563eb", DZ,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=576)
    svg += caption("② 关掉的那一方输出高阻：既不拉高也不拉低，等于从总线上「隐身」", "#059669", DZ,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=576)
    svg += caption("③ 全部高阻：总线悬空 → 靠上拉定电平；没上拉就是天线，电平不定还白耗电", "#7c3aed", DZ,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=576)
    svg += caption("④ 两个同时驱动且电平相反 = 直通电流——这是硬件上最容易烧片的错误之一", "#b91c1c", DZ,
                   "0;0;1;1", "0;0.85;0.9;1", y=576)
    save('tristate-bus.svg', svg + '</svg>')

# ======================= 图 58：推挽输出与直通电流（第 5 章 5.1） =======================
def make_pushpull_stage():
    DP = 11
    svg = svg_open('推挽输出：两个方向都能驱动，但绝不能同时开', h=620)
    svg += f'''
<text x="200" y="50" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">图腾柱：上管推高、下管拉低</text>
<text x="88" y="86" text-anchor="end" font-size="11.5" font-weight="bold" fill="#b45309">VDD 5V</text>
<line x1="150" y1="92" x2="150" y2="120" stroke="#334155" stroke-width="2.5"/>
<line x1="96" y1="92" x2="150" y2="92" stroke="#334155" stroke-width="2.5"/>
<rect x="112" y="120" width="76" height="46" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5"/>
<text x="150" y="140" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">上管 PMOS</text>
<text x="150" y="158" text-anchor="middle" font-size="10.5" fill="#475569">ON = 推高</text>
<line x1="150" y1="166" x2="150" y2="196" stroke="#334155" stroke-width="2.5"/>
<circle cx="150" cy="196" r="4.5" fill="#334155"/>
<line x1="150" y1="196" x2="290" y2="196" stroke="#334155" stroke-width="2.5"/>
<text x="296" y="192" font-size="12" font-weight="bold" fill="#059669">OUT</text>
<line x1="150" y1="196" x2="150" y2="226" stroke="#334155" stroke-width="2.5"/>
<rect x="112" y="226" width="76" height="46" rx="6" fill="#fef2f2" stroke="#dc2626" stroke-width="2.5"/>
<text x="150" y="246" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#dc2626">下管 NMOS</text>
<text x="150" y="264" text-anchor="middle" font-size="10.5" fill="#475569">ON = 拉低</text>
<line x1="150" y1="272" x2="150" y2="300" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(150, 314)}
<circle r="5" fill="#2563eb"><animateMotion dur="{DP}s" begin="-0.3s" repeatCount="indefinite" path="M150,92 L150,118"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DP}s" begin="-0.3s" repeatCount="indefinite" path="M152,168 L152,194 L288,196"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DP}s" begin="-1.2s" repeatCount="indefinite" path="M288,200 L152,200 L152,274 L150,298"/></circle>
<circle r="4" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-2.0s" repeatCount="indefinite" path="M150,116 L150,270 L150,116"/></circle>
<text x="330" y="120" font-size="11.5" font-weight="bold" fill="#2563eb">输出高：上管供流</text>
<text x="330" y="138" font-size="11" fill="#475569">（source current）</text>
<text x="330" y="170" font-size="11.5" font-weight="bold" fill="#dc2626">输出低：下管吸流</text>
<text x="330" y="188" font-size="11" fill="#475569">（sink current）</text>
<text x="330" y="220" font-size="11.5" font-weight="bold" fill="#059669">两个方向都主动驱动</text>
<text x="330" y="238" font-size="11" fill="#475569">——比开漏快得多</text>
<rect x="40" y="340" width="330" height="130" rx="8" fill="#fef2f2" stroke="#b91c1c" stroke-width="2"/>
<text x="56" y="366" font-size="12" font-weight="bold" fill="#b91c1c">⚠ 两个推挽直连 = 短路</text>
<text x="56" y="390" font-size="11" fill="#475569">一只推高、一只推低，电流只受管阻限制：</text>
<text x="56" y="410" font-size="11" font-weight="bold" fill="#dc2626">I = 5V / (25Ω+25Ω) = 100mA</text>
<text x="56" y="432" font-size="11" fill="#475569">够烧 IO；所以共享总线绝不能用推挽</text>
<text x="56" y="454" font-size="11" fill="#475569">（要用开漏 / 三态，见 5.2、5.4）</text>
<text x="420" y="340" font-size="12" font-weight="bold" fill="#b45309">切换瞬间：直通电流（shoot-through）</text>
<text x="420" y="362" font-size="11" fill="#475569">上下管换班的几 ns 里两个都半开，</text>
<text x="420" y="382" font-size="11" fill="#475569">VDD 到 GND 被短暂打通 → 电源毛刺 +</text>
<text x="420" y="402" font-size="11" fill="#475569">动态功耗的元凶。芯片靠「死区时间」</text>
<text x="420" y="422" font-size="11" fill="#475569">（先关后开）把它压掉。</text>
<text x="420" y="452" font-size="11.5" font-weight="bold" fill="#7c3aed">音频乙类推挽还要防交越失真（见 11.4）</text>
<line x1="40" y1="490" x2="760" y2="490" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="516" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">三兄弟对比：推挽 vs 开漏 vs 三态</text>
<text x="400" y="542" text-anchor="middle" font-size="11.5" fill="#475569">推挽：两个方向都主动驱动，但**不能共享总线**　·　开漏：只能拉低，靠上拉出高，**可以线与**　·　三态：加了「隐身」态，**可以共享总线**</text>
<text x="400" y="566" text-anchor="middle" font-size="11" fill="#64748b">选哪种，先问一句：这根线上会不会有第二个驱动器？</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.6s" repeatCount="indefinite" path="M98,92 L148,92"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DP}s" begin="-1.6s" repeatCount="indefinite" path="M150,304 L150,312"/></circle>
<circle r="4.5" fill="#2563eb"><animateMotion dur="{DP}s" begin="-2.4s" repeatCount="indefinite" path="M154,196 L286,196"/></circle>
{pulse(290, 176, 70, 24, '#059669', 1.7, 6)}
{pulse(40, 338, 330, 134, '#b91c1c', 1.9, 10)}
'''
    svg += caption("① 上管导通 = 主动推高；下管导通 = 主动拉低——两个方向都有低阻通路", "#2563eb", DP,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=600)
    svg += caption("② 所以推挽输出上升/下降沿都快、驱动强——MCU GPIO 默认就是它", "#059669", DP,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=600)
    svg += caption("③ 代价一：两个推挽直连就是短路，电流只受管阻限制（100mA 级）", "#b91c1c", DP,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=600)
    svg += caption("④ 代价二：换班瞬间有直通电流 → 电源毛刺；要靠死区时间压掉", "#b45309", DP,
                   "0;0;1;1", "0;0.85;0.9;1", y=600)
    save('pushpull-stage.svg', svg + '</svg>')

# ======================= 图 59：LM393 内部解剖（第 7 章 7.2） =======================
def make_lm393_inside():
    DL = 11
    svg = svg_open('解剖 LM393：关键是那只「只会拉低」的输出管', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">PNP 差分输入 → 增益级 → 开集电极输出管</text>
<rect x="40" y="90" width="150" height="80" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5"/>
<text x="115" y="118" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#2563eb">① PNP 差分输入</text>
<text x="115" y="140" text-anchor="middle" font-size="10.5" fill="#475569">共模 0 ~ Vcc−1.5V</text>
<text x="115" y="158" text-anchor="middle" font-size="10.5" fill="#475569">能一路接到地</text>
<line x1="190" y1="130" x2="230" y2="130" stroke="#334155" stroke-width="2.5"/>
<circle r="5" fill="#2563eb"><animateMotion dur="{DL}s" begin="-0.3s" repeatCount="indefinite" path="M192,130 L228,130"/></circle>
<rect x="230" y="90" width="140" height="80" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="300" y="118" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">② 增益级</text>
<text x="300" y="140" text-anchor="middle" font-size="10.5" fill="#475569">把 mV 差放大成判决</text>
<text x="300" y="158" text-anchor="middle" font-size="10.5" fill="#475569">V_OS 2mV 决定精度</text>
<line x1="370" y1="130" x2="410" y2="130" stroke="#334155" stroke-width="2.5"/>
<circle r="5" fill="#334155"><animateMotion dur="{DL}s" begin="-0.9s" repeatCount="indefinite" path="M372,130 L408,130"/></circle>
<rect x="410" y="90" width="160" height="80" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="2.5"/>
<text x="490" y="118" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#dc2626">③ 开集电极输出管</text>
<text x="490" y="140" text-anchor="middle" font-size="10.5" fill="#475569">只有一只 NPN 对地</text>
<text x="490" y="158" text-anchor="middle" font-size="10.5" fill="#475569">只会拉低，不会推高</text>
<rect x="410" y="210" width="160" height="60" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="2"/>
<text x="490" y="234" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">上拉电阻 10k</text>
<text x="490" y="254" text-anchor="middle" font-size="10.5" fill="#475569">额定范围内选上拉电压</text>
<line x1="490" y1="170" x2="490" y2="210" stroke="#dc2626" stroke-width="2.5"/>
<line x1="490" y1="270" x2="490" y2="300" stroke="#334155" stroke-width="2.5"/>
<circle cx="490" cy="300" r="4.5" fill="#334155"/>
<line x1="490" y1="300" x2="590" y2="300" stroke="#334155" stroke-width="2.5"/>
<text x="596" y="296" font-size="12" font-weight="bold" fill="#059669">OUT</text>
<circle r="5" fill="#b45309"><animateMotion dur="{DL}s" begin="-1.5s" repeatCount="indefinite" path="M490,272 L490,212"/></circle>
<text x="584" y="222" font-size="11.5" font-weight="bold" fill="#dc2626">输出管导通 → OUT 拉到地</text>
<text x="584" y="244" font-size="11" fill="#475569">输出管关断 → 10k 拉到高</text>
<text x="584" y="266" font-size="11" fill="#475569">NPN 集电极输出，需外接上拉</text>
<rect x="40" y="200" width="260" height="120" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"/>
<text x="56" y="226" font-size="11.5" font-weight="bold" fill="#334155">开集电极的三个红利</text>
<text x="56" y="250" font-size="11" fill="#475569">① 上拉接 3.3V → 5V 器件直接比 3.3V 逻辑</text>
<text x="56" y="272" font-size="11" fill="#475569">② 多个输出并联 = 线与（谁拉低谁说了算）</text>
<text x="56" y="294" font-size="11" fill="#475569">③ 不接上拉就没有高电平——这也能当使能</text>
<line x1="40" y1="350" x2="760" y2="350" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="376" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">LM393 关键参数（选型直接看这五行）</text>
<text x="120" y="406" font-size="11.5" font-weight="bold" fill="#b45309">V_OS 2mV</text>
<text x="120" y="426" font-size="10.5" fill="#475569">判决精度</text>
<text x="270" y="406" font-size="11.5" font-weight="bold" fill="#b45309">共模 0~Vcc−1.5V</text>
<text x="270" y="426" font-size="10.5" fill="#475569">可接地</text>
<text x="450" y="406" font-size="11.5" font-weight="bold" fill="#b45309">t_PD ≈1.3µs</text>
<text x="450" y="426" font-size="10.5" fill="#475569">大信号传播延迟</text>
<text x="610" y="406" font-size="11.5" font-weight="bold" fill="#b45309">2~36V 供电</text>
<text x="610" y="426" font-size="10.5" fill="#475569">单/双电源通吃</text>
<text x="700" y="406" font-size="11.5" font-weight="bold" fill="#b45309">I_q 0.4mA</text>
<text x="700" y="426" font-size="10.5" fill="#475569">低功耗</text>
{pulse(40, 88, 152, 84, '#2563eb', 2.0, 8)}
{pulse(408, 88, 164, 84, '#dc2626', 2.0, 8)}
<circle cx="490" cy="130" r="5" fill="none" stroke="#dc2626" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.8s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① 输入级用 PNP：共模范围能一路到地——单电源接地信号直接能比", "#2563eb", DL,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=468)
    svg += caption("② 输出只有一只对地 NPN：只会拉低、不会推高，所以必须外接上拉", "#dc2626", DL,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=468)
    svg += caption("③ 开集电极不是缺点：上拉电压须符合额定值 → 天然电平转换 + 多路可与（窗口检测器）", "#059669", DL,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=468)
    svg += caption("④ 选型只看五行：V_OS、共模范围、传播延迟、供电范围、静态电流", "#b45309", DL,
                   "0;0;1;1", "0;0.85;0.9;1", y=468)
    svg += note_box("LM393 的全部脾气都来自「PNP 输入 + 开集电极输出」这两个选择——先看结构，再看参数表", 510, DL,
                    "0;0.9;0.94;1", w=740)
    save('lm393-inside.svg', svg + '</svg>')

# ======================= 图 60：齐纳 vs 带隙（第 9 章 9.1） =======================
def make_ref_showdown():
    DR = 11
    svg = svg_open('齐纳 vs 带隙：两种基准，两套温漂账', h=672)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">同一个问题（要一个不动的电压），两条技术路线</text>
<rect x="34" y="76" width="350" height="240" rx="10" fill="#f8fafc" stroke="#b45309" stroke-width="1.8"/>
<text x="209" y="104" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#b45309">齐纳基准（Zener）</text>
<line x1="60" y1="150" x2="100" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="100" y1="126" x2="100" y2="174" stroke="#334155" stroke-width="2.5"/>
<path d="M88,132 L100,122 L112,132 Z" fill="#334155"/>
<path d="M88,168 L100,178 L112,168 Z" fill="#334155"/>
<line x1="100" y1="150" x2="140" y2="150" stroke="#334155" stroke-width="2.5"/>
<rect x="140" y="138" width="46" height="24" rx="3" fill="#fffbeb" stroke="#b45309" stroke-width="2.5"/>
<text x="163" y="126" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">R_s</text>
<line x1="186" y1="150" x2="230" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="230" y1="150" x2="230" y2="186" stroke="#334155" stroke-width="2.5"/>
<path d="M216,186 L244,186 L230,208 Z" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<line x1="216" y1="208" x2="244" y2="208" stroke="#334155" stroke-width="3.5"/>
<line x1="230" y1="208" x2="230" y2="238" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(230, 252)}
<line x1="230" y1="150" x2="300" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="300" cy="150" r="4.5" fill="#334155"/>
<text x="306" y="146" font-size="11.5" font-weight="bold" fill="#059669">V_REF</text>
<text x="60" y="290" font-size="11.5" font-weight="bold" fill="#b45309">5.6V 附近温漂最小</text>
<text x="230" y="290" font-size="11.5" font-weight="bold" fill="#dc2626">但噪声大、精度差</text>
<text x="60" y="310" font-size="11" fill="#475569">（齐纳击穿负温漂 ≈ 雪崩正温漂，互相抵消）</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DR}s" begin="-0.3s" repeatCount="indefinite" path="M62,150 L98,150"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DR}s" begin="-0.9s" repeatCount="indefinite" path="M188,150 L298,150"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DR}s" begin="-1.5s" repeatCount="indefinite" path="M230,210 L230,250"/></circle>
<rect x="416" y="76" width="350" height="240" rx="10" fill="#f8fafc" stroke="#2563eb" stroke-width="1.8"/>
<text x="591" y="104" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#2563eb">带隙基准（Bandgap）</text>
<text x="440" y="140" font-size="12" font-weight="bold" fill="#dc2626">V_BE</text>
<text x="440" y="160" font-size="10.5" fill="#475569">随温度下降</text>
<text x="440" y="180" font-size="11.5" font-weight="bold" fill="#dc2626">−2mV/℃</text>
<text x="560" y="140" font-size="12" font-weight="bold" fill="#059669">+ K·ΔV_BE</text>
<text x="560" y="160" font-size="10.5" fill="#475569">随温度上升</text>
<text x="560" y="180" font-size="11.5" font-weight="bold" fill="#059669">+0.177mV/℃×K</text>
<line x1="440" y1="196" x2="740" y2="196" stroke="#cbd5e1" stroke-width="1"/>
<text x="440" y="220" font-size="12" font-weight="bold" fill="#7c3aed">合成：K=2/0.177≈11.3</text>
<text x="440" y="242" font-size="11.5" fill="#475569">V_REF = V_BE + K·V_T·ln8 ≈ 1.26V</text>
<text x="440" y="264" font-size="11.5" font-weight="bold" fill="#2563eb">≈ 硅的带隙电压 → 名字由来</text>
<text x="440" y="292" font-size="11.5" font-weight="bold" fill="#b45309">配比全部来自「两只管子 + 两个比值」</text>
<text x="440" y="310" font-size="11" fill="#475569">版图面积比 8 好做好准，电阻比可激光修调</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DR}s" begin="-0.6s" repeatCount="indefinite" path="M592,196 L700,196"/></circle>
<circle cx="591" cy="196" r="5" fill="none" stroke="#2563eb" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.8s" repeatCount="indefinite"/></circle>
<line x1="400" y1="336" x2="400" y2="484" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="30" y="360" font-size="12" font-weight="bold" fill="#334155">温漂：同一条温度轴上比</text>
<line x1="60" y1="470" x2="740" y2="470" stroke="#64748b" stroke-width="1.4"/>
<line x1="60" y1="380" x2="60" y2="470" stroke="#64748b" stroke-width="1.4"/>
<text x="52" y="490" text-anchor="end" font-size="10.5" fill="#475569">−40℃</text>
<text x="734" y="490" text-anchor="end" font-size="10.5" fill="#475569">+125℃</text>
<path d="M70,414 Q210,392 300,416 Q340,428 360,442" fill="none" stroke="#b45309" stroke-width="3"/>
<text x="150" y="404" font-size="11" font-weight="bold" fill="#b45309">齐纳：抛物线，5.6V 处才触底</text>
<path d="M70,430 L360,430" fill="none" stroke="#2563eb" stroke-width="3"/>
<text x="150" y="450" font-size="11" font-weight="bold" fill="#2563eb">带隙：修调后能压到 3ppm/℃</text>
<text x="60" y="508" font-size="12" font-weight="bold" fill="#334155">怎么选</text>
<text x="90" y="534" font-size="11.5" fill="#475569">粗基准、成本敏感、要高压 → 齐纳（5.6V 附近选型）</text>
<text x="90" y="556" font-size="11.5" fill="#475569">精密基准、ADC 参考 → 带隙（现代基准芯片清一色）</text>
{pulse(34, 74, 352, 244, '#b45309', 2.0, 10)}
'''
    svg += caption("① 齐纳：靠击穿电压，简单粗暴便宜——但 5.6V 之外温漂就上去了", "#b45309", DR,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=592)
    svg += caption("② 带隙：用一正一负两条温漂曲线相加，让它们互相抵消", "#2563eb", DR,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=592)
    svg += caption("③ 配比 K 不是魔数：它等于 2mV/℃ ÷ (0.085mV/℃ × ln8) ≈ 11.3", "#7c3aed", DR,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=592)
    svg += caption("④ 选型口诀：粗基准看齐纳、精密基准看带隙——温漂差两个数量级", "#059669", DR,
                   "0;0;1;1", "0;0.85;0.9;1", y=592)
    svg += note_box("带隙能赢不是因为「更复杂」，而是因为它把温漂做成了「两个比值之比」——IC 里比值天生好匹配", 644, DR,
                    "0;0.9;0.94;1", w=740)
    save('ref-showdown.svg', svg + '</svg>')

# ======================= 图 61：PN 结的形成（第 2 章 2.1） =======================
def make_pn_junction():
    DJ = 11
    svg = svg_open('PN 结：一堵会自己调节高度的「电荷墙」', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">扩散想散开，电场往回推——平衡点就是内建电势</text>
<rect x="60" y="80" width="230" height="120" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="175" y="106" text-anchor="middle" font-size="13" font-weight="bold" fill="#2563eb">P 型（空穴多）</text>
<text x="175" y="128" text-anchor="middle" font-size="11" fill="#475569">受主离子带负电（固定不动）</text>
<text x="175" y="150" text-anchor="middle" font-size="11" fill="#475569">空穴 +</text>
<rect x="300" y="80" width="230" height="120" rx="6" fill="#fef2f2" stroke="#dc2626" stroke-width="2"/>
<text x="415" y="106" text-anchor="middle" font-size="13" font-weight="bold" fill="#dc2626">N 型（电子多）</text>
<text x="415" y="128" text-anchor="middle" font-size="11" fill="#475569">施主离子带正电（固定不动）</text>
<text x="415" y="150" text-anchor="middle" font-size="11" fill="#475569">电子 −</text>
<rect x="270" y="80" width="50" height="120" fill="#f1f5f9" stroke="#64748b" stroke-width="1.5" stroke-dasharray="4,3"/>
<text x="295" y="72" text-anchor="middle" font-size="11" font-weight="bold" fill="#64748b">耗尽层</text>
<line x1="270" y1="130" x2="250" y2="130" stroke="#2563eb" stroke-width="2.5"/>
<line x1="320" y1="130" x2="340" y2="130" stroke="#dc2626" stroke-width="2.5"/>
<circle r="6" fill="#dc2626"><animateMotion dur="{DJ}s" repeatCount="indefinite" path="M410,150 L316,150 L306,150"/></circle>
<circle r="6" fill="#2563eb"><animateMotion dur="{DJ}s" begin="-0.8s" repeatCount="indefinite" path="M180,150 L274,150 L284,150"/></circle>
<circle r="6" fill="#dc2626"><animateMotion dur="{DJ}s" begin="-1.6s" repeatCount="indefinite" path="M300,150 L340,150"/></circle>
<line x1="295" y1="230" x2="295" y2="290" stroke="#7c3aed" stroke-width="2.5"/>
<path d="M288,278 L295,292 L302,278 Z" fill="#7c3aed"/>
<text x="306" y="246" font-size="11" font-weight="bold" fill="#7c3aed">内建电场 E</text>
<text x="306" y="266" font-size="11" fill="#475569">把电子往回推</text>
<line x1="60" y1="318" x2="740" y2="318" stroke="#cbd5e1" stroke-width="1"/>
<text x="60" y="348" font-size="12.5" font-weight="bold" fill="#334155">三步认识它</text>
<text x="60" y="376" font-size="11.5" fill="#475569">① <tspan font-weight="bold" fill="#dc2626">复合</tspan>：浓度差驱动扩散，交界处电子掉进空穴两两湮灭（同一滴墨水滴进清水的统计规律）</text>
<text x="60" y="402" font-size="11.5" fill="#475569">② <tspan font-weight="bold" fill="#7c3aed">建墙</tspan>：跑掉的载流子留下不能动的带电离子 → 电荷墙 → 电场把后续电子往回推</text>
<text x="60" y="428" font-size="11.5" fill="#475569">③ <tspan font-weight="bold" fill="#059669">平衡</tspan>：扩散多一分、墙厚一分、推力大一分 —— 最终恰好抵消，动态平衡</text>
<rect x="60" y="452" width="680" height="76" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.8"/>
<text x="76" y="478" font-size="12" font-weight="bold" fill="#b45309">正向导通不是「过了 0.7V 突然开」</text>
<text x="76" y="502" font-size="11.5" fill="#475569">外加正压把内建电势垫高抵消一部分 → 墙变薄 → 扩散重新启动 → 电流爆发式增长。</text>
<text x="76" y="520" font-size="11.5" fill="#475569">二极管是「外加电压与内建电势的拔河」，指数曲线就是拔河的比分牌（见 2.2）。</text>
{pulse(268, 78, 54, 124, '#7c3aed', 2.0, 8)}
<circle cx="295" cy="130" r="5" fill="none" stroke="#7c3aed" stroke-width="2.4">
<animate attributeName="r" values="5;13;5" dur="1.8s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① 浓度差驱动扩散：N 侧电子往 P 侧跑，P 侧空穴往 N 侧跑", "#dc2626", DJ,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=560)
    svg += caption("② 复合掉的地方留下不能动的离子 → 变成一堵「电荷墙」（耗尽层）", "#7c3aed", DJ,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=560)
    svg += caption("③ 墙越高推力越大：扩散多一分它就厚一分——直到势均力敌", "#2563eb", DJ,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=560)
    svg += caption("④ 二极管不是开关，是拔河：外加电压抵掉多少内建电势，电流就涨多少", "#b45309", DJ,
                   "0;0;1;1", "0;0.85;0.9;1", y=560)
    svg += note_box("Si 的内建电势约 0.7V——记住它是「平衡态的墙高」，不是「导通门槛」", 600, DJ,
                    "0;0.9;0.94;1", w=720)
    save('pn-junction.svg', svg + '</svg>')

# ======================= 图 62：MOSFET 输出特性（第 4 章 4.2） =======================
def make_mosfet_curves():
    DM = 11
    X0, X1, Y0, Y1 = 400, 764, 116, 400
    def px(vds):
        return X0 + vds/10.0*(X1-X0)
    def py(id_):
        return Y1 - id_/30.0*(Y1-Y0)
    VT, K = 2.0, 0.9
    def curve(vgs, color, wid=2.4):
        pts = []
        for vds in np.linspace(0, 10, 240):
            vov = vgs - VT
            if vov <= 0:
                i = 0.0
            elif vds < vov:
                i = K*(vov*vds - vds*vds/2)      # 线性区
            else:
                i = K*vov*vov/2                   # 饱和区（恒流）
            pts.append(f"{px(vds):.0f},{py(min(i,30)):.0f}")
        return '<path d="M' + " L".join(pts) + f'" fill="none" stroke="{color}" stroke-width="{wid}"/>'
    svg = svg_open('MOSFET 输出特性：「饱和」在这里恰恰是放大区', h=620)
    svg += f'''
<text x="200" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">一条曲线 = 一个 V_GS；夹断点连成虚线</text>
<text x="40" y="96" font-size="11.5" font-weight="bold" fill="#2563eb">线性区（V_DS &lt; V_GS−V_TH）</text>
<text x="52" y="116" font-size="11" fill="#475569">沟道没夹断，I_D 随 V_DS 近似线性</text>
<text x="52" y="134" font-size="11" fill="#475569">→ 管子 = 受 V_GS 控制的<tspan font-weight="bold" fill="#2563eb">可变电阻</tspan></text>
<text x="40" y="164" font-size="11.5" font-weight="bold" fill="#059669">饱和区（V_DS ≥ V_GS−V_TH）</text>
<text x="52" y="184" font-size="11" fill="#475569">漏端夹断，再加 V_DS 也不增流</text>
<text x="52" y="202" font-size="11" fill="#475569">→ 管子 = <tspan font-weight="bold" fill="#059669">恒流源</tspan>，放大就用这里</text>
<text x="40" y="232" font-size="11.5" font-weight="bold" fill="#dc2626">词同义反的坑</text>
<text x="52" y="252" font-size="11" fill="#475569">MOSFET 饱和 = 恒流源 = 放大区</text>
<text x="52" y="270" font-size="11" fill="#475569">BJT 饱和 = 开关闭合 = 最小压降</text>
<text x="52" y="292" font-size="11" font-weight="bold" fill="#b45309">记法：MOS 看沟道，BJT 看结</text>
{curve(3.0, '#94a3b8', 2.0)}
{curve(4.0, '#2563eb', 2.4)}
{curve(5.0, '#059669', 2.4)}
{curve(6.0, '#7c3aed', 2.4)}
<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="#64748b" stroke-width="1.6"/>
<text x="{X1}" y="{Y1+36}" text-anchor="end" font-size="11" fill="#475569">V_DS →</text>
<text x="{X0-6}" y="{Y0+12}" text-anchor="end" font-size="10.5" fill="#475569">30mA</text>
<text x="{X0-6}" y="{py(10)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">10mA</text>
<text x="{px(5):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">5V</text>
<text x="{px(10):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">10V</text>
<line x1="{px(2):.0f}" y1="{Y0}" x2="{px(2):.0f}" y2="{Y1}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="{px(2)+6:.0f}" y="{Y0+16}" font-size="10" fill="#94a3b8">V_TH=2V</text>
<path d="M{px(2):.0f},{py(1.8):.0f} L{px(4):.0f},{py(7.2):.0f} L{px(6):.0f},{py(16.2):.0f} L{px(8):.0f},{py(28.8):.0f}" fill="none" stroke="#dc2626" stroke-width="1.6" stroke-dasharray="5,4"/>
<circle r="5" fill="#059669">{plain_motion(DM, curve(5.0, '#059669'))}</circle>
<circle r="5" fill="#2563eb">{plain_motion(DM, curve(4.0, '#2563eb'), begin='-1.4s')}</circle>
<text x="{px(6.5):.0f}" y="{Y0+34}" font-size="10.5" font-weight="bold" fill="#dc2626">虚线上是夹断点：分界线</text>
<text x="{X0+8}" y="{Y0-42}" font-size="11" font-weight="bold" fill="#2563eb">V_GS 越大，曲线越往上抬</text>
<text x="{X0+8}" y="{Y0-24}" font-size="11" fill="#475569">抬升量 ∝ (V_GS−V_TH)² → 跨导 g_m</text>
<rect x="40" y="446" width="720" height="86" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"/>
<text x="60" y="474" font-size="12" font-weight="bold" fill="#334155">河流比喻：沟道 = 河床</text>
<text x="60" y="498" font-size="11.5" fill="#475569">V_DS 小：河水从源平缓流到漏，水流随坡度线性增加（线性区）</text>
<text x="60" y="520" font-size="11.5" fill="#475569">V_DS 够大：漏端河床被「夹断」，水到断口被强电场直接甩过去——水量只由上游（V_GS）决定</text>
<circle r="5" fill="#7c3aed">{plain_motion(DM, curve(6.0, '#7c3aed'), begin='-0.7s')}</circle>
<circle r="5" fill="#94a3b8">{plain_motion(DM, curve(3.0, '#94a3b8'), begin='-2.1s')}</circle>
<circle cx="{px(2):.0f}" cy="{py(1.8):.0f}" r="5" fill="none" stroke="#dc2626" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.8s" repeatCount="indefinite"/>
<animate attributeName="opacity" values="0.95;0.2;0.95" dur="1.8s" repeatCount="indefinite"/></circle>
<circle cx="{px(10):.0f}" cy="{py(30):.0f}" r="5" fill="none" stroke="#059669" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="2.2s" begin="-0.8s" repeatCount="indefinite"/></circle>
{pulse(276, 114, 30, 288, '#dc2626', 2.0, 8)}
'''
    svg += caption("① 线性区：沟道没夹断，I_D 跟 V_DS 走——管子就是个可变电阻（模拟开关用这里）", "#2563eb", DM,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=556)
    svg += caption("② 夹断点：V_DS = V_GS−V_TH 处开始「恒流」——虚线把两个区分开", "#dc2626", DM,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=556)
    svg += caption("③ 饱和区里 I_D 只听 V_GS：曲线越高 = V_GS 越大，这就是跨导 g_m", "#059669", DM,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=556)
    svg += caption("④ 别被「饱和」骗：MOS 的饱和 = 恒流源 = 放大区；BJT 的饱和 = 开关闭合", "#b45309", DM,
                   "0;0;1;1", "0;0.85;0.9;1", y=556)
    save('mosfet-curves.svg', svg + '</svg>')

# ======================= 图 63：555 三种模式（第 10 章 10.2） =======================
def make_555_modes():
    DN = 11
    svg = svg_open('555 的三种人格：无稳态、单稳态、双稳态', h=620)
    svg += '''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">同一颗芯，接法不同 → 人格完全不同；区别只在「往哪个脚接 RC」</text>
'''
    cards = [
        ('无稳态 Astable', '#2563eb', 'R1 + R2 + C 自由振荡', '自激，不需要触发', '时钟 / PWM / 蜂鸣器 / 闪光灯',
         'f ≈ 1.44 / ((R1+2R2)·C)', True),
        ('单稳态 Monostable', '#059669', 'TRIG 触发一次 → 定时脉冲', '按一下，亮一拍', '按键消抖 / 定时 / 看门狗',
         't ≈ 1.1·R·C', False),
        ('双稳态 Bistable', '#7c3aed', 'TRIG/THRES 当 S/R 用', '两个稳定态，靠触发翻转', '简易锁存开关',
         '状态保持，无需 RC', False),
    ]
    x = 30
    for name, col, mode, beh, use, formula, osc in cards:
        svg += f'<rect x="{x}" y="76" width="240" height="300" rx="10" fill="#f8fafc" stroke="{col}" stroke-width="1.8"/>'
        svg += f'<text x="{x+120}" y="104" text-anchor="middle" font-size="13.5" font-weight="bold" fill="{col}">{name}</text>'
        svg += f'<line x1="{x+14}" y1="118" x2="{x+226}" y2="118" stroke="#cbd5e1" stroke-width="1"/>'
        svg += f'<text x="{x+16}" y="144" font-size="11.5" fill="#475569">接法</text>'
        svg += f'<text x="{x+16}" y="164" font-size="11" font-weight="bold" fill="#334155">{mode}</text>'
        svg += f'<text x="{x+16}" y="196" font-size="11.5" fill="#475569">脾气</text>'
        svg += f'<text x="{x+16}" y="216" font-size="11" font-weight="bold" fill="{col}">{beh}</text>'
        svg += f'<text x="{x+16}" y="248" font-size="11.5" fill="#475569">用途</text>'
        svg += f'<text x="{x+16}" y="268" font-size="10.5" fill="#334155">{use}</text>'
        svg += f'<text x="{x+16}" y="300" font-size="11.5" fill="#475569">关键式</text>'
        svg += f'<text x="{x+16}" y="322" font-size="11" font-weight="bold" fill="#b45309">{formula}</text>'
        # 迷你波形
        if osc:
            pts = []
            for i in range(121):
                t = i/120
                v = 1 if (t % 0.5) < 0.34 else 0
                pts.append(f"{x+30+t*180:.0f},{352-v*22:.0f}")
            svg += '<path d="M' + " L".join(pts) + f'" fill="none" stroke="{col}" stroke-width="2.2"/>'
            svg += f'<text x="{x+120}" y="368" text-anchor="middle" font-size="9.5" fill="#64748b">连续方波（自由跑）</text>'
        else:
            base = 352
            svg += f'<line x1="{x+30}" y1="{base}" x2="{x+210}" y2="{base}" stroke="{col}" stroke-width="2.2"/>'
            svg += f'<line x1="{x+80}" y1="{base}" x2="{x+80}" y2="{base-22}" stroke="{col}" stroke-width="2.2"/>'
            svg += f'<line x1="{x+80}" y1="{base-22}" x2="{x+140}" y2="{base-22}" stroke="{col}" stroke-width="2.2"/>'
            svg += f'<line x1="{x+140}" y1="{base-22}" x2="{x+140}" y2="{base}" stroke="{col}" stroke-width="2.2"/>'
            svg += f'<line x1="{x+140}" y1="{base}" x2="{x+210}" y2="{base}" stroke="{col}" stroke-width="2.2"/>'
            svg += f'<text x="{x+120}" y="368" text-anchor="middle" font-size="9.5" fill="#64748b">触发一次 → 一个脉冲（或保持）</text>'
        x += 253
    svg += f'''
<line x1="30" y1="404" x2="770" y2="404" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="432" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">三个模式的「同一性」与「差异」</text>
<text x="400" y="456" text-anchor="middle" font-size="11.5" fill="#475569">同一颗芯：内部两个比较器（1/3、2/3 Vcc）+ 一个 SR 触发器 + 一只放电管</text>
<text x="400" y="478" text-anchor="middle" font-size="11.5" fill="#475569">差异只在：电容接哪个脚、阈值脚接不接 RC、触发脚是否被自由拉到阈值之间</text>
<text x="400" y="504" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">记住这一句：无稳态 = 自己踩自己；单稳态 = 别人踩一脚；双稳态 = 两个门轮流锁</text>
<circle r="6" fill="#2563eb"><animateMotion dur="{DN}s" repeatCount="indefinite" path="M60,330 L240,330" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="6" fill="#059669"><animateMotion dur="{DN}s" begin="-1.1s" repeatCount="indefinite" path="M312,368 L312,330 L392,330" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="6" fill="#7c3aed"><animateMotion dur="{DN}s" begin="-2.2s" repeatCount="indefinite" path="M565,330 L745,330" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DN}s" begin="-0.5s" repeatCount="indefinite" path="M70,196 L158,196"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DN}s" begin="-1.3s" repeatCount="indefinite" path="M322,196 L410,196"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DN}s" begin="-2.1s" repeatCount="indefinite" path="M574,196 L662,196"/></circle>
{pulse(38, 130, 224, 60, '#2563eb', 2.0, 8)}
{pulse(291, 130, 224, 60, '#059669', 2.0, 8)}
{pulse(544, 130, 224, 60, '#7c3aed', 2.0, 8)}
'''
    svg += caption("① 无稳态：电容自己充放，输出永远在翻——不需要外部触发（时钟最爱）", "#2563eb", DN,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=552)
    svg += caption("② 单稳态：平时静默，TRIG 来一脚就输出一个 t≈1.1RC 的脉冲", "#059669", DN,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=552)
    svg += caption("③ 双稳态：TRIG/THRES 当置位/复位用，两个稳态之间来回锁", "#7c3aed", DN,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=552)
    svg += caption("④ 三种模式的差异只在「电容接哪只脚」——同一颗芯，三副面孔", "#b45309", DN,
                   "0;0;1;1", "0;0.85;0.9;1", y=552)
    save('555-modes.svg', svg + '</svg>')

# ======================= 图 64：负反馈四种拓扑（第 12 章 12.7） =======================
def make_feedback_topo():
    DF = 11
    def cell(x, y, sample, mix, locks, sid, zin, zout, col):
        p = f'<rect x="{x}" y="{y}" width="164" height="150" rx="9" fill="#f8fafc" stroke="{col}" stroke-width="1.8"/>'
        p += f'<text x="{x+82}" y="{y+26}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="{col}">采样{sample} · {mix}混合</text>'
        p += f'<line x1="{x+12}" y1="{y+38}" x2="{x+152}" y2="{y+38}" stroke="#cbd5e1" stroke-width="1"/>'
        p += f'<text x="{x+12}" y="{y+60}" font-size="10.5" fill="#475569">钉死的量</text>'
        p += f'<text x="{x+82}" y="{y+82}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="{col}">{locks}</text>'
        p += f'<text x="{x+12}" y="{y+104}" font-size="10.5" fill="#475569">等效身份</text>'
        p += f'<text x="{x+152}" y="{y+104}" text-anchor="end" font-size="10.5" font-weight="bold" fill="#334155">{sid}</text>'
        p += f'<text x="{x+12}" y="{y+124}" font-size="10.5" fill="#475569">输入阻抗</text>'
        p += f'<text x="{x+152}" y="{y+124}" text-anchor="end" font-size="10.5" font-weight="bold" fill="{col}">{zin}</text>'
        p += f'<text x="{x+12}" y="{y+142}" font-size="10.5" fill="#475569">输出阻抗</text>'
        p += f'<text x="{x+152}" y="{y+142}" text-anchor="end" font-size="10.5" font-weight="bold" fill="{col}">{zout}</text>'
        return p
    svg = svg_open('负反馈四种拓扑：稳定什么，就采样什么', h=620)
    svg += f'''
<text x="400" y="60" text-anchor="middle" font-size="11" fill="#64748b">反馈网络只干两件事：采样一个量、混合回输入 → 2×2 = 四种拓扑</text>
{cell(30, 86, '电压', '串联', '电压增益 A_v', '压控压源', '↑', '↓', '#2563eb')}
{cell(213, 86, '电压', '并联', '跨阻 V_out/I_in', '流控压源', '↓', '↓', '#059669')}
{cell(396, 86, '电流', '串联', '跨导 I_out/V_in', '压控流源', '↑', '↑', '#7c3aed')}
{cell(579, 86, '电流', '并联', '电流增益 A_i', '流控流源', '↓', '↑', '#b45309')}
<line x1="30" y1="258" x2="770" y2="258" stroke="#cbd5e1" stroke-width="1"/>
<text x="40" y="288" font-size="12.5" font-weight="bold" fill="#334155">判读口诀</text>
<text x="40" y="314" font-size="11.5" fill="#475569">想稳<tspan font-weight="bold" fill="#059669">电压</tspan> → 采样电压（输出阻抗跟着<tspan font-weight="bold">降</tspan>）　·　想稳<tspan font-weight="bold" fill="#dc2626">电流</tspan> → 采样电流（输出阻抗跟着<tspan font-weight="bold">升</tspan>）</text>
<text x="40" y="338" font-size="11.5" fill="#475569">想保<tspan font-weight="bold" fill="#2563eb">输入阻抗</tspan> → 串联混合　·　想泄放输入电流 → 并联混合</text>
<rect x="40" y="362" width="720" height="88" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.6"/>
<text x="58" y="388" font-size="12" font-weight="bold" fill="#2563eb">已经见过的一个例子：发射极电阻 Re（3.5 节）</text>
<text x="58" y="412" font-size="11.5" fill="#475569">它从输出回路<tspan font-weight="bold">串联采样电流</tspan>、再<tspan font-weight="bold">串联混合</tspan>回输入 → 属于「电流串联」</text>
<text x="58" y="436" font-size="11.5" fill="#475569">所以它钉死的是 I_C、把输出阻抗抬高了——这正是恒流源想要的性质</text>
<line x1="40" y1="474" x2="760" y2="474" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="502" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309">反馈什么时候翻脸成振荡？</text>
<text x="400" y="526" text-anchor="middle" font-size="11.5" fill="#475569">内部极点每级贡献最多 −90° 相移；攒够 −180° 时负反馈原地转正反馈</text>
<text x="400" y="548" text-anchor="middle" font-size="11.5" fill="#475569">此时若 |Aβ| ≥ 1 → 自激振荡；|Aβ| &lt; 1 → 只是振铃。相位裕度底线 45°，舒适 60°</text>
<text x="400" y="576" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">救法：密勒补偿造一个足够低的主极点，让增益在危险相移攒够前先滚到 1 以下</text>
{pulse(38, 118, 148, 60, '#2563eb', 2.0, 8)}
{pulse(221, 118, 148, 60, '#059669', 2.0, 8)}
{pulse(404, 118, 148, 60, '#7c3aed', 2.0, 8)}
{pulse(587, 118, 148, 60, '#b45309', 2.0, 8)}
<circle r="5" fill="#2563eb"><animateMotion dur="{DF}s" repeatCount="indefinite" path="M60,246 L196,246" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#b45309"><animateMotion dur="{DF}s" begin="-1.6s" repeatCount="indefinite" path="M610,246 L742,246" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DF}s" begin="-0.8s" repeatCount="indefinite" path="M243,246 L379,246"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DF}s" begin="-0.8s" repeatCount="indefinite" path="M426,246 L562,246"/></circle>
<circle cx="112" cy="168" r="5" fill="none" stroke="#2563eb" stroke-width="2.2"><animate attributeName="r" values="5;13;5" dur="2.2s" repeatCount="indefinite"/></circle>
<circle cx="295" cy="168" r="5" fill="none" stroke="#059669" stroke-width="2.2"><animate attributeName="r" values="5;13;5" dur="2.2s" begin="-1.1s" repeatCount="indefinite"/></circle>
<circle cx="478" cy="168" r="5" fill="none" stroke="#7c3aed" stroke-width="2.2"><animate attributeName="r" values="5;13;5" dur="2.2s" begin="-0.55s" repeatCount="indefinite"/></circle>
<circle cx="661" cy="168" r="5" fill="none" stroke="#b45309" stroke-width="2.2"><animate attributeName="r" values="5;13;5" dur="2.2s" begin="-1.65s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① 采样决定「稳什么」：采样电压稳电压、采样电流稳电流", "#2563eb", DF,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=606)
    svg += caption("② 混合决定「阻抗往哪走」：串联升输入阻抗、并联降输入阻抗", "#059669", DF,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=606)
    svg += caption("③ 四种拓扑各有身份：压控压源 / 流控压源 / 压控流源 / 流控流源", "#7c3aed", DF,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=606)
    svg += caption("④ 别忘后半段：相移攒够 180° 且 |Aβ|≥1，负反馈就变振荡器", "#b45309", DF,
                   "0;0;1;1", "0;0.85;0.9;1", y=606)
    save('feedback-topo.svg', svg + '</svg>')

# ======================= 图 65：真实电阻的等效模型（第 1 章 1.1） =======================
def make_resistor_model():
    DR = 11
    R, L, C = 1000.0, 10e-9, 0.2e-12
    f1 = 1/(2*np.pi*R*C)                # 体电容开始分流（R‖C 极点）
    f2 = R/(2*np.pi*L)                  # 引线电感与 R 等量级
    fsrf = 1/(2*np.pi*np.sqrt(L*C))     # L、C 谐振：|Z| 谷底

    def zmag(f):
        w = 2*np.pi*f
        zc = 1/(1j*w*C)
        zp = R*zc/(R+zc)                # R ∥ C（体电容跨在电阻两端）
        return abs(1j*w*L + zp)         # 再串引线电感 L

    X0, X1, Y0, Y1 = 400, 764, 120, 396
    def px(f):
        return X0 + (np.log10(f)-3)/8.0*(X1-X0)               # 1kHz .. 100GHz
    def py(z):
        return Y0 + (np.log10(2e4)-np.log10(max(z, 10)))/np.log10(2e3)*(Y1-Y0)
    real_d = "M" + " L".join(f"{px(f):.0f},{py(zmag(f)):.0f}" for f in np.logspace(3, 11, 320))
    svg = svg_open('真实电阻：高频时它不再是「一个电阻」', h=648)
    svg += f'''
<text x="205" y="50" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">等效模型：R 并 C（体电容），再串 L（引线电感）</text>
<text x="60" y="96" font-size="11.5" fill="#475569">理想 R</text>
<line x1="112" y1="92" x2="150" y2="92" stroke="#334155" stroke-width="2.5"/>
<circle cx="150" cy="92" r="3" fill="#334155"/>
<line x1="150" y1="92" x2="170" y2="92" stroke="#334155" stroke-width="2.5"/>
<rect x="170" y="80" width="60" height="24" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="200" y="97" text-anchor="middle" font-size="11" fill="#475569">1kΩ</text>
<line x1="230" y1="92" x2="250" y2="92" stroke="#334155" stroke-width="2.5"/>
<circle cx="250" cy="92" r="3" fill="#334155"/>
<line x1="150" y1="95" x2="150" y2="122" stroke="#334155" stroke-width="2"/>
<line x1="150" y1="122" x2="191" y2="122" stroke="#334155" stroke-width="2"/>
<line x1="191" y1="112" x2="191" y2="132" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="205" y1="112" x2="205" y2="132" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="205" y1="122" x2="250" y2="122" stroke="#334155" stroke-width="2"/>
<line x1="250" y1="122" x2="250" y2="95" stroke="#334155" stroke-width="2"/>
<text x="216" y="140" font-size="11" font-weight="bold" fill="#7c3aed">C 0.2pF</text>
<line x1="250" y1="92" x2="278" y2="92" stroke="#334155" stroke-width="2.5"/>
<path d="M278,92 q8,12 16,0 q8,-12 16,0 q8,12 16,0" fill="none" stroke="#dc2626" stroke-width="2.5"/>
<text x="308" y="76" font-size="11" font-weight="bold" fill="#dc2626">L 10nH</text>
<line x1="326" y1="92" x2="358" y2="92" stroke="#334155" stroke-width="2.5"/>
<text x="60" y="212" font-size="11.5" font-weight="bold" fill="#7c3aed">体电容先分流（f₁）</text>
<text x="60" y="234" font-size="11" fill="#475569">f₁ = 1/(2πRC) = 0.8GHz —— 这是</text>
<text x="60" y="252" font-size="11" fill="#475569">「1kΩ 电阻拿来做高频负载」的真实上限</text>
<text x="60" y="282" font-size="11.5" font-weight="bold" fill="#dc2626">引线电感接管（f₂）</text>
<text x="60" y="304" font-size="11" fill="#475569">f₂ = R/(2πL) = 15.9GHz —— 到那之后</text>
<text x="60" y="322" font-size="11" fill="#475569">感抗盖过电阻，元件重新「变回电感」</text>
<text x="60" y="352" font-size="11.5" font-weight="bold" fill="#b45309">选型结论</text>
<text x="60" y="374" font-size="11" fill="#475569">高频用贴片（引线≈0），且元件值本身</text>
<text x="60" y="392" font-size="11" fill="#475569">要按频率特性曲线复核</text>
<text x="{X0-6}" y="{py(1000)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">1kΩ</text>
<text x="{X0-6}" y="{py(100)+4:.0f}" text-anchor="end" font-size="10.5" fill="#475569">100Ω</text>
<text x="{px(1e3):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">1kHz</text>
<text x="{px(1e6):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">1MHz</text>
<text x="{px(1e9):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">1GHz</text>
<text x="{px(1e11):.0f}" y="{Y1+22}" text-anchor="middle" font-size="10" fill="#475569">100GHz</text>
<text x="{X1}" y="{Y1+40}" text-anchor="end" font-size="11" fill="#475569">频率 →</text>
<line x1="{X0}" y1="{py(1000):.0f}" x2="{X1}" y2="{py(1000):.0f}" stroke="#94a3b8" stroke-width="2" stroke-dasharray="6,4"/>
<text x="{X0+6}" y="{py(1000)-8:.0f}" font-size="10.5" fill="#94a3b8">理想 1kΩ：一条直线</text>
<path d="{real_d}" fill="none" stroke="#2563eb" stroke-width="3"/>
<circle cx="{px(f1):.0f}" cy="{py(zmag(f1)):.0f}" r="5.5" fill="#7c3aed"/>
<text x="{px(f1):.0f}" y="{py(zmag(f1))-26:.0f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#7c3aed">f₁=0.8GHz 起下坠</text>
<circle cx="{px(fsrf):.0f}" cy="{py(zmag(fsrf)):.0f}" r="5.5" fill="#059669"/>
<text x="{px(fsrf):.0f}" y="{py(zmag(fsrf))+22:.0f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">谷底 {zmag(fsrf):.0f}Ω @3.6GHz（LC 谐振把 R 短路）</text>
<circle cx="{px(f2):.0f}" cy="{py(zmag(f2)):.0f}" r="5.5" fill="#dc2626"/>
<text x="{px(f2):.0f}" y="{py(zmag(f2))-26:.0f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">f₂=15.9GHz：L 接管</text>
<circle r="5" fill="#2563eb">{plain_motion(DR, real_d)}</circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DR}s" begin="-0.4s" repeatCount="indefinite" path="M114,92 L168,92"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DR}s" begin="-1.1s" repeatCount="indefinite" path="M252,92 L276,92"/></circle>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DR}s" begin="-1.8s" repeatCount="indefinite" path="M150,124 L191,124"/></circle>
<circle cx="{px(f1):.0f}" cy="{py(zmag(f1)):.0f}" r="5" fill="none" stroke="#7c3aed" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.9s" repeatCount="indefinite"/></circle>
<circle cx="{px(f2):.0f}" cy="{py(zmag(f2)):.0f}" r="5" fill="none" stroke="#dc2626" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.9s" begin="-0.9s" repeatCount="indefinite"/></circle>
{pulse(60, 60, 300, 124, '#94a3b8', 2.0, 10)}
'''
    svg += caption("① 低频：R 说了算——远低于 f₁ 时，蓝线与理想 1kΩ 几乎重合", "#94a3b8", DR,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=560)
    svg += caption("② 中频：体电容 0.2pF 开始分流，阻抗按约 −20dB/dec 下坠", "#7c3aed", DR,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=560)
    svg += caption(f"③ 谷底：3.6GHz 处只剩 {zmag(fsrf):.0f}Ω——L 与 C 谐振，把 R 整个短路掉", "#059669", DR,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=560)
    svg += caption(f"④ 再往上：引线电感接管，阻抗重新爬升到 {zmag(1e11):.0f}Ω@100GHz——元件又「变回电感」", "#dc2626", DR,
                   "0;0;1;1", "0;0.85;0.9;1", y=560)
    svg += note_box("每个元件都有两个寄生夺权点：C 在 f₁=1/(2πRC) 开始、L 在 f₂=R/(2πL) 结束——中间才是它「当电阻」的区间", 600, DR,
                    "0;0.9;0.94;1", w=760)
    save('resistor-model.svg', svg + '</svg>')

# ======================= 图 66：特殊二极管家族（第 2 章 2.4） =======================
def make_diode_family():
    DD = 11
    svg = svg_open('特殊二极管家族：一族五口，各管一段活', h=620)
    svg += '''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">横轴：特征电压（V_F 或反向工作电压）　纵轴：速度　—— 每颗管子占的位置就说明了它的岗位</text>
'''
    fam = [
        ('普通硅管（基准）', 0.7, 1.0, '#475569', '整流/钳位（慢）', 700),
        ('肖特基', 0.3, 9.0, '#2563eb', '高频整流 / 防反接', 200),
        ('LED', 2.4, 0.7, '#dc2626', '发光（必须限流）', 120),
        ('TVS', 6.0, 8.5, '#7c3aed', 'ESD/浪涌 ns 级钳位', 60),
        ('稳压管', 5.6, 1.6, '#b45309', '简易基准 / 过压钳位', 700),
        ('变容管', 4.0, 3.0, '#059669', 'VCO 调谐（结电容可变）', 100),
    ]
    X0, Y0 = 90, 100
    PW, PH = 640, 300
    def px(v): return X0 + v/7.0*PW
    def py(s): return Y0 + PH - s/10.0*PH
    svg += f'<line x1="{X0}" y1="{Y0+PH}" x2="{X0+PW}" y2="{Y0+PH}" stroke="#64748b" stroke-width="1.6"/>'
    svg += f'<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y0+PH}" stroke="#64748b" stroke-width="1.6"/>'
    svg += f'<text x="{X0+PW}" y="{Y0+PH+46}" text-anchor="end" font-size="11" fill="#475569">特征电压 →</text>'
    svg += f'<text x="{X0-8}" y="{Y0+14}" text-anchor="end" font-size="11" fill="#475569">快</text>'
    svg += f'<text x="{X0-8}" y="{Y0+PH}" text-anchor="end" font-size="11" fill="#475569">慢</text>'
    for v in (1, 3, 5, 7):
        svg += f'<line x1="{px(v):.0f}" y1="{Y0+PH}" x2="{px(v):.0f}" y2="{Y0+PH+5}" stroke="#64748b" stroke-width="1.2"/>'
        svg += f'<text x="{px(v):.0f}" y="{Y0+PH+16}" text-anchor="middle" font-size="10" fill="#475569">{v}V</text>'
    for nm, vf, sp, col, use, w in fam:
        cx, cy = px(vf), py(sp)
        svg += f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="9" fill="{col}" opacity="0.85"/>'
        dx = 76 if cx < 190 else 0
        svg += f'<text x="{cx+dx:.0f}" y="{cy-14:.0f}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="{col}">{nm}</text>'
        svg += f'<text x="{cx+dx:.0f}" y="{cy+28:.0f}" text-anchor="middle" font-size="10" fill="#475569">{use}</text>'
    svg += f'''
<text x="400" y="456" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">五个成员 + 一个基准（普通硅管），五条「不能忘」的规矩</text>
<text x="70" y="468" font-size="11.5" fill="#475569">① <tspan font-weight="bold" fill="#dc2626">LED 必须限流</tspan>：它是二极管，正向压降一旦建立，电流就指数暴涨——串电阻或上恒流</text>
<text x="70" y="492" font-size="11.5" fill="#475569">② <tspan font-weight="bold" fill="#2563eb">肖特基快是因为「没有少子存储」</tspan>：金属-半导体结，反向恢复时间几乎为零</text>
<text x="70" y="516" font-size="11.5" fill="#475569">③ <tspan font-weight="bold" fill="#7c3aed">TVS 拼的是「面积」</tspan>：大面积结承受浪涌能量，ns 级把电压钳住，接在接口最前线</text>
<text x="70" y="540" font-size="11.5" fill="#475569">④ <tspan font-weight="bold" fill="#b45309">稳压管工作在击穿区</tspan>：这是唯一「故意让它击穿」的用法，5.6V 附近温漂最小</text>
<text x="70" y="564" font-size="11.5" fill="#475569">⑤ <tspan font-weight="bold" fill="#059669">变容管是「电压控电容」</tspan>：反压越大耗尽层越宽、结电容越小——VCO 靠它调频</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DD}s" begin="-0.5s" repeatCount="indefinite" path="M{px(0.2):.0f},{Y0+PH-6} L{px(2.0):.0f},{Y0+PH-6}"/></circle>
<circle r="4.5" fill="#f59e0b" opacity="0.55"><animateMotion dur="{DD}s" begin="-{DD/2+0.5:.1f}s" repeatCount="indefinite" path="M{px(0.2):.0f},{Y0+PH-6} L{px(2.0):.0f},{Y0+PH-6}"/></circle>
<circle cx="{px(fam[0][1]):.0f}" cy="{py(fam[0][2]):.0f}" r="5" fill="none" stroke="#475569" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" repeatCount="indefinite"/></circle>
<circle cx="{px(fam[1][1]):.0f}" cy="{py(fam[1][2]):.0f}" r="5" fill="none" stroke="#2563eb" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" begin="-0.7s" repeatCount="indefinite"/></circle>
<circle cx="{px(fam[5][1]):.0f}" cy="{py(fam[5][2]):.0f}" r="5" fill="none" stroke="#059669" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" begin="-1.4s" repeatCount="indefinite"/></circle>
{pulse(270, 108, 120, 120, '#2563eb', 2.0, 10)}
{pulse(196, 300, 130, 60, '#dc2626', 2.0, 10)}
<circle cx="{px(fam[3][1]):.0f}" cy="{py(fam[3][2]):.0f}" r="5" fill="none" stroke="#7c3aed" stroke-width="2.4">
<animate attributeName="r" values="5;12;5" dur="1.9s" repeatCount="indefinite"/></circle>
<circle cx="{px(fam[2][1]):.0f}" cy="{py(fam[2][2]):.0f}" r="5" fill="none" stroke="#dc2626" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="1.9s" begin="-0.6s" repeatCount="indefinite"/></circle>
<circle cx="{px(fam[4][1]):.0f}" cy="{py(fam[4][2]):.0f}" r="5" fill="none" stroke="#b45309" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="1.9s" begin="-1.3s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① 肖特基：0.3V 又最快——高频整流与防反接首选（但耐压低）", "#2563eb", DD,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=596)
    svg += caption("② LED：压降大、速度慢，但它是唯一「把电变成光」的那颗", "#dc2626", DD,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=596)
    svg += caption("③ TVS：速度最快的那位，专门守在接口门口替芯片挨打", "#7c3aed", DD,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=596)
    svg += caption("④ 选型看两件事：要它「快」还是「省压降」——位置越靠前线越看速度", "#b45309", DD,
                   "0;0;1;1", "0;0.85;0.9;1", y=596)
    save('diode-family.svg', svg + '</svg>')

# ======================= 图 67：上拉电阻取值（第 5 章 5.3） =======================
def make_pullup_sizing():
    DP = 11
    C = 100e-12
    def tr(R): return 0.8473*R*C
    svg = svg_open('上拉电阻取值：太大翻不动，太小白费电', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">总线的上拉：上升沿是 RC，低电平是电流</text>
<line x1="70" y1="96" x2="70" y2="136" stroke="#334155" stroke-width="2.5"/>
<text x="56" y="90" font-size="11.5" font-weight="bold" fill="#b45309">3.3V</text>
<rect x="58" y="136" width="24" height="34" rx="3" fill="#fffbeb" stroke="#b45309" stroke-width="2"/>
<text x="92" y="158" font-size="11.5" font-weight="bold" fill="#b45309">R_p 上拉</text>
<line x1="70" y1="170" x2="70" y2="200" stroke="#334155" stroke-width="2.5"/>
<line x1="70" y1="200" x2="330" y2="200" stroke="#334155" stroke-width="2.5"/>
<rect x="110" y="236" width="96" height="52" rx="6" fill="#f8fafc" stroke="#2563eb" stroke-width="2.5"/>
<text x="158" y="258" text-anchor="middle" font-size="12" font-weight="bold" fill="#2563eb">驱动器</text>
<text x="158" y="278" text-anchor="middle" font-size="10.5" fill="#475569">拉低时吸流</text>
<line x1="158" y1="236" x2="158" y2="200" stroke="#2563eb" stroke-width="2.5"/>
<line x1="158" y1="288" x2="158" y2="312" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(158, 326)}
<circle cx="250" cy="200" r="4.5" fill="#334155"/>
<line x1="250" y1="200" x2="250" y2="160" stroke="#334155" stroke-width="2.5"/>
<line x1="236" y1="160" x2="264" y2="160" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="236" y1="172" x2="264" y2="172" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="250" y1="172" x2="250" y2="140" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(250, 140)}
<text x="268" y="156" font-size="10.5" fill="#7c3aed">总线电容</text>
<text x="268" y="172" font-size="11" font-weight="bold" fill="#7c3aed">C ≈ 100pF</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DP}s" begin="-0.3s" repeatCount="indefinite" path="M160,234 L160,202"/></circle>
<circle r="5" fill="#b45309"><animateMotion dur="{DP}s" begin="-0.9s" repeatCount="indefinite" path="M70,172 L70,198 L246,200"/></circle>
<circle r="3.6" fill="#7c3aed"><animateMotion dur="2.6s" begin="-0.4s" repeatCount="indefinite" path="M196,268 L118,268"/></circle>
<circle r="3.6" fill="#7c3aed"><animateMotion dur="2.6s" begin="-1.7s" repeatCount="indefinite" path="M118,268 L196,268"/></circle>
<text x="360" y="96" font-size="12.5" font-weight="bold" fill="#334155">两条硬约束</text>
<text x="360" y="122" font-size="11.5" font-weight="bold" fill="#2563eb">① 上升沿：t_r ≈ 0.8473·R_p·C</text>
<text x="374" y="142" font-size="11" fill="#475569">R_p 越大，充得越慢 → 限制最高速率</text>
<text x="360" y="172" font-size="11.5" font-weight="bold" fill="#dc2626">② 低电平：I_low = V/R_p 必须灌得动</text>
<text x="374" y="192" font-size="11" fill="#475569">R_p 越小，驱动器吸的电流越大</text>
<text x="360" y="222" font-size="11.5" font-weight="bold" fill="#b45309">③ 空闲功耗：线为低时 R_p 一直在耗</text>
<text x="374" y="242" font-size="11" fill="#475569">低功耗系统宁可取大（10k~100k）</text>
<rect x="360" y="266" width="400" height="150" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"/>
<text x="376" y="292" font-size="12" font-weight="bold" fill="#334155">算一笔（3.3V / C=100pF）</text>
<text x="376" y="316" font-size="11.5" fill="#475569">R_p = 1kΩ → t_r ≈ 85ns，I_low = 3.3mA（太快但费电）</text>
<text x="376" y="338" font-size="11.5" font-weight="bold" fill="#059669">R_p = 4.7kΩ → t_r ≈ 400ns，I_low = 0.70mA ← 经典值</text>
<text x="376" y="360" font-size="11.5" fill="#475569">R_p = 10kΩ → t_r ≈ 847ns，I_low = 0.33mA（标准模式够用）</text>
<text x="376" y="382" font-size="11.5" fill="#dc2626">R_p = 47kΩ → t_r ≈ 4µs，I_low = 70µA（快速模式直接不合格）</text>
<text x="376" y="406" font-size="11" fill="#475569">I²C 标准模式（100kHz）要求 t_r &lt; 1000ns → R_p ≤ 11.8kΩ</text>
<line x1="40" y1="440" x2="760" y2="440" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="468" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309">为什么教科书都说 4.7k</text>
<text x="400" y="492" text-anchor="middle" font-size="11.5" fill="#475569">它是「够快（标准模式 400ns 有余量）+ 够省（0.7mA）」的折中点；</text>
<text x="400" y="514" text-anchor="middle" font-size="11.5" fill="#475569">快速模式 400kHz 需要 ≤3.5kΩ，所以实板常见 2.2k；而 MCU 内部 30~50kΩ 弱上拉只够防浮空，不能当 I²C 上拉</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.7s" repeatCount="indefinite" path="M60,200 L156,200"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DP}s" begin="-1.5s" repeatCount="indefinite" path="M252,202 L326,200"/></circle>
<circle cx="360" cy="322" r="5" fill="none" stroke="#059669" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="1.8s" repeatCount="indefinite"/></circle>
<circle cx="376" cy="360" r="4" fill="#dc2626"><animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/></circle>
{pulse(356, 264, 408, 156, '#059669', 2.0, 10)}
'''
    svg += caption("① 上拉太大：RC 充得慢，上升沿被拉长——高速总线的第一个瓶颈", "#b45309", DP,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=552)
    svg += caption("② 上拉太小：驱动器拉低时要吸大电流，还可能顶不住低电平门限", "#dc2626", DP,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=552)
    svg += caption("③ 算笔账：t_r≈0.8473·R·C；3.3V/100pF 下 4.7k 给 400ns、0.7mA", "#059669", DP,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=552)
    svg += caption("④ 结论：4.7k 是标准模式折中值，快速模式要 2.2k，内部弱上拉只防浮空", "#2563eb", DP,
                   "0;0;1;1", "0;0.85;0.9;1", y=552)
    save('pullup-sizing.svg', svg + '</svg>')

# ======================= 图 68：LM358 双运放（第 6 章 6.2） =======================
def make_lm358_dual():
    DL = 11
    svg = svg_open('LM358：单电源双运放，脾气全写在输入级和输出级上', h=620)
    svg += f'''
<text x="210" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">一只封装里两只运放</text>
<rect x="60" y="76" width="120" height="180" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="120" y="104" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">LM358</text>
<text x="120" y="126" text-anchor="middle" font-size="10.5" fill="#475569">DIP-8 / SOIC-8</text>
<line x1="60" y1="140" x2="180" y2="140" stroke="#cbd5e1" stroke-width="1"/>
<text x="76" y="164" font-size="11" font-weight="bold" fill="#2563eb">OUT1</text>
<text x="164" y="164" text-anchor="end" font-size="11" font-weight="bold" fill="#2563eb">V+</text>
<text x="76" y="188" font-size="11" font-weight="bold" fill="#dc2626">IN1−</text>
<text x="164" y="188" text-anchor="end" font-size="11" font-weight="bold" fill="#dc2626">OUT2</text>
<text x="76" y="212" font-size="11" font-weight="bold" fill="#dc2626">IN1+</text>
<text x="164" y="212" text-anchor="end" font-size="11" font-weight="bold" fill="#dc2626">IN2−</text>
<text x="76" y="236" font-size="11" font-weight="bold" fill="#334155">GND</text>
<text x="164" y="236" text-anchor="end" font-size="11" font-weight="bold" fill="#334155">IN2+</text>
<text x="210" y="196" font-size="11" fill="#475569">1 脚对着 1 脚看：</text>
<text x="210" y="216" font-size="11" fill="#475569">一个封装两只独立运放</text>
<text x="210" y="236" font-size="11" font-weight="bold" fill="#b45309">省一半板面积与成本</text>
<polygon points="332,110 332,190 400,150" fill="#f8fafc" stroke="#2563eb" stroke-width="2.5"/>
<text x="340" y="132" font-size="12" font-weight="bold" fill="#059669">+</text>
<text x="340" y="176" font-size="12" font-weight="bold" fill="#dc2626">−</text>
<text x="366" y="156" text-anchor="middle" font-size="11" font-weight="bold" fill="#2563eb">PNP</text>
<text x="366" y="174" text-anchor="middle" font-size="10" fill="#475569">输入级</text>
<text x="416" y="118" font-size="11.5" font-weight="bold" fill="#059669">输入级用 PNP</text>
<text x="416" y="138" font-size="11" fill="#475569">经典 LM358：0 ~ Vcc−1.5V（25℃）</text>
<text x="416" y="158" font-size="11" font-weight="bold" fill="#b45309">→ 全温范围还要核对共模上限</text>
<text x="416" y="182" font-size="11.5" font-weight="bold" fill="#dc2626">输出非轨到轨</text>
<text x="416" y="202" font-size="11" fill="#475569">正轨余量取决于负载、电源与温度</text>
<text x="416" y="222" font-size="11" font-weight="bold" fill="#7c3aed">→ 想「摆到轨」要换轨到轨型号</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DL}s" begin="-0.3s" repeatCount="indefinite" path="M182,164 L330,150"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DL}s" begin="-1.1s" repeatCount="indefinite" path="M330,170 L182,188"/></circle>
<rect x="60" y="290" width="700" height="86" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.6"/>
<text x="76" y="316" font-size="12" font-weight="bold" fill="#2563eb">输出摆幅：能到哪、不能到哪</text>
<line x1="96" y1="356" x2="700" y2="356" stroke="#64748b" stroke-width="2"/>
<line x1="96" y1="336" x2="700" y2="336" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"/>
<text x="96" y="332" font-size="10.5" fill="#94a3b8">Vcc = 5V（轨）</text>
<line x1="96" y1="376" x2="700" y2="376" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"/>
<text x="700" y="372" text-anchor="end" font-size="10.5" fill="#94a3b8">GND（轨）</text>
<line x1="96" y1="348" x2="700" y2="348" stroke="#dc2626" stroke-width="2.5"/>
<text x="104" y="344" font-size="10.5" font-weight="bold" fill="#dc2626">3.5V 为摆幅示意；不是所有负载和温度下的保证值</text>
<text x="400" y="404" text-anchor="middle" font-size="11" fill="#475569">先分别核对输入共模范围与输出摆幅，再判断信号是否会失真或削顶</text>
<line x1="40" y1="428" x2="760" y2="428" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="456" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">与 741 的三处关键差异</text>
<text x="90" y="486" font-size="11.5" fill="#475569">① <tspan font-weight="bold" fill="#059669">单电源能用</tspan>：PNP 输入级，共模含地——5V 系统不用再造负电源</text>
<text x="90" y="510" font-size="11.5" fill="#475569">② <tspan font-weight="bold" fill="#dc2626">输出非轨到轨</tspan>：按实际负载查规格，不统一扣 1.5V</text>
<text x="90" y="534" font-size="11.5" fill="#475569">③ <tspan font-weight="bold" fill="#b45309">速度看型号</tspan>：TI 经典 LM358 典型 GBW 0.7MHz、SR 0.3V/µs</text>
<circle r="4.5" fill="#059669"><animateMotion dur="{DL}s" begin="-0.5s" repeatCount="indefinite" path="M76,164 L158,164"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DL}s" begin="-1.2s" repeatCount="indefinite" path="M76,188 L160,180"/></circle>
<circle r="4.5" fill="#2563eb"><animateMotion dur="{DL}s" begin="-1.9s" repeatCount="indefinite" path="M96,356 L696,356"/></circle>
<circle cx="700" cy="348" r="5" fill="none" stroke="#dc2626" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" repeatCount="indefinite"/></circle>
<circle cx="96" cy="336" r="5" fill="none" stroke="#94a3b8" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" begin="-1.0s" repeatCount="indefinite"/></circle>
{pulse(328, 108, 78, 88, '#2563eb', 2.0, 10)}
'''
    svg += caption("① 单封装双运放：一个封装两只独立运放，省面积省成本（板子上最常见的就是它）", "#2563eb", DL,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=590)
    svg += caption("② 输入级 PNP → 共模范围含地：这是它能吃单电源的根本原因", "#059669", DL,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=590)
    svg += caption("③ 输出非轨到轨：余量随负载和温度变化，按具体型号手册核对", "#dc2626", DL,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=590)
    svg += caption("④ TI 经典 LM358：典型 GBW 0.7MHz / SR 0.3V/µs；B 版参数不同", "#b45309", DL,
                   "0;0;1;1", "0;0.85;0.9;1", y=590)
    save('lm358-dual.svg', svg + '</svg>')

# ======================= 图 69：BJT 三种组态（第 11 章 11.1） =======================
def make_bjt_configs():
    DC = 11
    def tri(x, y, col):
        return (f'<polygon points="{x},{y-34} {x},{y+34} {x+60},{y}" fill="#f8fafc" stroke="{col}" stroke-width="2.2"/>')
    svg = svg_open('一只晶体管的三种人生：共射、共集、共基', h=620)
    svg += '''
<text x="400" y="56" text-anchor="middle" font-size="11" fill="#64748b">信号从哪进、从哪出、哪个极做交流公共端 —— 决定它的性格</text>
'''
    conf = [
        ('共射 CE', '#2563eb', 'B 进 → C 出', '高（几十~几百）', '中 ~kΩ', '中 ~kΩ', '反相 180°', '放大主力'),
        ('共集 CC', '#059669', 'B 进 → E 出', '≈1（略小于 1）', '高', '低（Ω 级）', '同相', '缓冲/阻抗变换'),
        ('共基 CB', '#b45309', 'E 进 → C 出', '高', '极低（几十Ω）', '中', '同相', '高频放大'),
    ]
    x = 30
    for name, col, io, av, zin, zout, ph, use in conf:
        svg += f'<rect x="{x}" y="66" width="240" height="290" rx="10" fill="#f8fafc" stroke="{col}" stroke-width="1.8"/>'
        svg += f'<text x="{x+120}" y="94" text-anchor="middle" font-size="13.5" font-weight="bold" fill="{col}">{name}</text>'
        svg += tri(x+78, 150, col)
        svg += f'<text x="{x+146}" y="146" font-size="11" font-weight="bold" fill="{col}">{io}</text>'
        svg += f'<line x1="{x+14}" y1="196" x2="{x+226}" y2="196" stroke="#cbd5e1" stroke-width="1"/>'
        yy = 218
        for k, v in (('电压增益', av), ('输入阻抗', zin), ('输出阻抗', zout), ('相位', ph)):
            svg += f'<text x="{x+16}" y="{yy}" font-size="11" fill="#475569">{k}</text>'
            svg += f'<text x="{x+224}" y="{yy}" text-anchor="end" font-size="11" font-weight="bold" fill="{col}">{v}</text>'
            yy += 22
        svg += f'<line x1="{x+14}" y1="{yy-8}" x2="{x+226}" y2="{yy-8}" stroke="#e2e8f0" stroke-width="1"/>'
        svg += f'<text x="{x+16}" y="{yy+14}" font-size="11" fill="#475569">用途</text>'
        svg += f'<text x="{x+224}" y="{yy+14}" text-anchor="end" font-size="11" font-weight="bold" fill="{col}">{use}</text>'
        x += 253
    svg += f'''
<line x1="30" y1="378" x2="770" y2="378" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="406" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">三句话记住它们</text>
<text x="60" y="436" font-size="11.5" fill="#475569">① <tspan font-weight="bold" fill="#2563eb">共射</tspan>：电压放大最强、但输入输出阻抗都平庸——「主力但不好带」</text>
<text x="60" y="460" font-size="11.5" fill="#475569">② <tspan font-weight="bold" fill="#059669">共集（射随器）</tspan>：放弃电压增益，换来「高进低出」——前级带不动？中间插一级它</text>
<text x="60" y="484" font-size="11.5" fill="#475569">③ <tspan font-weight="bold" fill="#b45309">共基</tspan>：牺牲输入阻抗换高频性能——Miller 电容不再接地，高频放大器的最爱</text>
<rect x="60" y="506" width="680" height="76" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.6"/>
<text x="76" y="532" font-size="12" font-weight="bold" fill="#b45309">射随器为什么叫「跟随」</text>
<text x="76" y="554" font-size="11.5" fill="#475569">V_E = V_B − 0.7V：基极动多少、发射极跟着动多少（差一个死板的 0.7V）。它放大的不是电压而是<tspan font-weight="bold">电流</tspan>：</text>
<text x="76" y="574" font-size="11.5" fill="#475569">信号源只出 I_B，负载拿走 I_E = (1+β)·I_B —— 这就是「阻抗变换」的全部秘密</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DC}s" repeatCount="indefinite" path="M78,150 L136,150 L164,150" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DC}s" begin="-1.1s" repeatCount="indefinite" path="M331,150 L389,150 L417,150" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#b45309"><animateMotion dur="{DC}s" begin="-2.2s" repeatCount="indefinite" path="M584,150 L642,150 L670,150" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(38, 92, 224, 30, '#2563eb', 2.0, 8)}
{pulse(291, 92, 224, 30, '#059669', 2.0, 8)}
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-0.6s" repeatCount="indefinite" path="M50,340 L246,340"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DC}s" begin="-1.6s" repeatCount="indefinite" path="M303,340 L499,340"/></circle>
<circle cx="400" cy="552" r="5" fill="none" stroke="#b45309" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" repeatCount="indefinite"/></circle>
{pulse(544, 92, 224, 30, '#b45309', 2.0, 8)}
'''
    svg += caption("① 共射：电压增益最高但阻抗平庸，还好反相——放大主力的代价", "#2563eb", DC,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=604)
    svg += caption("② 共集：电压增益 ≈1 却成神器——高输入阻抗 + 极低输出阻抗 = 缓冲器", "#059669", DC,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=604)
    svg += caption("③ 共基：输入阻抗极低，但高频性能最好（没有 Miller 效应拖后腿）", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=604)
    svg += caption("④ 级联心法：共射打头阵放大、射随器垫后驱动、共基守高频前线", "#7c3aed", DC,
                   "0;0;1;1", "0;0.85;0.9;1", y=604)
    save('bjt-configs.svg', svg + '</svg>')

# ======================= 图 70：分立串联稳压（第 13 章 13.1） =======================
def make_discrete_ldo():
    DD = 11
    svg = svg_open('分立串联稳压：LDO 的祖爷爷，三块积木', h=620)
    svg += f'''
<text x="400" y="56" text-anchor="middle" font-size="11" fill="#64748b">基准 + 误差放大 + 调整管 —— 与 LDO 内部框图同构</text>
<line x1="70" y1="96" x2="70" y2="130" stroke="#334155" stroke-width="2.5"/>
<text x="56" y="90" font-size="11.5" font-weight="bold" fill="#b45309">Vin 12V</text>
<line x1="70" y1="130" x2="230" y2="130" stroke="#334155" stroke-width="2.5"/>
<circle cx="230" cy="130" r="4.5" fill="#334155"/>
<line x1="230" y1="130" x2="230" y2="160" stroke="#334155" stroke-width="2.5"/>
<rect x="196" y="160" width="68" height="52" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2.5"/>
<text x="230" y="182" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">调整管</text>
<text x="230" y="200" text-anchor="middle" font-size="10.5" fill="#475569">NPN 射随</text>
<line x1="230" y1="212" x2="230" y2="244" stroke="#334155" stroke-width="2.5"/>
<circle cx="230" cy="244" r="4.5" fill="#334155"/>
<line x1="230" y1="244" x2="370" y2="244" stroke="#334155" stroke-width="2.5"/>
<text x="376" y="240" font-size="12" font-weight="bold" fill="#059669">Vout</text>
<text x="376" y="260" font-size="11" font-weight="bold" fill="#059669">= V_Z − 0.7V</text>
<line x1="150" y1="130" x2="150" y2="176" stroke="#334155" stroke-width="2.5"/>
<rect x="132" y="176" width="36" height="30" rx="4" fill="#fffbeb" stroke="#b45309" stroke-width="2.2"/>
<text x="112" y="196" text-anchor="end" font-size="10.5" font-weight="bold" fill="#b45309">R_b</text>
<line x1="150" y1="206" x2="150" y2="232" stroke="#334155" stroke-width="2.5"/>
<path d="M138,232 L162,232 L150,254 Z" fill="#f8fafc" stroke="#b45309" stroke-width="2.2"/>
<line x1="138" y1="254" x2="162" y2="254" stroke="#b45309" stroke-width="3.5"/>
<line x1="150" y1="254" x2="150" y2="284" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(150, 298)}
<line x1="150" y1="243" x2="196" y2="186" stroke="#334155" stroke-width="2.5"/>
<text x="112" y="238" text-anchor="end" font-size="10.5" font-weight="bold" fill="#b45309">V_Z 6.2V</text>
<circle r="4.5" fill="#b45309"><animateMotion dur="{DD}s" begin="-0.3s" repeatCount="indefinite" path="M72,132 L148,132 L150,174"/></circle>
<circle r="4.5" fill="#2563eb"><animateMotion dur="{DD}s" begin="-0.9s" repeatCount="indefinite" path="M232,162 L232,210 L232,242 L368,244"/></circle>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DD}s" begin="-1.5s" repeatCount="indefinite" path="M152,241 L194,187"/></circle>
<circle r="4.5" fill="#b45309"><animateMotion dur="{DD}s" begin="-2.1s" repeatCount="indefinite" path="M150,256 L150,282"/></circle>
<text x="420" y="140" font-size="11.5" font-weight="bold" fill="#b45309">① 基准</text>
<text x="420" y="160" font-size="11" fill="#475569">齐纳管出 μA 级参考</text>
<text x="420" y="178" font-size="11" fill="#475569">（6.2V 附近温漂小）</text>
<text x="420" y="206" font-size="11.5" font-weight="bold" fill="#2563eb">② 调整管</text>
<text x="420" y="226" font-size="11" fill="#475569">NPN 射随器做电流放大</text>
<text x="420" y="244" font-size="11" fill="#475569">出 A 级负载电流</text>
<text x="420" y="272" font-size="11.5" font-weight="bold" fill="#7c3aed">③ 误差放大（隐含在射随器里）</text>
<text x="420" y="292" font-size="11" fill="#475569">Vout 一跌 → V_BE 变大 → 调整管</text>
<text x="420" y="310" font-size="11" fill="#475569">导通更深 → Vout 拉回：天然负反馈</text>
<rect x="60" y="336" width="700" height="76" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.6"/>
<text x="76" y="362" font-size="12" font-weight="bold" fill="#2563eb">缺的那一块：把「误差」真正放大</text>
<text x="76" y="384" font-size="11.5" fill="#475569">射随器的负反馈是「顺带」的，增益只有 1 —— 想让 Vout 更稳，得用运放当误差放大器：</text>
<text x="76" y="404" font-size="11.5" fill="#475569">齐纳基准 → 运放比 R 分压 → 驱动调整管。**7805/AMS1117 就是把这三块做进硅片**，再加保护电路。</text>
<line x1="40" y1="440" x2="760" y2="440" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="468" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">演进：为什么最后都做进芯片</text>
<text x="400" y="494" text-anchor="middle" font-size="11.5" fill="#475569">分立版：两颗元件 + 电阻，便宜、灵活，但温漂大（V_Z 与 V_BE 双重温漂）、无过流保护</text>
<text x="400" y="518" text-anchor="middle" font-size="11.5" fill="#475569">集成版（7805）：同样三块积木，加上**过流/过热/安全工作区保护**与激光修调——温漂低一个量级</text>
<text x="400" y="546" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">看懂分立版，就看懂了所有串联型线性稳压器的骨架</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DD}s" begin="-0.6s" repeatCount="indefinite" path="M196,166 L228,166"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DD}s" begin="-1.4s" repeatCount="indefinite" path="M230,246 L366,246"/></circle>
<circle cx="376" cy="250" r="5" fill="none" stroke="#059669" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" repeatCount="indefinite"/></circle>
<circle cx="150" cy="240" r="4" fill="#7c3aed"><animate attributeName="r" values="4;9;4" dur="1.7s" repeatCount="indefinite"/></circle>
{pulse(192, 156, 76, 62, '#2563eb', 2.0, 10)}
'''
    svg += caption("① 两块积木就能稳压：齐纳出基准、NPN 射随器出电流（Vout = V_Z − 0.7V）", "#b45309", DD,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=592)
    svg += caption("② 第三块是「顺带」的负反馈：Vout 一跌，V_BE 变大，管子导通更深把它拉回", "#7c3aed", DD,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=592)
    svg += caption("③ 但射随器自己只有 1 倍「反馈增益」——想更稳必须上运放做误差放大", "#2563eb", DD,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=592)
    svg += caption("④ 7805/AMS1117 就是这三块 + 保护做进硅片：看懂分立版就看懂了 LDO 骨架", "#059669", DD,
                   "0;0;1;1", "0;0.85;0.9;1", y=592)
    save('discrete-ldo.svg', svg + '</svg>')

# ======================= 图 71：BJT 载流子输运（第 3 章 3.1） =======================
def make_bjt_transport():
    DB = 11
    svg = svg_open('BJT 放大原理：99% 的电子来不及复合，就成了 I_C', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">NPN：两块 N 夹一块「极薄」的 P</text>
<rect x="80" y="90" width="130" height="130" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2.2"/>
<text x="145" y="118" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#2563eb">发射区 N+</text>
<text x="145" y="140" text-anchor="middle" font-size="10.5" fill="#475569">重掺杂</text>
<text x="145" y="162" text-anchor="middle" font-size="10.5" fill="#475569">发射结正偏</text>
<text x="145" y="182" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">↓ 注入电子</text>
<rect x="250" y="90" width="90" height="130" rx="6" fill="#fef2f2" stroke="#dc2626" stroke-width="2.2"/>
<text x="295" y="112" text-anchor="middle" font-size="12" font-weight="bold" fill="#dc2626">基区 P</text>
<text x="295" y="132" text-anchor="middle" font-size="10.5" fill="#475569">极薄</text>
<text x="295" y="150" text-anchor="middle" font-size="10.5" fill="#475569">轻掺杂</text>
<text x="295" y="176" text-anchor="middle" font-size="10" fill="#475569">（复合 1%）</text>
<rect x="380" y="90" width="130" height="130" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2.2"/>
<text x="445" y="118" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#2563eb">集电区 N</text>
<text x="445" y="140" text-anchor="middle" font-size="10.5" fill="#475569">集电结反偏</text>
<text x="445" y="162" text-anchor="middle" font-size="10.5" fill="#475569">强电场扫入</text>
<text x="445" y="182" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">→ I_C</text>
<line x1="210" y1="140" x2="248" y2="140" stroke="#334155" stroke-width="2"/>
<line x1="342" y1="140" x2="378" y2="140" stroke="#334155" stroke-width="2"/>
<text x="145" y="86" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">E</text>
<text x="295" y="86" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">B</text>
<text x="445" y="86" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">C</text>
<line x1="295" y1="220" x2="295" y2="252" stroke="#b45309" stroke-width="2.5"/>
<text x="305" y="244" font-size="11" font-weight="bold" fill="#b45309">I_B ≈ 1% I_E</text>
<circle r="5.5" fill="#2563eb"><animateMotion dur="{DB}s" begin="-0.2s" repeatCount="indefinite" path="M92,155 L246,150" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5.5" fill="#2563eb"><animateMotion dur="{DB}s" begin="-0.7s" repeatCount="indefinite" path="M92,135 L246,135" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5.5" fill="#2563eb"><animateMotion dur="{DB}s" begin="-1.2s" repeatCount="indefinite" path="M252,140 L376,140" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DB}s" begin="-1.8s" repeatCount="indefinite" path="M288,150 L300,214" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4" fill="#dc2626"><animateMotion dur="{DB}s" begin="-2.4s" repeatCount="indefinite" path="M280,165 L282,168" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4" fill="#dc2626"><animateMotion dur="{DB}s" begin="-2.7s" repeatCount="indefinite" path="M302,158 L305,161" keyPoints="0;1" keyTimes="0;1"/></circle>
<line x1="504" y1="90" x2="504" y2="480" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="600" y="112" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">五步物理图像</text>
<text x="560" y="146" font-size="11.5" fill="#475569">① 发射结<tspan font-weight="bold" fill="#059669">正偏</tspan> → 发射区向基区大量注入电子</text>
<text x="560" y="176" font-size="11.5" fill="#475569">② 基区<tspan font-weight="bold" fill="#dc2626">极薄且轻掺杂</tspan> → 99% 电子来不及复合</text>
<text x="560" y="206" font-size="11.5" fill="#475569">③ 集电结<tspan font-weight="bold" fill="#059669">反偏</tspan> → 强电场把电子扫入集电极</text>
<text x="560" y="236" font-size="11.5" fill="#475569">④ 只有约 <tspan font-weight="bold" fill="#b45309">1%</tspan> 在基区复合 → 形成小电流 I_B</text>
<text x="560" y="266" font-size="11.5" fill="#475569">⑤ 结果：I_C = β·I_B，<tspan font-weight="bold">小电流控制大电流</tspan></text>
<rect x="560" y="292" width="240" height="120" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.8"/>
<text x="570" y="318" font-size="12" font-weight="bold" fill="#b45309">为什么不能依赖 β</text>
<text x="570" y="342" font-size="11" fill="#475569">β 不是精密常数：</text>
<text x="570" y="362" font-size="11" fill="#475569">· 同一型号离散 50~300</text>
<text x="570" y="382" font-size="11" fill="#475569">· 随温度变化</text>
<text x="570" y="402" font-size="11" fill="#475569">· 随 I_C 大小变化</text>
<rect x="60" y="292" width="440" height="120" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>
<text x="76" y="318" font-size="12" font-weight="bold" fill="#2563eb">电流账（β=100 时）</text>
<text x="76" y="342" font-size="11.5" fill="#475569">I_E = I_B + I_C（基尔霍夫，永远成立）</text>
<text x="76" y="364" font-size="11.5" fill="#475569">I_B = 1% I_E → I_C = 99% I_E</text>
<text x="76" y="386" font-size="11.5" font-weight="bold" fill="#059669">所以 β = I_C/I_B ≈ 99 —— 它是「漏网比例」的倒数</text>
<text x="76" y="404" font-size="11" fill="#475569">设计时用「强制 β」（如 10）而非标称 β，见 3.5</text>
'''
    svg += caption("① 发射结正偏注入电子——这是「源」；电子多少由 V_BE 决定", "#2563eb", DB,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=520)
    svg += caption("② 基区极薄是关键：电子「来不及」复合就被扫走了——这是 β 的物理来源", "#dc2626", DB,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=520)
    svg += caption("③ 集电结反偏提供清扫电场：结构决定它「只能放大、不能反过来」", "#059669", DB,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=520)
    svg += caption("④ 记住 β 是「漏网比例的倒数」——离散大、随温度变，设计绝不依赖它", "#b45309", DB,
                   "0;0;1;1", "0;0.85;0.9;1", y=520)
    svg += note_box("BJT 是电流控制器件：真正的输入量是 I_B，输出是 I_C——这是与 MOSFET（电压控制）最本质的分野", 560, DB,
                    "0;0.9;0.94;1", w=760)
    save('bjt-transport.svg', svg + '</svg>')

# ======================= 图 72：BJT 作开关驱动继电器（第 3 章 3.5） =======================
def make_bjt_switch():
    DS = 11
    svg = svg_open('BJT 作开关：算对 Rb，再给线圈配一只续流二极管', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">5V/70mA 继电器 + 3.3V MCU 驱动</text>
<line x1="180" y1="90" x2="180" y2="120" stroke="#334155" stroke-width="2.5"/>
<text x="166" y="86" font-size="11.5" font-weight="bold" fill="#b45309">Vcc 5V</text>
<line x1="120" y1="120" x2="330" y2="120" stroke="#334155" stroke-width="2.5"/>
<line x1="180" y1="120" x2="180" y2="150" stroke="#334155" stroke-width="2.5"/>
<rect x="152" y="150" width="56" height="60" rx="5" fill="#fffbeb" stroke="#b45309" stroke-width="2.2"/>
<text x="180" y="176" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#b45309">线圈</text>
<text x="180" y="196" text-anchor="middle" font-size="10" fill="#475569">70mA</text>
<line x1="180" y1="210" x2="180" y2="248" stroke="#334155" stroke-width="2.5"/>
<circle cx="180" cy="248" r="4.5" fill="#334155"/>
<line x1="120" y1="120" x2="120" y2="150" stroke="#334155" stroke-width="2.5"/>
<path d="M108,150 L120,150 L120,210 L108,210" fill="none" stroke="#7c3aed" stroke-width="2.2"/>
<line x1="120" y1="150" x2="120" y2="150" stroke="#7c3aed" stroke-width="2.2"/>
<line x1="108" y1="150" x2="132" y2="150" stroke="#7c3aed" stroke-width="3.2"/>
<line x1="108" y1="210" x2="132" y2="210" stroke="#7c3aed" stroke-width="3.2"/>
<line x1="120" y1="210" x2="120" y2="248" stroke="#7c3aed" stroke-width="2.2"/>
<line x1="120" y1="248" x2="180" y2="248" stroke="#7c3aed" stroke-width="2.2"/>
<text x="60" y="186" font-size="11" font-weight="bold" fill="#7c3aed">1N4148</text>
<text x="60" y="204" font-size="10" fill="#dc2626">续流</text>
<text x="196" y="240" font-size="12" font-weight="bold" fill="#2563eb">C</text>
<polygon points="200,248 200,290 250,269" fill="#f8fafc" stroke="#2563eb" stroke-width="2.5"/>
<text x="216" y="266" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#2563eb">NPN</text>
<text x="196" y="310" font-size="12" font-weight="bold" fill="#059669">E</text>
<line x1="200" y1="290" x2="180" y2="290" stroke="#2563eb" stroke-width="2.5"/>
<line x1="180" y1="290" x2="180" y2="318" stroke="#2563eb" stroke-width="2.5"/>
{gnd_sym(180, 332)}
<line x1="150" y1="269" x2="118" y2="269" stroke="#334155" stroke-width="2.5"/>
<rect x="68" y="257" width="46" height="24" rx="3" fill="#f8fafc" stroke="#b45309" stroke-width="2.5"/>
<text x="91" y="245" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">R_b 360Ω</text>
<line x1="68" y1="269" x2="30" y2="269" stroke="#334155" stroke-width="2.5"/>
<text x="6" y="256" font-size="11.5" font-weight="bold" fill="#059669">MCU 3.3V</text>
<circle r="5" fill="#059669"><animateMotion dur="{DS}s" begin="-0.3s" repeatCount="indefinite" path="M32,269 L66,269"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DS}s" begin="-1.0s" repeatCount="indefinite" path="M116,269 L148,269"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DS}s" begin="-1.7s" repeatCount="indefinite" path="M182,250 L182,288 L180,316"/></circle>
<circle r="5" fill="#b45309"><animateMotion dur="{DS}s" begin="-2.4s" repeatCount="indefinite" path="M182,122 L182,148"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DS}s" begin="-3.0s" repeatCount="indefinite" path="M122,212 L122,246"/></circle>
<line x1="420" y1="80" x2="420" y2="560" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="620" y="76" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">三步算完（继电器 5V/70mA）</text>
<rect x="446" y="94" width="330" height="120" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>
<text x="462" y="120" font-size="12" font-weight="bold" fill="#2563eb">① 取「强制 β = 10」</text>
<text x="462" y="144" font-size="11.5" fill="#475569">深度饱和保险系数——不用标称 β</text>
<text x="462" y="166" font-size="11.5" font-weight="bold" fill="#059669">I_B = 70mA / 10 = 7mA</text>
<text x="462" y="190" font-size="11" fill="#475569">（若按 β=100 算只需 0.7mA，一旦</text>
<text x="462" y="206" font-size="11" fill="#475569">换成低 β 管子就不饱和了）</text>
<rect x="446" y="228" width="330" height="96" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.8"/>
<text x="462" y="254" font-size="12" font-weight="bold" fill="#b45309">② 算基极电阻</text>
<text x="462" y="278" font-size="11.5" fill="#475569">R_B = (V_MCU − V_BE) / I_B</text>
<text x="462" y="302" font-size="11.5" font-weight="bold" fill="#059669">= (3.3 − 0.7) / 7mA ≈ 371Ω</text>
<text x="462" y="318" font-size="10.5" fill="#475569">取标称值 360Ω（或 330Ω，偏大更安全）</text>
<rect x="446" y="338" width="330" height="150" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.8"/>
<text x="462" y="364" font-size="12" font-weight="bold" fill="#b91c1c">③ 续流二极管：不是可选项</text>
<text x="462" y="388" font-size="11.5" fill="#475569">线圈是感性负载：关断瞬间 L·di/dt 产生</text>
<text x="462" y="408" font-size="11.5" fill="#475569">反电动势（可到几十上百伏）</text>
<text x="462" y="430" font-size="11.5" font-weight="bold" fill="#dc2626">没有它 → 三极管 C-E 被击穿</text>
<text x="462" y="454" font-size="11" fill="#475569">1N4148 反并在线圈两端，给感应电流</text>
<text x="462" y="472" font-size="11" fill="#475569">一条泄放回路（方向：与电源相反）</text>
<text x="620" y="516" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#7c3aed">感性负载三兄弟：继电器 / 电机 / 电磁阀 —— 一律加续流或吸收</text>
<text x="620" y="540" text-anchor="middle" font-size="11" fill="#475569">驱动 MOS 时同理，且别忘了体二极管（见 4.4）</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DS}s" begin="-0.5s" repeatCount="indefinite" path="M448,120 L612,120"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DS}s" begin="-1.5s" repeatCount="indefinite" path="M448,300 L760,300"/></circle>
<circle cx="180" cy="240" r="4" fill="#7c3aed"><animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/></circle>
{pulse(444, 336, 334, 154, '#dc2626', 2.0, 10)}
'''
    svg += caption("① 用「强制 β=10」定 I_B：不依赖标称 β，才能保证深度饱和", "#2563eb", DS,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=586)
    svg += caption("② R_B=(3.3V−0.7V)/7mA≈371Ω，就近取标称 360Ω —— 分母是 I_B 不是 I_C，别算错", "#b45309", DS,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=586)
    svg += caption("③ 续流二极管必备：线圈反电动势能到上百伏，三极管扛不住", "#dc2626", DS,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=586)
    svg += caption("④ 电感（继电器/电机/电磁阀）都要有泄放回路——这是硬件保命常识", "#7c3aed", DS,
                   "0;0;1;1", "0;0.85;0.9;1", y=586)
    save('bjt-switch.svg', svg + '</svg>')

# ======================= 图 73：体二极管与栅极保护（第 4 章 4.4） =======================
def make_body_diode():
    DY = 11
    svg = svg_open('MOSFET 的两条命门：体二极管与栅氧层', h=620)
    svg += f'''
<text x="200" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">体二极管：白送的一只「反向并联」二极管</text>
<text x="26" y="150" font-size="12" font-weight="bold" fill="#2563eb">D</text>
<line x1="44" y1="146" x2="80" y2="146" stroke="#334155" stroke-width="2.5"/>
<line x1="80" y1="120" x2="80" y2="172" stroke="#334155" stroke-width="2.5"/>
<line x1="96" y1="120" x2="96" y2="172" stroke="#334155" stroke-width="2.5"/>
<line x1="96" y1="146" x2="140" y2="146" stroke="#334155" stroke-width="2.5"/>
<text x="150" y="176" font-size="12" font-weight="bold" fill="#059669">S</text>
<line x1="88" y1="146" x2="88" y2="200" stroke="#94a3b8" stroke-width="2"/>
<line x1="88" y1="200" x2="200" y2="200" stroke="#94a3b8" stroke-width="2"/>
<line x1="200" y1="200" x2="200" y2="146" stroke="#94a3b8" stroke-width="2"/>
<path d="M150,120 L200,120 L200,146" fill="none" stroke="#7c3aed" stroke-width="2.2"/>
<line x1="150" y1="120" x2="150" y2="200" stroke="#7c3aed" stroke-width="2.2"/>
<line x1="188" y1="108" x2="212" y2="108" stroke="#7c3aed" stroke-width="3.5"/>
<line x1="200" y1="108" x2="200" y2="120" stroke="#7c3aed" stroke-width="2"/>
<path d="M188,96 L200,86 L212,96 Z" fill="#7c3aed"/>
<text x="222" y="76" font-size="10.5" font-weight="bold" fill="#7c3aed">体二极管</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DY}s" begin="-0.3s" repeatCount="indefinite" path="M46,146 L78,146"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DY}s" begin="-1.0s" repeatCount="indefinite" path="M98,146 L138,146"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DY}s" begin="-1.7s" repeatCount="indefinite" path="M150,190 L198,190 L198,150"/></circle>
<line x1="236" y1="80" x2="236" y2="560" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="520" y="76" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">两处后果 + 一处保护</text>
<rect x="262" y="94" width="330" height="120" rx="8" fill="#f8fafc" stroke="#2563eb" stroke-width="1.8"/>
<text x="278" y="120" font-size="12" font-weight="bold" fill="#2563eb">① 好处：白送一只续流管</text>
<text x="278" y="144" font-size="11.5" fill="#475569">H 桥 / 同步 Buck 的「续流」环节，</text>
<text x="278" y="164" font-size="11.5" fill="#475569">正是体二极管在顶班（死区时间里）</text>
<text x="278" y="188" font-size="11.5" font-weight="bold" fill="#059669">→ 这是 MOS 能替代二极管整流的根</text>
<text x="278" y="206" font-size="11" fill="#475569">但它的压降比肖特基大、反向恢复更慢</text>
<rect x="262" y="228" width="330" height="110" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.8"/>
<text x="278" y="254" font-size="12" font-weight="bold" fill="#b91c1c">② 坏处：不能反向阻断</text>
<text x="278" y="278" font-size="11.5" fill="#475569">想用 MOS 做「理想二极管」防反接？</text>
<text x="278" y="300" font-size="11.5" font-weight="bold" fill="#dc2626">单管不行——反向时体二极管照样导通</text>
<text x="278" y="324" font-size="11.5" fill="#475569">要用两只背靠背（共源）才有阻断能力</text>
<rect x="262" y="352" width="330" height="136" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.8"/>
<text x="278" y="378" font-size="12" font-weight="bold" fill="#b45309">③ 栅氧层只有几十 nm，耐压 ±20V</text>
<text x="278" y="402" font-size="11.5" fill="#475569">栅极是「电容」，不是电阻——</text>
<text x="278" y="422" font-size="11.5" fill="#475569">一旦过压或静电，栅氧直接击穿（永久损坏）</text>
<text x="278" y="446" font-size="11.5" font-weight="bold" fill="#dc2626">未用的 MOS 栅极不得悬空！</text>
<text x="278" y="470" font-size="11" fill="#475569">驱动回路串 10~100Ω 抑制振铃 + 栅极加钳位/下拉</text>
<text x="600" y="508" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">三句话速记</text>
<text x="600" y="534" text-anchor="middle" font-size="11.5" fill="#475569">体二极管：白送续流、但断了「反向阻断」这条路</text>
<text x="600" y="556" text-anchor="middle" font-size="11.5" fill="#475569">栅极：当电容对待——防静电、防悬空、串小电阻</text>
<text x="600" y="578" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">死区时间里的续流，正是体二极管在顶班（见 13.7 H 桥）</text>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DY}s" begin="-0.5s" repeatCount="indefinite" path="M46,146 L78,146"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DY}s" begin="-1.3s" repeatCount="indefinite" path="M150,190 L198,190"/></circle>
<circle cx="200" cy="104" r="5" fill="none" stroke="#7c3aed" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="1.9s" repeatCount="indefinite"/></circle>
<circle cx="278" cy="440" r="4" fill="#dc2626"><animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/></circle>
{pulse(258, 350, 338, 142, '#b45309', 2.0, 10)}
'''
    svg += caption("① 体二极管是结构自带的：MOS 天然反向并联一只二极管，拆不掉", "#2563eb", DY,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=604)
    svg += caption("② 好处是 H 桥/同步 Buck 的死区续流有它顶班；坏处是想反向阻断就不行", "#dc2626", DY,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=604)
    svg += caption("③ 栅氧层几十 nm、耐压 ±20V：栅极当电容看，防静电防悬空", "#b45309", DY,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=604)
    svg += caption("④ 驱动串 10~100Ω 抑制振铃；未用管子栅极必须下拉或接地", "#7c3aed", DY,
                   "0;0;1;1", "0;0.85;0.9;1", y=604)
    save('body-diode.svg', svg + '</svg>')

# ======================= 图 74：CD4051 多路复用（第 8 章 8.2） =======================
def make_mux4051():
    DM = 11
    svg = svg_open('CD4051：八路传感器共用一个 ADC', h=732)
    svg += '''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">3 位地址选 8 路之一 —— 多路复用器就是「模拟旋转开关」</text>
<text x="220" y="100" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">CD4051（8 选 1）</text>
<rect x="120" y="120" width="200" height="260" rx="10" fill="#f8fafc" stroke="#2563eb" stroke-width="2.2"/>
<text x="220" y="148" text-anchor="middle" font-size="11.5" fill="#475569">8 路模拟输入（双向）</text>
'''
    for i in range(8):
        y = 176 + i*24
        svg += f'<line x1="70" y1="{y}" x2="120" y2="{y}" stroke="#334155" stroke-width="2"/>'
        svg += f'<circle cx="120" cy="{y}" r="3.5" fill="#334155"/>'
        svg += f'<text x="62" y="{y+4}" text-anchor="end" font-size="10.5" font-weight="bold" fill="#b45309">Y{i}</text>'
    svg += '''
<line x1="320" y1="200" x2="370" y2="200" stroke="#334155" stroke-width="2.5"/>
<text x="382" y="204" font-size="11.5" font-weight="bold" fill="#059669">COM 公共端</text>
<line x1="320" y1="300" x2="370" y2="300" stroke="#334155" stroke-width="2.5"/>
<text x="376" y="304" font-size="11.5" font-weight="bold" fill="#7c3aed">→ 送 ADC</text>
<text x="220" y="410" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">A0 A1 A2 三位地址（4051）</text>
<line x1="400" y1="430" x2="760" y2="430" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="580" y="470" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">通道选择表</text>
<text x="450" y="502" font-size="11.5" font-weight="bold" fill="#475569">A2 A1 A0</text>
<text x="600" y="502" font-size="11.5" font-weight="bold" fill="#475569">选中的通道</text>
'''
    for i, addr in enumerate(['0 0 0', '0 0 1', '0 1 0', '0 1 1', '1 0 0', '1 0 1', '1 1 0', '1 1 1']):
        y = 526 + i*20
        col = '#059669' if i == 5 else '#475569'
        svg += f'<text x="450" y="{y}" font-size="11" fill="{col}">{addr}</text>'
        svg += f'<text x="600" y="{y}" font-size="11" font-weight="bold" fill="{col}">Y{i}</text>'
        if i == 5:
            svg += f'<text x="640" y="{y}" font-size="10.5" fill="#059669">← 本例选中（接热敏电阻）</text>'
    svg += f'''
<circle r="5" fill="#059669"><animateMotion dur="{DM}s" begin="-0.3s" repeatCount="indefinite" path="M60,296 L118,296"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DM}s" begin="-0.9s" repeatCount="indefinite" path="M122,296 L318,300"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DM}s" begin="-1.5s" repeatCount="indefinite" path="M322,300 L368,300"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DM}s" begin="-2.1s" repeatCount="indefinite" path="M150,404 L290,404"/></circle>
<circle cx="220" cy="140" r="5" fill="none" stroke="#2563eb" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" repeatCount="indefinite"/></circle>
<circle cx="370" cy="200" r="5" fill="none" stroke="#059669" stroke-width="2.2">
<animate attributeName="r" values="5;12;5" dur="2.0s" begin="-1.0s" repeatCount="indefinite"/></circle>
<circle r="5" fill="#94a3b8"><animateMotion dur="{DM}s" begin="-4.0s" repeatCount="indefinite" path="M72,200 L118,200"/></circle>
<circle r="5" fill="#94a3b8"><animateMotion dur="{DM}s" begin="-5.5s" repeatCount="indefinite" path="M72,248 L118,248"/></circle>
<circle cx="370" cy="300" r="5" fill="none" stroke="#7c3aed" stroke-width="2.2"><animate attributeName="r" values="5;12;5" dur="2.0s" repeatCount="indefinite"/></circle>
<circle cx="320" cy="300" r="5" fill="none" stroke="#059669" stroke-width="2.2"><animate attributeName="r" values="5;12;5" dur="2.0s" begin="-1.0s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① 三位地址选通一路：8 个传感器轮流接到同一个 ADC——省掉 7 个 ADC", "#2563eb", DM,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=700)
    svg += caption("② 通道是双向的：COM 既能输出（送 ADC）、也能输入（做信号分配）", "#059669", DM,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=700)
    svg += caption("③ 切换瞬间有电荷注入与 Ron 变化——别在转换中途切通道（见 8.6）", "#dc2626", DM,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=700)
    svg += caption("④ 同族选型：4052 双 4 选 1、4053 三路 2 选 1、74HC4051 高速版", "#b45309", DM,
                   "0;0;1;1", "0;0.85;0.9;1", y=700)
    save('mux-4051.svg', svg + '</svg>')

# ======================= 图 75：达林顿管（第 3 章 3.6） =======================
def make_darlington():
    DD = 11
    svg = svg_open('达林顿管：β 相乘，代价是三笔', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">Q2 的基极电流，就是 Q1 的发射极电流</text>
<line x1="120" y1="92" x2="120" y2="122" stroke="#334155" stroke-width="2.5"/>
<text x="106" y="88" font-size="11.5" font-weight="bold" fill="#b45309">Vin</text>
<line x1="120" y1="122" x2="160" y2="122" stroke="#334155" stroke-width="2.5"/>
<circle cx="160" cy="122" r="4.5" fill="#334155"/>
<line x1="160" y1="122" x2="160" y2="152" stroke="#334155" stroke-width="2.5"/>
<polygon points="160,152 160,200 208,176" fill="#f8fafc" stroke="#2563eb" stroke-width="2.4"/>
<text x="172" y="170" font-size="10.5" font-weight="bold" fill="#2563eb">Q1</text>
<text x="172" y="188" font-size="9.5" fill="#475569">β₁</text>
<line x1="160" y1="200" x2="160" y2="248" stroke="#2563eb" stroke-width="2.5"/>
<circle cx="160" cy="248" r="4.5" fill="#334155"/>
<line x1="160" y1="248" x2="160" y2="278" stroke="#334155" stroke-width="2.5"/>
<polygon points="160,278 160,326 208,302" fill="#f8fafc" stroke="#059669" stroke-width="2.4"/>
<text x="172" y="296" font-size="10.5" font-weight="bold" fill="#059669">Q2</text>
<text x="172" y="314" font-size="9.5" fill="#475569">β₂</text>
<line x1="160" y1="326" x2="160" y2="366" stroke="#059669" stroke-width="2.5"/>
<line x1="160" y1="366" x2="120" y2="366" stroke="#334155" stroke-width="2.5"/>
<line x1="160" y1="366" x2="200" y2="366" stroke="#334155" stroke-width="2.5"/>
<line x1="120" y1="366" x2="120" y2="392" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(120, 406)}
<line x1="200" y1="366" x2="240" y2="366" stroke="#334155" stroke-width="2.5"/>
<circle cx="240" cy="366" r="4.5" fill="#334155"/>
<line x1="240" y1="366" x2="240" y2="200" stroke="#334155" stroke-width="2.5"/>
<line x1="240" y1="200" x2="208" y2="176" stroke="#334155" stroke-width="2.5"/>
<line x1="240" y1="200" x2="300" y2="200" stroke="#334155" stroke-width="2.5"/>
<text x="306" y="196" font-size="11.5" font-weight="bold" fill="#dc2626">I_C 总</text>
<line x1="208" y1="302" x2="300" y2="302" stroke="#334155" stroke-width="2.5"/>
<circle cx="240" cy="302" r="4" fill="#334155"/>
<line x1="240" y1="302" x2="240" y2="366" stroke="#334155" stroke-width="1" stroke-dasharray="4,3"/>
<text x="248" y="330" font-size="11" font-weight="bold" fill="#059669">I_E1=I_B2</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DD}s" begin="-0.3s" repeatCount="indefinite" path="M122,124 L158,124"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DD}s" begin="-1.0s" repeatCount="indefinite" path="M162,154 L162,198 L206,176"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DD}s" begin="-1.7s" repeatCount="indefinite" path="M162,250 L162,276 L206,302"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DD}s" begin="-2.4s" repeatCount="indefinite" path="M210,302 L298,300"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DD}s" begin="-3.0s" repeatCount="indefinite" path="M162,328 L162,364 L118,366"/></circle>
<line x1="360" y1="80" x2="360" y2="560" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="580" y="80" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">收益 vs 三笔代价</text>
<rect x="382" y="98" width="356" height="90" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>
<text x="398" y="124" font-size="12" font-weight="bold" fill="#2563eb">收益：β 相乘</text>
<text x="398" y="148" font-size="11.5" fill="#475569">I_C2 = β₂·I_B2 = β₂·I_E1 = β₂·(1+β₁)·I_B1</text>
<text x="398" y="172" font-size="11.5" font-weight="bold" fill="#059669">β_total ≈ β₁×β₂（可达 10000+）</text>
<rect x="382" y="202" width="356" height="72" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.8"/>
<text x="398" y="228" font-size="12" font-weight="bold" fill="#b45309">代价①：V_BE 翻倍</text>
<text x="398" y="252" font-size="11.5" fill="#475569">两级各 0.7V 串联 → 约 1.4V（输入信号被抬高）</text>
<text x="398" y="268" font-size="11" fill="#475569">低压 3.3V 系统里，1.4V 的损失不可忽略</text>
<rect x="382" y="288" width="356" height="72" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.8"/>
<text x="398" y="314" font-size="12" font-weight="bold" fill="#dc2626">代价②：V_CE(sat) 升高</text>
<text x="398" y="338" font-size="11.5" fill="#475569">Q2 无法深度饱和 → 约 0.9V（普通管 0.2V）</text>
<text x="398" y="354" font-size="11" fill="#475569">所以 1A 时白白多烧 0.9W 热</text>
<rect x="382" y="374" width="356" height="72" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.8"/>
<text x="398" y="400" font-size="12" font-weight="bold" fill="#64748b">代价③：速度慢</text>
<text x="398" y="424" font-size="11.5" fill="#475569">Q1 关断时 Q2 基区电荷要多绕一圈才泄放</text>
<text x="398" y="440" font-size="11" fill="#475569">（若不想慢，可在 Rbe 上并电阻加速泄放）</text>
<text x="580" y="474" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">什么时候值得</text>
<text x="580" y="498" text-anchor="middle" font-size="11.5" fill="#475569">需要「极小基极电流驱动大负载」时：MCU 引脚直接驱动继电器/步进电机</text>
<text x="580" y="520" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#059669">经典集成件 ULN2003：7 路达林顿 + 每路自带续流二极管</text>
<text x="580" y="542" text-anchor="middle" font-size="11" fill="#475569">（它把「续流」这件事也一起做进芯片了 —— 见 3.5 的教训）</text>
{pulse(380, 372, 360, 76, '#64748b', 2.0, 10)}
<circle r="5" fill="#2563eb"><animateMotion dur="{DD}s" begin="-0.65s" repeatCount="indefinite" path="M162,154 L162,198 L206,176"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DD}s" begin="-2.05s" repeatCount="indefinite" path="M162,250 L162,276 L206,302"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DD}s" begin="-2.75s" repeatCount="indefinite" path="M210,302 L298,300"/></circle>
<circle cx="208" cy="176" r="5" fill="none" stroke="#2563eb" stroke-width="2.2"><animate attributeName="r" values="5;13;5" dur="2.2s" repeatCount="indefinite"/></circle>
<circle cx="208" cy="302" r="5" fill="none" stroke="#059669" stroke-width="2.2"><animate attributeName="r" values="5;13;5" dur="2.2s" begin="-1.1s" repeatCount="indefinite"/></circle>
<circle cx="300" cy="200" r="5" fill="none" stroke="#dc2626" stroke-width="2.2"><animate attributeName="r" values="5;13;5" dur="2.2s" begin="-0.5s" repeatCount="indefinite"/></circle>
'''
    svg += caption("① β 相乘的机理：前一级的发射极电流就是后一级的基极电流——串联放大", "#2563eb", DD,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=592)
    svg += caption("② 代价一：V_BE 翻倍到 1.4V —— 3.3V 系统里这 1.4V 的损失不可忽略", "#b45309", DD,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=592)
    svg += caption("③ 代价二：V_CE(sat) 升到 0.9V（Q2 无法深度饱和）→ 大电流时白烧热", "#dc2626", DD,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=592)
    svg += caption("④ 用武之地：μA 级驱动 A 级负载；ULN2003 把 7 路达林顿+续流管做进一颗芯片", "#059669", DD,
                   "0;0;1;1", "0;0.85;0.9;1", y=592)
    save('darlington.svg', svg + '</svg>')

# ======================= 图 76：运放选型地图（第 6 章 6.4） =======================
def make_opamp_map():
    DO = 11
    X0, Y0, PW, PH = 90, 96, 640, 300
    def px(gbw): return X0 + (np.log10(gbw)-np.log10(0.5))/(np.log10(20)-np.log10(0.5))*PW
    def py(vos): return Y0 + (np.log10(vos)-np.log10(1e-6))/(np.log10(1e-2)-np.log10(1e-6))*PH
    parts = [
        ('µA741', 1.0, 2e-3, '#94a3b8', '教学化石', 40),
        ('LM358', 1.0, 2e-3, '#2563eb', '低速信号链', -74),
        ('TL072', 3.0, 3e-3, '#059669', '音频前级', 20),
        ('NE5532', 10.0, 5e-4, '#b45309', '音频黄金标准', 60),
        ('OP07', 0.6, 7.5e-5, '#7c3aed', '直流测量', 0),
        ('斩波零漂', 2.0, 1e-6, '#dc2626', '称重/热电偶', 76),
        ('MCP6001', 1.0, 4.5e-3, '#0ea5e9', '电池 RRIO', 96),
    ]
    svg = svg_open('运放选型地图：速度（横）× 直流精度（纵）', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">越往右上越贵 —— 先问「我到底需要哪一头」</text>
<line x1="{X0}" y1="{Y0+PH}" x2="{X0+PW}" y2="{Y0+PH}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y0+PH}" stroke="#64748b" stroke-width="1.6"/>
<text x="{X0+PW}" y="{Y0+PH+24}" text-anchor="end" font-size="11" fill="#475569">GBW（速度）→</text>
<text x="{X0+10}" y="{Y0+16}" font-size="11" font-weight="bold" fill="#94a3b8">↑ 精度高</text>
<text x="{X0+10}" y="{Y0+PH-8}" font-size="11" font-weight="bold" fill="#94a3b8">↓ 精度低</text>
'''
    for g in (1, 3, 10):
        svg += f'<line x1="{px(g):.0f}" y1="{Y0+PH}" x2="{px(g):.0f}" y2="{Y0+PH+5}" stroke="#64748b" stroke-width="1.2"/>'
        svg += f'<text x="{px(g):.0f}" y="{Y0+PH+18}" text-anchor="middle" font-size="10" fill="#475569">{g}MHz</text>'
    for v, lab in ((1e-2, '10mV'), (1e-3, '1mV'), (1e-4, '100µV'), (1e-5, '10µV'), (1e-6, '1µV')):
        svg += f'<text x="{X0-6}" y="{py(v)+4:.0f}" text-anchor="end" font-size="10" fill="#475569">{lab}</text>'
    for nm, g, v, col, use, dx in parts:
        cx, cy = px(g), py(v)
        svg += f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="8" fill="{col}" opacity="0.85"/>'
        svg += f'<text x="{cx+dx:.0f}" y="{cy-13:.0f}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="{col}">{nm}</text>'
        yy = cy+24 if cy < Y0+PH-30 else cy-34
        svg += f'<text x="{cx+dx:.0f}" y="{yy:.0f}" text-anchor="middle" font-size="10" fill="#475569">{use}</text>'
    svg += f'''
<line x1="40" y1="424" x2="760" y2="424" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="450" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">两把尺子先量清楚，再挑型号</text>
<text x="70" y="478" font-size="11.5" fill="#475569">① <tspan font-weight="bold" fill="#2563eb">速度尺</tspan>：GBW ≥ 增益 × 信号最高频率 × 10（裕量十倍）。LM358 增益 100 → 只有 10kHz 带宽</text>
<text x="70" y="502" font-size="11.5" fill="#475569">② <tspan font-weight="bold" fill="#7c3aed">精度尺</tspan>：$V_{{OS}}$ 会被增益放大——2mV 失调 × 100 倍 = 输出端 200mV 误差，直流电路第一杀手</text>
<text x="70" y="528" font-size="11.5" font-weight="bold" fill="#b45309">③ 还要看 $I_B$：源阻抗 &gt;100kΩ 必须选 FET 输入（TL072 的 30pA vs LM358 的 45nA，差 1000 倍）</text>
<text x="70" y="554" font-size="11.5" fill="#475569">④ 最后才比价格与封装——<tspan font-weight="bold">先定需求，再挑型号，别反过来</tspan></text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DO}s" repeatCount="indefinite" path="M{X0},{Y0+PH-2} L{X0+PW},{Y0+PH-2}" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DO}s" begin="-1.6s" repeatCount="indefinite" path="M{X0+2},{Y0+PH} L{X0+2},{Y0}" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DO}s" begin="-0.8s" repeatCount="indefinite" path="M{X0},{Y0+PH} L{X0+PW},{Y0}" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle cx="{px(10.0):.0f}" cy="{py(5e-4):.0f}" r="5" fill="none" stroke="#b45309" stroke-width="2.2">
<animate attributeName="r" values="5;13;5" dur="1.9s" repeatCount="indefinite"/></circle>
<circle cx="{px(2.0):.0f}" cy="{py(1e-6):.0f}" r="5" fill="none" stroke="#dc2626" stroke-width="2.2">
<animate attributeName="r" values="5;13;5" dur="1.9s" begin="-0.9s" repeatCount="indefinite"/></circle>
<circle cx="{px(0.6):.0f}" cy="{py(7.5e-5):.0f}" r="5" fill="none" stroke="#7c3aed" stroke-width="2.2">
<animate attributeName="r" values="5;13;5" dur="1.9s" begin="-1.4s" repeatCount="indefinite"/></circle>
<circle cx="{px(1.0):.0f}" cy="{py(2e-3):.0f}" r="5" fill="none" stroke="#2563eb" stroke-width="2.2">
<animate attributeName="r" values="5;13;5" dur="1.9s" begin="-0.5s" repeatCount="indefinite"/></circle>
{pulse(80, 90, 660, 312, '#94a3b8', 2.2, 10)}
'''
    svg += caption("① 横轴速度、纵轴精度：先判断自己站哪个区域，再挑型号", "#2563eb", DO,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=588)
    svg += caption("② GBW 记账：增益 × 带宽 = GBW，LM358 增益 100 时只剩 10kHz", "#059669", DO,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=588)
    svg += caption("③ 精度记账：V_OS 被增益放大，2mV×100=200mV —— 直流电路先看它", "#7c3aed", DO,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=588)
    svg += caption("④ 别忘了 I_B：高源阻抗必须 FET 输入，45nA 与 30pA 差 1000 倍", "#b45309", DO,
                   "0;0;1;1", "0;0.85;0.9;1", y=588)
    save('opamp-map.svg', svg + '</svg>')

# ======================= 图 77：Datasheet 六参数优先级（第 6 章 6.3） =======================
def make_datasheet_params():
    DP = 11
    svg = svg_open('Datasheet 五十页，先读这六行', h=732)
    svg += '''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">按「会咬人」的先后排序 —— 每一项都给出它咬在哪</text>
'''
    rows = [
        ('① V_OS 输入失调', '2mV (LM358) / 75µV (OP07)', '被增益放大：×100 → 输出 200mV 误差', '直流第一杀手，看 max 不看 typ', '#7c3aed'),
        ('② I_B 输入偏置电流', '45nA (BJT) / 30pA (JFET)', '流过高源阻抗 → 变成额外失调', '源阻抗 >100kΩ 必须 FET 输入', '#2563eb'),
        ('③ GBW 增益带宽积', '1MHz (LM358) / 10MHz (NE5532)', '闭环增益 × 带宽 = GBW', '选型：≥ 增益×最高频率×10', '#059669'),
        ('④ SR 压摆率', '0.5V/µs (LM358) / 9V/µs (NE5532)', '大信号被限速 → 三角波化', '全功率带宽 = SR/(2πVp)', '#dc2626'),
        ('⑤ A_OL 开环增益', '≥100dB 常见', '太浅则闭环精度不足', '看它随频率滚降的曲线', '#b45309'),
        ('⑥ 输出摆幅 / 轨到轨', 'Vcc−1.5V (LM358)', '够不到轨 → 摆幅不够', '接近电源轨就选 RRIO', '#0ea5e9'),
    ]
    y = 82
    for name, typ, harm, tip, col in rows:
        svg += f'<rect x="40" y="{y}" width="720" height="72" rx="8" fill="#f8fafc" stroke="{col}" stroke-width="1.6"/>'
        svg += f'<text x="56" y="{y+26}" font-size="12.5" font-weight="bold" fill="{col}">{name}</text>'
        svg += f'<text x="300" y="{y+26}" font-size="11" fill="#475569">{typ}</text>'
        svg += f'<text x="56" y="{y+50}" font-size="11.5" font-weight="bold" fill="#1e293b">咬在这里：{harm}</text>'
        svg += f'<text x="56" y="{y+66}" font-size="10.5" fill="#64748b">{tip}</text>'
        y += 82
    svg += f'''
<line x1="40" y1="{y+6}" x2="760" y2="{y+6}" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="{y+34}" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">读法：先按自己的电路「会疼的地方」跳读</text>
<text x="400" y="{y+58}" text-anchor="middle" font-size="11.5" fill="#475569">直流精密 → 先看 V_OS/I_B　·　高速 → 先看 GBW/SR　·　单电源低压 → 先看共模范围与输出摆幅</text>
<text x="400" y="{y+80}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">别从头读到尾：五十页里，就这六行在决定你的电路能不能工作</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" repeatCount="indefinite" path="M50,118 L754,118 L50,118" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-1.6s" repeatCount="indefinite" path="M50,200 L754,200" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DP}s" begin="-2.4s" repeatCount="indefinite" path="M50,282 L754,282" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DP}s" begin="-3.2s" repeatCount="indefinite" path="M50,364 L754,364" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.2s" repeatCount="indefinite" path="M50,164 L750,164"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.8s" repeatCount="indefinite" path="M50,246 L750,246"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-1.4s" repeatCount="indefinite" path="M50,328 L750,328"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-2.0s" repeatCount="indefinite" path="M50,410 L750,410"/></circle>
{pulse(38, 80, 724, 76, '#7c3aed', 2.0, 10)}
'''
    svg += caption("① 第一行永远是 V_OS：它被增益放大，直流电路的头号杀手", "#7c3aed", DP,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=690)
    svg += caption("② I_B 只在「高源阻抗」时才咬人——>100kΩ 就必须换 FET 输入", "#2563eb", DP,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=690)
    svg += caption("③ GBW 与 SR 分工：小信号看 GBW、大信号看 SR（两条不同的路）", "#059669", DP,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=690)
    svg += caption("④ 读法总结：按「你电路会疼的地方」跳读，别从头翻到尾", "#b45309", DP,
                   "0;0;1;1", "0;0.85;0.9;1", y=690)
    save('datasheet-params.svg', svg + '</svg>')

# ======================= 图 78：7805/AMS1117 故障地图（第 9 章 9.4） =======================
def make_ldo_failures():
    DF = 11
    svg = svg_open('7805/AMS1117 四种翻车：每一种都能事先算出来', h=742)
    svg += '''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">线性稳压的四种死法 —— 根因都是「忘了算一笔账」</text>
'''
    cases = [
        ('① 发烫关机', '#dc2626', '线性稳压把「多余的电压」全变成热',
         'P = (Vin − 5V) × I',
         '12V→5V @300mA = 2.1W —— 无散热片必热关断',
         '降输入压差 / 加散热片 / 换 DCDC'),
        ('② 输出有 100Hz 纹波', '#b45309', '整流谷值跌破「输出+压差」',
         'V_min = V_out + V_dropout',
         '输入电容不足 → 谷值掉下去 → 调整管失去余量',
         '加大输入电容 / 核算纹波谷值'),
        ('③ AMS1117 输出振荡', '#7c3aed', '输出电容 ESR 不在规格窗口内',
         'ESR 太小或太大都会失稳',
         'LDO 的环路补偿依赖输出电容的 ESR 零点',
         '按规格书选钽电容 / 换型号'),
        ('④ 上电过冲烧后级', '#0ea5e9', '输入高压 + 快上电，调整管来不及响应',
         'di/dt 与环路响应速度赛跑',
         '输出瞬间冲高 → 打坏 3.3V 后级芯片',
         '软启动 / 选带过冲抑制的型号'),
    ]
    y = 80
    for name, col, root, formula, why, fix in cases:
        svg += f'<rect x="34" y="{y}" width="732" height="112" rx="9" fill="#f8fafc" stroke="{col}" stroke-width="1.8"/>'
        svg += f'<text x="52" y="{y+26}" font-size="13" font-weight="bold" fill="{col}">{name}</text>'
        svg += f'<text x="52" y="{y+48}" font-size="11.5" fill="#475569">根因：{root}</text>'
        svg += f'<text x="52" y="{y+72}" font-size="12" font-weight="bold" fill="{col}">{formula}</text>'
        svg += f'<text x="52" y="{y+92}" font-size="11" fill="#475569">{why}</text>'
        svg += f'<text x="52" y="{y+107}" font-size="11" font-weight="bold" fill="#059669">解法：{fix}</text>'
        svg += f'<circle cx="742" cy="{y+56}" r="6" fill="{col}" opacity="0.75"/>'
        y += 122
    svg += f'''
<line x1="34" y1="{y+4}" x2="766" y2="{y+4}" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="{y+32}" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">四种死法，一个共同教训</text>
<text x="400" y="{y+56}" text-anchor="middle" font-size="11.5" fill="#475569">线性稳压不是「接上就稳」：<tspan font-weight="bold" fill="#dc2626">压差 × 电流 = 热</tspan>、<tspan font-weight="bold" fill="#b45309">输入谷值 ≥ 输出 + 压差</tspan>、</text>
<text x="400" y="{y+78}" text-anchor="middle" font-size="11.5" fill="#475569"><tspan font-weight="bold" fill="#7c3aed">输出电容 ESR 在窗口内</tspan>、<tspan font-weight="bold" fill="#0ea5e9">上电斜率受控</tspan> —— 四笔账，选型时全部要过一遍</text>
<text x="400" y="{y+100}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">大压差 + 大电流 = 直接上 DCDC，别跟线性稳压较劲</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DF}s" repeatCount="indefinite" path="M48,136 L748,136" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DF}s" begin="-1.5s" repeatCount="indefinite" path="M48,258 L748,258" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DF}s" begin="-3.0s" repeatCount="indefinite" path="M48,380 L748,380" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DF}s" begin="-4.5s" repeatCount="indefinite" path="M48,502 L748,502" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DF}s" begin="-0.2s" repeatCount="indefinite" path="M48,196 L744,196"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DF}s" begin="-1.2s" repeatCount="indefinite" path="M48,318 L744,318"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DF}s" begin="-2.2s" repeatCount="indefinite" path="M48,440 L744,440"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DF}s" begin="-3.2s" repeatCount="indefinite" path="M48,562 L744,562"/></circle>
{pulse(32, 78, 736, 116, '#dc2626', 2.0, 10)}
'''
    svg += caption("① 热账：P=(Vin−Vout)×I —— 12V→5V@300mA 就是 2.1W，没有散热片必然关机", "#dc2626", DF,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=706)
    svg += caption("② 纹波账：输入谷值必须 ≥ Vout + 压差，否则 100Hz 纹波直接透到输出", "#b45309", DF,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=706)
    svg += caption("③ 稳定性账：LDO 环路靠输出电容的 ESR 零点补偿，ESR 出窗口就振荡", "#7c3aed", DF,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=706)
    svg += caption("④ 上电账：快上电 + 大压差会过冲；软启动或换型号。大压差大电流请直接上 DCDC", "#0ea5e9", DF,
                   "0;0;1;1", "0;0.85;0.9;1", y=706)
    save('ldo-failures.svg', svg + '</svg>')

# ======================= 图 79：BJT 在线速判（第 3 章 3.8） =======================
def make_bjt_diagnosis():
    DX = 11
    svg = svg_open('BJT 在线速判：三个电压，指出故障在哪', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">NPN 放大态的正常值：V_B≈0.7V、V_E≈0V、V_C 明显高于 V_B</text>
<text x="200" y="86" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">正常：三个电压都「讲道理」</text>
<line x1="80" y1="150" x2="120" y2="150" stroke="#334155" stroke-width="2"/>
{resistor_v(120, 110, 36, 'R_C')}
<circle cx="155" cy="175" r="4.5" fill="#334155"/>
<polygon points="175,150 175,200 220,175" fill="#f8fafc" stroke="#2563eb" stroke-width="2.2"/>
<text x="186" y="172" font-size="10" font-weight="bold" fill="#2563eb">Q1</text>
<line x1="120" y1="175" x2="175" y2="175" stroke="#334155" stroke-width="2"/>
<line x1="155" y1="175" x2="155" y2="175" stroke="#334155" stroke-width="2"/>
<line x1="120" y1="175" x2="120" y2="175" stroke="#334155" stroke-width="2"/>
{resistor_v(155, 210, 40, '')}
<line x1="155" y1="250" x2="155" y2="276" stroke="#334155" stroke-width="2"/>
{gnd_sym(155, 290)}
<text x="52" y="130" font-size="11.5" font-weight="bold" fill="#b45309">+12V</text>
<line x1="120" y1="90" x2="120" y2="110" stroke="#334155" stroke-width="2"/>
<line x1="70" y1="90" x2="120" y2="90" stroke="#334155" stroke-width="2"/>
<text x="240" y="150" font-size="11.5" font-weight="bold" fill="#059669">V_C = 6.0V</text>
<text x="240" y="176" font-size="11.5" font-weight="bold" fill="#059669">V_B = 0.70V</text>
<text x="240" y="202" font-size="11.5" font-weight="bold" fill="#059669">V_E = 0.00V</text>
<text x="240" y="232" font-size="11" fill="#475569">V_BE = 0.70V ✓</text>
<text x="240" y="252" font-size="11" fill="#475569">V_C 高于 V_B ✓</text>
<circle r="5" fill="#059669"><animateMotion dur="{DX}s" begin="-0.3s" repeatCount="indefinite" path="M150,152 L150,172"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DX}s" begin="-1.0s" repeatCount="indefinite" path="M152,204 L152,246"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DX}s" begin="-1.7s" repeatCount="indefinite" path="M122,92 L120,108"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DX}s" begin="-2.2s" repeatCount="indefinite" path="M424,299 L764,299" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DX}s" begin="-3.4s" repeatCount="indefinite" path="M424,451 L764,451" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(416,186,352,76,'#b45309',2.0,10)}
{pulse(416,338,352,76,'#2563eb',2.0,10)}
<polygon points="175,150 175,200 220,175" fill="none" stroke="#059669" stroke-width="2.2" opacity="0">
<animate attributeName="opacity" values="0;0.9;0" dur="2.2s" repeatCount="indefinite"/></polygon>
<line x1="408" y1="76" x2="408" y2="560" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="590" y="90" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">异常读数 → 故障定位</text>
'''
    rows = [
        ('V_BE = 0V', '发射结开路 / 基极电阻虚焊', '查 R_B 焊点与管子 B-E 通断', '#dc2626'),
        ('V_BE = 0.7V，但 V_C ≈ +12V', '集电结开路 / R_C 虚焊（无电流）', '测 R_C 两端压差；断电测集电极回路', '#b45309'),
        ('V_BE = 0.7V，但 V_C ≈ 0.2V', '管子已饱和（基极电流过大）', '加大 R_B 或查负载是否短路', '#7c3aed'),
        ('V_B ≈ 0V', '基极回路断（R_B 开路/驱动没输出）', '测 R_B 左侧（驱动端）有没有电平', '#2563eb'),
        ('V_E > V_B', '管子未导通（V_BE 反偏）/ 装反', '查极性：NPN 还是 PNP？', '#0ea5e9'),
        ('三个电压都对但发热', '功耗问题，非电气故障', '核算 P=V_CE·I_C vs 散热能力', '#059669'),
    ]
    y = 112
    for title, root, act, col in rows:
        svg += f'<rect x="420" y="{y}" width="348" height="70" rx="8" fill="#f8fafc" stroke="{col}" stroke-width="1.6"/>'
        svg += f'<text x="434" y="{y+24}" font-size="12" font-weight="bold" fill="{col}">{title}</text>'
        svg += f'<text x="434" y="{y+44}" font-size="11" fill="#475569">→ {root}</text>'
        svg += f'<text x="434" y="{y+62}" font-size="10.5" font-weight="bold" fill="#334155">动作：{act}</text>'
        y += 76
    svg += f'''
<text x="200" y="330" font-size="12" font-weight="bold" fill="#b45309">记忆法：把三个电压当「三个人」</text>
<text x="60" y="358" font-size="11" fill="#475569">B 是「咽喉」：必须比 E 高 0.7V，否则没开</text>
<text x="60" y="382" font-size="11" fill="#475569">E 是「地线延伸」：直耦时贴地，抬高=发射极电阻太大</text>
<text x="60" y="406" font-size="11" fill="#475569">C 是「结果」：高=没电流，低=饱和了</text>
<rect x="60" y="430" width="300" height="110" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.6"/>
<text x="76" y="456" font-size="11.5" font-weight="bold" fill="#b45309">为什么先量电压、不先拆管子？</text>
<text x="76" y="480" font-size="11" fill="#475569">拆焊一次就有损伤风险（尤其多层板），</text>
<text x="76" y="500" font-size="11" fill="#475569">而三个电压在线 30 秒就能测完，</text>
<text x="76" y="520" font-size="11" font-weight="bold" fill="#dc2626">能定向到「哪个回路」，再动手。</text>
{pulse(416, 110, 352, 76, '#dc2626', 2.0, 10)}
'''
    svg += caption("① 正常态：V_BE=0.7V、V_C 高于 V_B —— 两条判据同时成立才叫「放大态」", "#059669", DX,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=580)
    svg += caption("② V_BE=0.7V 但 V_C 高挂电源：说明「有基极电流、无集电极电流」→ 查集电极回路", "#b45309", DX,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=580)
    svg += caption("③ 三个电压一量就能定向到回路——先测后拆，是最省时间的排故顺序", "#2563eb", DX,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=580)
    svg += caption("④ 电压全对却烫手：那是散热账（P=V_CE·I_C），不是电气故障", "#dc2626", DX,
                   "0;0;1;1", "0;0.85;0.9;1", y=580)
    save('bjt-diagnosis.svg', svg + '</svg>')

# ======================= 图 80：运放六个经典坑（第 6 章 6.6） =======================
def make_opamp_pitfalls():
    DO = 11
    svg = svg_open('运放的六个经典坑：每一个都能复现、都能预防', h=762)
    svg += '''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">症状 → 根因 → 解法，按现场出现频率排序</text>
'''
    pits = [
        ('输出锁定在电源轨', '#dc2626', '输入超共模范围 / 反相端反馈开路',
         '查共模范围（LM358 是 0~Vcc−1.5V）；查反馈电阻焊接'),
        ('相位反转（跳到相反轨）', '#b45309', '老式运放输入超共模时内部结正偏',
         '选带相位反转保护的型号；输入端限幅/钳位'),
        ('高频自激振荡', '#7c3aed', '驱动容性负载（长电缆）破坏相位裕度',
         '输出串 10~100Ω 隔离电阻 —— 最常用的急救措施'),
        ('输出三角波化', '#2563eb', 'SR 不足（大信号被限速）',
         '降幅度或换高速运放；算 f_max = SR/(2πVp)'),
        ('直流误差超标', '#059669', 'V_OS×增益；I_B×源阻抗',
         '换精密运放（OP07/斩波）；降低源阻抗'),
        ('微音效应/杂音', '#0ea5e9', '高增益受振动（陶瓷电容压电效应）',
         '换 C0G 电容；减振布局；避免机械应力'),
    ]
    y = 82
    for name, col, root, fix in pits:
        svg += f'<rect x="40" y="{y}" width="720" height="80" rx="9" fill="#f8fafc" stroke="{col}" stroke-width="1.6"/>'
        svg += f'<text x="58" y="{y+28}" font-size="12.5" font-weight="bold" fill="{col}">⚠ {name}</text>'
        svg += f'<text x="58" y="{y+52}" font-size="11" fill="#475569">根因：{root}</text>'
        svg += f'<text x="58" y="{y+70}" font-size="11" font-weight="bold" fill="#334155">解法：{fix}</text>'
        svg += f'<circle cx="742" cy="{y+40}" r="5" fill="{col}" opacity="0.8"/>'
        y += 88
    svg += f'''
<line x1="40" y1="{y+2}" x2="760" y2="{y+2}" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="{y+30}" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">三条「先量后换」的诊断动作</text>
<text x="400" y="{y+54}" text-anchor="middle" font-size="11.5" fill="#475569">① 先看<b>输出直流电平</b>：贴轨 → 查共模范围与反馈回路；居中但抖 → 查自激与去耦</text>
<text x="400" y="{y+76}" text-anchor="middle" font-size="11.5" fill="#475569">② 再看<b>输入端电压差</b>：虚短失效（差几百 mV）→ 反馈断了；差几 µV → 正常工作</text>
<text x="400" y="{y+98}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">③ 最后才怀疑运放本身——绝大多数「运放坏了」其实是外围（反馈、去耦、负载）</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DO}s" repeatCount="indefinite" path="M52,118 L748,118" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DO}s" begin="-1.5s" repeatCount="indefinite" path="M52,206 L748,206" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DO}s" begin="-3.0s" repeatCount="indefinite" path="M52,294 L748,294" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DO}s" begin="-4.5s" repeatCount="indefinite" path="M52,382 L748,382" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DO}s" begin="-6.0s" repeatCount="indefinite" path="M52,470 L748,470" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DO}s" begin="-7.5s" repeatCount="indefinite" path="M52,558 L748,558" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(38,432,724,84,'#059669',2.0,10)}
{pulse(38, 80, 724, 84, '#dc2626', 2.0, 10)}
'''
    svg += caption("① 输出贴轨是最高频故障：先查共模范围与反馈回路，别急着换运放", "#dc2626", DO,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=728)
    svg += caption("② 容性负载自激：输出串 10~100Ω 隔离电阻是最常用的急救", "#7c3aed", DO,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=728)
    svg += caption("③ 三角波化 = SR 不足；直流误差 = V_OS×增益 —— 两笔账都能提前算", "#2563eb", DO,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=728)
    svg += caption("④ 诊断顺序：输出电平 → 输入端压差 → 最后才怀疑运放本身", "#b45309", DO,
                   "0;0;1;1", "0;0.85;0.9;1", y=728)
    save('opamp-pitfalls.svg', svg + '</svg>')

# ======================= 图 81：比较器五个坑（第 7 章 7.4） =======================
def make_comparator_pitfalls():
    DC = 11
    svg = svg_open('比较器的五个坑：忘了上拉排第一', h=732)
    svg += '''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">LM393 是开集电极输出 —— 一半的「故障」都源于这件事</text>
'''
    pits = [
        ('输出一直为低', '#dc2626', 'LM393 忘接上拉电阻（开集电极只会拉低）',
         '输出加合适上拉 —— 没上拉，截止电位不受保证', '最高频'),
        ('阈值附近连发误触发', '#b45309', '无迟滞 + 输入噪声（信号在阈值上抖动）',
         '加正反馈迟滞（见 7.3）；输入端并小电容', '经典'),
        ('高频自激', '#7c3aed', '输出线耦合回输入（布线寄生）',
         '输入/输出走线远离；地平面隔离；串小电阻', '布线问题'),
        ('判决点偏移', '#2563eb', '输入源阻抗过高，I_B 压降改变阈值',
         '降低源阻抗；两输入端加对称补偿电阻', '精度问题'),
        ('上电瞬间误输出', '#059669', '电源爬升期内部状态未定',
         '加 RC 延时；或选带 POR（上电复位）的型号', '启动问题'),
    ]
    y = 84
    for name, col, root, fix, tag in pits:
        svg += f'<rect x="40" y="{y}" width="720" height="88" rx="9" fill="#f8fafc" stroke="{col}" stroke-width="1.6"/>'
        svg += f'<text x="58" y="{y+28}" font-size="12.5" font-weight="bold" fill="{col}">⚠ {name}</text>'
        svg += f'<text x="640" y="{y+28}" font-size="10.5" font-weight="bold" fill="{col}">[{tag}]</text>'
        svg += f'<text x="58" y="{y+52}" font-size="11" fill="#475569">根因：{root}</text>'
        svg += f'<text x="58" y="{y+74}" font-size="11" font-weight="bold" fill="#334155">解法：{fix}</text>'
        y += 96
    svg += f'''
<line x1="40" y1="{y+2}" x2="760" y2="{y+2}" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="{y+30}" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">开集电极这件事，一次说清</text>
<text x="400" y="{y+54}" text-anchor="middle" font-size="11.5" fill="#475569">开集电极输出 = 一只对地开关。<b>没有上拉就没有高电平</b>，而高电平的值由「上拉接到哪」决定 → 天然电平转换。</text>
<text x="400" y="{y+76}" text-anchor="middle" font-size="11.5" fill="#475569">多个开集电极输出可并联 = <b>线与</b>：谁拉低谁说了算 —— 窗口检测器就这么搭。</text>
<text x="400" y="{y+98}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">上拉取值要算：t_r≈0.8473·R·C（见 5.3），I²C 标准模式 R≤11.8kΩ</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DC}s" repeatCount="indefinite" path="M52,128 L748,128" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DC}s" begin="-1.5s" repeatCount="indefinite" path="M52,224 L748,224" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#7c3aed"><animateMotion dur="{DC}s" begin="-3.0s" repeatCount="indefinite" path="M52,320 L748,320" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DC}s" begin="-4.5s" repeatCount="indefinite" path="M52,416 L748,416" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DC}s" begin="-6.0s" repeatCount="indefinite" path="M52,512 L748,512" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(38,84,724,92,'#b45309',2.0,10)}
{pulse(38,276,724,92,'#7c3aed',2.0,10)}
{pulse(38, 82, 724, 92, '#dc2626', 2.0, 10)}
'''
    svg += caption("① 先查上拉：开集电极只能拉低，截止后的电位需要外部确定", "#dc2626", DC,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=690)
    svg += caption("② 阈值附近误触发：不是比较器坏，是缺迟滞——加正反馈造免疫区", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=690)
    svg += caption("③ 自激多是布线问题：输入输出走线远离、地平面隔离", "#7c3aed", DC,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=690)
    svg += caption("④ 记住开集电极的三个红利与一个义务：能转换电平/能与线/能当使能 —— 但必须给上拉", "#059669", DC,
                   "0;0;1;1", "0;0.85;0.9;1", y=690)
    save('comparator-pitfalls.svg', svg + '</svg>')

# ======================= 图 82：555 参数与三个坑（第 10 章 10.3） =======================
def make_555_params():
    DP = 11
    svg = svg_open('555 参数与三个坑：5 脚不能悬空', h=620)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">双极版 vs CMOS 版 —— 同一功能，两套代价</text>
<rect x="60" y="76" width="330" height="150" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>
<text x="225" y="102" text-anchor="middle" font-size="13" font-weight="bold" fill="#2563eb">双极版 NE555</text>
<text x="76" y="130" font-size="11.5" fill="#475569">电源</text>
<text x="374" y="130" text-anchor="end" font-size="11.5" font-weight="bold" fill="#2563eb">4.5 ~ 16V</text>
<text x="76" y="156" font-size="11.5" fill="#475569">输出电流</text>
<text x="374" y="156" text-anchor="end" font-size="11.5" font-weight="bold" fill="#059669">200mA（可直接驱动继电器）</text>
<text x="76" y="182" font-size="11.5" fill="#475569">静态功耗</text>
<text x="374" y="182" text-anchor="end" font-size="11.5" font-weight="bold" fill="#dc2626">大（mA 级）</text>
<text x="76" y="208" font-size="11.5" fill="#475569">输出摆幅</text>
<text x="374" y="208" text-anchor="end" font-size="11.5" font-weight="bold" fill="#dc2626">非轨到轨（约 Vcc−1.7V）</text>
<rect x="410" y="76" width="330" height="150" rx="9" fill="#ecfdf5" stroke="#059669" stroke-width="1.8"/>
<text x="575" y="102" text-anchor="middle" font-size="13" font-weight="bold" fill="#059669">CMOS 版 TLC555/LMC555</text>
<text x="426" y="130" font-size="11.5" fill="#475569">电源</text>
<text x="724" y="130" text-anchor="end" font-size="11.5" font-weight="bold" fill="#059669">2 ~ 15V</text>
<text x="426" y="156" font-size="11.5" fill="#475569">输出电流</text>
<text x="724" y="156" text-anchor="end" font-size="11.5" font-weight="bold" fill="#dc2626">小（驱动能力弱）</text>
<text x="426" y="182" font-size="11.5" fill="#475569">静态功耗</text>
<text x="724" y="182" text-anchor="end" font-size="11.5" font-weight="bold" fill="#059669">极低（µA 级）</text>
<text x="426" y="208" font-size="11.5" fill="#475569">输出摆幅</text>
<text x="724" y="208" text-anchor="end" font-size="11.5" font-weight="bold" fill="#059669">接近轨到轨</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DP}s" repeatCount="indefinite" path="M75,140 L370,140" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DP}s" begin="-1.4s" repeatCount="indefinite" path="M425,140 L720,140" keyPoints="0;1" keyTimes="0;1"/></circle>
<text x="400" y="252" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309">选型一句话</text>
<text x="400" y="276" text-anchor="middle" font-size="11.5" fill="#475569">要直接驱动（继电器/蜂鸣器）→ 双极版；要低功耗/电池供电 → CMOS 版</text>
<line x1="40" y1="296" x2="760" y2="296" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="324" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">三个坑</text>
'''
    pits = [
        ('① 5 脚（CTRL）悬空 → 频率漂移', '#dc2626',
         'CTRL 直接接到内部 2/3Vcc 分压点，悬空等于天线，拾取的干扰直接改变阈值',
         '标准做法：5 脚接 10nF 到地（这是所有 555 datasheet 的推荐电路）'),
        ('② 输出驱动容性负载 → 振荡', '#7c3aed',
         '输出级推挽 + 电容负载 = 相位裕度被破坏（同类问题见 6.6 运放自激）',
         '串 10~100Ω 隔离电阻；或减小负载电容'),
        ('③ 双极版电源毛刺 → 误触发', '#b45309',
         '输出翻转瞬间 200mA 级电流冲击电源，毛刺经电源耦合回内部比较器',
         '电源就近加 100nF 陶瓷 + 10µF 电解；5 脚那个 10nF 也顺带滤波'),
    ]
    y = 344
    for name, col, root, fix in pits:
        svg += f'<rect x="40" y="{y}" width="720" height="76" rx="9" fill="#f8fafc" stroke="{col}" stroke-width="1.6"/>'
        svg += f'<text x="58" y="{y+26}" font-size="12.5" font-weight="bold" fill="{col}">{name}</text>'
        svg += f'<text x="58" y="{y+48}" font-size="11" fill="#475569">根因：{root}</text>'
        svg += f'<text x="58" y="{y+68}" font-size="11" font-weight="bold" fill="#334155">解法：{fix}</text>'
        y += 84
    svg += f'''
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-0.6s" repeatCount="indefinite" path="M52,380 L748,380" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-1.8s" repeatCount="indefinite" path="M52,464 L748,464" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DP}s" begin="-3.0s" repeatCount="indefinite" path="M52,548 L748,548" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(38,426,724,76,'#7c3aed',2.0,10)}
{pulse(38,510,724,76,'#b45309',2.0,10)}
{pulse(38, 342, 724, 80, '#dc2626', 2.0, 10)}
'''
    svg += caption("① 5 脚悬空是 555 最常见的翻车——标准做法接 10nF 到地", "#dc2626", DP,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=604)
    svg += caption("② 输出带容性负载会振荡：串 10~100Ω —— 与运放自激同一套机理", "#7c3aed", DP,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=604)
    svg += caption("③ 双极版 200mA 翻转会打电源：就近 100nF + 10µF 是必需品", "#b45309", DP,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=604)
    svg += caption("④ 选型：要驱动能力选双极、要低功耗选 CMOS —— 参数表第二页就有答案", "#059669", DP,
                   "0;0;1;1", "0;0.85;0.9;1", y=604)
    save('ne555-params.svg', svg + '</svg>')

# ======================= 图 83：恒压源与恒流源（第 0 章 0.6） =======================
def make_source_types():
    DS = 11
    svg = svg_open('恒压源与恒流源：电源的两种性格', h=640)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">横轴 I、纵轴 V：恒压水平、恒流竖直；斜率幅值对应输出阻抗</text>
<text x="200" y="82" text-anchor="middle" font-size="13" font-weight="bold" fill="#2563eb">① 电压源：I 怎么变，V 都不动</text>
<line x1="70" y1="290" x2="330" y2="290" stroke="#64748b" stroke-width="1.6"/>
<line x1="70" y1="110" x2="70" y2="290" stroke="#64748b" stroke-width="1.6"/>
<text x="330" y="310" text-anchor="end" font-size="10.5" fill="#475569">负载电流 I →</text>
<text x="62" y="120" text-anchor="end" font-size="10.5" fill="#475569">5.0V</text>
<text x="62" y="220" text-anchor="end" font-size="10.5" fill="#475569">4.8V</text>
<line x1="70" y1="120" x2="330" y2="120" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="70" y1="220" x2="330" y2="220" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="70" y1="120" x2="330" y2="120" stroke="#059669" stroke-width="3.5"/>
<text x="82" y="148" font-size="10.5" font-weight="bold" fill="#059669">理想：水平线</text>
<line x1="70" y1="120" x2="330" y2="220" stroke="#dc2626" stroke-width="3"/>
<text x="238" y="212" font-size="11" font-weight="bold" fill="#dc2626">实际：斜线</text>
<text x="202" y="244" font-size="10.5" fill="#475569">斜率绝对值 = 输出阻抗</text>
<text x="70" y="266" font-size="10.5" fill="#475569">0A</text>
<text x="330" y="266" text-anchor="end" font-size="10.5" fill="#475569">2A</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DS}s" repeatCount="indefinite" path="M74,120 L326,120" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DS}s" begin="-1.4s" repeatCount="indefinite" path="M72,121 L328,219" keyPoints="0;1" keyTimes="0;1"/></circle>
<line x1="420" y1="76" x2="420" y2="356" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="600" y="82" text-anchor="middle" font-size="13" font-weight="bold" fill="#7c3aed">② 电流源：V 怎么变，I 都不动</text>
<line x1="470" y1="290" x2="730" y2="290" stroke="#64748b" stroke-width="1.6"/>
<line x1="470" y1="110" x2="470" y2="290" stroke="#64748b" stroke-width="1.6"/>
<text x="730" y="330" text-anchor="end" font-size="10.5" fill="#475569">负载电流 I →</text>
<text x="462" y="124" text-anchor="end" font-size="10.5" fill="#475569">10V</text>
<text x="462" y="294" text-anchor="end" font-size="10.5" fill="#475569">0V</text>
<text x="470" y="310" font-size="10.5" fill="#475569">0.99mA</text>
<text x="730" y="310" text-anchor="end" font-size="10.5" fill="#475569">1.00mA</text>
<line x1="470" y1="120" x2="730" y2="120" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="470" y1="200" x2="730" y2="200" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="730" y1="120" x2="730" y2="290" stroke="#059669" stroke-width="3.5"/>
<text x="478" y="104" font-size="11" font-weight="bold" fill="#059669">理想：竖线（任何电压都 1mA）</text>
<line x1="730" y1="290" x2="704" y2="120" stroke="#dc2626" stroke-width="3" stroke-dasharray="8,4"/>
<text x="478" y="246" font-size="10.5" font-weight="bold" fill="#dc2626">实际：近竖直（Ro=10MΩ，电流微降）</text>
<circle r="5" fill="#f59e0b"><animateMotion dur="{DS}s" begin="-0.7s" repeatCount="indefinite" path="M730,286 L730,124" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DS}s" begin="-2.1s" repeatCount="indefinite" path="M730,288 L704,122" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DS}s" begin="-2.8s" repeatCount="indefinite" path="M326,120 L74,120" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#2563eb"><animateMotion dur="{DS}s" begin="-3.5s" repeatCount="indefinite" path="M730,124 L730,286" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(66,112,268,182,'#2563eb',2.4,10)}
{pulse(466,112,268,182,'#7c3aed',2.4,10)}
<text x="200" y="348" text-anchor="middle" font-size="12" font-weight="bold" fill="#059669">斜率幅值越小 = 内阻越小 = 越「恒压」</text>
<text x="600" y="348" text-anchor="middle" font-size="12" font-weight="bold" fill="#7c3aed">斜率幅值越大 = 输出阻抗越大 = 越「恒流」</text>
<line x1="40" y1="372" x2="760" y2="372" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="400" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">算一笔：内阻怎么毁掉「恒压」</text>
<rect x="40" y="416" width="352" height="70" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.6"/>
<text x="56" y="440" font-size="11.5" font-weight="bold" fill="#2563eb">实验室电源：Zout ≈ 1mΩ</text>
<text x="56" y="462" font-size="11.5" fill="#475569">5A 时跌 5mV（0.1%）→ 基本可以当恒压源</text>
<text x="56" y="480" font-size="10.5" fill="#475569">ΔV = I × Zout = 5A × 1mΩ = 5mV</text>
<rect x="408" y="416" width="352" height="70" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.6"/>
<text x="424" y="440" font-size="11.5" font-weight="bold" fill="#dc2626">劣质适配器：Zout ≈ 100mΩ</text>
<text x="424" y="462" font-size="11.5" fill="#475569">2A 时跌 200mV（4%）→ 负载一重电压就塌</text>
<text x="424" y="480" font-size="10.5" fill="#475569">ΔV = 2A × 100mΩ = 200mV</text>
<rect x="40" y="498" width="720" height="76" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.6"/>
<text x="56" y="522" font-size="12" font-weight="bold" fill="#b45309">对偶关系（记住这张表，两个概念就不会混）</text>
<text x="56" y="546" font-size="11" fill="#475569">电压源：短路是灾难 / 开路正常 / 负载<b>并联</b>接（各自取电流）　‖　电流源：开路是灾难 / 短路正常 / 负载<b>串联</b>接（同一电流穿过）</text>
<text x="56" y="566" font-size="11.5" font-weight="bold" fill="#059669">实际元件：温度传感器激励、LED 驱动要「恒流」；供电、基准要「恒压」——同一套元件，两种用法</text>
'''
    svg += caption("① 横 I 纵 V：电压源是水平线，电流变化时端电压不动", "#2563eb", DS,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=612)
    svg += caption("② 横 I 纵 V：电流源是竖线，电压变化时电流不动——输出阻抗高", "#7c3aed", DS,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=612)
    svg += caption("③ 内阻是唯一变量：1mΩ 是恒压源、100mΩ 就是「会塌的电源」——两个都能现场算", "#dc2626", DS,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=612)
    svg += caption("④ 唯一真源是「恒压源」：恒流源都是拿恒压源 + 负反馈做出来的（见 13.5）", "#b45309", DS,
                   "0;0;1;1", "0;0.85;0.9;1", y=612)
    save('source-types.svg', svg + '</svg>')

# ======================= 图 84：戴维南与诺顿等效（第 1 章 1.4） =======================
def make_thevenin():
    DT = 11
    svg = svg_open('戴维南与诺顿：任何线性网络，都能压成两个元件', h=640)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">看着复杂，其实只需知道「开路电压」与「内阻」</text>
<text x="140" y="86" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#2563eb">原网络</text>
<line x1="60" y1="120" x2="220" y2="120" stroke="#334155" stroke-width="2.5"/>
<circle cx="140" cy="120" r="4.5" fill="#334155"/>
<text x="126" y="112" font-size="11" font-weight="bold" fill="#b45309">12V</text>
<line x1="140" y1="120" x2="140" y2="146" stroke="#334155" stroke-width="2.5"/>
{resistor_v(140, 146, 40, 'R1 10k')}
<circle cx="140" cy="206" r="4.5" fill="#334155"/>
<line x1="140" y1="206" x2="140" y2="230" stroke="#334155" stroke-width="2.5"/>
{resistor_v(140, 230, 40, 'R2 10k')}
<line x1="140" y1="290" x2="140" y2="310" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(140, 324)}
<line x1="140" y1="206" x2="240" y2="206" stroke="#334155" stroke-width="2.5"/>
<circle cx="240" cy="206" r="4.5" fill="#334155"/>
<circle cx="240" cy="290" r="4.5" fill="#334155"/>
<line x1="240" y1="206" x2="240" y2="290" stroke="#94a3b8" stroke-width="1.6" stroke-dasharray="5,4"/>
<text x="252" y="200" font-size="10.5" fill="#475569">输出端</text>
<text x="252" y="322" font-size="10.5" fill="#475569">输出端（看进去）</text>
<circle r="5" fill="#2563eb"><animateMotion dur="{DT}s" begin="-0.3s" repeatCount="indefinite" path="M60,120 L200,120 L140,122 L140,144"/></circle>
<circle r="4.5" fill="#059669"><animateMotion dur="{DT}s" begin="-0.9s" repeatCount="indefinite" path="M450,110 L450,240"/></circle>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="3.6s" repeatCount="indefinite" path="M580,180 m-17,0 a17,17 0 1,0 34,0 a17,17 0 1,0 -34,0"/></circle>
<circle r="4.5" fill="#f59e0b"><animateMotion dur="{DT}s" begin="-2.2s" repeatCount="indefinite" path="M142,208 L236,208 L236,286"/></circle>
<circle r="5" fill="#059669"><animateMotion dur="{DT}s" begin="-1.1s" repeatCount="indefinite" path="M142,208 L142,228"/></circle>
<text x="400" y="200" text-anchor="middle" font-size="26" font-weight="bold" fill="#94a3b8">⇒</text>
<text x="400" y="228" text-anchor="middle" font-size="11" fill="#64748b">只看这两个数</text>
<line x1="286" y1="140" x2="286" y2="256" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="480" y="86" text-anchor="middle" font-size="12" font-weight="bold" fill="#059669">戴维南 = 电压源 + 串电阻</text>
<line x1="430" y1="150" x2="470" y2="150" stroke="#334155" stroke-width="2.5"/>
<circle cx="450" cy="150" r="4.5" fill="#334155"/>
<line x1="450" y1="120" x2="450" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="436" y1="120" x2="464" y2="120" stroke="#059669" stroke-width="3.2"/>
<line x1="436" y1="132" x2="464" y2="132" stroke="#059669" stroke-width="3.2"/>
<line x1="450" y1="132" x2="450" y2="108" stroke="#334155" stroke-width="2.5"/>
<line x1="450" y1="150" x2="450" y2="176" stroke="#334155" stroke-width="2.5"/>
<rect x="432" y="176" width="36" height="26" rx="4" fill="#f8fafc" stroke="#2563eb" stroke-width="2.2"/>
<text x="450" y="194" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#2563eb">5k</text>
<line x1="450" y1="202" x2="450" y2="240" stroke="#334155" stroke-width="2.5"/>
<text x="470" y="122" font-size="12" font-weight="bold" fill="#059669">V_th = 6V<animate attributeName="opacity" values="1;0.45;1" dur="2.6s" repeatCount="indefinite"/></text>
<text x="470" y="192" font-size="12" font-weight="bold" fill="#2563eb">R_th = 5kΩ<animate attributeName="opacity" values="1;0.45;1" dur="2.6s" repeatCount="indefinite"/></text>
<text x="680" y="86" text-anchor="middle" font-size="12" font-weight="bold" fill="#7c3aed">诺顿 = 电流源 + 并电阻</text>
<line x1="620" y1="120" x2="620" y2="240" stroke="#334155" stroke-width="2.5"/>
<circle cx="620" cy="120" r="4.5" fill="#334155"/>
<circle cx="620" cy="240" r="4.5" fill="#334155"/>
<circle cx="580" cy="180" r="15" fill="none" stroke="#7c3aed" stroke-width="2.4"/>
<line x1="580" y1="172" x2="580" y2="192" stroke="#7c3aed" stroke-width="2.4"/>
<path d="M584,176 L584,184 M578,180 L580,180 M592,180 L620,180" fill="none" stroke="#7c3aed" stroke-width="2.2"/>
<line x1="580" y1="180" x2="574" y2="180" stroke="#7c3aed" stroke-width="2.2"/>
<line x1="620" y1="180" x2="620" y2="240" stroke="#334155" stroke-width="2.5"/>
<text x="640" y="150" font-size="12" font-weight="bold" fill="#7c3aed">I_N = 1.2mA<animate attributeName="opacity" values="1;0.45;1" dur="2.6s" repeatCount="indefinite"/></text>
<text x="640" y="222" font-size="12" font-weight="bold" fill="#2563eb">R_N = 5kΩ</text>
<text x="400" y="278" text-anchor="middle" font-size="12" font-weight="bold" fill="#b45309">两个等效互换：R_th = R_N = V_th / I_N</text>
<text x="400" y="302" text-anchor="middle" font-size="11.5" fill="#475569">6V ÷ 1.2mA = 5kΩ（I_N 就是输出短路电流）</text>
<line x1="40" y1="330" x2="760" y2="330" stroke="#cbd5e1" stroke-width="1"/>
<text x="400" y="356" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">怎么求：两条判据，一步到位</text>
<text x="60" y="384" font-size="11.5" fill="#475569">① <tspan font-weight="bold" fill="#059669">开路电压 V_th</tspan>：把负载拿掉，量输出端电压 → 这里 12V × 10k/(10k+10k) = <tspan font-weight="bold">6V</tspan></text>
<text x="60" y="408" font-size="11.5" fill="#475569">② <tspan font-weight="bold" fill="#7c3aed">短路电流 I_N</tspan>：输出端短路，算流过电流 → 12V / 10k = <tspan font-weight="bold">1.2mA</tspan>（R2 被短路）</text>
<text x="60" y="432" font-size="11.5" fill="#475569">③ <tspan font-weight="bold" fill="#2563eb">R_th = V_th / I_N</tspan>：把独立源「置零」再求等效电阻也行（电压源短路 → R1∥R2 = 5kΩ）</text>
<rect x="60" y="452" width="340" height="96" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.6"/>
<text x="76" y="476" font-size="12" font-weight="bold" fill="#2563eb">等效之后，带载误差一眼看出</text>
<text x="76" y="500" font-size="11" fill="#475569">V_out = V_th × R_L/(R_th+R_L)</text>
<text x="76" y="520" font-size="11" fill="#475569">R_L = R_th 时 → 只剩一半（3V）</text>
<text x="76" y="540" font-size="11" fill="#475569">R_L = 1MΩ 时 → 5.97V（只差 0.5%）</text>
<rect x="420" y="452" width="340" height="96" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.6"/>
<text x="436" y="476" font-size="12" font-weight="bold" fill="#b45309">为什么它是「万能钥匙」</text>
<text x="436" y="500" font-size="11" fill="#475569">不管原网络有 5 个还是 50 个元件，从任意两个</text>
<text x="436" y="520" font-size="11" fill="#475569">端子看进去都只剩「一个源 + 一个电阻」——</text>
<text x="436" y="540" font-size="11.5" font-weight="bold" fill="#dc2626">所以「带不动」永远只需比 R_th 与 R_L</text>
'''
    svg += caption("① 开路电压、短路电流，两个数就定下整个网络的对外性格", "#2563eb", DT,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=612)
    svg += caption("② 戴维南与诺顿是对偶：一个电压源串电阻，一个电流源并电阻", "#7c3aed", DT,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=612)
    svg += caption("③ 换算只需一个式子：R_th = V_th / I_N = 6V / 1.2mA = 5kΩ", "#059669", DT,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=612)
    svg += caption("④ 用途：判断「带不带得动」只需比 R_th 与 R_L —— 回溯 0.3 分压器与 0.6 恒压源", "#b45309", DT,
                   "0;0;1;1", "0;0.85;0.9;1", y=612)
    save('thevenin-norton.svg', svg + '</svg>')

# ======================= 图 85：恒流源的合规电压（第 13 章 13.5） =======================
def make_compliance_voltage():
    DC = 11
    svg = svg_open('恒流源也有天花板：合规电压算给你看', h=640)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">恒流源不是「万能」——负载太重，它就撑不住了</text>
<line x1="90" y1="86" x2="90" y2="120" stroke="#334155" stroke-width="2.5"/>
<text x="76" y="82" font-size="11.5" font-weight="bold" fill="#b45309">Vs 2.8V</text>
<line x1="90" y1="120" x2="330" y2="120" stroke="#334155" stroke-width="2.5"/>
<rect x="140" y="150" width="96" height="52" rx="6" fill="#f8fafc" stroke="#7c3aed" stroke-width="2.4"/>
<text x="188" y="172" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#7c3aed">恒流源</text>
<text x="188" y="190" text-anchor="middle" font-size="10.5" fill="#475569">I = 1mA</text>
<line x1="188" y1="120" x2="188" y2="150" stroke="#334155" stroke-width="2.5"/>
<line x1="188" y1="202" x2="188" y2="232" stroke="#334155" stroke-width="2.5"/>
<rect x="170" y="232" width="36" height="24" rx="4" fill="#fffbeb" stroke="#b45309" stroke-width="2.2"/>
<text x="220" y="248" font-size="10.5" font-weight="bold" fill="#b45309">R_sense 100</text>
<line x1="188" y1="256" x2="188" y2="286" stroke="#334155" stroke-width="2.5"/>
<rect x="150" y="286" width="76" height="52" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2.4"/>
<text x="188" y="308" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#2563eb">负载 R_L</text>
<text x="188" y="326" text-anchor="middle" font-size="10.5" fill="#475569">0 ~ 2kΩ</text>
<line x1="188" y1="338" x2="188" y2="362" stroke="#334155" stroke-width="2.5"/>
{gnd_sym(188, 376)}
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DC}s" begin="-0.3s" repeatCount="indefinite" path="M190,122 L190,148"/></circle>
<circle r="4.5" fill="#b45309"><animateMotion dur="{DC}s" begin="-1.0s" repeatCount="indefinite" path="M190,204 L190,230"/></circle>
<circle r="4.5" fill="#2563eb"><animateMotion dur="{DC}s" begin="-1.7s" repeatCount="indefinite" path="M190,258 L190,284"/></circle>
<circle r="4.5" fill="#334155"><animateMotion dur="{DC}s" begin="-2.4s" repeatCount="indefinite" path="M190,340 L190,360"/></circle>
<line x1="400" y1="80" x2="400" y2="560" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="590" y="96" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">合规电压：三块压降之和</text>
<rect x="424" y="112" width="330" height="140" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.6"/>
<text x="440" y="138" font-size="11.5" font-weight="bold" fill="#2563eb">V_S ≥ V_load + I×R_sense + V_drop</text>
<text x="440" y="164" font-size="11.5" fill="#475569">① 负载压降：2kΩ × 1mA = <tspan font-weight="bold">2.0V</tspan></text>
<text x="440" y="186" font-size="11.5" fill="#475569">② 采样电阻：100Ω × 1mA = <tspan font-weight="bold">0.1V</tspan></text>
<text x="440" y="208" font-size="11.5" fill="#475569">③ 调整管压差：≥ <tspan font-weight="bold">0.7V</tspan>（BJT）</text>
<text x="440" y="236" font-size="12" font-weight="bold" fill="#dc2626">合计需要 ≥ 2.8V —— 低于此值就不恒流了</text>
<text x="590" y="288" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">I-V 曲线：平坦到极限，然后塌下来</text>
<line x1="430" y1="440" x2="730" y2="440" stroke="#64748b" stroke-width="1.6"/>
<line x1="430" y1="320" x2="430" y2="440" stroke="#64748b" stroke-width="1.6"/>
<text x="730" y="460" text-anchor="end" font-size="10.5" fill="#475569">负载电压 V →</text>
<text x="422" y="330" text-anchor="end" font-size="10.5" fill="#475569">1mA</text>
<text x="422" y="440" text-anchor="end" font-size="10.5" fill="#475569">0</text>
<line x1="430" y1="336" x2="648" y2="336" stroke="#059669" stroke-width="3.2"/>
<path d="M648,336 Q664,352 672,440" fill="none" stroke="#dc2626" stroke-width="3.2"/>
<text x="440" y="326" font-size="10.5" font-weight="bold" fill="#059669">恒流区：稳稳 1mA</text>
<text x="676" y="392" font-size="10.5" font-weight="bold" fill="#dc2626">塌陷区</text>
<line x1="648" y1="320" x2="648" y2="440" stroke="#dc2626" stroke-width="1.2" stroke-dasharray="4,3"/>
<text x="590" y="478" text-anchor="middle" font-size="10.5" fill="#dc2626">2.0V 就是合规极限 → R_L,max = 2.0V/1mA = 2kΩ</text>
<circle r="5" fill="#059669"><animateMotion dur="{DC}s" begin="-0.5s" repeatCount="indefinite" path="M434,336 L644,336" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="5" fill="#dc2626"><animateMotion dur="{DC}s" begin="-1.6s" repeatCount="indefinite" path="M652,338 L670,436" keyPoints="0;1" keyTimes="0;1"/></circle>
<circle r="4.5" fill="#b45309"><animateMotion dur="{DC}s" begin="-0.8s" repeatCount="indefinite" path="M92,84 L92,118 L186,118 L186,146" keyPoints="0;1" keyTimes="0;1"/></circle>
{pulse(428,210,322,38,'#dc2626',2.6,8)}
<rect x="60" y="416" width="310" height="120" rx="8" fill="#fffbeb" stroke="#b45309" stroke-width="1.6"/>
<text x="76" y="442" font-size="11.5" font-weight="bold" fill="#b45309">换电源电压，天花板跟着变</text>
<text x="76" y="466" font-size="11" fill="#475569">V_S=2.8V → R_L,max = 2.0kΩ</text>
<text x="76" y="486" font-size="11" fill="#475569">V_S=5V → R_L,max = 4.2kΩ</text>
<text x="76" y="506" font-size="11" fill="#475569">V_S=12V → R_L,max = 11.2kΩ</text>
<text x="76" y="528" font-size="11" font-weight="bold" fill="#dc2626">要更大的负载空间？只能抬高 V_S</text>
<text x="400" y="580" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#7c3aed">工业 4~20mA 环流用 24V，就是这个道理：20mA×500Ω=10V 负载 + 采样 + 发射器裕量</text>
'''
    svg += caption("① 恒流源要「三块压降」：负载 + 采样电阻 + 调整管——缺一块就退出恒流区", "#2563eb", DC,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=612)
    svg += caption("② I-V 曲线：平坦到 2.0V（合规极限），再往下负载压降就把它拽出恒流区", "#dc2626", DC,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=612)
    svg += caption("③ 想驱动更大负载？抬高电源电压——R_L,max 与 V_S 成正比", "#b45309", DC,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=612)
    svg += caption("④ 这就解释了工业 4~20mA 环流为什么要 24V 供电——裕量是算出来的，不是拍的", "#7c3aed", DC,
                   "0;0;1;1", "0;0.85;0.9;1", y=612)
    save('compliance-voltage.svg', svg + '</svg>')

# ======================= 图 87：MOSFET 开通四拍（第 4 章 4.6） =======================
def make_mosfet_four_beats():
    """把同一次开通拆成四个能量状态：栅极电荷、沟道电流与损耗同步变化。"""
    DB = 10
    T0, T1 = 90, 760
    def tx(t):
        return T0 + t / 700 * (T1 - T0)

    vgs = [(0, 0), (150, 1.4), (400, 2.9), (560, 2.9), (700, 5.0)]
    ids = [(0, 0), (150, 0), (400, 5), (560, 5), (700, 5)]
    vds = [(0, 20), (150, 20), (400, 20), (560, 0.15), (700, 0.15)]
    pwr = [(t, vd * current) for (t, vd), (_, current) in zip(vds, ids)]

    def path(tab, ytop, ybot, vmax, color, width=2.5):
        pts = [f"{tx(t):.0f},{ybot - (value / vmax) * (ybot - ytop):.0f}" for t, value in tab]
        return ('<path d="M' + " L".join(pts) + f'" fill="none" stroke="{color}" '
                f'stroke-width="{width}" stroke-linejoin="round"/>')

    series = [
        ('#2563eb', [(t, 362 - v / 5 * 18) for t, v in vgs]),
        ('#059669', [(t, 392 - v / 5 * 18) for t, v in ids]),
        ('#dc2626', [(t, 422 - v / 20 * 18) for t, v in vds]),
        ('#b45309', [(t, 452 - p / 100 * 18) for t, p in pwr]),
    ]
    cursor = waveform_cursor(DB, 700, series, [], T0, T1, 324, 474)

    def mini_stage(x, title, time_text, color, current_text, vds_text, vgs_text,
                   channel, current_path=None, gate_path=None):
        current = flow(current_path, DB, n=2, color="#dc2626", r=4.2) if current_path else ''
        gate = flow(gate_path, DB, n=2, color="#7c3aed", r=3.6) if gate_path else ''
        return f'''<rect x="{x}" y="70" width="174" height="214" rx="10" fill="#f8fafc" stroke="{color}" stroke-width="1.8"/>
<text x="{x+87}" y="94" text-anchor="middle" font-size="13" font-weight="bold" fill="{color}">{title}</text>
<text x="{x+87}" y="113" text-anchor="middle" font-size="10.5" fill="#475569">{time_text}</text>
<text x="{x+18}" y="134" font-size="10.5" font-weight="bold" fill="#b45309">+20V</text>
<line x1="{x+54}" y1="128" x2="{x+54}" y2="143" stroke="#334155" stroke-width="2.3"/>
<rect x="{x+43}" y="143" width="22" height="30" fill="#fffbeb" stroke="#334155" stroke-width="2.2"/>
<text x="{x+75}" y="161" font-size="10" fill="#475569">R_L=4Ω</text>
<line x1="{x+54}" y1="173" x2="{x+54}" y2="198" stroke="#334155" stroke-width="2.3"/>
<rect x="{x+39}" y="198" width="30" height="30" rx="3" fill="{channel}" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+39}" y1="198" x2="{x+39}" y2="228" stroke="#334155" stroke-width="3.4"/>
<line x1="{x+3}" y1="213" x2="{x+39}" y2="213" stroke="#334155" stroke-width="2.2"/>
<text x="{x+5}" y="234" font-size="10" font-weight="bold" fill="#7c3aed">G</text>
<line x1="{x+54}" y1="228" x2="{x+54}" y2="239" stroke="#334155" stroke-width="2.3"/>
<line x1="{x+38}" y1="239" x2="{x+70}" y2="239" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+43}" y1="245" x2="{x+65}" y2="245" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+48}" y1="251" x2="{x+60}" y2="251" stroke="#334155" stroke-width="2.5"/>
{current}{gate}
<text x="{x+87}" y="266" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">I_D：{current_text}</text>
<text x="{x+87}" y="278" text-anchor="middle" font-size="10" fill="#475569">V_DS：{vds_text} · V_GS：{vgs_text}</text>'''

    cards = stage_cards([
        mini_stage(20, '① 延时区', '0–150ns', '#64748b', '0', '20V', '0→1.4V', '#cbd5e1'),
        mini_stage(212, '② 电流上升', '150–400ns', '#b45309', '0→5A', '20V', '1.4→2.9V', '#f59e0b',
                   'M266,128 V239', 'M215,213 H251'),
        mini_stage(404, '③ Miller 平台', '400–560ns', '#7c3aed', '5A', '20→0.15V', '≈2.9V', '#7c3aed',
                   'M458,128 V239', 'M407,213 H443'),
        mini_stage(596, '④ 完全增强', '560–700ns', '#059669', '5A', '0.15V', '2.9→5V', '#059669',
                   'M650,128 V239', 'M599,213 H635'),
    ], DB)

    svg = svg_open('MOSFET 开通四拍：栅极电荷如何变成热', h=680)
    svg += f'''
<text x="400" y="51" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">20V 母线 · 5A 负载 · 10mA 驱动 · AO3400：同一条电流路径，四种状态</text>
{cards[0]}
{cards[1]}
{cards[2]}
{cards[3]}
<text x="425" y="314" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">同一次开通：四条波形共用一条时间轴</text>
<rect x="{tx(0):.0f}" y="324" width="{tx(150)-tx(0):.0f}" height="150" fill="#cbd5e1" opacity="0.18"/>
<rect x="{tx(150):.0f}" y="324" width="{tx(400)-tx(150):.0f}" height="150" fill="#f59e0b" opacity="0.13"/>
<rect x="{tx(400):.0f}" y="324" width="{tx(560)-tx(400):.0f}" height="150" fill="#7c3aed" opacity="0.13"/>
<rect x="{tx(560):.0f}" y="324" width="{tx(700)-tx(560):.0f}" height="150" fill="#059669" opacity="0.13"/>
<text x="{tx(75):.0f}" y="338" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#64748b">① 延时</text>
<text x="{tx(275):.0f}" y="338" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#b45309">② 上升</text>
<text x="{tx(480):.0f}" y="338" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#7c3aed">③ 平台</text>
<text x="{tx(630):.0f}" y="338" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#059669">④ 增强</text>
<text x="28" y="360" font-size="11" font-weight="bold" fill="#2563eb">V_GS</text>
<text x="28" y="390" font-size="11" font-weight="bold" fill="#059669">I_D</text>
<text x="28" y="420" font-size="11" font-weight="bold" fill="#dc2626">V_DS</text>
<text x="28" y="450" font-size="11" font-weight="bold" fill="#b45309">P=V·I</text>
<line x1="{T0}" y1="362" x2="{T1}" y2="362" stroke="#cbd5e1" stroke-width="1"/>
<line x1="{T0}" y1="392" x2="{T1}" y2="392" stroke="#cbd5e1" stroke-width="1"/>
<line x1="{T0}" y1="422" x2="{T1}" y2="422" stroke="#cbd5e1" stroke-width="1"/>
<line x1="{T0}" y1="452" x2="{T1}" y2="452" stroke="#cbd5e1" stroke-width="1"/>
{path(vgs, 344, 362, 5, '#2563eb')}
{path(ids, 374, 392, 5, '#059669')}
{path(vds, 404, 422, 20, '#dc2626')}
{path(pwr, 434, 452, 100, '#b45309')}
<line x1="{tx(150):.0f}" y1="324" x2="{tx(150):.0f}" y2="474" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(400):.0f}" y1="324" x2="{tx(400):.0f}" y2="474" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(560):.0f}" y1="324" x2="{tx(560):.0f}" y2="474" stroke="#7c3aed" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(700):.0f}" y1="324" x2="{tx(700):.0f}" y2="474" stroke="#059669" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{tx(150)+5:.0f}" y="488" font-size="10.5" fill="#475569">150ns</text>
<text x="{tx(400)+5:.0f}" y="488" font-size="10.5" fill="#475569">400ns</text>
<text x="{tx(560)+5:.0f}" y="488" font-size="10.5" fill="#475569">560ns</text>
<text x="{tx(700):.0f}" y="488" text-anchor="end" font-size="10.5" fill="#475569">700ns</text>
{cursor}
<rect x="22" y="515" width="756" height="87" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
<text x="40" y="540" font-size="12" font-weight="bold" fill="#2563eb">四拍账本：电流先上来，电压再掉下去，乘积才是热</text>
<text x="40" y="563" font-size="11" fill="#475569">①150ns + ②250ns + ③160ns + ④140ns = 700ns；③ 平台：Q_gd = 10mA×160ns = 1.6nC</text>
<text x="40" y="585" font-size="11" fill="#475569">稳态导通：P_cond = 5²×0.03Ω = 0.75W；保守重叠估算：P_sw≈½×20×5×700ns×100kHz≈3.5W</text>
<text x="40" y="597" font-size="10.5" font-weight="bold" fill="#dc2626">所以栅极驱动不是「有没有电压」，而是「能不能把 Q_gd 搬得足够快」</text>
'''
    svg += caption('四阶段的因果链：C_GS 先充电 → I_D 上升 → C_GD 抢走驱动电流形成平台 → R_DS(on) 降到最低', '#7c3aed', DB,
                   '0;0;1;1', '0;0.84;0.89;1', y=650, size=13.2)
    save('mosfet-four-beats.svg', svg + '</svg>')

# ======================= 图 88：整流滤波电源四拍拆解（第 2 章 2.6） =======================
def make_rectifier_filter_beats():
    """整流滤波电源四拍拆解：AC→二极管→C∥R_L，从空电容到稳态纹波。"""
    DB = 12
    T0, T1 = 80, 760
    def tx(t):
        return T0 + t / 20 * (T1 - T0)          # ms → x（20ms 线性时间轴）
    def vy(v):
        return 390 + (15.6 - v) / 2.1 * 16      # V_C：15.6V→390，13.5V→406

    def mini_stage(x, title, time_text, color, current_text, voltage_text,
                   diode_color, cap_color, flow_path=None, flow_color="#dc2626"):
        fl = flow(flow_path, DB, n=2, color=flow_color, r=4.2) if flow_path else ''
        return f'''<rect x="{x}" y="70" width="174" height="214" rx="10" fill="#f8fafc" stroke="{color}" stroke-width="1.8"/>
<text x="{x+87}" y="94" text-anchor="middle" font-size="13" font-weight="bold" fill="{color}">{title}</text>
<text x="{x+87}" y="113" text-anchor="middle" font-size="10.5" fill="#475569">{time_text}</text>
<circle cx="{x+28}" cy="152" r="12" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<path d="M{x+20},152 q4,-8 8,0 q4,8 8,0" fill="none" stroke="#2563eb" stroke-width="1.8"/>
<text x="{x+28}" y="133" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#2563eb">AC</text>
<line x1="{x+40}" y1="152" x2="{x+46}" y2="152" stroke="#334155" stroke-width="2.2"/>
<polygon points="{x+62},152 {x+46},145 {x+46},159" fill="{diode_color}"/>
<line x1="{x+62}" y1="145" x2="{x+62}" y2="159" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+62}" y1="152" x2="{x+98}" y2="152" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+98}" y1="152" x2="{x+98}" y2="164" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+86}" y1="164" x2="{x+110}" y2="164" stroke="{cap_color}" stroke-width="3"/>
<line x1="{x+86}" y1="172" x2="{x+110}" y2="172" stroke="{cap_color}" stroke-width="3"/>
<line x1="{x+98}" y1="172" x2="{x+98}" y2="190" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+98}" y1="152" x2="{x+132}" y2="152" stroke="#334155" stroke-width="2.2"/>
<rect x="{x+126}" y="157" width="12" height="26" fill="#f8fafc" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+132}" y1="152" x2="{x+132}" y2="157" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+132}" y1="183" x2="{x+132}" y2="190" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+28}" y1="164" x2="{x+28}" y2="190" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+28}" y1="190" x2="{x+132}" y2="190" stroke="#334155" stroke-width="2.2"/>
<text x="{x+113}" y="170" font-size="9" font-weight="bold" fill="#475569">C</text>
<text x="{x+146}" y="172" font-size="9" font-weight="bold" fill="#475569">R_L</text>
<text x="{x+52}" y="141" font-size="9" font-weight="bold" fill="#475569">D</text>
{fl}
<text x="{x+87}" y="266" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">I_D：{current_text}</text>
<text x="{x+87}" y="278" text-anchor="middle" font-size="10" fill="#475569">V_C：{voltage_text}</text>'''

    cards = stage_cards([
        mini_stage(20, '① 初始态', 't=0 · 上电前', '#64748b', '0', '0V',
                   '#cbd5e1', '#cbd5e1'),
        mini_stage(212, '② 浪涌充电', '第一次过峰', '#b45309', '10~50A', '0→15.6V',
                   '#f59e0b', '#f59e0b', 'M246,152 L310,152', '#dc2626'),
        mini_stage(404, '③ 峰值充电', '稳态峰顶 · 导通角~20%', '#7c3aed', '5~10A', '13.5→15.6V',
                   '#7c3aed', '#7c3aed', 'M438,152 L502,152', '#dc2626'),
        mini_stage(596, '④ 谷值放电', '稳态谷值', '#059669', '0', '15.6→13.5V',
                   '#cbd5e1', '#059669', 'M630,152 L664,152 L664,190 L630,190', '#059669'),
    ], DB)

    # ---- 波形：20ms 线性轴；|sin| 峰值在 5/15ms，纹波周期 10ms ----
    ts = np.linspace(0, 20, 97)
    ac_d = "M" + " L".join(f"{tx(t):.0f},{378 - abs(np.sin(np.pi * t / 10)) * 20:.0f}" for t in ts)
    vc_t = [0, 4.3, 5.0, 14.3, 15.0, 20]
    vc_v = [14.47, 13.5, 15.6, 13.5, 15.6, 13.87]
    vc_d = "M" + " L".join(f"{tx(t):.0f},{vy(v):.0f}" for t, v in zip(vc_t, vc_v))
    def pulse(t0):
        return (f" L{tx(t0):.0f},438 L{tx(t0 + 0.35):.0f},416 L{tx(t0 + 0.7):.0f},438")
    id_d = (f"M{T0},438 L{tx(4.3):.0f},438" + pulse(4.3)
            + f" L{tx(14.3):.0f},438" + pulse(14.3) + f" L{T1},438")

    series = [
        ('#2563eb', [(t, 378 - abs(np.sin(np.pi * t / 10)) * 20) for t in ts]),
        ('#059669', [(t, vy(v)) for t, v in zip(vc_t, vc_v)]),
        ('#dc2626', [(0, 438), (4.3, 438), (4.65, 416), (5.0, 438),
                     (14.3, 438), (14.65, 416), (15.0, 438), (20, 438)]),
    ]
    cursor = waveform_cursor(DB, 20, series, [], T0, T1, 340, 458)
    svg = svg_open('整流滤波电源四拍拆解：从空电容到稳态纹波', h=680)
    svg += f'''
<text x="400" y="51" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">12V AC（峰值 17V）· 桥式整流 · 4700µF · 1A 负载：一个周期的四拍</text>
{cards[0]}
{cards[1]}
{cards[2]}
{cards[3]}
<text x="425" y="314" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">一个周期：AC 输入、电容电压、二极管电流</text>
<rect x="{T0}" y="340" width="{T1-T0}" height="105" fill="#e2e8f0" opacity="0.15"/>
<text x="24" y="374" font-size="11" font-weight="bold" fill="#2563eb">V_AC</text>
<text x="24" y="400" font-size="11" font-weight="bold" fill="#059669">V_C</text>
<text x="24" y="432" font-size="11" font-weight="bold" fill="#dc2626">I_D</text>
<line x1="{T0}" y1="378" x2="{T1}" y2="378" stroke="#cbd5e1" stroke-width="1"/>
<line x1="{T0}" y1="406" x2="{T1}" y2="406" stroke="#cbd5e1" stroke-width="1"/>
<line x1="{T0}" y1="438" x2="{T1}" y2="438" stroke="#cbd5e1" stroke-width="1"/>
<path d="{ac_d}" fill="none" stroke="#2563eb" stroke-width="2" stroke-dasharray="5,3"/>
<path d="{vc_d}" fill="none" stroke="#059669" stroke-width="2.5"/>
<path d="{id_d}" fill="none" stroke="#dc2626" stroke-width="2.5"/>
<line x1="{tx(5):.0f}" y1="340" x2="{tx(5):.0f}" y2="445" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(10):.0f}" y1="340" x2="{tx(10):.0f}" y2="445" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(15):.0f}" y1="340" x2="{tx(15):.0f}" y2="445" stroke="#64748b" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{tx(5):.0f}" y="458" text-anchor="middle" font-size="10.5" fill="#475569">5ms</text>
<text x="{tx(10):.0f}" y="458" text-anchor="middle" font-size="10.5" fill="#475569">10ms</text>
<text x="{tx(15):.0f}" y="458" text-anchor="middle" font-size="10.5" fill="#475569">15ms</text>
<text x="{T1}" y="458" text-anchor="end" font-size="10.5" fill="#475569">20ms</text>
{cursor}
<rect x="22" y="515" width="756" height="87" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
<text x="40" y="540" font-size="12" font-weight="bold" fill="#2563eb">四拍账本：导通角只有 20%，峰值电流是负载的 5~10 倍</text>
<text x="40" y="563" font-size="11" fill="#475569">纹波 ΔV = I·Δt/C = 1A×10ms/4700µF ≈ 2.1V；峰值电流 ≈ 10ms/2ms×1A = 5A</text>
<text x="40" y="585" font-size="11" fill="#475569">所以选整流管看 I_FRM（重复峰值），不是标称平均电流——1A 电源用 1N4007 余量很紧</text>
<text x="40" y="597" font-size="10.5" font-weight="bold" fill="#dc2626">上电浪涌 10~50A → 保险丝要选慢断型（T 型）</text>
'''
    svg += caption('四拍因果链：电容充电 → 二极管截止 → 电容放电 → 再充电', '#7c3aed', DB,
                   '0;0;1;1', '0;0.84;0.89;1', y=650, size=13.2)
    save('rectifier-filter-beats.svg', svg + '</svg>')

def waveform_cursor(dur, span, series, phases, x0, x1, y0, y1):
    """时间轴共用匀速游标；series 为 (颜色, [(时刻, y)])，重复时刻表示瞬跳。"""
    svg = f'''<g transform="translate({x0},0)">
<animateTransform attributeName="transform" type="translate" values="{x0},0;{x1},0" keyTimes="0;1" calcMode="linear" dur="{dur}s" repeatCount="indefinite"/>
<line x1="0" y1="{y0}" x2="0" y2="{y1}" stroke="#64748b" stroke-width="1.2" stroke-dasharray="3,3"/>
'''
    for color, samples in series:
        times = ';'.join(f'{t / span:.9f}' for t, _ in samples)
        values = ';'.join(f'{y:.3f}' for _, y in samples)
        svg += f'''<circle class="cursor-dot" cx="0" cy="{samples[0][1]:.3f}" r="4.2" fill="{color}">
<animate attributeName="cy" values="{values}" keyTimes="{times}" calcMode="linear" dur="{dur}s" repeatCount="indefinite"/>
</circle>'''
    svg += '</g>'
    # 字幕与波形使用同一时钟；离散切换避免相邻阶段叠字。
    phase_times = ';'.join(f'{t / span:.9f}' for t, _, _ in phases) + ';1'
    for i, (_, text, color) in enumerate(phases):
        values = ['1' if j == i else '0' for j in range(len(phases))]
        values.append(values[-1])
        svg += f'''<text class="waveform-phase" x="400" y="501" text-anchor="middle" font-size="12" font-weight="bold" fill="{color}" opacity="{values[0]}">{text}
<animate attributeName="opacity" values="{';'.join(values)}" keyTimes="{phase_times}" calcMode="discrete" dur="{dur}s" repeatCount="indefinite"/></text>'''
    return svg

def _motion_path(source):
    """animateMotion 的路径字符串：可传 <path d="…"> 元素或纯 'M…' 路径。"""
    m = re.search(r'd="([^"]+)"', source)
    return m.group(1) if m else source

def plain_motion(dur, source, begin=None):
    """干净的匀速弧长 animateMotion（导线流、非时间轴曲线用）。"""
    b = f' begin="{begin}"' if begin else ''
    return (f'<animateMotion dur="{dur}s"{b} repeatCount="indefinite" '
            f'path="{_motion_path(source)}"/>')

def linear_x_motion(dur, source, begin=None, n=512):
    """时间轴波形面板用：x 随时间匀速前进。

    折线且 x 单调时按真实时刻重配 keyPoints；其余情况退回匀速弧长。"""
    path = _motion_path(source)
    pts, cur = [], None
    for cmd, nums in re.findall(r'([A-Za-z])([^A-Za-z]*)', path):
        if cmd not in 'MLHV':
            return plain_motion(dur, path, begin)
        vals = [float(v) for v in nums.replace(',', ' ').split()]
        if cmd == 'M':
            if len(vals) < 2 or len(vals) % 2:
                return plain_motion(dur, path, begin)
            cur = (vals[0], vals[1])
            pts.append(cur)
            for i in range(2, len(vals), 2):
                cur = (vals[i], vals[i + 1])
                pts.append(cur)
        elif cmd == 'L':
            if len(vals) % 2:
                return plain_motion(dur, path, begin)
            for i in range(0, len(vals), 2):
                cur = (vals[i], vals[i + 1])
                pts.append(cur)
        elif cmd == 'H':
            for v in vals:
                cur = (v, cur[1])
                pts.append(cur)
        elif cmd == 'V':
            for v in vals:
                cur = (cur[0], v)
                pts.append(cur)
    if len(pts) < 2 or any(b[0] < a[0] - 1e-9 for a, b in zip(pts, pts[1:])):
        return plain_motion(dur, path, begin)
    x0, x1 = pts[0][0], pts[-1][0]
    segs = list(zip(pts, pts[1:]))
    lens = [np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs]
    total = sum(lens)
    if total <= 0 or x1 <= x0:
        return plain_motion(dur, path, begin)
    cum, acc = [0.0], 0.0
    for ln in lens:
        acc += ln
        cum.append(acc)
    kps, k = [], 0
    for i in range(n + 1):
        xt = x0 + (x1 - x0) * i / n
        while k + 1 < len(pts) and pts[k + 1][0] <= xt + 1e-9:
            k += 1
        if k + 1 >= len(pts):
            s = cum[k]
        else:
            a, b = pts[k], pts[k + 1]
            dx = b[0] - a[0]
            s = cum[k] + (xt - a[0]) / dx * lens[k]
        kps.append(s / total)
    b = f' begin="{begin}"' if begin else ''
    kt = ';'.join(f'{i / n:.6f}' for i in range(n + 1))
    kp = ';'.join(f'{v:.6f}' for v in kps)
    return (f'<animateMotion dur="{dur}s"{b} repeatCount="indefinite" calcMode="linear" '
            f'keyTimes="{kt}" keyPoints="{kp}" path="{path}"/>')

# ======================= 图 89：模拟开关开合四拍（第 8 章 8.6） =======================
def make_analog_switch_beats():
    """模拟开关四拍：开→通（存储 Q_ch）→关（电荷注入 ΔV）→补偿（dummy 管）。"""
    DB = 12
    T0, T1 = 80, 760
    def tx(t):
        return T0 + t / 20 * (T1 - T0)      # ms → x（20ms 线性轴）

    def mini_stage(x, title, time_text, color, row1, row2, tg_fill,
                   flow_path=None, flow_color="#f59e0b", extra=''):
        fl = flow(flow_path, DB, n=2, color=flow_color, r=4.0) if flow_path else ''
        return f'''<rect x="{x}" y="70" width="174" height="214" rx="10" fill="#f8fafc" stroke="{color}" stroke-width="1.8"/>
<text x="{x+87}" y="94" text-anchor="middle" font-size="13" font-weight="bold" fill="{color}">{title}</text>
<text x="{x+87}" y="113" text-anchor="middle" font-size="10.5" fill="#475569">{time_text}</text>
<circle cx="{x+22}" cy="152" r="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="{x+22}" y="137" text-anchor="middle" font-size="9" fill="#2563eb">V_in</text>
<line x1="{x+32}" y1="152" x2="{x+50}" y2="152" stroke="#334155" stroke-width="2.2"/>
<rect x="{x+50}" y="142" width="34" height="20" rx="3" fill="{tg_fill}" stroke="#334155" stroke-width="2"/>
<text x="{x+67}" y="156" text-anchor="middle" font-size="10" font-weight="bold" fill="#1e293b">TG</text>
<line x1="{x+67}" y1="142" x2="{x+67}" y2="130" stroke="#7c3aed" stroke-width="2"/>
<text x="{x+67}" y="126" text-anchor="middle" font-size="9" font-weight="bold" fill="#7c3aed">EN</text>
<line x1="{x+84}" y1="152" x2="{x+104}" y2="152" stroke="#334155" stroke-width="2.2"/>
<circle cx="{x+104}" cy="152" r="3" fill="#334155"/>
<line x1="{x+104}" y1="152" x2="{x+104}" y2="166" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+92}" y1="166" x2="{x+116}" y2="166" stroke="#2563eb" stroke-width="3"/>
<line x1="{x+92}" y1="174" x2="{x+116}" y2="174" stroke="#2563eb" stroke-width="3"/>
<line x1="{x+104}" y1="174" x2="{x+104}" y2="186" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+92}" y1="186" x2="{x+116}" y2="186" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+97}" y1="192" x2="{x+111}" y2="192" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+101}" y1="198" x2="{x+107}" y2="198" stroke="#334155" stroke-width="2.5"/>
<text x="{x+120}" y="172" font-size="9" font-weight="bold" fill="#2563eb">C_h</text>
{extra}
{fl}
<text x="{x+87}" y="266" text-anchor="middle" font-size="10.5" font-weight="bold" fill="{color}">{row1}</text>
<text x="{x+87}" y="278" text-anchor="middle" font-size="10" fill="#475569">{row2}</text>'''

    inj = '<polygon points="500,164 495,154 505,154" fill="#dc2626"/><polygon points="516,164 511,154 521,154" fill="#dc2626"/>'
    cards = stage_cards([
        mini_stage(20, '① 开', 'EN 上升 · 几十 ns', '#64748b', 'R_on：∞→45Ω', 'Q_ch 尚未建立',
                   '#cbd5e1'),
        mini_stage(212, '② 通', '导通期 · 采样', '#059669', 'Q_ch = 0.2pC', 'V_C：跟随 2.000V',
                   '#34d399', 'M244,152 L316,152', '#f59e0b'),
        mini_stage(404, '③ 关', 'EN 下降 · 电荷注入', '#dc2626', 'ΔV = Q_ch/2C_h = 10mV', 'V_C：2.000→1.990V',
                   '#cbd5e1', extra=inj),
        mini_stage(596, '④ 补偿', 'dummy 半尺寸管', '#7c3aed', '注入反向抵消', 'ΔV → ≈0',
                   '#34d399', 'M628,152 L700,152', '#7c3aed'),
    ], DB)

    # ---- 波形：EN 高=采样(0–8ms)，低=保持；关断瞬间 V_C 下陷 10mV ----
    en_d = f"M{T0},430 L{tx(8):.0f},430 L{tx(8):.0f},452 L{T1},452"
    vc_d = f"M{T0},366 L{tx(8):.0f},366 L{tx(8):.0f},386 L{T1},392"
    vin_d = f"M{T0},366 L{T1},366"
    cursor = waveform_cursor(DB, 20, [
        ('#2563eb', [(0, 366), (8, 366), (8, 386), (20, 392)]),
        ('#7c3aed', [(0, 430), (8, 430), (8, 452), (20, 452)]),
    ], [
        (0, '采样：EN 高，V_C 跟随输入；竖游标上的两点是同一时刻', '#059669'),
        (8, '保持：EN 变低时注入 10mV 台阶，之后缓慢下垂（未补偿）', '#dc2626'),
    ], T0, T1, 340, 458)

    svg = svg_open('模拟开关开合四拍：电荷注入如何毁掉采样精度（5V 传输门）', h=680)
    svg += f'''
<text x="400" y="51" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">V_DD=5V 传输门 · C_h=10pF · 被采信号 2.000V：一个采样周期的四拍</text>
{cards[0]}
{cards[1]}
{cards[2]}
{cards[3]}
<text x="425" y="314" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">一次采样：控制信号 EN 与保持电容电压 V_C（注入台阶放大）</text>
<rect x="{T0}" y="340" width="{T1-T0}" height="118" fill="#e2e8f0" opacity="0.15"/>
<text x="24" y="370" font-size="11" font-weight="bold" fill="#2563eb">V_C</text>
<text x="24" y="444" font-size="11" font-weight="bold" fill="#7c3aed">EN</text>
<line x1="{T0}" y1="366" x2="{T1}" y2="366" stroke="#cbd5e1" stroke-width="1"/>
<path d="{vin_d}" fill="none" stroke="#94a3b8" stroke-width="1.8" stroke-dasharray="5,4"/>
<path d="{vc_d}" fill="none" stroke="#2563eb" stroke-width="2.8"/>
<path d="{en_d}" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
<line x1="{tx(8):.0f}" y1="340" x2="{tx(8):.0f}" y2="458" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{tx(8)+6:.0f}" y="356" font-size="10.5" font-weight="bold" fill="#dc2626">关断 → 注入 10mV</text>
<text x="{T0}" y="472" font-size="10.5" fill="#475569">采样相（EN 高）</text>
<text x="{tx(8)+6:.0f}" y="472" font-size="10.5" fill="#475569">保持相（EN 低）</text>
{cursor}
<rect x="22" y="515" width="756" height="87" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
<text x="40" y="540" font-size="12" font-weight="bold" fill="#2563eb">四拍账本：精度与速度，在模拟开关这一级就定死了</text>
<text x="40" y="563" font-size="11" fill="#475569">Q_ch = C_ox·W·L·(V_GS−V_TH) ≈ 0.2pC（随信号电压变化）；ΔV = Q_ch/2C_h = 0.2pC/(2×10pF) = 10mV</text>
<text x="40" y="585" font-size="11" fill="#475569">12 位 / 2.048V：1 LSB = 500µV → 10mV = 20 个 LSB！加大 C_h 到 100pF 使 ΔV→1mV，代价 τ=R_on·C_h 长 10 倍</text>
<text x="40" y="597" font-size="10.5" font-weight="bold" fill="#dc2626">对策：dummy 半尺寸管反向注入 / 加大 C_h 摊薄 / 差分结构两侧等量相消</text>
'''
    svg += caption('四拍因果链：栅极驱动开启 → 沟道存电荷 → 关断注入 C_h → dummy 管抵消', '#7c3aed', DB,
                   '0;0;1;1', '0;0.84;0.89;1', y=650, size=13.2)
    save('analog-switch-beats.svg', svg + '</svg>')

# ======================= 图 90：LDO 负载瞬态四拍（第 9 章 9.5） =======================
def make_ldo_transient_beats():
    """LDO 负载瞬态四拍：ESR 跳变 → 电容放电 → 环路接管 → 重新锁定。"""
    DB = 12
    T0, T1 = 80, 760
    def tx(t):
        return T0 + t / 50 * (T1 - T0)              # µs → x（0..50µs 线性轴）
    def vy(v):
        return 348 + (5.01 - v) / 0.31 * 80         # V_OUT：5.01V→348，4.70V→428

    def mini_stage(x, title, time_text, color, row1, row2, ldo_fill, esr_c, cap_c,
                   flow_path=None, flow_color="#dc2626"):
        fl = flow(flow_path, DB, n=2, color=flow_color, r=4.0) if flow_path else ''
        return f'''<rect x="{x}" y="70" width="174" height="214" rx="10" fill="#f8fafc" stroke="{color}" stroke-width="1.8"/>
<text x="{x+87}" y="94" text-anchor="middle" font-size="13" font-weight="bold" fill="{color}">{title}</text>
<text x="{x+87}" y="113" text-anchor="middle" font-size="10.5" fill="#475569">{time_text}</text>
<text x="{x+14}" y="131" text-anchor="middle" font-size="9" fill="#475569">V_IN</text>
<line x1="{x+12}" y1="153" x2="{x+18}" y2="153" stroke="#334155" stroke-width="2.2"/>
<rect x="{x+18}" y="138" width="44" height="30" rx="4" fill="{ldo_fill}" stroke="#334155" stroke-width="2"/>
<text x="{x+40}" y="157" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#1e293b">LDO</text>
<line x1="{x+62}" y1="153" x2="{x+92}" y2="153" stroke="#334155" stroke-width="2.2"/>
<circle cx="{x+92}" cy="153" r="3" fill="#334155"/>
<line x1="{x+92}" y1="153" x2="{x+92}" y2="162" stroke="#334155" stroke-width="2.2"/>
<rect x="{x+87}" y="162" width="10" height="7" fill="#fef2f2" stroke="{esr_c}" stroke-width="1.8"/>
<line x1="{x+92}" y1="169" x2="{x+92}" y2="174" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+80}" y1="174" x2="{x+104}" y2="174" stroke="{cap_c}" stroke-width="3"/>
<line x1="{x+80}" y1="182" x2="{x+104}" y2="182" stroke="{cap_c}" stroke-width="3"/>
<line x1="{x+92}" y1="182" x2="{x+92}" y2="190" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+82}" y1="190" x2="{x+102}" y2="190" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+87}" y1="195" x2="{x+97}" y2="195" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+92}" y1="153" x2="{x+134}" y2="153" stroke="#334155" stroke-width="2.2"/>
<rect x="{x+128}" y="158" width="12" height="24" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<line x1="{x+134}" y1="153" x2="{x+134}" y2="158" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+134}" y1="182" x2="{x+134}" y2="190" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+92}" y1="190" x2="{x+134}" y2="190" stroke="#334155" stroke-width="2.2"/>
<text x="{x+92}" y="210" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#2563eb">C_out 10µF</text>
<text x="{x+134}" y="210" text-anchor="middle" font-size="9.5" font-weight="bold" fill="#475569">R_L</text>
<text x="{x+108}" y="168" font-size="9" font-weight="bold" fill="#dc2626">ESR</text>
{fl}
<text x="{x+87}" y="266" text-anchor="middle" font-size="10.5" font-weight="bold" fill="{color}">{row1}</text>
<text x="{x+87}" y="278" text-anchor="middle" font-size="10" fill="#475569">{row2}</text>'''

    cards = stage_cards([
        mini_stage(20, '① ESR 跳变', '零延迟 · 神仙难救', '#dc2626', 'ΔV₁ = 490mA×50mΩ', '≈ 25mV',
                   '#f8fafc', '#dc2626', '#2563eb'),
        mini_stage(212, '② 电容放电', 'µs 级 · 环路未醒', '#b45309', 'ΔV₂ = I·Δt/C', '≈ 245mV',
                   '#f8fafc', '#dc2626', '#f59e0b', 'M244,174 L316,182', '#f59e0b'),
        mini_stage(404, '③ 环路接管', '误差放大器调管', '#059669', '调整管电阻↓', 'V_OUT 回升',
                   '#d1fae5', '#dc2626', '#2563eb', 'M438,153 L502,153', '#059669'),
        mini_stage(596, '④ 重新锁定', '过冲/振铃后', '#7c3aed', 'V_OUT = 5V − 负载调整率', '≈ 4.990V',
                   '#f8fafc', '#dc2626', '#2563eb'),
    ], DB)

    # ---- 波形：t=5µs 负载阶跃；ESR 瞬跳 25mV → 电容放电 245mV → 环路拉回 ----
    vout_t = [0, 5, 5, 10, 30, 50]
    vout_v = [5.000, 5.000, 4.975, 4.730, 4.990, 4.990]
    vout_d = "M" + " L".join(f"{tx(t):.0f},{vy(v):.0f}" for t, v in zip(vout_t, vout_v))
    il_d = f"M{T0},462 L{tx(5):.0f},462 L{tx(5):.0f},436 L{T1},436"
    ref_y = f"{vy(5.000):.0f}"
    cursor = waveform_cursor(DB, 50, [
        ('#2563eb', [(t, vy(v)) for t, v in zip(vout_t, vout_v)]),
        ('#b45309', [(0, 462), (5, 462), (5, 436), (50, 436)]),
    ], [
        (0, '阶跃前：负载 10mA，输出 5V；竖游标上的两点是同一时刻', '#64748b'),
        (5, '电容支撑：ESR 先跳 25mV，再随电容放电继续下降', '#b45309'),
        (10, '环路接管：调整管加大供电，输出从谷底回升', '#059669'),
        (30, '重新稳定：负载保持 500mA，输出约 4.990V（示意）', '#7c3aed'),
    ], T0, T1, 336, 466)

    svg = svg_open('LDO 负载瞬态四拍：一次唤醒为何把 MCU 打到复位（AMS1117-5V）', h=680)
    svg += f'''
<text x="400" y="51" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">AMS1117-5V · C_out=10µF(ESR 50mΩ) · 负载 10mA→500mA：一次唤醒的四拍</text>
{cards[0]}
{cards[1]}
{cards[2]}
{cards[3]}
<text x="425" y="314" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">负载阶跃后：V_OUT 先跳后塌再拉回（跌落放大）</text>
<rect x="{T0}" y="336" width="{T1-T0}" height="140" fill="#e2e8f0" opacity="0.15"/>
<text x="22" y="360" font-size="11" font-weight="bold" fill="#2563eb">V_OUT</text>
<text x="22" y="446" font-size="11" font-weight="bold" fill="#b45309">I_L</text>
<line x1="{T0}" y1="{ref_y}" x2="{T1}" y2="{ref_y}" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="5,4"/>
<text x="{T1}" y="{int(ref_y)-6}" text-anchor="end" font-size="9.5" fill="#64748b">5.000V 标称</text>
<path d="{vout_d}" fill="none" stroke="#2563eb" stroke-width="2.8"/>
<path d="{il_d}" fill="none" stroke="#b45309" stroke-width="2.5"/>
<line x1="{tx(5):.0f}" y1="336" x2="{tx(5):.0f}" y2="466" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/>
<line x1="{tx(10):.0f}" y1="336" x2="{tx(10):.0f}" y2="466" stroke="#059669" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{tx(5)+4:.0f}" y="346" font-size="10" font-weight="bold" fill="#dc2626">阶跃 +490mA</text>
<text x="{tx(10)+6:.0f}" y="424" font-size="10" font-weight="bold" fill="#059669">环路接管 → 回升</text>
<text x="{tx(0):.0f}" y="482" font-size="10.5" fill="#475569">0</text>
<text x="{tx(5):.0f}" y="482" text-anchor="middle" font-size="10.5" fill="#475569">5µs</text>
<text x="{tx(10):.0f}" y="482" text-anchor="middle" font-size="10.5" fill="#475569">10µs</text>
<text x="{T1}" y="482" text-anchor="end" font-size="10.5" fill="#475569">50µs</text>
{cursor}
<rect x="22" y="515" width="756" height="87" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
<text x="40" y="540" font-size="12" font-weight="bold" fill="#2563eb">四拍账本：一次唤醒的跌落，够不够触发复位？</text>
<text x="40" y="563" font-size="11" fill="#475569">① ESR 跳变（零延迟）：ΔV₁ = 490mA×50mΩ ≈ 25mV；② 电容放电（µs 级）：ΔV₂ = 0.49A×5µs/10µF ≈ 245mV</text>
<text x="40" y="585" font-size="11" fill="#475569">总跌落 ≈ 25+245 = 270mV；3.3V 系统复位阈值 −5% = 165mV → 这次唤醒直接触发复位！</text>
<text x="40" y="597" font-size="10.5" font-weight="bold" fill="#dc2626">对策三板斧：加大 C_out 摊薄 ΔV₂ / 换低 ESR 陶瓷压掉 ΔV₁ / 选快环路 LDO 缩短 Δt</text>
'''
    svg += caption('四拍因果链：ESR 瞬跳 → 电容独自扛 → 环路拉回调管 → 重新锁定（可能过冲）', '#7c3aed', DB,
                   '0;0;1;1', '0;0.84;0.89;1', y=650, size=13.2)
    save('ldo-transient-beats.svg', svg + '</svg>')

# ======================= 图 91：555 无稳态四拍拆解（第 10 章 10.4） =======================
def make_555_astable_beats():
    """555 无稳态四拍：上电 → 充电(⅓→⅔) → 放电(⅔→⅓) → 无限循环。"""
    DB = 12
    T0, T1 = 80, 760
    PER = 1012.0                        # 541 + 471 µs
    def tx(t):
        return T0 + t / PER * (T1 - T0)
    def vy(v):
        return 420 - v / 9 * 62     # V_C：9V→358，0V→420

    def mini_stage(x, title, time_text, color, row1, row2, r1c, r2c, capc,
                   flow_path=None, flow_color="#dc2626"):
        fl = flow(flow_path, DB, n=2, color=flow_color, r=4.0) if flow_path else ''
        return f'''<rect x="{x}" y="70" width="174" height="214" rx="10" fill="#f8fafc" stroke="{color}" stroke-width="1.8"/>
<text x="{x+87}" y="94" text-anchor="middle" font-size="13" font-weight="bold" fill="{color}">{title}</text>
<text x="{x+87}" y="113" text-anchor="middle" font-size="10.5" fill="#475569">{time_text}</text>
<text x="{x+12}" y="130" font-size="9" font-weight="bold" fill="#b45309">VCC 9V</text>
<line x1="{x+12}" y1="134" x2="{x+100}" y2="134" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+40}" y1="134" x2="{x+40}" y2="140" stroke="#334155" stroke-width="2.2"/>
<rect x="{x+29}" y="140" width="22" height="24" fill="#f8fafc" stroke="{r1c}" stroke-width="2.2"/>
<text x="{x+55}" y="156" font-size="9" fill="#475569">R1 1k</text>
<line x1="{x+40}" y1="164" x2="{x+40}" y2="176" stroke="#334155" stroke-width="2.2"/>
<circle cx="{x+40}" cy="178" r="3" fill="#334155"/>
<text x="{x+47}" y="181" font-size="9" fill="#7c3aed">→7脚 DIS</text>
<line x1="{x+40}" y1="180" x2="{x+40}" y2="186" stroke="#334155" stroke-width="2.2"/>
<rect x="{x+29}" y="186" width="22" height="24" fill="#f8fafc" stroke="{r2c}" stroke-width="2.2"/>
<text x="{x+55}" y="202" font-size="9" fill="#475569">R2 6.8k</text>
<line x1="{x+40}" y1="210" x2="{x+40}" y2="216" stroke="#334155" stroke-width="2.2"/>
<circle cx="{x+40}" cy="218" r="3" fill="#334155"/>
<text x="{x+47}" y="221" font-size="9" fill="#7c3aed">→2/6脚</text>
<line x1="{x+40}" y1="220" x2="{x+40}" y2="226" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+28}" y1="226" x2="{x+52}" y2="226" stroke="{capc}" stroke-width="3"/>
<line x1="{x+28}" y1="234" x2="{x+52}" y2="234" stroke="{capc}" stroke-width="3"/>
<line x1="{x+40}" y1="234" x2="{x+40}" y2="240" stroke="#334155" stroke-width="2.2"/>
<line x1="{x+30}" y1="244" x2="{x+50}" y2="244" stroke="#334155" stroke-width="2.5"/>
<line x1="{x+34}" y1="249" x2="{x+46}" y2="249" stroke="#334155" stroke-width="2.5"/>
<text x="{x+58}" y="232" font-size="9" fill="#2563eb">C 100n</text>
<rect x="{x+104}" y="150" width="54" height="60" rx="6" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="{x+131}" y="180" text-anchor="middle" font-size="12" font-weight="bold" fill="#2563eb">555</text>
<text x="{x+131}" y="198" text-anchor="middle" font-size="9" font-weight="bold" fill="#dc2626">OUT</text>
<line x1="{x+158}" y1="180" x2="{x+166}" y2="180" stroke="#dc2626" stroke-width="2.4"/>
<polygon points="{x+166},180 {x+161},176 {x+161},184" fill="#dc2626"/>
{fl}
<text x="{x+87}" y="266" text-anchor="middle" font-size="10.5" font-weight="bold" fill="{color}">{row1}</text>
<text x="{x+87}" y="278" text-anchor="middle" font-size="10" fill="#475569">{row2}</text>'''

    cards = stage_cards([
        mini_stage(20, '① 上电', 't=0 · 上电瞬间', '#64748b', 'OUT：高 · 放电管关', 'C：0V 起步',
                   '#cbd5e1', '#cbd5e1', '#cbd5e1'),
        mini_stage(212, '② 充电', 'V_C：3→6V', '#b45309', 'OUT：高', 't_充 = 541µs',
                   '#f59e0b', '#f59e0b', '#2563eb', 'M252,134 L252,226', '#f59e0b'),
        mini_stage(404, '③ 放电', 'V_C：6→3V', '#dc2626', 'OUT：低', 't_放 = 471µs',
                   '#cbd5e1', '#dc2626', '#2563eb', 'M444,226 L444,178', '#dc2626'),
        mini_stage(596, '④ 循环', 'V_C：3↔6V', '#059669', 'OUT：方波 ≈990Hz', '占空比 ≈53%',
                   '#334155', '#334155', '#2563eb'),
    ], DB)

    # ---- 波形：V_C 指数充放电夹在 3V↔6V；OUT 方波 ----
    tc = np.linspace(0, 541, 48)
    vcc_charge = 9 - 6 * np.exp(-tc / 780)          # τ1=(R1+R2)C=780µs
    td = np.linspace(0, 471, 48)
    vcc_dis = 6 * np.exp(-td / 680)                 # τ2=R2·C=680µs
    vc_pts = list(zip(tc, vcc_charge)) + [(541 + t, v) for t, v in zip(td, vcc_dis)]
    vc_d = "M" + " L".join(f"{tx(t):.0f},{vy(v):.0f}" for t, v in vc_pts)
    out_d = f"M{T0},435 L{tx(541):.0f},435 L{tx(541):.0f},455 L{T1},455"
    cursor = waveform_cursor(DB, PER, [
        ('#2563eb', [(t, vy(v)) for t, v in vc_pts]),
        ('#dc2626', [(0, 435), (541, 435), (541, 455), (PER, 455)]),
    ], [
        (0, '稳态充电：V_C 从 3V 升向 6V，OUT 高（首次上电从 0V 起）', '#b45309'),
        (541, '稳态放电：到 6V 时 OUT 翻低，V_C 经 R2 降回 3V 后再循环', '#dc2626'),
    ], T0, T1, 340, 468)

    svg = svg_open('555 无稳态四拍：电容荡秋千，输出跳方波（R1=1k/R2=6.8k/C=100nF）', h=680)
    svg += f'''
<text x="400" y="51" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">R1=1kΩ · R2=6.8kΩ · C=100nF · V_CC=9V：一个完整周期（≈1.01ms）的四拍</text>
{cards[0]}
{cards[1]}
{cards[2]}
{cards[3]}
<text x="425" y="314" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">电容电压在 ⅓VCC↔⅔VCC 间荡秋千，输出同步跳方波</text>
<rect x="{T0}" y="340" width="{T1-T0}" height="128" fill="#e2e8f0" opacity="0.15"/>
<text x="24" y="392" font-size="11" font-weight="bold" fill="#2563eb">V_C</text>
<text x="24" y="450" font-size="11" font-weight="bold" fill="#dc2626">OUT</text>
<line x1="{T0}" y1="{vy(6):.0f}" x2="{T1}" y2="{vy(6):.0f}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="5,4"/>
<line x1="{T0}" y1="{vy(3):.0f}" x2="{T1}" y2="{vy(3):.0f}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="5,4"/>
<text x="{T1}" y="{vy(6)-4:.0f}" text-anchor="end" font-size="9" fill="#64748b">⅔VCC=6V</text>
<text x="{T1}" y="{vy(3)-4:.0f}" text-anchor="end" font-size="9" fill="#64748b">⅓VCC=3V</text>
<path d="{vc_d}" fill="none" stroke="#2563eb" stroke-width="2.6"/>
<path d="{out_d}" fill="none" stroke="#dc2626" stroke-width="2.6"/>
<line x1="{tx(541):.0f}" y1="340" x2="{tx(541):.0f}" y2="468" stroke="#dc2626" stroke-width="1" stroke-dasharray="3,3"/>
<text x="{tx(541)+6:.0f}" y="352" font-size="10" font-weight="bold" fill="#dc2626">THRES 触发 → 翻转</text>
<text x="{T0+4}" y="484" font-size="10" fill="#475569">充电相 541µs（OUT 高）</text>
<text x="{tx(541)+6:.0f}" y="484" font-size="10" fill="#475569">放电相 471µs（OUT 低）</text>
{cursor}
<rect x="22" y="515" width="756" height="87" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
<text x="40" y="540" font-size="12" font-weight="bold" fill="#2563eb">四拍账本：⅓→⅔ 恰好 0.693 个时间常数</text>
<text x="40" y="563" font-size="11" fill="#475569">t_充 = 0.693(R1+R2)C = 0.693×7.8kΩ×100nF ≈ 541µs（OUT 高）；t_放 = 0.693·R2·C ≈ 471µs（OUT 低）</text>
<text x="40" y="585" font-size="11" fill="#475569">f ≈ 1/1.012ms ≈ 990Hz；占空比 = 541/1012 ≈ 53%。充电走 R1+R2、放电只走 R2 → 占空比恒 &gt;50%</text>
<text x="40" y="597" font-size="10.5" font-weight="bold" fill="#dc2626">要准 50%：R2 两端并一只二极管，充电时抄近路绕过 R2（经典 555 占空比补丁）</text>
'''
    svg += caption('四拍因果链：上电 → 经 R1+R2 充到 ⅔ → 经 R2 放到 ⅓ → 无限循环', '#7c3aed', DB,
                   '0;0;1;1', '0;0.84;0.89;1', y=650, size=13.2)
    save('555-astable-beats.svg', svg + '</svg>')

# ======================= 图 92：水路 = 电路（第 0 章 0.1） =======================
def make_water_analogy():
    """全书通用比喻：电压/电流/电阻/电容/电感/二极管/MOSFET/地 → 一套水路。"""
    DW = 12
    loop = ("M156,180 H644 Q680,180 680,216 V424 Q680,460 644,460 "
            "H156 Q120,460 120,424 V216 Q120,180 156,180 Z")
    svg = svg_open('水路 = 电路：一张图看懂全书通用比喻（第 0 章 0.1）', h=620)
    svg += f'''
<text x="400" y="48" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">同一套直觉：水怎么流，电就怎么走——八个词，一张图</text>
<path d="{loop}" fill="none" stroke="#dbeafe" stroke-width="24" stroke-linejoin="round"/>
<path d="{loop}" fill="none" stroke="#93c5fd" stroke-width="15" stroke-linejoin="round"/>
{flow(loop, DW, n=9, color="#38bdf8", r=4.6)}
<circle cx="280" cy="180" r="27" fill="#e0f2fe" stroke="#0284c7" stroke-width="2.5"/>
<g><animateTransform attributeName="transform" type="rotate" from="0 280 180" to="360 280 180" dur="4s" repeatCount="indefinite"/>
<line x1="280" y1="180" x2="298" y2="168" stroke="#0284c7" stroke-width="2.6"/>
<line x1="280" y1="180" x2="262" y2="168" stroke="#0284c7" stroke-width="2.6"/>
<line x1="280" y1="180" x2="280" y2="201" stroke="#0284c7" stroke-width="2.6"/></g>
<circle cx="280" cy="180" r="5" fill="#0284c7"/>
<text x="280" y="144" text-anchor="middle" font-size="12" font-weight="bold" fill="#0369a1">水泵 = 电压 V</text>
<text x="280" y="128" text-anchor="middle" font-size="10" fill="#64748b">推动水流的「势」</text>
<rect x="474" y="164" width="92" height="32" rx="6" fill="#f8fafc"/>
<path d="M478,170 H506 L514,177 H526 L534,170 H562" fill="none" stroke="#0284c7" stroke-width="2.6"/>
<path d="M478,190 H506 L514,183 H526 L534,190 H562" fill="none" stroke="#0284c7" stroke-width="2.6"/>
<text x="520" y="144" text-anchor="middle" font-size="12" font-weight="bold" fill="#0369a1">细水管 = 电阻 R</text>
<text x="520" y="128" text-anchor="middle" font-size="10" fill="#64748b">管越细，同样水压流得越少</text>
<rect x="654" y="276" width="54" height="88" rx="8" fill="#e0f2fe" stroke="#0284c7" stroke-width="2.5"/>
<rect x="659" y="314" width="44" height="45" rx="3" fill="#7dd3fc" opacity="0.8"/>
<path d="M659,314 q7.3,-5 14.7,0 q7.3,5 14.7,0 q7.3,-5 14.6,0" fill="none" stroke="#0284c7" stroke-width="1.6"/>
<text x="681" y="384" text-anchor="middle" font-size="12" font-weight="bold" fill="#0369a1">蓄水池 = 电容 C</text>
<text x="681" y="400" text-anchor="middle" font-size="10" fill="#64748b">攒水位，水位不能突变</text>
<circle cx="520" cy="460" r="27" fill="#e0f2fe" stroke="#0284c7" stroke-width="2.5"/>
<g><animateTransform attributeName="transform" type="rotate" from="0 520 460" to="360 520 460" dur="5s" repeatCount="indefinite"/>
<line x1="520" y1="435" x2="520" y2="485" stroke="#0284c7" stroke-width="2.4"/>
<line x1="495" y1="460" x2="545" y2="460" stroke="#0284c7" stroke-width="2.4"/>
<line x1="502" y1="442" x2="538" y2="478" stroke="#0284c7" stroke-width="2.4"/>
<line x1="538" y1="442" x2="502" y2="478" stroke="#0284c7" stroke-width="2.4"/></g>
<circle cx="520" cy="460" r="4.5" fill="#0284c7"/>
<text x="520" y="504" text-anchor="middle" font-size="12" font-weight="bold" fill="#0369a1">水车 = 电感 L</text>
<text x="520" y="520" text-anchor="middle" font-size="10" fill="#64748b">转速不能突变，断电顶着冲</text>
<circle cx="280" cy="460" r="27" fill="#e0f2fe" stroke="#0284c7" stroke-width="2.5"/>
<polygon points="266,446 266,474 288,460" fill="#7dd3fc" stroke="#0284c7" stroke-width="2"/>
<line x1="288" y1="445" x2="288" y2="475" stroke="#0284c7" stroke-width="3"/>
<text x="280" y="504" text-anchor="middle" font-size="12" font-weight="bold" fill="#0369a1">单向阀 = 二极管</text>
<text x="280" y="520" text-anchor="middle" font-size="10" fill="#64748b">只许水往一个方向流</text>
<rect x="93" y="292" width="54" height="56" rx="6" fill="#e0f2fe" stroke="#0284c7" stroke-width="2.5"/>
<rect x="97" y="296" width="46" height="26" rx="3" fill="#7dd3fc" opacity="0.8"/>
<line x1="120" y1="292" x2="120" y2="276" stroke="#0284c7" stroke-width="2.5"/>
<circle cx="120" cy="271" r="4.5" fill="#0284c7"/>
<text x="92" y="312" text-anchor="end" font-size="12" font-weight="bold" fill="#0369a1">闸门 = MOSFET</text>
<text x="92" y="330" text-anchor="end" font-size="10" fill="#64748b">栅压一声令下</text>
<text x="400" y="252" text-anchor="middle" font-size="11" font-weight="bold" fill="#0284c7">水 流 = 电 流 I（必须成环）</text>
<line x1="330" y1="330" x2="470" y2="330" stroke="#0ea5e9" stroke-width="1.8" stroke-dasharray="6,4"/>
<text x="400" y="320" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#0369a1">海平面 = 地 GND</text>
<text x="400" y="348" text-anchor="middle" font-size="10" fill="#64748b">所有水位的 0V 基准（不是下水道）</text>
'''
    svg += caption('同一套直觉：水泵推水位 · 细管卡流量 · 水池攒水位 · 水车扛惯性 · 单向阀防倒流 · 闸门听指挥', '#0284c7', DW,
                   '0;0;1;1', '0;0.8;0.86;1', y=572, size=13)
    save('water-analogy.svg', svg + '</svg>')

# ======================= 图 93：树状供电（第 14 章 14.3） =======================
def make_power_tree():
    """树状供电：输入 → 板级储能 → 各模块 LDO/DCDC → 每芯片去耦，逐级净化。"""
    DP = 12
    rows = [118, 220, 322]
    regs = [('LDO 3.3V', '#2563eb', '低噪，喂模拟'),
            ('DCDC 5V', '#7c3aed', '高效，喂数字'),
            ('LDO 1.8V', '#059669', '核心电压')]
    chips = [('传感器（模拟）', '#2563eb'), ('MCU（数字）', '#7c3aed'), ('FPGA 核', '#059669')]
    svg = svg_open('树状供电：输入 → 储能 → 稳压 → 去耦，逐级净化', h=500)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">电源不是「一根线拉到底」：每一级都在替下一级挡脏</text>
<rect x="34" y="192" width="104" height="56" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>
<text x="86" y="216" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#1e293b">输入 12V</text>
<text x="86" y="234" text-anchor="middle" font-size="9.5" fill="#64748b">适配器 / 电池</text>
<rect x="196" y="184" width="128" height="72" rx="10" fill="#fffbeb" stroke="#b45309" stroke-width="2"/>
<text x="260" y="210" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#1e293b">板级储能</text>
<text x="260" y="228" text-anchor="middle" font-size="10" fill="#b45309">10~100µF 大电解</text>
<text x="260" y="244" text-anchor="middle" font-size="9.5" fill="#64748b">扛大电流脉冲</text>
<line x1="138" y1="220" x2="196" y2="220" stroke="#94a3b8" stroke-width="2.5"/>
<line x1="324" y1="220" x2="360" y2="220" stroke="#94a3b8" stroke-width="2.5"/>
<line x1="360" y1="118" x2="360" y2="322" stroke="#94a3b8" stroke-width="2.5"/>
{flow("M138,220 H196", DP, n=2, color="#f59e0b", r=4.5)}
{flow("M324,220 H360", DP, n=2, color="#f59e0b", r=4.5)}
{flow("M360,118 V322", DP, n=4, color="#f59e0b", r=4.5)}
'''
    for i, r in enumerate(rows):
        reg, rc, rsub = regs[i]
        ch, cc = chips[i]
        svg += f'''
<line x1="360" y1="{r}" x2="430" y2="{r}" stroke="#94a3b8" stroke-width="2.5"/>
<rect x="430" y="{r-26}" width="104" height="52" rx="10" fill="#f8fafc" stroke="{rc}" stroke-width="2"/>
<text x="482" y="{r-4}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="{rc}">{reg}</text>
<text x="482" y="{r+14}" text-anchor="middle" font-size="9.5" fill="#64748b">{rsub}</text>
<line x1="534" y1="{r}" x2="650" y2="{r}" stroke="#94a3b8" stroke-width="2.5"/>
<rect x="650" y="{r-26}" width="118" height="52" rx="10" fill="#f8fafc" stroke="{cc}" stroke-width="2"/>
<text x="709" y="{r-2}" text-anchor="middle" font-size="11" font-weight="bold" fill="{cc}">{ch}</text>
<text x="709" y="{r+16}" text-anchor="middle" font-size="9.5" fill="#64748b">+100nF 就近去耦</text>
{flow(f"M534,{r} H650", DP, n=3, color="#38bdf8", r=4.5)}
'''
    svg += '''
<text x="400" y="384" text-anchor="middle" font-size="11" font-weight="bold" fill="#0369a1">逐级净化：大电解挡低频脉动 → 稳压器压掉纹波 → 100nF 兜住芯片开关瞬间的高频</text>
<text x="400" y="406" text-anchor="middle" font-size="10.5" fill="#64748b">压差小/电流小/噪声敏感 → LDO；压差大/电流大 → DCDC（效率优先）+ 后级 LDO 净化</text>
'''
    svg += caption('口诀：输入 → 储能 → 稳压 → 去耦，一级替一级挡脏；去耦电容就近放，走线电感挡不住高频', '#2563eb', DP,
                   '0;0;1;1', '0;0.82;0.88;1', y=452, size=13)
    save('power-tree.svg', svg + '</svg>')

# ======================= 图 94：电压降（第 0 章 0.2） =======================
def make_voltage_drop():
    """欧姆定律的「电压降」视角：串联路径上各电阻按阻值瓜分总电压。"""
    DV = 10
    def vy(v):
        return 350 - v / 5 * 200          # 5V→150, 0V→350
    svg = svg_open('电压降：同一股电流，谁 R 大谁分得多', h=520)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">同一股电流流过所有电阻——每个电阻「留下」一份电压，加起来恰好等于电源</text>
<text x="190" y="86" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">电路：5V → 4kΩ → 1kΩ → GND</text>
<line x1="80" y1="110" x2="240" y2="110" stroke="#334155" stroke-width="2.5"/>
<text x="62" y="104" font-size="12.5" font-weight="bold" fill="#b45309">5V</text>
<circle cx="160" cy="110" r="3.5" fill="#334155"/>
<line x1="160" y1="110" x2="160" y2="124" stroke="#334155" stroke-width="2.5"/>
<rect x="148" y="124" width="24" height="56" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="182" y="146" font-size="12" font-weight="bold" fill="#b45309">4kΩ</text>
<text x="182" y="164" font-size="11" font-weight="bold" fill="#dc2626">降 4V</text>
<line x1="160" y1="180" x2="160" y2="198" stroke="#334155" stroke-width="2.5"/>
<circle cx="160" cy="202" r="3.5" fill="#334155"/>
<text x="182" y="206" font-size="12" font-weight="bold" fill="#059669">1V（节点）</text>
<line x1="160" y1="206" x2="160" y2="222" stroke="#334155" stroke-width="2.5"/>
<rect x="148" y="222" width="24" height="56" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<text x="182" y="244" font-size="12" font-weight="bold" fill="#b45309">1kΩ</text>
<text x="182" y="262" font-size="11" font-weight="bold" fill="#dc2626">降 1V</text>
<line x1="160" y1="278" x2="160" y2="298" stroke="#334155" stroke-width="2.5"/>
<line x1="140" y1="302" x2="180" y2="302" stroke="#334155" stroke-width="2.5"/>
<line x1="146" y1="310" x2="174" y2="310" stroke="#334155" stroke-width="2.5"/>
<line x1="152" y1="318" x2="168" y2="318" stroke="#334155" stroke-width="2.5"/>
{flow("M160,112 L160,298", DV, n=4, color="#f59e0b", r=5)}
<text x="128" y="202" text-anchor="end" font-size="11.5" font-weight="bold" fill="#2563eb">I = 1mA</text>
<text x="190" y="338" text-anchor="middle" font-size="11" fill="#475569">5V ÷ (4k+1k) = 1mA —— 同一股电流，处处相等</text>
<text x="600" y="86" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">沿回路走一圈，看电压怎么一级级掉下去</text>
<line x1="430" y1="{vy(0)}" x2="780" y2="{vy(0)}" stroke="#cbd5e1" stroke-width="1"/>
<line x1="430" y1="{vy(1)}" x2="780" y2="{vy(1)}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="430" y1="{vy(5)}" x2="780" y2="{vy(5)}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="4,3"/>
<text x="424" y="{vy(5)+4}" text-anchor="end" font-size="10.5" fill="#475569">5V</text>
<text x="424" y="{vy(1)+4}" text-anchor="end" font-size="10.5" fill="#475569">1V</text>
<text x="424" y="{vy(0)+4}" text-anchor="end" font-size="10.5" fill="#475569">0V</text>
<path d="M432,{vy(5)} L510,{vy(5)} L510,{vy(1)} L590,{vy(1)} L590,{vy(0)} L770,{vy(0)}" fill="none" stroke="#2563eb" stroke-width="3"/>
<text x="514" y="{(vy(5)+vy(1))//2}" font-size="11.5" font-weight="bold" fill="#dc2626">4kΩ 分到 4V</text>
<text x="594" y="{(vy(1)+vy(0))//2}" font-size="11.5" font-weight="bold" fill="#dc2626">1kΩ 分到 1V</text>
<text x="600" y="404" text-anchor="middle" font-size="11" fill="#475569">每一段竖降 = 跨过一个电阻的电压降；横走 = 沿理想导线（不降压）</text>
<circle r="4.5" fill="#2563eb"><animateMotion dur="{DV}s" repeatCount="indefinite" path="M432,{vy(5)} L510,{vy(5)} L510,{vy(1)} L590,{vy(1)} L590,{vy(0)} L770,{vy(0)}"/></circle>
<circle r="4.5" fill="#2563eb" opacity="0.6"><animateMotion dur="{DV}s" begin="-{DV/3:.2f}s" repeatCount="indefinite" path="M432,{vy(5)} L510,{vy(5)} L510,{vy(1)} L590,{vy(1)} L590,{vy(0)} L770,{vy(0)}"/></circle>
<circle r="4.5" fill="#2563eb" opacity="0.35"><animateMotion dur="{DV}s" begin="-{2*DV/3:.2f}s" repeatCount="indefinite" path="M432,{vy(5)} L510,{vy(5)} L510,{vy(1)} L590,{vy(1)} L590,{vy(0)} L770,{vy(0)}"/></circle>
<circle cx="160" cy="202" r="5" fill="none" stroke="#059669" stroke-width="2">
<animate attributeName="r" values="5;12;5" dur="1.7s" repeatCount="indefinite"/></circle>
<circle cx="160" cy="110" r="5" fill="none" stroke="#b45309" stroke-width="2">
<animate attributeName="r" values="5;12;5" dur="1.7s" begin="-0.85s" repeatCount="indefinite"/></circle>
'''
    svg += caption('口诀：V = I×R —— 同一电流下电压按电阻成比例分配（4k:1k = 4:1 → 4V:1V）', '#2563eb', DV,
                   '0;0;1;1', '0;0.8;0.86;1', y=452, size=13)
    save('voltage-drop.svg', svg + '</svg>')

# ======================= 图 95：PCB 布线四招（第 15 章 15.3） =======================
def make_pcb_routing():
    """布线规则可视化：45° 拐角 / 过孔寄生 / 差分对 / 敏感线包地。"""
    DP = 12
    svg = svg_open('PCB 布线四招：每一条规则背后都有物理', h=560)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="13.5" font-weight="bold" fill="#334155">同样的网络，画法不同，高频行为就不同</text>
<!-- 1: 45 度拐角 -->
<text x="210" y="88" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">① 拐角：用 45°，不用 90°</text>
<path d="M70,150 H160 V220" fill="none" stroke="#dc2626" stroke-width="7" stroke-linejoin="miter"/>
<text x="70" y="140" font-size="10.5" font-weight="bold" fill="#dc2626">90° 尖角</text>
<text x="120" y="244" font-size="10" fill="#475569">蚀刻不均、高频反射</text>
<path d="M250,150 H320 L370,200 V240" fill="none" stroke="#059669" stroke-width="7" stroke-linejoin="round"/>
<text x="250" y="140" font-size="10.5" font-weight="bold" fill="#059669">45° 折角</text>
<text x="300" y="264" font-size="10" fill="#475569">线宽连续、阻抗平顺</text>
<!-- 2: 过孔寄生 -->
<text x="610" y="88" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">② 过孔：1nH + 0.5pF / 个</text>
<line x1="500" y1="140" x2="700" y2="140" stroke="#2563eb" stroke-width="7"/>
<circle cx="600" cy="140" r="11" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>
<circle cx="600" cy="140" r="5" fill="#94a3b8"/>
<line x1="500" y1="220" x2="700" y2="220" stroke="#059669" stroke-width="7"/>
<line x1="600" y1="151" x2="600" y2="220" stroke="#334155" stroke-width="2.5" stroke-dasharray="5,4"/>
<text x="616" y="188" font-size="11" font-weight="bold" fill="#dc2626">L≈1nH · C≈0.5pF</text>
<text x="600" y="250" text-anchor="middle" font-size="10" fill="#475569">高速/大电流少打孔；电源过孔打多个并联</text>
<!-- 3: 差分对 -->
<text x="210" y="320" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">③ 差分对：等长 · 等距 · 紧邻</text>
<path d="M70,370 H200 L250,420 H350" fill="none" stroke="#7c3aed" stroke-width="5"/>
<path d="M70,398 H200 L250,448 H350" fill="none" stroke="#2563eb" stroke-width="5"/>
<text x="230" y="360" font-size="10" fill="#475569">间距恒定 → 差分阻抗恒定</text>
<text x="210" y="480" text-anchor="middle" font-size="10" fill="#475569">等长保证两线同时到达；紧邻让共模干扰同相抵消</text>
<!-- 4: 敏感线包地 -->
<text x="610" y="320" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">④ 敏感线：远离时钟，必要时包地</text>
<path d="M470,358 H540 L560,378 H700" fill="none" stroke="#dc2626" stroke-width="5"/>
<text x="470" y="348" font-size="10" font-weight="bold" fill="#dc2626">时钟 / 开关节点</text>
<path d="M470,396 H700" fill="none" stroke="#94a3b8" stroke-width="3" stroke-dasharray="6,4"/>
<path d="M470,440 H700" fill="none" stroke="#94a3b8" stroke-width="3" stroke-dasharray="6,4"/>
<path d="M470,418 H700" fill="none" stroke="#2563eb" stroke-width="5"/>
<text x="470" y="412" font-size="10" font-weight="bold" fill="#2563eb">敏感模拟线（两侧包地）</text>
<text x="610" y="490" text-anchor="middle" font-size="10" fill="#475569">平行走线越长、越近，串扰越大——包地是「屏蔽墙」</text>
{flow("M472,358 H538 L558,378 H698", DP, n=3, color="#dc2626", r=4.5)}
{flow("M472,418 H698", DP, n=4, color="#2563eb", r=4.5)}
'''
    svg += caption('口诀：45° 拐角、少打过孔、差分等长紧邻、敏感线包地——四条都源自「电感与耦合」', '#2563eb', DP,
                   '0;0;1;1', '0;0.8;0.86;1', y=534, size=13)
    save('pcb-routing.svg', svg + '</svg>')

# ======================= 图 86：共射放大器四拍拆解（第 3 章 3.9） =======================
def make_ce_dynamic():
    DQ = 12
    import math as _m
    def wv(x0, y0, w, cyc, amp, ph, n=72):
        pts=[]
        for i in range(n+1):
            x=x0+w*i/n
            y=y0-amp*_m.sin(2*_m.pi*cyc*i/n+ph)
            pts.append(f"{x:.1f},{y:.1f}")
        return " ".join(pts), "M"+" L".join(pts)
    out_poly, out_d = wv(430, 250, 326, 3, 17, 0.0)
    in_poly,  in_d  = wv(430, 118, 326, 3,  9, _m.pi)
    svg = svg_open('共射放大器四拍：一个正弦周期里，电流怎么「指挥」电压', h=680)
    svg += f'''
<text x="400" y="46" text-anchor="middle" font-size="14" font-weight="bold" fill="#334155">12V 单电源 · R_C=2kΩ · Q 点 I_C=3mA —— 输入升，输出降</text>
<line x1="372" y1="80" x2="372" y2="352" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="6,5"/>
<text x="64" y="88" text-anchor="end" font-size="11" font-weight="bold" fill="#b45309">12V</text>
<line x1="70" y1="96" x2="260" y2="96" stroke="#334155" stroke-width="2.5"/>
{resistor_v(110, 116, 40, 'R1')}
<circle cx="110" cy="176" r="4" fill="#334155"/>
{resistor_v(110, 196, 40, 'R2')}
{gnd_sym(110, 270)}
<line x1="110" y1="176" x2="178" y2="176" stroke="#334155" stroke-width="2.5"/>
<line x1="180" y1="164" x2="180" y2="188" stroke="#334155" stroke-width="3"/>
<line x1="182" y1="169" x2="194" y2="157" stroke="#334155" stroke-width="2.5"/>
<line x1="182" y1="183" x2="194" y2="195" stroke="#334155" stroke-width="2.5"/>
<polygon points="194,195 186,191 190,185" fill="#334155"/>
{resistor_v(194, 116, 32, 'R_C 2k')}
<line x1="194" y1="195" x2="194" y2="210" stroke="#334155" stroke-width="2.5"/>
{resistor_v(194, 230, 40, 'R_E 600')}
{gnd_sym(194, 304)}
<circle cx="194" cy="168" r="4" fill="#334155"/>
<line x1="194" y1="168" x2="244" y2="168" stroke="#334155" stroke-width="2.5"/>
<line x1="248" y1="156" x2="248" y2="180" stroke="#334155" stroke-width="2.5"/>
<line x1="256" y1="156" x2="256" y2="180" stroke="#334155" stroke-width="2.5"/>
<line x1="256" y1="168" x2="288" y2="168" stroke="#334155" stroke-width="2.5"/>
<circle cx="288" cy="168" r="4" fill="#334155"/>
<text x="296" y="172" font-size="10.5" fill="#475569">输出</text>
<circle cx="42" cy="176" r="12" fill="none" stroke="#2563eb" stroke-width="1.8"/>
<path d="M35,176 q3.5,-6 7,0 q3.5,6 7,0" fill="none" stroke="#2563eb" stroke-width="1.8"/>
<line x1="54" y1="176" x2="76" y2="176" stroke="#334155" stroke-width="2.5"/>
<line x1="76" y1="164" x2="76" y2="188" stroke="#334155" stroke-width="2.5"/>
<line x1="84" y1="164" x2="84" y2="188" stroke="#334155" stroke-width="2.5"/>
<line x1="84" y1="176" x2="106" y2="176" stroke="#334155" stroke-width="2.5"/>
<text x="42" y="204" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#2563eb">v_in 10mV</text>
<text x="126" y="167" font-size="10.5" fill="#475569">V_B≈2.5V</text>
<text x="222" y="152" font-size="10.5" fill="#475569">V_C=6V</text>
<text x="206" y="224" font-size="10.5" fill="#475569">V_E≈1.8V</text>
<circle r="4.5" fill="#059669"><animateMotion dur="{DQ}s" begin="-0.4s" repeatCount="indefinite" path="M112,176 L176,176"/></circle>
<circle r="4.5" fill="#b45309"><animateMotion dur="{DQ}s" begin="-1.2s" repeatCount="indefinite" path="M76,96 L106,96"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DQ}s" begin="-2.0s" repeatCount="indefinite" path="M194,98 L194,150"/></circle>
<circle r="4.5" fill="#7c3aed"><animateMotion dur="{DQ}s" begin="-2.8s" repeatCount="indefinite" path="M194,198 L194,246"/></circle>
<circle r="4.5" fill="#2563eb"><animateMotion dur="{DQ}s" begin="-1.0s" repeatCount="indefinite" path="{in_d}"/></circle>
<circle r="4.5" fill="#dc2626"><animateMotion dur="{DQ}s" begin="-4.0s" repeatCount="indefinite" path="{out_d}"/></circle>
<line x1="418" y1="100" x2="418" y2="340" stroke="#64748b" stroke-width="1.6"/>
<line x1="418" y1="340" x2="778" y2="340" stroke="#64748b" stroke-width="1.6"/>
<text x="412" y="164" text-anchor="end" font-size="10.5" fill="#475569">12V</text>
<text x="412" y="254" text-anchor="end" font-size="10.5" fill="#475569">6V</text>
<text x="412" y="314" text-anchor="end" font-size="10.5" fill="#475569">2V</text>
<text x="412" y="344" text-anchor="end" font-size="10.5" fill="#475569">0</text>
<line x1="418" y1="160" x2="766" y2="160" stroke="#dc2626" stroke-width="1.2" stroke-dasharray="5,4"/>
<line x1="418" y1="310" x2="766" y2="310" stroke="#dc2626" stroke-width="1.2" stroke-dasharray="5,4"/>
<line x1="418" y1="250" x2="766" y2="250" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<polyline points="{in_poly}" fill="none" stroke="#2563eb" stroke-width="2.2"/>
<polyline points="{out_poly}" fill="none" stroke="#dc2626" stroke-width="2.6"/>
<text x="756" y="100" text-anchor="end" font-size="10.5" font-weight="bold" fill="#2563eb">输入 v_in 10mVpp</text>
<text x="756" y="228" text-anchor="end" font-size="10.5" font-weight="bold" fill="#dc2626">输出 v_C ≈2.3Vpp（反相 230 倍）</text>
<line x1="772" y1="164" x2="772" y2="246" stroke="#059669" stroke-width="1.6"/>
<polygon points="772,160 768,168 776,168" fill="#059669"/>
<polygon points="772,250 768,242 776,242" fill="#059669"/>
<text x="778" y="209" font-size="10.5" font-weight="bold" fill="#059669">6V</text>
<line x1="772" y1="254" x2="772" y2="306" stroke="#b45309" stroke-width="1.6"/>
<polygon points="772,250 768,258 776,258" fill="#b45309"/>
<polygon points="772,310 768,302 776,302" fill="#b45309"/>
<text x="778" y="285" font-size="10.5" font-weight="bold" fill="#b45309">4V</text>
<text x="598" y="362" text-anchor="middle" font-size="10.5" fill="#475569">上行余量 6V（到 12V 截止）｜下行余量 4V（到 2V 饱和）</text>
<text x="598" y="380" text-anchor="middle" font-size="11" font-weight="bold" fill="#dc2626">→ 对称摆幅 = 2×min(6V, 4V) = 8.0Vpp（红线只用了 2.3Vpp）</text>
<rect x="29" y="390" width="178" height="126" rx="9" fill="#f8fafc" stroke="#059669" stroke-width="1.6"/>
<text x="45" y="414" font-size="12" font-weight="bold" fill="#059669">① 初始态（安静）</text>
<text x="45" y="438" font-size="10.5" fill="#475569">V_B≈2.5V、V_E≈1.8V</text>
<text x="45" y="458" font-size="10.5" fill="#475569">V_C=6V（I_C=3mA）</text>
<text x="45" y="478" font-size="10.5" fill="#475569">信号都叠在这个「地基」上</text>
<text x="45" y="498" font-size="10.5" fill="#475569">——它决定剩余空间</text>
<rect x="217" y="390" width="178" height="126" rx="9" fill="#f8fafc" stroke="#dc2626" stroke-width="1.6"/>
<text x="233" y="414" font-size="12" font-weight="bold" fill="#dc2626">② 正半周：输入 ↑</text>
<text x="233" y="438" font-size="10.5" fill="#475569">v_BE↑ → i_B↑ → i_C=βi_B↑</text>
<text x="233" y="458" font-size="10.5" fill="#475569">R_C 压降↑ → v_C 下降</text>
<text x="233" y="478" font-size="10.5" fill="#475569">v_C = 12 − i_C·R_C ↓</text>
<text x="233" y="498" font-size="10.5" fill="#475569">能量多分给 R_C，留给自己少</text>
<rect x="405" y="390" width="178" height="126" rx="9" fill="#f8fafc" stroke="#2563eb" stroke-width="1.6"/>
<text x="421" y="414" font-size="12" font-weight="bold" fill="#2563eb">③ 负半周：镜像</text>
<text x="421" y="438" font-size="10.5" fill="#475569">输入 ↓ → i_B↓ → i_C↓</text>
<text x="421" y="458" font-size="10.5" fill="#475569">R_C 压降↓ → v_C ↑</text>
<text x="421" y="478" font-size="10.5" fill="#475569">输出与输入反着走</text>
<text x="421" y="498" font-size="10.5" fill="#475569">一升一降，一个完整周期</text>
<rect x="593" y="390" width="178" height="126" rx="9" fill="#f8fafc" stroke="#b45309" stroke-width="1.6"/>
<text x="609" y="414" font-size="12" font-weight="bold" fill="#b45309">④ 边界：推过头</text>
<text x="609" y="438" font-size="10.5" fill="#475569">推猛→v_C 撞 V_E+0.2V=2V</text>
<text x="609" y="458" font-size="10.5" fill="#475569">底部削平（饱和失真）</text>
<text x="609" y="478" font-size="10.5" fill="#475569">拉猛→i_B=0，v_C 挂 12V</text>
<text x="609" y="498" font-size="10.5" fill="#475569">顶部削平（截止失真）</text>
{pulse(217,390,178,126,'#dc2626',2.2,10)}
{pulse(593,390,178,126,'#059669',2.2,10)}
<rect x="29" y="526" width="742" height="102" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.6"/>
<text x="45" y="550" font-size="12" font-weight="bold" fill="#2563eb">算一笔：两个余量，取小者</text>
<text x="45" y="576" font-size="11" fill="#475569">上行 6V（到截止 12V）、下行 4V（到饱和 V_E+0.2V=2V）→ 最大不失真摆幅 = 2×min(6V, 4V) = 8.0Vpp</text>
<text x="45" y="600" font-size="11" fill="#475569">增益 |A_v| = R_C/r_e ≈ 2kΩ/8.7Ω ≈ 230 → 满摆幅需输入 ≈35mVpp；本例 10mV → 输出 ≈2.3Vpp，远未削波</text>
<text x="45" y="622" font-size="11" font-weight="bold" fill="#dc2626">摆幅由「更小的那份余量」决定 —— Q 点偏置就是余量分配器</text>
'''
    svg += caption("① 输入升、输出降——反相不是公式，是 i_C 电流路径的必然", "#059669", DQ,
                   "0;1;1;0;0", "0;0.03;0.2;0.25;1", y=652)
    svg += caption("② 正半周把 v_C 往下压，负半周镜像往上抬", "#dc2626", DQ,
                   "0;0;1;1;0;0", "0;0.25;0.3;0.5;0.55;1", y=652)
    svg += caption("③ 两个余量：上行 6V、下行 4V —— 对称摆幅取小者 = 8.0Vpp", "#2563eb", DQ,
                   "0;0;1;1;0;0", "0;0.55;0.6;0.8;0.85;1", y=652)
    svg += caption("④ 削波先发生在余量小的一侧：2V 的饱和底先被压平", "#b45309", DQ,
                   "0;0;1;1", "0;0.85;0.9;1", y=652)
    save('ce-dynamic.svg', svg + '</svg>')

# ======================= 图 102：排故决策树（第 17 章 17.8） =======================
def make_diagnosis_tree():
    DT = 12
    SCX, SW, SH = 175, 270, 42          # 决策脊柱
    BCX, BW = 590, 280                  # 「否」分支目标
    LW, LH, LY = 175, 56, 438           # 底部四叶
    BUS_Y = 410
    spine = [
        (92,  '① 上电无反应？'),
        (160, '② 输入电压在不在？'),
        (228, '③ 关键电源轨都对吗？'),
        (296, '④ 复位 / 时钟正常吗？'),
        (364, '⑤ 有电有复位 → 看表现'),
    ]
    branches = [
        (160, '→ 17.1 电源类：保险 / 极性 / 连接', '#2563eb'),
        (228, '→ 17.1：带载跌落 / 纹波 / 使能', '#dc2626'),
        (296, '→ 17.3：复位 IC / 晶振 / 时序', '#b45309'),
    ]
    leaves = [
        (30,  '完全不动', '17.3 接口 / 固件 / 挂死', '#7c3aed'),
        (215, '读数不对', '17.2 反馈 / 校准 / 噪声', '#059669'),
        (400, '时好时坏', '17.6 焊接连接 → 再查 17.4', '#dc2626'),
        (585, '发热异常', '17.5 功耗 / 短路 / 散热', '#b45309'),
    ]
    body = ''
    # ---- 脊柱节点 ----
    for y, t in spine:
        body += (f'<rect x="{SCX-SW//2}" y="{y-SH//2}" width="{SW}" height="{SH}" rx="10" '
                 f'fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>'
                 f'<text x="{SCX}" y="{y+5}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1e293b">{t}</text>\n')
    # ---- 竖箭头 + 「是」 ----
    for i in range(len(spine) - 1):
        y1 = spine[i][0] + SH // 2
        y2 = spine[i + 1][0] - SH // 2
        body += (f'<line x1="{SCX}" y1="{y1}" x2="{SCX}" y2="{y2-3}" stroke="#334155" stroke-width="2.2"/>'
                 f'<polygon points="{SCX},{y2} {SCX-5},{y2-7} {SCX+5},{y2-7}" fill="#334155"/>'
                 f'<text x="{SCX+14}" y="{(y1+y2)/2+4:.0f}" font-size="11" font-weight="bold" fill="#059669">是</text>\n')
    # ---- 「否」分支 ----
    for y, t, col in branches:
        body += (f'<line x1="{SCX+SW//2}" y1="{y}" x2="{BCX-BW//2-3}" y2="{y}" stroke="{col}" stroke-width="2.2"/>'
                 f'<polygon points="{BCX-BW//2},{y} {BCX-BW//2-8},{y-5} {BCX-BW//2-8},{y+5}" fill="{col}"/>'
                 f'<text x="{SCX+SW//2+16}" y="{y-9}" font-size="11" font-weight="bold" fill="#dc2626">否</text>\n')
        body += (f'<rect x="{BCX-BW//2}" y="{y-SH//2}" width="{BW}" height="{SH}" rx="10" '
                 f'fill="#f8fafc" stroke="{col}" stroke-width="2.5"/>'
                 f'<text x="{BCX}" y="{y+5}" text-anchor="middle" font-size="12" font-weight="bold" fill="{col}">{t}</text>\n')
    # ---- 底部总线 + 四叶 ----
    body += (f'<line x1="{SCX}" y1="{spine[-1][0]+SH//2}" x2="{SCX}" y2="{BUS_Y}" stroke="#334155" stroke-width="2.2"/>'
             f'<line x1="{leaves[0][0]+LW//2}" y1="{BUS_Y}" x2="{leaves[-1][0]+LW//2}" y2="{BUS_Y}" stroke="#334155" stroke-width="2.2"/>')
    for x, t, s, col in leaves:
        cx = x + LW // 2
        body += (f'<line x1="{cx}" y1="{BUS_Y}" x2="{cx}" y2="{LY-3}" stroke="{col}" stroke-width="2.2"/>'
                 f'<polygon points="{cx},{LY} {cx-5},{LY-7} {cx+5},{LY-7}" fill="{col}"/>')
        body += (f'<rect x="{x}" y="{LY}" width="{LW}" height="{LH}" rx="10" fill="#f8fafc" stroke="{col}" stroke-width="2.5"/>'
                 f'<text x="{cx}" y="{LY+25}" text-anchor="middle" font-size="13" font-weight="bold" fill="{col}">{t}</text>'
                 f'<text x="{cx}" y="{LY+45}" text-anchor="middle" font-size="9.5" fill="#475569">{s}</text>\n')
    # ---- 连接段粒子（只走连线，不压文字） ----
    for i in range(len(spine) - 1):
        y1 = spine[i][0] + SH // 2
        y2 = spine[i + 1][0] - SH // 2
        body += flow(f'M{SCX},{y1} V{y2}', DT, n=2, color='#334155', r=4.5) + '\n'
    for y, _, col in branches:
        body += flow(f'M{SCX+SW//2},{y} H{BCX-BW//2}', DT, n=2, color=col, r=4.5) + '\n'
    body += flow(f'M{SCX},{spine[-1][0]+SH//2} V{BUS_Y}', DT, n=2, color='#334155', r=4.5) + '\n'
    for x, _, _, col in leaves:
        body += flow(f'M{x+LW//2},{BUS_Y} V{LY}', DT, n=2, color=col, r=4.5) + '\n'
    # ---- 起点呼吸圈 ----
    body += (f'<rect x="{SCX-SW//2-5}" y="{92-SH//2-5}" width="{SW+10}" height="{SH+10}" rx="14" fill="none" '
             f'stroke="#f59e0b" stroke-width="3" opacity="0">'
             f'<animate attributeName="opacity" values="0.1;0.85;0.1" dur="2.4s" repeatCount="indefinite"/></rect>')
    beats = [
        ('① 上电无反应：别急着拆——先分清是「没电」「没复位」还是「没时钟」', '#2563eb'),
        ('② 输入电压在不在：电源线 / 保险 / 极性 / 连接器——30 秒排除最常见的 17.1', '#dc2626'),
        ('③ 关键电源轨都对吗：带载跌落、纹波、使能脚——静态对 ≠ 动态对', '#b45309'),
        ('④ 复位与时钟正常吗：复位 IC、晶振起振、上电时序——数字电路的「心跳」', '#7c3aed'),
        ('⑤ 有电有复位却功能异常：按表现分流——不动 / 读数错 / 时好时坏 / 发热，各归其表', '#059669'),
    ]
    caps = ''
    for i, (txt, col) in enumerate(beats):
        a, b = i * 0.2, (i + 1) * 0.2
        if i < len(beats) - 1:
            caps += caption(txt, col, DT, "0;0;1;1;0;0",
                            f"0;{a:.2f};{a+0.02:.2f};{b:.2f};{b+0.02:.2f};1", y=530) + '\n'
        else:
            caps += caption(txt, col, DT, "0;0;1;1", f"0;{a:.2f};{a+0.02:.2f};1", y=530) + '\n'
    svg = svg_open('排故决策树：从「上电无反应」到具体表项', h=575)
    svg += f'''
<text x="400" y="58" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">先定方向、再查细节——每一「否」都直接落到一张速查表，别在细节里迷路</text>
{body}
'''
    svg += caps
    save('diagnosis-tree.svg', svg + '</svg>')

# ======================= 图 103：电容直流偏压降容（第 1 章 §1.7） =======================
def make_cap_derating():
    """教学示例，非厂商实测：5V 时 10µF × 26% = 2.6µF。

    曲线、扫压圆点、5V 工作点共用一组样本；不按介质代码规定降容百分比。
    原理依据：https://article.murata.com/en-us/article/voltage-characteristics-of-electrostatic-capacitance
    """
    duration = 12
    x0, x1, y0, y1 = 150, 690, 340, 140
    samples = [(0, 1), (1, .93), (2, .80), (3, .62), (4, .43), (5, .26), (6.3, .15)]
    points = [(x0 + v / 6.3 * (x1 - x0), y0 - r * (y0 - y1)) for v, r in samples]
    curve = 'M' + ' L'.join(f'{x:.4f},{y:.4f}' for x, y in points)
    times = ';'.join(f'{v / 6.3:.8f}' for v, _ in samples)
    px, py = points[5]
    svg = svg_open('电容直流偏压：标称容量 ≠ 工作容量', h=590)
    svg += f'''<desc>教学示意曲线，不代表任何具体料号。假设 10µF 电容在 5V 下保持率为 26%，有效容量为 2.6µF。</desc>
<text x="400" y="53" text-anchor="middle" font-size="12" fill="#475569">教学示例，非实测曲线；实际降容请查具体料号与测试条件</text>
<rect x="60" y="76" width="680" height="330" rx="10" fill="#f8fafc" stroke="#64748b" stroke-width="1.6"/>
<text x="400" y="100" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#334155">纵轴：有效容量 / 零偏压容量（各自归一化）</text>
<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#64748b" stroke-width="1.6"/>
<line x1="{x0}" y1="240" x2="{x1}" y2="240" stroke="#cbd5e1" stroke-dasharray="4,5"/>
<text x="138" y="144" text-anchor="end" font-size="11" fill="#475569">100%</text>
<text x="138" y="244" text-anchor="end" font-size="11" fill="#475569">50%</text>
<text x="138" y="344" text-anchor="end" font-size="11" fill="#475569">0</text>
<text x="{x0}" y="362" text-anchor="middle" font-size="11" fill="#475569">0V</text>
<text x="{px:.4f}" y="362" text-anchor="middle" font-size="11" fill="#dc2626">5V</text>
<text x="{x1}" y="362" text-anchor="middle" font-size="11" fill="#475569">6.3V</text>
<text x="420" y="387" text-anchor="middle" font-size="11.5" fill="#475569">横轴：施加的直流偏压 →（圆点匀速扫压）</text>
<path d="M{x0},{y1} L{x1},{y1}" fill="none" stroke="#059669" stroke-width="3"/>
<text x="684" y="130" text-anchor="end" font-size="11" fill="#065f46">C0G 参考：基本不受直流偏压影响</text>
<path id="cap-bias-curve" d="{curve}" fill="none" stroke="#dc2626" stroke-width="3"/>
<text x="340" y="185" font-size="11" fill="#dc2626">II 类陶瓷：一条假设的降容曲线</text>
<line x1="{px:.4f}" y1="{py:.4f}" x2="{px:.4f}" y2="{y0}" stroke="#dc2626" stroke-dasharray="4,4"/>
<line x1="{x0}" y1="{py:.4f}" x2="{px:.4f}" y2="{py:.4f}" stroke="#dc2626" stroke-dasharray="4,4"/>
<text x="138" y="{py + 4:.4f}" text-anchor="end" font-size="11" fill="#dc2626">26%</text>
<circle id="cap-bias-point" cx="{px:.4f}" cy="{py:.4f}" r="6" fill="#dc2626"/>
<text x="370" y="321" font-size="12" font-weight="bold" fill="#dc2626">5V 示例：10µF × 26% = 2.6µF</text>
<circle id="cap-bias-sweep" cx="{x0}" cy="{y1}" r="5" fill="#b45309" filter="url(#pglow)">
<animate attributeName="cx" values="{';'.join(f'{x:.4f}' for x, _ in points)}" keyTimes="{times}" calcMode="linear" dur="{duration}s" repeatCount="indefinite"/>
<animate attributeName="cy" values="{';'.join(f'{y:.4f}' for _, y in points)}" keyTimes="{times}" calcMode="linear" dur="{duration}s" repeatCount="indefinite"/>
</circle>
'''
    svg += note_box('X5R / X7R 是温度特性代码，不是降容等级。'
                    '实际容量取决于料号、偏压、温度与测试条件；选型要查曲线。'
                    '本例忽略 ESR 且纹波电流相同，容量降至 26% 时容性纹波约增至 3.85 倍。',
                    y=439, dur=duration, w=650)
    svg += '<g id="cap-bias-captions">' + beat_captions([
        ('① 标称容量有测试条件；加上直流偏压后，有效容量可能下降', '#2563eb'),
        ('② 匀速扫过偏压轴：II 类陶瓷降容，C0G 参考线基本平坦', '#b45309'),
        ('③ 本例 5V 时保持率 26%：10µF 变为 2.6µF，并非实测值', '#dc2626'),
        ('④ 同纹波电流、忽略 ESR：容性纹波约增至 1/0.26 = 3.85 倍', '#7c3aed'),
    ], duration, y=548) + '</g>'
    save('cap-derating.svg', svg + '</svg>')

# ======================= 图 104：运放输入级选型（第 12 章 §12.13） =======================
def make_opamp_input_stage():
    """低源阻抗比 e_n，高源阻抗比 I_b·R_s —— 数据取自第 12 章 §12.13。

    R_s=1MΩ：BJT（I_b=20nA）→ 20mV，CMOS（I_b=1pA）→ 1µV，差四个数量级；
    R_s=10kΩ：热噪声 √(4kTR_s)≈12.9 nV/√Hz 是地板，BJT(e_n=5) 总噪声 13.8 胜 CMOS(e_n=20) 的 23.8。
    """
    duration = 12
    svg = svg_open('运放输入级选型：源阻抗决定一切', h=590)
    svg += ('<text x="400" y="53" text-anchor="middle" font-size="12" fill="#475569">'
            '判据只有一条：V_err = I_b × R_s —— 低阻比 e_n，高阻比 I_b</text>\n')

    cards = [
        ('BJT 输入级', '#dc2626', ('偏置电流 I_b', '10 nA ~ 1 µA'),
         ('电压噪声 e_n', '3 ~ 10 nV/√Hz'), ('电流噪声 i_n', '较高'),
         'Rs &lt; 30 kΩ', '低阻下 e_n 主导'),
        ('CMOS 输入级', '#2563eb', ('偏置电流 I_b', '1 pA ~ 1 nA'),
         ('电压噪声 e_n', '10 ~ 30 nV/√Hz'), ('电流噪声 i_n', '极低'),
         'Rs &gt; 300 kΩ', 'I_b·R_s 几乎为零'),
        ('JFET 输入级', '#059669', ('偏置电流 I_b', '1 pA ~ 30 pA'),
         ('电压噪声 e_n', '10 ~ 20 nV/√Hz'), ('电流噪声 i_n', '极低'),
         '30 kΩ ~ 300 kΩ', 'e_n 与 I_b 都低'),
    ]
    for i, (name, col, r1, r2, r3, best, why) in enumerate(cards):
        x0 = 40 + i * 243
        svg += (f'<rect x="{x0}" y="80" width="234" height="220" rx="10" fill="#f8fafc" '
                f'stroke="{col}" stroke-width="2"/>\n')
        svg += (f'<text x="{x0+117}" y="109" text-anchor="middle" font-size="15" font-weight="bold" '
                f'fill="{col}">{name}</text>\n')
        svg += (f'<line x1="{x0+16}" y1="121" x2="{x0+218}" y2="121" stroke="{col}" '
                f'stroke-opacity="0.35" stroke-width="1.5"/>\n')
        for j, (lab, val) in enumerate((r1, r2, r3)):
            yy = 148 + j * 26
            svg += f'<text x="{x0+16}" y="{yy}" font-size="11.5" fill="#475569">{lab}</text>\n'
            svg += (f'<text x="{x0+218}" y="{yy}" text-anchor="end" font-size="12" font-weight="bold" '
                    f'fill="#1e293b">{val}</text>\n')
        svg += (f'<line x1="{x0+16}" y1="226" x2="{x0+218}" y2="226" stroke="{col}" '
                f'stroke-opacity="0.35" stroke-width="1.5"/>\n')
        svg += f'<text x="{x0+16}" y="248" font-size="11.5" fill="#475569">最佳区间</text>\n'
        svg += f'<text x="{x0+16}" y="270" font-size="13" font-weight="bold" fill="{col}">{best}</text>\n'
        svg += f'<text x="{x0+16}" y="290" font-size="11" fill="#475569">{why}</text>\n'

    svg += ('<rect x="40" y="320" width="720" height="112" rx="10" fill="#eff6ff" '
            'stroke="#2563eb" stroke-opacity="0.45" stroke-width="1.5"/>\n')
    svg += ('<text x="400" y="344" text-anchor="middle" font-size="12" font-weight="bold" '
            'fill="#1d4ed8">按源阻抗选输入级（横轴为对数刻度）</text>\n')
    svg += ('<line x1="70" y1="396" x2="730" y2="396" stroke="#64748b" stroke-width="1.4" '
            'stroke-dasharray="3,4"/>\n')
    for x1, x2, col, lab, cx in ((70, 314, '#dc2626', 'BJT 最佳', 192),
                                 (314, 479, '#059669', 'JFET 过渡区', 396),
                                 (479, 730, '#2563eb', 'CMOS 最佳', 604)):
        svg += f'<line x1="{x1}" y1="396" x2="{x2}" y2="396" stroke="{col}" stroke-width="9"/>\n'
        svg += (f'<text x="{cx}" y="372" text-anchor="middle" font-size="11.5" font-weight="bold" '
                f'fill="{col}">{lab}</text>\n')
    for tx, lab in ((70, '1 kΩ'), (314, '30 kΩ'), (479, '300 kΩ'), (730, '10 MΩ')):
        svg += f'<text x="{tx}" y="418" text-anchor="middle" font-size="10.5" fill="#475569">{lab}</text>\n'
    svg += ('<circle r="6" fill="#b45309" filter="url(#pglow)">'
            '<animateMotion dur="12s" begin="-3s" repeatCount="indefinite" path="M70,396 L730,396"/></circle>\n')

    svg += note_box('低阻源看 e_n（BJT 胜），高阻源看 I_b（CMOS / JFET 胜）：'
                    '1 MΩ 配 20 nA 就是 20 mV 直流误差，比运放自身的 V_os 大两个数量级。',
                    y=470, dur=duration, w=680)
    svg += beat_captions([
        ('① 三种输入级：先看 I_b、e_n、i_n 三个数，别看"低噪声"三个字', '#2563eb'),
        ('② 低源阻抗：热噪声 12.9 nV/√Hz 是地板，比的是 e_n → BJT 赢 1.7 倍', '#dc2626'),
        ('③ 高源阻抗 1 MΩ：BJT 的 I_b·R_s = 20 mV，CMOS 只有 1 µV —— 差四个数量级', '#059669'),
        ('④ RRIO 的代价：互补输入对在中点 g_m 凹陷 → 交越失真 + 失调台阶', '#7c3aed'),
    ], duration, y=555)
    save('opamp-input-stage.svg', svg + '</svg>')

# ======================= 图 105：晶体振荡器 Pierce 拓扑（第 13 章 §13.10） =======================
def make_crystal_pierce():
    """Pierce 拓扑 + 负阻判据：数据取自第 13 章 §13.10。

    22pF+22pF、C_stray=4pF → C_L=15pF；牵引灵敏度 18 ppm/pF（32.768kHz）；
    g_m,crit：8MHz 0.26 mA/V、32.768kHz 1.7 µA/V（这就是 RTC 能把功耗做到 µA 级的根因）。
    """
    duration = 12
    svg = svg_open('晶体振荡器：把频率钉在石英上', h=520)
    svg += ('<text x="400" y="53" text-anchor="middle" font-size="12" fill="#475569">'
            'Pierce 拓扑：一只反相器 + 反馈电阻 + 晶体 + 两只负载电容</text>\n')

    # ---- 左：电路 ----
    svg += ('<rect x="36" y="76" width="384" height="286" rx="10" fill="#f8fafc" '
            'stroke="#64748b" stroke-width="1.6"/>\n')
    svg += ('<text x="228" y="100" text-anchor="middle" font-size="12.5" font-weight="bold" '
            'fill="#334155">Pierce（皮尔斯）拓扑</text>\n')
    svg += '<line x1="150" y1="146" x2="160" y2="146" stroke="#334155" stroke-width="2.5"/>\n'
    svg += resistor_h(180, 146, 100, label='R_f 1~10 MΩ') + '\n'
    svg += '<line x1="300" y1="146" x2="310" y2="146" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<text x="226" y="190" text-anchor="middle" font-size="11" fill="#475569">反相器</text>\n'
    svg += '<polygon points="200,198 200,234 252,216" fill="#f8fafc" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<circle cx="256" cy="216" r="4" fill="#f8fafc" stroke="#334155" stroke-width="2"/>\n'
    svg += '<line x1="150" y1="216" x2="200" y2="216" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<line x1="260" y1="216" x2="310" y2="216" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<line x1="150" y1="146" x2="150" y2="306" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<line x1="310" y1="146" x2="310" y2="306" stroke="#334155" stroke-width="2.5"/>\n'
    # 晶体符号：两片电极板夹一块石英
    svg += '<line x1="150" y1="276" x2="214" y2="276" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<line x1="214" y1="264" x2="214" y2="288" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<rect x="220" y="260" width="20" height="32" rx="2" fill="#f8fafc" stroke="#334155" stroke-width="2"/>\n'
    svg += '<line x1="246" y1="264" x2="246" y2="288" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<line x1="246" y1="276" x2="310" y2="276" stroke="#334155" stroke-width="2.5"/>\n'
    svg += '<text x="230" y="252" text-anchor="middle" font-size="11" fill="#475569">XTAL 8 MHz</text>\n'
    for cx in (150, 310):
        svg += f'<line x1="{cx-12}" y1="306" x2="{cx+12}" y2="306" stroke="#334155" stroke-width="2.5"/>\n'
        svg += f'<line x1="{cx-12}" y1="316" x2="{cx+12}" y2="316" stroke="#334155" stroke-width="2.5"/>\n'
        svg += f'<line x1="{cx}" y1="316" x2="{cx}" y2="330" stroke="#334155" stroke-width="2.5"/>\n'
        svg += gnd_sym(cx, 344) + '\n'
    svg += '<text x="130" y="312" text-anchor="end" font-size="11.5" fill="#475569">C1</text>\n'
    svg += '<text x="130" y="326" text-anchor="end" font-size="10.5" fill="#475569">22 pF</text>\n'
    svg += '<text x="330" y="312" font-size="11.5" fill="#475569">C2</text>\n'
    svg += '<text x="330" y="326" font-size="10.5" fill="#475569">22 pF</text>\n'

    # ---- 右：为什么准 ----
    svg += ('<rect x="432" y="76" width="332" height="286" rx="10" fill="#eff6ff" '
            'stroke="#2563eb" stroke-opacity="0.45" stroke-width="1.5"/>\n')
    svg += ('<text x="598" y="104" text-anchor="middle" font-size="13" font-weight="bold" '
            'fill="#1d4ed8">为什么晶体准得离谱</text>\n')
    svg += ('<line x1="448" y1="116" x2="748" y2="116" stroke="#2563eb" '
            'stroke-opacity="0.3" stroke-width="1.5"/>\n')
    for j, txt in enumerate([
        '· Q 值 10⁴ ~ 10⁶（LC 只有 10 ~ 100）',
        '· 温漂 ±0.5 ppm/℃ 以内',
        '· C_L = C₁C₂/(C₁+C₂) + C_stray',
        '· 牵引灵敏度 ≈ 18 ppm/pF',
        '· 判据 R_neg ≥ 5 × ESR_max',
        '· g_m,crit = 4·ESR·ω²·(C₀+C_L)²',
        '· 8 MHz → 0.26 mA/V',
        '· 32.768 kHz → 1.7 µA/V',
    ]):
        svg += f'<text x="452" y="{142 + j*26}" font-size="11.5" fill="#334155">{txt}</text>\n'

    svg += note_box('别拿示波器探针直接量晶振引脚——10pF 探头会把 C_L 拉偏，'
                    '严重时直接停振；想测就量缓冲后的输出。',
                    y=400, dur=duration, w=660)
    svg += beat_captions([
        ('① 石英是机械谐振：Q 值 10⁴~10⁶，频率对元件容差极不敏感', '#2563eb'),
        ('② 唯一必须算的数：C_L = C₁C₂/(C₁+C₂) + C_stray，22pF+22pF → 15pF', '#059669'),
        ('③ 起振判据 R_neg ≥ 5×ESR；32.768kHz 只要 1.7 µA/V —— RTC 省电的根因', '#b45309'),
        ('④ 配错 C_L：18 ppm/pF × 3pF = 55 ppm → 每天差 4.8 秒', '#dc2626'),
    ], duration, y=485)
    save('crystal-pierce.svg', svg + '</svg>')

# ======================= 图 106：光耦与隔离（第 13 章 §13.11） =======================
def make_optocoupler_ctr():
    """CTR 是设计变量：按档位最小值 + 老化余量设计。数据取自第 13 章 §13.11。"""
    duration = 12
    svg = svg_open('光耦与隔离：CTR 是设计变量，不是常数', h=500)
    svg += ('<text x="400" y="53" text-anchor="middle" font-size="12" fill="#475569">'
            '信号能过，电流不能过：I_C = CTR × I_F</text>\n')

    svg += ('<rect x="36" y="76" width="400" height="268" rx="10" fill="#f8fafc" '
            'stroke="#64748b" stroke-width="1.6"/>\n')
    svg += ('<rect x="52" y="96" width="150" height="204" rx="8" fill="#fef2f2" '
            'stroke="#dc2626" stroke-width="1.6"/>\n')
    svg += ('<rect x="210" y="96" width="52" height="204" rx="6" fill="#eff6ff" '
            'stroke="#2563eb" stroke-width="1.6" stroke-dasharray="5,4"/>\n')
    svg += ('<rect x="270" y="96" width="150" height="204" rx="8" fill="#eff6ff" '
            'stroke="#2563eb" stroke-width="1.6"/>\n')
    svg += '<text x="127" y="120" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#dc2626">输入侧</text>\n'
    svg += '<text x="345" y="120" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#2563eb">输出侧</text>\n'
    svg += '<line x1="127" y1="142" x2="127" y2="166" stroke="#dc2626" stroke-width="2.5"/>\n'
    svg += '<polygon points="115,166 139,166 127,190" fill="#dc2626"/>\n'
    svg += '<line x1="115" y1="194" x2="139" y2="194" stroke="#dc2626" stroke-width="3.5"/>\n'
    svg += '<line x1="127" y1="194" x2="127" y2="216" stroke="#dc2626" stroke-width="2.5"/>\n'
    svg += '<text x="127" y="240" text-anchor="middle" font-size="11.5" fill="#334155">I_F = 4.5 mA</text>\n'
    svg += '<text x="127" y="260" text-anchor="middle" font-size="11" fill="#475569">V_F ≈ 1.2 V</text>\n'
    svg += '<text x="236" y="196" text-anchor="middle" font-size="11.5" fill="#1d4ed8">隔离栅</text>\n'
    svg += '<text x="236" y="216" text-anchor="middle" font-size="10" fill="#2563eb">kV 级</text>\n'
    svg += flow('M146,180 L300,180', duration, n=4, color='#f59e0b', r=4.5) + '\n'
    svg += ('<rect x="311" y="146" width="68" height="52" rx="6" fill="#f8fafc" '
            'stroke="#2563eb" stroke-width="1.8"/>\n')
    svg += '<text x="345" y="170" text-anchor="middle" font-size="11.5" fill="#2563eb">光敏</text>\n'
    svg += '<text x="345" y="188" text-anchor="middle" font-size="11.5" fill="#2563eb">三极管</text>\n'
    svg += '<text x="345" y="234" text-anchor="middle" font-size="11.5" fill="#334155">I_C = CTR × I_F</text>\n'
    svg += '<text x="345" y="256" text-anchor="middle" font-size="11" fill="#475569">CTR 50% ~ 600%</text>\n'
    svg += ('<text x="236" y="322" text-anchor="middle" font-size="11" fill="#334155">'
            '两个地之间没有欧姆通路：信号能过，电流不能过</text>\n')

    svg += ('<rect x="452" y="76" width="312" height="268" rx="10" fill="#fffbeb" '
            'stroke="#b45309" stroke-opacity="0.5" stroke-width="1.5"/>\n')
    svg += ('<text x="608" y="104" text-anchor="middle" font-size="13" font-weight="bold" '
            'fill="#92400e">CTR 的三个坑</text>\n')
    svg += ('<line x1="468" y1="116" x2="748" y2="116" stroke="#b45309" '
            'stroke-opacity="0.35" stroke-width="1.5"/>\n')
    for j, txt in enumerate([
        '① 同一型号分档：50% ~ 600%',
        '   设计按该档最小值算',
        '② 随温度与时间衰减',
        '   100℃ / 20mA 十年可能掉一半',
        '③ I_F &lt; 1mA 时 CTR 明显下降',
        '结论：最小值 × 2 倍老化余量',
        'R_in 470Ω → I_F = 4.5 mA',
    ]):
        svg += f'<text x="468" y="{144 + j*26}" font-size="11.5" fill="#334155">{txt}</text>\n'

    svg += note_box('隔离侧电源必须来自隔离侧——借原边的地，隔离就白做了。',
                    y=390, dur=duration, w=660)
    svg += beat_captions([
        ('① 隔离的本质：信号能过，电流不能过——两个地之间没有欧姆通路', '#2563eb'),
        ('② 光耦 = LED + 光敏三极管，中间隔着 kV 级绝缘', '#b45309'),
        ('③ CTR 按档位最小值算：50% 与 600% 是同一型号的两个档', '#dc2626'),
        ('④ 老化后 CTR 掉一半：R_in 从 1kΩ 改 470Ω，I_F 由 2.1mA 提到 4.5mA', '#059669'),
    ], duration, y=460)
    save('optocoupler-ctr.svg', svg + '</svg>')

# ======================= 图 107：误差预算 WC vs RSS（第 14 章 §14.8） =======================
def make_error_budget():
    """Buck 反馈分压的误差预算：WC ±2.7%，1σ ±0.45% → 3σ ±1.35%。数据取自 §14.8。"""
    duration = 12
    svg = svg_open('误差预算：最坏情况 vs 统计叠加', h=490)
    svg += ('<text x="400" y="53" text-anchor="middle" font-size="12" fill="#475569">'
            'Buck 反馈分压：WC ±2.7%，1σ ±0.45% → 3σ ±1.35%</text>\n')

    svg += ('<rect x="36" y="76" width="372" height="252" rx="10" fill="#f8fafc" '
            'stroke="#64748b" stroke-width="1.6"/>\n')
    svg += ('<text x="222" y="102" text-anchor="middle" font-size="12.5" font-weight="bold" '
            'fill="#334155">误差源与贡献</text>\n')
    svg += '<text x="56" y="130" font-size="11" fill="#475569">误差源</text>\n'
    svg += '<text x="272" y="130" text-anchor="end" font-size="11" fill="#475569">WC 贡献</text>\n'
    svg += '<text x="392" y="130" text-anchor="end" font-size="11" fill="#475569">1σ 贡献</text>\n'
    svg += '<line x1="52" y1="140" x2="392" y2="140" stroke="#cbd5e1" stroke-width="1.5"/>\n'
    for j, (a, b, c) in enumerate([
        ('反馈电阻容差 ±1%', '±1.0%', '±0.24%'),
        ('V_ref 初始精度 ±1%', '±1.0%', '±0.33%'),
        ('V_ref 温漂 50ppm/℃ × 40℃', '±0.2%', '±0.07%'),
        ('负载调整率', '±0.5%', '±0.17%'),
    ]):
        yy = 166 + j * 26
        svg += f'<text x="56" y="{yy}" font-size="11.5" fill="#334155">{a}</text>\n'
        svg += f'<text x="272" y="{yy}" text-anchor="end" font-size="11.5" fill="#1e293b">{b}</text>\n'
        svg += f'<text x="392" y="{yy}" text-anchor="end" font-size="11.5" fill="#1e293b">{c}</text>\n'
    svg += '<line x1="52" y1="260" x2="392" y2="260" stroke="#cbd5e1" stroke-width="1.5"/>\n'
    svg += '<text x="56" y="286" font-size="12" font-weight="bold" fill="#dc2626">合计</text>\n'
    svg += '<text x="272" y="286" text-anchor="end" font-size="12" font-weight="bold" fill="#dc2626">±2.7%</text>\n'
    svg += '<text x="392" y="286" text-anchor="end" font-size="12" font-weight="bold" fill="#2563eb">±0.45%</text>\n'

    svg += ('<rect x="428" y="76" width="336" height="252" rx="10" fill="#eff6ff" '
            'stroke="#2563eb" stroke-opacity="0.45" stroke-width="1.5"/>\n')
    svg += ('<text x="596" y="102" text-anchor="middle" font-size="12.5" font-weight="bold" '
            'fill="#1d4ed8">同一规格，两种结论</text>\n')
    svg += ('<rect x="504" y="170" width="184" height="22" rx="5" fill="#fef2f2" '
            'stroke="#dc2626" stroke-width="2"/>\n')
    svg += ('<rect x="550" y="202" width="92" height="22" rx="5" fill="#dbeafe" '
            'stroke="#2563eb" stroke-width="2"/>\n')
    svg += ('<line x1="596" y1="162" x2="596" y2="232" stroke="#334155" stroke-width="1.6" '
            'stroke-dasharray="4,4"/>\n')
    svg += '<text x="492" y="186" text-anchor="end" font-size="11.5" fill="#dc2626">WC</text>\n'
    svg += '<text x="492" y="218" text-anchor="end" font-size="11.5" fill="#2563eb">3σ</text>\n'
    svg += '<text x="694" y="186" font-size="11" fill="#dc2626">±2.7%</text>\n'
    svg += '<text x="648" y="218" font-size="11" fill="#2563eb">±1.35%</text>\n'
    svg += ('<text x="596" y="252" text-anchor="middle" font-size="11" fill="#334155">'
            '规格 ±1% → 良率 ≈ 97.5%（每千块 25 块超规）</text>\n')
    svg += '<text x="596" y="278" text-anchor="middle" font-size="11" fill="#475569">规格 ±2% → 良率 &gt; 99.7%</text>\n'
    svg += '<text x="596" y="304" text-anchor="middle" font-size="11" fill="#475569">3σ 大约只有 WC 的一半</text>\n'

    svg += note_box('车规 / 医疗按 WC 定规格，消费类按 RSS 的 3σ 估良率——'
                    '"留 20% 裕量"不是拍脑袋，是算出来的。',
                    y=360, dur=duration, w=660)
    svg += beat_captions([
        ('① WC：所有元件同时往同一方向偏到极限 —— 悲观，但概率极低', '#dc2626'),
        ('② RSS：各项独立随机，按 σ 平方和开根 —— 接近真实', '#2563eb'),
        ('③ 本例：WC ±2.7%，1σ ±0.45% → 3σ ±1.35%，约只有 WC 的一半', '#b45309'),
        ('④ 良率：规格 ±1% → 2Φ(2.24)−1 ≈ 97.5%，每千块 25 块超规', '#7c3aed'),
    ], duration, y=450)
    save('error-budget.svg', svg + '</svg>')

# ======================= 图 108：探头地线环（第 14 章 §14.8） =======================
def make_probe_ground_loop():
    """量到的纹波可能是假的：长地线夹形成大环路，拾取开关磁场。数据取自 §14.8。"""
    duration = 12
    svg = svg_open('探头地线环：量到的纹波可能是假的', h=500)
    svg += ('<text x="400" y="53" text-anchor="middle" font-size="12" fill="#475569">'
            '地夹夹在远处的地上 → 大环路 → 开关磁场在环里感应出电压</text>\n')

    svg += ('<rect x="36" y="76" width="356" height="248" rx="10" fill="#fef2f2" '
            'stroke="#dc2626" stroke-width="1.6"/>\n')
    svg += ('<text x="214" y="102" text-anchor="middle" font-size="12" font-weight="bold" '
            'fill="#dc2626">① 长地线夹：环路大</text>\n')
    svg += ('<path d="M170,152 C 240,132 310,152 330,214 L330,220 L170,220 Z" '
            'fill="#dc2626" fill-opacity="0.10"/>\n')
    svg += '<line x1="60" y1="220" x2="368" y2="220" stroke="#334155" stroke-width="3"/>\n'
    svg += ('<path d="M170,152 C 240,132 310,152 330,214" fill="none" '
            'stroke="#dc2626" stroke-width="2.2"/>\n')
    svg += '<line x1="170" y1="152" x2="170" y2="220" stroke="#dc2626" stroke-width="2.5"/>\n'
    svg += ('<rect x="156" y="118" width="28" height="34" rx="4" fill="#f8fafc" '
            'stroke="#334155" stroke-width="2"/>\n')
    svg += '<rect x="324" y="208" width="12" height="12" fill="#dc2626"/>\n'
    svg += pulse(240, 158, 60, 46, '#b45309', 1.4, 8) + '\n'
    svg += '<text x="270" y="188" text-anchor="middle" font-size="10.5" fill="#b45309">磁通</text>\n'
    svg += f'<path d="{sine_path(70, 360, 282, 14)}" fill="none" stroke="#dc2626" stroke-width="2.5"/>\n'
    svg += '<text x="214" y="316" text-anchor="middle" font-size="11" fill="#dc2626">量到 ~200 mV 假纹波</text>\n'

    svg += ('<rect x="408" y="76" width="356" height="248" rx="10" fill="#ecfdf5" '
            'stroke="#059669" stroke-width="1.6"/>\n')
    svg += ('<text x="586" y="102" text-anchor="middle" font-size="12" font-weight="bold" '
            'fill="#059669">② 弹簧地针：环路小</text>\n')
    svg += '<line x1="432" y1="220" x2="740" y2="220" stroke="#334155" stroke-width="3"/>\n'
    svg += '<path d="M596,206 L608,206 L608,220 L596,220 Z" fill="#059669" fill-opacity="0.20"/>\n'
    svg += '<line x1="596" y1="152" x2="596" y2="220" stroke="#059669" stroke-width="2.5"/>\n'
    svg += ('<rect x="582" y="118" width="28" height="34" rx="4" fill="#f8fafc" '
            'stroke="#334155" stroke-width="2"/>\n')
    svg += '<line x1="596" y1="206" x2="608" y2="206" stroke="#059669" stroke-width="2.2"/>\n'
    svg += '<line x1="608" y1="206" x2="608" y2="220" stroke="#059669" stroke-width="2.2"/>\n'
    svg += f'<path d="{sine_path(442, 730, 282, 5)}" fill="none" stroke="#059669" stroke-width="2.5"/>\n'
    svg += '<text x="586" y="316" text-anchor="middle" font-size="11" fill="#059669">量到真实纹波</text>\n'

    svg += note_box('地夹夹在远处的地上就形成大环路，开关电源的磁场在里面感应出电压；'
                    '弹簧地针把环路面积缩十倍以上。',
                    y=360, dur=duration, w=660)
    svg += beat_captions([
        ('① 探头的地夹也是导线：夹在远处的地上，就形成一个天线', '#dc2626'),
        ('② 开关电源的磁场穿过这个大环路 → 感应出假的 200 mV', '#b45309'),
        ('③ 弹簧地针把环路面积缩十倍以上，读数立刻干净', '#059669'),
        ('④ 高共模节点（高侧检测、H 桥输出）必须用差分探头', '#7c3aed'),
    ], duration, y=460)
    save('probe-ground-loop.svg', svg + '</svg>')

# ======================= 图 115：预测对实测（第 18 章 §18.2） =======================
def make_predict_measure():
    """Williams 仪式：下探头前先写下预测，实测超 20% 对账线就停手改模型。数字取自 §18.2。"""
    DUR = 12
    svg = svg_open('预测对实测：对不上的地方才是线索', h=540)
    svg += ('<text x="400" y="62" text-anchor="middle" font-size="12.5" fill="#475569">'
            '100kΩ × 1µF 上电复位：先把 69ms 写在纸上，再去抓波形</text>\n')
    # 左：预测曲线（τ=100ms，终值 5V，1τ=3.15V，2.5V 阈值 @ RC·ln2≈69ms）
    svg += ('<rect x="36" y="82" width="356" height="260" rx="10" fill="#eff6ff" '
            'stroke="#2563eb" stroke-width="1.6"/>\n')
    svg += ('<text x="214" y="108" text-anchor="middle" font-size="12.5" font-weight="bold" '
            'fill="#2563eb">① 纸上预测</text>\n')
    px0, px1, pybase, pytop = 66, 372, 300, 130   # 5V 在 pytop，0V 在 pybase
    pts = []
    for i in range(41):
        t = i / 40 * 3.2                          # 0~3.2τ
        x = px0 + (px1 - px0) * i / 40
        y = pybase - (pybase - pytop) * (1 - np.exp(-t))
        pts.append(f"{x:.0f},{y:.0f}")
    svg += f'<path d="{"M" + " L".join(pts)}" fill="none" stroke="#2563eb" stroke-width="2.5"/>\n'
    y_25 = pybase - (pybase - pytop) * 0.5        # 2.5V 阈值线
    y_1t = pybase - (pybase - pytop) * 0.632      # 1τ → 3.15V
    x_69 = px0 + (px1 - px0) * (0.693 / 3.2)
    x_1t = px0 + (px1 - px0) * (1.0 / 3.2)
    svg += f'<line x1="{px0}" y1="{y_25:.0f}" x2="{px1}" y2="{y_25:.0f}" stroke="#b45309" stroke-width="1.2" stroke-dasharray="4 4"/>\n'
    svg += f'<text x="{px1-4}" y="{y_25-5:.0f}" text-anchor="end" font-size="10.5" fill="#b45309">阈值 2.5V</text>\n'
    svg += f'<circle cx="{x_69:.0f}" cy="{y_25:.0f}" r="4.5" fill="#2563eb"/>\n'
    svg += f'<text x="{x_69:.0f}" y="{y_25+18:.0f}" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#2563eb">69ms</text>\n'
    svg += f'<circle cx="{x_1t:.0f}" cy="{y_1t:.0f}" r="4.5" fill="#2563eb"/>\n'
    svg += f'<text x="{x_1t+8:.0f}" y="{y_1t-8:.0f}" font-size="10.5" fill="#2563eb">1τ → 3.15V</text>\n'
    svg += f'<text x="214" y="330" text-anchor="middle" font-size="11" fill="#2563eb">t = RC·ln2 ≈ 69ms　写下来再测</text>\n'
    # 右：实测曲线（终值腰斩 ~2.5V、τ 减半 → 并着 ~100kΩ 漏电）
    svg += ('<rect x="408" y="82" width="356" height="260" rx="10" fill="#fef2f2" '
            'stroke="#dc2626" stroke-width="1.6"/>\n')
    svg += ('<text x="586" y="108" text-anchor="middle" font-size="12.5" font-weight="bold" '
            'fill="#dc2626">② 示波器实测</text>\n')
    qx0, qx1 = 438, 744
    pts = []
    for i in range(41):
        t = i / 40 * 3.2
        x = qx0 + (qx1 - qx0) * i / 40
        y = pybase - (pybase - pytop) * 0.5 * (1 - np.exp(-2 * t))
        pts.append(f"{x:.0f},{y:.0f}")
    svg += f'<path d="{"M" + " L".join(pts)}" fill="none" stroke="#dc2626" stroke-width="2.5"/>\n'
    pts = []
    for i in range(41):
        t = i / 40 * 3.2
        x = qx0 + (qx1 - qx0) * i / 40
        y = pybase - (pybase - pytop) * (1 - np.exp(-t))
        pts.append(f"{x:.0f},{y:.0f}")
    svg += f'<path d="{"M" + " L".join(pts)}" fill="none" stroke="#2563eb" stroke-width="1.4" stroke-dasharray="5 4" opacity="0.55"/>\n'
    qx_1t = qx0 + (qx1 - qx0) * (1.0 / 3.2)
    y_m1t = pybase - (pybase - pytop) * 0.5 * (1 - np.exp(-2.0))
    svg += f'<circle cx="{qx_1t:.0f}" cy="{y_m1t:.0f}" r="4.5" fill="#dc2626"/>\n'
    svg += f'<text x="{qx_1t+8:.0f}" y="{y_m1t+16:.0f}" font-size="10.5" font-weight="bold" fill="#dc2626">1τ 实测 2.2V</text>\n'
    svg += f'<text x="586" y="126" text-anchor="middle" font-size="10.5" fill="#64748b">（虚线=预测）</text>\n'
    svg += f'<text x="586" y="330" text-anchor="middle" font-size="11" fill="#dc2626">终值腰斩＋缓段更平 → 并着 ~100kΩ 漏电</text>\n'
    svg += flow(f'M{px0},{pybase} H{qx1}', DUR, n=3, color='#b45309', r=5)
    svg += note_box('对账阈值 20%：偏差在阈值内继续往下测；超线就停手改模型——'
                    '继续测只是在给错误的模型收集更多噪声。',
                    y=376, dur=DUR, w=660)
    svg += beat_captions([
        ('① 下探头之前，先把预期电平、幅度、时间尺度写在纸上：2.5V 阈值 @ 69ms', '#2563eb'),
        ('② 实测 140ms——偏差超 100%，撞破 20% 对账线，停手', '#b45309'),
        ('③ 另一个现场：1τ 应读 3.15V，实测只有 2.2V，缓段还更平', '#dc2626'),
        ('④ 终值减半＋τ 减半，两条线索同指：节点上并着一只 ~100kΩ 漏电阻', '#059669'),
    ], DUR, y=478)
    save('predict-measure.svg', svg + '</svg>')

# ======================= 图 116：间歇故障三把扳手（第 17 章 §17.6） =======================
def make_intermittent_forcing():
    """间歇故障逼迫流程：机械/热/电三把扳手轮着上，把"一天一次"逼成"按一下就坏"。取自 §17.6。"""
    DUR = 12
    svg = svg_open('间歇故障：先逼它现身，再在窗口里等它', h=540)
    svg += ('<text x="400" y="62" text-anchor="middle" font-size="12.5" fill="#475569">'
            '它在台上不出现，一切测量都失去靶子——所以先用应力把它逼成半必现</text>\n')
    wrenches = [
        ('机械应力', '#2563eb', '按压 · 扭转 · 轻敲', '虚焊/连接器松动'),
        ('热应力', '#dc2626', '冷冻喷剂 · 热风枪', '参数漂移/热应力裂纹'),
        ('电应力', '#b45309', '电压拉偏 · 负载阶跃', '裕度不足/闩锁边缘'),
    ]
    body = ''
    for i, (name, col, tools, target) in enumerate(wrenches):
        x = 60 + i * 240
        body += (f'<rect x="{x}" y="96" width="200" height="96" rx="11" fill="#f8fafc" '
                 f'stroke="{col}" stroke-width="2.5"/>\n'
                 f'<text x="{x+100}" y="124" text-anchor="middle" font-size="13.5" '
                 f'font-weight="bold" fill="{col}">{name}</text>\n'
                 f'<text x="{x+100}" y="148" text-anchor="middle" font-size="11.5" '
                 f'fill="#334155">{tools}</text>\n'
                 f'<text x="{x+100}" y="172" text-anchor="middle" font-size="10" '
                 f'fill="#64748b">主抓：{target}</text>\n')
        body += pulse(x + 100, 144, 180, 76, col, 1.6 + 0.3 * i, 10) + '\n'
        body += flow(f'M{x+100},196 V256', DUR, n=2, color=col, r=5)
    # 漏斗：复现率提升
    body += ('<path d="M180,266 L620,266 L470,330 L330,330 Z" fill="#f7eedb" '
             'stroke="#b45309" stroke-width="2"/>\n'
             '<text x="400" y="292" text-anchor="middle" font-size="12" font-weight="bold" '
             'fill="#b45309">每把单独用，记录哪一把改变复现率</text>\n'
             '<text x="400" y="316" text-anchor="middle" font-size="12.5" font-weight="bold" '
             'fill="#b45309">「一天一次」 → 「按一下就坏」</text>\n')
    body += flow('M400,336 V378', DUR, n=2, color='#b45309', r=5)
    # 测量窗口
    body += ('<rect x="120" y="384" width="560" height="64" rx="11" fill="#ecfdf5" '
             'stroke="#059669" stroke-width="2.2"/>\n'
             '<text x="400" y="410" text-anchor="middle" font-size="12.5" font-weight="bold" '
             'fill="#059669">复现窗口里挂着等：单次触发 / 毛刺触发 / 欠幅触发</text>\n'
             '<text x="400" y="434" text-anchor="middle" font-size="11.5" fill="#334155">'
             '晃动试验用通断蜂鸣档——一声断续，抵得上十分钟盯屏</text>\n')
    svg += body
    svg += beat_captions([
        ('① 间歇故障是最难缠的对手：它在台上不出现，一切测量都失去靶子', '#52606d'),
        ('② 三把扳手轮着上，每把单独用：机械扭转、冷冻热风、电压拉偏', '#2563eb'),
        ('③ 记录哪一把能显著改变复现率——从"一天一次"提到"按一下就坏"', '#b45309'),
        ('④ 然后在复现窗口里测量：单次/毛刺/欠幅触发挂着等，蜂鸣档听断续', '#059669'),
    ], DUR, y=494)
    save('intermittent-forcing.svg', svg + '</svg>')

def make_ground_bounce():
    """地弹：8 路输出同时翻转，160mA 瞬时电流挤过地脚电感，把"地"弹起来。数字取自 §5.1 动态功耗段。"""
    DUR = 12
    svg = svg_open('地弹：8 路同翻，把"地"弹起来', h=600)
    svg += ('<text x="400" y="62" text-anchor="middle" font-size="12.5" fill="#475569">'
            '8 个输出同时翻转 × 每路 20mA = 160mA 瞬时电流，全挤进公共地引脚</text>\n')
    body = ''
    # 顶部：8 路驱动器方块，在尖峰窗口（40%~60%）同时点亮
    for i in range(8):
        x = 90 + i * 78
        body += (f'<rect x="{x}" y="96" width="52" height="40" rx="7" fill="#eff6ff" '
                 f'stroke="#2563eb" stroke-width="1.8"/>'
                 f'<rect x="{x}" y="96" width="52" height="40" rx="7" fill="#dc2626" '
                 f'fill-opacity="0.28" opacity="0">'
                 f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
                 f'keyTimes="0;0.40;0.44;0.56;0.60;1" dur="{DUR}s" '
                 f'repeatCount="indefinite"/></rect>\n')
    body += ('<text x="400" y="88" text-anchor="middle" font-size="11.5" '
             'fill="#334155">8 路输出同时翻转（驱动档 20mA）</text>\n')
    body += flow('M400,142 V178', DUR, n=3, color='#dc2626', r=5,
                 keypoints='0;0.40;0.60;1', keytimes='0;0.40;0.60;1')
    body += ('<text x="452" y="168" font-size="11.5" font-weight="bold" fill="#dc2626">'
             'Σ 160mA 瞬时</text>\n')
    # 中部：两条波形——I_gnd 电流尖峰 / V_gnd 地弹（L·di/dt，沿上正沿下负）
    X0, X1 = 80, 720
    yI, yG = 260, 400
    body += (f'<text x="70" y="{yG+4}" text-anchor="end" font-size="12" '
             f'font-weight="bold" fill="#b45309">V（地）</text>\n'
             f'<text x="88" y="{yG-52}" text-anchor="end" font-size="11" fill="#64748b">'
             f'地脚走线电感 L</text>\n')
    for yc, col in ((yG, '#b45309'),):
        body += (f'<line x1="{X0}" y1="{yc}" x2="{X1}" y2="{yc}" stroke="#cbd5e1" '
                 f'stroke-width="1"/>\n')
    t0, t1 = 0.40, 0.60                     # 尖峰窗口
    x0, x1 = X0 + (X1 - X0) * t0, X0 + (X1 - X0) * t1
    xm = (x0 + x1) / 2
    # I_gnd：梯形尖峰 160mA
    body += (f'<path d="M{X0},{yI} L{x0},{yI} L{x0+18},{yI-64} L{x1-18},{yI-64} '
             f'L{x1},{yI} L{X1},{yI}" fill="none" stroke="#dc2626" stroke-width="2.6"/>\n'
             f'<text x="{xm+8:.0f}" y="{yI-72}" font-size="11.5" font-weight="bold" '
             f'fill="#dc2626">I（地）尖峰 160mA</text>\n')
    # V_gnd：di/dt 在上升沿顶出正尖、下降沿拽出负尖
    body += (f'<path d="M{X0},{yG} L{x0},{yG} L{x0+14},{yG-46} L{x0+30},{yG} '
             f'L{x1-30},{yG} L{x1-14},{yG+46} L{x1},{yG} L{X1},{yG}" fill="none" '
             f'stroke="#b45309" stroke-width="2.6"/>\n'
             f'<text x="{xm+8:.0f}" y="{yG-40}" font-size="11.5" font-weight="bold" '
             f'fill="#b45309">地弹 = L·di/dt</text>\n')
    # 底部：一路安静输出的高电平被拽出毛刺
    yQ = 500
    body += (f'<text x="70" y="{yQ+4}" text-anchor="end" font-size="12" '
             f'font-weight="bold" fill="#5b666f">安静输出</text>\n'
             f'<path d="M{X0},{yQ-30} L{x0},{yQ-30} L{x0+14},{yQ+14} L{x0+30},{yQ-30} '
             f'L{x1-30},{yQ-30} L{x1-14},{yQ+14} L{x1},{yQ-30} L{X1},{yQ-30}" fill="none" '
             f'stroke="#5b666f" stroke-width="2.4"/>\n'
             f'<text x="{x1+10:.0f}" y="{yQ+18}" font-size="11" fill="#5b666f">'
             f'它没翻转，电平却跟着抖——地被弹起来了</text>\n')
    # 扫动游标
    body += (f'<line x1="{X0}" y1="196" x2="{X0}" y2="540" stroke="#0f766e" '
             f'stroke-width="1.6" stroke-dasharray="6 4" opacity="0.75">'
             f'<animateTransform attributeName="transform" type="translate" '
             f'values="0 0;{X1-X0} 0" keyTimes="0;1" dur="{DUR}s" '
             f'repeatCount="indefinite"/></line>\n')
    svg += body
    svg += beat_captions([
        ('① 8 路输出同时翻转，每路 20mA——瞬时 160mA 全挤进公共地引脚', '#2563eb'),
        ('② 地脚走线有电感 L：I（地）尖峰一出，L·di/dt 把"地"往上顶', '#dc2626'),
        ('③ 上升沿顶出正尖、下降沿拽出负尖——安静的输出跟着抖出毛刺', '#b45309'),
        ('④ 对策：大电流翻转分散开、地引脚多给几只、低速信号别配高档驱动', '#059669'),
    ], DUR, y=574)
    save('ground-bounce.svg', svg + '</svg>')

def make_three_probe_audit():
    """先量电源的执行版：稳压器脚、芯片电源脚、去耦电容三触点对账，160mV 差折算 1.3Ω 路径电阻。取自 §18.1~18.2。"""
    DUR = 12
    svg = svg_open('三触点对账：160mV 去了哪里', h=560)
    svg += ('<text x="400" y="62" text-anchor="middle" font-size="12.5" fill="#475569">'
            '「先量电源」不是看一眼 5V 在不在——三处读数只在毫伏级上才允许有差别</text>\n')
    body = ''
    # PCB 轮廓
    body += ('<rect x="44" y="92" width="712" height="240" rx="14" fill="#f8fafc" '
             'stroke="#94a3b8" stroke-width="2"/>\n')
    # LDO 块与运放块
    body += ('<rect x="84" y="150" width="128" height="96" rx="10" fill="#eff6ff" '
             'stroke="#2563eb" stroke-width="2.2"/>\n'
             '<text x="148" y="190" text-anchor="middle" font-size="13" font-weight="bold" '
             'fill="#2563eb">LDO 稳压器</text>\n'
             '<text x="148" y="214" text-anchor="middle" font-size="11" fill="#334155">输出脚</text>\n')
    body += ('<rect x="588" y="150" width="128" height="90" rx="10" fill="#ecfdf5" '
             'stroke="#059669" stroke-width="2.2"/>\n'
             '<text x="652" y="190" text-anchor="middle" font-size="13" font-weight="bold" '
             'fill="#059669">运放</text>\n'
             '<text x="652" y="214" text-anchor="middle" font-size="11" fill="#334155">VCC 脚</text>\n')
    # 供电细走线（0.2mm×200mm，蛇形示意），串两个过孔
    body += ('<path d="M212,196 C300,196 320,258 400,258 C480,258 500,196 588,196" '
             'fill="none" stroke="#b45309" stroke-width="3.5"/>\n')
    for vx in (330, 470):
        body += (f'<circle cx="{vx}" cy="227" r="6" fill="#fff" stroke="#b45309" '
                 f'stroke-width="2.2"/>\n')
    body += ('<text x="400" y="286" text-anchor="middle" font-size="11" fill="#b45309">'
             '0.2mm 宽 × 200mm 长 ≈ 1000 个方 → 仅走线 ≈0.5Ω，再叠过孔与接插件</text>\n')
    # 去耦电容
    body += ('<line x1="652" y1="240" x2="652" y2="286" stroke="#334155" stroke-width="2"/>\n'
             '<line x1="636" y1="290" x2="668" y2="290" stroke="#334155" stroke-width="2.6"/>\n'
             '<line x1="640" y1="300" x2="664" y2="300" stroke="#334155" stroke-width="2.6"/>\n'
             '<line x1="652" y1="304" x2="652" y2="318" stroke="#334155" stroke-width="2"/>\n'
             '<text x="700" y="300" font-size="11" fill="#334155">去耦电容</text>\n')
    # 三只探头（按节拍依次出现，出现后保留）
    probes = [
        ((212, 196), '①', '5.02V', '#2563eb', (86, 118)),
        ((588, 196), '②', '4.86V', '#dc2626', (500, 118)),
        ((652, 322), '③', '4.86V 复核', '#059669', (520, 322)),
    ]
    n_beats = 5
    for i, ((px, py), tag, reading, col, (tx, ty)) in enumerate(probes):
        a = i / n_beats
        fade = 0.02
        kt = f'0;{a:.4f};{a+fade:.4f};1'
        kv = f'0;0;1;1'
        body += (f'<g opacity="0">'
                 f'<animate attributeName="opacity" values="{kv}" keyTimes="{kt}" '
                 f'dur="{DUR}s" repeatCount="indefinite"/>'
                 f'<circle cx="{px}" cy="{py}" r="9" fill="{col}"/>'
                 f'<text x="{px}" y="{py+4}" text-anchor="middle" font-size="10.5" '
                 f'font-weight="bold" fill="#fff">{tag}</text>'
                 f'<text x="{tx}" y="{ty}" font-size="13" font-weight="bold" '
                 f'fill="{col}">{reading}</text></g>\n')
    # 160mV 差值括号（第 4 拍出现）
    a = 3 / n_beats
    kt = f'0;{a:.4f};{a+0.02:.4f};1'
    body += (f'<g opacity="0">'
             f'<animate attributeName="opacity" values="0;0;1;1" keyTimes="{kt}" '
             f'dur="{DUR}s" repeatCount="indefinite"/>'
             f'<path d="M212,128 v-10 M588,128 v-10 M212,128 H588" fill="none" '
             f'stroke="#dc2626" stroke-width="1.8"/>'
             f'<text x="400" y="118" text-anchor="middle" font-size="12.5" '
             f'font-weight="bold" fill="#dc2626">ΔV = 160mV @ 负载 120mA</text></g>\n')
    # 底部算式卡与结论
    body += ('<rect x="84" y="368" width="632" height="96" rx="11" fill="#fef2f2" '
             'stroke="#dc2626" stroke-width="2"/>\n'
             '<text x="400" y="398" text-anchor="middle" font-size="13" font-weight="bold" '
             'fill="#dc2626">160mV ÷ 120mA ≈ 1.3Ω 路径电阻</text>\n'
             '<text x="400" y="424" text-anchor="middle" font-size="11.5" fill="#334155">'
             '走线 ≈0.5Ω（0.5mΩ/方 × 1000 方）＋ 两个过孔 ＋ 一段接插件，1Ω 出头毫不稀奇</text>\n'
             '<text x="400" y="450" text-anchor="middle" font-size="12.5" font-weight="bold" '
             'fill="#5b666f">病灶在走线，不在芯片——换运放是冤枉好人</text>\n')
    svg += body
    svg += beat_captions([
        ('① 触点一：LDO 输出脚，带载量得 5.02V', '#2563eb'),
        ('② 触点二：运放 VCC 脚只剩 4.86V——160mV 在路上丢了', '#dc2626'),
        ('③ 触点三：去耦电容两端复核，差值复现才作数', '#059669'),
        ('④ 160mV ÷ 120mA ≈ 1.3Ω：走线 0.5Ω＋过孔＋接插件', '#b45309'),
        ('⑤ 三处读数只差毫伏级才算过——病灶在走线，不在芯片', '#5b666f'),
    ], DUR, y=516)
    save('three-probe-audit.svg', svg + '</svg>')

# ======================= 推导图 1：分压公式（第 0 章 0.3） =======================
def make_derive_divider():
    DD = 16
    steps = [
        ('① 同一股电流', 'I = Vin / (R1 + R2)', '串联电路电流处处相等，总阻 = R1 + R2'),
        ('② 下臂的压降', 'Vout = I · R2', '欧姆定律：压降 = 流过的电流 × 阻值'),
        ('③ 代入消去 I', 'Vout = Vin · R2 / (R1 + R2)', '把第①行代进第②行，只剩电阻比'),
        ('④ 代入数字', '12V × 10k / 20k = 6V', '两臂等阻 → 各分一半'),
    ]
    n = len(steps)
    left = f'''<text x="196" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">同一股电流：先过 R1，再下 R2</text>
<text x="58" y="128" font-size="12.5" font-weight="bold" fill="#b45309">Vin 12V</text>
<line x1="58" y1="140" x2="135" y2="140" stroke="#334155" stroke-width="2.5"/>
''' + resistor_v(135, 160, 40, 'R1 10k') + '''
<line x1="135" y1="220" x2="135" y2="268" stroke="#334155" stroke-width="2.5"/>
<circle cx="135" cy="268" r="3.5" fill="#334155"/>
<line x1="135" y1="268" x2="250" y2="268" stroke="#334155" stroke-width="2.5"/>
<circle cx="250" cy="268" r="3.5" fill="#334155"/>
''' + resistor_v(135, 288, 40, 'R2 10k') + '''
''' + gnd_sym(135, 362) + '''
'''
    left += flow("M58,140 L135,140 L135,348", DD, n=3)
    left += f'''<line x1="103" y1="160" x2="103" y2="200" stroke="#dc2626" stroke-width="2"/>
<polygon points="98,195 103,203 108,195" fill="#dc2626"/>
<text x="96" y="186" text-anchor="end" font-size="11" font-weight="bold" fill="#dc2626">I·R1 = 6V</text>'''
    left += f'''<line x1="103" y1="288" x2="103" y2="328" stroke="#2563eb" stroke-width="2"/>
<polygon points="98,323 103,331 108,323" fill="#2563eb"/>
<text x="96" y="314" text-anchor="end" font-size="11" font-weight="bold" fill="#2563eb">I·R2 = 6V</text>
<rect x="243" y="252" width="58" height="30" rx="5" fill="#eff6ff" stroke="#2563eb" stroke-width="1.4"/>
<text x="272" y="272" text-anchor="middle" font-size="12" font-weight="bold" fill="#2563eb">Vout</text>'''
    left += f'''{chip(196, 470, '上下两臂一样大 → 各分一半', '#059669', 12)}
{chip(196, 496, '换 R2=5k：12 × 5/15 = 4V', '#64748b', 11)}'''
    svg = derive_frame('分压公式四步推导：I 先算出来，再乘下臂电阻', steps, left, h=680, dur=DD)
    svg += note_box("分压公式不是凭空给的：串联同流 → 欧姆定律 → 代入。它只在空载时成立", 636, DD,
                    delay_kt=None, w=740)
    save('derive-divider.svg', svg + '</svg>')

# ======================= 推导图 2：纹波公式（第 2 章 2.3） =======================
def make_derive_ripple():
    DR_ = 16
    steps = [
        ('① 电容的电荷账', 'Q = I · Δt', '负载恒流 → 放掉的电荷 = 电流 × 时间'),
        ('② 电压跟着电荷走', 'ΔV = Q / C', '由 C = Q / U 反解'),
        ('③ 合起来', 'ΔV = I · Δt / C', '把第①行代进第②行'),
        ('④ 桥式整流补两次', 'ΔV = I / (2f · C)', '全波每周期补两次 → Δt = 1/(2f)'),
        ('⑤ 代入数字', '1A / (2×50×4700µF) ≈ 2.1V', '50Hz 市电、1A 负载、4700µF'),
    ]
    n = len(steps)
    left = '''<text x="196" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">峰顶充电、其余时间放电</text>
<line x1="58" y1="140" x2="135" y2="140" stroke="#334155" stroke-width="2.5"/>
<line x1="135" y1="140" x2="135" y2="188" stroke="#334155" stroke-width="2.5"/>
<line x1="103" y1="190" x2="167" y2="190" stroke="#334155" stroke-width="3"/>
<line x1="103" y1="200" x2="167" y2="200" stroke="#334155" stroke-width="3"/>
<line x1="135" y1="202" x2="135" y2="250" stroke="#334155" stroke-width="2.5"/>
<text x="176" y="200" font-size="12" font-weight="bold" fill="#2f7f96">4700µF</text>
<line x1="135" y1="140" x2="300" y2="140" stroke="#334155" stroke-width="2.5"/>
''' + resistor_v(300, 160, 40, '', lcolor='#dc2626') + '''
<text x="324" y="184" font-size="12" font-weight="bold" fill="#dc2626">1A 负载</text>
<line x1="300" y1="220" x2="300" y2="250" stroke="#334155" stroke-width="2.5"/>
<line x1="135" y1="250" x2="300" y2="250" stroke="#334155" stroke-width="2.5"/>
''' + gnd_sym(218, 264) + '''
<polyline points="60,432 108,398 156,432 204,398 252,432 300,398 348,432" fill="none" stroke="#2563eb" stroke-width="2.2"/>
<line x1="60" y1="398" x2="348" y2="398" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="60" y1="432" x2="348" y2="432" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<text x="362" y="404" font-size="11" fill="#475569">峰</text>
<text x="362" y="438" font-size="11" fill="#475569">谷</text>
'''
    left += flow("M58,140 L135,140 L135,188", DR_, n=2, color="#059669")
    left += f'''<text x="150" y="300" font-size="11.5" font-weight="bold" fill="#059669">放电时：Q 一层层流走</text>'''
    left += f'''<line x1="352" y1="398" x2="352" y2="432" stroke="#dc2626" stroke-width="2"/>
<polygon points="347,404 352,396 357,404" fill="#dc2626"/>
<polygon points="347,426 352,434 357,426" fill="#dc2626"/>
<text x="376" y="420" font-size="12" font-weight="bold" fill="#dc2626">ΔV</text>'''
    left += f'''<text x="196" y="330" font-size="11.5" font-weight="bold" fill="#b45309">100Hz 的「锯齿」就是这么来的</text>'''
    left += f'''{chip(196, 466, 'C 翻倍 → ΔV 减半；f 翻倍 → ΔV 也减半', '#059669', 11.5)}'''
    svg = derive_frame('纹波公式五步推导：电荷 → 电压 → 整流补几次', steps, left, h=680, dur=DR_)
    svg += note_box("公式里的每个量都有出处：Q 是账本，C 是水桶，2f 是「每周期补两次水」", 636, DR_,
                    delay_kt=None, w=740)
    save('derive-ripple.svg', svg + '</svg>')

# ======================= 推导图 3：共射增益（第 11 章 11.5） =======================
def make_derive_gain():
    DG = 16
    steps = [
        ('① 跨导的定义', 'gm = ΔIc / ΔVbe', '输入电压抖一下，集电极电流跟着抖多少'),
        ('② 室温下的数值', 'gm ≈ 38 · Ic', 'VT ≈ 26mV：Ic=1mA → 38mS'),
        ('③ 电流转电压', 'ΔVout = −ΔIc · Rc', '电流涨 → Rc 压降涨 → 输出跌（反相）'),
        ('④ 串成增益', 'Av = ΔVout/ΔVin = −gm · Rc', '把②③代进比值的定义'),
        ('⑤ 代入数字', '−38mS × 2kΩ ≈ −76', '≈ 37.6dB 的电压增益'),
    ]
    n = len(steps)
    left = f'''<text x="196" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">跨导把电压变成电流，Rc 再把电流变回电压</text>
<text x="330" y="118" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">12V</text>
<line x1="262" y1="130" x2="360" y2="130" stroke="#334155" stroke-width="2.5"/>
<rect x="140" y="190" width="120" height="72" rx="9" fill="#f8fafc" stroke="#2563eb" stroke-width="1.8"/>
<text x="200" y="222" text-anchor="middle" font-size="13" font-weight="bold" fill="#2563eb">gm</text>
<text x="200" y="244" text-anchor="middle" font-size="10.5" fill="#475569">ΔIc / ΔVbe</text>
<polyline points="40,226 52,208 64,244 76,208 88,244 100,226" fill="none" stroke="#b45309" stroke-width="2.2"/>
<text x="70" y="272" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#b45309">ΔVbe</text>
<text x="330" y="284" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">输出反相</text>
<polyline points="300,332 312,314 324,350 336,314 348,350 360,332" fill="none" stroke="#dc2626" stroke-width="2.2"/>
{chip(196, 392, '电流信号 → 电压信号：全靠 Rc 这件「外套」', '#059669', 11.5)}
'''
    left += f'''<polygon points="132,226 140,220 140,232" fill="#2563eb"/>
<line x1="100" y1="226" x2="140" y2="226" stroke="#2563eb" stroke-width="2.2"/>'''
    left += f'''<line x1="330" y1="130" x2="330" y2="148" stroke="#334155" stroke-width="2.5"/>''' + resistor_v(330, 148, 40, 'Rc 2k') + '''
<line x1="330" y1="208" x2="330" y2="226" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="226" r="3.5" fill="#334155"/>'''
    left += f'''<line x1="260" y1="226" x2="326" y2="226" stroke="#dc2626" stroke-width="2.2"/>
<polygon points="320,220 330,226 320,232" fill="#dc2626"/>
<text x="292" y="212" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">ΔIc</text>
<line x1="330" y1="226" x2="330" y2="270" stroke="#cbd5e1" stroke-width="1.2" stroke-dasharray="4,3"/>'''
    left += f'''<text x="200" y="340" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#b45309">同样的形状，倒过来、放大 76 倍</text>'''
    svg = derive_frame('共射增益五步推导：gm 把电压变电流，Rc 再变回电压', steps, left, h=680, dur=DG)
    svg += note_box("Av = −gm·Rc：提升增益要么加大 Ic（更费电），要么加大 Rc（压降预算不够就撞轨）", 636, DG,
                    delay_kt=None, w=740)
    save('derive-gain.svg', svg + '</svg>')

# ======================= 推导图 4：负反馈增益（第 12 章） =======================
def make_derive_feedback():
    DF_ = 16
    steps = [
        ('① 开环：先不带反馈', 'Vout = A · Vd', 'Vd 是放大器的净输入'),
        ('② 输出被采样回来', 'Vfb = β · Vout', 'β 就是电阻分压比'),
        ('③ 净输入被减掉一截', 'Vd = Vs − Vfb', '负反馈与输入「对着干」'),
        ('④ 联立', 'Vout = A · (Vs − β·Vout)', '把②③代进①'),
        ('⑤ 移项求商', 'Af = A / (1 + Aβ)', '闭环增益：分母帮了一个忙'),
        ('⑥ 深反馈极限', 'Aβ ≫ 1 → Af ≈ 1 / β', '增益只由电阻比决定，与 A 无关'),
    ]
    n = len(steps)
    left = f'''<text x="196" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">反馈环：把输出的样本「还」回输入端</text>
<text x="40" y="222" font-size="11.5" font-weight="bold" fill="#b45309">Vs</text>
<line x1="56" y1="230" x2="94" y2="230" stroke="#334155" stroke-width="2.5"/>
<polygon points="88,224 98,230 88,236" fill="#334155"/>
<circle cx="112" cy="230" r="14" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
<text x="112" y="235" text-anchor="middle" font-size="12" font-weight="bold" fill="#334155">Σ</text>
<text x="98" y="222" font-size="11" fill="#059669">+</text>
<text x="98" y="248" font-size="11" fill="#dc2626">−</text>
<rect x="176" y="196" width="112" height="68" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>
<text x="232" y="226" text-anchor="middle" font-size="15" font-weight="bold" fill="#2563eb">A</text>
<text x="232" y="246" text-anchor="middle" font-size="10" fill="#475569">开环增益</text>
<line x1="126" y1="230" x2="170" y2="230" stroke="#334155" stroke-width="2.5"/>
<polygon points="164,224 174,230 164,236" fill="#334155"/>
<line x1="288" y1="230" x2="352" y2="230" stroke="#334155" stroke-width="2.5"/>
<polygon points="346,224 356,230 346,236" fill="#334155"/>
<text x="362" y="234" font-size="11.5" font-weight="bold" fill="#dc2626">Vout</text>
<rect x="204" y="312" width="56" height="34" rx="7" fill="#f7eedb" stroke="#b45309" stroke-width="1.6"/>
<text x="232" y="335" text-anchor="middle" font-size="13" font-weight="bold" fill="#b45309">β</text>
{chip(196, 386, 'Aβ 越深，输出越听 β 的话、越不听 A 的话', '#059669', 11.5)}
'''
    left += f'''<line x1="352" y1="230" x2="380" y2="230" stroke="#dc2626" stroke-width="2.2" stroke-dasharray="5,3"/>'''
    left += f'''<line x1="352" y1="230" x2="352" y2="330" stroke="#b45309" stroke-width="2"/>
<line x1="352" y1="330" x2="288" y2="330" stroke="#b45309" stroke-width="2"/>
<line x1="176" y1="330" x2="112" y2="330" stroke="#b45309" stroke-width="2"/>
<line x1="112" y1="330" x2="112" y2="246" stroke="#b45309" stroke-width="2"/>
<polygon points="106,252 112,242 118,252" fill="#b45309"/>'''
    left += f'''<text x="264" y="404" text-anchor="middle" font-size="10.5" fill="#64748b">β 越小 → 反馈越浅 → 增益留得越多</text>'''
    left += f'''{chip(112, 430, 'Af ≈ 1/β', '#2563eb', 11.5)}
{chip(112, 452, '教科书答案', '#475569', 10.5)}'''
    svg = derive_frame('负反馈增益六步推导：从 Vout = A·Vd 到 Af ≈ 1/β', steps, left, h=680, dur=DF_)
    svg += note_box("闭环增益不靠管子精度，靠电阻比——这就是负反馈能让电路「不挑元件」的原因", 636, DF_,
                    delay_kt=None, w=740)
    save('derive-feedback.svg', svg + '</svg>')

# ======================= 推导图 5：米勒电容（第 11 章 11.5） =======================
def make_derive_miller():
    DM = 16
    steps = [
        ('① 敌人是谁', 'Cbc 跨在输入与输出之间', '共射的集电结电容、共源的 Cgd'),
        ('② 输出反着摆', 'ΔVc = −A · ΔVb', '共射反相：输入升，输出降'),
        ('③ 电容承受的压差', '(1+A)·ΔVb', '两端往相反方向跑，摆幅被撬大'),
        ('④ 折回输入端', 'C_in = Cbc · (1+A)', '同一份电荷，输入源要多供 (1+A) 倍'),
        ('⑤ 代入数字', '10pF × (1+100) ≈ 1.01nF', '10pF 的小电容，看起来像 1nF'),
        ('⑥ 带宽被谁定', 'f_H = 1/(2π·Rs·C_in) ≈ 15.8kHz', 'Rs=10kΩ：想放到 MHz？早滚降了'),
    ]
    n = len(steps)
    left = f'''<text x="196" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">一只小电容，被增益撬成一只大电容</text>
<text x="46" y="196" font-size="11.5" font-weight="bold" fill="#b45309">ΔVb</text>
<polyline points="36,300 52,286 68,314 84,286 100,314 116,300" fill="none" stroke="#b45309" stroke-width="2.2"/>
<line x1="116" y1="300" x2="150" y2="300" stroke="#334155" stroke-width="2.5"/>
<polygon points="144,294 154,300 144,306" fill="#334155"/>
<circle cx="168" cy="300" r="4" fill="#334155"/>
<text x="168" y="330" text-anchor="middle" font-size="11" font-weight="bold" fill="#334155">b</text>
<rect x="196" y="264" width="112" height="72" rx="9" fill="#eff6ff" stroke="#2563eb" stroke-width="1.8"/>
<text x="252" y="296" text-anchor="middle" font-size="15" font-weight="bold" fill="#2563eb">−A</text>
<text x="252" y="318" text-anchor="middle" font-size="10" fill="#475569">反相放大</text>
<line x1="168" y1="300" x2="192" y2="300" stroke="#334155" stroke-width="2.5"/>
<line x1="308" y1="300" x2="352" y2="300" stroke="#334155" stroke-width="2.5"/>
<polygon points="346,294 356,300 346,306" fill="#334155"/>
<circle cx="368" cy="300" r="4" fill="#334155"/>
<text x="368" y="330" text-anchor="middle" font-size="11" font-weight="bold" fill="#334155">c</text>
<text x="332" y="272" text-anchor="middle" font-size="10.5" font-weight="bold" fill="#dc2626">ΔVc = −A·ΔVb</text>
<line x1="168" y1="300" x2="168" y2="196" stroke="#2f7f96" stroke-width="2.2"/>
<line x1="168" y1="196" x2="236" y2="196" stroke="#2f7f96" stroke-width="2.2"/>
<line x1="236" y1="182" x2="236" y2="210" stroke="#2f7f96" stroke-width="3"/>
<line x1="252" y1="182" x2="252" y2="210" stroke="#2f7f96" stroke-width="3"/>
<line x1="252" y1="196" x2="368" y2="196" stroke="#2f7f96" stroke-width="2.2"/>
<line x1="368" y1="196" x2="368" y2="300" stroke="#2f7f96" stroke-width="2.2"/>
<text x="244" y="172" text-anchor="middle" font-size="12" font-weight="bold" fill="#2f7f96">Cbc 10pF</text>
{chip(196, 398, '两端压差 = ΔVb − ΔVc = (1+A)·ΔVb', '#2f7f96', 11)}
{chip(196, 434, '同一份电荷 Q = C·ΔU，输入源要多搬 A 倍', '#b45309', 11)}
'''
    left += flow("M168,196 L236,196", DM, n=1, color="#2f7f96", r=3.4)
    left += flow("M252,196 L368,196 L368,300", DM, n=1, color="#2f7f96", r=3.4)
    svg = derive_frame('米勒电容六步推导：为什么 10pF 看起来像 1nF', steps, left, h=680, dur=DM)
    svg += note_box("增益越高，这只寄生电容越「重」——带宽与增益，从管子出生那天就在互相挤压", 636, DM,
                    delay_kt=None, w=740)
    save('derive-miller.svg', svg + '</svg>')

# ======================= 推导图 6：降压纹波（第 13 章 13.2） =======================
def make_derive_buck():
    DK = 16
    steps = [
        ('① 电感电流是三角波', 'ΔIL = (Vin−Vout)·D / (L·fsw)', '伏秒平衡：开关期间爬升、关断期间下降'),
        ('② 电容只收「净电荷」', 'ΔQ = ½ · (ΔIL/2) · (T/2)', '三角波围出的面积 = ½×底×高'),
        ('③ 化简成频率', 'ΔQ = ΔIL / (8·fsw)', 'T/2 换成 1/(2fsw)，三角形摊成常数 1/8'),
        ('④ 电容定义', 'ΔV = ΔQ / C', 'C = Q/U 反解'),
        ('⑤ 合并', 'ΔV = ΔIL / (8·fsw·C)', '公式里的 8 是三角波的几何，不是怪数'),
        ('⑥ 代入数字', '0.884A / (8×150k×100µF) ≈ 7.4mV', 'L、C、fsw 三家一起决定纹波'),
    ]
    n = len(steps)
    left = f'''<text x="196" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">电感吃三角波，电容吃电荷</text>
<text x="40" y="118" font-size="11.5" font-weight="bold" fill="#b45309">Vin 12V</text>
<line x1="36" y1="130" x2="96" y2="130" stroke="#334155" stroke-width="2.5"/>
<rect x="96" y="114" width="56" height="32" rx="6" fill="#f8fafc" stroke="#2563eb" stroke-width="2"/>
<text x="124" y="135" text-anchor="middle" font-size="11" font-weight="bold" fill="#2563eb">S</text>
<text x="124" y="104" text-anchor="middle" font-size="10" fill="#475569">150kHz</text>
<line x1="152" y1="130" x2="180" y2="130" stroke="#334155" stroke-width="2.5"/>
<circle cx="166" cy="130" r="3.2" fill="#334155"/>
<line x1="166" y1="130" x2="166" y2="168" stroke="#334155" stroke-width="2.4"/>
<polygon points="157,182 175,182 166,168" fill="#fffbeb" stroke="#334155" stroke-width="2.2"/>
<line x1="154" y1="168" x2="178" y2="168" stroke="#334155" stroke-width="2.6"/>
<line x1="166" y1="182" x2="166" y2="204" stroke="#334155" stroke-width="2.4"/>
<line x1="152" y1="204" x2="180" y2="204" stroke="#334155" stroke-width="2.5"/>
<line x1="157" y1="212" x2="175" y2="212" stroke="#334155" stroke-width="2.5"/>
<line x1="162" y1="219" x2="170" y2="219" stroke="#334155" stroke-width="2.5"/>
<text x="184" y="176" font-size="11.5" font-weight="bold" fill="#b45309">续流 D</text>
<text x="184" y="192" font-size="10" fill="#475569">S 断开时电流从这里走</text>
<rect x="180" y="114" width="84" height="32" rx="6" fill="#fffbeb" stroke="#b45309" stroke-width="2"/>
<text x="222" y="135" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">L 22µH</text>
<line x1="264" y1="130" x2="330" y2="130" stroke="#334155" stroke-width="2.5"/>
<circle cx="330" cy="130" r="4" fill="#334155"/>
<text x="356" y="134" font-size="11.5" font-weight="bold" fill="#dc2626">Vout 5V</text>
<line x1="330" y1="130" x2="330" y2="176" stroke="#334155" stroke-width="2.5"/>
<line x1="292" y1="178" x2="368" y2="178" stroke="#334155" stroke-width="3"/>
<line x1="292" y1="190" x2="368" y2="190" stroke="#334155" stroke-width="3"/>
<line x1="330" y1="192" x2="330" y2="216" stroke="#334155" stroke-width="2.5"/>
<line x1="314" y1="216" x2="346" y2="216" stroke="#334155" stroke-width="2.5"/>
<line x1="320" y1="224" x2="340" y2="224" stroke="#334155" stroke-width="2.5"/>
<line x1="326" y1="232" x2="334" y2="232" stroke="#334155" stroke-width="2.5"/>
<text x="378" y="188" font-size="11" font-weight="bold" fill="#2f7f96">100µF</text>
<polyline points="44,340 98,296 152,340 206,296 260,340 314,296" fill="none" stroke="#dc2626" stroke-width="2.2"/>
<line x1="44" y1="296" x2="318" y2="296" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="44" y1="340" x2="318" y2="340" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>
<line x1="330" y1="296" x2="330" y2="340" stroke="#dc2626" stroke-width="2"/>
<polygon points="325,302 330,294 335,302" fill="#dc2626"/>
<polygon points="325,334 330,342 335,334" fill="#dc2626"/>
<text x="344" y="322" font-size="11.5" font-weight="bold" fill="#dc2626">ΔIL</text>
{chip(196, 404, '电容不「制造」纹波，只是把电感的多余电荷兜住', '#2f7f96', 11)}
'''
    left += flow("M36,130 L92,130", DK, n=2, color="#dc2626", r=3.6)
    svg = derive_frame('降压纹波六步推导：那个 8 是三角波的面积', steps, left, h=680, dur=DK)
    svg += note_box("要更小的纹波？加大 C（线性）、提高 fsw（线性）、或加粗 L（线性）——三条路都写在同一行式子里", 636, DK,
                    delay_kt=None, w=740)
    save('derive-buck.svg', svg + '</svg>')

if __name__ == '__main__':
    make_rc_charge()
    make_bridge_rectifier()
    make_bjt_amplify()
    make_mosfet_switch()
    make_opamp_inverting()
    make_comparator_hysteresis()
    make_ne555_astable()
    make_pushpull_opendrain()
    make_ldo_feedback()
    make_analog_switch()
    make_cap_decoupling()
    make_pcb_return_path()
    make_diff_pair()
    make_buck_converter()
    make_wien_bridge()
    make_class_b()
    make_sallen_key()
    make_current_mirror()
    make_boost_converter()
    make_precision_rectifier()
    make_miller_effect()
    make_instrumentation_amp()
    make_rlc_resonance()
    make_sar_adc()
    make_bandgap()
    make_tl431()
    make_sample_hold()
    make_charge_pump()
    make_rc_lowpass()
    make_zener_regulator()
    make_constant_current()
    make_peak_detector()
    make_inverting_buckboost()
    make_ne555_monostable()
    make_h_bridge()
    make_clipper_clamper()
    make_neg_feedback()
    make_integrator()
    make_virtual_ground()
    make_schmitt_osc()
    make_impedance_freq()
    make_opamp_internals()
    make_debug_flow()
    make_fault_lookup()
    make_master_wisdom()
    make_design_flow()
    make_thinking_toolbox()
    make_ground_star()
    make_transformer()
    make_divider_loading()
    make_bjt_regions()
    make_signal_chain()
    make_thermal_runaway()
    make_cap_parasitics()
    make_miller_plateau()
    make_opamp_slew()
    make_diode_iv()
    make_comparator_opamp()
    make_noise_budget()
    make_probe_loading()
    make_transfer_gate()
    make_three_topologies()
    make_tristate_bus()
    make_pushpull_stage()
    make_lm393_inside()
    make_ref_showdown()
    make_pn_junction()
    make_mosfet_curves()
    make_555_modes()
    make_feedback_topo()
    make_resistor_model()
    make_diode_family()
    make_pullup_sizing()
    make_lm358_dual()
    make_bjt_configs()
    make_discrete_ldo()
    make_bjt_transport()
    make_bjt_switch()
    make_body_diode()
    make_mux4051()
    make_darlington()
    make_opamp_map()
    make_datasheet_params()
    make_ldo_failures()
    make_bjt_diagnosis()
    make_opamp_pitfalls()
    make_comparator_pitfalls()
    make_555_params()
    make_source_types()
    make_thevenin()
    make_compliance_voltage()
    make_ce_dynamic()
    make_mosfet_four_beats()
    make_rectifier_filter_beats()
    make_analog_switch_beats()
    make_ldo_transient_beats()
    make_555_astable_beats()
    make_water_analogy()
    make_power_tree()
    make_voltage_drop()
    make_pcb_routing()
    make_diagnosis_tree()
    make_cap_derating()
    make_opamp_input_stage()
    make_crystal_pierce()
    make_optocoupler_ctr()
    make_error_budget()
    make_probe_ground_loop()
    make_predict_measure()
    make_intermittent_forcing()
    make_ground_bounce()
    make_three_probe_audit()
    make_derive_divider()
    make_derive_ripple()
    make_derive_gain()
    make_derive_feedback()
    make_derive_miller()
    make_derive_buck()
    print(f'all {len(os.listdir(OUT))} SVGs regenerated into', os.path.abspath(OUT))

def _exp_axis(x, y, w, h, xlab, ylab):
    """左栏小坐标轴：返回轴线与端标签的 SVG 片段。"""
    return (f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y}" stroke="#94a3b8" stroke-width="1.4"/>\n'
            f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y - h}" stroke="#94a3b8" stroke-width="1.4"/>\n'
            f'<text x="{x + w + 4}" y="{y + 4}" font-size="11" fill="#64748b">{xlab}</text>\n'
            f'<text x="{x - 4}" y="{y - h - 4}" font-size="11" fill="#64748b">{ylab}</text>\n')


def _exp_vline_note(x, y1, y2, text, color="#dc2626"):
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{color}" stroke-width="2"/>\n'
            f'<text x="{x + 4}" y="{y1 + 10}" font-size="11" font-weight="bold" fill="{color}">{text}</text>\n')


def make_exp_source_sag():
    D = 14
    steps = [
        ('① 空载读数', 'V0 = 12.10 V', '先量开路电压'),
        ('② 接已知负载', 'V1 = 11.90 V @ 100Ω', '让电压掉 1%~5% 最合适'),
        ('③ 反推内阻', 'Rs = 100Ω × 0.20 / 11.90 ≈ 1.7Ω', '两次测量法（0.6 节）'),
        ('④ 外推塌陷', '2A → ΔV ≈ 3.4 V', '带不动：先看内阻再谈稳压'),
    ]
    left = _exp_axis(56, 300, 240, 150, 'I', 'V')
    left += '<line x1="56" y1="150" x2="296" y2="266" stroke="#b45309" stroke-width="2.4"/>\n'
    left += '<line x1="56" y1="150" x2="296" y2="150" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="5,4"/>\n'
    left += _exp_vline_note(180, 150, 208, '2A → 塌 3.4V')
    left += chip(180, 360, '斜率 = 输出阻抗 Rs', '#b45309', 12)
    left += chip(180, 390, '恒压源的性格由 Rs 决定', '#64748b', 11)
    svg = derive_frame('源的两次测量法：内阻一笔算出（失效边界）', steps, left, h=680, dur=D)
    svg += note_box("空载 12.10V、带 100Ω 后 11.90V → Rs≈1.7Ω；2A 负载要塌 3.4V——带载能力先看内阻", 636, D, delay_kt=None, w=740)
    save('exp-source-sag.svg', svg + '</svg>')

def make_exp_unit_guard():
    D = 14
    steps = [
        ('① 正确换档', '10 kΩ × 100 nF', '10⁴ × 10⁻⁷ = 10⁻³ s'),
        ('② 误当 100 µF', '10⁴ × 10⁻⁴ = 1 s', '差 1000 倍'),
        ('③ 误当 10 Ω', '10 × 10⁻⁷ = 1 µs', '又差 1000 倍'),
        ('④ 数量级闸', '先估「毫秒级」再按计算器', '算出 1s 或 1µs 立刻暴露'),
    ]
    left = _exp_axis(56, 330, 250, 120, '结果（s）', '')
    for x, lab, c in [(90, '1µs', '#64748b'), (180, '1ms ✓', '#059669'), (272, '1s', '#dc2626')]:
        left += f'<line x1="{x}" y1="210" x2="{x}" y2="330" stroke="{c}" stroke-width="2" stroke-dasharray="4,3"/>\n'
        left += f'<text x="{x - 10}" y="200" font-size="12" font-weight="bold" fill="{c}">{lab}</text>\n'
    left += chip(180, 400, '词头 m 与 M 差十亿倍', '#dc2626', 12)
    left += chip(180, 430, '算式旁先写单位再代数', '#64748b', 11)
    svg = derive_frame('单位错档一千倍：数量级先钉死', steps, left, h=680, dur=D)
    svg += note_box("τ = RC 的三种种结果：1µs / 1ms / 1s——先估数量级，再谈精度（0.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-unit-guard.svg', svg + '</svg>')

def make_exp_esr_ripple_split():
    D = 14
    steps = [
        ('① 容性纹波', 'ΔVc = ΔIL / (8 f C)', '22µF、0.6A、500kHz → 6.8mV'),
        ('② ESR 纹波', 'ΔVesr = ΔIL × ESR', '3mΩ → 1.8mV'),
        ('③ 换电解再看', '200mΩ → 120mV', '容量降到 1.5mV，ESR 说了算'),
        ('④ 药方', '低 ESR 加容量；高 ESR 先降 ESR', '同一句「纹波大」，两本账'),
    ]
    left = '<text x="56" y="110" font-size="13" font-weight="bold" fill="#334155">两种输出电容的纹波构成（示意）</text>\n'
    for i, (x, name, c, cap_h, esr_h) in enumerate([(110, '22µF 陶瓷', '#059669', 60, 18), (260, '100µF 电解', '#dc2626', 14, 120)]):
        left += f'<rect x="{x - 40}" y="{340 - cap_h}" width="34" height="{cap_h}" fill="#eff6ff" stroke="#2563eb" stroke-width="1.4"/>\n'
        left += f'<rect x="{x + 2}" y="{340 - esr_h}" width="34" height="{esr_h}" fill="#fef2f2" stroke="#dc2626" stroke-width="1.4"/>\n'
        left += f'<text x="{x}" y="360" text-anchor="middle" font-size="12" fill="#334155">{name}</text>\n'
    left += '<text x="70" y="180" font-size="11" fill="#2563eb">容性</text>\n'
    left += '<text x="70" y="200" font-size="11" fill="#dc2626">ESR</text>\n'
    left += '<line x1="62" y1="340" x2="330" y2="340" stroke="#94a3b8" stroke-width="1.4"/>\n'
    left += chip(196, 420, '谷底低而宽才叫去耦好手', '#059669', 12)
    svg = derive_frame('纹波的两本账：容性与 ESR 谁说了算', steps, left, h=680, dur=D)
    svg += note_box("22µF 陶瓷：容性 6.8mV 主导；100µF 电解：ESR 120mV 主导——药方各开各的（1.2 节算一笔）", 636, D, delay_kt=None, w=740)
    save('exp-esr-ripple-split.svg', svg + '</svg>')

def make_exp_cap_life():
    D = 14
    steps = [
        ('① 寿命公式', 'L = L0 × 2^((T0−T)/10)', '10°C 翻倍法则'),
        ('② 代入', '2000h @105°C，工作 65°C', 'L = 2000 × 2⁴'),
        ('③ 结果', '32000 h ≈ 3.7 年（连续通电）', '自发热算进 T'),
        ('④ 加速老化', '纹波电流超 30% → 寿命腰斩', 'ESR 发热直接抬 T'),
    ]
    left = _exp_axis(56, 320, 240, 160, '温度 (°C)', '寿命')
    left += '<path d="M56 160 Q150 210 296 300" fill="none" stroke="#dc2626" stroke-width="2.4"/>\n'
    for x, y, lab in [(110, 186, '85°'), (170, 216, '95°'), (240, 260, '105°')]:
        left += f'<circle cx="{x}" cy="{y}" r="4" fill="#b45309"/>\n'
        left += f'<text x="{x + 6}" y="{y - 6}" font-size="11" fill="#64748b">{lab}</text>\n'
    left += chip(180, 400, '第一个坏的总是电解电容', '#dc2626', 12)
    left += chip(180, 430, '换固态/聚合物，或提 L0 到 5000h+', '#64748b', 11)
    svg = derive_frame('电解电容寿命账：10°C 翻倍（失效边界）', steps, left, h=680, dur=D)
    svg += note_box("2000h@105°C 的电容工作在 65°C → 约 3.7 年；纹波电流超额 30% 再腰斩（1.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-cap-life.svg', svg + '</svg>')

def make_exp_conduction_angle():
    D = 14
    steps = [
        ('① 纹波账', 'ΔV = I·Δt/C ≈ 2.1 V', '1A、4700µF、全波 100Hz'),
        ('② 导通窗口', 'Δt_on ≈ 3 ms（峰顶小窗）', '只在 |vAC| > vC+2VF 导通'),
        ('③ 峰值电流', 'Ipk ≈ 1A × 10ms/3ms ≈ 3.3A', '全部电荷窄窗补回'),
        ('④ 再加 ESR', 'Ipk×ESR → 实际 4~5A', '选管看 IFRM 与结温'),
    ]
    left = _exp_axis(56, 320, 240, 150, 't (10ms)', 'v')
    left += '<path d="M56 200 Q106 130 156 200 Q206 270 256 200 Q281 165 296 185" fill="none" stroke="#2563eb" stroke-width="2.2"/>\n'
    left += '<line x1="126" y1="150" x2="186" y2="150" stroke="#dc2626" stroke-width="4" opacity="0.8"/>\n'
    left += '<text x="132" y="140" font-size="11" font-weight="bold" fill="#dc2626">导通窗 ≈3ms</text>\n'
    left += '<line x1="56" y1="270" x2="296" y2="270" stroke="#94a3b8" stroke-width="1" stroke-dasharray="4,3"/>\n'
    left += chip(180, 400, '平均 1A ≠ 峰值 3.3A', '#b45309', 12)
    left += chip(180, 430, 'IFRM（重复峰值）才是选型行', '#64748b', 11)
    svg = derive_frame('导通角与峰值电流：窄窗里的猛冲', steps, left, h=680, dur=D)
    svg += note_box("1A 平均的整流管每周期挨一次 3.3A 窄脉冲——选型看重复峰值与结温，不只看标称（2.6 节）", 636, D, delay_kt=None, w=740)
    save('exp-conduction-angle.svg', svg + '</svg>')

def make_exp_tvs_ladder():
    D = 14
    steps = [
        ('① 浪涌进来', 'IEC 8kV：330Ω/150pF', '系统级波形，前沿小于 1ns'),
        ('② TVS 先泄放', '钳到 9.2V @ 24A', '能量走地，Ppp≈223W'),
        ('③ 电阻限流', '(9.2−5.7)/330 ≈ 10mA', '把残压压到毫安级'),
        ('④ 芯片钳位兜底', '内部二极管最后一级', '三级缺一，芯片先死'),
    ]
    left = ''
    for i, (y, name, val, c) in enumerate([(130, '8kV 浪涌', 'IEC 脉冲', '#dc2626'),
                                           (230, 'TVS 9.2V', '泄放大能量', '#b45309'),
                                           (330, '330Ω → 10mA', '电阻限流', '#2563eb'),
                                           (430, 'GPIO 安全', '内部钳位兜底', '#059669')]):
        left += f'<rect x="70" y="{y - 24}" width="220" height="40" rx="6" fill="#f6eedb" stroke="{c}" stroke-width="1.6"/>\n'
        left += f'<text x="180" y="{y + 2}" text-anchor="middle" font-size="13" font-weight="bold" fill="{c}">{name} · {val}</text>\n'
        if i < 3:
            left += f'<line x1="180" y1="{y + 16}" x2="180" y2="{y + 56}" stroke="#94a3b8" stroke-width="2"/>\n'
            left += f'<polygon points="175,{y + 50} 185,{y + 50} 180,{y + 62}" fill="#94a3b8"/>\n'
    svg = derive_frame('接口防护三级削减：TVS → 电阻 → 钳位', steps, left, h=680, dur=D)
    svg += note_box("TVS 负责泄大能量，电阻+内部钳位负责毫安级残压——只装 TVS 不串电阻，芯片还是可能被打死（2.11 例 2-2）", 636, D, delay_kt=None, w=740)
    save('exp-tvs-ladder.svg', svg + '</svg>')

def make_exp_beta_drift():
    D = 14
    steps = [
        ('① β 在漂', '100 → 600（同型号合法范围）', '批次、温度都在动'),
        ('② 固定偏置', 'IB 不变 → IC = β·IB', 'IC 撞饱和，放大变开关'),
        ('③ 分压偏置', 'RE 负反馈拉住 IC', '同一漂移只动 ~4%'),
        ('④ 设计铁律', '按「β 怎么变都不怕」设计', 'Q 点居中 + RE 兜底'),
    ]
    left = '<text x="56" y="110" font-size="13" font-weight="bold" fill="#334155">同一漂移，两种偏置的 IC 落点</text>\n'
    left += '<line x1="70" y1="150" x2="330" y2="150" stroke="#94a3b8" stroke-width="1.2"/>\n'
    left += '<text x="336" y="154" font-size="11" fill="#64748b">IC</text>\n'
    left += '<rect x="90" y="150" width="90" height="130" fill="#fef2f2" stroke="#dc2626" stroke-width="1.4"/>\n'
    left += '<text x="135" y="220" text-anchor="middle" font-size="11.5" fill="#dc2626">固定偏置</text>\n'
    left += '<text x="135" y="238" text-anchor="middle" font-size="11" fill="#dc2626">撞饱和</text>\n'
    left += '<rect x="220" y="150" width="90" height="10" fill="#ecfdf5" stroke="#059669" stroke-width="1.4"/>\n'
    left += '<text x="265" y="184" text-anchor="middle" font-size="11.5" fill="#059669">分压偏置</text>\n'
    left += '<text x="265" y="202" text-anchor="middle" font-size="11" fill="#059669">≈4%</text>\n'
    left += chip(196, 330, '固定偏置的 IB 恒定 = 把 β 当常数', '#dc2626', 11.5)
    svg = derive_frame('β 漂移冲击工作点：偏置的失效边界', steps, left, h=680, dur=D)
    svg += note_box("β 从 100 漂到 600：固定偏置的 IC 直接撞饱和；分压偏置靠 RE 负反馈把漂移压到约 4%（3.4 节图）", 636, D, delay_kt=None, w=740)
    save('exp-beta-drift.svg', svg + '</svg>')

def make_exp_thermal_loop():
    D = 14
    steps = [
        ('① 起步', 'T↑', '环境或自热'),
        ('② 门槛降', 'VBE ≈ −2mV/°C', '同样偏置下 IC 指数涨'),
        ('③ 功耗涨', 'P = VCE × IC ↑', '更热'),
        ('④ 断环', 'RE 负反馈 / 散热 / 恒流驱动', '热失控必须从环上拆'),
    ]
    left = '<circle cx="180" cy="240" r="86" fill="none" stroke="#dc2626" stroke-width="2.6" stroke-dasharray="9,6"/>\n'
    for x, y, s in [(180, 138, 'T↑'), (262, 232, 'VBE↓'), (180, 348, 'IC↑·P↑'), (96, 232, '更热')]:
        left += f'<text x="{x}" y="{y}" text-anchor="middle" font-size="14" font-weight="bold" fill="#dc2626">{s}</text>\n'
    for x, y in [(238, 172), (238, 306), (120, 306), (120, 172)]:
        left += f'<polygon points="{x - 7},{y} {x + 7},{y} {x},{y + 11}" fill="#dc2626"/>\n'
    left += chip(180, 396, '正反馈：强者更强', '#dc2626', 12)
    left += chip(180, 426, 'LED 恒压驱动易烧，同根子', '#64748b', 11)
    svg = derive_frame('热失控：一条闭合的正反馈环（失效边界）', steps, left, h=680, dur=D)
    svg += note_box("VBE −2mV/°C 是导火索：升温→IC 涨→更热。断环靠 RE 负反馈、散热或恒流驱动（3.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-thermal-loop.svg', svg + '</svg>')

def make_exp_gate_charge():
    D = 14
    steps = [
        ('① 平台期', '栅流全部灌进 Cgd', 'VGS 停在平台，VDS 快速跌'),
        ('② 平台时长', 't ≈ Qgd / Idrv', '驱动电流是唯一的挤压器'),
        ('③ 提速代价', '10mA→40mA：160ns→40ns', 'dv/dt 也快四倍（4.6 例）'),
        ('④ 连锁', '振铃、EMI、误导通一起涨', '栅阻是三者交点'),
    ]
    left = _exp_axis(56, 320, 240, 160, 't', 'VGS')
    left += '<path d="M56 300 L96 240 L136 240 L176 160 L296 150" fill="none" stroke="#2563eb" stroke-width="2.4"/>\n'
    left += '<rect x="96" y="228" width="40" height="26" fill="#fffbeb" stroke="#b45309" stroke-width="1.4"/>\n'
    left += '<text x="116" y="218" text-anchor="middle" font-size="11" font-weight="bold" fill="#b45309">平台</text>\n'
    left += chip(180, 396, '平台期管子最烫：V、I 重叠', '#b45309', 12)
    left += chip(180, 426, '提速看 Qgd 与驱动电流', '#64748b', 11)
    svg = derive_frame('米勒平台的栅电荷账：驱动电流是挤压器', steps, left, h=680, dur=D)
    svg += note_box("平台时长 ≈ Qgd/Idrv：10mA→40mA 平台 160ns→40ns，但 dv/dt 同步快四倍（4.3/4.6 节）", 636, D, delay_kt=None, w=740)
    save('exp-gate-charge.svg', svg + '</svg>')

def make_exp_avalanche_edge():
    D = 14
    steps = [
        ('① 感性负载', 'v = −L·di/dt', '电流被迫从工作值跳向 0'),
        ('② 尖峰', '数百伏，极性与电源相反', '专烧驱动管'),
        ('③ 钳位', '续流二极管压到 ≈0.7V', '电流经 L/R 慢慢衰减'),
        ('④ 选型', '反向耐压盖住母线+尖峰', '慢恢复管会把尖峰变振铃'),
    ]
    left = _exp_axis(56, 320, 240, 160, 't', 'V')
    left += '<path d="M56 260 L140 258 L146 120 L154 262 L296 260" fill="none" stroke="#dc2626" stroke-width="2.4"/>\n'
    left += '<line x1="56" y1="180" x2="296" y2="180" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="5,4"/>\n'
    left += '<text x="150" y="130" font-size="11" font-weight="bold" fill="#dc2626">数百伏反冲</text>\n'
    left += '<text x="200" y="174" font-size="11" fill="#059669">续流钳位线</text>\n'
    left += chip(180, 396, '「并一只二极管」是结论，并哪一只是设计', '#059669', 11.5)
    svg = derive_frame('感性负载的关断尖峰：电感物理的必然推论', steps, left, h=680, dur=D)
    svg += note_box("断电瞬间 di/dt 极大，电感发飙出数百伏尖峰；续流二极管给惯性电流一条温柔出路（2.4 续流账）", 636, D, delay_kt=None, w=740)
    save('exp-avalanche-edge.svg', svg + '</svg>')

def make_exp_pullup_trade():
    D = 14
    steps = [
        ('① 快的一端', '1kΩ × 100pF：τ≈100ns 量级', '沿陡，灌电流 3.3mA'),
        ('② 慢的一端', '4.7kΩ × 100pF：τ≈470ns', '对照 300ns 快速模式上限'),
        ('③ 功耗账', '每一位拉低都要灌 V/R', '上拉越小越费电'),
        ('④ 折中', '2.2kΩ 起步按总线复核', 'I2C 的 4.7k 不是随便选'),
    ]
    left = '<line x1="56" y1="140" x2="330" y2="140" stroke="#94a3b8" stroke-width="1.2"/>\n'
    left += '<text x="336" y="144" font-size="11" fill="#64748b">3.3V</text>\n'
    left += '<line x1="56" y1="320" x2="330" y2="320" stroke="#94a3b8" stroke-width="1.2"/>\n'
    left += '<text x="336" y="324" font-size="11" fill="#64748b">0V</text>\n'
    left += '<path d="M60 320 Q110 240 190 170 Q240 148 300 144" fill="none" stroke="#059669" stroke-width="2.2"/>\n'
    left += '<path d="M60 320 Q130 290 230 220 Q290 176 330 160" fill="none" stroke="#b45309" stroke-width="2.2"/>\n'
    left += '<path d="M60 320 Q150 306 260 272 Q310 250 330 238" fill="none" stroke="#dc2626" stroke-width="2.2"/>\n'
    left += '<text x="200" y="128" font-size="11" fill="#059669">1k 快但费电</text>\n'
    left += '<text x="236" y="196" font-size="11" fill="#b45309">2.2k 折中</text>\n'
    left += '<text x="252" y="266" font-size="11" fill="#dc2626">4.7k 超 300ns 窗</text>\n'
    svg = derive_frame('上拉取值：上升沿与功耗的双边权衡', steps, left, h=680, dur=D)
    svg += note_box("3.3V、100pF 总线：4.7k 的时间常数约 470ns，对 300ns 快速模式已超限；1k 快但灌电流大（5.3 节图）", 636, D, delay_kt=None, w=740)
    save('exp-pullup-trade.svg', svg + '</svg>')

def make_exp_dead_time():
    D = 14
    steps = [
        ('① 换向瞬间', '上管未关、下管已开', '电源到地直通短路'),
        ('② 直通电流', '只受内阻限制，可达数十安', '发热与 EMI 都来了'),
        ('③ 死区', '先断后合，留几百 ns', '桥臂换向的保命窗'),
        ('④ 代价', '占空比损失一点点', '换来不炸管'),
    ]
    left = '<line x1="60" y1="170" x2="320" y2="170" stroke="#2563eb" stroke-width="2.2"/>\n'
    left += '<line x1="60" y1="260" x2="320" y2="260" stroke="#059669" stroke-width="2.2"/>\n'
    left += '<text x="326" y="174" font-size="11" fill="#2563eb">上管</text>\n'
    left += '<text x="326" y="264" font-size="11" fill="#059669">下管</text>\n'
    left += '<rect x="170" y="158" width="26" height="114" fill="#fef2f2" stroke="#dc2626" stroke-width="1.4"/>\n'
    left += '<text x="183" y="150" text-anchor="middle" font-size="11" font-weight="bold" fill="#dc2626">交越</text>\n'
    left += '<rect x="200" y="158" width="18" height="114" fill="#f6eedb" stroke="#b45309" stroke-width="1.2" stroke-dasharray="4,3"/>\n'
    left += '<text x="209" y="292" text-anchor="middle" font-size="11" fill="#b45309">死区</text>\n'
    left += chip(190, 386, '推挽图腾柱同一时刻只能一人上岗', '#dc2626', 11.5)
    svg = derive_frame('直通窗口与死区：换向瞬间谁在岗', steps, left, h=680, dur=D)
    svg += note_box("两管同岗 = 电源直灌地。死区让换向「先断后合」，代价只是几纳秒的占空比（5.1/13.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-dead-time.svg', svg + '</svg>')

def make_exp_gbw_swap():
    D = 14
    steps = [
        ('① 守恒量', 'GBW = A × BW ≈ 常数', '电压反馈运放的经验线'),
        ('② 增益 100', 'BW ≈ 100kHz（GBW=10MHz）', '带宽被吃掉'),
        ('③ 增益 10', 'BW ≈ 1MHz', '同料换配置'),
        ('④ 取舍', '要带宽就少要增益', '两级低增益常胜一级高增益'),
    ]
    left = _exp_axis(56, 320, 240, 160, '增益', '带宽')
    left += '<path d="M64 160 L96 220 L156 270 L296 302" fill="none" stroke="#2563eb" stroke-width="2.4"/>\n'
    for x, y, lab in [(96, 220, '×100→100kHz'), (156, 270, '×10→1MHz')]:
        left += f'<circle cx="{x}" cy="{y}" r="4" fill="#b45309"/>\n'
        left += f'<text x="{x + 8}" y="{y - 8}" font-size="11" fill="#b45309">{lab}</text>\n'
    left += chip(180, 396, 'GBW 是预算，不是指标库里的一个数', '#2563eb', 12)
    svg = derive_frame('增益带宽交换：GBW 是一笔守恒的预算', steps, left, h=680, dur=D)
    svg += note_box("GBW=10MHz 的运放：增益 100 只剩 100kHz 带宽——增益与带宽此消彼长（6.3/6.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-gbw-swap.svg', svg + '</svg>')

def make_exp_slew_wall():
    D = 14
    steps = [
        ('① 需求', 'SR ≥ 2π·f·Vpk', '5Vpk、100kHz → 3.14V/µs'),
        ('② 现实', '0.5V/µs（LM358 量级）', '差六倍'),
        ('③ 后果', '正弦变三角，幅度塌', '大信号先死'),
        ('④ 出路', '降幅、降频或换高速运放', '小信号 GBW 够也没用'),
    ]
    left = _exp_axis(56, 300, 240, 130, 't', 'Vout')
    left += '<path d="M56 260 Q106 160 156 260 Q206 360 256 260 Q281 210 296 235" fill="none" stroke="#94a3b8" stroke-width="1.6" stroke-dasharray="6,4"/>\n'
    left += '<path d="M56 260 L106 170 L156 260 L206 350 L256 260 L296 205" fill="none" stroke="#dc2626" stroke-width="2.4"/>\n'
    left += '<text x="196" y="150" font-size="11" fill="#94a3b8">想要的正弦</text>\n'
    left += '<text x="150" y="382" font-size="11" fill="#dc2626">压摆率不够 → 三角化</text>\n'
    left += chip(180, 420, '压摆率是大信号天花板', '#dc2626', 12)
    svg = derive_frame('压摆率墙：大信号的失效边界', steps, left, h=680, dur=D)
    svg += note_box("SR≥2πfVpk：5Vpk@100kHz 要 3.14V/µs；0.5V/µs 的运放直接把正弦画成三角（6.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-slew-wall.svg', svg + '</svg>')

def make_exp_hyst_window():
    D = 14
    steps = [
        ('① 一对门限', 'VTH+ 上行门槛，VTH− 下行', '三只电阻定窗'),
        ('② 免疫区', '窗宽 = VTH+ − VTH−', '窗内噪声不翻转'),
        ('③ 代价', '分辨率 = 窗宽', '窗越宽越「钝」'),
        ('④ 符号铁律', '两路分压符号必须同向', '接反即正反馈翻车'),
    ]
    left = _exp_axis(56, 320, 240, 150, 'Vin', 'Vout')
    left += '<path d="M56 300 L160 300 L160 160 L296 160" fill="none" stroke="#2563eb" stroke-width="2.4"/>\n'
    left += '<line x1="160" y1="160" x2="160" y2="300" stroke="#b45309" stroke-width="1.4" stroke-dasharray="5,4"/>\n'
    left += '<text x="166" y="236" font-size="11" font-weight="bold" fill="#b45309">窗口</text>\n'
    left += '<text x="90" y="288" font-size="11" fill="#64748b">VTH−</text>\n'
    left += '<text x="90" y="152" font-size="11" fill="#64748b">VTH+</text>\n'
    left += '<path d="M200 230 q14 -14 28 0 q14 14 28 0 q14 -14 26 2" fill="none" stroke="#dc2626" stroke-width="1.6"/>\n'
    left += '<text x="212" y="214" font-size="10.5" fill="#dc2626">噪声被免疫区挡住</text>\n'
    left += chip(180, 396, '迟滞免抖：给判决一对分离的门槛', '#059669', 12)
    svg = derive_frame('迟滞窗口：抗噪护城河的宽与窄', steps, left, h=680, dur=D)
    svg += note_box("窗宽就是抗噪护城河：200mV 毛刺在窗外进不来；代价是分辨率等于窗宽（7.3 节）", 636, D, delay_kt=None, w=740)
    save('exp-hyst-window.svg', svg + '</svg>')

def make_exp_delay_budget():
    D = 14
    steps = [
        ('① 运放兼职', 'LM358：恢复+爬坡 ≈ 50µs 级', '饱和恢复是主犯'),
        ('② 比较器', 'LM393：1.3µs + 上拉 0.3µs', '约 1.6µs 交卷'),
        ('③ 预算核对', '10kHz 周期 = 100µs', '50µs 已占一半'),
        ('④ 结论', '判决用比较器，放大归运放', '混用是自找的延迟'),
    ]
    left = '<text x="56" y="120" font-size="12.5" font-weight="bold" fill="#334155">同一 10kHz 方波的响应条（示意）</text>\n'
    left += '<rect x="70" y="150" width="240" height="26" fill="#fef2f2" stroke="#dc2626" stroke-width="1.4"/>\n'
    left += '<text x="80" y="168" font-size="11" fill="#dc2626">LM358 ≈ 50µs（半个周期）</text>\n'
    left += '<rect x="70" y="196" width="26" height="26" fill="#ecfdf5" stroke="#059669" stroke-width="1.4"/>\n'
    left += '<text x="104" y="214" font-size="11" fill="#059669">LM393 ≈ 1.6µs</text>\n'
    left += '<line x1="70" y1="240" x2="310" y2="240" stroke="#94a3b8" stroke-width="1.2"/>\n'
    left += '<text x="70" y="258" font-size="11" fill="#64748b">周期 100µs →</text>\n'
    left += chip(190, 320, '延迟是预算的一部分', '#b45309', 12)
    svg = derive_frame('判决延迟预算：运放兼职的代价', steps, left, h=680, dur=D)
    svg += note_box("LM358 在饱和恢复里呆滞几十 µs，LM393 只要约 1.6µs——10kHz 已是分水岭（ch07-delay-budget 图）", 636, D, delay_kt=None, w=740)
    save('exp-delay-budget.svg', svg + '</svg>')

def make_exp_inject_harmonic():
    D = 14
    steps = [
        ('① 注入随信号走', '0V→2pC，4V→1.6pC', '峰谷差 0.4pC'),
        ('② 落到电容上', '0.4pC / 10nF = 40µV', '12 位系统无感'),
        ('③ 换 1nF', '40µV → 0.4mV', '贴着 12 位噪声底'),
        ('④ 结论', '同一注入曲线，C 定台阶还是谐波', '加大电容的第三个好处'),
    ]
    left = _exp_axis(56, 300, 240, 150, 'Vin', 'Qinj')
    left += '<line x1="56" y1="160" x2="296" y2="176" stroke="#2563eb" stroke-width="2.2"/>\n'
    for x, y, lab in [(90, 166, '2pC'), (280, 174, '1.6pC')]:
        left += f'<circle cx="{x}" cy="{y}" r="4" fill="#b45309"/>\n'
        left += f'<text x="{x - 6}" y="{y - 10}" font-size="11" fill="#b45309">{lab}</text>\n'
    left += '<rect x="120" y="330" width="60" height="26" fill="#ecfdf5" stroke="#059669" stroke-width="1.4"/>\n'
    left += '<text x="150" y="348" text-anchor="middle" font-size="11" fill="#059669">10nF ✓</text>\n'
    left += '<rect x="210" y="330" width="60" height="26" fill="#fef2f2" stroke="#dc2626" stroke-width="1.4"/>\n'
    left += '<text x="240" y="348" text-anchor="middle" font-size="11" fill="#dc2626">1nF ✗</text>\n'
    left += chip(196, 402, '0.4pC 的峰谷差就是谐波来源', '#2563eb', 11.5)
    svg = derive_frame('电荷注入的信号相关性：从台阶到谐波', steps, left, h=680, dur=D)
    svg += note_box("注入 2pC→1.6pC 随信号缓变：0.4pC 落 10nF 是 40µV（无感），落 1nF 是 0.4mV（贴底）（8.3 节图）", 636, D, delay_kt=None, w=740)
    save('exp-inject-harmonic.svg', svg + '</svg>')

def make_exp_droop_budget():
    D = 14
    steps = [
        ('① 下垂率', 'dV/dt = I_leak / C_hold', '开关漏电+缓冲偏流'),
        ('② 代入', '2nA / 10nF = 0.2V/s', '总漏流按 2nA 兜底'),
        ('③ 保持 1ms', '掉 0.2mV = 0.4LSB（12 位）', '过'),
        ('④ 出口闸', 'τ 与 droop 两笔都要过', '端到端预算表的用法'),
    ]
    left = _exp_axis(56, 300, 240, 150, 't (1ms 保持)', 'Vhold')
    left += '<line x1="56" y1="160" x2="296" y2="184" stroke="#b45309" stroke-width="2.4"/>\n'
    left += '<line x1="56" y1="160" x2="296" y2="160" stroke="#94a3b8" stroke-width="1" stroke-dasharray="5,4"/>\n'
    left += _exp_vline_note(230, 160, 220, '−0.2mV', '#dc2626')
    left += chip(180, 380, '「记住」也会漏：droop 是时间税', '#b45309', 12)
    left += chip(180, 410, '加大 C 同时压 τ 与 droop', '#64748b', 11)
    svg = derive_frame('采样保持的 droop 预算：时间维度的税', steps, left, h=680, dur=D)
    svg += note_box("2nA 漏流落 10nF：0.2V/s → 1ms 掉 0.2mV = 0.4LSB，12 位可过（8.4 端到端设计例）", 636, D, delay_kt=None, w=740)
    save('exp-droop-budget.svg', svg + '</svg>')

def make_exp_ldo_zero():
    D = 14
    steps = [
        ('① 环路靠谁', '输出电容 ESR 零点补相位', 'LDO 稳定的隐藏支柱'),
        ('② 换 MLCC', 'ESR 几 mΩ → 零点跑到高频', '相位裕度 58°→32°'),
        ('③ 低温更糟', 'MLCC 容值再掉 10~15%', '雪上加霜'),
        ('④ 修法', '串 0.15Ω 造回零点，或选陶瓷稳定型', '换料前重看环路'),
    ]
    left = _exp_axis(56, 300, 240, 150, 'f', '相位裕度')
    left += '<path d="M56 150 L150 156 L200 240 L296 268" fill="none" stroke="#dc2626" stroke-width="2.4"/>\n'
    left += '<line x1="56" y1="216" x2="296" y2="216" stroke="#059669" stroke-width="1.2" stroke-dasharray="5,4"/>\n'
    left += '<text x="60" y="210" font-size="11" fill="#059669">45° 工程下限</text>\n'
    left += _exp_vline_note(200, 150, 250, '低温 −20°C', '#dc2626')
    left += chip(180, 380, '58°→32°：裕度被 ESR 零点带走了', '#dc2626', 11.5)
    svg = derive_frame('LDO 换料的隐性账：ESR 零点与稳定（失效边界）', steps, left, h=680, dur=D)
    svg += note_box("钽换 MLCC：ESR 从 200mΩ 掉到几 mΩ，零点移出、裕度 58°→32°，低温自激——串 0.15Ω 造回零点（ch16 案例 A）", 636, D, delay_kt=None, w=740)
    save('exp-ldo-zero.svg', svg + '</svg>')

def make_exp_psrr_roll():
    D = 14
    steps = [
        ('① 低频很硬', '1kHz：70dB', '纹波被压得很小'),
        ('② 中频滑坡', '100kHz：约 40dB', '−20dB/dec 起步'),
        ('③ 高频失守', '1MHz：20dB 或个位数', 'LDO 帮不上忙'),
        ('④ 分工', '前级 LC/磁珠补高频段', '两级各守一段'),
    ]
    left = _exp_axis(56, 300, 240, 160, 'f (log)', 'PSRR')
    left += '<path d="M56 150 L130 156 L210 230 L296 282" fill="none" stroke="#2563eb" stroke-width="2.4"/>\n'
    for x, y, lab in [(90, 154, '70dB'), (190, 226, '40dB'), (286, 278, '20dB')]:
        left += f'<circle cx="{x}" cy="{y}" r="4" fill="#b45309"/>\n'
        left += f'<text x="{x - 10}" y="{y - 10}" font-size="11" fill="#b45309">{lab}</text>\n'
    left += chip(180, 386, '纹波预算按频率分段算', '#2563eb', 12)
    svg = derive_frame('PSRR 随频率滚降：电源抑制是分段防守', steps, left, h=680, dur=D)
    svg += note_box("1kHz 处 70dB 的 LDO 到 1MHz 只剩 20dB——高频纹波要靠 LC 与磁珠补位（9.3 节）", 636, D, delay_kt=None, w=740)
    save('exp-psrr-roll.svg', svg + '</svg>')

def make_exp_555_mono_train():
    D = 14
    steps = [
        ('① 触发', '2 脚拉到 Vcc/3 以下', '下降沿起跑'),
        ('② 定时', 't = 1.1·R·C', '充到 2Vcc/3 结束'),
        ('③ 复位', '放电管拉低 7 脚', '等下一次触发'),
        ('④ 误差', '电解漏电让 C「存不住」', '长定时用薄膜或修调'),
    ]
    left = _exp_axis(56, 280, 240, 130, 't', '')
    left += '<path d="M56 260 L86 260 L86 190 L216 190 L216 260 L296 260" fill="none" stroke="#2563eb" stroke-width="2.4"/>\n'
    left += '<path d="M70 274 l10 -8 l10 8" fill="none" stroke="#b45309" stroke-width="2"/>\n'
    left += '<text x="64" y="292" font-size="11" fill="#b45309">触发脉冲</text>\n'
    left += '<text x="120" y="180" font-size="11" fill="#2563eb">t = 1.1RC</text>\n'
    left += chip(180, 372, '一触发，亮一拍', '#2563eb', 12)
    left += chip(180, 402, '长定时的敌人是漏电与温漂', '#64748b', 11)
    svg = derive_frame('单稳态触发链：一触发，亮一拍', steps, left, h=680, dur=D)
    svg += note_box("触发后输出维持 1.1RC：定时 1s 的取值要防电解漏电流——C 存不住电，定时就短（10.5 节）", 636, D, delay_kt=None, w=740)
    save('exp-555-mono-train.svg', svg + '</svg>')

def make_exp_555_duty():
    D = 14
    steps = [
        ('① 充电路径', 'RA → RB → C', '充到 2Vcc/3'),
        ('② 放电路径', 'C → RB → 7 脚', '放到 Vcc/3'),
        ('③ 占空比', 'D = (RA+RB)/(RA+2RB)', 'RA=0 时 D≈50% 仍不严格'),
        ('④ 独立调', '二极管旁路 RB 充电', '充放分开，D 自由'),
    ]
    left = '<rect x="80" y="140" width="230" height="120" rx="8" fill="#f6eedb" stroke="#334155" stroke-width="1.8"/>\n'
    left += '<text x="195" y="172" text-anchor="middle" font-size="13" font-weight="bold" fill="#334155">RA · RB · C</text>\n'
    left += '<path d="M100 210 L180 210" stroke="#2563eb" stroke-width="2.4"/>\n'
    left += '<text x="112" y="202" font-size="11" fill="#2563eb">充电 RA+RB</text>\n'
    left += '<path d="M290 210 L210 210" stroke="#059669" stroke-width="2.4"/>\n'
    left += '<text x="214" y="228" font-size="11" fill="#059669">放电 RB</text>\n'
    left += '<text x="195" y="248" text-anchor="middle" font-size="11" fill="#64748b">门限：2Vcc/3 与 Vcc/3</text>\n'
    left += chip(195, 320, 'D 由 RA、RB 的比例决定', '#b45309', 12)
    left += chip(195, 350, '对称方波要靠二极管 trick', '#64748b', 11)
    svg = derive_frame('555 占空比：充放两条路各管一段', steps, left, h=680, dur=D)
    svg += note_box("充经 RA+RB、放经 RB：D=(RA+RB)/(RA+2RB)；要独立调占空比就给充电加旁路二极管（10.2 节）", 636, D, delay_kt=None, w=740)
    save('exp-555-duty.svg', svg + '</svg>')

def make_exp_miller_mult():
    D = 14
    steps = [
        ('① 原始电容', 'Cgd = 10pF', '跨在反相输出的两端'),
        ('② 增益放大它', 'Cin = (1+A)·Cgd', 'A=100 → 1010pF'),
        ('③ 后果', '输入极点被拖低', '带宽先死在输入端'),
        ('④ 对策', '共源共栅把 A 压小', 'cascode 的另一层意义'),
    ]
    left = _exp_axis(56, 300, 240, 150, 'A（增益）', 'Cin')
    left += '<path d="M56 280 L296 150" fill="none" stroke="#dc2626" stroke-width="2.4"/>\n'
    for x, y, lab in [(120, 244, '1010pF'), (240, 178, '≈2.5nF@A=250')]:
        left += f'<circle cx="{x}" cy="{y}" r="4" fill="#b45309"/>\n'
        left += f'<text x="{x - 8}" y="{y - 10}" font-size="11" fill="#b45309">{lab}</text>\n'
    left += chip(180, 386, '放大器把自己的反馈电容放大', '#dc2626', 12)
    svg = derive_frame('米勒倍增：一只电容被增益放大', steps, left, h=680, dur=D)
    svg += note_box("Cin=(1+A)Cgd：A=100 时 10pF 变 1010pF——高频增益还没抢到手，带宽先被输入端吃掉（11.5 节）", 636, D, delay_kt=None, w=740)
    save('exp-miller-mult.svg', svg + '</svg>')

def make_exp_noise_ladder():
    D = 14
    steps = [
        ('① 带宽税', 'en × √BW', '带宽砍一半，噪声省 √2'),
        ('② 源阻税', '4kTRs', 'Rs 越大热噪声越大'),
        ('③ 电流税', 'in × Rs', '高源阻把电流噪声放大'),
        ('④ 预算收口', '三项折算到输入端求和', '再算 SNR 与 ENOB'),
    ]
    left = ''
    for i, (y, h, lab, c) in enumerate([(280, 40, '带宽税', '#2563eb'), (240, 80, '源阻税', '#b45309'), (200, 120, '电流税', '#dc2626')]):
        x = 80 + i * 76
        left += f'<rect x="{x}" y="{y - h}" width="52" height="{h}" fill="#f6eedb" stroke="{c}" stroke-width="1.5"/>\n'
        left += f'<text x="{x + 26}" y="{y + 22}" text-anchor="middle" font-size="11" fill="{c}">{lab}</text>\n'
    left += '<line x1="66" y1="280" x2="320" y2="280" stroke="#94a3b8" stroke-width="1.4"/>\n'
    left += '<text x="330" y="284" font-size="11" fill="#64748b">e_n</text>\n'
    left += chip(196, 360, '降噪顺序：带宽 → 源阻 → 管子', '#059669', 12)
    svg = derive_frame('噪声三税：一张预算表收口', steps, left, h=680, dur=D)
    svg += note_box("带宽、源阻、电流噪声三笔税折到输入端求和，才是 SNR 的真底——先砍带宽最便宜（11.6 节）", 636, D, delay_kt=None, w=740)
    save('exp-noise-ladder.svg', svg + '</svg>')

def make_exp_integrator_drift():
    D = 14
    steps = [
        ('① 理想', '方波进 → 三角波出', '恒流充电容'),
        ('② 失调作祟', 'I_bias 给 C 慢慢充', '输出爬向电源轨'),
        ('③ 修法', '并泄放电阻 Rf', '直流增益限到 −Rf/R'),
        ('④ 代价', '不再纯积分', '低频端拐弯'),
    ]
    left = _exp_axis(56, 300, 240, 150, 't', 'Vout')
    left += '<path d="M56 280 L96 230 L136 280 L176 230 L216 280 L256 230 L296 272" fill="none" stroke="#2563eb" stroke-width="2.2"/>\n'
    left += '<path d="M56 280 Q160 220 296 132" fill="none" stroke="#dc2626" stroke-width="1.8" stroke-dasharray="6,4"/>\n'
    left += '<text x="176" y="140" font-size="11" fill="#dc2626">漂移：输出爬向轨</text>\n'
    left += '<text x="120" y="330" font-size="11" fill="#059669">Rf 把爬坡拉回</text>\n'
    left += chip(180, 386, '积分器的漂移是直流账', '#dc2626', 12)
    svg = derive_frame('积分器漂移与泄放电阻（失效边界）', steps, left, h=680, dur=D)
    svg += note_box("偏置电流给 C 充电，输出慢爬向轨；并 Rf 泄掉直流，代价是低频不再是纯积分（12.4/12.11 节）", 636, D, delay_kt=None, w=740)
    save('exp-integrator-drift.svg', svg + '</svg>')

def make_exp_cload_isolate():
    D = 14
    steps = [
        ('① 病灶', 'Rout × Cload 新极点', '相位裕度被吃掉'),
        ('② 症状', '方波振铃甚至自激', '跟随器最凶险'),
        ('③ 修法', '输出串隔离电阻 Ro', '把负载电容拆出环路'),
        ('④ 代价', '直流精度略降', 'Ro 上有一点压降'),
    ]
    left = _exp_axis(56, 280, 240, 130, 't', 'Vout')
    left += '<path d="M56 260 L96 170 L136 250 L176 190 L216 244 L256 206 L296 232" fill="none" stroke="#dc2626" stroke-width="2.2"/>\n'
    left += '<path d="M56 260 L96 170 L136 250 L176 190 L226 226 L296 224" fill="none" stroke="#059669" stroke-width="2" stroke-dasharray="7,4"/>\n'
    left += '<text x="170" y="150" font-size="11" fill="#dc2626">串电阻前：振铃</text>\n'
    left += '<text x="216" y="212" font-size="11" fill="#059669">串 Ro 后：收敛</text>\n'
    left += chip(180, 366, '隔离电阻把极点拆出环路', '#059669', 12)
    svg = derive_frame('容性负载自激与隔离电阻（失效边界）', steps, left, h=680, dur=D)
    svg += note_box("Rout×Cload 的新极点拖垮相位裕度；输出串几十欧隔离电阻，振铃当场收敛（12.9 节）", 636, D, delay_kt=None, w=740)
    save('exp-cload-isolate.svg', svg + '</svg>')

def make_exp_volt_second():
    D = 14
    steps = [
        ('① 导通段', '(Vin − Vo)·Ton', '电感「充电」伏秒'),
        ('② 关断段', 'Vo·Toff', '电感「放电」伏秒'),
        ('③ 平衡', '两块面积相等', '稳态的入场券'),
        ('④ 结果', 'Vo = D·Vin；12V→5V：D≈0.42', '占空比即比值'),
    ]
    left = _exp_axis(56, 300, 240, 150, 't', 'VL')
    left += '<path d="M56 170 L146 170 L146 260 L236 260 L236 170 L296 170" fill="none" stroke="#2563eb" stroke-width="2.4"/>\n'
    left += '<rect x="66" y="176" width="70" height="78" fill="#eff6ff" stroke="#2563eb" stroke-width="1" opacity="0.7"/>\n'
    left += '<rect x="156" y="176" width="70" height="78" fill="#fef2f2" stroke="#dc2626" stroke-width="1" opacity="0.7"/>\n'
    left += '<text x="76" y="166" font-size="11" fill="#2563eb">充</text>\n'
    left += '<text x="186" y="282" font-size="11" fill="#dc2626">放</text>\n'
    left += chip(180, 386, '伏秒平衡是一切 Buck 公式的源头', '#2563eb', 12)
    svg = derive_frame('伏秒平衡：电感稳态的入场券', steps, left, h=680, dur=D)
    svg += note_box("充的伏秒 = 放的伏秒 → Vo=D·Vin；12V→5V 时 D≈0.42，纹波 ΔIL 由 L 与 f 定（13.2 节图）", 636, D, delay_kt=None, w=740)
    save('exp-volt-second.svg', svg + '</svg>')

def make_exp_crystal_pull():
    D = 14
    steps = [
        ('① 标称', 'CL = 12pF', '晶振按这个值校频'),
        ('② 实配', '两只 22pF → CL ≈ 15pF', '(C1·C2)/(C1+C2)+Cstray'),
        ('③ 牵引', '约 20ppm/pF × 3pF ≈ 55~60ppm', '频偏由此来'),
        ('④ 后果', '32.768kHz RTC 每天差 ≈4.8s', '负载电容错配的账'),
    ]
    left = '<rect x="70" y="140" width="100" height="42" rx="6" fill="#f6eedb" stroke="#334155" stroke-width="1.6"/>\n'
    left += '<text x="120" y="166" text-anchor="middle" font-size="12" fill="#334155">晶振 CL=12pF</text>\n'
    left += '<rect x="220" y="140" width="100" height="42" rx="6" fill="#fef2f2" stroke="#dc2626" stroke-width="1.6"/>\n'
    left += '<text x="270" y="166" text-anchor="middle" font-size="12" fill="#dc2626">实配 15pF</text>\n'
    left += '<line x1="170" y1="161" x2="220" y2="161" stroke="#94a3b8" stroke-width="2"/>\n'
    left += '<polygon points="212,156 212,166 222,161" fill="#94a3b8"/>\n'
    left += '<text x="196" y="150" text-anchor="middle" font-size="11" fill="#dc2626">+3pF</text>\n'
    left += '<path d="M80 260 Q170 250 300 224" fill="none" stroke="#dc2626" stroke-width="2.2"/>\n'
    left += '<text x="96" y="246" font-size="11" fill="#64748b">0</text>\n'
    left += '<text x="252" y="246" font-size="11" fill="#dc2626">−55ppm</text>\n'
    left += chip(196, 320, 'RTC 每天慢 4.8 秒', '#dc2626', 12)
    svg = derive_frame('晶振牵引灵敏度：3pF 偏差值多少秒', steps, left, h=680, dur=D)
    svg += note_box("两只 22pF 把 CL 从 12pF 顶到 15pF，约 55~60ppm 频偏：32.768kHz 的 RTC 每天差约 4.8 秒（13.10 节图）", 636, D, delay_kt=None, w=740)
    save('exp-crystal-pull.svg', svg + '</svg>')

def make_exp_wc_rss():
    D = 14
    steps = [
        ('① WC 口径', '各项最坏同向相加', '批产的悲观上界'),
        ('② RSS 口径', '平方和开根', '独立随机项的统计合成'),
        ('③ 对照', 'RSS 总是小于 WC', '六项 1σ 预算两算法'),
        ('④ 用法', '规格对 WC，良率看 RSS', '14.9 的双口径'),
    ]
    left = '<line x1="66" y1="300" x2="320" y2="300" stroke="#94a3b8" stroke-width="1.4"/>\n'
    left += '<rect x="100" y="160" width="52" height="140" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>\n'
    left += '<text x="126" y="322" text-anchor="middle" font-size="11.5" fill="#dc2626">WC</text>\n'
    left += '<rect x="210" y="220" width="52" height="80" fill="#ecfdf5" stroke="#059669" stroke-width="1.5"/>\n'
    left += '<text x="236" y="322" text-anchor="middle" font-size="11.5" fill="#059669">RSS</text>\n'
    left += '<text x="196" y="130" font-size="12.5" font-weight="bold" fill="#334155">六项 1σ 贡献的两种总账</text>\n'
    left += chip(196, 380, '规格线对 WC，良率心里用 RSS', '#2563eb', 12)
    svg = derive_frame('最坏情况 vs RSS：误差预算的两把尺', steps, left, h=680, dur=D)
    svg += note_box("同一份六项预算：WC 全同向相加是批产上界，RSS 平方和开根更贴良率——两把尺各管一件事（14.10 节）", 636, D, delay_kt=None, w=740)
    save('exp-wc-rss.svg', svg + '</svg>')

def make_exp_derate_chain():
    D = 14
    steps = [
        ('① 标称', '1/4W @ 70°C', '实验室名片'),
        ('② 高温降额', '85°C 机内 → 只剩七成', '厂商降额曲线线性下调'),
        ('③ 再打五折', '×50% 工程规则', '一只"1/4W"按 80~100mW 使唤'),
        ('④ 出口', '算 P=VI，对降额线', '「摸着不烫」不算数'),
    ]
    left = '<line x1="66" y1="300" x2="320" y2="300" stroke="#94a3b8" stroke-width="1.4"/>\n'
    bars = [(90, 200, '标称 250mW', '#2563eb'), (170, 140, '85°C 七成', '#b45309'), (250, 70, '×50% ≈ 87mW', '#dc2626')]
    for x, h, lab, c in bars:
        left += f'<rect x="{x}" y="{300 - h}" width="52" height="{h}" fill="#f6eedb" stroke="{c}" stroke-width="1.5"/>\n'
        left += f'<text x="{x + 26}" y="{322}" text-anchor="middle" font-size="11" fill="{c}">{lab}</text>\n'
    left += chip(196, 150, '降额是乘法，不是加法', '#dc2626', 12)
    svg = derive_frame('额定功率的降额链：标称值怎么缩水', steps, left, h=680, dur=D)
    svg += note_box("1/4W：85°C 环境只剩七成，再按 50% 规则折半——同一只电阻实际只配 80~100mW（0.9/14.2 节）", 636, D, delay_kt=None, w=740)
    save('exp-derate-chain.svg', svg + '</svg>')

def make_exp_return_cut():
    D = 14
    steps = [
        ('① 正常回流', '高频回流贴在信号线正下方', '最小回路面积'),
        ('② 地平面开槽', '回流绕过槽缝', '环路面积瞬间放大'),
        ('③ 代价', '面积×30 → 辐射 +30dB', 'EMC 三要素里路径失守'),
        ('④ 修法', '信号不跨槽，必要时桥接', '回流路径别开天窗'),
    ]
    left = '<rect x="60" y="150" width="260" height="120" fill="#eff6ff" stroke="#2563eb" stroke-width="1.4"/>\n'
    left += '<rect x="168" y="150" width="14" height="120" fill="#fffdf8" stroke="#dc2626" stroke-width="1.6"/>\n'
    left += '<text x="175" y="290" text-anchor="middle" font-size="11" fill="#dc2626">开槽（禁区）</text>\n'
    left += '<path d="M70 210 L166 210 Q186 240 206 210 L310 210" fill="none" stroke="#dc2626" stroke-width="2.2" stroke-dasharray="7,4"/>\n'
    left += '<path d="M70 210 L310 210" fill="none" stroke="#059669" stroke-width="1.6" stroke-dasharray="3,4"/>\n'
    left += '<text x="90" y="198" font-size="11" fill="#059669">理想回流（直行）</text>\n'
    left += '<text x="196" y="242" font-size="11" fill="#dc2626">绕行回流</text>\n'
    left += chip(196, 366, '回流绕多远，天线就有多长', '#dc2626', 12)
    svg = derive_frame('回流路径被割断：开槽的代价（失效边界）', steps, left, h=680, dur=D)
    svg += note_box("高频回流贴线正下方；地平面开槽逼它绕行，环路面积×30、辐射+30dB——信号别跨槽（15.2/15.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-return-cut.svg', svg + '</svg>')

def make_exp_via_stack():
    D = 14
    steps = [
        ('① 叠层', '四层板 0.2mm 介质', 'w≈0.35mm 就能到 50Ω'),
        ('② 双层板', '1.6mm 介质 → w≈3mm', '走不开，阻抗难做'),
        ('③ 传输线判据', '边沿 1ns → 临界 2.5cm', '超过 l_crit/6 才启用端接'),
        ('④ 过孔', '短桩少换层', '残桩是隐藏支路'),
    ]
    left = '<rect x="66" y="140" width="250" height="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.2"/>\n'
    left += '<rect x="66" y="158" width="250" height="30" fill="#f6eedb" stroke="#b45309" stroke-width="1.2"/>\n'
    left += '<rect x="66" y="188" width="250" height="18" fill="#eff6ff" stroke="#2563eb" stroke-width="1.2"/>\n'
    left += '<text x="191" y="236" text-anchor="middle" font-size="11.5" fill="#334155">四层：信号-地-电源-信号</text>\n'
    left += '<text x="191" y="262" text-anchor="middle" font-size="11" fill="#64748b">0.2mm 介质 → 50Ω 只需 w≈0.35mm</text>\n'
    left += chip(191, 320, '双层板同阻抗要 3mm 线宽', '#dc2626', 12)
    left += chip(191, 350, '1ns 边沿：2.5cm 内不当传输线', '#64748b', 11)
    svg = derive_frame('叠层与阻抗：同一只 50Ω 两种命运', steps, left, h=680, dur=D)
    svg += note_box("同一条 50Ω 微带近似：四层板 0.35mm 走得开，双层板要 3mm——叠层先定，布线才谈得上阻抗（15.3 节图）", 636, D, delay_kt=None, w=740)
    save('exp-via-stack.svg', svg + '</svg>')

def make_exp_log2_split():
    D = 14
    steps = [
        ('① 公式', 'n 个节点 ≤ ⌈log₂n⌉ 次测量', '每刀砍掉一半嫌疑'),
        ('② n=6', '⌈log₂6⌉ = 3', '剩 3 → 剩 1~2 → 锁定'),
        ('③ n=16', '4 次定位 1 个（例 16-2）', '中点下刀的完整记录'),
        ('④ 前提', '测量点本身可信', '先按 16.6 查探头与地'),
    ]
    left = ''
    xs = [90, 170, 250]
    for row, (cnt, y) in enumerate([(6, 130), (3, 220), (1, 310)]):
        n_box = max(cnt, 1)
        for k in range(n_box if row < 3 else 1):
            x = xs[row] - (n_box - 1) * 22 + k * 44 if row < 3 else xs[2]
            w = 34 if row < 3 else 44
            left += (f'<rect x="{x}" y="{y}" width="{w}" height="36" rx="5" fill="#f6eedb" '
                     f'stroke="#059669" stroke-width="1.5"/>\n')
    left += '<text x="90" y="188" text-anchor="middle" font-size="11" fill="#334155">6</text>\n'
    left += '<text x="170" y="278" text-anchor="middle" font-size="11" fill="#334155">3</text>\n'
    left += '<text x="250" y="368" text-anchor="middle" font-size="11" fill="#334155">1</text>\n'
    left += '<text x="140" y="182" font-size="11" fill="#b45309">刀①</text>\n'
    left += '<text x="222" y="272" font-size="11" fill="#b45309">刀②</text>\n'
    left += '<text x="288" y="362" font-size="11" fill="#b45309">刀③</text>\n'
    left += chip(196, 412, '每刀把嫌疑砍半', '#b45309', 12)
    svg = derive_frame('二分定位的对数数学：6 节点 3 刀', steps, left, h=680, dur=D)
    svg += note_box("⌈log₂6⌉=3：第一刀剩 3、第二刀剩 1~2、第三刀锁定；16 节点也只要 4 次（16.1/16.7 节）", 636, D, delay_kt=None, w=740)
    save('exp-log2-split.svg', svg + '</svg>')

def make_exp_cost_ladder():
    D = 14
    steps = [
        ('① 原理图改一处', '成本 1', '评审阶段：一行文字'),
        ('② 打样改一处', '成本 10', '重投板+器件+一周'),
        ('③ 量产后改', '成本 100', '召回、返修、品牌'),
        ('④ 对策', '评审四闸把故障往左推', '原理图→布局→首板→出货'),
    ]
    left = '<line x1="66" y1="300" x2="320" y2="300" stroke="#94a3b8" stroke-width="1.4"/>\n'
    for x, h, lab, c in [(90, 40, '1', '#059669'), (170, 110, '10', '#b45309'), (250, 200, '100', '#dc2626')]:
        left += f'<rect x="{x}" y="{300 - h}" width="52" height="{h}" fill="#f6eedb" stroke="{c}" stroke-width="1.5"/>\n'
        left += f'<text x="{x + 26}" y="{322}" text-anchor="middle" font-size="12" font-weight="bold" fill="{c}">{lab}</text>\n'
    left += chip(196, 130, '1-10-100：越靠左越便宜', '#dc2626', 13)
    left += chip(196, 160, '排故经验 → 设计约束', '#64748b', 11)
    svg = derive_frame('1-10-100 成本法则：把故障往左推', steps, left, h=680, dur=D)
    svg += note_box("原理图阶段改一处是 1，打样是 10，量产是 100——评审清单的价值就是把改动推到最左边（18.4 节）", 636, D, delay_kt=None, w=740)
    save('exp-cost-ladder.svg', svg + '</svg>')

def make_exp_contact_creep():
    D = 14
    steps = [
        ('① 起点', '接触电阻 mΩ 级', '镀层完好'),
        ('② 蠕变', '热循环拉扯 → 缓慢爬升', '裂纹从角落长向中心'),
        ('③ 危险窗', '爬到 Ω 级之前：时好时坏', '只量通断会漏掉'),
        ('④ 统计', '200 焊点 × 0.5% 不良 → 整板仅 ~63% 全好', '抽检与 X-Ray 的理由'),
    ]
    left = _exp_axis(56, 300, 240, 150, '热循环次数', '接触电阻')
    left += '<path d="M56 280 Q140 272 200 240 Q260 205 296 150" fill="none" stroke="#dc2626" stroke-width="2.4"/>\n'
    left += '<line x1="56" y1="200" x2="296" y2="200" stroke="#b45309" stroke-width="1.2" stroke-dasharray="5,4"/>\n'
    left += '<text x="64" y="194" font-size="11" fill="#b45309">通断判据的盲区</text>\n'
    left += _exp_vline_note(230, 150, 262, '漂移窗口', '#dc2626')
    left += chip(180, 386, '"时好时坏"的焊点常表现为阻值漂移', '#dc2626', 11.5)
    svg = derive_frame('接触电阻蠕变：只量通断会漏掉的漂移窗（失效边界）', steps, left, h=680, dur=D)
    svg += note_box('mΩ→Ω 的爬升路上有一段「通断仍导通、阻值已漂移」的盲区——要晃动与变温中量（17.6 节图）', 636, D, delay_kt=None, w=740)
    save('exp-contact-creep.svg', svg + '</svg>')

make_exp_source_sag()
make_exp_conduction_angle()
make_exp_tvs_ladder()
make_exp_unit_guard()
make_exp_derate_chain()
make_exp_esr_ripple_split()
make_exp_cap_life()
make_exp_avalanche_edge()
make_exp_beta_drift()
make_exp_thermal_loop()
make_exp_gate_charge()
make_exp_pullup_trade()
make_exp_dead_time()
make_exp_gbw_swap()
make_exp_slew_wall()
make_exp_hyst_window()
make_exp_delay_budget()
make_exp_inject_harmonic()
make_exp_droop_budget()
make_exp_ldo_zero()
make_exp_psrr_roll()
make_exp_555_mono_train()
make_exp_555_duty()
make_exp_miller_mult()
make_exp_noise_ladder()
make_exp_integrator_drift()
make_exp_cload_isolate()
make_exp_volt_second()
make_exp_crystal_pull()
make_exp_wc_rss()
make_exp_return_cut()
make_exp_via_stack()
make_exp_log2_split()
make_exp_contact_creep()
make_exp_cost_ladder()
