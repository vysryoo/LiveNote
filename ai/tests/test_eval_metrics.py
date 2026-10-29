from __future__ import annotations

import pytest

from eval.agreement import cohen_kappa, draw_rows
from eval.dataset import Section, draw_sample
from eval.judge import JudgeItem, build_user_prompt, cache_key, parse_judgment
from eval.report import precision_at_k, summarize
from eval.run_cards import eval_lecture_number, parse_sse, resource_content
from eval.run_retrieval import collection_name


def _section(lecture_id: str, field: str, index: int) -> Section:
    return Section(lecture_id=lecture_id, field=field, section_index=index, transcript="t", summary="s")


def test_precision_at_k_counts_missing_results_as_irrelevant():
    assert precision_at_k([True, False, True], 4) == 0.5
    assert precision_at_k([True, True, True, True, False], 4) == 1.0


def test_summarize_averages_sections_by_field_and_overall():
    rows = [
        {"section_key": "a#0", "field": "공학", "rank": 2, "relevant": False},
        {"section_key": "a#0", "field": "공학", "rank": 1, "relevant": True},
        {"section_key": "b#0", "field": "간호", "rank": 1, "relevant": True},
        {"section_key": "b#0", "field": "간호", "rank": 2, "relevant": True},
    ]

    summary = summarize(rows, k=2)

    assert summary["공학"]["precision"] == 0.5
    assert summary["간호"]["precision"] == 1.0
    assert summary["전체"]["precision"] == 0.75
    assert summary["전체"]["sections"] == 2
    assert list(summary)[-1] == "전체"


def test_cohen_kappa_matches_known_values():
    assert cohen_kappa([(True, True), (False, False)]) == 1.0
    # 관찰 일치 0.5, 우연 일치 0.5 → κ 0
    assert cohen_kappa([(True, True), (True, False), (False, True), (False, False)]) == 0.0
    with pytest.raises(ValueError):
        cohen_kappa([])


def test_draw_sample_takes_same_count_per_field_and_is_repeatable():
    sections = [_section("eng-1", "공학", i) for i in range(10)] + [_section("nur-2", "간호", i) for i in range(3)]

    first = draw_sample(sections, per_field=4, seed=1)
    second = draw_sample(sections, per_field=4, seed=1)

    assert first == second
    assert sum(s.field == "공학" for s in first) == 4
    assert sum(s.field == "간호" for s in first) == 3


def test_draw_rows_samples_each_layer():
    rows = [{"layer": "qna", "n": i} for i in range(30)] + [{"layer": "retrieval", "n": i} for i in range(5)]

    picked = draw_rows(rows, per_layer=10, seed=3)

    assert sum(r["layer"] == "qna" for r in picked) == 10
    assert sum(r["layer"] == "retrieval" for r in picked) == 5


def test_judge_prompt_and_cache_key_depend_on_content():
    item = JudgeItem(kind="qna", transcript="전사", summary="요약", content="질문: Q\n답변: A")
    other = JudgeItem(kind="qna", transcript="전사", summary="요약", content="질문: Q2\n답변: A")

    prompt = build_user_prompt(item)

    assert "[기준표]" in prompt and "질문: Q" in prompt
    assert cache_key(item) == cache_key(item)
    assert cache_key(item) != cache_key(other)


def test_parse_judgment_requires_boolean():
    assert parse_judgment('{"relevant": true, "reason": "직접 관련"}').relevant is True
    with pytest.raises(ValueError):
        parse_judgment('{"relevant": "yes", "reason": ""}')


def test_collection_name_is_per_experiment_and_lecture():
    assert collection_name("E0", "eng-1") == "eval_e0_eng-1"


def test_eval_lecture_number_is_unique_per_experiment_and_lecture():
    assert eval_lecture_number("E0", "eng-1") == 900000
    assert eval_lecture_number("E2", "art-3") == 900208
    with pytest.raises(ValueError):
        eval_lecture_number("baseline", "eng-1")


def test_parse_sse_reads_event_blocks():
    body = 'event: start\ndata: {"item": 0}\n\nevent: done\ndata: {"item": 0, "question": "Q"}\n\n'

    assert parse_sse(body) == [
        {"event": "start", "data": {"item": 0}},
        {"event": "done", "data": {"item": 0, "question": "Q"}},
    ]


def test_resource_content_excludes_service_reason():
    content = resource_content({"type": "WIKI", "title": "큐", "description": "설명", "url": "u", "reason": "추천 이유"})

    assert "큐" in content and "추천 이유" not in content
