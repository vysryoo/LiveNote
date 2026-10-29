"""
평가 데이터 준비

생성형 AI가 만든 강의 응답(response.md)을 평가에 쓸 파일로 바꾼다.

- slides.md, script.txt: 응답에서 강의 자료와 스크립트를 분리. 이미 있으면 그대로 두어 수동 수정을 보존
- material.pdf: 강의 자료를 슬라이드(16:9) 또는 노트(A4) 쪽으로 인쇄
- audio.wav: 스크립트를 문장 묶음 단위로 TTS 합성하고 사이에 쉼을 넣은 24kHz 모노 PCM
- meta.json: 기획표 정보, 분량, 슬라이드(쪽)별 음성 구간

사용:
    python -m eval.prepare_data eng-1
    python -m eval.prepare_data eng-1 --skip-audio
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import html
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

DATA_DIR = Path(__file__).resolve().parent / "data"
INBOX_DIR = DATA_DIR / "inbox"
TTS_CACHE_DIR = DATA_DIR / ".cache" / "tts"

SLIDES_START, SLIDES_END = "<<<SLIDES_MD>>>", "<<<END_SLIDES_MD>>>"
SCRIPT_START, SCRIPT_END = "<<<SCRIPT_TXT>>>", "<<<END_SCRIPT_TXT>>>"
MARKER_PATTERN = re.compile(r"^\[(?:슬라이드|쪽) (\d+)\]$")
SENTENCE_END_PATTERN = re.compile(r"(?<=[.?!])\s+")
FORBIDDEN_CHARS = "()*#→×÷\"[]"

SAMPLE_RATE = 24000
TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = os.getenv("EVAL_TTS_VOICE", "cedar")
TTS_INSTRUCTIONS = "한국 대학 강의실에서 교수가 학생들에게 설명하듯, 자연스럽고 차분한 속도의 한국어로 읽으세요."
TTS_CONCURRENCY = 4

# 백엔드 말 구간 인식(server_vad)의 침묵 기준이 500ms라, 문장 묶음 사이 쉼을 그보다 길게 두어 따로 전사되게 함
PAUSE_SECONDS = {
    "group": (0.6, 0.9),
    "paragraph": (0.9, 1.5),
    "slide": (1.5, 2.2),
    "end": (0.0, 0.0),
}
MAX_SENTENCES_PER_CHUNK = 3

SCRIPT_MIN_CHARS = 3000


@dataclass
class Paragraph:
    """스크립트 문단과 해당 슬라이드(쪽) 번호."""

    page: int
    text: str


@dataclass
class SpeechChunk:
    """TTS 한 번으로 합성할 문장 묶음과 뒤에 둘 쉼 종류."""

    page: int
    text: str
    pause_after: str


def split_response(response: str) -> Tuple[str, str]:
    """생성형 AI 응답을 강의 자료와 스크립트로 나눈다.

    Args:
        response: 구분 표시 줄이 들어 있는 응답 원문
    Returns:
        (강의 자료 Markdown, 스크립트)
    Raises:
        ValueError: 구분 표시 줄이 없는 경우
    """
    for marker in (SLIDES_START, SLIDES_END, SCRIPT_START, SCRIPT_END):
        if marker not in response:
            raise ValueError(f"응답에 구분 표시 줄이 없음: {marker}")
    material = response.split(SLIDES_START, 1)[1].split(SLIDES_END, 1)[0].strip()
    script = response.split(SCRIPT_START, 1)[1].split(SCRIPT_END, 1)[0].strip()
    return material, script


def split_pages(material: str) -> List[str]:
    """강의 자료를 '---' 줄 기준으로 슬라이드(쪽) 단위로 나눈다.

    Args:
        material: 강의 자료 Markdown
    Returns:
        슬라이드(쪽) Markdown 목록. 빈 쪽은 제외
    """
    return [page.strip() for page in re.split(r"^---\s*$", material, flags=re.M) if page.strip()]


def parse_script(script: str) -> List[Paragraph]:
    """스크립트를 슬라이드(쪽) 번호가 붙은 문단 목록으로 바꾼다.

    Args:
        script: '[슬라이드 N]' 또는 '[쪽 N]' 표시가 들어 있는 스크립트
    Returns:
        문단 목록. 첫 표시 전 문단은 1번으로 봄
    """
    paragraphs: List[Paragraph] = []
    page = 1
    buffer: List[str] = []

    def flush() -> None:
        text = " ".join(line.strip() for line in buffer).strip()
        if text:
            paragraphs.append(Paragraph(page=page, text=text))
        buffer.clear()

    for line in script.splitlines():
        marker = MARKER_PATTERN.match(line.strip())
        if marker:
            flush()
            page = int(marker.group(1))
        elif not line.strip():
            flush()
        else:
            buffer.append(line)
    flush()
    return paragraphs


def to_speech_chunks(paragraphs: List[Paragraph]) -> List[SpeechChunk]:
    """문단을 TTS 합성 단위(최대 3문장)로 나누고 뒤에 둘 쉼 종류를 정한다.

    Args:
        paragraphs: 스크립트 문단 목록
    Returns:
        합성 단위 목록. 마지막 단위의 쉼은 'end'
    """
    chunks: List[SpeechChunk] = []
    for index, paragraph in enumerate(paragraphs):
        sentences = [s for s in SENTENCE_END_PATTERN.split(paragraph.text) if s.strip()]
        groups = [
            " ".join(sentences[i:i + MAX_SENTENCES_PER_CHUNK])
            for i in range(0, len(sentences), MAX_SENTENCES_PER_CHUNK)
        ]
        next_page = paragraphs[index + 1].page if index + 1 < len(paragraphs) else None
        for group_index, group in enumerate(groups):
            if group_index < len(groups) - 1:
                pause = "group"
            elif next_page is None:
                pause = "end"
            elif next_page != paragraph.page:
                pause = "slide"
            else:
                pause = "paragraph"
            chunks.append(SpeechChunk(page=paragraph.page, text=group, pause_after=pause))
    return chunks


def check_script(page_count: int, paragraphs: List[Paragraph]) -> List[str]:
    """스크립트 형식과 분량을 점검한다.

    Args:
        page_count: 강의 자료의 슬라이드(쪽) 수
        paragraphs: 스크립트 문단 목록
    Returns:
        경고 문장 목록. 문제가 없으면 빈 목록
    """
    warnings: List[str] = []
    pages = [p.page for p in paragraphs]
    covered = sorted(set(pages))
    if covered != list(range(1, page_count + 1)):
        missing = sorted(set(range(1, page_count + 1)) - set(covered))
        extra = sorted(set(covered) - set(range(1, page_count + 1)))
        warnings.append(f"슬라이드 표시가 자료와 맞지 않음: 자료 {page_count}장, 빠진 번호 {missing}, 넘는 번호 {extra}")
    if pages != sorted(pages):
        warnings.append("슬라이드 표시 번호가 순서대로가 아님")
    text = " ".join(p.text for p in paragraphs)
    found = sorted({c for c in text if c in FORBIDDEN_CHARS})
    if found:
        warnings.append(f"음성 합성에 쓰지 않을 기호가 있음: {' '.join(found)}")
    if len(text) < SCRIPT_MIN_CHARS:
        warnings.append(f"스크립트가 짧음: 공백 포함 {len(text)}자")
    return warnings


def parse_plan(plan: str) -> Dict[str, Dict[str, str]]:
    """기획표(Markdown 표)를 강의ID별 항목으로 바꾼다.

    Args:
        plan: plan.md 내용
    Returns:
        {강의ID: {열 이름: 값}}
    """
    rows = [line.strip().strip("|").split("|") for line in plan.splitlines() if line.strip().startswith("|")]
    if len(rows) < 3:
        return {}
    header = [cell.strip() for cell in rows[0]]
    lectures: Dict[str, Dict[str, str]] = {}
    for row in rows[2:]:
        cells = [cell.strip() for cell in row]
        entry = dict(zip(header, cells))
        lectures[entry.get("강의ID", "")] = entry
    return lectures


def build_material_html(material: str, style: str) -> str:
    """강의 자료 Markdown을 쪽 단위 인쇄용 HTML로 바꾼다.

    Args:
        material: 강의 자료 Markdown
        style: 'slide'(16:9 한 장씩) 또는 'notes'(A4, 넘치면 다음 쪽으로 이어짐)
    Returns:
        HTML 문서
    """
    import markdown

    sections = []
    for page in split_pages(material):
        body = markdown.markdown(page, extensions=["tables"])
        body = re.sub(r"<p>\[그림: (.+?)\]</p>", r'<div class="figure">그림: \1</div>', body)
        density = "dense" if len(page.splitlines()) > 14 else "normal"
        sections.append(f'<section class="page {density}">{body}</section>')

    if style == "slide":
        page_css = """
