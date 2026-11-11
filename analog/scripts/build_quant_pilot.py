"""生成 ch17 三张风险试片的技术图层、底图提示词和合成配置；不调用生图服务。"""
from __future__ import annotations

import html
import json
from pathlib import Path

import yaml

from compose_technical_overlay import ROOT, compose
from make_grayscale_fixture import swatch_rgb, upstream_root

REVIEW = "docs/superpowers/visual/reviews/quant-pilot-2026-11-05"
PROMPTS = "docs/superpowers/visual/prompts/quant-pilot"
COLOURS = {"paper": "C-34", "ink": "C-32", "shade": "C-35", "accent": "C-26"}


def label(x, y, text, *, size=34, colour=None, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{colour or PALETTE["ink"]}" '
            f'text-anchor="{anchor}">{html.escape(text)}</text>')


def line(x1, y1, x2, y2, *, colour=None, dash=False, width=4):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{colour or PALETTE["ink"]}" stroke-width="{width}" '
            f'stroke-dasharray="{"12 9" if dash else "none"}"/>')


def panel(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PALETTE["paper"]}"/>'


def header(title, subtitle):
    return [panel(40, 40, 1368, 150), label(70, 105, title, size=50), label(70, 166, subtitle)]


def i2c():
    title = "I²C：上拉电阻的上限在哪里"
    items = header(title, "标准模式：上升时间 ≤ 1µs；只检查上升时间这一项约束")
    items += [panel(60, 215, 1328, 800), label(90, 265, "Rp,max = tr / (0.8473 × Cb)", size=42),
              label(90, 330, "上拉电阻 / kΩ"), line(240, 370, 240, 840), line(240, 840, 1260, 840)]
    x = lambda capacitance: 240 + (capacitance - 100) / 300 * 950
    y = lambda resistance: 840 - resistance / 12 * 440
    for tick in (0, 3, 6, 9, 12):
        items += [line(240, y(tick), 1260, y(tick), dash=True, width=1),
                  label(210, y(tick) + 10, str(tick), anchor="end")]
    for tick in (100, 200, 300, 400):
        items += [label(x(tick), 890, str(tick), anchor="middle")]
    points = " ".join(f"{x(c):.2f},{y(1e6 / (.8473 * c) / 1000):.2f}" for c in range(100, 401, 2))
    items += [f'<polyline points="{points}" fill="none" stroke="{PALETTE["ink"]}" stroke-width="6"/>',
              label(620, 470, "上限曲线（由正文公式计算）"),
              line(x(400), y(10) - 14, x(400), y(10) + 14, colour=PALETTE["accent"], width=6),
              line(x(400) - 14, y(10), x(400) + 14, y(10), colour=PALETTE["accent"], width=6),
              label(900, y(10) - 30, "10kΩ：超出上限", colour=PALETTE["accent"]),
              label(735, 805, "400pF → 约 2.9kΩ"),
              label(880, 951, "总线电容 Cb / pF"),
              label(90, 1050, "范围说明：未在本图检查灌电流等其他约束。")]
    return title, items


def thermal():
    title = "热阻串联：同样的功耗，两种温升"
    items = header(title, "正文中的教学估算；环境温度 25°C，功耗 3.5W")
    items += [panel(60, 215, 1328, 790),
              label(90, 275, "TJ = TA + P × (θJC + θCS + θSA)", size=40)]
    for x, name, value in [(100, "结 → 壳", "θJC ≈ 3°C/W"), (530, "壳 → 散热器", "θCS ≈ 1°C/W"),
                            (960, "散热器 → 空气", "θSA ≈ 5°C/W")]:
        items += [label(x, 375, name), label(x, 445, value)]
    items += [line(420, 400, 490, 400), line(850, 400, 920, 400),
              line(80, 500, 1350, 500),
              label(100, 590, "SOT-223 · θJA ≈ 60°C/W", size=36),
              label(100, 655, "25 + 3.5 × 60 = 235°C", colour=PALETTE["accent"], size=40),
              label(100, 718, "超过正文的 125°C 目标", colour=PALETTE["accent"]),
              label(780, 590, "TO-220 + 大散热器", size=36),
              label(780, 655, "25 + 3.5 × 9 ≈ 57°C", size=40),
              label(780, 718, "总热阻：3 + 1 + 5 = 9°C/W"),
              line(80, 775, 1350, 775),
              label(100, 850, "核算实际封装、安装界面和散热器，另留 20°C 裕量。"),
              label(100, 930, "本例提示：3.5W 的线性损耗，应考虑 Buck 方案。"),
              label(90, 1050, "链条等高排布，只用公式与标签表达热阻数值。")]
    return title, items


def priority():
    title = "排故顺序：先查最可能、也最好验证的项"
    items = header(title, "定性排序示意；格子面积不表示故障概率")
    items += [panel(60, 215, 1328, 790), line(240, 850, 1270, 850), line(240, 850, 240, 330),
              line(730, 330, 730, 850, dash=True), line(240, 590, 1270, 590, dash=True),
              label(70, 285, "先验概率"), label(170, 420, "高"), label(170, 750, "低"),
              label(350, 385, "优先核验", size=44, colour=PALETTE["accent"]),
              label(300, 465, "电源与连接：先用万用表"),
              label(300, 525, "先静后动，一次只改一项"),
              label(805, 405, "概率较高 · 成本较高", size=36),
              label(805, 485, "先补测量证据，再拆焊"),
              label(300, 700, "概率较低 · 易验证", size=36),
              label(300, 775, "记录结果，缩小嫌疑范围"),
              label(805, 700, "概率较低 · 难验证", size=36),
              label(805, 775, "放在后面，避免盲目换件"),
              label(350, 920, "容易验证"), label(940, 920, "需要备料 / 拆焊"),
              label(1040, 987, "验证成本 →"),
              label(90, 1050, "先记清症状：多少、何时、多常、最后改了什么。")]
    return title, items


