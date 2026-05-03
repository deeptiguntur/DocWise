import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.schemas import UploadResponse
from services.ingestion import ingest_pdf
from db.database import get_db, Document

router = APIRouter(prefix="/api", tags=["upload"])

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 50)) * 1024 * 1024


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {os.getenv('MAX_FILE_SIZE_MB', 50)}MB limit.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = await ingest_pdf(tmp_path, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        os.unlink(tmp_path)

    doc = Document(
        id=result["doc_id"],
        filename=result["filename"],
        total_pages=result["total_pages"],
        total_chunks=result["total_chunks"],
    )
    db.add(doc)
    await db.commit()

    return UploadResponse(
        doc_id=result["doc_id"],
        filename=result["filename"],
        total_pages=result["total_pages"],
        total_chunks=result["total_chunks"],
        message=f"Successfully processed {result['total_chunks']} chunks from {result['total_pages']} pages.",
    )


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "doc_id": doc.id,
        "filename": doc.filename,
        "total_pages": doc.total_pages,
        "total_chunks": doc.total_chunks,
        "created_at": doc.created_at,
    }