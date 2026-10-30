"""
QnA 생성 프롬프트

프롬프트 구성 요소:
- section_summary: 현재 강의 내용 (질문 생성 대상)
- rag_context: 강의 자료 조각·이전 구간 요약 (용어 확인용, 직접 출제 금지)
- scope_rule: 출제 범위 제한 (현재 강의에서 말한 내용만 근거)
- context_qp: 기존 질문 (중복 방지용)
"""
from __future__ import annotations

from typing import List, Optional

from core.schemas import QnAType, RAGChunk

from .models import PreviousQA, QARequest

# 화면이 수식 렌더링을 하지 않아 LaTeX를 쓰면 기호가 그대로 보임
SYSTEM_PROMPT = "당신은 교육 전문가입니다. 학습에 도움되는 질문과 답변을 생성합니다. 수식과 기호는 LaTeX 문법 없이 일반 텍스트로 씁니다."

TYPE_LABELS = {
    QnAType.CONCEPT: "개념",
    QnAType.APPLICATION: "응용",
    QnAType.COMPARISON: "비교",
    QnAType.ADVANCED: "심화",
}

TYPE_INSTRUCTIONS = {
    QnAType.CONCEPT: "현재 강의에서 핵심 개념/정의 질문 1개만 생성. 답변 5-6문장. 다른 유형(비교/응용/심화 등)을 섞지 말 것.",
    QnAType.APPLICATION: "현재 강의의 실제 적용/예시 질문 1개만 생성. 답변 5-6문장.",
    QnAType.COMPARISON: "현재 강의의 개념들 비교/대조 질문 1개만 생성. 답변 5-6문장. 다른 유형(개념/바교/심화 등)을 섞지 말 것.",
    QnAType.ADVANCED: "현재 강의의 원리/이유 심화 질문 1개만 생성. 답변 5-6문장. 다른 유형(개념/응용/심화 등)을 섞지 말 것.",
}

# 강의 자료에는 아직 설명하지 않은 뒷부분 내용도 들어 있어, 그 내용으로 출제하지 않도록 제한함
SCOPE_RULE = """━━━ 출제 범위 ━━━
- 질문과 답변은 '현재 강의'에 나온 내용만 근거로 함
- 참고 자료에만 있는 개념·세부 내용은 질문과 답변에 넣지 않음
- 응용·비교·심화 질문도 현재 강의에서 언급한 개념 안에서 만듦
- 현재 강의가 주제나 학습 목표 소개뿐이면, 소개된 범위(무엇을 왜 배우는지) 안에서만 질문함"""

TEMPLATE = """━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}

{rag_context}

{context_qp}

{scope_rule}

{subject_context}위 기존 질문과 중복되지 않게, {instruction}

{language_instruction}

출력 형식 (정확히 이 형식만, JSON·머리말 없이):
첫 줄: 질문 내용
둘째 줄부터: 답변 내용"""

# 프롬프트에 넣는 개수. 라우트 검색 개수(강의 자료 2 + 이전 요약 1)와 같음
MAX_RAG_CHUNKS = 3
MAX_PREVIOUS_QA = 3


def build_prompt(request: QARequest, q_type: QnAType) -> str:
    """질문 유형 하나의 생성 프롬프트를 만든다.

    Args:
        request: QnA 생성 요청
        q_type: 질문 유형
    Returns:
        사용자 메시지로 보낼 프롬프트
    """
    return TEMPLATE.format(
        section_summary=request.section_summary,
        rag_context=_rag_context(request.rag_chunks),
        context_qp=_previous_questions(request.previous_qa),
        scope_rule=SCOPE_RULE,
        subject_context=f"[과목: {request.subject}] " if request.subject else "",
        instruction=TYPE_INSTRUCTIONS[q_type],
        language_instruction=_language_instruction(request.language),
    )


def type_label(value: str) -> str:
    """질문 유형 값(CONCEPT 등)을 한글 이름으로 바꾼다. 이미 한글이거나 모르는 값이면 그대로 둔다.

    Args:
        value: 질문 유형 값 또는 이름
    Returns:
        한글 이름
    """
    try:
        return TYPE_LABELS[QnAType(value)]
    except ValueError:
        return value


def _rag_context(chunks: List[RAGChunk]) -> str:
    if not chunks:
        return ""
    lines = ["━━━ 참고 자료 (강의 자료·이전 구간. 아직 다루지 않은 내용 포함, 용어 확인용) ━━━"]
    lines += [f"{i}. {chunk.text}" for i, chunk in enumerate(chunks[:MAX_RAG_CHUNKS], 1)]
    return "\n".join(lines)


def _previous_questions(previous_qa: List[PreviousQA]) -> str:
    if not previous_qa:
        return ""
    lines = ["━━━ 기존 질문 (중복 금지) ━━━"]
    lines += [f"{i}. [{type_label(qa.type)}] {qa.question}" for i, qa in enumerate(previous_qa[-MAX_PREVIOUS_QA:], 1)]
    return "\n".join(lines)


def _language_instruction(language: Optional[str]) -> str:
    if not language:
        return ""
    if language.lower() in ("ko", "korean", "한국어"):
        return "질문과 답변을 한국어로 작성하세요."
    if language.lower() in ("en", "english", "영어"):
        return "Write questions and answers in English."
    return f"Write questions and answers in {language}."
