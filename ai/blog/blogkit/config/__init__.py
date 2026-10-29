"""
Config 패키지 초기화
"""
from .flags import (
    NO_SCORING,
    VERIFY_GOOGLE_DEFAULT,
    KEYWORD_MIN,
    KEYWORD_MAX,
    WEIGHT_TITLE_MATCH,
    WEIGHT_SNIPPET_MATCH,
    WEIGHT_DOMAIN_TRUST,
    TRUSTED_DOMAINS,
)
from .google_config import GoogleConfig
from . import prompts

__all__ = [
    "NO_SCORING",
    "VERIFY_GOOGLE_DEFAULT",
    "KEYWORD_MIN",
    "KEYWORD_MAX",
    "WEIGHT_TITLE_MATCH",
    "WEIGHT_SNIPPET_MATCH",
    "WEIGHT_DOMAIN_TRUST",
    "TRUSTED_DOMAINS",
    "GoogleConfig",
    "prompts",
]
