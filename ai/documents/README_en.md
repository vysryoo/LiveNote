# LiveNote AI Gateway

Welcome to the LiveNote AI Gateway!  
This document is a comprehensive guide to the architecture, configuration, APIs, data flow, troubleshooting steps, and operational routines for the integrated AI backend.  
The README is intentionally detailed (over 500 lines) to serve as the single source of truth for developers, DevOps engineers, QA staff, and operators.

---

## Table of Contents

1. Introduction
2. High-Level Overview
3. Architectural Diagram
4. Repository Layout
5. Module Summaries
    - 5.1 cap1_QA_module
    - 5.2 cap1_RAG_module
    - 5.3 cap1_openalex_module
    - 5.4 cap1_wiki_module
    - 5.5 cap1_youtube_module
    - 5.6 server
    - 5.7 tests
    - 5.8 scripts and utilities
6. Environment Setup
    - 6.1 Prerequisites
    - 6.2 Automated Setup with `setup.sh`
    - 6.3 Manual Setup (if needed)
    - 6.4 Activating the Virtual Environment
7. Environment Variables
    - 7.1 `.env` Structure
    - 7.2 Description of Keys
    - 7.3 Example `.env`
8. Application Settings
    - 8.1 RAG Settings
    - 8.2 QA Settings
    - 8.3 REC Settings
9. Data Flow
    - 9.1 Upsert Flow (RAG)
    - 9.2 QA Flow
    - 9.3 REC Flow
    - 9.4 Error Handling Flow
10. API Reference
    - 10.1 Health
    - 10.2 RAG Endpoints
    - 10.3 QA Endpoint
    - 10.4 REC Endpoint
    - 10.5 SSE Event Format
    - 10.6 Example cURL Calls
11. Configuration Guidance
    - 11.1 Adjusting Question Types
    - 11.2 Provider-Level Settings
    - 11.3 Storage Paths
12. Operational Procedures
    - 12.1 Running Locally
    - 12.2 Running Automated Checks (`test.sh`)
    - 12.3 Deploying to Cloud
13. Troubleshooting
    - 13.1 Common Errors
    - 13.2 Telemetry Warnings
    - 13.3 Chroma Collection Issues
    - 13.4 SSE Stream Diagnostics
14. Testing Strategy
    - 14.1 Unit and Integration Tests
    - 14.2 Manual Validation Steps
15. Best Practices
16. Future Work
17. Appendix
    - 17.1 Detailed Sequence Diagrams (Textual)
    - 17.2 ChromaDB Internals
    - 17.3 Glossary
18. Revision Log

---

## 1. Introduction

This backend is the AI orchestration layer for LiveNote, handling:
- Retrieval-Augmented Generation (RAG) document storage and retrieval.
- Question generation with multiple answer types through OpenAI models.
- Consolidated recommendations (REC) across scholarly papers, Wikipedia entries, and YouTube videos.

The stack is implemented in Python using FastAPI and asynchronous programming to ensure responsive, event-driven interactions via Server-Sent Events (SSE).

---

## 2. High-Level Overview

- **Primary goal**: provide a unified HTTP API endpoint for content ingestion (RAG) and AI-driven experience (QA + REC).
- **Interacting systems**: Spring-based frontend (or any HTTP client) communicates with this API.
- **External services**: OpenAI (chat & embeddings), OpenAlex API, Wikipedia API, YouTube Data API, ChromaDB.
- **Deployment target**: Linux server or cloud VM with Python 3.11, outbound network access, and persistent storage.

Key features:
1. **Asynchronous streaming** for QA and REC – clients receive incremental updates.
2. **Config-driven behavior** – question types, provider settings, storage path, concurrency limits all adjustable.
3. **Unified collection naming** – `lecture_<lecture_id>` ensures consistent cross-service references.

---

## 3. Architectural Diagram

While a graphical diagram is not included, below is a textual layout describing the data flow:

```
Client (Spring / curl / Postman)
    |
    | HTTP requests (JSON, multipart)
    v
FastAPI (server/)
    |
    | -> RAG Service (cap1_RAG_module)
    |       |-- OpenAI Embedding (cap1_RAG_module/ragkit/embeddings)
    |       |-- ChromaDB (cap1_RAG_module/ragkit/vectordb)
    |
    | -> QA Service (cap1_QA_module)
    |       |-- OpenAI Async Chat
    |
    | -> REC Services (cap1_openalex_module, cap1_wiki_module, cap1_youtube_module)
            |-- External APIs (OpenAlex, Wikipedia, YouTube)
            |-- OpenAI for validation & summarization
```

