# thesis-generator (ARAS prototype)

`thesis-generator` is a small prototype of an **Autonomous Research Agent System (ARAS)** built around a LangGraph supervisor/worker loop. It is currently focused on:

- A typed global state (`ThesisState`) shared across nodes
- A runnable LangGraph (`build_main_graph`) with researcher → writer → validator loops
- A CLI that generates Markdown output
- A FastAPI app that streams graph events
- Tool stubs for ingest/RAG, OpenAlex, PDF parsing, Scite tallies, and sandboxed code execution

This repository is intentionally lightweight: it provides testable scaffolding for an agentic thesis workflow, not a full thesis-quality generator yet.

## Current implementation status

What works today:

- **State model**: `src/thesis_generator/state.py` defines the core schema and a reducer.
- **Graph orchestration**: `src/thesis_generator/graph/builder.py` compiles a LangGraph with a supervisor router.
- **Researcher/Writer/Validator**:
  - Researcher enriches the state with perspectives/documents (currently search is injectable; default is no external fetch).
  - Writer drafts a minimal manuscript and enforces citation markers in each paragraph.
  - Validator scores documents via Scite tallies or a fallback and flags suspicious sources.
- **Tools**:
  - In-memory parent/child “vector store” ingest and keyword overlap search.
  - OpenAlex wrapper (via `pyalex`, optional at runtime) with pagination tests.
  - PDF → text/Markdown conversion with fallbacks (Docling → Unstructured → PyPDF2).
  - E2B sandbox execution wrapper with network egress blocked (tested via fakes).
- **Interfaces**:
  - CLI (`python -m thesis_generator.main`) outputs Markdown.
  - FastAPI app (`create_app`) streams JSON events.

## Requirements

- Python 3.11+
- Poetry (recommended) or another environment manager

## Setup

```bash
poetry install
```

## Environment variables

Copy the example file and set the values:

```bash
cp .env.example .env
```

This project does not automatically load `.env` at runtime yet; make sure the variables are present in your environment (for example via `direnv`, your shell profile, or exporting them before running commands).

Required:

- `OPENAI_API_KEY` (required by the current config loader even if you are not calling OpenAI yet)
- `SCITE_API_KEY` (used by `thesis_generator.tools.citation_check` for Scite tallies)

Optional:

- `OPENALEX_MAILTO` (recommended by OpenAlex; used by `pyalex` configuration)
- `E2B_API_KEY` (required only if you actually run E2B-backed sandbox execution)
- `LANGCHAIN_TRACING_V2`, `LANGCHAIN_ENDPOINT`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT` (LangSmith tracing)

Notes on Scite auth:

- This prototype currently sends `SCITE_API_KEY` as an `x-api-key` header to the tallies endpoint in `src/thesis_generator/tools/citation_check.py`.
- Scite’s public docs also describe Bearer tokens for restricted endpoints. If your account uses Bearer auth, you may need to adapt the client accordingly.

## Usage

### 1) CLI (generate Markdown)

```bash
poetry run python -m thesis_generator.main \
  --topic "Evaluating RAG systems" \
  --target-word-count 1200 \
  --style-guide apa \
  --output output/thesis.md
```

### 2) API server (stream events)

Run the FastAPI app:

```bash
poetry run uvicorn thesis_generator.app:create_app --factory --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl -s http://127.0.0.1:8000/health
```

Start a run (streams newline-delimited JSON events):

```bash
curl -N -X POST http://127.0.0.1:8000/run \
  -H 'Content-Type: application/json' \
  -d '{"topic":"Realtime systems","target_word_count":1200,"style_guide":"apa"}'
```

## Tool examples (library usage)

These are Python APIs used by agents/tests.

- Ingest + search: `thesis_generator.tools.ingest.ingest_documents`, `search_sections`
- OpenAlex: `thesis_generator.tools.openalex.OpenAlexAPI` (or `openalex_search` / `openalex_get_paper` tools)
- PDF parsing: `thesis_generator.tools.pdf_parser.parse_pdf_from_url`
- Scite tallies: `thesis_generator.tools.citation_check.check_citations`
- Sandbox execution: `thesis_generator.tools.code_execution.execute_python`

## Development

Run tests:

```bash
poetry run pytest
```

Lint/typecheck:

```bash
poetry run ruff check .
poetry run mypy src
```
