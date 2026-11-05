#!/usr/bin/env python3
"""Validate docs/circuits/handraw/manifest.json against path-B contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "docs" / "circuits" / "handraw" / "manifest.json"
REQUIRED = {
    "slug", "source_svg", "kp_id", "style", "colors",
    "frames", "export", "caption_ok", "bans_ok", "status",
}
ALLOWED_STYLE = {"FA-002", "FA-029"}
ALLOWED_STATUS = {"prompts_only", "rendered", "exported", "linked", "archived"}


def validate_manifest(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing manifest: {path}"]
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, list):
        return ["entries must be a list"]
    if len(entries) != 20:
        errors.append(f"expected 20 entries, got {len(entries)}")
    seen: set[str] = set()
    for i, entry in enumerate(entries):
        prefix = f"entries[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: not an object")
            continue
        missing = REQUIRED - set(entry)
        if missing:
            errors.append(f"{prefix}: missing {sorted(missing)}")
        slug = entry.get("slug")
        if slug in seen:
            errors.append(f"duplicate slug: {slug}")
        seen.add(slug)
        if entry.get("style") not in ALLOWED_STYLE:
            errors.append(f"{slug}: bad style {entry.get('style')}")
        colors = entry.get("colors") or {}
        if colors.get("primary") != "C-03" or colors.get("danger") != "C-15":
            errors.append(f"{slug}: colors must be C-03/C-15")
        if entry.get("status") not in ALLOWED_STATUS:
            errors.append(f"{slug}: bad status {entry.get('status')}")
        src = entry.get("source_svg")
        if src and not (ROOT / src).is_file():
            # 允许 archived 后源文件已搬家：若 status==archived 则检查 archive 旁路
            if entry.get("status") != "archived":
                errors.append(f"{slug}: source_svg missing: {src}")
        if not isinstance(entry.get("frames"), list):
            errors.append(f"{slug}: frames must be list")
        if entry.get("status") in {"rendered", "exported", "linked"}:
            frames = entry.get("frames") or []
            if not (3 <= len(frames) <= 8):
                errors.append(f"{slug}: need 3-8 frames when status>={entry['status']}")
            for rel in frames:
                if not (ROOT / rel).is_file():
                    errors.append(f"{slug}: missing frame {rel}")
        if entry.get("status") in {"exported", "linked"}:
            export = entry.get("export")
            if not export or not (ROOT / export).is_file():
                errors.append(f"{slug}: missing export {export}")
        if entry.get("status") in {"linked", "archived"}:
            if not entry.get("caption_ok") or not entry.get("bans_ok"):
                errors.append(f"{slug}: caption_ok/bans_ok must be true before link/archive")
    return errors


def main(argv: list[str] | None = None) -> int:
    path = Path(argv[1]) if argv and len(argv) > 1 else DEFAULT
    errors = validate_manifest(path)
    if errors:
        print("HANDRAW MANIFEST FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("HANDRAW MANIFEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
