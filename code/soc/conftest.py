# 让「在仓库根裸跑 pytest code/soc」也能导入包内模块：pytest 默认把测试
# 文件所在目录插进 sys.path，但从仓库根收集时包目录不在其中。CI 的
# python -m pytest（cwd=code/soc）不受影响，这里只是兜底。
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
