# QA Generate 동작 과정

## 📌 개요

`/qa/generate` 엔드포인트는 **Server-Sent Events (SSE) 스트리밍**을 사용하여 RAG (Retrieval-Augmented Generation) 기반 예상 질문을 생성합니다.

- **입력**: 강의 섹션의 요약 (section_summary)
- **동작**: RAG로 관련 청크 검색 → LLM으로 질문 생성
- **출력**: SSE 스트림 (qa_context → qa_partial × N → qa_complete)

---

## 🔄 전체 흐름도

```
[1] HTTP POST /qa/generate
         ↓
[2] QAGenerateRequest 검증 (Pydantic)
         ↓
[3] Collection ID 생성
         ↓
[4] RAG 검색 (retrieve)
    ├─ Vector DB에서 관련 청크 검색
    ├─ qa_retrieve_top_k 개수만큼 (기본 2개)
    └─ Score 내림차순 정렬
         ↓
[5] QARequest 구성
    ├─ section_summary (원본 요약)
    ├─ rag_context (검색된 청크들)
    ├─ num_questions (생성할 질문 수, 기본 3)
    └─ subject (과목명, 선택)
         ↓
[6] QAService.generate_questions_stream() 호출
    ├─ LLM 프롬프트 구성
    ├─ RAG 컨텍스트 주입
    └─ 스트리밍 생성 시작
         ↓
[7] SSE 이벤트 스트림 송신
    ├─ qa_context: RAG 청크 정보
    ├─ qa_partial: 각 질문 (JSON)
    └─ qa_complete: 종료 신호
         ↓
[8] 클라이언트 수신
```

---

## 🔍 단계별 상세 설명

### [1] HTTP POST /qa/generate

클라이언트가 `/qa/generate` 엔드포인트로 POST 요청을 보냅니다.

**요청 예시**:
```bash
curl -N -X POST "http://localhost:8000/qa/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "section_id": 1,
    "section_summary": "알고리즘의 효율성을 분석하는 방법...",
    "subject": "컴퓨터 과학"
  }'
```

**응답 타입**: `text/event-stream` (SSE)

---

### [2] QAGenerateRequest 검증 (Pydantic)

FastAPI가 요청 바디를 `QAGenerateRequest` 모델로 검증합니다.

**QAGenerateRequest 스키마**:
```python
class QAGenerateRequest(BaseModel):
    lecture_id: str          # 강의 ID (필수)
    section_id: int          # 섹션 번호 (필수)
    section_summary: str     # 섹션 요약 (필수)
    subject: Optional[str]   # 과목명 (선택)
```

**검증 사항**:
- `lecture_id`: 비어있지 않은 문자열
- `section_id`: 양의 정수
- `section_summary`: 비어있지 않은 문자열
- `subject`: 선택적 문자열

---

### [3] Collection ID 생성

RAG Vector DB의 컬렉션 ID를 생성합니다.

**코드** (`server/routes/qa.py`, 라인 45):
```python
collection_id = build_collection_id(
    prefix=settings.rag.collection_prefix,  # "lecture"
    lecture_id=request.lecture_id           # "cs101"
)
# 결과: "lecture_cs101"
```

**Collection ID 규칙**:
- 형식: `{prefix}_{lecture_id}`
- 예시: `lecture_cs101`, `lecture_math201`
- 각 강의별로 독립적인 Vector DB 컬렉션

---

### [4] RAG 검색 (retrieve)

RAG Service를 사용하여 관련 청크를 검색합니다.

**코드** (`server/routes/qa.py`, 라인 47-70):
```python
def _retrieve():
    return rag_service.retrieve(
        collection_id=collection_id,        # "lecture_cs101"
        query=request.section_summary,      # 섹션 요약 (검색 쿼리)
        top_k=settings.rag.qa_retrieve_top_k  # 2 (기본값)
    )

# 비동기 실행
rag_chunks = await asyncio.to_thread(_retrieve)
```

**RAG Service retrieve 함수** (`cap1_RAG_module/ragkit/service.py`, 라인 239):
```python
def retrieve(
    self,
    collection_id: str,
    query: str,
    top_k: int = 3,
    filters: Optional[Dict[str, str]] = None
) -> List[RetrievedChunk]:
    """
    Vector DB에서 관련 청크 검색
    
    Returns:
        List[RetrievedChunk]: score 내림차순 정렬된 청크 리스트
    """
```

**RetrievedChunk 구조**:
```python
class RetrievedChunk:
    text: str           # 청크 텍스트
    score: float        # 유사도 점수 (높을수록 관련성 높음)
    metadata: dict      # 메타데이터 (section_id, subject 등)
```

