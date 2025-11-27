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
- **Response**: `202 Accepted` + JSON  
  (실제 추천 결과는 `callback_url`로 비동기 전송)

### HTTP 메서드
```
POST /qa/generate
```

### 본문 예시

**예시 1: 기본 QA 생성 (question_types 미지정 → 설정 기본 사용, 생성 순서대로 콜백)** 
```json
{
  "lecture_id": 1,
  "section_index": 0,
  "section_summary": "스택과 큐의 차이점을 설명하고, 각각의 사용 사례를 다룹니다.",
  "callback_url": "https://example.com/qa"
}
```

**예시 2: question_types 지정 + 과목/이전 QA 포함**
```json
{
  "lecture_id": 2,
  "section_index": 3,
  "section_summary": "이진 탐색 트리의 삽입, 삭제, 검색 연산을 구현하고 시간 복잡도를 분석합니다.",
  "subject": "자료구조",
  "callback_url": "https://example.com/qa",
  "question_types": ["CONCEPT", "COMPARISON"],
  "previous_qa": [
    {
      "type": "CONCEPT",
      "question": "트리의 기본 개념은 무엇인가요?",
      "answer": "트리는 계층적 구조를 가진 자료구조로, 루트 노드를 시작으로 부모-자식 관계를 형성합니다."
    },
    {
      "type": "APPLICATION",
      "question": "이진 트리는 어떤 상황에서 사용하나요?",
      "answer": "이진 트리는 검색, 정렬, 우선순위 큐 구현 등에 활용됩니다."
    }
  ]
}
```

### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | int | 예 | RAG 컬렉션과 매핑되는 강의 ID. 사전에 업서트된 ID여야 함 |
| summary_id | int | 아니오 | 요약 ID. 없으면 `null` |
| section_index | int | 예 | 섹션 인덱스(0-base). 0 이상 정수 |
| section_summary | string | 예 | 섹션 요약 내용. 최소 10자 이상 권장 |
| subject | string | 아니오 | 과목 정보 (예: "자료구조", "운영체제"). 질문 생성 시 컨텍스트로 활용 |
| callback_url | string(URL) | 예 | 생성 결과를 받을 콜백 URL (`POST`로 호출됨) |
| question_types | array[enum] | 아니오 | 생성할 질문 유형 리스트. 미지정 시 서버 설정(`QASettings.question_types`) 기본 사용. Enum: `CONCEPT`, `APPLICATION`, `ADVANCED`, `COMPARISON` |
| previous_qa | array | 아니오 | 중복 방지를 위한 이전 QA 목록. 각 항목은 type, question, answer 포함 |
| previous_qa[].type | string | 예 | 질문 유형 (예: `CONCEPT`/`APPLICATION` 등). 구타입(개념/응용 등)도 허용하나 Enum 값 권장 |
| previous_qa[].question | string | 예 | 이전 질문 내용 |
| previous_qa[].answer | string | 예 | 이전 답변 내용 |

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
data: {"type":"CONCEPT","qa":{"type":"CONCEPT","question":"스택과 큐의 주요 차이점은 무엇인가요?","answer":"스택은 LIFO(Last In First Out) 방식으로 마지막에 들어간 데이터가 먼저 나오는 구조이고, 큐는 FIFO(First In First Out) 방식으로 먼저 들어간 데이터가 먼저 나오는 구조입니다."},"index":1}

event: qa_partial
data: {"type":"APPLICATION","qa":{"type":"APPLICATION","question":"웹 브라우저의 뒤로가기 기능은 스택과 큐 중 어느 자료구조를 사용하나요?","answer":"웹 브라우저의 뒤로가기 기능은 스택을 사용합니다. 가장 최근에 방문한 페이지부터 역순으로 돌아가야 하므로 LIFO 구조가 적합합니다."},"index":2}

event: qa_partial
data: {"type":"ADVANCED","qa":{"type":"ADVANCED","question":"우선순위 큐를 구현할 때 힙(Heap) 자료구조를 사용하는 이유는 무엇인가요?","answer":"힙은 삽입과 삭제 연산이 O(log n) 시간 복잡도를 가지므로, 우선순위 큐의 핵심 연산인 최댓값/최솟값 추출을 효율적으로 수행할 수 있습니다."},"index":3}

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
- `previous_qa`에 이전 질문을 포함하면 중복 질문 생성을 방지할 수 있습니다
- OpenAI API 오류 시 일부 질문만 생성될 수 있습니다 (qa_error 이벤트 확인)
- SSE 연결이 끊기면 클라이언트에서 재시도 로직 구현 필요
- `question_types`에 존재하지 않는 Enum 값이 들어오면 HTTP 422
- 콜백: 각 QA가 생성되는 순서대로 `qnaList`에 1개씩 담아 여러 번 전송됩니다. 최종 전체 목록 콜백은 보내지 않습니다.

