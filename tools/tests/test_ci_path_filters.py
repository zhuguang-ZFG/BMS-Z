"""Source-of-truth data must trigger the CI gates that consume it."""

from fnmatch import fnmatchcase
from functools import cache
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"


def _matches_github_path(path: str, pattern: str) -> bool:
    path_parts = path.split("/")
    pattern_parts = pattern.split("/")

    @cache
    def match(path_index: int, pattern_index: int) -> bool:
        if pattern_index == len(pattern_parts):
            return path_index == len(path_parts)
        token = pattern_parts[pattern_index]
        if token == "**":
            return match(path_index, pattern_index + 1) or (
                path_index < len(path_parts) and match(path_index + 1, pattern_index)
            )
        return (
            path_index < len(path_parts)
            and fnmatchcase(path_parts[path_index], token)
            and match(path_index + 1, pattern_index + 1)
        )

    return match(0, 0)


def test_curriculum_changes_trigger_tests_on_push_and_pull_request() -> None:
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    changed_paths = (
        "curriculum/concepts.json",
        "curriculum/hardware_cases.json",
        "curriculum/modules/example.json",
    )

    for event in ("push", "pull_request"):
        patterns = workflow["on"][event]["paths"]
        for changed in changed_paths:
            assert any(_matches_github_path(changed, pattern) for pattern in patterns), (
                f"{event} workflow ignores {changed}; curriculum validation would fail open"
            )
