# 작업 인수인계

이 문서는 다음 작업자(사람 또는 에이전트)가 대화 맥락 없이 작업을 이어받기 위한 것이다.

작업 시작 전 `AGENTS.md`를 읽는다. 코드를 한 줄이라도 수정한다면 `.agent/coding.md`를 먼저 읽는다.

---

## 1. 현재 상태 요약

| 항목 | 상태 |
| --- | --- |
| 프론트엔드 재작성 (M1~M7) | 완료 |
| 백엔드 DB 전환 (MySQL → PostgreSQL + Flyway) | 완료 |
| 실시간 전사 (OpenAI Realtime 정식 API 전환) | 완료 |
| 인증·소유자 확인 (REST, 녹음 WebSocket, STOMP, 백엔드↔AI 서버) | 완료 |
| 통신 구조 개선 R1~R7 (2절) | 완료 |
| 남은 문제 | 7절 |

이전 버전의 이 문서(커밋 `2d0c46f`)는 재작성 착수 전 설계를 담고 있다. 설계 결정의 근거가 필요하면 그 버전을 참고한다.

---

## 2. 통신 구조 개선 (R1~R7) 요약

| 단계 | 내용 |
| --- | --- |
| R1 | 쓰지 않는 WebSocket 핸들러, STOMP 엔드포인트, 모의 스트리밍 코드 삭제 |
| R2 | 백엔드 콜백의 가짜 토큰 스트리밍(카드당 약 3초 인위적 지연) 제거. 자료 카드 글자 연출은 프론트엔드가 담당 |
| R3 | Redis, RabbitMQ 설치 |
| R4 | STOMP 메시지를 RabbitMQ로 중계(`enableStompBrokerRelay`). 토픽 주소를 점 구분 형식으로 변경. 와일드카드 구독과 클라이언트 SEND 차단 |
| R5 | 섹션 상태와 시각 보정값을 Redis로 이전(재시작 후에도 섹션 번호 유지). 카드 저장 잠금을 Redis 잠금으로 바꾸고 DB 저장 확정 후 해제 |
| R6 | QnA를 실제 스트리밍으로 전환. AI 서버 → 백엔드는 SSE, 백엔드 → 브라우저는 STOMP |
| R7 | 자료 카드에 추천 이유 표시. AI 서버의 자리 표시 값(`Heuristic`, `search`, `검증 실패…` 등)은 숨김 |

R4·R5는 백엔드를 여러 대로 늘릴 수 있게 하기 위한 작업이다. 서버 두 대(8080, 8081)를 띄워 서버 간 메시지 전달과 동시 콜백의 카드 번호 중복 방지를 확인했다.

---

## 3. 저장소

- `vysryoo/LiveNote` (원본 `Team-GongGong-s/LiveNote_frontend`의 포크, public), 기본 브랜치 `main`
- 로컬 remote는 `origin` 하나
- 모노레포 구성: `frontend/`(React), `backend/`(Spring Boot), `ai/`(FastAPI)
- 원본 팀 저장소 히스토리에 노출됐던 배포 키는 폐기된 것으로 사용자가 확인함

---

## 4. 로컬 실행 환경 (macOS)

### 4-1. 설치된 도구

모두 Homebrew로 설치했다. Node.js, Java, PostgreSQL, Python은 keg-only라 PATH에 자동 등록되지 않는다. RabbitMQ 관리 명령(`rabbitmqctl`, `rabbitmq-plugins`)은 `/opt/homebrew/sbin`에 있다.

| 도구 | Homebrew 패키지 | 용도 |
| --- | --- | --- |
| Node.js 22 | `node@22` | 프론트엔드 |
| Java 17 | `openjdk@17` | 백엔드 |
| PostgreSQL 17 | `postgresql@17` (`brew services`로 상시 실행) | 백엔드 DB |
| Python 3.11 | `python@3.11` | AI 서버 |
| Redis 8 | `redis` (`brew services`로 상시 실행) | 녹음 상태(섹션, 시각 보정값), 카드 번호 예약, 잠금 |
| RabbitMQ 4 | `rabbitmq` (`brew services`로 상시 실행, `rabbitmq_stomp` 플러그인) | STOMP 메시지 중계 |

