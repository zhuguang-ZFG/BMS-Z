"""第 1 期 SOC 擂台的读者入口。

把类名留给 ``MyEstimator``。评分脚本这样跑::

    python3 challenges/01-soc/score.py --estimator challenges/01-soc/my_estimator.py:MyEstimator

接口
----
- ``__init__(self)`` 不要参数。公开题面在 ``score.py`` 顶部：假定容量 9.5 Ah，
  估计器初始 SOC 0.7。模型容量 10 Ah、模型初始 0.8 是出题用的，写进估计器
  就等于偷看答案的起点。
- ``step(self, current_a, v_meas, dt_s) -> float`` 返回这一步结束时的 SOC。
  充电电流为正。单位是 A、V、s。
- 不要读真值轨迹。评分脚本不会把它传进来。

下面这个类就是纯安时积分，和基线同一条公式，所以档位是「未胜过基线」。
把它换成你自己的递推，再跑上面的命令。

交作业：插件文件，加上讨论区「打卡」一帖
（https://github.com/zhuguang-ZFG/BMS-Z/discussions ，分类选打卡），
或者用 Issue 模板「共学打卡」。第 1 期 2026-10-06 开始，2026-11-02 结束。
"""
from __future__ import annotations

import numpy as np

# 和 score.py 公开题面一致。改这里等于改你的估计器，不是改评分。
SOC0 = 0.70
Q_AH = 9.5


class MyEstimator:
    """教学模板：只做安时积分，电压只收下、不用。"""

    def __init__(self) -> None:
        self.soc = SOC0
        self.q_ah = Q_AH

    def step(self, current_a: float, v_meas: float, dt_s: float) -> float:
        del v_meas
        self.soc += current_a * (dt_s / 3600.0) / self.q_ah
        self.soc = float(np.clip(self.soc, 0.0, 1.0))
        return self.soc
