"""
논문 추천 (OpenAlex)

검색어: LLM이 학술 검색용 영문 토큰 2~3개를 만든다
후보: OpenAlex 검색 → 중복 제거 → 키워드 일치로 재정렬 → 상위 CARD_LIMIT개
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from core import llm
from core.http import get_with_retry
from core.llm import ModelPurpose
from core.schemas import ResourceType

from ..context import previous_text, rag_text
from ..models import LLMScore, RecContext, Recommendation, Score
from ..pipeline import Provider

logger = logging.getLogger(__name__)

TOKEN_MIN = 2
TOKEN_MAX = 3
CARD_LIMIT = 13
ABSTRACT_MAX_LENGTH = 400
PER_PAGE = 40
TIMEOUT_SEC = 15
MAX_TOKENS_QUERY = 150
MAX_TOKENS_SCORE = 200

QUERY_PROMPT = f"""You are to produce terse technical search tokens for OpenAlex.

Current section summary:
{{section_summary}}

Previous sections context:
{{previous_summaries}}

RAG context:
{{rag_context}}

Return a JSON with {TOKEN_MIN}~{TOKEN_MAX} technical English tokens suitable for academic paper search:
{{{{
  "tokens": ["term1", "term2", ...]
}}}}

Rules:
- Extract core concepts and technical terms from all provided context
- Use precise academic terminology
- Expand abbreviations where needed
- Include field-specific keywords
- Keep it concise ({TOKEN_MIN}-{TOKEN_MAX} tokens max)
"""

SCORE_PROMPT = """Current section summary: {section_summary}

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


class PaperQuery(BaseModel):
    """검색 토큰 응답 형식."""

    tokens: List[str]


class OpenAlexClient:
    """OpenAlex works 검색 클라이언트."""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        """클라이언트를 만든다.

        Args:
            transport: httpx 전송 계층. 테스트에서 가짜 응답을 넣을 때 사용
        """
        self.http_client = httpx.AsyncClient(
            timeout=TIMEOUT_SEC,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            http2=True,
            transport=transport,
        )

    async def search_papers(self, query: Dict[str, Any], exclude_ids: Optional[List[str]] = None, sort_by: str = "relevance") -> List[Dict]:
        """논문을 검색한다.

        Args:
            query: {"tokens", "year_from"}
            exclude_ids: 제외할 논문 ID·URL 일부 문자열
            sort_by: relevance(연관성순), cited_by_count(인용순), hybrid(연관성 상위 60% 안에서 인용순)
        Returns:
            논문 목록. 초록이 없고 인용 100회 미만인 논문은 뺌. 실패하면 빈 목록
        """
        search = " ".join(query.get("tokens", []))
        filters = [
            f"from_publication_date:{query['year_from']}-01-01",
            "language:en",
            "is_paratext:false",
            "type:article",
        ]
        params = {
            "search": search,
            "filter": ",".join(filters),
            "sort": "cited_by_count:desc" if sort_by == "cited_by_count" else "relevance_score:desc",
            # hybrid는 넉넉히 받은 뒤 다시 거름
            "per_page": PER_PAGE * 2 if sort_by == "hybrid" else PER_PAGE,
        }
        try:
            response = await get_with_retry(self.http_client, f"{self.BASE_URL}/works", params=params)
            response.raise_for_status()
            works = response.json().get("results", [])
        except httpx.HTTPError as exc:
            logger.error("OpenAlex 검색 실패: %s", exc)
            return []

        exclude_tokens = [e.lower() for e in exclude_ids or []]
        papers = []
        for work in works:
            paper = _parse_work(work)
            if paper is None:
                continue
            ids = f"{paper['id']} {paper['url']}".lower()
            if any(token in ids for token in exclude_tokens):
                continue
            papers.append(paper)

        if sort_by == "hybrid" and papers:
            threshold = max(p["relevance_score"] for p in papers) * 0.6
            relevant = sorted((p for p in papers if p["relevance_score"] >= threshold), key=lambda p: p["cited_by_count"], reverse=True)
            papers = relevant[:PER_PAGE]
        logger.info("OpenAlex 검색: %r → %d개", search, len(papers))
        return papers

    async def close(self) -> None:
        """HTTP 연결을 닫는다."""
        await self.http_client.aclose()


