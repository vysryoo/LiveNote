"""
WikiKit 종합 테스트 (12개 시나리오)
"""
import asyncio
import logging
import time
from wikikit import WikiService, WikiRequest, PreviousSummary, RAGChunk

# 로깅 설정 (WARNING 레벨로 디테일 숨김)
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12가지 테스트 시나리오
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEST_SCENARIOS = [
    # ━━━ 기본 시나리오 (top_k 변형) ━━━
    {
        "name": "1. CS (Stack) - top_k=1, LLM 검증",
        "request": WikiRequest(
            lecture_id="lecture_cs_001",
            section_id=1,
            lecture_summary="Stack is a LIFO (Last In First Out) data structure used in computer science.",
            language="en",
            top_k=1,
            verify_wiki=True,
            wiki_lang="en",
            fallback_to_ko=False
        )
    },
    {
        "name": "2. Math (Calculus) - top_k=3, Heuristic",
        "request": WikiRequest(
            lecture_id="lecture_math_001",
            section_id=1,
            lecture_summary="Differentiation is the process of finding the rate of change of a function.",
            language="en",
            top_k=3,
            verify_wiki=False,  # Heuristic
            wiki_lang="en"
        )
    },
    {
        "name": "3. Physics (Quantum) - top_k=5, English",
        "request": WikiRequest(
            lecture_id="lecture_physics_001",
            section_id=1,
            lecture_summary="Schrödinger equation describes quantum state evolution in quantum mechanics.",
            language="en",
            top_k=5,
            verify_wiki=True,
            wiki_lang="en"
        )
    },
    {
        "name": "4. Chemistry (Organic) - top_k=10, EN+KO fallback",
        "request": WikiRequest(
            lecture_id="lecture_chemistry_001",
            section_id=1,
            lecture_summary="SN2 reaction is a nucleophilic substitution mechanism in organic chemistry.",
            language="en",
            top_k=10,
            verify_wiki=True,
            wiki_lang="en",
            fallback_to_ko=True  # 영어 부족 시 한국어 보충
        )
    },
    
    # ━━━ min_score 변형 ━━━
    {
        "name": "5. Biology (Cell) - min_score=1.0",
        "request": WikiRequest(
            lecture_id="lecture_biology_001",
            section_id=1,
            lecture_summary="Mitochondria are the powerhouse of the cell, generating ATP through cellular respiration.",
            language="en",
            top_k=5,
            verify_wiki=True,
            min_score=1.0  # 모든 결과 포함
        )
    },
    {
        "name": "6. History (Korean War) - min_score=5.0",
        "request": WikiRequest(
            lecture_id="lecture_history_001",
            section_id=1,
            lecture_summary="The Korean War was a conflict between North and South Korea from 1950 to 1953.",
            language="en",
            top_k=5,
            verify_wiki=True,
            min_score=5.0  # 중간 점수 이상
        )
    },
    {
        "name": "7. Literature (Shakespeare) - min_score=7.0",
        "request": WikiRequest(
            lecture_id="lecture_literature_001",
            section_id=1,
            lecture_summary="Hamlet is a tragedy written by William Shakespeare, exploring themes of revenge and madness.",
            language="en",
            top_k=5,
            verify_wiki=True,
            min_score=7.0  # 고품질만
        )
    },
    
    # ━━━ 언어 변형 ━━━
    {
        "name": "8. Economics (Korean) - min_score=5.0",
        "request": WikiRequest(
            lecture_id="lecture_economics_001",
            section_id=1,
            lecture_summary="시장경제는 수요와 공급의 원리로 작동하는 경제 체제입니다.",
            language="ko",
            top_k=5,
            verify_wiki=True,
            wiki_lang="ko",
            fallback_to_ko=False,  # 한국어만
            min_score=5.0
        )
    },
    {
        "name": "9. Philosophy (Kant) - Heuristic",
        "request": WikiRequest(
            lecture_id="lecture_philosophy_001",
            section_id=1,
            lecture_summary="Kant's categorical imperative emphasizes the universality of moral laws.",
            language="en",
            top_k=5,
            verify_wiki=False,  # Heuristic
            wiki_lang="en"
        )
    },
    {
        "name": "10. Art (Renaissance) - LLM 검증",
        "request": WikiRequest(
            lecture_id="lecture_art_001",
            section_id=1,
            lecture_summary="Renaissance art reflects humanistic thinking and classical revival in Europe.",
            language="en",
            top_k=5,
            verify_wiki=True,
            wiki_lang="en"
        )
    },
    
    # ━━━ 컨텍스트 활용 ━━━
    {
        "name": "11. AI (DQN) - 이전 섹션 + RAG 포함",
        "request": WikiRequest(
            lecture_id="lecture_ai_001",
            section_id=3,
            lecture_summary="DQN uses Experience Replay and Target Network to stabilize Q-learning in reinforcement learning.",
            language="en",
            top_k=5,
            verify_wiki=True,
            previous_summaries=[
                PreviousSummary(
                    section_id=1, 
                    summary="Reinforcement learning is a machine learning paradigm where agents learn through interaction."
                ),
                PreviousSummary(
                    section_id=2, 
                    summary="Q-learning is a value-based algorithm that learns optimal action-value functions."
                )
            ],
            rag_context=[
                RAGChunk(
                    text="Chapter 1. Reinforcement Learning - Markov Decision Process...",
                    score=0.88
                )
            ]
        )
    },
    {
        "name": "12. Medicine (Heart) - 중복 제거 테스트",
        "request": WikiRequest(
            lecture_id="lecture_medicine_001",
            section_id=2,
            lecture_summary="The heart is a muscular organ that pumps blood through the circulatory system.",
            language="en",
            top_k=5,
            verify_wiki=True,
            exclude_titles=["Circulatory system"]  # 이미 추천된 문서
        )
    }
]


