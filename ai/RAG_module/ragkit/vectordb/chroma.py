"""Chroma vector store implementation."""

import logging
import time
from typing import Any, List, Dict

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Vector store using Chroma for persistent storage.
    
    Attributes:
        persist_dir: Directory for persistent storage
        client: ChromaDB client instance
        
    Example:
        >>> store = ChromaVectorStore(persist_dir="./chroma_data")
        >>> store.create_collection("my_collection")
        >>> store.upsert_many(
        ...     collection_id="my_collection",
        ...     ids=["id1", "id2"],
        ...     texts=["text1", "text2"],
        ...     embeddings=[[0.1, 0.2], [0.3, 0.4]],
        ...     metadatas=[{"key": "val1"}, {"key": "val2"}]
        ... )
    """
    
    def __init__(self, persist_dir: str = "./chroma_data"):
        """Initialize Chroma vector store.
        
        Args:
            persist_dir: Directory for persistent storage
        """
        self.persist_dir = persist_dir
        
        # Create persistent client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        logger.info(f"Initialized ChromaVectorStore with persist_dir: {persist_dir}")
    
    def create_collection(self, collection_id: str) -> None:
        """Create a new collection or get existing one.
        
        Args:
            collection_id: Unique identifier for the collection
        """
        try:
            self.client.get_or_create_collection(name=collection_id)
            logger.info(f"Collection '{collection_id}' ready")
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_id}': {e}")
            raise
    
    def upsert_many(
        self,
        collection_id: str,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]] | None = None,
    ) -> int:
        """Upsert multiple documents into a collection.
        
        Args:
            collection_id: Target collection identifier
            ids: List of unique document IDs
            texts: List of text contents
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts
            
        Returns:
            Number of documents upserted
        """
        start_time = time.time()
        
        if not ids or len(ids) != len(texts) or len(ids) != len(embeddings):
            raise ValueError("ids, texts, and embeddings must have the same length")
        
        collection = self.client.get_collection(name=collection_id)
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{} for _ in ids]
        
        # Convert all metadata values to supported types
        cleaned_metadatas = []
        for metadata in metadatas:
            cleaned = {}
            for k, v in metadata.items():
                # Chroma supports: str, int, float, bool
                if isinstance(v, (str, int, float, bool)):
                    cleaned[k] = v
                else:
                    # Convert to string for other types
                    cleaned[k] = str(v)
            cleaned_metadatas.append(cleaned)
        
        try:
            collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=cleaned_metadatas,
            )
            
            elapsed = time.time() - start_time
            logger.info(
                f"Upserted {len(ids)} documents to '{collection_id}' in {elapsed:.2f}s"
            )
            
            return len(ids)
            
        except Exception as e:
            logger.error(f"Failed to upsert to '{collection_id}': {e}")
            raise
    
    def query(
        self,
        collection_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        where: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """Query the collection for similar documents.
        
        Args:
            collection_id: Collection to query
            query_embedding: Query vector
            top_k: Number of results to return
            where: Optional filter conditions
            
        Returns:
            List of results with id, text, score, and metadata
        """
        start_time = time.time()
        
        collection = self.client.get_collection(name=collection_id)
        
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert Chroma results to our format
            output = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # Chroma returns distances (lower is better)
                    # Convert to similarity score (higher is better)
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = 1.0 / (1.0 + distance)  # Convert distance to similarity
                    
                    output.append({
                        "id": doc_id,
                        "text": results["documents"][0][i],
                        "score": score,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    })
            
            elapsed = time.time() - start_time
            logger.debug(f"Query returned {len(output)} results in {elapsed:.2f}s")
            
            return output
            
        except Exception as e:
            logger.error(f"Failed to query '{collection_id}': {e}")
            raise
    
    def delete_collection(self, collection_id: str) -> None:
        """Delete a collection.
        
        Args:
            collection_id: Collection to delete
        """
        try:
            self.client.delete_collection(name=collection_id)
            logger.info(f"Deleted collection '{collection_id}'")
        except Exception as e:
            logger.warning(f"Failed to delete collection '{collection_id}': {e}")
    
    def list_collections(self) -> List[str]:
        """List all collection names.
        
        Returns:
            List of collection names
        """
        collections = self.client.list_collections()
        return [c.name for c in collections]
