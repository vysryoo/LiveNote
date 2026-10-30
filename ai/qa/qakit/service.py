"""
QA 생성 서비스 (병렬 처리)
"""

from typing import AsyncGenerator, List, Tuple

from .models import QARequest, QAResponse
from .config.prompts import PromptTemplates
from .graph import build_qa_graph
from .llm.openai_client import OpenAIClient


class QAService:
    """QA 생성 서비스"""
    
    def __init__(self):
        """초기화한다. 모델은 공통 LLM 계층의 QA 용도 설정을 따른다."""
        self.client = OpenAIClient()
        self.prompts = PromptTemplates()
        self.graph = build_qa_graph(self.client)
    
    async def generate_questions(
        self,
        request: QARequest
    ) -> List[QAResponse]:
        """
        병렬로 질문 생성하고 완료된 것들을 리스트로 반환 (실패한 유형은 제외)
        
        Args:
            request: QA 요청
        
        Returns:
            List[QAResponse]: 생성된 QA 리스트
        """
        qa_list: List[QAResponse] = []
        async for event_type, q_type, payload in self.stream_questions(request):
            if event_type == "qa":
                qa_list.append(QAResponse(
                    type=payload["type"],
                    question=payload["question"],
                    answer=payload["answer"],
                ))
        return qa_list
    
    async def stream_questions(
        self,
        request: QARequest
    ) -> AsyncGenerator[Tuple[str, str, dict], None]:
        """
        질문 유형별로 동시에 생성하며 생성 과정을 이벤트로 스트리밍

        이벤트 종류 (payload의 item은 질문 유형 순서, 0부터):
        - start: 생성 시작 {"item"}
        - question: 질문 완성 {"item", "text"}
        - answer: 답변 조각 {"item", "text"}
        - qa: 생성 완료 {"item", "type", "question", "answer"}
        - error: 생성 실패 {"item", "error"}. 이 항목의 qa 이벤트는 오지 않음

        Args:
            request: QA 요청

        Yields:
            Tuple[str, str, dict]: (이벤트 타입, 질문 유형, 페이로드)
        """
        # RAG context와 이전 QA context 분리
        rag_context = self.prompts.build_rag_context(request.rag_context)
        context_qp = self.prompts.build_context_qp(request.previous_qa)
        subject_context = self.prompts.build_subject_context(request.subject)
        language_instruction = self.prompts.build_language_instruction(request.language)

        question_types = request.question_types[:request.qa_count]
        if not question_types:
            return

        items = [
            (q_type, self.prompts.get_prompt(q_type).format(
                section_summary=request.section_summary,
                rag_context=rag_context,
                context_qp=context_qp,
                scope_rule=self.prompts.SCOPE_RULE,
                subject_context=subject_context,
                language_instruction=language_instruction
            ))
            for q_type in question_types
        ]
        # 받는 쪽이 중간에 끊으면 그래프 실행이 취소되어 남은 생성도 멈춤
        async for event in self.graph.astream({"items": items}, stream_mode="custom"):
            yield event
