# GoogleKit - 블로그 검색 추천 모듈

강의 요약을 기반으로 네이버 블로그 검색 API(NAVER API HUB)를 사용하여 관련 블로그 글을 검색하고 추천하는 모듈입니다.

Google Custom Search JSON API가 신규 가입을 받지 않고 2027-01-01 종료 예정이라 검색 API를 네이버로 교체했습니다. 모듈·클래스 이름(`blogkit`, `GoogleService`)은 서버 코드와의 연결을 유지하기 위해 그대로 둡니다.

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
# 네이버 블로그 검색 API (네이버 클라우드 콘솔의 NAVER API HUB에서 Application 등록 후 인증 정보)
NAVER_CLIENT_ID="YOUR_CLIENT_ID"
NAVER_CLIENT_SECRET="YOUR_CLIENT_SECRET"

# OpenAI API (키워드 생성 및 검증용)
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

### 2. 의존성 설치

```bash
cd blog
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
from blogkit.service import GoogleService
from blogkit.models import GoogleRequest

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
from blogkit.config import flags

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
cd blog
python test_google.py
```

## ⚙️ 설정

### GoogleConfig (blogkit/config/google_config.py)

```python
class GoogleConfig:
    # API 키
    NAVER_CLIENT_ID: str  # 네이버 Client ID
    NAVER_CLIENT_SECRET: str  # 네이버 Client Secret
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

### Flags (blogkit/config/flags.py)

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

NAVER API HUB의 NAVER 검색 분류는 월 최대 775,000건(분류 전체 공유), API 키당 초당 50건까지 호출할 수 있습니다. 현재 한시적 무료이며 유료 전환 시 사전 공지됩니다.

- 한 번의 추천 요청은 FANOUT 수만큼 API를 호출합니다.
- 네이버 블로그 검색은 언어 지정을 지원하지 않아 한국어 블로그 위주로 검색됩니다.

## 🔗 관련 링크

- [NAVER API HUB 블로그 검색 API 문서](https://api.ncloud-docs.com/docs/naver-api-hub-search-blog)
- [NAVER API HUB Application 등록](https://guide.ncloud-docs.com/docs/apihub-application)

## 📝 라이센스

MIT License
