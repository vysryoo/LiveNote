"""
FastAPI 서버 설정 정의
"""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, HttpUrl

from .models import QnAType


class RAGSettings(BaseModel):
    """RAG 관련 설정"""
    
    # RAG 컬렉션 ID를 만들 때 사용할 접두사 (lecture_id 결합)
    collection_prefix: str = Field(default="lecture", description="컬렉션 ID 접두사")
    # QA용 RAG 검색 개수
    qa_retrieve_top_k: int = Field(default=2, ge=1, description="QA 컨텍스트로 사용할 청크 개수")
    # REC용 RAG 검색 개수
    rec_retrieve_top_k: int = Field(default=2, ge=1, description="REC 컨텍스트로 사용할 청크 개수")


class QASettings(BaseModel):
    """QA 서비스 설정"""
    
    language: str = Field(default="ko", description="QA 생성 언어")
    question_types: List[QnAType] = Field(
        default_factory=lambda: [
            QnAType.CONCEPT,
            QnAType.APPLICATION,
            QnAType.COMPARISON,
            QnAType.ADVANCED,
        ],
        description="생성할 질문 유형"
    )
    qa_top_k: int = Field(default=4, ge=1, description="QA 생성 개수")


class OpenAlexSettings(BaseModel):
    """OpenAlex 추천 설정"""
    
    top_k: int = Field(default=1, ge=1, le=10, description="논문 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    #verify: bool = Field(default=False, description="LLM 검증 여부")
    year_from: int = Field(default=1960, description="검색 최소 연도")
    sort_by: str = Field(default="hybrid", description="정렬 기준")
    min_score: float = Field(default=5.0, ge=0.0, le=10.0, description="최소 점수")
    language: str = Field(default="ko", description="응답 언어")


class WikiSettings(BaseModel):
    """위키 추천 설정"""
    
    top_k: int = Field(default=1, ge=1, le=10, description="Wiki 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    #verify: bool = Field(default=True, description="LLM 검증 여부")
    wiki_lang: str = Field(default="en", description="Wikipedia 검색 언어")
    language: str = Field(default="ko", description="응답 언어")
    min_score: float = Field(default=5.0, ge=0.0, le=10.0, description="최소 점수")
    fallback_to_ko: bool = Field(default=True, description="부족 시 언어 fallback 여부")


class YouTubeSettings(BaseModel):
    """YouTube 추천 설정"""
    
    top_k: int = Field(default=1, ge=1, le=10, description="YouTube 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    #verify: bool = Field(default=False, description="LLM 검증 여부")
    yt_lang: str = Field(default="en", description="YouTube 검색 언어")
    language: str = Field(default="ko", description="응답 언어")
    min_score: float = Field(default=7.0, ge=0.0, le=10.0, description="최소 점수")


class GoogleSettings(BaseModel):
    """Google 검색 추천 설정"""
    
    top_k: int = Field(default=1, ge=1, le=10, description="Google 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    #verify: bool = Field(default=False, description="LLM 검증 여부")
    search_lang: str = Field(default="en", description="Google 검색 언어")
    language: str = Field(default="ko", description="응답 언어")
    min_score: float = Field(default=3.0, ge=0.0, le=10.0, description="최소 점수")


class RECSettings(BaseModel):
    """REC 통합 설정"""
    
    openalex: OpenAlexSettings = Field(default_factory=OpenAlexSettings)
    wiki: WikiSettings = Field(default_factory=WikiSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)
    google: GoogleSettings = Field(default_factory=GoogleSettings)


class SummarySettings(BaseModel):
    """요약 생성 설정"""

    model: str = Field(default="gpt-4o", description="요약에 사용할 OpenAI 모델명")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="샘플링 온도")
    max_tokens: int = Field(default=256, ge=1, description="최대 토큰")
    system_prompt: str = Field(
        default=(
            "당신은 강의 내용을 간결하게 요약하는 비서입니다. "
            "아래에서 제공하는 전사 텍스트는 하나의 섹션(약 30초 분량)에 해당하며, "
            "반드시 해당 섹션의 내용만 이용해서 요약하세요. "
            "다른 섹션이나 이전/이후 내용은 절대 추측하거나 언급하지 마세요. "
            "주어진 섹션을 한국어로 1~2문장 정도로 핵심만 요약해 주세요."
        ),
        description="시스템 프롬프트"
    )
    min_transcript_length: int = Field(
        default=10,
        ge=1,
        description="요약을 시도할 최소 전사 길이(문자 수)"
    )
    short_transcript_message: str = Field(
        default="요약을 생성하기에 강의가 너무 짧습니다.",
        description="전사가 너무 짧을 때 콜백으로 전송할 안내 메시지"
    )
    callback_url: HttpUrl | None = Field(
        default=None,
        description="기본 요약 콜백 URL (요청에서 미지정 시 사용)"
    )


class AppSettings(BaseModel):
    """서버 전체 설정"""
    
    rag: RAGSettings = Field(default_factory=RAGSettings)
    qa: QASettings = Field(default_factory=QASettings)
    rec: RECSettings = Field(default_factory=RECSettings)
    summary: SummarySettings = Field(default_factory=SummarySettings)
