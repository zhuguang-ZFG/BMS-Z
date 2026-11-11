#!/usr/bin/env python3
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_chapter_contract  # noqa: E402

VALID = """<a id="ch1"></a>
## 第 1 章 无源元件的真实面目

<!-- slot:hook -->
### 1.1 钩子现象
灯一闪。

<!-- slot:intuition -->
### 1.2 直觉
先想回路。

<!-- slot:quant -->
### 1.3 定量推导
> **口诀**：电阻吃电压。
**算一笔**：R = 1 kΩ，V = 5 V，则 I = 5 mA。

<!-- slot:limits -->
### 1.4 失效边界
频率高了模型崩。

<!-- slot:lab -->
### 1.5 动手验证
<figure><img src="assets/figures/ch01-hero-parasitics.svg"></figure>
> **图问**：图中寄生从哪一端先夺权？

<!-- slot:selfcheck -->
### 1.6 自检
### 验收清单
- [ ] 观察：摸温度
- [ ] 计算：算 τ
- [ ] 测量：示波器看波形
"""


class ChapterContractTests(unittest.TestCase):
    def test_valid_fixture_all_true(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ch.md"
            p.write_text(VALID, encoding="utf-8")
            result = check_chapter_contract.scan_chapter(p)
            self.assertTrue(all(result.values()), result)

    def test_empty_file_all_false(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "ch.md"
            p.write_text("", encoding="utf-8")
            result = check_chapter_contract.scan_chapter(p)
            self.assertFalse(any(result.values()), result)

    def test_v2_chapter_hero_counts_but_photos_alone_do_not(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ch.md'
            for directory in ['figures-v2','svg-v2']:
                p.write_text(VALID.replace('assets/figures/',f'assets/{directory}/'),encoding='utf-8')
                self.assertTrue(check_chapter_contract.scan_chapter(p)['hero_fig'])
            p.write_text(VALID.replace('assets/figures/','assets/photos/'),encoding='utf-8')
            self.assertFalse(check_chapter_contract.scan_chapter(p)['hero_fig'])

    def test_curriculum_map_lists_all_19_chapter_files(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "docs/superpowers/curriculum/2026-11-03-zero-to-engineer-map.md").read_text(encoding="utf-8")
        for name in [
            "p1-01-ch0.md", "p1-02-ch1.md", "p1-03-ch2.md", "p1-04-ch3.md", "p1-05-ch4.md",
            "p1-06-ch5.md", "p1-07-ch6.md", "p1-08-ch7.md", "p1-09-ch8.md", "p1-10-ch9.md",
            "p1-11-ch10.md", "p2-01-ch11.md", "p2-02-ch12.md", "p2-03-ch13.md", "p3-01-ch14.md",
            "p3-02-ch15.md", "p4-01-ch16.md", "p4-02-ch17.md", "p4-03-ch18.md",
        ]:
            self.assertIn(name, text)


if __name__ == "__main__":
    unittest.main()
