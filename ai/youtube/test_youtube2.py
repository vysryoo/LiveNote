"""
YouTubeKit 단일 테스트 (API 쿼터 절약용)
모든 필드를 포함한 완전한 테스트 - LLM vs Heuristic 비교
"""
import asyncio
import time
from youtubekit import YouTubeService, YouTubeRequest, PreviousSummary, RAGChunk


async def run_test(verify_yt: bool, test_name: str):
    """단일 테스트 실행"""
    
    print("=" * 80)
    print(f"🧪 {test_name}")
    print("=" * 80)
    print()
    
    # 이전 섹션 요약 (previous_summaries)
    previous_summaries = [
        PreviousSummary(
            section_id=0,
            summary="Introduction to Python programming: variables, data types, and basic syntax"
        ),
        PreviousSummary(
            section_id=1,
            summary="Control flow in Python: if statements, for loops, and while loops"
        )
    ]
    
    # RAG 컨텍스트 (강의 자료에서 추출)
    rag_context = [
        RAGChunk(
            text="List comprehension is a concise way to create lists in Python. "
                 "It consists of brackets containing an expression followed by a for clause.",
            metadata={"source": "lecture_notes.pdf", "page": 15}
        ),
        RAGChunk(
            text="Example: squares = [x**2 for x in range(10)] creates a list of squares from 0 to 81.",
            metadata={"source": "lecture_notes.pdf", "page": 15}
        ),
        RAGChunk(
            content="List comprehensions can also include conditional logic using if statements. "
                    "This makes them very powerful for data filtering and transformation.",
            metadata={"source": "code_examples.py", "line": 42}
        )
    ]
    
    # 제외할 영상 제목들
    exclude_titles = [
        "Python Tutorial for Beginners",  # 너무 기초
        "Complete Python Course",  # 너무 포괄적
    ]
    
    # 완전한 요청 객체 생성
    req = YouTubeRequest(
        lecture_id="python_adv_001",
        section_id=2,
        lecture_summary="Advanced Python list comprehensions: nested loops, conditional expressions, "
                       "and performance optimization techniques for data processing",
        language="en",
        top_k=3,
        verify_yt=verify_yt,  # LLM vs Heuristic
        yt_lang="en",
        min_score=6.0,
        previous_summaries=previous_summaries,
        rag_context=rag_context,
        exclude_titles=exclude_titles
    )
    
    print("📋 요청 정보:")
    print(f"   • verify_yt: {req.verify_yt} ({'LLM 검증' if verify_yt else 'Heuristic 점수'})")
    print(f"   • lecture_summary: {req.lecture_summary[:70]}...")
    print(f"   • top_k: {req.top_k}")
    print(f"   • previous_summaries: {len(previous_summaries)}개")
    print(f"   • rag_context: {len(rag_context)}개 청크")
    print(f"   • exclude_titles: {len(exclude_titles)}개")
    print()
    print("─" * 80)
    
    # 서비스 실행
    service = YouTubeService()
    
    start_time = time.time()
    
    try:
        results = await service.recommend_videos(req)
        
        elapsed = time.time() - start_time
        
        print()
        print("=" * 80)
        print(f"✅ 총 {len(results)}개 영상 추천 (처리 시간: {elapsed:.2f}초)")
        print("=" * 80)
        print()
        
        for idx, r in enumerate(results, 1):
            print(f"  [{idx}] 🎬 {r.video_info.title}")
            print(f"      📊 점수: {r.score:.1f}/10.0 (방법: {r.reason})")
            print(f"      🔗 URL: {r.video_info.url}")
            print(f"      📝 요약: {r.video_info.extract[:100]}...")
            print()
        
        print("=" * 80)
        print(f"⏱️  {test_name} 완료 - {elapsed:.2f}초")
        print("=" * 80)
        print()
        
        return elapsed, results
        
    except Exception as e:
        elapsed = time.time() - start_time
        print()
        print("=" * 80)
        print(f"❌ 테스트 실패 (소요 시간: {elapsed:.2f}초)")
        print("=" * 80)
        print(f"에러: {e}")
        
        import traceback
        traceback.print_exc()
        
        return elapsed, None


async def test_comparison():
    """LLM vs Heuristic 비교 테스트"""
    
    print("\n")
    print("🔬" * 40)
    print("LLM vs Heuristic 성능 비교 테스트")
    print("🔬" * 40)
    print("\n")
    
    # 1. LLM 검증 테스트
    time_llm, results_llm = await run_test(
        verify_yt=True, 
        test_name="테스트 1: LLM 검증 (verify_yt=True)"
    )
    
    print("\n" + "─" * 80 + "\n")
    
    # 2. Heuristic 테스트
    time_heuristic, results_heuristic = await run_test(
        verify_yt=False, 
        test_name="테스트 2: Heuristic 점수 (verify_yt=False)"
    )
    
    # 결과 비교
    print("\n")
    print("📊" * 40)
    print("최종 비교 결과")
    print("📊" * 40)
    print()
    
    print(f"⏱️  처리 시간:")
    print(f"   • LLM 검증:     {time_llm:.2f}초")
    print(f"   • Heuristic:    {time_heuristic:.2f}초")
    print(f"   • 시간 차이:    {abs(time_llm - time_heuristic):.2f}초")
    print(f"   • 빠른 방법:    {'Heuristic' if time_heuristic < time_llm else 'LLM'} "
          f"({min(time_llm, time_heuristic):.2f}초)")
    print()
    
    if results_llm and results_heuristic:
        print(f"📊 점수 비교:")
        print(f"   • LLM 평균:     {sum(r.score for r in results_llm)/len(results_llm):.1f}/10.0")
        print(f"   • Heuristic 평균: {sum(r.score for r in results_heuristic)/len(results_heuristic):.1f}/10.0")
        print()
        
        print(f"🎯 추천 영상:")
        print(f"   • LLM:         {len(results_llm)}개")
        print(f"   • Heuristic:   {len(results_heuristic)}개")
        print()
    
    print("=" * 80)
    print("🎉 비교 테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_comparison())
