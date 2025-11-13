"""
QAKit 모듈 테스트
"""

import os
import asyncio
import time
from dotenv import load_dotenv

from qakit.config.qa_config import QAConfig
from qakit.models import QARequest, RAGContext, RAGChunk, PreviousQA
from qakit.service import QAService


# .env 파일 로드
load_dotenv()

MODEL_CHOICES = {
    "1": "gpt-4o-mini",
    "2": "gpt-3.5-turbo",
    "3": "gpt-5-nano"
}
DEFAULT_MODEL = QAConfig.QA_MODEL


def select_model() -> str:
    """테스트에서 사용할 모델 선택"""
    print("\n📡 QA 테스트용 모델을 선택하세요:")
    for key, model in MODEL_CHOICES.items():
        suffix = " (기본)" if model == DEFAULT_MODEL else ""
        print(f"{key}. {model}{suffix}")

    selection = input(f"선택 (1/2/3, 기본 {DEFAULT_MODEL}): ").strip()
    chosen = MODEL_CHOICES.get(selection, DEFAULT_MODEL)
    print(f"▶️ 선택된 모델: {chosen}\n")
    return chosen


# 테스트 시나리오
TEST_SCENARIOS = [
    {
        "name": "CS (자료구조)",
        "lecture_id": "test_lecture_cs",
        "section_id": 1,
        "section_summary": """
스택(Stack)은 LIFO(Last In First Out) 구조를 가진 자료구조입니다.
데이터를 push로 삽입하고, pop으로 제거합니다.
함수 호출 스택, 브라우저 뒤로가기 등에 활용됩니다.
""",
        "subject": "CS",
        "question_types": ["개념", "응용", "비교"],
        "rag_context": RAGContext(chunks=[
            RAGChunk(text="배열은 연속된 메모리 공간에 데이터를 저장하는 자료구조입니다.", score=0.92),
            RAGChunk(text="큐(Queue)는 FIFO(First In First Out) 구조입니다.", score=0.88)
        ]),
        "previous_qa": [
            PreviousQA(type="개념", question="배열이란 무엇인가요?", answer="배열은 같은 타입의 데이터를 연속된 메모리에 저장하는 자료구조입니다.")
        ]
    },
    {
        "name": "수학 (미적분)",
        "lecture_id": "test_lecture_math",
        "section_id": 2,
        "section_summary": """
미분은 함수의 순간 변화율을 나타냅니다.
도함수 f'(x)는 x에서의 접선의 기울기를 의미합니다.
적분은 미분의 역연산으로, 곡선 아래 넓이를 구합니다.
""",
        "subject": "수학",
        "question_types": ["개념", "응용"],
        "rag_context": RAGContext(chunks=[
            RAGChunk(text="극한은 함수가 특정 값에 무한히 가까워지는 것을 의미합니다.", score=0.85)
        ])
    },
    {
        "name": "물리 (뉴턴 법칙)",
        "lecture_id": "test_lecture_physics",
        "section_id": 3,
        "section_summary": """
뉴턴의 제1법칙은 관성의 법칙입니다. 물체는 외력이 없으면 정지 또는 등속 운동을 유지합니다.
제2법칙은 F=ma로 표현되며, 힘은 질량과 가속도의 곱입니다.
제3법칙은 작용-반작용 법칙으로, 모든 힘에는 크기가 같고 방향이 반대인 반작용이 존재합니다.
""",
        "subject": "물리",
        "question_types": ["개념", "심화", "실습"],
        "rag_context": RAGContext(chunks=[
            RAGChunk(text="속도는 위치의 시간에 대한 변화율입니다.", score=0.90),
            RAGChunk(text="가속도는 속도의 시간에 대한 변화율입니다.", score=0.87)
        ])
    },
    {
        "name": "화학 (산화-환원)",
        "lecture_id": "test_lecture_chemistry",
        "section_id": 4,
        "section_summary": """
산화는 전자를 잃는 반응이고, 환원은 전자를 얻는 반응입니다.
산화-환원 반응에서 전자 이동이 일어나며, 산화수 변화로 확인할 수 있습니다.
산화제는 다른 물질을 산화시키면서 자신은 환원됩니다.
""",
        "subject": "화학",
        "question_types": ["개념", "비교", "실습"]
    },
    {
        "name": "역사 (임진왜란)",
        "lecture_id": "test_lecture_history",
        "section_id": 5,
        "section_summary": """
임진왜란은 1592년 일본의 조선 침략으로 시작된 7년 전쟁입니다.
이순신 장군의 거북선과 한산도 대첩이 중요한 승리였습니다.
명나라 지원군과 조선 의병의 활약으로 일본군을 격퇴했습니다.
""",
        "subject": "역사",
        "question_types": ["개념", "심화"],
        "rag_context": RAGContext(chunks=[
            RAGChunk(text="조선은 성리학을 국가 이념으로 삼았습니다.", score=0.75)
        ])
    }
]


