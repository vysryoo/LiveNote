"""
위키백과 문서 추천

검색어: LLM이 검색 언어로 키워드 2~3개를 만든다
후보: 키워드별 동시 검색 → 중복 제거 → 제외 → 재정렬 → 문서 도입부 조회 (동음이의어 문서 제외)
회차: 검색 언어판에서 top_k를 못 채우면 다른 언어판(en ↔ ko)으로 부족분을 채운다
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Sequence

import httpx
from pydantic import BaseModel

from core import llm
from core.config import WikiSettings
from core.http import get_with_retry
from core.llm import ModelPurpose
from core.schemas import ResourceType

from ..context import previous_text, rag_text
from ..models import LLMScore, RecContext, Recommendation, Score, one_line, to_prompt_line
from ..pipeline import Provider

logger = logging.getLogger(__name__)

KEYWORD_MIN = 2
KEYWORD_MAX = 3
# 동시에 검색할 키워드 수, 키워드 하나로 가져올 문서 수
FANOUT = 3
SEARCH_LIMIT = 3
# 문서 도입부에서 가져올 문장 수
EXTRACT_SENTENCES = 3
DETAIL_CONCURRENCY = 12
TIMEOUT_SEC = 15
MAX_TOKENS_QUERY = 100
MAX_TOKENS_SCORE = 80

# 위키백과는 요청이 몰리면 429로 거절하므로 프로세스 전체 동시 요청 수를 제한함
MAX_CONCURRENT_REQUESTS = 4
_semaphores: Dict[int, asyncio.Semaphore] = {}

KEYWORD_PROMPT = f"""Extract {KEYWORD_MIN}-{KEYWORD_MAX} Wikipedia search keywords from this lecture summary and related context.

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

