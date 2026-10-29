from __future__ import annotations

from typing import List

from qa.qakit.stream_parser import QAStreamParser


def _run(chunks: List[str]):
    parser = QAStreamParser()
    events = []
    for chunk in chunks:
        events.extend(parser.feed(chunk))
    events.extend(parser.finish())
    return parser, events


def test_first_line_is_question_and_rest_is_answer():
    parser, events = _run(["스택이란", " 무엇인가?\n", "스택은 마지막에 들어온 데이터가 ", "먼저 나가는 구조입니다."])

    assert events[0] == ("question", "스택이란 무엇인가?")
    assert all(kind == "answer" for kind, _ in events[1:])
    assert parser.question == "스택이란 무엇인가?"
    assert parser.answer == "스택은 마지막에 들어온 데이터가 먼저 나가는 구조입니다."


def test_question_is_emitted_once_line_completes():
    parser = QAStreamParser()
    assert parser.feed("스택이란") == []
    assert parser.feed(" 무엇인가?\n") == [("question", "스택이란 무엇인가?")]


def test_labels_and_emphasis_are_removed():
    parser, _ = _run(["**질문:** 큐란?\n", "답변: 큐는 먼저 들어온 데이터가 먼저 나가는 구조입니다."])

    assert parser.question == "큐란?"
    assert parser.answer == "큐는 먼저 들어온 데이터가 먼저 나가는 구조입니다."


def test_answer_label_split_across_chunks_is_removed():
    parser, events = _run(["Q: 힙이란?\n", "A", ": 힙은 ", "완전 이진 트리 기반 구조입니다."])

    assert parser.question == "힙이란?"
    assert parser.answer == "힙은 완전 이진 트리 기반 구조입니다."
    assert "".join(text for kind, text in events if kind == "answer").strip() == parser.answer


def test_blank_lines_before_question_are_skipped():
    parser, _ = _run(["\n\n덱이란?\n\n", "덱은 양쪽 끝에서 삽입과 삭제가 가능한 구조입니다."])

    assert parser.question == "덱이란?"
    assert parser.answer == "덱은 양쪽 끝에서 삽입과 삭제가 가능한 구조입니다."


def test_output_without_newline_becomes_question_only():
    parser, events = _run(["질문만 있는 출력"])

    assert events == [("question", "질문만 있는 출력")]
    assert parser.answer == ""


def test_short_answer_is_flushed_on_finish():
    parser, events = _run(["트리란?\n", "계층 구조"])

    assert events[-1] == ("answer", "계층 구조")
    assert parser.answer == "계층 구조"
