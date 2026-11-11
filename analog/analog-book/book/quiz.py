"""题库拆分：章节题进章末，答案进附录 F。"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .manifest import BookError
from .transforms import strip_emoji

SECTION_RE = re.compile(
    r'<p><a id="[^"]*quiz-ch(\d+)"></a></p>(.*?)'
    r'(?=<p><a id="[^"]*quiz-ch\d+"></a></p>|<h2[^>]*>[^<]*专题|$)',
    re.S)
QUESTION_RE = re.compile(
    r'<li>\s*<p><a id="(?P<raw>[^"]*q-(?P<kind>ch(?P<ch>\d+)|extra)-\d+)"'
    r'[^>]*></a>(?P<q>.*?)</p>\s*<details[^>]*>\s*<summary>.*?</summary>'
    r'(?P<a>.*?)</details>\s*</li>', re.S)
QID_RE = re.compile(r'(q-(?:ch\d+|extra)-\d+)$')


@dataclass(frozen=True)
class Question:
    id: str
    chapter: int | None
    question: str
    answer: str


@dataclass
class QuizData:
    chapters: dict[int, list[Question]]
    extra: list[Question]


def _answer_text(body: str) -> str:
    """单段答案去掉外层 <p>，多段/带公式的答案保留原有块级标记。"""
    body = body.strip()
    match = re.fullmatch(r"<p>(.*?)</p>", body, re.S)
    return strip_emoji((match.group(1) if match else body).strip())


def _question(match: re.Match) -> Question:
    qid = QID_RE.search(match.group("raw")).group(1)
    chapter = int(match.group("ch")) if match.group("kind").startswith("ch") else None
    return Question(id=qid, chapter=chapter,
                    question=strip_emoji(match.group("q").strip()),
                    answer=_answer_text(match.group("a")))


def parse_quiz(fragment: str) -> QuizData:
    chapters: dict[int, list[Question]] = {}
    for match in SECTION_RE.finditer(fragment):
        chapter = int(match.group(1))
        questions = [_question(item) for item in QUESTION_RE.finditer(match.group(2))]
        if not questions:
            raise BookError(f"题库第 {chapter} 章没有解析到题目")
        chapters[chapter] = questions
    if not chapters:
        raise BookError("题库中没有 quiz-chN 分节")
    extra = [_question(item) for item in QUESTION_RE.finditer(fragment)
             if item.group("kind") == "extra"]
    ids = [q.id for group in chapters.values() for q in group] + [q.id for q in extra]
    if len(ids) != len(set(ids)):
        raise BookError("题库题目 ID 重复")
    return QuizData(chapters=chapters, extra=extra)


def _exercises_anchor(questions: list[Question], stem: str) -> str:
    if questions and questions[0].chapter is not None:
        return f"chapter-{questions[0].chapter}--exercises"
    return f"{stem}--exercises"


def merge_exercises(fragment: str, questions: list[Question], stem: str) -> str:
    if not questions:
        return fragment
    anchor = _exercises_anchor(questions, stem)
    items = "".join(
        f'<li><a id="{stem}--q-{q.id}"></a>{q.question}</li>' for q in questions)
    existing = re.search(
        r'(<h2[^>]*>[^<]*本章练习[^<]*</h2>\s*<ol[^>]*>)(.*?)(</ol>)',
        fragment, re.S)
    if existing:
        marker = f'<a id="{anchor}"></a>'
        return (fragment[:existing.start(1)] + marker
                + fragment[existing.start(1):existing.start(2)]
                + existing.group(2) + items + fragment[existing.end(2):])
    section = (
        f'<section class="chapter-exercises" id="{anchor}">'
        f'<h2 id="{anchor}-title">本章练习</h2>'
        f'<ol class="exercise-list">{items}</ol>'
        '<p class="exercise-hint">答案见附录 F；先盖住答案在纸上算。</p></section>')
    return fragment + section


def render_answers(data: QuizData, chapter_stems: dict[int, str],
                   appendix_stem: str, note: str | None = None) -> str:
    rows = ['<h1 id="appendix-f-answers">习题答案与综合自测</h1>',
            '<p class="answers-note">%s</p>'
            % (note or "章节题按题号对应章末练习；专题题为综合加练。")]
    for chapter in sorted(data.chapters):
        stem = chapter_stems[chapter]
        rows.append(f'<section class="answer-group"><h2>第 {chapter} 章</h2>'
                    '<ol class="answer-list">')
        for q in data.chapters[chapter]:
            rows.append(
                f'<li id="{appendix_stem}--ans-{q.id}">'
                f'<a class="answer-ref" href="#{stem}--q-{q.id}">{q.id}</a>'
                f'<div class="answer-body">{q.answer}</div></li>')
        rows.append("</ol></section>")
    if data.extra:
        rows.append('<section class="answer-group"><h2>专题加练</h2>'
                    '<ol class="answer-list">')
        for q in data.extra:
            rows.append(
                f'<li id="{appendix_stem}--ans-{q.id}">'
                f'<p class="answer-question">{q.question}</p>'
                f'<div class="answer-body">{q.answer}</div></li>')
        rows.append("</ol></section>")
    return "\n".join(rows)
