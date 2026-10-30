# LiveNote AI 게이트웨이 안내서

본 문서는 LiveNote AI 백엔드의 전체 구조, 운영 절차, API 명세를 담은 종합 안내서입니다.

---

## 목차

1. 개요
2. 아키텍처 개요
3. 디렉터리 구조
4. 환경 구축
5. 환경 변수(.env)
6. API 명세
    - 6.1 Health 체크
    - 6.2 RAG 업서트
    - 6.3 QA 생성
    - 6.4 REC 추천
    - 6.5 요약 생성
7. 테스트 방법
8. 문제 해결

---

## 1. 개요

LiveNote AI 게이트웨이는 다음과 같은 기능을 제공합니다.

- **RAG** 기반 강의 자료·섹션 요약 저장 및 검색 (LangChain Chroma, OpenAI 임베딩)
- 질문 유형별 **QA 생성**과 SSE 스트리밍
- **OpenAlex / Wikipedia / YouTube / 네이버 블로그**를 통합한 **자료 추천(REC)**
- **섹션별 요약 생성**
- 요약·추천 결과는 **콜백 방식**으로 비동기 전송

---

## 2. 아키텍처 개요

```
백엔드(Spring)
     │  X-Internal-Api-Key
     ▼
FastAPI (server/)
 ├─ RAG 라우터     → rag (분할: page | recursive | semantic, Chroma 저장)
 ├─ QA 라우터      → 강의 자료·이전 요약 검색 → qa 그래프 (질문 유형별 동시 생성, SSE)
 ├─ REC 라우터     → 강의 자료·이전 요약 검색 → 추천 그래프 (논문 / 위키 / 영상 / 블로그 동시 실행, 종류별 콜백)
 └─ Summary 라우터 → summary 서비스 (프롬프트 | 모델 | 문자열) → 콜백
```

- **설정**: `core/config.py`의 설정 클래스 하나가 서버 시작 시 환경변수와 `ai/.env`를 한 번 읽음. 같은 키는 환경변수가 우선
- **LLM 호출**: 모든 모듈이 `core/llm.py`(LangChain `ChatOpenAI`)를 거침. 용도별 모델·추론 강도는 설정으로 지정하고, 호출마다 토큰 사용량을 JSON 로그로 남김. JSON 응답은 구조화 출력(`complete_json`)으로 받음
- **그래프**: QnA(`qa/graph.py`)와 추천(`recommend/graph.py`)은 LangGraph `Send`로 항목을 동시에 실행. 한 항목이 실패해도 나머지는 계속 진행
- **추천 공통 흐름**: `recommend/pipeline.py`가 검색어 생성 → 후보 검색 → 점수(LLM 검증 또는 휴리스틱) → `min_score`·`top_k`를 맡고, 자료 종류별 공급자(`recommend/providers/`)는 검색 API·프롬프트·휴리스틱만 구현. LLM 검증이 실패한 후보는 결과에서 뺌
- **외부 API**: 검색 API 클라이언트는 상주 연결을 쓰고, 429·503 응답은 `core/http.py`가 기다렸다가 최대 3번 다시 시도
- **강의 자료 분할**: 기본 `semantic`(이웃 문장 임베딩 거리가 크게 벌어지는 곳에서 자르고 문장 1개를 겹침). `RAG_CHUNK_STRATEGY`로 변경
- **검색**: 강의 자료 조각과 이전 섹션 요약을 따로 검색해 합침. 직전 3개 섹션 요약은 백엔드가 직접 보내므로 검색에서 제외
- **QnA 출제 범위**: 강의 자료에는 아직 설명하지 않은 내용도 있어, 현재 섹션에서 말한 내용만 근거로 출제하도록 제한
- **백그라운드 작업**: `core/tasks.py`가 콜백 작업의 참조를 보관하고, 서버 종료 시 최대 30초 기다림
- **시간 기록**: `core/timing.py`가 요청별 단계 경과 시간(ms)을 JSON 로그로 남김

---

## 3. 디렉터리 구조

