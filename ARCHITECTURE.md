# LiveNote 통신 구조 및 데이터 파이프라인 명세

프론트엔드(React), 백엔드(Spring Boot), 메시지 브로커(RabbitMQ), 외부 STT(OpenAI Realtime API), AI 서버(FastAPI) 간의 전체 통신 구조와 데이터 흐름을 정리한 문서임.

---

## 1. 핵심 아키텍처 및 기반 개념

### 1.1 두 종류의 WebSocket 회선 분리
프론트엔드와 백엔드 사이에는 목적과 수명 주기가 다른 2개의 WebSocket 회선이 독립적으로 동작함.

| 구분 | 오디오 전사 소켓 (`/ws/transcription`) | 세션 이벤트 소켓 (`/ws`) |
| --- | --- | --- |
| **프로토콜** | 순수 WebSocket (Raw WS) | WebSocket 위에서 동작하는 **STOMP** |
| **통신 대상** | **1:1 직통** (마이크 녹음자 본인 ↔ 백엔드) | **1:N 브로드캐스트** (백엔드 ↔ RabbitMQ ↔ 모든 시청자) |
| **연결 시점** | **녹음 시작 버튼 클릭 시** (`useAudioRecording.ts`) | **강의실 페이지(`/lectures/:id`) 진입 즉시** (`useSessionStream.ts`) |
| **종료 시점** | 녹음 중지 버튼 클릭 시 (OpenAI 연결도 함께 종료) | 강의실 페이지를 나갈 때 (언마운트 시) |
| **주요 역할** | 고빈도 바이너리 음성 업로드 + 발화 중 미확정 글자(`delta`) 초저지연 표시 | DB에 확정된 전사, 요약, QnA 스트리밍, 추천 자료를 모든 클라이언트에 동기화 |
| **분리 이유** | 0.17초마다 전송되는 바이너리 음성에 STOMP 텍스트 헤더 오버헤드를 없애고, 녹음 On/Off 시 전체 이벤트 연결이 끊기지 않도록 수명 주기를 분리함 | 토픽(`/topic/...`) 기반의 Pub/Sub 구조로 다중 사용자 및 다중 서버 확장에 대응함 |

---

### 1.2 STOMP와 RabbitMQ 브로드캐스트 구조
- **연결 구조**: `프론트엔드` ↔ `Spring Boot 백엔드 (:8080)` ↔ `RabbitMQ (:61613)`
  - 프론트엔드는 RabbitMQ에 직접 붙지 않고 백엔드의 `/ws` 엔드포인트로 연결함 (`StompConfig.java`).
  - 백엔드의 `StompAuthChannelInterceptor`가 중간에서 JWT 토큰 인증과 강의 접근 권한을 검증한 뒤, 내부망의 RabbitMQ STOMP 플러그인(`enableStompBrokerRelay`)으로 구독과 메시지를 중계(Relay)함.
- **패킷 형태**: HTTP가 아닌 **WebSocket 위에서 오가는 STOMP 프레임**이며, 프레임의 본문(Body)에 **JSON 문자열**이 담김.
- **RabbitMQ 분리 이유**: 백엔드가 1대(단일 노드)일 때는 백엔드 인메모리 브로커만으로도 동작하지만, 백엔드 서버를 여러 대로 증설(스케일아웃)했을 때 서로 다른 서버에 연결된 클라이언트들에게도 메시지를 누락 없이 브로드캐스트하기 위해 별도 서버 인스턴스로 구성함.

---

### 1.3 30초 섹션 분할 원리
- **텍스트 길이가 아닌 시간(초) 기준 분할**:
  - 백엔드가 원문 텍스트를 모아서 30초 덩어리로 잘라 보내는 구조가 아님.
  - `SectionAggregationService.assignSection()`에서 각 확정 문장의 발화 시작 시각(`startSec`)을 확인함.
  - 현재 섹션의 시작 시각으로부터 30초(`SECTION_SEC = 30`) 이상 경과한 문장이 들어오면 다음 섹션 번호(`sectionIndex + 1`)를 부여함.
