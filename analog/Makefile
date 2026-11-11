PY ?= python
export PYTHONIOENCODING := utf-8

.PHONY: readme gen bookdata labs fonts site book book-pdf epub book-check print-book print-volumes remake-check remake-ship test-static test-browser verify stats clean visual-audit visual-gray visual-ship
.PHONY: visual-check

readme:
	$(PY) scripts/build_readme.py

# docs/ 是唯一内容源，下面四样产物都从它派生；改完 docs/ 必须一起重生，
# 否则 CI 里的对账测试（README、实验包 zip、字体子集缺字、animations.yml）必然红灯。
# fonts 需要源字体：首次先跑 `python scripts/subset_fonts.py --download`（要联网）。
gen: readme bookdata labs fonts

bookdata:
	$(PY) scripts/build_book_data.py --write

labs:
	$(PY) scripts/build_lab_packages.py

fonts:
	$(PY) scripts/subset_fonts.py --build

site:
	$(PY) scripts/build_site.py --build

book:
	$(PY) analog-book/build_book.py

book-pdf:
	$(PY) analog-book/build_book.py --pdf

epub:
	$(PY) scripts/build_epub.py

book-check:
	$(PY) analog-book/build_book.py --check --no-build

print-book:
	$(PY) analog-book/build_print_book.py --no-build

# 16K 单卷 812 页超过 700 页硬上限：印刷版按自然篇界出上下卷，
# 每卷自带前置页、目录、插图/表格目录与本卷索引，参考文献与索引两卷都带。
print-volumes:
	$(PY) analog-book/build_print_book.py --volumes --pdf --no-build

# 整包重做（2026-11-03）两道内容闸：套话扫描 + 章节契约。
remake-check:
	$(PY) -B -m unittest discover -s scripts -p 'test_ai_slop.py' -v
	$(PY) -B -m unittest discover -s scripts -p 'test_chapter_contract.py' -v

# 整包重做总闸：任一线未绿不得宣称整包完成；通过后仍不自动 push，发布走既有 pages 门禁。
remake-ship: remake-check
	$(PY) scripts/check_ai_slop.py docs/p1-01-ch0.md docs/p1-02-ch1.md docs/p1-03-ch2.md \
	  docs/p1-04-ch3.md docs/p1-05-ch4.md docs/p1-06-ch5.md docs/p1-07-ch6.md docs/p1-08-ch7.md \
	  docs/p1-09-ch8.md docs/p1-10-ch9.md docs/p1-11-ch10.md docs/p2-01-ch11.md docs/p2-02-ch12.md \
	  docs/p2-03-ch13.md docs/p3-01-ch14.md docs/p3-02-ch15.md docs/p4-01-ch16.md docs/p4-02-ch17.md \
	  docs/p4-03-ch18.md
	$(PY) scripts/check_references.py analog-book/data/references.yml analog-book/data/sources.yml
	$(PY) -B -m unittest discover -s scripts -p 'test_svg_count_floor.py' -v
	$(PY) -B -m unittest discover -s scripts -p 'test_ship_residual.py' -v
	$(PY) scripts/check_ship_residual.py
	$(PY) scripts/build_book_data.py --check
	$(PY) scripts/build_lab_packages.py --check
	$(PY) scripts/subset_fonts.py --check
	$(PY) scripts/build_readme.py --check

test-static:
	$(PY) -B -m unittest discover -s scripts -p "test_epub.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_svg_assets.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_readme_links.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_a11y.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_docs_sync.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_docs_links.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_split_readme.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_page_structure.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_release_gate.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_publish_a4_book.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_publish_book.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_site_build.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_smartsymbols.py" -v
	$(PY) -B -m unittest discover -s analog-book/tests -p "test_build.py" -v

# 视觉密度与 manifest 闸：报告模式永远退出 0，闸模式在未改造章节上按设计失败。
visual-audit:
	$(PY) -B scripts/audit_visual_density.py

visual-gray:
	$(PY) -B scripts/make_grayscale_fixture.py --check
	$(PY) -B -m unittest discover -s scripts -p "test_grayscale_fixture.py"

visual-check:
	$(PY) -B scripts/check_visual_manifest.py
	$(PY) -B -m unittest discover -s scripts -p "test_visual_release.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_visual_calculations.py" -v
	$(PY) -B -m pytest scripts/test_pcb_visual_units.py scripts/test_design_visual_models.py -q
	$(PY) -B -m unittest discover -s scripts -p "test_visual_density.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_visual_distribution.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_visual_manifest.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_visual_fidelity.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_handraw_prompt_records.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_technical_overlay.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_papercut_figures.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_visual_contact_sheet.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_backlog_layout.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_visual_builder_review.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_visual_text_replacement.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_insert_visuals.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_animation_v2.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_animation_review.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_label_handraw_figures.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch02_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch03_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch04_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch05_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch06_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch07_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch09_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch10_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch11_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch12_animations.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_ch13_animations.py" -v
	$(PY) -B -m unittest discover -s analog-book/tests -p "test_visual_v2_assets.py" -v

visual-ship: visual-check
	$(PY) -B scripts/check_visual_release.py
	$(PY) -B scripts/audit_visual_density.py --gate

test-browser:
	$(PY) -B -m unittest discover -s scripts -p "test_visual_player.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_reading_journey.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_diagnostic.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_gallery_interactions.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_learning_interactions.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_waveform_timing.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_svg_layout.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_svg_contrast.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_reduced_motion.py" -v
	$(PY) -B -m unittest discover -s scripts -p "test_first_screen.py" -v
	$(PY) -B -m unittest discover -s analog-book/tests -p "test_browser_book.py" -v

verify: test-static
	$(PY) scripts/build_readme.py --check
	$(PY) scripts/build_book_data.py --check
	$(PY) scripts/build_lab_packages.py --check
	$(PY) scripts/subset_fonts.py --check
	$(PY) analog-book/build_book.py
	$(PY) analog-book/build_book.py --check --no-build

stats:
	$(PY) scripts/build_stats.py

clean:
	$(PY) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in (pathlib.Path('build'), pathlib.Path('analog-book/dist'))]"
	$(PY) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in list(pathlib.Path('.').rglob('__pycache__'))]"
