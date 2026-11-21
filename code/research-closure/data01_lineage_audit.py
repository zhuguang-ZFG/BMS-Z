#!/usr/bin/env python3
"""DATA01 NASA RW3 local lineage audit (stdlib only, no venv needed).

Verifies the claims the README/metadata make about the local copy:
- metadata.json required fields (citation, license, source_record, hashes);
- samples.csv header/rows parse, units numeric, current sign convention
  (充正放负) actually holds, source_sample continuity per series;
- recomputed CSV sha256 recorded as *local* lineage (the archive hash in
  metadata is of the upstream ZIP — not re-verifiable without re-download,
  recorded as 未重核 rather than assumed).

Writes evidence JSON; anything not checked is recorded unchecked, not assumed.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "soc" / "data" / "nasa_rw3"
OUT = Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

REQUIRED_META = ("title", "creators", "citation", "source_record", "license",
                 "archive_md5", "archive_sha256")
EXPECTED_HEADER = ["series", "source_step", "source_sample", "time_s",
                   "step_time_s", "current_a", "voltage_v", "temperature_c"]


def audit() -> dict:
    meta = json.loads((DATA / "metadata.json").read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_META if k not in meta]

    with (DATA / "samples.csv").open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header_ok = reader.fieldnames == EXPECTED_HEADER
        rows = list(reader)

    parse_failures = 0
    sign_violations = 0
    series_samples: dict[str, list[int]] = {}
    for r in rows:
        try:
            cur = float(r["current_a"])
            float(r["voltage_v"])
            float(r["temperature_c"])
            int(r["source_sample"])
        except (ValueError, KeyError):
            parse_failures += 1
            continue
        if r["series"] == "discharge" and cur > 0:
            sign_violations += 1
        if r["series"] == "charge" and cur < 0:
            sign_violations += 1
        series_samples.setdefault((r["series"], r["source_step"]), []).append(int(r["source_sample"]))

    continuity = {f"{s}#{st}": (samples == list(range(len(samples))))
                  for (s, st), samples in sorted(series_samples.items())}

    csv_sha = hashlib.sha256((DATA / "samples.csv").read_bytes()).hexdigest()
    return {
        "source_id": "DATA01",
        "metadata_required_fields_missing": missing,
        "license": meta.get("license"),
        "csv": {
            "header_ok": header_ok,
            "n_rows": len(rows),
            "parse_failures": parse_failures,
            "sign_convention_violations": sign_violations,
            "series_source_sample_continuous": continuity,
            "csv_sha256_local_recompute": csv_sha,
        },
        "archive_hash": {
            "recorded_sha256": meta.get("archive_sha256"),
            "verified_this_run": False,
            "note": "ZIP 归档摘要从 metadata 转录；本次未重新下载原始 ZIP，记未重核",
        },
        "naming_note": "未命名任何独立真值；reference_soc 假设见 docs/SOC真实数据专题.md",
    }


def main() -> int:
    report = audit()
    out = OUT / "data01-lineage.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": report["csv"]["n_rows"],
        "header_ok": report["csv"]["header_ok"],
        "parse_failures": report["csv"]["parse_failures"],
        "sign_violations": report["csv"]["sign_convention_violations"],
        "all_series_continuous": all(report["csv"]["series_source_sample_continuous"].values()),
        "metadata_missing": report["metadata_required_fields_missing"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
