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

- **RAG(Retrieval-Augmented Generation)** 기반의 문서 저장 및 검색
- **OpenAI**를 활용한 다중 질문 유형의 **QA 생성**
- **OpenAlex / Wikipedia / YouTube / Google**를 통합한 **자료 추천(REC)**
- **섹션별 요약 생성**
- 모든 생성 결과는 **콜백 방식**으로 비동기 전송

---

## 2. 아키텍처 개요

```
클라이언트(Spring / curl / Postman)
           │
           ▼
FastAPI (server/)
 ├─ RAG 라우터 → rag (OpenAI Embedding + ChromaDB)
 ├─ QA 라우터  → qa (OpenAI Chat Completion)
 ├─ REC 라우터 → openalex / wiki / youtube / blog
 └─ Summary 라우터 → OpenAI Chat Completion
```

- **server/**: FastAPI 앱, 라우터, 설정, 유틸리티
- **\*_module**: 각각의 기능을 담당하는 독립 모듈
- **ChromaDB**: `RAG_PERSIST_DIR` 경로에 벡터 데이터 저장
- **외부 API**: OpenAI, OpenAlex, Wikipedia, YouTube Data API, 네이버 블로그 검색

---

## 3. 디렉터리 구조

| 경로 | 설명 |
|------|------|
| `qa/` | QA 생성 모듈 |
| `rag/` | RAG 저장/검색 모듈 (Chroma + Embedding) |
| `openalex/` | 논문 추천 모듈 |
| `wiki/` | 위키 추천 모듈 |
| `youtube/` | 유튜브 추천 모듈 |
| `blog/` | 블로그 추천 모듈 (네이버 블로그 검색 사용) |
| `server/` | FastAPI 서버 구성 |
| `tests/` | 단위/통합 테스트 |
| `setup.sh` | 환경 구축 자동 스크립트 |
| `requirements.txt` | 런타임 의존성 목록 (로컬·Docker 공통, 버전 고정) |
| `requirements-dev.txt` | 테스트·검증 스크립트용 의존성 (`requirements.txt` 포함) |
| `.env.example` / `.env` | 환경 변수 템플릿 및 실제 설정 |

---

## 4. 환경 구축

### 4.1 사전 준비물
- Python 3.11
- OpenAI API Key, YouTube API Key, Google API Key

### 4.2 자동 설치
```bash
./setup.sh
```

### 4.3 수동 설치
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env  # 내용 수정 필요
```

### 4.4 서버 실행

> [!IMPORTANT]
> **서버 실행 명령어:**
> ```bash
> source .venv/bin/activate
> uvicorn server.main:app --reload --port 8003
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
ANONYMIZED_TELEMETRY="False"
CHROMA_TELEMETRY_ENABLED="False"
RAG_PERSIST_DIR="server_storage/chroma_data_real" #chroma db 위치 지정
INTERNAL_API_KEY="..." # 백엔드 env.properties와 같은 값. /health를 제외한 모든 API와 콜백이 X-Internal-Api-Key 헤더로 이 값을 확인하며, 비어 있으면 모든 요청을 거부
```

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
| google_exclude | array[string] | 아니오 | 제외할 구글 검색 URL |

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

**위키/유튜브/구글 콜백:**
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

- 4개 Provider(OpenAlex, Wiki, YouTube, Google)는 병렬 실행
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
  "phase": "FINAL"
}
```

#### 주의 사항

- `OPENAI_API_KEY` 미설정 시 500 오류
- `callback_url`이 없으면 400 오류
- 콜백 URL에는 `type=summary` 쿼리가 자동 추가됨

---

## 7. 테스트 방법

외부 API를 호출하지 않는 단위·통합 테스트는 `tests/`에 있다.

```bash
pytest
```

실제 API를 쓰는 정확도·응답 시간 측정은 `eval/`의 스크립트로 한다.

---

## 8. 문제 해결

### 자주 발생하는 에러

| 메시지 | 원인 | 해결 |
|--------|------|------|
| `metadata must be non-empty` | 메타데이터 없음 | 최신 코드 사용 (자동 보강) |
| HTTP 422 | 잘못된 Enum 값 | 올바른 Enum 값 확인 |

### Chroma 컬렉션 문제

- QA·REC 검색 대상 컬렉션이 없으면 오류 대신 빈 검색 결과로 처리하고 섹션 요약만으로 생성함. 컬렉션은 첫 확정 요약을 업서트할 때 생김

- `.env` 적용이 되지 않은 상태에서 서버 기동 → 기본 경로 사용
- 해결: `source .venv/bin/activate`로 `.env` 적용 후 서버 실행

---

## 부록

### 용어집

- **RAG**: 기존 데이터를 참고해 답변을 생성하는 방식
- **콜백**: 서버에서 클라이언트로 결과를 비동기 전송하는 방식
- **Provider**: 추천 자료를 제공하는 외부 서비스 (OpenAlex, Wiki, YouTube, Google)

---

### 끝.
