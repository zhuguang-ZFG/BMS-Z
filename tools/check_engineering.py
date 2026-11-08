#!/usr/bin/env python3
"""Validate the engineering deep-dive registries without conflating them with reader acceptance.

P2.1/P2.2 contract: stable IDs anchored to headings (never line numbers), versioned
schema, acyclic prerequisites taken from the minimal-pack mermaid graph, reference
existence in both directions (a removed target fails), source identity against the
adoption table, figures actually appearing in the visible teaching area, and
experiment<->student-task correspondence. Fingerprints detect content drift; refresh
them deliberately with --update after review, never silently.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ENGINEERING = ROOT / 'bms-book/engineering'
MANIFEST = ROOT / 'bms-book/engineering-manifest.json'
CLAIMS = ROOT / 'bms-book/engineering-claims.json'
FIGURES = ROOT / 'bms-book/engineering-figures.json'
EXPERIMENTS = ROOT / 'bms-book/engineering-experiments.json'
ADOPTION = ROOT / 'docs/superpowers/plans/bms-depth/source-adoption.md'
SCHEMA_VERSION = 1
SOURCE_ID = re.compile(r'\b(?:OS\d{2}|DATA01|EDU01|CASE01|SRC\d{2})\b')
HEADING = re.compile(r'^(#{1,6})\s+(.*)$')
FENCED = re.compile(r'^```')
COMMENT = re.compile(r'<!--[\s\S]*?-->')

UNIT_ID = re.compile(r'^[SDBRC]\d+$')
CLAIM_ID = re.compile(r'^[SDBRC]\d+-C\d+$')
FIGURE_ID = re.compile(r'^[SDBRC]\d+(?:-F\d+|-handdrawn-intro)$')
EXPERIMENT_ID = re.compile(r'^E\d+$')
LEVELS = ['intro', 'core', 'derivation', 'lab', 'research']
BOUNDARY = re.compile(r'不能|不代表|不证明|边界|待验|不适用')


def fingerprint_text(text: str) -> str:
    normalized = '\n'.join(line.rstrip() for line in text.strip().splitlines())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]


def fingerprint_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def load_json(path: Path, problems: list[str], label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f'{label}: unreadable ({exc})')
        return {}
    if data.get('schema_version') != SCHEMA_VERSION:
        problems.append(f'{label}: schema_version must be {SCHEMA_VERSION}')
    return data


def headings(text: str) -> list[tuple[int, str, int]]:
    """Return (level, heading_text, line_index) for every heading."""
    found = []
    for index, line in enumerate(text.splitlines()):
        match = HEADING.match(line)
        if match:
            found.append((len(match.group(1)), match.group(2).strip(), index))
    return found


def resolve_anchor(heads: list[tuple[int, str, int]], anchor: str) -> tuple[int, int] | None:
    """Resolve an anchor to (heading_line, end_line_exclusive); 'lead' is before the first level-2 heading."""
    lines_end = heads[-1][2] + 1 if heads else 0
    if anchor == 'lead':
        for level, _text, index in heads:
            if level == 2:
                return (-1, index)
        return (-1, lines_end)
    for position, (level, text, index) in enumerate(heads):
        token = text.split(None, 1)[0] if text.split() else text
        if token == anchor or text == anchor:
            end = lines_end
            for next_level, _next_text, next_index in heads[position + 1:]:
                if next_level <= level:
                    end = next_index
                    break
            return (index, end)
    return None


def section_text(text: str, span: tuple[int, int]) -> str:
    start, end = span
    lines = text.splitlines()
    return '\n'.join(lines[max(start, 0):end])


def visible_teaching_area(text: str) -> str:
    """Markdown with comments and fenced code removed; figure credits there do not count."""
    without_comments = COMMENT.sub('', text)
    kept, in_fence = [], False
    for line in without_comments.splitlines():
        if FENCED.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    return '\n'.join(kept)


def mermaid_edges(text: str) -> set[tuple[str, str]]:
    """Direct prerequisite edges (before --> after) from the minimal-pack mermaid graph."""
    edges: set[tuple[str, str]] = set()
    in_graph = False
    for line in text.splitlines():
        if line.strip().startswith('```mermaid'):
            in_graph = True
            continue
        if in_graph and line.strip().startswith('```'):
            break
        if in_graph:
            match = re.match(r'\s*([A-Za-z0-9]+)(?:\[[^\]]*\])?\s*-->\s*([A-Za-z0-9]+)(?:\[[^\]]*\])?\s*$', line)
            if match:
                edges.add((match.group(1), match.group(2)))
    return edges


def exp_by_id_units(experiments: list[dict]) -> set[str]:
    return {e.get('unit', '') for e in experiments}


def check(root: Path = ROOT, update: bool = False) -> list[str]:
    problems: list[str] = []
    manifest = load_json(MANIFEST if root == ROOT else root / MANIFEST.relative_to(ROOT), problems, 'manifest')
    claims_data = load_json(CLAIMS if root == ROOT else root / CLAIMS.relative_to(ROOT), problems, 'claims')
    figures_data = load_json(FIGURES if root == ROOT else root / FIGURES.relative_to(ROOT), problems, 'figures')
    experiments_data = load_json(EXPERIMENTS if root == ROOT else root / EXPERIMENTS.relative_to(ROOT), problems, 'experiments')

    units = manifest.get('units', [])
    claims = claims_data.get('claims', [])
    figures = figures_data.get('figures', [])
    experiments = experiments_data.get('experiments', [])

    unit_ids = [u.get('id', '') for u in units]
    for uid in unit_ids:
        if not UNIT_ID.match(uid):
            problems.append(f'manifest: malformed unit id {uid}')
    if len(unit_ids) != len(set(unit_ids)):
        problems.append('manifest: duplicate unit ids')
    unit_by_id = {u['id']: u for u in units if 'id' in u}

    adoption_text = ''
    adoption_path = ADOPTION if root == ROOT else root / ADOPTION.relative_to(ROOT)
    if adoption_path.is_file():
        adoption_text = adoption_path.read_text(encoding='utf-8')
    adopted_ids = set(SOURCE_ID.findall(adoption_text))

    # --- manifest: sources, anchors, fingerprints ---
    unit_texts: dict[str, str] = {}
    unit_heads: dict[str, list[tuple[int, str, int]]] = {}
    for unit in units:
        uid = unit.get('id', '?')
        source = unit.get('source')
        if not source:
            problems.append(f'{uid}: missing source')
            continue
        path = root / source
        if not path.is_file():
            problems.append(f'{uid}: source missing {source}')
            continue
        text = path.read_text(encoding='utf-8')
        unit_texts[uid] = text
        unit_heads[uid] = headings(text)
        anchor = unit.get('anchor')
        if anchor and resolve_anchor(unit_heads[uid], anchor) is None:
            problems.append(f'{uid}: anchor {anchor} not found in {source}')
        expected = fingerprint_text(text)
        if unit.get('fingerprint') != expected:
            if update:
                unit['fingerprint'] = expected
            else:
                problems.append(f'{uid}: source drifted, run with --update after review')
        for prereq in unit.get('prerequisites', []):
            if prereq not in unit_by_id:
                problems.append(f'{uid}: unknown prerequisite {prereq}')

    # --- manifest prerequisites must match the minimal-pack mermaid graph ---
    prereq_pack = root / 'bms-book/engineering/P1-先修最小包.md'
    if prereq_pack.is_file():
        declared = mermaid_edges(prereq_pack.read_text(encoding='utf-8'))
        registered = {(p, u['id']) for u in units for p in u.get('prerequisites', [])}
        for before, after in sorted(declared - registered):
            problems.append(f'manifest: mermaid edge {before}-->{after} not registered')
        for before, after in sorted(registered - declared):
            problems.append(f'manifest: prerequisite {before}-->{after} lacks mermaid edge')

    # --- reading levels (P2.3): levels are render-time filters, never content edits ---
    claims_by_unit: dict[str, list[dict]] = {}
    for claim in claims:
        claims_by_unit.setdefault(claim.get('unit', ''), []).append(claim)
    figures_by_unit: dict[str, list[dict]] = {}
    for figure in figures:
        figures_by_unit.setdefault(figure.get('unit', ''), []).append(figure)
    for unit in units:
        uid = unit.get('id', '?')
        levels = unit.get('levels', [])
        if not levels:
            problems.append(f'{uid}: reading levels must be declared')
            continue
        unknown = [level for level in levels if level not in LEVELS]
        for level in unknown:
            problems.append(f'{uid}: unknown level {level}')
        known = [level for level in levels if level in LEVELS]
        if len(known) != len(set(known)) or known != sorted(known, key=LEVELS.index):
            problems.append(f'{uid}: levels must be unique and in ladder order {LEVELS}')
        if 'research' in levels and not (uid.startswith('R') or unit.get('kind') == 'research'):
            problems.append(f'{uid}: research level is reserved for R units')
        if 'intro' in levels and uid in unit_texts:
            span = resolve_anchor(unit_heads[uid], 'lead')
            lead = section_text(unit_texts[uid], span).strip() if span else ''
            if len(lead) < 50 or not BOUNDARY.search(lead):
                problems.append(f'{uid}: intro lead needs >=50 chars and an explicit boundary statement')
        if 'core' in levels and uid in unit_texts:
            if unit.get('kind') in ('sample', 'research'):
                mechanisms = [f for f in figures_by_unit.get(uid, []) if f.get('kind') == 'mechanism']
                if not mechanisms:
                    problems.append(f'{uid}: core level needs at least one mechanism figure')
            elif len(unit_heads[uid]) < 2:
                problems.append(f'{uid}: core level needs at least two headings in the source')
        if 'derivation' in levels and not claims_by_unit.get(uid):
            problems.append(f'{uid}: derivation level needs at least one registered claim')
        if 'lab' in levels and uid not in exp_by_id_units(experiments):
            problems.append(f'{uid}: lab level needs at least one registered experiment')

    # --- acyclicity ---
    visiting, visited = set(), set()

    def visit(uid: str, trail: list[str]) -> None:
        if uid in visited:
            return
        if uid in visiting:
            problems.append(f'manifest: prerequisite cycle {"->".join(trail + [uid])}')
            return
        visiting.add(uid)
        for prereq in unit_by_id.get(uid, {}).get('prerequisites', []):
            if prereq in unit_by_id:
                visit(prereq, trail + [uid])
        visiting.discard(uid)
        visited.add(uid)

    for uid in unit_by_id:
        visit(uid, [])

    # --- claims ---

    claim_ids = [c.get('id', '') for c in claims]
    if len(claim_ids) != len(set(claim_ids)):
        problems.append('claims: duplicate claim ids')
    exp_tests_by_unit: dict[str, list[str]] = {}
    for exp in experiments:
        exp_tests_by_unit.setdefault(exp.get('unit', ''), []).extend(exp.get('tests', []))
    for claim in claims:
        cid = claim.get('id', '?')
        if not CLAIM_ID.match(cid):
            problems.append(f'claims: malformed id {cid}')
        uid = claim.get('unit', '')
        if uid not in unit_texts:
            problems.append(f'{cid}: unknown unit {uid}')
            continue
        span = resolve_anchor(unit_heads[uid], claim.get('anchor', ''))
        if span is None:
            problems.append(f'{cid}: anchor {claim.get("anchor")} not found in {uid}')
        else:
            expected = fingerprint_text(section_text(unit_texts[uid], span))
            if claim.get('fingerprint') != expected:
                if update:
                    claim['fingerprint'] = expected
                else:
                    problems.append(f'{cid}: anchored section drifted, run with --update after review')
        for source_id in claim.get('source_ids', []):
            if adopted_ids and source_id not in adopted_ids:
                problems.append(f'{cid}: unknown source_id {source_id}')
        for test_name in claim.get('evidence', []):
            found = False
            for test_file in exp_tests_by_unit.get(uid, []):
                path = root / test_file
                if path.is_file() and re.search(rf'def {re.escape(test_name)}\b', path.read_text(encoding='utf-8')):
                    found = True
                    break
            if not found:
                problems.append(f'{cid}: evidence test {test_name} not found in {uid} tests')

    # --- figures ---
    figure_ids = [f.get('id', '') for f in figures]
    if len(figure_ids) != len(set(figure_ids)):
        problems.append('figures: duplicate figure ids')
    figure_by_id = {f['id']: f for f in figures if 'id' in f}
    for figure in figures:
        fid = figure.get('id', '?')
        if not FIGURE_ID.match(fid):
            problems.append(f'figures: malformed id {fid}')
        uid = figure.get('unit', '')
        if uid not in unit_texts:
            problems.append(f'{fid}: unknown unit {uid}')
            continue
        path = root / figure.get('file', '')
        if not path.is_file():
            problems.append(f'{fid}: file missing {figure.get("file")}')
        else:
            expected = fingerprint_file(path)
            if figure.get('fingerprint') != expected:
                if update:
                    figure['fingerprint'] = expected
                else:
                    problems.append(f'{fid}: file drifted, run with --update after review')
            if path.suffix == '.svg':
                svg = path.read_text(encoding='utf-8')
                if not re.search(r'<title>[^<]+</title>', svg) or not re.search(r'<desc>[^<]+</desc>', svg):
                    problems.append(f'{fid}: svg needs non-empty <title> and <desc>')
        span = resolve_anchor(unit_heads[uid], figure.get('appears_in', ''))
        if span is None:
            problems.append(f'{fid}: appears_in anchor {figure.get("appears_in")} not found in {uid}')
        visible = visible_teaching_area(unit_texts[uid])
        filename = Path(figure.get('file', '')).name
        if filename and filename not in visible:
            problems.append(f'{fid}: {filename} not referenced in visible teaching area of {uid}')
        if figure.get('kind') != 'concept' and not figure.get('generator'):
            problems.append(f'{fid}: data/mechanism figure needs a generator')

    # every image file in a unit asset directory must be registered (removal fails loudly);
    # archived trial dirs are frozen by explicit listing, not by silence
    registered_files = {f.get('file', '') for f in figures}
    archived = {a['dir']: a for a in figures_data.get('archived', []) if 'dir' in a}
    assets_root = ENGINEERING if root == ROOT else root / ENGINEERING.relative_to(ROOT)
    if assets_root.is_dir():
        for asset in sorted(assets_root.glob('assets/*/*')):
            rel = asset.relative_to(root).as_posix()
            parent = asset.parent.relative_to(root).as_posix()
            if parent in archived:
                if rel not in archived[parent].get('files', []):
                    problems.append(f'figures: {rel} not listed in archived dir {parent}')
                continue
            if asset.is_file() and rel not in registered_files:
                problems.append(f'figures: unregistered asset {rel}')
        for directory, entry in archived.items():
            actual = sorted(p.relative_to(root).as_posix() for p in (root / directory).glob('*') if p.is_file())
            if sorted(entry.get('files', [])) != actual:
                problems.append(f'figures: archived dir {directory} listing stale, run with --update or fix')

    # --- experiments ---
    exp_ids = [e.get('id', '') for e in experiments]
    if len(exp_ids) != len(set(exp_ids)):
        problems.append('experiments: duplicate experiment ids')
    exp_by_id = {e['id']: e for e in experiments if 'id' in e}
    for exp in experiments:
        eid = exp.get('id', '?')
        if not EXPERIMENT_ID.match(eid):
            problems.append(f'experiments: malformed id {eid}')
        uid = exp.get('unit', '')
        if uid not in unit_texts:
            problems.append(f'{eid}: unknown unit {uid}')
            continue
        for key in ('script', 'figure_generator'):
            rel = exp.get(key)
            if rel and not (root / rel).is_file():
                problems.append(f'{eid}: {key} missing {rel}')
        for rel in exp.get('tests', []):
            if not (root / rel).is_file():
                problems.append(f'{eid}: tests missing {rel}')
        text_for_scenarios = unit_texts[uid]
        script = root / exp.get('script', '')
        if script.is_file():
            text_for_scenarios += '\n' + script.read_text(encoding='utf-8')
        for scenario in exp.get('scenarios', []):
            if scenario not in text_for_scenarios:
                problems.append(f'{eid}: scenario {scenario} not found in {uid} text or script')
        for anchor_key in ('student_tasks_anchor', 'rejects_anchor', 'frozen_anchor'):
            span = resolve_anchor(unit_heads[uid], exp.get(anchor_key, ''))
            if span is None:
                problems.append(f'{eid}: {anchor_key} {exp.get(anchor_key)} not found in {uid}')
        for source_id in exp.get('source_ids', []):
            if adopted_ids and source_id not in adopted_ids:
                problems.append(f'{eid}: unknown source_id {source_id}')
        if not exp.get('acceptance'):
            problems.append(f'{eid}: acceptance must name inputs, comparators and criteria')

    # --- cross-registry consistency ---
    for unit in units:
        uid = unit.get('id', '?')
        for fid in unit.get('figures', []):
            if fid not in figure_by_id:
                problems.append(f'manifest: {uid} lists unknown figure {fid}')
            elif figure_by_id[fid].get('unit') != uid:
                problems.append(f'manifest: figure {fid} registered under {figure_by_id[fid].get("unit")}, not {uid}')
        for eid in unit.get('experiments', []):
            if eid not in exp_by_id:
                problems.append(f'manifest: {uid} lists unknown experiment {eid}')
            elif exp_by_id[eid].get('unit') != uid:
                problems.append(f'manifest: experiment {eid} registered under {exp_by_id[eid].get("unit")}, not {uid}')
    for figure in figures:
        if figure.get('id') not in set(unit_by_id.get(figure.get('unit', ''), {}).get('figures', [])):
            problems.append(f'figures: {figure.get("id")} not listed in its unit manifest')
    for exp in experiments:
        if exp.get('id') not in set(unit_by_id.get(exp.get('unit', ''), {}).get('experiments', [])):
            problems.append(f'experiments: {exp.get("id")} not listed in its unit manifest')

    if update and not problems:
        for path, data in ((MANIFEST, manifest), (CLAIMS, claims_data), (FIGURES, figures_data)):
            target = path if root == ROOT else root / path.relative_to(ROOT)
            target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update', action='store_true', help='refresh fingerprints after deliberate review')
    args = parser.parse_args()
    problems = check(update=args.update)
    if problems:
        print('engineering registry check failed:')
        for problem in problems:
            print(f'- {problem}')
        return 1
    print('engineering registry check passed: manifest/claims/figures/experiments consistent')
    return 0


if __name__ == '__main__':
    sys.exit(main())
