# LiveNote 백엔드

Spring Boot 기반의 실시간 강의 노트 서비스 백엔드입니다.

---

## 실행 방법

### 사전 준비

> [!IMPORTANT]
> `./gradlew bootRun` 실행 전 반드시 `env.properties` 파일을 먼저 생성해야 합니다.  
> 파일이 없으면 DB 연결, AI 서버 연동, JWT 인증 등이 작동하지 않습니다.

> [!NOTE]
> **gradlew**는 Gradle Wrapper로, **Java 17**만 설치되어 있으면 Gradle을 별도 설치하지 않아도 자동으로 필요한 Gradle 버전을 다운로드하고 실행합니다.

### PostgreSQL 준비

PostgreSQL 17 기준입니다. 빈 데이터베이스만 만들면 테이블은 앱 시작 시 Flyway가 `src/main/resources/db/migration`의 마이그레이션으로 생성합니다.

```bash
brew install postgresql@17
brew services start postgresql@17
psql -d postgres -c "CREATE ROLE livenote LOGIN PASSWORD '비밀번호';"
psql -d postgres -c "CREATE DATABASE livenote OWNER livenote;"
```

> [!IMPORTANT]
> 스키마 변경은 `db/migration`에 `V{번호}__{설명}.sql` 파일을 추가하는 방식으로만 합니다. `ddl-auto`가 `validate`라서 엔티티와 테이블이 다르면 앱이 시작되지 않습니다.

### Redis·RabbitMQ 준비

RabbitMQ는 STOMP 플러그인(`rabbitmq_stomp`, 포트 61613)을 켜서 사용합니다. 기본 `guest` 계정 대신 앱 전용 계정과 vhost를 만듭니다.

```bash
brew install redis rabbitmq
rabbitmq-plugins enable --offline rabbitmq_stomp
brew services start redis
brew services start rabbitmq

rabbitmqctl add_vhost livenote
rabbitmqctl add_user livenote '비밀번호'
rabbitmqctl set_permissions -p livenote livenote ".*" ".*" ".*"
```

Homebrew 설치 기본값은 STOMP(61613)와 관리 화면(15672) 포트를 모든 네트워크 주소에 엽니다. 로컬에서만 쓰려면 `/opt/homebrew/etc/rabbitmq/rabbitmq.conf`에 다음을 넣고 `brew services restart rabbitmq`로 재시작합니다.

```
stomp.listeners.tcp.1 = 127.0.0.1:61613
management.tcp.ip = 127.0.0.1
```

> [!NOTE]
> RabbitMQ STOMP는 `/topic/` 뒤의 주소에 `/`를 허용하지 않습니다. `/topic/lectures/4/summary`는 `Invalid destination` 오류로 거부되고 `/topic/lectures.4.summary`처럼 `.`으로 구분해야 합니다.

### Gradle 빌드 및 실행

```bash
# Linux/macOS에서는 gradlew에 실행 권한이 필요할 수 있습니다
chmod +x gradlew

./gradlew bootRun
```

### IntelliJ에서 실행

1. 프로젝트 SDK 설정 (Java 17)
2. Gradle 빌드 스크립트 로드
3. Lombok 어노테이션 처리 활성화 (`Settings > Build > Compiler > Annotation Processors`)
4. `LivenoteApplication.java` 실행

---

## 환경 설정

### env.properties 설정

`src/main/resources/env.properties` 파일을 생성하고 다음 값을 설정합니다:

