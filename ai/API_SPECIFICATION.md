# LiveNote AI Gateway - API 명세서

## 목차
- [1. Health 체크](#1-health-체크)
- [2. RAG 업서트](#2-rag-업서트)
  - [2.1 PDF 업서트](#21-pdf-업서트)
  - [2.2 텍스트 업서트](#22-텍스트-업서트)
- [3. QA 생성](#3-qa-생성)
- [4. REC 추천](#4-rec-추천)
- [5. 공통 사항](#5-공통-사항)

---

## 1. Health 체크

### 형식
- **Content-Type**: N/A (요청 본문 없음)

### HTTP 메서드
```
GET /health
```

### 본문 예시
요청 본문 없음

### 입력 필드 설명
입력 필드 없음

### 출력 필드 설명

| 필드명 | 타입 | 설명 |
|--------|------|------|
| status | string | 서버 상태. 정상일 경우 `"ok"` |

### 응답

**예시 1: 정상 응답**
```json
{
  "status": "ok"
}
```

**예시 2: 서버 오류 (500)**
```json
{
  "detail": "Internal Server Error"
}
```

### 주의 사항
- 서버가 실행 중이지 않으면 연결 거부 오류가 발생합니다
- 이 엔드포인트는 인증이 필요 없습니다

### 참고
- 로드 밸런서나 모니터링 도구에서 헬스 체크용으로 사용됩니다
- 응답 시간이 느리면 서버 과부하 상태일 수 있습니다

---

## 2. RAG 업서트

### 2.1 PDF 업서트

#### 형식
- **Content-Type**: `multipart/form-data`

#### HTTP 메서드
```
POST /rag/pdf-upsert
```

#### 본문 예시

**예시 1: 기본 PDF 업로드**
```
lecture_id: "lec-001"
file: [PDF 파일 바이너리]
```

**예시 2: 메타데이터 포함 업로드**
```
lecture_id: "lec-002"
file: [PDF 파일 바이너리]
base_metadata: {"subject": "데이터구조", "professor": "홍길동", "year": 2024}
```

#### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | 강의를 식별하는 고유 ID. 공백 포함 불가, 영문/숫자/하이픈 권장 |
| file | file (PDF) | 예 | 업로드할 PDF 파일. 최대 크기는 서버 설정에 따름 |
| base_metadata | string(JSON) | 아니오 | 모든 페이지에 공통으로 적용할 메타데이터. JSON 문자열 형식 |

#### 출력 필드 설명

| 필드명 | 타입 | 설명 |
|--------|------|------|
| collection_id | string | 저장된 Chroma 컬렉션 이름. 형식: `lecture_<lecture_id>` |
| result.collection_id | string | 실제 업서트된 컬렉션 ID (확인용) |
| result.count | int | 업서트된 PDF 페이지 수 |
| result.embedding_dim | int | 임베딩 벡터 차원 (OpenAI text-embedding-3-large: 3072) |

#### 응답

**예시 1: 성공 응답 (3페이지 PDF)**
```json
{
  "collection_id": "lecture_lec-001",
  "result": {
    "collection_id": "lecture_lec-001",
    "count": 3,
    "embedding_dim": 3072
  }
}
```

**예시 2: 성공 응답 (10페이지 PDF, 메타데이터 포함)**
```json
{
  "collection_id": "lecture_lec-002",
  "result": {
    "collection_id": "lecture_lec-002",
    "count": 10,
    "embedding_dim": 3072
  }
}
```

#### 주의 사항
- PDF 파일이 아닌 경우 HTTP 400 오류 발생
- 빈 PDF 파일 업로드 시 HTTP 400 오류 발생
- `base_metadata`가 올바른 JSON 형식이 아니면 HTTP 400 오류 발생
- 동일한 `lecture_id`로 재업로드 시 기존 데이터를 덮어씁니다
- 텍스트가 없는 이미지 PDF는 추출 결과가 없을 수 있습니다

#### 참고
- PDF 추출에는 `PyMuPDF(fitz)` 라이브러리를 사용합니다
- 각 페이지는 별도 청크로 저장되며 `page` 메타데이터가 자동 부여됩니다
- 대용량 PDF (100페이지 이상)는 처리 시간이 길어질 수 있습니다
- 암호화된 PDF는 지원하지 않습니다

---

### 2.2 텍스트 업서트

#### 형식
- **Content-Type**: `application/json`

#### HTTP 메서드
```
POST /rag/text-upsert
```

#### 본문 예시

**예시 1: 기본 텍스트 업로드**
```json
{
  "lecture_id": "001",
  "items": [
    {"text": "스택은 LIFO(Last In First Out) 구조입니다."},
    {"text": "큐는 FIFO(First In First Out) 구조입니다."}
  ]
}
```

**예시 2: 메타데이터 포함 업로드**
```json
{
  "lecture_id": "002",
  "items": [
    {
      "text": "이진 탐색 트리는 각 노드가 최대 2개의 자식을 갖습니다.",
      "section_id": "1",
      "metadata": {"topic": "트리", "difficulty": "중"}
    },
    {
      "text": "AVL 트리는 자가 균형 이진 탐색 트리입니다.",
      "section_id": "2",
      "metadata": {"topic": "트리", "difficulty": "상"}
    }
  ]
}
```

#### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | 강의 ID. PDF 업서트와 동일한 ID 사용 시 동일 컬렉션에 저장됨 |
| items | array | 예 | 업서트할 텍스트 항목 배열. 최소 1개 이상 |
| items[].text | string | 예 | 저장할 텍스트 내용. 최소 10자 권장 |
| items[].id | string | 아니오 | 사용자 정의 문서 ID. 없으면 `uuid4()` 자동 생성 |
| items[].section_id | string | 아니오 | 섹션 ID. metadata에 `section_id` 키로 자동 병합됨 |
| items[].metadata | object | 아니오 | 추가 메타데이터. 없으면 `{"source": "text"}` 자동 부여 |

#### 출력 필드 설명

| 필드명 | 타입 | 설명 |
|--------|------|------|
| collection_id | string | 저장된 컬렉션 ID. 형식: `lecture_<lecture_id>` |
| result.collection_id | string | 실제 업서트된 컬렉션 ID (확인용) |
| result.count | int | 업서트된 텍스트 문서 수 |
| result.embedding_dim | int | 임베딩 벡터 차원 (OpenAI text-embedding-3-large: 3072) |

#### 응답

**예시 1: 성공 응답 (2개 항목)**
```json
{
  "collection_id": "lecture_001",
  "result": {
    "collection_id": "lecture_001",
    "count": 2,
    "embedding_dim": 3072
  }
}
```

**예시 2: 성공 응답 (메타데이터 포함, 5개 항목)**
```json
{
  "collection_id": "lecture_002",
  "result": {
    "collection_id": "lecture_002",
    "count": 5,
    "embedding_dim": 3072
  }
}
```

#### 주의 사항
- `items` 배열이 비어있으면 HTTP 400 오류 발생
- `text` 필드가 비어있거나 너무 짧으면 임베딩 품질이 낮아질 수 있습니다
- 동일한 `lecture_id`로 여러 번 호출 시 기존 데이터에 추가됩니다 (덮어쓰지 않음)
- `metadata`가 비어있으면 자동으로 `{"source": "text"}` 부여
- `section_id` 값은 metadata에도 병합되어 저장됩니다

#### 참고
- 텍스트 업서트는 PDF 업서트보다 훨씬 빠릅니다
- STT(음성→텍스트) 결과나 강의 요약을 저장하는 용도로 적합합니다
- 메타데이터는 추후 필터링 검색에 활용할 수 있습니다
- 대량 업서트 시 배치 크기는 100~200개 권장 (메모리 효율)

---

## 3. QA 생성

### 형식
- **Content-Type**: `application/json`
- **Response**: `text/event-stream` (SSE)

### HTTP 메서드
```
POST /qa/generate
```

### 본문 예시

**예시 1: 기본 QA 생성**
```json
{
  "lecture_id": "001",
  "section_id": 1,
  "section_summary": "스택과 큐의 차이점을 설명하고, 각각의 사용 사례를 다룹니다."
}
```

**예시 2: 과목 정보 포함 QA 생성**
```json
{
  "lecture_id": "002",
  "section_id": 3,
  "section_summary": "이진 탐색 트리의 삽입, 삭제, 검색 연산을 구현하고 시간 복잡도를 분석합니다.",
  "subject": "자료구조"
}
```

### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | RAG 컬렉션과 매핑되는 강의 ID. 사전에 업서트된 ID여야 함 |
| section_id | int | 예 | 섹션 번호. 1 이상의 정수 |
| section_summary | string | 예 | 섹션 요약 내용. 최소 10자 이상 권장 |
| subject | string | 아니오 | 과목 정보 (예: "자료구조", "운영체제"). 질문 생성 시 컨텍스트로 활용 |

### 출력 이벤트 설명

| 이벤트 타입 | 주요 필드 | 설명 |
|------------|-----------|------|
| qa_context | collection_id, chunk_count | QA 생성 전 사용된 컬렉션 ID 및 검색된 청크 수 |
| qa_partial | type, qa{question, answer}, index | 각 질문 유형별 생성 결과. 완료 순서대로 전송 |
| qa_error | type, error | 특정 유형 생성 실패 시 오류 정보 |
| qa_complete | total, duration_ms | 전체 생성 완료. 생성된 질문 수와 총 소요 시간 |

### 응답

**예시 1: 정상 SSE 스트림 (3개 질문 생성)**
```
event: qa_context
data: {"event":"context_ready","collection_id":"lecture_001","chunk_count":2}

event: qa_partial
data: {"type":"개념","qa":{"type":"개념","question":"스택과 큐의 주요 차이점은 무엇인가요?","answer":"스택은 LIFO(Last In First Out) 방식으로 마지막에 들어간 데이터가 먼저 나오는 구조이고, 큐는 FIFO(First In First Out) 방식으로 먼저 들어간 데이터가 먼저 나오는 구조입니다."},"index":1}

event: qa_partial
data: {"type":"응용","qa":{"type":"응용","question":"웹 브라우저의 뒤로가기 기능은 스택과 큐 중 어느 자료구조를 사용하나요?","answer":"웹 브라우저의 뒤로가기 기능은 스택을 사용합니다. 가장 최근에 방문한 페이지부터 역순으로 돌아가야 하므로 LIFO 구조가 적합합니다."},"index":2}

event: qa_partial
data: {"type":"심화","qa":{"type":"심화","question":"우선순위 큐를 구현할 때 힙(Heap) 자료구조를 사용하는 이유는 무엇인가요?","answer":"힙은 삽입과 삭제 연산이 O(log n) 시간 복잡도를 가지므로, 우선순위 큐의 핵심 연산인 최댓값/최솟값 추출을 효율적으로 수행할 수 있습니다."},"index":3}

event: qa_complete
data: {"total":3,"duration_ms":4521}
```

**예시 2: 일부 실패 포함 SSE 스트림**
```
event: qa_context
data: {"event":"context_ready","collection_id":"lecture_002","chunk_count":3}

event: qa_partial
data: {"type":"개념","qa":{"type":"개념","question":"이진 탐색 트리의 정의는 무엇인가요?","answer":"이진 탐색 트리는 각 노드가 최대 2개의 자식을 가지며, 왼쪽 서브트리의 모든 값은 부모 노드보다 작고 오른쪽 서브트리의 모든 값은 부모 노드보다 큰 특성을 만족하는 트리입니다."},"index":1}

event: qa_error
data: {"type":"응용","error":"OpenAI API rate limit exceeded"}

event: qa_partial
data: {"type":"심화","qa":{"type":"심화","question":"AVL 트리에서 회전(Rotation) 연산이 필요한 이유는 무엇인가요?","answer":"AVL 트리는 모든 노드의 왼쪽과 오른쪽 서브트리 높이 차이가 1 이하여야 하는 균형 조건을 유지해야 합니다. 회전 연산은 삽입/삭제 후 이 균형을 복구하는 데 사용됩니다."},"index":2}

event: qa_complete
data: {"total":2,"duration_ms":5128}
```

### 주의 사항
- `lecture_id`에 해당하는 컬렉션이 없으면 HTTP 404 오류 발생
- `section_summary`가 10자 미만이면 품질 낮은 질문이 생성될 수 있습니다
- 질문 유형 순서는 LLM 응답 속도에 따라 달라지며 보장되지 않습니다
- OpenAI API 오류 시 일부 질문만 생성될 수 있습니다 (qa_error 이벤트 확인)
- SSE 연결이 끊기면 클라이언트에서 재시도 로직 구현 필요

### 참고
- 질문 유형은 `server/config.py`의 `QASettings.question_types`에서 설정 (기본: 개념/응용/심화)
- 생성되는 질문 수는 `qa_top_k` 설정으로 조정 가능 (기본: 3개)
- RAG 검색에 사용되는 청크 수는 `RAGSettings.qa_retrieve_top_k`로 조정 (기본: 2개)
- 비동기 처리로 여러 질문을 동시에 생성하므로 순차 생성보다 빠릅니다

---

## 4. REC 추천

### 형식
- **Content-Type**: `application/json`
- **Response**: `text/event-stream` (SSE)

### HTTP 메서드
```
POST /rec/recommend
```

### 본문 예시

**예시 1: 기본 추천 요청**
```json
{
  "lecture_id": "001",
  "section_id": 1,
  "section_summary": "스택과 큐의 차이점을 설명하고 활용 사례를 다룹니다.",
  "previous_summaries": [],
  "yt_exclude": [],
  "wiki_exclude": [],
  "paper_exclude": [],
  "google_exclude": []
}
```

**예시 2: 이전 섹션 및 제외 항목 포함 요청**
```json
{
  "lecture_id": "002",
  "section_id": 3,
  "section_summary": "이진 탐색 트리의 삽입, 삭제, 검색 연산을 구현합니다.",
  "previous_summaries": [
    {"section_id": 1, "summary": "트리의 기본 개념과 용어"},
    {"section_id": 2, "summary": "이진 트리의 순회 방법"}
  ],
  "yt_exclude": ["Binary Search Tree Basics"],
  "wiki_exclude": ["이진 트리"],
  "paper_exclude": ["W2103456789"],
  "google_exclude": ["https://example.com/old-tutorial"]
}
```

### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | RAG 컬렉션과 매핑되는 강의 ID. 사전에 업서트된 ID여야 함 |
| section_id | int | 예 | 섹션 번호. 1 이상의 정수 |
| section_summary | string | 예 | 현재 섹션 요약 내용 |
| previous_summaries | array | 아니오 | 이전 섹션 요약 목록. `section_id`는 1 이상이어야 함 |
| yt_exclude | array[string] | 아니오 | 추천에서 제외할 유튜브 영상 제목 목록 |
| wiki_exclude | array[string] | 아니오 | 추천에서 제외할 위키피디아 문서 제목 목록 |
| paper_exclude | array[string] | 아니오 | 추천에서 제외할 논문 ID(OpenAlex ID) 목록 |
| google_exclude | array[string] | 아니오 | 추천에서 제외할 구글 검색 결과 URL 목록 |

### 출력 이벤트 설명

| 이벤트 타입 | 주요 필드 | 설명 |
|------------|-----------|------|
| rec_context | collection_id, chunk_count | 추천 생성 전 사용된 컬렉션 ID 및 검색된 청크 수 |
| rec_partial | source, count, items[], elapsed_ms | 각 Provider의 추천 결과. 완료 순서대로 전송 (source: openalex/wiki/youtube/google) |
| rec_error | source, error, elapsed_ms | 특정 Provider 실패 시 오류 정보 |
| rec_complete | completed_sources, duration_ms | 전체 완료. 성공한 Provider 수와 총 소요 시간 |

**items[] 구조 (Provider별 차이)**:
- **OpenAlex**: `{id, title, authors, year, cited_by_count, publication_date, url, abstract, score, reason}`
- **Wikipedia**: `{title, url, language, extract, score, reason}`
- **YouTube**: `{video_id, title, channel_title, published_at, view_count, url, description, score, reason}`
- **Google**: `{title, url, snippet, score, reason}`

### 응답

**예시 1: 정상 SSE 스트림 (4개 Provider 모두 성공)**
```
event: rec_context
data: {"event":"context_ready","collection_id":"lecture_001","chunk_count":3}

event: rec_partial
data: {"source":"wiki","count":2,"items":[{"title":"스택 (자료 구조)","url":"https://ko.wikipedia.org/wiki/%EC%8A%A4%ED%83%9D_(%EC%9E%90%EB%A3%8C_%EA%B5%AC%EC%A1%B0)","language":"ko","extract":"스택(stack)은 제한적으로 접근할 수 있는 나열 구조이다...","score":85.5,"reason":"스택의 개념과 구현을 잘 설명함"},{"title":"큐 (자료 구조)","url":"https://ko.wikipedia.org/wiki/%ED%81%90_(%EC%9E%90%EB%A3%8C_%EA%B5%AC%EC%A1%B0)","language":"ko","extract":"큐(queue)는 컴퓨터의 기본적인 자료 구조의 한가지로...","score":82.0,"reason":"큐의 기본 개념과 활용 사례 포함"}],"elapsed_ms":1234}

event: rec_partial
data: {"source":"youtube","count":2,"items":[{"video_id":"XYZ123","title":"Stack and Queue Explained","channel_title":"CS Academy","published_at":"2024-01-15T10:00:00Z","view_count":150000,"url":"https://www.youtube.com/watch?v=XYZ123","description":"Learn the differences between stack and queue...","score":78.5,"reason":"시각적 설명이 우수하고 예제가 풍부함"},{"video_id":"ABC456","title":"Data Structures: Stacks & Queues","channel_title":"Tech Tutorials","published_at":"2024-02-20T14:30:00Z","view_count":95000,"url":"https://www.youtube.com/watch?v=ABC456","description":"Complete guide to stack and queue implementation...","score":75.0,"reason":"구현 코드 예제 포함"}],"elapsed_ms":2156}

event: rec_partial
data: {"source":"openalex","count":2,"items":[{"id":"W2103456789","title":"Efficient Stack and Queue Implementations","authors":["John Smith","Jane Doe"],"year":2023,"cited_by_count":45,"publication_date":"2023-05-10","url":"https://openalex.org/W2103456789","abstract":"This paper presents novel implementations of stack and queue...","score":88.0,"reason":"최신 연구이며 인용 횟수가 높음"},{"id":"W1987654321","title":"Comparative Analysis of Stack-Based Algorithms","authors":["Alice Brown"],"year":2022,"cited_by_count":32,"publication_date":"2022-09-15","url":"https://openalex.org/W1987654321","abstract":"We compare various stack-based algorithms...","score":80.5,"reason":"알고리즘 비교 분석이 상세함"}],"elapsed_ms":3421}

event: rec_partial
data: {"source":"google","count":2,"items":[{"title":"Stack vs Queue: Complete Guide","url":"https://www.geeksforgeeks.org/stack-vs-queue/","snippet":"Learn the key differences between stack and queue data structures...","score":90.0,"reason":"실무 예제와 코드 구현이 포함됨"},{"title":"Understanding Stacks and Queues","url":"https://www.tutorialspoint.com/data_structures/stack_queue.htm","snippet":"A comprehensive tutorial on stack and queue operations...","score":85.5,"reason":"초보자 친화적인 설명"}],"elapsed_ms":1876}

event: rec_complete
data: {"completed_sources":4,"duration_ms":5421}
```

**예시 2: 일부 Provider 실패 포함 SSE 스트림**
```
event: rec_context
data: {"event":"context_ready","collection_id":"lecture_002","chunk_count":3}

event: rec_partial
data: {"source":"wiki","count":1,"items":[{"title":"이진 탐색 트리","url":"https://ko.wikipedia.org/wiki/%EC%9D%B4%EC%A7%84_%ED%83%90%EC%83%89_%ED%8A%B8%EB%A6%AC","language":"ko","extract":"이진 탐색 트리(binary search tree)는...","score":87.0,"reason":"개념 설명이 명확함"}],"elapsed_ms":1123}

event: rec_error
data: {"source":"youtube","error":"YouTube API quota exceeded","elapsed_ms":456}

event: rec_partial
data: {"source":"openalex","count":2,"items":[{"id":"W3012345678","title":"Binary Search Trees: A Survey","authors":["Bob Johnson"],"year":2024,"cited_by_count":12,"publication_date":"2024-03-01","url":"https://openalex.org/W3012345678","abstract":"This survey covers recent advances in binary search tree...","score":82.5,"reason":"최신 서베이 논문"}],"elapsed_ms":2987}

event: rec_partial
data: {"source":"google","count":2,"items":[{"title":"Binary Search Tree Implementation","url":"https://www.programiz.com/dsa/binary-search-tree","snippet":"Learn how to implement binary search tree with examples...","score":88.5,"reason":"코드 예제가 명확함"}],"elapsed_ms":1654}

event: rec_complete
data: {"completed_sources":3,"duration_ms":4987}
```

### 주의 사항
- `lecture_id`에 해당하는 컬렉션이 없으면 HTTP 404 오류 발생
- `previous_summaries`의 `section_id`는 1 이상이어야 하며, 현재 `section_id`보다 작아야 합니다
- Provider별 API 키가 없거나 할당량 초과 시 해당 Provider는 `rec_error` 이벤트 발생
- 4개 Provider가 모두 실패하면 `completed_sources: 0`으로 종료됩니다
- exclude 배열에 너무 많은 항목이 있으면 추천 결과가 적어질 수 있습니다

### 참고
- 4개 Provider(OpenAlex, Wiki, YouTube, Google)는 병렬로 실행되며 완료 순서는 보장되지 않습니다
- 각 Provider의 상세 동작은 다음 문서를 참조하세요:
  - OpenAlex: `documents/REC_OPENALEX_동작과정.md`
  - YouTube: `documents/REC_YOUTUBE_동작과정.md`
  - Google: `documents/REC_GOOGLE_동작과정.md`
  - Wikipedia: `documents/REC_WIKI_동작과정.md`
- Provider별 `top_k`, `verify`, `min_score` 등은 `server/config.py`에서 조정 가능
- RAG 검색에 사용되는 청크 수는 `RAGSettings.rec_retrieve_top_k`로 조정 (기본: 3개)

---

## 5. 공통 사항

### 5.1 HTTP 상태 코드

| 코드 | 의미 | 발생 상황 |
|------|------|-----------|
| 200 | OK | 요청 성공 (업서트 완료) |
| 400 | Bad Request | 잘못된 입력 (필수 필드 누락, 형식 오류) |
| 404 | Not Found | 존재하지 않는 컬렉션 (lecture_id) |
| 422 | Unprocessable Entity | 유효성 검증 실패 (Pydantic 모델) |
| 500 | Internal Server Error | 서버 내부 오류 (OpenAI/Chroma 오류 등) |

### 5.2 오류 응답 형식

**JSON 오류 응답**:
```json
{
  "detail": "Collection lecture_999 does not exist"
}
```

**SSE 오류 이벤트**:
```
event: qa_error
data: {"type":"응용","error":"OpenAI API rate limit exceeded"}
```

### 5.3 SSE 연결

**cURL 예시**:
```bash
curl -v -N -X POST http://127.0.0.1:8000/qa/generate \
  -H "Content-Type: application/json" \
  -d '{"lecture_id":"001","section_id":1,"section_summary":"..."}'
```

**JavaScript 예시**:
```javascript
const eventSource = new EventSource('http://127.0.0.1:8000/qa/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lecture_id: '001',
    section_id: 1,
    section_summary: '스택과 큐의 차이점'
  })
});

eventSource.addEventListener('qa_partial', (e) => {
  const data = JSON.parse(e.data);
  console.log('질문 생성:', data);
});

eventSource.addEventListener('qa_complete', (e) => {
  const data = JSON.parse(e.data);
  console.log('완료:', data);
  eventSource.close();
});
```

### 5.4 타임아웃 및 재시도

- **연결 타임아웃**: 30초 (서버 설정)
- **읽기 타임아웃**: 120초 (SSE 스트림)
- **재시도 정책**:
  - 업서트: 즉시 재시도 가능
  - QA/REC: 3초 대기 후 재시도 권장 (OpenAI rate limit 고려)

### 5.5 동시성 제한

- **업서트**: 제한 없음 (단, Chroma 락 발생 가능)
- **QA 생성**: 동시 10개 요청 권장
- **REC 추천**: 동시 5개 요청 권장 (4개 Provider × 동시성)

### 5.6 데이터 크기 제한

- **PDF 파일**: 최대 100MB (서버 설정 조정 가능)
- **텍스트 항목**: 항목당 최대 10,000자 권장
- **배열 크기**: 
  - `items[]`: 최대 500개
  - `previous_summaries[]`: 최대 10개
  - `*_exclude[]`: 각각 최대 50개

### 5.7 보안 고려사항

- 현재 버전은 인증 미구현 (내부 네트워크 전용)
- 운영 환경 배포 시 JWT 또는 API 키 인증 추가 권장
- CORS 설정은 `server/app.py`에서 조정 가능
- HTTPS 사용 권장 (API 키 노출 방지)

### 5.8 로깅 및 디버깅

- 서버 로그: `uvicorn server.main:app --log-level info`
- 각 모듈 로그: Python `logging` 모듈 사용
- 디버그 모드: `--log-level debug` (상세 로그 출력)
- 로그 파일: 기본적으로 stdout (파일 로깅은 별도 설정 필요)

---

**문서 버전**: 1.0  
**작성일**: 2025년 11월 15일  
**기준 코드**: module_intergration v1.0
