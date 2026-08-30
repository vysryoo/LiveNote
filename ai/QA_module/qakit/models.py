"""
QA 요청/응답 데이터 모델
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class RAGChunk(BaseModel):
    """RAG 검색 결과 청크"""
    text: str = Field(..., description="검색된 텍스트 청크")
    score: float = Field(..., ge=0.0, le=1.0, description="유사도 점수")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")


class RAGContext(BaseModel):
    """RAG 컨텍스트"""
    chunks: List[RAGChunk] = Field(default_factory=list, description="검색된 청크 리스트")


class PreviousQA(BaseModel):
    """이전 QA 항목"""
    type: str = Field(..., description="질문 유형 (개념/응용/비교 등)")
    question: str = Field(..., description="질문 내용")
    answer: str = Field(..., description="답변 내용")


class QARequest(BaseModel):
    """QA 생성 요청"""
    lecture_id: str = Field(..., description="강의 세션 ID")
    section_id: int = Field(..., ge=1, description="섹션 번호")
    section_summary: str = Field(..., min_length=10, description="섹션 요약 내용")
    subject: Optional[str] = Field(None, description="과목 (CS/수학/역사 등)")
    language: str = Field(default="ko", description="언어 (ko/en)")
    question_types: List[str] = Field(
        default_factory=list,
        description="질문 유형 리스트"
    )
    qa_count: int = Field(default=0, ge=0, le=5, description="생성할 질문 개수")
    rag_context: Optional[RAGContext] = Field(None, description="RAG 검색 컨텍스트")
    previous_qa: Optional[List[PreviousQA]] = Field(
        default_factory=list,
        description="중복 방지를 위한 이전 QA"
    )
    
    @field_validator('question_types')
    @classmethod
    def validate_question_types(cls, v: List[str]) -> List[str]:
        """질문 유형 검증"""
        # 유효한 유형만 허용
        valid_types = {"개념", "응용", "비교", "심화", "실습"}
        
        if v:  # 비어있지 않으면 검증
            invalid_types = [t for t in v if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"유효하지 않은 질문 유형: {invalid_types}. "
                    f"허용 유형: {sorted(valid_types)}"
                )
        
        return v
    
    @model_validator(mode='after')
    def set_defaults_and_validate(self):
        """기본값 설정 및 일치성 검증"""
        # 둘 다 비어있거나 0이면 기본값 설정
        if (not self.question_types or len(self.question_types) == 0) and self.qa_count == 0:
            self.question_types = ["개념", "응용"]
            self.qa_count = 2
        # question_types만 비어있으면 qa_count에 맞춰 기본 유형 설정
        elif not self.question_types or len(self.question_types) == 0:
            defaults = ["개념", "응용", "비교", "심화", "실습"]
            self.question_types = defaults[:self.qa_count]
        # qa_count가 0이면 question_types 개수로 설정
        elif self.qa_count == 0:
            self.qa_count = len(self.question_types)
        # 둘 다 유효하면 question_types 우선 (개수 맞춤)
        elif self.qa_count != len(self.question_types):
            # question_types 개수로 qa_count 조정
            self.qa_count = len(self.question_types)
        
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "lecture_id": "lecture_abc123",
                "section_id": 5,
                "section_summary": "C++ STL 벡터는 동적 배열로, push_back과 pop_back으로 요소를 관리합니다.",
                "subject": "CS",
                "language": "ko",
                "question_types": ["개념", "응용", "비교", "심화", "실습"],
                "qa_count": 3,
                "rag_context": {
                    "chunks": [
                        {
                            "text": "배열은 연속된 메모리 공간에 데이터를 저장합니다.",
                            "score": 0.92
                        }
                    ]
                },
                "previous_qa": [
                    {
                        "type": "개념",
                        "question": "배열이란 무엇인가요?",
                        "answer": "배열은 같은 타입의 데이터를 연속된 메모리에 저장하는 자료구조입니다."
                    }
                ]
            }
        }


class QAResponse(BaseModel):
    """QA 응답"""
    type: str = Field(..., description="질문 유형")
    question: str = Field(..., description="생성된 질문")
    answer: str = Field(..., description="생성된 답변")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "개념",
                "question": "C++ STL 벡터의 push_back과 pop_back은 어떤 역할을 하나요?",
                "answer": "push_back은 벡터의 끝에 새 요소를 추가하고, pop_back은 마지막 요소를 제거합니다."
            }
        }


class QACompleted(BaseModel):
    """QA 생성 완료 이벤트"""
    total: int = Field(..., description="총 생성된 QA 개수")
    duration_ms: int = Field(..., description="총 소요 시간 (밀리초)")


class QAError(BaseModel):
    """QA 생성 에러"""
    error: str = Field(..., description="에러 메시지")
    type: str = Field(..., description="실패한 질문 유형")