RabbitMQ는 앱 전용 계정·vhost(`livenote`)를 만들었고, STOMP·관리 화면 포트를 `127.0.0.1`에만 열도록 `/opt/homebrew/etc/rabbitmq/rabbitmq.conf`를 설정했다. 설치 절차는 `backend/README.md` 참조.

```bash
export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/opt/openjdk@17/bin:/opt/homebrew/opt/postgresql@17/bin:$PATH"
```

npm 10은 `vitest` 등 선택적 peer 의존성이 많은 패키지 설치 시 `Cannot read properties of null (reading 'edgesOut')` 오류를 냄. 패키지 추가는 `npx -y npm@11 install ...`로 수행함.

### 4-2. 설정 파일

모두 git 무시 대상이며 값은 이 문서에 적지 않는다.

| 파일 | 내용 |
| --- | --- |
| `backend/src/main/resources/env.properties` | PostgreSQL 접속 정보(앱 전용 계정 `livenote`, DB `livenote`), OpenAI 키, JWT 비밀값(Base64, 32바이트 이상), AI 서버 주소, AI 서버와 공유하는 내부 키(`INTERNAL_API_KEY`), RabbitMQ 계정(`RABBITMQ_*`), Redis 주소(`REDIS_*`) |
| `ai/.env` | OpenAI 키, 내부 키(`INTERNAL_API_KEY`, 백엔드와 같은 값). YouTube·Google 키는 미확보라 `not-configured` 임시값 (7-3 참조) |
| `frontend/.env` | 불필요. 개발 서버가 `/api`를 8080으로 프록시하고 실시간 연결은 `ws://localhost:8080` 기본값 사용 |

### 4-3. 실행 순서

PostgreSQL, Redis, RabbitMQ가 `brew services`로 실행 중이어야 한다. Redis와 RabbitMQ가 꺼져 있어도 백엔드는 시작된다(확인함). 다만 실시간 메시지 중계는 RabbitMQ에, 전사·카드 저장 시의 섹션 상태와 잠금은 Redis에 의존한다.

```bash
# AI 서버 (:8003)
cd ai && source .venv/bin/activate && uvicorn server.main:app --port 8003

# 백엔드 (:8080) — 시작 시 Flyway가 마이그레이션 적용
cd backend && ./gradlew bootRun

# 프론트엔드 (:3000)
cd frontend && npm run dev
```

AI 서버 가상환경은 `PYTHON_BIN=/opt/homebrew/opt/python@3.11/bin/python3.11 ./setup.sh`로 만들었다.

---

## 5. 통신 구조

| 구간 | 방식 | 인증 |
| --- | --- | --- |
| 브라우저 → 백엔드 REST | HTTP `/api/**` | `Authorization: Bearer {접근 토큰}`(30분). 다른 사용자의 강의는 404. 401을 받으면 프론트엔드가 `POST /api/auth/refresh`(갱신 토큰 `HttpOnly` 쿠키, 14일, Redis 저장, 사용 시 교체)로 새 토큰을 받아 한 번 재요청 |
| 브라우저 → 백엔드 녹음 | WebSocket `/ws/transcription?sessionId={강의}&token={JWT}` (PCM16 24kHz) | 브라우저 WebSocket은 헤더를 붙일 수 없어 쿼리로 토큰 전달. 연결할 때만 확인하므로 프론트엔드가 만료 1분 전이면 먼저 갱신. 강의 소유자 확인 |
| 백엔드 → 브라우저 실시간 | STOMP `/ws`, 토픽 `/topic/lectures.{강의}.{이름}` (transcripts, summary, section, qna, resources, stream, error) | CONNECT 프레임의 `Authorization` 헤더. 연결·재연결 직전에 만료가 임박했으면 먼저 갱신. 본인 강의 토픽만 구독 가능. 클라이언트 SEND 거부 |
| 백엔드 내부 STOMP 중계 | RabbitMQ STOMP(61613)로 relay | 앱 전용 계정. 확인을 마친 JWT는 RabbitMQ로 넘기기 전 제거 |
| 백엔드 → AI 서버 요청 | HTTP | `X-Internal-Api-Key` |
| AI 서버 → 백엔드 (요약·자료 추천) | 콜백 `POST /api/ai/callback?type=summary\|resources` | `X-Internal-Api-Key`. 틀리면 401 |
| AI 서버 → 백엔드 (QnA) | `POST /qa/generate`의 SSE 응답 (`start`, `question`, `answer`, `done`, `error`) | 요청에 `X-Internal-Api-Key` |
| 백엔드 → OpenAI | Realtime API(전사) | OpenAI 키 |

