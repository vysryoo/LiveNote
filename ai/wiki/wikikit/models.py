"""
Pydantic models for WikiKit module
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class RAGChunk(BaseModel):
    """RAG 검색 결과 청크"""
    text: str
    score: float
    metadata: Optional[dict] = None


class PreviousSummary(BaseModel):
    """이전 섹션 요약"""
    section_id: int
    summary: str
    timestamp: Optional[int] = None


class WikiPageInfo(BaseModel):
    """Wikipedia 문서 상세 정보"""
    url: str = Field(..., description="문서 URL")
    title: str = Field(..., description="문서 제목")
    extract: str = Field(..., description="문서 요약 (3문장 정도)")
    lang: str = Field(..., description="문서 언어 (ko/en)")
    page_id: int = Field(..., description="Wikipedia 페이지 ID")
    
    @field_validator('extract', 'title')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')


class WikiRequest(BaseModel):
    """Wikipedia 문서 추천 요청"""
    
    # ━━━ 필수 필드 ━━━
    lecture_id: str = Field(..., description="강의 세션 ID (추적용)")
    section_id: int = Field(..., ge=1, description="현재 섹션 번호")
    lecture_summary: str = Field(..., min_length=10, description="현재 강의 섹션 요약")
    
    # ━━━ 선택 필드 ━━━
    language: str = Field(default="en", description="응답 언어 (ko/en)")
    top_k: int = Field(default=5, ge=1, le=10, description="추천 문서 개수")
    verify_wiki: bool = Field(
        default=True, 
        description="LLM 검증 여부 (True: LLM, False: Heuristic)"
    )
    
    # ━━━ 컨텍스트 필드 ━━━
    previous_summaries: Optional[List[PreviousSummary]] = Field(
        default_factory=list,
        description="이전 N개 섹션 요약 (컨텍스트 확장용)"
    )
    rag_context: Optional[List[RAGChunk]] = Field(
        default_factory=list,
        description="RAG 검색 결과 (강의노트/이전 섹션)"
    )
    
    # ━━━ 검색 제어 필드 ━━━
    wiki_lang: str = Field(default="en", description="Wikipedia 검색 언어 (en/ko)")
    fallback_to_ko: bool = Field(
        default=True, 
        description="영어 결과 부족 시 한국어로 보충 여부"
    )
    exclude_titles: Optional[List[str]] = Field(
        default_factory=list,
        description="제외할 문서 제목 리스트 (중복 방지)"
    )
    min_score: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="최소 점수 임계값 (이 점수 미만 문서 제외)"
    )


class WikiResponse(BaseModel):
    """Wikipedia 문서 추천 응답"""
    lecture_id: str
    section_id: int
    page_info: WikiPageInfo
    reason: str = Field(..., description="추천 이유 (1-2문장)")
    score: float = Field(..., ge=0.0, le=15.0, description="관련도 점수 (0-10, LLM이 초과 가능)")
    
    @field_validator('reason')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')
