# Google Search Module 개발 플랜

## 📋 목차
1. [API 키 상황 분석](#1-api-키-상황-분석)
2. [모듈 구조 설계](#2-모듈-구조-설계)
3. [파라미터 설계](#3-파라미터-설계)
4. [구현 단계](#4-구현-단계)
5. [서버 통합](#5-서버-통합)
6. [테스트 계획](#6-테스트-계획)

---

## 1. API 키 상황 분석

### 1.1 YouTube API 키 재사용 가능성
새로운 키 생성 완료.
최상위 폴더 .env에 GOOGLE_SEARCH_API_KEY = ~ 로 넣었음.
  
- **Google Custom Search API**: 웹 검색 전용 (완전히 다른 서비스)
  - 필요 항목:
    1. **API Key** (새로 발급)
    2. **Search Engine ID (CX)** (Custom Search Engine 생성 필요)
  - Endpoint: `https://www.googleapis.com/customsearch/v1`

현재 키발급 완료하고 
<script async src="https://cse.google.com/cse.js?cx=6331b98807937433d">
</script>
<div class="gcse-search"></div>
CX 검색엔진 설정 완료. 유튜브, 위키 검색 결과에서 제외. 


#### Step 4: .env 설정
```bash
# Google Custom Search API
GOOGLE_SEARCH_API_KEY="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
GOOGLE_SEARCH_ENGINE_ID="6331b98807937433d" (유효한 엔진임. 예시 아님. .env also added)

# 기존 YouTube API (그대로 유지)
YOUTUBE_API_KEY="AIzaSyYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
```

---

## 2. 모듈 구조 설계

### 2.1 디렉터리 구조 (기존 모듈 패턴 준수)

```
cap1_google_module/
├── README.md                     # 모듈 사용법 및 설치 가이드
├── requirements.txt              # 의존성 (requests, pydantic 등)
├── setup.py                      # pip install -e . 지원
├── setup.sh                      # 자동 설치 스크립트
├── test_google.py               # 단위 테스트
├── googlekit/
│   ├── __init__.py              # 패키지 초기화 및 __all__ 정의
│   ├── models.py                # Pydantic 데이터 모델
│   ├── service.py               # 핵심 비즈니스 로직
│   ├── api/
│   │   ├── __init__.py
│   │   └── google_client.py    # Google Custom Search API 클라이언트
│   ├── config/
│   │   ├── __init__.py
│   │   ├── flags.py            # NO_SCORING, VERIFY_GOOGLE_DEFAULT
│   │   ├── google_config.py    # GoogleConfig 클래스
│   │   └── prompts.py          # LLM 프롬프트 템플릿
│   ├── llm/
│   │   ├── __init__.py
│   │   └── openai_client.py    # OpenAI API 래퍼
│   └── utils/
│       ├── __init__.py
│       ├── filters.py          # 중복 제거, 리랭킹
│       └── scoring.py          # Heuristic 점수 계산
└── googlekit.egg-info/          # pip install 후 생성
```

### 2.2 핵심 파일 역할 비교

| 파일 | OpenAlex | Wiki | YouTube | **Google** (신규) |
|------|----------|------|---------|-------------------|
| **API 클라이언트** | `openalex_client.py` | `wiki_client.py` | `youtube_client.py` | `google_client.py` |
| **서비스 로직** | `service.py` | `service.py` | `service.py` | `service.py` |
| **LLM 클라이언트** | `openai_client.py` | `openai_client.py` | `openai_client.py` | `openai_client.py` |
| **Config** | `openalex_config.py` | `wiki_config.py` | `youtube_config.py` | `google_config.py` |
| **Flags** | `flags.py` | `flags.py` | `flags.py` | `flags.py` |
| **Utils** | `filters.py` | `deduplicate_pages()` | `heuristic_score()` | `filters.py` + `scoring.py` |

---

## 3. 파라미터 설계

### 3.1 GoogleRequest 모델 (입력)

```python
class GoogleRequest(BaseModel):
    """Google 검색 결과 추천 요청"""
    
    # ━━━ 필수 필드 ━━━
    lecture_id: str = Field(..., description="강의 세션 ID (추적용)")
    section_id: int = Field(..., ge=1, description="현재 섹션 번호")
    lecture_summary: str = Field(..., min_length=10, description="현재 강의 섹션 요약")
    
    # ━━━ 선택 필드 ━━━
    language: str = Field(default="ko", description="응답 언어 (ko/en)")
    top_k: int = Field(default=5, ge=1, le=10, description="추천 검색 결과 개수")
    verify_google: bool = Field(
        default=flags.VERIFY_GOOGLE_DEFAULT,  # flags.py에서 기본값
        description="LLM 검증 여부 (True: LLM, False: Heuristic)"
    )
    
    # ━━━ 컨텍스트 필드 ━━━
    previous_summaries: List[PreviousSummary] = Field(
        default_factory=list,
        description="이전 N개 섹션 요약 (컨텍스트 확장용)"
    )
    rag_context: List[RAGChunk] = Field(
        default_factory=list,
        description="RAG 검색 결과 (강의노트/이전 섹션)"
    )
    
    # ━━━ 검색 제어 필드 ━━━
    search_lang: str = Field(default="ko", description="Google 검색 언어 (ko/en/auto)")
    exclude_urls: List[str] = Field(
        default_factory=list,
        description="제외할 URL 리스트 (중복 방지)"
    )
    min_score: float = Field(
        default=5.0,
        ge=0.0,
        le=10.0,
        description="최소 점수 임계값 (이 점수 미만 결과 제외)"
    )
    
    result_type: str = Field(
        default="all",
        description="검색 결과 타입 (all/news/blog)"
    )
```

**일관성 체크**:
- ✅ `lecture_id`, `section_id`, `lecture_summary`: 3개 모듈 공통
- ✅ `language`, `top_k`: 3개 모듈 공통
- ✅ `verify_google`: OpenAlex(`verify_openalex`), Wiki(`verify_wiki`), YouTube(`verify_yt`) 패턴
- ✅ `previous_summaries`, `rag_context`: 3개 모듈 공통
- ✅ `exclude_*`: Wiki(`exclude_titles`), YouTube(`exclude_titles`), OpenAlex(`exclude_ids`) 패턴
- ✅ `min_score`: 3개 모듈 공통
- 🆕 `search_lang`: Wiki(`wiki_lang`), YouTube(`yt_lang`) 패턴. 검색 및 1차로 검색어 추출하는데 응답 언어임. 다른 모듈 prompt도 참고.
- 🆕 `result_type`: Google 특화. 구현 all/news/blog 만으로 설정. 필드 비어있을시 default는 all로 flags.py에 설정가능하게 구

### 3.2 GoogleSearchResult 모델 (상세 정보)

```python
class GoogleSearchResult(BaseModel):
    """Google 검색 결과 상세 정보"""
    url: str = Field(..., description="웹페이지 URL")
    title: str = Field(..., description="페이지 제목")
    snippet: str = Field(..., description="페이지 요약 (3-4줄)")
    display_link: str = Field(..., description="표시 도메인 (예: ~ naver.com ~)")
    lang: str = Field(..., description="페이지 언어 (ko/en)")
    
    @field_validator('title', 'snippet')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')
```

**일관성 체크**:
- ✅ `url`, `title`: 3개 모듈 공통
- ✅ `snippet`: Wiki(`extract`), YouTube(`extract`) 패턴
- ✅ `lang`: Wiki(`lang`), YouTube(`lang`) 패턴
- 🆕 `display_link`: Google 특화 (도메인 표시)

### 3.3 GoogleResponse 모델 (출력)

```python
class GoogleResponse(BaseModel):
    """Google 검색 결과 추천 응답"""
    lecture_id: str = Field(..., description="강의 세션 ID")
    section_id: int = Field(..., description="섹션 번호")
    search_result: GoogleSearchResult = Field(..., description="검색 결과 정보")
    reason: str = Field(..., description="추천 이유 (1-2문장)")
    score: float = Field(..., ge=0.0, le=10.0, description="관련도 점수 (0-10)")
    
    @field_validator('reason')
    @classmethod
    def normalize_newlines(cls, v: str) -> str:
        """줄바꿈 문자를 공백으로 치환"""
        return v.replace('\n', ' ').replace('\r', ' ')
```

**일관성 체크**:
- ✅ `lecture_id`, `section_id`: 3개 모듈 공통
- ✅ `reason`, `score`: 3개 모듈 공통
- ✅ `*_info`: Wiki(`page_info`), YouTube(`video_info`), OpenAlex(`paper_info`) 패턴
  → Google: `search_result`

### 3.4 server/config.py 설정

```python
class GoogleSettings(BaseModel):
    """Google 검색 추천 설정"""
    
    top_k: int = Field(default=2, ge=1, le=10, description="Google 추천 개수")
    verify: bool = Field(default=True, description="LLM 검증 여부")
    search_lang: str = Field(default="en", description="Google 검색 언어")
    language: str = Field(default="ko", description="응답 언어")
    min_score: float = Field(default=3.0, ge=0.0, le=10.0, description="최소 점수")
    result_type: str = Field(default="all", description="검색 결과 타입")
    세이프 서치는 구현하지마. 


class RECSettings(BaseModel):
    """REC 통합 설정"""
    
    openalex: OpenAlexSettings = Field(default_factory=OpenAlexSettings)
    wiki: WikiSettings = Field(default_factory=WikiSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)
    google: GoogleSettings = Field(default_factory=GoogleSettings)  # 🆕 추가
```

**일관성 체크**:
- ✅ `top_k`, `verify`, `language`, `min_score`: 3개 모듈 공통 패턴
- ✅ `*_lang`: Wiki(`wiki_lang`), YouTube(`yt_lang`) → Google(`search_lang`)
- 🆕 `safe_search`, `result_type`: Google 특화

### 3.5 server/routes/rec.py RECRequest 확장

```python
class RECRequest(BaseModel):
    """REC 통합 요청"""
    
    lecture_id: str = Field(..., min_length=1, description="강의 ID")
    section_id: int = Field(..., ge=1, description="섹션 ID")
    section_summary: str = Field(..., min_length=10, description="섹션 요약")
    previous_summaries: List[PreviousSummary] = Field(default_factory=list, description="이전 요약")
    yt_exclude: List[str] = Field(default_factory=list, description="제외할 유튜브 제목")
    wiki_exclude: List[str] = Field(default_factory=list, description="제외할 위키 제목")
    paper_exclude: List[str] = Field(default_factory=list, description="제외할 논문 ID")
    google_exclude: List[str] = Field(default_factory=list, description="제외할 구글 URL")  # 🆕
```

---

## 4. 구현 단계

### Phase 1: 프로젝트 초기화 

#### 1.1 디렉터리 구조 생성
```bash
mkdir -p cap1_google_module/googlekit/{api,config,llm,utils}
touch cap1_google_module/{README.md,requirements.txt,setup.py,setup.sh,test_google.py}
touch cap1_google_module/googlekit/{__init__.py,models.py,service.py}
touch cap1_google_module/googlekit/api/{__init__.py,google_client.py}
touch cap1_google_module/googlekit/config/{__init__.py,flags.py,google_config.py,prompts.py}
touch cap1_google_module/googlekit/llm/{__init__.py,openai_client.py}
touch cap1_google_module/googlekit/utils/{__init__.py,filters.py,scoring.py}
```

#### 1.2 requirements.txt
```txt
# HTTP 클라이언트
requests>=2.31.0
aiohttp>=3.9.0

# 데이터 검증
pydantic>=2.0.0

# 환경 변수
python-dotenv>=1.0.0

# OpenAI API
openai>=1.0.0

# 유틸리티
python-dateutil>=2.8.0
```

여기 부분에서는 루트 폴더에 있는 requirements.txt도 필요하다면 업데이트 해야됨.
나중에 모듈을 포함하는 서버 전체 폴더를 배포 킷으로 만들어야하기 때문에 의존성 문제 없도록 설정해줘.

#### 1.3 setup.py (pip install 지원)
```python
from setuptools import setup, find_packages

setup(
    name="googlekit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "aiohttp>=3.9.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "python-dateutil>=2.8.0",
    ],
    python_requires=">=3.11",
)
```

---

### Phase 2: API 클라이언트 구현

#### 2.1 google_client.py 핵심 기능
```python
class GoogleSearchClient:
    """Google Custom Search API 클라이언트"""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: str, engine_id: str):
        self.api_key = api_key
        self.engine_id = engine_id
    
    async def search(
        self,
        query: str,
        lang: str = "ko",
        num: int = 10,
        safe_search: str = "active"
    ) -> List[Dict]:
        """
        Google Custom Search 호출
        
        Args:
            query: 검색 쿼리
            lang: 검색 언어 (ko/en)
            num: 결과 개수 (최대 10)
            safe_search: 세이프서치 (active/moderate/off)
            다시 말하지만 safe_search는 내가 프로그래밍 검색 엔지 설정에서 꺼놔서 구현 안 해도 돼.
            
        Returns:
            검색 결과 리스트
        """
        # API 호출 로직
        pass
```

**참고 패턴**:
- OpenAlex: `search_papers()` - 토큰 기반 검색
- Wiki: `search_pages()` - 키워드 검색
- YouTube: `search_videos()` - 쿼리 검색
- **Google**: `search()` - 키워드 + 언어 필터

---

### Phase 3: 데이터 모델 구현 (0.5일)

#### 3.1 models.py 구조
```python
# 1. RAGChunk (공통)
# 2. PreviousSummary (공통)
# 3. GoogleSearchResult (Google 특화)
# 4. GoogleRequest (입력)
# 5. GoogleResponse (출력)
```

---

### Phase 4: LLM 클라이언트 구현

#### 4.1 필요한 LLM 기능
```python
class GoogleLLMClient:
    """Google 검색을 위한 LLM 클라이언트"""
    
    async def generate_keywords(
        self, 
        lecture_summary: str,
        language: str,
        previous_summaries: List,
        rag_context: List
    ) -> List[str]:
        """
        강의 요약 → 검색 키워드 생성
        예: "하이퍼 스레딩" → ["hyper-threading", "SMT", "CPU multithreading"]
        """
        pass

요청 : 참고로 키워드 생성할 때는 search_lang로 응답 오게 하고.
score에서 readon 만들 때는 language (응답언어) 사용해야함.
    
    async def score_result(
        self,
        lecture_summary: str,
        title: str,
        snippet: str,
        language: str
    ) -> Dict[str, Any]:
        """
        검색 결과 LLM 검증
        Returns: {"score": 8.5, "reason": "..."}
        """
        pass
```

**참고 패턴**:
- OpenAlex: `generate_query()` → tokens
- Wiki: `generate_keywords()` → keywords
- YouTube: `generate_queries()` → queries
- **Google**: `generate_keywords()` → keywords (Wiki와 유사)

---

### Phase 5: 서비스 로직 구현 

#### 5.1 service.py 핵심 흐름
```python
class GoogleService:
    """Google 검색 추천 서비스"""
    
    async def recommend_results(self, request: GoogleRequest) -> List[GoogleResponse]:
        """
        검색 결과 추천 파이프라인
        
        흐름:
        1. 키워드 생성 (LLM)
        2. 팬아웃 병렬 검색 (Google API)
        3. 중복 제거 (URL 기준)
        4. 상위 N개 선택 (CARD_LIMIT)
        5. NO_SCORING 모드 체크
           - True: 검증 스킵, reason="search", score=10
           - False: 검증 단계 진행
        6. 조건부 검증 (LLM or Heuristic)
        7. min_score 필터링
        8. 점수 순 정렬 + top_k 반환
        """
        pass
```

**NO_SCORING 모드 구현 (필수)**:
```python
# NO_SCORING 모드: 검증 없이 검색 결과만 반환
if flags.NO_SCORING:
    logger.info("⚡ NO_SCORING 모드: 검증 스킵")
    results = []
    for item in search_results[:request.top_k]:
        result_info = GoogleSearchResult(
            url=item.get("link"),
            title=item.get("title"),
            snippet=item.get("snippet", "")[:300],
            display_link=item.get("displayLink"),
            lang=request.search_lang
        )
        results.append(GoogleResponse(
            lecture_id=request.lecture_id,
            section_id=request.section_id,
            search_result=result_info,
            reason="search",
            score=10.0
        ))
    return results
```

---

### Phase 6: 유틸리티 구현

#### 6.1 filters.py
```python
def deduplicate_results(results: List[Dict]) -> List[Dict]:
    """URL 기준 중복 제거"""
    pass

def rerank_results(results: List[Dict], keywords: List[str]) -> List[Dict]:
    """키워드 매칭도 기준 재정렬"""
    pass
```

#### 6.2 scoring.py
```python
def heuristic_score(
    title: str,
    snippet: str,
    keywords: List[str],
    display_link: str
) -> float:
    """
    Heuristic 점수 계산
    
    가중치:
    - 제목 매칭: 40%
    - 스니펫 매칭: 30%
    - 도메인 신뢰도: 30% (edu, gov 등 공신력 있는 사이 높음)
    """
    pass
```

---

### Phase 7: 설정 파일 구현 트

#### 7.1 google_config.py
```python
class GoogleConfig:
    """Google 모듈 설정"""
    
    # API 키
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # 검색 설정
    DEFAULT_TOP_K: int = 5
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_SEARCH_LANG: str = "en"
    SAFE_SEARCH: str = "active"
    
    # 제한
    MAX_TOP_K: int = 10
    CARD_LIMIT: int = 15  # 검증 대상 최대 수
    SEARCH_LIMIT: int = 10  # API 한 번 호출 시 최대 결과
    FANOUT: int = 3  # 동시 검색 키워드 개수
    
    # LLM 설정
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.2
    MAX_TOKENS_QUERY: int = 100
    MAX_TOKENS_SCORE: int = 80
    
    # 병렬 처리
    VERIFY_CONCURRENCY: int = 15
    
    @classmethod
    def validate(cls):
        if not cls.GOOGLE_SEARCH_API_KEY:
            raise ValueError("GOOGLE_SEARCH_API_KEY가 설정되지 않았습니다.")
        if not cls.GOOGLE_SEARCH_ENGINE_ID:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID가 설정되지 않았습니다.")
```

#### 7.2 flags.py
```python
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
    "edu",
    "gov",
    "arxiv.org",
    "scholar.google.com",
    "stackoverflow.com",
    "github.com",
    ... 등 위키, 유튜브 빼고 2개 정도 더 생각해줘.
]
```

---

## 5. 서버 통합

### 5.1 server/dependencies.py 수정
```python
from cap1_google_module.googlekit.service import GoogleService

# 전역 인스턴스
_google_service: Optional[GoogleService] = None

def get_google_service() -> GoogleService:
    """Google 서비스 싱글톤 반환"""
    global _google_service
    if _google_service is None:
        _google_service = GoogleService()
    return _google_service
```

### 5.2 server/routes/rec.py 수정
```python
from cap1_google_module.googlekit.models import (
    PreviousSummary as GooglePreviousSummary,
    GoogleRequest,
)

@router.post("/recommend", status_code=status.HTTP_200_OK)
async def recommend_resources(
    request: RECRequest,
    rag_service=Depends(get_rag_service),
    openalex_service=Depends(get_openalex_service),
    wiki_service=Depends(get_wiki_service),
    youtube_service=Depends(get_youtube_service),
    google_service=Depends(get_google_service),  # 🆕 추가
    settings: AppSettings = Depends(get_settings),
):
    # ... 기존 코드 ...
    
    # Google 요청 생성
    google_prev = [
        GooglePreviousSummary(
            section_id=ps.section_id,
            summary=ps.summary,
            timestamp=ps.timestamp
        )
        for ps in request.previous_summaries
    ]
    
    google_request = GoogleRequest(
        lecture_id=request.lecture_id,
        section_id=request.section_id,
        lecture_summary=request.section_summary,
        language=settings.rec.google.language,
        top_k=settings.rec.google.top_k,
        verify_google=settings.rec.google.verify,
        previous_summaries=google_prev,
        rag_context=to_google_rag_chunks(rag_chunks),
        search_lang=settings.rec.google.search_lang,
        exclude_urls=request.google_exclude,
        min_score=settings.rec.google.min_score,
        safe_search=settings.rec.google.safe_search,
        result_type=settings.rec.google.result_type,
    )
    
    # 병렬 실행에 Google 추가
    tasks = {
        asyncio.create_task(openalex_service.recommend_papers(openalex_request)): "openalex",
        asyncio.create_task(wiki_service.recommend_pages(wiki_request)): "wiki",
        asyncio.create_task(youtube_service.recommend_videos(youtube_request)): "youtube",
        asyncio.create_task(google_service.recommend_results(google_request)): "google",  # 🆕
    }
```

### 5.3 server/utils.py 수정
```python
def to_google_rag_chunks(chunks):
    """RAG 청크를 Google 모듈 형식으로 변환"""
    from cap1_google_module.googlekit.models import RAGChunk
    
    return [
        RAGChunk(
            text=chunk.get("text", ""),
            score=chunk.get("score", 0.0),
            metadata=chunk.get("metadata")
        )
        for chunk in chunks
    ]
```

### 5.4 .env.example 업데이트 (완료 이미 되어있음!)
```bash
# Google Custom Search API
GOOGLE_SEARCH_API_KEY="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
GOOGLE_SEARCH_ENGINE_ID="a1b2c3d4e5f6g7h8i"
```

---

## 6. 테스트 계획

### 6.1 단위 테스트 (test_google.py)
```python
import asyncio
from googlekit.service import GoogleService
from googlekit.models import GoogleRequest

async def test_basic_search():
    """기본 검색 테스트"""
    service = GoogleService()
    request = GoogleRequest(
        lecture_id="test101",
        section_id=1,
        lecture_summary="하이퍼 스레딩에 대해 공부합니다.",
        top_k=3
    )
    results = await service.recommend_results(request)
    assert len(results) > 0
    print(f"✅ {len(results)}개 결과 반환")

async def test_no_scoring_mode():
    """NO_SCORING 모드 테스트"""
    # flags.NO_SCORING = True로 설정
    service = GoogleService()
    request = GoogleRequest(
        lecture_id="test102",
        section_id=1,
        lecture_summary="멀티프로세싱과 멀티스레딩 비교",
        top_k=5
    )
    results = await service.recommend_results(request)
    
    # NO_SCORING 모드에서는 모든 결과가 score=10, reason="search"
    for result in results:
        assert result.score == 10.0
        assert result.reason == "search"
    
    print(f"✅ NO_SCORING 모드: {len(results)}개 결과")

if __name__ == "__main__":
    asyncio.run(test_basic_search())
    asyncio.run(test_no_scoring_mode())
```
응답 시간도 나오게!

### 6.2 통합 테스트 (server 레벨)
```bash
# test.sh에 Google 검증이 잘 실행되는지 판단.
curl -X POST http://localhost:8000/rec/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "test_google",
    "section_id": 1,
    "section_summary": "하이퍼 스레딩 기술에 대해 학습합니다.",
    "previous_summaries": [],
    "yt_exclude": [],
    "wiki_exclude": [],
    "paper_exclude": [],
    "google_exclude": []
  }'
```

위 방법 말고
{
  "lecture_id": "${LECTURE_ID}",
  "section_id": 1,
  "section_summary": "${SECTION_SUMMARY}",
  "previous_summaries": [],
  "yt_exclude": [],
  "wiki_exclude": [],
  "paper_exclude": []
}
이미 기존 테스트 코드 그대로 쓰되, google_exclude 필드 추가했을 때 결과 나오는지 확인 할 예정임.

**예상 출력**:
```
event: rec_partial
data: {"source": "google", "count": 2, "items": [...], "elapsed_ms": 1500}
```

---

## 7. 개발 체크리스트

### Phase 1: 초기화 ✅
- [ ] 디렉터리 구조 생성
- [ ] requirements.txt 작성
- [ ] setup.py 작성
- [ ] README.md 작성

### Phase 2: API 클라이언트 ✅
- [ ] google_client.py 구현
- [ ] Google Custom Search API 연동
- [ ] 에러 핸들링

### Phase 3: 데이터 모델 ✅
- [ ] RAGChunk, PreviousSummary (공통)
- [ ] GoogleSearchResult (상세 정보)
- [ ] GoogleRequest (입력)
- [ ] GoogleResponse (출력)
- [ ] Pydantic validator 추가

### Phase 4: LLM 클라이언트 ✅
- [ ] openai_client.py 구현
- [ ] generate_keywords() 구현
- [ ] score_result() 구현
- [ ] prompts.py 작성

### Phase 5: 서비스 로직 ✅
- [ ] service.py 핵심 흐름 구현
- [ ] NO_SCORING 모드 구현
- [ ] 검증 로직 (LLM/Heuristic)
- [ ] 병렬 처리 (Semaphore)

### Phase 6: 유틸리티 ✅
- [ ] filters.py (중복 제거, 리랭킹)
- [ ] scoring.py (Heuristic)

### Phase 7: 설정 ✅
- [ ] google_config.py
- [ ] flags.py
- [ ] .env 설정 추가

### Phase 8: 서버 통합 ✅
- [ ] server/dependencies.py 수정
- [ ] server/config.py 수정 (GoogleSettings)
- [ ] server/routes/rec.py 수정
- [ ] server/utils.py 수정 (to_google_rag_chunks)

### Phase 9: 테스트 ✅
- [ ] test_google.py 작성
- [ ] 단위 테스트 실행
- [ ] 통합 테스트 실행
- [ ] NO_SCORING vs Scoring 비교

### Phase 10: 문서화 ✅
- [ ] cap1_google_module/README.md 완성 (루트에 있는 README.md에도 추가 내용 추가해야함.)
- [ ] API 설정 가이드
- [ ] 사용 예시 추가

---

## 9. 주의사항 및 권장사항


### 9.1 도메인 신뢰도 고려
```python
TRUSTED_DOMAINS = [
    ".edu",               # 교육기관
    ".gov",               # 정부기관
    "arxiv.org",          # 논문 아카이브
    "scholar.google.com", # 학술 검색
    "stackoverflow.com",  # 기술 Q&A
    "github.com",         # 오픈소스
]

def domain_trust_score(display_link: str) -> float:
    """도메인 신뢰도 계산 (0.0-1.0)"""
    for trusted in TRUSTED_DOMAINS:
        if trusted in display_link.lower():
            return 1.0
    return 0.5  # 기본값
```


### 9.2 로깅 강화
```python
logger.info(f"🔍 Google 검색 시작 (keywords={keywords})")
logger.info(f"🌐 Google API 호출 (num={num}, lang={lang})")
logger.info(f"📊 검색 결과: {len(results)}개")
logger.info(f"⚡ NO_SCORING 모드: 검증 스킵") if NO_SCORING else None
```

---

## 10. 최종 디렉터리 구조

```
module_intergration/
├── cap1_google_module/          # 🆕 Google 검색 모듈
│   ├── README.md
│   ├── requirements.txt
│   ├── setup.py
│   ├── setup.sh
│   ├── test_google.py
│   └── googlekit/
│       ├── __init__.py
│       ├── models.py
│       ├── service.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── google_client.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── flags.py
│       │   ├── google_config.py
│       │   └── prompts.py
│       ├── llm/
│       │   ├── __init__.py
│       │   └── openai_client.py
│       └── utils/
│           ├── __init__.py
│           ├── filters.py
│           └── scoring.py
├── cap1_openalex_module/
├── cap1_wiki_module/
├── cap1_youtube_module/
├── cap1_QA_module/
├── cap1_RAG_module/
├── server/
│   ├── config.py              # GoogleSettings 추가
│   ├── dependencies.py        # get_google_service 추가
│   ├── routes/
│   │   └── rec.py            # Google 통합
│   └── utils.py              # to_google_rag_chunks 추가
├── .env                       # GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_ENGINE_ID 추가
└── .env.example              # 예시 업데이트
```

---

## 11. 다음 단계

1. **개발 플랜 검토** (현재 단계)
   - 이 문서 검토 및 수정
   - 파라미터 일관성 재확인

2. **구현 시작** (다음 단계)
   - Phase 1부터 순차적 구현
   - 각 Phase마다 커밋

3. **테스트 및 통합**
   - 단위 테스트
   - 서버 통합 테스트
   - NO_SCORING vs Scoring 비교

---

## 12. 참고 자료

### Google Custom Search API
- [공식 문서](https://developers.google.com/custom-search/v1/overview)
- [Pricing](https://developers.google.com/custom-search/v1/overview#pricing)
- [Python 클라이언트 예제](https://github.com/googleapis/google-api-python-client)

### 기존 모듈 참고
- OpenAlex: LLM 쿼리 생성, 병렬 검증
- Wiki: 키워드 생성, 팬아웃 검색
- YouTube: Heuristic 점수, 중복 제거

---

**개발 시작 전 확인사항**:
- [O] Google Custom Search API 키 발급 완료
- [O] Search Engine ID (CX) 생성 완료
- [O]  .env에 키 설정 완료
- [O] 이 플랜 검토 완료
- [ ] 일관성 체크 완료

**개발 완료 후 확인사항**:
- [ ] 단위 테스트 통과
- [ ] NO_SCORING 모드 동작 확인
- [ ] Scoring 모드 동작 확인
- [ ] 4개 소스(OpenAlex, Wiki, YouTube, Google) 병렬 실행 확인
- [ ] elapsed_ms 시간 표시 확인
- [ ] README.md 문서화 완료
