"""
자료 추천 서비스
"""
from __future__ import annotations

from typing import Dict, List, Optional

from core.config import Settings
from core.schemas import ResourceType

from .models import RecContext, Recommendation
from .pipeline import Provider, recommend
from .providers import build_providers


class RecommendService:
    """자료 종류별 공급자를 가지고 추천한다."""

    def __init__(self, settings: Settings, providers: Optional[Dict[ResourceType, Provider]] = None) -> None:
        """서비스를 만든다.

        Args:
            settings: 서버 설정
            providers: 자료 종류 → 공급자. None이면 설정으로 만듦
        """
        self.providers = providers or build_providers(settings)

    async def recommend(self, resource_type: ResourceType, context: RecContext) -> List[Recommendation]:
        """자료 종류 하나를 추천한다.

        Args:
            resource_type: 자료 종류
            context: 추천 입력
        Returns:
            점수 내림차순 추천 결과
        Raises:
            Exception: 검색어 생성이 실패한 경우
        """
        return await recommend(self.providers[resource_type], context)

    async def close(self) -> None:
        """공급자들의 연결을 닫는다."""
        for provider in self.providers.values():
            await provider.close()
