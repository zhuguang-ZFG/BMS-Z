"""Reject forward prerequisites, missing transitions and automatic answer reveal."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('ordered_course', ROOT / 'tools/check_course.py')
course = importlib.util.module_from_spec(spec)
spec.loader.exec_module(course)


def manifest():
    return json.loads((course.COURSE / 'manifest.json').read_text(encoding='utf-8'))


def test_existing_course_has_a_continuous_learnable_order():
    assert course.validate(manifest()) == []


def test_future_prerequisite_cannot_hide_a_cycle():
    data = copy.deepcopy(manifest())
    data['lessons'][0]['requires'] = ['24']
    assert any('not taught earlier' in message for message in course.validate(data))


def test_new_lesson_cannot_silently_skip_the_previous_project_step():
    data = copy.deepcopy(manifest())
    data['lessons'][6]['requires'] = ['01']
    assert any('missing transition' in message for message in course.validate(data))


def test_a_broken_lesson_file_is_not_a_complete_curriculum():
    data = copy.deepcopy(manifest())
    data['lessons'][4]['file'] = '05-does-not-exist.md'
    assert any('missing manuscript' in message for message in course.validate(data))
