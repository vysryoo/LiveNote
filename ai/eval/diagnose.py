"""
분할 방식별 문맥 단절 진단

- cuts: 평가 전용 벡터 DB에 저장된 조각마다 시작·끝이 문장 중간인지 판정해 끊긴 조각 비율을 구하고,
  검색 원자료가 있으면 끊긴 조각과 온전한 조각의 관련 판정 비율을 비교한다
- context: 추천 원자료와 같은 섹션의 검색 원자료(상위 2개)를 이어, 검색 문맥의 관련 개수별 추천 Precision@k를 구한다

문장 기준은 semantic 분할과 같은 split_sentences(줄바꿈·글머리표·문장 끝)다.
조각과 문장은 공백을 뺀 글자 위치로 대조한다. 정규화한 조각 텍스트와 PDF 원문은 공백만 다르기 때문이다.
semantic 조각은 문장을 묶어 만들므로 끊긴 조각이 정의상 없다.

context의 검색 문맥은 근사다. AI 서버가 추천에 실제로 쓴 조각은 응답에 없으므로,
같은 분할 방식·같은 섹션 요약으로 검색한 run_retrieval 결과의 상위 2개(서비스 rec_retrieve_top_k)를 쓴다.

비용: 없음 (저장된 벡터 DB 조각과 원자료만 읽음)

사용:
    python -m eval.diagnose cuts --experiments E0 E1 E2 --split test
    python -m eval.diagnose context --resource E14_resource_test --retrieval E2_retrieval_test
"""
from __future__ import annotations

import argparse
import bisect
import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

from eval.dataset import SPLITS, lecture_dir, lecture_ids
from eval.report import REPORT_DIR, load_raw, summarize, write_report
from eval.run_retrieval import CHROMA_DIR, collection_name

DEFAULT_K = 4
CONTEXT_TOP_K = 2
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class Skeleton:
    """공백을 뺀 문서 텍스트와 그 안의 문장 구간 [시작, 끝)."""

    text: str
    spans: List[Tuple[int, int]]

    def is_inside_sentence(self, position: int) -> bool:
        """위치가 어떤 문장의 첫 글자 뒤·마지막 글자 앞, 즉 문장 중간인지 판별한다.

        Args:
            position: 공백을 뺀 텍스트 안의 글자 경계 위치
        Returns:
            문장 중간이면 True
        """
        index = bisect.bisect_right(self.spans, (position, len(self.text) + 1)) - 1
        return index >= 0 and self.spans[index][0] < position < self.spans[index][1]


def strip_whitespace(text: str) -> str:
    """공백 문자를 모두 지운다.

    Args:
        text: 원문
    Returns:
        공백을 지운 텍스트
    """
    return WHITESPACE_PATTERN.sub("", text)


def build_skeletons(pages) -> List[Skeleton]:
    """PDF 쪽 원문으로 조각 위치를 찾을 기준 텍스트 두 개를 만든다.

    page·fixed·recursive 조각은 원문을 이어 붙인 텍스트에서 그대로 찾을 수 있고,
    semantic 조각은 글머리표를 뺀 문장을 이어 만들기 때문에 문장만 이어 붙인 텍스트에서 찾을 수 있다.

    Args:
        pages: 쪽 원문 목록 (rag.splitters.PageText)
    Returns:
        [원문 기준, 문장 기준]
    """
    from rag.splitters.recursive import join_pages
    from rag.splitters.semantic import split_sentences

    sentences = [strip_whitespace(s.text) for s in split_sentences(pages)]
    sentences = [s for s in sentences if s]
    raw = strip_whitespace(join_pages(pages)[0])
    raw_spans, cursor = [], 0
    for sentence in sentences:
        start = raw.find(sentence, cursor)
        if start < 0:
            continue
        raw_spans.append((start, start + len(sentence)))
        cursor = start + len(sentence)
    joined_spans, offset = [], 0
    for sentence in sentences:
        joined_spans.append((offset, offset + len(sentence)))
        offset += len(sentence)
    return [Skeleton(raw, raw_spans), Skeleton("".join(sentences), joined_spans)]


def find_cuts(chunk_texts: Sequence[str], skeletons: Sequence[Skeleton]) -> List[Optional[bool]]:
    """조각마다 시작이나 끝이 문장 중간인지 판정한다.

    Args:
        chunk_texts: 문서 순서(chunk_index 순)의 조각 텍스트
        skeletons: build_skeletons() 결과
    Returns:
        조각별 끊김 여부. 기준 텍스트에서 위치를 찾지 못한 조각은 None
    """
    cuts: List[Optional[bool]] = []
    hints = [0] * len(skeletons)
    for text in chunk_texts:
        target = strip_whitespace(text)
        cut: Optional[bool] = None
        for i, skeleton in enumerate(skeletons):
            # 겹침이 있는 방식은 다음 조각이 이전 조각 끝보다 앞에서 시작하므로 이전 조각 시작 위치부터 찾음
            start = skeleton.text.find(target, hints[i])
            if start < 0:
                start = skeleton.text.find(target)
            if target and start >= 0:
                hints[i] = start + 1
                cut = skeleton.is_inside_sentence(start) or skeleton.is_inside_sentence(start + len(target))
                break
        cuts.append(cut)
    return cuts


