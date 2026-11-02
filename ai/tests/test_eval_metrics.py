from __future__ import annotations

import pytest

from eval.agreement import cohen_kappa, draw_rows
from eval.compare import paired_bootstrap, section_precisions
from eval.dataset import Section, draw_sample
from eval.diagnose import build_skeletons, cut_judgments, find_cuts, label_context
from eval.judge import JudgeItem, build_user_prompt, cache_key, parse_judgment
from eval.report import precision_at_k, summarize
from eval.run_cards import eval_lecture_number, parse_sse, resource_content
from eval.run_latency import item_timings, percentile
from eval.run_retrieval import collection_name
from rag.splitters import PageText


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


def test_item_timings_takes_first_arrival_per_item():
    events = [
        (10.0, "start", {"item": 0}),
        (100.0, "question", {"item": 0, "text": "Q"}),
        (150.0, "answer", {"item": 0, "text": "a"}),
        (160.0, "answer", {"item": 0, "text": "b"}),
        (120.0, "question", {"item": 1, "text": "Q2"}),
        (400.0, "done", {"item": 0}),
        (500.0, "done", {"item": 1}),
    ]

    timings = item_timings(events)

    assert timings["질문 표시"] == [100.0, 120.0]
    assert timings["첫 답변 조각"] == [150.0]
    assert timings["항목 완료"] == [400.0, 500.0]
    assert timings["전체 완료"] == [500.0]
    assert percentile([1, 2, 3, 4], 0.5) == 2.5


def test_section_precisions_sorts_by_rank_per_section():
    rows = [
        {"section_key": "a#0", "rank": 2, "relevant": False},
        {"section_key": "a#0", "rank": 1, "relevant": True},
        {"section_key": "b#0", "rank": 1, "relevant": False},
    ]

    assert section_precisions(rows, k=1) == {"a#0": 1.0, "b#0": 0.0}


def test_paired_bootstrap_is_repeatable_and_uses_common_sections():
    before = {"a": 0.5, "b": 0.25, "c": 0.75, "only_before": 1.0}
    after = {"a": 1.0, "b": 0.5, "c": 1.0, "only_after": 0.0}

    first = paired_bootstrap(before, after, rounds=500, seed=1)

    assert first == paired_bootstrap(before, after, rounds=500, seed=1)
    assert first["sections"] == 3
    assert first["diff"] == pytest.approx(1 / 3)
    assert 0.25 <= first["ci_low"] <= first["diff"] <= first["ci_high"] <= 0.5
    assert (first["only_before"], first["only_after"]) == (1, 1)


def test_paired_bootstrap_interval_contains_zero_without_consistent_difference():
    before = {str(i): 0.5 for i in range(20)}
    after = {str(i): 0.5 + (0.25 if i % 2 else -0.25) for i in range(20)}

    result = paired_bootstrap(before, after, rounds=1000, seed=1)

    assert result["ci_low"] < 0 < result["ci_high"]


def test_find_cuts_detects_chunks_cut_inside_sentences():
    pages = [PageText(page=0, text="* 자율성 존중\n* 온정주의 비교\n대리 결정은 환자 의사를 따른다.")]
    skeletons = build_skeletons(pages)

    cuts = find_cuts(["자율성 존중 온정주의 비교", "대리 결정은 환자", "의사를 따른다."], skeletons)

    assert cuts == [False, True, True]


def test_find_cuts_locates_semantic_chunks_without_bullets_and_marks_unknown():
    pages = [PageText(page=0, text="* 첫 항목\n* 둘째 항목")]

    assert find_cuts(["첫 항목 둘째 항목", "없는 문장"], build_skeletons(pages)) == [False, None]


def test_cut_judgments_groups_by_cut_flag_per_lecture():
    rows = [
        {"lecture_id": "a", "chunk_id": "c0", "relevant": True},
        {"lecture_id": "a", "chunk_id": "c1", "relevant": False},
        {"lecture_id": "b", "chunk_id": "c0", "relevant": False},
        {"lecture_id": "b", "chunk_id": "c9", "relevant": True},
    ]

    groups = cut_judgments(rows, {"a|c0": False, "a|c1": True, "b|c0": True})

    assert groups == {"끊긴 조각": {"items": 2, "relevant": 0}, "온전한 조각": {"items": 1, "relevant": 1}}


def test_label_context_counts_relevant_top_chunks_per_section():
    retrieval = [
        {"section_key": "a#0", "rank": 1, "relevant": True},
        {"section_key": "a#0", "rank": 2, "relevant": False},
        {"section_key": "a#0", "rank": 3, "relevant": True},
    ]
    resources = [{"section_key": "a#0", "rank": 1, "relevant": True}, {"section_key": "b#0", "rank": 1, "relevant": True}]

    labeled = label_context(resources, retrieval)

    assert [(r["section_key"], r["context"]) for r in labeled] == [("a#0", "관련 문맥 1/2")]
