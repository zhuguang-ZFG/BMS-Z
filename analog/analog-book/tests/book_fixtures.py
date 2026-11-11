"""临时 docs/site/data 树，供新书管线测试使用。"""
from __future__ import annotations

import json
from pathlib import Path

FRONT = [
    {"kind": "half_title"},
    {"kind": "title_page"},
    {"kind": "copyright"},
    {"file": "p0-01-preface.md", "title": "前言"},
    {"file": "p0-02-how-to-use.md", "title": "怎样读这本书"},
    {"file": "p0-03-timeline.md", "title": "模拟电路简史"},
    {"file": "p0-11-conventions.md", "title": "排版、术语与引用约定"},
    {"file": "p0-12-symbols.md", "title": "符号与单位表"},
    {"kind": "toc"},
    {"kind": "list_of_figures"},
    {"kind": "list_of_tables"},
]

PARTS = [
    {"id": "I", "title": "基础", "subtitle": "先建立电路直觉",
     "intro": "这一篇从电压、电流与无源元件开始，先把电路为什么会这样工作讲清楚。"
              "你会反复使用欧姆定律、基尔霍夫定律与戴维南等效，把复杂网络化简成可计算的小模型。"
              "学完后，你应能独立分析由电源、电阻、电容、电感与负载组成的电路，并解释每个元件为什么在那里。"
              "遇到不确定的符号或单位，先回到附录 G 与前置约定页核对，再继续推导。",
     "opener_art": "part-i.svg",
     "units": [{"title": "电路直觉与无源世界",
                "chapters": ["p1-01-ch0.md", "p1-02-ch1.md"]}]},
    {"id": "II", "title": "器件", "subtitle": "从 PN 结到 555",
     "intro": "器件篇沿着 PN 结、二极管、BJT、MOSFET 一路走到运放、比较器、模拟开关、基准与 555。"
              "重点不是背参数，而是理解器件在什么条件下近似成什么模型，以及模型失效时会发生什么。"
              "每类器件都会配仿真与实测边界，帮助你把手算、仿真与真实波形对上。"
              "读完后，你应能根据数据手册和电路目标选出合适的器件，并预判它的非理想行为。",
     "opener_art": "part-ii.svg",
     "units": [
         {"title": "分立器件", "chapters": ["p1-03-ch2.md", "p1-04-ch3.md",
                                            "p1-05-ch4.md", "p1-06-ch5.md"]},
         {"title": "模拟集成器件", "chapters": ["p1-07-ch6.md", "p1-08-ch7.md",
                                                "p1-09-ch8.md", "p1-10-ch9.md",
                                                "p1-11-ch10.md"]},
     ]},
    {"id": "III", "title": "拓扑", "subtitle": "把器件接成可复用的电路",
     "intro": "拓扑篇把已经认识的器件接成可复用的电路块：放大、滤波、稳压、振荡与信号产生。"
              "你会看到同一组器件如何因偏置、反馈与负载不同而呈现完全不同的传递函数。"
              "分析时先抓大信号工作点，再看小信号等效，最后用仿真检查边角。"
              "目标是让你面对一张陌生原理图时，能先说出它属于哪类拓扑，再决定从哪里下手。",
     "opener_art": "part-iii.svg",
     "units": [{"title": "信号链与功率",
                "chapters": ["p2-01-ch11.md", "p2-02-ch12.md", "p2-03-ch13.md"]}]},
    {"id": "IV", "title": "设计", "subtitle": "从指标到可打样的板",
     "intro": "设计篇从指标出发，把想要什么翻译成增益、带宽、噪声、功耗与成本之间的取舍。"
              "你会练习选型、偏置、稳定性、保护与 PCB 布局，并学会在打样前用计算和仿真排除明显错误。"
              "这里没有唯一正确答案，只有被记录下来的假设、验证与余量。"
              "读完后，你应能独立完成一块小信号模拟板的设计评审。",
     "opener_art": "part-iv.svg",
     "units": [{"title": "方法与实现",
                "chapters": ["p3-01-ch14.md", "p3-02-ch15.md"]}]},
    {"id": "V", "title": "调试", "subtitle": "从现象到根因",
     "intro": "调试篇把前面学到的知识收束成一套可重复的排故方法：先观察现象，再分割电路，提出假设，用测量验证，最后回到根因。"
              "故障速查表覆盖电源、偏置、噪声、振荡、接口与焊接等常见问题，但它的用法是索引而不是背答案。"
              "你会看到经验丰富的工程师如何控制变量、选择接地点与探头，以及如何避免把假象当成结论。"
              "读完后，你应能在没有原理图标注的情况下，仍然有条理地缩小问题范围。",
     "opener_art": "part-v.svg",
     "units": [{"title": "方法与经验",
                "chapters": ["p4-01-ch16.md", "p4-02-ch17.md", "p4-03-ch18.md"]}]},
]

