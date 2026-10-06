#!/usr/bin/env bash
# 本地一键复跑 CI 全部检查门（与 .github/workflows/tests.yml 对齐）。
# 用法：bash scripts/local-gates.sh
# FAIL 使退出码非零；工具缺失记 SKIP，不算失败。CI 才是真门禁。
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

  if command -v ruff >/dev/null 2>&1; then
    if ruff check "$ROOT"; then report ruff PASS; else report ruff FAIL; fi
  else
    ruff_out="$("$PY" -m ruff check "$ROOT" 2>&1)" || true
    if printf '%s' "$ruff_out" | grep -q 'No module named'; then
      report ruff SKIP '未安装：pip install ruff==0.15.21'
    elif "$PY" -m ruff check "$ROOT"; then
      report ruff PASS
    else
      report ruff FAIL
    fi
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

echo
echo '==== 本地门结果 ===='
exit "$fail"
