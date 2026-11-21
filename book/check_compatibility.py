"""Automated browser layout checks; these do not claim physical e-reader coverage."""

from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
from pathlib import Path
import tempfile
import threading
import zipfile

from playwright.sync_api import sync_playwright

from combined_epub import OPF, xml

ROOT = Path(__file__).resolve().parents[1]
METRICS = """() => ({width:innerWidth,scroll:document.documentElement.scrollWidth,
color:getComputedStyle(document.body).color,
brokenImages:[...document.images].filter(x=>!x.complete||!x.naturalWidth).length})"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check(site, epub, output, channel=None):
    output.mkdir(parents=True, exist_ok=True)
    rows, failures = [], []
    with tempfile.TemporaryDirectory(prefix="reading-", dir=output) as work:
        extracted = Path(work)
        with zipfile.ZipFile(epub) as archive:
            archive.extractall(extracted)
            package = xml(archive.read("OEBPS/content.opf"))
        manifest = {i.get("id"): i.get("href") for i in package.find(OPF + "manifest")}
        spine = [manifest[i.get("idref")] for i in package.find(OPF + "spine")]
        server = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT))
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}/"
        site_url = base + site.relative_to(ROOT).as_posix() + "/downloads/index.html"
        epub_url = base + extracted.relative_to(ROOT).as_posix() + "/OEBPS/"

        def record(page, scope, case, document):
            metrics = page.evaluate(METRICS)
            row = {"scope": scope, "case": case, "document": document, **metrics}
            rows.append(row)
            if metrics["scroll"] > metrics["width"] + 1 or metrics["brokenImages"]:
                failures.append(row)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel=channel, headless=True)
                for name, width, height, theme in [
                    ("desktop", 1440, 1000, "light"),
                    ("phone", 360, 800, "light"),
                    ("narrow", 320, 760, "light"),
                    ("dark", 390, 844, "dark"),
                    ("large-type", 390, 844, "light"),
                    ("grayscale", 600, 800, "light"),
                ]:
                    page = browser.new_page(
                        viewport={"width": width, "height": height},
                        color_scheme=theme,
                        reduced_motion="reduce",
                    )
                    page.on(
                        "pageerror",
                        lambda err: failures.append({"script_error": str(err)}),
                    )
                    page.goto(site_url, wait_until="networkidle")
                    if name == "large-type":
                        page.add_style_tag(
                            content="html{font-size:32px!important}body{font-size:34px!important}"
                        )
                    if name == "grayscale":
                        page.add_style_tag(content="html{filter:grayscale(1)}")
                    for amps, volts in [(0, "3.70 V"), (30, "3.10 V"), (20, "3.30 V")]:
                        page.locator("#current").fill(str(amps))
                        assert page.locator("#meter-voltage").text_content() == volts
                    page.locator("#current").focus()
                    page.keyboard.press("ArrowLeft")
                    assert page.locator("#current-value").text_content() == "19 A"
                    assert page.locator("a[download]").count() == 8
                    page.locator("#current").fill("20")
                    page.locator("#current").blur()
                    page.locator(".cover img").scroll_into_view_if_needed()
                    page.wait_for_function(
                        "[...document.images].every(x=>x.complete&&x.naturalWidth)"
                    )
                    page.evaluate("scrollTo(0,0)")
                    record(page, "downloads", name, "index.html")
                    page.screenshot(
                        path=str(output / f"download-{name}.png"), full_page=True
                    )
                    page.close()
                page = browser.new_page(
                    java_script_enabled=False, viewport={"width": 360, "height": 800}
                )
                page.goto(site_url, wait_until="load")
                assert page.locator("a[download]").count() == 8
                assert page.locator("#meter-voltage").text_content() == "3.30 V"
                assert not page.locator(".experiment").is_visible()
                page.close()
                # Every spine document is exercised at a large font on a narrow screen.
                for index, document in enumerate(spine):
                    page = browser.new_page(
                        viewport={"width": 390, "height": 844}, reduced_motion="reduce"
                    )
                    page.goto(epub_url + document, wait_until="load")
                    page.add_style_tag(
                        content="html{font-size:28px!important}body{font-size:28px!important}"
                    )
                    page.evaluate("document.fonts.ready")
                    record(page, "epub", "large-type", document)
                    if document in {"guide.xhtml", "v2/book.xhtml"}:
                        page.screenshot(path=str(output / f"epub-{index}-large.png"))
                    page.close()
                for document in [
                    "guide.xhtml",
                    "v2/book.xhtml",
                    next(d for d in spine if d.startswith("v1/text/")),
                ]:
                    page = browser.new_page(
                        viewport={"width": 600, "height": 800}, color_scheme="dark"
                    )
                    page.goto(epub_url + document, wait_until="load")
                    record(page, "epub", "dark", document)
                    color = page.evaluate("getComputedStyle(document.body).color")
                    assert int(color.split("(")[1].split(",")[0]) >= 180, color
                    page.screenshot(
                        path=str(output / f"epub-dark-{Path(document).stem}.png")
                    )
                    page.close()
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    result = {
        "physical_device_tested": False,
        "epub_sha256": hashlib.sha256(epub.read_bytes()).hexdigest(),
        "scenarios": rows,
        "failures": failures,
        "passed": not failures,
    }
    (output / "compatibility.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if failures:
        raise ValueError(
            f"Compatibility failures: {json.dumps(failures, ensure_ascii=False)}"
        )
    print(
        f"PASS: {len(rows)} layout scenarios, keyboard interaction, no-JS fallback; no physical device claim"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=ROOT / "book/dist/site")
    parser.add_argument(
        "--epub", type=Path, default=ROOT / "book/dist/combined/from-analog-to-bms.epub"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "book/dist/compatibility")
    parser.add_argument(
        "--channel", default=None, help="Use msedge for a locally installed Edge"
    )
    args = parser.parse_args()
    check(args.site.resolve(), args.epub.resolve(), args.output.resolve(), args.channel)
