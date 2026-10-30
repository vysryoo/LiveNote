# LiveNote AI 서버 API 명세

백엔드가 호출하는 AI 서버 API입니다. 기본 포트는 8003입니다.

---

## 공통

- `/health`를 제외한 모든 요청에 `X-Internal-Api-Key` 헤더가 필요합니다. 값이 다르거나 서버에 키가 없으면 401
- 요약·추천 결과는 콜백으로 보냅니다. 콜백 요청에도 같은 `X-Internal-Api-Key` 헤더를 붙입니다
- JSON 필드는 snake_case와 camelCase를 모두 받습니다 (`/rag/*` 제외, snake_case만)
- 섹션 번호(`section_index`)는 0부터 셉니다
- 강의 자료 컬렉션이 없으면 오류 대신 빈 검색 결과로 처리하고, 섹션 요약만으로 생성합니다

| 상태 코드 | 경우 |
| --- | --- |
| 200 | 업서트 완료, QnA 스트림 시작 |
| 202 | 요약·추천 접수 (결과는 콜백) |
| 400 | 입력 오류 (PDF 아님, 빈 파일, 메타데이터 JSON 오류, 콜백 URL 없음, RAG 검색 실패) |
| 401 | 내부 키 불일치 |
| 422 | 필드 검증 실패 (필수 누락, 범위, 지원하지 않는 유형 값) |

오류 본문: `{"detail": "..."}`

---

## GET /health

인증 없음. `{"status": "ok"}`

---

## POST /rag/pdf-upsert

강의 자료 PDF를 조각내 저장합니다. `multipart/form-data`.

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | string | 예 | 강의 ID. 공백만 있으면 400 |
| file | PDF | 예 | `application/pdf`가 아니거나 비어 있으면 400 |
| base_metadata | string(JSON) | 아니오 | 모든 조각에 붙일 메타데이터 |

```json
{"collection_id": "lecture_7", "result": {"collection_id": "lecture_7", "count": 12, "embedding_dim": 3072}}
```

- `count`는 저장한 조각 수. 분할 방식은 서버 설정(기본 semantic)을 따릅니다
- 같은 파일 이름으로 다시 올리면 그 파일의 이전 조각을 지우고 새로 저장합니다
- 텍스트가 없는 쪽(이미지만 있는 쪽)은 건너뜁니다

## POST /rag/text-upsert

확정된 섹션 요약을 저장합니다. 이후 QnA·추천 검색에서 이전 요약으로 쓰입니다.

```json
{"lecture_id": "7", "items": [{"text": "스택은 LIFO 구조…", "id": "summary-301", "section_id": "5"}]}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | string | 예 | 강의 ID. 공백만 있으면 422 |
| items[].text | string | 예 | 요약 |
| items[].id | string | 아니오 | 같은 ID는 덮어씀. 없으면 텍스트 내용으로 만듦 |
| items[].section_id | string | 아니오 | 섹션 번호(0부터). 숫자면 검색 시 직전 3개 섹션을 빼는 데 씀 |
| items[].metadata | object | 아니오 | 추가 메타데이터 |

응답 형식은 `/rag/pdf-upsert`와 같습니다. `items`가 비면 422.

---

## POST /qa/generate

질문 유형별 QnA를 동시에 만들며 진행 과정을 SSE(`text/event-stream`)로 보냅니다.

```json
{
  "lectureId": 7,
  "sectionIndex": 5,
  "sectionSummary": "스택은 LIFO 자료구조이며 push와 pop으로 동작함",
  "subject": "자료구조",
  "questionTypes": ["CONCEPT", "COMPARISON"],
  "previousQa": [{"type": "CONCEPT", "question": "배열이란?", "answer": "…"}]
}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lectureId | int | 예 | 1 이상 |
| sectionIndex | int | 예 | 0 이상 |
| sectionSummary | string | 예 | 10자 이상, 공백만 있으면 422 |
| subject | string | 아니오 | 과목. 프롬프트에 넣음 |
| questionTypes | array | 아니오 | `CONCEPT`, `APPLICATION`, `COMPARISON`, `ADVANCED`. 없으면 네 유형 모두. 최대 4개 |
| previousQa | array | 아니오 | 이미 만든 QnA. 최근 3개를 중복 방지용으로 프롬프트에 넣음 |
| summaryId | int | 아니오 | 사용하지 않음 |

