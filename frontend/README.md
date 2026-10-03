# LiveNote 프론트엔드

React + TypeScript + Vite 기반의 실시간 강의 노트 서비스입니다.

---

## 실행 방법

```bash
cd frontend
npm install
npm run dev
```

> [!IMPORTANT]
> 실행 전 `frontend/.env` 파일 설정이 필요합니다:
>
> ```
> VITE_API_URL=http://localhost:8080
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
│   │   └── auth/         # 로그인, 회원가입, 설정 (api, hooks, components)
│   ├── legacy/           # 재작성 전 구 코드 (화면, 훅, API 서비스)
│   ├── shared/
│   │   ├── ui/           # shadcn/ui 컴포넌트
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
