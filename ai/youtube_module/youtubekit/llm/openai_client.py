"""
YouTube LLM 클라이언트 (OpenAI)
"""
from __future__ import annotations

import json
from typing import Any, Dict

from ..config.youtube_config import YouTubeConfig
from ..config import flags
from ..config import (
    QUERY_GENERATION_PROMPT,
    SUMMARY_PROMPT,
    SUMMARY_NO_TRANSCRIPT_PROMPT,
    SCORE_VIDEO_PROMPT,
)


class YouTubeLLMClient:
    """YouTube 추천을 위한 LLM 클라이언트"""
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or YouTubeConfig.OPENAI_API_KEY
        self.client = None
        
        if not YouTubeConfig.OFFLINE_MODE and self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
            except Exception:
                # OpenAI SDK 없으면 stub 모드
                self.client = None

    async def _chat_json(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """LLM JSON 응답 요청"""
        if YouTubeConfig.OFFLINE_MODE or not self.client:
            # Offline/테스트 모드: 기본 stub 반환
            try:
                return json.loads(prompt)
            except Exception:
                return {"stub": True}

        resp = await self.client.chat.completions.create(
            model=YouTubeConfig.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=YouTubeConfig.LLM_TEMPERATURE,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        return json.loads(content)

    async def generate_queries(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """검색 쿼리 생성"""
        if YouTubeConfig.OFFLINE_MODE:
            # Stub: 요약에서 간단히 추출
            summary = request_data.get("lecture_summary", "topic")
            return {
                "queries": [summary[:40], f"explained {summary[:30]} examples"],
                "rationale": "Derived from lecture summary (stub).",
            }

        prompt = QUERY_GENERATION_PROMPT.format(
            query_min=flags.QUERY_MIN,
            query_max=flags.QUERY_MAX,
            lecture_summary=request_data.get("lecture_summary", ""),
            language=request_data.get("language", "ko"),
            yt_lang=request_data.get("yt_lang", "en"),
            previous_summaries=request_data.get("previous_summaries", []),
            rag_context=request_data.get("rag_context", []),
        )
        return await self._chat_json(prompt, YouTubeConfig.MAX_TOKENS_QUERY)

    async def summarize_content(
        self, *, title: str, content: str, language: str
    ) -> Dict[str, Any]:
        """영상 내용 요약 (3문장)"""
        if YouTubeConfig.OFFLINE_MODE:
            text = content.strip().replace("\n", " ")
            if not text:
                text = title
            # 간단한 3문장 추출
            sent = text.split(". ")
            extract = ". ".join(sent[:3])[:400]
            return {"extract": extract or title}

        # 콘텐츠 길이 제한 (토큰 절약)
        truncated_content = content[:YouTubeConfig.MAX_CONTENT_LENGTH]
        if len(content) > YouTubeConfig.MAX_CONTENT_LENGTH:
            truncated_content += "..."
        
        prompt = SUMMARY_PROMPT.format(
            title=title, content=truncated_content, language=language
        )
        return await self._chat_json(prompt, YouTubeConfig.MAX_TOKENS_SUMMARY)

    async def summarize_content_no_transcript(
        self, *, title: str, description: str, channel: str, language: str
    ) -> Dict[str, Any]:
        """자막 없이 제목/설명만으로 요약 (2문장)"""
        if YouTubeConfig.OFFLINE_MODE:
            text = (description or title).strip().replace("\n", " ")
            sent = text.split(". ")
            extract = ". ".join(sent[:2])[:300]
            return {"extract": extract or title}

        # 설명 길이 제한
        truncated_desc = description[:500]
        if len(description) > 500:
            truncated_desc += "..."
        
        prompt = SUMMARY_NO_TRANSCRIPT_PROMPT.format(
            title=title, 
            description=truncated_desc, 
            channel=channel,
            language=language
        )
        return await self._chat_json(prompt, YouTubeConfig.MAX_TOKENS_SUMMARY)

    async def score_video(
        self, *, lecture_summary: str, title: str, extract: str, language: str
    ) -> Dict[str, Any]:
        """영상 관련도 점수 계산 (LLM)"""
        if YouTubeConfig.OFFLINE_MODE:
            # Stub: 간단한 heuristic
            base = 7.0 if title and extract and lecture_summary else 5.0
            reason = "Aligned with key terms (stub)."
            return {"score": base, "reason": reason}

        prompt = SCORE_VIDEO_PROMPT.format(
            lecture_summary=lecture_summary,
            title=title,
            extract=extract,
            language=language,
        )
        return await self._chat_json(prompt, YouTubeConfig.MAX_TOKENS_SCORE)
