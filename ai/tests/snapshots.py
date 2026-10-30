"""
스냅샷 비교

리팩토링 전후 결과와 LLM 프롬프트가 같은지 확인하기 위해 기대값을 tests/data/snapshots/*.json에 저장해 두고 비교한다.
기대값을 의도적으로 바꿀 때만 UPDATE_SNAPSHOTS=1로 실행해 다시 저장한다.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SNAPSHOT_DIR = Path(__file__).resolve().parent / "data" / "snapshots"


def assert_snapshot(name: str, actual: Any) -> None:
    """저장된 스냅샷과 비교한다. UPDATE_SNAPSHOTS=1이면 저장만 한다.

    Args:
        name: 스냅샷 파일 이름 (확장자 제외)
        actual: JSON으로 저장할 수 있는 실제 값
    Raises:
        AssertionError: 저장된 값과 다르거나 스냅샷 파일이 없는 경우
    """
    path = SNAPSHOT_DIR / f"{name}.json"
    serialized = json.dumps(actual, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if os.getenv("UPDATE_SNAPSHOTS") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
        return
    assert path.exists(), f"스냅샷 없음: {path}. UPDATE_SNAPSHOTS=1로 먼저 저장"
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert json.loads(serialized) == expected
