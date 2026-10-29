from __future__ import annotations

import asyncio
import logging
from typing import List

from .api import YouTubeAPIClient
from .llm import YouTubeLLMClient
from .models import (
    YouTubeRequest,
    YouTubeResponse,
    YouTubeVideoInfo,
)
from .utils import normalize_title, deduplicate_items, heuristic_score
from .config import flags

logger = logging.getLogger(__name__)


class YouTubeService:
    """High-level service for lecture-aware YouTube recommendations."""

    def __init__(self, yt_client: YouTubeAPIClient | None = None, llm: YouTubeLLMClient | None = None):
        from .config.youtube_config import YouTubeConfig
        self.yt = yt_client or YouTubeAPIClient(api_key=YouTubeConfig.YOUTUBE_API_KEY)
        self.llm = llm or YouTubeLLMClient(api_key=YouTubeConfig.OPENAI_API_KEY)

    async def recommend_videos(self, request: YouTubeRequest) -> List[YouTubeResponse]:
        from .config.youtube_config import YouTubeConfig
        from .config import flags
        
        # 1) Build queries (LLM or stub)
        q_payload = await self.llm.generate_queries(
            {
                "lecture_summary": request.lecture_summary,
                "language": request.language,
                "yt_lang": request.yt_lang,
                "previous_summaries": [s.model_dump() for s in request.previous_summaries],
                "rag_context": [c.model_dump() for c in request.rag_context],
            }
        )
        queries = list(dict.fromkeys([q.strip() for q in q_payload.get("queries", []) if q.strip()]))
        
        # 🔧 Query 개수 제한 (QUERY_MAX)
        if len(queries) > flags.QUERY_MAX:
            logger.info(f"Query 개수 제한: {len(queries)}개 → {flags.QUERY_MAX}개")
            queries = queries[:flags.QUERY_MAX]
        
        if not queries:
            queries = [request.lecture_summary[:60]]

        # 2) Search videos (fan-out) then fetch details
        # 🚀 OPTIMIZATION: Search all queries in parallel
        async def search_single_query(q: str):
            """Search videos for a single query in parallel"""
            items = await self.yt.search_videos(
                q=q, 
                lang=request.yt_lang, 
                max_results=flags.MAX_SEARCH_RESULTS  # 🔧 flags에서 가져옴
            )
            return [(normalize_title(it.title), it) for it in items]
        
        # Execute all searches in parallel
        search_results = await asyncio.gather(*[search_single_query(q) for q in queries])
        
        # Flatten results from all queries
        search_items = []
        for items in search_results:
            search_items.extend(items)

        # Apply exclusion by title early
        excludes = set(normalize_title(t) for t in request.exclude_titles)
        search_items = [(k, v) for (k, v) in search_items if k not in excludes]

        # Deduplicate
        dedup = deduplicate_items((k, v) for (k, v) in search_items)
        if not dedup:
            return []

        ids = [it.video_id for it in dedup]
        details = await self.yt.get_videos(ids)
        detail_map = {d.video_id: d for d in details}
        best_scores: list[float] = []  # min_score 탈락 후보 점수 추적

        # 🚀 NO_SCORING 모드: 검증 없이 검색 결과만 반환
        if flags.NO_SCORING:
            logger.info("⚡ NO_SCORING 모드: 검증 스킵 (description 사용)")
            results = []
            for it in dedup[:request.top_k]:
                d = detail_map.get(it.video_id)
                if not d:
                    continue
                
                vi = YouTubeVideoInfo(
                    url=d.url(),
                    title=d.title,
                    extract=d.description or "No description available",
                    lang=request.yt_lang
                )
                results.append(YouTubeResponse(
                    lecture_id=request.lecture_id,
                    section_id=request.section_id,
                    video_info=vi,
                    reason="search",
                    score=10.0
                ))
            logger.info(f"✅ NO_SCORING 결과: {len(results)}개 반환")
            return results

        # 3) Build candidate list with summary + (optional) LLM score
        # 🚀 OPTIMIZATION: Process videos in parallel with Semaphore (동시성 제한)
        semaphore = asyncio.Semaphore(YouTubeConfig.VERIFY_CONCURRENCY)
        
        async def process_single_video(it):
            """Process one video (summary + optional LLM verification) in parallel"""
            async with semaphore:  # 🔧 동시성 제한
                def best_heuristic_score(title: str, view_count: int, publish_time: str) -> float:
                    """모든 검색어 중 최고 휴리스틱 점수 계산"""
                    candidate_queries = queries or [request.lecture_summary[:60]]
                    scores = [
                        heuristic_score(
                            title=title,
                            query=q,
                            view_count=view_count,
                            publish_time=publish_time,
                        )
                        for q in candidate_queries
                    ]
                    return max(scores) if scores else 0.0

                d = detail_map.get(it.video_id)
                if not d:
                    # Fall back to basic snippet if details missing
                    title = it.title
                    content = it.description
                    lang = request.yt_lang
                    url = f"https://www.youtube.com/watch?v={it.video_id}"
                    
                    # 🔧 자막 없이 요약 (제목/설명만)
                    sum_payload = await self.llm.summarize_content_no_transcript(
                        title=title, 
                        description=content, 
                        channel="Unknown",
                        language=request.language
                    )
                    extract = sum_payload.get("extract", content[:300])
                    
                    # Heuristic only
                    base = best_heuristic_score(title=title, view_count=0, publish_time=it.publish_time)
                    best_scores.append(base)
                    if base < request.min_score:
                        logger.info(f"🧊 YT 필터링(min_score): {base:.2f} < {request.min_score} (no detail, url=https://www.youtube.com/watch?v={it.video_id})")
                        return None
                    
                    vi = YouTubeVideoInfo(url=url, title=title, extract=extract, lang=lang)
                    return YouTubeResponse(
                        lecture_id=request.lecture_id,
                        section_id=request.section_id,
                        video_info=vi,
                        reason="Heuristic",
                        score=base,
                    )

                # 🔧 자막 사용 여부 결정
                if flags.USE_TRANSCRIPT:
                    transcript = await self.yt.fetch_transcript(d.video_id, preferred_langs=[request.yt_lang, "en", "ko"])  # type: ignore[arg-type]
                    content_src = transcript or (d.description or d.title)
                    # 자막이 있으면 정상 요약
                    sum_payload = await self.llm.summarize_content(
                        title=d.title, content=content_src, language=request.language
                    )
                else:
                    # 자막 없이 제목/설명만으로 요약
                    sum_payload = await self.llm.summarize_content_no_transcript(
                        title=d.title,
                        description=d.description or "",
                        channel=d.channel_title,
                        language=request.language
                    )
                
                extract = sum_payload.get("extract", (d.description or d.title)[:300])

                # 🔧 verify_yt 모드에 따라 점수 결정
                if request.verify_yt:
                    # ✅ verify_yt=True: LLM 점수만 사용
                    ver = await self.llm.score_video(
                        lecture_summary=request.lecture_summary, 
                        title=d.title, 
                        extract=extract, 
                        language=request.language
                    )
                    score = float(ver.get("score", 5.0) or 5.0)
                    reason = ver.get("reason", "LLM verification")
                else:
                    # ✅ verify_yt=False: Heuristic만 사용
                    score = best_heuristic_score(
                        title=d.title,
                        view_count=d.view_count,
                        publish_time=d.publish_time,
                    )
                    reason = "Heuristic"

                best_scores.append(score)
                if score < request.min_score:
                    logger.info(f"🧊 YT 필터링(min_score): {score:.2f} < {request.min_score} (title={d.title[:60]!r})")
                    return None

                vi = YouTubeVideoInfo(
                    url=d.url(),
                    title=d.title,
                    extract=extract,
                    lang=d.default_lang or request.yt_lang,
                )
                return YouTubeResponse(
                    lecture_id=request.lecture_id,
                    section_id=request.section_id,
                    video_info=vi,
                    reason=reason,
                    score=round(score, 2),
                )
        
        # 🚀 Process all videos in parallel with asyncio.gather
        candidate_results = await asyncio.gather(*[process_single_video(it) for it in dedup], return_exceptions=True)
        
        # 🔧 Filter out None and exceptions (with error logging)
        candidates: List[YouTubeResponse] = []
        for idx, result in enumerate(candidate_results):
            if isinstance(result, Exception):
                logger.warning(
                    f"영상 처리 실패 (idx={idx}, video_id={dedup[idx].video_id if idx < len(dedup) else 'unknown'}): {result}",
                    exc_info=result
                )
            elif result is not None:
                candidates.append(result)

        # 4) Sort and cap by effective top_k
        candidates.sort(key=lambda r: r.score, reverse=True)
        final = candidates[: request.effective_top_k()]

        if not final:
            best = max(best_scores) if best_scores else None
            logger.info(f"🧊 YT 결과 없음: min_score={request.min_score}, best_score={best}")

        return final
