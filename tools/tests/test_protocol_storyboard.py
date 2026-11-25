"""Keep the visible wire bytes complete, including address and length."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gen_protocol_storyboard as generator  # noqa: E402


def wire_bytes(panel_number):
    root = ET.fromstring(generator.panel(panel_number))
    return bytes(int(t.text, 16) for t in root.iter("{http://www.w3.org/2000/svg}text")
                 if t.get("y") == "182")


def test_displayed_frame_includes_address_length_and_check_byte():
    for panel_number in (1, 2, 3, 4, 6):
        assert wire_bytes(panel_number) == bytes.fromhex("00 11 22 aa 55 01 03 02 0e 74 13")


def test_bad_flow_changes_only_one_checksum_bit():
    good, bad = wire_bytes(4), wire_bytes(5)
    assert good[:-1] == bad[:-1]
    assert good[-1] ^ bad[-1] == 1
    assert generator.trace(good)[-1] == (1, 0)
    assert generator.trace(bad)[-1] == (0, 1)
    assert generator.trace(good)[-2] == (0, 0)
