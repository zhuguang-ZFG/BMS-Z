"""Eight source-bound, static handdraw explanation plates for the KP reader.

Prussian-blue linework, KaiTi titles, paper grain; no people or decoration-only
animation. Values are manuscript teaching examples, never product settings.
Run from the repository root: python tools/gen_kp_handdraw.py.
"""
from __future__ import annotations

import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bms-book/assets/kp"
INK = "#003153"
MUTED = "#5c6d73"
RED = "#E34234"
PAPER = "#f6f1e3"
SCALE = 2
FONT = Path("C:/Windows/Fonts/msyh.ttc")
TITLE_FONT = Path("C:/Windows/Fonts/simkai.ttf")


class Plate:
    def __init__(self, title, subtitle, seed):
        self.rng = random.Random(seed)
        noise = np.random.default_rng(seed).normal(0, 0.75, (560, 960, 1))
        base = np.asarray(Image.new("RGB", (960, 560), PAPER), dtype=np.float32)
        self.image = Image.fromarray(np.clip(base + noise, 0, 255).astype("uint8")).resize((1920, 1120))
        self.draw = ImageDraw.Draw(self.image)
        self.text(42, 24, "BMS · 一图讲清一个判断", 12, MUTED)
        self.text(42, 54, title, 30, INK, True)
        self.text(44, 98, subtitle, 15, MUTED)
        self.line([(44, 127), (916, 127)], width=0.7, color="#bfc6c2")
        self.text(916, 532, "原理示意 / 非实拍 · 教学值，不作产品参数", 12, MUTED, anchor="ra")

    def text(self, x, y, value, size=16, color=INK, title=False, anchor=None):
        font = ImageFont.truetype(str(TITLE_FONT if title else FONT), round(size*SCALE))
        self.draw.text((x*SCALE, y*SCALE), str(value), font=font, fill=color, anchor=anchor)

    def line(self, points, width=1.6, color=INK, hand=True):
        coords = []
        for x, y in points:
            jitter = self.rng.uniform(-0.35, 0.35) if hand else 0
            coords.append((round((x+jitter)*SCALE), round((y-jitter)*SCALE)))
        self.draw.line(coords, fill=color, width=max(1, round(width*SCALE)), joint="curve")

    def box(self, x, y, w, h, color=INK, width=1.4):
        self.line([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)],width,color)

    def dot(self, x, y, r=4, color=INK):
        self.draw.ellipse(((x-r)*SCALE,(y-r)*SCALE,(x+r)*SCALE,(y+r)*SCALE),fill=color)

    def arrow(self, x0, y0, x1, y1, color=INK):
        self.line([(x0,y0),(x1,y1)],1.6,color)
        a=math.atan2(y1-y0,x1-x0)
        for turn in (-0.5,0.5):
            self.line([(x1,y1),(x1-10*math.cos(a+turn),y1-10*math.sin(a+turn))],1.6,color)

    def note(self, main, extra):
        self.line([(44,454),(916,454)],.7,"#bfc6c2")
        self.text(44,469,main,19,INK,True)
        self.text(44,501,extra,13,MUTED)

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        self.image.resize((960,560),Image.Resampling.LANCZOS).save(OUT/name,optimize=True)


def chemistry():
    p=Plate("先选单节窗口，再乘串数", "同为 16 串，不代表能共用充电设定。先看材料，再算包电压。", 11)
    for y,label,one,pack in [(205,"铁锂示例",3.65,58.4),(325,"三元示例",4.20,67.2)]:
        p.text(54,y-40,label,20,INK,True)
        for i in range(16):
            x=190+i*30
            p.box(x,y-5,23,42,width=1)
            p.line([(x+23,y+15),(x+30,y+15)],1)
        p.text(194,y+49,f"单节正常充电上限 {one:.2f} V × 16",16)
        p.text(760,y+5,f"{pack:.1f} V",30,INK,True)
        p.arrow(691,y+17,735,y+17)
    p.note("串数只负责相加，不能改写材料边界。", "58.4 V 与 67.2 V 是正文典型值换算；真实电芯型号、温度与手册版本仍须核对。")
    p.save("chemistry-window.png")


def weakest():
    p=Plate("平均值看着正常，最弱一节已经先到线", "同一股电流穿过所有串联电芯，保护却必须逐节判断。",12)
    x0,y0,w=86,370,43
    for i in range(16):
        value=2.75 if i==10 else 3.50
        h=value/4.0*190
        color=RED if i==10 else INK
        p.box(x0+i*w,y0-h,28,h,color,width=1.7)
        if i in (0,10,15):
            p.text(x0+i*w+14,y0+15,str(i+1),12,MUTED,anchor="ma")
    ay=y0-(55.25/16)/4*190
    for x in range(76,800,14):
        p.line([(x,ay),(x+7,ay)],.8,MUTED)
    p.text(807,ay-24,"平均",13,MUTED)
    p.text(807,ay-3,"3.453 V",16)
    p.text(76,157,"15 节 × 3.50 V",17)
    p.text(550,157,"这一节 2.75 V",18,RED)
    p.arrow(597,190,x0+10*w+14,y0-2.75/4*190-5,RED)
    p.text(88,410,"包电压 = 55.25 V    ·    平均值不会替弱单体承担风险",16)
    p.note("先找最低的一节，再问这份读数是否可信。", "本图不预设产品欠压阈值；开线诊断、数据质量和执行反馈仍须另行核验。")
    p.save("weakest-cell.png")


