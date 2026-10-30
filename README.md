# LiveNote

강의를 녹음하면 실시간 전사와 함께 섹션별 요약, QnA, 학습 자료 추천을 만들어 주는 강의 노트 서비스입니다.

---

## 구성

| 폴더 | 기술 | 역할 | 문서 |
| --- | --- | --- | --- |
| `frontend/` | React, TypeScript, Vite | 웹 화면 (:3000) | [frontend/README.md](frontend/README.md) |
| `backend/` | Spring Boot, PostgreSQL, Redis, RabbitMQ | 인증, 강의 데이터, 실시간 전사, 실시간 메시지 (:8080) | [backend/README.md](backend/README.md) |
| `ai/` | FastAPI, LangChain·LangGraph | 요약, QnA, 자료 추천, 강의 자료 검색 (:8003) | [ai/README.md](ai/README.md), [ai/API_SPECIFICATION.md](ai/API_SPECIFICATION.md) |

```
브라우저 ── REST, 녹음 WebSocket, STOMP ──▶ 백엔드 ── HTTP, SSE, 콜백 ──▶ AI 서버
                                             └── Realtime API (전사) ──▶ OpenAI
```

---

## 실행 방법

각 폴더 README의 준비 과정(설정 파일, DB)을 마친 뒤 AI 서버 → 백엔드 → 프론트엔드 순서로 실행합니다.

```bash
cd ai && uv run uvicorn server.main:app --port 8003
cd backend && ./gradlew bootRun
cd frontend && npm run dev
```

---

## 문서

| 문서 | 내용 |
| --- | --- |
| [HANDOFF.md](HANDOFF.md) | 현재 상태, 로컬 실행 환경, 통신 구조, 남은 문제, 평가 결과 |
| [AGENTS.md](AGENTS.md) | 코드·커밋·PR 작성 규칙 (세부 규칙은 `.agent/`) |
