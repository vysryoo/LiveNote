"""
OpenAlex Provider 전용 플래그
"""

# ━━━ 검증 스위치 ━━━
NO_SCORING = False  # True이면 검증 없이 검색 결과만 반환 (빠른 테스트용)
VERIFY_OPENALEX_DEFAULT = True  # 기본값: LLM 검증

# ━━━ 토큰 생성 설정 ━━━
TOKEN_MIN = 2  # 최소 검색 토큰 개수
TOKEN_MAX = 4  # 최대 검색 토큰 개수
