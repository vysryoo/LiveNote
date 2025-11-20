아래 요구사항에 맞춰 FastAPI 기반 AI 서버(`module_integration` 폴더)와 Spring Boot 백엔드(`backend` 폴더)를 통합하세요. 콜백 방식으로 동작하며, DB 스키마·API 스펙·데이터 흐름을 모두 반영해야 합니다.

## 공통
- 콜백 방식을 사용합니다. AI 서버는 작업 결과를 `callbackUrl`(예: `http://localhost:8080/api/ai/callback?type=qna|resources`)로 POST 합니다. SSE는 사용하지 않습니다.
- 백엔드는 콜백을 받아 DB에 저장하고 WebSocket 등으로 프론트에 전달합니다.
- 스키마 확장: `resources` 테이블에 `reason TEXT`, `detail JSON` 컬럼을 추가하세요(기존 컬럼 유지). `detail`에는 provider별 메타데이터(예: authors, view_count, abstract 등)를 JSON으로 그대로 담습니다.
- AI 서버가 콜백 payload에 필요한 필드를 빠짐없이 내려주도록 스키마/DTO를 확장합니다.

## Spring 백엔드 변경
1) `/api/ai/generate-resources`
   - 현재 섹션의 summary를 `section_summary`로 전송.
   - 직전 N개(설정값으로 조정 가능) summary를 `previous_summaries`에 담아 전송.
   - exclude 필드: 직전 N(위에 N가 다른 변수임)개 섹션의 추천자료를 조회해 source별로 `yt_exclude`, `wiki_exclude`, `paper_exclude`, `google_exclude`에 채워 넣습니다 (N은 설정값으로 조정 가능. N is number of sections. previous sections).
   - 응답은 콜백으로 받습니다. 필요하면 DTO/필드 구조를 수정해도 됩니다.

2) `/api/ai/generate-qna`
   - AI 서버의 `/qa/generate`에 요청.
   - subject는 Lecture.subject를 그대로 사용.
   - `previous_qa`는 직전 M개 섹션의 QnA를 담아 전송 (M은 설정값으로 조정 가능).
   - 응답은 콜백으로 받습니다. 필요하면 DTO/필드 구조를 수정해도 됩니다.

3) PDF 업서트
   - 백엔드에 PDF 업로드 엔드포인트를 추가하고, AI 서버의 `POST /rag/pdf-upsert`를 호출하도록 연결합니다.

4) 텍스트 업서트
   - 30초 요약이 생성될 때마다 AI 서버의 `/rag/text-upsert`를 호출하세요.
   - upsert only one generated summary. and fill the metadata correct.

5) 콜백 처리
   - `type=qna|resources`로 구분해 `/api/ai/callback`에서 저장합니다.
   - Resource 저장 시 `reason`, provider별 메타데이터를 `detail` JSON에 넣고, 기존 필드(title, url, type, score 등)도 저장합니다.
   - QnA 저장 시 필요한 필드(type, question, answer 등)를 모두 저장합니다.
   - 관련해서 DB 테이블에 필드도 추가해도 됨. reason. destails 필드.

## FastAPI AI 서버 변경
- 콜백 기반으로 동작하도록 `/qa/generate`, `/rec/recommend`에 `callbackUrl`을 받아 처리하세요.
- 작업 완료 시 provider별 결과를 즉시 `callbackUrl`로 POST 합니다 (SSE 사용 안 함). Wiki가 끝나면 먼저 콜백, 이후 OpenAlex/Google/YouTube도 완료되는 대로 콜백을 별도로 보냅니다. (꼭 wiki부터 먼저 콜백할 필요없고 되는 것부터 콜백하라는 의미)
- 콜백 payload 예시(리소스):
  ```json
  {
    "lectureId": 1,
    "summaryId": 10,
    "sectionIndex": 0,
    "resources": [
      {
        "type": "wiki",
        "title": "...",
        "url": "...",
        "description": "...",
        "score": 82.0,
        "reason": "...",
        "detail": { "language": "ko", "extract": "...", "publish_date": "...", "view_count": 12345 }
      }
    ]
  }
  ```
- 콜백 payload 예시(QnA):
  ```json
  {
    "lectureId": 1,
    "summaryId": 10,
    "sectionIndex": 0,
    "qnaList": [
      { "type": "concept", "question": "...", "answer": "..." }
    ]
  }
  ```


## 설정
- “이전 N개 요약/자료/QA” 윈도우는 설정값으로 조정 가능하게 프로퍼티를 추가하세요(백엔드).

## 검증
- end-to-end 시나리오: 요약 생성(30초) → /rag/text-upsert 호출 → 프론트가 `/api/ai/generate-resources` 또는 `/api/ai/generate-qna` 호출 → AI 서버가 작업 후 콜백 → 백엔드가 저장 + WebSocket 전송 → 프론트 렌더링.
