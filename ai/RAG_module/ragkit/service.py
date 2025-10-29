"""RAG Service - High-level API for RAG operations."""

import logging
from pathlib import Path
from typing import List, Dict, Any

from ragkit.config import RAGConfig
from ragkit.embeddings.openai import OpenAIEmbeddingService
from ragkit.models import UpsertItem, RetrieveFilters, RetrievedChunk
from ragkit.utils.pdf import load_pdf_pages
from ragkit.utils.text import make_id, normalize_text
from ragkit.vectordb.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)


class RAGService:
    """High-level service for RAG operations.
    
    This service provides a clean interface for:
    - Upserting text documents
    - Upserting PDF files (auto page-split)
    - Retrieving relevant chunks
    
    Example:
        >>> from ragkit import RAGService, RAGConfig
        >>> config = RAGConfig()
        >>> service = RAGService(config)
        >>> 
        >>> # Upsert text
        >>> result = service.upsert_text("my_collection", [
        ...     UpsertItem(text="Hello world", metadata={"source": "test"})
        ... ])
        >>> print(result)
        {'collection_id': 'my_collection', 'count': 1, 'embedding_dim': 3072}
        >>> 
        >>> # Retrieve
        >>> chunks = service.retrieve("my_collection", "greeting", top_k=3)
        >>> print(chunks[0].text)
        'Hello world'
    """
    
    def __init__(self, config: RAGConfig | None = None):
        """Initialize RAG service.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        self.config = config or RAGConfig()
        
        # Initialize embedding service
        self.embedding_service = OpenAIEmbeddingService(
            model=self.config.embedding_model,
            api_key=self.config.openai_api_key
        )
        
        # Initialize vector store
        self.vector_store = ChromaVectorStore(
            persist_dir=self.config.persist_dir
        )
        
        logger.info("RAGService initialized")
    
    def upsert_text(
        self,
        collection_id: str,
        items: List[UpsertItem] | List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Upsert text items into a collection.
        
        Args:
            collection_id: Target collection identifier
            items: List of UpsertItem objects or dicts with 'text' field
            
        Returns:
            Dict with collection_id, count, and embedding_dim
            
        Example:
            >>> result = service.upsert_text("lectures", [
            ...     UpsertItem(
            ...         text="Vector databases store embeddings",
            ...         metadata={"subject": "CS", "timestamp": 1234567890}
            ...     ),
            ...     {"text": "RAG combines retrieval and generation"}
            ... ])
            >>> print(f"Upserted {result['count']} items")
            Upserted 2 items
        """
        if not items:
            logger.warning("No items to upsert")
            return {"collection_id": collection_id, "count": 0, "embedding_dim": 0}
        
        # Convert dicts to UpsertItem if needed
        upsert_items = []
        for item in items:
            if isinstance(item, dict):
                upsert_items.append(UpsertItem(**item))
            else:
                upsert_items.append(item)
        
        # Create collection if needed
        self.vector_store.create_collection(collection_id)
        
        # Prepare data for upserting
        ids = []
        texts = []
        metadatas = []
        
        for item in upsert_items:
            # Generate ID if not provided
            if item.id:
                doc_id = item.id
            else:
                doc_id = make_id(item.text)
            
            ids.append(doc_id)
            texts.append(item.text)
            
            # Merge section_id into metadata
            metadata = dict(item.metadata)
            if item.section_id:
                metadata["section_id"] = item.section_id
            
            metadatas.append(metadata)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Upsert to vector store
        count = self.vector_store.upsert_many(
            collection_id=collection_id,
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        
        embedding_dim = len(embeddings[0]) if embeddings else 0
        
        logger.info(
            f"[Upsert] collection={collection_id} count={count} dim={embedding_dim}"
        )
        
        return {
            "collection_id": collection_id,
            "count": count,
            "embedding_dim": embedding_dim,
        }
    
    def upsert_pdf(
        self,
        collection_id: str,
        pdf_path: str,
        base_metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Upsert PDF file with automatic page splitting.
        
        Args:
            collection_id: Target collection identifier
            pdf_path: Path to PDF file
            base_metadata: Optional metadata to add to all pages
            
        Returns:
            Dict with collection_id, count, and embedding_dim
            
        Example:
            >>> result = service.upsert_pdf(
            ...     "lectures",
            ...     "lecture_01.pdf",
            ...     base_metadata={"subject": "Computer Science", "year": 2025}
            ... )
            >>> print(f"Upserted {result['count']} pages")
            Upserted 15 pages
        """
        # Load PDF pages
        documents = load_pdf_pages(pdf_path)
        
        if not documents:
            logger.warning(f"No pages loaded from {pdf_path}")
            return {"collection_id": collection_id, "count": 0, "embedding_dim": 0}
        
        # Create collection if needed
        self.vector_store.create_collection(collection_id)
        
        # Prepare data
        ids = []
        texts = []
        metadatas = []
        
        source_name = Path(pdf_path).name
        base_name = Path(pdf_path).stem
        
        for doc in documents:
            page_num = doc.metadata.get("page", 0)
            
            # Create deterministic ID: {basename}|p{page_num}
            doc_id = f"{base_name}|p{page_num}"
            ids.append(doc_id)
            
            # Normalize text
            text = normalize_text(doc.page_content)
            texts.append(text)
            
            # Merge metadata
            metadata = dict(doc.metadata)
            metadata["source"] = source_name
            
            if base_metadata:
                metadata.update(base_metadata)
            
            metadatas.append(metadata)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} PDF pages")
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Upsert to vector store
        count = self.vector_store.upsert_many(
            collection_id=collection_id,
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        
        embedding_dim = len(embeddings[0]) if embeddings else 0
        
        logger.info(
            f"[Upsert PDF] collection={collection_id} count={count} dim={embedding_dim}"
        )
        
        return {
            "collection_id": collection_id,
            "count": count,
            "embedding_dim": embedding_dim,
        }
    
    def retrieve(
        self,
        collection_id: str,
        query: str,
        top_k: int = 5,
        filters: RetrieveFilters | None = None,
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks from a collection.
        
        Args:
            collection_id: Collection to query
            query: Query text
            top_k: Number of results to return
            filters: Optional filters
            
        Returns:
            List of RetrievedChunk objects, sorted by score (descending)
            
        Example:
            >>> chunks = service.retrieve(
            ...     "lectures",
            ...     "What is a vector database?",
            ...     top_k=3,
            ...     filters=RetrieveFilters(subject="Computer Science")
            ... )
            >>> for chunk in chunks:
            ...     print(f"{chunk.score:.2f}: {chunk.text[:50]}...")
            0.92: Vector databases store and query high-dimensional...
        """
        # Generate query embedding
        logger.info(f"Generating query embedding for: '{query[:50]}...'")
        query_embedding = self.embedding_service.embed_query(query)
        
        # Build where clause from filters
        where = None
        if filters:
            where = {}
            
            if filters.subject:
                where["subject"] = filters.subject
            
            if filters.section_id:
                where["section_id"] = filters.section_id
            
            # Note: Chroma's where clause has limited support for numeric comparisons
            # For min/max timestamp, we filter in-memory after retrieval
            
            # Add custom filters
            if filters.custom:
                where.update(filters.custom)
            
            # If no filters were added, set to None
            if not where:
                where = None
        
        # Query vector store
        results = self.vector_store.query(
            collection_id=collection_id,
            query_embedding=query_embedding,
            top_k=top_k,
            where=where,
        )
        
        # Convert to RetrievedChunk objects
        chunks = []
        for result in results:
            metadata = result["metadata"]
            
            # Apply timestamp filters if needed
            if filters:
                if filters.min_timestamp is not None:
                    ts = metadata.get("timestamp")
                    if ts is not None and ts < filters.min_timestamp:
                        continue
                
                if filters.max_timestamp is not None:
                    ts = metadata.get("timestamp")
                    if ts is not None and ts > filters.max_timestamp:
                        continue
            
            chunk = RetrievedChunk(
                id=result["id"],
                text=result["text"],
                score=result["score"],
                metadata=metadata,
                section_id=metadata.get("section_id"),
            )
            chunks.append(chunk)
        
        # Sort by score descending
        chunks.sort(key=lambda c: c.score, reverse=True)
        
        # Take top_k after filtering
        chunks = chunks[:top_k]
        
        logger.info(
            f"[Retrieve] q='{query[:30]}...' -> "
            f"ids={[c.id for c in chunks[:3]]} "
            f"scores={[round(c.score, 2) for c in chunks[:3]]}"
        )
        
        return chunks
