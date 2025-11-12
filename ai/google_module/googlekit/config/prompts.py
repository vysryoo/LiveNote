"""
Google 검색을 위한 LLM 프롬프트 템플릿
"""

# ━━━ 키워드 생성 프롬프트 ━━━
KEYWORD_GENERATION_PROMPT = """You are an expert search query generator for academic content.

Given a lecture summary, generate 2-4 focused search keywords or phrases in {language}.

**Guidelines:**
- Generate technical terms, concepts, or specific topics
- Use terminology that would find relevant web resources
- Prioritize technical documentation, tutorials, and educational content
- Return ONLY the keywords, one per line
- No explanations, no numbering

**Lecture Summary:**
{lecture_summary}

{context}

**Search Keywords ({language}):**"""


KEYWORD_CONTEXT_TEMPLATE = """**Previous Context:**
{previous_summaries}

**Related Materials:**
{rag_context}
"""


# ━━━ 검증 프롬프트 ━━━
SCORING_PROMPT = """You are evaluating the relevance of a search result to a lecture topic.

**Lecture Summary:**
{lecture_summary}

**Search Result:**
Title: {title}
Snippet: {snippet}

**Task:**
Rate the relevance on a scale of 0-10 and provide a brief reason in {language}.

**Scoring Guidelines:**
- 9-10: Highly relevant, directly explains the topic with detailed technical content
- 7-8: Very relevant, covers key concepts with good technical depth
- 5-6: Moderately relevant, provides useful background or related information
- 3-4: Somewhat relevant, mentions the topic but lacks depth
- 0-2: Not relevant, off-topic or too general

**Response Format (JSON only):**
{{"score": <float>, "reason": "<1-2 sentences in {language}>"}}

**JSON Response:**"""
