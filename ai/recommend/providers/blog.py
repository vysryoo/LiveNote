"""
블로그 글 추천 (네이버 블로그 검색)

Google Custom Search JSON API가 신규 가입을 받지 않고 2027-01-01 종료 예정이라 블로그 검색을 네이버로 대체했다.
네이버 개발자센터의 검색 API는 신규 발급이 종료돼, 네이버 클라우드의 NAVER API HUB 엔드포인트를 사용한다.

검색어: LLM이 검색 키워드를 한 줄에 하나씩 만든다
후보: 결과가 없으면 끝 단어를 빼며 재검색 → URL 기준 중복 제거 → 제외 → 재정렬 → 상위 CARD_LIMIT개
"""
from __future__ import annotations

import asyncio
import html
import logging
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

import httpx

from core import llm
from core.config import BlogSettings
from core.http import get_with_retry
from core.llm import ModelPurpose
from core.schemas import ResourceType

from ..context import previous_text, rag_text
from ..models import LLMScore, RecContext, Recommendation, Score, one_line
from ..pipeline import Provider

logger = logging.getLogger(__name__)

KEYWORD_MIN = 1
# 동시에 검색할 키워드 수, 검색 한 번에 받을 결과 수
FANOUT = 1
SEARCH_LIMIT = 10
CARD_LIMIT = 15
TIMEOUT_SEC = 10.0
MAX_TOKENS_QUERY = 150
MAX_TOKENS_SCORE = 120
# 휴리스틱 가중치 (합계 1.0)와 가점 도메인
WEIGHT_TITLE_MATCH = 0.4
WEIGHT_SNIPPET_MATCH = 0.3
WEIGHT_DOMAIN_TRUST = 0.3
TRUSTED_DOMAINS = [".edu", ".gov", "arxiv.org", "scholar.google.com", "stackoverflow.com", "github.com", "microsoft.com", "mozilla.org"]

# 네이버가 검색어 일치 부분을 <b> 태그로 감싸서 돌려줌
TAG_PATTERN = re.compile(r"<[^>]+>")

KEYWORD_PROMPT = """You are an expert search query generator for academic content.

Generate {keyword_min} specific search queries in {language} for the given lecture topic.

**Guidelines:**
- Use short technical phrases (2-4 words). Naver blog search returns few results for long queries
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

SCORE_PROMPT = """You are evaluating the relevance of a search result to a lecture topic.

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


@dataclass(frozen=True)
class BlogPost:
    """검색 결과 블로그 글."""

    title: str
    url: str
    snippet: str
    # 블로거 이름. 없으면 블로그 주소
    blogger: str


def _strip_html(text: str) -> str:
    return html.unescape(TAG_PATTERN.sub("", text or "")).strip()


