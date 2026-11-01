#!/usr/bin/env python3
"""Securely prompt for a MiMo API key and write the ignored local config file."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = ROOT / ".local" / "mimo.env"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--base-url", default="https://api.xiaomimimo.com/v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        configured = args.out.is_file() and any(
            line.startswith("MIMO_API_KEY=") and line.partition("=")[2].strip()
            for line in args.out.read_text(encoding="utf-8").splitlines()
        )
        print(f"MiMo 本机配置：{'已就绪' if configured else '未配置'}（{args.out}）")
        return 0 if configured else 1

    key = getpass.getpass("MiMo API key（输入不回显）：").strip()
    if not key:
        parser.error("密钥不能为空")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        f"MIMO_API_KEY={key}\nMIMO_BASE_URL={args.base_url.rstrip('/')}\n",
        encoding="utf-8",
        newline="\n",
    )
    try:
        os.chmod(args.out, 0o600)
    except OSError:
        pass
    print(f"MiMo 密钥已写入本机忽略文件：{args.out}（未显示密钥）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
