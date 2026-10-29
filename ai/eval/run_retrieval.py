"""
검색 단계 Precision@k 측정

강의 자료 PDF를 분할 방식별로 평가 전용 벡터 DB에 저장하고, 섹션 요약으로 검색한 상위 k개 조각을 채점한다.
분할 방식의 효과를 다른 단계(검색어 생성, 후보 검증 등)와 떼어 보는 층이다.

비용: PDF·질의 임베딩(text-embedding-3-large)과 채점(gpt-6.1-terra). 이미 저장한 컬렉션과 채점 결과는 재사용한다.

사용:
    python -m eval.run_retrieval --experiment E0 --strategy page --split test
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Callable, Dict, List

from eval.dataset import Section, lecture_dir, split_sections
from eval.judge import judge_rows, judge_settings
from eval.prepare_data import DATA_DIR
from eval.report import save_raw, summarize, write_report

CHROMA_DIR = DATA_DIR / ".chroma"
DEFAULT_K = 4


def _index_page(rag, collection_id: str, pdf_path: Path) -> None:
    rag.upsert_pdf(collection_id, str(pdf_path))


# 분할 방식별 PDF 저장 함수. P6에서 recursive, semantic 추가
INDEXERS: Dict[str, Callable] = {"page": _index_page}


def collection_name(experiment: str, lecture_id: str) -> str:
    """실험·강의별 평가 전용 컬렉션 이름을 만든다.

    Args:
        experiment: 실험 이름 (예: E0)
        lecture_id: 강의ID
    Returns:
        Chroma 컬렉션 이름
    """
    return f"eval_{experiment.lower()}_{lecture_id}"


def _ensure_index(rag, experiment: str, strategy: str, lecture_id: str) -> str:
    collection_id = collection_name(experiment, lecture_id)
    store = rag.vector_store
    existing = {c if isinstance(c, str) else c.name for c in store.client.list_collections()}
    if collection_id not in existing or store.client.get_collection(collection_id).count() == 0:
        INDEXERS[strategy](rag, collection_id, lecture_dir(lecture_id) / "material.pdf")
    return collection_id


def retrieve_rows(experiment: str, strategy: str, sections: List[Section], k: int) -> List[dict]:
    """섹션마다 상위 k개 조각을 검색해 채점 전 원자료 행을 만든다.

    Args:
        experiment: 실험 이름
        strategy: 분할 방식 (INDEXERS 키)
        sections: 평가할 섹션 목록
        k: 검색 개수
    Returns:
        원자료 행 목록 (relevant, reason은 채점 후 채움)
    """
    from dotenv import load_dotenv

    from rag.ragkit.config import RAGConfig
    from rag.ragkit.service import RAGService

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    rag = RAGService(RAGConfig(persist_dir=str(CHROMA_DIR)))
    collections = {lid: _ensure_index(rag, experiment, strategy, lid) for lid in {s.lecture_id for s in sections}}
    rows = []
    for section in sections:
        chunks = rag.retrieve(collections[section.lecture_id], section.summary, top_k=k)
        for rank, chunk in enumerate(chunks, 1):
            rows.append({
                "experiment": experiment,
                "layer": "retrieval",
                "lecture_id": section.lecture_id,
                "field": section.field,
                "section_key": section.key,
                "rank": rank,
                "chunk_id": chunk.id,
                "score": round(chunk.score, 4),
                "content": chunk.text,
                "transcript": section.transcript,
                "summary": section.summary,
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="검색 단계 Precision@k 측정")
    parser.add_argument("--experiment", required=True, help="실험 이름 (예: E0)")
    parser.add_argument("--strategy", required=True, choices=sorted(INDEXERS))
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--lectures", nargs="*", help="일부 강의만 측정 (확인용)")
    parser.add_argument("--max-sections", type=int, help="강의당 섹션 수 제한 (확인용)")
    args = parser.parse_args()

    sections = split_sections(args.split)
    if args.lectures:
        sections = [s for s in sections if s.lecture_id in args.lectures]
    if args.max_sections:
        kept: Dict[str, int] = {}
        filtered = []
        for s in sections:
            kept[s.lecture_id] = kept.get(s.lecture_id, 0) + 1
            if kept[s.lecture_id] <= args.max_sections:
                filtered.append(s)
        sections = filtered

    rows = asyncio.run(judge_rows(retrieve_rows(args.experiment, args.strategy, sections, args.k)))
    name = f"{args.experiment}_retrieval_{args.split}"
    if args.lectures or args.max_sections:
        name += "_partial"
    raw_path = save_raw(name, rows)
    summary = summarize(rows, args.k)
    settings = {
        "실험": args.experiment,
        "분할 방식": args.strategy,
        "데이터": f"{args.split} ({', '.join(sorted({s.lecture_id for s in sections}))})",
        "검색 질의": "섹션 확정 요약",
        "검색 대상": "강의 자료 PDF 조각만 (섹션 요약 제외)",
        **judge_settings(),
    }
    report_path = write_report(name, f"{args.experiment} 검색 단계 Precision@{args.k}", settings, summary, args.k)
    for group, values in summary.items():
        print(f"{group}: {values['precision'] * 100:.1f}% ±{(values['ci95'] or 0) * 100:.1f}%p ({values['sections']}섹션)")
    print("원자료:", raw_path)
    print("보고서:", report_path)


if __name__ == "__main__":
    main()
