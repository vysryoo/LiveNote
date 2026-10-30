"""
자료 종류별 추천 공급자
"""
from __future__ import annotations

from typing import Dict

from core.config import Settings
from core.schemas import ResourceType

from ..pipeline import Provider
from .blog import BlogProvider, NaverBlogClient
from .paper import PaperProvider
from .video import VideoProvider, YouTubeClient
from .wiki import WikiClient, WikiProvider


def build_providers(settings: Settings) -> Dict[ResourceType, Provider]:
    """서버 설정으로 자료 종류별 공급자를 만든다.

    Args:
        settings: 서버 설정 (API 키, 자료 종류별 추천 기준)
    Returns:
        자료 종류 → 공급자
    Raises:
        ValueError: 네이버 검색 인증 정보가 비어 있는 경우
    """
    rec = settings.rec
    return {
        ResourceType.PAPER: PaperProvider(rec.paper),
        ResourceType.WIKI: WikiProvider(rec.wiki, api=WikiClient(settings.wikikit_user_agent)),
        ResourceType.VIDEO: VideoProvider(rec.video, api=YouTubeClient(settings.youtube_api_key)),
        ResourceType.BLOG: BlogProvider(
            rec.blog, api=NaverBlogClient(settings.naver_client_id, settings.naver_client_secret)
        ),
    }
