"""
OpenAlexKit 핵심 서비스
"""
import asyncio
import logging
from typing import List

from core.llm import ModelPurpose, model_settings

from .models import OpenAlexRequest, OpenAlexResponse, PaperInfo
from .config.openalex_config import OpenAlexConfig
from .config import flags
from .api.openalex_client import OpenAlexAPIClient
from .llm.openai_client import OpenAIClient
from .utils.filters import deduplicate_papers, rerank_papers

logger = logging.getLogger(__name__)


class OpenAlexService:
    """OpenAlex 논문 추천 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        # 설정 검증
        OpenAlexConfig.validate()
        
        # 클라이언트 초기화
        self.api_client = OpenAlexAPIClient()
        self.llm_client = OpenAIClient()
    
    async def recommend_papers(
        self, 
        request: OpenAlexRequest
    ) -> List[OpenAlexResponse]:
        """
        논문 추천 (병렬 검증)
        
        흐름:
        1. 섹션 요약 → 검색 쿼리 생성 (LLM)
        2. OpenAlex API 호출 (필터 적용)
        3. 논문 파싱 + 중복 제거 + 재랭킹
        4. 상위 N개 선택 (CARD_LIMIT)
        5. 조건부 검증:
           - verify_openalex=True: LLM 병렬 검증
           - verify_openalex=False: Heuristic 스코어링
        6. 점수 순 정렬 → top_k 반환
        
        Args:
            request: OpenAlexRequest
        
        Returns:
            List[OpenAlexResponse]: 추천 논문 리스트 (top_k개)
        """
        logger.info(
            f"🚀 논문 추천 시작: lecture={request.lecture_id}, "
            f"section={request.section_id}, verify={request.verify_openalex}"
        )
        
        try:
            # 1. 검색 쿼리 생성 (LLM)
            logger.info(f"🔍 OpenAlex 검색 시작 (lecture={request.lecture_id}, section={request.section_id})")
            logger.info(f"   ├─ section_summary: {request.section_summary[:100]}...")
            logger.info(f"   ├─ previous_summaries: {len(request.previous_summaries)}개")
            logger.info(f"   └─ rag_context: {len(request.rag_context)}개")
            
            query = await self._generate_search_query(request)
            
            tokens = query.get('tokens', [])
            logger.info(f"📝 생성된 쿼리:")
            logger.info(f"   ├─ tokens: {tokens} (총 {len(tokens)}개)")
            logger.info(f"   └─ year_from: {query.get('year_from')}")
            
            if not tokens:
                logger.warning("⚠️  검색 토큰이 생성되지 않았습니다")
                return []
            
            # TOKEN 수 경고
            if len(tokens) > 3:
                logger.warning(f"⚠️  TOKEN 수가 많습니다 ({len(tokens)}개). 검색 결과가 없을 수 있습니다.")
                logger.warning(f"   권장: 2-3개 TOKEN (현재: {tokens})")
            
            # 2. OpenAlex API 호출
            logger.info(f"🌐 OpenAlex API 호출:")
            logger.info(f"   ├─ search_str: {' '.join(tokens)}")
            logger.info(f"   ├─ year_from: {query.get('year_from')}")
            logger.info(f"   ├─ sort_by: {request.sort_by}")
            logger.info(f"   └─ exclude_ids: {len(request.exclude_ids)}개")
            
            papers = await self.api_client.search_papers(
                query=query,
                exclude_ids=request.exclude_ids,
                sort_by=request.sort_by
            )
            
            if not papers:
                logger.warning(f"⚠️  검색된 논문이 없습니다 (tokens={tokens})")
                logger.warning(f"   가능한 원인:")
                logger.warning(f"   1. TOKEN이 너무 많음 ({len(tokens)}개) → 2-3개 권장")
                logger.warning(f"   2. year_from이 부적절 ({query.get('year_from')}) → 2015 권장")
                logger.warning(f"   3. 검색어가 너무 구체적 → 일반적인 학술 용어 사용")
                return []
            
            logger.info(f"📚 검색된 논문: {len(papers)}개")
            logger.info(f"   상위 3개 제목:")
            for i, paper in enumerate(papers[:3], 1):
                logger.info(f"   {i}. {paper.get('title', 'Unknown')[:80]}...")
            
            # 3. 중복 제거 + 재랭킹
            before_dedup = len(papers)
            papers = deduplicate_papers(papers)
            papers = rerank_papers(papers, query)
            logger.info(f"🔄 중복 제거: {before_dedup}개 → {len(papers)}개")
            
            # 4. 상위 N개 선택 (CARD_LIMIT)
            papers = papers[:OpenAlexConfig.CARD_LIMIT]
            logger.info(f"📄 검증 대상: {len(papers)}개 (상한: {OpenAlexConfig.CARD_LIMIT})")
            logger.info(f"   ├─ verify_openalex: {request.verify_openalex}")
            logger.info(f"   ├─ NO_SCORING: {flags.NO_SCORING}")
            logger.info(f"   └─ min_score: {request.min_score}")
            
            # 🚀 NO_SCORING 모드: 검증 없이 검색 결과만 반환
            if flags.NO_SCORING:
                logger.info("⚡ NO_SCORING 모드: 검증 스킵")
                results = []
                for paper in papers[:request.top_k]:
                    info = PaperInfo(
                        title=paper.get("title", "Unknown"),
                        authors=paper.get("authors", []),
                        year=paper.get("publication_year"),
                        citations=paper.get("cited_by_count", 0),
                        url=paper.get("url", ""),
                        abstract=paper.get("abstract", "No abstract available")[:500]
                    )
                    results.append(OpenAlexResponse(
                        lecture_id=request.lecture_id,
                        section_id=request.section_id,
                        paper_info=info,
                        reason="search",
                        score=10.0
                    ))
                logger.info(f"✅ NO_SCORING 결과: {len(results)}개 반환")
                return results
            
            # 5. 조건부 검증
            if request.verify_openalex:
                # LLM 병렬 검증
                logger.info(f"✨ LLM 병렬 검증 시작:")
                logger.info(f"   ├─ 대상: {len(papers)}개")
                logger.info(f"   ├─ 동시성: {OpenAlexConfig.VERIFY_CONCURRENCY}")
                logger.info(f"   └─ 모델: {model_settings(ModelPurpose.VERIFY).model}")
                results = await self._verify_papers_parallel(papers, request, query)
            else:
                # Heuristic 스코어링
                logger.info(f"🔢 Heuristic 스코어링 시작 ({len(papers)}개)")
                results = self._heuristic_score(papers, query, request)
            
            # 6. 점수 필터링 (min_score 이상만 선택)
            filtered_results = [r for r in results if r.score >= request.min_score]
            
            if len(filtered_results) < len(results):
                filtered_count = len(results) - len(filtered_results)
                logger.info(
                    f"🔍 점수 필터링: {len(results)}개 → {len(filtered_results)}개 "
                    f"(제외: {filtered_count}개, min_score: {request.min_score})"
                )
                # 제외된 논문의 점수 분포
                excluded_scores = sorted([r.score for r in results if r.score < request.min_score], reverse=True)
                if excluded_scores:
                    logger.info(f"   제외된 점수: {excluded_scores[:5]}" + ("..." if len(excluded_scores) > 5 else ""))
            
            # 7. 점수 순 정렬 + top_k 반환 (필터링된 결과에서)
            filtered_results.sort(key=lambda x: x.score, reverse=True)
            final_results = filtered_results[:request.top_k]
            
            if final_results:
                scores = [r.score for r in final_results]
                logger.info(
                    f"✅ 논문 추천 완료: {len(final_results)}개"
                )
                logger.info(f"   ├─ 점수 범위: {min(scores):.1f} ~ {max(scores):.1f}")
                logger.info(f"   └─ 평균 점수: {sum(scores)/len(scores):.1f}")
                # 최종 결과 요약
                for i, result in enumerate(final_results, 1):
                    logger.info(f"   {i}. [{result.score:.1f}점] {result.paper_info.title[:60]}...")
            else:
                logger.warning(f"⚠️  min_score {request.min_score} 이상인 논문이 없습니다")
                if results:
                    max_score = max(r.score for r in results)
                    logger.warning(f"   최고 점수: {max_score:.1f} (min_score를 {max_score:.1f} 이하로 낮추세요)")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ 논문 추천 실패: {e}")
            return []
    
    async def _generate_search_query(self, request: OpenAlexRequest) -> dict:
        """
        섹션 요약 → OpenAlex 검색 쿼리 생성 (LLM)
        
        Args:
            request: OpenAlexRequest
            
        Returns:
            {"tokens": ["term1", "term2"], "year_from": 2015}
        """
        try:
            # LLM에게 전달할 데이터 준비
            request_data = {
                "section_summary": request.section_summary,
                "previous_summaries": request.previous_summaries,
                "rag_context": request.rag_context,
            }
            
            logger.info("🤖 LLM 쿼리 생성 시작")
            # LLM 쿼리 생성
            result = await self.llm_client.generate_query(request_data)
            
            logger.info(f"✅ LLM 쿼리 생성 완료: {result}")
            
            # year_from 추가
            result["year_from"] = request.year_from
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 쿼리 생성 실패: {e}", exc_info=True)
            return {"tokens": [], "year_from": request.year_from}
    
    async def _verify_papers_parallel(
        self, 
        papers: List[dict], 
        request: OpenAlexRequest,
        query: dict
    ) -> List[OpenAlexResponse]:
        """
        병렬 LLM 검증 (Semaphore 동시성 제어)
        
        Args:
            papers: 논문 리스트
            request: OpenAlexRequest
            query: 검색 쿼리 (tokens 포함)
            
        Returns:
            List[OpenAlexResponse]: 검증된 논문 리스트
        """
        semaphore = asyncio.Semaphore(OpenAlexConfig.VERIFY_CONCURRENCY)
        
        async def verify_with_limit(paper: dict):
            async with semaphore:
                return await self._verify_single_paper(paper, request, query)
        
        logger.info(f"✨ 병렬 LLM 검증 시작 (동시성: {OpenAlexConfig.VERIFY_CONCURRENCY})")
        
        results = await asyncio.gather(
            *[verify_with_limit(paper) for paper in papers],
            return_exceptions=True
        )
        
        # 에러 처리
        verified = []
        for paper, result in zip(papers, results):
            if isinstance(result, Exception):
                logger.error(f"❌ 검증 실패: {result}")
                # Fallback: score=5.0
                verified.append(OpenAlexResponse(
                    lecture_id=request.lecture_id,
                    section_id=request.section_id,
                    paper_info=self._parse_paper_info(paper),
                    reason="검증 실패 (fallback)",
                    score=5.0
                ))
            else:
                verified.append(result)
        
        logger.info(f"✅ 병렬 검증 완료: {len(verified)}개")
        
        return verified
    
    async def _verify_single_paper(
        self, 
        paper: dict, 
        request: OpenAlexRequest,
        query: dict
    ) -> OpenAlexResponse:
        """
        단일 논문 검증 (LLM)
        
        Args:
            paper: 논문 정보
            request: OpenAlexRequest
            query: 검색 쿼리 (tokens 포함)
            
        Returns:
            OpenAlexResponse
        """
        try:
            # 키워드 문자열 생성
            keywords = ", ".join(query.get("tokens", []))
            
            # LLM 검증
            result = await self.llm_client.score_paper(
                paper=paper,
                section_summary=request.section_summary,
                keywords=keywords,
                language=request.language
            )
            
            return OpenAlexResponse(
                lecture_id=request.lecture_id,
                section_id=request.section_id,
                paper_info=self._parse_paper_info(paper),
                reason=result.get("reason", "검증 완료"),
                score=result.get("score", 5.0)
            )
            
        except Exception as e:
            logger.error(f"❌ 논문 검증 실패: {e}")
            return OpenAlexResponse(
                lecture_id=request.lecture_id,
                section_id=request.section_id,
                paper_info=self._parse_paper_info(paper),
                reason="검증 실패 (오류)",
                score=5.0
            )
    
    def _heuristic_score(
        self, 
        papers: List[dict], 
        query: dict,
        request: OpenAlexRequest
    ) -> List[OpenAlexResponse]:
        """
        Heuristic 스코어링 (LLM 없이 빠른 평가)
        
        점수 계산:
        - 제목 키워드 매칭: +3점
        - 초록 키워드 매칭: +1점
        - relevance_score 가중치: +2점
        - 기본 점수: 5.0
        
        Args:
            papers: 논문 리스트
            query: 검색 쿼리 (tokens 포함)
            request: OpenAlexRequest
            
        Returns:
            List[OpenAlexResponse]: 점수가 부여된 논문 리스트
        """
        logger.info("🔢 Heuristic 스코어링 시작...")
        
        tokens = [kw.lower() for kw in query.get("tokens", [])]
        results = []
        
        for paper in papers:
            title_lower = paper.get("title", "").lower()
            abstract_lower = paper.get("abstract", "").lower()
            
            # 기본 점수
            score = 5.0
            
            # 키워드 매칭
            for kw in tokens:
                if kw in title_lower:
                    score += 0.5
                if kw in abstract_lower:
                    score += 0.2
            
            # relevance_score 가중치
            relevance = paper.get("relevance_score", 0)
            score += min(relevance / 10, 2.0)  # 최대 +2점
            
            # 10점 초과 방지
            score = min(score, 10.0)
            
            # 이유 생성 (단순화)
            reason = "Heuristic"
            
            results.append(OpenAlexResponse(
                lecture_id=request.lecture_id,
                section_id=request.section_id,
                paper_info=self._parse_paper_info(paper),
                reason=reason,
                score=score
            ))
        
        logger.info(f"✅ Heuristic 스코어링 완료: {len(results)}개")
        
        return results
    
    def _parse_paper_info(self, paper: dict) -> PaperInfo:
        """
        논문 정보를 PaperInfo로 변환
        
        Args:
            paper: 논문 딕셔너리
            
        Returns:
            PaperInfo
        """
        return PaperInfo(
            url=paper.get("url", ""),
            title=paper.get("title", ""),
            abstract=paper.get("abstract", "")[:OpenAlexConfig.ABSTRACT_MAX_LENGTH],
            year=paper.get("year"),
            cited_by_count=paper.get("cited_by_count", 0),
            authors=paper.get("authors", [])
        )
    
    async def close(self):
        """리소스 정리"""
        await self.api_client.close()