- **전사는 문장별 실시간 전송, 요약·카드는 섹션별 전송**:
  - 전사(`Transcript`)는 문장이 확정될 때마다 `sectionIndex`를 붙여 즉시 개별 전송하고, 프론트엔드(`buildSectionViews()`)가 같은 `sectionIndex`끼리 묶어 화면에 표시함.
  - 섹션 내 발화 누적 시간(`elapsedSec = lastEndSec - startSec`)이 **15초**에 도달하면 부분 요약(`PARTIAL`), **30초**에 도달하면 최종 요약(`FINAL`)을 위해 해당 섹션의 원문들을 하나로 합쳐 AI 서버로 전송함.

---

## 2. 파이프라인별 상세 통신 명세

시스템의 전체 데이터 흐름은 **1) 음성·전사 → 2) 요약 → 3) QA & 4) REC (병렬)**의 4대 실시간 파이프라인과 이를 뒷받침하는 **5) RAG 파이프라인**으로 구성됨. 백엔드와 AI 서버 간 모든 통신은 `X-Internal-Api-Key` 헤더로 인증함.

---

### 2.1 음성 및 실시간 전사 (Audio & Transcription) 파이프라인

| 단계 | 구간 (From → To) | 통신 방식 (경로) | 데이터 포맷 | 데이터 내용 | 전송 시점 / 주기 | 저장 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 프론트 → 백엔드 | 순수 WS (`/ws/transcription`) | Binary (`PCM16`, 24kHz, Mono) | 마이크 원본 음성 조각 | **약 0.17초마다** (4096 샘플 버퍼가 찰 때마다) | 미저장 |
| 2 | 백엔드 → OpenAI | 순수 WS (`wss://api.openai.com/v1/realtime`) | JSON (오디오 `Base64` 인코딩) | `input_audio_buffer.append` 이벤트 | 프론트로부터 바이너리 수신 즉시 중계 | 미저장 |
| 3-A | OpenAI → 백엔드 | 순수 WS | JSON 텍스트 프레임 | `...transcription.delta` (말하는 중인 글자 조각) | 발화 중 실시간 (수십~수백 ms 간격) | 미저장 |
| 3-B | OpenAI → 백엔드 | 순수 WS | JSON 텍스트 프레임 | `...transcription.completed` (완성된 한 문장) | 발화 후 **침묵 0.5초**(`silence_duration_ms: 500`) 감지 시 | - |
| 4-A | 백엔드 → 프론트 (녹음자 1:1) | 순수 WS (`/ws/transcription`) | JSON (`isFinal: false / true`) | `{type: "transcript", data: {content, isFinal}}` | OpenAI로부터 `delta` 또는 `completed` 수신 즉시 | 미저장 |
| 4-B | 백엔드 → 프론트 (전체 1:N) | WS STOMP (`/topic/lectures.{id}.transcripts`) | STOMP + JSON (`isFinal: true`) | `sectionIndex`, `startSec`, `endSec`, `text` | `completed` 문장의 섹션 배정 및 DB 저장 직후 | **RDB 저장** (`Transcript`) |

- **관련 파일**:
  - 프론트엔드: `frontend/src/features/session/audio/useAudioRecording.ts`, `frontend/src/features/session/audio/pcm.ts`
  - 백엔드: `RealtimeTranscriptionWebSocketHandler.java`, `OpenAiTranscriptionSession.java`, `TranscriptService.java`
- **섹션 전환 알림**: 섹션 번호가 바뀔 때마다 백엔드는 `/topic/lectures.{id}.section` 토픽으로 새 `sectionIndex`를 브로드캐스트함.

---

### 2.2 섹션 요약 (Summary) 파이프라인

| 단계 | 구간 (From → To) | 통신 방식 (경로) | 데이터 포맷 | 데이터 내용 | 전송 시점 / 주기 | 저장 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 백엔드 → AI 서버 | HTTP POST (`/summary/generate`) | JSON | `lecture_id`, `section_index`, `phase`(`PARTIAL`/`FINAL`), `transcript`(섹션 누적 원문), `callback_url` | 섹션 내 전사 길이가 **15초(`PARTIAL`)**, **30초(`FINAL`)** 도달 시 | - |
| 2 | AI 서버 → 백엔드 | HTTP POST 콜백 (`/api/ai/callback?type=summary`) | JSON | `lecture_id`, `section_index`, `phase`, `text`(요약 결과), `status` | AI 서버가 LLM 요약 생성을 끝낸 직후 (비동기 웹훅) | `PARTIAL`: 미저장 / `FINAL`: **RDB 저장** (`Summary`) |
| 3 | 백엔드 → 프론트 (전체 1:N) | WS STOMP (`/topic/lectures.{id}.summary`) | STOMP + JSON | `{type: "summary", sectionIndex, text, phase}` | AI 서버 콜백 수신 직후 | - |

