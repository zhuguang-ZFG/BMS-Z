"""Catch readable-looking PDF figures whose copied numbers are corrupted."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_reading_sketches as checks  # noqa: E402


class ReadingSketchOutputTests(unittest.TestCase):
    def test_exact_numbers_and_same_page_caption_are_required(self):
        entry = {'drawing':'sample', 'title':'Reading', 'asset':'sample.svg',
                 'caption':'Caption', 'question':'Question'}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'sample.svg').write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><text>3.16 V</text></svg>', encoding='utf-8')
            for value, caption_on_next, expected_error in [
                ('3.16 V', False, None),
                ('M.KP V', False, '3.16 V'),
                ('3.16 V', True, 'Caption'),
            ]:
                with self.subTest(value=value, caption_on_next=caption_on_next):
                    output = root/'proof.pdf'
                    with fitz.open() as pdf:
                        page = pdf.new_page()
                        page.insert_text((30,30), 'Reading\n'+value+'\nQuestion')
                        if caption_on_next:
                            page = pdf.new_page()
                        page.insert_text((30,90), 'Caption')
                        pdf.save(output)
                    with patch.object(checks, 'ROOT', root):
                        if expected_error:
                            with self.assertRaisesRegex(ValueError, expected_error):
                                checks.check_pdf(output, [entry])
                        else:
                            self.assertEqual(checks.check_pdf(output, [entry])[0]['page'], 1)


if __name__ == '__main__':
    unittest.main()
