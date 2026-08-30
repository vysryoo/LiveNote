"""YouTubeKit 종합 테스트 - 실제 YouTube API 사용 (순차 실행)"""
import asyncio
import logging
import time
from youtubekit import YouTubeService, YouTubeRequest

logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEST_SCENARIOS = [
    {
        "name": "1️⃣ [top_k=1] CS - Stack Algorithm (단일 영상 추천)",
        "request": YouTubeRequest(
            lecture_id="yt_test_1",
            section_id=1,
            lecture_summary="Stack data structure: LIFO operations, push and pop methods, and practical applications",
            language="en",
            top_k=1,
            verify_yt=True,
            yt_lang="en",
            min_score=5.0
        )
    },
    {
        "name": "2️⃣ [top_k=3] ML - Transformer (3개 영상 추천)",
        "request": YouTubeRequest(
            lecture_id="yt_test_2",
            section_id=1,
            lecture_summary="Transformer architecture with self-attention mechanism for NLP tasks",
            language="en",
            top_k=3,
            verify_yt=True,
            yt_lang="en",
            min_score=5.0
        )
    },
    {
        "name": "3️⃣ [top_k=5] 한국사 - 조선시대 (5개 영상 추천)",
        "request": YouTubeRequest(
            lecture_id="yt_test_3",
            section_id=1,
            lecture_summary="조선시대의 정치 체제와 성리학의 발전, 과거제도와 양반 사회 구조",
            language="ko",
            top_k=5,
            verify_yt=False,
            yt_lang="ko",
            min_score=3.0
        )
    },
    {
        "name": "4️⃣ [LLM 검증] Python - Decorators",
        "request": YouTubeRequest(
            lecture_id="yt_test_4",
            section_id=1,
            lecture_summary="Python decorators: function wrappers, @property, @staticmethod, and practical examples",
            language="en",
            top_k=3,
            verify_yt=True,
            yt_lang="en",
            min_score=5.0
        )
    },
    {
        "name": "5️⃣ [Heuristic] JavaScript - Async/Await",
        "request": YouTubeRequest(
            lecture_id="yt_test_5",
            section_id=1,
            lecture_summary="JavaScript async/await syntax for handling asynchronous operations and promises",
            language="en",
            top_k=3,
            verify_yt=False,
            yt_lang="en",
            min_score=5.0
        )
    },
    {
        "name": "6️⃣ [English] Quantum Mechanics",
        "request": YouTubeRequest(
            lecture_id="yt_test_6",
            section_id=1,
            lecture_summary="Quantum superposition and wave-particle duality in quantum mechanics",
            language="en",
            top_k=3,
            verify_yt=True,
            yt_lang="en",
            min_score=5.0
        )
    },
    {
        "name": "7️⃣ [Korean] 데이터베이스 - SQL",
        "request": YouTubeRequest(
            lecture_id="yt_test_7",
            section_id=1,
            lecture_summary="SQL 기본 쿼리: SELECT, JOIN, WHERE 절과 인덱스 최적화",
            language="ko",
            top_k=3,
            verify_yt=True,
            yt_lang="ko",
            min_score=5.0
        )
    },
    {
        "name": "8️⃣ [min_score=3.0] React - Hooks",
        "request": YouTubeRequest(
            lecture_id="yt_test_8",
            section_id=1,
            lecture_summary="React Hooks: useState, useEffect, and custom hooks for state management",
            language="en",
            top_k=5,
            verify_yt=False,
            yt_lang="en",
            min_score=3.0
        )
    },
    {
        "name": "9️⃣ [min_score=7.0] Docker - Kubernetes",
        "request": YouTubeRequest(
            lecture_id="yt_test_9",
            section_id=1,
            lecture_summary="Docker containerization and Kubernetes orchestration for microservices deployment",
            language="en",
            top_k=5,
            verify_yt=True,
            yt_lang="en",
            min_score=7.0
        )
    },
    {
        "name": "🔟 [exclude_titles] Git - Version Control",
        "request": YouTubeRequest(
            lecture_id="yt_test_10",
            section_id=1,
            lecture_summary="Git version control: branching, merging, and collaborative workflows",
            language="en",
            top_k=5,
            verify_yt=False,
            yt_lang="en",
            min_score=5.0,
            exclude_titles=["Git Tutorial for Beginners"]
        )
    },
    {
        "name": "1️⃣1️⃣ [Full Fields] FastAPI - REST API Development",
        "request": YouTubeRequest(
            lecture_id="yt_test_11",
            section_id=2,
            lecture_summary="FastAPI framework for building REST APIs with automatic documentation and type validation",
            language="en",
            top_k=3,
            verify_yt=True,
            yt_lang="en",
            min_score=6.0,
            previous_summaries=[],  # 이전 섹션 요약 없음
            rag_context=[],  # RAG 컨텍스트 없음
            exclude_titles=["FastAPI Crash Course"]
        )
    },
    {
        "name": "1️⃣2️⃣ [Full Fields + Context] TensorFlow - Neural Networks",
        "request": YouTubeRequest(
            lecture_id="yt_test_12",
            section_id=3,
            lecture_summary="TensorFlow deep learning framework for building and training neural networks with GPU acceleration",
            language="en",
            top_k=4,
            verify_yt=True,
            yt_lang="en",
            min_score=6.5,
            previous_summaries=[
                {"section_id": 1, "summary": "Introduction to machine learning fundamentals and supervised learning"},
                {"section_id": 2, "summary": "Neural network basics: perceptron, activation functions, backpropagation"}
            ],
            rag_context=[
                {"text": "TensorFlow is an open-source platform for machine learning", "score": 0.92, "source": "lecture_notes.pdf"},
                {"text": "GPU acceleration speeds up neural network training significantly", "score": 0.88, "source": "textbook_ch5.pdf"}
            ],
            exclude_titles=["TensorFlow Tutorial", "Deep Learning Basics"]
        )
    },
    {
        "name": "1️⃣3️⃣ [Full Fields Korean] 블록체인 - 스마트 컨트랙트",
        "request": YouTubeRequest(
            lecture_id="yt_test_13",
            section_id=4,
            lecture_summary="스마트 컨트랙트 개발: Solidity 언어, 이더리움 플랫폼, 탈중앙화 애플리케이션 구축",
            language="ko",
            top_k=5,
            verify_yt=True,
            yt_lang="ko",
            min_score=5.5,
            previous_summaries=[
                {"section_id": 1, "summary": "블록체인 기초: 분산 원장, 합의 알고리즘, 암호화 해시"},
                {"section_id": 2, "summary": "이더리움 플랫폼 구조와 가스 개념"},
                {"section_id": 3, "summary": "Solidity 언어 기본 문법과 데이터 타입"}
            ],
            rag_context=[
                {"text": "스마트 컨트랙트는 자동으로 실행되는 디지털 계약", "score": 0.95, "source": "blockchain_course.pdf"},
                {"text": "Solidity는 이더리움 스마트 컨트랙트 작성 언어", "score": 0.90, "source": "ethereum_docs.pdf"}
            ],
            exclude_titles=["블록체인 입문", "비트코인 기초"]
        )
    },
]

