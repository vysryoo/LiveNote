"""
OpenAlex Provider 전용 프롬프트
"""
from . import flags


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 프롬프트 1: 쿼리 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUERY_GENERATION_PROMPT = f"""You are to produce terse technical search tokens for OpenAlex.

Current section summary:
{{section_summary}}

Previous sections context:
{{previous_summaries}}

RAG context:
{{rag_context}}

Return a JSON with {flags.TOKEN_MIN}~{flags.TOKEN_MAX} technical English tokens suitable for academic paper search:
{{{{
  "tokens": ["term1", "term2", ...]
}}}}

Rules:
- Extract core concepts and technical terms from all provided context
- Use precise academic terminology
- Expand abbreviations where needed
- Include field-specific keywords
- Keep it concise ({flags.TOKEN_MIN}-{flags.TOKEN_MAX} tokens max)
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 프롬프트 2: 논문 검증
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCORE_PAPER_PROMPT = """현재 섹션 요약: {section_summary}

키워드: {keywords}
논문 제목: {title}
논문 초록: {abstract}
출판 연도: {year}
인용 횟수: {cited_by_count}

Does this paper directly cover the core concept discussed in the lecture?

Scoring (엄격한 기준):
- 10: 강의에 나온 개념을 처음 제시한 논문일 경우 부여 (Seminal/foundational paper that FIRST introduced the concept)
   - Highly cited (typically >10,000) AND matches core concept perfectly
- 9: 강의 핵심 개념을 **직접** 다루고, 방법론/응용 명확
- 7-8: 핵심 개념 다루지만 **부분적** 또는 간접적
- 4-6: 관련 배경지식이지만 강의 주제와 약간 벗어남
- 1-3: 키워드만 겹치고 실제 내용 무관

Return JSON (**reason 한 문장, 줄바꿈 금지, 한국어**):
{{"score": <number>, "reason": "명확한 한 문장 평가"}}
"""

