import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_visual_contact_sheet as sheet


class ContactSheetTests(unittest.TestCase):
    def test_nested_destination_uses_real_relative_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            asset = root / "assets/a.svg"
            asset.parent.mkdir()
            asset.write_text("<svg/>", encoding="utf-8")
            destination = root / "docs/reviews/nested/index.html"
            with patch.object(sheet, "ROOT", root):
                card = sheet.card({"id": "a", "chapter": 0, "type": "V3", "kind": "figure",
                                   "layout_id": "IG-015", "status": "planned", "technical_proof": "assets/a.svg"}, destination)
            self.assertIn('../../../assets/a.svg', card)
            self.assertIn('仅技术校样', card)
            self.assertIn('待评', card)

    def test_missing_asset_is_pending_without_broken_image(self):
        card = sheet.card({"id": "a", "chapter": 0, "type": "V3", "kind": "figure",
                           "layout_id": "IG-015", "status": "planned", "output": "missing.svg"}, Path("review.html"))
        self.assertNotIn('<img', card)
        self.assertIn('待生成', card)


if __name__ == "__main__":
    unittest.main()
