# LiveNote AI 서버

FastAPI + LangChain·LangGraph 기반의 실시간 강의 노트 서비스 AI 서버입니다. 백엔드만 호출하며, API는 [API_SPECIFICATION.md](API_SPECIFICATION.md)에 있습니다.

---

## 실행 방법

[uv](https://docs.astral.sh/uv/)가 필요합니다. Python 3.11이 없으면 uv가 받습니다.

```bash
./setup.sh                                      # 의존성 설치, .env가 없으면 .env.example 복사
uv run uvicorn server.main:app --port 8003      # 서버 (:8003)
uv run pytest                                   # 테스트 (외부 API 호출 없음)
```

의존성은 `pyproject.toml`과 `uv.lock`으로 관리합니다. `uv add <패키지>==<버전>`으로 바꾸고 두 파일을 함께 커밋합니다.

---

## 환경 설정

`ai/.env` 또는 셸 환경변수로 지정합니다. 같은 키는 셸 환경변수가 우선합니다. 예시는 [.env.example](.env.example)에 있습니다.

필수 (하나라도 비어 있으면 서버가 시작되지 않음)

| 변수 | 설명 |
| --- | --- |
| `OPENAI_API_KEY` | 생성 모델, 임베딩 |
| `INTERNAL_API_KEY` | 백엔드 `env.properties`와 같은 값. 요청 인증과 콜백 헤더에 사용 |
| `YOUTUBE_API_KEY` | YouTube Data API v3 |
| `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` | 네이버 클라우드 NAVER API HUB 블로그 검색 |

선택

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `LLM_MODEL` | `gpt-6-luna` | 모든 LLM 호출의 모델 |
| `LLM_<용도>_MODEL`, `LLM_<용도>_REASONING_EFFORT` | -, `none` | 용도별 모델·추론 강도. 용도: `SUMMARY`, `QA`, `QUERY`, `VERIFY` |
| `RAG_PERSIST_DIR`, `RAG_UPLOAD_DIR` | `server_storage/chroma_data`, `server_storage/uploads` | 벡터 저장소, 업로드 PDF. 상대 경로는 `ai/` 기준 |
| `RAG_CHUNK_STRATEGY` | `semantic` | 강의 자료 분할 방식: `page`, `recursive`, `semantic` |
| `SUMMARY_CALLBACK_URL` | - | 요약 요청에 콜백 URL이 없을 때 사용 |

분할 세부값(`RAG_SEMANTIC_*`, `RAG_CHUNK_*`)과 요청 처리 기준(검색 개수, 질문 유형, 추천 개수·최소 점수)은 `core/config.py`에 있습니다.

---

## 파일 구조

```
ai/
├── server/         # FastAPI 앱, 라우트, 요청 모델, 서비스 묶음, QnA·추천 공통 RAG 문맥 검색, 내부 인증, 콜백 전송
├── core/           # 설정, LLM 호출, 외부 API 재시도, 로깅, 공용 모델
├── rag/            # PDF 분할(page, recursive, semantic), Chroma 저장·검색
├── qa/             # QnA 프롬프트, 생성 그래프, 스트림 파서
├── recommend/      # 추천 공통 흐름, 추천 그래프, 공급자(providers/: 논문, 위키, 영상, 블로그)
├── summary/        # 섹션 요약
├── eval/           # 정확도·응답 시간·전사 오류율 측정과 보고서(results/)
└── tests/          # 테스트, 스냅샷(data/snapshots/)
```

---

## 기능 설명

- **RAG**: 강의 자료 PDF를 의미 단위로 나눠 저장하고, 확정된 섹션 요약도 저장합니다. QnA·추천 요청 때 강의 자료 조각과 이전 섹션 요약을 따로 검색해 합칩니다
- **QnA**: 질문 유형(개념, 응용, 비교, 심화)별로 동시에 생성하고 SSE로 스트리밍합니다. 현재 섹션에서 말한 내용만 근거로 출제합니다
- **자료 추천**: 논문(OpenAlex), 위키백과, 영상(YouTube), 블로그(네이버)를 동시에 추천하고 종류마다 콜백합니다. 검색어 생성 → 후보 검색 → 점수(LLM 검증 또는 휴리스틱) → 상위 결과 순서이며, 검증에 실패한 후보는 뺍니다
- **요약**: 섹션 전사를 1~2문장으로 요약하고 콜백합니다
- **LLM 호출**: 모든 호출이 `core/llm.py`를 거치며, 호출마다 토큰 사용량을 JSON 로그로 남깁니다

---

## 평가

실제 API를 쓰므로 비용이 듭니다. 평가 데이터(`eval/data/`)는 git에 없습니다.

| 스크립트 | 측정 |
| --- | --- |
| `eval.run_retrieval` | 강의 자료 검색 Precision@4 |
| `eval.run_cards` | QnA·추천 자료 Precision@4 (AI 서버를 띄운 뒤 실행) |
| `eval.run_latency` | QnA 스트리밍 응답 시간 |
| `eval.transcription_cer` | 전사 글자 오류율 |

평가 데이터는 `eval.prepare_data`, `eval.collect_sections`로 만듭니다. 채점은 `gpt-6.1-terra`의 이진 판정이고, 결과는 `eval/results/`에 있습니다.

현재 설정 기준 결과 (보고서 이름은 `실험_측정대상_데이터`, 데이터는 `dev` 또는 `test`)

| 측정 | 보고서 | 결과 |
| --- | --- | --- |
| 강의 자료 검색 Precision@4 | `E2_retrieval_test` | 88.5% (133섹션) |
| QnA Precision@4 | `E14_qna_test` | 88.8% (60섹션) |
| 추천 자료 Precision@4 | `E14_resource_test` | 87.5% (30섹션) |
| QnA 스트리밍 응답 시간 | `L_after` | 질문 표시 중앙값 1,613ms, 전체 완료 중앙값 2,753ms |
| 전사 글자 오류율 | `T_transcription` | 2.92% (`gpt-transcribe`) |
