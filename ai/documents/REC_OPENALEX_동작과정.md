# REC Recommend 동작 과정 (OpenAlex)

## 📚 개요

이 문서는 **OpenAlex 논문 추천 시스템**의 전체 동작 과정을 설명합니다.

**핵심 특징:**
- LLM 기반 검색 쿼리 생성 (TOKEN_MIN=2, TOKEN_MAX=3개 토큰)
- OpenAlex API를 통한 학술 논문 검색
- 병렬 LLM 검증 (Semaphore 동시성 제어, 최대 20개)
- Heuristic 스코어링 (빠른 평가)
- NO_SCORING 모드 지원
- JSON 파싱 오류 방지 (MAX_TOKENS_SCORE=200, reason 50자 제한)

---

## 🔄 전체 흐름도

```
┌──────────────────────────────────────────────────────────────────┐
│                    OpenAlex 논문 추천 시스템                      │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  1. 검색 쿼리 생성 (LLM)                │
        │     - 섹션 요약 분석                    │
        │     - 이전 섹션 컨텍스트                │
        │     - RAG 컨텍스트                      │
        │     → TOKEN_MIN~TOKEN_MAX 토큰 생성    │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  2. OpenAlex API 호출                   │
        │     - tokens: ["term1", "term2", ...]  │
        │     - 필터: year_from, language, type  │
        │     - 정렬: relevance/cited/hybrid     │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  3. 논문 파싱 + 필터링                  │
        │     - 초록 역색인 → 텍스트 변환        │
        │     - 초록 없음 + 인용 100 미만 제외   │
        │     - exclude_ids 필터링                │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  4. 중복 제거 + 재랭킹                  │
        │     - deduplicate_papers()             │
        │     - rerank_papers()                  │
        │     → 상위 CARD_LIMIT개 선택           │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  5. 조건부 검증                         │
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
        │  6. 점수 필터링 + 정렬                  │
        │     - min_score 이상만 선택             │
        │     - 점수 내림차순 정렬                │
        │     → top_k개 반환                      │
        └────────────────────────────────────────┘
```

---

## 📋 단계별 상세 설명

### **1단계: 검색 쿼리 생성 (LLM)**

**목적:** 섹션 요약 → 학술 논문 검색에 적합한 TOKEN 생성

**입력:**
```python
request_data = {
    "section_summary": str,          # 현재 섹션 요약
    "previous_summaries": List[...], # 이전 섹션 요약들
    "rag_context": List[...]         # RAG 벡터 DB 검색 결과
}
```

**처리 과정:**
1. **컨텍스트 준비**
   - 섹션 요약: 현재 강의 내용
   - 이전 섹션: 강의 흐름 파악
   - RAG 컨텍스트: 관련 자료 (상위 3개)

2. **LLM 프롬프트 생성**
   ```
   QUERY_GENERATION_PROMPT:
   - Extract core concepts and technical terms
   - Use precise academic terminology
   - Expand abbreviations where needed
   - Include field-specific keywords
   - Keep it concise (TOKEN_MIN-TOKEN_MAX tokens max)
   ```

3. **OpenAI API 호출**
   - Model: `gpt-4o` (현재 설정)
   - Temperature: `0.2` (일관성 우선, 0.3→0.2)
   - Max Tokens: `150`

**출력:**
```json
{
  "tokens": ["neural network", "backpropagation", "gradient descent"],
  "year_from": 1930
}
```

**특징:**
- **TOKEN_MIN=2, TOKEN_MAX=3**: 2~3개의 핵심 토큰 생성 (4→3 감소)
- **JSON 파싱 오류 대응**: 섹션 요약에서 단어 추출 (Fallback)
- **년도 필터**: `year_from`은 request에서 받음 (기본: 1930)

---

### **2단계: OpenAlex API 호출**

**목적:** 생성된 TOKEN으로 학술 논문 검색

**API 엔드포인트:**
```
GET https://api.openalex.org/works
```

**요청 파라미터:**
```python
params = {
    "search": "neural network backpropagation gradient descent",  # tokens 결합
    "filter": "from_publication_date:1930-01-01,language:en,is_paratext:false,type:article",
    "sort": "relevance_score:desc",  # 정렬 옵션
    "per_page": 25  # 한 번에 가져올 논문 수
}
```

**필터 설명:**
- `from_publication_date:1930-01-01`: 1930년 이후 논문만 (설정 가능)
- `language:en`: 영어 논문만
- `is_paratext:false`: 보조 자료 제외 (실제 논문만)
- `type:article`: 학술 논문만 (리뷰, 책 제외)

