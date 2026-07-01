"""Static seed data: a small curated knowledge base for RAG + GraphRAG.

In production, this seed corpus is the *bootstrap* layer only — the
JobScraperAgent, ResourceFinderAgent, and friends continuously ingest fresh
scraped job postings, company pages, and learning-resource pages into the
same vector store / knowledge graph at runtime (see app/tools/rag.py
`add_documents` and app/tools/graph_rag.py `add_skill_resource_edge`). The
seed data below exists so RAG/GraphRAG retrieval returns *something real
and inspectable* the very first time the stack boots, before any live
scraping has happened.
"""
