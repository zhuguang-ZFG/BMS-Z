"""Question-led reading desk for the collection's offline editions."""

from html import escape
from pathlib import Path

ASSETS = Path(__file__).with_name("assets")


def size(value):
    return (
        f"{value / 1048576:.1f} MiB" if value >= 1048576 else f"{value / 1024:.1f} KiB"
    )


def edition(item):
    name = escape(item["latest"])
    label = escape(item["label"])
    return f'''<div class="edition">
<div><a class="download" href="{name}" download>{label} <span aria-hidden="true">↓</span></a>
<span class="size">{size(item["bytes"])}</span><p>{escape(item["description"])}</p></div>
<details><summary>版本与校验</summary><a href="{escape(item["versioned"])}">{escape(item["versioned"])}</a>
<p>SHA-256</p><code>{escape(item["sha256"])}</code></details></div>'''


def landing_page(release, files):
    combined = "".join(edition(f) for f in files if f["volume"] == "combined")
    volumes = []
    for volume in release["volumes"]:
        slug = "volume-1" if volume["id"] == "I" else "volume-2"
        links = "".join(edition(f) for f in files if f["volume"] == slug)
        volumes.append(
            f'<section class="volume"><p class="index">卷 {escape(volume["id"])}</p><h3>{escape(volume["title"])}</h3><p>{escape(volume.get("subtitle", ""))}</p>{links}</section>'
        )
    report = (
        '<a href="combined-build-report.json">合集构建记录</a>'
        if release.get("combined_report")
        else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="从模拟电路到 BMS：两卷合集下载。带着测量、保护、估算三个问题，读懂从电芯到系统的工程故事。">
<title>{escape(release["title"])} · 两卷合集下载</title>
<link rel="stylesheet" href="download.css"><script src="download.js" defer></script>
</head><body><a class="skip" href="#downloads">跳到合集下载</a>
<div class="page"><header class="masthead"><a href="../reading.html">BMS-Z / 开源工程书架</a><span>两卷合集 · v{escape(release["version"])}</span></header>
<main><section class="opening" aria-labelledby="title"><div class="opening-copy">
<p class="index">从一个读数开始</p><h1 id="title">从模拟电路<br>到 <span>BMS</span></h1>
<p class="lead">电压降了，是电量少了？<br>保护触发了，为什么还没关断？</p>
<p>沿着一个个现场问题，从器件原理走到电池管理系统。先猜，再算，最后拿证据说话。</p>
<a class="jump" href="#downloads">把两卷带走 <span aria-hidden="true">↘</span></a>
<a class="quiet" href="#routes">先挑一个问题读</a></div>
<figure class="notebook"><figcaption><span>实验手记 01</span><strong>同一颗电芯，两个读数。</strong></figcaption>
<svg class="meter" viewBox="0 0 460 264" role="img" aria-labelledby="meter-title meter-desc">
<title id="meter-title">负载变化时的端电压</title><desc id="meter-desc">教学模型：开路电压 3.70 伏，内阻 20 毫欧；20 安放电时端电压为 3.30 伏。下方滑块可以改变电流。</desc>
<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
<path d="M40 65 Q72 62 107 66 L109 191 Q73 195 39 190Z" stroke-width="2.2" fill="var(--cell)"/>
<path d="M58 64 L58 55 L88 55 L89 64 M72 84V104 M62 94H82 M62 170H82" stroke-width="2"/>
<path d="M45 117L102 119 M45 123L102 125 M45 129L102 131" stroke-width=".7"/>
<path d="M144 121Q174 114 203 121L196 115 M203 121L196 128" stroke="var(--accent)" stroke-width="2"/>
<path d="M228 69Q313 64 413 70L416 201Q323 207 227 201Z" stroke-width="2" fill="var(--meter)"/>
<path d="M243 88H399V157H243Z" stroke-width="1"/>
<circle cx="322" cy="181" r="11" stroke-width="1.8"/><path d="M322 181L328 174 M246 181H264 M379 181H397" stroke-width="2"/>
</g><g fill="currentColor" font-family="system-ui,sans-serif">
<text x="74" y="231" text-anchor="middle" font-size="15">Uoc = 3.70 V</text>
<text x="174" y="151" text-anchor="middle" font-size="13">观察读数</text>
<text id="meter-voltage" x="321" y="137" text-anchor="middle" font-family="Consolas,monospace" font-size="40">3.30 V</text>
<text x="322" y="233" text-anchor="middle" font-size="15">端电压 U</text></g></svg>
<div class="experiment" hidden><label for="current">试着改变放电电流 <output id="current-value" for="current">20 A</output></label>
<input id="current" type="range" min="0" max="30" step="1" value="20" aria-describedby="assumptions">
<div class="range-ends"><span>0 A · 静置</span><span>30 A · 带载</span></div></div>
<p class="equation" id="equation">3.70 − 20 × 0.020 = <strong>3.30 V</strong></p>
<p class="pencil">少掉的 <span id="drop">0.40</span> V，原来是欧姆压降。</p>
<p class="fine" id="assumptions">教学模型 U = Uoc − I × R0，R0 = 20 mΩ。只看瞬时欧姆压降，忽略极化、温度与容量变化。图中箭头表示观察关系。</p>
<noscript><p class="fine">静态示例：0 A 时为 3.70 V；20 A 时为 3.30 V。</p></noscript></figure></section>
<section id="downloads" class="collection" aria-labelledby="collection-title">
<figure class="cover"><img src="collection-cover.png" width="1191" height="1684" loading="lazy" alt="合集封面：从模拟电路到 BMS，同一颗电芯的两次电压观察"><figcaption>两卷装进一本，线索连在一起。</figcaption></figure>
<div><p class="index">完整合集</p><h2 id="collection-title">一本书，两段相接的旅程。</h2><p>卷一建立电路直觉，卷二把它用到 BMS。统一封面、总目录与导读；EPUB 的跨卷引用可直接跳转，PDF 保留两卷书签。</p>
{combined}<p class="fine">手机与可调字号阅读选 EPUB；保留整页图文关系选 PDF。交互实验收在下方分卷 HTML 中。</p></div></section>
<section id="routes" class="routes" aria-labelledby="routes-title"><p class="index">带着问题入书</p><h2 id="routes-title">今天，先追哪条线索？</h2>
<a class="route" href="../book/05-测量链.html"><span class="route-no">01</span><div><h3>这个读数，可信吗？</h3><p>从基准与采样走到误差预算。读完画一张误差传递图。</p><small>卷一 9、12、13 章 → 卷二 5–6 章</small></div><span aria-hidden="true">↗</span></a>
<a class="route" href="../book/07-保护tick48.html"><span class="route-no">02</span><div><h3>异常出现了，为什么还没断？</h3><p>跟着采样、去抖和关断走三拍，解释动作发生的时刻。</p><small>卷一 16–17 章 → 卷二 7–9 章</small></div><span aria-hidden="true">↗</span></a>
<a class="route" href="../book/10-模型OCV四项.html"><span class="route-no">03</span><div><h3>只看电压，能猜出电量吗？</h3><p>拆开开路电压、端电压与 SOC，再看模型能补上什么。</p><small>卷二 10–13 章 · 从一张曲线走到状态估计</small></div><span aria-hidden="true">↗</span></a>
<p class="reading-note">留一页空白做手记：<strong>我的猜测 → 我的计算 → 证据 → 还不能证明什么。</strong></p></section>
<section aria-labelledby="volumes-title" class="separate"><p class="index">分卷阅读</p><h2 id="volumes-title">也可以一次只带走一卷。</h2><p>HTML 可离线查看公式、插图与交互；PDF 适合整页阅读；EPUB 支持随字号重排。</p><div class="volumes">{"".join(volumes)}</div></section>
<section class="verification" aria-label="版本与文件校验"><h2>把这一版收好</h2><p>v{escape(release["version"])} · 稳定下载地址与版本文件均在上方。校验值用于核对下载是否完整。</p><nav aria-label="校验文件"><a href="SHA256SUMS.txt">SHA-256 校验清单</a><a href="downloads.json">文件与版本清单</a>{report}</nav><p class="fine">16K 印刷分册随 <a href="https://github.com/zhuguang-ZFG/BMS-Z/releases">GitHub Release</a> 工件提供。</p></section></main>
<footer><a href="../reading.html">← 返回书籍与阅读路线</a><span>文档 CC BY-SA 4.0 · 代码 MIT</span></footer></div></body></html>"""
