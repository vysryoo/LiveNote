# QAKit - 실시간 강의 AI 질문 생성 모듈

**LiveNote 프로젝트를 위한 AI 기반 예상 질문/답변 생성 모듈**

> 💡 **이 모듈의 역할**: Spring 백엔드가 강의 섹션 요약을 보내면, RAG 컨텍스트와 이전 QA를 참고하여 학습에 도움되는 질문 3-5개를 병렬로 생성하는 것

## 📋 목차

- [이 모듈이 하는 일](#-이-모듈이-하는-일)
- [LiveNote에서의 실제 사용 흐름](#-livenote에서의-실제-사용-흐름)
- [설치](#-설치)
- [핵심 API](#-핵심-api)
- [실전 사용 예제](#-실전-사용-예제)
- [테스트](#-테스트)
- [문제 해결](#-문제-해결)

---

## 🎯 이 모듈이 하는 일

LiveNote는 **실시간 강의를 전사하고 요약**하는 서비스입니다. 이 QA 모듈은:

### 1. **섹션마다 예상 질문 생성** (매 1분)
```
섹션 요약: "스택은 LIFO 구조입니다..."
  ↓ AI 생성
질문 1: [개념] 스택이란 무엇인가요?
질문 2: [응용] 스택을 어떻게 활용하나요?
질문 3: [비교] 스택과 큐의 차이는?
```

### 2. **5가지 질문 유형 지원**
| 유형 | 설명 | 예시 |
|------|------|------|
| **개념** | 정의/원리 | "스택이란 무엇인가요?" |
| **응용** | 실전 활용 | "스택을 어떻게 활용하나요?" |
| **비교** | 차이점 | "스택과 큐의 차이는?" |
| **심화** | 원리 탐구 | "왜 LIFO 구조를 사용하나요?" |
| **실습** | 문제풀이 | "스택으로 괄호 검사를 구현하세요" |

### 3. **컨텍스트 활용**
```
입력:
- 현재 섹션: "스택의 실전 응용..."
- RAG 검색 결과: ["스택은 LIFO...", "큐는 FIFO..."]
- 이전 QA: [{"type": "개념", "q": "배열이란?", ...}]

출력:
- 중복 없는 새로운 질문 3개
- 현재 섹션에 집중
- 이전 내용은 참고만
```

---

## 🔄 LiveNote에서의 실제 사용 흐름

### **Phase 1: 강의 중 - 섹션마다 반복** (매 1분)

```
실시간 오디오 → STT → LLM 요약 → Spring → RAG 검색
                                    ↓
                              QA 모듈 (질문 생성)
                                    ↓
                              Spring → 프론트엔드
```

#### **섹션 3 (120~180초): "스택 응용"**

**1. Spring이 RAG에서 이전 내용 검색**
```python
POST /rag/retrieve
{
  "collection_id": "session_abc123",
  "query": "스택의 실전 응용...",
  "top_k": 3
}

# 응답
{
  "chunks": [
    {"text": "스택은 LIFO 구조입니다...", "score": 0.92},
    {"text": "큐는 FIFO 구조입니다...", "score": 0.65}
  ]
}
```

**2. Spring이 QA 모듈에 질문 생성 요청**
```python
from qakit.models import QARequest, RAGContext, RAGChunk, PreviousQA
from qakit.service import QAService

# QA 모듈 호출
service = QAService()

request = QARequest(
    session_id="session_abc123",
    section_id=3,
    section_summary="스택의 실전 응용: 괄호 검사, 후위 표기법 계산...",
    subject="CS",
    question_types=["개념", "응용", "심화"],
    qa_count=3,
    rag_context=RAGContext(chunks=[
        RAGChunk(text="스택은 LIFO 구조입니다...", score=0.92),
        RAGChunk(text="큐는 FIFO 구조입니다...", score=0.65)
    ]),
    previous_qa=[
        PreviousQA(
            type="개념",
            question="배열이란 무엇인가요?",
            answer="배열은 같은 타입의 데이터를..."
        )
    ]
)

# 병렬 생성 (평균 1.5초)
qa_list = await service.generate_questions(request)
```

**3. QA 모듈이 생성하는 질문**
```python
[
    {
        "type": "개념",
        "question": "스택에서 괄호 검사는 어떻게 동작하나요?",
        "answer": "여는 괄호를 만나면 push하고, 닫는 괄호를 만나면 pop하여 짝이 맞는지 확인합니다..."
    },
    {
        "type": "응용",
        "question": "후위 표기법 계산을 스택으로 어떻게 구현하나요?",
        "answer": "숫자는 push하고, 연산자를 만나면 2개를 pop하여 계산 후 결과를 다시 push합니다..."
    },
    {
        "type": "심화",
        "question": "왜 괄호 검사에 스택을 사용하나요?",
        "answer": "가장 최근에 연 괄호부터 닫아야 하는 LIFO 특성이 스택과 정확히 일치하기 때문입니다..."
    }
]
```

**4. Spring이 프론트엔드에 전달**
```python
# WebSocket으로 실시간 전송
ws.send({
    "section_id": 3,
    "qa_list": [
        {"type": "개념", "q": "...", "a": "..."},
        {"type": "응용", "q": "...", "a": "..."},
        {"type": "심화", "q": "...", "a": "..."}
    ]
})
```

---

## ✨ 핵심 개념 3가지

### 1. **병렬 생성으로 속도 향상**
```
순차 실행:
개념 → (1.5초) → 응용 → (1.5초) → 심화 → (1.5초)
총 4.5초

병렬 실행:
개념 ┐
응용 ├→ (1.5초)
심화 ┘
총 1.5초
```

### 2. **프롬프트 구조**
```python
━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}  # 질문 생성 대상

━━━ 참고 자료 (이전 강의, 참고만) ━━━
{rag_context}      # 배경지식용

━━━ 기존 질문 (중복 금지) ━━━
{context_qp}       # 중복 방지용
```

### 3. **메타데이터 활용**
```python
QARequest(
    session_id="session_abc123",  # 세션 추적
    section_id=3,                  # 섹션 번호
    subject="CS",                  # 과목 (프롬프트 최적화)
    language="ko",                 # 언어 (한국어/영어)
    ...
)
```

---

## 📦 설치

### 사전 요구사항

- **Python 3.11 이상**
- **OpenAI API 키** ([발급 방법](https://platform.openai.com/api-keys))

### 빠른 설치 (setup.sh 사용)

```bash
# 1. 디렉토리 이동
cd cap2_QA_module

# 2. 자동 환경 설정
./setup.sh

# 출력:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 QAKit 환경 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✅ 가상환경 생성 완료
# ✅ 패키지 설치 완료
# ✅ .env 파일 설정 완료
# 
# 📌 다음 단계:
# 1. .env 파일에 OpenAI API 키 설정 (필요시)
# 2. 테스트 실행: python test_qa.py

# 3. .env 파일 편집 (API 키 입력)
vim .env
# OPENAI_API_KEY=sk-your-key-here

# 4. 테스트
source .venv/bin/activate
python test_qa.py
```

### 수동 설치

```bash
# 1. 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 패키지 설치
pip install -e .

# 3. API 키 설정
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 4. 테스트
python test_qa.py
```

---

## 🔧 핵심 API

### `generate_questions()` - 질문 생성

**언제 사용?** Spring이 섹션 요약을 받고 예상 질문을 생성할 때 (매 1분)

#### **입력 파라미터**

```python
from qakit.models import QARequest, RAGContext, RAGChunk, PreviousQA
from qakit.service import QAService

service = QAService()

request = QARequest(
    # ━━━ 필수 필드 ━━━
    session_id="session_abc123",        # 세션 ID (추적용)
    section_id=3,                       # 섹션 번호 (1, 2, 3, ...)
    section_summary="스택의 실전 응용: 괄호 검사, 후위 표기법...",  
                                        # 현재 섹션 요약 (최소 10자)
    
    # ━━━ 선택 필드 ━━━
    subject="CS",                       # 과목 (CS/수학/물리 등)
    language="ko",                      # 언어 (ko/en)
    question_types=["개념", "응용", "심화"],  
                                        # 질문 유형 (최대 5개)
    qa_count=3,                         # 생성할 질문 개수 (1~5)
    
    # ━━━ 컨텍스트 필드 ━━━
    rag_context=RAGContext(             # RAG 검색 결과 (선택)
        chunks=[
            RAGChunk(
                text="스택은 LIFO 구조입니다...",
                score=0.92,
                metadata={"section_id": 1}
            ),
            RAGChunk(
                text="큐는 FIFO 구조입니다...",
                score=0.65,
                metadata={"section_id": 2}
            )
        ]
    ),
    previous_qa=[                       # 이전 QA (중복 방지용)
        PreviousQA(
            type="개념",
            question="배열이란 무엇인가요?",
            answer="배열은 같은 타입의 데이터를 연속된 메모리에..."
        )
    ]
)

# 병렬 생성 (비동기)
qa_list = await service.generate_questions(request)
```

#### **필드 상세 설명**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `session_id` | `str` | ✅ | 세션 고유 ID (예: `session_abc123`) |
| `section_id` | `int` | ✅ | 섹션 번호 (1, 2, 3, ...) |
| `section_summary` | `str` | ✅ | 섹션 요약 내용 (최소 10자) |
| `subject` | `str` | ❌ | 과목명 (CS, 수학, 물리 등) |
| `language` | `str` | ❌ | 언어 코드 (기본값: `ko`) |
| `question_types` | `List[str]` | ❌ | 질문 유형 리스트. **기본값**: 빈 리스트 + `qa_count=0`이면 `["개념", "응용"]` 2개 생성. 허용 유형: `개념`, `응용`, `비교`, `심화`, `실습` |
| `qa_count` | `int` | ❌ | 생성할 질문 개수 (0~5). **기본값**: 0 (자동 설정). **중요**: `qa_count`와 `question_types` 개수를 일치시켜야 함. 불일치 시 `question_types` 우선 |
| `rag_context` | `RAGContext` | ❌ | RAG 검색 결과 |
| `previous_qa` | `List[PreviousQA]` | ❌ | 이전 QA (중복 방지용) |

#### **출력 형식**

```python
# 반환 타입: List[QAResponse]
[
    QAResponse(
        type="개념",
        question="스택에서 괄호 검사는 어떻게 동작하나요?",
        answer="여는 괄호를 만나면 push하고, 닫는 괄호를 만나면 pop하여 짝이 맞는지 확인합니다. 스택이 비어있거나 짝이 맞지 않으면 검사 실패입니다."
    ),
    QAResponse(
        type="응용",
        question="후위 표기법 계산을 스택으로 어떻게 구현하나요?",
        answer="숫자는 push하고, 연산자를 만나면 2개를 pop하여 계산 후 결과를 다시 push합니다. 최종적으로 스택에 남은 값이 결과입니다."
    ),
    QAResponse(
        type="심화",
        question="왜 괄호 검사에 스택을 사용하나요?",
        answer="가장 최근에 연 괄호부터 닫아야 하는 LIFO 특성이 스택과 정확히 일치하기 때문입니다. 이는 중첩된 구조를 처리하는 데 이상적입니다."
    )
]
```

#### **반환 필드 설명**

| 필드 | 타입 | 설명 |
|------|------|------|
| `type` | `str` | 질문 유형 (`개념`, `응용`, `비교`, `심화`, `실습`) |
| `question` | `str` | 생성된 질문 내용 |
| `answer` | `str` | 생성된 답변 내용 (2-3문장) |

---

## 💼 실전 사용 예제

### 예제 1: 기본 사용 (최소 파라미터)

```python
import asyncio
from qakit.models import QARequest
from qakit.service import QAService

async def generate_qa_basic():
    service = QAService()
    
    # 최소 파라미터만 제공
    request = QARequest(
        session_id="session_123",
        section_id=1,
        section_summary="Python의 리스트는 동적 배열로, append()와 pop()으로 데이터를 관리합니다."
    )
    
    # 질문 생성 (기본값: 개념/응용/비교 3개)
    qa_list = await service.generate_questions(request)
    
    # 결과 출력
    for qa in qa_list:
        print(f"\n[{qa.type}] {qa.question}")
        print(f"답변: {qa.answer}")

# 실행
asyncio.run(generate_qa_basic())
```

**출력:**
```
[개념] Python의 리스트란 무엇인가요?
답변: Python의 리스트는 동적 배열로, 여러 타입의 데이터를 저장할 수 있는 자료구조입니다. append() 메서드로 요소를 추가하고, pop() 메서드로 마지막 요소를 제거할 수 있습니다.

[응용] 리스트를 실제로 어떻게 활용하나요?
답변: 리스트는 데이터 수집, 정렬, 필터링 등 다양한 작업에 활용됩니다. 예를 들어 학생 성적을 저장하고 평균을 계산하거나, 쇼핑 카트에 상품을 추가/제거하는 데 사용할 수 있습니다.

[비교] 리스트와 튜플의 차이는?
답변: 리스트는 가변(mutable) 자료구조로 요소를 추가/삭제할 수 있지만, 튜플은 불변(immutable)으로 생성 후 수정할 수 없습니다. 리스트는 대괄호[], 튜플은 소괄호()를 사용합니다.
```

---

### 예제 2: RAG 컨텍스트 포함

```python
from qakit.models import QARequest, RAGContext, RAGChunk

async def generate_qa_with_rag():
    service = QAService()
    
    request = QARequest(
        session_id="session_abc123",
        section_id=3,
        section_summary="스택의 실전 응용: 괄호 검사, 후위 표기법 계산, 함수 호출 스택",
        subject="CS",
        
        # RAG에서 검색한 이전 내용
        rag_context=RAGContext(chunks=[
            RAGChunk(
                text="스택은 LIFO(Last In First Out) 구조를 가진 자료구조입니다. 데이터를 push로 삽입하고 pop으로 제거합니다.",
                score=0.92,
                metadata={"section_id": 1}
            ),
            RAGChunk(
                text="큐는 FIFO(First In First Out) 구조로, 먼저 들어간 데이터가 먼저 나옵니다.",
                score=0.65,
                metadata={"section_id": 2}
            )
        ])
    )
    
    qa_list = await service.generate_questions(request)
    
    for qa in qa_list:
        print(f"\n✅ [{qa.type}] {qa.question}")
        print(f"   💡 {qa.answer}")

asyncio.run(generate_qa_with_rag())
```

**출력:**
```
✅ [개념] 스택에서 괄호 검사는 어떻게 동작하나요?
   💡 여는 괄호를 만나면 push하고, 닫는 괄호를 만나면 pop하여 짝이 맞는지 확인합니다. 스택이 비어있거나 짝이 맞지 않으면 검사 실패입니다.

✅ [응용] 후위 표기법 계산을 스택으로 어떻게 구현하나요?
   💡 숫자는 push하고, 연산자를 만나면 2개를 pop하여 계산 후 결과를 다시 push합니다. 최종적으로 스택에 남은 값이 결과입니다.

✅ [비교] 스택과 큐의 차이는?
   💡 스택은 LIFO 구조로 마지막에 삽입된 데이터가 먼저 제거되며, 큐는 FIFO 구조로 먼저 삽입된 데이터가 먼저 제거됩니다. 스택은 함수 호출, 큐는 작업 대기열에 주로 사용됩니다.
```

---

### 예제 3: 중복 방지 (이전 QA 포함)

```python
from qakit.models import QARequest, PreviousQA

async def generate_qa_no_duplicate():
    service = QAService()
    
    request = QARequest(
        session_id="session_abc123",
        section_id=5,
        section_summary="힙(Heap)은 완전 이진 트리 기반의 자료구조로, 우선순위 큐 구현에 사용됩니다.",
        
        # 이전에 생성된 질문들 (중복 방지)
        previous_qa=[
            PreviousQA(
                type="개념",
                question="이진 트리란 무엇인가요?",
                answer="이진 트리는 각 노드가 최대 2개의 자식을 가지는 트리 구조입니다."
            ),
            PreviousQA(
                type="비교",
                question="스택과 큐의 차이는?",
                answer="스택은 LIFO, 큐는 FIFO 구조입니다."
            )
        ]
    )
    
    qa_list = await service.generate_questions(request)
    
    print("━━━ 새로 생성된 질문 (중복 없음) ━━━")
    for i, qa in enumerate(qa_list, 1):
        print(f"\n{i}. [{qa.type}] {qa.question}")

asyncio.run(generate_qa_no_duplicate())
```

**출력:**
```
━━━ 새로 생성된 질문 (중복 없음) ━━━

1. [개념] 힙이란 무엇인가요?
2. [응용] 힙을 우선순위 큐로 어떻게 활용하나요?
3. [심화] 왜 힙에 완전 이진 트리를 사용하나요?
```

---

### 예제 4: 맞춤형 질문 유형

```python
async def generate_custom_types():
    service = QAService()
    
    # 수학 과목 - 심화/실습 위주
    request = QARequest(
        session_id="math_session",
        section_id=1,
        section_summary="미분은 함수의 순간 변화율을 나타냅니다. 도함수 f'(x)는 x에서의 접선의 기울기를 의미합니다.",
        subject="수학",
        question_types=["심화", "실습"],  # 원하는 유형만 선택
        qa_count=2
    )
    
    qa_list = await service.generate_questions(request)
    
    for qa in qa_list:
        print(f"\n[{qa.type}] {qa.question}")
        print(f"→ {qa.answer}")

asyncio.run(generate_custom_types())
```

**출력:**
```
[심화] 왜 미분이 순간 변화율을 나타내나요?
→ 미분은 극한을 통해 구간을 무한히 작게 만들어 특정 점에서의 변화율을 계산하기 때문입니다. 이는 평균 변화율의 극한값으로 정의됩니다.

[실습] f(x) = x² + 3x를 x=2에서 미분하세요.
→ f'(x) = 2x + 3이므로 f'(2) = 2(2) + 3 = 7입니다. 따라서 x=2에서의 접선의 기울기는 7입니다.
```

---

### 예제 5: 강의 세션 전체 흐름

```python
async def full_lecture_session():
    service = QAService()
    
    # 섹션 1 (0~60초)
    print("\n━━━ 섹션 1: 스택 개념 ━━━")
    qa_list_1 = await service.generate_questions(QARequest(
        session_id="cs_lecture",
        section_id=1,
        section_summary="스택은 LIFO 구조입니다. push와 pop으로 데이터를 관리합니다.",
        question_types=["개념", "응용"]
    ))
    
    # 섹션 2 (60~120초) - 이전 QA 포함
    print("\n━━━ 섹션 2: 큐 개념 ━━━")
    qa_list_2 = await service.generate_questions(QARequest(
        session_id="cs_lecture",
        section_id=2,
        section_summary="큐는 FIFO 구조입니다. enqueue와 dequeue로 데이터를 관리합니다.",
        question_types=["개념", "비교"],
        previous_qa=[
            PreviousQA(
                type=qa_list_1[0].type,
                question=qa_list_1[0].question,
                answer=qa_list_1[0].answer
            )
        ]
    ))
    
    # 섹션 3 (120~180초) - RAG + 이전 QA 모두 포함
    print("\n━━━ 섹션 3: 스택 응용 ━━━")
    qa_list_3 = await service.generate_questions(QARequest(
        session_id="cs_lecture",
        section_id=3,
        section_summary="스택의 실전 응용: 괄호 검사, 후위 표기법",
        question_types=["응용", "실습"],
        rag_context=RAGContext(chunks=[
            RAGChunk(text="스택은 LIFO 구조입니다...", score=0.92)
        ]),
        previous_qa=[
            PreviousQA(type=qa.type, question=qa.question, answer=qa.answer)
            for qa in (qa_list_1 + qa_list_2)[-2:]  # 최근 2개
        ]
    ))
    
    # 전체 결과
    print("\n━━━ 전체 생성된 QA ━━━")
    all_qa = qa_list_1 + qa_list_2 + qa_list_3
    for i, qa in enumerate(all_qa, 1):
        print(f"{i}. [{qa.type}] {qa.question}")

asyncio.run(full_lecture_session())
```

---

## 🧪 테스트

### 종합 테스트 실행

```bash
# 테스트 실행
python test_qa.py

# 모드 선택
# 1. 전체 테스트 (5개 시나리오)
# 2. 단일 테스트 (빠른 확인)
```

**테스트 시나리오:**
1. **CS (자료구조)**: 스택, 큐
2. **수학 (미적분)**: 미분, 적분  
3. **물리 (뉴턴 법칙)**: 3가지 법칙
4. **화학 (산화-환원)**: 산화, 환원
5. **역사 (임진왜란)**: 이순신, 거북선

**예상 출력:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 QAKit 모듈 테스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ API 키 로드 완료
✅ QAService 초기화 완료

📝 시나리오: CS (자료구조)
   요약: 스택(Stack)은 LIFO(Last In First Out) 구조를 가진...
   질문 유형: ['개념', '응용', '비교']
   ✅ [개념] 스택이란 무엇인가요?
      💡 스택은 LIFO 구조를 가진 자료구조로...
   ✅ [응용] 스택은 어떻게 활용하나요?
      💡 함수 호출 시에 매우 유용하게 활용됩니다...
   ✅ [비교] 스택과 큐의 차이는?
      💡 스택은 LIFO 구조로, 마지막에 삽입된 데이터가...
   ⏱️  완료: 3개 질문, 4257ms

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 총 13개 질문 생성 완료!
⏱️  총 소요 시간: 19432ms (평균: 1494ms/질문)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ⚙️ 설정

### `qakit/config/qa_config.py`

```python
class QAConfig:
    # OpenAI API
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_TIMEOUT: int = 30  # 타임아웃 (초)
    
    # 모델 설정
    QA_MODEL: str = "gpt-4o-mini"        # 모델명
    QA_MAX_TOKENS: int = 300             # 최대 토큰 수
    QA_TEMPERATURE: float = 0.5          # 창의성 (0~1)
    
    # 기본값
    DEFAULT_LANGUAGE: str = "ko"
    DEFAULT_QUESTION_TYPES: list = ["개념", "응용", "비교", "심화", "실습"]
    DEFAULT_QA_COUNT: int = 3
    
    # 검증
    MIN_SUMMARY_LENGTH: int = 10         # 최소 요약 길이
    MAX_QA_COUNT: int = 5                # 최대 질문 개수
```

### `qakit/config/prompts.py`

```python
# 프롬프트 구성 요소:
# - section_summary: 현재 강의 내용 (질문 생성 대상)
# - rag_context: 이전 강의 노트 (참고만, 직접 출제 금지)
# - context_qp: 기존 질문 (중복 방지용)

QA_CONCEPT = """━━━ 현재 강의 (여기서만 질문 생성) ━━━
{section_summary}

{rag_context}

{context_qp}

현재 강의에서 핵심 개념/정의 질문 1개만 생성. 답변 2-3문장.

JSON 출력 (정확히 이 형식만):
{{"type":"개념","q":"질문 내용","a":"답변 내용"}}"""
```

---

## 🔧 문제 해결

### OpenAI API 키 오류

```bash
# .env 파일 확인
cat .env
# OPENAI_API_KEY=sk-...

# 환경변수 직접 설정
export OPENAI_API_KEY='sk-your-key-here'

# Python에서 확인
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

### 타임아웃 조정

```python
# config/qa_config.py
OPENAI_TIMEOUT = 60  # 30초 → 60초
```

### JSON 파싱 오류

```python
# OpenAI가 코드 블록으로 감싸서 반환하는 경우 자동 처리됨
# openai_client.py에서 ```json ... ``` 제거 로직 포함
```

### 질문 품질 개선

```python
# 1. Temperature 조정 (더 창의적: 0.7, 더 일관적: 0.3)
QA_TEMPERATURE = 0.7

# 2. Max Tokens 증가 (더 긴 답변)
QA_MAX_TOKENS = 500

# 3. 프롬프트 커스터마이징
# prompts.py에서 각 유형별 프롬프트 수정
```

---

## 📁 프로젝트 구조

```
cap2_QA_module/
├── qakit/                      # 핵심 라이브러리
│   ├── __init__.py            # 패키지 초기화
│   ├── service.py             # QAService (병렬 생성)
│   ├── models.py              # Pydantic 모델
│   ├── config/
│   │   ├── __init__.py
│   │   ├── qa_config.py       # 모델/타임아웃 설정
│   │   └── prompts.py         # 5가지 프롬프트
│   └── llm/
│       ├── __init__.py
│       └── openai_client.py   # OpenAI API 래퍼
├── test_qa.py                 # 종합 테스트 (5개 시나리오)
├── setup.sh                   # 환경 설정 스크립트
├── setup.py                   # 패키지 설정
├── requirements.txt           # 의존성
├── .env                       # API 키 (gitignore)
├── .gitignore
└── README.md
```

---

## 📊 성능 지표

### 응답 시간

| 질문 개수 | 순차 실행 | 병렬 실행 | 향상 |
|-----------|-----------|-----------|------|
| 1개 | ~1.5초 | ~1.5초 | - |
| 3개 | ~4.5초 | ~1.8초 | **2.5배** |
| 5개 | ~7.5초 | ~2.2초 | **3.4배** |

### 토큰 사용량 (gpt-4o-mini)

| 요소 | 입력 토큰 | 출력 토큰 |
|------|-----------|-----------|
| 섹션 요약 (100자) | ~30 | - |
| RAG 컨텍스트 (3개) | ~150 | - |
| 이전 QA (3개) | ~100 | - |
| 프롬프트 | ~80 | - |
| **질문 1개 생성** | ~360 | ~100 |
| **질문 3개 생성** | ~1,080 | ~300 |

### 비용 추정 (gpt-4o-mini)

- 입력: $0.15 / 1M 토큰
- 출력: $0.60 / 1M 토큰
- **질문 3개 생성**: ~$0.00034 (₩0.45)
- **1시간 강의 (60개 섹션)**: ~$0.02 (₩27)

---

## 🤝 기여

이슈와 풀 리퀘스트를 환영합니다!

## 📄 라이선스

MIT License
