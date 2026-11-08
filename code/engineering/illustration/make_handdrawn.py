"""Generate source-bound hand-drawn assets, or verify their recorded identities.

Set BMS_IMAGE_API_KEY outside the repository. Run --only <key> for one image,
--all for the 37-image cutover, or --check for a network-free integrity check.
Existing matching records are reused; --replace explicitly requests regeneration.
The model is nondeterministic: hashes establish provenance, not repeatable pixels.
WebP delivery images are padded, never cropped or stretched.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tempfile
import threading
from contextlib import contextmanager
import struct
import sys
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

import handdraw_api
from handdrawn_assets import ASSETS, REFERENCE, ROOT

OUT = ROOT / "bms-book/illustrations/handdraw"
MANIFEST = OUT / "manifest.json"
MODEL = handdraw_api.DEFAULT_MODEL
SCHEMA = "bms-original-handdraw-v1"
PAUSE = OUT / "PAUSE"
_manifest_mutex = threading.Lock()


class BatchPaused(RuntimeError):
    pass


@contextmanager
def publisher_lock():
    """Exactly one generation command may spend and publish at a time."""
    OUT.mkdir(parents=True, exist_ok=True)
    lock = OUT / ".publisher.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        lock.unlink()


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def png_size(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG with IHDR")
    return struct.unpack(">II", data[16:24])


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".part", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_manifest() -> dict:
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("schema") != SCHEMA:
            raise ValueError("handdraw manifest schema differs; review before replacing it")
        return manifest
    return {
        "schema": SCHEMA,
        "style": {"name": "BMS original engineering handdraw", "canonical_id": None},
        "reference": {"path": _relative(REFERENCE), "sha256": sha256(REFERENCE.read_bytes())},
        "assets": {},
    }


def merge_record(key: str, record: dict) -> None:
    """Caller owns publisher_lock; merge the latest atomic manifest, not a snapshot."""
    with _manifest_mutex:
        latest = load_manifest()
        latest["assets"][key] = record
        _atomic(MANIFEST, (json.dumps(latest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def _problems(key: str, record: dict, reference_hash: str) -> list[str]:
    from PIL import Image

    asset = ASSETS[key]
    problems = []
    expected = {
        "prompt_sha256": sha256(asset.prompt.encode("utf-8")),
        "reference_sha256": reference_hash,
        "model": MODEL,
        "file": asset.target,
        "width": asset.canvas[0],
        "height": asset.canvas[1],
    }
    for field, value in expected.items():
        if record.get(field) != value:
            problems.append(f"{key}: {field} differs")
    for field, digest in (("source_png", "source_sha256"), ("file", "image_sha256"), ("prompt_file", "prompt_sha256")):
        path = ROOT / record.get(field, "")
        if not path.is_file() or sha256(path.read_bytes()) != record.get(digest):
            problems.append(f"{key}: {field} missing or SHA-256 differs")
    if record.get("visual_acceptance", "").startswith("rejected"):
        problems.append(f"{key}: visual review rejected this candidate")
    target = ROOT / record.get("file", asset.target)
    if target.is_file():
        with Image.open(target) as image:
            image.load()
            if image.format != "WEBP" or image.size != asset.canvas:
                problems.append(f"{key}: delivery format or canvas differs")
    return problems


def check(manifest: dict) -> list[str]:
    records = manifest.get("assets", {})
    problems = [f"missing record: {key}" for key in sorted(ASSETS.keys() - records.keys())]
    problems += [f"unexpected record: {key}" for key in sorted(records.keys() - ASSETS.keys())]
    reference_hash = sha256(REFERENCE.read_bytes())
    if manifest.get("reference", {}).get("sha256") != reference_hash:
        problems.append("style reference SHA-256 differs")
    for key in sorted(ASSETS.keys() & records.keys()):
        problems.extend(_problems(key, records[key], reference_hash))
    return problems


def _generate(key: str) -> dict:
    if PAUSE.exists():
        raise BatchPaused("queue paused before sending a paid request")
    asset = ASSETS[key]
    result = handdraw_api.edit(asset.prompt, REFERENCE, model=MODEL, size=asset.size)
    return publish(key, result)


def publish(key: str, result: handdraw_api.ImageResult) -> dict:
    from PIL import Image, ImageOps

    asset = ASSETS[key]
    prompt_bytes = asset.prompt.encode("utf-8")
    reference_bytes = REFERENCE.read_bytes()
    source_size = png_size(result.png)
    with Image.open(io.BytesIO(result.png)) as source:
        source.load()
        if source.format != "PNG":
            raise ValueError(f"{key}: response is not a decoded PNG")
        source = source.convert("RGBA")
        fitted = ImageOps.contain(source, asset.canvas, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", asset.canvas, "#fffdf5")
        position = ((canvas.width - fitted.width) // 2, (canvas.height - fitted.height) // 2)
        canvas.paste(fitted, position, fitted)
        encoded = io.BytesIO()
        canvas.save(encoded, format="WEBP", quality=92, method=6)
        webp = encoded.getvalue()
    source_path = OUT / f"{key}.png"
    prompt_path = OUT / f"{key}.prompt.txt"
    target = ROOT / asset.target
    _atomic(source_path, result.png)
    _atomic(prompt_path, prompt_bytes)
    _atomic(target, webp)
    record = {
        "file": asset.target,
        "source_png": _relative(source_path),
        "prompt_file": _relative(prompt_path),
        "model": MODEL,
        "endpoint": "images/edits",
        "transport": "HTTPS certificate verified; redirects refused; base64 response only",
        "prompt_sha256": sha256(prompt_bytes),
        "reference_sha256": sha256(reference_bytes),
        "source_sha256": sha256(result.png),
        "image_sha256": sha256(webp),
        "source_width": source_size[0],
        "source_height": source_size[1],
        "width": asset.canvas[0],
        "height": asset.canvas[1],
        "bytes": len(webp),
        "conversion": "Pillow contain, centered warm-paper padding, no crop or stretch; WebP quality92",
        "revised_prompt": result.revised_prompt,
        "visual_acceptance": "pending independent visual review",
    }
    _atomic(OUT / f"{key}.record.json", (json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return record


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--only", choices=sorted(ASSETS))
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--jobs", type=int, choices=range(1, 5), default=4)
    args = parser.parse_args()
    if not REFERENCE.is_file():
        parser.error(f"project-owned style reference missing: {REFERENCE}")
    manifest = load_manifest()
    if args.check:
        problems = check(manifest)
        for problem in problems:
            print(problem)
        if not problems:
            print(f"PASS: {len(ASSETS)} hand-drawn assets; prompt/reference/PNG/WebP hashes and canvases")
        return int(bool(problems))
    reference_hash = sha256(REFERENCE.read_bytes())
    keys = sorted(ASSETS) if args.all else [args.only]
    pending = []
    failures = []
    for key in keys:
        record = manifest["assets"].get(key)
        if record and not args.replace:
            differences = _problems(key, record, reference_hash)
            if differences:
                print(f"REVIEW {key}: " + "; ".join(differences) + "; explicit --replace required", flush=True)
                failures.append(key)
            else:
                print(f"reuse {key}", flush=True)
        else:
            pending.append(key)
    waiting = iter(pending)
    paused = PAUSE.exists()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        active = {}

        def fill_queue() -> None:
            while len(active) < args.jobs and not PAUSE.exists():
                key = next(waiting, None)
                if key is None:
                    return
                active[pool.submit(_generate, key)] = key

        fill_queue()
        while active:
            finished, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in finished:
                key = active.pop(future)
                try:
                    record = future.result()
                except BatchPaused:
                    paused = True
                    continue
                except (handdraw_api.ImageApiError, OSError, ValueError) as error:
                    detail = f"; {error.body}" if isinstance(error, handdraw_api.ImageApiError) else ""
                    print(f"FAILED {key}: {error}{detail}", flush=True)
                    failures.append(key)
                    if isinstance(error, handdraw_api.ImageApiError) and error.status in {401, 403}:
                        _atomic(PAUSE, b"Authorization or quota refused; authorized resolution required before resuming.\n")
                    continue
                merge_record(key, record)
                print(f"generated {key}: {record['file']} ({record['bytes']} bytes)", flush=True)
            paused = paused or PAUSE.exists()
            fill_queue()
    if failures:
        print("Unfinished images (not retried automatically): " + ", ".join(sorted(failures)))
    if paused:
        print("PAUSED: in-flight results retained; queued images were not submitted")
    return 2 if paused else int(bool(failures))


def main() -> int:
    if "--check" in sys.argv:
        return _main()
    try:
        with publisher_lock():
            return _main()
    except FileExistsError:
        print("Another publisher owns .publisher.lock; no images submitted")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
