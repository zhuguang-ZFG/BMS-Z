from __future__ import annotations

import base64
import json
from pathlib import Path
import sys

import pytest


VIDEO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VIDEO))
try:
    import narrate
finally:
    sys.path.pop(0)


def test_mimo_config_prefers_environment_without_leaking_key(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / "mimo.env"
    env_file.write_text(
        "MIMO_API_KEY=file-secret\nMIMO_BASE_URL=https://file.example/v1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MIMO_API_KEY", "environment-secret")
    monkeypatch.setenv("MIMO_TTS_MODEL", "mimo-v2.5-tts")
    config = narrate.load_mimo_config(env_file)
    assert config["key"] == "environment-secret"
    assert config["base_url"] == "https://file.example/v1"
    assert config["voices"]["teacher"] == "茉莉"
    assert "environment-secret" not in narrate.mimo_cache_id(config)


def test_mimo_request_uses_audio_chat_contract(tmp_path) -> None:
    env_file = tmp_path / "mimo.env"
    env_file.write_text("MIMO_API_KEY=test-only\n", encoding="utf-8")
    config = narrate.load_mimo_config(env_file)
    body = narrate.mimo_request_body("四点二五伏是动作线。", "teacher", "+4%", config)
    assert body["model"] == "mimo-v2.5-tts"
    assert body["audio"] == {"format": "wav", "voice": "茉莉"}
    assert body["messages"][-1] == {
        "role": "assistant",
        "content": "四点二五伏是动作线。",
    }
    assert "数字" in body["messages"][0]["content"]


def test_mimo_synthesis_decodes_audio_without_logging_secret(tmp_path, monkeypatch) -> None:
    config = {
        "key": "test-only-secret",
        "base_url": "https://example.invalid/v1",
        "model": "mimo-v2.5-tts",
        "style": "自然。",
        "voices": {"teacher": "茉莉", "guest": "茉莉", "announcer": "茉莉"},
    }
    wav = b"RIFF" + b"0" * 600
    response = {
        "choices": [{"message": {"audio": {"data": base64.b64encode(wav).decode()}}}]
    }
    monkeypatch.setattr(narrate, "call_mimo", lambda body, cfg: response)
    monkeypatch.setattr(narrate, "to_wav", lambda src, dst: dst.write_bytes(src.read_bytes()))
    dst = tmp_path / "beat.wav"
    narrate.synth_mimo("测试", "teacher", "+4%", dst, config)
    assert dst.read_bytes() == wav
    public = json.dumps({"engine": narrate.mimo_cache_id(config)}, ensure_ascii=False)
    assert config["key"] not in public


def test_mimo_config_requires_secret(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("MIMO_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="set_mimo_key.py"):
        narrate.load_mimo_config(tmp_path / "missing.env")