async def test_qa_generation(model: str | None = None):
    """QA 생성 테스트"""
    print("\n" + "="*60)
    print("🚀 QAKit 모듈 테스트")
    print("="*60)
    
    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        print("   .env 파일에 OPENAI_API_KEY를 추가해주세요.")
        return
    
    print(f"✅ API 키 로드 완료: {api_key[:20]}...")
    
    # QAService 초기화
    qa_service = QAService(api_key=api_key, model=model)
    print("✅ QAService 초기화 완료\n")
    
    total_questions = 0
    total_time = 0
    
    # 각 시나리오 테스트
    for scenario in TEST_SCENARIOS:
        print(f"\n📝 시나리오: {scenario['name']}")
        print(f"   요약: {scenario['section_summary'][:50]}...")
        print(f"   질문 유형: {scenario['question_types']}")
        
        # QARequest 생성
        request = QARequest(
            lecture_id=scenario["lecture_id"],
            section_id=scenario["section_id"],
            section_summary=scenario["section_summary"],
            subject=scenario.get("subject"),
            question_types=scenario["question_types"],
            qa_count=len(scenario["question_types"]),
            rag_context=scenario.get("rag_context"),
            previous_qa=scenario.get("previous_qa", [])
        )
        
        # QA 생성
        start_time = time.time()
        try:
            qa_list = await qa_service.generate_questions(request)
            elapsed = int((time.time() - start_time) * 1000)
            
            # 결과 출력
            for qa in qa_list:
                print(f"   ✅ [{qa.type}] {qa.question}")
                print(f"      💡 {qa.answer[:60]}...")
            
            print(f"   ⏱️  완료: {len(qa_list)}개 질문, {elapsed}ms\n")
            
            total_questions += len(qa_list)
            total_time += elapsed
            
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}\n")
    
    # 전체 요약
    print("="*60)
    print(f"✨ 총 {total_questions}개 질문 생성 완료!")
    print(f"⏱️  총 소요 시간: {total_time}ms (평균: {total_time//total_questions if total_questions else 0}ms/질문)")
    print("="*60 + "\n")


async def test_single_qa(model: str | None = None):
    """단일 QA 생성 테스트 (빠른 확인용)"""
    print("\n" + "="*60)
    print("� 단일 QA 생성 테스트")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다!")
        return
    
    qa_service = QAService(api_key=api_key, model=model)
    
    request = QARequest(
        lecture_id="quick_test",
        section_id=1,
        section_summary="Python의 리스트(list)는 동적 배열로, 여러 타입의 데이터를 저장할 수 있습니다. append()로 추가하고 pop()으로 제거합니다.",
        question_types=["개념"],
        qa_count=1,
        rag_context=RAGContext(chunks=[
            RAGChunk(text="튜플(tuple)은 불변 자료구조입니다.", score=0.85)
        ])
    )
    
    start_time = time.time()
    qa_list = await qa_service.generate_questions(request)
    elapsed = int((time.time() - start_time) * 1000)
    
    if qa_list:
        qa = qa_list[0]
        print(f"\n✅ [{qa.type}] {qa.question}")
        print(f"💡 {qa.answer}")
        print(f"⏱️  소요 시간: {elapsed}ms\n")
    else:
        print("❌ QA 생성 실패\n")


