"""
YouTubeKit 데이터 모델 정의
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from .config import flags


class RAGChunk(BaseModel):
    """RAG 검색 결과 청크"""
    text: Optional[str] = Field(default=None, description="청크 텍스트 내용")
    content: Optional[str] = Field(default=None, description="청크 텍스트 내용 (text의 별칭)")
    score: float = Field(default=0.0, description="유사도 점수")
    source: Optional[str] = Field(default=None, description="출처 (파일명 등)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="메타데이터")
    
    @field_validator('text', mode='before')
    @classmethod
    def use_content_if_text_missing(cls, v, info):
        """text가 없으면 content 사용"""
        if v is None and 'content' in info.data:
            return info.data['content']
        return v


class PreviousSummary(BaseModel):
    """이전 섹션 요약"""
    section_id: int = Field(..., description="섹션 번호")
    summary: str = Field(..., description="섹션 요약 텍스트")
    timestamp: Optional[int] = Field(default=None, description="타임스탬프 (ms)")


class YouTubeVideoInfo(BaseModel):
    """YouTube 동영상 상세 정보"""
    url: str = Field(..., description="동영상 URL")
    title: str = Field(..., description="동영상 제목")
    extract: str = Field(..., description="동영상 요약 (3문장 정도)")
    lang: str = Field(..., description="동영상 언어 (ko/en)")
    
    @field_validator('title', 'extract')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')


class YouTubeRequest(BaseModel):
    """YouTube 동영상 추천 요청"""
    
    # ━━━ 필수 필드 ━━━
    lecture_id: str = Field(..., description="강의 세션 ID (추적용)")
    section_id: int = Field(..., ge=1, description="현재 섹션 번호")
    lecture_summary: str = Field(..., min_length=10, description="현재 강의 섹션 요약")
    
    # ━━━ 선택 필드 ━━━
    language: str = Field(default="ko", description="응답 언어 (ko/en)")
    top_k: int = Field(default=5, ge=1, le=10, description="추천 동영상 개수")
    verify_yt: bool = Field(
        default=flags.VERIFY_YT_DEFAULT, 
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
    yt_lang: str = Field(default="en", description="YouTube 검색 언어 (en/ko)")
    exclude_titles: List[str] = Field(
        default_factory=list,
        description="제외할 동영상 제목 리스트 (중복 방지)"
    )
    min_score: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="최소 점수 임계값 (이 점수 미만 동영상 제외)"
    )
    
    # ━━━ 별칭 지원 ━━━
    tok_k: Optional[int] = Field(default=None, description="top_k 별칭")
    
    @field_validator("top_k")
    @classmethod
    def clamp_top_k(cls, v: int) -> int:
        return max(1, min(10, v))
    
    def effective_top_k(self) -> int:
        """tok_k가 있으면 우선 사용, 없으면 top_k 사용"""
        return int(self.tok_k) if self.tok_k is not None else int(self.top_k)


class YouTubeResponse(BaseModel):
    """YouTube 동영상 추천 응답"""
    lecture_id: str = Field(..., description="강의 세션 ID")
    section_id: int = Field(..., description="섹션 번호")
    video_info: YouTubeVideoInfo = Field(..., description="동영상 정보")
    reason: str = Field(..., description="추천 이유 (1-2문장)")
    score: float = Field(..., ge=0.0, le=10.0, description="관련도 점수 (0-10)")
    
    @field_validator('reason')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')
