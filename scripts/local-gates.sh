#!/usr/bin/env bash
# 本地一键复跑 CI 全部检查门（与 .github/workflows/tests.yml 对齐）。
# 用法：bash scripts/local-gates.sh
# FAIL 使退出码非零；工具缺失记 SKIP，不算失败。CI 才是真门禁。
# 本地专属的门：「生成图对账」（CI 的 numpy 跟着 requirements 区间走，浮点微差会
# 让无关 PR 变红）、「社交卡对账」（要系统里的中文字体，runner 上没有）、
# 「发布记录对账」（要和 git 标签、gh 的 Release 比，CI 的 checkout 抓不到 tag）。
# 理由都见 tools/README.md 与 docs/维护说明.md。
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fail=0
report() {
  printf '%-16s %s' "$1" "$2"
  if [ -n "${3:-}" ]; then printf '  (%s)' "$3"; fi
  printf '\n'
  if [ "$2" = "FAIL" ]; then fail=1; fi
}

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys' >/dev/null 2>&1; then
    PY="$c"
    break
  fi
done

if [ -z "$PY" ]; then
  report 'python 解释器' FAIL 'python3/python 均不可用'
else
  if "$PY" .github/scripts/check_docs.py; then
    report check_docs PASS
  else
    report check_docs FAIL
  fi

  # ruff 一律走模块形式：本机 PATH 上有个解析不动的 ruff 存根（command -v 说在、
  # 实际 spawn 失败），会把全绿的仓库报成 FAIL。python3 -m ruff 两边都稳。
  if "$PY" -m ruff --version >/dev/null 2>&1; then
    if "$PY" -m ruff check "$ROOT"; then report ruff PASS; else report ruff FAIL; fi
  else
    report ruff SKIP '未安装：pip install ruff==0.15.21'
  fi

  if "$PY" -m pytest --version >/dev/null 2>&1; then
    ( cd "$ROOT/code/soc" && "$PY" -m pytest tests/ -q )
    if [ $? -eq 0 ]; then report 'pytest soc' PASS; else report 'pytest soc' FAIL; fi
    ( cd "$ROOT/code/soc" && "$PY" compare.py >/dev/null )
    if [ $? -eq 0 ]; then report 'compare.py 冒烟' PASS; else report 'compare.py 冒烟' FAIL; fi
    ( cd "$ROOT/code/protocol" && "$PY" -m pytest tests/ -q )
    if [ $? -eq 0 ]; then report 'pytest protocol' PASS; else report 'pytest protocol' FAIL; fi
    "$PY" -m pytest challenges/01-soc/test_arena.py challenges/02-frames/test_rescue.py -q
    if [ $? -eq 0 ]; then report 'pytest 擂台基线' PASS; else report 'pytest 擂台基线' FAIL; fi
  else
    report 'pytest soc' SKIP 'pytest 未安装：pip install -r code/requirements.txt'
    report 'pytest protocol' SKIP '同上'
    report 'compare.py 冒烟' SKIP '同上'
    report 'pytest 擂台基线' SKIP '同上'
  fi
fi

if command -v gcc >/dev/null 2>&1; then
  (
    cd "$ROOT/code/firmware" || exit 1
    gcc -std=c99 -Wall -Wextra -Werror -o test_bms_local bms.c test_bms.c
  )
  if [ $? -eq 0 ] && "$ROOT/code/firmware/test_bms_local"; then
    report '固件 gcc+run' PASS
  else
    report '固件 gcc+run' FAIL
  fi
  rm -f "$ROOT/code/firmware/test_bms_local"
  (
    cd "$ROOT/code/firmware" || exit 1
    gcc -std=c99 -Wall -Wextra -Werror -o hil_replay_local bms.c hil_replay.c
  )
  if [ $? -eq 0 ] && "$ROOT/code/firmware/hil_replay_local"; then
    report hil_replay PASS
  else
    report hil_replay FAIL
  fi
  rm -f "$ROOT/code/firmware/hil_replay_local"
else
  report '固件 gcc+run' SKIP 'gcc 不在 PATH'
  report hil_replay SKIP 'gcc 不在 PATH'
fi

# 7. 生成图对账（本地专属，CI 不跑）。把生成器输出写到临时目录，与 assets 里
#    的入库版本逐字节比对。拦两类事故：手改生成产物、改了生成器没重新生成。
#    比对发生在临时目录，不改 assets、也不依赖 git 暂存状态。
if [ -n "$PY" ] && "$PY" -c 'import numpy' >/dev/null 2>&1; then
  tmp_regen="$(mktemp -d)"
  if "$PY" tools/gen_mechanism_svgs.py --out "$tmp_regen" >/dev/null 2>&1; then
    regen_fail=0
    for f in "$tmp_regen"/*.svg; do
      name="$(basename "$f")"
      cmp -s "$f" "$ROOT/docs/circuits/assets/$name" || { regen_fail=1; break; }
    done
    if [ "$regen_fail" -eq 0 ]; then
      report '生成图对账' PASS
    else
      report '生成图对账' FAIL "$name 与再生成结果不一致，看 tools/README.md 的对账说明"
    fi
  else
    report '生成图对账' FAIL '生成器跑不动：python3 tools/gen_mechanism_svgs.py 的报错'
  fi
  rm -rf "$tmp_regen"
else
  report '生成图对账' SKIP 'numpy 不可用：pip install -r code/requirements.txt'
fi

# 8. 社交卡对账（本地专属，CI 不跑）。这张位图原先没有源：147→148 那轮 README、
#    门户 HTML、路线图动画都跟着改了，只有它还写 147，而它是分享出去最先看到的一张。
#    现在由 tools/gen_social_card.py 画，图上的三个数从仓库现算，这里比对字节。
#    CI 不跑：中文字体在系统字体目录，runner 上没有，缺字会画成方框。
if [ -n "$PY" ] && "$PY" -c 'import PIL' >/dev/null 2>&1; then
  tmp_card="$(mktemp -d)"
  if "$PY" tools/gen_social_card.py --out "$tmp_card" >/dev/null 2>&1; then
    if cmp -s "$tmp_card/bms-roadmap-social.png" "$ROOT/docs/circuits/assets/bms-roadmap-social.png"; then
      report '社交卡对账' PASS
    else
      report '社交卡对账' FAIL '入库的社交卡与再生成结果不一致：跑 python3 tools/gen_social_card.py'
    fi
  else
    report '社交卡对账' FAIL '生成器跑不动：多半是系统里没有 Noto Sans SC'
  fi
  rm -rf "$tmp_card"
else
  report '社交卡对账' SKIP 'Pillow 不可用：pip install pillow'
fi

# 9. 发布记录对账（本地专属，CI 不跑）。docs/维护说明.md 的「发布记录」表抄了
#    标签 sha 和 Release 发布时间，抄错就是一条没人会点的假凭据。CI 的 checkout
#    不抓 tag、也没有 gh 登录，所以这里用 git / gh 的现值比。check_docs.py 里
#    同一张表的文本侧对账（版本集合、日期、写法）CI 每次都跑，两边不重复。
if [ -n "$PY" ]; then
  "$PY" .github/scripts/check_docs.py --release-truth
  case $? in
    0) report '发布记录对账' PASS ;;
    3) report '发布记录对账' SKIP '缺 git 或 gh（gh 要登录）：原因见上面的「注意」行；文本侧已对过' ;;
    *) report '发布记录对账' FAIL '发布记录表与 git 标签 / gh Release 对不上' ;;
  esac
else
  report '发布记录对账' SKIP 'python 解释器不可用'
fi

echo
echo '==== 本地门结果 ===='
exit "$fail"