@page { size: 254mm 142.875mm; margin: 0; }
section.page { width: 254mm; height: 142.875mm; padding: 10mm 16mm; overflow: hidden; }
section.page.normal { font-size: 15pt; }
section.page.dense { font-size: 11pt; }
h1 { font-size: 1.6em; margin: 0 0 0.5em; color: #1f2a5a; }
"""
    else:
        page_css = """
@page { size: A4; margin: 20mm 18mm; }
section.page { font-size: 10.5pt; line-height: 1.7; }
h1 { font-size: 18pt; } h2 { font-size: 13pt; margin-top: 1.2em; }
"""
    # Apple SD Gothic Neo·나눔고딕으로 인쇄하면 pypdf 추출 시 띄어쓰기가 사라져 AppleGothic 사용
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: "AppleGothic", "Noto Sans KR", sans-serif; color: #222; word-break: keep-all; }}
section.page {{ page-break-after: always; }}
section.page:last-child {{ page-break-after: auto; }}
table {{ border-collapse: collapse; margin: 0.6em 0; }}
th, td {{ border: 1px solid #999; padding: 0.25em 0.5em; }}
th {{ background: #eef1f7; }}
ul {{ margin: 0.3em 0; padding-left: 1.2em; }}
.figure {{ border: 1px dashed #aaa; background: #f6f6f6; color: #666; padding: 0.6em; margin: 0.5em 0; font-size: 0.85em; }}
{page_css}
</style></head><body>
{''.join(sections)}
</body></html>"""


def render_pdf(html_text: str, out_path: Path) -> None:
    """HTML을 헤드리스 Chrome으로 PDF로 인쇄한다.

    Args:
        html_text: 인쇄할 HTML 문서
        out_path: 저장할 PDF 경로
    Raises:
        RuntimeError: Chrome을 찾지 못했거나 인쇄에 실패한 경우
    """
    chrome = os.getenv("CHROME_PATH") or next(
        (
            path
            for path in (
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                shutil.which("google-chrome"),
                shutil.which("chromium"),
            )
            if path and Path(path).exists()
        ),
        None,
    )
    if not chrome:
        raise RuntimeError("Chrome을 찾지 못함. CHROME_PATH 환경변수로 지정")
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "material.html"
        html_path.write_text(html_text, encoding="utf-8")
        result = subprocess.run(
            [
                chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={out_path}", html_path.as_uri(),
            ],
            capture_output=True,
            timeout=120,
        )
    if result.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"PDF 인쇄 실패: {result.stderr.decode(errors='ignore')[-300:]}")


