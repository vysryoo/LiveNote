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
SPRING_DATASOURCE_URL=jdbc:mysql://localhost:3306/livenote
SPRING_DATASOURCE_USERNAME=root
SPRING_DATASOURCE_PASSWORD=password

# AI 서버
AI_SERVER_URL=http://localhost:8003

# OpenAI
OPENAI_API_KEY=sk-proj-xxxx

# JWT
APP_JWT_SECRET=your-secret-key-here

# 콜백 (프론트엔드가 접근 가능한 백엔드 URL)
APP_CALLBACK_BASE_URL=http://localhost:8080
```

---

### application.yml 변수 설명

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `SPRING_DATASOURCE_URL` | - | MySQL 데이터베이스 JDBC URL |
| `SPRING_DATASOURCE_USERNAME` | - | DB 사용자명 |
| `SPRING_DATASOURCE_PASSWORD` | - | DB 비밀번호 |
| `AI_SERVER_URL` | - | AI 서버 URL (QA/REC/요약 생성) |
| `OPENAI_API_KEY` | - | OpenAI API 키 (STT용) |
| `APP_JWT_SECRET` | - | JWT 토큰 서명키 |
| `APP_CALLBACK_BASE_URL` | localhost:8080 | AI 서버 콜백을 받을 백엔드 URL |
| `APP_OPENAI_STT_MODEL` | whisper-1 | OpenAI STT 모델 |
| `APP_TRANSCRIPTION_PADDING_SECONDS` | 2.0 | 전사 패딩 시간(초) |
| `APP_TRANSCRIPTION_SPEED_MULTIPLIER` | 1.2 | 전사 속도 배율 |
| `APP_STREAMING_CHUNK_SIZE` | 10 | 스트리밍 청크 크기 |
| `APP_STREAMING_DELAY_MS` | 100 | 스트리밍 지연 시간(ms) |

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
│   └── env.properties               # 환경 변수 (gitignore)
├── build.gradle                     # Gradle 빌드 설정
└── gradlew                          # Gradle 래퍼
```

---

## 기능 설명

### 인증 및 사용자 관리

- **JWT 기반 인증**: 로그인 시 JWT 토큰 발급, API 요청 시 토큰 검증
- **사용자 관리**: 회원가입, 로그인, 프로필 조회

### 강의 관리

- **강의 CRUD**: 사용자별 강의 목록 생성/조회/삭제
- **강의 상세**: 강의에 속한 전사, 요약, QA, 추천 자료 조회

### 실시간 전사 (WebSocket)

- **오디오 스트리밍**: WebSocket으로 실시간 오디오 청크 수신 (PCM16)
- **OpenAI Whisper STT**: 오디오를 텍스트로 변환
- **전사 저장**: 섹션별 전사 내용 DB 저장
- **실시간 전송**: STOMP를 통해 프론트엔드로 전사 결과 푸시

### 섹션 집계

- **15초 PARTIAL**: 15초 경계마다 부분 요약 요청
- **30초 FINAL**: 30초 경계마다 최종 요약 + RAG 업서트 + 자료/QA 트리거

### AI 서버 연동

- **요약 요청**: 전사 완료 시 AI 서버에 요약 생성 요청
- **QA 생성 요청**: 섹션 요약 기반 질문/답변 생성 요청 (이전 QA 포함하여 중복 방지)
- **자료 추천 요청**: 섹션 요약 기반 관련 자료 추천 요청 (exclude 목록 전달)
- **콜백 수신**: AI 서버로부터 비동기 결과 수신 및 DB 저장/STOMP 푸시

### 콜백 처리 (`/api/ai/callback`)

| 타입 | 설명 |
|------|------|
| `summary` | 요약 결과 수신 → DB 저장 → STOMP `/topic/lectures/{id}/summary` 푸시 |
| `qna` | QA 결과 수신 → DB 저장 → STOMP `/topic/lectures/{id}/qna` 푸시 |
| `resources` | 추천 자료 수신 → DB 저장 → STOMP `/topic/lectures/{id}/resources` 푸시 |

### 추천 자료 관리

- **자료 유형**: 논문(PAPER), 위키(WIKI), 유튜브(VIDEO), 블로그(BLOG)
- **북마크**: 사용자가 추천 자료 북마크 저장/삭제

---

## API 엔드포인트

### 인증

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/api/auth/register` | POST | 회원가입 `{loginId, password}` |
| `/api/auth/login` | POST | 로그인 `{loginId, password}` → `{ok, data:{token, user}}` |

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
| `/api/ai/callback?type=qna` | POST | AI 서버 QA 콜백 수신 |

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
| `/ws` | STOMP | 브로커 연결 |
| `/topic/lectures/{id}/transcripts` | STOMP 구독 | 전사 이벤트 수신 |
| `/topic/lectures/{id}/summary` | STOMP 구독 | 요약 이벤트 수신 |
| `/topic/lectures/{id}/resources` | STOMP 구독 | 자료 이벤트 수신 |
| `/topic/lectures/{id}/qna` | STOMP 구독 | QA 이벤트 수신 |
| `/topic/lectures/{id}/section` | STOMP 구독 | 섹션 전환 이벤트 수신 |
| `/topic/lectures/{id}/error` | STOMP 구독 | 오류 이벤트 수신 |
| `/topic/lectures/{id}/stream` | STOMP 구독 | 카드 스트리밍 토큰 수신 |

---

## 기술 스택

- **Java 17** + **Spring Boot 3**
- **Spring WebSocket** + **STOMP**
- **Spring Data JPA** + **MySQL**
- **JWT** (인증)
- **OpenAI Whisper** (STT)
- **Gradle**

---

### 끝.