**검색 프로세스**:
1. **임베딩 생성**: `query` (section_summary)를 OpenAI Embedding API로 벡터화
2. **벡터 검색**: ChromaDB에서 코사인 유사도 기반 검색
3. **Top-K 선택**: `qa_retrieve_top_k`개 청크 선택 (기본 2개)
4. **정렬**: Score 내림차순 정렬

**로깅 출력** (디버깅용):
```
🔍 RAG 검색 결과 (collection_id=lecture_cs101)
📝 Query: 알고리즘의 효율성을 분석하는 방법...
📊 Retrieved 2 chunks (top_k=2)
================================================================================
[Chunk 1] Score: 0.8542
Text: 알고리즘 시간 복잡도는 Big-O 표기법으로 표현합니다...
Metadata: {'section_id': '1', 'subject': '컴퓨터 과학'}

[Chunk 2] Score: 0.7821
Text: O(n)은 선형 시간 복잡도를 의미합니다...
Metadata: {'section_id': '2', 'difficulty': 'intermediate'}
```

---

### [5] QARequest 구성

QA Service에 전달할 `QARequest` 객체를 구성합니다.

**코드** (`server/routes/qa.py`, 라인 72-76):
```python
qa_req = QARequest(
    section_summary=request.section_summary,  # 원본 요약
    rag_context=rag_chunks,                   # 검색된 청크들 (List[RetrievedChunk])
    num_questions=settings.qa.num_questions,  # 생성할 질문 수 (기본 3)
    subject=request.subject                   # 과목명 (선택)
)
```

**QARequest 스키마**:
```python
class QARequest(BaseModel):
    section_summary: str                # 섹션 요약 (원본)
    rag_context: List[RetrievedChunk]   # RAG 검색 결과
    num_questions: int = 3              # 생성할 질문 수
    subject: Optional[str] = None       # 과목명
```

**rag_context의 역할**:
- LLM 프롬프트에 **추가 컨텍스트**로 주입
- 섹션 요약만으로 부족한 정보를 RAG로 보완
- 더 정확하고 구체적인 질문 생성 가능

---

### [6] QAService.generate_questions_stream() 호출

QA Service를 사용하여 질문 생성 스트림을 시작합니다.

**코드** (`server/routes/qa.py`, 라인 80):
```python
async for event in qa_service.generate_questions_stream(qa_req):
    yield event
```

**QAService 내부 동작** (`cap1_QA_module/qakit/service.py`):

1. **프롬프트 구성**:
   ```python
   # 시스템 프롬프트
   system_prompt = f"""당신은 학습 자료를 분석하여 예상 질문을 생성하는 전문가입니다.
   과목: {request.subject or '일반'}
   섹션 요약:
   {request.section_summary}
   
   참고 자료 (RAG 컨텍스트):
   {format_rag_context(request.rag_context)}
   
   {request.num_questions}개의 질문을 생성하세요.
   """
   ```

2. **RAG 컨텍스트 포맷팅**:
   ```python
   def format_rag_context(rag_chunks):
       context = ""
       for i, chunk in enumerate(rag_chunks, 1):
           context += f"\n[참고 {i}] (Score: {chunk.score:.2f})\n"
           context += f"{chunk.text}\n"
       return context
   ```

3. **LLM 스트리밍 호출**:
   ```python
   async for chunk in llm_client.stream_chat_completion(
       messages=[{"role": "system", "content": system_prompt}],
       response_format={"type": "json_object"}
   ):
       # JSON 파싱 및 이벤트 생성
   ```

---

### [7] SSE 이벤트 스트림 송신

Server-Sent Events (SSE) 형식으로 클라이언트에 스트리밍합니다.

**이벤트 타입**:

#### 1) `qa_context` (첫 번째 이벤트)
RAG 검색 결과를 전송합니다.

```
event: qa_context
data: {
  "rag_chunks": [
    {
      "text": "알고리즘 시간 복잡도는...",
      "score": 0.8542,
      "metadata": {"section_id": "1", "subject": "컴퓨터 과학"}
    },
    {
      "text": "O(n)은 선형 시간...",
      "score": 0.7821,
      "metadata": {"section_id": "2"}
    }
  ]
}
```

#### 2) `qa_partial` (각 질문마다)
생성된 질문을 하나씩 전송합니다.