```properties
# 데이터베이스
SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/livenote
SPRING_DATASOURCE_USERNAME=livenote
SPRING_DATASOURCE_PASSWORD=password

# AI 서버
AI_SERVER_URL=http://localhost:8003

# OpenAI
OPENAI_API_KEY=sk-proj-xxxx

# JWT
APP_JWT_SECRET=your-secret-key-here

# 콜백 (프론트엔드가 접근 가능한 백엔드 URL)
APP_CALLBACK_BASE_URL=http://localhost:8080

# AI 서버와 공유하는 내부 키 (ai/.env의 INTERNAL_API_KEY와 같은 값)
INTERNAL_API_KEY=openssl-rand-hex-32로-생성한-값

# RabbitMQ (STOMP 중계, 앱 전용 계정과 vhost)
RABBITMQ_STOMP_HOST=localhost
RABBITMQ_STOMP_PORT=61613
RABBITMQ_USERNAME=livenote
RABBITMQ_PASSWORD=password
RABBITMQ_VHOST=livenote

# Redis (녹음 상태와 잠금)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

### application.yml 변수 설명

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `SPRING_DATASOURCE_URL` | - | PostgreSQL 데이터베이스 JDBC URL |
| `SPRING_DATASOURCE_USERNAME` | - | DB 사용자명 |
| `SPRING_DATASOURCE_PASSWORD` | - | DB 비밀번호 |
| `AI_SERVER_URL` | - | AI 서버 URL (QA/REC/요약 생성) |
| `OPENAI_API_KEY` | - | OpenAI API 키 (STT용) |
| `APP_JWT_SECRET` | - | JWT 토큰 서명키 |
| `APP_JWT_EXPIRATION_MS` | 1800000 | 접근 토큰 유효 시간(ms) |
| `APP_JWT_REFRESH_EXPIRATION_DAYS` | 14 | 갱신 토큰 유효 기간(일) |
| `APP_JWT_REFRESH_COOKIE_SECURE` | true | 갱신 토큰 쿠키의 Secure 속성. HTTPS가 아닌 주소에서 쿠키가 저장되지 않으면 false |
| `APP_CALLBACK_BASE_URL` | localhost:8080 | AI 서버 콜백을 받을 백엔드 URL |
| `INTERNAL_API_KEY` | - | AI 서버와 공유하는 내부 키. 백엔드→AI 요청과 AI→백엔드 콜백의 `X-Internal-Api-Key` 헤더로 사용 |
| `RABBITMQ_STOMP_HOST` | localhost | STOMP 메시지를 중계할 RabbitMQ 주소 |
| `RABBITMQ_STOMP_PORT` | 61613 | RabbitMQ STOMP 플러그인 포트 |
| `RABBITMQ_USERNAME` | - | RabbitMQ 계정 |
| `RABBITMQ_PASSWORD` | - | RabbitMQ 비밀번호 |
| `RABBITMQ_VHOST` | livenote | RabbitMQ vhost |
| `REDIS_HOST` | localhost | 녹음 상태(섹션, 시각 보정값)와 잠금을 저장할 Redis 주소 |
| `REDIS_PORT` | 6379 | Redis 포트 |
| `APP_OPENAI_STT_MODEL` | whisper-1 | OpenAI STT 모델 |
| `APP_OPENAI_REALTIME_TRANSCRIPTION_MODEL` | gpt-4o-transcribe | 실시간 전사 세션의 전사 모델 |
| `APP_TRANSCRIPTION_PADDING_SECONDS` | 2.0 | 전사 패딩 시간(초) |
| `APP_TRANSCRIPTION_SPEED_MULTIPLIER` | 1.2 | 전사 속도 배율 |

#### 히스토리/중복 방지 설정

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `app.ai.history.previous-summary-count` | 3 | REC에 전달할 직전 요약 수 |
| `app.ai.history.previous-resource-sections` | 3 | REC exclude 윈도우 (이전 N섹션 자료 제외) |
| `app.ai.history.previous-qa-sections` | 3 | QA에 전달할 직전 QA 섹션 수 |

---

## 파일 구조

```
backend/
├── src/main/java/com/capstone/livenote/
│   ├── LivenoteApplication.java    # 메인 엔트리 포인트
│   ├── application/                 # 애플리케이션 계층
│   │   ├── ai/                      # AI 서버 연동 (콜백, 요청)
│   │   ├── audio/                   # 오디오 처리
│   │   ├── openai/                  # OpenAI STT 연동
│   │   └── ws/                      # WebSocket 핸들러
│   ├── domain/                      # 도메인 계층
│   │   ├── lecture/                 # 강의 엔티티/레포지토리
│   │   ├── transcript/              # 전사 관리
│   │   ├── summary/                 # 요약 관리
│   │   ├── qna/                     # QA 관리
│   │   ├── resource/                # 추천 자료 관리
│   │   ├── bookmark/                # 북마크 관리
│   │   └── user/                    # 사용자/인증
│   └── global/                      # 전역 설정/예외처리
├── src/main/resources/
│   ├── application.yml              # 애플리케이션 설정
│   ├── db/migration/                # Flyway 스키마 마이그레이션
│   └── env.properties               # 환경 변수 (gitignore)
├── build.gradle                     # Gradle 빌드 설정
└── gradlew                          # Gradle 래퍼
```

---

## 기능 설명

### 인증 및 사용자 관리

- **JWT 기반 인증**: 로그인 시 접근 토큰(JWT, 30분)과 갱신 토큰(14일)을 발급. 갱신 토큰은 `HttpOnly` 쿠키(`livenote_refresh`, 경로 `/api/auth`)로만 주고받고 Redis에 해시로 저장. 갱신할 때마다 새 갱신 토큰으로 교체
- **사용자 관리**: 회원가입, 로그인, 프로필 조회

### 강의 관리

- **강의 CRUD**: 사용자별 강의 목록 생성/조회/삭제
- **강의 상세**: 강의에 속한 전사, 요약, QA, 추천 자료 조회

### 실시간 전사 (WebSocket)

- **오디오 스트리밍**: WebSocket으로 실시간 오디오 청크 수신 (PCM16)
- **OpenAI Whisper STT**: 오디오를 텍스트로 변환
- **전사 저장**: 섹션별 전사 내용 DB 저장
- **실시간 전송**: STOMP를 통해 프론트엔드로 전사 결과 푸시. 메시지는 RabbitMQ가 중계해 백엔드 인스턴스가 여러 개여도 모든 구독자에게 전달됨

### 섹션 집계

- **15초 PARTIAL**: 15초 경계마다 부분 요약 요청
- **30초 FINAL**: 30초 경계마다 최종 요약 + RAG 업서트 + 자료/QA 트리거
- **상태 저장**: 강의별 현재 섹션과 시각 보정값은 Redis에 저장해 서버 여러 대와 재시작 후에도 이어짐. Redis에 없으면 DB의 마지막 섹션에서 다시 만듦
- **동시 처리**: 같은 강의의 전사, 같은 섹션의 카드 콜백은 Redis 잠금으로 한 번에 하나씩 처리

### AI 서버 연동

- **요약 요청**: 전사 완료 시 AI 서버에 요약 생성 요청
- **QA 생성 요청**: 섹션 요약 기반 질문/답변 생성 요청 (이전 QA 포함하여 중복 방지). AI 서버의 SSE 응답을 받아 질문과 답변 조각을 STOMP `/topic/lectures.{id}.stream`으로 중계하고, 완성되면 저장 후 `/topic/lectures.{id}.qna`로 섹션 전체 목록 푸시
- **자료 추천 요청**: 섹션 요약 기반 관련 자료 추천 요청 (exclude 목록 전달)
- **콜백 수신**: AI 서버로부터 요약·자료 추천 결과를 비동기로 수신해 DB 저장/STOMP 푸시

### 콜백 처리 (`/api/ai/callback`)

| 타입 | 설명 |
|------|------|
| `summary` | 요약 결과 수신 → DB 저장 → STOMP `/topic/lectures.{id}.summary` 푸시 |
| `resources` | 추천 자료 수신 → DB 저장 → STOMP `/topic/lectures.{id}.resources` 푸시 |

### 추천 자료 관리

- **자료 유형**: 논문(PAPER), 위키(WIKI), 유튜브(VIDEO), 블로그(BLOG)
- **북마크**: 사용자가 추천 자료 북마크 저장/삭제

---

## API 엔드포인트

### 인증

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/auth/register` | POST | 회원가입 `{loginId, password}` |
| `/api/auth/login` | POST | 로그인 `{loginId, password}` → `{ok, data:{token, user}}` + 갱신 토큰 쿠키 |
| `/api/auth/refresh` | POST | 갱신 토큰 쿠키로 새 접근 토큰 발급 → `{ok, data:{token}}` + 새 갱신 토큰 쿠키. 쿠키가 없거나 만료·폐기됐으면 401 |
| `/api/auth/logout` | POST | 갱신 토큰 폐기와 쿠키 삭제 |

