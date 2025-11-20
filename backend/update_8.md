# Update 8 (Backend Spring)

## Summary
- AI 요청/콜백 경로에 로그를 추가해 디버깅 가시성 강화.
- 리소스/QnA 콜백 저장 시 reason/detail/summaryId 등을 안전히 매핑하고 WebSocket 브로드캐스트 유지.
- 이전 요약/자료 exclude, 이전 QnA 컨텍스트를 빌드하는 서비스 로직에 대한 단위테스트 추가.
- 최종 30초 요약 생성 시 벡터DB `/rag/text-upsert` 자동 호출, PDF 업로드 엔드포인트로 `/rag/pdf-upsert` 연동 추가.

## File changes (핵심)
- `application/ai/controller/AiCallbackController.java`: 콜백 수신 시 타입/키 로그.
- `application/ai/service/AiRequestService.java`: 이전 요약/자료/QnA 컨텍스트 누적, exclude 계산, 로그 추가.
- `application/ai/service/ResourceCallbackService.java`: reason/detail JSON 저장, 콜백 수량 로그.
- `application/ai/service/QnaCallbackService.java`: 타입 매핑/summaryId 저장, 콜백 수량 로그.
- `application/ai/client/RagClient.java` + `application/ai/controller/AiController.java`: PDF 업로드→`/rag/pdf-upsert` 연동, 최종 요약 시 `/rag/text-upsert` 호출 지원.
- `src/test/java/.../AiRequestServiceTest.java`: 이전 요약/자료 exclude, 이전 QnA/subject 전달 검증.
- `src/test/java/.../ResourceCallbackServiceTest.java`: reason/detail JSON 매핑 및 WS 전송 검증.
- `src/test/java/.../QnaCallbackServiceTest.java`: 타입 매핑/summaryId·WS 전송 검증.
- `.gitignore`: 로컬 `.env`/`*.env`, `db/schema.sql` 무시 추가.

## Test
- `./gradlew test --info` (pass)

## Frontend usage (주요 엔드포인트)
- `/api/ai/generate-resources` (POST, params: `lectureId`, `sectionIndex`): 콜백 기반 추천 요청
- `/api/ai/generate-qna` (POST, params: `lectureId`, `sectionIndex`): 콜백 기반 QnA 요청
- `/api/ai/pdf-upload` (POST multipart: `lectureId`, `file`, optional `metadata` JSON): PDF 업서트 → AI 서버 `/rag/pdf-upsert`
- 30초 요약 생성 시 백엔드가 자동 `/rag/text-upsert` 호출 (프론트 호출 불필요)
- 콜백은 `/api/ai/callback?type=qna|resources`로 수신됨 (프론트는 WS로 `/topic/lectures/{lectureId}/qna|resources` 구독)

## Folder snapshot (변경 관련)
- `src/main/java/com/capstone/livenote/application/ai/controller/AiCallbackController.java`
- `src/main/java/com/capstone/livenote/application/ai/service/{AiRequestService,QnaCallbackService,ResourceCallbackService}.java`
- `src/test/java/com/capstone/livenote/application/ai/service/{AiRequestServiceTest,QnaCallbackServiceTest,ResourceCallbackServiceTest}.java`
- `.gitignore`
