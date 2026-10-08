"""从 NASA RW3 原始归档确定性导出实测子集；仅此转换步骤需要 scipy。

python code/soc/prepare_nasa.py --archive path/to/archive.zip --out path/to/data
归档下载地址和校验值见 data/nasa_rw3/metadata.json。本脚本不下载、不解压到磁盘。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

ARCHIVE_MD5 = "aa53dce833e0ce7ee75376846dec4e59"
RECORD = "https://zenodo.org/records/15277374"
DOWNLOAD = (RECORD + "/files/2.%20Battery_Uniform_Distribution_Discharge_Room_Temp_DataSet_2Post.zip")
MEMBER = "Battery_Uniform_Distribution_Discharge_Room_Temp_DataSet_2Post/data/Matlab/RW3.mat"
SELECTION = {"ocv": [0], "capacity": [2], "pulse": [5, 6, 7],
             "validation": list(range(32, 50))}
FIELDS = ["series", "source_step", "source_sample", "time_s", "step_time_s",
          "current_a", "voltage_v", "temperature_c"]


def convert(archive: Path, output: Path) -> dict:
    try:
        from scipy.io import loadmat
    except ImportError as exc:
        raise RuntimeError("转换 MATLAB 原始文件需要 scipy：pip install scipy；运行已附 CSV 不需要") from exc
    raw = archive.read_bytes()
    if hashlib.md5(raw).hexdigest() != ARCHIVE_MD5:
        raise ValueError("归档 MD5 与 NASA 数据记录不符，请使用文档指定的原始 ZIP")
    with zipfile.ZipFile(io.BytesIO(raw)) as package:
        mat = package.read(MEMBER)
    data = loadmat(io.BytesIO(mat), simplify_cells=True)["data"]
    lines = io.StringIO(newline="")
    writer = csv.DictWriter(lines, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    counts, steps = {}, {}
    for series, indices in SELECTION.items():
        origin = float(data["step"][indices[0]]["time"][0])
        count = 0
        for index in indices:
            step = data["step"][index]
            steps[str(index)] = dict(type=step["type"], comment=step["comment"],
                                     date=step["date"], samples=len(step["time"]))
            for sample, (time, relative, current, voltage, temp) in enumerate(zip(
                step["time"], step["relativeTime"], step["current"],
                step["voltage"], step["temperature"], strict=True,
            )):
                values = [time - origin, relative, -current, voltage, temp]
                writer.writerow(dict(zip(FIELDS, [series, index, sample,
                                                 *(format(float(v), ".12g") for v in values)], strict=True)))
                count += 1
        counts[series] = count
    payload = lines.getvalue().encode("utf-8")
    metadata = dict(
        title="NASA PCoE Randomized Battery Usage — RW3 measured subset",
        creators=["B. Bole", "C. Kulkarni", "M. Daigle"],
        citation="Bole, Kulkarni and Daigle (2014), Randomized Battery Usage Data Set, NASA Ames Research Center",
        source_record=RECORD, download_url=DOWNLOAD, license="CC-BY-4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        archive_md5=ARCHIVE_MD5, archive_sha256=hashlib.sha256(raw).hexdigest(),
        source_member=MEMBER, source_member_sha256=hashlib.sha256(mat).hexdigest(),
        csv_sha256=hashlib.sha256(payload).hexdigest(), selection=SELECTION,
        rows=counts, source_steps=steps,
        transformations=["Selected complete source steps; source_step and source_sample are zero-based",
                         "Negated source current: this repository uses positive charging current",
                         "Subtracted first absolute timestamp within each series; retained inter-step gaps",
                         "Kept all samples without resampling; decimal formatting to 12 significant digits"],
        soc_reference="Not measured SOC. Constructed offline from measured current and calibration capacity.",
        validation_preceding_charge=dict(source_step=31, end_voltage_v=float(data["step"][31]["voltage"][-1])),
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "samples.csv").write_bytes(payload)
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        metadata = convert(args.archive, args.out)
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"Conversion failed: {exc}\n")
    print(json.dumps(metadata["rows"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
