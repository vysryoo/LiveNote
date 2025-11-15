# REC YouTube 동작 과정

## 📚 개요

**YouTube 영상 추천 시스템**의 전체 동작 과정을 설명합니다.

**핵심 특징:**
- LLM 기반 검색 쿼리 생성 (QUERY_MAX=3개 제한)
- YouTube Data API v3를 통한 영상 검색
- 병렬 검색 (여러 쿼리 동시 실행)
- Transcript 추출 (youtube-transcript-api)
- LLM 검증 (Semaphore 동시성 제어, 최대 20개)
- Heuristic 스코어링 (빠른 평가)
- NO_SCORING 모드 지원

---

## 🔄 전체 흐름도

```
┌──────────────────────────────────────────────────────────────────┐
│                    YouTube 영상 추천 시스템                       │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  1. 검색 쿼리 생성 (LLM)                │
        │     - 강의 요약 분석                    │
        │     - 이전 강의 컨텍스트                │
        │     - RAG 컨텍스트                      │
        │     → 최대 3개 쿼리 생성               │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  2. YouTube API 병렬 검색               │
        │     - 각 쿼리별 영상 검색 (병렬)        │
        │     - 중복 제거 (제목 정규화)           │
        │     - exclude_titles 필터링             │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  3. 영상 상세 정보 가져오기             │
        │     - Video ID로 Details 조회          │
        │     - Transcript 추출 (자막)           │
        │     - 언어 필터링                       │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  4. 조건부 검증                         │
        │     ┌────────────┬────────────────┐    │
        │     │ verify=True│  verify=False  │    │
        │     ├────────────┼────────────────┤    │
        │     │ LLM 병렬   │  Heuristic     │    │
        │     │ 검증       │  스코어링      │    │
        │     └────────────┴────────────────┘    │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  5. 점수 필터링 + 정렬                  │
        │     - min_score 이상만 선택             │
        │     - 점수 내림차순 정렬                │
        │     → top_k개 반환                      │
        └────────────────────────────────────────┘
```

---

## ⚙️ 주요 설정

### **server/config.py**
```python
class YouTubeSettings(BaseModel):
    top_k: int = Field(default=3)           # 반환할 영상 수
    verify: bool = Field(default=True)      # LLM 검증 ON/OFF
    min_score: float = Field(default=0.0)   # 최소 점수
    yt_lang: str = Field(default="ko")      # 영상 언어
```

### **cap1_youtube_module/youtubekit/config/youtube_config.py**
```python
class YouTubeConfig:
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2
    
    VERIFY_CONCURRENCY: int = 20  # 병렬 검증 동시성
    
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
```

### **cap1_youtube_module/youtubekit/config/flags.py**
```python
NO_SCORING = False           # True: 검증 스킵
QUERY_MAX = 3                # 최대 쿼리 수
MAX_SEARCH_RESULTS = 10      # 쿼리당 최대 검색 결과
```

---

## 🔍 검색 결과 없음 FAQ

### Q1: "YouTube 영상이 검색되지 않아요"

**가능한 원인:**
1. **쿼리 생성 실패**: LLM이 적절한 검색어 생성 실패
2. **언어 필터**: `yt_lang` 설정과 영상 언어 불일치
3. **Transcript 없음**: 자막이 없는 영상 제외됨
4. **exclude_titles**: 이미 추천된 영상들이 제외됨

**해결 방법:**
- `yt_lang="en"` (영어 영상 검색)
- `QUERY_MAX=5` (쿼리 수 증가)
- 로그 확인: 쿼리가 적절한지 확인

---

## 📝 요약

**YouTube 영상 추천 시스템**은 5단계로 동작합니다:

1. **쿼리 생성**: LLM이 강의 요약 → 최대 3개 검색 쿼리 생성
2. **병렬 검색**: 각 쿼리로 YouTube API 검색 (병렬 실행)
3. **상세 조회**: Video ID → Details + Transcript 추출
4. **검증**: LLM 병렬 검증 또는 Heuristic 스코어링
5. **반환**: min_score 이상 + 점수 정렬 → top_k개 반환

**핵심 설정:**
- `QUERY_MAX=3`: 쿼리 수 제한
- `VERIFY_CONCURRENCY=20`: 병렬 검증 동시성
- `yt_lang="ko"`: 한국어 영상 우선

---

**작성일:** 2025년 11월 14일  
**버전:** 1.0  
**관련 파일:**
- `cap1_youtube_module/youtubekit/service.py`
- `cap1_youtube_module/youtubekit/llm/youtube_llm.py`
- `cap1_youtube_module/youtubekit/api/youtube_client.py`
