"""Web 图片纪律单测：首图之外懒加载 + data URI 嗅探宽高。

回归基线（2026-11-12）：合并后站点对账 check_pages.py 对 downloads/ 里的
单文件书要求全部 <img> 带 loading="lazy"（首图豁免）与数值 width/height；
旧行为是 391 张图 0 懒加载、270 张缺宽高。"""
import base64
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build_book import apply_web_image_discipline  # noqa: E402

SVG = base64.b64encode(
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 940">'
    b'<rect width="560" height="940"/></svg>').decode()
PNG = base64.b64encode(
    b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR"
    + (320).to_bytes(4, "big") + (240).to_bytes(4, "big")
    + b"\x08\x06\x00\x00\x00" + b"x" * 20).decode()
GIF = base64.b64encode(
    b"GIF89a" + (10).to_bytes(2, "little")
    + (7).to_bytes(2, "little") + b"zz").decode()


def img(src: str, alt: str = "图", extra: str = "") -> str:
    return f'<img src="data:image/{src}" alt="{alt}"{extra}>'


class WebImageDisciplineTests(unittest.TestCase):
    def test_first_image_keeps_eager_and_gets_sniffed_dims(self):
        out = apply_web_image_discipline(img(f"svg+xml;base64,{SVG}"))
        self.assertNotIn('loading="lazy"', out)
        self.assertIn('width="560"', out)
        self.assertIn('height="940"', out)

    def test_later_images_get_lazy(self):
        out = apply_web_image_discipline(
            img(f"png;base64,{PNG}", "一") + img(f"png;base64,{PNG}", "二"))
        second = out[out.index('alt="二"'):]
        self.assertIn('loading="lazy"', second)
        first = out[:out.index('alt="二"')]
        self.assertNotIn('loading="lazy"', first)

    def test_png_ihdr_dimensions(self):
        out = apply_web_image_discipline(img(f"png;base64,{PNG}"))
        self.assertIn('width="320"', out)
        self.assertIn('height="240"', out)

    def test_gif_header_dimensions(self):
        out = apply_web_image_discipline(img(f"gif;base64,{GIF}"))
        self.assertIn('width="10"', out)
        self.assertIn('height="7"', out)

    def test_partial_dims_replaced_with_native_pair(self):
        out = apply_web_image_discipline(img(f"gif;base64,{GIF}", extra=' width="5"'))
        self.assertIn('width="10"', out)
        self.assertIn('height="7"', out)

    def test_existing_numeric_pair_is_preserved(self):
        out = apply_web_image_discipline(
            img(f"png;base64,{PNG}", extra=' width="320" height="240"'))
        self.assertIn('width="320" height="240"', out)

    def test_style_and_script_blocks_are_untouched(self):
        document = (
            "<style>/* <img src=\"data:image/png;base64,AAAA\"> */</style>"
            "<script>// '<img src=\"x\">'</script>"
            + img(f"svg+xml;base64,{SVG}"))
        out = apply_web_image_discipline(document)
        self.assertIn('<img src="data:image/png;base64,AAAA">', out)
        self.assertIn("// '<img src=\"x\">'", out)

    def test_empty_src_is_left_alone(self):
        out = apply_web_image_discipline('<img alt="占位">')
        self.assertEqual(out, '<img alt="占位">')


if __name__ == "__main__":
    unittest.main()