SCORE_PROMPT = """Lecture: {lecture_summary}

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


class WikiKeywords(BaseModel):
    """검색 키워드 응답 형식."""

    keywords: List[str]


@dataclass(frozen=True)
class WikiSearchHit:
    """검색 결과 문서."""

    page_id: int
    title: str
    # 검색어 일치 부분. 위키백과가 HTML 태그를 붙여 돌려줌
    snippet: str


@dataclass(frozen=True)
class WikiPage:
    """점수를 매길 문서. snippet은 이 문서를 찾은 검색 결과의 일치 부분이다."""

    page_id: int
    title: str
    extract: str
    url: str
    disambiguation: bool
    snippet: str = ""


def _semaphore() -> asyncio.Semaphore:
    # 세마포어는 이벤트 루프에 묶이므로 루프마다 따로 만듦
    loop_id = id(asyncio.get_running_loop())
    if loop_id not in _semaphores:
        _semaphores[loop_id] = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    return _semaphores[loop_id]


class WikiClient:
    """위키백과 검색·문서 조회 클라이언트."""

    BASE_URL = "https://{lang}.wikipedia.org/w/api.php"

    def __init__(self, user_agent: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        """클라이언트를 만든다.

        Args:
            user_agent: 위키백과 API 정책상 연락처를 담은 User-Agent
            transport: httpx 전송 계층. 테스트에서 가짜 응답을 넣을 때 사용
        """
        self.http_client = httpx.AsyncClient(
            timeout=TIMEOUT_SEC,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
            transport=transport,
        )

    async def close(self) -> None:
        """HTTP 연결을 닫는다."""
        await self.http_client.aclose()

    async def _get_json(self, lang: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """위키백과 API를 호출한다. 429·503이면 기다렸다가 다시 시도한다 (core.http).

        Args:
            lang: 위키백과 언어판 (en/ko)
            params: 쿼리 파라미터
        Returns:
            응답 JSON
        Raises:
            httpx.HTTPStatusError: 재시도 후에도 실패하거나 다른 오류 상태인 경우
        """
        response = await get_with_retry(self.http_client, self.BASE_URL.format(lang=lang), params=params, limiter=_semaphore())
        response.raise_for_status()
        return response.json()

    async def search_pages(self, keyword: str, lang: str = "en", limit: int = 6) -> List[WikiSearchHit]:
        """키워드로 문서를 검색한다.

        Args:
            keyword: 검색 키워드
            lang: 언어판 (en/ko)
            limit: 결과 개수
        Returns:
            검색 결과 목록. 실패하면 빈 목록
        """
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": keyword,
            "srlimit": limit,
            "srprop": "snippet|titlesnippet",
            "uselang": lang,
        }
        try:
            hits = (await self._get_json(lang, params)).get("query", {}).get("search", [])
            return [
                WikiSearchHit(page_id=hit.get("pageid"), title=hit.get("title", ""), snippet=hit.get("snippet", ""))
                for hit in hits
            ]
        except Exception as exc:
            logger.error("위키백과 검색 실패 (keyword=%r, lang=%s): %s", keyword, lang, exc)
            return []

    async def get_page_extract(self, page_id: int, lang: str = "en") -> Optional[WikiPage]:
        """문서 도입부를 조회한다.

        Args:
            page_id: 문서 ID
            lang: 언어판 (en/ko)
        Returns:
            문서 도입부 (snippet은 빈 값). 문서가 없거나 실패하면 None
        """
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|info|pageprops",
            # 동음이의어 문서 여부. 언어판과 관계없이 같은 속성으로 표시됨
            "ppprop": "disambiguation",
            "pageids": page_id,
            "exintro": True,
            "explaintext": True,
            "exsentences": EXTRACT_SENTENCES,
            "inprop": "url",
            "uselang": lang,
        }
        try:
            page = (await self._get_json(lang, params)).get("query", {}).get("pages", {}).get(str(page_id))
        except Exception as exc:
            logger.error("위키백과 문서 조회 실패 (pageid=%s, lang=%s): %s", page_id, lang, exc)
            return None
        if not page or page.get("missing"):
            return None
        return WikiPage(
            page_id=page_id,
            title=page.get("title", ""),
            extract=page.get("extract", ""),
            url=page.get("fullurl", f"https://{lang}.wikipedia.org/?curid={page_id}"),
            disambiguation="disambiguation" in page.get("pageprops", {}),
        )


class WikiProvider(Provider[WikiPage]):
    """위키백과 문서 추천."""

    resource_type = ResourceType.WIKI
    verify_concurrency = 10

    def __init__(self, settings: WikiSettings, api: WikiClient) -> None:
        super().__init__(settings)
        self.search_lang = settings.search_lang
        self.fallback_to_other_lang = settings.fallback_to_other_lang
        self.api = api

    async def close(self) -> None:
        await self.api.close()

    async def build_queries(self, context: RecContext) -> List[str]:
        prompt = KEYWORD_PROMPT.format(
            lecture_summary=context.summary,
            search_language=self.search_lang,
            previous_summaries=previous_text(context),
            rag_context=rag_text(context),
        )
        try:
            result = await llm.complete_json(ModelPurpose.QUERY, [("user", prompt)], WikiKeywords, max_tokens=MAX_TOKENS_QUERY)
            return result.keywords
        except Exception:
            logger.exception("위키 키워드 생성 실패")
            return context.summary.split()[:3]

    def search_rounds(self) -> Sequence[Optional[str]]:
        if not self.fallback_to_other_lang:
            return [self.search_lang]
        return [self.search_lang, "ko" if self.search_lang == "en" else "en"]

    async def find_candidates(self, queries: List[str], context: RecContext, search_round: Optional[str]) -> List[WikiPage]:
        lang = search_round or self.search_lang
        searches = await asyncio.gather(
            *[self.api.search_pages(keyword, lang, SEARCH_LIMIT) for keyword in queries[:FANOUT]], return_exceptions=True
        )
        hits = [hit for result in searches if not isinstance(result, Exception) for hit in result]
        excluded = {title.lower() for title in context.excluded(self.resource_type)}
        hits = [hit for hit in _deduplicate(hits) if hit.title.lower() not in excluded]
        return await self.fetch_details(_rerank(hits, queries), lang)

    async def fetch_details(self, search_results: List[WikiSearchHit], lang: str) -> List[WikiPage]:
        """검색 결과마다 문서 도입부를 동시에 조회한다. 동음이의어 문서는 다른 문서 목록일 뿐이라 뺀다.

        Args:
            search_results: 검색 결과 목록
            lang: 언어판
        Returns:
            조회에 성공한 문서 목록 (검색 결과 순서). 검색 결과의 snippet을 함께 담음
        """
        semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)

        async def fetch(hit: WikiSearchHit) -> Optional[WikiPage]:
            async with semaphore:
                page = await self.api.get_page_extract(hit.page_id, lang)
            if not page or page.disambiguation:
                return None
            return replace(page, snippet=hit.snippet)

        pages = await asyncio.gather(*[fetch(hit) for hit in search_results], return_exceptions=True)
        return [p for p in pages if isinstance(p, WikiPage)]

    async def llm_score(self, candidate: WikiPage, context: RecContext, queries: List[str]) -> Score:
        prompt = SCORE_PROMPT.format(
            lecture_summary=context.summary,
            title=candidate.title,
            extract=to_prompt_line(candidate.extract[:300]),
            language=self.language,
        )
        result = await llm.complete_json(
            ModelPurpose.VERIFY,
            [("system", "Return only valid JSON."), ("user", prompt)],
            LLMScore,
            max_tokens=MAX_TOKENS_SCORE,
        )
        return Score(result.score, result.reason)

    def heuristic_score(self, candidate: WikiPage, context: RecContext, queries: List[str]) -> Score:
        title = candidate.title.lower()
        extract = candidate.extract.lower()
        score = 5.0
        for keyword in (q.lower() for q in queries):
            if keyword in title:
                score += 2.0
            elif keyword in extract:
                score += 0.5
        return Score(min(score, 10.0), "Heuristic")

    def to_recommendation(self, candidate: WikiPage, score: Score) -> Recommendation:
        detail = {
            "url": candidate.url,
            "title": one_line(candidate.title),
            "extract": one_line(candidate.extract),
            "lang": self.search_lang,
            "page_id": candidate.page_id,
        }
        return Recommendation(
            type=self.resource_type,
            title=detail["title"],
            url=detail["url"],
            description=detail["extract"],
            score=score.score,
            reason=one_line(score.reason),
            detail=detail,
        )


def _deduplicate(hits: List[WikiSearchHit]) -> List[WikiSearchHit]:
    seen, unique = set(), []
    for hit in hits:
        title = hit.title.lower().strip()
        if title and title not in seen:
            seen.add(title)
            unique.append(hit)
    return unique


def _rerank(hits: List[WikiSearchHit], keywords: List[str]) -> List[WikiSearchHit]:
    lowered = [k.lower() for k in keywords]

    def match_score(hit: WikiSearchHit) -> float:
        title, snippet = hit.title.lower(), hit.snippet.lower()
        return sum(2.0 if k in title else 0.5 if k in snippet else 0.0 for k in lowered)

    return sorted(hits, key=match_score, reverse=True)
