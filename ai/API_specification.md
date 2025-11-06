예상 질문/답변을 생성
- method : POST
- path : /qa/generate

**Request Body (예시)**

```json
{
  "lecture_id": "session_abc123",
  "section_id": 3,
  "section_summary": "스택의 실전 응용: 괄호 검사, 후위 표기법 계산...",
  "subject": "CS",
  "language": "ko",
  "question_types": ["개념", "응용", "심화"],
  "qa_count": 3,
  "rag_context": {
    "chunks": [
      { "text": "스택은 LIFO 구조입니다...", "score": 0.92, "metadata": {"section_id": 1} },
      { "text": "큐는 FIFO 구조입니다...", "score": 0.65, "metadata": {"section_id": 2} }
    ]
  },
  "previous_qa": [
    { "type": "개념", "question": "배열이란 무엇인가요?", "answer": "배열은 같은 타입의 데이터를..." }
  ]
}
```

**Response Body (예시)**

```json
{
  "lecture_id": "session_abc123",
  "section_id": 3,
	"data" : 
	[
	  { "type": "개념", "question": "스택에서 괄호 검사는 어떻게 동작하나요?", "answer": "여는 괄,...(2~3문장)" },
	  { "type": "응용", "question": "후위 표기법 계산을 스택으로 어떻게 구현하나요?", "answer": "숫자는 push..." },
	  { "type": "심화", "question": "왜 괄호 검사에 스택을 사용하나요?", "answer": "LIFO 특성이..." }
	]
}
```

- 400 잘못된 요청

```json
{
  "error": "섹션 요약이 너무 짧습니다",
  "detail": { "field": "section_summary", "min_length": 10, "received_length": 7 }
}
```

- 500 서버오류

```json
{
  "error": "질문 생성 중 오류가 발생했습니다",
  "detail": { "message": "OpenAI timeout" }
}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | string | ✅ | 세션 식별자 |
| section_id | integer | ✅ | 현재 섹션 번호 |
| section_summary | string | ✅ | 현재 섹션 요약. (10자 이상) |
| subject | string | ❌ | 과목/도메인 키 |
| language | string | ❌ | 응답 언어(디폴트 ko) |
| question_types | string[] | ❌ | 생성할 질문 유형 목록(`개념`, `응용`, `비교` 을 기본으로 사용하면됨!) |
| qa_count | integer | ❌ | 생성 개수(기본 3~5권장) |
| rag_context | object[] | ❌ | RAG 검색 결과(텍스트, 점수, 메타데이터) |
| previous_qa | object[] | ❌ | 중복 방지용 과거 QA |

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| lecture_id | string | 섹션 식별자 |
| section_id | integer | 현재 섹션 번호 |
| data.type | string | 질문 유형(개념/응용/비교/심화/실습) |
| data.question | string | 생성된 질문 |
| data.answer | string | 생성된 답변(2~3문장) |

---

텍스트 업서트(요약저장)

- Method: POST
- Path: /rag/upsert-text
- Headers: Content-Type: application/json

**Request Body (예시)**

```json
{
  "collection_id": "session_abc123", //lecture_id 그대로 써도 됨. 같은 PK임.
  "items": [
    {
      "text": "스택은 LIFO 구조입니다. push와 pop으로 데이터를 관리하며...",
      "metadata": {
        "section_id": 1,
        "timestamp": 1703001234567,
        "duration": 60,
        "subject": "CS"
      }
    }
  ]
}

```

**Response Body (예시)**

```json
{
  "collection_id": "session_abc123",
  "count": 1,
  "embedding_dim": 3072
}

```

- 400 잘못된 요청

```json
{
  "error": "잘못된 요청 본문입니다",
  "detail": {
    "field": "items[0].text",
    "message": "텍스트는 비어 있을 수 없습니다"
  }
}

