"""compare.py --plot 分支的冒烟测试。运行：cd code/soc && python3 -m pytest tests/ -q

matplotlib 大版本升级把出图跑挂时，只跑 compare.py 的 CI 步骤发现不了
（默认不带 --plot）；这里单独锁住出图路径。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

COMPARE = Path(__file__).resolve().parents[1] / "compare.py"


def test_plot_flag_writes_png(tmp_path):
    """--plot 必须在 cwd 下产出 soc_comparison.png（脚本按相对路径保存）。"""
    proc = subprocess.run(
        [sys.executable, str(COMPARE), "--plot"],
        cwd=tmp_path, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "soc_comparison.png").exists(), proc.stdout
