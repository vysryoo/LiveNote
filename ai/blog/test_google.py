"""
Google 검색 추천 모듈 테스트
"""
import asyncio
import time
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from blogkit.service import GoogleService
from blogkit.models import GoogleRequest


async def test_basic_search():
    """기본 검색 테스트"""
    print("=" * 60)
    print("🧪 테스트 1: 기본 검색")
    print("=" * 60)
    
    service = GoogleService()
    request = GoogleRequest(
        lecture_id="test101",
        section_id=1,
        lecture_summary="하이퍼 스레딩(Hyper-Threading)은 인텔의 동시 멀티스레딩 기술입니다.",
        top_k=3,
        search_lang="en",
        language="ko"
    )
    
    start = time.perf_counter()
    results = await service.recommend_results(request)
    elapsed = int((time.perf_counter() - start) * 1000)
    
    print(f"\n✅ 결과: {len(results)}개")
    print(f"⏱️  소요 시간: {elapsed}ms")
    
    for i, result in enumerate(results, 1):
        print(f"\n--- 결과 {i} ---")
        print(f"제목: {result.search_result.title}")
        print(f"URL: {result.search_result.url}")
        print(f"점수: {result.score}")
        print(f"이유: {result.reason}")
        print(f"도메인: {result.search_result.display_link}")
    
    assert len(results) > 0, "검색 결과가 없습니다."
    print("\n✅ 테스트 1 통과!")


async def test_no_scoring_mode():
    """NO_SCORING 모드 테스트"""
    print("\n" + "=" * 60)
    print("🧪 테스트 2: NO_SCORING 모드")
    print("=" * 60)
    
    # NO_SCORING 플래그 활성화
    from blogkit.config import flags
    original_flag = flags.NO_SCORING
    flags.NO_SCORING = True
    
    try:
        service = GoogleService()
        request = GoogleRequest(
            lecture_id="test102",
            section_id=1,
            lecture_summary="CPU 멀티프로세싱과 멀티스레딩의 차이점을 비교합니다.",
            top_k=5,
            search_lang="en",
            language="ko"
        )
        
        start = time.perf_counter()
        results = await service.recommend_results(request)
        elapsed = int((time.perf_counter() - start) * 1000)
        
        print(f"\n✅ 결과: {len(results)}개")
        print(f"⏱️  소요 시간: {elapsed}ms")
        
        # NO_SCORING 모드 검증
        for i, result in enumerate(results, 1):
            print(f"\n--- 결과 {i} ---")
            print(f"제목: {result.search_result.title}")
            print(f"점수: {result.score} (should be 10.0)")
            print(f"이유: {result.reason} (should be 'search')")
            
            assert result.score == 10.0, f"NO_SCORING 모드에서 점수가 10.0이 아닙니다: {result.score}"
            assert result.reason == "search", f"NO_SCORING 모드에서 이유가 'search'가 아닙니다: {result.reason}"
        
        print("\n✅ 테스트 2 통과!")
    
    finally:
        # 플래그 원상복구
        flags.NO_SCORING = original_flag


async def test_heuristic_mode():
    """Heuristic 검증 모드 테스트"""
    print("\n" + "=" * 60)
    print("🧪 테스트 3: Heuristic 검증 모드")
    print("=" * 60)
    
    service = GoogleService()
    request = GoogleRequest(
        lecture_id="test103",
        section_id=1,
        lecture_summary="운영체제의 메모리 관리 기법에 대해 학습합니다.",
        top_k=3,
        verify_google=False,  # Heuristic 모드
        search_lang="en",
        language="ko"
    )
    
    start = time.perf_counter()
    results = await service.recommend_results(request)
    elapsed = int((time.perf_counter() - start) * 1000)
    
    print(f"\n✅ 결과: {len(results)}개")
    print(f"⏱️  소요 시간: {elapsed}ms")
    
    for i, result in enumerate(results, 1):
        print(f"\n--- 결과 {i} ---")
        print(f"제목: {result.search_result.title}")
        print(f"점수: {result.score}")
        print(f"이유: {result.reason}")
    
    print("\n✅ 테스트 3 통과!")


async def main():
    """메인 테스트 실행"""
    print("🚀 GoogleKit 테스트 시작\n")
    
    try:
        await test_basic_search()
        await test_no_scoring_mode()
        await test_heuristic_mode()
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
