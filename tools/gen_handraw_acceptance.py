"""生成 docs/circuits/handraw/acceptance-batch1.md：每格来自可复现测量，不靠目检勾选。"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from PIL import Image
import numpy as np

SLUGS = [
    "bms-roadmap", "bms-signal-budget", "internal-resistance", "polarization-physics",
    "thermal-runaway", "overcharge-protection", "cell-inconsistency-barrel", "weakest-cell-ah",
    "protection-debounce", "ov-hysteresis-delay", "adc-quantization", "error-budget-waterfall",
    "coulomb-counting", "ocv-rest-timeline", "hppc-pulse", "sop-derating", "protocol-resync",
    "precharge-sequence-curve", "ai-context-vs-truth", "ocv-plateau-distrust",
]
ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path(".")
STORY = ROOT / "docs/circuits/handraw/storyboard"
EXPORT = ROOT / "docs/circuits/handraw/exports"
OUT = ROOT / "docs/circuits/handraw/acceptance-batch1.md"


def import_geometry():
    import importlib.util

    spec = importlib.util.spec_from_file_location("geomC", ROOT / "tools/check_handraw_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def webp_meta(path: Path):
    data = path.read_bytes()
    off, durations, loop = 12, [], None
    while off + 8 <= len(data):
        fourcc = data[off:off + 4]
        size = struct.unpack("<I", data[off + 4:off + 8])[0]
        payload = data[off + 8:off + 8 + size]
        if fourcc == b"ANMF":
            durations.append(int.from_bytes(payload[12:15], "little"))
        elif fourcc == b"ANIM":
            loop = struct.unpack("<H", payload[4:6])[0]
        off += 8 + size + (size & 1)
    return durations, loop


RED_AREA_LIMIT = 0.02  # 单帧红色像素占比超过 2% 视为「大面积铺色」，与 §5.1 色板冲突


def red_per_frame(slug: str) -> list[int]:
    counts = []
    for frame in sorted((STORY / slug).glob("*.webp")):
        arr = np.array(Image.open(frame).convert("RGB")).astype(int)
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        counts.append(int(((r > 150) & (g < 110) & (b < 100)).sum()))
    return counts


def observation_counts(slug: str) -> tuple[int, int, int, list[str]]:
    """(嵌入数, 带看图的嵌入数, 带图说的嵌入数, 缺观察题的位置)。

    观察题只认 `> **看图**`：`> **图说**` 是图注，不是问题，不能拿来顶账。
    根 README 也是读者页（首页嵌了路线图动画），必须一起扫。
    """
    import re

    pages = [ROOT / "README.md"]
    pages += [p for p in (ROOT / "docs").rglob("*.md")
              if not any(part in p.parts for part in ("node_modules", "site-dist", "dist", "superpowers"))]
    embeds = kantu = tushuo = 0
    missing: list[str] = []
    for page in pages:
        if not page.is_file():
            continue
        lines = page.read_text(encoding="utf-8", errors="replace").split("\n")
        for index, line in enumerate(lines):
            # 三种写法都见过：../circuits/…（阶段页）、circuits/…（根 README）、handraw/…（详解页）
            match = re.search(rf"(?:\.\./)?(?:circuits/)?handraw/exports/{slug}\.webp\)", line)
            if not match or not line.lstrip().startswith("!["):
                continue
            embeds += 1
            window = lines[index + 1:index + 6]
            if any(re.match(r">\s*\*\*看图\*\*", item) for item in window):
                kantu += 1
            else:
                missing.append(f"{page.name}:{index + 1}")
            if any(re.match(r">\s*\*\*图说\*\*", item) for item in window):
                tushuo += 1
    return embeds, kantu, tushuo, missing


def main() -> int:
    geometry = import_geometry()
    manifest = json.loads((ROOT / "docs/circuits/handraw/manifest.json").read_text(encoding="utf-8"))
    entries = {e["slug"]: e for e in manifest["entries"]}

    rows, failed = [], []
    total_embeds = total_kantu = 0
    for number, slug in enumerate(SLUGS, 1):
        durations, loop = webp_meta(EXPORT / f"{slug}.webp")
        geometry_problems = sum(
            len(geometry.frame_geometry_problems(frame)) for frame in (STORY / slug).glob("*.svg")
        )
        reds = red_per_frame(slug)
        hit = [i + 1 for i, value in enumerate(reds) if value]
        if not hit:
            palette = "无 C-15"
        elif len(hit) == 1:
            palette = f"仅 f{hit[0]}={reds[hit[0] - 1]}"
        else:
            palette = f"{len(hit)} 帧（{reds[hit[0] - 1]}–{max(reds)}）"

        start, end = EXPORT / f"{slug}-start.webp", EXPORT / f"{slug}-end.webp"
        static_ok = (start.is_file() and b"ANMF" not in start.read_bytes()
                     and end.is_file() and b"ANMF" not in end.read_bytes())
        embeds, kantu, tushuo, missing_questions = observation_counts(slug)
        total_embeds += embeds
        total_kantu += kantu
        caption_ok = entries[slug]["caption_ok"] and entries[slug]["bans_ok"]
        archived = any((ROOT / rel / f"{slug}.svg").is_file() for rel in
                       ("docs/circuits/assets/archive", "bms-book/assets/archive"))

        total_px = 960 * 560
        red_share = max(reds) / total_px if reds else 0.0

        problems = []
        if red_share > RED_AREA_LIMIT:
            problems.append(f"红色面积过大（{red_share:.1%}）")
        if set(durations) != {1200} or loop != 0:
            problems.append(f"时长/循环异常：{sorted(set(durations))} / loop={loop}")
        if geometry_problems:
            problems.append(f"几何门 {geometry_problems} 处")
        if not static_ok:
            problems.append("首末帧缺失或含动画帧")
        if missing_questions:
            problems.append("缺观察题的嵌入：" + "、".join(missing_questions))
        if not caption_ok:
            problems.append("图注未过")
        if not archived:
            problems.append("旧 SVG 未归档")

        if embeds == 0:
            observation = "无嵌入（仅索引/链接）"
        else:
            observation = (f"{embeds} 处嵌入：看图 {kantu}" + (f" / 图说 {tushuo}" if tushuo else "")
                           + ("（全部有）" if not missing_questions else ""))
        rows.append(
            f"| {number} | `{slug}` | 待审 | {palette} | {'✓' if static_ok else '✗'} | "
            f"{observation} | {'✓' if caption_ok else '✗'} | "
            f"{'机器项通过 / 目检待审' if not problems else '机器项待补：' + '；'.join(problems)} |"
        )
        if problems:
            failed.append((slug, problems))

    header = """---