QnA 흐름: 백엔드가 SSE의 `start`를 받으면 Redis에 카드 번호를 예약하고, `question`·`answer`를 STOMP `stream` 토픽으로 그대로 중계한다. `done`을 받으면 DB에 저장하고 완료 메시지와 섹션 전체 QnA 목록을 보낸다. 상세 형식은 `ai/README.md` 6.3절 참조.

개발용 API(`TestController` 등)는 `dev` 프로필에서만 등록된다.

---

## 6. 프론트엔드 구조와 규칙

파일 구조는 `frontend/README.md` 참조.

| 영역 | 내용 |
| --- | --- |
| 라우팅 | React Router. `/`, `/signup`, `/lectures`, `/lectures/:lectureId`, `/settings`. 화면별 lazy 로딩 |
| 서버 상태 | TanStack Query. 키는 `["auth","me"]`, `["lectures","list"]`, `["lectures","detail",id]`, `["lectures","detail",id,"currentSection"]` |
| 실시간 상태 | `features/session/state/sessionReducer.ts`. 서버에 완성본이 없는 것(실시간 전사, 생성 중 카드)만 담음 |
| 현재 섹션 | Query 캐시에만 존재. 쓰기 지점은 STOMP `section` 처리 함수 하나 |
| STOMP 처리 | `features/session/realtime/handlers.ts`의 순수 함수. 연결·재연결 시 강의 상세를 다시 받음 (주기적 조회 없음) |
| 카드 연출 | QnA는 생성 중 카드에 실제 토큰이 쌓이고, 완성 후에는 연출 없음. 자료 카드는 분할 화면을 연 뒤 도착한 카드에만 초당 약 100자 글자 연출(`useTypewriter`) |
| 폼 | react-hook-form + zod. 폼 제출 실패는 폼 안에, 성공과 폼 외 실패는 토스트로 표시 |
| 다국어 | i18next, 4개 언어(`ko`, `en`, `ja`, `zh`). 키 타입 검사 적용 |
| 린트 | React Compiler 규칙 18종 포함 에러 0·경고 0 상태. `src/shared/ui`(shadcn/ui)만 제외 |
| 테스트 | Vitest 71개. reducer, 메시지 스키마, STOMP 처리 함수, 표시용 순수 함수, HTTP 클라이언트 |

주의할 규칙.

- `Trans` 컴포넌트에는 항상 `t={t}`를 넘긴다. 넘기지 않으면 React Compiler가 이전 언어의 `Trans`를 재사용해 언어 변경이 반영되지 않음
- 스트리밍 카드의 섹션 번호는 카드 ID(`{접두사}_{강의}_{섹션}_{카드}`)에서 꺼낸다. 백엔드 `stream` 메시지에 `sectionIndex` 필드가 없고, 접두사는 코드 경로마다 `qna`, `res`, `resource`로 다름. 카드 종류는 메시지의 `type`으로 판단함
- 백엔드 응답은 zod로 검사한다. 대소문자(`FINAL`/`final` 등)와 누락 값을 허용하도록 작성되어 있음
- STOMP 토픽 주소에 `/`를 쓰지 않는다. RabbitMQ STOMP가 `/topic/` 뒤의 `/`를 `Invalid destination`으로 거부함

---

## 7. 검증 방법

### 7-1. 자동 검사

```bash
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
cd backend && ./gradlew test        # 36개. 컨텍스트 로딩 테스트에 PostgreSQL 필요 (Redis·RabbitMQ 없이도 통과 확인)
cd ai && .venv/bin/python -m pytest -q tests
```

