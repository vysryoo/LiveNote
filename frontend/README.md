# LiveNote 프론트엔드

React + TypeScript + Vite 기반의 실시간 강의 노트 서비스 프론트엔드입니다.

---

## 실행 방법

Node.js 22가 필요합니다. 백엔드가 `localhost:8080`에서 실행 중이어야 합니다.

```bash
npm install
npm run dev        # 개발 서버 (:3000)
npm run build      # 배포 빌드
```

검사

```bash
npm run typecheck && npm run lint && npm test
```

---

## 환경 설정

설정 없이 동작합니다. 개발 서버가 `/api` 요청을 8080으로 전달하고, 실시간 연결은 `ws://localhost:8080`에 직접 연결합니다. 다른 주소를 쓸 때만 `frontend/.env`에 지정합니다.

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `VITE_API_URL` | `/api` | REST API 주소 |
| `VITE_WS_URL` | `ws://localhost:8080` | 녹음 WebSocket·STOMP 주소 |

---

## 파일 구조

```
src/
├── main.tsx            # 엔트리 포인트
├── app/                # 라우터, 로그인 확인, 전역 프로바이더
├── features/
│   ├── auth/           # 로그인, 회원가입, 설정
│   ├── landing/        # 랜딩 페이지 (구역별 컴포넌트)
│   ├── lectures/       # 강의 목록, 생성, 이름 변경, 삭제, 종료
│   └── session/        # 강의 화면
│       ├── audio/      # 마이크 녹음 (PCM16 24kHz)
│       └── realtime/   # STOMP 구독과 메시지 처리 함수
├── shared/
│   ├── components/     # 기능 공용 컴포넌트 (헤더, 사용자 메뉴, 언어 선택, 폼 오류)
│   ├── ui/             # shadcn/ui 컴포넌트 (사용하는 것만 보관)
│   ├── lib/            # HTTP 클라이언트, 로그인 토큰 저장
│   └── i18n/           # i18next 설정, 언어별 번역 (ko, en, ja, zh)
└── styles/             # 글로벌 스타일, 브랜드 그라데이션 유틸리티
```

각 기능 폴더는 다음과 같이 나눕니다.

| 폴더 | 내용 |
| --- | --- |
| `api/` | 백엔드 요청과 zod 응답 스키마 |
| `hooks/` | TanStack Query 훅, 화면 흐름 훅 |
| `components/` | 화면 |
| `lib/` | 화면 없는 계산과 상태 (예: 세션 reducer, 섹션 목록 계산). 테스트를 같은 폴더에 둠 |

---

## 기능 설명

- **실시간 전사**: 녹음을 WebSocket으로 보내고 전사를 실시간으로 표시
- **섹션별 요약, QnA, 자료 추천**: 백엔드가 STOMP로 보내는 카드를 표시. QnA는 생성 중인 글자가 실시간으로 쌓임
- **강의 기록**: 지난 강의의 전사, 요약, QnA, 자료, 북마크 조회
- **다국어**: 한국어, 영어, 일본어, 중국어
