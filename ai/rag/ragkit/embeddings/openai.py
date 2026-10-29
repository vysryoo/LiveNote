"""OpenAI embedding service."""

import logging
import os
import time
from typing import List

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService:
    """Service for generating embeddings using OpenAI's API.
    
    Attributes:
        model: The OpenAI embedding model to use
        client: OpenAI client instance
        
    Example:
        >>> service = OpenAIEmbeddingService(model="text-embedding-3-large")
        >>> embeddings = service.embed_texts(["Hello world", "How are you?"])
        >>> len(embeddings)
        2
    """
    
    def __init__(self, model: str = "text-embedding-3-large", api_key: str | None = None):
        """Initialize the OpenAI embedding service.
        
        Args:
            model: The embedding model name
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
        """
        self.model = model
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI embedding service with model: {model}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each is a list of floats)
            
        Example:
            >>> embeddings = service.embed_texts(["Hello", "World"])
            >>> len(embeddings[0])  # dimension
            3072
        """
        if not texts:
            return []
        
        start_time = time.time()
        logger.debug(f"Embedding {len(texts)} texts with model {self.model}")
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            embeddings = [item.embedding for item in response.data]
            elapsed = time.time() - start_time
            
            logger.info(
                f"Generated {len(embeddings)} embeddings "
                f"(dim={len(embeddings[0])}) in {elapsed:.2f}s"
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        embeddings = self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of embeddings for this model.
        
        Returns:
            Embedding dimension (e.g., 3072 for text-embedding-3-large)
        """
        # Known dimensions for OpenAI models
        dimensions = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }
        return dimensions.get(self.model, 1536)
