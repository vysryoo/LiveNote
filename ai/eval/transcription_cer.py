"""
전사 정확도 비교 (글자 오류율, CER)

TTS로 녹음을 만든 원문(script.txt)을 정답으로 보고, 서비스가 받은 전사와의 글자 오류율을 구한다.
공백·문장부호·슬라이드 표시는 빼고 비교한다. 영문 약어를 한글로 받아 적은 경우(예: pn → 피엔)도
오류로 세므로, 값은 모델 사이의 상대 비교에 쓴다.

비용: 없음 (이미 수집한 전사 파일만 읽음)

사용:
    python -m eval.transcription_cer --label gpt-4o-transcribe=sections.json \\
        --label gpt-transcribe=sections_gpt-transcribe.json eng-2 nur-1 art-2
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
from datetime import date
from typing import Dict, List, Tuple

from rapidfuzz.distance import Levenshtein

from eval.prepare_data import INBOX_DIR, MARKER_PATTERN
from eval.report import REPORT_DIR

# 한글·영문·숫자만 남김
KEEP_PATTERN = re.compile(r"[^0-9a-z가-힣]")
LATIN_OR_DIGIT = re.compile(r"[a-z0-9]")


def normalize(text: str) -> str:
    """비교용으로 소문자로 바꾸고 한글·영문·숫자 외 문자를 지운다.

    Args:
        text: 원문
    Returns:
        정리한 문자열
    """
    return KEEP_PATTERN.sub("", text.lower())


def load_reference(lecture_id: str) -> str:
    """원문 스크립트에서 슬라이드(쪽) 표시 줄을 빼고 읽는다.

    Args:
        lecture_id: 강의ID
    Returns:
        원문
    """
    lines = (INBOX_DIR / lecture_id / "script.txt").read_text(encoding="utf-8").splitlines()
    return " ".join(line for line in lines if not MARKER_PATTERN.match(line.strip()))


def load_hypothesis(lecture_id: str, file_name: str) -> str:
    """수집한 파일의 전사를 시간 순서로 이어 붙인다.

    Args:
        lecture_id: 강의ID
        file_name: inbox/{강의ID}/ 아래 수집 결과 파일 이름
    Returns:
        전사
    """
    collected = json.loads((INBOX_DIR / lecture_id / file_name).read_text(encoding="utf-8"))
    return " ".join(t["text"] or "" for t in collected["transcripts"])


def cer(reference: str, hypothesis: str) -> Tuple[float, int, int]:
    """글자 오류율을 구한다.

    Args:
        reference: 정답
        hypothesis: 전사
    Returns:
        (오류율, 편집 거리, 정답 글자 수). 정리 후 기준
    """
    ref, hyp = normalize(reference), normalize(hypothesis)
    distance = Levenshtein.distance(ref, hyp)
    return distance / len(ref), distance, len(ref)


def cer_without_notation(reference: str, hypothesis: str) -> float:
    """영문·숫자가 섞인 차이 구간을 뺀 글자 오류율을 구한다.

    원문은 TTS용이라 영문 용어·숫자를 한글로 적었고(예: 헤모다이알리시스, 백), 전사는 영문·숫자로
    적기도 한다(hemodialysis, 100). 이런 표기 차이를 오류에서 빼고 본다.

    Args:
        reference: 정답
        hypothesis: 전사
    Returns:
        오류율. 정리 후 정답 글자 수 기준
    """
    ref, hyp = normalize(reference), normalize(hypothesis)
    errors = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_opcodes():
        if tag != "equal" and not LATIN_OR_DIGIT.search(ref[i1:i2] + hyp[j1:j2]):
            errors += max(i2 - i1, j2 - j1)
    return errors / len(ref)


def main() -> None:
    parser = argparse.ArgumentParser(description="전사 글자 오류율 비교")
    parser.add_argument("lecture_ids", nargs="+")
    parser.add_argument("--label", action="append", required=True, help="이름=파일 (예: gpt-transcribe=sections_x.json)")
    parser.add_argument("--name", default="T_transcription", help="보고서 파일 이름")
    args = parser.parse_args()

    labels = [tuple(item.split("=", 1)) for item in args.label]
    rows: Dict[str, Dict[str, Tuple[float, int, int]]] = {}
    strict: Dict[str, Dict[str, Tuple[float, int]]] = {}
    for lecture_id in args.lecture_ids:
        reference = load_reference(lecture_id)
        hypotheses = {label: load_hypothesis(lecture_id, file) for label, file in labels}
        rows[lecture_id] = {label: cer(reference, text) for label, text in hypotheses.items()}
        strict[lecture_id] = {
            label: (cer_without_notation(reference, text), len(normalize(reference))) for label, text in hypotheses.items()
        }

    lines = [f"# 전사 글자 오류율 (CER)", "", f"측정일: {date.today().isoformat()}", "", "## 조건", ""]
    lines += [
        "- 정답: TTS 녹음에 쓴 원문 스크립트 (`script.txt`, 슬라이드 표시 제외)",
        "- 비교 전 소문자로 바꾸고 한글·영문·숫자 외 문자(공백, 문장부호) 제거",
        "- 영문 약어를 한글로 받아 적은 경우 등 표기 차이도 오류로 셈",
        "- 녹음은 백엔드 실시간 전사 WebSocket에 실제 속도로 전송",
        "",
        "## 결과",
        "",
        "| 강의 | " + " | ".join(label for label, _ in labels) + " |",
        "| --- | " + " | ".join("---" for _ in labels) + " |",
    ]
    totals = {label: [0, 0] for label, _ in labels}
    for lecture_id, by_label in rows.items():
        cells = []
        for label, _ in labels:
            rate, distance, length = by_label[label]
            totals[label][0] += distance
            totals[label][1] += length
            cells.append(f"{rate * 100:.2f}%")
        lines.append(f"| {lecture_id} | " + " | ".join(cells) + " |")
    lines.append("| 전체 | " + " | ".join(f"{d / n * 100:.2f}%" for d, n in totals.values()) + " |")

    lines += [
        "",
        "## 결과 (영문·숫자가 섞인 차이 구간 제외)",
        "",
        "원문은 영문 용어·숫자를 한글로 적었고 전사는 영문·숫자로 적기도 해서, 그런 표기 차이를 뺀 값",
        "",
        "| 강의 | " + " | ".join(label for label, _ in labels) + " |",
        "| --- | " + " | ".join("---" for _ in labels) + " |",
    ]
    strict_totals = {label: [0.0, 0] for label, _ in labels}
    for lecture_id, by_label in strict.items():
        cells = []
        for label, _ in labels:
            rate, length = by_label[label]
            strict_totals[label][0] += rate * length
            strict_totals[label][1] += length
            cells.append(f"{rate * 100:.2f}%")
        lines.append(f"| {lecture_id} | " + " | ".join(cells) + " |")
    lines.append("| 전체 | " + " | ".join(f"{e / n * 100:.2f}%" for e, n in strict_totals.values()) + " |")

    path = REPORT_DIR / f"{args.name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[lines.index("## 결과"):]))
    print("보고서:", path)


if __name__ == "__main__":
    main()