JOBS = {
    "ch17-i2c-rise-time-budget": (i2c, "17.3", "IG-015", "V3",
        "横版参数图底纸。正上方俯视，纸纤维与手工切边集中于画幅边缘，中心是平整奶油白纸面，供后叠坐标图。纸面没有凸起曲线、刻度、坐标轴或电路符号。",
        "A landscape parameter-chart backing sheet seen orthographically from above. Paper fibres and hand-cut edges are confined to the perimeter. The central cream paper is flat, reserved for a deterministic plot. No raised curves, ticks, axes or circuit symbols."),
    "ch17-thermal-chain-audit": (thermal, "17.5.1", "IG-012", "V3",
        "横版热阻链底纸。正上方俯视，三段等厚纸带沿上边缘首尾相接，表现连接关系而非数值大小。主体计算区保持平整留白，纸层阴影只在外边缘。",
        "A landscape thermal-chain backing sheet seen orthographically from above. Three equal-thickness paper strips join along the upper edge, communicating connectivity rather than magnitude. Keep the calculation area flat and blank; shadows stay at the outer edges."),
    "ch17-prior-cost-matrix": (priority, "17.0", "IG-014", "V4",
        "横版取舍矩阵底纸。四块等面积、等厚度纸层平铺，正上方俯视，边缘微有剪切纤维。不要画透视台阶，中心预留平整白区给后叠四象限和判读句。",
        "A landscape trade-off matrix backing sheet. Four paper pieces of equal area and thickness lie flat, viewed orthographically from above, with subtle cut fibres at the edges. No perspective steps. Reserve a flat blank centre for the deterministic quadrant diagram and labels."),
}

PALETTE = {}


def main():
    upstream = upstream_root()
    PALETTE.update({role: "#" + "".join(f"{v:02x}" for v in swatch_rgb(c, upstream))
                    for role, c in COLOURS.items()})
    folder, prompts = ROOT / REVIEW, ROOT / PROMPTS
    folder.mkdir(parents=True, exist_ok=True)
    prompts.mkdir(parents=True, exist_ok=True)
    (folder / "original-request.txt").write_text("继续完成spec计划", encoding="utf-8")
    manifest = {"meta": {"status": "technical-proofs-only", "planner": "article-illustration-planner",
                         "approval": "pending-new-base-images-and-human-review"}, "assets": []}
    for asset_id, (draw, anchor, layout, kind, zh, en) in JOBS.items():
        title, elements = draw()
        markup = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1448 1086">' + "\n".join(elements) + '</svg>\n'
        overlay = f"{REVIEW}/{asset_id}-overlay.svg"
        (ROOT / overlay).write_text(markup, encoding="utf-8")
        spec = {"id": asset_id, "title": title, "alt": title + "；技术校样，纸雕底图与人工复评尚未完成。",
                "canvas": [1448, 1086], "print_width_mm": 138, "paper": PALETTE["paper"],
                "base_image": f"{REVIEW}/{asset_id}-base.png", "overlay": overlay,
                "output": f"{REVIEW}/{asset_id}.svg"}
        (folder / f"{asset_id}.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        compose(spec, print_only=True)
        record = {"id": asset_id, "kind": "pilot-base-image", "status": "planned",
                  "generator": "pending", "style_id": "FF-015", "layout_id": layout,
                  "color_ids": list(COLOURS.values()), "reference_policy": "name+style+traits",
                  "reference_image": None, "capability_baseline": "gpt-image-2",
                  "source_facts": [f"docs/p4-02-ch17.md#{anchor}"],
                  "output": spec["base_image"], "overlay": overlay,
                  "text_policy": "底图无文字、数字、公式与电路符号；全部由确定性 SVG 覆盖。",
                  "zh_prompt": "风格名称：Paper Sculpture Illustration（纸雕插画）。参考作者与风格名称：纸雕。主题色：奶油白（Cream White）纸、炭黑（Charcoal Black）墨、石板灰（Slate Gray）边缘阴影、柿子橙（Persimmon Orange）重点。核心风格特征：纸雕；场景只保留最必要的物件与动作；大面积留白。" + zh + " 横版 4:3，无文字、字母、数字、单位、公式、图例和标注。纸层高度不编码任何数值；重点橙只落纸白区。无微缩桌面摆拍、景深虚化或人物。",
                  "en_prompt": "Style name: Paper Sculpture Illustration. Reference author and style name: Paper Sculpture. Theme color: cream white paper, charcoal black ink, slate grey edge shadows and persimmon orange accents. Core style traits: paper sculpture; only essential objects and actions; generous whitespace. " + en + " Landscape 4:3. No text, letters, digits, units, equations, legends or labels. Layer height never encodes a quantity. Orange accents only on cream paper. No miniature desktop staging, depth-of-field blur or people."}
        (prompts / f"{asset_id}.md").write_text("---\n" + yaml.safe_dump(record, allow_unicode=True, sort_keys=False, width=100) + "---\n", encoding="utf-8")
        manifest["assets"].append({"id": asset_id, "chapter": 17, "kind": "figure", "type": kind,
                                   "anchor": anchor, "layout_id": layout, "status": "planned",
                                   "technical_proof": f"{REVIEW}/{asset_id}-print.svg",
                                   "composition": f"{REVIEW}/{asset_id}.json",
                                   "prompt_file": f"{PROMPTS}/{asset_id}.md", "review_scores": {}})
    (folder / "pilot-manifest.yml").write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"3 张技术图层与提示词 → {REVIEW}；底图未生成，评分未填")


if __name__ == "__main__":
    main()
