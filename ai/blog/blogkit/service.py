"""
Google 검색 추천 서비스
"""
import asyncio
import logging
from typing import List

from .models import GoogleRequest, GoogleResponse, GoogleSearchResult
from .api.naver_client import NaverBlogSearchClient
from .llm.openai_client import GoogleLLMClient
from .utils import (
    deduplicate_results,
    rerank_results,
    filter_excluded_urls,
    heuristic_score,
    calculate_reason,
)
from .config import flags
from .config.google_config import GoogleConfig

logger = logging.getLogger(__name__)


class GoogleService:
    """Google 검색 추천 서비스"""
    
    def __init__(self):
        """초기화"""
        GoogleConfig.validate()
        
        self.api_client = NaverBlogSearchClient()
        self.llm_client = GoogleLLMClient()
        self.config = GoogleConfig
    
    async def recommend_results(
        self,
        request: GoogleRequest
    ) -> List[GoogleResponse]:
        """
        검색 결과 추천 파이프라인
        
        흐름:
        1. 키워드 생성 (LLM)
        2. 팬아웃 병렬 검색 (Google API)
        3. 중복 제거 (URL 기준)
        4. 제외 URL 필터링
        5. 재정렬 (키워드 매칭)
        6. 상위 N개 선택 (CARD_LIMIT)
        7. NO_SCORING 모드 체크
           - True: 검증 스킵, reason="search", score=10
           - False: 검증 단계 진행
        8. 조건부 검증 (LLM or Heuristic)
        9. min_score 필터링
        10. 점수 순 정렬 + top_k 반환
        
        Args:
            request: Google 검색 요청
            
        Returns:
            추천 검색 결과 리스트
        """
        logger.info(f"🔍 Google 검색 시작 (lecture_id={request.lecture_id}, section_id={request.section_id})")
        
        # 1. 키워드 생성
        logger.info(f"🤖 LLM 키워드 생성 시작 (language={request.search_lang})")
        
        prev_summaries = [
            {"section_id": ps.section_id, "summary": ps.summary}
            for ps in request.previous_summaries
        ]
        rag_chunks = [
            {"text": chunk.text, "score": chunk.score}
            for chunk in request.rag_context
        ]
        
        keywords = await self.llm_client.generate_keywords(
            lecture_summary=request.lecture_summary,
            language=request.search_lang,
            previous_summaries=prev_summaries,
            rag_context=rag_chunks
        )
        
        if not keywords:
            logger.warning("⚠️  키워드가 생성되지 않았습니다.")
            return []
        
        logger.info(f"✅ 키워드 생성 완료: {keywords}")
        
        # 2. 팬아웃 병렬 검색
        logger.info(f"🌐 네이버 블로그 팬아웃 검색 시작 (keywords={len(keywords)}개)")
        
        search_tasks = [
            self._search_shortening(keyword, request.search_lang)
            for keyword in keywords[:self.config.FANOUT]
        ]
        
        search_results_list = await asyncio.gather(*search_tasks)
        
        # 결과 병합
        all_results = []
        for results in search_results_list:
            all_results.extend(results)
        
        logger.info(f"📊 검색 결과 수집: {len(all_results)}개")
        
        if not all_results:
            logger.warning("⚠️  검색 결과가 없습니다.")
            return []
        
        # 3. 중복 제거
        unique_results = deduplicate_results(all_results)
        
        # 4. 제외 URL 필터링
        filtered_results = filter_excluded_urls(unique_results, request.exclude_urls)
        
        if not filtered_results:
            logger.warning("⚠️  필터링 후 결과가 없습니다.")
            return []
        
        # 5. 재정렬
        reranked_results = rerank_results(filtered_results, keywords)
        
        # 6. 상위 N개 선택
        top_results = reranked_results[:self.config.CARD_LIMIT]
        
        logger.info(f"📥 검증 대상: {len(top_results)}개")
        
        # 7. NO_SCORING 모드 체크
        if flags.NO_SCORING:
            logger.info("⚡ NO_SCORING 모드: 검증 스킵")
            
            responses = []
            for item in top_results[:request.top_k]:
                result_info = GoogleSearchResult(
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", "")[:300],
                    display_link=item.get("displayLink", ""),
                    lang=request.search_lang
                )
                
                responses.append(GoogleResponse(
                    lecture_id=request.lecture_id,
                    section_id=request.section_id,
                    search_result=result_info,
                    reason="search",
                    score=10.0
                ))
            
            logger.info(f"✅ NO_SCORING 결과: {len(responses)}개")
            return responses
        
        # 8. 검증 (LLM or Heuristic)
        if request.verify_google:
            logger.info("🤖 LLM 검증 시작")
            verified_results = await self._verify_with_llm(
                top_results,
                request.lecture_summary,
                request.language,
                keywords,
                request.lecture_id,
                request.section_id
            )
        else:
            logger.info("📊 Heuristic 검증 시작")
            verified_results = self._verify_with_heuristic(
                top_results,
                keywords,
                request.language,
                request.lecture_id,
                request.section_id
            )
        
        logger.info(f"✅ 검증 완료: {len(verified_results)}개")
        
        # 9. min_score 필터링
        filtered_by_score = [
            result for result in verified_results
            if result.score >= request.min_score
        ]
        
        logger.info(f"🎯 min_score 필터링: {len(filtered_by_score)}개 (>= {request.min_score})")
        
        # 10. 점수 순 정렬 + top_k 반환
        filtered_by_score.sort(key=lambda x: x.score, reverse=True)
        final_results = filtered_by_score[:request.top_k]
        
        logger.info(f"✅ Google 검색 완료: {len(final_results)}개 반환")
        
        return final_results
    
    async def _search_shortening(self, keyword: str, lang: str) -> List[dict]:
        """결과가 없으면 마지막 단어를 하나씩 빼며 다시 검색한다.

        네이버 블로그 검색은 모든 단어가 들어간 글만 찾아, 전문 용어가 많은 키워드는 결과가 없을 수 있음.

        Args:
            keyword: LLM이 만든 검색 키워드
            lang: 검색 언어
        Returns:
            검색 결과 목록. 한 단어까지 줄여도 없으면 빈 목록
        """
        words = keyword.split()
        while words:
            results = await self.api_client.search(query=" ".join(words), lang=lang, num=self.config.SEARCH_LIMIT)
            if results or len(words) == 1:
                return results
            logger.info(f"🔁 검색 결과 없음, 키워드 축소: {' '.join(words)!r} → {' '.join(words[:-1])!r}")
            words = words[:-1]
        return []

    async def _verify_with_llm(
        self,
        results: List[dict],
        lecture_summary: str,
        language: str,
        keywords: List[str],
        lecture_id: str,
        section_id: int
    ) -> List[GoogleResponse]:
        """
        LLM을 사용한 검증
        
        Args:
            results: 검색 결과 리스트
            lecture_summary: 강의 요약
            language: 응답 언어
            keywords: 검색 키워드
            lecture_id: 강의 ID
            section_id: 섹션 ID
            
        Returns:
            검증된 GoogleResponse 리스트
        """
        semaphore = asyncio.Semaphore(self.config.VERIFY_CONCURRENCY)
        
        async def verify_one(item: dict):
            async with semaphore:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                url = item.get("link", "")
                
                # LLM 점수 계산
                llm_result = await self.llm_client.score_result(
                    lecture_summary=lecture_summary,
                    title=title,
                    snippet=snippet,
                    url=url,
                    language=language
                )
                
                result_info = GoogleSearchResult(
                    url=item.get("link", ""),
                    title=title,
                    snippet=snippet[:300],
                    display_link=item.get("displayLink", ""),
                    lang=language
                )
                
                return GoogleResponse(
                    lecture_id=lecture_id,
                    section_id=section_id,
                    search_result=result_info,
                    reason=llm_result["reason"],
                    score=llm_result["score"]
                )
        
        # 병렬 검증
        tasks = [verify_one(item) for item in results]
        
        verified = await asyncio.gather(*tasks)
        
        return verified
    
    def _verify_with_heuristic(
        self,
        results: List[dict],
        keywords: List[str],
        language: str,
        lecture_id: str,
        section_id: int
    ) -> List[GoogleResponse]:
        """
        Heuristic을 사용한 검증
        
        Args:
            results: 검색 결과 리스트
            keywords: 검색 키워드
            language: 응답 언어
            lecture_id: 강의 ID
            section_id: 섹션 ID
            
        Returns:
            검증된 GoogleResponse 리스트
        """
        verified = []
        
        for item in results:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            display_link = item.get("displayLink", "")
            
            # Heuristic 점수 계산
            score = heuristic_score(title, snippet, keywords, display_link)
            reason = calculate_reason(title, snippet, keywords, score, language)
            
            result_info = GoogleSearchResult(
                url=item.get("link", ""),
                title=title,
                snippet=snippet[:300],
                display_link=display_link,
                lang=language
            )
            
            verified.append(GoogleResponse(
                lecture_id=lecture_id,
                section_id=section_id,
                search_result=result_info,
                reason=reason,
                score=score
            ))
        
        return verified