```

- 500 서버오류

```json
{
  "error": "업서트 처리 중 오류가 발생했습니다",
  "detail": { "message": "OpenAI timeout" }
}
```

- 입력필드 상세

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| collection_id | string | ✅ | 저장 대상 컬렉션 ID. 실시간 세션은 lecture_ID 사용 권장(e.g., session_abc123). 영문/숫자/하이픈/언더스코어만 허용. |
| items | object[] | ✅ | 업서트할 청크 목록. 최소 1개. |
| items[].text | string | ✅ | 저장할 섹션 요약 텍스트(비어있으면 안 됨). |
| items[].metadata | object | ❌ | 검색/필터용 메타데이터(자유 필드). 아래 권장 키 사용 가능. |
| └ section_id | integer | 권장 | 섹션 번호(1부터). |
| └ type | string | 권장 | “summary”로 기본 저장됨.
”lecture note”는 강의노트.
같은 콜렉션에서 종류 구분 용도. |
| └ timestamp | integer | 권장 | 밀리초 epoch(예: 1703001234567). |
| └ duration | integer | 권장 | 섹션 길이(초). |
| └ subject | string | 권장 | 과목 키(e.g., CS). |
- 출력필드 상세
    
    
    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | collection_id | string | 저장된 컬렉션 ID(Echo). |
    | count | integer | 저장(업서트)된 청크 수. |
    | embedding_dim | integer | 임베딩 벡터 차원(정보용, 예: 3072). |

유의사항

- 이 엔드포인트는 실시간 섹션 요약 저장용입니다(PDF 업로드 아님).
- collection_id는 세션 단위로 고정 사용을 권장합니다(예: session_abc123). 혹은 lectureID
- metadata는 자유 확장 가능하며, 인덱싱/필터링에 활용됩니다.
- 내부적으로 임베딩 생성 후 벡터DB(ChromaDB)에 텍스트와 메타데이터를 함께 저장합니다.
- 내부 개별 ID는 자동 생성되며 응답에는 포함하지 않습니다.

검증/규칙 요약

- collection_id가 비어있거나 허용 문자 집합을 벗어나면 400.
- items가 비어있거나 items[].text가 비어있으면 400.
- 서버 측 임베딩/벡터DB 오류 시 500.

---

PDF 업서트(강의노트 저장)

- method : POST
- path : /rag/upsert-pdf

Request Body (예시)

```json
{
  "collection_id": "lecture_notes_cs",
  "pdf_path": "/data/notes/data_structure.pdf",
  "metadata": {
    "subject": "CS",
    "course": "데이터구조",
    "language": "ko"
  }
}

```

Response Body (예시)

```json
{
  "collection_id": "lecture_notes_cs",
  "count": 20,
  "embedding_dim": 3072
}

```

- 400 잘못된 요청

```json
{
  "error": "잘못된 요청 본문입니다",
  "detail": {
    "field": "pdf_path",
    "message": "파일을 찾을 수 없습니다 또는 비어 있습니다"
  }
}

```

- 500 서버오류

```json
{
  "error": "업서트 처리 중 오류가 발생했습니다",
  "detail": { "message": "OpenAI timeout" }
}

