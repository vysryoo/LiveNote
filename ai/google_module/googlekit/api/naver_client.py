"""
네이버 블로그 검색 API 클라이언트 (NAVER API HUB)

Google Custom Search JSON API가 신규 가입을 받지 않고 2027-01-01 종료 예정이라 블로그 검색을 네이버로 대체한다.
네이버 개발자센터의 검색 API는 신규 발급이 종료돼, 네이버 클라우드의 NAVER API HUB 엔드포인트를 사용한다.
"""
import html
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from ..config.google_config import GoogleConfig

logger = logging.getLogger(__name__)

# 네이버가 검색어 일치 부분을 <b> 태그로 감싸서 돌려줌
TAG_PATTERN = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return html.unescape(TAG_PATTERN.sub("", text or "")).strip()


class NaverBlogSearchClient:
    """네이버 블로그 검색 API 클라이언트"""

    BASE_URL = "https://naverapihub.apigw.ntruss.com/search/v1/blog"
    MAX_DISPLAY = 100

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        """
        초기화

        Args:
            client_id: NAVER API HUB Application의 Client ID (None이면 환경 변수 사용)
            client_secret: NAVER API HUB Application의 Client Secret (None이면 환경 변수 사용)
            transport: HTTP 전송 계층. 테스트에서 실제 요청 대신 사용
        """
        self.client_id = client_id or GoogleConfig.NAVER_CLIENT_ID
        self.client_secret = client_secret or GoogleConfig.NAVER_CLIENT_SECRET
        self.transport = transport

        if not self.client_id:
            raise ValueError("NAVER_CLIENT_ID가 설정되지 않았습니다.")
        if not self.client_secret:
            raise ValueError("NAVER_CLIENT_SECRET가 설정되지 않았습니다.")

    async def search(
        self,
        query: str,
        lang: str = "ko",
        num: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        블로그 글을 검색한다.

        Args:
            query: 검색 쿼리
            lang: 호출부 호환용. 네이버 블로그 검색은 언어 지정을 지원하지 않아 사용하지 않음
            num: 결과 개수 (최대 100)

        Returns:
            {"title", "link", "snippet", "displayLink"} 목록. 실패하면 빈 목록
        """
        params = {"query": query, "display": min(num, self.MAX_DISPLAY), "sort": "sim"}
        headers = {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, transport=self.transport) as client:
                response = await client.get(self.BASE_URL, params=params, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ 네이버 블로그 검색 오류 ({response.status_code}): {response.text[:200]}")
                return []

            items = response.json().get("items", [])
            logger.info(f"🔍 네이버 블로그 검색 응답: {len(items)}개 결과")
            return [
                {
                    "title": _clean(item.get("title", "")),
                    "link": item.get("link", ""),
                    "snippet": _clean(item.get("description", "")),
                    "displayLink": item.get("bloggername", "") or item.get("bloggerlink", ""),
                }
                for item in items
            ]
        except httpx.HTTPError as e:
            logger.error(f"❌ 네이버 블로그 검색 호출 실패: {e}")
            return []
        except ValueError as e:
            logger.error(f"❌ 네이버 블로그 검색 응답 해석 실패: {e}")
            return []
