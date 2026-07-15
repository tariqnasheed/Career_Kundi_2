"""
tools/embeddings.py
=======================
Embedding model abstraction backing semantic search and the RAG vector
store (app/tools/rag.py).

Current behavior
----------------
Uses `LocalHashEmbeddings`, a zero-dependency, deterministic embedding
function suitable for local development and tests. This is NOT a trained
semantic embedding model.

LLM-R2 (deferred): migrate embeddings to a local Ollama / sentence-transformers
path aligned with the local Ollama 8B LLM provider. Do not use cloud Gemini
embeddings as the active CareerKundi path.

Deprecated legacy Gemini embedding settings may still exist on `Settings`
(`gemini_embedding_model`, `gemini_api_key`) but are not used here.
"""

from __future__ import annotations

import hashlib
import math

from langchain_core.embeddings import Embeddings

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
    """Return the local embedding singleton (Gemini path removed; see LLM-R2)."""
    global _EMBEDDINGS_CACHE
    if _EMBEDDINGS_CACHE is None:
        _EMBEDDINGS_CACHE = LocalHashEmbeddings()
    return _EMBEDDINGS_CACHE
