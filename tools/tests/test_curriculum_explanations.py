"""Reader-facing causal explanations, not source-text or field-count tests."""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gen_curriculum_pages as generator


def example():
    import json
    return copy.deepcopy(json.loads((ROOT / "curriculum/concepts.json").read_text(encoding="utf-8"))["concepts"][0])


def test_explanation_keeps_causal_steps_and_boundary_in_book():
    row = example()
    row["explanation"] = {"mechanism": "同一拍的三个读数仍不能直接证明内部安全。", "worked_steps": ["先记录电压。", "再核对同拍电流与温度。"], "boundary": "刚撤载不等于已经静置。", "watch_for": "先看读数如何进入估计。"}
    rendered = generator.book_block([row], "1-1")
    assert row["explanation"]["mechanism"] in rendered
    assert all(step in rendered for step in row["explanation"]["worked_steps"])
    assert row["explanation"]["boundary"] in rendered
    assert row["explanation"]["watch_for"] in rendered
    assert "kp-three-probes" in rendered
