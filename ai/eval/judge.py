"""
LLM 채점

평가 대상 하나가 섹션과 관련 있는지를 이진(관련/무관)으로 판정한다. Precision@k 계산에 쓴다.

- 채점 모델은 서비스 생성 모델(gpt-6-luna)과 다른 gpt-6.1-terra. 자기 출력에 후한 경향을 피하기 위함
- 판정 기준표는 대상 종류별로 고정하고 버전을 결과에 남긴다
- 같은 입력의 판정은 캐시해 다시 실행해도 같은 결과와 비용 0을 보장한다
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from core.timing import logger as timing_logger
from eval.prepare_data import DATA_DIR

JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", "gpt-6.1-terra")
JUDGE_REASONING_EFFORT = os.getenv("EVAL_JUDGE_EFFORT", "low")
RUBRIC_VERSION = "v1"
JUDGE_CONCURRENCY = 8
JUDGE_CACHE_DIR = DATA_DIR / ".cache" / "judge"
CONTENT_MAX_CHARS = 1500

SYSTEM_PROMPT = """당신은 대학 강의 보조 서비스가 만든 결과를 평가하는 채점자입니다.
강의의 한 구간(약 30초)의 전사와 요약, 그리고 서비스가 그 구간에 대해 내놓은 평가 대상 하나가 주어집니다.
아래 기준표에 따라 평가 대상이 이 구간과 관련 있는지(relevant) 판정하세요.
판단 근거는 구간 전사를 기준으로 삼고, 확실하지 않으면 relevant=false로 판정합니다.
reason에는 판정 이유를 한국어 한 문장으로 적습니다."""

RUBRICS = {
    "retrieval": (
        "평가 대상: 강의 자료(PDF)에서 검색된 조각.\n"
        "relevant=true: 이 구간에서 설명하는 개념·설명·예시와 같은 내용이거나 직접 이어지는 내용을 담고 있어 구간을 이해하는 데 직접 도움이 됨.\n"
        "relevant=false: 같은 과목이라도 이 구간과 다른 주제만 다룸, 또는 표지·목차처럼 내용이 거의 없음."
    ),
    "resource": (
        "평가 대상: 서비스가 추천한 외부 자료(논문, 위키, 영상, 블로그) 카드.\n"
        "relevant=true: 구간 주제와 직접 관련 있고, 학생이 이 구간을 이해하거나 더 공부하는 데 쓸 만한 자료.\n"
        "relevant=false: 이름만 비슷한 다른 분야·다른 의미의 자료, 이 구간과 연결되지 않을 만큼 일반적인 자료."
    ),
    "qna": (
        "평가 대상: 서비스가 만든 예상 질문과 답변.\n"
        "relevant=true: 질문이 이 구간에서 다룬 내용에서 나왔고, 답변이 질문에 맞게 답하며 사실과 맞음.\n"
        "relevant=false: 구간과 무관한 질문, 사실과 다른 답변, 질문에 답하지 않는 답변."
    ),
}

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "judgment",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {"relevant": {"type": "boolean"}, "reason": {"type": "string"}},
            "required": ["relevant", "reason"],
            "additionalProperties": False,
        },
    },
}


@dataclass(frozen=True)
class JudgeItem:
    """채점할 대상 하나와 기준이 되는 섹션."""

    kind: str
    transcript: str
    summary: str
    content: str


@dataclass(frozen=True)
class Judgment:
    """채점 결과."""

    relevant: bool
    reason: str


def build_user_prompt(item: JudgeItem) -> str:
    """채점 요청 본문을 만든다.

    Args:
        item: 채점 대상
    Returns:
        사용자 메시지 본문
    Raises:
        KeyError: 지원하지 않는 대상 종류인 경우
    """
    return (
        f"[기준표]\n{RUBRICS[item.kind]}\n\n"
        f"[구간 전사]\n{item.transcript}\n\n"
        f"[구간 요약]\n{item.summary}\n\n"
        f"[평가 대상]\n{item.content[:CONTENT_MAX_CHARS]}"
    )


def cache_key(item: JudgeItem) -> str:
    """채점 모델, 기준표 버전, 입력으로 캐시 키를 만든다.

    Args:
        item: 채점 대상
    Returns:
        SHA-256 16진 문자열
    """
    raw = json.dumps(
        [JUDGE_MODEL, JUDGE_REASONING_EFFORT, RUBRIC_VERSION, SYSTEM_PROMPT, build_user_prompt(item)],
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_judgment(content: str) -> Judgment:
    """채점 모델 응답(JSON)을 결과로 바꾼다.

    Args:
        content: 모델 응답 본문
    Returns:
        채점 결과
    Raises:
        ValueError: JSON 형식이 아니거나 relevant 값이 불리언이 아닌 경우
    """
    data = json.loads(content)
    if not isinstance(data.get("relevant"), bool):
        raise ValueError(f"relevant 값이 불리언이 아님: {content[:200]}")
    return Judgment(relevant=data["relevant"], reason=str(data.get("reason", "")))


async def _judge_one(client, item: JudgeItem, semaphore: asyncio.Semaphore) -> Judgment:
    path = JUDGE_CACHE_DIR / f"{cache_key(item)}.json"
    if path.exists():
        return parse_judgment(path.read_text(encoding="utf-8"))
    async with semaphore:
        started = time.perf_counter()
        response = await client.chat.completions.create(
            model=JUDGE_MODEL,
            reasoning_effort=JUDGE_REASONING_EFFORT,
            response_format=RESPONSE_FORMAT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(item)},
            ],
        )
    _log_usage(response, (time.perf_counter() - started) * 1000)
    content = response.choices[0].message.content or ""
    judgment = parse_judgment(content)
    JUDGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return judgment


def _log_usage(response, elapsed_ms: float) -> None:
    usage = getattr(response, "usage", None)
    details = getattr(usage, "completion_tokens_details", None)
    record = {
        "event": "llm",
        "purpose": "judge",
        "model": JUDGE_MODEL,
        "elapsed_ms": round(elapsed_ms, 1),
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "reasoning_tokens": getattr(details, "reasoning_tokens", 0) or 0,
    }
    timing_logger.info(json.dumps(record, ensure_ascii=False))


async def judge_items(items: List[JudgeItem]) -> List[Judgment]:
    """여러 대상을 동시에 채점한다. 캐시에 있는 대상은 요청하지 않는다.

    Args:
        items: 채점 대상 목록
    Returns:
        입력 순서와 같은 채점 결과 목록
    """
    from dotenv import load_dotenv
    from openai import AsyncOpenAI

    from core.logs import setup_logging

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    setup_logging()
    semaphore = asyncio.Semaphore(JUDGE_CONCURRENCY)
    async with AsyncOpenAI(timeout=120.0, max_retries=3) as client:
        return list(await asyncio.gather(*[_judge_one(client, item, semaphore) for item in items]))


async def judge_rows(rows: List[dict]) -> List[dict]:
    """원자료 행을 채점해 relevant, reason을 채운다.

    Args:
        rows: kind에 맞는 layer, transcript, summary, content가 있는 행 목록
    Returns:
        같은 행 목록 (채점 결과 포함)
    """
    items = [JudgeItem(kind=r["layer"], transcript=r["transcript"], summary=r["summary"], content=r["content"]) for r in rows]
    for row, judgment in zip(rows, await judge_items(items)):
        row["relevant"] = judgment.relevant
        row["reason"] = judgment.reason
    return rows


def judge_settings() -> dict:
    """보고서에 남길 채점 설정을 돌려준다.

    Returns:
        {"채점 모델", "채점 추론 강도", "채점 기준표 버전"}
    """
    return {"채점 모델": JUDGE_MODEL, "채점 추론 강도": JUDGE_REASONING_EFFORT, "채점 기준표 버전": RUBRIC_VERSION}
