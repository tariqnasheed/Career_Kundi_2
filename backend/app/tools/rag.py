"""
tools/rag.py
================
Retrieval-Augmented Generation: a local, file-persisted FAISS vector store
that every Executor agent queries BEFORE generating content, per the
platform-wide mandate in §3.6 ("No generation without retrieval").

Lifecycle
---------
1. On first boot, `get_vector_store()` builds a FAISS index from
   `app.data.seed_corpus.SEED_DOCUMENTS` and persists it to
   `settings.vector_store_url`.
2. On every subsequent boot, the persisted index is loaded from disk
   instead of being rebuilt (fast startup).
3. At runtime, `add_documents()` lets any agent (most notably
   JobScraperAgent and ResourceFinderAgent) ingest freshly scraped content
   into the SAME index, so RAG quality improves the more the platform is
   used — this is the "continuously ingest" behavior described in
   app/data/__init__.py.

Semantic deduplication (§3.3) is implemented in `add_documents`: before
inserting a new chunk we check its cosine similarity against existing
vectors and skip near-duplicates (similarity > 0.95) to avoid bloating the
index and wasting context-window budget on redundant retrieval.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import get_logger
from app.data.seed_corpus import SEED_DOCUMENTS
from app.tools.embeddings import get_embeddings

logger = get_logger(__name__)

_VECTOR_STORE_SINGLETON = None

SEMANTIC_DEDUP_THRESHOLD = 0.95  # cosine similarity above which a new chunk is considered a duplicate


def _seed_documents_as_langchain_docs() -> list[Document]:
    """Convert the static seed corpus into LangChain `Document` objects with source metadata."""
    return [
        Document(
            page_content=f"{doc.title}\n\n{doc.text}",
            metadata={"doc_id": doc.doc_id, "category": doc.category, "source": doc.source, "title": doc.title},
        )
        for doc in SEED_DOCUMENTS
    ]


def get_vector_store():
    """
    Return the process-wide FAISS vector store singleton, building it from
    the seed corpus on first call (and persisting to disk) or loading the
    previously persisted index on subsequent calls / restarts.
    """
    global _VECTOR_STORE_SINGLETON
    if _VECTOR_STORE_SINGLETON is not None:
        return _VECTOR_STORE_SINGLETON

    from langchain_community.vectorstores import FAISS

    store_path = Path(settings.vector_store_url)
    embeddings = get_embeddings()

    if (store_path / "index.faiss").exists():
        logger.info("vector_store_loading_from_disk", path=str(store_path))
        _VECTOR_STORE_SINGLETON = FAISS.load_local(
            str(store_path), embeddings, allow_dangerous_deserialization=True
        )
    else:
        logger.info("vector_store_building_from_seed_corpus", num_docs=len(SEED_DOCUMENTS))
        store_path.mkdir(parents=True, exist_ok=True)
        docs = _seed_documents_as_langchain_docs()
        _VECTOR_STORE_SINGLETON = FAISS.from_documents(docs, embeddings)
        _VECTOR_STORE_SINGLETON.save_local(str(store_path))

    return _VECTOR_STORE_SINGLETON


def retrieve(query: str, k: int = 5, category: str | None = None) -> list[Document]:
    """
    Top-k similarity search against the vector store, optionally filtered to
    one seed-corpus `category` (skill_taxonomy | interview_pattern |
    learning_resource | career_advice). This is the function every
    Executor agent calls before constructing its generation prompt.
    """
    store = get_vector_store()
    # Over-fetch then filter client-side — FAISS's metadata filtering support
    # varies by LangChain version, so this keeps the call site simple and
    # version-agnostic.
    raw_results = store.similarity_search(query, k=k * 3 if category else k)
    if category:
        raw_results = [d for d in raw_results if d.metadata.get("category") == category]
    return raw_results[:k]


def add_documents(documents: list[Document]) -> int:
    """
    Ingest freshly retrieved content (scraped job postings, company pages,
    resource pages) into the persistent vector store, applying semantic
    deduplication first. Returns the number of documents actually inserted
    (after dedup).
    """
    if not documents:
        return 0

    store = get_vector_store()

    # Semantic dedup: embed each candidate and skip it if a near-identical
    # vector already exists in the index (§3.3 "Semantic Deduplication").
    to_insert = []
    for doc in documents:
        # `similarity_search_with_relevance_scores` embeds the query text
        # internally, so we pass the raw content straight in rather than
        # embedding it a second time here (the previous `query_vec` line was a
        # redundant, unused embedding call — pure wasted cost per document).
        existing = store.similarity_search_with_relevance_scores(doc.page_content, k=1)
        if existing:
            _, score = existing[0]
            if score >= SEMANTIC_DEDUP_THRESHOLD:
                continue
        to_insert.append(doc)

    if to_insert:
        store.add_documents(to_insert)
        store.save_local(settings.vector_store_url)
        logger.info("vector_store_documents_ingested", count=len(to_insert), skipped=len(documents) - len(to_insert))

    return len(to_insert)


def format_context_for_prompt(documents: list[Document], max_chars: int = 4000) -> str:
    """
    Render retrieved documents into a numbered, citable context block ready
    to splice into an Executor's prompt, e.g.:

        [1] Source: O*NET Technology Skills Database — Programming Languages
        Python is a high-level, interpreted...

    Truncates to `max_chars` (§3.3 "Context Window Optimization" — keep
    injected context under ~4k tokens) by greedily including documents in
    relevance order until the budget is spent.
    """
    lines: list[str] = []
    used = 0
    for i, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "unknown source")
        snippet = f"[{i}] Source: {source}\n{doc.page_content.strip()}\n"
        if used + len(snippet) > max_chars and lines:
            break
        lines.append(snippet)
        used += len(snippet)
    return "\n".join(lines)


def citations_from_documents(documents: list[Document]) -> list[dict]:
    """Build the `[{"n": 1, "title": ..., "source": ...}]` citation list paired with `format_context_for_prompt`."""
    return [
        {"n": i, "title": doc.metadata.get("title", "Untitled"), "source": doc.metadata.get("source", "")}
        for i, doc in enumerate(documents, start=1)
    ]
