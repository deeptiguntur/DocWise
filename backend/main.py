import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from db.database import init_db
from routers import upload, chat
from models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    os.makedirs(os.getenv("CHROMA_PERSIST_DIR", "./data/chroma"), exist_ok=True)
    yield


app = FastAPI(
    title="DocWise AI",
    description="Intelligent document agent — ask anything, know everything.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(chat.router)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        app="DocWise AI",
    )


@app.get("/")
async def root():
    return {
        "app": "DocWise AI",
        "tagline": "Ask anything. Know everything.",
        "docs": "/docs",
        "health": "/health",
    }