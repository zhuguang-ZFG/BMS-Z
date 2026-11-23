from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
CHECK_DOCS_PATH = ROOT / ".github" / "scripts" / "check_docs.py"
SPEC = importlib.util.spec_from_file_location("release_ledger_check_docs", CHECK_DOCS_PATH)
assert SPEC is not None and SPEC.loader is not None
check_docs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_docs
SPEC.loader.exec_module(check_docs)


SNAPSHOT = {
    "标签": "pre-merge-analog-2026-11-11",
    "标签指向": "`7ca01bfc22fe631c3318c42a69faf5ad90cb089b`（轻量标签）",
    "用途": "合并模拟电路卷一前的安全快照，不是 Release。",
}
SNAPSHOT_SHA = "7ca01bfc22fe631c3318c42a69faf5ad90cb089b"


def test_snapshot_registry_is_explicit_and_well_formed() -> None:
    rows = check_docs.release_table_rows()
    assert check_docs.check_snapshot_registry(rows) == []
    assert [row["标签"] for row in check_docs.snapshot_table_rows()] == [SNAPSHOT["标签"]]


def test_registered_snapshot_matches_git_identity() -> None:
    actual = {SNAPSHOT["标签"]: ("轻量标签", {SNAPSHOT_SHA})}

    assert check_docs.check_repository_tag_truth(actual, set(), [SNAPSHOT]) == []


def test_unregistered_git_tag_is_rejected() -> None:
    actual = {"unclassified-checkpoint": ("轻量标签", {SNAPSHOT_SHA})}

    problems = check_docs.check_repository_tag_truth(actual, set(), [])

    assert any("unclassified-checkpoint" in problem for problem in problems)


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        (("附注标签", {SNAPSHOT_SHA}), "轻量标签"),
        (("轻量标签", {"0" * 40}), "7ca01bfc"),
    ],
)
def test_snapshot_type_or_sha_drift_is_rejected(
    actual: tuple[str, set[str]], expected: str
) -> None:
    problems = check_docs.check_repository_tag_truth(
        {SNAPSHOT["标签"]: actual}, set(), [SNAPSHOT]
    )

    assert any(expected in problem for problem in problems)


def test_snapshot_cannot_also_be_a_github_release() -> None:
    problems = check_docs.check_snapshot_release_truth({SNAPSHOT["标签"]}, [SNAPSHOT])

    assert len(problems) == 1
    assert SNAPSHOT["标签"] in problems[0]
