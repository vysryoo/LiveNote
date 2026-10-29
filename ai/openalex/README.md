# OpenAlexKit - 학술 논문 검색 및 추천 모듈

**LiveNote 프로젝트를 위한 OpenAlex API 기반 논문 추천 시스템**

> 💡 **이 모듈의 역할**: 실시간 강의 섹션 요약을 받아서 OpenAlex API로 학술 논문을 검색하고, LLM으로 검증하여 학습에 도움되는 고품질 논문 리스트를 추천합니다.

---

## 📋 목차

- [이 모듈이 하는 일](#-이-모듈이-하는-일)
- [LiveNote에서의 실제 사용 흐름](#-livenote에서의-실제-사용-흐름)
- [설치](#-설치)
- [핵심 API](#-핵심-api)
- [실전 사용 예제](#-실전-사용-예제)
- [테스트](#-테스트)
- [프로젝트 구조](#-프로젝트-구조)
- [설정 및 커스터마이징](#-설정-및-커스터마이징)
- [문제 해결](#-문제-해결)
- [통합 가이드](#-통합-가이드)

---

## 🎯 이 모듈이 하는 일

LiveNote는 **실시간 강의를 전사하고 요약**하는 서비스입니다. 이 OpenAlex 모듈은:

### 1. **섹션 요약 → 학술 논문 검색**
```
입력: "스택의 실전 응용: 괄호 검사, 후위 표기법 계산..."
  ↓ LLM 쿼리 생성
검색: ["stack data structure", "postfix notation", "bracket matching"]
  ↓ OpenAlex API
결과: 25개 논문 검색
```

### 2. **고품질 필터링 + 검증**
```
25개 논문
  ↓ 중복 제거 (DOI/제목)
18개 논문
  ↓ 재랭킹 (키워드 매칭)
상위 10개 선택
  ↓ LLM 병렬 검증 (관련도 점수 0-10)
Top 5 논문 추천
```

### 3. **추천 이유와 함께 반환**
```json
{
  "title": "Stack-based algorithms for expression evaluation",
  "score": 9.5,
  "reason": "후위 표기법 계산의 스택 기반 알고리즘을 명확히 설명하며 강의 내용과 직접 연관됩니다.",
  "url": "https://doi.org/10.1145/1234567",
  "year": 2018,
  "cited_by_count": 234
}
```

---

## 🔄 LiveNote에서의 실제 사용 흐름

### **Phase 1: 강의 중 - 섹션마다 논문 추천** (매 1분)

```
실시간 오디오 → STT → LLM 요약 → Spring → OpenAlex 모듈
                                    ↓
                              논문 추천 리스트 반환
```

#### **섹션 3 (120~180초): "스택 응용" 강의**

**1. Spring이 OpenAlex 모듈에 요청**
```python
from openalexkit import OpenAlexService, OpenAlexRequest, PreviousSummary, RAGChunk

service = OpenAlexService()

request = OpenAlexRequest(
    lecture_id="lecture_abc123",
    section_id=3,
    section_summary="스택의 실전 응용: 괄호 검사, 후위 표기법 계산, 함수 호출 스택",
    language="ko",
    top_k=5,
    verify_openalex=True,  # LLM 검증 활성화
    previous_summaries=[
        PreviousSummary(
            section_id=1,
            summary="스택은 LIFO 구조입니다..."
        ),
        PreviousSummary(
            section_id=2,
            summary="큐는 FIFO 구조입니다..."
        )
    ],
    rag_context=[
        RAGChunk(
            text="1장. 스택과 큐 - 자료구조의 기본...",
            score=0.89
        )
    ],
    year_from=2010,
    sort_by="hybrid",  # hybrid: 연관성 + 인용수 균형
    min_score=5.0      # 5점 이상만 추천
)

# 논문 추천
results = await service.recommend_papers(request)
```

**2. OpenAlex 모듈이 하는 일**
```python
# (1) 섹션 요약 → LLM 쿼리 생성
query = {
    "tokens": ["stack data structure", "postfix notation", "bracket matching"]
}

# (2) OpenAlex API 호출 (필터 적용)
#     - from_publication_date: 2010-01-01
#     - language: en
#     - type: article
papers = search_openalex(query)  # 25개 검색

# (3) 전처리
papers = deduplicate(papers)  # 중복 제거 → 18개
papers = rerank(papers, query)  # 재랭킹 (키워드 매칭)

# (4) LLM 병렬 검증 (상위 10개)
#     동시성: 5개씩 병렬 처리
for paper in papers[:10]:
    score, reason = llm_verify(paper, section_summary)

# (5) 점수 순 정렬 → Top 5 반환
results = sorted_papers[:5]
```

**3. 반환 결과**
```python
[
    OpenAlexResponse(
        lecture_id="lecture_abc123",
        section_id=3,
        paper_info=PaperInfo(
            url="https://doi.org/10.1145/1234567",
            title="Stack-based algorithms for expression evaluation",
            abstract="This paper presents efficient stack-based algorithms...",
            year=2018,
            cited_by_count=234,
            authors=["John Doe", "Jane Smith"]
        ),
        reason="후위 표기법 계산의 스택 기반 알고리즘을 명확히 설명하며 강의 내용과 직접 연관됩니다.",
        score=9.5
    ),
    # ... 나머지 4개 논문
]
```

#### 📋 반환 필드 상세 설명

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `lecture_id` | str | 요청 강의 세션 ID (추적용) | `"lecture_abc123"` |
| `section_id` | int | 섹션 번호 | `3` |
| **`paper_info`** | PaperInfo | **논문 상세 정보** | ↓ |
| ├─ `url` | str | 논문 접근 URL (DOI 또는 OpenAlex ID) | `"https://doi.org/10.1145/1234567"` |
| ├─ `title` | str | 논문 제목 | `"Stack-based algorithms..."` |
| ├─ `abstract` | str | 논문 초록 (최대 500자) | `"This paper presents..."` |
| ├─ `year` | int | 출판 연도 | `2018` |
| ├─ `cited_by_count` | int | 피인용 횟수 | `234` |
| └─ `authors` | List[str] | 저자 리스트 | `["John Doe", "Jane Smith"]` |
| **`reason`** | str | **추천 이유 (1-2문장)** | ↓ |
| **`score`** | float | **관련도 점수 (0-10)** | `9.5` |

#### 🔍 `reason` 필드 이해하기

**1. LLM 검증 모드 (`verify_openalex=True`)**
```python
# 예시 1: 원조 논문 (10점)
reason = "DQN에서 Experience Replay와 Target Network의 역할을 직접 다루며, Q-learning의 발전을 명확히 설명하고 있다."
score = 10.0

# 예시 2: 핵심 개념 직접 다룸 (9점)
reason = "후위 표기법 계산의 스택 기반 알고리즘을 명확히 설명하며 강의 내용과 직접 연관됩니다."
score = 9.0

# 예시 3: 부분적 관련 (7-8점)
reason = "스택 자료구조의 응용 사례를 다루고 있으나 후위 표기법에 대한 구체적 설명은 부족하다."
score = 7.5

# 예시 4: 배경지식 (4-6점)
reason = "자료구조의 일반적 개념을 다루지만 스택의 실전 응용에 대한 내용은 제한적이다."
score = 5.0
```

**2. Heuristic 모드 (`verify_openalex=False`)**
```python
# 모든 논문 동일한 reason
reason = "Heuristic"
score = 7.5  # 점수는 키워드 매칭 기반으로 계산

# 점수 계산 로직:
# - 기본 점수: 5.0
# - 제목 키워드 매칭: +0.5점/키워드
# - 초록 키워드 매칭: +0.2점/키워드
# - OpenAlex relevance_score: 최대 +2.0점
```

#### 💡 검증 모드 선택 가이드

| 모드 | 속도 | 정확도 | reason 품질 | 사용 시나리오 |
|------|------|--------|-------------|---------------|
| **LLM** (`verify_openalex=True`) | 느림 (7-10초) | 높음 | 구체적 평가 | 고품질 추천 필요, 학습 효과 중시 |
| **Heuristic** (`verify_openalex=False`) | 빠름 (3-5초) | 중간 | `"Heuristic"` 고정 | 빠른 필터링, 대략적 순위 매기기 |

#### 🎯 활용 예시

**예시 1: LLM 검증 결과 해석**
```python
# 9.5점 논문 → 강의 핵심 개념 직접 다룸
if paper.score >= 9.0:
    print("✅ 강의와 직접 관련된 고품질 논문")
    print(f"이유: {paper.reason}")

# 7-8점 → 부분적 관련
elif paper.score >= 7.0:
    print("📌 관련 있지만 부분적")

# 5-6점 → 배경지식
elif paper.score >= 5.0:
    print("📚 배경지식 수준")
```

**예시 2: Heuristic 결과 해석**
```python
# reason은 "Heuristic"으로 고정
# 점수만으로 판단
if paper.reason == "Heuristic":
    if paper.score >= 8.0:
        print("✅ 키워드 매칭도 높음 (추천)")
    elif paper.score >= 6.0:
        print("📌 중간 정도 관련")
    else:
        print("📚 약간 관련")
```

---

## ✨ 핵심 개념

### 1. **검색 쿼리 생성 (LLM)**
- 입력: 섹션 요약 + 이전 섹션 + RAG 컨텍스트
- 출력: 2-4개 학술 검색 토큰 (영어)
- 예: `["stack data structure", "postfix notation"]`

### 2. **논문 필터링**
- **초록 없음**: 인용 수 < 100 → 제외
- **중복 제거**: DOI 또는 정규화된 제목 기준
- **재랭킹**: 키워드 매칭 점수 (제목 3점, 초록 1점)

### 3. **LLM 검증 (병렬)**
- 동시성: 5개씩 병렬 처리 (Semaphore)
- 점수: 0-10 (엄격한 기준)
  - **10**: 개념을 처음 제시한 논문
  - **9**: 핵심 개념을 직접 다룸
  - **7-8**: 부분적 또는 간접적 관련
  - **4-6**: 배경지식이지만 주제와 약간 벗어남
  - **1-3**: 키워드만 겹침

### 4. **Heuristic 스코어링 (빠른 대안)**
- LLM 검증 비활성화 시 사용
- 점수 계산:
  - 제목 키워드 매칭: +0.5점/키워드
  - 초록 키워드 매칭: +0.2점/키워드
  - relevance_score 가중치: 최대 +2점
  - 기본 점수: 5.0

---

## 📦 설치

### 사전 요구사항

- **Python 3.11 이상**
- **OpenAI API 키** ([발급 방법](https://platform.openai.com/api-keys))

### 빠른 설치 (setup.sh 사용)

```bash
# 1. 디렉토리 이동
cd openalex

# 2. 자동 설치 스크립트 실행
chmod +x setup.sh
./setup.sh

# 3. .env 파일에 API 키 설정
# .env 파일을 열어서 OPENAI_API_KEY=sk-your-key-here 수정

# 4. 가상환경 활성화
source .venv/bin/activate

# 5. 테스트 실행 (선택)
python test_openalex.py
```

### 수동 설치

```bash
# 1. 디렉토리 이동
cd openalex

# 2. 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 패키지 설치
pip install -e .

# 4. API 키 설정
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 5. 테스트 (선택)
python test_openalex.py
```

---

## 🔧 핵심 API

### `OpenAlexService.recommend_papers()`

**논문 추천 (핵심 메서드)**

```python
from openalexkit import OpenAlexService, OpenAlexRequest

service = OpenAlexService()

# 요청 생성
request = OpenAlexRequest(
    lecture_id="lecture_abc123",
    section_id=3,
    section_summary="스택의 실전 응용: 괄호 검사, 후위 표기법 계산",
    language="ko",
    top_k=5,
    verify_openalex=True,  # LLM 검증 (False: Heuristic)
    year_from=2010,
    sort_by="hybrid",      # 정렬 방식 선택
    min_score=5.0          # 최소 점수 임계값
)

# 논문 추천
results = await service.recommend_papers(request)

for paper in results:
    print(f"[{paper.score:.1f}] {paper.paper_info.title}")
    print(f"  → {paper.reason}")
    print(f"  📎 {paper.paper_info.url}")
```

**파라미터 설명:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `lecture_id` | str | ✅ | 강의 세션 ID (추적용) |
| `section_id` | int | ✅ | 현재 섹션 번호 |
| `section_summary` | str | ✅ | 현재 섹션 요약 (최소 10자) |
| `language` | str | ❌ | 응답 언어 (기본: "ko") |
| `top_k` | int | ❌ | 추천 논문 개수 (기본: 5, 최대: 10) |
| `verify_openalex` | bool | ❌ | LLM 검증 여부 (기본: True) |
| `previous_summaries` | List | ❌ | 이전 섹션 요약 리스트 |
| `rag_context` | List | ❌ | RAG 검색 결과 리스트 |
| `year_from` | int | ❌ | 논문 출판 연도 필터 (기본: 2015) |
| `exclude_ids` | List[str] | ❌ | 제외할 논문 ID 리스트 |
| `sort_by` | str | ❌ | 정렬 기준 (기본: "hybrid")<br>- "relevance": 키워드 연관성 우선<br>- "cited_by_count": 인용수 우선<br>- "hybrid": 연관성 + 인용수 균형 |
| `min_score` | float | ❌ | 최소 점수 임계값 (기본: 3.0)<br>이 점수 미만 논문은 제외 (0.0~10.0) |

---

## 💼 실전 사용 예제

### 예제 1: 최소 파라미터 (빠른 추천)

```python
import asyncio
from openalexkit import OpenAlexService, OpenAlexRequest

async def simple_recommend():
    service = OpenAlexService()
    
    request = OpenAlexRequest(
        lecture_id="simple_001",
        section_id=1,
        section_summary="미분은 함수의 순간 변화율을 나타냅니다. 도함수 f'(x)는 접선의 기울기입니다.",
        verify_openalex=False  # Heuristic (빠름)
    )
    
    results = await service.recommend_papers(request)
    
    for paper in results:
        print(f"[{paper.score:.1f}] {paper.paper_info.title}")
    
    await service.close()

asyncio.run(simple_recommend())
```

### 예제 2: 전체 컨텍스트 포함 (고품질)

```python
from openalexkit import (
    OpenAlexService,
    OpenAlexRequest,
    PreviousSummary,
    RAGChunk
)

async def full_context_recommend():
    service = OpenAlexService()
    
    request = OpenAlexRequest(
        lecture_id="full_001",
        section_id=5,
        section_summary="양자 얽힘은 두 입자가 거리에 관계없이 상관관계를 유지하는 현상입니다.",
        language="ko",
        top_k=3,
        verify_openalex=True,  # LLM 검증 (정확)
        previous_summaries=[
            PreviousSummary(
                section_id=3,
                summary="파동-입자 이중성은 빛과 물질의 특성입니다."
            ),
            PreviousSummary(
                section_id=4,
                summary="슈뢰딩거 방정식은 양자 상태의 시간 변화를 기술합니다."
            )
        ],
        rag_context=[
            RAGChunk(
                text="양자역학의 기본 원리: 중첩, 얽힘, 측정...",
                score=0.92
            )
        ],
        year_from=2000
    )
    
    results = await service.recommend_papers(request)
    
    print(f"✅ {len(results)}개 논문 추천 완료")
    for i, paper in enumerate(results, 1):
        print(f"\n{i}. [{paper.score:.1f}] {paper.paper_info.title}")
        print(f"   → {paper.reason}")
        print(f"   📎 {paper.paper_info.url}")
        print(f"   🏷️  {paper.paper_info.year} | CITE:{paper.paper_info.cited_by_count}")
    
    await service.close()

asyncio.run(full_context_recommend())
```

### 예제 3: 중복 방지 (세션 캐시)

```python
# Spring 백엔드에서 세션별 추천 이력 관리
lecture_cache = {}  # {lecture_id: set(paper_ids)}

async def recommend_with_cache(lecture_id: str, section_id: int, summary: str):
    service = OpenAlexService()
    
    # 이미 추천한 논문 ID 가져오기
    exclude_ids = list(lecture_cache.get(lecture_id, set()))
    
    request = OpenAlexRequest(
        lecture_id=lecture_id,
        section_id=section_id,
        section_summary=summary,
        exclude_ids=exclude_ids  # 중복 방지
    )
    
    results = await service.recommend_papers(request)
    
    # 추천한 논문 ID 캐시에 추가
    if lecture_id not in lecture_cache:
        lecture_cache[lecture_id] = set()
    
    for paper in results:
        lecture_cache[lecture_id].add(paper.paper_info.url)
    
    await service.close()
    
    return results
```

---

## 🧪 테스트

```bash
python test_openalex.py
```

20개의 다양한 시나리오 (CS, Math, Physics, Chemistry, Biology, Economics, Psychology, History)를 테스트합니다.

**주요 테스트 시나리오:**
- **CS (5개)**: 자료구조, 알고리즘, 머신러닝, 웹개발, 데이터베이스
- **Math (3개)**: 미적분, 선형대수, 확률론
- **Physics (3개)**: 양자역학, 고전역학, 열역학
- **Chemistry (3개)**: 유기화학, 무기화학, 물리화학
- **Biology (3개)**: 세포생물학, 분자생물학, 생태학
- **기타 (3개)**: 경제학, 심리학, 역사학

---

## 📁 프로젝트 구조

```
openalex/
├── .env                          # 환경 변수 (OPENAI_API_KEY)
├── README.md                     # 이 문서
├── setup.sh                      # 환경 설정 스크립트
├── setup.py                      # 패키지 설치 설정
├── test_openalex.py             # 통합 테스트 (20개 시나리오)
│
└── openalexkit/                 # 메인 패키지
    ├── __init__.py              # 패키지 초기화
    ├── models.py                # 데이터 모델 (Pydantic)
    ├── service.py               # OpenAlexService 메인 로직
    │
    ├── config/                  # 설정 관리
    │   ├── __init__.py
    │   ├── flags.py             # 기능 플래그 (VERIFY_OPENALEX_DEFAULT 등)
    │   ├── openalex_config.py   # OpenAlex API 설정
    │   └── prompts.py           # LLM 프롬프트 템플릿
    │
    ├── api/                     # 외부 API 클라이언트
    │   ├── __init__.py
    │   └── openalex_client.py   # OpenAlex API 래퍼
    │
    ├── llm/                     # LLM 통합
    │   ├── __init__.py
    │   └── openai_client.py     # OpenAI GPT 클라이언트
    │
    └── utils/                   # 유틸리티 함수
        ├── __init__.py
        ├── filters.py           # 중복 제거, 재정렬
        └── parser.py            # OpenAlex 데이터 파싱
```

### 주요 디렉토리 설명

- **config/**: 모든 설정을 한 곳에서 관리
  - `flags.py`: VERIFY_OPENALEX_DEFAULT, TOKEN_MIN/MAX 등 기능 플래그
  - `prompts.py`: LLM 프롬프트 템플릿 (간결하고 영어 위주)
  - `openalex_config.py`: OpenAlex API 엔드포인트 및 필터 설정

- **api/**: 외부 API 통신 계층
  - `openalex_client.py`: OpenAlex 검색 API 호출 및 응답 처리

- **llm/**: LLM 통합 계층
  - `openai_client.py`: 쿼리 생성 및 논문 검증 (GPT-4o-mini)

- **utils/**: 공통 유틸리티
  - `parser.py`: OpenAlex inverted index → 일반 텍스트 변환
  - `filters.py`: 논문 중복 제거 및 스코어 기반 재정렬

---

## ⚙️ 설정 및 커스터마이징
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
총 시나리오: 5개
총 추천 논문: 23개
총 소요 시간: 18432ms (평균: 3686ms/시나리오)
```

---

## ⚙️ 설정 및 커스터마이징

### 환경 변수 (`.env`)

```bash
# 필수
OPENAI_API_KEY=sk-your-key-here

# 선택 (기본값 사용 가능)
# LLM_MODEL=gpt-6-luna
# LLM_VERIFY_REASONING_EFFORT=none
```

### 코드 레벨 설정

**`openalexkit/config/openalex_config.py`**

```python
class OpenAlexConfig:
    # LLM 설정
    # 모델·추론 강도는 core.llm 용도별 설정을 따름 (환경변수 LLM_MODEL, LLM_<용도>_MODEL)
    MAX_TOKENS_QUERY = 100
    MAX_TOKENS_SCORE = 80
    
    # 검색 제한
    CARD_LIMIT = 10  # 검증 대상 최대 수
    MAX_TOP_K = 10   # 최대 반환 개수
    
    # 병렬 처리
    VERIFY_CONCURRENCY = 5  # 동시 검증 수 (1-10 권장)
    
    # API 타임아웃
    TIMEOUT = 10  # 초
```

### 프롬프트 커스터마이징

**`openalexkit/config/prompts.py`**

```python
# 쿼리 생성 프롬프트 수정
QUERY_GENERATION_PROMPT = """
You are a technical search expert...
(프롬프트 내용 수정)
"""

# 논문 검증 프롬프트 수정
SCORE_PAPER_PROMPT = """
You are an expert in assessing...
(점수 기준 조정)
"""
```

---

## 🔧 문제 해결

### OpenAI API 키 오류

```bash
# 환경변수 확인
echo $OPENAI_API_KEY

# 설정 안 되어 있으면
export OPENAI_API_KEY='sk-your-key-here'

# 또는 .env 파일 생성
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### OpenAlex API 타임아웃

```python
# config/openalex_config.py에서 타임아웃 조정
class OpenAlexConfig:
    TIMEOUT = 15  # 10 → 15초로 증가
```

### LLM 검증이 느릴 때

```python
# 방법 1: Heuristic 스코어링 사용
request = OpenAlexRequest(
    ...,
    verify_openalex=False  # LLM 대신 Heuristic
)

# 방법 2: 동시성 증가 (API 속도제한 주의)
class OpenAlexConfig:
    VERIFY_CONCURRENCY = 10  # 5 → 10으로 증가
```

### 검색 결과가 없을 때

```python
# 1. year_from 낮추기
request = OpenAlexRequest(
    ...,
    year_from=2000  # 2015 → 2000
)

# 2. 섹션 요약 구체화
# ❌ "AI에 대해 설명합니다"
# ✅ "딥러닝의 역전파 알고리즘은 경사하강법으로 가중치를 업데이트합니다"
```

### 논문 초록이 짧을 때

```python
# config/openalex_config.py에서 초록 길이 조정
class OpenAlexConfig:
    ABSTRACT_MAX_LENGTH = 1000  # 500 → 1000자로 증가
```

---

## 🤝 통합 가이드

### LiveNote 백엔드 통합

이 모듈은 LiveNote의 Spring 백엔드와 FastAPI 서버를 통해 통합됩니다:

```
LiveNote Backend (Spring)
    ↓
FastAPI Wrapper (추천 논문 API)
    ↓
OpenAlexKit (이 모듈)
    ↓
OpenAlex API + OpenAI GPT-4o-mini
```

**FastAPI 래퍼 예시:**

```python
from fastapi import FastAPI
from openalexkit import OpenAlexService, OpenAlexRequest

app = FastAPI()
service = OpenAlexService()

@app.post("/recommend-papers")
async def recommend_papers(request: OpenAlexRequest):
    """논문 추천 API"""
    results = await service.recommend_papers(request)
    return {
        "lecture_id": request.lecture_id,
        "section_id": request.section_id,
        "papers": [
            {
                "title": r.paper_info.title,
                "url": r.paper_info.url,
                "score": r.score,
                "reason": r.reason,
                "year": r.paper_info.year,
                "cited_by_count": r.paper_info.cited_by_count,
                "authors": r.paper_info.authors
            }
            for r in results
        ]
    }
```

---

## 📄 라이선스

MIT License

---

**이 모듈을 LiveNote 프로젝트에 통합하여 학습자에게 고품질 학술 논문을 추천하세요!** 🚀
