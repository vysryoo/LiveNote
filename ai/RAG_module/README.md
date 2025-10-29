# RAGKit

**Production-ready Python library for RAG (Retrieval-Augmented Generation)** using ChromaDB and OpenAI embeddings.

## ✨ Features

- 🚀 **Simple API** - 3 core methods: `upsert_text()`, `upsert_pdf()`, `retrieve()`
- 📄 **PDF Support** - Automatic page splitting and metadata management
- 🔑 **Deterministic IDs** - Hash-based IDs for idempotent operations
- 🏷️ **Rich Metadata** - Store and filter by custom metadata
- 💾 **Persistent Storage** - ChromaDB with SQLite backend
- 🌏 **Multilingual** - Full Korean/Unicode support
- ✅ **Well-Tested** - 15 comprehensive tests

## 📦 Installation

### Prerequisites

- Python 3.11+
- OpenAI API key

### Setup

```bash
# 1. Clone or navigate to the project
cd RAG_module

# 2. Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install the package in editable mode
pip install -e .

# 4. Set your OpenAI API key
export OPENAI_API_KEY='your-api-key-here'

# Or create a .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## 🚀 Quick Start

### Basic Usage

```python
from ragkit import RAGService, RAGConfig
from ragkit.models import UpsertItem

# Initialize service
config = RAGConfig()
service = RAGService(config)

# Upsert text documents
items = [
    UpsertItem(
        text="Vector databases store embeddings efficiently.",
        metadata={"source": "docs", "topic": "databases"}
    ),
    UpsertItem(
        text="RAG combines retrieval with generation.",
        metadata={"source": "docs", "topic": "ai"}
    )
]

result = service.upsert_text("my_collection", items)
print(f"Upserted {result['count']} items")

# Retrieve relevant chunks
chunks = service.retrieve("my_collection", "What is RAG?", top_k=3)

for chunk in chunks:
    print(f"[{chunk.score:.2f}] {chunk.text}")
```

### PDF Upload

```python
# Automatically splits PDF into pages
result = service.upsert_pdf(
    collection_id="lectures",
    pdf_path="lecture_01.pdf",
    base_metadata={"course": "CS101", "year": 2025}
)

print(f"Ingested {result['count']} pages")
```

### Filtered Retrieval

```python
from ragkit.models import RetrieveFilters

# Filter by metadata
filters = RetrieveFilters(
    subject="computer_science",
    min_timestamp=1704067200,
    custom={"difficulty": "intermediate"}
)

chunks = service.retrieve(
    collection_id="lectures",
    query="vector databases",
    top_k=5,
    filters=filters
)
```

## 📚 API Reference

### RAGService

#### `upsert_text(collection_id, items)`
Upsert text documents into a collection.

**Parameters:**
- `collection_id` (str): Target collection
- `items` (List[UpsertItem]): Documents to upsert

**Returns:** `{"collection_id": str, "count": int, "embedding_dim": int}`

#### `upsert_pdf(collection_id, pdf_path, base_metadata=None)`
Upsert PDF with automatic page splitting.

**Parameters:**
- `collection_id` (str): Target collection
- `pdf_path` (str): Path to PDF file
- `base_metadata` (dict, optional): Metadata for all pages

**Returns:** `{"collection_id": str, "count": int, "embedding_dim": int}`

#### `retrieve(collection_id, query, top_k=5, filters=None)`
Retrieve relevant chunks.

**Parameters:**
- `collection_id` (str): Collection to query
- `query` (str): Query text
- `top_k` (int): Number of results
- `filters` (RetrieveFilters, optional): Metadata filters

**Returns:** `List[RetrievedChunk]`

### Data Models

#### UpsertItem
```python
@dataclass
class UpsertItem:
    text: str
    id: str | None = None              # Auto-generated if None
    metadata: dict[str, Any] = {}
    section_id: str | None = None
```

#### RetrieveFilters
```python
@dataclass
class RetrieveFilters:
    subject: str | None = None
    section_id: str | None = None
    min_timestamp: int | str | None = None
    max_timestamp: int | str | None = None
    custom: dict[str, Any] = {}