| 경로 | 설명 |
|------|------|
| `server/` | FastAPI 앱, 라우터, 서비스 주입(`Services`), 내부 인증, 콜백 전송 |
| `core/` | 설정, LLM 호출, 외부 API 재시도, 로깅, 공용 모델, 백그라운드 작업, 시간 기록 |
| `rag/` | 강의 자료 분할·저장·검색 |
| `qa/` | QnA 프롬프트, 생성 그래프, 스트림 파서 |
| `recommend/` | 자료 추천 공통 흐름, 추천 그래프, 공급자(`providers/`: 논문 OpenAlex, 위키백과, 영상 YouTube, 블로그 네이버) |
| `summary/` | 섹션 요약 |
| `eval/` | 정확도(Precision@k)·응답 시간·전사 오류율 측정 도구와 보고서(`eval/results/`) |
| `tests/` | 단위·통합 테스트 (외부 API 호출 없음) |
| `setup.sh` | 환경 구축 스크립트 (`uv sync`, `.env` 준비) |
| `pyproject.toml` | 의존성 목록 (런타임, `dev` 그룹: 테스트·평가) |
| `uv.lock` | 간접 의존성까지 고정한 잠금 파일 |
| `.env.example` / `.env` | 환경 변수 템플릿 및 실제 설정 |
| `API_SPECIFICATION.md` | API 상세 명세 |

---

## 4. 환경 구축