### 강의

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/lectures` | GET | 강의 목록 조회 |
| `/api/lectures` | POST | 강의 생성 `{title, subject, sttLanguage}` |
| `/api/lectures/{id}` | GET | 강의 상세 조회 |
| `/api/lectures/{id}` | DELETE | 강의 삭제 |

### 전사

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/transcripts` | GET | 전사 목록 조회 `?lectureId` |
| `/api/transcripts/{id}` | GET | 전사 상세 조회 |

### 요약

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/summaries` | GET | 요약 목록 조회 `?lectureId` |
| `/api/summaries/{id}` | GET | 요약 상세 조회 |

### QnA

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/qna` | GET | QA 목록 조회 `?lectureId` |
| `/api/qna/{id}` | GET | QA 상세 조회 |

### 추천 자료

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/resources` | GET | 자료 목록 조회 `?lectureId` |
| `/api/resources/{id}` | GET | 자료 상세 조회 |

### 북마크

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/bookmarks` | GET | 북마크 목록 조회 |
| `/api/bookmarks` | POST | 북마크 추가 `{resourceId}` |
| `/api/bookmarks/{id}` | DELETE | 북마크 삭제 |

### AI 트리거 (수동 생성)

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/ai/generate-summary` | POST | 요약 수동 생성 `?lectureId&sectionIndex` |
| `/api/ai/generate-resources` | POST | 자료 추천 수동 생성 `?lectureId&sectionIndex` |
| `/api/ai/generate-qna` | POST | QA 수동 생성 `?lectureId&sectionIndex` |

### AI 콜백

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/ai/callback?type=summary` | POST | AI 서버 요약 콜백 수신 |
| `/api/ai/callback?type=resources` | POST | AI 서버 자료 콜백 수신 |

