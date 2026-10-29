"""
YouTube 설정 모듈
"""
from . import flags
from .youtube_config import YouTubeConfig
from .prompts import (
    QUERY_GENERATION_PROMPT,
    SUMMARY_PROMPT,
    SUMMARY_NO_TRANSCRIPT_PROMPT,
    SCORE_VIDEO_PROMPT,
)

__all__ = [
    "flags",
    "YouTubeConfig",
    "QUERY_GENERATION_PROMPT",
    "SUMMARY_PROMPT",
    "SUMMARY_NO_TRANSCRIPT_PROMPT",
    "SCORE_VIDEO_PROMPT",
]

