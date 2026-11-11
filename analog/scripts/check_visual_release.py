#!/usr/bin/env python3
"""Final visual inventory gate; generated assets are not accepted deliverables.

The manifest validator permits migration work in progress. This gate enforces
the accepted design's release floors, evidence and legacy disposition instead.
Counts use main outputs, never the three SVG files in an animation bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import audit_visual_density as density
import check_visual_manifest as manifest

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'docs/superpowers/visual/baseline-2026-11-04.json'
ACCEPTED = {'accepted', 'published'}
MOTION_TAGS = {'animate', 'animateMotion', 'animateTransform'}
REDUCTION_FLOOR_PCT = 10


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def inventory(data: dict, root: Path) -> tuple[dict, list[str]]:
    """Count independently reviewed main assets, checking the evidence version."""
    errors = []
    accepted = {'animation': set(), 'figure': set(), 'photo': set()}
    seen_outputs, seen_animation_hashes = set(), set()
    for asset in data['assets']:
        if asset.get('status') not in ACCEPTED:
            continue
        aid, output, kind = asset['id'], asset['output'], asset['kind']
        path = root / output
        if output in seen_outputs:
            errors.append(f'{aid}: duplicate main output {output}')
            continue
        seen_outputs.add(output)
        record = asset.get('review_record', {})
        if not record.get('record') or not (root / record['record']).is_file():
            errors.append(f'{aid}: missing review evidence')
            continue
        if not path.is_file() or record.get('asset_sha256') != digest(path):
            errors.append(f'{aid}: reviewed bytes differ from current output')
            continue
        dims = manifest.SCORE_DIMS + (manifest.ANIM_DIMS if kind == 'animation' else [])
        scores = asset.get('review_scores', {})
        if any(type(scores.get(d)) not in (int, float) or not 4 <= scores[d] <= 5 for d in dims):
            errors.append(f'{aid}: incomplete or failing review scores')
            continue
        if kind == 'animation':
            if sum(scores[d] for d in dims) < 30:
                errors.append(f'{aid}: animation score below 30/35')
                continue
            try:
                tree = ET.parse(path)
            except (ET.ParseError, OSError):
                errors.append(f'{aid}: invalid animation SVG')
                continue
            if not any(el.tag.rsplit('}', 1)[-1] in MOTION_TAGS for el in tree.iter()):
                errors.append(f'{aid}: static output cannot count as animation')
                continue
            sha = digest(path)
            if sha in seen_animation_hashes:
                errors.append(f'{aid}: duplicate animation bytes')
                continue
            seen_animation_hashes.add(sha)
        accepted[kind].add(output)
    return accepted, errors


def legacy_errors(data: dict, baseline: dict, root: Path) -> list[str]:
    errors = []
    by_output = {a['output']: a for a in data['assets']}
    for name in baseline['inventory']['svg_animations']['sha256']:
        output = 'assets/svg/' + name
        asset = by_output.get(output, {})
        disposition = asset.get('legacy_disposition', {})
        action = disposition.get('action')
        record = disposition.get('record')
        if (action not in {'keep', 'rebuild', 'retire'} or not disposition.get('reason')
                or not record or not (root / record).is_file()):
            errors.append(f'{output}: missing individual legacy disposition')
        elif action == 'keep' and asset.get('status') not in ACCEPTED:
            errors.append(f'{output}: kept animation lacks acceptance')
        elif action == 'rebuild':
            replacement = by_output.get(disposition.get('replacement'), {})
            if replacement.get('status') not in ACCEPTED or replacement.get('output') == output:
                errors.append(f'{output}: rebuilt replacement lacks acceptance')
    return errors


def character_reduction(baseline: dict, rows: list[dict]) -> dict:
    """两个口径分别算：prose 是规格要压的正文，raw 含 alt/图注/标签，只作参考。

    插图替代文字时 raw 会因图注变多而上升，拿它判闸会把「图真的替了字」误报成失败。
    """
    measured = {}
    for key, name in (('prose_chars', 'prose'), ('chars', 'raw')):
        before = sum(r[key] for r in baseline['chapters'])
        after = sum(r[key] for r in rows)
        measured[name] = 1 - after / before
    return measured


def reduction_errors(baseline: dict, rows: list[dict]) -> tuple[list[str], dict]:
    measured = character_reduction(baseline, rows)
    before = sum(r['prose_chars'] for r in baseline['chapters'])
    after = sum(r['prose_chars'] for r in rows)
    errors = []
    # 整数交叉相乘判闸：1 - 900/1000 在浮点下是 0.0999…，正好压到 10% 会被误判。
    if after * 100 > before * (100 - REDUCTION_FLOOR_PCT):
        errors.append(f'chapter prose character reduction: '
                      f'{measured["prose"]:.1%} < {REDUCTION_FLOOR_PCT}%')
    return errors, measured


def check(data: dict, baseline: dict, rows: list[dict], root: Path = ROOT) -> dict:
    accepted, errors = inventory(data, root)
    errors += legacy_errors(data, baseline, root)
    total = sum(row['visuals'] for row in rows)
    animations = len(accepted['animation'])
    statics = len(accepted['figure'] | accepted['photo'])
    for label, actual, floor in [('inline visuals', total, 390),
                                  ('reviewed animations', animations, 220),
                                  ('reviewed static assets', statics, 180)]:
        if actual < floor:
            errors.append(f'{label}: {actual} < {floor}')
    accepted_paths = set.union(*accepted.values())
    by_output = {a['output']: a for a in data['assets']}
    for row in rows:
        ch = row['chapter']
        paths = set(row['assets'])
        for output in sorted(paths - accepted_paths):
            errors.append(f'ch{ch}: inline asset lacks current acceptance: {output}')
        for output in sorted(paths):
            action = by_output.get(output, {}).get('legacy_disposition', {}).get('action')
            if action in {'rebuild', 'retire'}:
                errors.append(f'ch{ch}: replaced/retired animation still inline: {output}')
        if len(paths & accepted['animation']) < 6:
            errors.append(f'ch{ch}: fewer than 6 reviewed inline animations')
        if (row['visuals'] < row['budget'] or row['longest_gap'] > 1500
                or row['clusters'] or row['h2_no_visual']):
            errors.append(f'ch{ch}: density gate failed')
        if ch in {0, 8, 17}:
            v2 = {p for p in paths & accepted['animation'] if p.startswith('assets/svg-v2/')}
            if len(v2) < 4 or len(paths & (accepted['figure'] | accepted['photo'])) < 6:
                errors.append(f'ch{ch}: pilot needs 4 V2 animations and 6 static assets')
    reduction_failures, measured = reduction_errors(baseline, rows)
    errors += reduction_failures
    return {'inline_visuals': total, 'accepted_animations': animations,
            'accepted_static_assets': statics,
            'source_character_reduction': measured['prose'],
            'raw_character_reduction': measured['raw'],
            'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    result = check(manifest.load(), json.loads(BASELINE.read_text(encoding='utf-8')),
                   [density.audit(path) for path in density.chapters()])
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'errors'}, ensure_ascii=False))
    for error in result['errors'][:30]:
        print('FAIL:', error)
    print(f'visual release: {len(result["errors"])} failures')
    return int(bool(result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
