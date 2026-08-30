"""
YouTube API 클라이언트 (Data API v3 + Transcript)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..config.youtube_config import YouTubeConfig

logger = logging.getLogger(__name__)


@dataclass
class YouTubeSearchItem:
    """YouTube 검색 결과 아이템"""
    video_id: str
    title: str
    description: str
    channel_title: str
    publish_time: str


@dataclass
class YouTubeVideoDetail:
    """YouTube 동영상 상세 정보"""
    video_id: str
    title: str
    description: str
    default_lang: Optional[str]
    view_count: int
    duration_iso8601: Optional[str]
    channel_title: str
    publish_time: str

    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


class YouTubeAPIClient:
    """YouTube Data API v3 클라이언트"""
    
    BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: Optional[str] = None, timeout: float | None = None):
        self.api_key = api_key or YouTubeConfig.YOUTUBE_API_KEY
        self.timeout = timeout or YouTubeConfig.TIMEOUT

    async def search_videos(
        self, q: str, lang: str, max_results: int = 8
    ) -> List[YouTubeSearchItem]:
        """YouTube 동영상 검색"""
        if YouTubeConfig.OFFLINE_MODE or not self.api_key:
            # Offline stub
            return [
                YouTubeSearchItem(
                    video_id=f"stub_{i}",
                    title=f"{q} tutorial {i}",
                    description=f"This is a stub video about {q}.",
                    channel_title="StubChannel",
                    publish_time="2024-01-01T00:00:00Z",
                )
                for i in range(1, min(max_results, 5) + 1)
            ]

        params = {
            "part": "snippet",
            "type": "video",
            "q": q,
            "relevanceLanguage": lang,
            "maxResults": max_results,
            "key": self.api_key,
        }

        from importlib import import_module
        httpx = import_module("httpx")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.BASE}/search", params=params)
            resp.raise_for_status()
            data = resp.json()

        items: List[YouTubeSearchItem] = []
        for it in data.get("items", []):
            vid = it.get("id", {}).get("videoId")
            sn = it.get("snippet", {})
            if not vid or not sn:
                continue
            items.append(
                YouTubeSearchItem(
                    video_id=vid,
                    title=sn.get("title", ""),
                    description=sn.get("description", ""),
                    channel_title=sn.get("channelTitle", ""),
                    publish_time=sn.get("publishedAt", ""),
                )
            )
        return items

    async def get_videos(self, ids: List[str]) -> List[YouTubeVideoDetail]:
        """YouTube 동영상 상세 정보 조회"""
        if not ids:
            return []

        if YouTubeConfig.OFFLINE_MODE or not self.api_key:
            # Offline stub
            return [
                YouTubeVideoDetail(
                    video_id=vid,
                    title=f"Stub Video {vid}",
                    description="This is a stub description.",
                    default_lang="en",
                    view_count=1000 + i * 100,
                    duration_iso8601="PT10M",
                    channel_title="StubChannel",
                    publish_time="2024-01-01T00:00:00Z",
                )
                for i, vid in enumerate(ids)
            ]

        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(ids),
            "key": self.api_key,
        }
        
        from importlib import import_module
        httpx = import_module("httpx")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.BASE}/videos", params=params)
            resp.raise_for_status()
            data = resp.json()

        details: List[YouTubeVideoDetail] = []
        for it in data.get("items", []):
            vid = it.get("id")
            sn = it.get("snippet", {})
            stats = it.get("statistics", {})
            cd = it.get("contentDetails", {})
            if not vid:
                continue
            details.append(
                YouTubeVideoDetail(
                    video_id=vid,
                    title=sn.get("title", ""),
                    description=sn.get("description", ""),
                    default_lang=sn.get("defaultLanguage") or sn.get("defaultAudioLanguage"),
                    view_count=int(stats.get("viewCount", 0)),
                    duration_iso8601=cd.get("duration"),
                    channel_title=sn.get("channelTitle", ""),
                    publish_time=sn.get("publishedAt", ""),
                )
            )
        return details

    async def fetch_transcript(
        self, video_id: str, preferred_langs: List[str] | None = None
    ) -> str | None:
        """
        자막 가져오기 (youtube_transcript_api 사용)
        
        실패하면 None 반환 (자막 없음/비공개/오류)
        """
        if YouTubeConfig.OFFLINE_MODE:
            return None
            
        preferred_langs = preferred_langs or ["en", "ko"]
        
        # 🔧 Sync 함수를 async로 변환 (run_in_executor 사용)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._fetch_transcript_sync, 
            video_id, 
            preferred_langs
        )
    
    def _fetch_transcript_sync(self, video_id: str, preferred_langs: List[str]) -> str | None:
        """자막 가져오기 (동기 버전) - 버전 호환"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import (
                NoTranscriptFound,
                VideoUnavailable,
                TranscriptsDisabled,
            )
        except ImportError:
            logger.debug("youtube_transcript_api 미설치: 자막 생략 (%s)", video_id)
            return None

        try:
            # 방법 1: 인스턴스 메서드 시도 (최신 버전)
            try:
                api = YouTubeTranscriptApi()
                fetched = api.fetch(video_id, languages=preferred_langs)
                texts = [snippet.text for snippet in fetched]
                return " ".join(texts).strip()[:4000]
            except (AttributeError, NoTranscriptFound):
                pass  # 다음 방법 시도

            # 방법 2: 클래스 메서드 시도 (구버전 호환)
            try:
                chunks = YouTubeTranscriptApi.get_transcript(video_id, languages=preferred_langs)
                texts = [c.get("text", "") for c in chunks]
                return " ".join(texts).strip()[:4000]
            except (AttributeError, NoTranscriptFound):
                pass  # 다음 방법 시도

            # 방법 3: list 메서드로 수동/자동 자막 모두 시도
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

                # 수동 자막 우선
                for lang in preferred_langs:
                    try:
                        transcript = transcript_list.find_transcript([lang])
                        chunks = transcript.fetch()
                        texts = [c["text"] for c in chunks]
                        return " ".join(texts).strip()[:4000]
                    except Exception:
                        continue

                # 자동 생성 자막
                try:
                    transcript = transcript_list.find_generated_transcript(preferred_langs)
                    chunks = transcript.fetch()
                    texts = [c["text"] for c in chunks]
                    return " ".join(texts).strip()[:4000]
                except Exception:
                    pass
            except Exception:
                pass

            # 모든 방법 실패
            logger.debug(f"자막 없음 (모든 방법 실패): {video_id}")
            return None

        except NoTranscriptFound:
            logger.debug(f"자막 없음: {video_id}")
            return None
        except VideoUnavailable:
            logger.warning(f"비공개/삭제된 영상: {video_id}")
            return None
        except TranscriptsDisabled:
            logger.debug(f"자막 비활성화: {video_id}")
            return None
        except Exception as e:
            logger.warning(f"자막 가져오기 실패 ({video_id}): {e}")
            return None
