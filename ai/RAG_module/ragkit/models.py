"""Data models for RAG operations."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UpsertItem:
    """Item to be upserted into the vector database.
    
    Attributes:
        text: The text content to embed and store
        id: Optional unique identifier (auto-generated if None)
        metadata: Optional metadata dict
        section_id: Optional section identifier for grouping
        
    Example:
        >>> item = UpsertItem(
        ...     text="Vector databases are efficient",
        ...     metadata={"source": "lecture", "page": 5},
        ...     section_id="intro"
        ... )
    """
    
    text: str
    id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    section_id: str | None = None


@dataclass
class RetrieveFilters:
    """Filters for retrieval queries.
    
    Attributes:
        subject: Filter by subject metadata field
        section_id: Filter by section_id
        min_timestamp: Filter by minimum timestamp (ISO format or unix timestamp)
        max_timestamp: Filter by maximum timestamp
        custom: Additional custom filters as key-value pairs
        
    Example:
        >>> filters = RetrieveFilters(
        ...     subject="computer science",
        ...     min_timestamp=1609459200
        ... )
    """
    
    subject: str | None = None
    section_id: str | None = None
    min_timestamp: int | str | None = None
    max_timestamp: int | str | None = None
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    """A retrieved chunk from the vector database.
    
    Attributes:
        id: Unique identifier of the chunk
        text: The text content
        score: Similarity score (higher is more similar)
        metadata: Associated metadata
        section_id: Section identifier if available
        
    Example:
        >>> chunk = RetrievedChunk(
        ...     id="doc1|p1",
        ...     text="RAG combines retrieval and generation",
        ...     score=0.92,
        ...     metadata={"source": "paper.pdf", "page": 1}
        ... )
    """
    
    id: str
    text: str
    score: float
    metadata: dict[str, Any]
    section_id: str | None = None
