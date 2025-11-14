#!/bin/bash

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RAG Text Upsert 다양한 테스트 케이스
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BASE_URL="http://localhost:8000"
API_ENDPOINT="/rag/text-upsert"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 RAG Text Upsert 테스트 시작"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 1: 기본 텍스트 업서트 (최소 필드)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📝 테스트 1: 기본 텍스트 업서트 (text만 있는 경우)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "items": [
      {
        "text": "데이터베이스는 구조화된 데이터의 집합입니다. 관계형 데이터베이스는 테이블 형태로 데이터를 저장합니다."
      },
      {
        "text": "SQL은 Structured Query Language의 약자로, 데이터베이스를 조작하는 표준 언어입니다."
      }
    ]
  }' | python3 -m json.tool
echo ""
echo "✅ 동작 과정:"
echo "   1. lecture_id='cs101' → collection_id='lecture_cs101' 생성"
echo "   2. 각 item의 text 자동 ID 생성 (해시 기반)"
echo "   3. metadata에 'source':'text' 자동 추가"
echo "   4. OpenAI API로 임베딩 생성 (text-embedding-3-large)"
echo "   5. ChromaDB에 벡터 저장"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 2: ID 명시 + section_id 포함
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📝 테스트 2: ID와 section_id 명시 (수동 ID + 섹션 구분)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "items": [
      {
        "text": "객체지향 프로그래밍(OOP)은 프로그램을 객체들의 모음으로 보는 프로그래밍 패러다임입니다.",
        "id": "cs101_oop_intro",
        "section_id": "1"
      },
      {
        "text": "캡슐화, 상속, 다형성은 OOP의 3대 특징입니다.",
        "id": "cs101_oop_features",
        "section_id": "1"
      },
      {
        "text": "클래스는 객체를 생성하기 위한 템플릿입니다.",
        "id": "cs101_class_def",
        "section_id": "2"
      }
    ]
  }' | python3 -m json.tool
echo ""
echo "✅ 동작 과정:"
echo "   1. 'id' 필드가 있으면 → 해당 ID 사용 (자동 생성 안 함)"
echo "   2. 'section_id' → metadata['section_id']로 저장"
echo "   3. 같은 ID로 다시 upsert하면 → 덮어쓰기 (업데이트)"
echo "   4. section_id별로 query 시 필터링 가능"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 3: 풍부한 메타데이터 (과목, 분류, 난이도 등)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📝 테스트 3: 풍부한 메타데이터 (과목, 분류, 난이도, 키워드)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "items": [
      {
        "text": "알고리즘의 시간 복잡도는 Big-O 표기법으로 나타냅니다. O(n), O(log n), O(n^2) 등이 있습니다.",
        "id": "algo_complexity",
        "section_id": "3",
        "metadata": {
          "subject": "알고리즘",
          "category": "시간복잡도",
          "difficulty": "중급",
          "keywords": ["Big-O", "복잡도", "성능"],
          "professor": "김교수",
          "chapter": 3,
          "is_important": true
        }
      },
      {
        "text": "정렬 알고리즘에는 버블정렬, 퀵정렬, 병합정렬 등이 있습니다.",
        "id": "sorting_intro",
        "section_id": "3",
        "metadata": {
          "subject": "알고리즘",
          "category": "정렬",
          "difficulty": "초급",
          "keywords": ["정렬", "버블정렬", "퀵정렬"],
          "professor": "김교수",
          "chapter": 3
        }
      }
    ]
  }' | python3 -m json.tool
