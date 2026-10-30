"""
검색어 생성 프롬프트에 넣는 강의 문맥

공급자 모두 같은 기준으로 이전 섹션 요약과 RAG 조각(강의 자료·이전 요약)을 텍스트로 만든다.
"""
from __future__ import annotations

from textwrap import shorten

from .models import RecContext

MAX_PREVIOUS_SUMMARIES = 3
MAX_RAG_CHUNKS = 3
MAX_CHARS = 200
EMPTY = "None"


def previous_text(context: RecContext) -> str:
    """최근 이전 섹션 요약을 한 줄에 하나씩 만든다.

    Args:
        context: 추천 입력
    Returns:
        "Section 번호: 요약" 줄 목록. 없으면 "None"
    """
    lines = [
        f"Section {ps.section_id}: {shorten(ps.summary, width=MAX_CHARS, placeholder='…')}"
        for ps in context.previous_summaries[-MAX_PREVIOUS_SUMMARIES:]
    ]
    return "\n".join(lines) or EMPTY


def rag_text(context: RecContext) -> str:
    """검색 점수가 높은 RAG 조각을 한 줄에 하나씩 만든다.

    Args:
        context: 추천 입력
    Returns:
        "- 조각" 줄 목록. 없으면 "None"
    """
    lines = [f"- {shorten(c.text, width=MAX_CHARS, placeholder='…')}" for c in context.rag_chunks[:MAX_RAG_CHUNKS] if c.text.strip()]
    return "\n".join(lines) or EMPTY
