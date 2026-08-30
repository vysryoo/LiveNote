"""
OpenAlexKit 통합 테스트 (파라미터 변형 테스트)
- 입력 파라미터 명확히 표시
- 출력 결과 보기 좋게 포맷팅
- 다양한 파라미터 조합 테스트
  * top_k 변형: 1, 3, 5, 10 (4개)
  * sort_by 변형: relevance, cited_by_count, hybrid (4개)
  * min_score 변형: 1.0, 3.0, 5.0, 7.0 (4개)
  * hybrid+LLM+context: 전체 컨텍스트 활용 (2개)
- 총 14개 시나리오
"""
import asyncio
import logging
import os
import sys
from typing import List
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openalexkit import (
    OpenAlexService,
    OpenAlexRequest,
    PreviousSectionSummary,
    RAGChunk
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 로깅 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    level=logging.WARNING,  # 테스트 출력 깔끔하게
    format='%(message)s'
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트 시나리오 정의 (14개 - 4가지 파라미터 변형)
# - top_k 변형: 4개 시나리오 (top_k=1, 3, 5, 10)
# - sort_by 변형: 4개 시나리오 (relevance, cited_by_count, hybrid x2)
# - min_score 변형: 4개 시나리오 (1.0, 3.0, 5.0, 7.0)
# - hybrid+LLM+context: 2개 시나리오 (전체 컨텍스트 활용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEST_SCENARIOS = [
    # ━━━ Group 1: top_k 변형 (4개) ━━━
    {
        "name": "1️⃣ [top_k=1] CS - 알고리즘 (단일 논문 추천)",
        "request": OpenAlexRequest(
            lecture_id="topk_test_1",
            section_id=1,
            section_summary="퀵소트 알고리즘의 시간 복잡도와 분할 정복 전략",
            language="ko",
            top_k=1,  # 1개만
            verify_openalex=True,
            year_from=2000,
            sort_by="hybrid"
        )
    },
    {
        "name": "2️⃣ [top_k=3] Physics - 양자역학 (3개 추천)",
        "request": OpenAlexRequest(
            lecture_id="topk_test_3",
            section_id=1,
            section_summary="Schrödinger equation and quantum superposition",
            language="en",
            top_k=3,  # 3개
            verify_openalex=True,
            year_from=2005,
            sort_by="hybrid"
        )
    },
    {
        "name": "3️⃣ [top_k=5] ML - Transformer (5개 추천)",
        "request": OpenAlexRequest(
            lecture_id="topk_test_5",
            section_id=1,
            section_summary="Attention mechanism in Transformer architecture",
            language="en",
            top_k=5,  # 5개 (기본값)
            verify_openalex=False,  # Heuristic (빠름)
            year_from=2017,
            sort_by="hybrid"
        )
    },
    {
        "name": "4️⃣ [top_k=10] Math - 선형대수 (10개 추천)",
        "request": OpenAlexRequest(
            lecture_id="topk_test_10",
            section_id=1,
            section_summary="고유값과 고유벡터의 응용: PCA와 그래프 이론",
            language="ko",
            top_k=10,  # 10개 (최대)
            verify_openalex=False,
            year_from=2010,
            sort_by="hybrid"
        )
    },
    
    # ━━━ Group 2: sort_by 변형 (4개) ━━━
    {
        "name": "5️⃣ [relevance] Chemistry - 유기화학 (연관성 우선)",
        "request": OpenAlexRequest(
            lecture_id="sort_relevance",
            section_id=1,
            section_summary="벤젠 고리의 공명 구조와 방향족성",
            language="ko",
            top_k=3,
            verify_openalex=False,
            year_from=2005,
            sort_by="relevance"  # 연관성 우선
        )
    },
    {
        "name": "6️⃣ [cited_by_count] Biology - 세포생물학 (인용수 우선)",
        "request": OpenAlexRequest(
            lecture_id="sort_citation",
            section_id=1,
            section_summary="미토콘드리아의 ATP 생성과 전자전달계",
            language="ko",
            top_k=3,
            verify_openalex=True,
            year_from=2010,
            sort_by="cited_by_count"  # 인용수 우선
        )
    },
    {
        "name": "7️⃣ [hybrid] Economics - 게임이론 (균형 정렬)",
        "request": OpenAlexRequest(
            lecture_id="sort_hybrid_1",
            section_id=1,
            section_summary="Nash equilibrium and prisoner's dilemma",
            language="en",
            top_k=3,
            verify_openalex=False,
            year_from=1990,
            sort_by="hybrid"  # 균형
        )
    },
    {
        "name": "8️⃣ [hybrid] CS - 데이터베이스 (균형 정렬)",
        "request": OpenAlexRequest(
            lecture_id="sort_hybrid_2",
            section_id=1,
            section_summary="B-Tree index structure and range query optimization",
            language="en",
            top_k=3,
            verify_openalex=True,
            year_from=2015,
            sort_by="hybrid"  # 균형
        )
    },
    
    # ━━━ Group 3: min_score 변형 (4개) ━━━
    {
        "name": "9️⃣ [min_score=1.0] Psychology - 인지심리학 (낮은 임계값)",
        "request": OpenAlexRequest(
            lecture_id="minscore_1",
            section_id=1,
            section_summary="작업 기억과 주의 집중의 신경과학적 메커니즘",
            language="ko",
            top_k=5,
            verify_openalex=False,
            year_from=2010,
            sort_by="hybrid",
            min_score=1.0  # 매우 낮은 임계값 (거의 모두 통과)
        )
    },
    {
        "name": "🔟 [min_score=3.0] History - 근대사 (기본 임계값)",
        "request": OpenAlexRequest(
            lecture_id="minscore_3",
            section_id=1,
            section_summary="산업혁명이 유럽 사회에 미친 영향",
            language="ko",
            top_k=5,
            verify_openalex=False,
            year_from=2000,
            sort_by="hybrid",
            min_score=3.0  # 기본값
        )
    },
    {
        "name": "1️⃣1️⃣ [min_score=5.0] Physics - 상대성이론 (중간 임계값)",
        "request": OpenAlexRequest(
            lecture_id="minscore_5",
            section_id=1,
            section_summary="Special relativity: time dilation and length contraction",
            language="en",
            top_k=5,
            verify_openalex=True,
            year_from=2000,
            sort_by="hybrid",
            min_score=5.0  # 중간 임계값 (품질 중시)
        )
    },
    {
        "name": "1️⃣2️⃣ [min_score=7.0] AI - 딥러닝 (높은 임계값)",
        "request": OpenAlexRequest(
            lecture_id="minscore_7",
            section_id=1,
            section_summary="Convolutional neural networks for image recognition",
            language="en",
            top_k=5,
            verify_openalex=True,
            year_from=2012,
            sort_by="hybrid",
            min_score=7.0  # 높은 임계값 (매우 엄격, 일부만 통과)
        )
    },
    
    # ━━━ Group 4: hybrid + LLM + full context (2개) ━━━
    {
        "name": "1️⃣3️⃣ [hybrid+LLM+context] ML - 강화학습 (전체 컨텍스트)",
        "request": OpenAlexRequest(
            lecture_id="hybrid_llm_1",
            section_id=3,
            section_summary="Q-learning과 DQN의 차이: Experience Replay와 Target Network의 역할",
            language="ko",
            top_k=5,
            verify_openalex=True,  # LLM 검증
            previous_summaries=[
                PreviousSectionSummary(
                    section_id=1,
                    summary="강화학습의 기본 개념: 에이전트, 환경, 상태, 행동, 보상"
                ),
                PreviousSectionSummary(
                    section_id=2,
                    summary="Markov Decision Process와 Bellman 방정식"
                )
            ],
            rag_context=[
                RAGChunk(
                    text="3장. Deep Q-Network (DQN)\n- Experience Replay: 학습 데이터의 상관관계 제거\n- Target Network: 학습 안정성 향상",
                    score=0.94
                ),
                RAGChunk(
                    text="Q-learning은 테이블 기반 방법이고, DQN은 신경망을 사용하여 Q-function을 근사합니다.",
                    score=0.88
                )
            ],
            year_from=2013,
            sort_by="hybrid",
            min_score=5.0
        )
    },
    {
        "name": "1️⃣4️⃣ [hybrid+LLM+context] NLP - Transformer (전체 컨텍스트)",
        "request": OpenAlexRequest(
            lecture_id="hybrid_llm_2",
            section_id=4,
            section_summary="BERT와 GPT의 차이점: Bidirectional vs Autoregressive 사전학습",
            language="ko",
            top_k=5,
            verify_openalex=True,  # LLM 검증
            previous_summaries=[
                PreviousSectionSummary(
                    section_id=1,
                    summary="자연어처리의 발전: RNN → LSTM → Attention Mechanism"
                ),
                PreviousSectionSummary(
                    section_id=2,
                    summary="Transformer 아키텍처: Self-Attention과 Positional Encoding"
                ),
                PreviousSectionSummary(
                    section_id=3,
                    summary="전이학습(Transfer Learning)과 사전학습(Pre-training)의 중요성"
                )
            ],
            rag_context=[
                RAGChunk(
                    text="BERT (Bidirectional Encoder Representations from Transformers)\n- Masked Language Model (MLM) 사전학습\n- 양방향 컨텍스트 학습\n- 분류, NER 등 하류 태스크에 효과적",
                    score=0.96
                ),
                RAGChunk(
                    text="GPT (Generative Pre-trained Transformer)\n- Causal Language Model (CLM) 사전학습\n- 단방향(왼쪽→오른쪽) 컨텍스트\n- 텍스트 생성에 특화",
                    score=0.91
                ),
                RAGChunk(
                    text="사전학습 모델은 대규모 코퍼스에서 언어의 패턴을 학습한 후, 작은 데이터셋으로 미세조정(Fine-tuning)합니다.",
                    score=0.85
                )
            ],
            year_from=2017,
            sort_by="hybrid",
            min_score=6.0
        )
    }
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 유틸리티 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_separator(char="━", length=80):
    """구분선 출력"""
    print(char * length)


def print_header(text: str):
    """헤더 출력"""
    print_separator()
    print(f"📌 {text}")
    print_separator()


def print_input_params(request: OpenAlexRequest):
    """입력 파라미터 출력"""
    print("\n🔹 입력 파라미터:")
    print(f"   Lecture ID: {request.lecture_id}")
    print(f"   Section ID: {request.section_id}")
    print(f"   Section Summary: {request.section_summary}")
    
    if request.previous_summaries:
        print(f"   Previous Summaries: {len(request.previous_summaries)}개")
        for ps in request.previous_summaries:
            print(f"      - 섹션 {ps.section_id}: {ps.summary}")
    else:
        print(f"   Previous Summaries: (없음)")
    
    if request.rag_context:
        print(f"   RAG Context: {len(request.rag_context)}개")
        for rc in request.rag_context:
            print(f"      - [{rc.score:.2f}] {rc.text}")
    else:
        print(f"   RAG Context: (없음)")
    
    print(f"   Language: {request.language}")
    print(f"   Top K: {request.top_k}")
    print(f"   Verify OpenAlex: {'LLM' if request.verify_openalex else 'Heuristic'}")
    print(f"   Year From: {request.year_from}")
    print(f"   Sort By: {request.sort_by}")
    print(f"   Min Score: {request.min_score}")
    
    if request.exclude_ids:
        print(f"   Exclude IDs: {request.exclude_ids}")


def print_paper_result(idx: int, paper):
    """논문 결과 출력 (보기 좋게)"""
    print(f"\n   [{idx}] 점수: {paper.score:.1f}/10")
    print(f"       제목: {paper.paper_info.title}")
    
    # 저자 (최대 3명)
    authors = paper.paper_info.authors[:3] if paper.paper_info.authors else []
    authors_str = ", ".join(authors)
    if len(paper.paper_info.authors) > 3:
        authors_str += f" 외 {len(paper.paper_info.authors) - 3}명"
    print(f"       저자: {authors_str if authors_str else 'N/A'}")
    
    print(f"       출판연도: {paper.paper_info.year}")
    print(f"       인용횟수: {paper.paper_info.cited_by_count}")
    print(f"       초록: {paper.paper_info.abstract}")
    print(f"       URL: {paper.paper_info.url}")
    print(f"       평가: {paper.reason}")


async def run_single_test(scenario: dict, service: OpenAlexService) -> dict:
    """단일 테스트 실행"""
    name = scenario["name"]
    request = scenario["request"]
    
    print_header(name)
    print_input_params(request)
    
    print("\n🔹 실행 중...")
    import time
    start = time.time()
    
    try:
        results = await service.recommend_papers(request)
        elapsed = time.time() - start
        
        print(f"\n✅ 완료! (실행시간: {elapsed:.2f}초)")
        print(f"\n🔹 출력 결과: {len(results)}개 논문")
        
        if results:
            for idx, paper in enumerate(results, 1):
                print_paper_result(idx, paper)
        else:
            print("   (검색 결과 없음)")
        
        return {
            "name": name,
            "status": "성공",
            "count": len(results),
            "elapsed": elapsed
        }
    
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n❌ 실패: {e}")
        return {
            "name": name,
            "status": "실패",
            "error": str(e),
            "elapsed": elapsed
        }


async def run_all_tests():
    """전체 테스트 실행"""
    # API 키 확인
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    print_header("OpenAlexKit 통합 테스트 시작")
    print(f"✅ API 키 로드 완료: {api_key[:20]}...")
    print(f"📊 테스트 시나리오: {len(TEST_SCENARIOS)}개\n")
    
    # 서비스 초기화
    service = OpenAlexService()
    
    # 테스트 실행
    results = []
    for idx, scenario in enumerate(TEST_SCENARIOS, 1):
        print(f"\n{'='*80}")
        print(f"테스트 {idx}/{len(TEST_SCENARIOS)}")
        result = await run_single_test(scenario, service)
        results.append(result)
        await asyncio.sleep(0.5)  # API Rate Limit 방지
    
    # 서비스 종료
    await service.close()
    
    # 요약 출력
    print_header("테스트 요약")
    total_time = sum(r["elapsed"] for r in results)
    success_count = sum(1 for r in results if r["status"] == "성공")
    
    print(f"✅ 성공: {success_count}/{len(results)}")
    print(f"⏱️  총 실행시간: {total_time:.2f}초")
    print(f"\n상세 결과:")
    
    for r in results:
        status_icon = "✅" if r["status"] == "성공" else "❌"
        if r["status"] == "성공":
            print(f"  {status_icon} {r['name']}: {r['count']}개 논문, {r['elapsed']:.2f}초")
        else:
            print(f"  {status_icon} {r['name']}: {r['error']}")
    
    print_separator()
    print("🎉 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
