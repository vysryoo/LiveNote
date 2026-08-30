# WikiKit 📚

**Wikipedia 문서 추천 모듈** - LiveNote의 실시간 강의 섹션 요약을 기반으로 학습에 도움되는 Wikipedia 문서를 검색하고 추천합니다.

---

## 📋 목차

1. [모듈 개요](#-모듈-개요)
2. [주요 기능](#-주요-기능)
3. [설치 방법](#-설치-방법)
4. [빠른 시작](#-빠른-시작)
5. [API 문서](#-api-문서)
6. [입력 필드 상세](#-입력-필드-상세)
7. [출력 필드 상세](#-출력-필드-상세)
8. [테스트 실행](#-테스트-실행)
9. [설정 커스터마이징](#-설정-커스터마이징)
10. [문제 해결](#-문제-해결)
11. [통합 가이드](#-통합-가이드)

---

## 🎯 모듈 개요

**WikiKit**은 강의 섹션 요약을 입력받아 Wikipedia API로 문서를 검색하고, LLM으로 검증하여 고품질 학습 자료를 추천하는 순수 Python 라이브러리입니다.

### 주요 특징

- ✅ **영문 우선 검색**: 영문 Wikipedia 우선 → 부족 시 한국어 보충
- ✅ **LLM 검증**: OpenAI API로 문서 관련도 평가 (선택 가능)
- ✅ **병렬 처리**: 검색/fetch/검증 모두 비동기 병렬 실행
- ✅ **Extract 제공**: 문서 요약 (3문장) 포함
- ✅ **FastAPI 독립**: 순수 Python 라이브러리 (통합 시 쉽게 래핑 가능)

---

## 🚀 주요 기능

### 1️⃣ 팬아웃 병렬 검색
- 여러 키워드로 동시 검색
- 중복 제거 + 재랭킹

### 2️⃣ 조건부 검증
- `verify_wiki=True`: LLM으로 관련도 평가 (정확도 우선)
- `verify_wiki=False`: Heuristic 스코어링 (속도 우선)

### 3️⃣ Fallback 전략
- 영문 결과 부족 시 → 한국어 자동 보충
- `fallback_to_ko=True` (기본값)

### 4️⃣ Extract 포함
- Wikipedia API에서 문서 요약 (3문장) 가져오기
- LLM 없이도 내용 파악 가능

---

## 📦 설치 방법

### 1. 저장소 클론

```bash
cd module_intergration/wiki_module
```

### 2. 자동 설정 스크립트 실행

```bash
chmod +x setup.sh
./setup.sh
```

스크립트가 다음을 자동으로 수행합니다:
- 가상환경 생성 (`.venv`)
- 의존성 설치 (`pydantic`, `httpx`, `openai`, `python-dotenv`)
- `.env` 파일 생성

### 3. API 키 설정

`.env` 파일을 열어 OpenAI API 키를 입력하세요:

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. 가상환경 활성화

```bash
source .venv/bin/activate
```

---

## ⚡ 빠른 시작

### 기본 사용 예제

```python
import asyncio
from wikikit import WikiService, WikiRequest

async def main():
    # 서비스 초기화
    service = WikiService()
    
    # 요청 생성
    request = WikiRequest(
        lecture_id="demo_001",
        section_id=1,
        lecture_summary="Stack is a LIFO data structure used in computer science.",
        language="en",
        top_k=5,
        verify_wiki=True  # LLM 검증 활성화
    )
    
    # 추천 실행
    results = await service.recommend_pages(request)
    
    # 결과 출력
    for i, res in enumerate(results, 1):
        print(f"{i}. [{res.score:.1f}] {res.page_info.title}")
        print(f"   → {res.reason}")
        print(f"   📎 {res.page_info.url}")
        print(f"   📄 {res.page_info.extract[:100]}...")
        print()

asyncio.run(main())
```

**예상 출력**:
```
1. [9.5] Stack (abstract data type)
   → Directly explains stack data structure and LIFO concept.
   📎 https://en.wikipedia.org/wiki/Stack_(abstract_data_type)
   📄 In computer science, a stack is an abstract data type that serves as a collection of elements...

2. [8.2] Data structure
   → Provides foundational knowledge on data structures.
   📎 https://en.wikipedia.org/wiki/Data_structure
   📄 A data structure is a data organization, management, and storage format...
```

---

## 📖 API 문서

### WikiService.recommend_pages()

```python
async def recommend_pages(request: WikiRequest) -> List[WikiResponse]:
    """
    Wikipedia 문서 추천
    
    Args:
        request: WikiRequest (입력 파라미터)
    
    Returns:
        List[WikiResponse]: 추천 문서 리스트 (top_k개)
    
    Raises:
        ValueError: OPENAI_API_KEY 미설정
        Exception: API 호출 실패
    """
```

**흐름**:
1. 키워드 생성 (LLM)
2. 팬아웃 병렬 검색 (영문 우선)
3. 중복 제거
4. 상세 정보 병렬 fetch (extract 가져오기)
5. 조건부 검증 (LLM or Heuristic)
6. `min_score` 필터링
7. 결과 부족 시 한국어 보충
8. 점수 순 정렬 → `top_k` 반환

---

## 📝 입력 필드 상세

### WikiRequest

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `lecture_id` | `str` | ✅ | - | 강의 세션 ID (추적용) |
| `section_id` | `int` | ✅ | - | 현재 섹션 번호 (≥1) |
| `lecture_summary` | `str` | ✅ | - | 현재 강의 섹션 요약 (최소 10자) |
| `language` | `str` | ❌ | `"en"` | 응답 언어 (`ko`/`en`) |
| `top_k` | `int` | ❌ | `5` | 추천 문서 개수 (1-10) |
| `verify_wiki` | `bool` | ❌ | `True` | LLM 검증 여부 (`True`: LLM, `False`: Heuristic) |
| `previous_summaries` | `List[PreviousSummary]` | ❌ | `[]` | 이전 섹션 요약 (컨텍스트 확장용) |
| `rag_context` | `List[RAGChunk]` | ❌ | `[]` | RAG 검색 결과 (강의노트/이전 섹션) |
| `wiki_lang` | `str` | ❌ | `"en"` | Wikipedia 검색 언어 (`en`/`ko`) |
| `fallback_to_ko` | `bool` | ❌ | `True` | 영어 결과 부족 시 한국어 보충 여부 |
| `exclude_titles` | `List[str]` | ❌ | `[]` | 제외할 문서 제목 (중복 방지) |
| `min_score` | `float` | ❌ | `5.0` | 최소 점수 임계값 (0.0-10.0) |

#### 예시: 컨텍스트 활용

```python
### 입력 (WikiRequest)

```python
request = WikiRequest(
    lecture_id="lecture_cs_001",        # 강의 세션 ID (추적용)
    section_id=1,                       # 현재 섹션 번호
```

---

## 📤 출력 필드 상세

### WikiResponse

| 필드 | 타입 | 설명 |
|------|------|------|
| `lecture_id` | `str` | 요청한 강의 세션 ID |
| `section_id` | `int` | 요청한 섹션 번호 |
| `page_info` | `WikiPageInfo` | 문서 상세 정보 |
| `reason` | `str` | 추천 이유 (1-2문장) |
| `score` | `float` | 관련도 점수 (0.0-10.0) |

### WikiPageInfo

| 필드 | 타입 | 설명 |
|------|------|------|
| `url` | `str` | 문서 URL |
| `title` | `str` | 문서 제목 |
| `extract` | `str` | 문서 요약 (3문장 정도) |
| `lang` | `str` | 문서 언어 (`en`/`ko`) |
| `page_id` | `int` | Wikipedia 페이지 ID |

#### 예시 응답

```python
WikiResponse(
    lecture_id="demo_001",
    section_id=1,
    page_info=WikiPageInfo(
        url="https://en.wikipedia.org/wiki/Stack_(abstract_data_type)",
        title="Stack (abstract data type)",
        extract="In computer science, a stack is an abstract data type that serves as a collection of elements, with two main operations: push and pop. The order in which elements come off a stack gives rise to its alternative name, LIFO (last in, first out).",
        lang="en",
        page_id=28845
    ),
    reason="Directly explains stack data structure and LIFO concept.",
    score=9.5
)
```

---

## 🧪 테스트 실행

### 종합 테스트 (12개 시나리오)

```bash
python test_wiki.py
```

**테스트 시나리오**:
1. CS (Stack) - `top_k=1`, LLM 검증
2. Math (Calculus) - `top_k=3`, Heuristic
3. Physics (Quantum) - `top_k=5`, 영문
4. Chemistry (Organic) - `top_k=10`, 영문+한국어 보충
5. Biology (Cell) - `min_score=1.0`
6. History (Korean War) - `min_score=5.0`
7. Literature (Shakespeare) - `min_score=7.0`
8. Economics (Korean) - 한국어 검색
9. Philosophy (Kant) - Heuristic
10. Art (Renaissance) - LLM 검증
11. AI (DQN) - 이전 섹션 + RAG 포함
12. Medicine (Heart) - 중복 제거 테스트

**예상 소요 시간**: 약 30-60초 (API 속도에 따라 다름)

---

## ⚙️ 설정 커스터마이징

### config/wiki_config.py

```python
class WikiConfig:
    # ━━━ OpenAI API ━━━
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # ━━━ Wikipedia API ━━━
    TIMEOUT: int = 10  # HTTP 타임아웃 (초)
    
    # ━━━ 기본값 ━━━
    DEFAULT_LANGUAGE: str = "en"
    DEFAULT_TOP_K: int = 5
    DEFAULT_WIKI_LANG: str = "en"  # 영문 우선
    
    # ━━━ 검색 설정 ━━━
    SEARCH_LIMIT: int = 6      # 키워드당 검색 결과 수
    FANOUT: int = 3            # 병렬 검색 키워드 개수
    
    # ━━━ LLM 설정 ━━━
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    MAX_TOKENS_QUERY: int = 100  # 키워드 생성용
    MAX_TOKENS_SCORE: int = 80   # 스코어링용
    
    # ━━━ 병렬 처리 ━━━
    DETAIL_CONCURRENCY: int = 6   # 상세 정보 fetch 동시성
    VERIFY_CONCURRENCY: int = 5   # LLM 검증 동시성
```

### 프롬프트 수정

`config/prompts.py`에서 프롬프트를 커스터마이징할 수 있습니다:

```python
KEYWORD_GENERATION_PROMPT = """Extract 2-3 Wikipedia search keywords..."""
SCORE_PAGE_PROMPT = """Rate relevance (0-10)..."""
```

---

## 🛠️ 문제 해결

### 1. `OPENAI_API_KEY` 오류

**증상**:
```
ValueError: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.
```

**해결**:
- `.env` 파일에 API 키가 올바르게 설정되었는지 확인
- 파일 위치: `wiki_module/.env`

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 2. 검색 결과 없음

**증상**:
```
⚠️ Wikipedia(en) 검색 결과 없음
```

**원인**:
- 키워드가 너무 모호하거나 전문적
- Wikipedia에 관련 문서가 없음

**해결**:
- `lecture_summary`를 더 구체적으로 작성
- `fallback_to_ko=True`로 설정 (한국어 보충)

### 3. LLM 검증 느림

**증상**:
- 테스트 완료까지 1분 이상 소요

**해결**:
- `verify_wiki=False`로 설정 (Heuristic 사용)
- `VERIFY_CONCURRENCY` 증가 (병렬 처리 개수)

```python
# config/wiki_config.py
VERIFY_CONCURRENCY: int = 10  # 기본값: 5
```

### 4. HTTP Timeout

**증상**:
```
httpx.ReadTimeout: ...
```

**해결**:
- `TIMEOUT` 증가

```python
# config/wiki_config.py
TIMEOUT: int = 20  # 기본값: 10
```

---

## 🔗 통합 가이드

### Spring Boot 통합 예제

```java
@RestController
@RequestMapping("/api/wiki")
public class WikiController {
    
    @PostMapping("/recommend")
    public ResponseEntity<List<WikiResponse>> recommendWiki(
        @RequestBody WikiRequest request
    ) {
        // Python 스크립트 호출
        ProcessBuilder pb = new ProcessBuilder(
            "python3", "wikikit_wrapper.py",
            "--lecture-id", request.getLectureId(),
            "--section-id", String.valueOf(request.getSectionId()),
            "--lecture-summary", request.getLectureSummary(),
            "--top-k", String.valueOf(request.getTopK())
        );
        
        Process process = pb.start();
        
        // JSON 응답 파싱
        String output = new String(process.getInputStream().readAllBytes());
        List<WikiResponse> results = objectMapper.readValue(
            output, 
            new TypeReference<List<WikiResponse>>() {}
        );
        
        return ResponseEntity.ok(results);
    }
}
```

### Python Wrapper 스크립트

```python
# wikikit_wrapper.py
import asyncio
import json
import sys
import argparse
from wikikit import WikiService, WikiRequest

async def main(args):
    service = WikiService()
    
    request = WikiRequest(
        lecture_id=args.lecture_id,
        section_id=args.section_id,
        lecture_summary=args.lecture_summary,
        top_k=args.top_k,
        verify_wiki=True
    )
    
    results = await service.recommend_pages(request)
    
    # JSON 출력
    output = [res.model_dump() for res in results]
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lecture-id", required=True)
    parser.add_argument("--section-id", type=int, required=True)
    parser.add_argument("--lecture-summary", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    
    args = parser.parse_args()
    asyncio.run(main(args))
```

---

## 📚 추가 자료

### Wikipedia API 문서
- **공식 문서**: https://www.mediawiki.org/wiki/API:Main_page
- **검색 API**: https://www.mediawiki.org/wiki/API:Search
- **페이지 정보**: https://www.mediawiki.org/wiki/API:Query

### 기존 모듈 참고
- **RAGKit**: `RAG_module/`
- **QAKit**: `cap2_QA_module/`
- **OpenAlexKit**: `cap3_openalex_module/`

---

## 📄 라이선스

MIT License

---

## 👥 기여자

LiveNote Team

---

**Questions?** 문제가 발생하면 이슈를 등록해주세요! 🐛
