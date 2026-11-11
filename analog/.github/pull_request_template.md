## 这次改了什么

<!-- 一句话说清动机。如果是修错，直接引原文那一段。 -->

## 类型

- [ ] 📝 内容纠错（错别字 / 公式 / 事实 / 链接）
- [ ] ➕ 新增主题小节
- [ ] 🎬 新增或修改动画（`scripts/generate_svgs.py` + `assets/svg/`）
- [ ] 🧩 新增实物图 / datasheet / 视频资源
- [ ] 🧪 新增自测题
- [ ] ⚙️ 工程化（脚本 / CI / 站点）

## 自查清单（CI 会重复检查一遍）

- [ ] **只改了 `docs/`**（以及 `scripts/`、`assets/svg/`、`.github/`），`README.md` 是跑脚本生成的
- [ ] 跑过 `python scripts/build_readme.py`，`README.md` 已同步
- [ ] 若动了 `scripts/generate_svgs.py`，跑过 `python scripts/generate_svgs.py` 重新生成全部 SVG
- [ ] 新增跨页链接用的是 `pN-MM-slug.md#anchor` 形式，且目标锚点真实存在
- [ ] 本地四项检查通过：
      `python -B -m unittest discover -s scripts -p "test_docs_sync.py"`
      `python -B -m unittest discover -s scripts -p "test_docs_links.py"`
      `python -B -m unittest discover -s scripts -p "test_readme_links.py"`
      `python -B -m unittest discover -s scripts -p "test_svg_assets.py"`
- [ ] 新增外链已在浏览器里点开确认不是 404（CI 的 lychee 也会查，但先自查能省一轮）

## 依据 / 参考

<!-- 教材页码、datasheet 型号+页码、实测截图、参考链接……有依据的改动才可靠。 -->

## 相关 Issue

<!-- Closes #123 -->
