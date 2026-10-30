"""
위키백과 문서 추천

검색어: LLM이 검색 언어로 키워드 2~3개를 만든다
후보: 키워드별 동시 검색 → 중복 제거 → 제외 → 재정렬 → 문서 도입부 조회 (동음이의어 문서 제외)
회차: 검색 언어판에서 top_k를 못 채우면 다른 언어판(en ↔ ko)으로 부족분을 채운다
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from textwrap import shorten
from typing import Any, Dict, List, Optional, Sequence

import httpx

from core import llm
from core.llm import ModelPurpose
from core.schemas import ResourceType

from ..models import RecContext, Recommendation, Score, one_line
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

# 위키백과는 요청이 몰리면 429로 거절하므로 프로세스 전체 동시 요청 수를 제한하고, 거절되면 기다렸다 다시 시도함
MAX_CONCURRENT_REQUESTS = 4
MAX_RETRIES = 3
RETRY_STATUSES = {429, 503}
MAX_RETRY_WAIT_SEC = 10.0
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


def _semaphore() -> asyncio.Semaphore:
    # 세마포어는 이벤트 루프에 묶이므로 루프마다 따로 만듦
    loop_id = id(asyncio.get_running_loop())
    if loop_id not in _semaphores:
        _semaphores[loop_id] = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    return _semaphores[loop_id]


def retry_wait_seconds(response: httpx.Response, attempt: int) -> float:
    """다시 시도하기 전 기다릴 시간을 정한다. Retry-After(초)가 있으면 따르고, 없으면 1·2·4초로 늘린다.

    Args:
        response: 거절 응답
        attempt: 지금까지 시도 횟수 (1부터)
    Returns:
        대기 시간(초). 최대 10초
    """
    header = response.headers.get("Retry-After", "")
    wait = float(header) if header.replace(".", "", 1).isdigit() else 2.0 ** (attempt - 1)
    return min(wait, MAX_RETRY_WAIT_SEC)


class WikiClient:
    """위키백과 검색·문서 조회 클라이언트."""

    BASE_URL = "https://{lang}.wikipedia.org/w/api.php"

    def __init__(self, user_agent: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        """클라이언트를 만든다.

        Args:
            user_agent: 위키백과 API 정책상 연락처를 담은 User-Agent
            transport: httpx 전송 계층. 테스트에서 가짜 응답을 넣을 때 사용
        """
        self.user_agent = user_agent
        self._transport = transport

    async def _get_json(self, lang: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """위키백과 API를 호출한다. 429·503이면 기다렸다가 최대 3번 다시 시도한다.

        Args:
            lang: 위키백과 언어판 (en/ko)
            params: 쿼리 파라미터
        Returns:
            응답 JSON
        Raises:
            httpx.HTTPStatusError: 재시도 후에도 실패하거나 다른 오류 상태인 경우
        """
        url = self.BASE_URL.format(lang=lang)
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SEC,
            headers={"User-Agent": self.user_agent, "Accept": "application/json"},
            transport=self._transport,
        ) as client:
            for attempt in range(1, MAX_RETRIES + 2):
                async with _semaphore():
                    response = await client.get(url, params=params)
                if response.status_code not in RETRY_STATUSES or attempt > MAX_RETRIES:
                    response.raise_for_status()
                    return response.json()
                wait = retry_wait_seconds(response, attempt)
                logger.warning("위키백과 %d, %.1f초 후 재시도 (%d/%d)", response.status_code, wait, attempt, MAX_RETRIES)
                await asyncio.sleep(wait)
        raise RuntimeError("unreachable")

    async def search_pages(self, keyword: str, lang: str = "en", limit: int = 6) -> List[Dict[str, Any]]:
        """키워드로 문서를 검색한다.

        Args:
            keyword: 검색 키워드
            lang: 언어판 (en/ko)
            limit: 결과 개수
        Returns:
            [{"title", "pageid", "snippet"}, ...]. 실패하면 빈 목록
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
            return (await self._get_json(lang, params)).get("query", {}).get("search", [])
        except Exception as exc:
            logger.error("위키백과 검색 실패 (keyword=%r, lang=%s): %s", keyword, lang, exc)
            return []

    async def get_page_extract(self, page_id: int, lang: str = "en") -> Optional[Dict[str, Any]]:
        """문서 도입부를 조회한다.

        Args:
            page_id: 문서 ID
            lang: 언어판 (en/ko)
        Returns:
            {"title", "extract", "url", "pageid", "disambiguation"}. 문서가 없거나 실패하면 None
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
        return {
            "title": page.get("title", ""),
            "extract": page.get("extract", ""),
            "url": page.get("fullurl", f"https://{lang}.wikipedia.org/?curid={page_id}"),
            "pageid": page_id,
            "disambiguation": "disambiguation" in page.get("pageprops", {}),
        }


class WikiProvider(Provider[Dict[str, Any]]):
    """위키백과 문서 추천."""

    resource_type = ResourceType.WIKI
    verify_concurrency = 10

    def __init__(
        self, top_k: int, verify: bool, min_score: float, language: str, wiki_lang: str, fallback_to_ko: bool, api: WikiClient
    ) -> None:
        super().__init__(top_k, verify, min_score, language)
        self.wiki_lang = wiki_lang
        self.fallback_to_ko = fallback_to_ko
        self.api = api

    async def build_queries(self, context: RecContext) -> List[str]:
        prompt = KEYWORD_PROMPT.format(
            lecture_summary=context.summary,
            search_language=self.wiki_lang,
            previous_summaries=_previous_text(context),
            rag_context=_rag_text(context),
        )
        try:
            content = await llm.complete(ModelPurpose.QUERY, [("user", prompt)], max_tokens=MAX_TOKENS_QUERY, json_mode=True)
            return json.loads(content).get("keywords", [])
        except Exception:
            logger.exception("위키 키워드 생성 실패")
            return context.summary.split()[:3]

    def search_rounds(self) -> Sequence[Optional[str]]:
        if not self.fallback_to_ko:
            return [self.wiki_lang]
        return [self.wiki_lang, "ko" if self.wiki_lang == "en" else "en"]

    async def find_candidates(self, queries: List[str], context: RecContext, search_round: Optional[str]) -> List[Dict[str, Any]]:
        lang = search_round or self.wiki_lang
        searches = await asyncio.gather(
            *[self.api.search_pages(keyword, lang, SEARCH_LIMIT) for keyword in queries[:FANOUT]], return_exceptions=True
        )
        pages = [page for result in searches if not isinstance(result, Exception) for page in result]
        excluded = {title.lower() for title in context.excluded(self.resource_type)}
        pages = [p for p in _deduplicate(pages) if p.get("title", "").lower() not in excluded]
        return await self.fetch_details(_rerank(pages, queries), lang)

    async def fetch_details(self, search_results: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
        """검색 결과마다 문서 도입부를 동시에 조회한다. 동음이의어 문서는 다른 문서 목록일 뿐이라 뺀다.

        Args:
            search_results: 검색 결과 목록
            lang: 언어판
        Returns:
            조회에 성공한 문서 목록 (검색 결과 순서). 검색 결과의 snippet을 함께 담음
        """
        semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)

        async def fetch(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            async with semaphore:
                page = await self.api.get_page_extract(result.get("pageid"), lang)
            if not page or page.get("disambiguation"):
                return None
            return {**page, "snippet": result.get("snippet", "")}

        pages = await asyncio.gather(*[fetch(r) for r in search_results], return_exceptions=True)
        return [p for p in pages if isinstance(p, dict)]

    async def llm_score(self, candidate: Dict[str, Any], context: RecContext, queries: List[str]) -> Score:
        extract = candidate.get("extract", "")[:300].replace("\n", " ").replace('"', "'").strip()
        prompt = SCORE_PROMPT.format(
            lecture_summary=context.summary, title=candidate.get("title", ""), extract=extract, language=self.language
        )
        try:
            content = await llm.complete(
                ModelPurpose.VERIFY,
                [("system", "Return only valid JSON."), ("user", prompt)],
                max_tokens=MAX_TOKENS_SCORE,
                json_mode=True,
            )
            result = _parse_score_json(content)
            return Score(float(result.get("score", 5.0)), result.get("reason", "LLM evaluation"))
        except Exception:
            logger.exception("위키 문서 검증 실패")
            return Score(5.0, "Scoring failed")

    def heuristic_score(self, candidate: Dict[str, Any], context: RecContext, queries: List[str]) -> Score:
        title = candidate.get("title", "").lower()
        extract = candidate.get("extract", "").lower()
        score = 5.0
        for keyword in (q.lower() for q in queries):
            if keyword in title:
                score += 2.0
            elif keyword in extract:
                score += 0.5
        return Score(min(score, 10.0), "Heuristic")

    def to_recommendation(self, candidate: Dict[str, Any], score: Score) -> Recommendation:
        detail = {
            "url": candidate.get("url", ""),
            "title": one_line(candidate.get("title", "")),
            "extract": one_line(candidate.get("extract", "")),
            "lang": self.wiki_lang,
            "page_id": candidate.get("pageid", 0),
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


def _previous_text(context: RecContext) -> str:
    lines = [f"[{ps.section_id}] " + shorten(ps.summary, width=120, placeholder="…") for ps in context.previous_summaries[-2:]]
    return "\n".join(lines) or "None"


def _rag_text(context: RecContext) -> str:
    lines = [f"{shorten(c.text, width=120, placeholder='…')} (score≈{c.score:.2f})" for c in context.rag_chunks[:2] if c.text]
    return "\n".join(lines) or "None"


def _deduplicate(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen, unique = set(), []
    for page in pages:
        title = page.get("title", "").lower().strip()
        if title and title not in seen:
            seen.add(title)
            unique.append(page)
    return unique


def _rerank(pages: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    lowered = [k.lower() for k in keywords]

    def match_score(page: Dict[str, Any]) -> float:
        title, snippet = page.get("title", "").lower(), page.get("snippet", "").lower()
        return sum(2.0 if k in title else 0.5 if k in snippet else 0.0 for k in lowered)

    return sorted(pages, key=match_score, reverse=True)


def _parse_score_json(text: str) -> Dict[str, Any]:
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.replace("\n", " ").replace("\r", " ").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        score = re.search(r'"?score"?\s*:\s*(\d+(?:\.\d+)?)', text)
        reason = re.search(r'"?reason"?\s*:\s*"([^"]*)"', text)
        return {
            "score": float(score.group(1)) if score else 5.0,
            "reason": reason.group(1) if reason else "Parsing failed",
        }
