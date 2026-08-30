"""
OpenAI LLM client
"""
import json
import logging
import re
from textwrap import shorten
from typing import List, Dict, Sequence, Optional
from openai import AsyncOpenAI

from ..config import WikiConfig, prompts

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API 클라이언트"""
    
    def __init__(self):
        self.config = WikiConfig()
        self.config.validate()
        self.client = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY)
    
    async def generate_keywords(
        self, 
        lecture_summary: str,
        language: str = "en",
        search_language: str = "en",
        previous_summaries: Optional[Sequence] = None,
        rag_context: Optional[Sequence] = None
    ) -> List[str]:
        """
        강의 요약 → Wikipedia 검색 키워드 생성
        
        Args:
            lecture_summary: 강의 섹션 요약
            language: 언어 (en/ko)
            
        Returns:
            키워드 리스트 ["keyword1", "keyword2", ...]
        """
        try:
            def build_prev_text(items: Optional[Sequence]) -> str:
                if not items:
                    return "None"
                lines = []
                for item in list(items)[-2:]:
                    section_id = getattr(item, "section_id", None)
                    summary = getattr(item, "summary", None) or str(item)
                    prefix = f"[{section_id}] " if section_id is not None else ""
                    lines.append(prefix + shorten(str(summary), width=120, placeholder="…"))
                return "\n".join(lines) if lines else "None"
            
            def build_rag_text(items: Optional[Sequence]) -> str:
                if not items:
                    return "None"
                lines = []
                for item in list(items)[:2]:
                    text = getattr(item, "text", None) or getattr(item, "content", "")
                    if not text:
                        continue
                    snippet = shorten(str(text), width=120, placeholder="…")
                    score = getattr(item, "score", None)
                    if score is not None:
                        lines.append(f"{snippet} (score≈{score:.2f})")
                    else:
                        lines.append(snippet)
                return "\n".join(lines) if lines else "None"
            
            prompt = prompts.KEYWORD_GENERATION_PROMPT.format(
                lecture_summary=lecture_summary,
                language=language,
                search_language=search_language,
                previous_summaries=build_prev_text(previous_summaries),
                rag_context=build_rag_text(rag_context)
            )
            
            response = await self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.MAX_TOKENS_QUERY,
                temperature=self.config.LLM_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            keywords = result.get("keywords", [])
            
            logger.info(f"📚 키워드 생성 (search={search_language}, output={language}): {keywords}")
            return keywords
            
        except Exception as e:
            logger.error(f"❌ 키워드 생성 실패: {e}")
            # Fallback: 첫 단어 추출
            words = lecture_summary.split()[:3]
            return words
    
    async def score_page(
        self, 
        lecture_summary: str,
        title: str,
        extract: str,
        language: str = "ko"
    ) -> Dict:
        """
        문서 관련도 평가
        
        Args:
            lecture_summary: 강의 요약
            title: 문서 제목
            extract: 문서 요약
            
        Returns:
            {"score": 9.5, "reason": "..."}
        """
        try:
            # 텍스트 정제
            extract_clean = extract[:300].replace("\n", " ").replace('"', "'").strip()
            
            prompt = prompts.SCORE_PAGE_PROMPT.format(
                lecture_summary=lecture_summary,
                title=title,
                extract=extract_clean,
                language=language
            )
            
            response = await self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.MAX_TOKENS_SCORE,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            raw_response = response.choices[0].message.content
            result = self._safe_parse_json(raw_response)
            
            return {
                "score": float(result.get("score", 5.0)),
                "reason": result.get("reason", "LLM evaluation")
            }
            
        except Exception as e:
            logger.error(f"❌ LLM 스코어링 실패: {e}")
            return {"score": 5.0, "reason": "Scoring failed"}
    
    def _safe_parse_json(self, text: str) -> Dict:
        """안전한 JSON 파싱"""
        try:
            # 코드펜스 제거
            text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
            text = text.replace("\n", " ").replace("\r", " ").strip()
            
            return json.loads(text)
            
        except json.JSONDecodeError:
            # 정규식 fallback
            score_match = re.search(r'"?score"?\s*:\s*(\d+(?:\.\d+)?)', text)
            reason_match = re.search(r'"?reason"?\s*:\s*"([^"]*)"', text)
            
            return {
                "score": float(score_match.group(1)) if score_match else 5.0,
                "reason": reason_match.group(1) if reason_match else "Parsing failed"
            }
