"""
Google 검색 추천을 위한 데이터 모델
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

from .config import flags


# ━━━ 공통 모델 ━━━
class RAGChunk(BaseModel):
    """RAG 검색 결과 청크"""
    text: str = Field(..., description="청크 텍스트")
    score: float = Field(..., ge=0.0, description="관련도 점수")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="메타데이터")


class PreviousSummary(BaseModel):
    """이전 섹션 요약"""
    section_id: int = Field(..., ge=1, description="섹션 번호")
    summary: str = Field(..., min_length=1, description="섹션 요약")
    timestamp: Optional[str] = Field(default=None, description="타임스탬프")


# ━━━ Google 특화 모델 ━━━
class GoogleSearchResult(BaseModel):
    """Google 검색 결과 상세 정보"""
    url: str = Field(..., description="웹페이지 URL")
    title: str = Field(..., description="페이지 제목")
    snippet: str = Field(..., description="페이지 요약 (3-4줄)")
    display_link: str = Field(..., description="표시 도메인 (예: naver.com)")
    lang: str = Field(..., description="페이지 언어 (ko/en)")
    
    @field_validator('title', 'snippet')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')


class GoogleRequest(BaseModel):
    """Google 검색 결과 추천 요청"""
    
    # ━━━ 필수 필드 ━━━
    lecture_id: str = Field(..., description="강의 세션 ID (추적용)")
    section_id: int = Field(..., ge=1, description="현재 섹션 번호")
    lecture_summary: str = Field(..., min_length=10, description="현재 강의 섹션 요약")
    
    # ━━━ 선택 필드 ━━━
    language: str = Field(default="ko", description="응답 언어 (ko/en)")
    top_k: int = Field(default=5, ge=1, le=10, description="추천 검색 결과 개수")
    verify_google: bool = Field(
        default=flags.VERIFY_GOOGLE_DEFAULT,
        description="LLM 검증 여부 (True: LLM, False: Heuristic)"
    )
    
    # ━━━ 컨텍스트 필드 ━━━
    previous_summaries: List[PreviousSummary] = Field(
        default_factory=list,
        description="이전 N개 섹션 요약 (컨텍스트 확장용)"
    )
    rag_context: List[RAGChunk] = Field(
        default_factory=list,
        description="RAG 검색 결과 (강의노트/이전 섹션)"
    )
    
    # ━━━ 검색 제어 필드 ━━━
    search_lang: str = Field(default="ko", description="Google 검색 언어 (ko/en/auto)")
    exclude_urls: List[str] = Field(
        default_factory=list,
        description="제외할 URL 리스트 (중복 방지)"
    )
    min_score: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="최소 점수 임계값 (이 점수 미만 결과 제외)"
    )


class GoogleResponse(BaseModel):
    """Google 검색 결과 추천 응답"""
    lecture_id: str = Field(..., description="강의 세션 ID")
    section_id: int = Field(..., description="섹션 번호")
    search_result: GoogleSearchResult = Field(..., description="검색 결과 정보")
    reason: str = Field(..., description="추천 이유 (1-2문장)")
    score: float = Field(..., ge=0.0, le=15.0, description="관련도 점수 (0-10, LLM이 초과 가능)")
    
    @field_validator('reason')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')