```

### 2) 입력필드

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| collection_id | string | ✅ | 강의/노트 컬렉션 식별자. 내부적으로 collection_id로 사용. 외부에서는 lecture_id 써도 무관. 같은 pk |
| pdf_path | string | ✅ | AI 서버가 직접 읽을 수 있는 PDF 파일 경로(절대 경로 권장). |
| metadata | object | ❌ | 모든 페이지에 공통 적용할 메타데이터. |
| └subject | string | 선택 | 과목 키(예: CS). |
| └type | string | 권장 | ”lecture note”로 기본 저장됨.
“summary”는 강의노트.
같은 콜렉션에서 종류 구분 용도. |
| └course | string | 선택 | 강좌명/코스명. |
| └language | string | 선택 | 문서 언어(예: ko, en). |
- 출력필드 상세
    
    
    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | collection_id | string | 저장된 컬렉션 ID(Echo). |
    | count | integer | 저장(업서트)된 페이지 수. |
    | embedding_dim | integer | 임베딩 벡터 차원(정보용, 예: 3072). |

검증/규칙 요약

- lecture_id는 비어 있으면 안 됨(영문/숫자/하이픈/언더스코어 사용 권장).
- pdf_path가 비어있거나 파일이 존재하지 않으면 400.
- 내부 임베딩/벡터DB 오류는 500.

비고

- 이 엔드포인트는 강의노트 PDF 저장용입니다(요약 텍스트 저장 아님).
- 파일 바이너리 업로드가 아닌 경로 기반(JSON) 입력만 처리합니다.
- 응답의 collection_id는 요청 lecture_id와 동일합니다.

---

검색(retrieve)

- Method: POST
- Path: /rag/retrieve
- Headers: Content-Type: application/json

Request Body (예시)

```json
{
  "collection_id": "session_abc123",
  "query": "스택의 실전 응용: 괄호 검사...",
  "top_k": 3,
  "filters": {
    "subject": "CS",
    "min_timestamp": 1703000000000
  }
}
```

Response Body (예시)

```json
{
  "collection_id": "session_abc123",
  "query": "스택의 실전 응용: 괄호 검사...",
  "top_k": 3,
  "chunks": [
    { "id": "7f3e9a2b1c4d5e", "text": "스택은 LIFO 구조입니다...", "score": 0.92, "metadata": { "section_id": 1 } },
    { "id": "auto_...", "text": "스택의 실전 응용: 괄호 검사...", "score": 0.88, "metadata": { "section_id": 3 } },
    { "id": "auto_...", "text": "큐는 FIFO 구조입니다...", "score": 0.65, "metadata": { "type": "lecture note" } }
  ]
}

```

- 400 잘못된 요청

```json
{
  "error": "잘못된 요청 본문입니다",
  "detail": { "field": "query", "message": "쿼리는 비어 있을 수 없습니다" }
}

```

- 400 파라미터 충돌

```json
{
  "error": "컬렉션 파라미터 오류",
  "detail": { "message": "collection_id 또는 collections 중 하나만 제공하세요" }
}

```

- 500 서버오류

```json
{
  "error": "검색 처리 중 오류가 발생했습니다",
  "detail": { "message": "timeout" }
}