def chunk_key(lecture_id: str, chunk_id: str) -> str:
    """강의마다 겹치지 않는 조각 키를 만든다.

    Args:
        lecture_id: 강의ID
        chunk_id: 벡터 DB 조각 ID
    Returns:
        "강의ID|조각 ID"
    """
    return f"{lecture_id}|{chunk_id}"


def collection_cuts(experiment: str, lecture_id: str) -> Tuple[Dict[str, Optional[bool]], Dict[str, int], str]:
    """평가 전용 벡터 DB에 저장된 강의 자료 조각의 끊김 여부를 구한다.

    Args:
        experiment: run_retrieval 실험 이름
        lecture_id: 강의ID
    Returns:
        ({"강의ID|조각 ID": 끊김 여부}, {"강의ID|조각 ID": 글자 수}, 분할 방식). 예전 형식 조각 ID는 강의마다 같아 강의ID를 붙임
    Raises:
        chromadb.errors.NotFoundError: 해당 실험·강의 컬렉션이 없는 경우
    """
    import chromadb

    from rag.pdf import load_pdf_pages

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    stored = client.get_collection(collection_name(experiment, lecture_id)).get(include=["documents", "metadatas"])
    # 리팩토링 전에 저장한 page 컬렉션(E0 등)은 chunk_index·strategy 없이 page만 있음
    order = sorted(range(len(stored["ids"])), key=lambda i: stored["metadatas"][i].get("chunk_index", stored["metadatas"][i].get("page", 0)))
    ids = [chunk_key(lecture_id, stored["ids"][i]) for i in order]
    texts = [stored["documents"][i] for i in order]
    skeletons = build_skeletons(load_pdf_pages(str(lecture_dir(lecture_id) / "material.pdf")))
    strategy = stored["metadatas"][order[0]].get("strategy", "-") if order else "-"
    return dict(zip(ids, find_cuts(texts, skeletons))), {i: len(t) for i, t in zip(ids, texts)}, strategy


def cut_judgments(rows: List[dict], cuts: Dict[str, Optional[bool]]) -> Dict[str, dict]:
    """검색 판정을 끊긴 조각과 온전한 조각으로 나눠 관련 비율을 구한다.

    Args:
        rows: 검색 원자료. 각 행에 lecture_id, chunk_id, relevant
        cuts: {"강의ID|조각 ID": 끊김 여부}
    Returns:
        {"끊긴 조각" | "온전한 조각": {"items", "relevant"}}. 위치를 찾지 못한 조각의 판정은 뺌
    """
    groups = {"끊긴 조각": {"items": 0, "relevant": 0}, "온전한 조각": {"items": 0, "relevant": 0}}
    for row in rows:
        cut = cuts.get(chunk_key(row["lecture_id"], row["chunk_id"]))
        if cut is None:
            continue
        group = groups["끊긴 조각" if cut else "온전한 조각"]
        group["items"] += 1
        group["relevant"] += int(bool(row["relevant"]))
    return groups


def label_context(resource_rows: List[dict], retrieval_rows: List[dict], top_k: int = CONTEXT_TOP_K) -> List[dict]:
    """추천 판정 행마다 같은 섹션 검색 상위 top_k개 중 관련 개수를 붙인다.

    Args:
        resource_rows: 추천 원자료
        retrieval_rows: 같은 분할 방식의 검색 원자료
        top_k: 추천 요청에 들어가는 강의 자료 조각 수
    Returns:
        "context" 열('관련 문맥 N/top_k')을 붙인 추천 원자료. 검색 원자료에 없는 섹션은 뺌
    """
    relevant_counts: Dict[str, int] = {}
    for row in retrieval_rows:
        if row["rank"] <= top_k:
            relevant_counts[row["section_key"]] = relevant_counts.get(row["section_key"], 0) + int(bool(row["relevant"]))
    return [
        {**row, "context": f"관련 문맥 {relevant_counts[row['section_key']]}/{top_k}"}
        for row in resource_rows
        if row["section_key"] in relevant_counts
    ]


def _ratio(count: int, total: int) -> str:
    return f"{count / total * 100:.1f}%" if total else "-"


