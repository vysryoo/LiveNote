"""Pytest configuration and shared fixtures."""

import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from ragkit.config import RAGConfig
from ragkit.service import RAGService


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@pytest.fixture
def temp_persist_dir():
    """Create a temporary directory for Chroma persistence."""
    temp_dir = tempfile.mkdtemp(prefix="test_chroma_")
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def rag_config(temp_persist_dir):
    """Create a test RAG configuration."""
    return RAGConfig(
        persist_dir=temp_persist_dir,
        embedding_model="text-embedding-3-small",  # Use smaller model for tests
    )


@pytest.fixture
def rag_service(rag_config):
    """Create a RAG service instance for testing."""
    # Check if OPENAI_API_KEY is set
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping live tests")
    
    return RAGService(rag_config)


@pytest.fixture
def sample_pdf_path():
    """Get path to sample PDF for testing."""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    pdf_path = test_data_dir / "simple_test.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found at {pdf_path}")
    
    return str(pdf_path)


@pytest.fixture
def sample_lecture_pdf_path():
    """Get path to sample lecture PDF for testing."""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    pdf_path = test_data_dir / "sample_lecture.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Test PDF not found at {pdf_path}")
    
    return str(pdf_path)
