# Update 8 (Backend Spring)

## Summary
- AI 요청/콜백 경로에 로그를 추가해 디버깅 가시성 강화.
- 리소스/QnA 콜백 저장 시 reason/detail/summaryId 등을 안전히 매핑하고 WebSocket 브로드캐스트 유지.
- 이전 요약/자료 exclude, 이전 QnA 컨텍스트를 빌드하는 서비스 로직에 대한 단위테스트 추가.

## File changes (핵심)
- `application/ai/controller/AiCallbackController.java`: 콜백 수신 시 타입/키 로그.
- `application/ai/service/AiRequestService.java`: 이전 요약/자료/QnA 컨텍스트 누적, exclude 계산, 로그 추가.
- `application/ai/service/ResourceCallbackService.java`: reason/detail JSON 저장, 콜백 수량 로그.
- `application/ai/service/QnaCallbackService.java`: 타입 매핑/summaryId 저장, 콜백 수량 로그.
- `src/test/java/.../AiRequestServiceTest.java`: 이전 요약/자료 exclude, 이전 QnA/subject 전달 검증.
- `src/test/java/.../ResourceCallbackServiceTest.java`: reason/detail JSON 매핑 및 WS 전송 검증.
- `src/test/java/.../QnaCallbackServiceTest.java`: 타입 매핑/summaryId·WS 전송 검증.
- `.gitignore`: 로컬 `.env`/`*.env`, `db/schema.sql` 무시 추가.

## Test
- `./gradlew test --info` (pass)

## Folder snapshot (변경 관련)
- `src/main/java/com/capstone/livenote/application/ai/controller/AiCallbackController.java`
- `src/main/java/com/capstone/livenote/application/ai/service/{AiRequestService,QnaCallbackService,ResourceCallbackService}.java`
- `src/test/java/com/capstone/livenote/application/ai/service/{AiRequestServiceTest,QnaCallbackServiceTest,ResourceCallbackServiceTest}.java`
- `.gitignore`