### 참고
- 질문 유형은 `server/config.py`의 `QASettings.question_types`에서 설정 (기본: 개념/응용/심화)
- 생성되는 질문 수는 `qa_top_k` 설정으로 조정 가능 (기본: 3개)
- RAG 검색에 사용되는 청크 수는 `RAGSettings.qa_retrieve_top_k`로 조정 (기본: 2개)
- 비동기 처리로 여러 질문을 동시에 생성하므로 순차 생성보다 빠릅니다
- `previous_qa`는 동일 섹션에서 여러 번 호출할 때 유용합니다 (추가 질문 생성 시)

---

## 4. REC 추천

### 형식
- **Content-Type**: `application/json`
- **Response**: `202 Accepted` + JSON  
  (실제 추천 결과는 `callback_url`로 비동기 전송)

### HTTP 메서드
```
POST /rec/recommend
```

### 본문 예시

**예시 1: 기본 추천 요청 (필수 필드만, resource_types 미지정 → 모든 Provider 실행)**
```json
{
  "lecture_id": 1,
  "section_index": 0,
  "section_summary": "스택과 큐의 차이점을 설명하고 활용 사례를 다룹니다.",
  "callback_url": "https://example.com/rec-callback",
  "previous_summaries": [],
  "yt_exclude": [],
  "wiki_exclude": [],
  "paper_exclude": [],
  "google_exclude": []
}
```

**예시 2: 이전 섹션, 제외 항목, resource_types 지정 (Wiki+YouTube만 실행)**
```json
{
  "lecture_id": 2,
  "summary_id": 10,
  "section_index": 2,
  "section_summary": "이진 탐색 트리의 삽입, 삭제, 검색 연산을 구현합니다.",
  "previous_summaries": [
    {"section_index": 0, "summary": "트리의 기본 개념과 용어", "timestamp": 111111},
    {"section_index": 1, "summary": "이진 트리의 순회 방법", "timestamp": 222222}
  ],
  "callback_url": "https://example.com/rec-callback",
  "yt_exclude": ["Binary Search Tree Basics"],
  "wiki_exclude": ["이진 트리"],
  "paper_exclude": ["W2103456789"],
  "google_exclude": ["https://example.com/old-tutorial"],
  "resource_types": ["WIKI", "VIDEO"]
}
```

### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | int | 예 | RAG 컬렉션과 매핑되는 강의 ID. 1 이상 정수 |
| summary_id | int | 아니오 | 요약 ID. 없으면 `null` |
| section_index | int | 예 | 섹션 인덱스(0-base). 0 이상 정수 |
| section_summary | string | 예 | 현재 섹션 요약 내용 (최소 10자 권장) |
| callback_url | string(URL) | 예 | 추천 결과를 받을 콜백 URL (`POST`로 호출됨) |
| previous_summaries | array | 아니오 | 이전 섹션 요약 목록 |
| previous_summaries[].section_index | int | 예 | 이전 섹션 인덱스(0-base). 0 이상 정수 |
| previous_summaries[].summary | string | 예 | 이전 섹션 요약 내용 |
| previous_summaries[].timestamp | int | 아니오 | 해당 요약의 타임스탬프(ms). 없으면 `null` |
| yt_exclude | array[string] | 아니오 | 추천에서 제외할 유튜브 영상 제목 목록 |
| wiki_exclude | array[string] | 아니오 | 추천에서 제외할 위키피디아 문서 제목 목록 |
| paper_exclude | array[string] | 아니오 | 추천에서 제외할 논문 ID(OpenAlex ID) 목록 |
| google_exclude | array[string] | 아니오 | 추천에서 제외할 구글 검색 결과 URL 목록 |
| resource_types | array[enum] | 아니오 | 실행할 Provider 필터. 미지정 시 모든 Provider(OpenAlex/Wiki/YouTube/Google) 실행. Enum: `PAPER`(OpenAlex), `WIKI`(Wikipedia), `VIDEO`(YouTube), `BLOG`(Google) |

**exclude 적용 규칙 (resource_types 지정 시)**  
- `PAPER` → OpenAlex 호출 시 `paper_exclude`를 `exclude_ids`로 전달 (OpenAlex 모듈이 ID/URL/DOI 포함 여부로 제외 처리)  
- `WIKI` → Wikipedia 호출 시 `wiki_exclude`를 `exclude_titles`로 전달  
- `VIDEO` → YouTube 호출 시 `yt_exclude`를 `exclude_titles`로 전달  
- `BLOG` → Google 호출 시 `google_exclude`를 `exclude_urls`로 전달  
그 외 exclude 배열은 무시. 콜백 직전 추가 필터링은 없습니다.

### 동작 방식