class NaverBlogClient:
    """네이버 블로그 검색 API 클라이언트."""

    BASE_URL = "https://naverapihub.apigw.ntruss.com/search/v1/blog"
    MAX_DISPLAY = 100

    def __init__(self, client_id: str, client_secret: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        """클라이언트를 만든다.

        Args:
            client_id: NAVER API HUB Application의 Client ID
            client_secret: NAVER API HUB Application의 Client Secret
            transport: httpx 전송 계층. 테스트에서 실제 요청 대신 사용
        Raises:
            ValueError: 인증 정보가 비어 있는 경우
        """
        if not client_id or not client_secret:
            raise ValueError("NAVER_CLIENT_ID, NAVER_CLIENT_SECRET이 설정되지 않음")
        self.headers = {"X-NCP-APIGW-API-KEY-ID": client_id, "X-NCP-APIGW-API-KEY": client_secret}
        self.http_client = httpx.AsyncClient(timeout=TIMEOUT_SEC, transport=transport)

    async def close(self) -> None:
        """HTTP 연결을 닫는다."""
        await self.http_client.aclose()

    async def search(self, query: str, num: int = 10) -> List[BlogPost]:
        """블로그 글을 검색한다.

        Args:
            query: 검색어
            num: 결과 개수 (최대 100)
        Returns:
            검색 결과 목록. 제목과 요약의 HTML 태그는 지움. 실패하면 빈 목록
        """
        params = {"query": query, "display": min(num, self.MAX_DISPLAY), "sort": "sim"}
        try:
            response = await get_with_retry(self.http_client, self.BASE_URL, params=params, headers=self.headers)
            if response.status_code != 200:
                logger.error("네이버 블로그 검색 오류 (%d): %s", response.status_code, response.text[:200])
                return []
            items = response.json().get("items", [])
        except (httpx.HTTPError, ValueError) as exc:
            logger.error("네이버 블로그 검색 실패: %s", exc)
            return []
        return [
            BlogPost(
                title=_strip_html(item.get("title", "")),
                url=item.get("link", ""),
                snippet=_strip_html(item.get("description", "")),
                blogger=item.get("bloggername", "") or item.get("bloggerlink", ""),
            )
            for item in items
        ]


class BlogProvider(Provider[BlogPost]):
    """네이버 블로그 글 추천."""

    resource_type = ResourceType.BLOG
    verify_concurrency = 15

    def __init__(self, settings: BlogSettings, api: NaverBlogClient) -> None:
        super().__init__(settings)
        self.search_lang = settings.search_lang
        self.api = api

    async def close(self) -> None:
        await self.api.close()

    async def build_queries(self, context: RecContext) -> List[str]:
        context_text = ""
        if context.previous_summaries or context.rag_chunks:
            context_text = KEYWORD_CONTEXT_TEMPLATE.format(
                previous_summaries=previous_text(context), rag_context=rag_text(context)
            )
        prompt = KEYWORD_PROMPT.format(
            keyword_min=KEYWORD_MIN,
            language=self.search_lang,
            lecture_summary=context.summary,
            context=context_text,
        )
        try:
            content = await llm.complete(ModelPurpose.QUERY, [("user", prompt)], max_tokens=MAX_TOKENS_QUERY)
        except Exception:
            logger.exception("블로그 키워드 생성 실패")
            return context.summary.split()[:3]
        keywords = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().startswith("#")]
        return keywords[:FANOUT]

    async def find_candidates(self, queries: List[str], context: RecContext, search_round: Optional[str]) -> List[BlogPost]:
        searches = await asyncio.gather(*[self.search_shortening(keyword) for keyword in queries[:FANOUT]])
        posts = [post for found in searches for post in found]
        excluded = {_url_key(url) for url in context.excluded(self.resource_type)}
        posts = [post for post in _deduplicate(posts) if _url_key(post.url) not in excluded]
        return _rerank(posts, queries)[:CARD_LIMIT]

    async def search_shortening(self, keyword: str) -> List[BlogPost]:
        """결과가 없으면 마지막 단어를 하나씩 빼며 다시 검색한다.

        네이버 블로그 검색은 모든 단어가 들어간 글만 찾아, 전문 용어가 많은 키워드는 결과가 없을 수 있음.

        Args:
            keyword: LLM이 만든 검색 키워드
        Returns:
            검색 결과 목록. 한 단어까지 줄여도 없으면 빈 목록
        """
        words = keyword.split()
        while words:
            results = await self.api.search(query=" ".join(words), num=SEARCH_LIMIT)
            if results or len(words) == 1:
                return results
            words = words[:-1]
        return []

    async def llm_score(self, candidate: BlogPost, context: RecContext, queries: List[str]) -> Score:
        prompt = SCORE_PROMPT.format(
            lecture_summary=context.summary,
            title=candidate.title,
            snippet=candidate.snippet,
            url=candidate.url,
            language=self.language,
        )
        result = await llm.complete_json(ModelPurpose.VERIFY, [("user", prompt)], LLMScore, max_tokens=MAX_TOKENS_SCORE)
        return Score(result.score, result.reason)

    def heuristic_score(self, candidate: BlogPost, context: RecContext, queries: List[str]) -> Score:
        title, snippet = candidate.title.lower(), candidate.snippet.lower()
        per_match = 10.0 / len(queries)
        title_score = min(sum(per_match for q in queries if q.lower() in title), 10.0)
        snippet_score = min(sum(per_match for q in queries if q.lower() in snippet), 10.0)
        domain = candidate.blogger.lower()
        domain_score = 10.0 if any(trusted in domain for trusted in TRUSTED_DOMAINS) else 5.0
        score = title_score * WEIGHT_TITLE_MATCH + snippet_score * WEIGHT_SNIPPET_MATCH + domain_score * WEIGHT_DOMAIN_TRUST
        return Score(round(score, 2), "Heuristic")

    def to_recommendation(self, candidate: BlogPost, score: Score) -> Recommendation:
        detail = {
            "url": candidate.url,
            "title": one_line(candidate.title),
            "snippet": one_line(candidate.snippet[:300]),
            "display_link": candidate.blogger,
            "lang": self.language,
        }
        return Recommendation(
            type=self.resource_type,
            title=detail["title"],
            url=detail["url"],
            description=detail["snippet"],
            score=score.score,
            reason=one_line(score.reason),
            detail=detail,
        )


def _url_key(url: str) -> str:
    # 프로토콜과 www를 빼고 비교
    parsed = urlparse(url)
    return f"{parsed.netloc.replace('www.', '')}{parsed.path}"


def _deduplicate(posts: List[BlogPost]) -> List[BlogPost]:
    seen, unique = set(), []
    for post in posts:
        if post.url and _url_key(post.url) not in seen:
            seen.add(_url_key(post.url))
            unique.append(post)
    return unique


def _rerank(posts: List[BlogPost], keywords: List[str]) -> List[BlogPost]:
    lowered = [k.lower() for k in keywords]

    def match_score(post: BlogPost) -> float:
        title, snippet = post.title.lower(), post.snippet.lower()
        return sum((2.0 if k in title else 0.0) + (1.0 if k in snippet else 0.0) for k in lowered)

    return sorted(posts, key=match_score, reverse=True)
