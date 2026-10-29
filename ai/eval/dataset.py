"""
평가 데이터 읽기와 표본 추출

강의별 meta.json·sections.json과 dev/test 구분(splits.json)을 읽고, 실험에 쓸 섹션 표본을 고정한다.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from eval.prepare_data import DATA_DIR, INBOX_DIR

SPLITS_PATH = DATA_DIR / "splits.json"
SAMPLES_PATH = DATA_DIR / "samples.json"
SAMPLE_SEED = 20261029


@dataclass(frozen=True)
class Section:
    """평가 단위가 되는 강의 섹션."""

    lecture_id: str
    field: str
    section_index: int
    transcript: str
    summary: str
    style: str = ""
    subject: str = ""

    @property
    def key(self) -> str:
        return f"{self.lecture_id}#{self.section_index}"


def lecture_ids(split: str) -> List[str]:
    """dev 또는 test에 속한 강의ID 목록을 돌려준다.

    Args:
        split: 'dev' 또는 'test'
    Returns:
        강의ID 목록
    """
    return json.loads(SPLITS_PATH.read_text(encoding="utf-8"))[split]


def lecture_dir(lecture_id: str) -> Path:
    """강의 데이터 폴더 경로를 돌려준다.

    Args:
        lecture_id: 강의ID
    Returns:
        inbox/{강의ID} 경로
    """
    return INBOX_DIR / lecture_id


def load_sections(lecture_id: str) -> List[Section]:
    """강의 하나의 확정 요약 섹션을 읽는다.

    Args:
        lecture_id: 강의ID
    Returns:
        섹션 목록. section_index 순서
    """
    folder = lecture_dir(lecture_id)
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    collected = json.loads((folder / "sections.json").read_text(encoding="utf-8"))
    return [
        Section(
            lecture_id=lecture_id,
            field=meta["field"],
            style=meta.get("material_style", ""),
            subject=meta.get("subject", ""),
            section_index=s["section_index"],
            transcript=s["transcript"],
            summary=s["summary"],
        )
        for s in collected["sections"]
    ]


def split_sections(split: str) -> List[Section]:
    """dev 또는 test 전체 섹션을 읽는다.

    Args:
        split: 'dev' 또는 'test'
    Returns:
        섹션 목록. 강의 순서, 강의 안에서는 section_index 순서
    """
    return [section for lecture_id in lecture_ids(split) for section in load_sections(lecture_id)]


def draw_sample(sections: List[Section], per_field: int, seed: int) -> List[Section]:
    """분야마다 같은 수의 섹션을 무작위로 뽑는다.

    Args:
        sections: 후보 섹션 목록
        per_field: 분야당 뽑을 수. 후보가 적으면 전부
        seed: 난수 시드
    Returns:
        뽑은 섹션 목록. 원래 순서 유지
    """
    rng = random.Random(seed)
    by_field: Dict[str, List[Section]] = {}
    for section in sections:
        by_field.setdefault(section.field, []).append(section)
    chosen = set()
    for field in sorted(by_field):
        candidates = by_field[field]
        chosen.update(s.key for s in rng.sample(candidates, min(per_field, len(candidates))))
    return [s for s in sections if s.key in chosen]


def fixed_sample(name: str, split: str, per_field: int) -> List[Section]:
    """실험 사이에 같은 표본을 쓰도록 처음 뽑은 표본을 samples.json에 저장하고 재사용한다.

    Args:
        name: 표본 이름 (예: 'qna', 'resource')
        split: 'dev' 또는 'test'
        per_field: 분야당 섹션 수
    Returns:
        표본 섹션 목록
    """
    sections = split_sections(split)
    saved = json.loads(SAMPLES_PATH.read_text(encoding="utf-8")) if SAMPLES_PATH.exists() else {}
    sample_id = f"{name}:{split}:{per_field}"
    if sample_id not in saved:
        saved[sample_id] = [s.key for s in draw_sample(sections, per_field, SAMPLE_SEED + len(name))]
        SAMPLES_PATH.write_text(json.dumps(saved, ensure_ascii=False, indent=2), encoding="utf-8")
    keys = set(saved[sample_id])
    return [s for s in sections if s.key in keys]