이벤트 (`item`은 요청한 유형 순서, 0부터. 유형끼리는 동시에 생성되어 이벤트가 섞여 도착함)

| 이벤트 | data | 설명 |
| --- | --- | --- |
| start | `{"item", "type"}` | 생성 시작 |
| question | `{"item", "text"}` | 질문 완성 |
| answer | `{"item", "text"}` | 답변 조각. 여러 번 옴 |
| done | `{"item", "type", "question", "answer"}` | 항목 완료 |
| error | `{"item", "message"}` | 항목 실패. 이 항목의 `done`은 오지 않음 |

```
event: start
data: {"item": 0, "type": "CONCEPT"}

event: question
data: {"item": 0, "text": "스택은 어떤 순서로 원소를 꺼내나요?"}

event: answer
data: {"item": 0, "text": "스택은 마지막에 넣은"}

event: done
data: {"item": 0, "type": "CONCEPT", "question": "…", "answer": "…"}
```

- RAG 검색이 실패하면 스트림을 열기 전에 400으로 응답합니다
- 강의 자료 조각 2개와 이전 섹션 요약 1개(직전 3개 섹션 제외)를 검색해 참고 자료로 넣습니다
- 받는 쪽이 연결을 끊으면 남은 생성도 멈춥니다

---

## POST /summary/generate

섹션 전사를 1~2문장으로 요약하고 결과를 콜백으로 보냅니다.

```json
{"lectureId": 7, "sectionIndex": 5, "summaryId": 301, "transcript": ["문장 1", "문장 2"], "phase": "FINAL", "callbackUrl": "http://backend/api/ai/callback"}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lectureId | int | 예 | 1 이상 |
| sectionIndex | int | 예 | 0 이상 |
| transcript | string 또는 string[] | 예 | 배열은 줄바꿈으로 합침. 비어 있으면 422 |
| callbackUrl | URL | 조건부 | 없으면 서버 설정 `SUMMARY_CALLBACK_URL`. 둘 다 없으면 400 |
| summaryId | int | 아니오 | 콜백에 그대로 돌려줌 |
| startSec / endSec | int | 아니오 | 없으면 `sectionIndex × 30`, `startSec + 30` |
| phase | string | 아니오 | 기본 `FINAL`. 대문자로 바꿈 |

즉시 응답: `202 {"status": "accepted"}`. 공백을 뺀 전사가 10자 이하면 요약하지 않고 `202 {"status": "skipped", "reason": "too_short"}`로 응답한 뒤 안내 문구를 콜백합니다.

콜백: `POST {callbackUrl}?type=summary` (쿼리에 `type=summary`를 붙임)

```json
{"id": 301, "summaryId": 301, "lectureId": 7, "sectionIndex": 5, "startSec": 150, "endSec": 180, "text": "요약", "phase": "FINAL", "status": "COMPLETED"}
```

`status`는 `COMPLETED` 또는 `TOO_SHORT`. 요약 생성이 실패하면 콜백을 보내지 않고 서버 로그만 남깁니다.

---

## POST /rec/recommend

자료 종류별 추천을 동시에 실행하고, 종류마다 끝나는 대로 콜백을 보냅니다.

```json
{
  "lectureId": 7,
  "summaryId": 301,
  "sectionIndex": 5,
  "sectionSummary": "스택은 LIFO 자료구조이며 push와 pop으로 동작함",
  "callbackUrl": "http://backend/api/ai/callback?type=resources",
  "previousSummaries": [{"sectionIndex": 4, "summary": "연결 리스트 삽입과 삭제"}],
  "paperExclude": [], "wikiExclude": [], "ytExclude": [], "googleExclude": [],
  "resourceTypes": ["WIKI", "BLOG"]
}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lectureId | int | 예 | 1 이상 |
| sectionIndex | int | 예 | 0 이상 |
| sectionSummary | string | 예 | 10자 이상, 공백만 있으면 422 |
| callbackUrl | URL | 예 | 결과를 받을 주소 |
| previousSummaries | array | 아니오 | `{sectionIndex, summary(5자 이상), timestamp?}`. 최근 3개를 검색어 생성 프롬프트에 넣음 |
| resourceTypes | array | 아니오 | `PAPER`(OpenAlex), `WIKI`(위키백과), `VIDEO`(YouTube), `BLOG`(네이버 블로그). 없으면 네 종류 모두 |
| paperExclude | string[] | 아니오 | 제외할 논문 ID·URL 일부 문자열 |
| wikiExclude | string[] | 아니오 | 제외할 위키 문서 제목 (대소문자 무시) |
| ytExclude | string[] | 아니오 | 제외할 영상 제목 (특수문자·대소문자 무시) |
| googleExclude | string[] | 아니오 | 제외할 블로그 URL (프로토콜·www 무시). 이름은 백엔드 호환용 |
| summaryId | int | 아니오 | 콜백에 그대로 돌려줌 |