def run_cuts(experiments: List[str], split: str) -> None:
    lines = [
        f"# 분할 방식별 문맥 단절 ({split})", "", f"측정일: {date.today().isoformat()}", "", "## 조건", "",
        f"- 실험: `{', '.join(experiments)}`", f"- 강의: `{', '.join(lecture_ids(split))}`",
        "- 문장 기준: `split_sentences` (줄바꿈·글머리표·문장 끝)",
        "- 끊긴 조각: 시작이나 끝이 문장 중간인 조각",
        "- page·semantic은 정의상 0% (문장 기준이 쪽 안에서만 나뉘고, semantic은 문장을 묶어 만듦)",
        "", "## 저장된 조각", "", "| 실험 | 분할 방식 | 조각 | 평균 글자 | 끊긴 조각 | 위치 못 찾음 |", "| --- | --- | --- | --- | --- | --- |",
    ]
    judged_lines = [
        "", "## 검색 판정 (끊김 여부별 관련 비율)", "",
        "| 실험 | 끊긴 조각 판정 | 끊긴 조각 관련 | 온전한 조각 판정 | 온전한 조각 관련 |", "| --- | --- | --- | --- | --- |",
    ]
    for experiment in experiments:
        cuts: Dict[str, Optional[bool]] = {}
        sizes: Dict[str, int] = {}
        strategies = set()
        for lecture_id in lecture_ids(split):
            lecture_cuts, lecture_sizes, strategy = collection_cuts(experiment, lecture_id)
            cuts.update(lecture_cuts)
            sizes.update(lecture_sizes)
            strategies.add(strategy)
        found = [c for c in cuts.values() if c is not None]
        lines.append(
            f"| {experiment} | {', '.join(sorted(strategies))} | {len(cuts)} | {sum(sizes.values()) / max(len(sizes), 1):.0f} "
            f"| {_ratio(sum(found), len(found))} | {len(cuts) - len(found)} |"
        )
        print(f"{experiment}: 조각 {len(cuts)}개, 끊긴 조각 {_ratio(sum(found), len(found))}, 위치 못 찾음 {len(cuts) - len(found)}")
        try:
            rows = load_raw(f"{experiment}_retrieval_{split}")
        except FileNotFoundError:
            continue
        groups = cut_judgments(rows, cuts)
        cut, whole = groups["끊긴 조각"], groups["온전한 조각"]
        judged_lines.append(
            f"| {experiment} | {cut['items']} | {_ratio(cut['relevant'], cut['items'])} "
            f"| {whole['items']} | {_ratio(whole['relevant'], whole['items'])} |"
        )
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"B_cuts_{split}.md"
    path.write_text("\n".join(lines + judged_lines) + "\n", encoding="utf-8")
    print("보고서:", path)


def run_context(resource: str, retrieval: str, k: int) -> None:
    rows = label_context(load_raw(resource), load_raw(retrieval))
    summary = summarize(rows, k)
    by_context = summarize(rows, k, group_key="context")
    settings = {
        "추천 원자료": resource,
        "검색 원자료": retrieval,
        "검색 문맥": f"검색 상위 {CONTEXT_TOP_K}개 중 관련 판정 개수 (같은 분할·같은 요약으로 다시 검색한 근사)",
    }
    path = write_report(
        f"B_context_{resource}", f"{resource} 검색 문맥별 추천 Precision@{k}", settings, summary, k, extra={"검색 문맥별": by_context}
    )
    for group, values in by_context.items():
        print(f"{group}: {values['precision'] * 100:.1f}% ({values['sections']}섹션)")
    print("보고서:", path)


def main() -> None:
    parser = argparse.ArgumentParser(description="분할 방식별 문맥 단절 진단")
    commands = parser.add_subparsers(dest="command", required=True)
    cuts = commands.add_parser("cuts", help="끊긴 조각 비율과 끊김 여부별 검색 관련 비율")
    cuts.add_argument("--experiments", nargs="+", required=True, help="run_retrieval 실험 이름 (예: E0 E2)")
    cuts.add_argument("--split", default="test", choices=SPLITS)
    context = commands.add_parser("context", help="검색 문맥 관련 개수별 추천 Precision@k")
    context.add_argument("--resource", required=True, help="추천 원자료 이름 (예: E14_resource_test)")
    context.add_argument("--retrieval", required=True, help="같은 분할 방식의 검색 원자료 이름 (예: E2_retrieval_test)")
    context.add_argument("--k", type=int, default=DEFAULT_K)
    args = parser.parse_args()

    if args.command == "cuts":
        run_cuts(args.experiments, args.split)
    else:
        run_context(args.resource, args.retrieval, args.k)


if __name__ == "__main__":
    main()