**정렬 옵션 (sort_by):**

| 옵션 | 설명 | 사용 시기 |
|------|------|-----------|
| `relevance` | 키워드 연관성 우선 (기본값) | 강의 주제와 정확히 일치하는 논문 필요 |
| `cited_by_count` | 인용수 우선 | 영향력 있는 논문 필요 (Seminal paper) |
| `hybrid` | 연관성 상위 60% 중 인용수 높은 논문 | 연관성 + 영향력 균형 |

**응답 예시:**
```json
{
  "results": [
    {
      "id": "https://openalex.org/W2100837269",
      "title": "Learning representations by back-propagating errors",
      "abstract_inverted_index": {"We": [0, 45], "describe": [1], ...},
      "publication_year": 1986,
      "cited_by_count": 25834,
      "doi": "https://doi.org/10.1038/323533a0",
      "authorships": [...],
      "relevance_score": 0.98
    }
  ]
}
```

---

### **3단계: 논문 파싱 + 필터링**

**목적:** OpenAlex 응답 → 내부 형식 변환 + 저품질 논문 제거

**파싱 과정:**

1. **기본 정보 추출**
   ```python
   paper_id = work.get("id")
   title = work.get("title")
   year = work.get("publication_year")
   cited_by_count = work.get("cited_by_count", 0)
   doi = work.get("doi")
   url = doi if doi else paper_id
   ```

2. **초록 역색인 → 텍스트 변환**
   ```python
   # OpenAlex는 초록을 역색인으로 저장
   # {"We": [0, 45], "describe": [1], ...} → "We describe ..."
   abstract_inverted = work.get("abstract_inverted_index")
   abstract = parse_abstract_inverted_index(abstract_inverted)
   ```

3. **저자 추출 (상위 5명)**
   ```python
   authors = []
   for authorship in work.get("authorships", [])[:5]:
       name = authorship.get("author", {}).get("display_name")
       if name:
           authors.append(name)
   ```

**필터링 규칙:**

| 조건 | 처리 |
|------|------|
| 초록 없음 + 인용 100 미만 | ⏭️ 제외 |
| 초록 없음 + 인용 100 이상 | ✅ 유지 (영향력 있는 논문) |
| exclude_ids에 포함 | ⏭️ 제외 |
| 초록 50자 미만 | ⏭️ 제외 |

**출력 형식:**
```python
{
    "id": "https://openalex.org/W2100837269",
    "title": "Learning representations by back-propagating errors",
    "abstract": "We describe a new learning procedure...",
    "year": 1986,
    "cited_by_count": 25834,
    "url": "https://doi.org/10.1038/323533a0",
    "authors": ["Geoffrey E. Hinton", "David E. Rumelhart", ...],
    "no_abstract": False,
    "relevance_score": 0.98
}
```

---

### **4단계: 중복 제거 + 재랭킹**

**목적:** 유사 논문 제거 + 연관성 재평가

**처리:**
```python
papers = deduplicate_papers(papers)  # 제목 유사도 기반
papers = rerank_papers(papers, query)  # relevance_score 가중치 재조정
papers = papers[:OpenAlexConfig.CARD_LIMIT]  # 상위 N개 (예: 10개)
```

**CARD_LIMIT:**
- 검증 대상 논문 수 제한 (기본: 13개, 10→13 증가)
- 검증 시간 단축 (LLM 호출 비용 절감)

---

### **5단계: 조건부 검증**

**NO_SCORING 모드:**
```python
if flags.NO_SCORING:
    # 검증 없이 검색 결과만 반환
    # score=10.0 고정, reason="search"
    return papers[:request.top_k]
```

#### **5-1. LLM 병렬 검증 (verify=True)**

**목적:** GPT-4o로 논문-강의 연관성 정확히 평가

**처리 흐름:**
1. **Semaphore 동시성 제어**
   ```python
   semaphore = asyncio.Semaphore(VERIFY_CONCURRENCY)  # 20개 동시 실행 (5→20)
   
   async def verify_with_limit(paper):
       async with semaphore:
           return await _verify_single_paper(paper, request, query)
   
   results = await asyncio.gather(*[verify_with_limit(p) for p in papers])
   ```

