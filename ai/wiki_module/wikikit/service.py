"""
Wikipedia document recommendation service
"""
import asyncio
import logging
import time
from typing import List, Dict

from .models import WikiRequest, WikiResponse, WikiPageInfo
from .api import WikiAPIClient
from .llm import OpenAIClient
from .utils import deduplicate_pages, rerank_pages
from .config import WikiConfig
from .config import flags

logger = logging.getLogger(__name__)


class WikiService:
    """Wikipedia 문서 추천 서비스"""
    
    def __init__(self):
        self.api_client = WikiAPIClient()
        self.llm_client = OpenAIClient()
        self.config = WikiConfig()
    
    async def recommend_pages(
        self, 
        request: WikiRequest
    ) -> List[WikiResponse]:
        """
        위키 문서 추천 (병렬 검증)
        
        흐름:
        1. 키워드 생성 (LLM)
        2. 팬아웃 병렬 검색 (영문 우선)
        3. 중복 제거
        4. 상세 정보 병렬 fetch
        5. 조건부 검증 (LLM or Heuristic)
        6. min_score 필터링
        7. 결과 부족 시 한국어 보충 (fallback)
        8. top_k 반환
        
        Args:
            request: WikiRequest
        
        Returns:
            List[WikiResponse]: 추천 문서 리스트
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Wikipedia 검색 시작 (lecture={request.lecture_id}, section_id={request.section_id})")
            
            # 1. 키워드 생성
            logger.info(f"🔑 키워드 생성 시작 (NO_SCORING={flags.NO_SCORING})")
            keywords = await self.llm_client.generate_keywords(
                lecture_summary=request.lecture_summary,
                language=request.language,
                search_language=request.wiki_lang,
                previous_summaries=request.previous_summaries,
                rag_context=request.rag_context
            )
            
            if not keywords:
                logger.warning("⚠️ 키워드 생성 실패")
                return []
            
            logger.info(f"✅ 키워드 생성 완료: {keywords}")
            
            # 2. 영문 팬아웃 검색 + 검증
            logger.info(f"🔍 Wikipedia({request.wiki_lang}) 팬아웃 검색 시작")
            primary_cards = await self._search_and_verify(
                keywords, 
                request.wiki_lang, 
                request
            )
            
            # min_score 필터링
            valid_primary = [c for c in primary_cards if c.score >= request.min_score]
            
            logger.info(
                f"✅ Wikipedia({request.wiki_lang}) 완료: {len(primary_cards)}개 중 "
                f"{request.min_score}점 이상 {len(valid_primary)}개"
            )
            
            # 3. Fallback: top_k보다 적으면 한국어로 보충
            final_cards = valid_primary
            need_more = request.top_k - len(valid_primary)
            
            if need_more > 0 and request.fallback_to_ko:
                fallback_lang = "ko" if request.wiki_lang == "en" else "en"
                logger.info(f"🔄 {fallback_lang.upper()} Wikipedia Fallback 시작 (부족: {need_more}개)")
                
                fallback_cards = await self._search_and_verify(
                    keywords,
                    fallback_lang,
                    request
                )
                
                valid_fallback = [c for c in fallback_cards if c.score >= request.min_score]
                
                logger.info(
                    f"✅ Wikipedia({fallback_lang}) 완료: {len(fallback_cards)}개 중 "
                    f"{request.min_score}점 이상 {len(valid_fallback)}개"
                )
                
                # 보충
                final_cards = valid_primary + valid_fallback[:need_more]
            
            # 스코어 정렬
            final_cards.sort(key=lambda x: x.score, reverse=True)
            
            total_time = time.time() - start_time
            topk = min(len(final_cards), request.top_k)
            
            logger.info(
                f"🎯 Wikipedia 전체 완료: {len(final_cards)}개 → 상위 {topk}개 반환 (시간: {total_time:.2f}s)"
            )
            
            return final_cards[:topk]
            
        except Exception as e:
            logger.error(f"❌ Wikipedia 검색 실패: {e}", exc_info=True)
            return []
    
    async def _search_and_verify(
        self, 
        keywords: List[str], 
        lang: str, 
        request: WikiRequest
    ) -> List[WikiResponse]:
        """
        팬아웃 검색 + 상세 fetch + 검증 파이프라인
        
        Args:
            keywords: 검색 키워드
            lang: 언어 (en/ko)
            request: WikiRequest
            
        Returns:
            검증된 WikiResponse 리스트
        """
        try:
            # 1. 팬아웃 검색
            logger.info(f"📡 Wikipedia({lang}) 팬아웃 검색 시작 (keywords={keywords})")
            all_results = await self._fanout_search(keywords, lang, request.exclude_titles)
            
            if not all_results:
                logger.warning(f"⚠️ Wikipedia({lang}) 검색 결과 없음 (keywords={keywords})")
                return []
            
            logger.info(f"📊 Wikipedia({lang}) 검색 결과: {len(all_results)}개")
            
            # 2. 상세 정보 fetch (병렬)
            logger.info(f"📥 Wikipedia({lang}) 상세 정보 fetch 시작")
            pages = await self._fetch_details_parallel(all_results, lang)
            
            if not pages:
                logger.warning(f"⚠️ Wikipedia({lang}) 상세 정보 fetch 실패")
                return []
            
            logger.info(f"✅ Wikipedia({lang}) 상세 정보 fetch 완료: {len(pages)}개")
            
            # 🚀 NO_SCORING 모드: 검증 없이 검색 결과만 반환
            if flags.NO_SCORING:
                logger.info(f"⚡ Wikipedia({lang}) NO_SCORING 모드: 검증 스킵 (pages={len(pages)})")
                results = []
                for page in pages[:self.config.CARD_LIMIT]:
                    info = WikiPageInfo(
                        title=page.get("title", "Unknown"),
                        url=page.get("url", ""),
                        extract=page.get("snippet", "")[:500]
                    )
                    results.append(WikiResponse(
                        lecture_id=request.lecture_id,
                        section_id=request.section_id,
                        page_info=info,
                        reason="search",
                        score=10.0
                    ))
                logger.info(f"✅ NO_SCORING 결과: {len(results)}개 반환")
                return results
            
            # 3. 검증/스코어링
            if request.verify_wiki:
                logger.info(f"🔍 Wikipedia({lang}) LLM 검증 시작 (병렬)")
                verified = await self._verify_pages_parallel(pages, request, keywords)
            else:
                logger.info(f"⚡ Wikipedia({lang}) Heuristic 스코어 사용 (LLM 스킵)")
                verified = self._heuristic_score(pages, request, keywords)
            
            return verified
            
        except Exception as e:
            logger.error(f"❌ Wikipedia({lang}) 검색/검증 실패: {e}", exc_info=True)
            return []
            return []
    
    async def _fanout_search(
        self, 
        keywords: List[str], 
        lang: str,
        exclude_titles: List[str]
    ) -> List[Dict]:
        """팬아웃 병렬 검색"""
        try:
            # 병렬 검색
            fanout_count = min(len(keywords), self.config.FANOUT)
            search_tasks = [
                self.api_client.search_pages(kw, lang, self.config.SEARCH_LIMIT)
                for kw in keywords[:fanout_count]
            ]
            
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 결과 병합
            all_pages = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"검색 실패: {result}")
                    continue
                all_pages.extend(result)
            
            # 중복 제거
            unique_pages = deduplicate_pages(all_pages)
            
            # 제외 제목 필터링
            exclude_set = set(t.lower() for t in exclude_titles)
            filtered = [
                p for p in unique_pages
                if p.get("title", "").lower() not in exclude_set
            ]
            
            # 재랭킹
            ranked = rerank_pages(filtered, keywords)
            
            logger.info(f"📚 팬아웃 병합: {len(ranked)}개")
            return ranked
            
        except Exception as e:
            logger.error(f"❌ 팬아웃 검색 실패: {e}")
            return []
    
    async def _fetch_details_parallel(
        self, 
        search_results: List[Dict], 
        lang: str
    ) -> List[Dict]:
        """문서 상세 정보 병렬 fetch"""
        try:
            semaphore = asyncio.Semaphore(self.config.DETAIL_CONCURRENCY)
            
            async def fetch_with_limit(result: Dict):
                async with semaphore:
                    page_id = result.get("pageid")
                    page_detail = await self.api_client.get_page_extract(page_id, lang)
                    
                    if page_detail:
                        # 검색 결과의 snippet도 보존
                        page_detail["snippet"] = result.get("snippet", "")
                        return page_detail
                    return None
            
            pages = await asyncio.gather(
                *[fetch_with_limit(r) for r in search_results],
                return_exceptions=True
            )
            
            # 성공한 결과만
            valid_pages = [p for p in pages if isinstance(p, dict) and p]
            
            logger.info(f"🔄 상세 정보 fetch: {len(valid_pages)}개")
            return valid_pages
            
        except Exception as e:
            logger.error(f"❌ 상세 정보 fetch 실패: {e}")
            return []
    
    async def _verify_pages_parallel(
        self, 
        pages: List[Dict], 
        request: WikiRequest,
        keywords: List[str]
    ) -> List[WikiResponse]:
        """병렬 LLM 검증"""
        try:
            semaphore = asyncio.Semaphore(self.config.VERIFY_CONCURRENCY)
            
            async def verify_with_limit(page: Dict):
                async with semaphore:
                    try:
                        result = await self.llm_client.score_page(
                            request.lecture_summary,
                            page.get("title", ""),
                            page.get("extract", ""),
                            language=request.language
                        )
                        
                        return WikiResponse(
                            lecture_id=request.lecture_id,
                            section_id=request.section_id,
                            page_info=WikiPageInfo(
                                url=page.get("url", ""),
                                title=page.get("title", ""),
                                extract=page.get("extract", ""),
                                lang=request.wiki_lang,
                                page_id=page.get("pageid", 0)
                            ),
                            reason=result.get("reason", ""),
                            score=result.get("score", 5.0)
                        )
                        
                    except Exception as e:
                        logger.warning(f"⚠️ 검증 실패 (fallback): {e}")
                        # Heuristic fallback
                        return self._heuristic_score_single(page, request, keywords)
            
            verified = await asyncio.gather(
                *[verify_with_limit(p) for p in pages],
                return_exceptions=True
            )
            
            # 에러 필터링
            valid = [v for v in verified if isinstance(v, WikiResponse)]
            
            return valid
            
        except Exception as e:
            logger.error(f"❌ LLM 검증 실패: {e}")
            return []
    
    def _heuristic_score(
        self, 
        pages: List[Dict], 
        request: WikiRequest,
        keywords: List[str]
    ) -> List[WikiResponse]:
        """Heuristic 스코어링 (LLM 없이)"""
        return [self._heuristic_score_single(p, request, keywords) for p in pages]
    
    def _heuristic_score_single(
        self, 
        page: Dict, 
        request: WikiRequest,
        keywords: List[str]
    ) -> WikiResponse:
        """단일 페이지 Heuristic 스코어"""
        keywords_lower = [kw.lower() for kw in keywords]
        
        title_lower = page.get("title", "").lower()
        extract_lower = page.get("extract", "").lower()
        
        # 키워드 매칭 점수
        score = 5.0  # 기본 점수
        matched = []
        
        for kw in keywords_lower:
            if kw in title_lower:
                score += 2.0
                matched.append(kw)
            elif kw in extract_lower:
                score += 0.5
                matched.append(kw)
        
        score = min(score, 10.0)
        
        # 추천 이유
        if matched:
            keywords_text = ", ".join(set(matched[:2]))
            reason = f"Related to: {keywords_text}"
        else:
            reason = "Wikipedia encyclopedia article"
        
        return WikiResponse(
            lecture_id=request.lecture_id,
            section_id=request.section_id,
            page_info=WikiPageInfo(
                url=page.get("url", ""),
                title=page.get("title", ""),
                extract=page.get("extract", ""),
                lang=request.wiki_lang,
                page_id=page.get("pageid", 0)
            ),
            reason=reason,
            score=score
        )
