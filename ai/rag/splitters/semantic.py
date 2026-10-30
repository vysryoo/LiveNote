"""의미 단위 분할 (Semantic Chunking).

LangChain SemanticChunker(langchain-experimental, 2026-05 지원 종료)와 같은 방식으로 경계를 정하고,
슬라이드용 문장 분리, 크기 보정, 문장 겹침을 더한다.

1. 줄바꿈·글머리표·문장 끝으로 문장을 나눈다
2. 문장마다 앞뒤 1문장을 붙인 묶음을 임베딩한다
3. 이웃 묶음의 코사인 거리가 문서 안 거리 분포의 백분위수 기준을 넘는 곳에서 자른다
4. 최소 토큰보다 짧은 조각은 이웃과 합치고, 최대 토큰보다 긴 조각은 문장 단위로 다시 나눈다
5. 각 조각 앞에 이전 조각의 마지막 문장 N개를 붙인다
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence

import numpy as np
from langchain_text_splitters import TextSplitter

from .base import Chunk, ChunkSettings, PageText, count_tokens, normalize

BULLET_PATTERN = re.compile(r"^\s*(?:[*\-•▪◦·]|\d+[.)])\s+")
SENTENCE_END_PATTERN = re.compile(r"(?<=[.?!])\s+")
LINE_END_PATTERN = re.compile(r"[.?!:]\s*$")
# PDF는 긴 문장을 쪽 너비에서 줄바꿈해 저장하므로, 문단이 있는 쪽(가장 긴 줄이 이 이상)에서
# 가장 긴 줄의 일정 비율 이상 찬 줄은 문장이 이어지는 것으로 봄
WRAP_PAGE_MIN_CHARS = 55
WRAP_LINE_RATIO = 0.75


@dataclass(frozen=True)
class Sentence:
    """분할 단위 문장과 해당 쪽."""

    text: str
    page: int


def join_wrapped_lines(lines: Sequence[str]) -> List[str]:
    """PDF 줄바꿈으로 끊긴 문장 줄을 다시 잇는다.

    Args:
        lines: 쪽 원문의 줄 목록
    Returns:
        이어 붙인 줄 목록
    """
    lengths = [len(line.strip()) for line in lines]
    longest = max(lengths, default=0)
    if longest < WRAP_PAGE_MIN_CHARS:
        return [line for line in lines if line.strip()]
    joined: List[str] = []
    carry = ""
    for line, length in zip(lines, lengths):
        if not line.strip():
            continue
        carry = f"{carry} {line.strip()}" if carry else line.strip()
        if length < longest * WRAP_LINE_RATIO or LINE_END_PATTERN.search(line):
            joined.append(carry)
            carry = ""
    if carry:
        joined.append(carry)
    return joined


def split_sentences(pages: Sequence[PageText]) -> List[Sentence]:
    """쪽 원문을 문장 목록으로 나눈다. 줄바꿈과 글머리표도 문장 경계로 본다.

    슬라이드는 마침표 없는 글머리표 항목이 대부분이라 문장 끝만으로 나누면 한 장 전체가 한 문장이 되기 때문이다.
    PDF 줄바꿈으로 끊긴 문단 줄은 먼저 잇는다.

    Args:
        pages: 쪽 원문 목록
    Returns:
        문장 목록 (빈 문장 제외)
    """
    sentences: List[Sentence] = []
    for page in pages:
        for line in join_wrapped_lines(page.text.splitlines()):
            line = BULLET_PATTERN.sub("", line).strip()
            for part in SENTENCE_END_PATTERN.split(line):
                part = normalize(part)
                if part:
                    sentences.append(Sentence(text=part, page=page.page))
    return sentences


def cosine_distances(vectors: Sequence[Sequence[float]]) -> List[float]:
    """이웃한 벡터 사이 코사인 거리(1 - 코사인 유사도)를 구한다.

    Args:
        vectors: 벡터 목록
    Returns:
        길이 len(vectors) - 1의 거리 목록
    """
    matrix = np.asarray(vectors, dtype=float)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    unit = matrix / np.where(norms == 0, 1, norms)
    return list(1.0 - np.sum(unit[:-1] * unit[1:], axis=1))


def breakpoints(distances: Sequence[float], percentile: float) -> List[int]:
    """거리가 백분위수 기준을 넘는 위치를 경계로 고른다.

    Args:
        distances: 이웃 거리 목록. i번째 값은 문장 i와 i+1 사이
        percentile: 0~100. 높을수록 경계가 적음
    Returns:
        경계 위치 목록. 값 i는 문장 i 뒤에서 자른다는 뜻
    """
    if not distances:
        return []
    threshold = float(np.percentile(distances, percentile))
    return [i for i, distance in enumerate(distances) if distance > threshold]


def group_by_breakpoints(count: int, cuts: Sequence[int]) -> List[List[int]]:
    """문장 인덱스를 경계 위치로 묶는다.

    Args:
        count: 문장 수
        cuts: 경계 위치 (문장 i 뒤에서 자름)
    Returns:
        묶음별 문장 인덱스 목록
    """
    groups, start = [], 0
    for cut in sorted(cuts):
        groups.append(list(range(start, cut + 1)))
        start = cut + 1
    if start < count:
        groups.append(list(range(start, count)))
    return [g for g in groups if g]


def fit_sizes(groups: List[List[int]], tokens: Sequence[int], min_tokens: int, max_tokens: int) -> List[List[int]]:
    """짧은 묶음은 다음 묶음과 합치고(마지막이면 이전과), 긴 묶음은 문장 단위로 다시 나눈다.

    Args:
        groups: 묶음별 문장 인덱스
        tokens: 문장별 토큰 수
        min_tokens: 최소 토큰
        max_tokens: 최대 토큰. 문장 하나가 이보다 길면 그 문장만 따로 둠
    Returns:
        보정한 묶음 목록
    """
    merged: List[List[int]] = []
    for group in groups:
        if merged and sum(tokens[i] for i in merged[-1]) < min_tokens:
            merged[-1] = merged[-1] + group
        else:
            merged.append(list(group))
    if len(merged) > 1 and sum(tokens[i] for i in merged[-1]) < min_tokens:
        last = merged.pop()
        merged[-1] = merged[-1] + last

    fitted: List[List[int]] = []
    for group in merged:
        current: List[int] = []
        for index in group:
            if current and sum(tokens[i] for i in current) + tokens[index] > max_tokens:
                fitted.append(current)
                current = []
            current.append(index)
        if current:
            fitted.append(current)
    return fitted


class SemanticSplitter(TextSplitter):
    """이웃 문장 묶음의 임베딩 거리로 주제 전환 지점을 찾아 자르는 분할기."""

    def __init__(self, embeddings, settings: ChunkSettings, **kwargs) -> None:
        """분할기를 만든다.

        Args:
            embeddings: LangChain Embeddings (embed_documents 제공)
            settings: semantic_* 기준값
            **kwargs: TextSplitter 기본 인자
        """
        super().__init__(**kwargs)
        self._embeddings = embeddings
        self._settings = settings

    def split_text(self, text: str) -> List[str]:
        """텍스트 하나를 조각 텍스트 목록으로 나눈다.

        Args:
            text: 원문
        Returns:
            조각 텍스트 목록
        """
        return [chunk.text for chunk in self.split_pages([PageText(page=0, text=text)])]

    def split_pages(self, pages: Sequence[PageText]) -> List[Chunk]:
        """쪽 원문 목록을 조각으로 나누고 쪽 범위를 기록한다.

        Args:
            pages: 쪽 원문 목록
        Returns:
            조각 목록
        """
        sentences = split_sentences(pages)
        if not sentences:
            return []
        texts = [s.text for s in sentences]
        windows = [" ".join(texts[max(i - 1, 0):i + 2]) for i in range(len(texts))]
        vectors = self._embeddings.embed_documents(windows) if len(windows) > 1 else []
        cuts = breakpoints(cosine_distances(vectors), self._settings.semantic_percentile) if vectors else []
        groups = fit_sizes(
            group_by_breakpoints(len(sentences), cuts),
            [count_tokens(t) for t in texts],
            self._settings.semantic_min_tokens,
            self._settings.semantic_max_tokens,
        )
        overlap = self._settings.semantic_overlap_sentences
        chunks: List[Chunk] = []
        for number, group in enumerate(groups):
            prefix = []
            if overlap and number > 0:
                prefix = groups[number - 1][-overlap:]
            body = " ".join(texts[i] for i in prefix + group)
            chunks.append(Chunk(
                text=body,
                page_start=sentences[group[0]].page,
                page_end=sentences[group[-1]].page,
                index=number,
            ))
        return chunks


def split_semantic(pages: List[PageText], settings: ChunkSettings, embeddings) -> List[Chunk]:
    """의미 단위로 분할한다.

    Args:
        pages: 쪽 원문 목록
        settings: semantic_* 기준값
        embeddings: LangChain Embeddings
    Returns:
        조각 목록
    """
    return SemanticSplitter(embeddings, settings).split_pages(pages)
