#!/usr/bin/env python3
"""手绘草图批次：落盘 SVG、纸墨皮肤、预览与 manifest 登记。"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import check_visual_manifest as manifest
from compose_technical_overlay import preview
from label_handraw_figures import label

from scripts.visuals import static_fig
from scripts.visuals.font_gate import assert_covered

REVIEW = ROOT / 'docs/superpowers/visual/reviews/task8-2026-11-05'
PROMPTS = ROOT / 'docs/superpowers/visual/prompts'
ASSETS = ROOT / 'assets/figures-v2'
CANVAS = (1000, 700)
PRINT_MM = 138
STYLE = 'FA-029'
COLORS = ['C-30', 'C-31', 'C-29']


def build_one(asset_id: str, meta: dict) -> None:
    inner = '\n'.join(meta['draw']())
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS[0]} {CANVAS[1]}">'
           f'\n{inner}\n</svg>\n')
    svg = label(static_fig.finalize(svg, meta['title']), meta)
    assert_covered(svg, asset_id)
    REVIEW.mkdir(parents=True, exist_ok=True)
    review_svg = REVIEW / f'{asset_id}.svg'
    review_svg.write_text(svg, encoding='utf-8')
    outputs = {
        'composite': ASSETS / f'{asset_id}.svg',
        'print': ASSETS / f'{asset_id}-print.svg',
    }
    outputs['composite'].write_text(svg, encoding='utf-8')
    outputs['print'].write_text(svg, encoding='utf-8')
    # 2x 预览：网页/画廊里缩小显示时不糊；SVG 本身仍是矢量，印刷不受影响。
    report = preview(review_svg, {'canvas': list(CANVAS), 'print_width_mm': PRINT_MM,
                                  'scale': 2})
    for name, path in outputs.items():
        print(asset_id, name, report)
    webp = review_svg.with_suffix('.webp')
    (ASSETS / f'{asset_id}.webp').write_bytes(webp.read_bytes())
    spec = {
        'id': asset_id, 'title': meta['title'], 'alt': meta['alt'],
        'anchor': meta['anchor'], 'source': meta['source'],
        'canvas': list(CANVAS), 'print_width_mm': PRINT_MM,
        'generator': 'python-handraw-v1',
        'output': f'assets/figures-v2/{asset_id}.svg',
        'print_fallback': f'assets/figures-v2/{asset_id}-print.svg',
    }
    (REVIEW / f'{asset_id}.json').write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def register(asset_id: str, meta: dict, data: dict) -> None:
    prompt = PROMPTS / f'{asset_id}.md'
    record = {
        'id': asset_id, 'generator': 'python-handraw-v1',
        'reference_policy': 'name+style+traits', 'style_id': STYLE,
        'layout_id': 'IG-013', 'color_ids': COLORS, 'numbers': meta.get('numbers', []),
        'source_facts': [f'{meta["source"]}#{meta["anchor"]}'],
        'authorization': '2026-11-05 用户要求增加手绘插图',
        'composition': f'docs/superpowers/visual/reviews/task8-2026-11-05/{asset_id}.json',
        'zh_prompt': (f'风格名称：手绘纸墨草图。主题：{meta["title"]}。'
                      '象牙纸、佩恩灰墨线、赭石标记；线条略带手绘弯曲，'
                      '中文标签保持印刷可读，几何不编码虚假量值。'),
        'en_prompt': (f'Style name: hand-drawn paper-and-ink sketch. Subject: {meta["title"]}. '
                      'Ivory paper, Payne grey ink, ochre accents; slightly bowed hand-drawn '
                      'lines with print-readable Chinese labels. Geometry never encodes values.'),
    }
    prompt.write_text('---\n' + yaml.safe_dump(
        record, allow_unicode=True, sort_keys=False, width=100) + '---\n',
        encoding='utf-8')
    asset = {
        'id': asset_id, 'chapter': meta['chapter'], 'kind': 'figure', 'type': 'V4',
        'anchor': meta['anchor'], 'purpose': meta['title'], 'style_id': STYLE,
        'layout_id': 'IG-013', 'color_ids': COLORS,
        'source_facts': record['source_facts'], 'prompt_file': f'docs/superpowers/visual/prompts/{asset_id}.md',
        'output': f'assets/figures-v2/{asset_id}.svg',
        'print_fallback': f'assets/figures-v2/{asset_id}-print.svg',
        'preview': f'assets/figures-v2/{asset_id}.webp',
        'alt': meta['alt'], 'status': 'generated',
        'status_history': ['planned', 'generated'], 'review_scores': {},
        'generator': 'python-handraw-v1', 'composition': record['composition'],
        'quant_rules': {'layer_encodes_value': False},
    }
    old = next((a for a in data['assets'] if a['id'] == asset_id), None)
    if old is None:
        data['assets'].append(asset)
        return
    # 重跑 builder 只刷新图形与元数据；人工审图结果仅在底图字节未变时原样带过来，
    # 否则一次「重建」会把已签核的评分留在改过的图上，或把评分悄悄清空。
    raw = (ASSETS / f'{asset_id}.svg').read_bytes().replace(b'\r\n', b'\n')
    reviewed = (old.get('review_record') or {}).get('asset_sha256')
    if reviewed and reviewed == hashlib.sha256(raw).hexdigest():
        for field in ('status', 'status_history', 'review_scores', 'review_record'):
            if old.get(field):
                asset[field] = old[field]
    data['assets'][data['assets'].index(old)] = asset


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenes", default="scripts.visuals.scenes.handdrawn_wave2")
    ap.add_argument("--only", help="逗号分隔的资产 id；只重出这些，防止误建模块里的旧场景")
    args = ap.parse_args()
    scenes = importlib.import_module(args.scenes).SCENES
    if args.only:
        wanted = [item.strip() for item in args.only.split(",") if item.strip()]
        missing = [item for item in wanted if item not in scenes]
        if missing:
            raise SystemExit(f"{args.scenes} 不含: {', '.join(missing)}")
        scenes = {item: scenes[item] for item in wanted}
    data = manifest.load()
    for asset_id, meta in scenes.items():
        build_one(asset_id, meta)
        register(asset_id, meta, data)
    manifest.dump(data)
    print(f'{len(scenes)} 张手绘草图已绘制；待人工审图。')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
