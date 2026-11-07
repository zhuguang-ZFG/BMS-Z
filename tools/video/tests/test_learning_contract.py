"""Consumer-visible microcourse learning targets; new tests require review."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

VIDEO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VIDEO))


def load_module(name, filename):
    module_spec = importlib.util.spec_from_file_location(name, VIDEO / filename)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("field,value", [
    ("kp_id", None),
    ("kp_id", "missing-kp"),
    ("kp_id", ["load-voltage-drop", "ocv-trust"]),
    ("ladder_level", "L6"),
    ("through_input", ""),
    ("retrieve_task", ""),
])
def test_spec_gate_rejects_unusable_microcourse_target(tmp_path, monkeypatch, field, value):
    spec_mod = load_module("learning_gate_spec", "spec.py")
    spec = json.loads((VIDEO / "microcourses/m01-load-voltage-drop.json").read_text(encoding="utf-8"))
    spec.update(kp_id="load-voltage-drop", ladder_level="L3", through_input="20 A × 20 mΩ", retrieve_task="闭卷复算压降并解释 SOC 是否瞬间变化。")
    spec[field] = value
    path = tmp_path / "m01-load-voltage-drop.json"
    path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(spec_mod, "find_spec", lambda _: path)
    problems = spec_mod.check(path.stem)
    assert any(field in item for item in problems), problems


def test_published_body_exposes_resolved_target_and_retrieval():
    publish = load_module("learning_publish", "publish.py")
    spec = json.loads((VIDEO / "microcourses/m01-load-voltage-drop.json").read_text(encoding="utf-8"))
    spec.update(kp_id="load-voltage-drop", ladder_level="L3", through_input="20 A × 20 mΩ", retrieve_task="闭卷复算压降并解释 SOC 是否瞬间变化。")
    body = publish.body_of(spec, {"duration": 60, "beats": []})
    assert "load-voltage-drop · L3" in body
    assert "20 A × 20 mΩ" in body
    assert spec["retrieve_task"] in body
    assert "http" not in body and "github" not in body
    target = publish.spec_mod.learning_target(spec)
    assert target["url"].endswith("#kp-load-voltage-drop-l3")


def test_series_publication_does_not_acquire_microcourse_requirements():
    publish = load_module("learning_series_publish", "publish.py")
    spec = json.loads((VIDEO / "specs/ep01-prerequisites.json").read_text(encoding="utf-8"))
    body = publish.body_of(copy.deepcopy(spec), {"duration": 60, "beats": []})
    assert spec["title"] in body
    assert "本课知识点" not in body
