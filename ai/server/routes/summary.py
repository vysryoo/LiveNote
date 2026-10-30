"""
요약 생성 API (Callback)
"""
from __future__ import annotations

import logging
from typing import List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field, HttpUrl, field_validator

from core.config import Settings
from core.tasks import run_in_background
from core.timing import RequestTimer
from summary.service import SHORT_TRANSCRIPT_MESSAGE

from ..callback import post_callback
from ..dependencies import Services, get_app_settings, get_services
from ..models import CamelModel

router = APIRouter(prefix="/summary", tags=["SUMMARY"])
logger = logging.getLogger(__name__)


class SummaryGenerateRequest(CamelModel):
    """요약 생성 입력"""

    lecture_id: int = Field(..., ge=1, description="강의 ID")
    section_index: int = Field(..., ge=0, description="섹션 인덱스(0-base)")
    transcript: List[str] | str = Field(
        ...,
        description="전사 텍스트 (문장 배열 또는 단일 문자열)"
    )
    summary_id: Optional[int] = Field(default=None, description="기존 요약 ID (옵션)")
    start_sec: Optional[int] = Field(default=None, ge=0, description="요약 시작 초 (옵션)")
    end_sec: Optional[int] = Field(default=None, ge=0, description="요약 종료 초 (옵션)")
    phase: str = Field(default="FINAL", description="요약 단계 (예: PARTIAL/FINAL)")
    callback_url: Optional[HttpUrl] = Field(default=None, description="콜백 URL (미지정 시 설정값 사용)")

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, value: List[str] | str) -> List[str] | str:
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("transcript는 비어 있을 수 없습니다.")
            return value.strip()
        cleaned = [line.strip() for line in value if isinstance(line, str) and line.strip()]
        if not cleaned:
            raise ValueError("transcript는 비어 있을 수 없습니다.")
        return cleaned

    @field_validator("phase")
    @classmethod
    def normalize_phase(cls, value: str) -> str:
        return (value or "FINAL").upper()


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_summary(
    request: SummaryGenerateRequest,
    services: Services = Depends(get_services),
    settings: Settings = Depends(get_app_settings),
):
    """요약 생성 콜백 엔드포인트"""
    timer = RequestTimer(
        "summary", lecture_id=request.lecture_id, section_index=request.section_index, phase=request.phase
    )
    timer.mark("received")
    transcript_text = _to_transcript_text(request.transcript)
    callback_url = _resolve_callback_url(request.callback_url, settings)

    if services.summary.is_too_short(transcript_text):
        logger.info(
            "요약 건너뜀: lectureId=%s section=%s 이유=too_short len=%s",
            request.lecture_id,
            request.section_index,
            len(transcript_text.strip()),
        )
        payload = _build_callback_payload(
            request,
            SHORT_TRANSCRIPT_MESSAGE,
            status="TOO_SHORT",
        )

        async def send_skip():
            await post_callback(callback_url, payload, settings)
            timer.mark("skipped_callback_sent")

        run_in_background(send_skip(), name=f"summary-skip-{request.lecture_id}-{request.section_index}")
        return {"status": "skipped", "reason": "too_short"}

    async def run_and_callback():
        try:
            summary_text = await services.summary.summarize(transcript_text)
            timer.mark("generated", summary_chars=len(summary_text))
            payload = _build_callback_payload(request, summary_text, status="COMPLETED")
            await post_callback(callback_url, payload, settings)
            timer.mark("callback_sent")
        except Exception as exc:  # pragma: no cover - 네트워크/외부 API 예외
            timer.mark("failed")
            logger.exception("요약 생성 실패: %s", exc)

    run_in_background(run_and_callback(), name=f"summary-{request.lecture_id}-{request.section_index}")
    return {"status": "accepted"}


def _build_callback_payload(request: SummaryGenerateRequest, summary_text: str, status: str | None = None) -> dict:
    """백엔드로 전송할 페이로드 생성"""
    start_sec = request.start_sec if request.start_sec is not None else request.section_index * 30
    end_sec = request.end_sec if request.end_sec is not None else start_sec + 30
    payload = {
        "id": request.summary_id,
        "summaryId": request.summary_id,
        "lectureId": request.lecture_id,
        "sectionIndex": request.section_index,
        "startSec": start_sec,
        "endSec": end_sec,
        "text": summary_text,
        "phase": request.phase,
    }
    if status:
        payload["status"] = status
    return payload


def _resolve_callback_url(explicit_url: Optional[HttpUrl], settings: Settings) -> str:
    """요청/설정 기반으로 콜백 URL 결정 후 type=summary 보장"""
    target = explicit_url or settings.summary.callback_url or settings.summary_callback_url
    if not target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="callback_url이 지정되지 않았습니다 (요청, settings.summary.callback_url, SUMMARY_CALLBACK_URL 중 하나 필요).",
        )
    return _ensure_summary_type(str(target))


def _ensure_summary_type(url: str) -> str:
    """콜백 URL에 type=summary 쿼리 추가"""
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query_params.setdefault("type", "summary")
    new_query = urlencode(query_params)
    return urlunparse(parsed._replace(query=new_query))


def _to_transcript_text(transcript: List[str] | str) -> str:
    """문장 배열/단일 텍스트를 하나의 문자열로 변환"""
    if isinstance(transcript, str):
        return transcript.strip()
    return "\n".join(transcript).strip()
