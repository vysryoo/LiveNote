"""
스트리밍 효과 측정

AI 서버 /qa/generate(SSE)를 여러 번 호출해, 화면에 처음 내용이 보이는 시각과 완성 시각을 비교한다.

- 질문 표시: 항목의 question 이벤트 도착 (스트리밍에서 사용자가 처음 읽을 수 있는 시각)
- 첫 답변 조각: 항목의 첫 answer 이벤트 도착
- 항목 완료: 항목의 done 이벤트 도착 (항목별로 완성본을 보냈다면 처음 보였을 시각)
- 전체 완료: 응답 종료 (모든 항목을 한 번에 보냈다면 처음 보였을 시각)

시각은 요청을 보낸 순간부터 측정 도구가 이벤트를 받은 순간까지(ms)이며, 백엔드 중계와 브라우저 표시 시간은 포함하지 않는다.

비용: AI 서버의 QnA 생성 모델 호출

사용:
    python -m eval.run_latency --runs 20 --label none
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from datetime import date
from pathlib import Path
from typing import Dict, List

from eval.dataset import fixed_sample
from eval.report import RAW_DIR, REPORT_DIR
from eval.run_cards import AI_URL, QNA_TYPES, eval_lecture_number

LATENCY_EXPERIMENT = "E0"
METRICS = ["질문 표시", "첫 답변 조각", "항목 완료", "전체 완료"]


def percentile(values: List[float], ratio: float) -> float:
    """선형 보간 백분위수를 구한다.

    Args:
        values: 값 목록. 비어 있으면 안 됨
        ratio: 0.0~1.0 (예: 0.9는 p90)
    Returns:
        백분위수
    """
    ordered = sorted(values)
    position = (len(ordered) - 1) * ratio
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def item_timings(events: List[tuple]) -> Dict[str, List[float]]:
    """한 요청의 (경과 ms, 이벤트, data) 목록에서 항목별 측정값을 뽑는다.

    Args:
        events: 도착 순서의 (경과 ms, 이벤트 이름, data dict)
    Returns:
        {지표: 항목별 값 목록}. '전체 완료'는 값 하나
    """
    first: Dict[str, Dict[int, float]] = {"question": {}, "answer": {}, "done": {}}
    for elapsed, event, data in events:
        if event in first and data.get("item") not in first[event]:
            first[event][data.get("item")] = elapsed
    return {
        "질문 표시": list(first["question"].values()),
        "첫 답변 조각": list(first["answer"].values()),
        "항목 완료": list(first["done"].values()),
        "전체 완료": [events[-1][0]] if events else [],
    }


async def _measure_once(session, headers: dict, payload: dict) -> List[tuple]:
    started = time.perf_counter()
    events = []
    async with session.post(f"{AI_URL}/qa/generate", json=payload, headers=headers) as res:
        res.raise_for_status()
        buffer = ""
        async for raw in res.content.iter_any():
            buffer += raw.decode("utf-8")
            while "\n\n" in buffer:
                block, buffer = buffer.split("\n\n", 1)
                fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
                if "event" in fields:
                    elapsed = (time.perf_counter() - started) * 1000
                    events.append((elapsed, fields["event"], json.loads(fields.get("data", "{}"))))
    return events


async def measure(runs: int) -> Dict[str, List[float]]:
    """표본 섹션으로 QnA 생성을 차례로 호출해 지표별 값을 모은다. 동시 요청이 시간에 영향을 주지 않도록 한 번에 하나씩 보낸다.

    Args:
        runs: 호출 횟수. QnA 표본 섹션을 앞에서부터 순서대로 사용
    Returns:
        {지표: 값 목록 (ms)}
    """
    import aiohttp
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    headers = {"X-Internal-Api-Key": os.getenv("INTERNAL_API_KEY", "")}
    sections = fixed_sample("qna", "test", 20)[:runs]
    collected: Dict[str, List[float]] = {metric: [] for metric in METRICS}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
        for section in sections:
            payload = {
                "lectureId": eval_lecture_number(LATENCY_EXPERIMENT, section.lecture_id),
                "sectionIndex": section.section_index,
                "sectionSummary": section.summary,
                "questionTypes": QNA_TYPES,
            }
            for metric, values in item_timings(await _measure_once(session, headers, payload)).items():
                collected[metric] += values
    return collected


def main() -> None:
    parser = argparse.ArgumentParser(description="스트리밍 효과 측정")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--label", required=True, help="조건 이름 (예: none, low). 파일 이름에 사용")
    parser.add_argument("--model", default="gpt-6-luna", help="AI 서버 QA 모델 (보고서 기록용)")
    parser.add_argument("--effort", default=None, help="AI 서버 QA 추론 강도 (보고서 기록용)")
    args = parser.parse_args()

    collected = asyncio.run(measure(args.runs))
    name = f"L_{args.label}"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"{name}.json").write_text(json.dumps(collected, indent=2), encoding="utf-8")

    lines = [
        f"# 스트리밍 측정 ({args.label})", "", f"측정일: {date.today().isoformat()}", "", "## 조건", "",
        f"- QA 모델: `{args.model}`", f"- 추론 강도: `{args.effort or args.label}`",
        f"- 요청: QnA 표본 섹션 {args.runs}개, 섹션당 4개 유형 동시 생성, 한 번에 요청 하나",
        "- 시각: AI 서버에 요청을 보낸 순간부터 SSE 이벤트 도착까지 (백엔드 중계·브라우저 표시 제외)",
        "", "## 결과 (ms)", "", "| 지표 | 건수 | 중앙값 | p90 |", "| --- | --- | --- | --- |",
    ]
    for metric in METRICS:
        values = collected[metric]
        if values:
            lines.append(f"| {metric} | {len(values)} | {statistics.median(values):.0f} | {percentile(values, 0.9):.0f} |")
            print(f"{metric}: 중앙값 {statistics.median(values):.0f}ms, p90 {percentile(values, 0.9):.0f}ms ({len(values)}건)")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("보고서:", REPORT_DIR / f"{name}.md")


if __name__ == "__main__":
    main()