AI 서버 테스트는 `test_rag_text.py::test_text_upsert_preserves_metadata` 1개가 실패한다. 통신 구조 개선 전부터 실패하던 테스트다.

### 7-2. 실제 환경 확인 (마이크 없이)

headless Chrome에 오디오 파일을 가짜 마이크로 넣어 녹음부터 요약·QnA까지 확인할 수 있다.

```
--use-fake-ui-for-media-stream
--use-fake-device-for-media-stream
--use-file-for-fake-audio-capture=<WAV 경로>
--disable-features=AudioServiceSandbox
```

- macOS에서는 `AudioServiceSandbox`를 끄지 않으면 파일을 읽지 못하고 무음이 입력됨
- `afconvert`로 만든 WAV는 읽지 못함. Python `wave` 모듈로 다시 쓴 16비트 PCM WAV를 사용함
- 합성 음성은 문장마다 `say -v Yuna "..." -o 파일.aiff`로 만든 뒤 문장 사이에 1초 이상 무음을 넣는다. 쉼 없이 이어진 음성은 OpenAI의 발화 종료 감지가 동작하지 않아 녹음을 멈출 때까지 전사가 오지 않음

### 7-3. 여러 서버 확인

`./gradlew bootJar`로 만든 jar를 `--server.port=8080`, `--server.port=8081`로 두 번 실행한다. 한쪽에 보낸 콜백이 다른 쪽에 연결된 구독자에게 전달되는지, 같은 섹션 콜백을 두 서버에 동시에 보냈을 때 카드가 빠지지 않는지 확인할 수 있다.

---

## 8. 남은 문제

### 8-1. 백엔드

| 문제 | 근거 |
| --- | --- |
| 강의 종료 API가 요청 본문(제목)을 읽지 않음. 프론트엔드가 제목 변경 API를 먼저 호출해 우회 중 | `LectureController.endLecture()` |

### 8-2. AI 서버

| 문제 | 근거 |
| --- | --- |
| 위키 추천에 주제와 무관한 문서가 섞일 수 있음 (예: "Stack" 검색 시 인물 문서 "Robert Stack") | 위키 LLM 검증이 꺼져 있어 제목·본문의 키워드 일치로만 점수를 매김(`_heuristic_score_single`). 동음이의어 문서는 `pageprops`로 제외함 |
| 논문(OpenAlex) 추천의 성공·실패 로그가 남지 않은 사례가 있음 | 확인 시점에 처리 중이었는지 멈췄는지 미확인 |

### 8-3. 프론트엔드

| 문제 | 근거 |
| --- | --- |
| 먼저 완성된 QnA 카드가 아직 생성 중인 카드 위로 올라감 | `SplitPane`이 완성 카드 목록 아래에 생성 중 카드를 따로 붙여 렌더링함 |

### 8-4. 설정

- YouTube·Google 키가 없으면 AI 서버가 시작되지 않음(`google_config.py`의 시작 시 검사). 임시값으로 시작하게 했으며, 이 경우 영상·블로그 추천만 빈 결과가 됨

---

## 9. 미결 사항

1. 영어·일본어·중국어 번역 검토. 재작성 중 추가한 문구 약 100개와 "추천 이유" 문구는 에이전트가 작성함
2. YouTube·Google 키 확보
3. 8절 문제의 처리 순서

---

## 10. 사용자 응대 시 참고

- 사용자는 프론트엔드 라이브러리와 아키텍처 패턴에 대한 사전 지식이 많지 않다. 선택지를 제시할 때는 이 저장소의 실제 코드를 근거로 먼저 설명한 뒤 고르게 한다
- 설명과 보고는 한국어로 한다
- 결정이 필요한 질문은 한 번에 하나씩 묻는다
- 각 단계는 시작 전에 무엇을 어떻게 할지 설명하고 동의를 받은 뒤 진행해 왔다
- 커밋은 성격별로 나누고, 각 커밋이 단독으로 빌드·테스트를 통과하는지 확인해 왔다. 커밋과 push는 사용자가 요청할 때만 한다
