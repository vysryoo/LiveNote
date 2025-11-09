"""
YouTube Provider 전용 플래그
"""

# ━━━ 검증 스위치 ━━━
NO_SCORING = False  # True이면 검증 없이 검색 결과만 반환 (빠른 테스트용)
VERIFY_YT_DEFAULT = False  # 기본값: Heuristic (False), LLM (True)
USE_TRANSCRIPT = False    # 자막 사용 여부 (False: 제목/설명만 사용)

# ━━━ 쿼리 생성 설정 ━━━
QUERY_MIN = 1  # 최소 검색 쿼리 개수
QUERY_MAX = 2  # 최대 검색 쿼리 개수

# ━━━ 검색 결과 설정 ━━━
MAX_SEARCH_RESULTS = 8  # YouTube API 검색 시 최대 결과 수. 8

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 휴리스틱 필터 가중치 (합계 = 1.0)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WEIGHT_TITLE_MATCH = 0.5  # 제목 유사도
WEIGHT_VIEWS = 0.3         # 조회수
WEIGHT_RECENCY = 0.2       # 최신성