def hysteresis():
    p=Plate("断开与恢复，走的不是同一条线", "确认时间拦短毛刺；两条电压线防止反复跳闸。两件事分开看。",13)
    def x(t):
        return 90+t/7*740
    def y(v):
        return 335-(v-4.10)/.26*145
    for voltage,label,col in [(4.28,"动作线 4.28 V",RED),(4.18,"恢复线 4.18 V",INK)]:
        for a in range(90,845,16):
            p.line([(a,y(voltage)),(a+8,y(voltage))],1,col)
        p.text(610,y(voltage)-24,label,16,col)
    points=[(0,4.12),(1.5,4.12),(1.5,4.34),(1.8,4.34),(1.8,4.12),(3,4.12),(3,4.32),(4.4,4.32),(4.4,4.22),(6.2,4.22),(6.2,4.12),(7,4.12)]
    p.line([(x(t),y(v)) for t,v in points],2)
    p.text(130,151,"0.3 s 毛刺：未满 1 s",16)
    p.text(390,151,"持续越线：3→4 s",16)
    p.text(57,370,"开关",14,MUTED)
    p.line([(x(0),383),(x(4),383),(x(4),407),(x(6.2),407),(x(6.2),383),(x(7),383)],2)
    p.dot(x(4),407,4,RED)
    p.text(x(4),421,"4.0 s 断开",13,RED,anchor="ma")
    p.text(x(6.2),421,"6.2 s 恢复",13,INK,anchor="ma")
    p.note("4.22 V 已低于动作线，仍不能按本例立即合上。", "教学回差为 4.28−4.18=0.10 V；图示可恢复型策略，不替代锁存故障的人工清除条件。")
    p.save("hysteresis.png")


def ruler():
    p=Plate("刻度更细，不会让零点自动归位", "ADC 位数管分辨率；固定偏置让整把尺子一起搬走。",14)
    for y,offset,title in [(210,0,"参考刻度"),(330,24,"测量刻度：零点偏高 24 mV")]:
        p.text(70,y-45,title,20,INK,True)
        p.line([(130,y),(820,y)],1.5)
        for i in range(41):
            xx=160+i*14
            p.line([(xx,y-8),(xx,y+12 if i%5 else y+21)],1)
        p.text(165,y+28,"格宽不变：5 V / 4096 ≈ 1.22 mV",16)
        xx=300+offset/1.22*14
        p.dot(xx,y,6,INK)
        p.arrow(xx,y-50,xx,y-12,INK)
    p.line([(300,216),(300,338)],1,MUTED)
    p.line([(575,290),(575,342)],1,INK)
    p.text(640,269,"同一个输入",16)
    p.text(640,294,"却整体偏了约 20 格",16,INK)
    p.note("多次平均会缩小随机散布，固定的 24 mV 仍在。", "先分清随机噪声和固定偏置，再决定平均、校准或检查参考源；数字为正文教学值。")
    p.save("measurement-ruler.png")


def capacity():
    p=Plate("还能装几成，与能多快拿出来，要分开量", "容量描述能量储备；内阻决定同样电流先吃掉多少端电压。",15)
    for x,capacity,label in [(110,5,"新电池"),(330,4,"老化示例")]:
        p.text(x+64,164,label,22,INK,True,anchor="ma")
        p.box(x,220,128,155,INK,2)
        p.box(x+43,208,42,12,INK,1.5)
        fill_h=capacity/5*135
        p.draw.rectangle((int((x+8)*2),int((366-fill_h)*2),int((x+120)*2),732),fill="#d8e3e5")
        p.text(x+64,291,f"{capacity:.1f} Ah",27,INK,True,anchor="mm")
    p.text(105,399,"容量 SOH：4.0 / 5.0 = 80%",17)
    p.text(566,165,"同样 20 A",22,INK,True)
    for y,r,v,length in [(238,20,.40,140),(333,45,.90,315)]:
        p.text(565,y-35,f"内阻 {r} mΩ",16)
        p.box(565,y,length,24,INK,1.4)
        p.text(565+length+10,y+2,f"{v:.2f} V",19)
    p.note("同样电流多掉 0.50 V，功率可能比续航更早受限。", "5.0/4.0 Ah 与 20/45 mΩ 是同一教学家族示例，不是特定电芯寿命测量或报废标准。")
    p.save("capacity-vs-power.png")


