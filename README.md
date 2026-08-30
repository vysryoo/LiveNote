# LiveNote

실시간 강의 노트 서비스. 프론트엔드 · 백엔드 · AI 서버 세 컴포넌트를 하나의 레포로 합친 모노레포입니다.

```
LiveNote/
├── frontend/   React 18 + TypeScript + Vite (포트 5173)
├── backend/    Spring Boot 3.5 / Java 17 / Gradle (포트 8080)
└── ai/         Python + FastAPI (포트 8003)
    ├── QA_module/         질의응답
    ├── RAG_module/        문서 임베딩 · 검색 (ChromaDB)
    ├── wiki_module/       위키 자료 추천
    ├── google_module/     구글 검색 자료 추천
    ├── openalex_module/   논문 자료 추천
    └── youtube_module/    유튜브 자료 추천
```

컴포넌트별 상세 문서는 각 디렉토리의 `README.md`를 보세요. AI 서버 API 명세는 [ai/API_SPECIFICATION.md](ai/API_SPECIFICATION.md)에 있습니다.

## 실행

세 컴포넌트를 각각 띄운 뒤 프론트에서 접속합니다. 프론트는 백엔드(8080)를, 백엔드는 AI 서버(8003)를 호출합니다.

### frontend

```bash
cd frontend
npm install
npm run dev
```

`frontend/.env` 필요:

```
VITE_API_URL=http://localhost:8080
VITE_WS_URL=ws://localhost:8080
```

### backend

```bash
cd backend
./gradlew bootRun
```

Java 17 toolchain을 사용합니다. `backend/src/main/resources/application.yml`이 다음 환경변수를 읽습니다 (또는 `src/main/resources/env.properties`로 주입):

```
SPRING_DATASOURCE_URL / SPRING_DATASOURCE_USERNAME / SPRING_DATASOURCE_PASSWORD
AI_SERVER_URL
```

스키마는 [backend/db/schema.sql](backend/db/schema.sql) 참고.

### ai

```bash
cd ai
bash setup.sh                 # venv 생성 + 6개 모듈 editable 설치
source .venv/bin/activate
uvicorn server.main:app --reload --port 8003
```

`ai/.env`는 [ai/.env.example](ai/.env.example)을 복사해 채웁니다 (`OPENAI_API_KEY` 등).

Docker로 띄우려면:

```bash
cd ai && docker compose up --build
```

## 모노레포 구성

원래 세 개의 레포로 나뉘어 있던 것을 히스토리를 보존한 채 합쳤습니다.

| 디렉토리 | 원본 | 브랜치 |
|---|---|---|
| `frontend/` | `Team-GongGong-s/LiveNote_frontend` | `master` |
| `backend/` | `Team-GongGong-s/LiveNote_backend` | `dev` |
| `ai/` | `Team-GongGong-s/LiveNote_ai-server` | `main` |
| `ai/QA_module/` | `nongman25/cap1_QA_module` | `main` |
| `ai/RAG_module/` | `nongman25/cap1_RAG_module` | `main` |
| `ai/wiki_module/` | `nongman25/cap1_wiki_module` | `main` |

통합하면서 바뀐 점:

- 프론트엔드 코드가 `Front-end/` 하위에 중첩돼 있던 것을 `frontend/` 바로 아래로 평탄화
- AI 서버의 서브모듈 3개를 일반 디렉토리로 흡수하고 `.gitmodules` 제거
- 모듈 디렉토리명에서 `cap1_` 접두사 제거 (`cap1_QA_module` → `QA_module`). 모듈 내부 패키지명(`qakit`, `ragkit` 등)은 원래 접두사가 없어 그대로입니다
- 원본에 커밋돼 있던 EC2 private key(`sireal-key.pem`)를 이 레포 히스토리에서 제거

### 원본 레포와 동기화

컴포넌트 단위로 `git subtree`를 씁니다.

```bash
# upstream 변경 가져오기
git remote add be-upstream https://github.com/Team-GongGong-s/LiveNote_backend.git
git subtree pull --prefix=backend be-upstream dev

# 변경분을 포크로 밀어 PR 올리기
git remote add fe-fork https://github.com/vysryoo/LiveNote_frontend.git
git subtree push --prefix=frontend fe-fork feature/refactor
```

프론트엔드는 경로가 평탄화됐고 AI 모듈은 이름이 바뀌었으므로, 해당 컴포넌트의 subtree 동기화에는 수동 조정이 필요합니다.
