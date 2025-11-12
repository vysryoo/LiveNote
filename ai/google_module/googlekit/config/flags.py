"""
Google Provider 전용 플래그
"""

# ━━━ 검증 스위치 ━━━
NO_SCORING = False  # True이면 검증 없이 검색 결과만 반환 (빠른 테스트용)
VERIFY_GOOGLE_DEFAULT = True  # 기본값: LLM 검증

# ━━━ 키워드 생성 설정 ━━━
KEYWORD_MIN = 2  # 최소 키워드 개수
KEYWORD_MAX = 4  # 최대 키워드 개수

# ━━━ 신뢰도 가중치 ━━━
WEIGHT_TITLE_MATCH = 0.4
WEIGHT_SNIPPET_MATCH = 0.3
WEIGHT_DOMAIN_TRUST = 0.3

# ━━━ 신뢰 도메인 리스트 ━━━
TRUSTED_DOMAINS = [
    ".edu",
    ".gov",
    "arxiv.org",
    "scholar.google.com",
    "stackoverflow.com",
    "github.com",
    "microsoft.com",
    "mozilla.org",
]