def test_validation():
    """QARequest 검증 로직 테스트"""
    print("\n" + "="*60)
    print("🧪 QARequest 검증 로직 테스트")
    print("="*60 + "\n")

    # 테스트 1: 기본값 (둘 다 비어있음)
    print("1️⃣ 기본값 테스트 (question_types=[], qa_count=0)")
    try:
        req = QARequest(
            lecture_id="test1",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=[],
            qa_count=0
        )
        print(f"   ✅ question_types: {req.question_types}")
        print(f"   ✅ qa_count: {req.qa_count}")
        print(f"   → 기대값: ['개념', '응용'], 2\n")
    except Exception as e:
        print(f"   ❌ 에러: {e}\n")

    # 테스트 2: question_types 하나만
    print("2️⃣ question_types=['응용'] 하나, qa_count=3")
    try:
        req = QARequest(
            lecture_id="test2",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=["응용"],
            qa_count=3
        )
        print(f"   ✅ question_types: {req.question_types}")
        print(f"   ✅ qa_count: {req.qa_count}")
        print(f"   → 기대값: ['응용'], 1 (question_types 우선)\n")
    except Exception as e:
        print(f"   ❌ 에러: {e}\n")

    # 테스트 3: 잘못된 유형
    print("3️⃣ 잘못된 유형 테스트 (['개념', '잘못된유형'])")
    try:
        req = QARequest(
            lecture_id="test3",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=["개념", "잘못된유형"],
            qa_count=2
        )
        print(f"   ❌ 검증 실패! 통과되면 안됨")
        print(f"   question_types: {req.question_types}\n")
    except ValueError as e:
        print(f"   ✅ 정상 차단: {str(e)[:80]}...\n")

    # 테스트 4: 6개 이상 (MAX_QA_COUNT 초과)
    print("4️⃣ qa_count=6 (MAX_QA_COUNT 초과)")
    try:
        req = QARequest(
            lecture_id="test4",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=["개념", "응용", "비교", "심화", "실습", "추가"],
            qa_count=6
        )
        print(f"   ❌ 검증 실패! 통과되면 안됨")
        print(f"   qa_count: {req.qa_count}\n")
    except ValueError as e:
        print(f"   ✅ 정상 차단: {str(e)[:80]}...\n")

    # 테스트 5: question_types 6개 (잘못된 유형 포함)
    print("5️⃣ question_types 6개 with '추가' (잘못된 유형)")
    try:
        req = QARequest(
            lecture_id="test5",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=["개념", "응용", "비교", "심화", "실습", "추가"],
            qa_count=0
        )
        print(f"   ❌ 검증 실패! 통과되면 안됨")
        print(f"   question_types: {req.question_types}\n")
    except ValueError as e:
        print(f"   ✅ 정상 차단: {str(e)[:80]}...\n")

    # 테스트 6: 불일치 (question_types 우선)
    print("6️⃣ 불일치 테스트 (types=2개, count=5) - question_types 우선")
    try:
        req = QARequest(
            lecture_id="test6",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=["개념", "응용"],
            qa_count=5
        )
        print(f"   ✅ question_types: {req.question_types}")
        print(f"   ✅ qa_count: {req.qa_count}")
        print(f"   → 기대값: ['개념', '응용'], 2 (question_types 우선)\n")
    except Exception as e:
        print(f"   ❌ 에러: {e}\n")

    # 테스트 7: 불일치 (question_types < qa_count)
    print("7️⃣ 불일치 테스트 (types=5개, count=2) - question_types 우선")
    try:
        req = QARequest(
            lecture_id="test7",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=["개념", "응용", "비교", "심화", "실습"],
            qa_count=2
        )
        print(f"   ✅ question_types: {req.question_types}")
        print(f"   ✅ qa_count: {req.qa_count}")
        print(f"   → 기대값: ['개념', '응용', '비교', '심화', '실습'], 5 (question_types 우선)\n")
    except Exception as e:
        print(f"   ❌ 에러: {e}\n")

    # 테스트 8: question_types만 지정 (qa_count=0)
    print("8️⃣ question_types=['심화', '실습'], qa_count=0")
    try:
        req = QARequest(
            lecture_id="test8",
            section_id=1,
            section_summary="테스트 내용입니다.",
            question_types=["심화", "실습"],
            qa_count=0
        )
        print(f"   ✅ question_types: {req.question_types}")
        print(f"   ✅ qa_count: {req.qa_count}")
        print(f"   → 기대값: ['심화', '실습'], 2\n")
    except Exception as e:
        print(f"   ❌ 에러: {e}\n")

    print("="*60)
    print("✨ 테스트 완료!")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n📌 실행 모드 선택:")
    print("1. 전체 테스트 (5개 시나리오)")
    print("2. 단일 테스트 (빠른 확인)")
    print("3. 검증 테스트 (QARequest 유효성 검사)")
    
    choice = input("\n선택 (1/2/3, 기본값 1): ").strip() or "1"
    selected_model = None
    
    if choice in {"1", "2"}:
        selected_model = select_model()
    
    if choice == "2":
        asyncio.run(test_single_qa(model=selected_model))
    elif choice == "3":
        test_validation()
    else:
        asyncio.run(test_qa_generation(model=selected_model))
