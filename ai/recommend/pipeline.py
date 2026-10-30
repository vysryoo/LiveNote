"""
자료 추천 공통 흐름

1. 공급자가 LLM으로 검색어를 만든다
2. 검색 회차마다 공급자가 후보를 찾는다 (검색, 중복 제거, 제외, 재정렬, 상세 조회)
3. 후보마다 동시에 점수를 매긴다. verify면 LLM, 아니면 휴리스틱. 실패한 후보는 뺀다
4. min_score 이상만 남긴다. 회차가 여럿이면 앞 회차 결과가 top_k에 못 미칠 때만 다음 회차를 돌려 부족분을 채운다
5. 점수순으로 top_k개를 돌려준다
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Sequence, TypeVar

from core.schemas import ResourceType

from .models import RecContext, Recommendation, Score

logger = logging.getLogger(__name__)

CandidateT = TypeVar("CandidateT")


class Provider(ABC, Generic[CandidateT]):
    """자료 종류 하나의 추천 공급자. 공통 흐름에서 종류마다 다른 부분만 구현한다."""

    resource_type: ResourceType
    # LLM 검증 동시 호출 수
    verify_concurrency: int = 10

    def __init__(self, top_k: int, verify: bool, min_score: float, language: str) -> None:
        """공통 설정을 받는다.

        Args:
            top_k: 추천 개수
            verify: True면 LLM으로 점수를 매기고, False면 휴리스틱
            min_score: 남길 최소 점수 (0~10)
            language: 추천 이유 언어
        """
        self.top_k = top_k
        self.verify = verify
        self.min_score = min_score
        self.language = language

    @abstractmethod
    async def build_queries(self, context: RecContext) -> List[str]:
        """검색어를 만든다. 빈 목록이면 추천하지 않는다."""

    def search_rounds(self) -> Sequence[Optional[str]]:
        """검색 회차 목록. 기본은 한 번이며, 값은 find_candidates에 그대로 전달된다."""
        return [None]

    @abstractmethod
    async def find_candidates(self, queries: List[str], context: RecContext, search_round: Optional[str]) -> List[CandidateT]:
        """검색어로 점수를 매길 후보를 찾는다."""

    async def prepare(self, candidate: CandidateT, context: RecContext) -> CandidateT:
        """점수를 매기기 전 후보를 보강한다. 기본은 그대로 둔다."""
        return candidate

    def uses_llm(self, candidate: CandidateT) -> bool:
        """이 후보를 LLM으로 점수 매길지 정한다."""
        return self.verify

    @abstractmethod
    async def llm_score(self, candidate: CandidateT, context: RecContext, queries: List[str]) -> Score:
        """LLM으로 관련도 점수를 매긴다. 예외를 내면 그 후보는 결과에서 빠진다."""

    @abstractmethod
    def heuristic_score(self, candidate: CandidateT, context: RecContext, queries: List[str]) -> Score:
        """LLM 없이 관련도 점수를 매긴다."""

    @abstractmethod
    def to_recommendation(self, candidate: CandidateT, score: Score) -> Recommendation:
        """점수를 매긴 후보를 추천 결과로 바꾼다."""

    async def close(self) -> None:
        """공급자가 가진 연결을 닫는다."""


async def recommend(provider: Provider[Any], context: RecContext) -> List[Recommendation]:
    """공급자 하나로 추천한다.

    Args:
        provider: 자료 종류 공급자
        context: 추천 입력
    Returns:
        점수 내림차순 추천 결과. 최대 top_k개
    Raises:
        Exception: 검색어 생성이 실패한 경우 (공급자가 처리하지 않은 예외)
    """
    kind = provider.resource_type.value
    queries = await provider.build_queries(context)
    logger.info("추천 검색어: %s %s", kind, queries)
    if not queries:
        return []

    results: List[Recommendation] = []
    for number, search_round in enumerate(provider.search_rounds()):
        need = provider.top_k - len(results)
        if number > 0 and need <= 0:
            break
        try:
            candidates = await provider.find_candidates(queries, context, search_round)
        except Exception:
            logger.exception("추천 후보 검색 실패: %s round=%s", kind, search_round)
            candidates = []
        scored = await _score_all(provider, candidates, context, queries)
        valid = [r for r in scored if r.score >= provider.min_score]
        logger.info(
            "추천 후보: %s round=%s 후보 %d개, 점수 %d개, min_score(%s) 이상 %d개",
            kind, search_round, len(candidates), len(scored), provider.min_score, len(valid),
        )
        results += valid if number == 0 else valid[:need]

    results.sort(key=lambda r: r.score, reverse=True)
    return results[: provider.top_k]


async def _score_all(
    provider: Provider[Any], candidates: List[Any], context: RecContext, queries: List[str]
) -> List[Recommendation]:
    semaphore = asyncio.Semaphore(provider.verify_concurrency)

    async def score_one(candidate: Any) -> Recommendation:
        async with semaphore:
            candidate = await provider.prepare(candidate, context)
            if provider.uses_llm(candidate):
                score = await provider.llm_score(candidate, context, queries)
            else:
                score = provider.heuristic_score(candidate, context, queries)
            return provider.to_recommendation(candidate, score)

    outcomes = await asyncio.gather(*[score_one(c) for c in candidates], return_exceptions=True)
    scored: List[Recommendation] = []
    for outcome in outcomes:
        if isinstance(outcome, Exception):
            logger.warning("추천 후보 점수 실패, 제외: %s %s", provider.resource_type.value, outcome)
        else:
            scored.append(outcome)
    return scored
