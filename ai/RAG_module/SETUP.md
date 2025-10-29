# RAGKit Setup Guide

Complete setup instructions for RAGKit - a Python library for RAG using ChromaDB and OpenAI.

## Prerequisites

- **Python 3.11+**
- **OpenAI API key** (get one at https://platform.openai.com/api-keys)
- **macOS/Linux/Windows** (macOS/Linux recommended for best experience)

## Installation Steps

### 1. Navigate to Project

```bash
cd /path/to/RAG_module
```

### 2. Create Virtual Environment

We strongly recommend using a virtual environment to avoid dependency conflicts.

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

### 3. Install RAGKit

Install the package in editable mode (for development):

```bash
pip install -e .
```

This will install all dependencies:
- `openai`
- `chromadb`
- `pypdf`
- `pytest`

### 4. Set OpenAI API Key

**Option A: Environment Variable**

```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

**Option B: .env File (Recommended)**

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

Then load it before running scripts:

```bash
source .env && export $(cat .env | grep -v '^#' | xargs)
```

## Verification

Run the setup verification script:

```bash
python verify_setup.py
```

Expected output:
```
✓ OpenAI API key found
✓ Chroma directory exists
✓ RAGKit module imported
✓ RAGService initialized
✓ All checks passed!
```

## Run Tests

```bash
# Load environment variables
source .env && export $(cat .env | grep -v '^#' | xargs)

# Run all tests
pytest -v
```

You should see all 15 tests pass:
- 5 text upsert tests
- 5 PDF upsert tests
- 5 retrieve tests

## First Run

Try the simple demo:

```bash
python examples/test_light.py
```

Or the comprehensive demo:

```bash
python demo_comprehensive.py
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'ragkit'"

**Solution:**
```bash
source .venv/bin/activate
pip install -e .
```

### "OpenAI API key not found"

**Solution:**
```bash
export OPENAI_API_KEY='sk-your-key'
# or
echo "OPENAI_API_KEY=sk-your-key" > .env
source .env && export $(cat .env | grep -v '^#' | xargs)
```

### "chromadb installation fails with C++ build errors"

**Solution:**
```bash
pip install chromadb --no-build-isolation
```

This uses pre-built binaries instead of compiling from source.

### Tests fail with "chroma_data already exists"

**Solution:**
```bash
rm -rf chroma_data
pytest -v
```

## Next Steps

1. Read the [README.md](README.md) for API documentation
2. Explore the `examples/` directory
3. Check out `tests/` for usage patterns
4. Start building your RAG application!

## Quick Reference

| Command | Purpose |
|---------|---------|
| `source .venv/bin/activate` | Activate venv |
| `pip install -e .` | Install RAGKit |
| `export OPENAI_API_KEY=sk-...` | Set API key |
| `pytest -v` | Run tests |
| `python verify_setup.py` | Verify setup |
| `python examples/test_light.py` | Simple demo |

---

**Need help?** Open an issue on the repository.
