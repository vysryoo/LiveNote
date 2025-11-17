"""Configuration for RAG service."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _default_persist_dir() -> str:
    return os.getenv("RAG_PERSIST_DIR", "server_storage/chroma_data")


def _default_embedding_model() -> str:
    return os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-large")


def _default_api_key() -> str | None:
    return os.getenv("RAG_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")


@dataclass
class RAGConfig:
    """Configuration for RAG service."""
    
    persist_dir: str = field(default_factory=_default_persist_dir)
    embedding_model: str = field(default_factory=_default_embedding_model)
    openai_api_key: str | None = field(default_factory=_default_api_key)
    
    def __post_init__(self):
        """Ensure persist_dir exists."""
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