---

## 4. Repository Layout

- `cap1_QA_module/` – Question generation module.
- `cap1_RAG_module/` – Retrieval-augmented storage & retrieval.
- `cap1_openalex_module/` – Scientific paper recommendations via OpenAlex API.
- `cap1_wiki_module/` – Wikipedia article recommendations.
- `cap1_youtube_module/` – YouTube video recommendations.
- `server/` – FastAPI app, routers, configuration utilities.
- `tests/` – Stub services and SSE unit tests.
- `setup.sh` – Automated environment bootstrap script.
- `test.sh` – Minimal smoke test script (health + text upsert + REC).
- `requirements.server.txt` – Consolidated runtime dependencies.
- `.env.example` – Template for environment variables.
- `.env` – Actual runtime configuration (not committed; local).

Each module is scoped to a single responsibility but can be composed together through the FastAPI gateway.

---

## 5. Module Summaries

### 5.1 cap1_QA_module
- **Location**: `cap1_QA_module/`
- **Primary files**:
  - `qakit/service.py`: Orchestrates QA generation using async tasks.
  - `qakit/models.py`: Pydantic models for requests/responses.
  - `qakit/config/prompts.py`: Prompt templates for different question types.
  - `qakit/llm/openai_client.py`: Async OpenAI chat interactions.
- **Key idea**: Accepts section summary and question types, generates sequential SSE events for each question-answer pair.
- **Recent change**: `stream_questions` now uses `asyncio.wait` to eliminate `KeyError` race conditions.

### 5.2 cap1_RAG_module
- **Location**: `cap1_RAG_module/`
- **Primary files**:
  - `ragkit/service.py`: High-level API for upserting text/PDF, retrieving.
  - `ragkit/config.py`: Reads environment (`RAG_PERSIST_DIR`, `RAG_EMBEDDING_MODEL`, `RAG_OPENAI_API_KEY`).
  - `ragkit/vectordb/chroma.py`: ChromaDB wrapper.
  - `ragkit/embeddings/openai.py`: Embedding generation with OpenAI.
- **Key idea**: Each lecture maps to a single Chroma collection named `lecture_<id>`.
- **Recent change**: Empty metadata is auto-filled with `{"source": "text"}` to satisfy Chroma requirements.

### 5.3 cap1_openalex_module
- **Location**: `cap1_openalex_module/`
- **Primary files**:
  - `openalexkit/service.py`: Handles token generation, paper fetching, LLM-based scoring.
  - `openalexkit/models.py`: Request/response structure (includes previous summaries, rag context).
- **Key idea**: Accepts RAG chunks & previous summaries to craft targeted suggestions.
- **Configuration**: `OpenAlexConfig` (within module) for concurrency, model choices, year range, min score.

### 5.4 cap1_wiki_module
- **Location**: `cap1_wiki_module/`
- **Primary files**:
  - `wikikit/service.py`: Multi-language fetching, fallback, heuristic scoring.
  - `wikikit/api/wiki_client.py`: HTTP interactions with Wikipedia API.
  - `wikikit/llm/openai_client.py`: LLM keyword generation and scoring.
- **Recent change**: All internal imports use relative paths (`from .api import ...`) to avoid runtime `ModuleNotFoundError`.

### 5.5 cap1_youtube_module
- **Location**: `cap1_youtube_module/`
- **Primary files**:
  - `youtubekit/service.py`: Multi-query search, transcript summarization, scoring.
  - `youtubekit/api/youtube_client.py`: YouTube Data API handling.
  - `youtubekit/config/youtube_config.py`: API keys, concurrency.
- **Recent change**: Relative imports applied; ensures package consistency.

