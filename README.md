# ContextIQ — AI Conversational Assistant (RAG + LangGraph)

A complete portfolio-ready **document question-answering app** with a polished responsive frontend, FastAPI backend, LangGraph workflow, document upload, grounded responses, and source excerpts.

## Run locally

Requires Python 3.10+.

```bash
cd backend
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
# Optional: set OPENAI_API_KEY to enable generated answers
uvicorn main:app --reload --port 8000
```

Open `frontend/index.html` in your browser (or serve it with `python -m http.server 5500` from the frontend folder). Upload `sample_document.txt` and ask **“What are the limitations?”**

### API key

- macOS/Linux: `export OPENAI_API_KEY='your-key'`
- Windows PowerShell: `$env:OPENAI_API_KEY='your-key'`
- Optional: `OPENAI_MODEL=gpt-4o-mini` (default)
- Never put API keys in frontend files or Git commits.

## Architecture

`Browser → FastAPI → LangGraph (retrieve → answer) → OpenAI (optional)`

- PDF extraction: pypdf
- Chunking: overlapping character windows
- Retrieval: lexical term-frequency ranking (a simple, transparent RAG baseline, **not vector search**)
- Answer generation: OpenAI chat completion, constrained to retrieved context
- Sources: named documents and numbered excerpts
- Storage: in-memory (resets on restart)

## API

- `GET /api/health`
- `GET /api/documents`
- `POST /api/upload` (multipart file)
- `DELETE /api/documents/{id}`
- `POST /api/chat` with `{"question":"..."}`

## Public deployment

Deploy backend to a Python hosting provider using `pip install -r requirements.txt` and `uvicorn main:app --host 0.0.0.0 --port $PORT`. Configure `OPENAI_API_KEY` as a server-side secret. Host `frontend/` as a static site and change the `API` constant in `frontend/app.js` to your backend HTTPS URL. Add authentication, rate limiting, persistent document storage, restricted CORS, and a privacy policy **before** accepting real user documents. A public URL is not created automatically.

## Portfolio description

**ContextIQ — AI Knowledge Assistant** | Python, FastAPI, LangGraph, OpenAI API, JavaScript, HTML/CSS

Built an interactive document Q&A app with PDF/TXT upload, retrieval-augmented answers, source-backed responses, and a responsive dashboard. Implemented a LangGraph retrieval-to-generation workflow and a no-key retrieval fallback. Designed REST APIs for document ingestion and chat. **Source:** [Add your GitHub repository] · **Live demo:** [Add deployed URL]

## Important notes

This is a new portfolio demonstration, not evidence that this exact code was used at a prior employer. Do not upload proprietary or sensitive employer documents. No public demo URL is included until you deploy it.
