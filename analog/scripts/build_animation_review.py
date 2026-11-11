"""生成 V2 动画审阅页，内含动态 SVG 与静帧/分镜，无需本地服务器。"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import re
from pathlib import Path

from check_visual_manifest import ROOT, load


def image_data(path: str):
    return 'data:image/svg+xml;base64,' + base64.b64encode((ROOT / path).read_bytes()).decode('ascii')


def review_status(asset: dict) -> str:
    labels = {'planned': '待生成', 'generated': '已生成，待审阅',
              'reviewed': '已审阅，待验收', 'accepted': '已验收', 'published': '已发布'}
    status = asset.get('status', '')
    label = labels.get(status, status or '未登记状态')
    if status in {'accepted', 'published'}:
        record = asset.get('review_record') or {}
        path = ROOT / asset['output']
        digest = hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if record.get('asset_sha256') != digest:
            return label + '（当前文件与审阅哈希不符，须复审）'
        evidence = record.get('record')
        if not evidence or not (ROOT / evidence).is_file():
            return label + '（缺审阅记录，须补证据）'
    return label


def build(chapter: int | None = None, output: Path | None = None):
    output = output or ROOT / 'build/visual-v2/review.html'
    output.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for a in load()['assets']:
        if a.get('kind') != 'animation' or not a.get('output', '').startswith('assets/svg-v2/'):
            continue
        if chapter is not None and a.get('chapter') != chapter:
            continue
        svg = (ROOT / a['output']).read_text(encoding='utf-8')
        # 每张 SVG 的局部 ID 隔离，内联多个动画时不借用邻图的渐变/滤镜。
        prefix = a['id'] + '-'
        ids = re.findall(r'\bid="([^"]+)"', svg)
        for value in ids:
            svg = svg.replace('id="' + value + '"', 'id="' + prefix + value + '"')
            svg = svg.replace('url(#' + value + ')', 'url(#' + prefix + value + ')')
        svg = re.sub(r'aria-labelledby="([^"]+)"',
                     lambda m: 'aria-labelledby="' + ' '.join(prefix + x for x in m.group(1).split()) + '"', svg)
        duration = float(str(a['duration']).removesuffix('s'))
        buttons = ''.join(f'<button type="button" data-time="{b["start"] + .6}">{html.escape(b["name"])}</button>' for b in a['beats'])
        facts = '；'.join(a.get('source_facts', []))
        status = review_status(a)
        cards.append(f'<article data-duration="{duration}"><h2>{html.escape(a["id"])}</h2>'
                     f'<p>{html.escape(status)} · 第 {a["chapter"]} 章</p>'
                     f'<p>事实来源：{html.escape(facts)}</p>'
                     '<div class="canvas">' + svg + '</div>'
                     '<div class="controls"><button type="button" data-replay>重播一次</button>' + buttons + '</div>'
                     f'<details><summary>结论静帧与完整打印分镜</summary><img alt="结论静帧" src="{image_data(a["reduced_motion"])}">'
                     f'<img alt="打印分镜" src="{image_data(a["storyboard"])}"></details></article>')
    script = """document.querySelectorAll('article').forEach(card=>{
const svg=card.querySelector('svg'),duration=Number(card.dataset.duration);let frame;
svg.pauseAnimations();svg.setCurrentTime(duration);
card.querySelector('[data-replay]').onclick=()=>{cancelAnimationFrame(frame);svg.setCurrentTime(0);svg.unpauseAnimations();
function end(){if(svg.getCurrentTime()>=duration){svg.pauseAnimations();svg.setCurrentTime(duration);}else{frame=requestAnimationFrame(end);}}frame=requestAnimationFrame(end);};
card.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{cancelAnimationFrame(frame);svg.pauseAnimations();svg.setCurrentTime(Number(b.dataset.time));});});"""
    document = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>V2 动画技术审阅</title><style>body{margin:24px auto;max-width:1100px;padding:0 16px;background:#e2d9cf;color:#2a2927;font-family:system-ui,sans-serif}'
                'article{margin:32px 0;padding:20px;border:1px solid #535453}h1{font-size:28px}h2{font-size:18px;overflow-wrap:anywhere}'
                'svg,img{display:block;width:100%;height:auto}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}'
                'button,summary{font:inherit;min-height:44px;padding:8px;cursor:pointer}details img{margin:20px 0}'
                'body.gray .canvas,body.gray details img{filter:grayscale(1)}</style>'
                f'<h1>V2 动画技术审阅</h1><p>共 {len(cards)} 个场景，默认停在结论帧。可重播或按节拍查看；'
                '状态来自 manifest。本页生成成功不代表通过目视或最终 PDF 验收。</p>'
                '<button type="button" onclick="document.body.classList.toggle(\'gray\');this.setAttribute(\'aria-pressed\',document.body.classList.contains(\'gray\'))" aria-pressed="false">切换灰度对照</button>'
                + ''.join(cards) + '<script>' + script + '</script></html>')
    output.write_text(document, encoding='utf-8')
    print(output.resolve())
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chapter', type=int, choices=range(19))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(args.chapter, args.output)
