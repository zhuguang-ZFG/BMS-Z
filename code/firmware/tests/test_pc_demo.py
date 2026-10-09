"""跨语言契约：真实 C 决策影响模型下一拍，传输损坏不能变成有效遥测。"""
import json
import shutil
import subprocess
import sys

import pytest

import pc_demo


@pytest.fixture(scope="module")
def executable(tmp_path_factory):
    if shutil.which("gcc") is None:
        pytest.skip("PC 综合实验需要 gcc；CI 的 Linux runner 会执行此项")
    return pc_demo.build_bridge(tmp_path_factory.mktemp("bridge"))


@pytest.fixture(scope="module")
def replay(executable):
    return pc_demo.simulate(executable)


def test_protection_controls_next_tick_and_keeps_first_snapshot(replay):
    rows, _, _, report = replay
    assert report["passed"]
    assert [r["fault"] for r in rows[45:49]] == ["NONE", "NONE", "OVP", "OVP"]
    assert rows[47]["actual_a"] == 2.0   # 先采样，再决策；不能倒写本拍电流。
    assert rows[48]["actual_a"] == 0.0
    assert rows[60]["fault"] == "SCD"
    assert rows[60]["snapshot_tick"] == 48
    assert rows[60]["snapshot_current_ma"] == 2000
    assert rows[60]["snapshot_cell0_mv"] == 4300
    for previous, current in zip(rows[:-1], rows[1:], strict=True):
        key = "charge_on" if current["requested_a"] > 0 else "discharge_on"
        assert current["actual_a"] == (current["requested_a"] if previous[key] else 0.0)


def test_wire_can_be_replayed_independently_in_arbitrary_chunks(replay):
    rows, received, wire, _ = replay
    parser = pc_demo.FrameParser()
    decoded = []
    for start in range(0, len(wire), 7):
        for byte in wire[start:start + 7]:
            frame = parser.feed(byte)
            if frame is not None:
                decoded.append(pc_demo.decode(frame))
    decoded.extend(pc_demo.decode(frame) for frame in parser.flush())
    assert decoded == received
    assert len(received) == len(rows) - 1
    assert parser.frames_bad_crc == 1
    assert received[12]["tick"] == 14  # 唯一坏帧 13 被丢弃，下帧找回。
    assert received[-1]["tick"] == 100

def test_innovation_flags_sensor_faults_without_truth(replay):
    rows, _, _, report = replay
    # 无真值口径（对照 SOC 专题 §5）：不碰 soc_mean_true，只看新息。
    assert report["checks"]["innovation_flags_sensor_faults"]
    steady = [abs(r["innovation_mv"]) for r in rows if r["phase"] in ("charge", "discharge")]
    baseline = sorted(steady)[len(steady) // 2]
    for phase in ("ovp_sensor", "short_sensor"):
        peak = max(abs(r["innovation_mv"]) for r in rows if r["phase"] == phase)
        assert peak > 20 * baseline
    # 温度不进观测方程：hot 窗口没有新增跳变，只是短路污染的衰减尾巴。
    hot = max(abs(r["innovation_mv"]) for r in rows if r["phase"] == "hot_sensor")
    unload = max(abs(r["innovation_mv"]) for r in rows if r["phase"] == "unload")
    assert hot < unload


@pytest.mark.parametrize("line", [
    "3700 3700 3700 3700 0 250 0 50 extra\n",
    "3700 3700 3700 3700 99999999999999999999999 250 0 50\n",
    "3700 3700 3700 3700 0 250 0 101\n",
    "3700 3700 3700 3700 0 250 2 50\n",
    "3700 3700 3700 3700 0 nan 0 50\n",
    "3700 3700 3700 3700 0 250 0 50",
])
def test_bridge_rejects_malformed_input_before_deciding(executable, line):
    result = subprocess.run([str(executable)], input=line, text=True,
                            capture_output=True, timeout=5)
    assert result.returncode == 2
    assert not result.stdout
    assert "invalid input" in result.stderr


def test_decode_rejects_reserved_fault_mask_bits():
    def frame_with_fault_mask(fault_mask):
        payload = pc_demo.TELEMETRY.pack(
            1, 1, 50, fault_mask, 0, 0, 0, 250, 3700, 3700, 3700, 3700)
        return pc_demo.Frame(1, 0x10, payload)

    assert pc_demo.decode(frame_with_fault_mask(0x10))["fault_mask"] == 0x10
    with pytest.raises(ValueError, match="遥测字段越界"):
        pc_demo.decode(frame_with_fault_mask(0x20))


def test_cli_writes_reviewable_artifacts(tmp_path, executable):
    result = subprocess.run([sys.executable, str(pc_demo.CODE / "firmware/pc_demo.py"),
                             "--out", str(tmp_path)], text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / "report.json").read_text())["passed"]
    assert (tmp_path / "wire.bin").stat().st_size == 100 * (24 + 6) + 3
    assert (tmp_path / "samples.csv").read_text().count("\n") == 101
    assert (tmp_path / "telemetry.csv").read_text().count("\n") == 100
    assert any(row["fault"] == "SCD" for row in json.loads((tmp_path / "events.json").read_text()))