- **관련 파일**: `SectionAggregationService.java`, `AiServerClient.java`, `AiCallbackController.java`, `SummaryCallbackService.java`
- **결과에 따른 연쇄 트리거**:
  - **15초 `PARTIAL` 요약 도착 시**: DB에는 저장하지 않고 화면에만 전송한 뒤, **QA 생성(`CONCEPT`, `APPLICATION`)과 자료 추천(`WIKI`, `BLOG`)을 동시에 자동 호출**함 (`CardRequestService.startAutoCards()`). 30초가 끝날 때까지 기다리지 않고 15초 시점에 카드를 미리 생성해 체감 지연을 단축함.
  - **30초 `FINAL` 요약 도착 시**: DB에 최종 요약본을 저장하고 화면에 전송한 뒤, **AI 서버 RAG 저장소에 최종 요약 텍스트를 업서트**함.

---

### 2.3 질문 및 답변 (QA) 파이프라인

| 단계 | 구간 (From → To) | 통신 방식 (경로) | 데이터 포맷 | 데이터 내용 | 전송 시점 / 주기 | 저장 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 백엔드 → AI 서버 | HTTP POST (`/qa/generate`) | JSON 요청 (`Accept: text/event-stream`) | `lecture_id`, `section_index`, `section_summary`, `subject`, `previous_qa`, `question_types` | **자동**: 15초 `PARTIAL` 요약 콜백 직후 / **수동**: 사용자가 섹션 클릭 시 추가 생성 요청 | - |
| 2 | AI 서버 → 백엔드 | **SSE** (`text/event-stream`) | SSE 이벤트 (`start`, `question`, `answer`, `done`, `error`) + JSON | 생성 중인 질문·답변 글자 조각 및 완료 데이터 | LLM이 토큰을 생성할 때마다 실시간 스트리밍 | `done` 이벤트 시 **RDB 저장** (`Qna`) |
| 3-A | 백엔드 → 프론트 (전체 1:N) | WS STOMP (`/topic/lectures.{id}.stream`) | STOMP + JSON | `{type: "qna_stream", cardId, isComplete: false/true, token, title}` | AI 서버 SSE 토큰을 받는 즉시 실시간 중계 | - |
| 3-B | 백엔드 → 프론트 (전체 1:N) | WS STOMP (`/topic/lectures.{id}.qna`) | STOMP + JSON | `{type: "qna", sectionIndex, items: [...]}` | 모든 QnA 카드 DB 저장 완료 직후 전체 목록 전송 | - |

- **관련 파일**: `CardRequestService.java`, `QnaStreamService.java`, `StreamGateway.java`
- **특징**: 요약이나 추천과 달리 QnA는 콜백(Webhook)을 쓰지 않고, 요청에 대한 응답 연결을 유지한 채 **SSE(Server-Sent Events)**로 토큰을 스트리밍 받아 STOMP로 즉시 변환 중계함.

---

### 2.4 자료 추천 (Recommendation, REC) 파이프라인

