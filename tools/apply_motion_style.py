#!/usr/bin/env python3
"""把 ``motion_style`` 的注记层应用到 docs/circuits/assets/ 的手写动画。

生成器产出的 32 张由 ``gen_mechanism_svgs.py`` 在 ``wrap()`` 里自动装饰；
这里默认刷新：先剥离既有 bms 层再按当前样式重插，改过装饰代码后重跑即可。
运行（仓库根目录）：

    python tools/apply_motion_style.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "circuits" / "assets"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import motion_style  # noqa: E402


def main() -> None:
    changed = 0
    total = 0
    for path in sorted(ASSETS.glob("*.svg")):
        source = path.read_text(encoding="utf-8")
        decorated = motion_style.decorate(source, refresh=True)
        total += 1
        if decorated == source:
            continue
        path.write_text(decorated, encoding="utf-8", newline="\n")
        changed += 1
    print(f"motion style applied: {changed}/{total} files changed")


if __name__ == "__main__":
    main()
