# REC Google 동작 과정

## 📚 개요

**Google Custom Search 추천 시스템**의 전체 동작 과정을 설명합니다.

**핵심 특징:**
- LLM 기반 검색 쿼리 생성 (QUERY_MAX=3개 제한)
- Google Custom Search API를 통한 웹 검색
- 병렬 검색 (여러 쿼리 동시 실행)
- Trafilatura를 통한 본문 추출
- LLM 검증 (Semaphore 동시성 제어, 최대 20개)
- Heuristic 스코어링 (빠른 평가)
- NO_SCORING 모드 지원

---

## 🔄 전체 흐름도

```
┌──────────────────────────────────────────────────────────────────┐
│                    Google 검색 추천 시스템                        │
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
        │  2. Google Custom Search 병렬 검색     │
        │     - 각 쿼리별 웹 검색 (병렬)          │
        │     - 중복 제거 (URL 정규화)            │
        │     - exclude_urls 필터링               │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  3. 웹페이지 본문 추출                  │
        │     - Trafilatura로 본문 추출          │
        │     - 메타데이터 추출 (저자, 날짜)      │
        │     - 텍스트 정제                       │
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
class GoogleSettings(BaseModel):
    top_k: int = Field(default=3)           # 반환할 검색 결과 수
    verify: bool = Field(default=True)      # LLM 검증 ON/OFF
    min_score: float = Field(default=0.0)   # 최소 점수
```

### **cap1_google_module/googlekit/config/google_config.py**
```python
class GoogleConfig:
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2
    
    VERIFY_CONCURRENCY: int = 20  # 병렬 검증 동시성
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
```

### **cap1_google_module/googlekit/config/flags.py**
```python
NO_SCORING = False           # True: 검증 스킵
QUERY_MAX = 3                # 최대 쿼리 수
MAX_SEARCH_RESULTS = 10      # 쿼리당 최대 검색 결과
```

---

## 🔍 검색 결과 없음 FAQ

### Q1: "Google 검색 결과가 없어요"

**가능한 원인:**
1. **쿼리 생성 실패**: LLM이 적절한 검색어 생성 실패
2. **본문 추출 실패**: Trafilatura가 본문 추출 실패
3. **너무 짧은 본문**: 본문 길이가 너무 짧아서 제외됨
4. **exclude_urls**: 이미 추천된 URL들이 제외됨
5. **API 제한**: Google Custom Search API 할당량 초과

**해결 방법:**
- `QUERY_MAX=5` (쿼리 수 증가)
- API 키 확인 (GOOGLE_API_KEY, GOOGLE_CSE_ID)
- 로그 확인: 본문 추출 성공 여부

---

## 📝 요약

**Google 검색 추천 시스템**은 5단계로 동작합니다:

1. **쿼리 생성**: LLM이 강의 요약 → 최대 3개 검색 쿼리 생성
2. **병렬 검색**: 각 쿼리로 Google Custom Search (병렬 실행)
3. **본문 추출**: Trafilatura로 웹페이지 본문 추출
4. **검증**: LLM 병렬 검증 또는 Heuristic 스코어링
5. **반환**: min_score 이상 + 점수 정렬 → top_k개 반환

**핵심 설정:**
- `QUERY_MAX=3`: 쿼리 수 제한
- `VERIFY_CONCURRENCY=20`: 병렬 검증 동시성
- `MAX_SEARCH_RESULTS=10`: 쿼리당 검색 결과 수

---

**작성일:** 2025년 11월 14일  
**버전:** 1.0  
**관련 파일:**
- `cap1_google_module/googlekit/service.py`
- `cap1_google_module/googlekit/llm/google_llm.py`
- `cap1_google_module/googlekit/api/google_client.py`