```

### 2) 입력필드

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| collection_id | string | ✅ | 강의/노트 컬렉션 식별자. 내부적으로 collection_id로 사용. 외부에서는 lecture_id 써도 무관. 같은 pk |
| query | string | ✅ | 검색 쿼리 텍스트 |
| top_k | interger | ✅ | 반환할 개수(2,3 권장). 관련된 내용 몇개까지 긁어올지 내용입니다. |
| filters | object | 선택 | 메타데이터 기반 필터. |
| filters.subject | string | 선택 | metadata.subject 일치 필터 |
| filter.confidence | number | 선택 |  score >= confidence 인 것만 뽑아옴. top_K 안 지켜질 수 있음. |
| filters.section_id | integer | 선택 | 특정 섹션만. |
| filters.min_timestamp | integer | 선택 | 최소 타임스탬프 |
| filters.max_timestamp | integer | 선택 | 최대 타임스탬프 |
| filters.custom | object | 선택 |  임의의 키=값 일치 필터(Chroma where로 전달). |
- 출력필드 상세
    
    
    | 필드명 | 타입 | 설명 |
    | --- | --- | --- |
    | collection_id | string | 요청 echo(단일 요청 시) |
    | query | string | 요청 쿼리 echo |
    | top_k | integer | 요청된 상위 개수(필터 후 상한) |
    | chunks | object[] | 결과 목록(점수 내림차순). |
    | .chunks[].text:  | string | 원문 텍스트. |
    | chunks[].score:  —  | number | 유사도 점수(1/(1+distance)). |
    | chunks[].metadata  | object | 저장된 메타데이터 그대로 반환. |

유의사항

- collection_id 비우면400.
- collection_id는 영문/숫자/하이픈/언더스코어만 권장(기타 문자는 400 처리 권장).
- 점수는 Chroma distance를 1/(1+distance)로 변환한 유사도이며 높을수록 유사함.
- filters.subject/section_id/custom은 동등 비교로 처리(Chroma where). min/max_timestamp는 검색 후 메모리에서 후필터링.
- 결과는 점수 내림차순 정렬 후 top_k 적용. 멀티 컬렉션의 경우 컬렉션별 검색→병합→정렬→top_k 적용.

검증/규칙 요약

- query가 비어 있으면 400.
- collection_id와 collections를 동시에 제공하면 400.
- collections가 비어 있거나 유효하지 않으면 400.
- 서버 측 임베딩/벡터DB 오류 시 500.

---
유튜브 학습 영상 추천

- Method: POST
- Path: /youtube/recommend
- Headers: Content-Type: application/json

Request Body (예시)

```json
{
  "lecture_id": "lecture_cs101",
  "section_id": 3,
  "lecture_summary": "스택 오버플로 방지와 재귀 호출 스택 동작을 정리한 섹션입니다.",
  "language": "ko",
  "top_k": 3,
  "verify_yt": true,
  "yt_lang": "en",
  "min_score": 6.0,
  "exclude_titles": [
    "Stack Data Structure Basics"
  ],
  "previous_summaries": [
    {
      "section_id": 1,
      "summary": "스택은 LIFO 구조이며 push/pop 연산으로 동작합니다.",
      "timestamp": 1703000600000
    }
  ],
  "rag_context": [
    {
      "text": "호출 스택과 재귀 함수의 종료 조건 설명",
      "score": 0.88,
      "source": "lecture_notes.pdf#page=5",
      "metadata": { "section_id": 2 }
    }
  ]
}
```

Response Body (예시)

```json
{
  "lecture_id": "lecture_cs101",
  "section_id": 3,
  "videos": [
    {
      "score": 8.9,
      "reason": "재귀 호출에서 스택 프레임이 어떻게 관리되는지 실습 코드로 확인할 수 있습니다.",
      "video_info": {
        "title": "Preventing Stack Overflow in Recursive Functions",
        "url": "https://www.youtube.com/watch?v=abcd1234",
        "extract": "Explains recursion call stacks, overflow scenarios, and mitigation patterns.",
        "lang": "en"
      }
    },
    {
      "score": 8.3,
      "reason": "스택 기반 수식 계산 사례를 시각적으로 설명합니다.",
      "video_info": {
        "title": "Stack Applications: Postfix Evaluation",
        "url": "https://www.youtube.com/watch?v=wxyz5678",
        "extract": "Walks through postfix evaluation using stack operations with sample code.",
        "lang": "en"
      }
    }
  ]
}
```

- 400 잘못된 요청

```json
{
  "error": "lecture_summary 길이가 너무 짧습니다",
  "detail": {
    "field": "lecture_summary",
    "min_length": 10,
    "received_length": 6
  }
}
```

- 500 서버오류

```json
{
  "error": "YouTube 추천 중 외부 API 오류가 발생했습니다",
  "detail": { "message": "YouTube Data API quota exhausted" }
}
```

### 1) 입력필드

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | string | ✅ | 강의 세션 식별자. 기존 session_id 대신 사용. |
| section_id | integer | ✅ | 현재 섹션 번호(1 이상). |
| lecture_summary | string | ✅ | 현재 섹션 요약(최소 10자). |
| language | string | ❌ | 추천 설명 언어 (`ko`/`en`, 기본 `ko`). |
| top_k | integer | ❌ | 반환할 영상 수(1~10, 기본 5). |
| verify_yt | boolean | ❌ | True면 LLM 검증, False면 휴리스틱 검증(기본 False). |
| previous_summaries | object[] | ❌ | 이전 섹션 요약 리스트(컨텍스트 보강). |
| └ section_id | integer | ❌ | 이전 섹션 번호. |
| └ summary | string | ❌ | 이전 섹션 요약 텍스트. |
| └ timestamp | integer | ❌ | 요약 생성 시각(ms, 선택). |
| rag_context | object[] | ❌ | RAG 검색 결과 청크 목록. text 또는 content 제공. |
| └ text | string | ❌ | 청크 본문. content가 존재하면 자동으로 사용. |
| └ score | number | ❌ | 유사도 점수(0~1 권장). |
| └ source | string | ❌ | 출처 정보(파일명, 문서 페이지 등). |
| └ metadata | object | ❌ | 추가 메타데이터. |
| yt_lang | string | ❌ | YouTube 검색 언어(기본 `en`). |
| exclude_titles | string[] | ❌ | 제외할 영상 제목 목록. |
| min_score | number | ❌ | 추천 최소 점수(0~10, 기본 5.0). |

- 출력필드 상세

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| lecture_id | string | 요청 echo. |
| section_id | integer | 요청 섹션 번호 echo. |
| videos | object[] | 추천된 영상 리스트. (최대 top_k) |
| videos[].video_info.title | string | 영상 제목. |
| videos[].video_info.url | string | 영상 URL. |
| videos[].video_info.extract | string | 2~3문장 요약. |
| videos[].video_info.lang | string | 영상 언어 코드. |
| videos[].reason | string | 추천 이유(1~2문장). |
| videos[].score | number | 관련도 점수(0.0~10.0). |

유의사항

- YouTube Data API 키와 OpenAI API 키가 환경변수로 설정돼 있어야 정상 동작합니다.
- verify_yt=False일 때는 휴리스틱 점수만 사용하므로 품질이 낮을 수 있습니다.
- 최소 점수(min_score)보다 낮은 영상은 응답에서 자동 제거됩니다.

---

위키피디아 문서 추천

- Method: POST
- Path: /wiki/recommend
- Headers: Content-Type: application/json

Request Body (예시)

```json
{
  "lecture_id": "lecture_cs101",
  "section_id": 3,
  "lecture_summary": "스택을 활용한 괄호 검사와 후위 표기법 계산을 설명한 섹션입니다.",
  "language": "ko",
  "top_k": 4,
  "verify_wiki": true,
  "wiki_lang": "en",
  "fallback_to_ko": true,
  "min_score": 5.5,
  "previous_summaries": [
    {
      "section_id": 2,
      "summary": "큐는 FIFO 구조이며 버퍼 관리에 사용됩니다."
    }
  ],
  "rag_context": [
    {
      "text": "자료구조에서 스택과 큐의 차이점을 정리한 표",
      "score": 0.91,
      "metadata": { "section_id": 2 }
    }
  ],
  "exclude_titles": [
    "Stack (abstract data type)"
  ]
}
```

Response Body (예시)

```json
{
  "lecture_id": "lecture_cs101",
  "section_id": 3,
  "pages": [
    {
      "score": 9.1,
      "reason": "스택 기반 괄호 검사 알고리즘과 후위 표기법 평가 과정을 모두 설명합니다.",
      "page_info": {
        "title": "Stack (abstract data type)",
        "url": "https://en.wikipedia.org/wiki/Stack_(abstract_data_type)",
        "extract": "Defines stack operations and covers algorithmic use cases such as parsing and expression evaluation.",
        "lang": "en",
        "page_id": 12345
      }
    },
    {
      "score": 8.6,
      "reason": "후위 표기법 계산 예제를 제공해 학습 흐름을 보완합니다.",
      "page_info": {
        "title": "Reverse Polish notation",
        "url": "https://en.wikipedia.org/wiki/Reverse_Polish_notation",
        "extract": "Explains postfix notation, evaluation rules, and historic usage in computing.",
        "lang": "en",
        "page_id": 67890
      }
    }
  ]
}
```

- 400 잘못된 요청

```json
{
  "error": "lecture_summary가 최소 길이 요건을 충족하지 않습니다",
  "detail": {
    "field": "lecture_summary",
    "min_length": 10,
    "received_length": 8
  }
}
```

- 500 서버오류

```json
{
  "error": "Wikipedia 추천 중 외부 API 오류가 발생했습니다",
  "detail": { "message": "MediaWiki API timeout" }
}
```

### 1) 입력필드

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | string | ✅ | 강의 세션 식별자. |
| section_id | integer | ✅ | 현재 섹션 번호(1 이상). |
| lecture_summary | string | ✅ | 현재 섹션 요약(최소 10자). |
| language | string | ❌ | 응답 언어(`ko`/`en`, 기본 `en`). |
| top_k | integer | ❌ | 반환할 문서 수(1~10, 기본 5). |
| verify_wiki | boolean | ❌ | True면 LLM 검증, False면 휴리스틱(기본 True). |
| previous_summaries | object[] | ❌ | 이전 섹션 요약 리스트. |
| └ section_id | integer | ❌ | 이전 섹션 번호. |
| └ summary | string | ❌ | 이전 섹션 요약. |
| └ timestamp | integer | ❌ | 요약 생성 시각(ms, 선택). |
| rag_context | object[] | ❌ | RAG 검색 결과 청크 목록. |
| └ text | string | ❌ | 청크 본문. |
| └ score | number | ❌ | 유사도 점수. |
| └ metadata | object | ❌ | 추가 메타데이터. |
| wiki_lang | string | ❌ | Wikipedia 검색 언어(기본 `en`). |
| fallback_to_ko | boolean | ❌ | 영문 결과 부족 시 한국어 보충 여부(기본 True). |
| exclude_titles | string[] | ❌ | 제외할 문서 제목 리스트. |
| min_score | number | ❌ | 추천 최소 점수(0~10, 기본 5.0). |

- 출력필드 상세

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| lecture_id | string | 요청 echo. |
| section_id | integer | 요청 섹션 번호 echo. |
| pages | object[] | 추천된 위키 문서 리스트. |
| pages[].page_info.title | string | 문서 제목. |
| pages[].page_info.url | string | 문서 URL. |
| pages[].page_info.extract | string | Wikipedia에서 가져온 요약(3문장 내외). |
| pages[].page_info.lang | string | 문서 언어 코드. |
| pages[].page_info.page_id | integer | Wikipedia 페이지 ID. |
| pages[].reason | string | 추천 이유(1~2문장). |
| pages[].score | number | 관련도 점수(0.0~10.0). |

유의사항

- verify_wiki=True일 때 OpenAI API 키가 필수입니다.
- fallback_to_ko=True면 영문 결과 부족 시 한국어 검색을 자동 수행합니다.
- min_score 아래 문서는 제거되며, 남는 문서가 없으면 빈 배열을 반환합니다.

---

학술 논문 추천 (OpenAlex)

- Method: POST
- Path: /openalex/recommend
- Headers: Content-Type: application/json

Request Body (예시)

```json
{
  "lecture_id": "lecture_cs101",
  "section_id": 3,
  "section_summary": "스택의 실전 응용과 함수 호출 스택의 구조를 설명한 섹션입니다.",
  "language": "ko",
  "top_k": 5,
  "verify_openalex": true,
  "year_from": 2018,
  "sort_by": "hybrid",
  "min_score": 6.0,
  "exclude_ids": [
    "https://openalex.org/W123456789"
  ],
  "previous_summaries": [
    {
      "section_id": 1,
      "summary": "스택의 기본 개념과 push/pop 연산을 다룹니다.",
      "timestamp": 1703000300000
    }
  ],
  "rag_context": [
    {
      "text": "스택 기반 후위 표기법 계산 알고리즘",
      "score": 0.93,
      "metadata": { "section_id": 2 }
    }
  ]
}
```

Response Body (예시)

```json
{
  "lecture_id": "lecture_cs101",
  "section_id": 3,
  "papers": [
    {
      "score": 9.3,
      "reason": "스택을 활용한 식 평가 알고리즘을 논문 수준으로 정리한 자료입니다.",
      "paper_info": {
        "title": "Stack-Based Algorithms for Expression Evaluation",
        "url": "https://doi.org/10.1145/1234567",
        "abstract": "Presents stack-based parsing and evaluation strategies for arithmetic expressions.",
        "year": 2021,
        "cited_by_count": 134,
        "authors": [
          "Jane Doe",
          "John Smith"
        ]
      }
    },
    {
      "score": 8.7,
      "reason": "재귀 호출과 스택 프레임 분석을 다뤄 강의 심화 학습에 적합합니다.",
      "paper_info": {
        "title": "Analyzing Call Stack Behavior in Modern Languages",
        "url": "https://openalex.org/W987654321",
        "abstract": "Analyzes call stack growth, overflow mitigation, and debugging techniques.",
        "year": 2019,
        "cited_by_count": 82,
        "authors": [
          "Alice Kim",
          "Robert Lee"
        ]
      }
    }
  ]
}
```

- 400 잘못된 요청

```json
{
  "error": "section_summary가 최소 길이 요건을 충족하지 않습니다",
  "detail": {
    "field": "section_summary",
    "min_length": 10,
    "received_length": 5
  }
}
```

- 500 서버오류

```json
{
  "error": "OpenAlex 추천 처리 중 외부 API 오류가 발생했습니다",
  "detail": { "message": "OpenAlex service unavailable" }
}
```

### 1) 입력필드

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | string | ✅ | 강의 세션 식별자. (기존 session_id 대체) |
| section_id | integer | ✅ | 현재 섹션 번호(1 이상). |
| section_summary | string | ✅ | 현재 섹션 요약(최소 10자). |
| language | string | ❌ | 응답 언어(`ko`/`en`, 기본 `ko`). |
| top_k | integer | ❌ | 반환할 논문 수(1~10, 기본 5). |
| verify_openalex | boolean | ❌ | True면 LLM 검증, False면 휴리스틱(기본 True). |
| previous_summaries | object[] | ❌ | 이전 섹션 요약 리스트. |
| └ section_id | integer | ❌ | 이전 섹션 번호. |
| └ summary | string | ❌ | 이전 섹션 요약. |
| └ timestamp | integer | ❌ | 요약 생성 시각(ms, 선택). |
| rag_context | object[] | ❌ | RAG 검색 결과 청크 목록. |
| └ text | string | ❌ | 청크 본문. |
| └ score | number | ❌ | 유사도 점수. |
| └ metadata | object | ❌ | 추가 메타데이터. |
| year_from | integer | ❌ | 검색 시작 연도(YYYY, 기본 2015). |
| exclude_ids | string[] | ❌ | 제외할 논문 ID/URL 목록. |
| sort_by | string | ❌ | 정렬 기준(`relevance`, `cited_by_count`, `hybrid`). |
| min_score | number | ❌ | 추천 최소 점수(0~10, 기본 5.0). |

- 출력필드 상세

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| lecture_id | string | 요청 echo. |
| section_id | integer | 요청 섹션 번호 echo. |
| papers | object[] | 추천된 논문 리스트. |
| papers[].paper_info.title | string | 논문 제목. |
| papers[].paper_info.url | string | 논문 URL (DOI/OpenAlex). |
| papers[].paper_info.abstract | string | 논문 초록 요약. |
| papers[].paper_info.year | integer | 출판 연도(선택). |
| papers[].paper_info.cited_by_count | integer | 인용 수. |
| papers[].paper_info.authors | string[] | 저자 이름 목록. |
| papers[].reason | string | 추천 이유(1~2문장). |
| papers[].score | number | 관련도 점수(0.0~10.0). |

유의사항

- FastAPI 래퍼에서는 기존 session_id 대신 lecture_id 필드를 사용합니다.
- verify_openalex=True일 때 OpenAI API 키가 필요합니다.
- year_from 필터로 최신 논문을 우선 추천할 수 있으며, min_score 미만 논문은 제거됩니다.

---