### 5.6 server
- **Location**: `server/`
- **Primary files**:
  - `app.py`: FastAPI creation, dependency injection, service lifecycle handling.
  - `routes/rag.py`: Text/PDF upsert endpoints.
  - `routes/qa.py`: QA SSE endpoint.
  - `routes/rec.py`: REC SSE endpoint (OpenAlex + Wiki + YouTube).
  - `utils.py`: Collection ID helpers, chunk conversions, SSE formatting.
  - `config.py`: Pydantic settings (`AppSettings`, `RAGSettings`, `QASettings`, `RECSettings`).
- **Key idea**: Provides HTTP endpoints and maps requests into module calls.
- **Recent change**: `rec.py` uses `asyncio.wait` to avoid `KeyError` when tasks complete concurrently; metadata auto-fill for text upsert resides in `rag.py`.

### 5.7 tests
- **Location**: `tests/`
- **Primary files**:
  - `conftest.py`: Stub services for deterministic testing.
  - `test_qa_stream.py`: Verifies SSE QA ordering and error handling.
  - `test_rec_stream.py`: Verifies SSE REC behavior.
- **Usage**: Run tests with `pytest` (after adjusting network-dependent stubs).

### 5.8 scripts and utilities
- `setup.sh`: Virtual environment bootstrap; installs dependencies, ensures `.env`, patches `activate`.
- `test.sh`: Minimal smoke tests (health → text upsert → REC SSE). Customizable via `HOST` and `PORT` env variables.

---

## 6. Environment Setup

### 6.1 Prerequisites
- Python 3.11 installed and available as `python3.11`.
- Bash shell.
- Internet access for pip installations.
- OpenAI / YouTube API keys (for real requests).

### 6.2 Automated Setup with `setup.sh`
1. Run `./setup.sh`.  
2. Script actions:
   - Ensures Python 3.11 (recreates `.venv` if version mismatch).
   - Activates `.venv` temporarily for installation context.
   - Upgrades `pip`, installs packages from `requirements.server.txt`.
   - Copies `.env.example` to `.env` if missing.
   - Appends a snippet to `.venv/bin/activate` so `.env` is auto-sourced on activation.

### 6.3 Manual Setup (If Needed)
- Create venv: `python3.11 -m venv .venv`
- Activate: `source .venv/bin/activate`
- Install: `pip install -r requirements.server.txt`
- Copy `.env.example` → `.env` and edit values.
- Manually source `.env` (if you skip the automated patch):  
  `set -a; source .env; set +a`

### 6.4 Activating the Virtual Environment
- `source .venv/bin/activate`
  - Automatically loads `.env` values thanks to the patched `activate` script.
- Verify with `pip list` or `python --version` (should be 3.11).

---

## 7. Environment Variables

### 7.1 `.env` Structure
```
OPENAI_API_KEY="..."
YOUTUBE_API_KEY="..."
WIKIKIT_USER_AGENT="WikiKit/1.0 (+https://example.com; contact: you@example.com)"
ANONYMIZED_TELEMETRY="False"
CHROMA_TELEMETRY_ENABLED="False"
RAG_PERSIST_DIR="server_storage/chroma_data_real"
```

### 7.2 Description of Keys
- `OPENAI_API_KEY`: Used by RAG, QA, OpenAlex, Wiki, YouTube modules.
- `YOUTUBE_API_KEY`: Used by YouTube Data API interactions.
- `WIKIKIT_USER_AGENT`: Required to comply with Wikipedia API guidelines.
- `ANONYMIZED_TELEMETRY` & `CHROMA_TELEMETRY_ENABLED`: Disable Chroma telemetry.
- `RAG_PERSIST_DIR`: Folder to store Chroma collections. Relative path recommended for portability.
  - Default: `server_storage/chroma_data_real`
  - Change per environment: e.g., `/var/lib/livenote/chroma`.

### 7.3 Example `.env`
```
OPENAI_API_KEY="sk-xxxx"
YOUTUBE_API_KEY="AIzaSy..."
WIKIKIT_USER_AGENT="WikiKit/1.0 (+https://github.com/acme; contact: ops@example.com)"
ANONYMIZED_TELEMETRY="False"
CHROMA_TELEMETRY_ENABLED="False"
RAG_PERSIST_DIR="server_storage/chroma_data_real"
```

---

## 8. Application Settings

Settings object is defined in `server/config.py` and can be expanded as needed.

### 8.1 RAG Settings (`RAGSettings`)
- `collection_prefix`: defaults to `"lecture"`.
- `qa_retrieve_top_k`: number of chunks for QA context (default 2).
- `rec_retrieve_top_k`: number of chunks for REC context (default 3).