async def run_single_test(service: WikiService, scenario: dict):
    """단일 시나리오 실행"""
    request = scenario["request"]
    
    start = time.time()
    
    try:
        # 추천 실행
        results = await service.recommend_pages(request)
        
        elapsed = (time.time() - start) * 1000  # ms
        
        # 상세한 결과 출력
        print(f"\n📝 {scenario['name']}")
        print(f"   📥 입력 (WikiRequest):")
        print(f"      - lecture_id: {request.lecture_id}")
        print(f"      - section_id: {request.section_id}")
        print(f"      - lecture_summary: \"{request.lecture_summary[:50]}...\"")
        print(f"      - top_k: {request.top_k} | verify_wiki: {request.verify_wiki}")
        print(f"      - wiki_lang: {request.wiki_lang} | fallback_to_ko: {request.fallback_to_ko}")
        print(f"      - min_score: {request.min_score}")
        
        if not results:
            print("   ⚠️  결과 없음")
        else:
            print(f"\n   📤 출력 (List[WikiResponse]): {len(results)}개 문서 ({elapsed:.0f}ms)")
            
            for i, res in enumerate(results, 1):
                print(f"\n      [{i}] WikiResponse:")
                print(f"         ├─ lecture_id: {res.lecture_id}")
                print(f"         ├─ section_id: {res.section_id}")
                print(f"         ├─ score: {res.score:.1f}")
                print(f"         ├─ reason: \"{res.reason}\"")
                print(f"         └─ page_info (WikiPageInfo):")
                print(f"            ├─ title: \"{res.page_info.title}\"")
                print(f"            ├─ lang: {res.page_info.lang}")
                print(f"            ├─ page_id: {res.page_info.page_id}")
                print(f"            ├─ url: {res.page_info.url}")
                print(f"            └─ extract: \"{res.page_info.extract}\"")
        
        return len(results), elapsed
        
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        logger.error(f"시나리오 실패: {scenario['name']}", exc_info=True)
        return 0, 0


async def main():
    """전체 테스트 실행"""
    print("\n" + "━" * 80)
    print("🚀 WikiKit 종합 테스트 (12개 시나리오)")
    print("━" * 80)
    
    try:
        # WikiService 초기화
        service = WikiService()
        
        total_docs = 0
        total_time = 0
        
        # 각 시나리오 실행
        for scenario in TEST_SCENARIOS:
            docs, elapsed = await run_single_test(service, scenario)
            total_docs += docs
            total_time += elapsed
        
        # 전체 통계
        print("\n" + "━" * 80)
        print(f"✨ 총 {total_docs}개 문서 추천 완료! ({len(TEST_SCENARIOS)}개 시나리오)")
        print(f"⏱️  총 소요 시간: {total_time:.0f}ms (평균: {total_time/len(TEST_SCENARIOS):.0f}ms)")
        print("━" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        logger.error("전체 테스트 실패", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
