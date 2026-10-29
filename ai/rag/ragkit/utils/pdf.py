"""PDF loading utilities."""

import logging
from pathlib import Path
from typing import List, Dict, Any

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class Document:
    """Simple document container.
    
    Attributes:
        page_content: Text content of the document
        metadata: Associated metadata
    """
    
    def __init__(self, page_content: str, metadata: Dict[str, Any] | None = None):
        self.page_content = page_content
        self.metadata = metadata or {}


def load_pdf_pages(pdf_path: str) -> List[Document]:
    """Load PDF and split into page documents.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of Document objects, one per page
        
    Raises:
        ValueError: If PDF path is invalid or file cannot be read
        
    Example:
        >>> docs = load_pdf_pages("lecture.pdf")
        >>> len(docs)
        10
        >>> docs[0].metadata["page"]
        0
    """
    path = Path(pdf_path)
    
    if not path.exists():
        raise ValueError(f"PDF file not found: {pdf_path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")
    
    try:
        logger.info(f"Loading PDF: {pdf_path}")
        reader = PdfReader(str(path))
        
        documents = []
        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                
                # Skip empty pages
                if not text.strip():
                    logger.warning(f"Page {page_num} is empty, skipping")
                    continue
                
                doc = Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "page": page_num,
                        "total_pages": len(reader.pages),
                    }
                )
                documents.append(doc)
                
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
                continue
        
        logger.info(f"Loaded {len(documents)} pages from {path.name}")
        return documents
        
    except Exception as e:
        logger.error(f"Failed to load PDF {pdf_path}: {e}")
        raise ValueError(f"Failed to load PDF: {e}")