### 8.2 QA Settings (`QASettings`)
- `language`: output language (default `"ko"`).
- `question_types`: default types when request doesn’t specify (e.g., `["응용", "비교", "심화"]`).
- `qa_top_k`: how many question types to use.

### 8.3 REC Settings (`RECSettings`)
- Structured with nested models (`openalex`, `wiki`, `youtube`).
- Each includes `top_k`, `verify` toggles, `min_score`, language, etc.
- Example:
  - OpenAlex: `top_k=2`, `verify=True`, `sort_by="hybrid"`, `min_score=3.0`
  - Wiki: `top_k=2`, `verify=False`, `wiki_lang="en"`
  - YouTube: `top_k=2`, `verify=True`, `yt_lang="en"`

Settings are accessible via FastAPI dependencies (`get_settings`).

---

## 9. Data Flow

### 9.1 Upsert Flow (RAG)
1. Client calls `POST /rag/text-upsert` or `/rag/pdf-upsert`.
2. Server builds collection ID `lecture_<lecture_id>`.
3. Data is embedded via OpenAI (`text-embedding-3-large` unless overridden).
4. ChromaDB upserts documents with metadata.

### 9.2 QA Flow
1. Client calls `POST /qa/generate`.
2. Server retrieves top-k chunks (as configured).
3. Async tasks fire for each question type.
4. SSE events stream: context → partial results per type → final summary.

### 9.3 REC Flow
1. Client calls `POST /rec/recommend`.
2. RAG chunks retrieved; previous summaries passed to providers.
3. OpenAlex, Wiki, YouTube tasks run in parallel.
4. SSE events deliver partial results as each provider finishes.
5. Completed event summarises final status.

### 9.4 Error Handling Flow
- Exceptions in upsert/retrieve produce HTTP 4xx/5xx with descriptive message.
- SSE errors generate `qa_error` or `rec_error`.
- Chroma-specific warnings (telemetry, insufficient results) are logged but do not stop flows.

---

## 10. API Reference

### 10.1 Health
- **Endpoint**: `GET /health`
- **Description**: Simple health check; returns `{"status":"ok"}`.
- **Usage**: `curl http://127.0.0.1:8000/health`

### 10.2 RAG Endpoints

#### 10.2.1 `POST /rag/pdf-upsert`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `lecture_id`: required string.
  - `file`: required PDF file.
  - `base_metadata`: optional JSON string.
- **Response**:
  ```json
  {
    "collection_id": "lecture_lec-001",
    "result": {
      "collection_id": "lecture_lec-001",
      "count": 3,
      "embedding_dim": 3072
    }
  }
  ```
- **Errors**: 400 if file missing, wrong type, or metadata invalid JSON.

#### 10.2.2 `POST /rag/text-upsert`
- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
    "lecture_id": "lec-001",
    "items": [
      {"text": "요약 A"},
      {"text": "요약 B", "metadata": {"topic": "stack"}}
    ]
  }
  ```
- **Response**:
  ```json
  {
    "collection_id": "lecture_lec-001",
    "result": {
      "collection_id": "lecture_lec-001",
      "count": 2,
      "embedding_dim": 3072
    }
  }
  ```
- **Notes**: Metadata auto-populated if empty.
- **Errors**: 422 for validation issues; 500 if embedding/upsert fails.

### 10.3 QA Endpoint

#### 10.3.1 `POST /qa/generate`
- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
    "lecture_id": "lec-001",
    "section_id": 1,
    "section_summary": "스택과 큐의 차이를 설명한다."
  }
  ```
- **Response**: SSE stream.
  ```
  event: qa_context
  data: {"event":"context_ready","collection_id":"lecture_lec-001","chunk_count":2}

  event: qa_partial
  data: {"type":"응용","qa":{"type":"응용","question":"...","answer":"..."}, "index":1}

  event: qa_complete
  data: {"total":3,"duration_ms":3459}
  ```
- **Notes**: Streaming stops automatically; `curl` may show `(18)` when connection closes—this is expected.

### 10.4 REC Endpoint