```

#### RetrievedChunk
```python
@dataclass
class RetrievedChunk:
    id: str
    text: str
    score: float                        # Higher = more similar
    metadata: dict[str, Any]
    section_id: str | None = None
```

## 🧪 Testing

```bash
# Run all tests (requires OPENAI_API_KEY)
source .env && export $(cat .env | grep -v '^#' | xargs)
pytest -v

# Run specific test file
pytest tests/test_upsert_text.py -v

# Run with coverage
pytest --cov=ragkit --cov-report=html
```

## 🎯 Examples

### Simple Demo
```bash
python examples/test_light.py
```

### Comprehensive Demo
```bash
python demo_comprehensive.py
```

This demo shows:
- Upserting 10 text documents
- Upserting 1 PDF file
- Running 3 queries with filters
- Displaying top 2 results per query

### PDF Ingestion
```bash
python examples/ingest_pdf_pages.py test_data/sample_lecture.pdf my_collection
```

## ⚙️ Configuration

**RAGConfig** options:

```python
RAGConfig(
    persist_dir="./chroma_data",           # Chroma storage directory
    embedding_model="text-embedding-3-large",  # OpenAI model
    openai_api_key=None                    # Defaults to OPENAI_API_KEY env
)
```

### Embedding Models

- `text-embedding-3-large`: 3072 dimensions (high performance, recommended)
- `text-embedding-3-small`: 1536 dimensions (faster, cheaper)
- `text-embedding-ada-002`: 1536 dimensions (legacy)

## 🔑 Deterministic IDs

- **Text upsert:** If `UpsertItem.id` is `None`, generates `hash(text)[:14]`
- **PDF upsert:** Uses `{pdf_basename}|p{page_num}` format

This ensures idempotent operations - re-upserting the same content won't create duplicates.

## 📁 Project Structure

```
ragkit/                     # Core library
  ├── __init__.py
  ├── config.py            # RAGConfig
  ├── models.py            # UpsertItem, RetrieveFilters, RetrievedChunk
  ├── service.py           # RAGService (main API)
  ├── embeddings/
  │   └── openai.py       # OpenAI embedding service
  ├── vectordb/
  │   └── chroma.py       # ChromaDB interface
  └── utils/
      ├── pdf.py          # PDF loading
      └── text.py         # Text utilities

tests/                      # 15 comprehensive tests
  ├── conftest.py
  ├── test_upsert_text.py  # 5 tests
  ├── test_upsert_pdf.py   # 5 tests
  └── test_retrieve.py     # 5 tests

examples/                   # Example scripts
  ├── test_light.py
  └── ingest_pdf_pages.py

test_data/                  # Auto-generated PDFs
  ├── simple_test.pdf      # 3 pages
  └── sample_lecture.pdf   # 6 pages
```

## 🐛 Troubleshooting

### ImportError
```bash
source .venv/bin/activate
pip install -e .
```

### API Key Error
```bash
export OPENAI_API_KEY='sk-...'
# Or add to .env file
```

### Chroma DB Error
```bash
# Delete and recreate
rm -rf chroma_data
python your_script.py
```

## 📈 Performance

- Text upsert: ~1-2s for 10 documents
- PDF upsert: ~0.5-1s per page
- Query: ~0.3-0.5s per query
- All timings depend on OpenAI API response time

## 🚦 Future Enhancements

- [ ] FastAPI wrapper for REST API
- [ ] Streaming retrieval support
- [ ] Advanced text chunking strategies
- [ ] Hybrid search (vector + keyword)
- [ ] Reranking with cross-encoders
- [ ] Batch processing optimization

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Please ensure:
- Type hints on all functions
- Docstrings with examples
- Tests for new features
- Code formatted with `black` or `ruff`

## 📞 Support

For issues or questions, please open an issue on the repository.

---

**Built with ❤️ for clean, production-ready RAG systems.**
