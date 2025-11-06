"""
OpenAlexKit 데이터 모델 정의
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RAGChunk(BaseModel):
    """RAG 검색 결과 청크"""
    text: str = Field(..., description="청크 텍스트 내용")
    score: float = Field(..., description="유사도 점수")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="메타데이터")


class PreviousSectionSummary(BaseModel):
    """이전 섹션 요약"""
    section_id: int = Field(..., description="섹션 번호")
    summary: str = Field(..., description="섹션 요약 텍스트")
    timestamp: Optional[int] = Field(default=None, description="타임스탬프 (ms)")


class OpenAlexRequest(BaseModel):
    """OpenAlex 논문 추천 요청"""
    
    # ━━━ 필수 필드 ━━━
    lecture_id: str = Field(..., description="강의 세션 ID (추적용)")
    section_id: int = Field(..., ge=1, description="현재 섹션 번호")
    section_summary: str = Field(..., min_length=10, description="현재 섹션 요약")
    
    # ━━━ 선택 필드 ━━━
    language: str = Field(default="ko", description="응답 언어 (ko/en)")
    top_k: int = Field(default=5, ge=1, le=10, description="추천 논문 개수")
    verify_openalex: bool = Field(
        default=True, 
        description="LLM 검증 여부 (True: LLM, False: Heuristic)"
    )
    
    # ━━━ 컨텍스트 필드 ━━━
    previous_summaries: List[PreviousSectionSummary] = Field(
        default_factory=list,
        description="이전 N개 섹션 요약 (컨텍스트 확장용)"
    )
    rag_context: List[RAGChunk] = Field(
        default_factory=list,
        description="RAG 검색 결과 (강의노트/이전 섹션)"
    )
    
    # ━━━ 검색 제어 필드 ━━━
    year_from: int = Field(default=2015, description="논문 출판 연도 필터 (YYYY)")
    exclude_ids: List[str] = Field(
        default_factory=list,
        description="제외할 논문 ID 리스트 (중복 방지)"
    )
    sort_by: str = Field(
        default="hybrid",
        description="정렬 기준 (relevance: 키워드 연관성, cited_by_count: 인용수, hybrid: 균형)"
    )
    min_score: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="최소 점수 임계값 (이 점수 미만 논문 제외, 기본: 5.0)"
    )


class PaperInfo(BaseModel):
    """논문 상세 정보"""
    url: str = Field(..., description="논문 URL (DOI or OpenAlex ID)")
    title: str = Field(..., description="논문 제목")
    abstract: str = Field(..., description="논문 초록 (최대 500자)")
    year: Optional[int] = Field(None, description="출판 연도")
    cited_by_count: int = Field(default=0, description="피인용 수")
    authors: List[str] = Field(default_factory=list, description="저자 리스트")


class OpenAlexResponse(BaseModel):
    """OpenAlex 논문 추천 응답"""
    lecture_id: str = Field(..., description="강의 세션 ID")
    section_id: int = Field(..., description="섹션 번호")
    paper_info: PaperInfo = Field(..., description="논문 정보")
    reason: str = Field(..., description="추천 이유 (1-2문장, 한국어/영어)")
    score: float = Field(..., ge=0.0, le=10.0, description="관련도 점수 (0-10)")