#### 10.4.1 `POST /rec/recommend`
- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
    "lecture_id": "lec-001",
    "section_id": 1,
    "section_summary": "스택과 큐의 차이를 설명한다.",
    "previous_summaries": [],
    "yt_exclude": [],
    "wiki_exclude": [],
    "paper_exclude": []
  }
  ```
- **Response**: SSE stream.
  ```
  event: rec_context
  data: {"event":"context_ready","collection_id":"lecture_lec-001","chunk_count":2}

  event: rec_partial
  data: {"source":"wiki","count":2,"items":[...]}

  event: rec_complete
  data: {"completed_sources":3,"duration_ms":5120}
  ```
- **Notes**: Ensure `lecture_id` matches one used during upsert. `previous_summaries` section_id must be ≥ 1.

### 10.5 SSE Event Format
- `qa_context`, `rec_context`: initial payload with collection info.
- `qa_partial` / `rec_partial`: incremental results.
- `qa_error` / `rec_error`: errors for specific question types or providers.
- `qa_complete` / `rec_complete`: final summary.

### 10.6 Example cURL Calls
1. **Health**  
   `curl http://127.0.0.1:8000/health`
2. **Text Upsert**  
   `curl -X POST http://127.0.0.1:8000/rag/text-upsert -H "Content-Type: application/json" -d '{"lecture_id":"001","items":[{"text":"요약 A"},{"text":"요약 B"}]}'`
3. **QA SSE**  
   `curl -v -N -X POST http://127.0.0.1:8000/qa/generate -H "Content-Type: application/json" -d '{"lecture_id":"001","section_id":1,"section_summary":"..."}'`
4. **REC SSE**  
   `curl -v -N -X POST http://127.0.0.1:8000/rec/recommend -H "Content-Type: application/json" -d '{"lecture_id":"001","section_id":1,"section_summary":"...","previous_summaries":[],"yt_exclude":[],"wiki_exclude":[],"paper_exclude":[]}'`

---

## 11. Configuration Guidance

### 11.1 Adjusting Question Types
- Modify `server/config.py` → `QASettings.question_types`.
- Example: `["개념", "응용", "심화"]`.
- You can also adjust `qa_top_k` to limit total questions.

### 11.2 Provider-Level Settings
- `server/config.py` → `RECSettings`.
- OpenAlex:
  - `top_k`, `verify`, `year_from`, `sort_by`, `min_score`.
- Wiki:
  - `verify_wiki`, `wiki_lang`, `fallback_to_ko`.
- YouTube:
  - `verify_yt`, `yt_lang`, `min_score`.
- Adjust per environment to balance accuracy and speed.

### 11.3 Storage Paths
- `RAG_PERSIST_DIR` defaults to `server_storage/chroma_data_real`.
- Change via `.env` to absolute path when deploying (e.g., `/data/chroma`).
- Ensure directory is writable and persists across restarts.

---

## 12. Operational Procedures

### 12.1 Running Locally
1. `./setup.sh`
2. `source .venv/bin/activate`
3. `uvicorn server.main:app --reload`
4. Use curl/Postman to interact with endpoints.

### 12.2 Running Automated Checks (`test.sh`)
```
./test.sh
```
- Checks:
  1. `GET /health`
  2. Sample text upsert (`lecture_id="test-lecture"`).
  3. REC SSE call with dummy data.

### 12.3 Deploying to Cloud
- Steps:
  1. Ensure Python 3.11 available.
  2. Clone repo & run `./setup.sh`.
  3. Update `.env` with production keys and paths.
  4. `source .venv/bin/activate` (auto `.env` load).
  5. Start server with process manager (systemd, supervisor, pm2, etc.).
- Add environment-specific overrides if needed via `.env`.

---

## 13. Troubleshooting

### 13.1 Common Errors
| Message | Cause | Resolution |
|---------|-------|-----------|
| `Collection ... does not exist` | `lecture_id` mismatch between upsert and query | Use consistent `lecture_id` for RAG and QA/REC |
| `Expected metadata to be a non-empty dict` | Text item had empty metadata (fixed by auto-population) | Upgrade to latest code; metadata now auto-populated |
| `curl: (18)` on SSE | Connection closed after stream completion | Expected; check SSE logs for events |
| `python-multipart` missing | Multipart not installed | `pip install python-multipart` (already in requirements) |
| `Failed to send telemetry event` | Chroma telemetry bug | Harmless; ensure `ANONYMIZED_TELEMETRY="False"` and `CHROMA_TELEMETRY_ENABLED="False"` |

