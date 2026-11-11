#!/usr/bin/env python3
"""发现并运行 assets/spice 下的 ngspice deck，按 assert.json 校验测量值。"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPICE_DIR = ROOT / "assets" / "spice"
DEFAULT_REPORT = ROOT / "build" / "spice" / "report.json"
# ngspice 的 AVG/MAX/MIN 会在数值后追一句 “from= … to= …”／“at= …”，
# 行尾锚定会让整行匹配失败（i_load 那类 FIND 却匹配得上，错误只露一半）。
MEASURE_RE = re.compile(
    r"^\s*([A-Za-z_]\w*)\s*=\s*"
    r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)", re.M)
ANALYSES = {"tran", "ac", "op", "dc"}
REQUIRED = {"deck", "analysis", "data", "min_rows", "metrics"}


@dataclass(frozen=True)
class Case:
    directory: Path
    deck: Path
    spec: dict


def find_ngspice() -> Path | None:
    candidates = []
    override = os.environ.get("NGSPICE")
    if override:
        candidates.append(Path(override))
    for command in ("ngspice", "ngspice.exe"):
        found = shutil.which(command)
        if found:
            candidates.append(Path(found))
    for candidate in candidates:
        if candidate.expanduser().is_file():
            return candidate.expanduser().resolve()
    return None


def validate_spec(spec: dict, deck: Path) -> None:
    if set(spec) != REQUIRED:
        raise ValueError(f"{deck}: assert.json 字段应为 {sorted(REQUIRED)}")
    if spec["deck"] != deck.name:
        raise ValueError(f"{deck}: assert.deck 必须是 {deck.name}")
    if spec["analysis"] not in ANALYSES:
        raise ValueError(f"{deck}: 未知 analysis {spec['analysis']}")
    if not isinstance(spec["min_rows"], int) or spec["min_rows"] < 1:
        raise ValueError(f"{deck}: min_rows 必须为正整数")
    if not isinstance(spec["metrics"], dict) or not spec["metrics"]:
        raise ValueError(f"{deck}: metrics 不能为空")
    for name, metric in spec["metrics"].items():
        if set(metric) != {"expected", "tolerance"}:
            raise ValueError(f"{deck}: metric {name} 字段不合法")
        if not isinstance(metric["expected"], (int, float)):
            raise ValueError(f"{deck}: metric {name} expected 不是数字")
        if not isinstance(metric["tolerance"], (int, float)) \
                or metric["tolerance"] <= 0:
            raise ValueError(f"{deck}: metric {name} tolerance 必须为正")


def discover_cases(root: Path = SPICE_DIR) -> list[Case]:
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"SPICE 目录不存在: {root}")
    cases = []
    assertions = set(root.glob("**/assert.json"))
    for deck in sorted(root.glob("**/*.cir")):
        spec_path = deck.with_name("assert.json")
        if not spec_path.is_file():
            raise ValueError(f"{deck}: 缺少 assert.json")
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        validate_spec(spec, deck)
        text = deck.read_text(encoding="utf-8")
        if re.search(r"^\s*\.(include|lib)\b", text, re.I | re.M):
            raise ValueError(f"{deck}: deck 必须自包含，不得 .include/.lib 外部模型")
        if Path(spec["data"]).is_absolute():
            raise ValueError(f"{deck}: data 必须是相对路径")
        cases.append(Case(deck.parent, deck, spec))
        assertions.discard(spec_path)
    if assertions:
        raise ValueError("孤儿 assert.json: " + ", ".join(
            str(path.relative_to(root)) for path in sorted(assertions)))
    if not cases:
        raise ValueError(f"{root} 下没有 .cir deck")
    return cases


def parse_measurements(text: str) -> dict[str, float]:
    return {name: float(value) for name, value in MEASURE_RE.findall(text)}


def compare_metrics(actual: dict[str, float],
                    expected: dict[str, dict]) -> list[str]:
    problems = []
    for name, spec in expected.items():
        if name not in actual:
            problems.append(f"缺少测量值 {name}")
            continue
        error = abs(actual[name] - spec["expected"])
        if error > spec["tolerance"]:
            problems.append(
                f"{name}={actual[name]:.6g}，期望 {spec['expected']:.6g} "
                f"±{spec['tolerance']:.6g}（差 {error:.6g}）")
    return problems


def load_data(path: Path, min_rows: int) -> list[tuple[float, float]]:
    rows = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        try:
            time_value, voltage = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        rows.append((time_value, voltage))
    if len(rows) < min_rows:
        raise ValueError(f"{path}: 数据 {len(rows)} 行，少于 {min_rows}")
    if not all(b[0] > a[0] for a, b in zip(rows, rows[1:])):
        raise ValueError(f"{path}: 时间列不是严格递增")
    return rows


def run_case(case: Case, ngspice: Path,
             output_dir: Path | None = None, timeout: int = 120) -> dict:
    directory = (Path(output_dir) if output_dir
                 else ROOT / "build" / "spice" / case.deck.parent.name)
    directory.mkdir(parents=True, exist_ok=True)
    deck_copy = directory / case.deck.name
    shutil.copy2(case.deck, deck_copy)
    started = time.monotonic()
    result = subprocess.run(
        [str(ngspice), "-b", deck_copy.name],
        cwd=directory, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout)
    log = (result.stdout or "") + (result.stderr or "")
    problems = []
    if result.returncode != 0:
        problems.append(f"ngspice 退出码 {result.returncode}")
    metrics = parse_measurements(log)
    problems += compare_metrics(metrics, case.spec["metrics"])
    data_source = directory / case.spec["data"]
    rows = []
    if not data_source.is_file():
        problems.append(f"缺少数据文件 {data_source.name}")
    else:
        try:
            rows = load_data(data_source, case.spec["min_rows"])
        except ValueError as exc:
            problems.append(str(exc))
    return {
        "case": case.deck.parent.name + "/" + case.deck.name,
        "seconds": round(time.monotonic() - started, 2),
        "returncode": result.returncode,
        "metrics": metrics,
        "rows": len(rows),
        "problems": problems,
        "log": log[-4000:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SPICE_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
    try:
        cases = discover_cases(args.root)
    except ValueError as exc:
        print(f"spice error: {exc}", file=sys.stderr)
        return 1
    ngspice = find_ngspice()
    require = os.environ.get("BOOK_REQUIRE_NGSPICE") == "1"
    if ngspice is None:
        message = "未找到 ngspice；安装后重试，或设置 BOOK_REQUIRE_NGSPICE=1 强制 CI 失败"
        print("spice skip: " + message)
        return 1 if require else 0
    reports, failed = [], False
    for case in cases:
        result = run_case(case, ngspice, timeout=args.timeout)
        reports.append(result)
        if result["problems"]:
            failed = True
            print(f"spice FAIL {result['case']}")
            for problem in result["problems"]:
                print("  " + problem)
        else:
            print(f"spice OK   {result['case']} ({result['rows']} rows, "
                  f"{result['seconds']}s)")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps({"ngspice": str(ngspice), "cases": reports},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
