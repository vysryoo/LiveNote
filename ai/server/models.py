"""
라우트 공용 요청 모델 타입
"""
from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict


def _reject_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("공백만으로 된 값은 받지 않음")
    return value


# 공백만 있는 문자열을 거부하는 문자열 타입
NonBlankStr = Annotated[str, AfterValidator(_reject_blank)]


def to_camel(string: str) -> str:
    """snake_case를 camelCase로 바꾼다."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """camelCase 필드 이름으로도 받는 요청 모델."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
