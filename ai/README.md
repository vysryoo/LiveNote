# LiveNote AI 게이트웨이 안내서

본 문서는 LiveNote AI 백엔드의 전체 구조, 운영 절차, API 명세, 설정 방법 등을 모두 담은 종합 안내서입니다. 개발자, QA 담당자, DevOps, 운영자가 동일한 기준으로 시스템을 이해하고 유지보수할 수 있도록 500줄 이상으로 구성되어 있습니다.

---

## 목차

1. 개요
2. 전체 흐름 요약
3. 아키텍처 개요
4. 디렉터리 구조
5. 모듈별 요약
    - 5.1 cap1_QA_module
    - 5.2 cap1_RAG_module
    - 5.3 cap1_openalex_module
    - 5.4 cap1_wiki_module
    - 5.5 cap1_youtube_module
    - 5.6 cap1_google_module
    - 5.7 server
    - 5.8 tests
    - 5.9 스크립트 및 보조 파일
6. 환경 구축
    - 6.1 사전 준비물
    - 6.2 `setup.sh` 자동 설치
    - 6.3 수동 설치 방법
    - 6.4 가상환경 활성화
7. 환경 변수(.env)
    - 7.1 기본 구조
    - 7.2 키 설명
    - 7.3 예시
8. 애플리케이션 설정 (AppSettings)
    - 8.1 RAG 설정
    - 8.2 QA 설정
    - 8.3 REC 설정
9. 데이터 흐름
    - 9.1 업서트(Upsert) 흐름
    - 9.2 QA 흐름
    - 9.3 REC 흐름
    - 9.4 오류 처리 흐름
10. API 명세
    - 10.1 Health 체크
    - 10.2 RAG 업서트
    - 10.3 QA 생성
    - 10.4 REC 추천
    - 10.5 SSE 이벤트 포맷
    - 10.6 cURL 예시
11. 설정 가이드
    - 11.1 질문 유형 조정
    - 11.2 Provider 세부 설정
    - 11.3 저장소 경로 지정
12. 운영 절차
    - 12.1 로컬 실행
    - 12.2 `test.sh` 점검
    - 12.3 클라우드 배포
13. 문제 해결
    - 13.1 자주 발생하는 에러
    - 13.2 텔레메트리 경고
    - 13.3 Chroma 컬렉션 문제
    - 13.4 SSE 진단
14. 테스트 전략
    - 14.1 자동 테스트
    - 14.2 수동 검증
15. 모범 사례
16. 향후 개선 계획
17. 부록
    - 17.1 시퀀스 다이어그램(텍스트)
    - 17.2 ChromaDB 설명
    - 17.3 용어집
18. 변경 이력

---

## 1. 개요

LiveNote AI 게이트웨이는 다음과 같은 기능을 제공합니다.

- **RAG(Retrieval-Augmented Generation)** 기반의 문서 저장 및 검색.
- **OpenAI**를 활용한 다중 질문 유형의 **QA 생성**.
- **OpenAlex / Wikipedia / YouTube**를 통합한 자료 추천(REC).
- 모든 생성 결과는 **SSE(Server-Sent Events)** 스트림으로 클라이언트에 전달.

이 문서에서는 전체 시스템을 이해하기 위해 필요한 내용을 시작부터 배포까지 단계별로 다룹니다.

---

## 2. 전체 흐름 요약

1. **RAG 업서트**  
   텍스트 또는 PDF를 업로드하면 OpenAI 임베딩을 생성하고 ChromaDB에 저장합니다. 컬렉션 이름은 `lecture_<lecture_id>` 형식으로 통일합니다.

2. **QA 요청**  
   특정 섹션 요약과 `lecture_id`를 입력하면 저장된 청크를 불러오고, 미리 지정된 질문 유형에 대해 OpenAI Chat Completion을 비동기로 호출한 뒤 SSE로 순차 전송합니다.

3. **REC 요청**  
   같은 `lecture_id`를 기반으로 RAG 청크를 읽고, 각 Provider(OpenAlex, Wiki, YouTube)에 전달하여 추천 목록을 생성합니다. 결과는 준비되는 순서대로 스트림으로 내려보냅니다.

---

## 3. 아키텍처 개요

```
클라이언트(Spring / curl / Postman)
           │
           ▼
FastAPI (server/)
 ├─ RAG 라우터 → cap1_RAG_module (OpenAI Embedding + ChromaDB)
 ├─ QA 라우터  → cap1_QA_module (OpenAI Chat Completion)
 └─ REC 라우터 → cap1_openalex_module / cap1_wiki_module / cap1_youtube_module
```

