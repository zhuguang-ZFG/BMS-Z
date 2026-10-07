"""发版当场重数：一条命令数出「共 N 条 / M 个提交 / P 个 PR」，别沿用两天前的数。

用法：
    python3 tools/release_stats.py --from v1.2.0 --to v1.3.0
    python3 tools/release_stats.py --from v1.3.0            # 数到 HEAD，起草下一版用

CHANGELOG 小节默认按 `--to` 的标签名找（去掉前导 v）；找不到就用 `## [Unreleased]`，
也可以 `--section 1.4.0` 点名。条目数只数小节里以 `- ` 开头的行。
"""

import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PR_TAIL = re.compile(r"\(#(\d+)\)\s*$")


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        sys.exit(f"git {' '.join(args)} 失败：{detail[:240]}")
    return proc.stdout


def exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


def changelog_section(name: str) -> tuple[str, str]:
    """返回 (小节名, 正文)。先按给定名找，找不到退回 Unreleased。

    小节名容忍开头那个可选的 `v`（1.0.0 那节当年就是写成 `## [v1.0.0]` 的），与
    check_docs.py 的 `CL_HEADING` / `changelog_sections()` 同一口径。不认的话，点名
    一个带 v 的小节会静默退回 Unreleased——数出来的条目是另一节的账，而两句的提交数
    来自同一个 git 区间，看起来完全正常。退回 Unreleased 本身是发版草案要的行为，
    所以实际用哪一节必须由这里返回的名字说出去，门在那边对账。
    """
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    base = re.sub(r"^v(?=\d)", "", name)
    for try_name in (base, "Unreleased"):
        m = re.search(rf"^## \[((?:v?){re.escape(try_name)})\][^\n]*\n", text, re.M)
        if m:
            return m.group(1), text[m.end() :].split("\n## [", 1)[0]
    sys.exit("CHANGELOG.md 里既没有目标小节也没有 ## [Unreleased]")


def sentence(bullets: int, frm: str, total: int, uniq: list[int], direct: int) -> str:
    """CHANGELOG 版本节首那句的唯一拼法。

    check_docs.py 的 `CL_COUNT` / `CL_COUNT_NOPR` 认的就是这一句，那边的 CI 门
    （`check_release_wording()`）会拿这个函数拼出来的两种句式回灌正则，
    所以改这里的措辞必须同步改门的正则，否则当场红。
    """
    span = f"PR #{uniq[0]}–#{uniq[-1]} 共 {len(uniq)} 个" if uniq else "没有带 PR 号的提交"
    return (
        f"共 {bullets} 条，覆盖 `{frm}` 之后 {total} 个提交"
        f"（{span}，加 {direct} 个直接提交）"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="数一个发版区间里的条目与提交")
    ap.add_argument("--from", dest="frm", required=True, help="上一版的标签，如 v1.2.0")
    ap.add_argument("--to", dest="to", default="HEAD", help="本版标签或 HEAD（默认 HEAD）")
    ap.add_argument("--section", help="CHANGELOG 小节名，默认按 --to 推")
    a = ap.parse_args()

    for ref in (a.frm, a.to):
        if not exists(ref):
            print(f"FAIL: 本地找不到 {ref}——先 `git fetch --tags` 再数", file=sys.stderr)
            return 2

    total = int(git("rev-list", "--count", f"{a.frm}..{a.to}").strip())
    subjects = git("log", "--format=%s", f"{a.frm}..{a.to}").splitlines()
    prs = [int(m.group(1)) for s in subjects if (m := PR_TAIL.search(s))]
    uniq = sorted(set(prs))
    direct = total - len(prs)

    name = a.section or a.to.lstrip("v")
    used, body = changelog_section(name)
    bullets = len([ln for ln in body.splitlines() if ln.startswith("- ")])

    print(f"CHANGELOG 小节：## [{used}]")
    print(sentence(bullets, a.frm, total, uniq, direct))
    if len(prs) != len(uniq):
        print(f"注意：带 PR 号的提交 {len(prs)} 个但号码只有 {len(uniq)} 个，有 PR  squash 过两次")
    return 0


if __name__ == "__main__":
    sys.exit(main())
