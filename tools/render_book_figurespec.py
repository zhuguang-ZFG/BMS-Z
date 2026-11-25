"""Render an authored FigureSpec with the reviewed, pinned ARIS renderer.

The upstream helper is installed separately; this tool never downloads code.
"""

import argparse
import hashlib
import importlib.util
import json
from html import escape
from pathlib import Path


RENDERER_SHA256 = "02b4e01e46b51aeca12722ddd7b21bb7da3c3b175bba5d129c45d671fb07a0bc"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--renderer", type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.renderer.read_bytes()).hexdigest() != RENDERER_SHA256:
        parser.error("renderer differs from the reviewed ARIS commit; review before updating the hash")
    module_spec = importlib.util.spec_from_file_location("aris_figure_renderer", args.renderer)
    renderer = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(renderer)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    issues = renderer.validate_spec(spec)
    if issues:
        parser.error("\n".join(issues))
    title = escape(spec["title"])
    desc = escape(spec["description"])
    svg = renderer.render_svg(spec)
    svg = svg.replace("<svg ", '<svg role="img" aria-labelledby="figure-title figure-desc" ', 1)
    end = svg.index(">") + 1
    svg = svg[:end] + f'\n  <title id="figure-title">{title}</title>\n  <desc id="figure-desc">{desc}</desc>' + svg[end:]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg.rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"Rendered {args.output}")


if __name__ == "__main__":
    main()
