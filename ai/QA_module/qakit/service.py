"""
QA 생성 서비스 (병렬 처리)
"""

import asyncio
from typing import List

from .models import QARequest, QAResponse
from .config.prompts import PromptTemplates
from .llm.openai_client import OpenAIClient


class QAService:
    """QA 생성 서비스"""
    
    def __init__(self, api_key: str = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경변수에서 로드)
        """
        self.client = OpenAIClient(api_key=api_key)
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
        # RAG context와 이전 QA context 분리
        rag_context = self.prompts.build_rag_context(request.rag_context)
        context_qp = self.prompts.build_context_qp(request.previous_qa)
        
        # 각 질문 유형별 태스크 생성
        tasks = []
        for i, q_type in enumerate(request.question_types[:request.qa_count]):
            task = self._generate_one_question(
                section_summary=request.section_summary,
                question_type=q_type,
                rag_context=rag_context,
                context_qp=context_qp
            )
            tasks.append(task)
        
        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 성공한 것만 필터링
        qa_list = []
        for result in results:
            if isinstance(result, Exception):
                print(f"⚠️  QA 생성 중 오류: {result}")
                continue
            if result:
                qa_list.append(QAResponse(**result))
        
        return qa_list
    
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
