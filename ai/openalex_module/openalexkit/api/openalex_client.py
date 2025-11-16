"""
OpenAlex API 클라이언트
"""
import logging
from typing import List, Dict, Optional
import httpx

from ..config.openalex_config import OpenAlexConfig
from ..utils.parser import parse_abstract_inverted_index

logger = logging.getLogger(__name__)


class OpenAlexAPIClient:
    """OpenAlex API 클라이언트"""
    
    BASE_URL = "https://api.openalex.org"
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=OpenAlexConfig.TIMEOUT,
            limits=httpx.Limits(
                max_connections=20,  # 10→20 (병렬 처리 개선)
                max_keepalive_connections=10
            ),
            http2=True  # HTTP/2 활성화 (멀티플렉싱)
        )
    
    async def search_papers(
        self, 
        query: Dict, 
        exclude_ids: Optional[List[str]] = None,
        sort_by: str = "relevance"
    ) -> List[Dict]:
        """
        OpenAlex API 검색
        
        Args:
            query: 검색 쿼리 (tokens, year_from 포함)
            exclude_ids: 제외할 논문 ID 리스트
            sort_by: 정렬 기준 ("relevance", "cited_by_count", "hybrid")
                - "relevance": 키워드 연관성 우선 (기본값)
                - "cited_by_count": 인용수 우선
                - "hybrid": 연관성 높은 논문 중 인용수 상위 선택
            
        Returns:
            List[Dict]: 파싱된 논문 리스트
        """
        try:
            # 검색 문자열 생성 (tokens 기반)
            tokens = query.get("tokens", [])
            search_str = " ".join(tokens)
            
            # year_from 처리
            year_from = query.get("year_from", OpenAlexConfig.DEFAULT_YEAR_FROM)
            
            # 필터 구성
            filters = [
                f"from_publication_date:{year_from}-01-01",
                "language:en",
                "is_paratext:false",
                "type:article",
            ]
            
            # 정렬 옵션 결정
            if sort_by == "cited_by_count":
                sort_param = "cited_by_count:desc"
            elif sort_by == "hybrid":
                # Hybrid 모드: 더 많은 논문 가져온 후 재정렬
                sort_param = "relevance_score:desc"
                per_page = OpenAlexConfig.PER_PAGE * 2  # 50개 가져오기
            else:  # relevance (기본값)
                sort_param = "relevance_score:desc"
                per_page = OpenAlexConfig.PER_PAGE
            
            # OpenAlex API 호출
            params = {
                "search": search_str,
                "filter": ",".join(filters),
                "sort": sort_param,
                "per_page": per_page if sort_by == "hybrid" else OpenAlexConfig.PER_PAGE
            }
            
            logger.info(f"🔍 OpenAlex API 요청:")
            logger.info(f"   ├─ URL: {self.BASE_URL}/works")
            logger.info(f"   ├─ search: \"{search_str}\"")
            logger.info(f"   ├─ filters: {filters}")
            logger.info(f"   ├─ sort: {sort_param}")
            logger.info(f"   └─ per_page: {params['per_page']}")
            
            response = await self.http_client.get(
                f"{self.BASE_URL}/works",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            works = data.get("results", [])
            logger.info(f"📄 OpenAlex 원본 검색: {len(works)}개")
            
            if len(works) == 0:
                logger.warning(f"⚠️  검색 결과 없음. 가능한 원인:")
                logger.warning(f"   1. 검색어가 너무 구체적: \"{search_str}\"")
                logger.warning(f"   2. TOKEN 수가 많음: {len(tokens)}개")
                logger.warning(f"   3. year_from 필터: {year_from}")
                logger.warning(f"   해결: TOKEN 줄이기 (2-3개), year_from 조정 (2015)")
                return []
            
            # 파싱 및 필터링
            papers = []
            exclude_set = set(exclude_ids or [])
            
            for work in works:
                paper = self._parse_paper(work)
                
                if paper is None:
                    continue
                
                # 제외 ID 체크
                if paper.get("id") in exclude_set:
                    logger.debug(f"⏭️  제외됨 (exclude_ids): {paper.get('title', '')[:50]}")
                    continue
                
                papers.append(paper)
            
            # Hybrid 모드: 연관성 점수 0.5 이상인 논문 중 인용수로 재정렬
            if sort_by == "hybrid" and papers:
                # 연관성 임계값 (상위 60%)
                threshold = max(p.get("relevance_score", 0) for p in papers) * 0.6
                relevant_papers = [p for p in papers if p.get("relevance_score", 0) >= threshold]
                
                # 인용수로 정렬
                relevant_papers.sort(key=lambda x: x.get("cited_by_count", 0), reverse=True)
                papers = relevant_papers[:OpenAlexConfig.PER_PAGE]
                
                logger.info(f"🔄 Hybrid 재정렬: 연관성 {threshold:.2f} 이상 논문 {len(relevant_papers)}개 → 인용수 상위 {len(papers)}개 선택")
            
            logger.info(f"✅ OpenAlex 파싱 완료: {len(papers)}개")
            return papers
            
        except httpx.TimeoutException:
            logger.error("❌ OpenAlex API 타임아웃")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ OpenAlex API HTTP 오류: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"❌ OpenAlex API 호출 실패: {e}")
            return []
    
    def _parse_paper(self, work: Dict) -> Optional[Dict]:
        """
        OpenAlex work 객체 파싱
        
        Args:
            work: OpenAlex work 객체
            
        Returns:
            Dict or None (필터링됨)
        """
        try:
            # 기본 정보
            paper_id = work.get("id", "")
            title = work.get("title", "")
            year = work.get("publication_year")
            cited_by_count = work.get("cited_by_count", 0)
            doi = work.get("doi", "")
            url = doi if doi else paper_id
            
            # 초록 파싱
            abstract_inverted = work.get("abstract_inverted_index")
            abstract = parse_abstract_inverted_index(abstract_inverted)
            
            # 저자 파싱
            authors = []
            authorships = work.get("authorships", [])
            for authorship in authorships[:5]:  # 상위 5명만
                author = authorship.get("author", {})
                name = author.get("display_name")
                if name:
                    authors.append(name)
            
            # 초록 없는 논문 필터링
            no_abstract = not abstract or len(abstract.strip()) < 50
            
            if no_abstract:
                # 초록 없고 인용 수 낮음 → 제외
                if cited_by_count < 100:
                    logger.debug(
                        f"⏭️  제외됨 (초록 없음 + 인용 수 {cited_by_count}): {title[:50]}"
                    )
                    return None
            
            return {
                "id": paper_id,
                "title": title,
                "abstract": abstract,
                "year": year,
                "cited_by_count": cited_by_count,
                "url": url,
                "authors": authors,
                "no_abstract": no_abstract,
                "relevance_score": work.get("relevance_score", 0.0)
            }
            
        except Exception as e:
            logger.error(f"❌ 논문 파싱 실패: {e}")
            return None
    
    async def close(self):
        """HTTP 클라이언트 종료"""
        await self.http_client.aclose()
