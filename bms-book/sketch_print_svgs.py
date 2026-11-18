# 一次性批处理：对 bms-book/assets/print/*.svg 跑 sketch_pass 手绘变换
# 用法: python sketch_print_svgs.py [--dry-run]
# 已被 snapshot_visuals 冻结时手绘化的文件带 data-sketch-pass 标记，这里跳过。
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from sketch_pass import (  # noqa: E402
    SKETCH_MARK,
    already_sketched,
    assert_well_formed,
    flatten_tags,
    sketch_file,
)

TARGET = ROOT / "assets" / "print"
CAP = 200_000  # print 图体积上限宽松（原图最大约 60KB 量级，抖动后仍远低于）


def main() -> int:
    dry = "--dry-run" in sys.argv
    for path in sorted(TARGET.glob("*.svg")):
        raw = path.read_text(encoding="utf-8")
        if already_sketched(raw):
            print(f"{path.name}: 已有 {SKETCH_MARK} 标记，跳过（避免二次叠加）")
            continue
        src = flatten_tags(raw.strip())
        out = sketch_file(src, path.stem)
        assert_well_formed(out, path.name)
        size = len(out.encode("utf-8"))
        if size > CAP:
            raise SystemExit(f"{path.name}: 变换后 {size}B 超 {CAP}B 上限")
        print(f"{path.name}: {len(src.encode())}B -> {size}B")
        if not dry:
            path.write_text(out, encoding="utf-8", newline="\n")  # 快照门要求 LF
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
