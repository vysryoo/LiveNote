"""
Precision@k 집계와 보고서 작성

섹션마다 Precision@k(상위 k개 중 관련 판정 비율)를 구하고 분야별·전체 평균을 낸다.
원자료(섹션 내용 포함)는 eval/data/results/에, 집계 보고서는 eval/results/에 저장한다.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List

from eval.prepare_data import DATA_DIR

RAW_DIR = DATA_DIR / "results"
REPORT_DIR = Path(__file__).resolve().parent / "results"


def precision_at_k(labels: List[bool], k: int) -> float:
    """상위 k개 판정에서 관련 비율을 구한다. 결과가 k개보다 적으면 부족분은 무관으로 본다.

    Args:
        labels: 순위 순서의 관련 여부
        k: 기준 개수
    Returns:
        0.0~1.0
    """
    return sum(labels[:k]) / k


def summarize(rows: List[dict], k: int) -> Dict[str, dict]:
    """섹션별 Precision@k를 분야별·전체로 평균낸다.

    Args:
        rows: 판정 원자료. 각 행에 field, section_key, rank, relevant
        k: 기준 개수
    Returns:
        {분야 또는 '전체': {"precision", "sections", "items", "ci95"}}
    """
    by_section: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        by_section[row["section_key"]].append(row)
    groups: Dict[str, List[float]] = defaultdict(list)
    items: Dict[str, int] = defaultdict(int)
    for section_rows in by_section.values():
        section_rows.sort(key=lambda r: r["rank"])
        value = precision_at_k([r["relevant"] for r in section_rows], k)
        for group in (section_rows[0]["field"], "전체"):
            groups[group].append(value)
            items[group] += min(len(section_rows), k)
    summary = {}
    for group, values in groups.items():
        mean = sum(values) / len(values)
        # 판정 단위(섹션 수 × k) 기준 정규 근사 95% 신뢰구간 반폭
        n = len(values) * k
        summary[group] = {
            "precision": round(mean, 4),
            "sections": len(values),
            "items": items[group],
            "ci95": round(1.96 * math.sqrt(mean * (1 - mean) / n), 4) if n else None,
        }
    return dict(sorted(summary.items(), key=lambda kv: (kv[0] == "전체", kv[0])))


def save_raw(name: str, rows: List[dict]) -> Path:
    """판정 원자료를 JSON Lines로 저장한다.

    Args:
        name: 파일 이름 (확장자 제외)
        rows: 판정 원자료
    Returns:
        저장한 경로
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{name}.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return path


def write_report(name: str, title: str, settings: dict, summary: Dict[str, dict], k: int) -> Path:
    """집계 보고서(Markdown)를 저장한다.

    Args:
        name: 파일 이름 (확장자 제외)
        title: 보고서 제목
        settings: 실험 조건 (분할 방식, 모델, 채점 설정 등)
        summary: summarize() 결과
        k: 기준 개수
    Returns:
        저장한 경로
    """
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", "", f"측정일: {date.today().isoformat()}", "", "## 조건", ""]
    lines += [f"- {key}: `{value}`" for key, value in settings.items()]
    lines += ["", f"## Precision@{k}", "", "| 분야 | Precision | 95% 신뢰구간 | 섹션 | 판정 |", "| --- | --- | --- | --- | --- |"]
    for group, values in summary.items():
        ci = f"±{values['ci95'] * 100:.1f}%p" if values["ci95"] is not None else "-"
        lines.append(
            f"| {group} | {values['precision'] * 100:.1f}% | {ci} | {values['sections']} | {values['items']} |"
        )
    path = REPORT_DIR / f"{name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
