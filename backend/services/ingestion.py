import pdfplumber
import uuid
import os
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from services.vector_store import get_vector_store


def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "text": text.strip(),
                    "page_number": i + 1,
                    "total_pages": len(pdf.pages),
                })
    return pages


def chunk_pages(pages: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for page in pages:
        splits = splitter.split_text(page["text"])
        for split in splits:
            chunks.append({
                "text": split,
                "page_number": page["page_number"],
                "total_pages": page["total_pages"],
            })
    return chunks


async def ingest_pdf(file_path: str, filename: str) -> Dict[str, Any]:
    doc_id = str(uuid.uuid4())
    chunk_size = int(os.getenv("CHUNK_SIZE", 512))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 50))

    pages = parse_pdf(file_path)
    if not pages:
        raise ValueError("No extractable text found in PDF.")

    chunks = chunk_pages(pages, chunk_size, chunk_overlap)

    vs = get_vector_store()
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "page_number": c["page_number"],
            "total_pages": c["total_pages"],
        }
        for c in chunks
    ]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    vs.add_texts(texts=documents, metadatas=metadatas, ids=ids)

    return {
        "doc_id": doc_id,
        "filename": filename,
        "total_pages": pages[0]["total_pages"] if pages else 0,
        "total_chunks": len(chunks),
    }