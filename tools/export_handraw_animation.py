#!/usr/bin/env python3
"""Export handraw storyboard frames into pausable WebP animations.

Reads docs/circuits/handraw/manifest.json, exports every entry whose status is
rendered/exported/linked and whose frames exist, and writes:

    exports/<slug>.webp
    exports/<slug>-start.webp
    exports/<slug>-end.webp

Entries still at prompts_only are skipped and counted, never treated as failures.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "circuits" / "handraw" / "manifest.json"
EXPORT_DIR = Path("docs") / "circuits" / "handraw" / "exports"
RENDERED = {"rendered", "exported", "linked"}
DEFAULT_DURATION_MS = 1200


def _load_frames(root: Path, entry: dict) -> list[Path]:
    # 帧序以文件名为准：manifest 里的顺序可能被手工重排，不能当真源。
    frames = sorted((root / rel for rel in entry.get("frames") or []), key=lambda p: p.name)
    if not 3 <= len(frames) <= 8:
        raise ValueError(f"need 3-8 frames, got {len(frames)}")
    missing = [str(p) for p in frames if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"missing frames: {missing}")
    return frames


def export_slug(root: Path, entry: dict, duration_ms: int = DEFAULT_DURATION_MS) -> Path:
    """Build exports/<slug>.webp plus -start/-end stills; return animation path."""
    slug = entry["slug"]
    frames = _load_frames(root, entry)
    images = [Image.open(p).convert("RGB") for p in frames]
    out_dir = root / EXPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    anim = out_dir / f"{slug}.webp"
    images[0].save(
        anim,
        format="WEBP",
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        quality=97,
        method=4,
    )
    images[0].save(out_dir / f"{slug}-start.webp", format="WEBP", quality=97)
    images[-1].save(out_dir / f"{slug}-end.webp", format="WEBP", quality=97)
    return anim


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_MS)
    args = parser.parse_args(argv)

    manifest = Path(args.manifest)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    root = manifest.resolve().parents[3]
    exported = skipped = failed = 0
    for entry in data.get("entries", []):
        status = entry.get("status")
        if status not in RENDERED:
            skipped += 1
            continue
        try:
            path = export_slug(root, entry, args.duration)
        except Exception as exc:  # noqa: BLE001 - report each slug, never skip silently
            failed += 1
            print(f"FAIL {entry.get('slug')}: {exc}")
            continue
        exported += 1
        print(f"ok   {entry.get('slug')} -> {path.relative_to(root).as_posix()}")
    print(f"exported={exported} skipped={skipped} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