2. **LLM 프롬프트**
   ```
   SCORE_PAPER_PROMPT:
   - 현재 섹션 요약: {section_summary}
   - 키워드: {keywords}
   - 논문 제목: {title}
   - 논문 초록: {abstract}
   - 출판 연도: {year}
   - 인용 횟수: {cited_by_count}
   
   점수 기준 (엄격):
   - 10점: Seminal paper (개념을 처음 제시)
   - 9점: 강의 핵심 개념 직접 다룸
   - 7-8점: 핵심 개념 부분적/간접적
   - 4-6점: 관련 배경지식 (주제 약간 벗어남)
   - 1-3점: 키워드만 겹침
   ```

3. **OpenAI API 호출**
   - Model: `gpt-4o`
   - Temperature: `0.2`
   - Max Tokens: `200` (120→200, reason 잘림 방지)

**출력:**
```json
{
  "score": 9.0,
  "reason": "Backpropagation 알고리즘을 처음 제시한 논문으로, 강의 핵심 개념을 직접 다룸"
}
```

**에러 처리:**
- JSON 파싱 실패 → Fallback: 점수만 추출 시도 (regex)
- reason 잘림 감지 → MAX_TOKENS_SCORE 증가 권장
- API 오류 → `score=5.0`, `reason="검증 실패 (API 오류)"`

#### **5-2. Heuristic 스코어링 (verify=False)**

**목적:** LLM 없이 빠른 평가 (비용 절감, 속도 향상)

**점수 계산:**
```python
score = 5.0  # 기본 점수

# 키워드 매칭
for token in query["tokens"]:
    if token.lower() in title.lower():
        score += 0.5  # 제목 매칭
    if token.lower() in abstract.lower():
        score += 0.2  # 초록 매칭

# relevance_score 가중치 (최대 +2점)
score += min(paper["relevance_score"] / 10, 2.0)

# 10점 초과 방지
score = min(score, 10.0)
```

**특징:**
- 제목 키워드 매칭: +0.5점/토큰
- 초록 키워드 매칭: +0.2점/토큰
- OpenAlex relevance_score 활용
- 검증 시간: LLM의 1/10 이하

---

### **6단계: 점수 필터링 + 정렬**

**목적:** 고품질 논문만 선택 + 최종 반환

**처리:**
```python
# min_score 이상만 선택
filtered_results = [r for r in results if r.score >= request.min_score]

# 점수 내림차순 정렬
filtered_results.sort(key=lambda x: x.score, reverse=True)

# top_k개 반환
final_results = filtered_results[:request.top_k]
```

**로그 예시:**
```
✅ 논문 추천 완료: 3개 (최고 점수: 9.0)
⚠️  min_score 4.0 이상인 논문이 없습니다
```

---

## ⚙️ 유효한 설정 가이드

### **1. server/config.py (서버 설정)**

```python
class OpenAlexSettings(BaseModel):
    top_k: int = Field(default=3, ge=1, le=10)
    verify: bool = Field(default=True)  # LLM 검증 ON/OFF
    year_from: int = Field(default=1930)  # 논문 출판 년도 필터
    min_score: float = Field(default=0.0, ge=0.0, le=10.0)  # 최소 점수
    sort_by: str = Field(default="relevance")  # relevance/cited_by_count/hybrid
```

**설정 권장 값:**

| 설정 | 권장 값 | 설명 |
|------|---------|------|
| `top_k` | `3` | 반환할 논문 수 (1~10) |
| `verify` | `True` | LLM 검증 활성화 (정확도 우선) |
| `year_from` | `2015` | 최근 논문 우선 (트렌드 파악) |
| `min_score` | `7.0` | 고품질 논문만 필터링 |
| `sort_by` | `relevance` | 강의 주제와 정확히 일치하는 논문 |

**⚠️ 검색 결과 없음 문제:**
- `year_from=1930` + `min_score=0.0`: 너무 관대함 (품질 낮음)
- `year_from=1930` + TOKEN 병렬 검색 실패: 모든 TOKEN이 매칭 안 됨
- **해결책**: `year_from=2015`, `min_score=7.0`, `verify=True`

### **2. cap1_openalex_module/openalexkit/config/openalex_config.py**