APPENDICES = [
    {"id": "A", "title": "动画与图示索引", "transform": "animation_index",
     "data": "analog-book/data/animations.yml"},
    {"id": "B", "title": "公式与设计速查", "files": ["p0-08-cheatsheet.md"]},
    {"id": "C", "title": "常用芯片速查",
     "files": ["p6-01-s6-1.md", "p6-02-s6-2.md", "p6-03-s6-3.md",
               "p6-04-s6-4.md", "p6-05-s6-5.md"]},
    {"id": "D", "title": "视频课程与配套资源",
     "files": ["p7-01-s7-1.md", "p7-02-s7-2.md", "p7-03-s7-3.md",
               "p8-02-s8-2.md", "p8-03-s8-3.md", "p8-04-s8-4.md",
               "p8-05-s8-5.md", "p8-06-s8-6.md", "p8-07-s8-7.md",
               "p8-08-s8-8.md", "p8-09-s8-9.md"]},
    {"id": "E", "title": "学习路线、选读与诊断",
     "files": ["p0-04-by-need.md", "p0-05-picks.md", "p0-06-roadmap.md",
               "p0-09-diagnostic.md", "p8-01-s8-1.md", "p8-11-s8-11.md"]},
    {"id": "F", "title": "习题答案与综合自测", "transform": "answers",
     "files": ["p9-00-quiz.md"]},
    {"id": "G", "title": "术语表", "files": ["p9-15-glossary.md", "p8-10-s8-10.md"]},
    {"id": "H", "title": "模型、近似与适用边界", "files": ["p0-10-model-limits.md"]},
]

EXCLUDED = [
    {"file": "index.md", "reason": "站点首页"},
    {"file": "p0-07-toc.md", "reason": "由书内详细目录替代"},
    {"file": "p1-00-part1.md", "reason": "由书内第 I 篇首页替代"},
    {"file": "p2-00-part2.md", "reason": "由书内第 III 篇首页替代"},
    {"file": "p3-00-part3.md", "reason": "由书内第 IV 篇首页替代"},
    {"file": "p4-00-part4.md", "reason": "由书内第 V 篇首页替代"},
    {"file": "p5-00-part5.md", "reason": "附录 A 素材"},
    {"file": "p6-00-part6.md", "reason": "附录 C 分隔页由构建生成"},
    {"file": "p7-00-part7.md", "reason": "附录 D 分隔页由构建生成"},
    {"file": "p8-00-part8.md", "reason": "附录 D/E/G 分隔页由构建生成"},
]

BACK = [
    {"kind": "bibliography"},
    {"kind": "index", "terms": "analog-book/data/index-terms.yml"},
    {"file": "p9-12-changelog.md", "title": "版本记录"},
    {"file": "p9-13-thanks.md", "title": "致谢"},
    {"file": "p9-14-credits.md", "title": "来源与许可"},
    {"kind": "colophon"},
]


def manifest():
    data = {
        "schema": 2,
        "title": "通往模拟电路之路",
        "subtitle": "从欧姆定律到芯片内部结构",
        "edition": "第一版",
        "version": "2.0.0-draft.1",
        "source_version": "3.61",
        "date": "2026-10-25",
        "language": "zh-CN",
        "author": "zhuguang-ZFG 与贡献者",
        "site_url": "https://aliyun-hutuji.donglicao.com/analog-circuit-roadmap/",
        "repository": "https://github.com/zhuguang-ZFG/analog-circuit-roadmap",
        "license": "CC BY-SA 4.0",
        "trim": {"width_mm": 185, "height_mm": 260},
        "front_matter": FRONT,
        "parts": PARTS,
        "appendices": APPENDICES,
        "excluded_pages": EXCLUDED,
        "back_matter": BACK,
        "cover": {
            "bleed_mm": 3, "crop_marks": True, "paper_caliper_mm": 0.10,
            "spine_allowance_mm": 1.0, "isbn_area": False,
            "back_cover": {
                "blurb": "把直觉、推导、仿真、实测与排故连起来。",
                "audience": "电子、自动化、通信与嵌入式方向的学生和工程师。",
                "highlights": ["19 章完整知识链", "三层读法", "可复现仿真",
                               "实测实验", "故障速查与索引"],
            },
        },
        "release": {"edition_status": "draft", "stable_version": "1.0.0"},
    }
    # 每个测试拿到独立副本，避免用例内的修改污染共享常量。
    return json.loads(json.dumps(data))


def direct_files(manifest_data):
    files = [e["file"] for e in manifest_data["front_matter"] if "file" in e]
    for part in manifest_data["parts"]:
        for unit in part["units"]:
            files.extend(unit["chapters"])
    for appendix in manifest_data["appendices"]:
        files.extend(appendix.get("files", []))
    files.extend(e["file"] for e in manifest_data["back_matter"] if "file" in e)
    return files