1. 클라이언트가 `/rec/recommend`로 추천 요청을 보냅니다.
2. 서버는 내부 RAG에서 컨텍스트 청크를 검색합니다.
3. RAG 검색에 성공하면 HTTP `202 Accepted`와 함께 `collection_id`를 응답하고,  
   이후 백그라운드에서 4개 Provider(OpenAlex, Wiki, YouTube, Google)를 비동기로 호출합니다.
4. 각 Provider의 추천 결과는 준비되는 대로 `callback_url`로 별도 `POST` 요청으로 전달됩니다.

### 즉시 응답 형식 (`202 Accepted`)

**예시 1: 정상 접수**
```json
{
  "status": "accepted",
  "collection_id": "lecture_1"
}
```

**예시 2: RAG 검색 실패 (400)**
```json
{
  "detail": "RAG 검색 실패: Collection lecture_999 does not exist"
}
```

### 콜백 요청 형식

서버는 각 Provider별로 한 번씩(최대 4회) `callback_url`로 POST를 수행합니다.

#### HTTP 메서드

```
POST {callback_url}
```

#### 콜백 본문 예시

**예시 1: 논문(OpenAlex) 추천 콜백**
```json
{
  "lectureId": 1,
  "summaryId": 10,
  "sectionIndex": 0,
  "resources": [
    {
      "type": "PAPER",
      "title": "Efficient Stack and Queue Implementations",
      "url": "https://openalex.org/W2103456789",
      "description": "This paper presents novel implementations of stack and queue...",
      "score": 88.0,
      "reason": "최신 연구이며 인용 횟수가 높음",
      "detail": {
        "openalexId": "W2103456789",
        "citedByCount": 45,
        "publicationDate": "2023-05-10",
        "authors": ["John Smith", "Jane Doe"]
      }
    }
  ]
}
```

**예시 2: 위키/유튜브/구글 콜백 (혼합 예시)**
```json
{
  "lectureId": 1,
  "summaryId": 10,
  "sectionIndex": 0,
  "resources": [
    {
      "type": "WIKI",
      "title": "스택 (자료 구조)",
      "url": "https://ko.wikipedia.org/wiki/%EC%8A%A4%ED%83%9D_(%EC%9E%90%EB%A3%8C_%EA%B5%AC%EC%A1%B0)",
      "description": "스택(stack)은 제한적으로 접근할 수 있는 나열 구조이다...",
      "score": 85.5,
      "reason": "스택의 개념과 구현을 잘 설명함",
      "detail": {
        "language": "ko",
        "extract": "스택(stack)은 제한적으로 접근할 수 있는 나열 구조이다..."
      }
    },
    {
      "type": "VIDEO",
      "title": "Stack and Queue Explained",
      "url": "https://www.youtube.com/watch?v=XYZ123",
      "description": "Learn the differences between stack and queue...",
      "score": 78.5,
      "reason": "시각적 설명이 우수하고 예제가 풍부함",
      "detail": {
        "videoId": "XYZ123",
        "channelTitle": "CS Academy",
        "viewCount": 150000
      }
    },
    {
      "type": "BLOG",
      "title": "Stack vs Queue: Complete Guide",
      "url": "https://www.geeksforgeeks.org/stack-vs-queue/",
      "description": "Learn the key differences between stack and queue data structures...",
      "score": 90.0,
      "reason": "실무 예제와 코드 구현이 포함됨",
      "detail": {
        "snippet": "Learn the key differences between stack and queue data structures..."
      }
    }
  ]
}
```

### 주의 사항
 - `lecture_id`에 해당하는 컬렉션이 없으면 HTTP 404 오류 발생
 - `previous_summaries`의 `section_index`는 0 이상이어야 하며, 일반적으로 현재 `section_index`보다 작아야 합니다
 - Provider별 API 키가 없거나 할당량 초과 시 해당 Provider의 추천은 콜백 `resources`에 포함되지 않고 서버 로그에만 기록됩니다
 - 4개 Provider가 모두 실패한 경우에도 콜백이 0개 또는 `resources: []` 형태로 도착할 수 있습니다
 - exclude 배열에 너무 많은 항목이 있으면 추천 결과가 적어질 수 있습니다
 - `resource_types`에 존재하지 않는 Enum 값이 들어오면 HTTP 422
 - OpenAlex는 요청 단계에서만 `exclude_ids`(ID/URL/DOI 부분 매칭)로 제외합니다. Wiki/YouTube/Google은 요청 단계에서만 제외를 적용합니다.

### 참고
- 4개 Provider(OpenAlex, Wiki, YouTube, Google)는 병렬로 실행되며 콜백 도착 순서는 보장되지 않습니다
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
| 202 | Accepted | 비동기 요청 접수 (QA/REC 콜백) |
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