```python
class OpenAlexConfig:
    # LLM 설정
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.2  # 0.3→0.2
    
    # TOKEN 생성 범위
    TOKEN_MIN: int = 2  # 최소 토큰 수
    TOKEN_MAX: int = 3  # 최대 토큰 수 (4→3)
    
    # 검색 설정
    PER_PAGE: int = 40  # API 페이지당 논문 수 (25→40)
    CARD_LIMIT: int = 13  # 검증 대상 논문 수 (10→13)
    
    # 검증 설정
    VERIFY_CONCURRENCY: int = 20  # 병렬 검증 동시성 (5→20)
    
    # 필터링 설정
    ABSTRACT_MAX_LENGTH: int = 400  # LLM 전달 초록 길이
    DEFAULT_YEAR_FROM: int = 1930  # 기본 년도 필터
    
    # LLM 토큰 설정
    MAX_TOKENS_QUERY: int = 150  # 쿼리 생성
    MAX_TOKENS_SCORE: int = 200  # 논문 검증 (120→200)
```

**설정 조정 가이드:**

| 시나리오 | 설정 |
|---------|------|
| 고품질 논문만 필요 | `year_from=2015`, `min_score=7.0`, `verify=True` |
| 빠른 응답 필요 | `verify=False` (Heuristic), `CARD_LIMIT=5` |
| 최신 트렌드 파악 | `year_from=2020`, `sort_by=cited_by_count` |
| Seminal paper 찾기 | `year_from=1930`, `sort_by=cited_by_count`, `min_score=9.0` |
| 비용 절감 | `verify=False`, `CARD_LIMIT=5`, `PER_PAGE=10` |

### **3. cap1_openalex_module/openalexkit/config/flags.py**

```python
NO_SCORING = False  # True: 검증 스킵, False: 검증 실행
TOKEN_MIN = 2       # LLM 생성 최소 토큰 수
TOKEN_MAX = 3       # LLM 생성 최대 토큰 수 (4→3)
```

---

## 🔍 검색 결과 없음 FAQ

### Q1: "자꾸 검색 결과가 없다는데, 왜 그럴까?"

**가능한 원인:**

1. **TOKEN 생성 실패**
   ```
   📝 생성된 쿼리: tokens=[], year_from=1930
   ⚠️  검색 토큰이 생성되지 않았습니다
   ```
   - LLM이 섹션 요약에서 학술 용어 추출 실패
   - **해결**: 섹션 요약 품질 확인, LLM 프롬프트 개선

2. **TOKEN이 너무 구체적**
   ```
   tokens=["neural network backpropagation gradient descent momentum optimization"]
   ⚠️  검색된 논문이 없습니다
   ```
   - 모든 TOKEN이 동시에 포함된 논문이 없음
   - **해결**: `TOKEN_MIN=2`, `TOKEN_MAX=3` (범위 좁히기)

3. **year_from 필터가 너무 최근**
   ```
   year_from=2023
   ⚠️  검색된 논문이 없습니다
   ```
   - 2023년 이후 논문이 OpenAlex에 아직 등록 안 됨
   - **해결**: `year_from=2015` (최근 10년)

4. **min_score 임계값이 너무 높음**
   ```
   🔍 점수 필터링: 5개 → 0개 (min_score: 9.0)
   ⚠️  min_score 9.0 이상인 논문이 없습니다
   ```
   - 검증은 완료했으나 점수가 낮음
   - **해결**: `min_score=7.0` (현실적인 임계값)

5. **OpenAlex API 타임아웃/오류**
   ```
   ❌ OpenAlex API 타임아웃
   ❌ OpenAlex API HTTP 오류: 429 (Too Many Requests)
   ```
   - API 제한 초과, 네트워크 문제
   - **해결**: 재시도, API 키 설정 (rate limit 증가)

### Q2: "코드 문제는 아니고 진짜 검색 된게 없는거야?"

**확인 방법:**

1. **로그 분석**
   ```python
   # service.py 로그 확인
   logger.info(f"📝 생성된 쿼리: tokens={query.get('tokens', [])}, year_from={query.get('year_from')}")
   logger.info(f"🌐 OpenAlex API 호출 (tokens={len(query.get('tokens', []))}개)")
   logger.info(f"📚 검색된 논문: {len(papers)}개")
   ```

2. **OpenAlex API 직접 테스트**
   ```bash
   # 브라우저에서 확인
   https://api.openalex.org/works?search=neural+network+backpropagation&filter=from_publication_date:1930-01-01,language:en,is_paratext:false,type:article&sort=relevance_score:desc&per_page=25
   ```

3. **TOKEN 병렬 검색 확인**
   ```python
   # openalex_client.py
   # tokens = ["neural network", "backpropagation", "gradient descent"]
   # search_str = "neural network backpropagation gradient descent"
   # → OpenAlex는 "AND" 검색 (모든 TOKEN 포함 논문만)
   ```

