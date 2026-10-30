"""
AI 서버 설정

환경변수와 ai/.env를 서버 시작 시 한 번 읽는다. 같은 키가 둘 다 있으면 환경변수가 우선한다.
요청 처리 방식(검색 개수, 질문 유형, 추천 기준 등)은 코드 기본값을 쓰고, 테스트에서는 객체를 만들어 바꾼다.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.schemas import QnAType

AI_ROOT = Path(__file__).resolve().parents[1]


class RAGSettings(BaseModel):
    """RAG 검색 설정."""

    # 컬렉션 ID = 접두사 + "_" + 강의 ID
    collection_prefix: str = Field(default="lecture", description="컬렉션 ID 접두사")
    qa_retrieve_top_k: int = Field(default=2, ge=1, description="QA 컨텍스트로 사용할 강의 자료 조각 개수")
    rec_retrieve_top_k: int = Field(default=2, ge=1, description="추천 컨텍스트로 사용할 강의 자료 조각 개수")
    # 강의 자료 조각과 따로 검색해 뒤에 붙임
    summary_retrieve_top_k: int = Field(default=1, ge=0, description="함께 넣을 이전 섹션 요약 개수")
    # 백엔드가 previousSummaries로 직접 보내는 직전 섹션 수. 검색에서는 이 범위를 뺌
    recent_summary_window: int = Field(default=3, ge=0, description="요약 검색에서 제외할 직전 섹션 수")


class QASettings(BaseModel):
    """QnA 생성 설정."""

    language: str = Field(default="ko", description="QA 생성 언어")
    question_types: List[QnAType] = Field(
        default_factory=lambda: [QnAType.CONCEPT, QnAType.APPLICATION, QnAType.COMPARISON, QnAType.ADVANCED],
        description="생성할 질문 유형",
    )
    max_question_types: int = Field(default=4, ge=1, description="한 요청에서 생성할 질문 유형 최대 개수 (유형마다 1개씩 생성)")


class PaperSettings(BaseModel):
    """논문 추천 설정 (OpenAlex)."""

    top_k: int = Field(default=1, ge=1, le=10, description="논문 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    year_from: int = Field(default=1960, description="검색 최소 연도")
    sort_by: str = Field(default="hybrid", description="정렬 기준")
    min_score: float = Field(default=5.0, ge=0.0, le=10.0, description="최소 점수")
    language: str = Field(default="ko", description="응답 언어")


class WikiSettings(BaseModel):
    """위키 추천 설정."""

    top_k: int = Field(default=1, ge=1, le=10, description="Wiki 추천 개수")
    verify: bool = Field(default=False, description="LLM 검증 여부")
    wiki_lang: str = Field(default="en", description="Wikipedia 검색 언어")
    language: str = Field(default="ko", description="응답 언어")
    min_score: float = Field(default=5.0, ge=0.0, le=10.0, description="최소 점수")
    fallback_to_ko: bool = Field(default=True, description="부족 시 언어 fallback 여부")


class VideoSettings(BaseModel):
    """영상 추천 설정 (YouTube)."""

    top_k: int = Field(default=1, ge=1, le=10, description="YouTube 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    yt_lang: str = Field(default="en", description="YouTube 검색 언어")
    language: str = Field(default="ko", description="응답 언어")
    min_score: float = Field(default=7.0, ge=0.0, le=10.0, description="최소 점수")


class BlogSettings(BaseModel):
    """블로그 추천 설정 (네이버 블로그)."""

    top_k: int = Field(default=1, ge=1, le=10, description="블로그 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    # 블로그 검색이 네이버라 검색 키워드를 한국어로 생성
    search_lang: str = Field(default="ko", description="블로그 검색 키워드 언어")
    language: str = Field(default="ko", description="응답 언어")
    min_score: float = Field(default=3.0, ge=0.0, le=10.0, description="최소 점수")


class RECSettings(BaseModel):
    """자료 추천 설정."""

    paper: PaperSettings = Field(default_factory=PaperSettings)
    wiki: WikiSettings = Field(default_factory=WikiSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    blog: BlogSettings = Field(default_factory=BlogSettings)


class SummarySettings(BaseModel):
    """요약 생성 설정."""

    # 모델과 추론 강도는 LLM 용도 설정(llm_summary_*)을 따름
    max_tokens: int = Field(default=256, ge=1, description="최대 토큰")
    min_transcript_length: int = Field(default=10, ge=1, description="요약을 시도할 최소 전사 길이(문자 수)")
    callback_url: Optional[HttpUrl] = Field(default=None, description="기본 요약 콜백 URL (요청에서 미지정 시 사용)")


class Settings(BaseSettings):
    """서버 전체 설정. 대문자 환경변수 이름(예: OPENAI_API_KEY)이 같은 이름의 소문자 필드에 들어간다."""

    model_config = SettingsConfigDict(env_file=AI_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    # 외부 서비스 키
    openai_api_key: str = ""
    internal_api_key: str = ""
    youtube_api_key: str = ""
    naver_client_id: str = ""
    naver_client_secret: str = ""
    wikikit_user_agent: str = "WikiKit/0.1 (+https://github.com/nongman25; contact: wook252wook@gmail.com)"
    summary_callback_url: Optional[HttpUrl] = None

    # LLM 모델과 추론 강도. 용도별 값이 없으면 llm_model, 그것도 없으면 core.llm 기본값
    llm_model: Optional[str] = None
    llm_summary_model: Optional[str] = None
    llm_qa_model: Optional[str] = None
    llm_query_model: Optional[str] = None
    llm_verify_model: Optional[str] = None
    llm_summary_reasoning_effort: Optional[str] = None
    llm_qa_reasoning_effort: Optional[str] = None
    llm_query_reasoning_effort: Optional[str] = None
    llm_verify_reasoning_effort: Optional[str] = None

    # RAG 저장소와 강의 자료 분할. 분할 값이 없으면 rag.splitters.ChunkSettings 기본값
    rag_persist_dir: Path = AI_ROOT / "server_storage" / "chroma_data"
    rag_upload_dir: Path = AI_ROOT / "server_storage" / "uploads"
    rag_embedding_model: str = "text-embedding-3-large"
    rag_openai_api_key: Optional[str] = None
    rag_chunk_strategy: Optional[str] = None
    rag_chunk_tokens: Optional[int] = None
    rag_chunk_overlap_tokens: Optional[int] = None
    rag_semantic_percentile: Optional[float] = None
    rag_semantic_overlap_sentences: Optional[int] = None
    rag_semantic_min_tokens: Optional[int] = None
    rag_semantic_max_tokens: Optional[int] = None

    # 요청 처리 방식
    rag: RAGSettings = Field(default_factory=RAGSettings)
    qa: QASettings = Field(default_factory=QASettings)
    rec: RECSettings = Field(default_factory=RECSettings)
    summary: SummarySettings = Field(default_factory=SummarySettings)

    @field_validator("rag_persist_dir", "rag_upload_dir")
    @classmethod
    def resolve_from_ai_root(cls, path: Path) -> Path:
        """상대 경로는 실행 위치가 아니라 ai/ 폴더 기준으로 바꾼다."""
        return path if path.is_absolute() else AI_ROOT / path

    def check_required(self) -> None:
        """서버 실행에 필요한 키가 모두 있는지 확인한다.

        Raises:
            ValueError: 빠진 키가 있는 경우. 빠진 환경변수 이름을 모두 담음
        """
        required = {
            "OPENAI_API_KEY": self.openai_api_key,
            "INTERNAL_API_KEY": self.internal_api_key,
            "YOUTUBE_API_KEY": self.youtube_api_key,
            "NAVER_CLIENT_ID": self.naver_client_id,
            "NAVER_CLIENT_SECRET": self.naver_client_secret,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"환경변수가 설정되지 않음: {', '.join(missing)}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """환경변수와 ai/.env로 만든 설정을 돌려준다. 처음 한 번만 읽는다.

    Returns:
        서버 설정
    """
    return Settings()
