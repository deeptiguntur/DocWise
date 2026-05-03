import os
from functools import lru_cache
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings


@lru_cache(maxsize=1)
def get_embeddings():
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
    )


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    collection = os.getenv("COLLECTION_NAME", "docwise_docs")
    os.makedirs(persist_dir, exist_ok=True)
    return Chroma(
        collection_name=collection,
        embedding_function=get_embeddings(),
        persist_directory=persist_dir,
    )


def search_chunks(query: str, doc_id: str, top_k: int = 5):
    vs = get_vector_store()
    results = vs.similarity_search_with_score(
        query=query,
        k=top_k,
        filter={"doc_id": doc_id},
    )
    return [
        {
            "text": doc.page_content,
            "page_number": doc.metadata.get("page_number"),
            "filename": doc.metadata.get("filename"),
            "score": round(float(score), 4),
        }
        for doc, score in results
    ]