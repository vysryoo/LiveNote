# YouTubeKit - 강의 섹션 맞춤 유튜브 추천 모듈

실시간 강의 요약과 RAG 컨텍스트를 기반으로 관련 유튜브 영상을 검색·요약·검증하여 추천합니다.

## 🚀 주요 기능

- **LLM 기반 검색어 생성**: 강의 컨텍스트(이전 섹션, RAG 청크) 반영
- **YouTube Data API v3 연동**: 검색 + 상세 정보 수집
- **자막/설명 기반 3문장 요약**: LLM 요약 + 오프라인 fallback
- **LLM 또는 Heuristic 검증**: 관련도 점수(0.0~10.0) 기반 필터링
- **제목 중복/제외 처리**: 중복 제거 및 노이즈 필터
- **완전 비동기 병렬화**: Query + Video 병렬 처리 (4.2x 빠름, 11-13초)

## 📦 설치

```bash
cd module_intergration/youtube_module
chmod +x setup.sh
./setup.sh
```

### 환경변수 설정 (`.env`)

```bash
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=...  # YouTube Data API v3 Key
```

## 💡 사용 예시

```python
import asyncio
from youtubekit import (
    YouTubeService, 
    YouTubeRequest, 
    PreviousSummary, 
    RAGChunk
)

async def main():
    service = YouTubeService()
    
    req = YouTubeRequest(
        lecture_id="python_adv_001",
        section_id=2,
        lecture_summary="Advanced Python list comprehensions: nested loops, "
                       "conditional expressions, and performance optimization",
        language="en",
        top_k=3,
        verify_yt=True,  # LLM 검증 (False: Heuristic)
        yt_lang="en",
        min_score=6.0,
        
        # 컨텍스트 확장
        previous_summaries=[
            PreviousSummary(
                section_id=1,
                summary="Control flow in Python: if, for, while loops"
            )
        ],
        
        # RAG 검색 결과
        rag_context=[
            RAGChunk(
                text="List comprehension is a concise way to create lists...",
                score=0.92,
                metadata={"source": "lecture_notes.pdf", "page": 15}
            )
        ],
        
        # 제외 제목
        exclude_titles=["Python Tutorial for Beginners"]
    )
    
    results = await service.recommend_videos(req)
    
    for idx, r in enumerate(results, 1):
        vi = r.video_info
        print(f"[{idx}] {vi.title}")
        print(f"    📊 점수: {r.score:.1f}/10.0")
        print(f"    🔗 URL: {vi.url}")
        print(f"    💡 이유: {r.reason}")
        print(f"    📝 요약: {vi.extract}\n")

asyncio.run(main())
```

## 📋 API 문서

### YouTubeService.recommend_videos()

```python
async def recommend_videos(request: YouTubeRequest) -> list[YouTubeResponse]
```

**처리 흐름**
1. 검색어 생성 (LLM, 컨텍스트 반영)
2. YouTube 검색 (병렬 처리)
3. 상세 정보/자막 수집 (Semaphore(20))
4. 3문장 요약 생성 (자막 또는 설명 기반)
5. 조건부 검증 (LLM 또는 Heuristic)
6. `min_score` 필터 + 점수순 정렬
7. `top_k` 반환

### 입력: YouTubeRequest

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `lecture_id` | string | ✅ | - | 강의 세션 ID |
| `section_id` | int | ✅ | - | 현재 섹션 번호 (≥1) |
| `lecture_summary` | string | ✅ | - | 현재 섹션 요약 (≥10자) |
| `language` | string | ❌ | `"ko"` | 응답 언어 (`ko`/`en`) |
| `top_k` | int | ❌ | `5` | 추천 개수 (1~10) |
| `verify_yt` | bool | ❌ | `False` | LLM 검증 (True: LLM, False: Heuristic) |
| `previous_summaries` | array | ❌ | `[]` | 이전 섹션 요약 리스트 |
| `rag_context` | array | ❌ | `[]` | RAG 검색 결과 |
| `yt_lang` | string | ❌ | `"en"` | YouTube 검색 언어 |
| `exclude_titles` | array | ❌ | `[]` | 제외할 영상 제목 |
| `min_score` | float | ❌ | `5.0` | 최소 점수 (0.0~10.0) |

### 출력: YouTubeResponse

```python
class YouTubeResponse:
    lecture_id: str         # 강의 세션 ID
    section_id: int         # 섹션 번호
    video_info: YouTubeVideoInfo
    reason: str            # 추천 이유 (1-2문장)
    score: float           # 관련도 점수 (0.0~10.0)

class YouTubeVideoInfo:
    url: str               # 동영상 URL
    title: str             # 제목
    extract: str           # 3문장 요약 (자막/설명 기반)
    lang: str              # 언어 (ko/en)
```

## 🔧 설정 및 플래그