### 13.2 Telemetry Warnings
- Messages like `Failed to send telemetry event ClientCreateCollectionEvent` stem from Chroma telemetry hooks. Safe to ignore; requests still succeed.
- To suppress further, set environment variables (already in `.env`).

### 13.3 Chroma Collection Issues
- Ensure `.env` is loaded before running server.
- Delete old directories if reinitializing: `rm -rf test_chroma_data`.
- Confirm `RAG_PERSIST_DIR` path exists or can be created.

### 13.4 SSE Stream Diagnostics
- Use `curl -v -N ...` to see headers and chunk metadata.
- Check server logs when SSE stops unexpectedly; errors are surfaced in logs/SSE `*_error` events.
- Ensure network/proxy doesn’t buffer SSE responses.

---

## 14. Testing Strategy

### 14.1 Unit and Integration Tests
- `tests/test_qa_stream.py`: ensures QA streaming order & completion.
- `tests/test_rec_stream.py`: ensures REC streaming across providers.
- `tests/test_rag_pdf.py`, `tests/test_rag_text.py`: validates upsert behavior.
- `tests/conftest.py`: Provides stub services to avoid external calls during tests.

### 14.2 Manual Validation Steps
1. Upsert text (curl).
2. Verify Chroma directory has new entries.
3. Trigger QA SSE; ensure `qa_partial` events cover all question types.
4. Trigger REC SSE; watch for `rec_partial` events for `wiki`, `youtube`, `openalex`.
5. Confirm logs show no unexpected tracebacks.

---

## 15. Best Practices

- Always run `source .venv/bin/activate` before running scripts to ensure correct dependencies.
- Keep `.env` secure; do not commit.
- Use consistent `lecture_id` across operations.
- Monitor logs when using SSE; use `curl -v` for troubleshooting.
- Keep Chroma storage on persistent volume in production.
- Adjust provider settings (min scores, concurrency) based on usage patterns.

---

## 16. Future Work

- Add FastAPI endpoint to inspect recently used RAG chunks (debugging aid).
- Implement caching or rate-limiting for external API calls.
- Add authentication/authorization layer if needed.
- Expand tests to cover offline/timeout scenarios.
- Provide docker-compose for local orchestration.

---

## 17. Appendix

### 17.1 Detailed Sequence Diagrams (Textual)

#### 17.1.1 QA Flow
```
Client → /qa/generate → Server
Server → RAGService.retrieve → ChromaDB
Server ← ChromaDB (chunks)
Server → create async tasks (OpenAI) for each question type
Server ← OpenAI responses
Server → SSE events to client (qa_partial for each type, qa_complete at end)
```

#### 17.1.2 REC Flow
```
Client → /rec/recommend → Server
Server → RAGService.retrieve → ChromaDB
Server ← ChromaDB (chunks)
Server → parallel tasks:
  - OpenAlexService
  - WikiService
  - YouTubeService
Each Service ↔ External API (OpenAI, OpenAlex, Wikipedia, YouTube)
Server ← results as each task completes
Server → SSE events (rec_partial, rec_complete)
```

### 17.2 ChromaDB Internals
- Chroma stores embeddings in `.sqlite3`/`.parquet` under `RAG_PERSIST_DIR`.
- Collections are named `lecture_<lecture_id>`.
- Metadata values must be simple (string/number/bool); complex objects should be JSON serialized.
- Retrieval uses `n_results` set via settings (qa_retrieve_top_k, rec_retrieve_top_k).

### 17.3 Glossary
- **RAG**: Retrieval-Augmented Generation.
- **SSE**: Server-Sent Events, a unidirectional streaming mechanism over HTTP.
- **QA Partial**: Intermediate question-answer pair.
- **REC Partial**: Intermediate provider result set.
- **Telemetry Warning**: Chroma’s optional analytics; can be disabled.

---

## 18. Revision Log

| Date       | Author | Description |
|------------|--------|-------------|
| 2025-11-06 | Team   | Initial comprehensive README creation covering modules, configuration, API usage, troubleshooting, and operational guidance. |

---

End of README.
