"""从 D13 的合成回放报告重建新息诊断图。"""
import argparse
from io import StringIO
from pathlib import Path

import matplotlib as mpl
from matplotlib.figure import Figure

import d13_ekf


OUT = Path(__file__).resolve().parents[3] / "bms-book/engineering/assets/d13-ekf"
FILENAME = "D13-F3-innovation-checks.svg"


def diagnostic_figure(report: dict) -> str:
    control, flat = report["whitening"], report["boundary"]["whitening"]
    ink, muted, alert = "#1d3848", "#526b78", "#953e21"
    with mpl.rc_context({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "svg.hashsalt": "d13-innovation"}):
        fig = Figure(figsize=(4.8, 3.25), facecolor="white")
        axes = fig.subplots(2)
        fig.subplots_adjust(left=0.19, right=0.95, top=0.88, bottom=0.13, hspace=1.05)
        for ax, title, ticks, origin in zip(
            axes, ("Σ NIS / n", "r₁"), ((0, 0.5, 1, 1.5, 2), (-0.5, -0.25, 0, 0.25, 0.5)),
            (1, 0), strict=True,
        ):
            ax.set_title(title, loc="left", fontsize=13, color=ink, fontweight="bold")
            ax.set_xlim(ticks[0], ticks[-1])
            ax.set_xticks(ticks, [f"{x:g}" for x in ticks])
            ax.set_ylim(-0.4, 1.5)
            ax.set_yticks((1, 0), [f"n = {s['n']}" for s in (control, flat)])
            ax.tick_params(axis="both", colors=muted, labelsize=10, length=0, pad=5)
            ax.spines[:].set_visible(False)
            ax.spines["bottom"].set_visible(True)
            ax.spines["bottom"].set_color("#abb8bc")
            ax.axvline(origin, color="#aab5b7", linestyle=":", linewidth=1)

        for row, sample in zip((1, 0), (control, flat), strict=True):
            n, limit = sample["n"], sample["ar1_limit"]
            intervals = ((sample["chi2_95_low"] / n, sample["chi2_95_high"] / n),
                         (-limit, limit))
            for key, ax, (low, high), value, inside in zip(
                ("nis", "ar1"), axes, intervals, (sample["nis_mean"], sample["ar1"]),
                (sample["within_95"], sample["ar1_within_limit"]), strict=True,
            ):
                ax.plot([low, high], [row, row], color=muted, linewidth=2,
                        marker="|", markersize=8, gid=f"{key}-{n}-band")
                color = ink if inside else alert
                ax.plot(value, row, marker="o" if inside else "D", color=color,
                        markeredgecolor="white", markeredgewidth=0.8, markersize=7,
                        gid=f"{key}-{n}-point")
                ax.annotate(f"{value:.4f}", (value, row), xytext=(0, 6),
                            textcoords="offset points", ha="center", color=color, fontsize=10)

        title = "两段合成回放的新息平方均值与一阶自相关"
        desc = (f"两组 NIS 均值都在各自的参考区间内。平坦区的 {flat['n']} 次观测中，"
                f"一阶自相关 {flat['ar1']:.4f} 超出参考上界 {flat['ar1_limit']:.4f}。")
        buf = StringIO()
        fig.savefig(buf, format="svg", metadata={"Title": title, "Date": None})
    svg = buf.getvalue().replace("</title>", f"</title>\n <desc>{desc}</desc>", 1)
    return "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out", type=Path, default=OUT)
    out = cli.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    (out / FILENAME).write_text(diagnostic_figure(d13_ekf.build_report()),
                                encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
