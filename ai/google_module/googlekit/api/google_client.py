"""
Google Custom Search API 클라이언트
"""
import aiohttp
import logging
from typing import List, Dict, Any, Optional

from ..config.google_config import GoogleConfig

logger = logging.getLogger(__name__)


class GoogleSearchClient:
    """Google Custom Search API 클라이언트"""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: Optional[str] = None, engine_id: Optional[str] = None):
        """
        초기화
        
        Args:
            api_key: Google Search API 키 (None이면 환경 변수 사용)
            engine_id: Search Engine ID (None이면 환경 변수 사용)
        """
        self.api_key = api_key or GoogleConfig.GOOGLE_SEARCH_API_KEY
        self.engine_id = engine_id or GoogleConfig.GOOGLE_SEARCH_ENGINE_ID
        
        if not self.api_key:
            raise ValueError("GOOGLE_SEARCH_API_KEY가 설정되지 않았습니다.")
        if not self.engine_id:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID가 설정되지 않았습니다.")
    
    async def search(
        self,
        query: str,
        lang: str = "ko",
        num: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Google Custom Search 호출
        
        Args:
            query: 검색 쿼리
            lang: 검색 언어 (ko/en)
            num: 결과 개수 (최대 10)
            
        Returns:
            검색 결과 리스트
        """
        params = {
            "key": self.api_key,
            "cx": self.engine_id,
            "q": query,
            "lr": f"lang_{lang}",  # Language restrict
            "num": min(num, 10),  # 최대 10개
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Google API 오류 ({response.status}): {error_text}")
                        return []
                    
                    data = await response.json()
                    items = data.get("items", [])
                    
                    logger.info(f"🔍 Google API 응답: {len(items)}개 결과")
                    
                    # 결과 정규화
                    results = []
                    for item in items:
                        results.append({
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "displayLink": item.get("displayLink", ""),
                        })
                    
                    return results
        
        except aiohttp.ClientError as e:
            logger.error(f"❌ Google API 호출 실패: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Google API 예외 발생: {e}")
            return []