echo ""
echo "✅ 동작 과정:"
echo "   1. metadata 필드에 임의의 JSON 데이터 저장 가능"
echo "   2. 검색 시 metadata 필터링 가능 (예: difficulty='중급')"
echo "   3. ChromaDB에 메타데이터로 저장되어 검색 조건 활용"
echo "   4. 배열(keywords), 불린(is_important), 숫자(chapter) 모두 가능"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 4: 두 번째 lecture (다른 강의)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📝 테스트 4: 다른 강의 (lecture_id='math201')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "math201",
    "items": [
      {
        "text": "미적분학은 변화율과 누적을 다루는 수학의 한 분야입니다.",
        "section_id": "1",
        "metadata": {
          "subject": "수학",
          "category": "미적분",
          "semester": "2025-1",
          "university": "서울대학교"
        }
      },
      {
        "text": "도함수는 함수의 순간 변화율을 나타냅니다. f(x)의 도함수는 lim(h→0) [f(x+h)-f(x)]/h로 정의됩니다.",
        "id": "calc_derivative",
        "section_id": "1",
        "metadata": {
          "subject": "수학",
          "category": "미적분",
          "subcategory": "도함수",
          "formula": true,
          "semester": "2025-1"
        }
      }
    ]
  }' | python3 -m json.tool
echo ""
echo "✅ 동작 과정:"
echo "   1. lecture_id='math201' → collection_id='lecture_math201' 생성"
echo "   2. cs101과 완전히 별개의 컬렉션 (독립적 벡터 DB)"
echo "   3. 강의별로 격리되어 검색 성능 향상"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 5: 혼합 케이스 (ID 있는 것, 없는 것, metadata 있는 것, 없는 것)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📝 테스트 5: 혼합 케이스 (모든 조합)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "items": [
      {
        "text": "스택은 LIFO(Last In First Out) 자료구조입니다."
      },
      {
        "text": "큐는 FIFO(First In First Out) 자료구조입니다.",
        "id": "queue_def"
      },
      {
        "text": "연결 리스트는 노드들이 포인터로 연결된 자료구조입니다.",
        "section_id": "4"
      },
      {
        "text": "이진 트리는 각 노드가 최대 2개의 자식을 가지는 트리입니다.",
        "id": "binary_tree",
        "section_id": "4"
      },
      {
        "text": "해시 테이블은 키-값 쌍을 저장하는 자료구조로, O(1) 평균 시간복잡도를 가집니다.",
        "metadata": {
          "subject": "자료구조",
          "difficulty": "중급"
        }
      },
      {
        "text": "그래프는 정점(Vertex)과 간선(Edge)으로 구성됩니다.",
        "id": "graph_def",
        "section_id": "5",
        "metadata": {
          "subject": "자료구조",
          "category": "그래프",
          "difficulty": "고급",
          "keywords": ["그래프", "정점", "간선"],
          "applications": ["최단경로", "네트워크", "소셜네트워크"]
        }
      }
    ]
  }' | python3 -m json.tool
echo ""
echo "✅ 동작 과정:"
echo "   [Item 1] text만 → ID 자동생성, metadata={'source':'text'}"
echo "   [Item 2] text + id → 지정된 ID 사용, metadata={'source':'text'}"
echo "   [Item 3] text + section_id → ID 자동, metadata={'section_id':'4','source':'text'}"
echo "   [Item 4] text + id + section_id → 지정 ID, metadata={'section_id':'4','source':'text'}"
echo "   [Item 5] text + metadata → ID 자동, 지정된 metadata 사용"
echo "   [Item 6] 모두 있음 → 지정 ID, 모든 필드 활용"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 6: 대량 업서트 (10개 항목)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📝 테스트 6: 대량 업서트 (10개 항목 - 성능 테스트)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "math201",
    "items": [
      {"text": "적분은 함수의 누적값을 계산하는 방법입니다.", "section_id": "2", "metadata": {"chapter": 2}},
      {"text": "정적분은 정해진 구간에서의 적분입니다.", "section_id": "2", "metadata": {"chapter": 2}},
      {"text": "부정적분은 원시함수를 찾는 것입니다.", "section_id": "2", "metadata": {"chapter": 2}},
      {"text": "치환적분법은 복잡한 적분을 간단하게 만듭니다.", "section_id": "3", "metadata": {"chapter": 3}},
      {"text": "부분적분법은 곱의 적분에 사용됩니다.", "section_id": "3", "metadata": {"chapter": 3}},
      {"text": "삼각함수의 적분에는 특수한 공식이 있습니다.", "section_id": "3", "metadata": {"chapter": 3, "type": "공식"}},
      {"text": "이상적분은 무한 구간이나 불연속점을 포함합니다.", "section_id": "4", "metadata": {"chapter": 4, "difficulty": "고급"}},
      {"text": "중적분은 다변수 함수의 적분입니다.", "section_id": "5", "metadata": {"chapter": 5, "difficulty": "고급"}},
      {"text": "푸비니 정리는 중적분의 순서를 바꿀 수 있게 합니다.", "section_id": "5", "metadata": {"chapter": 5, "theorem": true}},
      {"text": "그린 정리는 선적분과 중적분을 연결합니다.", "section_id": "6", "metadata": {"chapter": 6, "theorem": true, "difficulty": "최상급"}}
    ]
  }' | python3 -m json.tool
