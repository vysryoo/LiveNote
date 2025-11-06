# OpenAlex Module 통합 노트

**작성일**: 2025-10-30  
**목적**: OpenAlex 모듈 개발 완료 및 통합 안내

---

## 📋 개발 완료 항목

### ✅ Phase 1-8 모두 완료

1. **기본 구조**: 디렉토리, setup.py, requirements.txt, .gitignore, __init__.py
2. **모델 정의**: Pydantic 모델 (OpenAlexRequest, OpenAlexResponse, PaperInfo, RAGChunk, PreviousSectionSummary)
3. **설정 관리**: config/ (openalex_config.py, flags.py, prompts.py)
4. **API 클라이언트**: OpenAlexAPIClient, OpenAIClient
5. **유틸리티**: parser.py, filters.py
6. **핵심 서비스**: OpenAlexService (전체 흐름 조율)
7. **테스트**: test_openalex.py (5개 시나리오)
8. **문서화**: README.md (RAGKit/QAKit 스타일)

---

## 📁 모듈 위치

```
module_intergration/
├── cap1_RAG_module/           # RAGKit (참고)
├── cap2_QA_module/            # QAKit (참고, 존재 시)
└── cap3_openalex_module/      # ✨ OpenAlexKit (신규)
    ├── README.md
    ├── setup.py
    ├── requirements.txt
    ├── test_openalex.py
    └── openalexkit/
        ├── __init__.py
        ├── models.py
        ├── service.py
        ├── config/
        ├── api/
        ├── llm/
        └── utils/
```

---

## 🚀 빠른 시작

### 1. 설치

```bash
cd module_intergration/cap3_openalex_module

# 가상환경 생성
python -m venv .venv
source .venv/bin/activate

# 패키지 설치
pip install -e .

# API 키 설정
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### 2. 기본 사용법

```python
import asyncio
from openalexkit import OpenAlexService, OpenAlexRequest

async def main():
    service = OpenAlexService()
    
    request = OpenAlexRequest(
        session_id="test_001",
        section_id=1,
        section_summary="스택의 실전 응용: 괄호 검사, 후위 표기법 계산",
        language="ko",
        top_k=5,
        verify_openalex=True
    )
    
    results = await service.recommend_papers(request)
    
    for paper in results:
        print(f"[{paper.score:.1f}] {paper.paper_info.title}")
        print(f"  → {paper.reason}")
    
    await service.close()

asyncio.run(main())
```

### 3. 테스트 실행

```bash
python test_openalex.py
```

**예상 결과**:
- 5개 시나리오 실행 (CS, 수학, 물리, 화학, 생물)
- 총 20-25개 논문 추천
- 평균 3-5초/시나리오

---

## 🔑 핵심 기능

### 1. 검색 쿼리 생성 (LLM)
- 섹션 요약 → 학술 검색 토큰 (2-4개, 영어)
- 예: "스택 응용" → `["stack data structure", "postfix notation"]`

### 2. OpenAlex API 검색
- 필터: 출판 연도, 언어(영어), 논문 타입
- 결과: 25개 논문

### 3. 전처리
- 중복 제거 (DOI/제목 기준)
- 재랭킹 (키워드 매칭 점수)

### 4. 검증 (조건부)
- **LLM 검증** (verify_openalex=True): 병렬 처리, 점수 0-10
- **Heuristic** (verify_openalex=False): 빠른 키워드 기반 점수

### 5. 추천 결과
- Top-K 논문 (점수 순 정렬)
- 각 논문: 제목, URL, 초록, 연도, 인용 수, 저자, 점수, 이유

---

## ⚙️ 설정 커스터마이징

### 환경 변수 (.env)

```bash
OPENAI_API_KEY=sk-your-key-here
```

### 코드 레벨 (config/openalex_config.py)

```python
class OpenAlexConfig:
    LLM_MODEL = "gpt-4o-mini"           # LLM 모델
    LLM_TEMPERATURE = 0.3                # Temperature
    CARD_LIMIT = 10                      # 검증 대상 최대 수
    VERIFY_CONCURRENCY = 5               # 병렬 검증 동시성
    TIMEOUT = 10                         # HTTP 타임아웃 (초)
    ABSTRACT_MAX_LENGTH = 500            # 초록 최대 길이
```

### 프롬프트 (config/prompts.py)

- `QUERY_GENERATION_PROMPT`: 검색 쿼리 생성 프롬프트
- `SCORE_PAPER_PROMPT`: 논문 검증 프롬프트

---

## 🔗 통합 가이드

### Spring 백엔드 통합 (향후)

**옵션 1: FastAPI 래퍼** (권장)
```python
# fastapi_wrapper.py
from fastapi import FastAPI
from openalexkit import OpenAlexService, OpenAlexRequest

