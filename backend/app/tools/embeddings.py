"""
tools/embeddings.py
=======================
Embedding model abstraction backing semantic search and the RAG vector
store (app/tools/rag.py).

Live mode uses Gemini's `text-embedding-004` via `langchain-google-genai`.
Mock/local mode uses `LocalHashEmbeddings`, a zero-dependency, deterministic
embedding function: it hashes n-grams of the input text into a fixed-size
float vector. This is NOT a real semantic embedding (it doesn't capture
meaning the way a trained model does — superficially similar n-grams score
as similar), but it is genuinely deterministic, fast, requires no model
download, and is enough to make FAISS similarity search, RAG retrieval, and
the Reflector's "did we retrieve relevant context" checks all exercise real
code paths in local development with zero setup. Swap in a real model
(Gemini embeddings, or `sentence-transformers/all-MiniLM-L6-v2`, already
declared in pyproject.toml as a dependency for this exact upgrade path) by
setting GEMINI_API_KEY — no other code changes needed.
"""

from __future__ import annotations

import hashlib
import math

from langchain_core.embeddings import Embeddings

from app.core.config import settings

EMBEDDING_DIM = 384  # Matches all-MiniLM-L6-v2's output dimensionality for drop-in compatibility


class LocalHashEmbeddings(Embeddings):
    """Deterministic, dependency-free embedding function for offline/mock mode."""

    def _embed(self, text: str) -> list[float]:
        tokens = text.lower().split()
        vector = [0.0] * EMBEDDING_DIM
        if not tokens:
            return vector
        # Hash every word + its bigram into a pseudo-random but deterministic
        # bucket, accumulating a simple bag-of-features vector. Normalizing
        # at the end gives cosine similarity sane behavior in FAISS.
        for i, token in enumerate(tokens):
            grams = [token]
            if i + 1 < len(tokens):
                grams.append(f"{token}_{tokens[i + 1]}")
            for gram in grams:
                digest = hashlib.sha256(gram.encode()).digest()
                bucket = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[bucket] += sign

        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


_EMBEDDINGS_CACHE: Embeddings | None = None


def get_embeddings() -> Embeddings:
    """Return the configured embedding model singleton, live Gemini or local fallback."""
    global _EMBEDDINGS_CACHE
    if _EMBEDDINGS_CACHE is None:
        if settings.llm_mode == "live":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            _EMBEDDINGS_CACHE = GoogleGenerativeAIEmbeddings(
                model=f"models/{settings.gemini_embedding_model}",
                google_api_key=settings.gemini_api_key,
            )
        else:
            _EMBEDDINGS_CACHE = LocalHashEmbeddings()
    return _EMBEDDINGS_CACHE
