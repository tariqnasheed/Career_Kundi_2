"""
Shared tool layer used by every agent: LLM providers, embeddings, the RAG
vector store, the GraphRAG knowledge graph, the web scraper, search
grounding, and the prompt/result cache. Agents never call an external API
directly — they always go through one of these tools, which is what makes
mock-mode (no API keys) a drop-in replacement for live mode everywhere.
"""
