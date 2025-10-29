"""Generate test PDF files for testing."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch


def create_sample_lecture_pdf(output_path: str):
    """Create a sample lecture PDF with multiple pages."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title page
    title = Paragraph("컴퓨터 과학 강의 노트", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    subtitle = Paragraph("주제: Vector Databases and RAG", styles['Heading2'])
    story.append(subtitle)
    story.append(Spacer(1, 0.5*inch))
    
    info = Paragraph("강의자: 김교수<br/>날짜: 2025년 3월 15일<br/>과목: CS301", styles['Normal'])
    story.append(info)
    story.append(PageBreak())
    
    # Page 1: Introduction
    story.append(Paragraph("1. Introduction to Vector Databases", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    content1 = """
    Vector databases are specialized database systems designed to store and query 
    high-dimensional vectors efficiently. Unlike traditional databases that store 
    structured data in rows and columns, vector databases excel at handling 
    unstructured data like text, images, and audio by converting them into 
    numerical representations called embeddings.
    
    These databases use advanced indexing techniques such as HNSW (Hierarchical 
    Navigable Small World) graphs and IVF (Inverted File Index) to enable fast 
    approximate nearest neighbor search across millions or billions of vectors.
    """
    story.append(Paragraph(content1, styles['Normal']))
    story.append(PageBreak())
    
    # Page 2: RAG Architecture
    story.append(Paragraph("2. Retrieval-Augmented Generation (RAG)", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    content2 = """
    RAG is a powerful technique that combines information retrieval with text 
    generation. The process involves two main steps:
    
    1. Retrieval: Given a user query, the system retrieves relevant context from 
       a knowledge base using semantic search over vector embeddings.
    
    2. Generation: The retrieved context is then provided to a large language 
       model (LLM) along with the original query to generate an informed response.
    
    This approach allows LLMs to access up-to-date information without requiring 
    retraining, making it ideal for question-answering systems, chatbots, and 
    knowledge management applications.
    """
    story.append(Paragraph(content2, styles['Normal']))
    story.append(PageBreak())
    
    # Page 3: Embeddings
    story.append(Paragraph("3. Understanding Embeddings", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    content3 = """
    Embeddings are dense vector representations of data that capture semantic 
    meaning. In natural language processing, sentence embeddings transform text 
    into fixed-size vectors where similar meanings result in vectors that are 
    close together in the embedding space.
    
    Popular embedding models include:
    - OpenAI's text-embedding-3-large (3072 dimensions)
    - text-embedding-3-small (1536 dimensions)
    - Sentence-BERT variants
    
    The dimensionality-curse challenge: As dimension increases, the volume of 
    space increases exponentially, making traditional indexing methods inefficient.
    """
    story.append(Paragraph(content3, styles['Normal']))
    story.append(PageBreak())
    
    # Page 4: Chroma DB
    story.append(Paragraph("4. ChromaDB Overview", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    content4 = """
    ChromaDB is an open-source embedding database designed for AI applications. 
    Key features include:
    
    - Simple API for adding, querying, and managing embeddings
    - Persistent storage with SQLite backend
    - Built-in support for metadata filtering
    - Compatibility with various embedding models
    - In-memory and persistent modes
    
    ChromaDB uses HNSW algorithm for efficient similarity search and supports 
    multiple distance metrics including cosine similarity, L2 distance, and 
    inner product.
    """
    story.append(Paragraph(content4, styles['Normal']))
    story.append(PageBreak())
    
    # Page 5: Best Practices
    story.append(Paragraph("5. Best Practices for RAG Systems", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    content5 = """
    When building production RAG systems, consider these best practices:
    
    1. Chunk Size: Balance between too small (loses context) and too large 
       (dilutes relevance). Typical range: 500-1500 tokens.
    
    2. Metadata: Store rich metadata (timestamps, sources, sections) to enable 
       filtering and debugging.
    
    3. Hybrid Search: Combine vector search with keyword-based search for better 
       precision.
    
    4. Reranking: Use a cross-encoder model to rerank top-k results for improved 
       relevance.
    
    5. Monitoring: Track retrieval quality metrics and user feedback to improve 
       the system over time.
    """
    story.append(Paragraph(content5, styles['Normal']))
    
    # Build PDF
    doc.build(story)


def create_simple_test_pdf(output_path: str):
    """Create a simple test PDF with 3 pages."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Page 0
    story.append(Paragraph("Test Document - Page 0", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("This is the first page of the test document.", styles['Normal']))
    story.append(PageBreak())
    
    # Page 1
    story.append(Paragraph("Page 1: STL Vector Container", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    content = """
    The STL vector is a dynamic array that can grow and shrink automatically. 
    It provides random access to elements with O(1) time complexity. The capacity 
    of a vector represents the amount of allocated storage, which may be larger 
    than the size to allow for efficient growth.
    """
    story.append(Paragraph(content, styles['Normal']))
    story.append(PageBreak())
    
    # Page 2
    story.append(Paragraph("Page 2: Korean Language Test", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("안녕하세요. 이것은 한국어 테스트 페이지입니다.", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("벡터 데이터베이스는 고차원 벡터를 효율적으로 저장하고 검색합니다.", styles['Normal']))
    
    doc.build(story)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Get script directory
    script_dir = Path(__file__).parent
    test_data_dir = script_dir / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Create PDFs
    print("Creating sample lecture PDF...")
    create_sample_lecture_pdf(str(test_data_dir / "sample_lecture.pdf"))
    print(f"✓ Created: {test_data_dir / 'sample_lecture.pdf'}")
    
    print("\nCreating simple test PDF...")
    create_simple_test_pdf(str(test_data_dir / "simple_test.pdf"))
    print(f"✓ Created: {test_data_dir / 'simple_test.pdf'}")
    
    print("\n✅ All test PDFs created successfully!")
