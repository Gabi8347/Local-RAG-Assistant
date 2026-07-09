# Local RAG Assistant

A fully offline document Q&A (RAG) assistant built with Microsoft Foundry Local. This project is being developed as part of the "Building Your First Local RAG Application with Foundry Local" internship.

## About the Project

- **Goal:** An assistant that can answer questions from the user's own documents (SWE210 notes, Algorithm course notes, PDF textbooks, etc.) without requiring an internet connection.
- **Architecture:** User question → vector search in SQLite (retrieval) → retrieved content + question sent to a local LLM (augment) → model generates an answer (generate).
- **Core technologies:** Python, Foundry Local SDK, SQLite, embeddings.

## Environment Setup

### 1. Project folder and virtual environment (venv)

```powershell
mkdir C:\dev\Local-RAG-Assistant
cd C:\dev\Local-RAG-Assistant
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Note:** The project folder should live at a simple path with no non-ASCII characters (e.g. `C:\dev\...`). Paths like `OneDrive\Desktop` can cause problems both from sync behavior and from non-ASCII characters.

### 2. Required libraries

```powershell
pip install -r requirements.txt
```

To verify the installation:
```powershell
pip show foundry-local-sdk
```

## Using the Foundry Local SDK (v1.2.3)

**Important:** The installed version (1.2.3) uses a different API than some tutorial/documentation examples. The simple `FoundryLocalManager("phi-3.5-mini")` call does not work in this version — the correct flow is below.

### Correct usage flow

1. Create a `Configuration(app_name=...)` object
2. Initialize with `FoundryLocalManager.initialize(config)` (singleton pattern)
3. Access the manager via `FoundryLocalManager.instance`
4. Call `manager.start_web_service()`
5. Find the desired model with `manager.catalog.get_model(alias)`
6. `model.download()` — downloads the model if it isn't already on disk
7. `model.load()` — loads the model into memory
8. `model.get_chat_client()` — gets the chat client
9. `client.complete_chat(messages)` — sends the question; read the answer via `response.choices[0].message.content`

### Week 1 proof-of-concept (chat-only, superseded by the RAG loop below)

```python
from foundry_local_sdk import FoundryLocalManager, Configuration

model_alias = "phi-3.5-mini"

# 1-3. Start Foundry Local
config = Configuration(app_name="local-rag-assistant")
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance

# 4. Start the web service
manager.start_web_service()

# 5. Find the model
model = manager.catalog.get_model(model_alias)

# 6-7. Download and load
print("Downloading model (may take a while the first time)...")
model.download()
print("Loading model...")
model.load()

# 8. Get chat client
client = model.get_chat_client()

# 9. Ask a question
messages = [
    {"role": "user", "content": "Hello, who are you?"}
]

response = client.complete_chat(messages)
print(response.choices[0].message.content)
```

### Available model aliases (discovered via `catalog.list_models()`)

| Alias | Model ID |
|---|---|
| phi-4-reasoning | Phi-4-reasoning-generic-cpu:1 |
| phi-4-mini-reasoning | Phi-4-mini-reasoning-generic-cpu:3 |
| phi-4-mini | Phi-4-mini-instruct-generic-cpu:5 |
| phi-3-mini-128k | Phi-3-mini-128k-instruct-generic-cpu:3 |
| phi-3.5-mini | Phi-3.5-mini-instruct-generic-cpu:2 |
| phi-4 | Phi-4-generic-cpu:2 |
| phi-3-mini-4k | Phi-3-mini-4k-instruct-generic-cpu:3 |

| qwen3-embedding-0.6b | Qwen3-Embedding-0.6B-generic-cpu |
| qwen3-embedding-8b | Qwen3-Embedding-8B-generic-cpu |

## Embeddings, SQLite Storage and Retrieval

The embedding model follows the same `download()` / `load()` pattern as the chat model, but exposes `model.get_embedding_client()` instead of `get_chat_client()`. The client has two methods:

- `client.generate_embedding(text)` — single text → `CreateEmbeddingResponse`
- `client.generate_embeddings([text, ...])` — batch → one embedding per input

Embeddings are stored in SQLite (`db.py`) with this schema:

```sql
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    embedding TEXT NOT NULL   -- JSON-encoded float list
)
```

`db.get_top_chunks(query_embedding, top_k)` loads all rows, scores them with cosine similarity in Python, and returns the closest matches. There's no vector index — fine at this scale (tens to low hundreds of chunks), would need `sqlite-vec` or similar for larger corpora.

## Ingestion Pipeline (`ingest.py`)

Extracts text from every PDF in `documents/` with `pypdf`, splits it into ~800-character overlapping chunks, embeds each chunk, and stores it via `db.insert_chunk`. Run it whenever you add new files:

```powershell
python ingest.py
```

> Scanned/image-only PDFs (no text layer) will silently produce 0 chunks — `pypdf` can't extract text from them without OCR, which isn't implemented here.

## Asking Questions (`main.py`)

`main.py` loads both models, then runs an interactive loop: your question is embedded, the top matching chunks are retrieved from SQLite, and both are sent to the chat model as context so it answers only from your own documents.

```powershell
python main.py
```

## Issues Encountered and Fixes

| Issue | Fix |
|---|---|
| `python -m venv venv` hung on a OneDrive path with non-ASCII characters | Moved the project to `C:\dev\Local-RAG-Assistant` |
| `.\venv\Scripts\activate` not recognized in PowerShell | Use `.\venv\Scripts\Activate.ps1` instead (run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first if needed) |
| `pip show` lists the package but `import foundry_local` fails | The actual module name is `foundry_local_sdk`, not `foundry_local` |
| `FoundryLocalManager(model_alias)` → `AttributeError: 'str' object has no attribute 'validate'` | The API changed in v1.2.3; use the `Configuration` + `initialize()` + `.instance` flow shown above |
| `manager.endpoint` → `AttributeError` | This version has no `endpoint`/`api_key`; use `model.get_chat_client()` instead |
| Scanned PDF produces 0 chunks | No text layer to extract; needs OCR (not implemented) — skip the file |

## Project Structure

```
Local-RAG-Assistant/
├── main.py              # RAG CLI: answer_query() + interactive loop
├── ingest.py             # PDF → text → chunks → embeddings → SQLite
├── db.py                 # SQLite schema, insert_chunk, get_top_chunks
├── test_embeddings.py     # Standalone embedding + cosine similarity check
├── test_db.py             # Standalone SQLite insert/retrieve check
├── requirements.txt       # Pinned dependencies
├── documents/             # Source documents (gitignored — each contributor adds their own)
├── rag.db                 # SQLite database (gitignored, generated by ingest.py)
└── venv/                  # Virtual environment (not committed to git)
```

## Progress

- [x] Foundry Local installed, chat model working (Week 1)
- [x] Embedding model discovered and tested, SQLite schema + retrieval (Week 2)
- [x] PDF ingestion pipeline (Week 3)
- [x] `answer_query()` + interactive CLI (Week 4)
- [ ] Pin remaining housekeeping / final write-up

## References

- Main source: [Building Your First Local RAG Application with Foundry Local](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-your-first-local-rag-application-with-foundry-local/4501968)
- Foundry Local SDK: [github.com/microsoft/Foundry-Local](https://github.com/microsoft/Foundry-Local)