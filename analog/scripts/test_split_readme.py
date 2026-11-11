"""Regression coverage for the migration that originally stranded heading anchors."""
import unittest

from split_readme import split_sections


class SplitSectionsTests(unittest.TestCase):
    def test_pre_heading_anchors_move_with_their_heading(self):
        sections = split_sections([
            '# Guide', 'Introduction', '', '<a id="part1"></a>', '',
            '# 第一篇', 'Overview', '<a id="ch0"></a>', '## 第 0 章', 'Content',
        ])
        self.assertEqual(3, len(sections))
        self.assertNotIn('<a id="part1"></a>', sections[0][1])
        self.assertIn('<a id="part1"></a>', sections[1][1])
        self.assertNotIn('<a id="ch0"></a>', sections[1][1])
        self.assertIn('<a id="ch0"></a>', sections[2][1])

    def test_code_headings_and_gallery_entries_stay_in_their_section(self):
        sections = split_sections([
            '# Guide', '```markdown', '# example', '## example', '```',
            '# 第五篇', '## 5.1 Animation', 'Description',
        ])
        self.assertEqual(2, len(sections))
        self.assertIn('# example', sections[0][1])
        self.assertIn('## example', sections[0][1])
        self.assertIn('## 5.1 Animation', sections[1][1])


if __name__ == '__main__':
    unittest.main()
