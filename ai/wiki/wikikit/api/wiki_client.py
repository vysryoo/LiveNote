"""
Wikipedia API client
"""
import asyncio
import logging
from typing import Any, List, Dict, Optional
import httpx

from ..config import WikiConfig

logger = logging.getLogger(__name__)

# 위키백과는 요청이 몰리면 429로 거절하므로 프로세스 전체 동시 요청 수를 제한하고, 거절되면 기다렸다 다시 시도함
MAX_CONCURRENT_REQUESTS = 4
MAX_RETRIES = 3
RETRY_STATUSES = {429, 503}
MAX_RETRY_WAIT_SEC = 10.0
_semaphores: Dict[int, asyncio.Semaphore] = {}


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


class WikiAPIClient:
    """Wikipedia API 클라이언트"""
    
    BASE_URL = "https://{lang}.wikipedia.org/w/api.php"
    
    def __init__(self, transport: Optional[httpx.AsyncBaseTransport] = None):
        """클라이언트를 만든다.

        Args:
            transport: httpx 전송 계층. 테스트에서 가짜 응답을 넣을 때 사용
        """
        self.config = WikiConfig()
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
            timeout=self.config.TIMEOUT,
            headers={"User-Agent": self.config.USER_AGENT, "Accept": "application/json"},
            transport=self._transport,
        ) as client:
            for attempt in range(1, MAX_RETRIES + 2):
                async with _semaphore():
                    response = await client.get(url, params=params)
                if response.status_code not in RETRY_STATUSES or attempt > MAX_RETRIES:
                    response.raise_for_status()
                    return response.json()
                wait = retry_wait_seconds(response, attempt)
                logger.warning(f"⏳ 위키백과 {response.status_code}, {wait:.1f}초 후 재시도 ({attempt}/{MAX_RETRIES})")
                await asyncio.sleep(wait)
        raise RuntimeError("unreachable")
    
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
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": keyword,
                "srlimit": limit,
                "srprop": "snippet|titlesnippet",
                "uselang": lang
            }
            
            data = await self._get_json(lang, params)
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
            {"title": "...", "extract": "...", "url": "...", "pageid": 123, "disambiguation": False} or None
        """
        try:
            params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|info|pageprops",
                # 동음이의어 문서 여부. 언어판과 관계없이 같은 속성으로 표시됨
                "ppprop": "disambiguation",
                "pageids": page_id,
                "exintro": True,  # 도입부만
                "explaintext": True,  # 일반 텍스트
                "exsentences": self.config.EXTRACT_SENTENCES,  # 3문장
                "inprop": "url",
                "uselang": lang
            }
            
            data = await self._get_json(lang, params)
            pages = data.get("query", {}).get("pages", {})
            page = pages.get(str(page_id))

            if not page or page.get("missing"):
                logger.warning(f"⚠️ 페이지 없음 (pageid={page_id})")
                return None

            return {
                "title": page.get("title", ""),
                "extract": page.get("extract", ""),
                "url": page.get("fullurl", f"https://{lang}.wikipedia.org/?curid={page_id}"),
                "pageid": page_id,
                "disambiguation": "disambiguation" in page.get("pageprops", {}),
            }
                
        except Exception as e:
            logger.error(f"❌ 상세 정보 fetch 실패 (pageid={page_id}, lang={lang}): {e}")
            return None
