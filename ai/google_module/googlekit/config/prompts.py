"""
Google 검색을 위한 LLM 프롬프트 템플릿
"""

# ━━━ 키워드 생성 프롬프트 ━━━
KEYWORD_GENERATION_PROMPT = """You are an expert search query generator for academic content.

Generate {keyword_min} specific search queries in {language} for the given lecture topic.

**Guidelines:**
- Use detailed technical phrases (3-7 words)
- Include specific concepts, technologies, or methodologies
- Create queries optimized for Google search to find high-quality results
- Return ONLY the queries, one per line

**Lecture Summary:**
{lecture_summary}

{context}

**Search Queries:**"""


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
URL: {url}
Snippet: {snippet}

**Task:**
Rate the relevance on a scale of 0-10 and provide a brief reason in {language}.

**Scoring Guidelines:**
- 10: Original authoritative source (official documentation, seminal papers, standard specifications)
- 9: Highly relevant with comprehensive technical depth and accurate explanations
- 7-8: Very relevant, covers key concepts with good technical details
- 5-6: Moderately relevant, provides useful background or related information
- 3-4: Somewhat relevant, mentions the topic but lacks depth
- 0-2: Not relevant, off-topic or too general

**Response Format (JSON only):**
{{"score": <float>, "reason": "<1-2 sentences in {language}>"}}

**JSON Response:**"""