```
event: qa_partial
data: {
  "question_id": 1,
  "question_text": "Big-O 표기법이란 무엇인가요?",
  "answer_text": "Big-O 표기법은 알고리즘의 시간 복잡도를...",
  "difficulty": "easy"
}

event: qa_partial
data: {
  "question_id": 2,
  "question_text": "O(n)과 O(n^2)의 차이는?",
  "answer_text": "O(n)은 입력 크기에 비례하지만...",
  "difficulty": "medium"
}

event: qa_partial
data: {
  "question_id": 3,
  "question_text": "최악의 시간 복잡도를 가진 정렬 알고리즘은?",
  "answer_text": "버블 소트는 O(n^2)로...",
  "difficulty": "hard"
}
```

#### 3) `qa_complete` (마지막 이벤트)
스트림 종료 신호입니다.

```
event: qa_complete
data: {"status": "done", "total_questions": 3}
```

**코드** (`server/routes/qa.py`, 라인 78-84):
```python
@router.post("/generate", response_class=StreamingResponse)
async def generate_qa(request: QAGenerateRequest):
    # ... RAG 검색 ...
    
    async def event_stream():
        async for event in qa_service.generate_questions_stream(qa_req):
            yield event
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

---

### [8] 클라이언트 수신

클라이언트는 SSE 스트림을 수신하여 실시간으로 처리합니다.

**JavaScript 예시**:
```javascript
const eventSource = new EventSource('/qa/generate');

// RAG 컨텍스트 수신
eventSource.addEventListener('qa_context', (event) => {
  const data = JSON.parse(event.data);
  console.log('RAG Chunks:', data.rag_chunks);
});

// 각 질문 수신
eventSource.addEventListener('qa_partial', (event) => {
  const question = JSON.parse(event.data);
  displayQuestion(question);
});

// 완료 신호
eventSource.addEventListener('qa_complete', (event) => {
  console.log('QA 생성 완료');
  eventSource.close();
});
```

---

## 📊 RAG 검색 상세

### qa_retrieve_top_k 설정

**설정 파일** (`server/config.py`):
```python
class RAGConfig(BaseModel):
    qa_retrieve_top_k: int = Field(default=2, description="QA 생성 시 RAG 검색 개수")
