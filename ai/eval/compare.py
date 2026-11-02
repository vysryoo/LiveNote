"""
두 실험의 Precision@k 차이와 짝지은 부트스트랩 95% 구간

같은 섹션끼리 짝지어 섹션별 Precision@k 차이를 구하고, 섹션을 복원추출로 다시 뽑아 평균 차이의 분포를 만든다.
같은 섹션은 두 조건에서 같은 요약과 같은 채점 기준을 쓰므로 섹션마다 다른 난이도가 차이에서 상쇄된다.
한쪽 원자료에만 있는 섹션(결과가 하나도 없던 섹션 등)은 짝이 없어 빼고, 보고서에 개수를 남긴다.

비용: 없음 (저장된 원자료만 읽음)

사용:
    python -m eval.compare E0_retrieval_test E2_retrieval_test
"""
from __future__ import annotations

import argparse
import random
from collections import defaultdict
from datetime import date
from typing import Dict, List

from eval.dataset import SAMPLE_SEED
from eval.report import REPORT_DIR, load_raw, precision_at_k
from eval.run_latency import percentile

DEFAULT_K = 4
BOOTSTRAP_ROUNDS = 10000


def section_precisions(rows: List[dict], k: int) -> Dict[str, float]:
    """원자료를 섹션별 Precision@k로 바꾼다.

    Args:
        rows: 판정 원자료. 각 행에 section_key, rank, relevant
        k: 기준 개수
    Returns:
        {section_key: Precision@k}
    """
    by_section: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        by_section[row["section_key"]].append(row)
    return {
        key: precision_at_k([r["relevant"] for r in sorted(section_rows, key=lambda r: r["rank"])], k)
        for key, section_rows in by_section.items()
    }


def paired_bootstrap(
    before: Dict[str, float], after: Dict[str, float], rounds: int = BOOTSTRAP_ROUNDS, seed: int = SAMPLE_SEED
) -> dict:
    """짝지은 섹션의 평균 차이(after - before)와 부트스트랩 95% 구간을 구한다.

    Args:
        before: 기준 조건의 {section_key: 값}
        after: 비교 조건의 {section_key: 값}
        rounds: 다시 뽑는 횟수
        seed: 난수 시드. 같으면 같은 구간이 나옴
    Returns:
        {"sections", "before", "after", "diff", "ci_low", "ci_high", "only_before", "only_after"}. 값은 0.0~1.0 비율
    Raises:
        ValueError: 짝지을 섹션이 없는 경우
    """
    keys = sorted(before.keys() & after.keys())
    if not keys:
        raise ValueError("두 원자료에 공통 섹션이 없음")
    diffs = [after[key] - before[key] for key in keys]
    rng = random.Random(seed)
    means = [sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(rounds)]
    return {
        "sections": len(keys),
        "before": sum(before[key] for key in keys) / len(keys),
        "after": sum(after[key] for key in keys) / len(keys),
        "diff": sum(diffs) / len(diffs),
        "ci_low": percentile(means, 0.025),
        "ci_high": percentile(means, 0.975),
        "only_before": len(before.keys() - after.keys()),
        "only_after": len(after.keys() - before.keys()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="두 실험의 Precision@k 차이 (짝지은 부트스트랩)")
    parser.add_argument("before", help="기준 원자료 이름 (예: E0_retrieval_test)")
    parser.add_argument("after", help="비교 원자료 이름 (예: E2_retrieval_test)")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    args = parser.parse_args()

    result = paired_bootstrap(
        section_precisions(load_raw(args.before), args.k), section_precisions(load_raw(args.after), args.k)
    )
    name = f"C_{args.before}_vs_{args.after}"
    lines = [
        f"# {args.before} → {args.after} Precision@{args.k} 차이", "", f"측정일: {date.today().isoformat()}", "", "## 조건", "",
        f"- 기준: `{args.before}`", f"- 비교: `{args.after}`",
        f"- 방법: 같은 섹션끼리 짝지은 부트스트랩 {BOOTSTRAP_ROUNDS:,}회, 시드 `{SAMPLE_SEED}`",
        f"- 짝지은 섹션: `{result['sections']}` (기준에만 있음 `{result['only_before']}`, 비교에만 있음 `{result['only_after']}`)",
        "", "## 결과", "", "| 기준 | 비교 | 차이 | 95% 구간 |", "| --- | --- | --- | --- |",
        f"| {result['before'] * 100:.1f}% | {result['after'] * 100:.1f}% | {result['diff'] * 100:+.1f}%p "
        f"| [{result['ci_low'] * 100:+.1f}, {result['ci_high'] * 100:+.1f}] |",
    ]
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"{name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"{result['before'] * 100:.1f}% → {result['after'] * 100:.1f}% ({result['diff'] * 100:+.1f}%p, "
        f"95% [{result['ci_low'] * 100:+.1f}, {result['ci_high'] * 100:+.1f}], {result['sections']}섹션)"
    )
    print("보고서:", path)


if __name__ == "__main__":
    main()
