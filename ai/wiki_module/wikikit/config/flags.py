"""
Wikipedia Provider flags
"""

# ━━━ 검증 스위치 ━━━
NO_SCORING = False  # True이면 검증 없이 검색 결과만 반환
VERIFY_WIKI_DEFAULT = True  # 기본값: 검증 활성화

# ━━━ 키워드 생성 설정 ━━━
KEYWORD_MIN = 2  # 최소 키워드 개수
KEYWORD_MAX = 3  # 최대 키워드 개수 (간소화)

# ━━━ Fallback 설정 ━━━
FALLBACK_TO_KO_DEFAULT = True  # 기본값: 한국어 보충