```

**환경 변수**:
```bash
# .env
QA_RETRIEVE_TOP_K=2  # 기본값
```

**의미**:
- QA 생성 시 RAG에서 **2개 청크**를 검색
- Score가 높은 순서대로 선택
- 더 많은 청크 = 더 풍부한 컨텍스트 vs 더 많은 토큰 비용

### Score 계산

**ChromaDB 벡터 검색**:
1. Query 임베딩 벡터: `q` (3072차원)
2. 청크 임베딩 벡터: `c` (3072차원)
3. 코사인 유사도: `score = cos(q, c) = (q · c) / (|q| × |c|)`
4. 범위: -1 ~ 1 (1에 가까울수록 유사)

**Score 해석**:
- **0.9 이상**: 매우 관련성 높음
- **0.7 ~ 0.9**: 관련성 있음
- **0.5 ~ 0.7**: 다소 관련성
- **0.5 미만**: 관련성 낮음

---

## 🎯 실제 예시

### 예시 1: CS101 알고리즘 시간 복잡도

**입력**:
```json
{
  "lecture_id": "cs101",
  "section_id": 1,
  "section_summary": "알고리즘의 효율성을 분석하는 방법에 대해 학습합니다. Big-O 표기법을 사용하여 시간 복잡도를 표현하며, O(1), O(log n), O(n), O(n log n), O(n^2) 등 다양한 복잡도를 비교합니다.",
  "subject": "컴퓨터 과학"
}
```

**RAG 검색 결과**:
```python
[
  RetrievedChunk(
    text="알고리즘 시간 복잡도는 입력 크기 n에 대한 실행 시간을 나타냅니다. Big-O 표기법으로 최악의 경우를 표현합니다.",
    score=0.8542,
    metadata={"section_id": "1", "id": "algo_complexity"}
  ),
  RetrievedChunk(
    text="O(n)은 선형 시간 복잡도로, 입력 크기에 비례하여 실행 시간이 증가합니다.",
    score=0.7821,
    metadata={"section_id": "2", "difficulty": "intermediate"}
  )
]
```

**생성된 질문**:
```json
[
  {
    "question_id": 1,
    "question_text": "Big-O 표기법이란 무엇인가요?",
    "answer_text": "Big-O 표기법은 알고리즘의 시간 복잡도를 표현하는 방법으로, 최악의 경우 실행 시간을 나타냅니다.",
    "difficulty": "easy"
  },
  {
    "question_id": 2,
    "question_text": "O(n)과 O(n^2)의 차이를 설명하세요.",
    "answer_text": "O(n)은 입력 크기에 비례하여 선형적으로 증가하지만, O(n^2)는 제곱으로 증가하여 훨씬 느립니다.",
    "difficulty": "medium"
  },
  {
    "question_id": 3,
    "question_text": "시간 복잡도 O(1), O(log n), O(n), O(n log n), O(n^2)를 효율성 순으로 나열하세요.",
    "answer_text": "O(1) > O(log n) > O(n) > O(n log n) > O(n^2) 순으로 효율적입니다.",
    "difficulty": "hard"
  }
]
```

---

### 예시 2: MATH201 미적분 도함수

**입력**:
```json
{
  "lecture_id": "math201",
  "section_id": 1,
  "section_summary": "도함수는 함수의 순간 변화율을 나타냅니다. 극한의 개념을 사용하여 정의하며, 미분 계수를 계산하는 다양한 공식을 학습합니다.",
  "subject": "수학"
}
```

**RAG 검색 결과**:
```python
[
  RetrievedChunk(
    text="f(x)의 도함수는 lim(h→0) [f(x+h)-f(x)]/h로 정의됩니다.",
    score=0.9123,
    metadata={"section_id": "1", "id": "calc_derivative"}
  ),
  RetrievedChunk(
    text="미분 공식: d/dx(x^n) = n*x^(n-1)",
    score=0.8456,
    metadata={"section_id": "1", "subject": "수학"}
  )
]
```

**생성된 질문**:
```json
[
  {
    "question_id": 1,
    "question_text": "도함수의 정의를 수식으로 나타내세요.",
    "answer_text": "f'(x) = lim(h→0) [f(x+h)-f(x)]/h",
    "difficulty": "easy"
  },
  {
    "question_id": 2,
    "question_text": "x^3의 도함수를 구하세요.",
    "answer_text": "d/dx(x^3) = 3*x^2",
    "difficulty": "medium"
  },
  {
    "question_id": 3,
    "question_text": "도함수가 0인 점의 의미는 무엇인가요?",
    "answer_text": "극값 또는 변곡점을 나타낼 수 있습니다.",
    "difficulty": "hard"
  }
]
```

---

## 🔧 설정 값

### RAG 설정 (config.py)

```python
class RAGConfig(BaseModel):
    collection_prefix: str = "lecture"        # 컬렉션 접두사
    qa_retrieve_top_k: int = 2                # QA 생성 시 검색 개수
    persist_dir: str = "server_storage/chroma_data"  # ChromaDB 저장 경로
```

### QA 설정 (config.py)

```python
class QAConfig(BaseModel):
    num_questions: int = 3                    # 생성할 질문 수
    model: str = "gpt-4o-mini"                # 사용 LLM 모델
    temperature: float = 0.7                  # 생성 다양성
```

### 환경 변수 (.env)

```bash
# RAG 설정
RAG_PERSIST_DIR=server_storage/chroma_data
QA_RETRIEVE_TOP_K=2

# QA 설정
NUM_QUESTIONS=3
QA_MODEL=gpt-4o-mini
QA_TEMPERATURE=0.7

# OpenAI API
OPENAI_API_KEY=your_api_key_here
```

---

## ❓ FAQ

### Q1: RAG 검색 개수를 늘리면 어떻게 되나요?

**A**: `qa_retrieve_top_k`를 늘리면 (예: 2 → 5):
- **장점**: 더 풍부한 컨텍스트, 더 정확한 질문 생성
- **단점**: LLM 입력 토큰 증가 → 비용 증가, 응답 시간 증가

**권장값**:
- 짧은 섹션: 2개
- 긴 섹션: 3~5개
- 매우 긴 섹션: 5~10개

---

### Q2: RAG 검색이 실패하면 어떻게 되나요?

**A**: RAG 검색 실패 시:
1. `rag_chunks = []` (빈 리스트)
2. QARequest의 `rag_context`가 빈 리스트
3. LLM이 `section_summary`만으로 질문 생성
4. 여전히 질문은 생성되지만, 정확도가 떨어질 수 있음

**에러 처리** (`server/routes/qa.py`, 라인 58-61):
```python
except Exception as e:
    print(f"❌ RAG 검색 실패: {e}")
    rag_chunks = []  # 빈 리스트로 계속 진행
