"""Minimal stdlib client for the OpenAI-compatible image endpoint.

TLS is verified with the interpreter's default context (on Windows this loads the
system ROOT store). Never disable verification: the bearer key is sent on every
call. The API key comes from ``BMS_IMAGE_API_KEY`` and is never written to disk.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
import urllib.parse
import uuid
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_URL = "https://new.orbitix.site"
DEFAULT_MODEL = "gpt-image-2.6-flare"


class ImageApiError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass(frozen=True)
class ImageResult:
    png: bytes
    revised_prompt: str | None
    response_id: str | None


def _key() -> str:
    key = os.environ.get("BMS_IMAGE_API_KEY", "").strip()
    if not key:
        raise ImageApiError("BMS_IMAGE_API_KEY is not set")
    return key


def _base() -> str:
    base = os.environ.get("BMS_IMAGE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ImageApiError("image API base must be an HTTPS origin without userinfo")
    return base


def _decode(payload: dict) -> ImageResult:
    items = payload.get("data") or []
    if not items:
        raise ImageApiError("response has no data[]", body=json.dumps(payload)[:400])
    item = items[0]
    if not item.get("b64_json"):
        raise ImageApiError("response must include b64_json; image URLs are not fetched")
    png = base64.b64decode(item["b64_json"], validate=True)
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ImageApiError("decoded payload is not a PNG")
    return ImageResult(png=png, revised_prompt=item.get("revised_prompt"), response_id=payload.get("id"))


def generate(prompt: str, *, model: str = DEFAULT_MODEL, size: str = "1536x1024") -> ImageResult:
    body = json.dumps({
        "model": model, "prompt": prompt, "n": 1, "size": size,
        "response_format": "b64_json",
    }).encode()
    request = urllib.request.Request(
        _base() + "/v1/images/generations",
        data=body,
        headers={"Authorization": "Bearer " + _key(), "Content-Type": "application/json"},
    )
    return _post(request)


def edit(
    prompt: str,
    reference: Path,
    *,
    model: str = DEFAULT_MODEL,
    size: str = "1536x1024",
) -> ImageResult:
    data = Path(reference).read_bytes()
    boundary = "----bms" + uuid.uuid4().hex
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )

    field("model", model)
    field("prompt", prompt)
    field("n", "1")
    field("size", size)
    field("response_format", "b64_json")
    media_type = mimetypes.guess_type(reference.name)[0] or "application/octet-stream"
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; '
        f'filename="{reference.name}"\r\nContent-Type: {media_type}\r\n\r\n'.encode()
    )
    parts.append(data)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        _base() + "/v1/images/edits",
        data=b"".join(parts),
        headers={
            "Authorization": "Bearer " + _key(),
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    return _post(request)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ImageApiError("image API redirects are not followed with bearer credentials")


def _post(request: urllib.request.Request) -> ImageResult:
    try:
        opener = urllib.request.build_opener(_NoRedirect())
        with opener.open(request, timeout=300) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:  # surface the server message, not a guess
        raise ImageApiError(
            f"HTTP {error.code}", status=error.code,
            body=error.read()[:800].decode("utf-8", "replace"),
        ) from error
    except urllib.error.URLError as error:
        raise ImageApiError(f"transport error: {error.reason}") from error
    return _decode(payload)
