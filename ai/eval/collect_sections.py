"""
평가 데이터 수집

준비된 강의 녹음(audio.wav)과 자료(material.pdf)를 실제 서비스 경로로 넣어 전사·섹션·요약을 만든다.
브라우저 대신 백엔드 녹음 WebSocket에 24kHz PCM16 음성을 실제 속도로 보낸다.

순서: 로그인 → 강의 생성(PDF 업로드) → 음성 전송 → 연결 종료 → 강의 종료 → 확정 요약이 더 늘지 않을 때까지 대기
결과: eval/data/inbox/{강의ID}/sections.json

백엔드는 자동 카드 생성을 끈 상태(APP_AI_AUTO_CARDS_ENABLED=false)로 띄운다. 이 도구는 OpenAI 비용이 든다
(실시간 전사, 섹션 요약).

환경변수:
    EVAL_LOGIN_ID, EVAL_PASSWORD: 백엔드 계정
    EVAL_BACKEND_URL: 백엔드 주소 (기본 http://localhost:8080)

사용:
    python -m eval.collect_sections eng-1 eng-2 ...
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List

from eval.prepare_data import INBOX_DIR

BACKEND_URL = os.getenv("EVAL_BACKEND_URL", "http://localhost:8080")
SAMPLE_RATE = 24000
# 프런트엔드 녹음과 같은 크기(4096샘플, 약 170ms). 백엔드 WebSocket 메시지 한도가 8192바이트라 이보다 크면 연결이 끊김
CHUNK_SAMPLES = 4096
# 마지막 말 구간이 끝났다고 인식되도록 녹음 끝에 붙이는 침묵
TRAILING_SILENCE_SEC = 2.0
# 연결을 닫은 뒤 서버가 남은 전사를 마무리하는 시간(최대 10초)보다 길게 기다림
DRAIN_WAIT_SEC = 15
SUMMARY_POLL_SEC = 10
SUMMARY_STABLE_POLLS = 3
SUMMARY_MAX_WAIT_SEC = 180


def iter_pcm_chunks(wav_path: Path, chunk_samples: int = CHUNK_SAMPLES) -> Iterator[bytes]:
    """WAV 파일을 일정 길이의 PCM16 조각으로 나눠 돌려준다.

    Args:
        wav_path: 24kHz, 16bit, 모노 WAV 경로
        chunk_samples: 조각 하나의 샘플 수
    Returns:
        PCM16 바이트 조각을 차례로 돌려주는 반복자
    Raises:
        ValueError: WAV 형식이 24kHz 16bit 모노가 아닌 경우
    """
    with wave.open(str(wav_path), "rb") as wav:
        if (wav.getframerate(), wav.getsampwidth(), wav.getnchannels()) != (SAMPLE_RATE, 2, 1):
            raise ValueError(f"24kHz 16bit 모노 WAV만 지원: {wav_path}")
        while True:
            frames = wav.readframes(chunk_samples)
            if not frames:
                return
            yield frames


def build_sections(transcripts: List[dict], summaries: List[dict]) -> List[dict]:
    """강의 상세 응답의 전사와 요약을 섹션 단위로 묶는다.

    확정(FINAL) 요약이 없는 섹션은 제외한다. 강의 종료 시점의 마지막 섹션은 30초를 채우지 못하면 확정 요약이 생기지 않는다.

    Args:
        transcripts: 상세 응답의 transcripts (sectionIndex, startSec, endSec, text)
        summaries: 상세 응답의 summaries (sectionIndex, startSec, endSec, text, phase)
    Returns:
        섹션 목록 (section_index, start_sec, end_sec, transcript, summary). section_index 순서
    """
    final_summaries = {
        s["sectionIndex"]: s for s in summaries if str(s.get("phase", "FINAL")).upper() == "FINAL" and s.get("text")
    }
    sections = []
    for index in sorted(final_summaries):
        lines = [t for t in transcripts if t.get("sectionIndex") == index]
        lines.sort(key=lambda t: t.get("startSec") or 0)
        summary = final_summaries[index]
        sections.append({
            "section_index": index,
            "start_sec": summary.get("startSec"),
            "end_sec": summary.get("endSec"),
            "transcript": " ".join(t["text"].strip() for t in lines if t.get("text")),
            "summary": summary["text"].strip(),
        })
    return sections


async def _login(session) -> str:
    login_id, password = os.getenv("EVAL_LOGIN_ID"), os.getenv("EVAL_PASSWORD")
    if not login_id or not password:
        raise RuntimeError("EVAL_LOGIN_ID, EVAL_PASSWORD 환경변수가 필요함")
    async with session.post(f"{BACKEND_URL}/api/auth/login", json={"loginId": login_id, "password": password}) as res:
        res.raise_for_status()
        return (await res.json())["data"]["token"]


async def _create_lecture(session, token: str, title: str, subject: str, pdf_path: Path) -> int:
    import aiohttp

    form = aiohttp.FormData()
    form.add_field("title", title)
    form.add_field("subject", subject)
    form.add_field("sttLanguage", "ko")
    form.add_field("files", pdf_path.read_bytes(), filename=pdf_path.name, content_type="application/pdf")
    async with session.post(f"{BACKEND_URL}/api/lectures", data=form, headers={"Authorization": f"Bearer {token}"}) as res:
        res.raise_for_status()
        return (await res.json())["data"]["id"]


async def _stream_audio(session, token: str, backend_lecture_id: int, wav_path: Path) -> int:
    ws_url = BACKEND_URL.replace("http", "ws", 1) + f"/ws/transcription?sessionId={backend_lecture_id}&token={token}"
    received = 0
    async with session.ws_connect(ws_url, max_msg_size=0) as ws:

        async def drain() -> None:
            nonlocal received
            async for message in ws:
                if message.type.name == "TEXT" and '"transcript"' in message.data:
                    received += 1

        reader = asyncio.create_task(drain())
        started = time.monotonic()
        sent_samples = 0
        silence = b"\x00\x00" * int(TRAILING_SILENCE_SEC * SAMPLE_RATE)
        chunks = list(iter_pcm_chunks(wav_path))
        chunks += [silence[i:i + CHUNK_SAMPLES * 2] for i in range(0, len(silence), CHUNK_SAMPLES * 2)]
        for chunk in chunks:
            await ws.send_bytes(chunk)
            sent_samples += len(chunk) // 2
            # 실제 녹음과 같은 속도로 보내도록 보낸 음성 길이만큼 시간이 지날 때까지 기다림
            delay = started + sent_samples / SAMPLE_RATE - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
        await ws.close()
        await asyncio.wait_for(reader, timeout=DRAIN_WAIT_SEC)
    return received


async def _fetch_detail(session, token: str, backend_lecture_id: int) -> dict:
    async with session.get(
        f"{BACKEND_URL}/api/lectures/{backend_lecture_id}/detail", headers={"Authorization": f"Bearer {token}"}
    ) as res:
        res.raise_for_status()
        return (await res.json())["data"]


async def collect(lecture_id: str) -> dict:
    """강의 하나의 녹음을 서비스에 넣고 섹션별 전사·요약을 저장한다.

    Args:
        lecture_id: 강의ID (예: eng-1). inbox/{강의ID}/에 audio.wav, material.pdf, meta.json이 있어야 함
    Returns:
        저장한 sections.json 내용
    Raises:
        RuntimeError: 계정 환경변수가 없는 경우
        aiohttp.ClientResponseError: 백엔드 요청이 실패한 경우
    """
    import aiohttp

    lecture_dir = INBOX_DIR / lecture_id
    meta = json.loads((lecture_dir / "meta.json").read_text(encoding="utf-8"))
    title = f"[eval] {lecture_id} {meta['topic']}"

    async with aiohttp.ClientSession() as session:
        token = await _login(session)
        backend_lecture_id = await _create_lecture(session, token, title, meta["subject"], lecture_dir / "material.pdf")
        print(f"{lecture_id}: 강의 생성 id={backend_lecture_id}, 음성 전송 시작 ({meta['audio_sec']}초)")
        received = await _stream_audio(session, token, backend_lecture_id, lecture_dir / "audio.wav")
        await asyncio.sleep(DRAIN_WAIT_SEC)

        # 종료 API와 상세 조회는 녹음이 끝난 뒤라 새 토큰으로 요청
        token = await _login(session)
        async with session.post(
            f"{BACKEND_URL}/api/lectures/{backend_lecture_id}/end",
            json={"title": title},
            headers={"Authorization": f"Bearer {token}"},
        ) as res:
            res.raise_for_status()

        # 마지막 섹션들의 확정 요약은 콜백으로 늦게 도착하므로 개수가 더 늘지 않을 때까지 기다림
        stable, last_count, waited = 0, -1, 0
        detail = await _fetch_detail(session, token, backend_lecture_id)
        while stable < SUMMARY_STABLE_POLLS and waited < SUMMARY_MAX_WAIT_SEC:
            await asyncio.sleep(SUMMARY_POLL_SEC)
            waited += SUMMARY_POLL_SEC
            detail = await _fetch_detail(session, token, backend_lecture_id)
            count = len(detail.get("summaries") or [])
            stable = stable + 1 if count == last_count else 0
            last_count = count

    sections = build_sections(detail.get("transcripts") or [], detail.get("summaries") or [])
    result = {
        "lecture_id": lecture_id,
        "backend_lecture_id": backend_lecture_id,
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "transcript_messages": received,
        "transcripts": [
            {k: t.get(k) for k in ("sectionIndex", "startSec", "endSec", "text")}
            for t in detail.get("transcripts") or []
        ],
        "sections": sections,
    }
    (lecture_dir / "sections.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


async def _collect_all(lecture_ids: List[str]) -> None:
    results = await asyncio.gather(*[collect(lecture_id) for lecture_id in lecture_ids], return_exceptions=True)
    for lecture_id, result in zip(lecture_ids, results):
        if isinstance(result, Exception):
            print(f"{lecture_id}: 실패 {type(result).__name__}: {result}")
        else:
            print(f"{lecture_id}: 전사 {len(result['transcripts'])}줄, 확정 요약 섹션 {len(result['sections'])}개")


def main() -> None:
    parser = argparse.ArgumentParser(description="평가 데이터 수집 (실제 서비스 경로)")
    parser.add_argument("lecture_ids", nargs="+", help="강의ID (예: eng-1)")
    args = parser.parse_args()
    asyncio.run(_collect_all(args.lecture_ids))


if __name__ == "__main__":
    main()
