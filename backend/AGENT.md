# DocWise AI — Project Spec (AGENT.md)

## What it is
An intelligent document agent that answers questions from PDFs, summarizes content,
creates notes, generates quizzes, and searches the web when needed.

## Assistant persona
Name: **Wise**
Personality: knowledgeable, concise, friendly, always cites sources

## Tech stack
- **Backend**: FastAPI + Python 3.11
- **Agent**: LangGraph ReAct loop
- **LLM**: Groq (llama-3.1-8b-instant)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector store**: ChromaDB (persisted locally)
- **PDF parsing**: pdfplumber
- **Web search**: Tavily API
- **Database**: SQLite via SQLAlchemy async
- **Streaming**: FastAPI SSE (StreamingResponse)
- **Frontend**: React + Vite + Tailwind (separate)
- **Hosting**: Railway (backend), Vercel (frontend)

## Folder structure
backend/
  main.py              # FastAPI app, CORS, lifespan
  routers/
    upload.py          # POST /api/upload, GET /api/documents/{doc_id}
    chat.py            # POST /api/chat/stream, GET/DELETE /api/chat/history
  services/
    ingestion.py       # parse → chunk → embed → store
    vector_store.py    # ChromaDB wrapper, search_chunks()
    agent.py           # LangGraph ReAct agent, run_agent_stream()
  tools/
    agent_tools.py     # 5 tools: search_pdf, web_search, summarize, generate_quiz, direct_answer
  models/
    schemas.py         # Pydantic request/response models
  db/
    database.py        # SQLAlchemy models: Document, ChatMessage
  requirements.txt
  .env.example
  AGENT.md             # this file

## Agent tools
| Tool | When to use |
|------|-------------|
| search_pdf | Content inside the uploaded PDF |
| web_search | Current events, facts not in doc |
| summarize | Chapter/section/page range summaries |
| generate_quiz | Flashcards, MCQ, study questions |
| direct_answer | Greetings, general knowledge, no retrieval needed |

## API endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/upload | Upload and ingest PDF |
| GET | /api/documents/{doc_id} | Get document metadata |
| POST | /api/chat/stream | SSE streaming chat |
| GET | /api/chat/history/{session_id} | Get chat history |
| DELETE | /api/chat/history/{session_id} | Clear chat history |

## SSE stream format
- `data: [TOOL:tool_name]` — agent selected a tool
- `data: token` — streamed response token
- `data: [DONE]` — stream complete

## Environment variables
See .env.example for all required keys.
