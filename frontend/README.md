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
│   ├── App.tsx           # 메인 애플리케이션
│   ├── main.tsx          # 엔트리 포인트
│   ├── index.css         # 글로벌 스타일
│   ├── components/       # UI 컴포넌트
│   ├── hooks/            # 커스텀 훅
│   ├── services/         # API 서비스
│   ├── i18n/             # 다국어 지원
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