| 단계 | 구간 (From → To) | 통신 방식 (경로) | 데이터 포맷 | 데이터 내용 | 전송 시점 / 주기 | 저장 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 백엔드 → AI 서버 | HTTP POST (`/rec/recommend`) | JSON | `lecture_id`, `section_index`, `section_summary`, `previous_summaries`, 제외 목록(`yt_exclude` 등), `resource_types`, `callback_url` | **자동**: 15초 `PARTIAL` 요약 직후 (`WIKI`, `BLOG`) / **수동**: 섹션 선택 시 추가 요청 (`YOUTUBE`, `PAPER` 등) | - |
| 2 | AI 서버 → 백엔드 | HTTP POST 콜백 (`/api/ai/callback?type=resources`) | JSON | 외부 API 검색 및 관련성 평가가 완료된 추천 자료 배열 | 외부 검색(위키, 네이버 블로그, YouTube 등) 완료 직후 | **RDB 저장** (`Resource`) |
| 3 | 백엔드 → 프론트 (전체 1:N) | WS STOMP (`/topic/lectures.{id}.resources`) | STOMP + JSON | `{type: "resources", sectionIndex, items: [...]}` | 콜백 수신 및 DB 저장 직후 (카드별 타이핑 스트림도 `/stream`으로 선전송) | - |

- **관련 파일**: `CardRequestService.java`, `ResourceCallbackService.java`

---

### 2.5 RAG (지식 베이스 색인) 파이프라인

| 구분 | 구간 (From → To) | 통신 방식 (경로) | 데이터 포맷 | 데이터 내용 | 전송 시점 / 주기 | 저장 여부 |
| --- | --- | --- | --- | --- | --- | --- |
| 교재 업로드 | 백엔드 → AI 서버 | HTTP POST (`/rag/pdf-upsert`) | `multipart/form-data` | `lecture_id`, PDF 원본 파일 | 강의 생성 시 사용자가 PDF 파일을 첨부했을 때 (동기 대기 후 `collection_id` 반환) | **ChromaDB 벡터 저장** |
| 요약 색인 | 백엔드 → AI 서버 | HTTP POST (`/rag/text-upsert`) | JSON | `lecture_id`, `items` (최종 요약문 텍스트 및 시간 메타데이터) | 30초 섹션의 `FINAL` 요약 콜백이 도착해 DB 저장된 직후 | **ChromaDB 벡터 저장** |

---

## 3. 시간 흐름에 따른 전체 동작 시나리오 (0초 ~ 30초)

1. **강의실 입장**: 프론트엔드가 `/ws`(STOMP) 회선을 연결하고 해당 강의의 모든 토픽(`transcripts`, `summary`, `qna`, `resources`, `stream`, `section`, `error`)을 구독함.
2. **녹음 시작 (0초)**: 프론트엔드가 `/ws/transcription`(순수 WS)을 열고 0.17초마다 `PCM16` 음성을 전송함 → 백엔드가 OpenAI Realtime WS로 중계함.
3. **0초 ~ 15초 (실시간 전사)**:
   - 발화 중: OpenAI `delta` → 백엔드 `/ws/transcription` → 녹음자 화면에 즉시 타이핑 표시.
   - 문장 종료(침묵 0.5초): OpenAI `completed` → 백엔드 DB 저장(`sectionIndex = 0`) → STOMP `/transcripts`로 전체 브로드캐스트.
4. **15초 도달 (`PARTIAL` 트리거)**:
   - 백엔드가 0~15초 전사 원문을 묶어 AI 서버에 `PARTIAL` 요약 요청(`POST /summary/generate`).
   - AI 서버가 요약 콜백 반환 → 백엔드가 STOMP `/summary`로 화면에 중간 요약 표시 (DB 미저장).
   - **동시에 백엔드가 AI 서버로 QnA 생성(`POST /qa/generate` SSE) 및 자료 추천(`POST /rec/recommend`)을 자동 요청** → 완성되는 대로 STOMP `/stream`, `/qna`, `/resources`로 화면에 카드 노출 및 DB 저장.
5. **30초 도달 (`FINAL` 트리거 및 섹션 전환)**:
   - 백엔드가 0~30초 전사 원문 전체를 묶어 AI 서버에 `FINAL` 요약 요청(`POST /summary/generate`) 및 다음 섹션 번호(`sectionIndex = 1`)를 STOMP `/section`으로 알림.
   - AI 서버가 최종 요약 콜백 반환 → 백엔드가 DB에 요약 저장 → STOMP `/summary`로 확정 요약 브로드캐스트 → AI 서버 `/rag/text-upsert`로 벡터 DB에 요약본 색인.
   - 이후 들어오는 음성 전사는 `sectionIndex = 1`로 배정되며 위 과정이 30초 단위로 반복됨.

