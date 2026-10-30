# 작업 인수인계

다음 작업자(사람 또는 에이전트)가 대화 맥락 없이 작업을 이어받기 위한 문서다.

작업 시작 전 `AGENTS.md`를 읽는다. 코드를 한 줄이라도 수정한다면 `.agent/coding.md`를 먼저 읽는다.

---

## 1. 현재 상태

프론트엔드 재작성, 백엔드 PostgreSQL 전환, 실시간 전사, 인증, 통신 구조 개선(RabbitMQ 중계, Redis 상태, QnA 스트리밍), AI 서버 리팩토링까지 끝났다. 자료 추천 4종(논문, 위키, 영상, 블로그)은 실제 키로 동작을 확인했다. 남은 문제는 7절.

재작성 착수 전 설계 결정의 근거가 필요하면 이 문서의 이전 버전(커밋 `2d0c46f`)을 참고한다.

---

## 2. 저장소

- `vysryoo/LiveNote` (원본 `Team-GongGong-s/LiveNote_frontend`의 포크, public), 기본 브랜치 `main`, remote는 `origin` 하나
- 모노레포: `frontend/`(React), `backend/`(Spring Boot), `ai/`(FastAPI)
- 원본 팀 저장소 히스토리에 노출됐던 배포 키는 폐기된 것으로 사용자가 확인함

---

## 3. 로컬 실행 (macOS)

Homebrew로 설치했다. Node.js, Java, PostgreSQL, Python은 keg-only라 PATH에 직접 넣는다.

| 도구 | 패키지 | 용도 |
| --- | --- | --- |
| Node.js 22 | `node@22` | 프론트엔드 |
| Java 17 | `openjdk@17` | 백엔드 |
| PostgreSQL 17 | `postgresql@17` (`brew services`) | 백엔드 DB |
| Redis 8 | `redis` (`brew services`) | 녹음 상태(섹션, 시각 보정값), 카드 번호 예약, 잠금 |
| RabbitMQ 4 | `rabbitmq` (`brew services`, `rabbitmq_stomp`) | STOMP 메시지 중계. 앱 전용 계정·vhost `livenote`, 포트는 `127.0.0.1`만. 설치 절차는 `backend/README.md` |
| Python 3.11, uv | `python@3.11`, `uv` | AI 서버 |

```bash
export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/opt/openjdk@17/bin:/opt/homebrew/opt/postgresql@17/bin:$PATH"

cd ai && uv run uvicorn server.main:app --port 8003   # AI 서버. 가상환경은 ai/setup.sh
cd backend && ./gradlew bootRun                       # 백엔드 :8080. 시작 시 Flyway 마이그레이션
cd frontend && npm run dev                            # 프론트엔드 :3000
```

설정 파일 (git 무시 대상, 값은 여기 적지 않음)

