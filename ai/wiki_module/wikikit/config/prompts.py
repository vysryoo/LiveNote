"""
Wikipedia Provider prompts (간소화 버전)
"""
from . import flags

# ━━━ 키워드 생성 프롬프트 (간소화) ━━━
KEYWORD_GENERATION_PROMPT = f"""Extract {flags.KEYWORD_MIN}-{flags.KEYWORD_MAX} Wikipedia search keywords from this lecture summary and related context.

Lecture Summary:
{{lecture_summary}}

Recent Sections:
{{previous_summaries}}

RAG Context:
{{rag_context}}

Rules:
- Use {{search_language}} terms (en → English, ko → 한국어)
- Return keywords in {{search_language}}
- Focus on core concepts and technical terms.
- Focus on Lecture Summary. Rag Context, Recent Sections are just for reference only
- Keep keywords simple and searchable

Output (JSON only):
{{{{
  "keywords": ["keyword1", "keyword2"]
}}}}
"""

# ━━━ 문서 검증 프롬프트 (간소화) ━━━
SCORE_PAGE_PROMPT = """Lecture: {lecture_summary}

Document Title: {title}
Document Summary: {extract}

Rate relevance (0-10):
- 8-10: Directly explains lecture concepts
- 6-7: Provides foundational knowledge
- 4-5: Related but indirect
- 1-3: Keyword match only

Output (JSON, one line):
{{"score": <number>, "reason": "<1 sentence in {language}>"}}
"""
