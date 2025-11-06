"""
OpenAI API 클라이언트 (LLM)
"""
import json
import logging
from typing import Dict, Any
import httpx
from openai import AsyncOpenAI

from ..config.openalex_config import OpenAlexConfig
from ..config import prompts

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API 클라이언트 (쿼리 생성 + 논문 검증)"""
    
    def __init__(self):
        # HTTP 클라이언트 설정
        http_client = httpx.AsyncClient(
            http2=True,
            timeout=15.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
        )
        
        self.client = AsyncOpenAI(
            api_key=OpenAlexConfig.OPENAI_API_KEY,
            http_client=http_client
        )
    
    async def generate_query(self, request_data: Dict) -> Dict[str, Any]:
        """
        섹션 요약 → OpenAlex 검색 쿼리 생성 (LLM)
        
        Args:
            request_data: {
                "section_summary": str,
                "previous_summaries": List[PreviousSectionSummary],
                "rag_context": List[RAGChunk]
            }
            
        Returns:
            {"tokens": ["term1", "term2", ...]}
        """
        try:
            # 컨텍스트 준비
            section_summary = request_data.get("section_summary", "")
            previous_summaries = request_data.get("previous_summaries", [])
            rag_context = request_data.get("rag_context", [])
            
            # Previous summaries 텍스트화
            prev_text = ""
            if previous_summaries:
                prev_items = [
                    f"섹션 {ps.section_id}: {ps.summary}" 
                    for ps in previous_summaries
                ]
                prev_text = "\n".join(prev_items)
            else:
                prev_text = "(없음)"
            
            # RAG context 텍스트화
            rag_text = ""
            if rag_context:
                rag_items = [
                    f"[{rc.score:.2f}] {rc.text[:100]}..." 
                    for rc in rag_context[:3]  # 상위 3개만
                ]
                rag_text = "\n".join(rag_items)
            else:
                rag_text = "(없음)"
            
            # 프롬프트 생성
            prompt = prompts.QUERY_GENERATION_PROMPT.format(
                section_summary=section_summary,
                previous_summaries=prev_text,
                rag_context=rag_text
            )
            
            logger.info("🤖 LLM 쿼리 생성 시작...")
            
            # OpenAI API 호출
            response = await self.client.chat.completions.create(
                model=OpenAlexConfig.LLM_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=OpenAlexConfig.LLM_TEMPERATURE,
                max_tokens=OpenAlexConfig.MAX_TOKENS_QUERY
            )
            
            # 응답 파싱
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱 (코드 블록 제거)
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            tokens = result.get("tokens", [])
            
            logger.info(f"✅ LLM 쿼리 생성 완료: {tokens}")
            
            return {"tokens": tokens}
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {e}, content: {content}")
            # Fallback: 섹션 요약에서 단어 추출
            words = section_summary.split()[:3]
            return {"tokens": words}
        except Exception as e:
            logger.error(f"❌ LLM 쿼리 생성 실패: {e}")
            return {"tokens": []}
    
    async def score_paper(
        self, 
        paper: Dict, 
        section_summary: str,
        keywords: str
    ) -> Dict[str, Any]:
        """
        단일 논문 검증 (LLM)
        
        Args:
            paper: 논문 정보 (title, abstract, year, cited_by_count)
            section_summary: 현재 섹션 요약
            keywords: 검색 키워드
            
        Returns:
            {"score": float, "reason": str}
        """
        try:
            # 텍스트 정제 (JSON 깨짐 방지)
            title = paper.get("title", "").replace("\n", " ").replace('"', "'").strip()
            abstract = paper.get("abstract", "").replace("\n", " ").replace('"', "'").strip()
            section_clean = section_summary.replace("\n", " ").replace('"', "'").strip()
            
            # 프롬프트 생성
            prompt = prompts.SCORE_PAPER_PROMPT.format(
                section_summary=section_clean,
                keywords=keywords,
                title=title,
                abstract=abstract[:OpenAlexConfig.ABSTRACT_MAX_LENGTH],
                year=paper.get("year", "N/A"),
                cited_by_count=paper.get("cited_by_count", 0)
            )
            
            # OpenAI API 호출
            response = await self.client.chat.completions.create(
                model=OpenAlexConfig.LLM_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=OpenAlexConfig.LLM_TEMPERATURE,
                max_tokens=OpenAlexConfig.MAX_TOKENS_SCORE
            )
            
            # 응답 파싱
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱 (코드 블록 제거)
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            result = json.loads(content)
            score = float(result.get("score", 5.0))
            reason = result.get("reason", "검증 완료")
            
            return {"score": score, "reason": reason}
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 실패: {e}, content: {content}")
            return {"score": 5.0, "reason": "검증 실패 (JSON 파싱 오류)"}
        except Exception as e:
            logger.error(f"❌ LLM 논문 검증 실패: {e}")
            return {"score": 5.0, "reason": "검증 실패 (API 오류)"}
