"""YouTubeKit 컴포넌트별 테스트 - 성능 진단 및 API 키 검증"""
import asyncio
import time
from dotenv import load_dotenv
import os

load_dotenv()

print("="*80)
print("🔍 YouTubeKit 컴포넌트별 성능 테스트")
print("="*80)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: 환경 변수 확인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[TEST 1] 환경 변수 확인")
print("-" * 80)
openai_key = os.getenv("OPENAI_API_KEY", "")
youtube_key = os.getenv("YOUTUBE_API_KEY", "") or os.getenv("KEY", "")
offline_mode = os.getenv("YT_OFFLINE_MODE", "0")

print(f"✓ OPENAI_API_KEY: {'설정됨' if openai_key else '❌ 없음'} ({len(openai_key)} chars)")
print(f"✓ YouTube API KEY: {'설정됨' if youtube_key else '❌ 없음'} ({len(youtube_key)} chars)")
print(f"✓ YT_OFFLINE_MODE: {offline_mode}")

if not youtube_key:
    print("\n❌ YouTube API 키가 설정되지 않았습니다!")
    exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: YouTube API 직접 호출 테스트 (가장 기본)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[TEST 2] YouTube API 직접 호출 (순수 HTTP)")
print("-" * 80)

async def test_youtube_api_direct():
    """YouTube API를 직접 호출해서 키가 작동하는지 테스트"""
    import aiohttp
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": youtube_key,
        "part": "snippet",
        "q": "python tutorial",
        "type": "video",
        "maxResults": 1
    }
    
    start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                elapsed = time.time() - start
                
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ YouTube API 작동 확인! ({elapsed:.2f}초)")
                    if 'items' in data and len(data['items']) > 0:
                        video = data['items'][0]['snippet']
                        print(f"   제목: {video['title']}")
                        print(f"   채널: {video['channelTitle']}")
                    return True
                else:
                    error_data = await resp.text()
                    print(f"❌ API 에러 (Status {resp.status}): {error_data}")
                    return False
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"❌ 타임아웃! ({elapsed:.2f}초 경과)")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 에러 ({elapsed:.2f}초): {e}")
        return False

result = asyncio.run(test_youtube_api_direct())
if not result:
    print("\n⚠️  YouTube API 키에 문제가 있습니다. 계속 진행하시겠습니까?")
    # exit(1)  # 주석 처리 - 계속 테스트 진행

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: YouTubeClient 초기화 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[TEST 3] YouTubeClient 초기화")
print("-" * 80)

try:
    from youtubekit.api.youtube_client import YouTubeAPIClient
    from youtubekit.config.youtube_config import YouTubeConfig
    
    start = time.time()
    config = YouTubeConfig()
    client = YouTubeAPIClient(api_key=config.YOUTUBE_API_KEY)
    elapsed = time.time() - start
    print(f"✅ YouTubeAPIClient 초기화 성공 ({elapsed:.4f}초)")
except Exception as e:
    print(f"❌ 초기화 실패: {e}")
    import traceback
    traceback.print_exc()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: YouTubeClient.search_videos() 성능 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[TEST 4] YouTubeClient.search_videos() 성능")
print("-" * 80)

async def test_search_videos():
    from youtubekit.api.youtube_client import YouTubeAPIClient
    from youtubekit.config.youtube_config import YouTubeConfig
    
    config = YouTubeConfig()
    client = YouTubeAPIClient(api_key=config.YOUTUBE_API_KEY)
    
    start = time.time()
    try:
        videos = await client.search_videos("python tutorial", lang="en", max_results=3)
        elapsed = time.time() - start
        
        print(f"✅ 검색 완료: {len(videos)}개 영상 ({elapsed:.2f}초)")
        for idx, v in enumerate(videos, 1):
            print(f"   [{idx}] {v.title[:60]}...")
        return videos
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 검색 실패 ({elapsed:.2f}초): {e}")
        import traceback
        traceback.print_exc()
        return []

videos = asyncio.run(test_search_videos())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 5: OpenAI LLM 요약 테스트 (병목 지점 의심)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[TEST 5] OpenAI LLM 요약 생성 (병목 의심 지점)")
print("-" * 80)

async def test_llm_summarize():
    from youtubekit.llm.openai_client import YouTubeLLMClient
    from youtubekit.config.youtube_config import YouTubeConfig
    
    if not videos:
        print("⚠️  이전 테스트에서 영상을 가져오지 못해 스킵합니다.")
        return
    
    config = YouTubeConfig()
    llm = YouTubeLLMClient(api_key=config.OPENAI_API_KEY)
    
    video = videos[0]
    
    print(f"영상: {video.title}")
    print(f"설명 길이: {len(video.description)} chars")
    
    start = time.time()
    try:
        result = await llm.summarize_content(
            title=video.title,
            content=video.description,
            language="en"
        )
        elapsed = time.time() - start
        
        summary = result.get("extract", "")
        print(f"✅ 요약 생성 완료 ({elapsed:.2f}초)")
        print(f"   요약: {summary[:200]}...")
        return summary
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 요약 실패 ({elapsed:.2f}초): {e}")
        import traceback
        traceback.print_exc()
        return None

summary = asyncio.run(test_llm_summarize())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: LLM 검증 테스트 (가장 오래 걸림 예상)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n[TEST 6] OpenAI LLM 검증 (verify_yt=True 시나리오)")
print("-" * 80)

async def test_llm_verify():
    from youtubekit.llm.openai_client import YouTubeLLMClient
    from youtubekit.config.youtube_config import YouTubeConfig
    
    if not videos or not summary:
        print("⚠️  이전 테스트 실패로 스킵합니다.")
        return
    
    config = YouTubeConfig()
    llm = YouTubeLLMClient(api_key=config.OPENAI_API_KEY)
    
    video = videos[0]
    lecture_summary = "Python programming tutorial for beginners"
    
    print(f"강의 요약: {lecture_summary}")
    print(f"영상: {video.title}")
    
    start = time.time()
    try:
        result = await llm.score_video(
            lecture_summary=lecture_summary,
            title=video.title,
            extract=summary,
            language="en"
        )
        elapsed = time.time() - start
        
        score = result.get("score", 0)
        reason = result.get("reason", "")
        print(f"✅ LLM 검증 완료 ({elapsed:.2f}초)")
        print(f"   점수: {score}/10.0")
        print(f"   이유: {reason[:100]}...")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 검증 실패 ({elapsed:.2f}초): {e}")
        import traceback
        traceback.print_exc()
        return None

verify_result = asyncio.run(test_llm_verify())

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 최종 요약
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*80)
print("📊 성능 분석 요약")
print("="*80)
print("""
예상 병목 지점:
1. YouTube API 검색: 1-3초 (정상)
2. OpenAI LLM 요약 (각 영상마다): 2-5초 ⚠️
3. OpenAI LLM 검증 (각 영상마다): 3-6초 ⚠️⚠️

만약 top_k=3, verify_yt=True라면:
- 검색: 2초
- 요약 3개: 3초 x 3 = 9초
- 검증 3개: 5초 x 3 = 15초
- 총합: 약 26초 이상!

해결 방안:
1. 병렬 처리 (asyncio.gather) - 가장 효과적
2. verify_yt=False 사용 (Heuristic만) - 15초 절약
3. top_k 줄이기
4. LLM 모델 변경 (gpt-4o-mini -> gpt-3.5-turbo)
""")
