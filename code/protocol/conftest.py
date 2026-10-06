# 同 code/soc/conftest.py：兜底让仓库根裸跑 pytest code/protocol 时能导入包内模块。
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