**판단 기준:**
- `📚 검색된 논문: 0개` → **OpenAlex API 문제** (TOKEN이 너무 구체적)
- `📚 검색된 논문: 25개` → `⚠️ min_score 이상인 논문이 없습니다` → **검증 문제** (min_score 낮추기)

### Q3: "TOKEN_MIN=2, TOKEN_MAX=4 병렬 검색에서 일치하는게 없어서?"

**아니요, TOKEN은 병렬 검색이 아닙니다!**

**잘못된 이해:**
```
❌ tokens = ["neural network", "backpropagation"]
❌ → "neural network" OR "backpropagation" (OR 검색)
```

**올바른 동작:**
```
✅ tokens = ["neural network", "backpropagation"]
✅ search_str = "neural network backpropagation"
✅ → "neural network AND backpropagation" (AND 검색)
```

**실제 처리:**
```python
# openalex_client.py, 라인 47-48
tokens = query.get("tokens", [])
search_str = " ".join(tokens)  # 공백으로 결합
```

**OpenAlex 검색 동작:**
- `search_str = "neural network backpropagation"`
- OpenAlex는 **모든 단어가 포함된 논문만** 반환 (AND 검색)
- TOKEN이 많을수록 검색 결과 **감소** (더 구체적)

**해결 방법:**
- `TOKEN_MIN=2`, `TOKEN_MAX=3`: 토큰 수 줄이기
- `sort_by=hybrid`: 연관성 높은 논문 중 인용수 높은 것 선택
- `year_from=2015`: 최근 논문으로 범위 좁히기

---

## 📊 실제 예시

### **예시 1: 성공 케이스 (검색 결과 있음)**

**입력:**
```python
request = OpenAlexRequest(
    lecture_id="lecture_1",
    section_id="section_3",
    section_summary="이 섹션에서는 Backpropagation 알고리즘의 원리와 gradient descent 최적화 방법을 다룹니다.",
    previous_summaries=[],
    rag_context=[],
    year_from=2015,
    top_k=3,
    verify_openalex=True,
    min_score=7.0
)
```

**처리:**
```
1. 쿼리 생성 (LLM)
   tokens=["backpropagation", "gradient descent", "neural network"]

2. OpenAlex API 호출
   search_str="backpropagation gradient descent neural network"
   year_from=2015
   📚 검색된 논문: 18개

3. 파싱 + 필터링
   초록 없음 + 인용 100 미만 제외 → 15개

4. 중복 제거 + 재랭킹
   상위 10개 선택 (CARD_LIMIT)

5. LLM 병렬 검증
   ✨ 병렬 LLM 검증 시작 (동시성: 5)
   ✅ 병렬 검증 완료: 10개
   
   결과 예시:
   - Paper 1: score=9.0, "Backpropagation 알고리즘을 다룬 핵심 논문"
   - Paper 2: score=8.5, "Gradient descent 최적화 방법 상세 설명"
   - Paper 3: score=7.8, "Neural network training 전반 다룸"

6. 점수 필터링 + 정렬
   min_score=7.0 이상: 8개 → top_k=3 반환

✅ 논문 추천 완료: 3개 (최고 점수: 9.0)
```

**출력:**
```json
[
  {
    "lecture_id": "lecture_1",
    "section_id": "section_3",
    "paper_info": {
      "title": "Efficient BackProp",
      "authors": ["Yann LeCun", "Léon Bottou", ...],
      "year": 2012,
      "citations": 15234,
      "url": "https://doi.org/...",
      "abstract": "We present a practical guide to..."
    },
    "reason": "Backpropagation 알고리즘의 효율적 구현을 다룬 핵심 논문",
    "score": 9.0
  },
  ...
]
```

### **예시 2: 실패 케이스 (검색 결과 없음)**

**입력:**
```python
request = OpenAlexRequest(
    lecture_id="lecture_2",
    section_id="section_5",
    section_summary="이번 섹션에서는 최신 AI 기술의 윤리적 쟁점을 논의합니다.",
    previous_summaries=[],
    rag_context=[],
    year_from=1930,  # ⚠️ 너무 오래됨
    top_k=3,
    verify_openalex=True,
    min_score=0.0
)
```

**처리:**
```
1. 쿼리 생성 (LLM)
   tokens=["AI ethics", "ethical issues", "artificial intelligence morality"]
   ⚠️ TOKEN이 너무 많고 구체적 (4개)

2. OpenAlex API 호출
   search_str="AI ethics ethical issues artificial intelligence morality"
   year_from=1930
   ⚠️ 모든 TOKEN이 동시에 포함된 논문이 없음
   📚 검색된 논문: 0개

❌ 논문 추천 실패: 검색 결과 없음
```

