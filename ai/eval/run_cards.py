"""
카드(QnA·추천 자료) Precision@4 측정

AI 서버 API를 직접 호출해 표본 섹션마다 QnA 4개(개념·응용·비교·심화)와 추천 자료 4종(논문·위키·영상·블로그)을 만들고 채점한다.
사용자가 실제로 받는 결과의 정확도를 보는 층이다.

- 강의 자료는 실험마다 별도 강의 번호로 /rag/pdf-upsert에 올린다. 분할 방식은 AI 서버 설정을 따르므로 실험 조건에 맞춰 서버를 띄운다
- 벡터 DB에는 강의 자료만 넣고 섹션 요약은 넣지 않는다. 직전 섹션 요약 3개는 서비스와 같이 previousSummaries로 보낸다
- 이전 QnA와 제외 목록은 보내지 않는다 (섹션마다 독립 측정)

비용: AI 서버의 생성 모델 호출, YouTube 검색(섹션당 100단위), 채점(gpt-6.1-terra)

사용:
    python -m eval.run_cards --experiment E0 --strategy page --layers qna resource
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import quote
from typing import Dict, List

from eval.dataset import Section, fixed_sample, lecture_dir, load_sections
from eval.judge import judge_rows, judge_settings
from eval.report import save_raw, summarize, write_report

AI_URL = os.getenv("EVAL_AI_URL", "http://localhost:8003")
CALLBACK_PORT = int(os.getenv("EVAL_CALLBACK_PORT", "9911"))
QNA_TYPES = ["CONCEPT", "APPLICATION", "COMPARISON", "ADVANCED"]
RESOURCE_TYPES = ["PAPER", "WIKI", "VIDEO", "BLOG"]
ALL_LECTURES = ["eng-1", "eng-2", "eng-3", "nur-1", "nur-2", "nur-3", "art-1", "art-2", "art-3"]
K = 4
SECTION_CONCURRENCY = 3
RESOURCE_TIMEOUT_SEC = 240
PREVIOUS_SUMMARY_COUNT = 3


def eval_lecture_number(experiment: str, lecture_id: str) -> int:
    """실험·강의마다 겹치지 않는 AI 서버용 강의 번호를 만든다. 실제 강의 번호와 겹치지 않게 900000대를 쓴다.

    Args:
        experiment: 'E' 뒤에 숫자가 붙은 실험 이름 (예: E0)
        lecture_id: 강의ID
    Returns:
        강의 번호
    Raises:
        ValueError: 실험 이름 형식이 맞지 않는 경우
    """
    match = re.fullmatch(r"E(\d{1,2})", experiment)
    if not match:
        raise ValueError(f"실험 이름은 E0~E99 형식이어야 함: {experiment}")
    return 900000 + int(match.group(1)) * 100 + ALL_LECTURES.index(lecture_id)


def previous_summaries(section: Section) -> List[dict]:
    """서비스처럼 직전 섹션 요약 최대 3개를 만든다.

    Args:
        section: 현재 섹션
    Returns:
        [{sectionIndex, summary}] 목록. 오래된 것부터
    """
    earlier = [s for s in load_sections(section.lecture_id) if s.section_index < section.section_index]
    return [{"sectionIndex": s.section_index, "summary": s.summary} for s in earlier[-PREVIOUS_SUMMARY_COUNT:]]


def parse_sse(body: str) -> List[dict]:
    """SSE 응답 본문을 이벤트 목록으로 바꾼다.

    Args:
        body: text/event-stream 본문
    Returns:
        [{"event", "data"}] 목록
    """
    events = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        if "event" in fields and "data" in fields:
            events.append({"event": fields["event"], "data": json.loads(fields["data"])})
    return events


def qna_content(question: str, answer: str) -> str:
    """채점에 넘길 QnA 본문을 만든다.

    Args:
        question: 질문
        answer: 답변
    Returns:
        채점 본문
    """
    return f"질문: {question}\n답변: {answer}"


def resource_content(resource: dict) -> str:
    """채점에 넘길 추천 자료 본문을 만든다. 서비스가 붙인 추천 이유는 채점에 영향을 주지 않도록 넣지 않는다.

    Args:
        resource: 콜백으로 받은 자료 (type, title, description, url)
    Returns:
        채점 본문
    """
    return (
        f"종류: {resource.get('type')}\n제목: {resource.get('title')}\n"
        f"설명: {resource.get('description') or ''}\n주소: {resource.get('url')}"
    )


def _base_row(experiment: str, layer: str, section: Section, rank: int, content: str) -> dict:
    return {
        "experiment": experiment,
        "layer": layer,
        "lecture_id": section.lecture_id,
        "field": section.field,
        "section_key": section.key,
        "rank": rank,
        "content": content,
        "transcript": section.transcript,
        "summary": section.summary,
    }


async def _upsert_pdfs(session, headers: dict, experiment: str, lecture_ids: List[str]) -> None:
    import aiohttp

    for lecture_id in lecture_ids:
        form = aiohttp.FormData()
        form.add_field("lecture_id", str(eval_lecture_number(experiment, lecture_id)))
        pdf = lecture_dir(lecture_id) / "material.pdf"
        form.add_field("file", pdf.read_bytes(), filename=pdf.name, content_type="application/pdf")
        async with session.post(f"{AI_URL}/rag/pdf-upsert", data=form, headers=headers) as res:
            res.raise_for_status()
            result = (await res.json())["result"]
            print(f"{lecture_id}: 강의 자료 저장 {result.get('count')}개 조각")


async def _run_qna(session, headers: dict, experiment: str, section: Section) -> List[dict]:
    payload = {
        "lectureId": eval_lecture_number(experiment, section.lecture_id),
        "sectionIndex": section.section_index,
        "sectionSummary": section.summary,
        # 실제 백엔드처럼 강의 과목을 함께 보냄
        "subject": section.subject or None,
        "questionTypes": QNA_TYPES,
    }
    async with session.post(f"{AI_URL}/qa/generate", json=payload, headers=headers) as res:
        res.raise_for_status()
        events = parse_sse(await res.text())
    done = sorted((e["data"] for e in events if e["event"] == "done"), key=lambda d: d["item"])
    return [
        {**_base_row(experiment, "qna", section, d["item"] + 1, qna_content(d["question"], d["answer"])), "type": d["type"]}
        for d in done
    ]


async def _run_resources(session, headers: dict, experiment: str, section: Section, inbox: Dict[str, asyncio.Queue]) -> List[dict]:
    key = f"{experiment}:{section.key}"
    queue = inbox.setdefault(key, asyncio.Queue())
    payload = {
        "lectureId": eval_lecture_number(experiment, section.lecture_id),
        "sectionIndex": section.section_index,
        "sectionSummary": section.summary,
        # 섹션 키의 '#'이 URL 조각 구분자로 해석되지 않도록 인코딩
        "callbackUrl": f"http://127.0.0.1:{CALLBACK_PORT}/callback?key={quote(key, safe='')}",
        "previousSummaries": previous_summaries(section),
        "resourceTypes": RESOURCE_TYPES,
    }
    async with session.post(f"{AI_URL}/rec/recommend", json=payload, headers=headers) as res:
        res.raise_for_status()
    resources: List[dict] = []
    for _ in RESOURCE_TYPES:
        try:
            resources += await asyncio.wait_for(queue.get(), timeout=RESOURCE_TIMEOUT_SEC)
        except asyncio.TimeoutError:
            print(f"{section.key}: 추천 콜백 시간 초과")
            break
    resources.sort(key=lambda r: RESOURCE_TYPES.index(r["type"]) if r.get("type") in RESOURCE_TYPES else len(RESOURCE_TYPES))
    return [
        {**_base_row(experiment, "resource", section, rank, resource_content(r)), "type": r.get("type"), "url": r.get("url")}
        for rank, r in enumerate(resources, 1)
    ]


async def _start_callback_server(inbox: Dict[str, asyncio.Queue]):
    from aiohttp import web

    async def handle(request):
        body = await request.json()
        inbox.setdefault(request.query["key"], asyncio.Queue()).put_nowait(body.get("resources") or [])
        return web.json_response({})

    app = web.Application()
    app.router.add_post("/callback", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", CALLBACK_PORT).start()
    return runner


async def generate_rows(experiment: str, layers: List[str], qna_sections: List[Section], resource_sections: List[Section]) -> List[dict]:
    """AI 서버에서 카드를 만들어 채점 전 원자료 행을 만든다.

    Args:
        experiment: 실험 이름
        layers: 'qna', 'resource' 중 측정할 층
        qna_sections: QnA 표본 섹션
        resource_sections: 추천 자료 표본 섹션
    Returns:
        원자료 행 목록
    """
    import aiohttp
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    headers = {"X-Internal-Api-Key": os.getenv("INTERNAL_API_KEY", "")}
    inbox: Dict[str, asyncio.Queue] = {}
    runner = await _start_callback_server(inbox)
    semaphore = asyncio.Semaphore(SECTION_CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=600)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            lectures = sorted({s.lecture_id for s in qna_sections + resource_sections})
            await _upsert_pdfs(session, headers, experiment, lectures)

            async def limited(coro):
                async with semaphore:
                    return await coro

            tasks = []
            if "qna" in layers:
                tasks += [limited(_run_qna(session, headers, experiment, s)) for s in qna_sections]
            if "resource" in layers:
                tasks += [limited(_run_resources(session, headers, experiment, s, inbox)) for s in resource_sections]
            results = await asyncio.gather(*tasks)
    finally:
        await runner.cleanup()
    return [row for rows in results for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="카드(QnA·추천 자료) Precision@4 측정")
    parser.add_argument("--experiment", required=True, help="실험 이름 (예: E0)")
    parser.add_argument("--strategy", required=True, help="AI 서버의 분할 방식 (보고서 기록용)")
    parser.add_argument("--layers", nargs="+", default=["qna", "resource"], choices=["qna", "resource"])
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    parser.add_argument("--qna-per-field", type=int, default=20)
    parser.add_argument("--resource-per-field", type=int, default=10)
    parser.add_argument("--model", default=os.getenv("EVAL_SERVICE_MODEL", "gpt-6-luna"), help="AI 서버 생성 모델 (보고서 기록용)")
    args = parser.parse_args()

    qna_sections = fixed_sample("qna", args.split, args.qna_per_field)
    resource_sections = fixed_sample("resource", args.split, args.resource_per_field)
    rows = asyncio.run(generate_rows(args.experiment, args.layers, qna_sections, resource_sections))
    rows = asyncio.run(judge_rows(rows))

    for layer in args.layers:
        layer_rows = [r for r in rows if r["layer"] == layer]
        name = f"{args.experiment}_{layer}_{args.split}"
        raw_path = save_raw(name, layer_rows)
        sections = qna_sections if layer == "qna" else resource_sections
        per_field = args.qna_per_field if layer == "qna" else args.resource_per_field
        # 생성에 모두 실패해 행이 없는 섹션도 분모에 들어가도록 무관 판정 1건으로 채움 (Precision 0)
        produced = {r["section_key"] for r in layer_rows}
        missing = [s.key for s in sections if s.key not in produced]
        summary = summarize(layer_rows + [
            {"section_key": key, "field": next(s.field for s in sections if s.key == key), "rank": 1, "relevant": False}
            for key in missing
        ], K)
        settings = {
            "실험": args.experiment,
            "분할 방식": args.strategy,
            "생성 모델": args.model,
            "데이터": f"{args.split}, {len(sections)}섹션 (분야당 최대 {per_field})",
            "생성 실패 섹션": len(missing),
            "QnA 과목 정보 전달": "예" if layer == "qna" else "-",
            **judge_settings(),
        }
        title = "QnA" if layer == "qna" else "추천 자료"
        report_path = write_report(name, f"{args.experiment} {title} Precision@{K}", settings, summary, K)
        print(f"[{title}]")
        for group, values in summary.items():
            print(f"  {group}: {values['precision'] * 100:.1f}% ±{(values['ci95'] or 0) * 100:.1f}%p ({values['sections']}섹션)")
        print("  원자료:", raw_path)
        print("  보고서:", report_path)


if __name__ == "__main__":
    main()
