# GoogleKit - Google Custom Search 기반 검색 추천 모듈

강의 요약을 기반으로 Google Custom Search API를 사용하여 관련 웹 자료를 검색하고 추천하는 모듈입니다.

## 📋 주요 기능

- **LLM 기반 키워드 생성**: 강의 요약에서 검색 키워드 자동 생성
- **팬아웃 병렬 검색**: 여러 키워드로 동시 검색하여 결과 수집
- **중복 제거 및 재정렬**: URL 기반 중복 제거 및 키워드 매칭도 기준 재정렬
- **조건부 검증**: LLM 또는 Heuristic 방식으로 검색 결과 검증
- **NO_SCORING 모드**: 검증 없이 빠른 검색 결과 반환

## 🔧 설치

### 1. 환경 변수 설정

`.env` 파일에 다음 환경 변수를 추가하세요:

```bash
# Google Custom Search API
GOOGLE_SEARCH_API_KEY="YOUR_API_KEY"
GOOGLE_SEARCH_ENGINE_ID="YOUR_SEARCH_ENGINE_ID"

# OpenAI API (키워드 생성 및 검증용)
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

### 2. 의존성 설치

```bash
cd google_module
pip install -e .
```

또는:

```bash
./setup.sh
```

## 📖 사용 예시

### 기본 사용

```python
import asyncio
from googlekit.service import GoogleService
from googlekit.models import GoogleRequest

async def main():
    service = GoogleService()
    
    request = GoogleRequest(
        lecture_id="lecture_001",
        section_id=1,
        lecture_summary="하이퍼 스레딩(Hyper-Threading)은 인텔의 동시 멀티스레딩 기술입니다.",
        top_k=3,
        search_lang="en",  # 검색 키워드 언어
        language="ko"      # 응답 언어
    )
    
    results = await service.recommend_results(request)
    
    for result in results:
        print(f"제목: {result.search_result.title}")
        print(f"URL: {result.search_result.url}")
        print(f"점수: {result.score}")
        print(f"이유: {result.reason}")
        print()

asyncio.run(main())
```

### NO_SCORING 모드 (빠른 검색)

```python
from googlekit.config import flags

# NO_SCORING 모드 활성화
flags.NO_SCORING = True

# 검색 실행 (검증 스킵)
results = await service.recommend_results(request)
```

### Heuristic 검증 모드

```python
request = GoogleRequest(
    lecture_id="lecture_001",
    section_id=1,
    lecture_summary="운영체제의 메모리 관리 기법",
    verify_google=False,  # Heuristic 모드 (LLM 사용 안 함)
    top_k=5
)

results = await service.recommend_results(request)
```

## 🧪 테스트

```bash
cd google_module
python test_google.py
```

## ⚙️ 설정

### GoogleConfig (googlekit/config/google_config.py)

```python
class GoogleConfig:
    # API 키
    GOOGLE_SEARCH_API_KEY: str  # Google Search API 키
    GOOGLE_SEARCH_ENGINE_ID: str  # Search Engine ID
    OPENAI_API_KEY: str  # OpenAI API 키
    
    # 검색 설정
    DEFAULT_TOP_K: int = 5  # 기본 추천 개수
    DEFAULT_LANGUAGE: str = "ko"  # 기본 응답 언어
    DEFAULT_SEARCH_LANG: str = "en"  # 기본 검색 언어
    
    # 제한
    MAX_TOP_K: int = 10  # 최대 추천 개수
    CARD_LIMIT: int = 15  # 검증 대상 최대 수
    SEARCH_LIMIT: int = 10  # API 한 번 호출 시 최대 결과
    FANOUT: int = 3  # 동시 검색 키워드 개수
    
    # LLM 설정
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    
    # 병렬 처리
    VERIFY_CONCURRENCY: int = 15  # 검증 동시 실행 수
```

### Flags (googlekit/config/flags.py)

```python
# 검증 스위치
NO_SCORING = False  # True이면 검증 없이 검색 결과만 반환
VERIFY_GOOGLE_DEFAULT = True  # 기본값: LLM 검증

# 신뢰 도메인
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
```

## 📊 API 할당량

Google Custom Search API는 **하루 100회 무료 요청**을 제공합니다.

- FANOUT=3인 경우, 한 번의 추천 요청은 최대 3회의 API 호출을 사용합니다.
- 초과 사용 시 추가 요금이 발생할 수 있으니 주의하세요.

## 🔗 관련 링크

- [Google Custom Search API 문서](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine 생성](https://programmablesearchengine.google.com/)

## 📝 라이센스

MIT License
