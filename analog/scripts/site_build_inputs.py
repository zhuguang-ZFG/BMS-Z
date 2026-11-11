"""站点构建输入的清单 + 临时副本工具（四个浏览器测试共用）。

`scripts/build_site.py` 的输入不止 `docs/`：章首手绘章徽读的是
`analog-book/static/illustrations/chNN.svg`。test_calcs / test_diagnostic /
test_first_screen / test_reading_journey 各自把仓库子集复制到临时目录再构建，
少复制一样就直接 FileNotFoundError（章徽波实测踩过）。
输入清单集中在这里：以后 build_site 再读新的仓库路径，只改本文件一处。
"""
import shutil
from pathlib import Path

BUILD_DIRS = ('docs', 'assets', 'scripts', 'analog-book/static/illustrations',
              'analog-book/fonts')
BUILD_ROOT_FILES = ('CONTRIBUTING.md', 'CONTRIBUTORS.md', 'LICENSE')
_IGNORE = shutil.ignore_patterns('__pycache__', '_probe*')


def copy_build_inputs(root, work):
    """把 build_site.py 需要的仓库内容复制到临时工作目录 work。"""
    root, work = Path(root), Path(work)
    for rel in BUILD_DIRS:
        shutil.copytree(root / rel, work / rel, ignore=_IGNORE)
    for rel in BUILD_ROOT_FILES:
        shutil.copyfile(root / rel, work / rel)
