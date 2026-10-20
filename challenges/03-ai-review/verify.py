#!/usr/bin/env python3
"""练习自检：可见测试是绿的，而隐藏检查应当红。

退出码 0 只表示夹具完整（问题都还在），不表示你审对了。
先写审查记录，再看 ANSWER.md 和本脚本。
"""
from __future__ import annotations

import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE / "project"
REPORT = PROJECT / "gates_report.txt"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        args,
        cwd=PROJECT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def visible_tests() -> tuple[bool, str]:
    proc = _run([sys.executable, "-m", "pytest", "test_frame_gate.py", "-q"])
    lines = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode == 0, lines[-1] if lines else "（pytest 没有输出）"


def load_gate():
    sys.path.insert(0, str(PROJECT))
    return importlib.import_module("frame_gate")


def bad_crc_counted(gate_mod) -> tuple[bool, str]:
    gate = gate_mod.FrameGate()
    raw = bytearray(gate_mod.build_frame(0x20, 0x03, b"ok"))
    raw[-1] ^= 0xFF
    frames = gate.feed(bytes(raw))
    return gate.bad_crc == 1 and frames == [], f"bad_crc={gate.bad_crc} frames={len(frames)}"


def resync_recovers(gate_mod) -> tuple[bool, str]:
    inner = gate_mod.build_frame(0x20, 0x03, b"in")
    outer = bytearray(gate_mod.build_frame(0x21, 0x01, b"xx" + inner + b"yy"))
    outer[-1] ^= 0xFF
    gate = gate_mod.FrameGate()
    frames = gate.feed(bytes(outer))
    ok = frames == [(0x20, 0x03, b"in")] and gate.bad_crc == 1
    return ok, f"frames={frames!r} bad_crc={gate.bad_crc}"


def binary_payload_delivered(gate_mod) -> tuple[bool, str]:
    gate = gate_mod.FrameGate()
    frames = gate.feed(gate_mod.build_frame(0x20, 0x03, b"\xff\x00"))
    return frames == [(0x20, 0x03, b"\xff\x00")], f"frames={frames!r}"


def payload_limit(gate_mod) -> tuple[bool, str]:
    payload = bytes(gate_mod.MAX_PAYLOAD)
    gate = gate_mod.FrameGate()
    frames = gate.feed(gate_mod.build_frame(0x20, 0x03, payload))
    ok = frames == [(0x20, 0x03, payload)] and gate.bad_len == 0
    return ok, f"frames={len(frames)} bad_len={gate.bad_len}"


def external_imports() -> tuple[bool, str]:
    tree = ast.parse((PROJECT / "frame_gate.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    allowed = set(sys.stdlib_module_names) | {"__future__", "frame_gate"}
    found = sorted(name for name in names if name not in allowed)
    return not found, "、".join(found) if found else "未发现"


def report_reproducible() -> tuple[bool, str]:
    proc = _run([sys.executable, "make_report.py"])
    if proc.returncode != 0:
        return False, f"生成器退出码 {proc.returncode}"
    generated = proc.stdout.strip().splitlines()
    committed = REPORT.read_text(encoding="utf-8").strip().splitlines()
    if generated == committed:
        return True, "生成器输出与文件一致"
    details = []
    for index, line in enumerate(generated):
        other = committed[index] if index < len(committed) else "<缺行>"
        if line != other:
            details.append(f"第 {index + 1} 行 生成器 {line!r} / 文件 {other!r}")
    if len(generated) != len(committed):
        details.append(f"行数 生成器 {len(generated)} / 文件 {len(committed)}")
    return False, "；".join(details)


def main() -> int:
    gate = load_gate()
    checks = [
        ("可见测试（pytest）", True, visible_tests()),
        ("坏帧计数为 1", False, bad_crc_counted(gate)),
        ("坏帧内嵌好帧能被救回", False, resync_recovers(gate)),
        ("二进制载荷照常交付", False, binary_payload_delivered(gate)),
        ("载荷 64 字节仍在边界内", False, payload_limit(gate)),
        ("没有引入外部依赖", False, external_imports()),
        ("生成报告可由生成器复现", False, report_reproducible()),
    ]

    print("依次检查：可见测试应当绿；隐藏检查应当红（红才是夹具完整）。\n")
    print(f"{'检查':<24}{'实际':<8}{'夹具期望':<10}判定")
    print("-" * 56)
    broken = []
    for name, expected, (passed, detail) in checks:
        if passed != expected:
            broken.append(name)
        print(
            f"{name:<24}{'通过' if passed else '失败':<8}"
            f"{'通过' if expected else '失败':<10}"
            f"{'OK' if passed == expected else '夹具异常'}"
        )
        if detail:
            print(f"    {detail}")
    print()
    if broken:
        print("FAIL: 这些检查的结果和夹具设计不一致：" + "、".join(broken))
        print("先确认 project/ 没有被改过；如果你真的修好了 bug，隐藏检查变绿是意料之中的。")
        return 1
    print("OK: 夹具完整：可见测试全绿，5 类隐藏问题都还在。")
    print("这只是对答案用的自检；你的审查记录要自己写，见 README.md。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
