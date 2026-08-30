# RAGKit - 실시간 강의 RAG 시스템

**LiveNote 프로젝트를 위한 RAG(Retrieval-Augmented Generation) 벡터 데이터베이스 모듈**

> 💡 **이 모듈의 역할**: Spring 백엔드가 실시간 강의 전사본과 요약본을 저장하고, 관련된 이전 내용을 검색해서 LLM에게 컨텍스트를 제공하는 것

## 📋 목차

- [이 모듈이 하는 일](#-이-모듈이-하는-일)
- [LiveNote에서의 실제 사용 흐름](#-livenote에서의-실제-사용-흐름)
- [설치](#-설치)
- [핵심 API 3가지](#-핵심-api-3가지)
- [실전 사용 예제](#-실전-사용-예제)
- [테스트](#-테스트)
- [문제 해결](#-문제-해결)

---

## 🎯 이 모듈이 하는 일

LiveNote는 **실시간 강의를 전사하고 요약**하는 서비스입니다. 이 RAG 모듈은:

### 1. **강의 중 실시간 저장** (매 1분마다)
```
섹션 1: "스택은 LIFO 구조입니다..." → 벡터DB 저장
섹션 2: "큐는 FIFO 구조입니다..." → 벡터DB 저장
섹션 3: "스택의 실전 응용..." → 벡터DB 저장
```

### 2. **이전 내용 검색** (섹션마다)
```
현재: "스택의 실전 응용..."
  ↓ 검색
과거: "스택은 LIFO 구조..." (유사도 0.92)
과거: "큐는 FIFO 구조..." (유사도 0.65)
```

### 3. **LLM에게 컨텍스트 제공**
```
LLM에게 전달:
- 현재 섹션: "스택의 실전 응용..."
- 관련된 이전 섹션: "스택은 LIFO 구조..."
- 강의노트: "1장. 스택과 큐..."

↓

LLM이 생성:
- 예상 질문 3개
- 추천 자료 (Wikipedia, 논문 등)
```

---

## 🔄 LiveNote에서의 실제 사용 흐름

### **Phase 1: 강의 시작 전 - 강의노트 업로드** (1회만)

```
학생 → Spring → RAG 모듈
```

**1. 학생이 강의노트 PDF 업로드**
```
data_structure.pdf (20페이지)
```

**2. Spring이 RAG 모듈에 요청**
```python
# Spring에서 FastAPI로 HTTP 요청
POST /rag/upsert-pdf
{
  "collection_id": "lecture_notes_cs",  # 강의노트 저장소
  "pdf_file": <data_structure.pdf>,
  "metadata": {
    "type": "lecture note",
    "subject": "CS",
    "course": "데이터구조"
  }
}
```

**3. RAG 모듈이 하는 일**
```python
# 1. PDF를 페이지별로 분할
pages = [
  "1장. 스택과 큐...",
  "2장. 트리 구조...",
  ...
  "20장. 그래프 알고리즘..."
]

# 2. 각 페이지를 벡터로 변환 (OpenAI 임베딩)
for page in pages:
    embedding = openai.embed(page)  # [3072차원 벡터]
    
# 3. ChromaDB에 저장
vectordb.save(
    collection="lecture_notes_cs",
    embeddings=[...],
    texts=pages
)
```

**4. 결과 → ChromaDB 상태**
```
�� Collection: "lecture_notes_cs"
├── data_structure|p0: [벡터] + "1장. 스택과 큐..."
├── data_structure|p1: [벡터] + "2장. 트리..."
├── ...
└── data_structure|p19: [벡터] + "20장. 그래프..."
```

---

### **Phase 2: 강의 중 - 섹션마다 반복** (매 1분)

```
실시간 오디오 → STT → LLM 요약 → Spring → RAG 모듈
                                    ↓
                              LLM (Q&A 생성)
```

#### **섹션 1 (0~60초): "스택 설명"**

**1. Spring이 섹션 요약 저장 요청**
```python
POST /rag/upsert-text
{
  "collection_id": "session_abc123",  # 이 강의 세션 ID
  "items": [{
    "text": "스택은 LIFO 구조입니다. push와 pop으로 데이터를 관리하며...",
    "metadata": {
      "section_id": 1,
      "type": "summary",
      "timestamp": 1703001234567,
      "subject": "CS"
    }
  }]
}
```

**2. RAG 모듈이 하는 일**
```python
# 임베딩 생성 + 저장
embedding = openai.embed("스택은 LIFO...")

# 실제 저장되는 내용 (metadata 포함!)
vectordb.upsert(
    collection_id="session_abc123",
    ids=["7f3e9a2b1c4d5e"],        # 자동 생성된 ID
    embeddings=[embedding],         # 3072차원 벡터
    documents=["스택은 LIFO..."],   # 원본 텍스트
    metadatas=[{
        "section_id": 1,            # ✅ 메타데이터도 함께 저장
        "type": "summary",
        "timestamp": 1703001234567, # ✅ 검색 필터에 사용 가능
        "subject": "CS"             # ✅ 과목별 필터 가능
    }]
)
```

**3. 결과 → ChromaDB 상태**
```
📦 Collection: "session_abc123"
└── 7f3e9a2b1c4d5e: 
    ├── 벡터: [3072차원]
    ├── 텍스트: "스택은 LIFO..."
    └── 메타데이터: {section_id: 1, timestamp: 1703001234567, subject: "CS"}
```

---

#### **섹션 3 (120~180초): "스택 응용"**

**1. Spring이 섹션 저장 + 즉시 검색**
```python
# (1) 먼저 저장
POST /rag/upsert-text
{
  "collection_id": "session_abc123",
  "items": [{
    "text": "스택의 실전 응용: 괄호 검사, 후위 표기법 계산...",
    "metadata": {"section_id": 3, "type": "summary"}
  }]
}

# (2) 바로 검색 (이전 관련 내용 찾기)
POST /rag/retrieve
{
  "collection_id": "session_abc123",
  "query": "스택의 실전 응용: 괄호 검사...",
  "top_k": 3
}
```

**2. RAG 모듈이 반환하는 결과**
```json
{
  "chunks": [
    {
      "text": "스택은 LIFO 구조입니다...",  // 섹션 1 (관련도 높음)
      "score": 0.92,
      "metadata": {"section_id": 1}
    },
    {
      "text": "스택의 실전 응용: 괄호 검사...",  // 섹션 3 (자기 자신)
      "score": 0.88,
      "metadata": {"section_id": 3}
    },
    {
      "text": "큐는 FIFO 구조입니다...",  // 섹션 2 (관련도 낮음)
      "score": 0.65,
      "metadata": {"section_id": 2}
    }
  ]
}
```

**3. Spring이 이 결과로 하는 일**
```python
# LLM에게 컨텍스트 제공
context = """
[이전 내용 1] 스택은 LIFO 구조입니다...
[이전 내용 2] 큐는 FIFO 구조입니다...
[현재 내용] 스택의 실전 응용: 괄호 검사...
"""

# GPT에게 질문
"위 강의 내용을 바탕으로 학생이 궁금해할 질문 3개를 만들어줘"
→ Q1: "스택과 큐의 차이는?"
→ Q2: "괄호 검사를 스택으로 어떻게 구현하나요?"
→ Q3: "후위 표기법 계산 알고리즘은?"
```

---

### **Phase 3: 강의노트 + 실시간 섹션 함께 검색** -> 그냥 하나 콜렉션에 요약이랑 PDF랑 다 떼려 박아도 됨. distingusin using metadata:type field.

```python
POST /rag/retrieve
{
  "collections": [
    "session_abc123",      # 실시간 섹션
    "lecture_notes_cs"     # 강의노트
  ],
  "query": "스택의 실전 응용",
  "top_k": 5
}
```

**결과 (두 컬렉션에서 합쳐서 top 5)**
```json
[
  {"text": "스택은 LIFO...", "score": 0.92, "source": "live_section"},
  {"text": "1장. 스택과 큐...", "score": 0.89, "source": "pdf"},
  {"text": "스택의 실전 응용...", "score": 0.88, "source": "live_section"},
  {"text": "10장. 스택 응용...", "score": 0.85, "source": "pdf"},
  {"text": "큐는 FIFO...", "score": 0.65, "source": "live_section"}
]
```

---

## ✨ 핵심 개념 3가지

### 1. **컬렉션 = 저장소**
- `lecture_notes_cs`: 모든 CS 강의노트 (사전 업로드)
- `session_abc123`: 특정 강의 세션의 실시간 섹션들

### 2. **섹션 = 1분 단위 청크**
```
섹션 1 (0~60초): "스택은..."
섹션 2 (60~120초): "큐는..."
섹션 3 (120~180초): "스택 응용..."
```
→ Spring이 1분마다 잘라서 RAG에 저장

### 3. **검색 = 유사도 기반**
```
쿼리: "스택 응용"
  ↓ (벡터 유사도 계산)
결과: 
- 0.92: "스택은 LIFO..." (가장 유사)
- 0.65: "큐는 FIFO..." (덜 유사)
```

---

## 📦 설치

### 사전 요구사항

- **Python 3.11 이상**
- **OpenAI API 키** ([발급 방법](https://platform.openai.com/api-keys))

### 빠른 설치

```bash
# 1. 디렉토리 이동
cd RAG_module

# 2. 가상환경 생성
python -m venv .venv
source .venv/bin/activate

# 3. 패키지 설치
pip install -e .

# 4. API 키 설정
export OPENAI_API_KEY='sk-your-key-here'

# 5. 테스트 (선택)
python all_test.py
```

---

## 🔧 핵심 API 3가지

### 1️⃣ `upsert_text()` - 섹션 요약 저장

**언제 사용?** Spring이 LLM에서 받은 섹션 요약을 저장할 때 (매 1분)

```python
from ragkit import RAGService
from ragkit.models import UpsertItem

service = RAGService()

# 섹션 요약 저장
result = service.upsert_text(
    collection_id="session_abc123",  # 세션 ID
    items=[
        UpsertItem(
            text="스택은 LIFO 구조입니다. push와 pop으로...",
            metadata={
                "section_id": 1,
                "timestamp": 1703001234567,
                "duration": 60,
                "subject": "CS"
            }
        )
    ]
)

print(f"✅ 저장 완료: {result['count']}개")
# ✅ 저장 완료: 1개
```

**반환값:**
```python
{
    "collection_id": "session_abc123",
    "count": 1,               # 저장된 청크 수
    "embedding_dim": 3072     # 벡터 차원 (정보용)
}
```

---

### 2️⃣ `upsert_pdf()` - 강의노트 저장

**언제 사용?** 강의 시작 전 학생이 업로드한 PDF를 저장할 때 (1회)

```python
# PDF 자동 분할 + 저장
result = service.upsert_pdf(
    collection_id="lecture_notes_cs",
    pdf_path="data_structure.pdf",
    base_metadata={
        "subject": "CS",
        "type" : "lecture note",
        "course": "데이터구조"
    }
)

print(f"✅ {result['count']}페이지 저장 완료")
# ✅ 20페이지 저장 완료
```

**내부 동작:**
```python
# 1. PDF → 페이지별 분할
pages = [
    "1장. 스택과 큐...",
    "2장. 트리...",
    ...
]

# 2. 각 페이지 → 벡터 변환 + 저장
for page_num, text in enumerate(pages):
    id = f"data_structure|p{page_num}"  # 결정적 ID
    embedding = openai.embed(text)
    vectordb.save(id, embedding, text)
```

---

### 3️⃣ `retrieve()` - 관련 내용 검색

**언제 사용?** 현재 섹션과 관련된 이전 내용을 찾을 때 (매 섹션마다)

```python
# 유사한 청크 검색
chunks = service.retrieve(
    collection_id="session_abc123",
    query="스택의 실전 응용: 괄호 검사...",
    top_k=3
)

for chunk in chunks:
    print(f"[{chunk.score:.2f}] {chunk.text[:30]}...")
    print(f"   섹션 ID: {chunk.metadata['section_id']}")

# 출력:
# [0.92] 스택은 LIFO 구조입니다...
#    섹션 ID: 1
# [0.88] 스택의 실전 응용: 괄호 검사...
#    섹션 ID: 3
# [0.65] 큐는 FIFO 구조입니다...
#    섹션 ID: 2
```

**필터 사용:**
```python
from ragkit.models import RetrieveFilters

# 특정 조건으로 검색
chunks = service.retrieve(
    collection_id="session_abc123",
    query="스택",
    top_k=5,
    filters=RetrieveFilters(
        subject="CS",                  # 과목 필터
        min_timestamp=1703000000000    # 최근 N분 내용만
    )
)
```

---

## 💼 실전 사용 예제

### 예제 1: 강의 세션 시작

```python
from ragkit import RAGService
from ragkit.models import UpsertItem

service = RAGService()

# 1. 강의노트 업로드 (강의 시작 전 1회)
result = service.upsert_pdf(
    collection_id="lecture_notes_cs",
    pdf_path="data_structure.pdf",
    base_metadata={"subject": "CS"}
)
print(f"강의노트 {result['count']}페이지 저장 완료")

# 2. 섹션 1: 스택 설명 (0~60초)
service.upsert_text(
    collection_id="session_abc123",
    items=[UpsertItem(
        text="스택은 LIFO 구조입니다...",
        metadata={"section_id": 1, "timestamp": 1703001234567}
    )]
)

# 3. 섹션 2: 큐 설명 (60~120초)
service.upsert_text(
    collection_id="session_abc123",
    items=[UpsertItem(
        text="큐는 FIFO 구조입니다...",
        metadata={"section_id": 2, "timestamp": 1703001294567}
    )]
)

# 4. 섹션 3: 스택 응용 (120~180초)
# → 먼저 저장
service.upsert_text(
    collection_id="session_abc123",
    items=[UpsertItem(
        text="스택의 실전 응용: 괄호 검사...",
        metadata={"section_id": 3}
    )]
)

# → 즉시 검색 (이전 관련 내용)
related = service.retrieve(
    collection_id="session_abc123",
    query="스택의 실전 응용...",
    top_k=3
)

# 5. LLM에게 컨텍스트 제공
context = "\n".join([
    f"[관련 내용 {i+1}] {chunk.text}"
    for i, chunk in enumerate(related)
])

print("LLM에게 전달할 컨텍스트:")
print(context)
```

---

### 예제 2: 여러 컬렉션 검색 (강의노트 + 실시간 섹션)

```python
# 방법 1: 각 컬렉션에서 검색 후 합치기
session_chunks = service.retrieve("session_abc123", "스택 응용", top_k=3)
notes_chunks = service.retrieve("lecture_notes_cs", "스택 응용", top_k=2)

all_chunks = session_chunks + notes_chunks
all_chunks.sort(key=lambda c: c.score, reverse=True)

# 방법 2: 컬렉션별로 분리해서 사용
context = f"""
# 실시간 강의 내용
{session_chunks[0].text}

# 강의노트 참고
{notes_chunks[0].text}
"""
```

---

## 📊 메타데이터 활용

### 자유롭게 추가 가능

```python
# 어떤 필드든 추가 가능
UpsertItem(
    text="내용",
    metadata={
        "section_id": 1,
        "timestamp": 1703001234567,
        "duration": 60,
        "subject": "CS",
        "language": "ko",
        "speaker": "교수님",
        "confidence": 0.95,
        "keywords": ["스택", "LIFO"],
        # 원하는 필드 무제한 추가
    }
)
```

### 검색 시 필터링

```python
from ragkit.models import RetrieveFilters

# 커스텀 필터
chunks = service.retrieve(
    "session_abc123",
    "스택",
    filters=RetrieveFilters(
        custom={
            "language": "ko",
            "confidence": 0.9  # confidence >= 0.9인 것만
        }
    )
)
```

---

## 🧪 테스트

```bash
# 전체 테스트 (60개 텍스트 + 20페이지 PDF)
python all_test.py
```

**출력 예시:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 RAGKit 종합 테스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Phase 1: 텍스트 업서트 (60개 청크)
✅ 60개 섹션 저장 완료 (임베딩 차원: 3072)

📄 Phase 2: PDF 업서트 (20페이지)
✅ 20페이지 저장 완료

🔍 Phase 3: 검색 테스트 (7개 쿼리)
  ✅ 쿼리 1: "인공지능의 기초" → 5개 결과
  ✅ 쿼리 2: "메모리 관리" → 5개 결과
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 모든 테스트 통과!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 문제 해결

### ChromaDB 텔레메트리 경고 메시지

**증상:**
```
Failed to send telemetry event ClientStartEvent: 
capture() takes 1 positional argument but 3 were given
```

**원인:**
- ChromaDB 0.5.23 내부 버그
- 텔레메트리 시스템의 함수 서명 불일치
- **기능에는 전혀 영향 없음** (모든 테스트 정상 작동)

**해결:**
`all_test.py`에 이미 적용되어 있습니다:
```python
# ChromaDB 텔레메트리 비활성화
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

# 텔레메트리 경고 메시지 필터링
class StderrFilter:
    def write(self, message):
        if "Failed to send telemetry event" not in message:
            self.original_stderr.write(message)

sys.stderr = StderrFilter(sys.stderr)
```

자체 코드에서도 사용하려면:
```python
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
# ↑ chromadb import 전에 설정
```

---

### ChromaDB 초기화 오류

```bash
# 기존 DB 삭제
rm -rf test_chroma_data/

# 다시 테스트
python all_test.py
```

### OpenAI API 키 오류

```bash
# 환경변수 확인
echo $OPENAI_API_KEY

# 설정 안 되어 있으면
export OPENAI_API_KEY='sk-your-key-here'
```

### 컬렉션 이름 오류

```python
# ❌ 한글/공백 사용 불가
collection_id = "강의_컬렉션"  # 오류 발생
collection_id = "my collection"  # 오류 발생

# ✅ 영문/숫자/하이픈/언더스코어만
collection_id = "lecture_collection"
collection_id = "session-abc-123"
collection_id = "cs_notes_2025"
```

---

## 📁 프로젝트 구조

```
RAG_module/
├── ragkit/                 # 핵심 라이브러리
│   ├── __init__.py
│   ├── config.py          # RAGConfig
│   ├── service.py         # RAGService (핵심 API)
│   ├── models.py          # UpsertItem, RetrievedChunk 등
│   ├── embeddings/
│   │   └── openai.py      # OpenAI 임베딩
│   ├── vectordb/
│   │   └── chroma.py      # ChromaDB 래퍼
│   └── utils/
│       ├── pdf.py         # PDF 처리
│       └── text.py        # 텍스트 유틸
├── tests/                 # 단위 테스트
├── all_test.py            # 종합 테스트 (데모용)
├── requirements.txt
└── README_KR.md
```

---

## 🤝 기여

이슈와 풀 리퀘스트를 환영합니다!

## 📄 라이선스

MIT License
