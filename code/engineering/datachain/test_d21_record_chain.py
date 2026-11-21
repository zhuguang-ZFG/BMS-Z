"""D21 record chain: source identity, unit transform, time alignment, and replay lineage."""

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d21_record_chain", HERE / "d21_record_chain.py")
assert spec is not None and spec.loader is not None
d21 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d21
spec.loader.exec_module(d21)


def _write_records(path: Path, rows: list[dict[str, object]]) -> Path:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=d21.RECORD_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_default_chain_normalizes_units_and_aligns_sources():
    report = d21.build_report(d21.default_records())

    assert report["scenario_id"] == d21.SCENARIO_ID
    assert report["counts"]["raw_records"] == 11
    assert report["counts"]["quarantined_records"] == 1

    transformed = {
        (row["source_id"], row["record_seq"], row["field"]): row
        for row in report["normalized_records"]
    }
    assert transformed[("afe", 1, "pack_v")]["value"] == pytest.approx(51.2)
    assert transformed[("afe", 1, "pack_v")]["canonical_unit"] == "V"
    assert transformed[("afe", 3, "pack_current_a")]["value"] == pytest.approx(12.0)
    assert transformed[("estimator", 1, "soc")]["value"] == pytest.approx(0.60)
    assert transformed[("firmware", 1, "epoch")]["value"] == 41

    aligned = report["aligned_series"]
    pack_v_40 = next(
        row
        for row in aligned
        if row["field"] == "pack_v" and row["t_ms"] == 40.0
    )
    assert pack_v_40["value"] == pytest.approx(51.3)
    assert pack_v_40["source_t_ms"] == 20.0
    assert pack_v_40["age_ms"] == pytest.approx(20.0)
    assert pack_v_40["deliverable"] is True

    stale_pack_v = next(
        row
        for row in aligned
        if row["field"] == "pack_v" and row["t_ms"] == 200.0
    )
    assert stale_pack_v["age_ms"] == pytest.approx(180.0)
    assert stale_pack_v["deliverable"] is False
    assert report["counts"]["stale_rows"] > 0


def test_invalid_quality_is_quarantined_and_never_aligned():
    report = d21.build_report(d21.default_records())
    quarantine = report["quarantine"]
    assert len(quarantine) == 1
    assert quarantine[0]["source_id"] == "estimator"
    assert quarantine[0]["quality"] == "invalid"
    assert all(
        not (row["source_id"] == "estimator" and row["source_seq"] == 3)
        for row in report["aligned_series"]
    )


def test_rejects_time_rollback_duplicate_sequence_bad_unit_and_unknown_field(tmp_path):
    good = d21.default_records()
    bad_time = [dict(row) for row in good]
    bad_time[2]["t_ms"] = 10.0
    with pytest.raises(ValueError, match="time rollback"):
        d21.build_report(bad_time)

    bad_seq = [dict(row) for row in good]
    bad_seq[4]["record_seq"] = bad_seq[3]["record_seq"]
    with pytest.raises(ValueError, match="record_seq"):
        d21.build_report(bad_seq)

    bad_unit = [dict(row) for row in good]
    bad_unit[0]["unit"] = "dA"
    with pytest.raises(ValueError, match="unit"):
        d21.build_report(bad_unit)

    bad_field = [dict(row) for row in good]
    bad_field[0]["field"] = "mystery"
    with pytest.raises(ValueError, match="field"):
        d21.build_report(bad_field)


def test_out_of_range_after_unit_conversion_is_rejected():
    records = d21.default_records()
    records[0]["raw_value"] = 51200.0  # 写成 V 会是 51.2 kV，不是“电压有点高”
    records[0]["unit"] = "V"
    with pytest.raises(ValueError, match="range"):
        d21.build_report(records)


def test_lineage_metadata_rejects_replay_with_different_source(tmp_path):
    source = _write_records(tmp_path / "records.csv", d21.default_records())
    first = tmp_path / "first"
    assert d21.main(["--records", str(source), "--out", str(first)]) == 0

    metadata = json.loads((first / "lineage.json").read_text(encoding="utf-8"))
    assert metadata["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert metadata["config_sha256"] == d21.config_fingerprint()

    source.write_text(source.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    second = tmp_path / "second"
    assert d21.main(["--records", str(source), "--out", str(second), "--metadata", str(first / "lineage.json")]) == 2


def test_cli_default_export_and_roundtrip(tmp_path):
    out = tmp_path / "out"
    assert d21.main(["--out", str(out)]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["scenario_id"] == d21.SCENARIO_ID
    assert (out / "records.csv").is_file()
    assert (out / "normalized_records.csv").is_file()
    assert (out / "aligned_series.csv").is_file()
    assert (out / "lineage.json").is_file()

    replay = tmp_path / "replay"
    assert d21.main([
        "--records",
        str(out / "records.csv"),
        "--out",
        str(replay),
        "--metadata",
        str(out / "lineage.json"),
    ]) == 0
    replay_report = json.loads((replay / "report.json").read_text(encoding="utf-8"))
    assert replay_report["counts"] == report["counts"]


def test_default_metadata_replay_without_records(tmp_path):
    out = tmp_path / "out"
    assert d21.main(["--out", str(out)]) == 0

    replay = tmp_path / "replay"
    assert d21.main([
        "--out",
        str(replay),
        "--metadata",
        str(out / "lineage.json"),
    ]) == 0
    original_report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    replay_report = json.loads((replay / "report.json").read_text(encoding="utf-8"))
    assert replay_report["counts"] == original_report["counts"]
    assert (replay / "records.csv").read_bytes() == (out / "records.csv").read_bytes()
