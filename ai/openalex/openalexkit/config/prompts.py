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

SCORE_PAPER_PROMPT = """Current section summary: {section_summary}

Keywords: {keywords}
Paper title: {title}
Abstract: {abstract}
Publication year: {year}
Citation count: {cited_by_count}

Does this paper directly cover the core concept discussed in the lecture?

Scoring (strict criteria):
- 10: Seminal/foundational paper that FIRST introduced the concept
   - Highly cited (typically >10,000) AND matches core concept perfectly
- 9: Directly addresses core concept with clear methodology/application
- 7-8: Covers core concept but partially or indirectly
- 4-6: Related background but slightly off-topic
- 1-3: Only keyword overlap, content unrelated

Return JSON (reason: one sentence, no line breaks, in {language}):
{{"score": <number>, "reason": "clear one-sentence evaluation"}}
"""

