from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gen_curriculum_pages  # noqa: E402


def curriculum() -> dict:
    return json.loads((ROOT / "curriculum" / "concepts.json").read_text(encoding="utf-8"))


def test_generated_question_map_is_not_hand_maintained() -> None:
    expected = gen_curriculum_pages.render(curriculum())
    actual = (ROOT / "docs" / "核心问题地图.md").read_text(encoding="utf-8")
    assert actual == expected
    assert "不要手改正文" in actual


def test_animation_index_does_not_infer_levels_from_ceiling() -> None:
    row = curriculum()["concepts"][0]
    row["animations"] = ["docs/circuits/assets/example.svg"]
    row["ladder"] = {
        "L2": {"media": [row["animations"][0]]},
        "L3": {"media": ["bms-book/demos/probes.py"]},
    }
    rendered = gen_curriculum_pages.block_animation_targets([row])
    assert "[example](../circuits/assets/example.svg)" in rendered
    assert f"#kp-{row['id']}-l2" in rendered
    assert f"#kp-{row['id']}-l3" not in rendered


def test_every_concept_has_precheck_and_deliverable() -> None:
    for concept in curriculum()["concepts"]:
        assert concept["precheck"].endswith(("？", "?"))
        assert concept["deliverable"].strip()
        assert set(concept["teaching"]) == {"hook", "worked_example", "misconception"}
        assert all(value.strip() for value in concept["teaching"].values())
        assert 1 <= concept["difficulty"] <= 3
        assert concept["status"] in {"active", "pilot", "retired"}


def test_generated_map_exposes_one_checkable_delivery_per_concept() -> None:
    data = curriculum()
    rendered = gen_curriculum_pages.render(data)
    assert rendered.count("- [ ] **交付**") == len(data["concepts"])
    for index, concept in enumerate(data["concepts"], 1):
        assert f"### {index}. {concept['question']}" in rendered
        for prerequisite in concept["prerequisites"]:
            target_index = next(
                i for i, item in enumerate(data["concepts"], 1) if item["id"] == prerequisite
            )
            target = next(item for item in data["concepts"] if item["id"] == prerequisite)
            anchor = gen_curriculum_pages.slugify(f"{target_index}. {target['question']}")
            assert f"](#{anchor})" in rendered
