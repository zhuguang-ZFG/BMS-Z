#!/usr/bin/env python3
"""把全库口诀汇总成 docs/口诀速查.md。

生成逻辑在 .github/scripts/check_docs.py 的 build_koujue_page()——检查器每次
跑的时候都会重算一遍并与入库版本比对，正文里口诀增改之后没重新生成，CI 直接
红灯。本脚本只是那个函数的命令行入口：

    python3 tools/gen_koujue_index.py            # 生成/覆盖 docs/口诀速查.md
    python3 tools/gen_koujue_index.py --check    # 只比对，不同步则退出码 1
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".github" / "scripts"))
from check_docs import KOUJUE_PAGE, ROOT, build_koujue_page  # noqa: E402


def main() -> int:
    page = build_koujue_page()
    target = ROOT / KOUJUE_PAGE
    if "--check" in sys.argv:
        if target.exists() and target.read_text(encoding="utf-8") == page:
            print("ok: 口诀速查页与正文口诀同步")
            return 0
        print("FAIL: 口诀速查页与正文口诀不同步，去掉 --check 重新生成")
        return 1
    target.write_text(page, encoding="utf-8", newline="\n")
    print(f"OK {KOUJUE_PAGE} {page.count(chr(10))} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
