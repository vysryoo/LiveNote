"""
서버 유틸 함수 모음
"""
from __future__ import annotations

import json
from typing import Any, Iterable, List

from cap1_QA_module.qakit.models import RAGChunk as QARAGChunk, RAGContext as QARAGContext
from cap1_openalex_module.openalexkit.models import RAGChunk as OpenAlexRAGChunk
from cap1_wiki_module.wikikit.models import RAGChunk as WikiRAGChunk
from cap1_youtube_module.youtubekit.models import RAGChunk as YouTubeRAGChunk
from cap1_google_module.googlekit.models import RAGChunk as GoogleRAGChunk


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


def to_qa_rag_context(chunks: Iterable[Any]) -> QARAGContext:
    """RAG 청크를 QA 컨텍스트로 변환"""
    qa_chunks = []
    for chunk in chunks:
        qa_chunks.append(
            QARAGChunk(
                text=getattr(chunk, "text", ""),
                score=getattr(chunk, "score", 0.0),
                metadata=_as_metadata(chunk)
            )
        )
    return QARAGContext(chunks=qa_chunks)


def to_openalex_rag_chunks(chunks: Iterable[Any]) -> List[OpenAlexRAGChunk]:
    """RAG 청크를 OpenAlex 컨텍스트로 변환"""
    return [
        OpenAlexRAGChunk(text=getattr(chunk, "text", ""), score=getattr(chunk, "score", 0.0), metadata=_as_metadata(chunk))
        for chunk in chunks
    ]


def to_wiki_rag_chunks(chunks: Iterable[Any]) -> List[WikiRAGChunk]:
    """RAG 청크를 Wikipedia 컨텍스트로 변환"""
    return [
        WikiRAGChunk(text=getattr(chunk, "text", ""), score=getattr(chunk, "score", 0.0), metadata=_as_metadata(chunk))
        for chunk in chunks
    ]


def to_youtube_rag_chunks(chunks: Iterable[Any]) -> List[YouTubeRAGChunk]:
    """RAG 청크를 YouTube 컨텍스트로 변환"""
    return [
        YouTubeRAGChunk(text=getattr(chunk, "text", ""), score=getattr(chunk, "score", 0.0), metadata=_as_metadata(chunk))
        for chunk in chunks
    ]


def to_google_rag_chunks(chunks: Iterable[Any]) -> List[GoogleRAGChunk]:
    """RAG 청크를 Google 컨텍스트로 변환"""
    return [
        GoogleRAGChunk(text=getattr(chunk, "text", ""), score=getattr(chunk, "score", 0.0), metadata=_as_metadata(chunk))
        for chunk in chunks
    ]


def format_sse(data: dict, event: str | None = None) -> bytes:
    """SSE 포맷으로 직렬화"""
    serialized = json.dumps(data, ensure_ascii=False)
    if event:
        payload = f"event: {event}\n"
    else:
        payload = ""
    payload += f"data: {serialized}\n\n"
    return payload.encode("utf-8")