```

---

### Q3: 같은 section_summary로 여러 번 요청하면?

**A**:
- **RAG 검색 결과**: 동일 (같은 쿼리 → 같은 벡터 → 같은 청크)
- **생성된 질문**: 다를 수 있음 (LLM temperature > 0)

**재현 가능하게 하려면**:
```python
# .env
QA_TEMPERATURE=0  # 완전 결정적
```

---

### Q4: 특정 메타데이터로 필터링 가능한가요?

**A**: 현재 구현에서는 지원하지 않지만, 추가 가능합니다.

**수정 예시**:
```python
# server/routes/qa.py
rag_chunks = rag_service.retrieve(
    collection_id=collection_id,
    query=request.section_summary,
    top_k=settings.rag.qa_retrieve_top_k,
    filters={"difficulty": "easy"}  # 쉬운 문제만 검색
)
```

---

### Q5: SSE 대신 일반 JSON 응답으로 받을 수 있나요?

**A**: 가능합니다. 별도 엔드포인트를 추가하면 됩니다.

**새 엔드포인트 예시**:
```python
@router.post("/generate-sync")
async def generate_qa_sync(request: QAGenerateRequest):
    # RAG 검색
    rag_chunks = await asyncio.to_thread(...)
    
    # 질문 생성 (스트림 없이)
    questions = await qa_service.generate_questions(qa_req)
    
    return {
        "rag_chunks": rag_chunks,
        "questions": questions
    }
```

---

### Q6: RAG 청크의 Score가 너무 낮으면?

**A**: Score 임계값을 설정하여 필터링할 수 있습니다.

**수정 예시**:
```python
# server/routes/qa.py
MIN_SCORE = 0.5

rag_chunks = [
    chunk for chunk in rag_chunks 
    if chunk.score >= MIN_SCORE
]

if not rag_chunks:
    print("⚠️ 관련성 높은 청크 없음")
```

---

### Q7: 여러 강의를 동시에 검색할 수 있나요?

**A**: 현재는 단일 강의만 지원합니다. 여러 강의를 검색하려면:

**방법 1**: 여러 컬렉션 검색 후 병합
```python
cs101_chunks = rag_service.retrieve("lecture_cs101", query, top_k=1)
math201_chunks = rag_service.retrieve("lecture_math201", query, top_k=1)
rag_chunks = cs101_chunks + math201_chunks
```

**방법 2**: 통합 컬렉션 생성
```python
# 모든 강의를 "lecture_all" 컬렉션에 업서트
# metadata에 lecture_id 추가
```

---

## 📋 요약

1. **입력**: `lecture_id`, `section_id`, `section_summary`, `subject`
2. **RAG 검색**: Vector DB에서 `qa_retrieve_top_k`개 청크 검색 (기본 2개)
3. **LLM 생성**: RAG 컨텍스트 + 섹션 요약으로 질문 생성
4. **SSE 스트림**: `qa_context` → `qa_partial` × N → `qa_complete`
5. **설정**: `.env`에서 `QA_RETRIEVE_TOP_K`, `NUM_QUESTIONS` 조정 가능

**핵심 포인트**:
- RAG로 **더 정확한 질문** 생성
- SSE로 **실시간 스트리밍**
- `qa_retrieve_top_k`로 **검색 개수 조정**
- Score로 **관련성 측정**

---

## 🧪 테스트 방법

### 1. 서버 로그 확인

```bash
# 서버 시작
uvicorn server.main:app --reload

# RAG 검색 결과가 콘솔에 출력됨 (라인 47-70 로깅)
```

### 2. 테스트 스크립트 실행

```bash
# verify_test/test_qa_rag.sh 실행
./verify_test/test_qa_rag.sh

# 4개 테스트 케이스 실행 (cs101 × 2, math201 × 2)
# 각 요청마다 RAG 검색 결과가 서버 콘솔에 출력됨
```

### 3. 수동 테스트

```bash
# 단일 요청 테스트
curl -N -X POST "http://localhost:8000/qa/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "section_id": 1,
    "section_summary": "알고리즘 효율성 분석...",
    "subject": "컴퓨터 과학"
  }'
```

---

## 📚 관련 문서

- [RAG_TEXT_UPSERT_동작과정.md](./RAG_TEXT_UPSERT_동작과정.md): RAG 업서트 프로세스
- [API_specification.md](./API_specification.md): 전체 API 명세
- [server/routes/qa.py](./server/routes/qa.py): QA 엔드포인트 구현
- [cap1_QA_module/qakit/service.py](./cap1_QA_module/qakit/service.py): QA Service 구현
- [cap1_RAG_module/ragkit/service.py](./cap1_RAG_module/ragkit/service.py): RAG Service 구현