즉시 응답: `202 {"status": "accepted", "collection_id": "lecture_7"}`

콜백: 자료 종류마다 한 번 `POST {callbackUrl}`. 도착 순서는 보장하지 않습니다.

```json
{
  "lectureId": 7,
  "summaryId": 301,
  "sectionIndex": 5,
  "resources": [{
    "type": "WIKI",
    "title": "Stack (abstract data type)",
    "url": "https://en.wikipedia.org/wiki/Stack_(abstract_data_type)",
    "description": "In computer science, a stack is …",
    "score": 7.0,
    "reason": "Heuristic",
    "detail": {"url": "…", "title": "…", "extract": "…", "lang": "en", "page_id": 273993}
  }]
}
```

| `type` | `description` | `detail` |
| --- | --- | --- |
| PAPER | 초록 (400자) | `url`, `title`, `abstract`, `year`, `cited_by_count`, `authors` |
| WIKI | 문서 도입부 3문장 | `url`, `title`, `extract`, `lang`, `page_id` |
| VIDEO | LLM이 제목·설명으로 쓴 2문장 요약 | `url`, `title`, `extract`, `lang` |
| BLOG | 검색 결과 요약 (300자) | `url`, `title`, `snippet`, `display_link`, `lang` |

- `score`는 0~10. LLM 검증이면 `reason`이 한 문장 설명이고, 휴리스틱이면 `"Heuristic"`입니다
- 종류별 기본 개수는 1개. 검증 방식과 최소 점수는 서버 설정(`core/config.py`의 `RECSettings`)을 따릅니다

| 종류 | 점수 | 최소 점수 |
| --- | --- | --- |
| PAPER | LLM 검증 | 5.0 |
| WIKI | 휴리스틱 (제목·도입부 키워드 일치) | 5.0 |
| VIDEO | LLM 검증 | 7.0 |
| BLOG | LLM 검증 | 3.0 |

- WIKI는 영어 위키백과에서 개수를 못 채우면 한국어 위키백과에서 부족분을 채웁니다
- LLM 검증이 실패한 후보는 결과에서 뺍니다
- 검색 API가 429·503으로 거절하면 대기 후 최대 3번 다시 시도합니다
- 한 종류의 추천이 실패해도 다른 종류는 계속 진행하고, 실패한 종류는 `resources: []`로 콜백합니다
- RAG 검색이 실패하면 접수 전에 400으로 응답합니다