class PaperProvider(Provider[Dict[str, Any]]):
    """OpenAlex 논문 추천."""

    resource_type = ResourceType.PAPER
    verify_concurrency = 20

    def __init__(self, top_k: int, verify: bool, min_score: float, language: str, year_from: int, sort_by: str, api=None) -> None:
        super().__init__(top_k, verify, min_score, language)
        self.year_from = year_from
        self.sort_by = sort_by
        self.api = api or OpenAlexClient()

    async def build_queries(self, context: RecContext) -> List[str]:
        prompt = QUERY_PROMPT.format(
            section_summary=context.summary, previous_summaries=previous_text(context), rag_context=rag_text(context)
        )
        try:
            query = await llm.complete_json(ModelPurpose.QUERY, [("user", prompt)], PaperQuery, max_tokens=MAX_TOKENS_QUERY)
        except Exception:
            logger.exception("논문 검색어 생성 실패")
            return []
        return query.tokens

    async def find_candidates(self, queries: List[str], context: RecContext, search_round: Optional[str]) -> List[Dict[str, Any]]:
        query = {"tokens": queries, "year_from": self.year_from}
        papers = await self.api.search_papers(query=query, exclude_ids=context.excluded(self.resource_type), sort_by=self.sort_by)
        return _rerank(_deduplicate(papers), queries)[:CARD_LIMIT]

    async def llm_score(self, candidate: Dict[str, Any], context: RecContext, queries: List[str]) -> Score:
        prompt = SCORE_PROMPT.format(
            section_summary=_clean(context.summary),
            keywords=", ".join(queries),
            title=_clean(candidate.get("title", "")),
            abstract=_clean(candidate.get("abstract", ""))[:ABSTRACT_MAX_LENGTH],
            year=candidate.get("year", "N/A"),
            cited_by_count=candidate.get("cited_by_count", 0),
            language=self.language,
        )
        result = await llm.complete_json(ModelPurpose.VERIFY, [("user", prompt)], LLMScore, max_tokens=MAX_TOKENS_SCORE)
        return Score(result.score, result.reason)

    def heuristic_score(self, candidate: Dict[str, Any], context: RecContext, queries: List[str]) -> Score:
        title = candidate.get("title", "").lower()
        abstract = candidate.get("abstract", "").lower()
        score = 5.0
        for token in (q.lower() for q in queries):
            score += (0.5 if token in title else 0.0) + (0.2 if token in abstract else 0.0)
        score += min(candidate.get("relevance_score", 0) / 10, 2.0)
        return Score(min(score, 10.0), "Heuristic")

    def to_recommendation(self, candidate: Dict[str, Any], score: Score) -> Recommendation:
        detail = {
            "url": candidate.get("url", ""),
            "title": candidate.get("title", ""),
            "abstract": candidate.get("abstract", "")[:ABSTRACT_MAX_LENGTH],
            "year": candidate.get("year"),
            "cited_by_count": candidate.get("cited_by_count", 0),
            "authors": candidate.get("authors", []),
        }
        return Recommendation(
            type=self.resource_type,
            title=detail["title"],
            url=detail["url"],
            description=detail["abstract"],
            score=score.score,
            reason=score.reason,
            detail=detail,
        )

    async def close(self) -> None:
        await self.api.close()


def _parse_work(work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    abstract = _abstract_text(work.get("abstract_inverted_index"))
    cited_by_count = work.get("cited_by_count", 0)
    no_abstract = len(abstract.strip()) < 50
    if no_abstract and cited_by_count < 100:
        return None
    paper_id = work.get("id", "")
    return {
        "id": paper_id,
        "title": work.get("title", ""),
        "abstract": abstract,
        "year": work.get("publication_year"),
        "cited_by_count": cited_by_count,
        "url": work.get("doi") or paper_id,
        "authors": [a["author"]["display_name"] for a in work.get("authorships", [])[:5] if a.get("author", {}).get("display_name")],
        "no_abstract": no_abstract,
        "relevance_score": work.get("relevance_score", 0.0),
    }


def _abstract_text(inverted_index: Optional[Dict[str, List[int]]]) -> str:
    # OpenAlex는 초록을 {단어: [위치, ...]} 역색인으로 줌
    if not inverted_index:
        return ""
    positions = sorted((pos, word) for word, places in inverted_index.items() for pos in places)
    return " ".join(word for _, word in positions)[:ABSTRACT_MAX_LENGTH]


def _deduplicate(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen, unique = set(), []
    for paper in papers:
        url = paper.get("url", "")
        key = url if url.startswith("http") else re.sub(r"[^\w\s]", "", paper.get("title", "").lower()).strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(paper)
    return unique


def _rerank(papers: List[Dict[str, Any]], tokens: List[str]) -> List[Dict[str, Any]]:
    lowered = [t.lower() for t in tokens]

    def match_score(paper: Dict[str, Any]) -> int:
        title, abstract = paper.get("title", "").lower(), paper.get("abstract", "").lower()
        return sum((3 if t in title else 0) + (1 if t in abstract else 0) for t in lowered)

    return sorted(papers, key=lambda p: (match_score(p), p.get("relevance_score", 0)), reverse=True)


def _clean(text: str) -> str:
    # 프롬프트의 JSON 예시가 깨지지 않도록 줄바꿈과 큰따옴표를 바꿈
    return text.replace("\n", " ").replace('"', "'").strip()
