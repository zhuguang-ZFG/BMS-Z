"""Exercise cleanup path parsing in cmd.exe without deleting or changing ACLs."""

from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Requires Windows cmd.exe")


def run_cleanup(tmp_path, delayed_expansion):
    source = (ROOT / "cleanup-tmp-elevated.cmd").read_text(encoding="utf-8")
    # Only relocate the working directory and intercept the three filesystem
    # operations. Preserve their arguments so cmd.exe still parses real paths.
    source, count = re.subn(
        r"(?m)^cd /d [^\n]+", 'cd /d "%~dp0" || exit /b 1', source
    )
    assert count == 1

    intercepted = []

    def record_operation(match):
        indent, command, arguments = match.groups()
        intercepted.append(command)
        return (
            f'{indent}"%BMS_CLEANUP_TEST_PYTHON%" "%~dp0record.py" '
            f"{command}{arguments}"
        )

    source = re.sub(
        r"(?m)^([ \t]*)(takeown|icacls|rd)([ \t]+[^\n]*)$",
        record_operation,
        source,
    )
    assert Counter(intercepted) == Counter({"takeown": 1, "icacls": 1, "rd": 1})
    (tmp_path / "cleanup.cmd").write_text(source, encoding="ascii")
    (tmp_path / "record.py").write_text(
        "import json, os, sys\n"
        "with open(os.environ['BMS_CLEANUP_TEST_LOG'], 'a', encoding='utf-8') as log:\n"
        "    log.write(json.dumps(sys.argv[1:]) + '\\n')\n",
        encoding="ascii",
    )
    log = tmp_path / "operations.jsonl"
    env = {
        **os.environ,
        "BMS_CLEANUP_TEST_PYTHON": sys.executable,
        "BMS_CLEANUP_TEST_LOG": str(log),
        "BMS_CLEANUP_TEST_VALUE": "serve",
    }
    result = subprocess.run(
        [os.environ.get("COMSPEC", "cmd.exe"), "/d", f"/v:{delayed_expansion}",
         "/c", "cleanup.cmd"],
        cwd=tmp_path,
        env=env,
        input="\n",
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    operations = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    return result.stdout.splitlines(), operations


@pytest.mark.parametrize("delayed_expansion", ["off", "on"])
def test_cleanup_preserves_literal_paths_and_protected_directories(tmp_path, delayed_expansion):
    targets = [
        ".tmp-normal",
        ".tmp-%BMS_CLEANUP_TEST_VALUE%",
        ".tmp-!BMS_CLEANUP_TEST_VALUE!",
        ".tmp-amp&echo CLEANUP_INJECTION_MARKER",
        ".tmp-caret^ (parentheses)",
        ".tmp-中文",
        "bms-book/.tmp-pytest-normal",
        "code/protocol/.tmp-pytest",
        "code/soc/.tmp-pytest",
        "bms-book/.local/tmp/pytest-of-zhugu",
        ".local/book-depth-check",
        ".local/book-tests-check",
        ".local/book-v042-checktests",
        ".local/book-visual-check",
        ".local/project-tests-check",
        ".local/pytest-book-link-fix-check",
    ]
    protected = [
        ".tmp-serve", ".local/keep-tests", "bms-book/.tmp-other",
        ".local/book-v042-tests-extra",
    ]
    for relative in targets + protected:
        (tmp_path / relative).mkdir(parents=True)
    for relative in [".tmp-file", ".local/book-depth-file"]:
        (tmp_path / relative).write_text("keep", encoding="ascii")

    output, operations = run_cleanup(tmp_path, delayed_expansion)

    assert "CLEANUP_INJECTION_MARKER" not in output
    target_indices = {"takeown": 2, "icacls": 1, "rd": 3}
    actual = Counter(
        (row[0], Path(row[target_indices[row[0]]])) for row in operations
    )
    expected = Counter(
        (command, Path(target)) for command in target_indices for target in targets
    )
    assert actual == expected
