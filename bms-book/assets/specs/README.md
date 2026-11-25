# 可编辑图解源

`communication-diagnostic-route.json` 是第 19 章排障路线图的 FigureSpec 源。改布局或文字时改 JSON，再生成 SVG；不手改生成结果。

渲染器来自 [ARIS](https://github.com/wanshuiyin/auto-claude-code-research-in-sleep/tree/3fefd34146d3317e407aec65a5a29335de87b9ee)，MIT，固定提交 `3fefd34146d3317e407aec65a5a29335de87b9ee` 的 `skills/figure-spec/scripts/figure_renderer.py`。安装 Codex `figure-spec` 后，把该文件放到技能的 `scripts/` 目录；保留上游 LICENSE。仓库脚本先核验渲染器 SHA-256，再渲染并从 JSON 添加 title/desc 无障碍描述。运行环境：Python 3.10+，无需网络或额外 Python 包。

```sh
python tools/render_book_figurespec.py bms-book/assets/specs/communication-diagnostic-route.json bms-book/assets/communication-diagnostic-route.svg --renderer /path/to/figure-spec/scripts/figure_renderer.py
```

图中内容与布局为本项目原创，沿用本书许可。证据范围见第 19 章参考资料；图示不代表硬件实测。
