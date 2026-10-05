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
| 실제 환경 연동 확인 | 완료 (브라우저 → 백엔드 → AI 서버 → OpenAI) |
| 원격 저장소 push | **미실시** (로컬 `main`에만 커밋됨) |
| 백엔드·AI 서버의 기존 문제 | 미해결 (6절) |

이전 버전의 이 문서(커밋 `2d0c46f`)는 재작성 착수 전 설계를 담고 있다. 설계 결정의 근거가 필요하면 그 버전을 참고한다.

---

## 2. 저장소

- `vysryoo/LiveNote` (원본 `Team-GongGong-s/LiveNote_frontend`의 포크, public), 기본 브랜치 `main`
- 로컬 remote는 `origin` 하나
- 모노레포 구성: `frontend/`(React), `backend/`(Spring Boot), `ai/`(FastAPI)
- 원본 팀 저장소 히스토리에 노출됐던 배포 키는 폐기된 것으로 사용자가 확인함

---

## 3. 로컬 실행 환경 (macOS)

### 3-1. 설치된 도구

모두 Homebrew로 설치했고 keg-only라 PATH에 자동 등록되지 않는다.

| 도구 | Homebrew 패키지 | 용도 |
| --- | --- | --- |
| Node.js 22 | `node@22` | 프론트엔드 |
| Java 17 | `openjdk@17` | 백엔드 |
| PostgreSQL 17 | `postgresql@17` (`brew services`로 상시 실행) | 백엔드 DB |
| Python 3.11 | `python@3.11` | AI 서버 |

```bash
export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/opt/openjdk@17/bin:/opt/homebrew/opt/postgresql@17/bin:$PATH"
```

npm 10은 `vitest` 등 선택적 peer 의존성이 많은 패키지 설치 시 `Cannot read properties of null (reading 'edgesOut')` 오류를 냄. 패키지 추가는 `npx -y npm@11 install ...`로 수행함.

### 3-2. 설정 파일

모두 git 무시 대상이며 값은 이 문서에 적지 않는다.

| 파일 | 내용 |
| --- | --- |
| `backend/src/main/resources/env.properties` | PostgreSQL 접속 정보(앱 전용 계정 `livenote`, DB `livenote`), OpenAI 키, JWT 비밀값(Base64, 32바이트 이상), AI 서버 주소 |
| `ai/.env` | OpenAI 키. YouTube·Google 키는 미확보라 `not-configured` 임시값 (6-3 참조) |
| `frontend/.env` | 불필요. 개발 서버가 `/api`를 8080으로 프록시하고 실시간 연결은 `ws://localhost:8080` 기본값 사용 |

### 3-3. 실행 순서

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

## 4. 프론트엔드 구조와 규칙

파일 구조는 `frontend/README.md` 참조.

| 영역 | 내용 |
| --- | --- |
| 라우팅 | React Router. `/`, `/signup`, `/lectures`, `/lectures/:lectureId`, `/settings`. 화면별 lazy 로딩 |
| 서버 상태 | TanStack Query. 키는 `["auth","me"]`, `["lectures","list"]`, `["lectures","detail",id]`, `["lectures","detail",id,"currentSection"]` |
| 실시간 상태 | `features/session/state/sessionReducer.ts`. 서버에 완성본이 없는 것(실시간 전사, 생성 중 카드)만 담음 |
| 현재 섹션 | Query 캐시에만 존재. 쓰기 지점은 STOMP `/section` 처리 함수 하나 |
| STOMP 처리 | `features/session/realtime/handlers.ts`의 순수 함수. 연결·재연결 시 강의 상세를 다시 받음 (주기적 조회 없음) |
| 폼 | react-hook-form + zod. 폼 제출 실패는 폼 안에, 성공과 폼 외 실패는 토스트로 표시 |
| 다국어 | i18next, 4개 언어(`ko`, `en`, `ja`, `zh`). 키 타입 검사 적용 |
| 린트 | React Compiler 규칙 18종 포함 에러 0·경고 0 상태. `src/shared/ui`(shadcn/ui)만 제외 |
| 테스트 | Vitest 64개. reducer, 메시지 스키마, STOMP 처리 함수, 표시용 순수 함수, HTTP 클라이언트 |

주의할 규칙.

