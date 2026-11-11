"""合成资产须自包含；打印无位图；印刷文字可读；缺底图不得静默替代。"""
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image

import compose_technical_overlay as overlay


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        Image.new("RGB", (1448, 1086), "white").save(self.root / "base.png")
        self.markup = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1448 1086"><text x="60" y="80" font-size="34" fill="#222222">电流 3mA</text></svg>'
        (self.root / "overlay.svg").write_text(self.markup, encoding="utf-8")
        self.spec = {"title": "测量", "alt": "电流读数", "overlay": "overlay.svg",
                     "base_image": "base.png", "output": "out/figure.svg", "paper": "#fff8ee"}

    def test_composite_embeds_base_and_print_is_all_vector(self):
        outputs = overlay.compose(self.spec, self.root)
        composite = outputs["composite"].read_text(encoding="utf-8")
        printed = outputs["print"].read_text(encoding="utf-8")
        self.assertIn("data:image/png;base64,", composite)
        self.assertNotIn("<image", printed)
        self.assertIn("电流 3mA", printed)
        ET.fromstring(composite)

    def test_missing_base_fails_before_writing(self):
        (self.root / "base.png").unlink()
        with self.assertRaises(FileNotFoundError):
            overlay.compose(self.spec, self.root)
        self.assertFalse((self.root / "out").exists())

    def test_print_only_is_explicit_and_never_claims_composite(self):
        (self.root / "base.png").unlink()
        self.assertEqual({"print"}, set(overlay.compose(self.spec, self.root, print_only=True)))

    def test_small_or_low_contrast_text_rejected(self):
        for markup in (self.markup.replace('font-size="34"', 'font-size="20"'),
                       self.markup.replace('#222222', '#eeeeee')):
            with self.assertRaises(ValueError):
                overlay.validate_overlay(markup, self.spec)

    def test_external_or_active_content_rejected(self):
        for fragment in ('<script>alert(1)</script>', '<image href="https://example.org/x"/>',
                         '<rect onload="alert(1)"/>', '<style>@import url(x)</style>'):
            with self.assertRaises(ValueError):
                overlay.validate_overlay(self.markup.replace('</svg>', fragment + '</svg>'), self.spec)

    def test_wrong_aspect_is_not_silently_cropped(self):
        Image.new("RGB", (100, 100)).save(self.root / "base.png")
        with self.assertRaises(ValueError):
            overlay.compose(self.spec, self.root)

    def test_output_cannot_escape_workspace(self):
        self.spec["output"] = "../escape.svg"
        with self.assertRaises(ValueError):
            overlay.compose(self.spec, self.root)

    def test_python_vector_base_survives_print_without_shadows(self):
        del self.spec['base_image']
        self.spec['base_svg'] = 'base.svg'
        (self.root / 'base.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1448 1086">'
            '<rect data-paper-shadow="true" width="10" height="10"/>'
            '<path id="chip-shape" d="M0 0L10 0L10 10Z"/></svg>', encoding='utf-8')
        outputs = overlay.compose(self.spec, self.root)
        self.assertIn('data-paper-shadow', outputs['composite'].read_text(encoding='utf-8'))
        printed = outputs['print'].read_text(encoding='utf-8')
        self.assertNotIn('data-paper-shadow', printed)
        self.assertIn('chip-shape', printed)
        self.assertNotIn('<image', printed)

    def test_vector_base_cannot_smuggle_text_or_external_resources(self):
        del self.spec['base_image']
        self.spec['base_svg'] = 'base.svg'
        for body in ('<text>数字</text>', '<image href="remote.png"/>', '<rect style="fill:url(remote.svg)"/>'):
            (self.root / 'base.svg').write_text('<svg viewBox="0 0 1448 1086">' + body + '</svg>', encoding='utf-8')
            with self.assertRaises(ValueError):
                overlay.compose(self.spec, self.root)


if __name__ == "__main__":
    unittest.main()
