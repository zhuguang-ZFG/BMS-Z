"""4S PC 综合实验：电芯模型 → SOC → 原版 C 状态机 → 字节流 → 接收日志。

运行：python code/firmware/pc_demo.py --out code/firmware/pc-demo-output
只需 code/requirements.txt 和 gcc。内部管道不是串口，1 秒一拍不是硬件保护时序。
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from queue import Empty, Queue
import shutil
import struct
import subprocess
import sys
import tempfile
from threading import Thread

import numpy as np

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "soc"))
sys.path.insert(0, str(CODE / "protocol"))
from cell_model import TheveninCell  # noqa: E402
from estimators import EKFEstimator  # noqa: E402
from frames import Frame, FrameParser  # noqa: E402

# cmd=0x10，载荷 24 字节，大端。字段与教程中的协议表一一对应。
TELEMETRY = struct.Struct(">IBBHBBih4H")
STATES = ("INIT", "STANDBY", "CHARGE", "DISCHARGE", "BALANCE", "FAULT", "SLEEP")


class Firmware:
    """通过有超时的管道调用真实 C 实现，不复制状态机逻辑。"""

    def __init__(self, executable: Path):
        self.process = subprocess.Popen(
            [str(executable)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
        )
        self.replies: Queue = Queue()
        self.reader = Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.process.stdout:
            self.replies.put(line)
        self.replies.put(None)

    def tick(self, mv: list[int], ma: int, temp: int, charger: bool, soc: int) -> dict:
        self.process.stdin.write(" ".join(map(str, [*mv, ma, temp, int(charger), soc])) + "\n")
        self.process.stdin.flush()
        try:
            line = self.replies.get(timeout=10)
        except Empty as exc:
            raise RuntimeError("C 状态机 10 秒内没有响应") from exc
        if line is None:
            raise RuntimeError("C 状态机提前退出：" + self.process.stderr.read())
        return json.loads(line)

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.reader.join(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()


def build_bridge(directory: Path, compiler: str = "gcc") -> Path:
    cc = shutil.which(compiler)
    if cc is None:
        raise RuntimeError(f"找不到 C 编译器 {compiler}；先安装 gcc 并加入 PATH")
    executable = directory / ("pc_bridge.exe" if sys.platform == "win32" else "pc_bridge")
    subprocess.run(
        [cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-o", str(executable),
         str(CODE / "firmware/bms.c"), str(CODE / "firmware/pc_bridge.c")],
        check=True, capture_output=True, text=True, timeout=60,
    )
    return executable


def scenario(k: int) -> tuple[float, bool, str]:
    """索引从 0 开始；故障是采样端注入，未声称模拟 MOS 损坏或电芯热行为。"""
    if k < 5:
        return 0.0, False, "idle"
    if k < 25:
        return 2.0, True, "charge"
    if k < 45:
        return -2.0, False, "discharge"
    if k < 50:
        return 2.0, True, "ovp_sensor"
    if k < 60:
        return -2.0, False, "recovery"
    if k < 65:
        return -2.0, False, "short_sensor"
    if k < 70:
        return 0.0, False, "unload"
    if k < 75:
        return -2.0, False, "hot_sensor"
    if k < 80:
        return -2.0, False, "cool"
    if k < 90:
        return 2.0, True, "charge"
    return 0.0, False, "idle"


def decode(frame: Frame) -> dict:
    if frame.addr != 1 or frame.cmd != 0x10 or len(frame.data) != TELEMETRY.size:
        raise ValueError("不是本实验的 0x10 遥测帧")
    tick, state, soc, fault, mos, balance, ma, temp, *mv = TELEMETRY.unpack(frame.data)
    if state >= len(STATES) or soc > 100 or mos > 3 or balance > 15:
        raise ValueError("遥测字段越界")
    return dict(tick=tick, state=STATES[state], soc_pct=soc, fault_mask=fault,
                charge_on=mos & 1, discharge_on=(mos >> 1) & 1,
                balance_mask=balance, current_ma=ma, temp_c10=temp,
                **{f"cell{i}_mv": value for i, value in enumerate(mv)})


def simulate(executable: Path) -> tuple[list[dict], list[dict], bytes, dict]:
    cells = [TheveninCell(10.0, 0.020, 0.015, 3000.0, soc0=s)
             for s in (0.78, 0.76, 0.75, 0.74)]
    estimator = EKFEstimator(0.70, 9.5, 0.020, 0.015, 3000.0)
    parser = FrameParser()
    firmware = Firmware(executable)
    rows, received = [], []
    wire = bytearray()
    previous = dict(charge_on=0, discharge_on=0, balance_mask=0)
    try:
        for k in range(100):
            requested, charger, phase = scenario(k)
            allowed = previous["charge_on"] if requested > 0 else previous["discharge_on"]
            actual = requested if allowed else 0.0
            voltages = [float(cell.step(actual - (0.15 if previous["balance_mask"] & (1 << i)
                                                   else 0.0), 1.0))
                        for i, cell in enumerate(cells)]
            mv = [round(v * 1000) for v in voltages]
            ma, temp = round(actual * 1000), 250
            if phase == "ovp_sensor":
                mv[0] = 4300
            elif phase == "short_sensor":
                ma = -31000
            elif phase == "hot_sensor":
                temp = 650
            # 估算器和固件吃同一组带故障的采样；估算受扰也必须如实保留。
            estimated = estimator.step(ma / 1000, float(np.mean(mv)) / 1000, 1.0)
            innovation_mv = estimator.last_innovation_v * 1000
            result = firmware.tick(mv, ma, temp, charger, round(estimated * 100))
            row = dict(phase=phase, requested_a=requested, actual_a=actual,
                       soc_mean_true=float(np.mean([cell.soc for cell in cells])),
                       soc_mean_est=estimated, innovation_mv=innovation_mv,
                       current_ma=ma, temp_c10=temp,
                       **{f"cell{i}_mv": value for i, value in enumerate(mv)}, **result)
            rows.append(row)
            previous = result
            payload = TELEMETRY.pack(
                result["tick"], result["state_id"], result["soc_pct"], result["fault_mask"],
                result["charge_on"] | (result["discharge_on"] << 1), result["balance_mask"],
                ma, temp, *mv,
            )
            packet = bytearray(Frame(1, 0x10, payload).to_bytes())
            if k == 12:
                packet[-1] ^= 0x01       # 损坏第 13 帧 CRC，下一帧仍应正常接收。
            chunk = (b"\x00\xff\x19" if k == 32 else b"") + packet
            wire.extend(chunk)
            for byte in chunk:
                frame = parser.feed(byte)
                if frame is not None:
                    received.append(decode(frame))
        received.extend(decode(frame) for frame in parser.flush())  # 流已结束。
    finally:
        firmware.close()
    # 无真值口径的稳态基线：恒流段新息绝对值的中位数，避开负载阶跃瞬态。
    steady_innovation = float(np.median([abs(r["innovation_mv"]) for r in rows
                                         if r["phase"] in ("charge", "discharge")]))
    checks = {
        "ovp_after_three_samples": rows[45]["fault"] == "NONE" and rows[46]["fault"] == "NONE"
        and rows[47]["fault"] == "OVP" and rows[47]["charge_on"] == 0,
        "cutoff_controls_next_sample": rows[48]["actual_a"] == 0.0,
        "short_cuts_both_paths": rows[60]["fault"] == "SCD"
        and rows[60]["charge_on"] == rows[60]["discharge_on"] == 0,
        "snapshot_keeps_first_ovp": rows[-1]["snapshot_fault"] == "OVP"
        and rows[-1]["snapshot_tick"] == 48 and rows[-1]["snapshot_cell0_mv"] == 4300,
        "overtemperature_detected": rows[70]["fault"] == "OT",
        "crc_bad_frame_rejected": parser.frames_bad_crc == 1
        and [r["tick"] for r in received] == [i for i in range(1, 101) if i != 13],
        "telemetry_matches_firmware": all(
            all(r[key] == rows[r["tick"] - 1][key] for key in r) for r in received),
        # 无真值口径（对照 SOC 专题 §5）：采样对不上模型时新息自己会喊。
        "innovation_flags_sensor_faults": max(
            max(abs(r["innovation_mv"]) for r in rows if r["phase"] == phase)
            for phase in ("ovp_sensor", "short_sensor")) > 20 * steady_innovation,
    }
    report = dict(kind="synthetic_pc_integration", samples=len(rows), dt_s=1,
                  received_frames=len(received), bad_crc=parser.frames_bad_crc,
                  resyncs=parser.resyncs, checks=checks, passed=all(checks.values()))
    return rows, received, bytes(wire), report


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(output: Path, compiler: str = "gcc") -> dict:
    with tempfile.TemporaryDirectory(prefix="bms-pc-") as tmp:
        rows, received, wire, report = simulate(build_bridge(Path(tmp), compiler))
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "samples.csv", rows)
    write_csv(output / "telemetry.csv", received)
    (output / "wire.bin").write_bytes(wire)
    events = [row for i, row in enumerate(rows)
              if i == 0 or (row["state"], row["fault_mask"]) !=
              (rows[i - 1]["state"], rows[i - 1]["fault_mask"])]
    (output / "events.json").write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "pc-demo-output")
    parser.add_argument("--cc", default="gcc", help="C99 编译器命令或可执行文件路径")
    args = parser.parse_args()
    try:
        report = run(args.out, args.cc)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"PC demo failed: {exc}\n{getattr(exc, 'stderr', '')}\n")
    print(json.dumps(report, indent=2))
    print(f"Output: {args.out.resolve()}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