### `youtubekit/config/flags.py`

```python
# 검증 스위치
VERIFY_YT_DEFAULT = False  # 기본값: Heuristic (False), LLM (True)
USE_TRANSCRIPT = True      # 자막 사용 (False: 제목/설명만)

# 쿼리 생성
QUERY_MIN = 1
QUERY_MAX = 2

# 검색 결과
MAX_SEARCH_RESULTS = 8

# Heuristic 가중치 (합계 = 1.0)
WEIGHT_TITLE_MATCH = 0.5   # 제목 유사도
WEIGHT_VIEWS = 0.3         # 조회수
WEIGHT_RECENCY = 0.2       # 최신성
```

### 4가지 동작 모드

| 모드 | `verify_yt` | `USE_TRANSCRIPT` | 점수 방법 | 요약 길이 | 처리 시간 |
|------|------------|-----------------|---------|---------|---------|
| **LLM Full** | True | True | LLM only | 자막 기반 3문장 | ~13초 |
| **LLM Fast** | True | False | LLM only | 제목/설명 2문장 | ~10초 |
| **Heuristic** | False | True | Heuristic only | 자막 기반 3문장 | ~14초 |
| **Heuristic Fast** | False | False | Heuristic only | 제목/설명 2문장 | ~11초 |

## 🧪 테스트

### 기본 테스트 (13개 시나리오)

```bash
python test_youtube.py
```

**주요 시나리오:**
1. 기본 추천 (top_k=3, Heuristic)
2. exclude_titles 적용
3. min_score 필터
4. 언어 제어 (yt_lang='ko')
5. verify_yt=True (LLM 검증)
6. previous_summaries 컨텍스트
7. rag_context 활용
8. 모든 필드 포함 테스트

### 비교 테스트 (LLM vs Heuristic)

```bash
python test_youtube2.py
```

**최종 비교 결과:**
```
⏱️  처리 시간:
   • LLM 검증:     12.97초
   • Heuristic:    14.23초
   • 빠른 방법:    LLM (12.97초)

📊 점수 비교:
   • LLM 평균:     9.0/10.0
   • Heuristic 평균: 6.7/10.0

🎯 추천 영상:
   • LLM:         3개
   • Heuristic:   2개
```

**결론:** LLM 검증이 품질·속도 모두 우수 (단, OpenAI API 비용 발생)

## 📁 아키텍처

```
youtubekit/
├── service.py              # YouTubeService (오케스트레이션)
├── models.py               # Pydantic 모델 (요청/응답)
├── api/
│   └── youtube_client.py   # YouTube Data API v3 래퍼
├── llm/
│   └── openai_client.py    # LLM 호출 (검색어/요약/검증)
├── utils/
│   └── filters.py          # 중복 제거/Heuristic 점수
└── config/
    ├── flags.py            # 동작 플래그 및 가중치
    ├── prompts.py          # 프롬프트 템플릿
    └── youtube_config.py   # API 키 설정
```

## ⚡ 성능 최적화

### 병렬화 구현

- **Query 레벨**: `asyncio.gather()` - 모든 검색 쿼리 동시 처리
- **Video 레벨**: `asyncio.gather()` + `Semaphore(20)` - 최대 20개 영상 동시 처리
- **API 호출**: `httpx.AsyncClient` - 비동기 HTTP 요청

### 성능 측정 (3개 영상 기준)

| 구현 | 처리 시간 | 개선율 |
|------|---------|-------|
| 순차 처리 | ~50초 | - |
| 병렬 처리 | ~11-13초 | **4.2x 빠름** ✅ |

**병목 요인:**
- YouTube Data API 응답 시간 (~1-2초/요청)
- OpenAI API 추론 시간 (~2-3초/영상)
- YouTube Transcript API (~0.5-1초/영상)

## ⚠️ 주의사항

### YouTube Transcript API

- **IP 차단 가능**: 과도한 요청 시 YouTube IP 차단
- **자막 미제공**: 모든 영상에 자막이 있는 것은 아님
- **Fallback**: 자막 실패 시 설명(description) 기반 요약

### 버전 호환성

- `youtube_transcript_api`: 3가지 방법으로 fallback 구현
  1. 인스턴스 메서드 (`api.fetch()`) - 최신 버전
  2. 클래스 메서드 (`get_transcript()`) - 구버전
  3. list 메서드 (`list_transcripts()`) - 수동/자동 자막

### 환경 요구사항

- Python 3.10+
- OpenAI API 키 (gpt-4o-mini 권장)
- YouTube Data API v3 키 (일일 쿼터 10,000)

## 📝 라이선스

© LiveNote 팀 내부 모듈. 상업적 사용 시 팀 승인 필요.

---

**Last Updated:** 2025년 11월 5일  
**Version:** 1.0.0  
**Contact:** LiveNote 개발팀
