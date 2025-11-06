"""
YouTube LLM 프롬프트 템플릿
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 검색 쿼리 생성 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUERY_GENERATION_PROMPT = """
Generate {query_min}-{query_max} YouTube search queries focused on: "{lecture_summary}"

Settings:
- Answer language: {language}
- Video language preference: {yt_lang}

Additional context (reference only):
- Previous: {previous_summaries}
- RAG: {rag_context}

Return JSON:
{{
  "queries": ["query1", "query2", ...],
  "rationale": "one sentence"
}}

Focus on lecture_summary. Keep queries concise with key technical terms.
""".strip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 영상 요약 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY_PROMPT = """
Summarize YouTube video in exactly 3 sentences ({language}).
Make it informative so students understand the content without watching the video.

Title: "{title}"
Content: "{content}"

Return JSON:
{{
  "extract": "Sentence 1. Sentence 2. Sentence 3."
}}

Keep it concise and helpful for learners.
""".strip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자막 없이 요약 프롬프트 (제목/설명만으로 예상)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY_NO_TRANSCRIPT_PROMPT = """
Based on title and description only, predict video content in exactly 2 sentences ({language}).

Title: "{title}"
Description: "{description}"
Channel: "{channel}"

Return JSON:
{{
  "extract": "Sentence 1. Sentence 2."
}}

Be brief and informative.
""".strip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 영상 점수 평가 프롬프트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCORE_VIDEO_PROMPT = """
Evaluate video relevance to lecture section.

Lecture Summary: {lecture_summary}
Video Title: {title}
Video Summary: {extract}

Scoring (엄격한 기준):
- 10: 강의에서 다룬 개념의 **공식 튜토리얼** 또는 **창시자 직접 설명**
     (Official tutorial OR creator's explanation of the concept)
- 9: 강의 핵심 개념을 **직접** 다루고, 예제/실습 포함
- 7-8: 핵심 개념 다루지만 **부분적** 또는 이론 위주
- 5-6: 관련 배경지식이지만 강의 주제와 약간 벗어남
- 3-4: 키워드만 겹치고 다른 맥락
- 1-2: 거의 무관

Return JSON (reason in {language}, one sentence, no line breaks):
{{
  "score": <number>,
  "reason": "명확한 한 문장 평가"
}}
""".strip()

