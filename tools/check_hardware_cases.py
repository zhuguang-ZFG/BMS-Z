#!/usr/bin/env python3
"""Validate pinned open-hardware teardown cases and vehicle tracks."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "curriculum" / "hardware_cases.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    tracks = data.get("tracks", [])
    cases = data.get("cases", [])
    track_ids = {track.get("id") for track in tracks}
    case_ids = {case.get("id") for case in cases}
    if len(track_ids) != len(tracks):
        errors.append("车辆路线 id 重复或缺失")
    if len(case_ids) != len(cases):
        errors.append("硬件案例 id 重复或缺失")
    for track in tracks:
        for key in ("id", "name", "identity", "architecture", "focus", "case_ids"):
            if not track.get(key):
                errors.append(f"track {track.get('id')}: 缺 {key}")
        for case_id in track.get("case_ids", []):
            if case_id not in case_ids:
                errors.append(f"track {track.get('id')}: 未知案例 {case_id}")
    for case in cases:
        case_id = case.get("id", "(missing)")
        for key in ("repo", "sha", "license", "development_status", "primary_track", "role", "source_files", "teaches", "warning"):
            if not case.get(key):
                errors.append(f"case {case_id}: 缺 {key}")
        if not REPO_RE.fullmatch(str(case.get("repo", ""))):
            errors.append(f"case {case_id}: repo 不是 owner/name")
        if not SHA_RE.fullmatch(str(case.get("sha", ""))):
            errors.append(f"case {case_id}: sha 必须是 40 位小写提交哈希")
        if case.get("primary_track") not in track_ids:
            errors.append(f"case {case_id}: 未知 primary_track {case.get('primary_track')}")
    return errors


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        print(f"FAIL ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS：{len(data['tracks'])} 条应用路线 / {len(data['cases'])} 个固定版本硬件案例")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
