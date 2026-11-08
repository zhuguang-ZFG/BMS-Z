"""Security and paid-artifact publication boundaries; requires independent review."""
from __future__ import annotations

import io
import json
import sys
import urllib.request
from http.client import HTTPMessage
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import handdraw_api as api  # noqa: E402
import make_handdrawn as pipeline  # noqa: E402


def test_plaintext_endpoint_is_refused_before_credentials(monkeypatch):
    monkeypatch.setenv('BMS_IMAGE_BASE_URL', 'http://example.invalid')
    with pytest.raises(api.ImageApiError, match='HTTPS'):
        api._base()


def test_url_only_image_is_refused_without_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('untrusted image URL must never trigger network access')
    monkeypatch.setattr(api.urllib.request, 'urlopen', forbidden)
    with pytest.raises(api.ImageApiError, match='b64_json'):
        api._decode({'data': [{'url': 'http://example.invalid/picture.png'}]})


def test_authenticated_redirect_is_refused():
    with pytest.raises(api.ImageApiError, match='redirects'):
        api._NoRedirect().redirect_request(
            urllib.request.Request('https://example.invalid'), io.BytesIO(),
            302, 'redirect', HTTPMessage(), 'https://other.invalid',
        )


def test_concurrent_record_merges_preserve_every_completed_image(tmp_path, monkeypatch):
    target = tmp_path / 'manifest.json'
    target.write_text(json.dumps({'schema': pipeline.SCHEMA, 'assets': {}}), encoding='utf-8')
    monkeypatch.setattr(pipeline, 'MANIFEST', target)
    def publish(index):
        pipeline.merge_record(str(index), {'image_sha256': str(index)})
    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(publish, range(12)))
    records = json.loads(target.read_text(encoding='utf-8'))['assets']
    assert records == {str(index): {'image_sha256': str(index)} for index in range(12)}


def test_second_publisher_cannot_start_a_paid_batch(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, 'OUT', tmp_path)
    with pipeline.publisher_lock():
        with pytest.raises(FileExistsError):
            with pipeline.publisher_lock():
                pytest.fail('second publisher acquired the same command lock')
    assert not (tmp_path / '.publisher.lock').exists()


def test_existing_paid_candidate_needs_explicit_replace(tmp_path, monkeypatch):
    target = tmp_path / 'manifest.json'
    target.write_text(json.dumps({'schema': pipeline.SCHEMA, 'assets': {'s2-hero': {'visual_acceptance':'rejected'}}}),encoding='utf-8')
    monkeypatch.setattr(pipeline, 'MANIFEST', target)
    monkeypatch.setattr(pipeline, 'PAUSE', tmp_path / 'PAUSE')
    monkeypatch.setattr(sys, 'argv', ['make_handdrawn.py', '--only', 's2-hero'])
    def forbidden(key):
        pytest.fail('a rejected paid candidate must not silently trigger another paid request')
    monkeypatch.setattr(pipeline, '_generate', forbidden)
    assert pipeline._main() == 1
    assert json.loads(target.read_text(encoding='utf-8'))['assets']['s2-hero']['visual_acceptance'] == 'rejected'
