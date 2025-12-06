# 실행 가이드

1. `Back-end/src/main/resources/application.yml`에 OpenAI API 키 설정
2. `Front-end/.env` 파일 생성 후 백엔드 연결 정보 설정 (예: `VITE_BACKEND_TYPE`, `VITE_API_URL`, `VITE_WS_URL`)
3. IntelliJ에서 Spring Boot 실행
 - 프로젝트 SDK 설정 (Java17)
 - Maven 빌드 스크립트 로드
 - Lombok 어노테이션 처리 활성화
4. `Front-end`에서 `npm install` 실행
5. `Front-end`에서 `npm run dev` 실행
