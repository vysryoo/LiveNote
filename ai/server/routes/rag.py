"""
RAG 관련 API 엔드포인트
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from core.config import Settings
from rag.service import SummaryItem, build_collection_id

from ..dependencies import Services, get_app_settings, get_services
from ..models import NonBlankStr

router = APIRouter(prefix="/rag", tags=["RAG"])


class TextUpsertItem(BaseModel):
    """텍스트 업서트 입력 청크"""
    
    text: str = Field(..., min_length=1, description="저장할 텍스트")
    id: Optional[str] = Field(default=None, description="선택적 ID")
    section_id: Optional[str] = Field(default=None, description="섹션 ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class TextUpsertRequest(BaseModel):
    """텍스트 업서트 요청"""
    
    lecture_id: NonBlankStr = Field(..., min_length=1, description="강의 ID")
    items: List[TextUpsertItem] = Field(..., min_length=1, description="업서트할 청크들")


@router.post("/pdf-upsert", status_code=status.HTTP_200_OK)
async def upsert_pdf(
    lecture_id: str = Form(..., description="강의 ID"),
    file: UploadFile = File(..., description="업로드할 PDF 파일"),
    base_metadata: str | None = Form(None, description="PDF 전체에 적용할 메타데이터(JSON)"),
    services: Services = Depends(get_services),
    settings: Settings = Depends(get_app_settings),
):
    """PDF 문서를 업서트"""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드할 수 있습니다."
        )
    
    lecture_id = lecture_id.strip()
    if not lecture_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lecture_id는 비어 있을 수 없습니다."
        )
    
    metadata = _parse_metadata(base_metadata)
    pdf_path = _prepare_upload_path(settings, lecture_id, file.filename)

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="빈 파일은 업로드할 수 없습니다."
        )
    pdf_path.write_bytes(content)
    
    collection_id = build_collection_id(settings.rag.collection_prefix, lecture_id)
    result = await asyncio.to_thread(
        services.rag.upsert_pdf, collection_id=collection_id, pdf_path=str(pdf_path), base_metadata=metadata
    )
    return {"collection_id": collection_id, "result": result}


@router.post("/text-upsert", status_code=status.HTTP_200_OK)
async def upsert_text(
    request: TextUpsertRequest,
    services: Services = Depends(get_services),
    settings: Settings = Depends(get_app_settings),
):
    """텍스트 요약본 업서트"""
    collection_id = build_collection_id(settings.rag.collection_prefix, request.lecture_id)
    
    # 이 경로로 들어오는 텍스트는 백엔드가 보내는 섹션 확정 요약
    summaries = [
        SummaryItem(text=item.text, id=item.id, section_id=item.section_id, metadata=dict(item.metadata))
        for item in request.items
    ]
    result = await asyncio.to_thread(services.rag.upsert_summaries, collection_id=collection_id, items=summaries)
    return {"collection_id": collection_id, "result": result}


def _parse_metadata(base_metadata: Optional[str]) -> Optional[dict[str, Any]]:
    """PDF 메타데이터 JSON 문자열을 dict로 바꾼다. 없으면 None, 형식이 틀리면 400으로 거절한다."""
    if not base_metadata:
        return None
    try:
        return json.loads(base_metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"base_metadata JSON 파싱 실패: {exc}"
        ) from exc


def _prepare_upload_path(settings: Settings, lecture_id: str, filename: Optional[str]) -> Path:
    """강의별 업로드 폴더를 만들고 PDF를 저장할 경로를 돌려준다. 파일 이름의 경로 부분은 버린다."""
    upload_dir = settings.rag_upload_dir / lecture_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / Path(filename or "uploaded.pdf").name
