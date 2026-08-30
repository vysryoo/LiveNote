"""
OpenAI API 클라이언트
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any

from openai import AsyncOpenAI, APIError, APITimeoutError

from ..config.qa_config import QAConfig


class OpenAIClient:
    """OpenAI API 비동기 클라이언트"""
    
    def __init__(self, api_key: str = None, model: Optional[str] = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경변수에서 로드)
        """
        # API 키 우선순위: 파라미터 > 환경변수 > config
        final_api_key = api_key or os.getenv("OPENAI_API_KEY") or QAConfig.OPENAI_API_KEY
        self.client = AsyncOpenAI(
            api_key=final_api_key,
            timeout=QAConfig.OPENAI_TIMEOUT
        )
        self.model = model or QAConfig.QA_MODEL
        self.max_tokens = QAConfig.QA_MAX_TOKENS
        self.temperature = QAConfig.QA_TEMPERATURE
    
    async def generate_qa(
        self,
        prompt: str,
        question_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        단일 QA 생성
        
        Args:
            prompt: 프롬프트 텍스트
            question_type: 질문 유형
        
        Returns:
            {"type": "개념", "q": "질문", "a": "답변"} 또는 None (실패 시)
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 교육 전문가입니다. 학습에 도움되는 질문과 답변을 JSON 형식으로 생성합니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 코드 블록 제거 (```json ... ```)
            if content.startswith("```"):
                # 첫 줄과 마지막 줄 제거
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
            
            # JSON 파싱
            try:
                qa_data = json.loads(content)
                
                # 필드명 통일 (q/a → question/answer)
                return {
                    "type": qa_data.get("type", question_type),
                    "question": qa_data.get("q", ""),
                    "answer": qa_data.get("a", "")
                }
            except json.JSONDecodeError as je:
                print(f"⚠️ JSON 파싱 실패: {je}")
                # JSON 파싱 실패 시 텍스트에서 추출 시도
                return self._parse_text_response(content, question_type)
        
        except APITimeoutError as te:
            print(f"⚠️ OpenAI API timeout: {question_type} - {te}")
            return None
        except APIError as e:
            print(f"⚠️ OpenAI API error: {question_type} - {e}")
            return None
        except Exception as e:
            print(f"⚠️ Unexpected error in [{question_type}]: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_text_response(self, text: str, question_type: str) -> Optional[Dict[str, Any]]:
        """
        JSON 파싱 실패 시 텍스트에서 QA 추출
        
        Args:
            text: 응답 텍스트
            question_type: 질문 유형
        
        Returns:
            QA 딕셔너리 또는 None
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        question = None
        answer = None
        
        for line in lines:
            if line.startswith(("질문:", "Q:", "q:")):
                question = line.split(":", 1)[1].strip()
            elif line.startswith(("답변:", "A:", "a:")):
                answer = line.split(":", 1)[1].strip()
        
        if question and answer:
            return {
                "type": question_type,
                "question": question,
                "answer": answer
            }
        
        return None