### 카드 스트리밍

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/start-qna-stream` | POST | QnA 카드 스트리밍 시작 |
| `/api/start-resources-stream` | POST | 자료 카드 스트리밍 시작 |
| `/api/cards-status` | GET | 카드 상태 조회 `?lectureId&sectionIndex` |

### WebSocket/STOMP

| 경로 | 프로토콜 | 설명 |
|------|----------|------|
| `/ws/transcription?sessionId={lectureId}` | WebSocket | 실시간 STT (Binary PCM16 ↔ JSON transcript) |
| `/ws` | STOMP | 브로커 연결. CONNECT 헤더에 `Authorization: Bearer {토큰}` 필요. 구독은 본인 강의 토픽만 허용, 클라이언트 SEND는 거부 |
| `/topic/lectures.{id}.transcripts` | STOMP 구독 | 전사 이벤트 수신 |
| `/topic/lectures.{id}.summary` | STOMP 구독 | 요약 이벤트 수신 |
| `/topic/lectures.{id}.resources` | STOMP 구독 | 자료 이벤트 수신 |
| `/topic/lectures.{id}.qna` | STOMP 구독 | QA 이벤트 수신 |
| `/topic/lectures.{id}.section` | STOMP 구독 | 섹션 전환 이벤트 수신 |
| `/topic/lectures.{id}.error` | STOMP 구독 | 오류 이벤트 수신 |
| `/topic/lectures.{id}.stream` | STOMP 구독 | 카드 스트리밍 토큰 수신 |

---

## 기술 스택

- **Java 17** + **Spring Boot 3**
- **Spring WebSocket** + **STOMP** (RabbitMQ 중계)
- **Spring Data JPA** + **PostgreSQL** + **Flyway**
- **Spring Data Redis** (서버 간 공유 상태와 잠금)
- **JWT** (인증)
- **OpenAI Whisper** (STT)
- **Gradle**

---

### 끝.
