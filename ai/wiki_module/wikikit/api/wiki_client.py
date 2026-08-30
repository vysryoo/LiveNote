"""
Wikipedia API client
"""
import logging
from typing import List, Dict, Optional
import httpx

from ..config import WikiConfig

logger = logging.getLogger(__name__)


class WikiAPIClient:
    """Wikipedia API 클라이언트"""
    
    BASE_URL = "https://{lang}.wikipedia.org/w/api.php"
    
    def __init__(self):
        self.config = WikiConfig()
    
    async def search_pages(
        self, 
        keyword: str, 
        lang: str = "en",
        limit: int = 6
    ) -> List[Dict]:
        """
        Wikipedia 검색 (단일 키워드)
        
        Args:
            keyword: 검색 키워드
            lang: 언어 (en/ko)
            limit: 결과 개수
            
        Returns:
            검색 결과 리스트 [{"title": "...", "pageid": 123, "snippet": "..."}, ...]
        """
        try:
            url = self.BASE_URL.format(lang=lang)
            
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": keyword,
                "srlimit": limit,
                "srprop": "snippet|titlesnippet",
                "uselang": lang
            }
            
            async with httpx.AsyncClient(
                timeout=self.config.TIMEOUT,
                headers={"User-Agent": self.config.USER_AGENT, "Accept": "application/json"},
            ) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("query", {}).get("search", [])
                logger.info(f"  ↳ '{keyword}' ({lang}) → {len(results)}개")
                return results
                
        except Exception as e:
            logger.error(f"❌ 검색 실패 (keyword='{keyword}', lang={lang}): {e}")
            return []
    
    async def get_page_extract(
        self, 
        page_id: int, 
        lang: str = "en"
    ) -> Optional[Dict]:
        """
        문서 상세 정보 가져오기 (extract 포함)
        
        Args:
            page_id: 페이지 ID
            lang: 언어 (en/ko)
            
        Returns:
            {"title": "...", "extract": "...", "url": "...", "pageid": 123} or None
        """
        try:
            url = self.BASE_URL.format(lang=lang)
            
            params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|info",
                "pageids": page_id,
                "exintro": True,  # 도입부만
                "explaintext": True,  # 일반 텍스트
                "exsentences": self.config.EXTRACT_SENTENCES,  # 3문장
                "inprop": "url",
                "uselang": lang
            }
            
            async with httpx.AsyncClient(
                timeout=self.config.TIMEOUT,
                headers={"User-Agent": self.config.USER_AGENT, "Accept": "application/json"},
            ) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                pages = data.get("query", {}).get("pages", {})
                page = pages.get(str(page_id))
                
                if not page or page.get("missing"):
                    logger.warning(f"⚠️ 페이지 없음 (pageid={page_id})")
                    return None
                
                return {
                    "title": page.get("title", ""),
                    "extract": page.get("extract", ""),
                    "url": page.get("fullurl", f"https://{lang}.wikipedia.org/?curid={page_id}"),
                    "pageid": page_id
                }
                
        except Exception as e:
            logger.error(f"❌ 상세 정보 fetch 실패 (pageid={page_id}, lang={lang}): {e}")
            return None
