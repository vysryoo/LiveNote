"""
서버 유틸 함수 모음
"""
from __future__ import annotations

import json
from typing import Any, Iterable, List

from core.schemas import RAGChunk
from qa.qakit.models import RAGContext as QARAGContext
from pydantic import BaseModel, ConfigDict


def build_collection_id(prefix: str, lecture_id: str) -> str:
    """RAG 컬렉션 ID 생성"""
    lecture_id = lecture_id.strip()
    if not lecture_id:
        raise ValueError("lecture_id는 비어 있을 수 없습니다.")
    return f"{prefix}_{lecture_id}"


def _as_metadata(chunk: Any) -> dict:
    """메타데이터 가져오기"""
    metadata = getattr(chunk, "metadata", None)
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    return dict(metadata)


def to_rag_chunks(chunks: Iterable[Any]) -> List[RAGChunk]:
    """RAG 검색 결과를 모듈 공통 조각 형식으로 변환"""
    return [
        RAGChunk(text=getattr(chunk, "text", ""), score=getattr(chunk, "score", 0.0), metadata=_as_metadata(chunk))
        for chunk in chunks
    ]


def to_qa_rag_context(chunks: Iterable[Any]) -> QARAGContext:
    """RAG 검색 결과를 QA 컨텍스트로 변환"""
    return QARAGContext(chunks=to_rag_chunks(chunks))


def format_sse(data: dict, event: str | None = None) -> bytes:
    """SSE 포맷으로 직렬화"""
    serialized = json.dumps(data, ensure_ascii=False)
    if event:
        payload = f"event: {event}\n"
    else:
        payload = ""
    payload += f"data: {serialized}\n\n"
    return payload.encode("utf-8")


def to_camel(string: str) -> str:
    """snake_case → camelCase 변환"""
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """camelCase 요청/응답을 위한 베이스 모델"""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
