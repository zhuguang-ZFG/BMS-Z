"""Render the three mechanism trials required by SPEC-v3 section 6.2.

These are source-authored engineering drawings, not image-model schematics.
S1/S3 trials validate the visual language only; they do not mark those chapters
or their experiments complete. Quantitative S2 figures share this same renderer.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
IDENTIFICATION = ROOT / "code/engineering/identification"
sys.path.insert(0, str(IDENTIFICATION))
spec = importlib.util.spec_from_file_location("make_s2_figures", IDENTIFICATION / "make_s2_figures.py")
if spec is None or spec.loader is None:
    raise RuntimeError("S2 figure renderer unavailable")
fig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fig)
OUT = ROOT / "bms-book/engineering/assets/style-trials"


def line(x1: int, y1: int, x2: int, y2: int, cls: str = "wire") -> str:
    return f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'


def dot(x: int, y: int) -> str:
    return f'<circle class="node" cx="{x}" cy="{y}" r="3.5"/>'


def s1_signal_chain() -> str:
    parts = [
        fig.text(24, 32, "S1 信号链试版：端子、转换、数据质量与反馈", "title"),
        fig.text(24, 66, "蓝实线是模拟连接，虚线是数字数据；RC 支路与 ADC 共用明确的负参考。", "sub"),
        # Cell and input RC. The capacitor is a shunt after the input resistor.
        line(80, 150, 170, 150), line(80, 150, 80, 202),
        line(60, 202, 100, 202, "plate"), line(68, 220, 92, 220, "plate"),
        line(80, 220, 80, 310), line(80, 310, 380, 310),
        '<rect class="r0" x="170" y="137" width="60" height="26"/>',
        line(230, 150, 340, 150), dot(270, 150),
        line(270, 150, 270, 206), line(250, 206, 290, 206, "plate"),
        line(250, 224, 290, 224, "plate"), line(270, 224, 270, 310), dot(270, 310),
        fig.text(80, 126, "+ 端子", "lbl", "middle"),
        fig.text(80, 340, "− 参考", "lbl", "middle"),
        fig.text(200, 126, "输入电阻", "lbl", "middle"),
        fig.text(292, 219, "滤波电容", "lbl"),
        '<rect class="load" x="340" y="126" width="110" height="52" rx="3"/>',
        fig.text(395, 157, "采样 / ADC", "lbl", "middle"),
        line(380, 178, 380, 310),
        fig.text(350, 340, "同一参考点", "lbl", "middle"),
        line(450, 150, 500, 150, "dash"),
        '<polygon class="node" points="500,150 490,145 490,155"/>',
        '<rect class="load" x="500" y="110" width="230" height="88" rx="3"/>',
        fig.text(615, 139, "读数 · 有效位 · 时刻", "eq", "middle"),
        fig.text(615, 175, "标定后仍须检查质量和年龄", "small", "middle"),
        line(615, 198, 615, 258, "dash"),
        '<polygon class="node" points="615,258 610,248 620,248"/>',
        fig.text(615, 286, "保护判决 / 确认计数", "lbl", "middle"),
        fig.text(24, 382, "动作链不是同一瞬间", "eq"),
        fig.text(90, 420, "采样窗口", "lbl", "middle"),
        fig.text(285, 420, "确认计数", "lbl", "middle"),
        fig.text(480, 420, "执行命令", "lbl", "middle"),
        fig.text(680, 420, "实际反馈", "lbl", "middle"),
        line(145, 414, 225, 414, "dash"), line(340, 414, 420, 414, "dash"),
        line(535, 414, 620, 414, "dash"),
        fig.text(24, 470, "试版边界：仅核对信号连接和视觉语言；不构成 S1 实验、时限或器件精度验收。", "small"),
    ]
    return fig.svg(800, 490, "S1 信号链视觉试版", "电芯正端经输入电阻到采样ADC，电容从采样节点接至负参考；ADC输出数字读数、有效性与时间，再进入保护判决和执行反馈。", "\n".join(parts))


def s3_power_path() -> str:
    parts = [
        fig.text(24, 32, "S3 功率回路试版：先经预充电阻，不走主闸", "title"),
        fig.text(24, 66, "当前只画预充阶段：预充触点闭合、主触点断开，外部负载已卸；回流明确接回负端。", "sub"),
        '<circle class="wire" cx="70" cy="300" r="30"/>',
        fig.text(70, 298, "+", "sym", "middle"), fig.text(70, 321, "−", "sym", "middle"),
        line(70, 270, 70, 210), line(70, 330, 70, 390),
        line(70, 210, 230, 210), line(330, 210, 620, 210),
        line(230, 210, 316, 178), dot(230, 210), dot(330, 210),
        fig.text(282, 245, "主触点 Km：断", "lbl", "middle"),
        # Precharge branch taps the same two nodes on either side of Km.
        line(170, 210, 170, 120), line(170, 120, 225, 120),
        line(225, 120, 285, 120), dot(225, 120), dot(285, 120),
        line(285, 120, 350, 120),
        '<rect class="r0" x="350" y="107" width="80" height="26"/>',
        line(430, 120, 470, 120), line(470, 120, 470, 210),
        dot(170, 210), dot(470, 210),
        fig.text(252, 94, "预充触点 Kp：合", "lbl", "middle"),
        fig.text(390, 94, "预充电阻", "lbl", "middle"),
        line(620, 210, 620, 285), line(600, 285, 640, 285, "plate"),
        line(600, 305, 640, 305, "plate"), line(620, 305, 620, 390),
        line(620, 390, 70, 390),
        fig.text(650, 302, "母线电容", "lbl"),
        fig.text(112, 353, "电池组", "lbl"),
        # Arrow marks follow, rather than substitute for, the closed physical path.
        '<polygon class="node" points="320,120 310,114 310,126"/>',
        '<polygon class="node" points="620,263 614,253 626,253"/>',
        '<polygon class="node" points="430,390 440,384 440,396"/>',
        fig.text(24, 437, "电流路径：正端 → Kp → 电阻 → 电容 → 负端", "eq"),
        fig.text(24, 470, "合主闸还要另查：采样有效、反馈一致、压差与器件限制；电容电压高不等于已获许可。", "small"),
        fig.text(24, 494, "试版边界：仅核对物理回路与视觉；不是高压搭建指南，也不是 S3 实验完成证据。", "small"),
    ]
    return fig.svg(800, 514, "S3 预充功率路径视觉试版", "电池正端分出主触点支路与预充触点加电阻的并联支路，预充支路闭合而主触点断开，电流经电阻给母线电容充电，并从电容负端回到电池负端。", "\n".join(parts))


def main() -> None:
    targets = {
        "S1-signal-chain-trial.svg": s1_signal_chain(),
        "S2-equivalent-circuit-trial.svg": fig.f1_circuit(),
        "S3-power-path-trial.svg": s3_power_path(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, source in targets.items():
        (OUT / name).write_text(source, encoding="utf-8")
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()
