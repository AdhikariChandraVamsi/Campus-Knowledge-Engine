"""
ChromaDB interface.
All vector operations go through this service.
No other part of the app imports chromadb directly.
"""
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings

# Singleton instances — loaded once, reused across requests
_chroma_client: Optional[chromadb.PersistentClient] = None
_collection = None
_embedding_model: Optional[SentenceTransformer] = None


def get_chroma_collection():
    """Lazy-load ChromaDB client and collection."""
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        _collection = _chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )
    return _collection


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load embedding model. Downloads on first call (~90MB)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedding_model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convert a list of text strings to embedding vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def store_chunks(
    chunks: List[dict],
    document_id: str,
    university_id: str,
) -> int:
    """
    Store chunks in ChromaDB.
    Each chunk dict must have: {id, text, metadata}
    metadata must include university_id for isolation filtering.
    Returns number of chunks stored.
    """
    collection = get_chroma_collection()

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Generate embeddings for all chunks at once (batched = faster)
    embeddings = embed_texts(texts)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(chunks)


def query_chunks(
    query_text: str,
    university_id: str,
    filters: dict,
    n_results: int = 5,
    exact_where: dict = None,
) -> List[dict]:
    """
    Semantic search with mandatory university_id isolation.
    filters: additional metadata filters (dept, semester, section, doc_type)
    Returns list of {text, metadata, similarity_score}
    """
    collection = get_chroma_collection()

    if exact_where is not None:
        where_clause = exact_where
    else:
        # Build the where clause — university_id is ALWAYS included
        where_clause = {"$and": [{"university_id": {"$eq": university_id}}]}
        for key, value in filters.items():
            if value:
                where_clause["$and"].append({key: {"$eq": value}})

        # If only one filter condition, simplify (ChromaDB requires $and for multiple)
        if len(where_clause["$and"]) == 1:
            where_clause = where_clause["$and"][0]

    query_embedding = embed_texts([query_text])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_clause,
        include=["documents", "metadatas", "distances"],
    )

    # Convert distances to similarity scores (cosine distance → similarity)
    output = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            similarity = 1 - distance  # ChromaDB cosine distance
            output.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity_score": round(similarity, 4),
            })

    return output


def delete_chunks_by_document(document_id: str) -> int:
    """Remove all chunks belonging to a document from ChromaDB."""
    collection = get_chroma_collection()
    results = collection.get(where={"document_id": {"$eq": document_id}})
    if results["ids"]:
        collection.delete(ids=results["ids"])
    return len(results["ids"])
