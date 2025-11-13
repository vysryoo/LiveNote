"""
QA 생성 서비스 (병렬 처리)
"""

import asyncio
from typing import AsyncGenerator, List, Optional, Tuple

from .models import QARequest, QAResponse
from .config.prompts import PromptTemplates
from .llm.openai_client import OpenAIClient


class QAService:
    """QA 생성 서비스"""
    
    def __init__(self, api_key: str = None, model: Optional[str] = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경변수에서 로드)
        """
        self.client = OpenAIClient(api_key=api_key, model=model)
        self.prompts = PromptTemplates()
    
    async def generate_questions(
        self,
        request: QARequest
    ) -> List[QAResponse]:
        """
        병렬로 질문 생성하고 완료된 것들을 리스트로 반환
        
        Args:
            request: QA 요청
        
        Returns:
            List[QAResponse]: 생성된 QA 리스트
        """
        qa_list: List[QAResponse] = []
        async for event_type, q_type, payload in self.stream_questions(request):
            if event_type == "qa":
                qa_list.append(QAResponse(**payload))
        return qa_list
    
    async def stream_questions(
        self,
        request: QARequest
    ) -> AsyncGenerator[Tuple[str, str, dict], None]:
        """
        질문을 완료되는 순서대로 스트리밍
        
        Args:
            request: QA 요청
        
        Yields:
            Tuple[str, str, dict]: (이벤트 타입, 질문 유형, 페이로드)
        """
        # RAG context와 이전 QA context 분리
        rag_context = self.prompts.build_rag_context(request.rag_context)
        context_qp = self.prompts.build_context_qp(request.previous_qa)
        
        # 각 질문 유형별 태스크 생성
        task_map: dict[asyncio.Task, str] = {}
        for q_type in request.question_types[:request.qa_count]:
            coroutine = self._generate_one_question(
                section_summary=request.section_summary,
                question_type=q_type,
                rag_context=rag_context,
                context_qp=context_qp
            )
            task = asyncio.create_task(coroutine)
            task_map[task] = q_type
        
        if not task_map:
            return

        pending = set(task_map.keys())
        while pending:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for finished in done:
                q_type = task_map.get(finished, "unknown")
                try:
                    result = finished.result()
                except Exception as exc:
                    print(f"⚠️  QA 생성 중 오류: {exc}")
                    yield ("error", q_type, {"error": str(exc)})
                    continue

                if result:
                    yield ("qa", q_type, result)
    
    async def _generate_one_question(
        self,
        section_summary: str,
        question_type: str,
        rag_context: str,
        context_qp: str
    ) -> dict:
        """
        단일 질문 생성
        
        Args:
            section_summary: 섹션 요약
            question_type: 질문 유형
            rag_context: RAG 컨텍스트 (참고용)
            context_qp: 이전 QA (중복 방지용)
        
        Returns:
            {"type": "개념", "question": "...", "answer": "..."}
        """
        # 프롬프트 구성
        prompt_template = self.prompts.get_prompt(question_type)
        prompt = prompt_template.format(
            section_summary=section_summary,
            rag_context=rag_context,
            context_qp=context_qp
        )
        
        # OpenAI API 호출
        qa_data = await self.client.generate_qa(prompt, question_type)
        
        return qa_data or {
            "type": question_type,
            "question": f"[생성 실패] {question_type} 질문",
            "answer": "API 오류로 생성에 실패했습니다."
        }
