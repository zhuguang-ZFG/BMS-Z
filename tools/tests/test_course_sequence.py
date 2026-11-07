"""Reject forward prerequisites, missing transitions and automatic answer reveal."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

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


def test_every_lesson_must_declare_its_own_illustration():
    data = manifest()
    del data['lessons'][0]['illustration']
    assert any('missing or mismatched lesson illustration' in message for message in course.validate(data))
    data = manifest()
    data['lessons'][1]['illustration'] = data['lessons'][0]['illustration']
    assert any('reused lesson illustration' in message for message in course.validate(data))


@pytest.fixture
def illustrated_course(tmp_path):
    data = manifest()
    for lesson in data['lessons']:
        for name in (lesson['file'], lesson['illustration']):
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(course.COURSE / name, target)
    assert course.validate(data, tmp_path) == []
    return data, tmp_path


def test_missing_image_file_fails_even_if_the_manuscript_links_it(illustrated_course):
    data, directory = illustrated_course
    (directory / data['lessons'][0]['illustration']).unlink()
    assert any('missing illustration file' in message for message in course.validate(data, directory))


@pytest.mark.parametrize('location', ['absent', 'comment', 'code', 'answer'])
def test_a_hidden_or_unused_illustration_does_not_count_as_coverage(illustrated_course, location):
    data, directory = illustrated_course
    lesson = data['lessons'][0]
    path = directory / lesson['file']
    text = path.read_text(encoding='utf-8')
    image = next(line for line in text.splitlines() if f"]({lesson['illustration']})" in line)
    text = text.replace(image, '')
    if location == 'comment':
        text += f'\n<!-- {image} -->\n'
    elif location == 'code':
        text += f'\n```markdown\n{image}\n```\n'
    elif location == 'answer':
        text = text.replace('</details>', f'{image}\n</details>')
    path.write_text(text, encoding='utf-8')
    assert any('first image before the answer' in message for message in course.validate(data, directory))
