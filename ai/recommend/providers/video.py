"""
YouTube 영상 추천

검색어: LLM이 학생이 검색창에 칠 법한 2~5단어 검색어 1개를 만든다
후보: 검색 → 제목 정규화 후 제외·중복 제거 → 영상 상세 조회
준비: 후보마다 LLM이 제목·설명으로 영상 내용을 2문장 요약 (카드 설명)
점수: 상세 정보가 있으면 LLM 검증 또는 휴리스틱(제목 유사도·조회수·최신성). 상세 정보가 없으면 휴리스틱만
"""
from __future__ import annotations

import asyncio
import math
import re
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel
from rapidfuzz import fuzz

from core import llm
from core.http import get_with_retry
from core.llm import ModelPurpose
from core.schemas import ResourceType

from ..models import LLMScore, RecContext, Recommendation, Score, one_line
from ..pipeline import Provider

QUERY_MIN = 1
QUERY_MAX = 1
MAX_SEARCH_RESULTS = 10
TIMEOUT_SEC = 10
MAX_TOKENS_QUERY = 300
MAX_TOKENS_SUMMARY = 400
MAX_TOKENS_SCORE = 300
MAX_DESCRIPTION_LENGTH = 500
# 휴리스틱 가중치 (합계 1.0)
WEIGHT_TITLE_MATCH = 0.5
WEIGHT_VIEWS = 0.3
WEIGHT_RECENCY = 0.2

QUERY_PROMPT = """
Generate {query_min} YouTube search queries (use {query_language}) focused on: "{lecture_summary}"

Settings:
- Query language: {query_language}
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
Each query must be 2-5 words, like what a student types into YouTube search. Do not list every concept from the summary.
""".strip()

SUMMARY_PROMPT = """
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

SCORE_PROMPT = """
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


class VideoQueries(BaseModel):
    """검색어 응답 형식."""

    queries: List[str]
    rationale: str


class VideoSummary(BaseModel):
    """영상 내용 요약 응답 형식."""

    extract: str


@dataclass(frozen=True)
class YouTubeSearchItem:
    """검색 결과 영상."""

    video_id: str
    title: str
    description: str
    channel_title: str
    publish_time: str


@dataclass(frozen=True)
class YouTubeVideoDetail:
    """영상 상세 정보."""

    video_id: str
    title: str
    description: str
    default_lang: Optional[str]
    view_count: int
    duration_iso8601: Optional[str]
    channel_title: str
    publish_time: str

    def url(self) -> str:
        """영상 주소를 돌려준다."""
        return f"https://www.youtube.com/watch?v={self.video_id}"


@dataclass(frozen=True)
class VideoCandidate:
    """점수를 매길 영상. 상세 조회에 실패한 영상은 detail이 None이다."""

    item: YouTubeSearchItem
    detail: Optional[YouTubeVideoDetail]
    extract: str = ""


class YouTubeClient:
    """YouTube Data API v3 클라이언트."""

    BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        """클라이언트를 만든다.

        Args:
            api_key: YouTube Data API 키
            transport: httpx 전송 계층. 테스트에서 가짜 응답을 넣을 때 사용
        """
        self.api_key = api_key
        self.http_client = httpx.AsyncClient(timeout=TIMEOUT_SEC, transport=transport)

    def _auth_headers(self) -> Dict[str, str]:
        # 키를 URL 쿼리에 넣으면 요청 실패 시 오류 메시지와 로그에 URL째 남으므로 헤더로 보냄
        return {"X-Goog-Api-Key": self.api_key}

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = await get_with_retry(self.http_client, f"{self.BASE}/{path}", params=params, headers=self._auth_headers())
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """HTTP 연결을 닫는다."""
        await self.http_client.aclose()

    async def search_videos(self, q: str, lang: str, max_results: int = 8) -> List[YouTubeSearchItem]:
        """영상을 검색한다.

        Args:
            q: 검색어
            lang: 선호 언어 (relevanceLanguage)
            max_results: 결과 개수
        Returns:
            검색 결과 목록
        Raises:
            httpx.HTTPStatusError: API 오류 응답
        """
        data = await self._get("search", {"part": "snippet", "type": "video", "q": q, "relevanceLanguage": lang, "maxResults": max_results})
        items = []
        for it in data.get("items", []):
            video_id, snippet = it.get("id", {}).get("videoId"), it.get("snippet", {})
            if video_id and snippet:
                items.append(YouTubeSearchItem(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    channel_title=snippet.get("channelTitle", ""),
                    publish_time=snippet.get("publishedAt", ""),
                ))
        return items

    async def get_videos(self, ids: List[str]) -> List[YouTubeVideoDetail]:
        """영상 상세 정보를 조회한다.

        Args:
            ids: 영상 ID 목록
        Returns:
            조회된 영상 목록
        Raises:
            httpx.HTTPStatusError: API 오류 응답
        """
        if not ids:
            return []
        data = await self._get("videos", {"part": "snippet,contentDetails,statistics", "id": ",".join(ids)})
        details = []
        for it in data.get("items", []):
            snippet, stats = it.get("snippet", {}), it.get("statistics", {})
            if it.get("id"):
                details.append(YouTubeVideoDetail(
                    video_id=it["id"],
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    default_lang=snippet.get("defaultLanguage") or snippet.get("defaultAudioLanguage"),
                    view_count=int(stats.get("viewCount", 0)),
                    duration_iso8601=it.get("contentDetails", {}).get("duration"),
                    channel_title=snippet.get("channelTitle", ""),
                    publish_time=snippet.get("publishedAt", ""),
                ))
        return details