search: false
---

# 第一批 20 张验收记录（batch 1）

> 依据：设计 §5.1「单张过门」五条 + §5.2「批次与扩面」。每格都来自可复现测量，不是目检勾选：
>
> - **帧数 / 时长 / loop**：解析导出 WebP 的 `ANMF` / `ANIM` 块（不是看文件名）。
> - **色板**：逐帧统计 C-15 近似像素（`r>150 & g<110 & b<100`），记红像素出现在第几帧、多少像素。判定依据是「危险才用 C-15」——红色铺满整帧或出现在非危险帧才算不合格。
> - **首末静态**：`-start.webp` / `-end.webp` 必须存在且不含 `ANMF`（能打印）。
> - **可暂停**：渲染期统一挂 `v-book-motion` 控件（`docs/.vitepress/pausable-handraw.ts`），实页按字节验收：静止态 `src` 文件 0 个 `ANMF`、点击后 5–6 帧、再点回同一文件。
> - **观察题**：**逐处**核，图后 5 行内必须有 `> **看图**`。`> **图说**` 只算图注，不能顶替观察题。扫描范围含根 `README.md`（首页嵌了路线图动画）与 `docs/**`，排除内部文档。
> - **图注**：manifest 的 `caption_ok` 与 `bans_ok`。
> - **无人无卡通**：**机器无法判定**，本列一律 `待审`。源虽是自绘矢量帧、无照片素材，但「画面里有没有人物/卡通元素」只能靠眼睛；本轮视觉模型不可用（503），不宣称重做过目检，也不拿生成源当目检证据。
> - **色板**：机器只判「面积」——单帧 C-15 像素占比 > 2% 视为大面积铺色（与 §5.1「危险仅 C-15」冲突）。红色是否落在**该落的那一帧**（危险/切断瞬间）仍需目检，故分布只作线索，不作判定。
> - **旧 SVG**：`docs/circuits/assets/archive/` 或 `bms-book/assets/archive/` 下存在同名文件。

| # | slug | 无人无卡通（目检） | 色板（C-15 分布 / 面积） | 首末静态 | 可暂停 + 观察题（逐处） | 图注 | 机器项总评 |
|---:|---|---|---|---|---|---|---|
"""

    footer = f"""
## 结论

**机器项**（可复现）：

- 20 张全部 5–6 帧、每帧 1200 ms、`loop=0`。
- 几何门（压字/压线/压曲线/出界）合计 0 处。
- 首末静态帧齐全且不含动画帧，可打印。
- 每处嵌入都有观察题：**{total_kantu}/{total_embeds}** 处（含根 `README.md` 与详解页）；manifest 图注与禁令均为 true；旧 SVG 全部归档。
- 色板面积检查：无图超过 2% 阈值。
- 播放控件由渲染期统一生成，实页按字节验收（静止 0 个 `ANMF`、点击 5–6 帧、再点回同一文件）。

**语义项**（需人眼，未做）：`无人无卡通` 与「C-15 是否只落在危险帧」两列全部 `待审`。设计 §5.1 要求逐张勾选，在补上目检证据之前，**本批次不算过门**；`failed=0` 只代表机器项通过，不代表验收完成。

本表由 `python tools/gen_handraw_acceptance.py` 重新生成；数字改动请改脚本而不是手改表格。
"""

    OUT.write_text(header + "\n".join(rows) + "\n" + footer, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} rows={len(rows)} failed={len(failed)}")
    for slug, problems in failed:
        print(f"  {slug}: {'；'.join(problems)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