### 4.1 사전 준비물
- [uv](https://docs.astral.sh/uv/) (`brew install uv`). Python 3.11이 없으면 uv가 내려받음
- OpenAI API Key, YouTube API Key, Naver 검색 API Key

### 4.2 설치
```bash
./setup.sh
```

`setup.sh`는 `uv sync`로 `.venv`를 `uv.lock`과 같은 상태로 맞추고, `.env`가 없으면 `.env.example`을 복사한다.
수동으로 할 때는 다음과 같다.

```bash
uv sync
cp .env.example .env  # 키 값 채우기
```

### 4.3 의존성 변경
```bash
uv add <패키지>==<버전>           # 런타임 의존성
uv add --group dev <패키지>==<버전> # 테스트·평가용
```

`pyproject.toml`과 `uv.lock`이 함께 바뀌므로 둘 다 커밋한다.

### 4.4 서버 실행

> [!IMPORTANT]
> **서버 실행 명령어:**
> ```bash
> uv run uvicorn server.main:app --reload --port 8003
> ```
> 기본 포트는 **8003**입니다. <- 백엔드와의 정합성을 위해서 8003 포트를 추천. 

---

## 5. 환경 변수(.env)

```bash
OPENAI_API_KEY="sk-proj-xxxx". #현재 openai키를 비워둬서 직접 설정하셔야합니다.
YOUTUBE_API_KEY="AIzaSy...." # Google Cloud Console에서 YouTube Data API v3 사용 설정 후 API 키 발급
NAVER_CLIENT_ID="..." # 네이버 클라우드 콘솔의 NAVER API HUB에서 블로그 검색 Application 등록 후 인증 정보 확인
NAVER_CLIENT_SECRET="..."
WIKIKIT_USER_AGENT="WikiKit/1.0 (+https://example.com; contact: you@example.com)"
RAG_PERSIST_DIR="server_storage/chroma_data_real" #chroma db 위치 지정. 상대 경로는 ai/ 기준
INTERNAL_API_KEY="..." # 백엔드 env.properties와 같은 값. /health를 제외한 모든 API와 콜백이 X-Internal-Api-Key 헤더로 이 값을 확인하며, 비어 있으면 모든 요청을 거부
```

- `OPENAI_API_KEY`, `INTERNAL_API_KEY`, `YOUTUBE_API_KEY`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 중 하나라도 비어 있으면 서버가 시작 단계에서 멈춤
- 같은 이름의 셸 환경변수가 있으면 `.env` 값보다 우선함

선택 설정 (없으면 기본값 사용):

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `LLM_MODEL` | `gpt-6-luna` | 모든 LLM 호출의 모델 |
| `LLM_<용도>_MODEL` | - | 용도별 모델. 용도: `SUMMARY`, `QA`, `QUERY`(검색어 생성), `VERIFY`(후보 검증) |
| `LLM_<용도>_REASONING_EFFORT` | `none` | 용도별 추론 강도. 추론 모델(gpt-5·gpt-6 계열)에만 전달 |
| `RAG_CHUNK_STRATEGY` | `semantic` | 강의 자료 분할 방식: `page`(쪽 단위), `recursive`(토큰 수 기준), `semantic`(의미 단위) |
| `RAG_CHUNK_TOKENS` / `RAG_CHUNK_OVERLAP_TOKENS` | 300 / 50 | `recursive` 조각 크기와 겹침(토큰) |
| `RAG_SEMANTIC_PERCENTILE` | 95 | `semantic` 경계 기준 백분위수. 높을수록 경계가 적음 |
| `RAG_SEMANTIC_OVERLAP_SENTENCES` | 1 | `semantic` 조각 앞에 붙이는 이전 조각 문장 수 |
| `RAG_SEMANTIC_MIN_TOKENS` / `RAG_SEMANTIC_MAX_TOKENS` | 40 / 200 | `semantic` 조각 최소·최대 토큰 |
| `RAG_UPLOAD_DIR` | `server_storage/uploads` | 업로드한 PDF 저장 위치 (상대 경로는 `ai/` 기준) |
| `RAG_EMBEDDING_MODEL` | `text-embedding-3-large` | 임베딩 모델 |
| `RAG_OPENAI_API_KEY` | - | 임베딩에만 다른 OpenAI 키를 쓸 때 |
| `SUMMARY_CALLBACK_URL` | - | 요약 요청에 콜백 URL이 없을 때 쓸 기본값 |

---

## 6. API 명세

### 6.1 Health 체크

- **Endpoint**: `GET /health`
- **응답**: `{"status":"ok"}`

---

### 6.2 RAG 업서트

#### `POST /rag/text-upsert`

- **형식**: `application/json`
- **본문 예시**:
```json
{
  "lecture_id": "001",
  "items": [
    {"text": "요약 A"},
    {"text": "요약 B", "metadata": {"topic": "stack"}}
  ]
}
```

#### `POST /rag/pdf-upsert`

- **형식**: `multipart/form-data`
- **필드**: `lecture_id`, `file` (PDF)

---

### 6.3 QA 생성

- **Content-Type**: `application/json`
- **Response**: `200 OK` + `text/event-stream` (SSE)
- 질문 유형별로 동시에 생성하며, 생성 과정을 같은 응답으로 이어서 전송

#### HTTP 메서드

```
POST /qa/generate
```

#### 본문 예시

**기본 QA 생성:**
```json
{
  "lecture_id": 1,
  "section_index": 0,
  "section_summary": "스택과 큐의 차이점을 설명하고, 각각의 사용 사례를 다룹니다."
}
```

**question_types 지정:**
```json
{
  "lecture_id": 2,
  "section_index": 3,
  "section_summary": "이진 탐색 트리의 삽입, 삭제, 검색 연산을 구현합니다.",
  "subject": "자료구조",
  "question_types": ["CONCEPT", "COMPARISON"],
  "previous_qa": [
    {
      "type": "CONCEPT",
      "question": "트리의 기본 개념은 무엇인가요?",
      "answer": "트리는 계층적 구조를 가진 자료구조입니다."
    }
  ]
}
```

#### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | int | 예 | RAG 컬렉션과 매핑되는 강의 ID |
| section_index | int | 예 | 섹션 인덱스(0-base) |
| section_summary | string | 예 | 섹션 요약 내용 (최소 10자 권장) |
| subject | string | 아니오 | 과목 정보 |
| question_types | array[enum] | 아니오 | 생성할 질문 유형. Enum: `CONCEPT`, `APPLICATION`, `ADVANCED`, `COMPARISON` |
| previous_qa | array | 아니오 | 중복 방지를 위한 이전 QA 목록 |

#### 응답 이벤트 형식

`item`은 질문 유형 순서(0부터)이며, 여러 유형의 이벤트가 섞여서 도착합니다.

```
event: start
data: {"item":0,"type":"CONCEPT"}

event: question
data: {"item":0,"text":"스택이란 무엇인가요?"}

event: answer
data: {"item":0,"text":"스택은 마지막에 들어온 "}

event: answer
data: {"item":0,"text":"데이터가 먼저 나가는 구조입니다."}

event: done
data: {"item":0,"type":"CONCEPT","question":"스택이란 무엇인가요?","answer":"스택은 마지막에 들어온 데이터가 먼저 나가는 구조입니다."}

event: error
data: {"item":1,"message":"..."}
```

- `question`은 질문이 완성되면 한 번, `answer`는 답변 조각이 생성될 때마다 전송
- `error`가 온 항목은 `done`이 오지 않음

#### 주의 사항

- 강의 컬렉션이 아직 없으면(첫 확정 요약 업서트 전) 참고 자료 없이 섹션 요약만으로 생성
- 그 밖의 RAG 검색 실패는 스트림을 시작하지 않고 HTTP 400
- `question_types`에 잘못된 Enum 값이 들어오면 HTTP 422
- 모델 출력 형식은 "첫 줄 질문, 이후 답변"이며, 모델이 붙이는 `질문:`, `답변:` 같은 머리말은 서버가 제거

---

### 6.4 REC 추천

- **Content-Type**: `application/json`
- **Response**: `202 Accepted` + JSON
- 실제 추천 결과는 `callback_url`로 비동기 전송

#### HTTP 메서드

```
POST /rec/recommend
```

#### 본문 예시

**기본 추천 (모든 Provider):**
```json
{
  "lecture_id": 1,
  "section_index": 0,
  "section_summary": "스택과 큐의 차이점을 설명합니다.",
  "callback_url": "https://example.com/rec-callback",
  "previous_summaries": [],
  "yt_exclude": [],
  "wiki_exclude": [],
  "paper_exclude": [],
  "google_exclude": []
}
```

**특정 Provider만 실행 (WIKI+VIDEO):**
```json
{
  "lecture_id": 2,
  "section_index": 2,
  "section_summary": "이진 탐색 트리를 구현합니다.",
  "callback_url": "https://example.com/rec-callback",
  "resource_types": ["WIKI", "VIDEO"],
  "wiki_exclude": ["이진 트리"],
  "yt_exclude": ["Binary Search Tree Basics"]
}
```

#### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | int | 예 | RAG 컬렉션과 매핑되는 강의 ID |
| section_index | int | 예 | 섹션 인덱스(0-base) |
| section_summary | string | 예 | 현재 섹션 요약 내용 |
| callback_url | string(URL) | 예 | 추천 결과를 받을 콜백 URL |
| resource_types | array[enum] | 아니오 | 실행할 Provider. Enum: `PAPER`, `WIKI`, `VIDEO`, `BLOG` |
| yt_exclude | array[string] | 아니오 | 제외할 유튜브 영상 제목 |
| wiki_exclude | array[string] | 아니오 | 제외할 위키 문서 제목 |
| paper_exclude | array[string] | 아니오 | 제외할 논문 ID |
| google_exclude | array[string] | 아니오 | 제외할 블로그 URL (필드 이름은 기존 호환을 위해 유지) |

#### 즉시 응답 (`202 Accepted`)

```json
{
  "status": "accepted",
  "collection_id": "lecture_1"
}
```

#### 콜백 형식 예시

**논문(PAPER) 콜백:**
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
      "description": "This paper presents novel implementations...",
      "score": 88.0,
      "reason": "최신 연구이며 인용 횟수가 높음"
    }
  ]
}
```

**위키/유튜브/블로그 콜백:**
```json
{
  "lectureId": 1,
  "sectionIndex": 0,
  "resources": [
    {
      "type": "WIKI",
      "title": "스택 (자료 구조)",
      "url": "https://ko.wikipedia.org/wiki/스택",
      "score": 85.5
    },
    {
      "type": "VIDEO",
      "title": "Stack and Queue Explained",
      "url": "https://www.youtube.com/watch?v=XYZ123",
      "score": 78.5
    }
  ]
}
```

#### 주의 사항

- 4개 Provider(OpenAlex, Wiki, YouTube, 네이버 블로그)는 추천 그래프에서 동시 실행
- 콜백 도착 순서는 보장되지 않음
- `resource_types`에 잘못된 Enum 값이 들어오면 HTTP 422

---

### 6.5 요약 생성

- **Content-Type**: `application/json`
- **Response**: `202 Accepted` + JSON
- 실제 요약 결과는 `callback_url`로 비동기 전송

#### HTTP 메서드

```
POST /summary/generate
```

#### 본문 예시

**단일 텍스트 전사 요약:**
```json
{
  "lecture_id": 7,
  "summary_id": 301,
  "section_index": 5,
  "start_sec": 150,
  "end_sec": 180,
  "phase": "FINAL",
  "callback_url": "https://example.com/api/ai/callback",
  "transcript": "이번 섹션에서는 분산 시스템의 리더 선출과 네트워크 파티션 대응 전략을 다루었습니다..."
}
```

**문장 배열 요약 (callback_url 미지정 시 서버 기본값 사용):**
```json
{
  "lecture_id": 8,
  "section_index": 2,
  "phase": "PARTIAL",
  "transcript": [
    "캐시 일관성 문제를 소개했습니다.",
    "MESI 프로토콜의 동작 단계를 설명했습니다."
  ]
}
```

#### 입력 필드 설명

| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| lecture_id | int | 예 | 강의 ID (1 이상) |
| section_index | int | 예 | 섹션 인덱스(0-base) |
| transcript | string / array | 예 | 전사 텍스트 (문자열 또는 문장 배열) |
| callback_url | string(URL) | 조건부 | 요청/ 서버 설정 / 환경변수 중 하나 필요 |
| summary_id | int | 아니오 | 기존 요약 ID |
| start_sec | int | 아니오 | 요약 구간 시작 초 |
| end_sec | int | 아니오 | 요약 구간 종료 초 |
| phase | string | 아니오 | 요약 단계 (기본 `FINAL`) |

#### 즉시 응답 (`202 Accepted`)

```json
{
  "status": "accepted"
}
```

#### 콜백 형식

```json
{
  "id": 301,
  "summaryId": 301,
  "lectureId": 7,
  "sectionIndex": 5,
  "startSec": 150,
  "endSec": 180,
  "text": "요약된 내용이 여기에 들어갑니다.",
  "phase": "FINAL",
  "status": "COMPLETED"
}
```

#### 주의 사항

- 공백을 뺀 전사가 10자 이하면 요약하지 않고 `{"status":"skipped","reason":"too_short"}`로 응답하며, 안내 문구를 `status: "TOO_SHORT"`로 콜백함
- `callback_url`이 없으면 400 오류
- 콜백 URL에는 `type=summary` 쿼리가 자동 추가됨

---

## 7. 테스트 방법

외부 API를 호출하지 않는 단위·통합 테스트는 `tests/`에 있다.

```bash
uv run pytest
```

실제 API를 쓰는 측정은 `eval/`의 스크립트로 한다. 비용이 들며, 결과 보고서는 `eval/results/`에 저장된다.

| 스크립트 | 측정 |
|------|------|
| `eval.prepare_data` / `eval.collect_sections` | 평가 데이터 준비(PDF·TTS 녹음), 실제 서비스 경로로 전사·섹션·요약 수집 |
| `eval.run_retrieval` | 강의 자료 검색 Precision@4 (분할 방식별) |
| `eval.run_cards` | QnA·추천 자료 Precision@4 (AI 서버를 띄운 상태에서 실행) |
| `eval.run_latency` | QnA 스트리밍 응답 시간 |
| `eval.transcription_cer` | 전사 모델별 글자 오류율 |

채점은 `gpt-6.1-terra`가 이진 판정(관련/무관)으로 하며, 데이터는 dev(조정용)와 test(최종 측정용)로 나눠 쓴다.

---

## 8. 문제 해결

### 자주 발생하는 에러

| 메시지 | 원인 | 해결 |
|--------|------|------|
| `metadata must be non-empty` | 메타데이터 없음 | 최신 코드 사용 (자동 보강) |
| HTTP 422 | 잘못된 Enum 값 | 올바른 Enum 값 확인 |

### Chroma 컬렉션 문제

- QA·REC 검색 대상 컬렉션이 없으면 오류 대신 빈 검색 결과로 처리하고 섹션 요약만으로 생성함. 컬렉션은 첫 확정 요약을 업서트할 때 생김

- 서버는 시작할 때 셸 환경변수와 `ai/.env`를 읽고, 같은 키는 셸 환경변수가 우선함. 측정 등에서 저장 경로(`RAG_PERSIST_DIR`)만 바꿀 때는 셸에서 지정하면 됨

---

## 부록

### 용어집

- **RAG**: 기존 데이터를 참고해 답변을 생성하는 방식
- **콜백**: 서버에서 클라이언트로 결과를 비동기 전송하는 방식
- **Provider**: 추천 자료를 제공하는 외부 서비스 (OpenAlex, Wiki, YouTube, 네이버 블로그)

---

### 끝.