def all_docs(manifest_data):
    return direct_files(manifest_data) + [e["file"] for e in manifest_data["excluded_pages"]]


def write_docs(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for name in all_docs(manifest()):
        title = Path(name).stem.replace("-", " ")
        (root / name).write_text(f"# {title}\n\n正文示例。\n", encoding="utf-8")


def write_site(site: Path) -> Path:
    """在给定的最终 site 目录下写出站点夹具。"""
    site.mkdir(parents=True, exist_ok=True)
    for rel in ("assets/stylesheets/main.abc.min.css", "assets/stylesheets/palette.abc.min.css"):
        path = site / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("body{margin:0}", encoding="utf-8")
    for name in ("typography", "gallery", "learning", "reading", "diag"):
        path = site / "stylesheets" / f"{name}.css"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("/* fixture */", encoding="utf-8")
    for name in ("calc", "learning", "learning-catalog", "diag"):
        path = site / "javascripts" / f"{name}.js"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("/* fixture */", encoding="utf-8")
    svg = site / "assets" / "svg" / "fixture.svg"
    svg.parent.mkdir(parents=True, exist_ok=True)
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="40"></svg>',
                   encoding="utf-8")
    for name in all_docs(manifest()):
        title = Path(name).stem.replace("-", " ")
        body = f'<h1>{title}</h1><p>正文示例。</p><h2>1.1 示例小节</h2><p>内容。</p>'
        if name == "p1-01-ch0.md":
            body = ('<h1>📘 第 0 章 电路直觉</h1><p>正文。</p>'
                    '<h2>0.1 电压与电位</h2><p>内容。</p>'
                    '<figure><img src="assets/svg/fixture.svg" alt="夹具图">'
                    '<figcaption>夹具插图</figcaption></figure>'
                    '<p><strong>表 0-1　夹具表</strong></p>'
                    '<table><tr><td>1</td></tr></table>')
        if name == "p9-00-quiz.md":
            body = ('<h1>自测</h1>'
                    '<p><a id="quiz-ch0"></a></p><h2>第 0 章</h2><ol>'
                    '<li><p><a id="q-ch0-01" data-quiz-question="true"></a>'
                    '示例问题？</p><details class="note"><summary>答案</summary>'
                    '<p>示例答案。</p></details></li></ol>'
                    '<p><a id="quiz-ch1"></a></p><h2>第 1 章</h2><ol>'
                    '<li><p><a id="q-ch1-01" data-quiz-question="true"></a>'
                    '第二题？</p><details class="note"><summary>答案</summary>'
                    '<p>第二答案。</p></details></li></ol>'
                    '<h2>专题加练</h2><ol>'
                    '<li><p><a id="q-extra-01" data-quiz-question="true"></a>'
                    '综合题？</p><details class="note"><summary>答案</summary>'
                    '<p>综合答案。</p></details></li></ol>')
        path = site / name.replace(".md", ".html")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<html><body><article class="md-content__inner md-typeset">'
            + body + "</article></body></html>", encoding="utf-8")
    return site


def write_data(data: Path) -> Path:
    """在给定的最终 data 目录下写出数据夹具。"""
    from book.data import EXPECTED_ANIMATIONS
    data.mkdir(parents=True, exist_ok=True)
    animations = [
        {"id": f"anim-{i:03d}", "file": "p5-00-part5.md", "title": f"动画 {i}",
         "chapter": i % 19, "anchor": f"demo{i}", "one_line": "示例动画。",
         "static_svg": "assets/svg/fixture.svg"}
        for i in range(1, EXPECTED_ANIMATIONS + 1)
    ]
    import yaml
    (data / "animations.yml").write_text(
        yaml.safe_dump(animations, allow_unicode=True, sort_keys=False), encoding="utf-8")
    terms = [
        {"term": "米勒效应", "english": "Miller effect",
         "primary": "page-p1-01-ch0", "anchors": ["page-p1-01-ch0"], "see_also": []},
        {"term": "欧姆定律", "english": "Ohm's law",
         "primary": "page-p1-01-ch0", "anchors": ["page-p1-01-ch0"], "see_also": []},
    ]
    (data / "index-terms.yml").write_text(
        yaml.safe_dump(terms, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (data / "sources.yml").write_text("[]\n", encoding="utf-8")
    (data / "references.yml").write_text("[]\n", encoding="utf-8")
    signoff = [{"chapter": i, "draft_version": "2.0.0-draft.1",
                "technical_reviewer": "", "editorial_reviewer": "",
                "safety_reviewer": "", "date": "2026-10-25", "open_issues": []}
               for i in range(19)]
    (data / "chapter-signoff.yml").write_text(
        yaml.safe_dump(signoff, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return data