- `Trans` 컴포넌트에는 항상 `t={t}`를 넘긴다. 넘기지 않으면 React Compiler가 이전 언어의 `Trans`를 재사용해 언어 변경이 반영되지 않음
- 스트리밍 카드의 섹션 번호는 카드 ID(`{접두사}_{강의}_{섹션}_{카드}`)에서 꺼낸다. 백엔드 `/stream` 메시지에 `sectionIndex` 필드가 없고, 접두사는 코드 경로마다 `qna`, `res`, `resource`로 다름. 카드 종류는 메시지의 `type`으로 판단함
- 백엔드 응답은 zod로 검사한다. 대소문자(`FINAL`/`final` 등)와 누락 값을 허용하도록 작성되어 있음

---

## 5. 검증 방법

### 5-1. 자동 검사

```bash
cd frontend
npm run typecheck
npm run lint
npm test
npm run build
```

백엔드 `./gradlew test`는 기존 테스트 3개 문제로 실패함 (6-1 참조).

### 5-2. 실제 환경 확인 (마이크 없이)

headless Chrome에 오디오 파일을 가짜 마이크로 넣어 녹음부터 요약·QnA까지 확인할 수 있다.

```
--use-fake-ui-for-media-stream
--use-fake-device-for-media-stream
--use-file-for-fake-audio-capture=<WAV 경로>
--disable-features=AudioServiceSandbox
```

- macOS에서는 `AudioServiceSandbox`를 끄지 않으면 파일을 읽지 못하고 무음이 입력됨
- `afconvert`로 만든 WAV는 읽지 못함. Python `wave` 모듈로 쓴 16비트 PCM WAV를 사용함
- 합성 음성은 `say -v Yuna "..." -o 파일.aiff`로 만든 뒤 변환함

---

## 6. 남은 문제

### 6-1. 백엔드

| 문제 | 근거 |
| --- | --- |
| 로그인 토큰이 1시간 뒤 만료되고 갱신 수단이 없음. 1시간이 넘는 녹음 중 요청이 거부될 수 있음 | `application.yml`의 `app.jwt.expiration: 3600000` |
| 강의 목록이 최근 20개만 반환됨. 화면의 "지금까지 N개" 숫자도 20에서 멈춤 | `LectureController.list()`의 `PageRequest.of(0, 20)` |
| 강의 삭제·제목 변경·종료 API가 소유자를 확인하지 않음 | `LectureController`의 `delete`, `updateTitle`, `endLecture` |
| 강의 종료 API가 요청 본문(제목)을 읽지 않음. 프론트엔드가 제목 변경 API를 먼저 호출해 우회 중 | `LectureController.endLecture()` |
| 발화 시간을 실제보다 길게 계산함 (여유 2초, 배율 1.2). 화면 경과 시간이 실제보다 빠름 | `app.transcription.padding-seconds`, `speed-multiplier` |
| 기존 테스트 3개 실패. `AiRequestServiceTest`는 컴파일 오류로 `./gradlew test` 전체를 막음. `QnaCallbackServiceTest`, `ResourceCallbackServiceTest`는 실행 후 실패 | 본 코드 변경 후 테스트 미수정 (PostgreSQL 전환 전부터 존재) |

### 6-2. AI 서버

| 문제 | 근거 |
| --- | --- |
| PDF 없이 만든 강의의 첫 섹션에 QnA·자료 추천이 생성되지 않음. `/rec/recommend`가 400을 반환함 | `rec.py`에서 400을 내는 경우는 RAG 검색 실패와 자료 유형 없음뿐. RAG 컬렉션이 아직 없어서로 **추정**, 확인 필요 |
| 논문(OpenAlex) 추천의 성공·실패 로그가 남지 않은 사례가 있음 | 확인 시점에 처리 중이었는지 멈췄는지 미확인 |

### 6-3. 설정

- YouTube·Google 키가 없으면 AI 서버가 시작되지 않음(`google_config.py`의 시작 시 검사). 임시값으로 시작하게 했으며, 이 경우 영상·블로그 추천만 빈 결과가 됨

---

## 7. 미결 사항

1. 원격 저장소 push 여부
2. 영어·일본어·중국어 번역 검토. 재작성 중 추가한 문구 약 100개는 에이전트가 작성함
3. YouTube·Google 키 확보
4. 6절 문제의 처리 순서

---

## 8. 사용자 응대 시 참고

- 사용자는 프론트엔드 라이브러리와 아키텍처 패턴에 대한 사전 지식이 많지 않다. 선택지를 제시할 때는 이 저장소의 실제 코드를 근거로 먼저 설명한 뒤 고르게 한다
- 결정이 필요한 질문은 한 번에 하나씩 묻는다
- 각 단계는 시작 전에 무엇을 어떻게 할지 설명하고 동의를 받은 뒤 진행해 왔다
- 커밋은 성격별로 나누고, 각 커밋이 단독으로 빌드·테스트를 통과하는지 확인해 왔다