- **server/**: FastAPI 앱, 라우터, 설정, 유틸리티.
- **cap1_*_module**: 각각의 기능을 담당하는 독립 모듈.
- **ChromaDB**: `RAG_PERSIST_DIR` 경로에 벡터 데이터를 저장.
- **OpenAI**: 임베딩과 Chat Completion에 모두 사용.
- **외부 API**: OpenAlex, Wikipedia, YouTube Data API.

---

## 4. 디렉터리 구조

| 경로 | 설명 |
|------|------|
| `cap1_QA_module/` | QA 생성 모듈 |
| `cap1_RAG_module/` | RAG 저장/검색 모듈 (Chroma + Embedding) |
| `cap1_openalex_module/` | 논문 추천 모듈 |
| `cap1_wiki_module/` | 위키 추천 모듈 |
| `cap1_youtube_module/` | 유튜브 추천 모듈 |
| `server/` | FastAPI 서버 구성 |
| `tests/` | 단위/통합 테스트 |
| `setup.sh` | 환경 구축 자동 스크립트 |
| `test.sh` | 헬스/업서트/REC 확인용 간단 스크립트 |
| `requirements.server.txt` | 런타임 의존성 목록 |
| `.env.example` / `.env` | 환경 변수 템플릿 및 실제 설정 |

각 디렉터리의 역할은 아래 모듈 요약에서 자세히 설명합니다.

---

## 5. 모듈별 요약

### 5.1 cap1_QA_module
- 위치: `cap1_QA_module/`
- 주요 파일:
  - `qakit/service.py`: QA 생성 로직. 질문 유형별 비동기 작업을 실행하고 SSE에 맞는 이벤트를 반환.
  - `qakit/models.py`: Pydantic 기반 요청/응답 모델, `QARequest`, `QAResponse`, `RAGContext` 등 정의.
  - `qakit/config/prompts.py`: 질문 유형에 따른 프롬프트 템플릿.
  - `qakit/llm/openai_client.py`: AsyncOpenAI 클라이언트, Chat Completion 호출.
- 특징:
  - `stream_questions`는 `asyncio.wait`를 사용하여 완료된 작업만 순서대로 처리합니다.
  - 질문 유형과 개수는 서버 설정에서 조정 가능합니다.

### 5.2 cap1_RAG_module
- 위치: `cap1_RAG_module/`
- 주요 파일:
  - `ragkit/service.py`: 텍스트/PDF 업서트, 청크 검색, 예외처리.
  - `ragkit/config.py`: 환경 변수 (`RAG_PERSIST_DIR`, `RAG_EMBEDDING_MODEL`, `RAG_OPENAI_API_KEY`)를 읽어서 설정.
  - `ragkit/vectordb/chroma.py`: Chroma PersistentClient 래퍼.
  - `ragkit/embeddings/openai.py`: OpenAI Embedding API 호출.
- 특징:
  - 업서트 시 메타데이터가 비어 있으면 자동으로 `{"source": "text"}`를 추가합니다.
  - 컬렉션 이름은 항상 `lecture_<lecture_id>` 형태이며, 설정의 prefix로 조정 가능.

### 5.3 cap1_openalex_module
- 주요 파일:
  - `openalexkit/service.py`: 키워드 생성 → OpenAlex API 검색 → LLM 검증 → SSE 송출.
  - `openalexkit/models.py`: 요청(`OpenAlexRequest`), 응답(`OpenAlexResponse`), 논문 정보(`PaperInfo`) 구조.
- 특징:
  - `OpenAlexConfig`에서 동시성, 모델 이름, 최소 점수, 정렬 기준 등을 조정.
  - LLM 검증은 `verify_openalex=True`일 때만 수행 (속도 vs 정확도 조절 가능).

### 5.4 cap1_wiki_module
- 주요 파일:
  - `wikikit/service.py`: 키워드 생성, 팬아웃 검색, LLM/휴리스틱 평가, SSE 대응.
  - `wikikit/api/wiki_client.py`: Wikipedia API 호출 (httpx 기반).
  - `wikikit/llm/openai_client.py`: 키워드 생성과 문서 검증에 OpenAI 사용.
- 특징:
  - 상대 경로 import를 적용해 패키지 의존성을 확실히 함.
  - fallback 언어 설정(`fallback_to_ko`)으로 결과 부족 시 다른 언어 재검색.

### 5.5 cap1_youtube_module
- 주요 파일:
  - `youtubekit/service.py`: 다중 쿼리 검색, transcript(external), LLM 점수화.
  - `youtubekit/api/youtube_client.py`: YouTube Data API, transcript fetch.
  - `youtubekit/config/youtube_config.py`: API 키, 동시성, 모델 이름 등.
- 특징:
  - verify_yt 여부에 따라 LLM 스코어 vs 휴리스틱 사용.
  - transcript 가져오기 실패 시 fallback 로직 포함.

### 5.6 cap1_google_module
- 주요 파일:
  - `googlekit/service.py`: LLM 키워드 생성, 팬아웃 병렬 검색, LLM/Heuristic 검증.
  - `googlekit/api/google_client.py`: Google Custom Search API 클라이언트.
  - `googlekit/config/google_config.py`: API 키, Search Engine ID, 동시성 설정.
  - `googlekit/llm/openai_client.py`: 키워드 생성 및 검색 결과 LLM 검증.
  - `googlekit/utils/filters.py`: 중복 제거, 재정렬, URL 필터링.
  - `googlekit/utils/scoring.py`: Heuristic 점수 계산.
- 특징:
  - verify_google 여부에 따라 LLM 스코어 vs Heuristic 사용.
  - NO_SCORING 모드 지원 (검증 없이 빠른 검색).
  - 신뢰 도메인(.edu, .gov, arxiv.org 등) 가중치 반영.

### 5.7 server
- 주요 파일:
  - `app.py`: FastAPI 생성, 서비스 인스턴스 구성, lifespan 관리.
  - `routes/rag.py`: 텍스트/PDF 업서트 endpoint.
  - `routes/qa.py`: QA 이벤트 스트림 endpoint.
  - `routes/rec.py`: REC 이벤트 스트림 endpoint (OpenAlex/Wiki/YouTube/Google 통합).
  - `config.py`: AppSettings와 하위 설정(RAG/QA/REC) 정의.
  - `utils.py`: 컬렉션 ID 생성, 청크 변환, SSE 직렬화.
- 특징:
  - 서비스 인스턴스는 지연 로딩 방식으로 생성 (`_ensure_service`).
  - SSE 이벤트는 `format_sse`를 통해 JSON → 바이트 변환.

### 5.8 tests
- 구성:
  - `conftest.py`: Stub 서비스 정의, 가상 환경 설정.
  - `test_rag_pdf.py`, `test_rag_text.py`: 업서트 검증.
  - `test_qa_stream.py`, `test_rec_stream.py`: 스트리밍 동작 확인.
- 참고:
  - 실제 API 키/외부 호출 없이도 테스트를 수행할 수 있도록 설계.

### 5.9 스크립트 및 보조 파일
- `setup.sh`: Python 3.11 가상환경 생성 → 의존성 설치 → `.env` 자동 로드 패치.
- `test.sh`: 서버 실행 중 health 체크, 텍스트 업서트, REC 호출을 순서대로 수행.

---

## 6. 환경 구축

### 6.1 사전 준비물
- Python 3.11 (`python3.11` 명령어로 접근 가능해야 함).
- Bash shell 환경.
- 외부 네트워크(패키지 설치 및 API 호출).
- OpenAI API Key, YouTube API Key, Wikipedia 용 User-Agent 문자열.

### 6.2 `setup.sh` 자동 설치
```
./setup.sh
```
- 수행 내용:
  1. Python 3.11 확인 (기존 `.venv`가 다른 버전이면 삭제 후 재생성).
  2. `.venv` 활성화 후 `pip`, `setuptools`, `wheel` 업그레이드.
  3. `requirements.server.txt` 설치.
  4. `.env`가 없으면 `.env.example` 복사.
  5. `.venv/bin/activate` 스크립트에 `.env` 자동 로드 코드 삽입.

### 6.3 수동 설치 방법
1. `python3.11 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.server.txt`
4. `.env.example`를 `.env`로 복사하고 내용 수정.
5. `set -a; source .env; set +a`로 환경 변수 적재 (수동 방식).

### 6.4 가상환경 활성화
```
source .venv/bin/activate
```
- 이후 `.env`가 자동으로 읽히므로 추가로 export할 필요 없음.
- `deactivate` 명령으로 가상환경 종료.

---

## 7. 환경 변수(.env)

### 7.1 기본 구조
```
OPENAI_API_KEY="..."
YOUTUBE_API_KEY="..."
GOOGLE_SEARCH_API_KEY="..."
GOOGLE_SEARCH_ENGINE_ID="..."
WIKIKIT_USER_AGENT="WikiKit/1.0 (+https://example.com; contact: you@example.com)"
ANONYMIZED_TELEMETRY="False"
CHROMA_TELEMETRY_ENABLED="False"
RAG_PERSIST_DIR="server_storage/chroma_data_real"
```

### 7.2 키 설명
- `OPENAI_API_KEY`: OpenAI 요청 전반에 사용.
- `YOUTUBE_API_KEY`: YouTube Data API.
- `GOOGLE_SEARCH_API_KEY`: Google Custom Search API 키.
- `GOOGLE_SEARCH_ENGINE_ID`: Programmable Search Engine ID (CX).
- `WIKIKIT_USER_AGENT`: Wikipedia API 호출 시 필수 헤더.
- `ANONYMIZED_TELEMETRY`, `CHROMA_TELEMETRY_ENABLED`: Chroma 텔레메트리 비활성화.
- `RAG_PERSIST_DIR`: ChromaDB 저장 경로. 상대 경로로 지정하면 프로젝트 루트 기준.

### 7.3 예시
```
OPENAI_API_KEY="sk-proj-xxxx"
YOUTUBE_API_KEY="AIzaSy...."
GOOGLE_SEARCH_API_KEY="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
GOOGLE_SEARCH_ENGINE_ID="a1b2c3d4e5f6g7h8i"
WIKIKIT_USER_AGENT="WikiKit/1.0 (+https://github.com/acme; contact: ops@example.com)"
ANONYMIZED_TELEMETRY="False"
CHROMA_TELEMETRY_ENABLED="False"
RAG_PERSIST_DIR="server_storage/chroma_data_real"
```

---

## 8. 애플리케이션 설정 (AppSettings)

`server/config.py` 내 `AppSettings`는 RAG, QA, REC 설정을 품고 있습니다.

### 8.1 RAG 설정 (`RAGSettings`)
- `collection_prefix`: 컬렉션 이름 앞에 붙는 접두사 (기본 `"lecture"`).
- `qa_retrieve_top_k`: QA 용 RAG 청크 수 (기본 2).
- `rec_retrieve_top_k`: REC 용 RAG 청크 수 (기본 3).

### 8.2 QA 설정 (`QASettings`)
- `language`: 기본 언어(기본 `"ko"`).
- `question_types`: 기본 질문 유형 배열.
- `qa_top_k`: 사용할 질문 유형 수.

### 8.3 REC 설정 (`RECSettings`)
- OpenAlex/Wiki/YouTube/Google 각각 별도 서브 설정 보유.
  - OpenAlexSettings: `top_k`, `verify`, `year_from`, `sort_by`, `min_score`, `language`
  - WikiSettings: `top_k`, `verify`, `wiki_lang`, `language`, `min_score`, `fallback_to_ko`
  - YouTubeSettings: `top_k`, `verify`, `yt_lang`, `language`, `min_score`
  - GoogleSettings: `top_k`, `verify`, `search_lang`, `language`, `min_score`
- 예: OpenAlex → `top_k`, `verify`, `sort_by`, `min_score`, `year_from`.
- Wiki → `verify_wiki`, `wiki_lang`, `fallback_to_ko`.
- YouTube → `verify_yt`, `yt_lang`, `min_score`.
- 값은 `.env`로 직접 바꾸는 대신 코드에서 수정 후 배포하거나 Pydantic 설정을 확장하여 환경 변수 연결 가능.

---

## 9. 데이터 흐름

### 9.1 업서트(Upsert) 흐름
1. 텍스트 업서트(`POST /rag/text-upsert`) 또는 PDF 업서트(`POST /rag/pdf-upsert`) 요청.
2. `build_collection_id`가 `lecture_<lecture_id>` 생성.
3. OpenAI 임베딩 생성 → ChromaDB에 저장.
4. 메타데이터와 청크 ID는 자동 생성/수정.

### 9.2 QA 흐름
1. `POST /qa/generate` 호출.
2. RAG 청크 검색 (설정된 top_k).
3. 각 질문 유형별 `asyncio.create_task`로 OpenAI 호출.
4. 완료되는 순서대로 `qa_partial` 이벤트 출력.
5. 모든 질문이 완료되면 `qa_complete` 이벤트로 종료.

### 9.3 REC 흐름
1. `POST /rec/recommend` 호출.
2. RAG 청크 검색 (설정된 top_k).
3. OpenAlex, Wiki, YouTube, Google task를 동시에 실행.
4. 끝나는 순서대로 `rec_partial` 이벤트 전송.
5. 모든 작업 종료 시 `rec_complete`.

### 9.4 오류 처리 흐름
- 업서트 실패: HTTP 400/500으로 응답 (원인 포함).
- QA, REC 중 특정 작업 실패: `qa_error`/`rec_error` 이벤트 전송 후 다른 작업 지속.
- 로그: Uvicorn 로그를 참조하여 OpenAI, Chroma, 외부 API 오류 파악.

---

## 10. API 명세

### 10.1 Health 체크
- **Endpoint**: `GET /health`
- **응답**: `{"status":"ok"}`
- **용도**: 서버 상태 확인.

### 10.2 RAG 업서트

#### 10.2.1 `POST /rag/pdf-upsert`
- **형식**: `multipart/form-data`
- **필드**:
  - `lecture_id`: 문자열 (필수)
  - `file`: PDF 파일 (필수)
  - `base_metadata`: JSON 문자열 (선택)
- **입력 필드 설명**

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | 강의를 식별하는 ID. 공백 불가 |
| file | file (PDF) | 예 | 업로드할 PDF 파일 |
| base_metadata | string(JSON) | 아니오 | 모든 페이지에 공통으로 적용할 메타데이터 (예: `{"subject":"AI"}`) |

- **출력 필드 설명**

| 필드명 | 타입 | 설명 |
|--------|------|------|
| collection_id | string | 저장된 Chroma 컬렉션 이름 (`lecture_<lecture_id>`) |
| result.collection_id | string | 실제 업서트된 컬렉션 ID |
| result.count | int | 업서트된 페이지 수 |
| result.embedding_dim | int | 임베딩 벡터 차원 |

- **응답**:
  ```
  {
    "collection_id": "lecture_lec-001",
    "result": {
      "collection_id": "lecture_lec-001",
      "count": 3,
      "embedding_dim": 3072
    }
  }
  ```
- **주의 사항**:
  - 잘못된 파일 형식 → 400.
  - 빈 파일 업로드 → 400.
  - metadata JSON 파싱 실패 → 400.

#### 10.2.2 `POST /rag/text-upsert`
- **형식**: `application/json`
- **본문 예시**:
  ```json
  {
    "lecture_id": "001",
    "items": [
      {"text": "요약 A"},
      {"text": "요약 B", "metadata": {"topic": "stack"}}
    ]
  }
  ```
- **입력 필드 설명**

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | 강의 ID |
| items | array | 예 | 업서트할 텍스트 목록 |
| items[].text | string | 예 | 저장할 텍스트 내용 |
| items[].id | string | 아니오 | 사용자 정의 문서 ID (없으면 자동 생성) |
| items[].section_id | string | 아니오 | 섹션 ID. metadata에 병합됨 |
| items[].metadata | object | 아니오 | 추가 메타데이터. 없으면 `{"source":"text"}` 자동 부여 |

- **출력 필드 설명**

| 필드명 | 타입 | 설명 |
|--------|------|------|
| collection_id | string | 저장된 컬렉션 ID (`lecture_<lecture_id>`) |
| result.collection_id | string | 실제 업서트 컬렉션 ID |
| result.count | int | 업서트된 문서 수 |
| result.embedding_dim | int | 임베딩 벡터 차원 |

- **응답**:
  ```
  {
    "collection_id": "lecture_001",
    "result": {
      "collection_id": "lecture_001",
      "count": 2,
      "embedding_dim": 3072
    }
  }
  ```
- **메타데이터 자동 보강**:
  - metadata가 비어 있으면 `{"source":"text"}` 추가.
  - `section_id` 값을 metadata에도 병합.

### 10.3 QA 생성

#### 10.3.1 `POST /qa/generate`
- **형식**: `application/json`
- **본문 예시**:
  ```json
  {
    "lecture_id": "001",
    "section_id": 1,
    "section_summary": "스택과 큐의 차이를 설명한다."
  }
  ```
- **입력 필드 설명**

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | RAG 컬렉션과 매핑되는 강의 ID |
| section_id | int | 예 | 섹션 번호 (1 이상) |
| section_summary | string | 예 | 섹션 요약. 최소 10자 |
| subject | string | 아니오 | 과목 정보 (선택) |

- **출력 이벤트 설명**

| 이벤트 | 주요 필드 | 설명 |
|--------|-----------|------|
| qa_context | collection_id, chunk_count | QA 생성 전에 사용된 컬렉션 및 청크 수 |
| qa_partial | type, qa{question, answer}, index | 각 질문 유형별 생성 결과 |
| qa_error | type, error | 특정 유형 생성 실패 시 |
| qa_complete | total, duration_ms | 전체 생성 완료 통계 |

- **응답**: SSE 스트림
  ```
  event: qa_context
  data: {"event":"context_ready","collection_id":"lecture_001","chunk_count":2}

  event: qa_partial
  data: {"type":"응용","qa":{"type":"응용","question":"...","answer":"..."}, "index":1}

  event: qa_complete
  data: {"total":3,"duration_ms":3459}
  ```
- **참고**: 질문 유형 순서는 완료 시간에 따라 달라질 수 있습니다.

### 10.4 REC 추천

#### 10.4.1 `POST /rec/recommend`
- **형식**: `application/json`
- **본문 예시**:
  ```json
  {
    "lecture_id": "001",
    "section_id": 1,
    "section_summary": "스택과 큐의 차이를 설명한다.",
    "previous_summaries": [],
    "yt_exclude": [],
    "wiki_exclude": [],
    "paper_exclude": [],
    "google_exclude": []
  }
  ```
- **입력 필드 설명**

| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| lecture_id | string | 예 | RAG 컬렉션과 매핑되는 강의 ID |
| section_id | int | 예 | 섹션 번호 (1 이상) |
| section_summary | string | 예 | 섹션 요약 |
| previous_summaries | array | 아니오 | 이전 섹션 요약 목록 (`section_id` ≥ 1) |
| yt_exclude | array[string] | 아니오 | 추천에서 제외할 유튜브 제목 목록 |
| wiki_exclude | array[string] | 아니오 | 제외할 위키 제목 목록 |
| paper_exclude | array[string] | 아니오 | 제외할 논문 ID 목록 |
| google_exclude | array[string] | 아니오 | 제외할 구글 검색 URL 목록 |

- **출력 이벤트 설명**

| 이벤트 | 주요 필드 | 설명 |
|--------|-----------|------|
| rec_context | collection_id, chunk_count | 추천에 사용된 컬렉션 및 청크 수 |
| rec_partial | source, count, items[], elapsed_ms | 각 Provider의 결과 (items는 Provider별 모델 dump) |
| rec_error | source, error, elapsed_ms | 특정 Provider 실패 시 |
| rec_complete | completed_sources, duration_ms | 완료된 Provider 수와 소요 시간 |

- **응답**: SSE 스트림
  ```
  event: rec_context
  data: {"event":"context_ready","collection_id":"lecture_001","chunk_count":2}

  event: rec_partial
  data: {"source":"wiki","count":2,"items":[...],"elapsed_ms":1234}

  event: rec_partial
  data: {"source":"google","count":2,"items":[...],"elapsed_ms":1567}

  event: rec_complete
  data: {"completed_sources":4,"duration_ms":5120}
  ```
- `previous_summaries.section_id` ≥ 1 이어야 하며, lecture_id는 업서트와 동일해야 합니다.
- **Provider 순서**: OpenAlex, Wiki, YouTube, Google (병렬 실행, 완료 순서대로 스트림 전송)

### 10.5 SSE 이벤트 포맷
- `qa_context`, `rec_context`: 초기 컨텍스트 정보.
- `qa_partial`, `rec_partial`: 각각의 결과 아이템.
- `qa_error`, `rec_error`: 특정 작업 실패.
- `qa_complete`, `rec_complete`: 전체 요약.

### 10.6 cURL 예시
1. 건강 상태  
   `curl http://127.0.0.1:8000/health`
2. 텍스트 업서트  
   `curl -X POST http://127.0.0.1:8000/rag/text-upsert -H "Content-Type: application/json" -d '{"lecture_id":"001","items":[{"text":"요약 A"},{"text":"요약 B"}]}'`
3. QA SSE  
   `curl -v -N -X POST http://127.0.0.1:8000/qa/generate -H "Content-Type: application/json" -d '{"lecture_id":"001","section_id":1,"section_summary":"..."}'`
4. REC SSE  
   `curl -v -N -X POST http://127.0.0.1:8000/rec/recommend -H "Content-Type: application/json" -d '{"lecture_id":"001","section_id":1,"section_summary":"...","previous_summaries":[],"yt_exclude":[],"wiki_exclude":[],"paper_exclude":[]}'`

---

## 11. 설정 가이드

### 11.1 질문 유형 조정
- `server/config.py` → `QASettings.question_types` 변경.
- ex) `["개념", "응용", "심화"]`.
- `qa_top_k`로 질문 개수 조절.

### 11.2 Provider 세부 설정
- `server/config.py` → `RECSettings`.
- OpenAlex:
  - `top_k`, `verify`, `year_from`, `sort_by`, `min_score`.
- Wiki:
  - `verify_wiki`, `wiki_lang`, `fallback_to_ko`.
- YouTube:
  - `verify_yt`, `yt_lang`, `min_score`.
- 필요 시 설정 구조를 확장하거나 별도 config 파일을 도입할 수 있음.

### 11.3 설정 우선순위

**검증(Verification) 설정 우선순위:**
1. **server/config.py의 verify 필드** (최우선)
   - 예: `OpenAlexSettings.verify = True` → 강제로 검증 활성화
   - `None`이면 다음 단계로 fallback
2. **각 모듈의 VERIFY_*_DEFAULT** (fallback)
   - 예: `openalexkit/config/flags.py`의 `VERIFY_OPENALEX_DEFAULT`
   - server/config.py에서 verify를 지정하지 않았을 때만 사용

**NO_SCORING 모드:**
- 각 모듈의 `config/flags.py`에서 `NO_SCORING = True`로 설정
- 검증 단계를 완전히 스킵하고 검색 결과만 빠르게 반환
- 효과:
  - OpenAlex: 논문 검색 결과 → `reason="search"`, `score=10`
  - Wiki: 문서 검색 결과 → `reason="search"`, `score=10`
  - YouTube: 동영상 검색 결과 (description 사용) → `reason="search"`, `score=10`
- 프로토타입 개발/테스트 시 유용 (검증 비용 절감)

### 11.4 저장소 경로 지정
- `.env` → `RAG_PERSIST_DIR`.
- 상대 경로 사용 시 프로젝트 루트를 기준으로 자동 생성.
- 운영 환경에서는 `/var/lib/livenote/chroma` 등 절대 경로 지정 권장.

---

## 12. 운영 절차

### 12.1 로컬 실행
1. `./setup.sh`
2. `source .venv/bin/activate`
3. `uvicorn server.main:app --reload`
4. cURL 또는 Postman으로 API 호출.

### 12.2 `test.sh` 점검
```
./test.sh
```
- 수행 순서:
  1. `/health`
  2. 텍스트 업서트 (임시 lecture_id)
  3. REC SSE 간단 호출

### 12.3 클라우드 배포
- Python 3.11 설치 → `./setup.sh` → `.env` 수정 → `source .venv/bin/activate`.
- `uvicorn` 또는 WSGI 옵션으로 실행.
- systemd, supervisor, pm2 등으로 백그라운드 실행 관리 권장.

---

## 13. 문제 해결

### 13.1 자주 발생하는 에러
| 메시지 | 원인 | 해결 |
|--------|------|------|
| `Collection ... does not exist` | 업서트된 `lecture_id`와 다름 | 동일한 `lecture_id` 사용 |
| `metadata must be non-empty` | 메타데이터 없음 | 최신 코드 사용 (자동 보강) |
| `curl: (18)` | SSE 연결 종료 알림 | 정상 동작, SSE 이벤트 확인 |
| `python-multipart` 필요 | multipart 업로드 사용 | `pip install python-multipart` (이미 포함) |
| `Failed to send telemetry event` | Chroma 텔레메트리 버그 | 무시 가능; 비활성화 유지 |

### 13.2 텔레메트리 경고
- Chroma 내부에서 발생하는 경고로 결과에는 영향 없음.
- `.env`에서 텔레메트리를 끄면 빈도 감소.

### 13.3 Chroma 컬렉션 문제
- `.env` 적용이 되지 않은 상태에서 서버 기동 → 기본 `test_chroma_data` 사용.
- 해결: `source .venv/bin/activate`로 `.env` 적용 후 서버 실행.
- 필요 시 옛 경로 삭제: `rm -rf test_chroma_data`.

### 13.4 SSE 진단
- `curl -v -N ...`를 사용하여 이벤트 수신을 확인.
- 스트림 중간 종료 시 서버 콘솔 로그 확인.
- `qa_error`, `rec_error` 이벤트로 세부 정보를 수신.

---

## 14. 테스트 전략

### 14.1 자동 테스트
- `pytest` 실행.
- 주요 테스트:
  - `test_rag_pdf.py`, `test_rag_text.py`: 업서트 검증.
  - `test_qa_stream.py`: QA 스트리밍 순서와 완료 이벤트 확인.
  - `test_rec_stream.py`: REC 스트리밍, 에러 처리 검증.
- `tests/conftest.py`: Stub 서비스로 외부 API 호출 대체.

### 14.2 수동 검증
1. 텍스트 업서트 → Chroma 데이터 생성 확인.
2. QA SSE → 질문별 `qa_partial` 수신 확인.
3. REC SSE → `wiki`, `youtube`, `openalex` 순차적 이벤트 확인.
4. 로그에서 예외/경고 여부 확인.
5. API 키/환경 설정 오류 여부 재확인.

---

## 15. 모범 사례

- 항상 `source .venv/bin/activate` 후 작업 (의존성 일관성 유지).
- `.env` 파일은 버전 관리 제외 (민감 정보 보안).
- `lecture_id`는 업서트/QA/REC 전체에서 동일하게 사용.
- Chroma 저장소는 운영 환경에서 안정적인 경로 사용.
- 오타나 잘못된 URL로 인해 422/400 발생 시 바로 로그 확인.
- 텔레메트리 경고는 무시하되, 잦은 경우 Chroma 버전 업그레이드 고려.

---

## 16. 향후 개선 계획

- RAG 청크 내용을 REST로 조회할 수 있는 디버그 endpoint 추가.
- 캐시 전략(예: OpenAI 응답 캐시) 적용 검토.
- 인증/권한 관리 레이어 도입 (토큰 기반).
- Docker Compose 구성으로 전체 스택 로컬 실행.
- 모듈별 로그 레벨 세분화 및 구조화된 로깅.

---

## 17. 부록

### 17.1 시퀀스 다이어그램(텍스트)

#### 17.1.1 QA 흐름
```
클라이언트 → /qa/generate → FastAPI
FastAPI → RAGService.retrieve → ChromaDB
FastAPI ← ChromaDB (청크 리스트)
FastAPI → OpenAI (질문 유형별 비동기 호출)
FastAPI ← OpenAI (응답)
FastAPI → SSE (qa_partial, qa_complete)
```

#### 17.1.2 REC 흐름
```
클라이언트 → /rec/recommend → FastAPI
FastAPI → RAGService.retrieve → ChromaDB
FastAPI ← ChromaDB (청크)
FastAPI → OpenAlex/Wiki/YouTube (동시에 요청)
각 Provider ↔ 외부 API (OpenAI 포함)
FastAPI ← Provider 응답
FastAPI → SSE (rec_partial, rec_complete)
```

### 17.2 ChromaDB 설명
- 컬렉션 이름: `lecture_<id>`
- 저장 위치: `RAG_PERSIST_DIR` 경로
- 메타데이터 요구사항: key-value, 문자열/숫자/불리언만 허용 (복잡한 경우 JSON 문자열로 변환)
- retrieve 시 top_k 기본값:
  - QA: `settings.rag.qa_retrieve_top_k`
  - REC: `settings.rag.rec_retrieve_top_k`

### 17.3 용어집
- **RAG**: 기존 데이터를 참고해 답변을 생성하는 방식.
- **SSE**: 서버에서 클라이언트로 일방향 스트림을 전송하는 HTTP 표준.
- **QA Partial**: 하나의 질문-답변 페어.
- **REC Partial**: 하나의 데이터 소스에서 가져온 추천 목록.
- **Telemetry Warning**: Chroma가 익명 통계 전송 실패 시 출력하는 경고, 기능 영향 없음.

---

## 18. 변경 이력

| 날짜 | 작성자 | 변경 내용 |
|------|--------|-----------|
| 2025-11-06 | 팀 | 전체 README를 한국어로 번역 및 보강하여 500줄 이상의 종합 문서로 구성 |

---

### 끝.