def frame_age():
    p=Plate("一帧没坏，不代表这份数据还能用", "CRC 检查字节是否矛盾；时间戳、版本和身份回答另外的问题。",16)
    p.text(63,166,"收到的帧",19,INK,True)
    fields=[("头",85),("长度",100),("测量值",180),("计数",105),("CRC",105)]
    x=66
    for label,width in fields:
        p.box(x,209,width,58)
        p.text(x+width/2,226,label,18,anchor="ma")
        x+=width
    p.text(744,225,"校验通过",23,INK,True)
    p.arrow(680,238,725,238)
    p.line([(120,358),(810,358)],1.8)
    p.dot(180,358)
    p.dot(720,358,5,RED)
    p.text(180,378,"采样时刻",16,anchor="ma")
    p.text(720,378,"现在才收到",16,RED,anchor="ma")
    p.arrow(200,329,700,329)
    p.text(450,293,"年龄：这段时间不在 CRC 答案里",18,anchor="ma")
    p.note("旧的正确帧也能过校验，控制前还要检查是否过期。", "再核对端序、比例、固件版本、身份与计数器；‘结构合法’只是进入下一道检查的资格。")
    p.save("frame-vs-age.png")


def precharge():
    p=Plate("预充看母线爬到哪里，不是只等秒表", "同一教学输入：400 V · 1 mF · 170 Ω；故障对照不是产品门槛。",17)
    def tx(t):
        return 100+t/.7*600
    def vy(v):
        return 395-v/400*220
    p.line([(100,174),(100,395),(720,395)],1.5)
    for val in (0,200,400):
        p.text(87,vy(val),str(val),13,MUTED,anchor="rm")
    p.text(75,146,"V",15,MUTED)
    p.line([(tx(i*.007),vy(400*(1-math.exp(-i*.007/.17)))) for i in range(101)],2.5)
    for t,v,label in [(.17,253,"1τ：253 V"),(.51,380,"3τ：约 380 V")]:
        p.dot(tx(t),vy(v),5)
        p.text(tx(t)+15,vy(v)-38 if t > .4 else vy(v)-10,label,17)
        p.line([(tx(t),vy(v)+10),(tx(t),395)],.7,MUTED)
        p.text(tx(t),413,f"{t:.2f} s",14,MUTED,anchor="ma")
    for x in range(100,701,16):
        p.line([(x,vy(40)),(x+8,vy(40))],1.3,RED)
    p.text(740,269,"停在 40 V",20,RED,True)
    p.text(740,307,"保持主闸断开",17)
    p.note("同样过了 0.51 s，低压故障曲线不能套‘等待完成’。", "τ=RC=0.17 s；真实判据还需电压、超时和接触器反馈，3τ 不等于严格稳态。")
    p.save("precharge-window.png")


def signoff():
    p=Plate("解释可以起草，结论要回到证据", "同一条数值，沿来源、计算、复核走；不从模型记忆直达安全配置。",18)
    p.box(72,171,207,222,width=1.3)
    p.text(96,188,"原文 / 运行记录",20,INK,True)
    for yy,width in [(231,147),(255,116),(279,147),(303,92)]:
        p.line([(96,yy),(96+width,yy)],1)
    p.text(96,343,"字段 · 单位 · 版本",15,MUTED)
    p.arrow(295,278,378,278)
    p.box(397,213,179,128)
    p.text(419,238,"程序复算",23,INK,True)
    p.text(419,282,"固定输入与规则",16)
    p.arrow(593,278,666,278)
    p.box(687,172,209,222,width=1.3)
    p.text(710,189,"人复核并签字",21,INK,True)
    for yy,label in [(237,"谁"),(272,"依据"),(307,"日期 / 配置版本")]:
        p.text(709,yy,label,16)
        p.line([(752,yy+24),(875,yy+24)],.8,MUTED)
    p.line([(196,418),(818,418)],1,RED)
    p.line([(479,404),(499,432)],2,RED)
    p.line([(499,404),(479,432)],2,RED)
    p.text(426,368,"不能绕过复算和复核",15,RED)
    p.note("能说出来源，才知道结论由什么支撑。", "模型输出可作候选和附件；原文、输入、规则或配置改变后，重新计算并复核适用范围。")
    p.save("evidence-signoff.png")


def main():
    if not FONT.is_file() or not TITLE_FONT.is_file():
        raise FileNotFoundError("Microsoft YaHei and KaiTi font files are required; do not silently substitute")
    for draw in (chemistry,weakest,hysteresis,ruler,capacity,frame_age,precharge,signoff):
        draw()
    print(f"generated 8 static teaching handdraw plates in {OUT}")


if __name__ == "__main__":
    main()