async def _synthesize_chunk(client, chunk: SpeechChunk, semaphore: asyncio.Semaphore) -> bytes:
    key = hashlib.sha256(f"{TTS_MODEL}|{TTS_VOICE}|{TTS_INSTRUCTIONS}|{chunk.text}".encode()).hexdigest()
    cache_path = TTS_CACHE_DIR / f"{key}.pcm"
    if cache_path.exists():
        return cache_path.read_bytes()
    async with semaphore:
        response = await client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=chunk.text,
            instructions=TTS_INSTRUCTIONS,
            response_format="pcm",
        )
    pcm = response.content
    TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(pcm)
    return pcm


async def synthesize_audio(chunks: List[SpeechChunk], out_path: Path, seed: int) -> List[dict]:
    """합성 단위를 TTS로 읽혀 쉼과 함께 하나의 WAV로 합친다.

    같은 문장은 캐시를 써서 다시 요청하지 않는다. 쉼 길이는 seed로 고정한다.

    Args:
        chunks: 합성 단위 목록
        out_path: 저장할 WAV 경로 (24kHz, 16bit, 모노)
        seed: 쉼 길이 난수 시드
    Returns:
        합성 단위별 {page, start_ms, end_ms, text} 목록
    """
    from dotenv import load_dotenv
    from openai import AsyncOpenAI

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    semaphore = asyncio.Semaphore(TTS_CONCURRENCY)
    async with AsyncOpenAI(timeout=120.0, max_retries=3) as client:
        pcms = await asyncio.gather(*[_synthesize_chunk(client, chunk, semaphore) for chunk in chunks])

    rng = random.Random(seed)
    timeline = []
    position = 0
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        for chunk, pcm in zip(chunks, pcms):
            start = position
            wav.writeframes(pcm)
            position += len(pcm) // 2
            timeline.append({
                "page": chunk.page,
                "start_ms": round(start * 1000 / SAMPLE_RATE),
                "end_ms": round(position * 1000 / SAMPLE_RATE),
                "text": chunk.text,
            })
            low, high = PAUSE_SECONDS[chunk.pause_after]
            silence = int(rng.uniform(low, high) * SAMPLE_RATE)
            wav.writeframes(b"\x00\x00" * silence)
            position += silence
    return timeline


