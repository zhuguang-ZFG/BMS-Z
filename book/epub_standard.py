"""Run the official EPUBCheck validator when EPUBCHECK_JAR is configured."""

import json
import os
from pathlib import Path
import subprocess
import tempfile


def check(path: Path) -> dict | None:
    jar = os.environ.get("EPUBCHECK_JAR")
    if not jar:
        return None
    if not Path(jar).is_file():
        raise ValueError(f"EPUBCHECK_JAR does not exist: {jar}")
    with tempfile.TemporaryDirectory(prefix="epubcheck-", dir=path.parent) as work:
        report = Path(work) / "report.json"
        result = subprocess.run(
            ["java", "-jar", jar, str(path), "--json", str(report)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if not report.is_file():
            raise ValueError(
                "EPUBCheck did not produce a report: " + result.stderr[-2000:]
            )
        data = json.loads(report.read_text(encoding="utf-8"))
        counts = {
            key: data["checker"][key]
            for key in ("nFatal", "nError", "nWarning", "nUsage")
        }
        if result.returncode or any(counts.values()):
            raise ValueError(
                f"EPUBCheck failed: {counts}\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
            )
        return {"version": data["checker"]["checkerVersion"], **counts}
