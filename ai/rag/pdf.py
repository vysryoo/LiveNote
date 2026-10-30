"""
PDF 쪽 텍스트 읽기
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from pypdf import PdfReader

from .splitters import PageText

logger = logging.getLogger(__name__)


def load_pdf_pages(pdf_path: str) -> List[PageText]:
    """PDF를 쪽 단위 텍스트로 읽는다. 텍스트가 없는 쪽은 건너뛴다.

    Args:
        pdf_path: PDF 경로
    Returns:
        쪽 원문 목록. 쪽 번호는 0부터
    Raises:
        ValueError: 파일이 없거나 PDF가 아니거나 읽지 못한 경우
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise ValueError(f"PDF 파일 없음: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"PDF 파일이 아님: {pdf_path}")

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ValueError(f"PDF 읽기 실패: {exc}") from exc

    pages: List[PageText] = []
    for number, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
        except Exception as exc:
            logger.warning("쪽 텍스트 추출 실패 (page=%d): %s", number, exc)
            continue
        if text.strip():
            pages.append(PageText(page=number, text=text))
    logger.info("PDF 읽기: %s, %d쪽", path.name, len(pages))
    return pages