| 파일 | 내용 |
| --- | --- |
| `backend/src/main/resources/env.properties` | PostgreSQL(계정·DB `livenote`), OpenAI 키, JWT 비밀값(Base64, 32바이트 이상), AI 서버 주소, `INTERNAL_API_KEY`, `RABBITMQ_*`, `REDIS_*` |
| `ai/.env` | `OPENAI_API_KEY`, `INTERNAL_API_KEY`(백엔드와 같은 값), `YOUTUBE_API_KEY`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`. 하나라도 비면 AI 서버가 시작되지 않음 |
| `frontend/.env` | 불필요. 개발 서버가 `/api`를 8080으로 프록시 |

- Redis·RabbitMQ가 꺼져 있어도 백엔드는 시작되지만, 실시간 중계는 RabbitMQ에, 섹션 상태와 잠금은 Redis에 의존한다
- npm 10은 선택적 peer 의존성이 많은 패키지 설치 시 `edgesOut` 오류를 낸다. 패키지 추가는 `npx -y npm@11 install ...`

---

## 4. 통신 구조

| 구간 | 방식 | 인증 |
| --- | --- | --- |
| 브라우저 → 백엔드 REST | `/api/**` | `Authorization: Bearer`(30분). 다른 사용자의 강의는 404. 401이면 `POST /api/auth/refresh`(갱신 토큰 `HttpOnly` 쿠키, 14일, Redis, 사용 시 교체) 후 한 번 재요청 |
| 브라우저 → 백엔드 녹음 | WebSocket `/ws/transcription?sessionId={강의}&token={JWT}` (PCM16 24kHz) | 쿼리 토큰. 연결 시에만 확인하므로 만료 1분 전이면 먼저 갱신. 강의 소유자 확인 |
| 백엔드 → 브라우저 | STOMP `/ws`, 토픽 `/topic/lectures.{강의}.{이름}` (transcripts, summary, section, qna, resources, stream, error) | CONNECT의 `Authorization`. 본인 강의 토픽만 구독. 클라이언트 SEND 거부 |
| 백엔드 STOMP 중계 | RabbitMQ STOMP(61613) | 앱 전용 계정. 확인을 마친 JWT는 넘기기 전 제거 |
| 백엔드 ↔ AI 서버 | HTTP 요청, 콜백 `POST /api/ai/callback?type=summary\|resources`, QnA는 SSE | 양방향 `X-Internal-Api-Key`. 형식은 `ai/API_SPECIFICATION.md` |
| 백엔드 → OpenAI | Realtime API 전사 (`gpt-transcribe`) | OpenAI 키 |

- QnA: 백엔드가 SSE `start`에서 Redis에 카드 번호를 예약하고 `question`·`answer`를 STOMP `stream`으로 중계, `done`에서 DB에 저장한 뒤 섹션 전체 QnA를 보낸다
- 강의 데이터 조회는 `GET /api/lectures/{id}/detail` 하나. 녹음은 WebSocket 하나로만 받는다. 전체 API는 `backend/README.md`
- 개발용 API(`TestController` 등)는 `dev` 프로필에서만 등록된다
- 백엔드를 여러 대 띄워도 된다 (RabbitMQ 중계, Redis 상태·잠금). 8080·8081 두 대로 서버 간 전달과 동시 콜백의 카드 번호 중복 방지를 확인했다

---

## 5. 프론트엔드 규칙

파일 구조는 `frontend/README.md`.

| 영역 | 내용 |
| --- | --- |
| 라우팅 | React Router. `/`, `/signup`, `/lectures`, `/lectures/:lectureId`, `/settings`. 화면별 lazy 로딩 |
| 서버 상태 | TanStack Query. 키 `["auth","me"]`, `["lectures","list"]`, `["lectures","detail",id]`, `["lectures","detail",id,"currentSection"]` |
| 실시간 상태 | `features/session/state/sessionReducer.ts`. 서버에 완성본이 없는 것(실시간 전사, 생성 중 카드)만 |
| 현재 섹션 | Query 캐시에만 있음. 쓰기 지점은 STOMP `section` 처리 함수 하나 |
| STOMP 처리 | `features/session/realtime/handlers.ts`의 순수 함수. 연결·재연결 시 강의 상세를 다시 받음 |
| 카드 연출 | QnA는 실제 토큰이 쌓임. 자료 카드는 분할 화면을 연 뒤 도착한 카드에만 글자 연출(`useTypewriter`) |
| 폼 | react-hook-form + zod. 제출 실패는 폼 안, 그 외는 토스트 |
| 다국어 | i18next `ko`, `en`, `ja`, `zh`. 키 타입 검사 |

- `Trans` 컴포넌트에는 항상 `t={t}`를 넘긴다. 빠지면 React Compiler가 이전 언어의 `Trans`를 재사용함
- 스트리밍 카드의 섹션 번호는 카드 ID(`{접두사}_{강의}_{섹션}_{카드}`)에서 꺼낸다. `stream` 메시지에 `sectionIndex`가 없고 접두사는 경로마다 `qna`, `res`, `resource`로 다름. 카드 종류는 `type`으로 판단
- 백엔드 응답은 zod로 검사한다. 대소문자(`FINAL`/`final`)와 누락 값을 허용하도록 작성됨
- STOMP 토픽 주소에 `/`를 쓰지 않는다. RabbitMQ가 `Invalid destination`으로 거부함
- AI 서버의 자리 표시 이유(`Heuristic` 등)는 자료 카드에서 숨긴다

---

## 6. 검증 방법

```bash
cd frontend && npm run typecheck && npm run lint && npm test && npm run build   # Vitest 82개
cd backend && ./gradlew test     # 54개. PostgreSQL 필요 (Redis·RabbitMQ 없이도 통과)
cd ai && uv run pytest           # 109개, 외부 API 호출 없음
```

마이크 없이 실제 흐름 확인: headless Chrome에 오디오 파일을 가짜 마이크로 넣는다.

```
--use-fake-ui-for-media-stream --use-fake-device-for-media-stream
--use-file-for-fake-audio-capture=<WAV 경로> --disable-features=AudioServiceSandbox
```

- macOS는 `AudioServiceSandbox`를 끄지 않으면 무음이 입력됨
- `afconvert`로 만든 WAV는 못 읽음. Python `wave`로 다시 쓴 16비트 PCM WAV 사용
- 합성 음성은 문장마다 `say -v Yuna`로 만들고 문장 사이에 1초 이상 무음을 넣는다. 쉼이 없으면 OpenAI 발화 종료 감지가 동작하지 않음

---

## 7. 남은 문제

| 영역 | 문제 | 근거 |
| --- | --- | --- |
| AI | 위키 추천에 주제와 무관한 문서가 섞일 수 있음 (예: "Stack" → 인물 "Robert Stack") | 위키는 LLM 검증 없이 키워드 일치 휴리스틱으로 점수를 매김(`ai/recommend/providers/wiki.py`) |
| AI | 위키 언어 보충 시 점수가 아닌 검색 순서로 부족분을 고름 | 리팩토링에서 기존 동작을 유지함 |
| AI | 영상 후보마다 LLM을 2회(요약, 점수) 호출 | 1회로 합치려면 품질 측정 필요 |
| 설정 | YouTube 할당량 하루 10,000 단위, 영상 추천 1회 약 101 단위 | 오토 모드는 섹션마다 영상을 요청해 하루 녹음 약 50분에서 소진될 수 있음 |
| 설정 | 블로그는 네이버 블로그 검색(NAVER API HUB, 한시적 무료, 월 775,000건 공유 한도) | Google Custom Search가 신규 가입을 받지 않고 2027-01-01 종료 예정. 요청 필드 `google_exclude`는 호환을 위해 이름 유지 |
| 번역 | 영어·일본어·중국어 문구 검토 필요 | 재작성 중 추가한 문구 약 100개와 "추천 이유" 문구를 에이전트가 작성함 |

---

## 8. AI 서버

구조와 설정은 `ai/README.md`, API는 `ai/API_SPECIFICATION.md`.

- 모든 LLM 호출은 `ai/core/llm.py`(LangChain)를 거친다. 기본 모델 `gpt-6-luna`(추론 강도 none), 용도별로 바꿀 수 있다
- QnA·추천은 LangGraph로 항목을 동시에 실행한다. 추천은 공통 흐름(`recommend/pipeline.py`)과 공급자 4종으로 나뉜다
- 강의 자료 분할 기본값은 semantic. 기존에 저장된 강의 자료는 page 방식으로 나뉜 채 남아 있고, 새로 올리는 자료부터 적용된다
- 테스트는 추천·QnA 프롬프트와 결과를 스냅샷(`ai/tests/data/snapshots/`)으로 고정한다. 프롬프트를 바꾸면 `UPDATE_SNAPSHOTS=1 uv run pytest`로 갱신하고 diff를 확인한다

---

## 9. 평가

합성 강의 9개(공학·간호·예술 × 3, TTS 녹음)를 실제 서비스 경로로 넣어 섹션 전사·요약을 모으고, `gpt-6.1-terra`의 이진 판정 Precision@4로 측정했다. dev 3강으로 조정하고 test 6강에서 측정했다. 보고서는 `ai/eval/results/`.

| 측정 (test) | 변경 | 결과 |
| --- | --- | --- |
| 강의 자료 검색 | page → semantic 분할 | 75.6% → 88.5% (+13.0%p, 95% 신뢰구간 [+9.6, +16.2]) |
| QnA | 출제 범위 제한 (E2 → E13) | 75.0% → 87.9% (+12.9%p [+6.2, +20.0]). dev에서도 +11.5%p |
| QnA | 리팩토링 후 코드 (E13 → E14) | 87.9% → 88.8% (+0.8%p [-2.1, +4.2], 구간이 0을 포함해 차이 없음으로 봄). E2 대비 +13.8%p [+6.7, +21.2] |
| 추천 자료 | 리팩토링 후 코드 (E14) | 87.5% ±5.9%p. 논문 92.3%, 위키 80.0%, 영상 100%, 블로그 100%. 분야별 간호 92.5%, 공학 97.5%, 예술 72.5% |
| QnA 응답 시간 | LangGraph 전환 | 그래프 부담 1ms 미만. 질문 표시 중앙값 약 1.5초 |
| 전사 글자 오류율 (dev) | gpt-4o-transcribe → gpt-transcribe | 2.56% → 2.92% (영문·숫자 표기 차이 제외 1.37% → 1.72%) |

- 신뢰구간은 같은 섹션끼리 짝지은 부트스트랩 95% 구간
- E14 추천은 이전 비교 기준이 없어 개선 폭이 아닌 현재 수준이다. 측정 중 위키백과 문서 조회 23건이 429 재시도 후에도 실패했다 (모든 섹션에 위키 결과는 나옴)
- 추천 오답은 위키(휴리스틱, "인스타그램"처럼 주제와 무관한 문서)와 예술 분야 논문(주제 일부만 겹침)에 몰려 있다
- `E0_resource_test.md`(추천 80.0%)는 위키백과 429 오류로 위키 추천이 빠진 상태의 값이라 쓰지 않는다

미룬 실험

| 실험 | 비고 |
| --- | --- |
| 위키 추천 개선 | E14 오답이 몰린 위키를 LLM 검증으로 바꾸거나 휴리스틱 보강. dev에서 비교 후 결정 |
| 주제 전환이 잦은 강의(회의형) | 견고성 측정, 녹음을 주제 단위로 섹션 분할(백엔드 포함). 시나리오·지표를 측정 전에 고정 |
| 구조가 복잡한 자료(법학 판례) | page·recursive·semantic 비교. 지표를 측정 전에 고정 |

---

## 10. 사용자 응대 시 참고

- 설명과 보고는 한국어로 한다
- 사용자는 프론트엔드 라이브러리와 아키텍처 패턴의 사전 지식이 많지 않다. 이 저장소의 실제 코드를 근거로 먼저 설명한 뒤 고르게 한다
- 결정이 필요한 질문은 한 번에 하나씩 묻는다
- 각 단계는 시작 전에 무엇을 어떻게 할지 설명하고 동의를 받은 뒤 진행한다
- 비용이 드는 실행(OpenAI 등)은 견적을 내고 승인받은 뒤 한다
- 커밋은 성격별로 나누고 각 커밋이 단독으로 테스트를 통과하게 한다. 커밋과 push는 사용자가 요청할 때만 한다
