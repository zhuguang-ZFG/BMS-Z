"""OS02 加性探针：核对 PyBOP 26.10 与固定 notebook（316b28d）ECM 流程的可复现性。

结论只作登记证据：S2 标准库基准（os02_ecm_benchmark.py）始终是验收基线。
"""
import json
import platform
from pathlib import Path

EVIDENCE = Path(__file__).parent / "evidence" / "os02-pybop-probe.json"

TRUE = {"OCV": 3.700, "R0": 0.010, "R1": 0.030, "C1": 2000.0, "R2": 0.015, "C2": 40000.0}


def main():
    import pybop

    result = {
        "source_id": "OS02",
        "probe": "PyBOP 26.10 加性对照：验证固定 notebook(316b28d) 的多脉冲 ECM 流程可否在本环境复现",
        "python": platform.python_version(),
        "pybop_version": pybop.__version__,
    }

    # 1) 模型清单：26.10 是否还提供经验 ECM/Thevenin
    import pybop.models as models

    result["model_families"] = sorted(
        m.name for m in __import__("pkgutil").iter_modules(models.__path__)
    )
    try:
        from pybop.models import Thevenin  # noqa: F401

        result["thevenin_available"] = True
    except ImportError:
        result["thevenin_available"] = False
    result["notebook_ecm_path_reproducible"] = result["thevenin_available"]
    result["note"] = (
        "pybop 26.10 models 仅含 "
        + ", ".join(result["model_families"])
        + "；固定 notebook(v25.x 时代)的 Thevenin ECM 流程在 26.10 已不可复现"
        "（与研究文档 'v25.10前后API重构，不得混用旧教程' 一致）。"
        "S2 标准库基准 os02_ecm_benchmark.py 为验收基线，本探针仅作环境事实登记。"
    )

    # 2) 与 S2 同合成数据的量级对照：用 pybop 自带例模型成本接口不可行（无 ECM），
    #    故以 S2 基准自身结果为准，此处只记录 pybop 可导入、版本与模型清单。
    result["acceptance_baseline"] = "code/research-closure/evidence/os02-ecm-benchmark.json"
    result["mendeley_license_check"] = {
        "status": "pending",
        "reason": "notebook 原始 Mendeley 数据集本地未取得，快照文档无数据集标识；"
                  "许可核验需先定位数据集条目，不得凭notebook示例图推断",
    }

    EVIDENCE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