app = FastAPI()
service = OpenAlexService()

@app.post("/recommend-papers")
async def recommend_papers(request: OpenAlexRequest):
    results = await service.recommend_papers(request)
    return {"papers": [r.dict() for r in results]}
```

**옵션 2: 직접 호출**
```python
# Python subprocess로 호출 (Spring에서)
import subprocess
import json

result = subprocess.run(
    ["python", "recommend.py", json.dumps(request_data)],
    capture_output=True,
    text=True
)
papers = json.loads(result.stdout)
```

### REC 모듈 통합 (최종 목표)

```
REC 모듈 (통합 자료 추천)
├── Provider: OpenAlex (논문)   ← 이 모듈
├── Provider: Wikipedia (백과)
├── Provider: YouTube (영상)
└── Provider: Web (블로그)
```

---

## 📊 테스트 시나리오

### 1. CS (자료구조) - RAG + 이전 섹션 포함
- 섹션: "스택의 실전 응용..."
- 컨텍스트: 이전 2섹션 + RAG 1개
- 검증: LLM

### 2. 수학 (미적분) - 최소 파라미터
- 섹션: "미분은 함수의 순간 변화율..."
- 컨텍스트: 없음
- 검증: Heuristic (빠름)

### 3. 물리 (양자역학) - 영어 + LLM 검증
- 섹션: "Schrödinger equation describes..."
- 언어: 영어
- 검증: LLM

### 4. 화학 (유기화학) - 중복 제거 테스트
- 섹션: "SN2 반응은 친핵체가..."
- exclude_ids 포함
- 검증: LLM

### 5. 생물 (세포생물학) - RAG만 포함
- 섹션: "미토콘드리아는 세포의 에너지 공장..."
- 컨텍스트: RAG 1개만
- 검증: LLM

---

## 🎯 명세서 준수 체크리스트

### ✅ 모든 요구사항 충족

- [x] Pydantic 모델 정의 (OpenAlexRequest, OpenAlexResponse, PaperInfo)
- [x] OpenAlex API 클라이언트 (search_papers, _parse_paper)
- [x] OpenAI LLM 클라이언트 (generate_query, score_paper)
- [x] 유틸리티 (parse_abstract_inverted_index, deduplicate, rerank)
- [x] OpenAlexService (recommend_papers, 병렬 검증)
- [x] 설정 관리 (config/, 프롬프트 분리)
- [x] 테스트 (5개 시나리오)
- [x] README.md (RAGKit/QAKit 스타일)
- [x] 에러 처리 (try-except, fallback 점수)
- [x] 로깅 (logging 모듈)
- [x] 병렬 처리 (asyncio.Semaphore)

### ✅ 코딩 스타일 일관성

- [x] RAGKit과 동일한 디렉토리 구조
- [x] QAKit과 동일한 병렬 처리 패턴
- [x] 기존 OpenAlexProvider 로직 참고 (중복 제거, 재랭킹, LLM 검증)

### ✅ 문서화

- [x] README.md (사용 흐름, 예제, 문제 해결)
- [x] 모든 함수에 docstring
- [x] 코드 주석 (핵심 로직 설명)

---

## 🔧 문제 해결

### API 키 오류
```bash
export OPENAI_API_KEY='sk-your-key-here'
# 또는
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### 검색 결과 없음
- `year_from` 낮추기 (2015 → 2000)
- 섹션 요약 구체화

### LLM 검증 느림
- `verify_openalex=False` (Heuristic 사용)
- `VERIFY_CONCURRENCY` 증가 (5 → 10)

---

## 🎓 참고 자료

### 기존 코드
- **RAGKit**: `cap1_RAG_module/` (모듈 구조)
- **QAKit**: `cap2_QA_module/` (병렬 처리, 프롬프트)
- **OpenAlexProvider**: `프로토타입_전사통합2/services/resources/provider_openalex.py`

### 외부 문서
- [OpenAlex API 문서](https://docs.openalex.org/)
- [OpenAI API 문서](https://platform.openai.com/docs)

---

## 📝 다음 단계 (선택)

1. **FastAPI 래퍼 작성** (Spring 통합용)
2. **Docker 이미지 생성** (배포용)
3. **CI/CD 파이프라인** (자동 테스트)
4. **REC 모듈 통합** (Wiki, YouTube, Web Provider와 통합)

---

**OpenAlexKit 개발 완료! 고품질 학술 논문 추천 모듈을 LiveNote에 통합하세요.** 🚀

---

파일 생성 시점: 2025-10-30  
위치: module_intergration/cap3_openalex_module/
