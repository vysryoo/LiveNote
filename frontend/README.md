# LiveNote 프론트엔드

React + TypeScript + Vite 기반의 실시간 강의 노트 서비스입니다.

---

## 실행 방법

```bash
cd frontend
npm install
npm run dev
```

> [!NOTE]
> 백엔드가 `localhost:8080`에서 실행 중이면 별도 설정 없이 동작합니다. 개발 서버가 `/api` 요청을 8080으로 전달하고, 실시간 연결은 `ws://localhost:8080`에 직접 연결합니다.
> 다른 주소를 쓰려면 `frontend/.env`에 설정합니다:
>
> ```
> VITE_API_URL=http://localhost:8080/api
> VITE_WS_URL=ws://localhost:8080
> ```

---

## 파일 구조

```
frontend/
├── src/
│   ├── main.tsx          # 엔트리 포인트
│   ├── app/              # 라우터, 전역 프로바이더
│   ├── features/
│   │   ├── auth/         # 로그인, 회원가입, 설정 (api, hooks, components)
│   │   ├── landing/      # 랜딩 페이지
│   │   ├── lectures/     # 강의 목록, 생성, 이름 변경, 삭제, 종료
│   │   └── session/      # 세션 화면, 실시간 구독, 녹음
│   ├── shared/
│   │   ├── ui/           # shadcn/ui 컴포넌트
│   │   ├── components/   # 기능 공용 컴포넌트
│   │   ├── lib/          # 공용 HTTP 클라이언트, 로그인 토큰 저장
│   │   └── i18n/         # i18next 설정, 언어별 번역 파일
│   ├── styles/           # 글로벌 스타일 (globals.css)
│   └── assets/           # 정적 파일
├── public/               # 정적 자산
├── index.html            # HTML 템플릿
├── vite.config.ts        # Vite 설정
└── package.json          # 의존성
```

---

## 기능 설명

- **실시간 전사**: WebSocket 기반 음성 인식 및 텍스트 표시
- **섹션별 요약**: AI 기반 강의 내용 요약
- **QA 생성**: 학습 내용 기반 질문/답변 자동 생성
- **자료 추천**: 논문, 위키, 유튜브, 블로그 추천
- **다국어 지원**: i18n 기반 다국어 UI