echo ""
echo "✅ 동작 과정:"
echo "   1. 10개 항목의 text를 한 번에 OpenAI API로 전송"
echo "   2. 배치 임베딩 생성 (효율적)"
echo "   3. ChromaDB에 bulk upsert"
echo "   4. 응답 시간 확인 가능"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 7: 업데이트 테스트 (같은 ID로 다시 upsert)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo "📝 테스트 7: 업데이트 테스트 (같은 ID로 덮어쓰기)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7-1. 초기 데이터 삽입"
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "items": [
      {
        "text": "파이썬은 인터프리터 언어입니다. (구버전)",
        "id": "python_intro_v1",
        "metadata": {"version": 1, "updated_at": "2025-01-01"}
      }
    ]
  }' | python3 -m json.tool
echo ""
echo "7-2. 같은 ID로 업데이트 (내용 변경)"
sleep 1
curl -X POST "${BASE_URL}${API_ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_id": "cs101",
    "items": [
      {
        "text": "파이썬은 동적 타이핑을 지원하는 고수준 인터프리터 언어입니다. (신버전 - 더 상세함)",
        "id": "python_intro_v1",
        "metadata": {"version": 2, "updated_at": "2025-01-14"}
      }
    ]
  }' | python3 -m json.tool
echo ""
echo "✅ 동작 과정:"
echo "   1. 첫 번째 upsert: 'python_intro_v1' ID로 저장"
echo "   2. 두 번째 upsert: 같은 ID → 기존 데이터 덮어쓰기"
echo "   3. 임베딩도 새로 생성되어 갱신됨"
echo "   4. metadata도 완전히 교체됨"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 요약
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 모든 테스트 완료!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 테스트 요약:"
echo "   - 총 7개 테스트 케이스"
echo "   - 2개 강의 (cs101, math201)"
echo "   - 다양한 필드 조합 테스트"
echo ""
echo "🔍 내부 동작 흐름:"
echo "   1. 요청 → FastAPI 엔드포인트 (/rag/text-upsert)"
echo "   2. Pydantic 검증 (TextUpsertRequest)"
echo "   3. collection_id 생성 (lecture_{lecture_id})"
echo "   4. items 전처리 (metadata 병합, section_id 처리)"
echo "   5. RAGService.upsert_text() 호출"
echo "   6. ID 생성 or 사용 (make_id() 함수)"
echo "   7. OpenAI Embedding API 호출 (text-embedding-3-large)"
echo "   8. ChromaDB upsert_many() 호출"
echo "   9. 결과 반환 (collection_id, count, embedding_dim)"
echo ""
echo "📁 저장 위치:"
echo "   - ChromaDB: server_storage/chroma_data/ 또는 chroma_data_real/"
echo "   - 컬렉션: lecture_cs101, lecture_math201"
echo ""
echo "🔗 다음 단계:"
echo "   - /rag/query로 검색 테스트"
echo "   - /qa/generate로 QA 생성 테스트"
echo "   - /rec/recommend로 추천 테스트"
echo ""