def _page_ranges(timeline: List[dict]) -> List[dict]:
    ranges: Dict[int, dict] = {}
    for item in timeline:
        entry = ranges.setdefault(item["page"], {"page": item["page"], "start_ms": item["start_ms"]})
        entry["end_ms"] = item["end_ms"]
    return list(ranges.values())


def _pdf_page_count(pdf_path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(str(pdf_path)).pages)


def prepare(lecture_id: str, skip_audio: bool = False) -> dict:
    """강의 하나의 평가 데이터를 만든다.

    Args:
        lecture_id: 강의ID (예: eng-1). inbox/{강의ID}/response.md가 있어야 함
        skip_audio: True면 음성 합성을 건너뜀
    Returns:
        저장한 meta.json 내용
    Raises:
        FileNotFoundError: 응답 파일이나 기획표가 없는 경우
        KeyError: 기획표에 강의ID가 없는 경우
    """
    lecture_dir = INBOX_DIR / lecture_id
    plan = parse_plan((INBOX_DIR / "plan.md").read_text(encoding="utf-8"))
    info = plan[lecture_id]
    style = "notes" if "노트" in info.get("자료 형태", "") else "slide"

    slides_path = lecture_dir / "slides.md"
    script_path = lecture_dir / "script.txt"
    if not slides_path.exists() or not script_path.exists():
        material, script = split_response((lecture_dir / "response.md").read_text(encoding="utf-8"))
        slides_path.write_text(material + "\n", encoding="utf-8")
        script_path.write_text(script + "\n", encoding="utf-8")
    material = slides_path.read_text(encoding="utf-8")
    script = script_path.read_text(encoding="utf-8")

    pages = split_pages(material)
    paragraphs = parse_script(script)
    warnings = check_script(len(pages), paragraphs)
    script_text = " ".join(p.text for p in paragraphs)

    pdf_path = lecture_dir / "material.pdf"
    render_pdf(build_material_html(material, style), pdf_path)
    pdf_pages = _pdf_page_count(pdf_path)
    if style == "slide" and pdf_pages != len(pages):
        warnings.append(f"PDF 쪽 수({pdf_pages})가 슬라이드 수({len(pages)})와 다름. 넘친 슬라이드 확인 필요")

    meta = {
        "lecture_id": lecture_id,
        "field": info.get("분야"),
        "subject": info.get("과목명"),
        "topic": info.get("이번 회차 주제"),
        "prerequisites": info.get("수강 전제 지식"),
        "key_concepts": info.get("핵심 개념 8~10개"),
        "material_style": style,
        "language": "ko",
        "source": "생성형 AI로 작성한 합성 강의 자료와 스크립트, TTS 음성",
        "material_pages": len(pages),
        "pdf_pages": pdf_pages,
        "script_chars": len(script_text),
        "script_chars_without_spaces": len(re.sub(r"\s", "", script_text)),
        "warnings": warnings,
    }

    if not skip_audio:
        chunks = to_speech_chunks(paragraphs)
        seed = int(hashlib.sha256(lecture_id.encode()).hexdigest()[:8], 16)
        timeline = asyncio.run(synthesize_audio(chunks, lecture_dir / "audio.wav", seed))
        meta.update({
            "tts": {"model": TTS_MODEL, "voice": TTS_VOICE, "instructions": TTS_INSTRUCTIONS},
            "audio_sec": round(timeline[-1]["end_ms"] / 1000, 1) if timeline else 0,
            "page_ranges": _page_ranges(timeline),
            "chunks": timeline,
        })

    (lecture_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="평가 데이터 준비")
    parser.add_argument("lecture_ids", nargs="+", help="강의ID (예: eng-1)")
    parser.add_argument("--skip-audio", action="store_true", help="음성 합성 생략")
    args = parser.parse_args()
    for lecture_id in args.lecture_ids:
        meta = prepare(lecture_id, skip_audio=args.skip_audio)
        summary = {k: meta.get(k) for k in ("material_pages", "pdf_pages", "script_chars", "audio_sec")}
        print(lecture_id, json.dumps(summary, ensure_ascii=False))
        for warning in meta["warnings"]:
            print("  경고:", warning)


if __name__ == "__main__":
    main()