**해결:**
```python
# 설정 수정
request = OpenAlexRequest(
    year_from=2015,  # 최근 논문만
    min_score=7.0,   # 고품질 필터
    top_k=3,
    verify_openalex=True
)

# + prompts.py 수정 (TOKEN 범위 좁히기)
TOKEN_MIN = 2
TOKEN_MAX = 3  # 4 → 3
```

**재시도:**
```
1. 쿼리 생성 (LLM)
   tokens=["AI ethics", "artificial intelligence"]
   ✅ TOKEN 수 감소 (4 → 2)

2. OpenAlex API 호출
   search_str="AI ethics artificial intelligence"
   year_from=2015
   📚 검색된 논문: 42개

3-6. (중략)

✅ 논문 추천 완료: 3개 (최고 점수: 8.5)
```

---

## 🚀 최적화 팁

### **1. 빠른 응답이 필요할 때**
```python
# server/config.py
class OpenAlexSettings(BaseModel):
    verify: bool = Field(default=False)  # Heuristic 스코어링
    top_k: int = Field(default=3)

# cap1_openalex_module/openalexkit/config/openalex_config.py
CARD_LIMIT = 5  # 검증 대상 줄이기
PER_PAGE = 10   # API 호출 결과 줄이기
```

### **2. 고품질 논문만 필요할 때**
```python
# server/config.py
class OpenAlexSettings(BaseModel):
    verify: bool = Field(default=True)  # LLM 검증
    min_score: float = Field(default=7.0)  # 높은 임계값
    year_from: int = Field(default=2015)  # 최근 논문
```

### **3. 비용 절감이 필요할 때**
```python
# NO_SCORING 모드 활성화
# cap1_openalex_module/openalexkit/config/flags.py
NO_SCORING = True  # 검증 스킵

# 또는 Heuristic 스코어링
verify: bool = Field(default=False)
CARD_LIMIT = 5
```

### **4. 검색 결과 없음 해결**
```python
# 1. TOKEN 범위 줄이기
TOKEN_MIN = 2
TOKEN_MAX = 3  # 4 → 3

# 2. year_from 조정
year_from = 2015  # 1930 → 2015

# 3. min_score 낮추기
min_score = 7.0  # 9.0 → 7.0

# 4. sort_by 변경
sort_by = "hybrid"  # relevance → hybrid (연관성 + 인용수)
```

---

## 📝 요약

**OpenAlex 논문 추천 시스템**은 6단계로 동작합니다:

1. **쿼리 생성**: LLM이 섹션 요약 → 2-4개 학술 TOKEN 생성
2. **API 호출**: OpenAlex API로 논문 검색 (년도, 언어, 타입 필터)
3. **파싱**: 초록 역색인 변환, 저품질 논문 제거
4. **재랭킹**: 중복 제거 + 연관성 재평가 → 상위 10개 선택
5. **검증**: LLM 병렬 검증 (verify=True) 또는 Heuristic 스코어링 (verify=False)
6. **반환**: min_score 이상 + 점수 정렬 → top_k개 반환

**핵심 설정:**
- `year_from=2015`: 최근 논문 우선
- `min_score=7.0`: 고품질 필터
- `verify=True`: LLM 검증 (정확도 우선)
- `TOKEN_MIN=2, TOKEN_MAX=3`: 토큰 수 적절히 제한

**검색 결과 없음 해결:**
- TOKEN 범위 줄이기 (TOKEN_MAX=3)
- year_from 조정 (2015)
- min_score 낮추기 (7.0)
- sort_by 변경 (hybrid)
- 로그 분석 (어느 단계에서 실패?)

---

**작성일:** 2025년 11월 14일  
**버전:** 1.1  
**업데이트:** TOKEN_MAX: 4→3, MAX_TOKENS_SCORE: 120→200, VERIFY_CONCURRENCY: 5→20  
**관련 파일:**
- `cap1_openalex_module/openalexkit/service.py` (메인 로직)
- `cap1_openalex_module/openalexkit/llm/openai_client.py` (LLM 클라이언트)
- `cap1_openalex_module/openalexkit/api/openalex_client.py` (API 클라이언트)
- `cap1_openalex_module/openalexkit/config/prompts.py` (프롬프트)
- `server/config.py` (서버 설정)
