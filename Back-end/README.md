# LiveNote Backend

Java Spring Boot 기반의 LiveNote 백엔드 서버입니다.  
브라우저에서 수집한 오디오를 OpenAI Realtime API에 전달하여 **30초 단위 실시간 전사 & 요약**, **자료 탐색 추천**, **AI Q&A**를 제공합니다.

## ⚙️ 기술 스택

- Java 17, Spring Boot 3.2.x
- Spring Security + JWT
- Spring Data JPA (H2 dev / MySQL prod)
- WebSocket (`/ws/transcription`)
- OpenAI Realtime & GPT-4o APIs

## 🔑 주요 기능

| 영역 | 설명 |
| --- | --- |
| 인증 | 회원가입·로그인, JWT 발급 |
| 강의 관리 | 생성/조회/수정/삭제, 종료 처리 |
| 실시간 전사/요약 | WebSocket으로 음성 → 실시간 전사, 30초 구간 요약 |
| 자료 & Q&A | 섹션별 추천 자료/AI Q&A 생성 및 조회 |
| 북마크/설정 | 섹션별 북마크, 사용자 프로필/언어/비밀번호 변경 |
| AI 콜백 | `/api/ai/callback`으로 OpenAI 생성 결과 저장 |

## 📡 실시간 흐름

1. 프론트엔드가 `ws://localhost:8080/ws/transcription?sessionId={lectureId}`로 PCM16 오디오 전송
2. 백엔드 `TranscriptionWebSocketHandler` → OpenAI Realtime API
3. OpenAI에서 전사/요약을 수신 후:
   - DB 저장 (`Transcript`, `Summary`)
   - WebSocket으로 프론트엔드에 push
4. 프론트엔드는 새 요약을 클릭하면 자료·Q&A가 REST API로 조회되고, 없으면 OpenAI 생성 API(`/api/ai/generate-*`)를 호출합니다.

## 🚀 빠른 시작 (인텔리제이 기준)

1. **IntelliJ IDEA에서 `Back-end` 폴더를 프로젝트로 열기**
2. **JDK 17 설정 확인** (File → Project Structure → Project SDK: 17 이상)
3. **`src/main/resources/application.yml`에서 OpenAI API 키 설정** (42번째 줄 `openai.api-key` 값 변경)
4. **`LiveNoteApplication.java` 우클릭 → Run 'LiveNoteApplication'** 실행

> 💡 **참고**: H2 인메모리 DB 사용 중이므로 별도 DB 설치 불필요. OpenAI API 키만 설정하면 바로 실행 가능합니다.  
> 💡 Maven 의존성은 IntelliJ가 자동으로 다운로드합니다.

## 🚀 상세 실행 방법

1. **환경 변수 / `application.yml` 설정**
   ```yaml
   spring:
     datasource:
       url: jdbc:h2:mem:livenote   # dev DB
       username: sa
       password: ""

   jwt:
     secret: ${JWT_SECRET:livenote-secret-key}

   openai:
     api-key: ${OPENAI_API_KEY}
     realtime-model: gpt-4o-realtime-preview-2024-10-01
     transcription-model: gpt-4o-transcribe
   ```
   > 실제 OpenAI 키를 환경 변수로 주입하거나 `application.yml`에 직접 입력하세요.  
   > `Back-end/.gitignore`가 `target/` 등을 제외하므로 빌드 산출물은 커밋되지 않습니다.

2. **의존성 및 빌드**
   ```bash
   cd Back-end
   mvn clean install
   ```

3. **서버 실행**
   ```bash
   mvn spring-boot:run
   ```
   또는 IDE에서 `LiveNoteApplication.java` 실행 → `http://localhost:8080`

## 🔐 인증 & 엔드포인트

- 모든 REST API는 `/api` prefix 사용
- 인증 필요 시 `Authorization: Bearer {JWT}` 헤더 필수
- 주요 엔드포인트
  - `POST /api/auth/signup`, `POST /api/auth/login`
  - `GET /api/lectures`, `POST /api/lectures`, `PATCH /api/lectures/{id}/title`, `DELETE /api/lectures/{id}`
  - `POST /api/ai/generate-summary`, `/generate-qna`, `/generate-resources`
  - `GET /api/resources`, `GET /api/qna`, `POST /api/bookmarks`

## 🧪 개발 참고

- H2 콘솔: `http://localhost:8080/h2-console`
  - JDBC URL: `jdbc:h2:mem:livenote`, user: `sa`, password: (없음)
- WebSocket 테스트: 브라우저 실시간 전사 또는 `wscat` 등 사용
- 문제가 되는 push 보호: `target/` 등 빌드 산출물에 비밀 키가 포함되지 않도록 주의

## 📎 관련 문서

- 상위 환경 설정 가이드: `../SETUP.md`
- API 어댑터 (프론트): `Front-end/src/services/adapters/spring.ts`