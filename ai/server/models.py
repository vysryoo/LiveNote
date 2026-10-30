"""
라우트 공용 요청 모델 타입과 함수
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


def build_collection_id(prefix: str, lecture_id: str) -> str:
    """강의의 RAG 컬렉션 ID를 만든다.

    Args:
        prefix: 컬렉션 ID 접두사
        lecture_id: 강의 ID. 앞뒤 공백은 지움
    Returns:
        "접두사_강의ID"
    Raises:
        ValueError: 강의 ID가 비어 있는 경우
    """
    lecture_id = lecture_id.strip()
    if not lecture_id:
        raise ValueError("lecture_id는 비어 있을 수 없습니다.")
    return f"{prefix}_{lecture_id}"


def to_camel(string: str) -> str:
    """snake_case를 camelCase로 바꾼다."""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """camelCase 필드 이름으로도 받는 요청 모델."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
