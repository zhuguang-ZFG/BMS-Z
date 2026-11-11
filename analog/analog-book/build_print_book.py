#!/usr/bin/env python3
"""16K 印刷书入口：实现位于 analog-book/book/cli.py。"""
import sys
from pathlib import Path

BOOK_DIR = Path(__file__).resolve().parent
if str(BOOK_DIR) not in sys.path:
    sys.path.insert(0, str(BOOK_DIR))

from book.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
