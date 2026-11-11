"""Build the two planned ch2 mechanism scenes, preserving unchanged reviews."""
import hashlib
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import check_visual_manifest as manifest
from scripts.visuals.render import write
from scripts.visuals.scenes.ch02_charge_window_v2 import META as CHARGE
from scripts.visuals.scenes.ch02_bridge_power_v2 import META as BRIDGE


def build():
    data = manifest.load()
    for meta in [CHARGE, BRIDGE]:
        aid = meta['id']
        tl, layers = meta['scene']()
        # Purpose-designed print diagram: do not shrink four full scenes into tiny cells.
        write(tl, layers, ROOT / 'assets/svg-v2', aid, print_storyboard=meta['storyboard']())
        output = f'assets/svg-v2/{aid}.svg'
        reduced = f'assets/svg-v2/{aid}-static.svg'
        storyboard = f'assets/svg-v2/{aid}-storyboard.svg'
        prompt = f'docs/superpowers/visual/prompts/{aid}.md'
        facts = [meta['source'] + '#' + meta['anchor']]
        record = {
            'id': aid, 'generator': 'svg-v2-scene', 'reference_policy': 'none',
            'style_id': meta['style_id'], 'layout_id': meta['layout_id'], 'color_ids': ['C-34', 'C-32'],
            'source_facts': facts, 'numbers': meta.get('numbers', []), 'zh_prompt': meta['alt'], 'en_prompt': meta['en_prompt'],
        }
        (ROOT / prompt).write_text('---\n' + yaml.safe_dump(record, allow_unicode=True, sort_keys=False) + '---\n', encoding='utf-8')
        asset = {
            'id': aid, 'chapter': 2, 'kind': 'animation', 'type': meta['type'],
            'anchor': meta['anchor'], 'purpose': meta['purpose'], 'style_id': meta['style_id'],
            'layout_id': meta['layout_id'], 'color_ids': record['color_ids'],
            'source_facts': facts, 'prompt_file': prompt, 'output': output,
            'print_fallback': storyboard, 'storyboard': storyboard, 'reduced_motion': reduced,
            'alt': meta['alt'], 'status': 'generated', 'status_history': ['planned', 'generated'],
            'review_scores': {}, 'duration': tl.duration, 'parameters': [],
            'beats': [{'name': b.name, 'start': b.start, 'end': b.end, 'caption': b.caption} for b in tl.beats],
            'conclusion_frame': {'beat': tl.beats[-1].name, 'output': reduced},
        }
        old = next((a for a in data['assets'] if a['id'] == aid), None)
        sha = hashlib.sha256((ROOT / output).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
        if old and old.get('review_record', {}).get('asset_sha256') == sha:
            for key in ['status', 'status_history', 'review_scores', 'review_record', 'reviewed_by', 'review_method']:
                if key in old:
                    asset[key] = old[key]
        if old:
            data['assets'][data['assets'].index(old)] = asset
        else:
            data['assets'].append(asset)
        print(aid, asset['status'])
    manifest.dump(data)
    manifest.dump(manifest.animation_index(data), manifest.MANIFEST.with_name('animation-v2-manifest.yml'))


if __name__ == '__main__':
    build()