class VideoProvider(Provider[VideoCandidate]):
    """YouTube 영상 추천."""

    resource_type = ResourceType.VIDEO
    verify_concurrency = 20

    def __init__(self, top_k: int, verify: bool, min_score: float, language: str, yt_lang: str, api: YouTubeClient) -> None:
        super().__init__(top_k, verify, min_score, language)
        self.yt_lang = yt_lang
        self.api = api

    async def close(self) -> None:
        await self.api.close()

    async def build_queries(self, context: RecContext) -> List[str]:
        prompt = QUERY_PROMPT.format(
            query_min=QUERY_MIN,
            query_max=QUERY_MAX,
            lecture_summary=context.summary,
            query_language=self.yt_lang or self.language or "en",
            yt_lang=self.yt_lang,
            previous_summaries=[s.model_dump() for s in context.previous_summaries],
            rag_context=[c.model_dump() for c in context.rag_chunks],
        )
        result = await llm.complete_json(ModelPurpose.QUERY, [("user", prompt)], VideoQueries, max_tokens=MAX_TOKENS_QUERY)
        queries = list(dict.fromkeys(q.strip() for q in result.queries if q.strip()))[:QUERY_MAX]
        return queries or [context.summary[:60]]

    async def find_candidates(self, queries: List[str], context: RecContext, search_round: Optional[str]) -> List[VideoCandidate]:
        searches = await asyncio.gather(*[self.api.search_videos(q=q, lang=self.yt_lang, max_results=MAX_SEARCH_RESULTS) for q in queries])
        excluded = {normalize_title(t) for t in context.excluded(self.resource_type)}
        seen, items = set(), []
        for item in (item for result in searches for item in result):
            key = normalize_title(item.title)
            if key not in excluded and key not in seen:
                seen.add(key)
                items.append(item)
        if not items:
            return []
        details = {d.video_id: d for d in await self.api.get_videos([it.video_id for it in items])}
        return [VideoCandidate(item=it, detail=details.get(it.video_id)) for it in items]

    async def prepare(self, candidate: VideoCandidate, context: RecContext) -> VideoCandidate:
        detail = candidate.detail
        if detail is None:
            title, description, channel = candidate.item.title, candidate.item.description, "Unknown"
        else:
            title, description, channel = detail.title, detail.description or "", detail.channel_title
        if len(description) > MAX_DESCRIPTION_LENGTH:
            description = description[:MAX_DESCRIPTION_LENGTH] + "..."
        prompt = SUMMARY_PROMPT.format(title=title, description=description, channel=channel, language=self.language)
        result = await llm.complete_json(ModelPurpose.VERIFY, [("user", prompt)], VideoSummary, max_tokens=MAX_TOKENS_SUMMARY)
        return replace(candidate, extract=result.extract)

    def uses_llm(self, candidate: VideoCandidate) -> bool:
        return self.verify and candidate.detail is not None

    async def llm_score(self, candidate: VideoCandidate, context: RecContext, queries: List[str]) -> Score:
        prompt = SCORE_PROMPT.format(
            lecture_summary=context.summary, title=candidate.detail.title, extract=candidate.extract, language=self.language
        )
        result = await llm.complete_json(ModelPurpose.VERIFY, [("user", prompt)], LLMScore, max_tokens=MAX_TOKENS_SCORE)
        return Score(round(result.score, 2), result.reason)

    def heuristic_score(self, candidate: VideoCandidate, context: RecContext, queries: List[str]) -> Score:
        detail = candidate.detail
        if detail is None:
            return Score(_best_heuristic(candidate.item.title, 0, candidate.item.publish_time, queries), "Heuristic")
        return Score(round(_best_heuristic(detail.title, detail.view_count, detail.publish_time, queries), 2), "Heuristic")

    def to_recommendation(self, candidate: VideoCandidate, score: Score) -> Recommendation:
        detail = candidate.detail
        if detail is None:
            url, title, lang = f"https://www.youtube.com/watch?v={candidate.item.video_id}", candidate.item.title, self.yt_lang
        else:
            url, title, lang = detail.url(), detail.title, detail.default_lang or self.yt_lang
        info = {"url": url, "title": one_line(title), "extract": one_line(candidate.extract), "lang": lang}
        return Recommendation(
            type=self.resource_type,
            title=info["title"],
            url=url,
            description=info["extract"],
            score=score.score,
            reason=one_line(score.reason),
            detail=info,
        )


def normalize_title(title: str) -> str:
    """중복·제외 비교용으로 제목을 정규화한다 (소문자, 한글·영숫자·공백·_-만 남김).

    Args:
        title: 영상 제목
    Returns:
        정규화한 제목
    """
    title = re.sub(r"\s+", " ", title.lower())
    return re.sub(r"[^a-z0-9가-힣 _\-]", "", title).strip()


def heuristic_score(*, title: str, query: str, view_count: int, publish_time: str) -> float:
    """제목과 검색어의 유사도, 조회수, 최신성의 가중 평균을 0~10으로 계산한다.

    Args:
        title: 영상 제목
        query: 검색어
        view_count: 조회수
        publish_time: 게시 시각 (ISO 8601)
    Returns:
        점수 (0~10)
    """
    similarity = fuzz.token_set_ratio(title, query) / 100.0
    views = min(1.0, math.log10(view_count + 1) / 6.0) if view_count > 0 else 0.0
    try:
        recency = max(0.0, min(1.0, (int(publish_time[:4]) - 2015) / 10.0))
    except (TypeError, ValueError):
        recency = 0.5
    raw = WEIGHT_TITLE_MATCH * similarity + WEIGHT_VIEWS * views + WEIGHT_RECENCY * recency
    return max(0.0, min(10.0, raw * 10.0))


def _best_heuristic(title: str, view_count: int, publish_time: str, queries: List[str]) -> float:
    return max(heuristic_score(title=title, query=q, view_count=view_count, publish_time=publish_time) for q in queries)
