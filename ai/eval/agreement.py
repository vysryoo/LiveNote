"""
사람 판정과 LLM 채점의 일치도

LLM 채점 결과에서 층(검색·추천·QnA)마다 표본을 뽑아 사람이 판정할 CSV를 만들고, 판정이 끝나면 Cohen's κ를 계산한다.
사람이 LLM 판정에 끌려가지 않도록 CSV에는 LLM 판정을 넣지 않고 별도 파일에 둔다.

사용:
    python -m eval.agreement sample E0_retrieval_test E0_qna_test E0_resource_test --per-layer 20
    (eval/data/human_labels.csv의 human 열에 1(관련) 또는 0(무관) 입력)
    python -m eval.agreement score
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from typing import Dict, List, Tuple

from eval.prepare_data import DATA_DIR
from eval.report import RAW_DIR

LABELS_PATH = DATA_DIR / "human_labels.csv"
KEY_PATH = DATA_DIR / "human_labels_key.json"
SAMPLE_SEED = 20261029
CSV_FIELDS = ["id", "layer", "lecture_id", "section_key", "transcript", "summary", "content", "human"]


def cohen_kappa(pairs: List[Tuple[bool, bool]]) -> float:
    """두 판정자의 이진 판정 일치도(Cohen's κ)를 구한다.

    Args:
        pairs: (판정자 A, 판정자 B) 목록
    Returns:
        κ 값. 두 판정자가 모두 한 값만 썼으면 일치율(1.0 또는 0.0)
    Raises:
        ValueError: 판정 쌍이 없는 경우
    """
    if not pairs:
        raise ValueError("판정 쌍이 없음")
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    a_yes = sum(a for a, _ in pairs) / n
    b_yes = sum(b for _, b in pairs) / n
    expected = a_yes * b_yes + (1 - a_yes) * (1 - b_yes)
    if expected == 1:
        return observed
    return (observed - expected) / (1 - expected)


def draw_rows(rows: List[dict], per_layer: int, seed: int = SAMPLE_SEED) -> List[dict]:
    """층마다 같은 수의 판정 행을 무작위로 뽑는다.

    Args:
        rows: LLM 채점 원자료 행
        per_layer: 층당 뽑을 수
        seed: 난수 시드
    Returns:
        뽑은 행 목록
    """
    rng = random.Random(seed)
    by_layer: Dict[str, List[dict]] = {}
    for row in rows:
        by_layer.setdefault(row["layer"], []).append(row)
    picked = []
    for layer in sorted(by_layer):
        candidates = by_layer[layer]
        picked += rng.sample(candidates, min(per_layer, len(candidates)))
    return picked


def sample(raw_names: List[str], per_layer: int) -> int:
    """사람 판정용 CSV와 LLM 판정 정답 파일을 만든다. 이미 있으면 덮어쓰지 않는다.

    Args:
        raw_names: eval/data/results/의 원자료 파일 이름 (확장자 제외)
        per_layer: 층당 표본 수
    Returns:
        뽑은 행 수
    Raises:
        FileExistsError: 판정 CSV가 이미 있는 경우
    """
    if LABELS_PATH.exists():
        raise FileExistsError(f"이미 있음: {LABELS_PATH}")
    rows = []
    for name in raw_names:
        rows += [json.loads(line) for line in (RAW_DIR / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
    picked = draw_rows(rows, per_layer)
    key = {}
    with LABELS_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for index, row in enumerate(picked, 1):
            row_id = f"h{index:03d}"
            key[row_id] = row["relevant"]
            writer.writerow({**{k: row.get(k, "") for k in CSV_FIELDS}, "id": row_id, "human": ""})
    KEY_PATH.write_text(json.dumps(key, indent=2), encoding="utf-8")
    return len(picked)


def score() -> dict:
    """사람 판정이 입력된 CSV와 LLM 판정을 비교한다.

    Returns:
        층별·전체 {"items", "agreement", "kappa", "llm_positive", "human_positive"}
    Raises:
        ValueError: human 열에 0·1이 아닌 값이 있는 경우
    """
    key = json.loads(KEY_PATH.read_text(encoding="utf-8"))
    pairs: Dict[str, List[Tuple[bool, bool]]] = {}
    with LABELS_PATH.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            value = row["human"].strip()
            if value == "":
                continue
            if value not in ("0", "1"):
                raise ValueError(f"{row['id']}: human 값은 0 또는 1이어야 함 ({value})")
            pair = (key[row["id"]], value == "1")
            pairs.setdefault(row["layer"], []).append(pair)
            pairs.setdefault("전체", []).append(pair)
    result = {}
    for group, group_pairs in pairs.items():
        n = len(group_pairs)
        result[group] = {
            "items": n,
            "agreement": round(sum(a == b for a, b in group_pairs) / n, 3),
            "kappa": round(cohen_kappa(group_pairs), 3),
            "llm_positive": round(sum(a for a, _ in group_pairs) / n, 3),
            "human_positive": round(sum(b for _, b in group_pairs) / n, 3),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="사람 판정과 LLM 채점 일치도")
    sub = parser.add_subparsers(dest="command", required=True)
    sample_parser = sub.add_parser("sample")
    sample_parser.add_argument("raw_names", nargs="+")
    sample_parser.add_argument("--per-layer", type=int, default=20)
    sub.add_parser("score")
    args = parser.parse_args()
    if args.command == "sample":
        print(f"{sample(args.raw_names, args.per_layer)}건 → {LABELS_PATH}")
    else:
        for group, values in score().items():
            print(group, json.dumps(values, ensure_ascii=False))


if __name__ == "__main__":
    main()