def print_separator(char="━", length=80):
    print(char * length)

def print_request_info(name: str, req: YouTubeRequest):
    print(f"\n{'='*80}")
    print(f"📺 {name}")
    print(f"{'='*80}")
    print(f"📋 요청 정보:")
    print(f"   • lecture_id: {req.lecture_id}")
    print(f"   • section_id: {req.section_id}")
    print(f"   • lecture_summary: {req.lecture_summary}")
    print(f"   • language: {req.language}")
    print(f"   • top_k: {req.top_k}")
    print(f"   • verify_yt: {req.verify_yt} {'(LLM 검증)' if req.verify_yt else '(Heuristic)'}")
    print(f"   • yt_lang: {req.yt_lang}")
    print(f"   • min_score: {req.min_score}")
    if req.exclude_titles:
        print(f"   • exclude_titles: {req.exclude_titles}")
    print_separator()

def print_video_results(results, processing_time: float):
    if not results:
        print("❌ 결과 없음 (min_score 임계값 미달 또는 검색 실패)\n")
        return
    
    print(f"\n✅ 총 {len(results)}개 영상 추천 (처리 시간: {processing_time:.2f}초)\n")
    
    for idx, resp in enumerate(results, 1):
        vi = resp.video_info
        print(f"  [{idx}] 🎬 {vi.title}")
        print(f"      📊 점수: {resp.score:.1f}/10.0")
        print(f"      🔗 URL: {vi.url}")
        print(f"      🌐 언어: {vi.lang}")
        print(f"      💡 추천 이유: {resp.reason}")
        print(f"      📝 요약:")
        
        extract_lines = vi.extract.split('. ')
        for line in extract_lines:
            if line.strip():
                print(f"         • {line.strip()}")
        print()

async def run_test_scenario(scenario_idx: int, scenario: dict):
    """개별 테스트 시나리오 실행 (병렬 실행 가능)"""
    name = scenario["name"]
    req = scenario["request"]
    
    try:
        print_request_info(name, req)
        
        service = YouTubeService()
        start_time = time.time()
        results = await service.recommend_videos(req)
        processing_time = time.time() - start_time
        
        print_video_results(results, processing_time)
        
        return {
            "scenario_idx": scenario_idx,
            "name": name,
            "success": True,
            "processing_time": processing_time,
            "result_count": len(results)
        }
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}\n")
        logger.error(f"Error in scenario {scenario_idx}: {e}", exc_info=True)
        return {
            "scenario_idx": scenario_idx,
            "name": name,
            "success": False,
            "error": str(e)
        }

async def run_all_tests_sequential():
    """모든 테스트를 순차적으로 실행 (기존 방식)"""
    print("\n" + "="*80)
    print("🎥 YouTubeKit 종합 테스트 시작 (순차 실행 모드)")
    print("="*80)
    print(f"총 {len(TEST_SCENARIOS)}개 시나리오 테스트")
    print("="*80 + "\n")
    
    success_count = 0
    total_start = time.time()
    
    for idx, scenario in enumerate(TEST_SCENARIOS, 1):
        result = await run_test_scenario(idx, scenario)
        if result.get("success", False):
            success_count += 1
        
        if idx < len(TEST_SCENARIOS):
            await asyncio.sleep(1)
    
    total_time = time.time() - total_start
    
    print("\n" + "="*80)
    print("📊 테스트 결과 요약 (순차 실행)")
    print("="*80)
    print(f"✅ 성공: {success_count}/{len(TEST_SCENARIOS)} 시나리오")
    print(f"⏱️  총 소요 시간: {total_time:.2f}초")
    print(f"⚡ 평균 처리 시간: {total_time/len(TEST_SCENARIOS):.2f}초/시나리오")
    print("="*80 + "\n")
    
    if success_count == len(TEST_SCENARIOS):
        print("🎉 모든 테스트 통과!")
    else:
        print(f"⚠️  {len(TEST_SCENARIOS) - success_count}개 시나리오 실패")

if __name__ == "__main__":
    asyncio.run(run_all_tests_sequential())
