from __future__ import annotations

import wave

import pytest

from eval.collect_sections import build_sections, iter_pcm_chunks


def test_build_sections_keeps_final_summaries_with_their_transcripts():
    transcripts = [
        {"sectionIndex": 0, "startSec": 10, "endSec": 20, "text": "둘째 "},
        {"sectionIndex": 0, "startSec": 0, "endSec": 10, "text": "첫째"},
        {"sectionIndex": 1, "startSec": 30, "endSec": 40, "text": "마지막"},
    ]
    summaries = [
        {"sectionIndex": 0, "startSec": 0, "endSec": 31, "text": "요약0", "phase": "FINAL"},
        {"sectionIndex": 1, "startSec": 31, "endSec": 40, "text": "부분", "phase": "PARTIAL"},
    ]

    sections = build_sections(transcripts, summaries)

    assert sections == [
        {"section_index": 0, "start_sec": 0, "end_sec": 31, "transcript": "첫째 둘째", "summary": "요약0"},
    ]


def test_iter_pcm_chunks_splits_wav_and_rejects_other_formats(tmp_path):
    path = tmp_path / "a.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\x01\x00" * 10)

    assert [len(c) for c in iter_pcm_chunks(path, chunk_samples=4)] == [8, 8, 4]

    other = tmp_path / "b.wav"
    with wave.open(str(other), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00")
    with pytest.raises(ValueError):
        list(iter_pcm_chunks(other))
