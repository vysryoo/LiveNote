"""
Google 검색을 위한 OpenAI LLM 클라이언트
"""
import asyncio
import json
import logging
from typing import List, Dict, Any

from core.llm import ModelPurpose, complete

from ..config.google_config import GoogleConfig
from ..config import prompts
from ..config import flags

logger = logging.getLogger(__name__)


class GoogleLLMClient:
    """Google 검색을 위한 LLM 클라이언트"""
    
    def __init__(self, api_key: str = None):
        """
        초기화
        
        Args:
            api_key: OpenAI API 키 (None이면 환경 변수 사용)
        """
        api_key = api_key or GoogleConfig.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
    
    async def generate_keywords(
        self,
        lecture_summary: str,
        language: str,
        previous_summaries: List[Dict] = None,
        rag_context: List[Dict] = None
    ) -> List[str]:
        """
        강의 요약 → 검색 키워드 생성
        
        Args:
            lecture_summary: 강의 요약
            language: 키워드 생성 언어 (search_lang)
            previous_summaries: 이전 섹션 요약 (선택)
            rag_context: RAG 컨텍스트 (선택)
            
        Returns:
            검색 키워드 리스트
        """
        # 컨텍스트 구성
        context = ""
        if previous_summaries or rag_context:
            prev_text = ""
            if previous_summaries:
                prev_text = "\n".join([
                    f"Section {s['section_id']}: {s['summary']}"
                    for s in previous_summaries[:3]  # 최근 3개만
                ])
            
            rag_text = ""
            if rag_context:
                rag_text = "\n".join([
                    chunk['text'][:200]
                    for chunk in rag_context[:3]  # 최대 3개
                ])
            
            context = prompts.KEYWORD_CONTEXT_TEMPLATE.format(
                previous_summaries=prev_text or "None",
                rag_context=rag_text or "None"
            )
        
        # 프롬프트 생성
        prompt = prompts.KEYWORD_GENERATION_PROMPT.format(
            keyword_min=flags.KEYWORD_MIN,
            keyword_max=flags.KEYWORD_MAX,
            language=language,
            lecture_summary=lecture_summary,
            context=context
        )
        
        try:
            content = await complete(
                ModelPurpose.QUERY, [("user", prompt)], max_tokens=GoogleConfig.MAX_TOKENS_QUERY
            )
            
            # 키워드 파싱 (줄바꿈 기준)
            keywords = [
                line.strip()
                for line in content.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            
            logger.info(f"🤖 LLM 키워드 생성: {keywords}")
            
            return keywords[:GoogleConfig.FANOUT]  # 최대 FANOUT 개수만 반환
        
        except Exception as e:
            logger.error(f"❌ LLM 키워드 생성 실패: {e}")
            # 폴백: 강의 요약의 주요 단어 추출
            fallback = lecture_summary.split()[:3]
            logger.warning(f"⚠️  폴백 키워드 사용: {fallback}")
            return fallback
    
    async def score_result(
        self,
        lecture_summary: str,
        title: str,
        snippet: str,
        url: str,
        language: str
    ) -> Dict[str, Any]:
        """
        검색 결과 LLM 검증
        
        Args:
            lecture_summary: 강의 요약
            title: 검색 결과 제목
            snippet: 검색 결과 스니펫
            url: 검색 결과 URL
            language: 응답 언어
            
        Returns:
            {"score": 8.5, "reason": "..."}
        """
        prompt = prompts.SCORING_PROMPT.format(
            lecture_summary=lecture_summary,
            title=title,
            snippet=snippet,
            url=url,
            language=language
        )
        
        try:
            content = await complete(
                ModelPurpose.VERIFY, [("user", prompt)], max_tokens=GoogleConfig.MAX_TOKENS_SCORE, json_mode=True
            )
            
            # JSON 파싱 시도
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON 파싱 실패, 내용: {content[:200]}")
                # 간단한 정규식으로 score와 reason 추출 시도
                import re
                score_match = re.search(r'"score"\s*:\s*([0-9.]+)', content)
                reason_match = re.search(r'"reason"\s*:\s*"([^"]*)"', content)
                
                if score_match and reason_match:
                    return {
                        "score": float(score_match.group(1)),
                        "reason": reason_match.group(1)
                    }
                raise e
            
            return {
                "score": float(result.get("score", 0.0)),
                "reason": result.get("reason", "")
            }
        
        except Exception as e:
            logger.error(f"❌ LLM 검증 실패: {e}")
            return {"score": 0.0, "reason": "검증 실패"}
