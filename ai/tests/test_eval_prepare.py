from __future__ import annotations

import pytest

from eval.prepare_data import (
    Paragraph,
    check_script,
    parse_plan,
    parse_script,
    split_pages,
    split_response,
    to_speech_chunks,
)


def test_split_response_extracts_material_and_script():
    response = "<<<SLIDES_MD>>>\n# 표지\n<<<END_SLIDES_MD>>>\n<<<SCRIPT_TXT>>>\n[슬라이드 1]\n안녕하세요.\n<<<END_SCRIPT_TXT>>>"

    material, script = split_response(response)

    assert material == "# 표지"
    assert script == "[슬라이드 1]\n안녕하세요."


def test_split_response_requires_markers():
    with pytest.raises(ValueError):
        split_response("# 표지만 있음")


def test_split_pages_ignores_table_separator_rows():
    material = "# 1장\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n\n---\n\n# 2장\n\n---\n\n"

    pages = split_pages(material)

    assert [page.splitlines()[0] for page in pages] == ["# 1장", "# 2장"]


def test_parse_script_assigns_pages_and_splits_paragraphs():
    script = "[슬라이드 1]\n첫 문단입니다.\n\n\n둘째 문단입니다.\n[쪽 2]\n셋째 문단\n이어지는 줄입니다."

    paragraphs = parse_script(script)

    assert paragraphs == [
        Paragraph(page=1, text="첫 문단입니다."),
        Paragraph(page=1, text="둘째 문단입니다."),
        Paragraph(page=2, text="셋째 문단 이어지는 줄입니다."),
    ]


def test_to_speech_chunks_groups_sentences_and_sets_pauses():
    paragraphs = [
        Paragraph(page=1, text="하나. 둘? 셋! 넷."),
        Paragraph(page=1, text="다섯."),
        Paragraph(page=2, text="여섯."),
    ]

    chunks = to_speech_chunks(paragraphs)

    assert [(c.page, c.text, c.pause_after) for c in chunks] == [
        (1, "하나. 둘? 셋!", "group"),
        (1, "넷.", "paragraph"),
        (1, "다섯.", "slide"),
        (2, "여섯.", "end"),
    ]


def test_check_script_reports_missing_page_and_symbols():
    paragraphs = [Paragraph(page=1, text="가" * 3000), Paragraph(page=3, text="브이 (아웃) 곱하기")]

    warnings = check_script(page_count=3, paragraphs=paragraphs)

    assert any("빠진 번호 [2]" in w for w in warnings)
    assert any("( )" in w for w in warnings)


def test_parse_plan_reads_rows_by_lecture_id():
    plan = "| 강의ID | 분야 | 자료 형태 |\n| --- | --- | --- |\n| eng-1 | 공학 | 슬라이드형 |\n| eng-3 | 공학 | 노트형 |\n"

    lectures = parse_plan(plan)

    assert lectures["eng-3"]["자료 형태"] == "노트형"
    assert lectures["eng-1"]["분야"] == "공학"

