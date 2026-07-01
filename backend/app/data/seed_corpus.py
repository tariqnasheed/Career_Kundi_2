"""
data/seed_corpus.py
=======================
Hand-curated seed documents for the RAG vector store. Each entry is a real,
factually-written snippet (skill definitions, interview-pattern guidance,
learning-resource descriptions) with a `source` attribution so every
Reflector citation-integrity check (§3.6) has a real `source -> chunk`
mapping to validate against, even in mock/offline mode.

This is intentionally a SEED — small enough to read end-to-end, large
enough to make retrieval meaningfully different across different skills.
JobEnricherAgent / ResourceFinderAgent / StudyMaterialAgent expand on this
at runtime via live web scraping + Google Search grounding once API keys
are configured (see app/tools/scraper.py, app/tools/search.py).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedDocument:
    doc_id: str
    category: str  # skill_taxonomy | interview_pattern | learning_resource | career_advice
    title: str
    text: str
    source: str  # attribution shown in citations


SEED_DOCUMENTS: list[SeedDocument] = [
    # --- Skill taxonomy --------------------------------------------------------
    SeedDocument(
        "skill-python-001", "skill_taxonomy", "Python (programming language)",
        "Python is a high-level, interpreted, dynamically-typed programming language widely used in "
        "backend engineering, data science, and automation. Core competency areas for hiring assessment "
        "typically include: data structures (lists, dicts, sets, tuples), the GIL and concurrency models "
        "(threading vs multiprocessing vs asyncio), generators/iterators, decorators, context managers, "
        "packaging (pip/uv/poetry), and testing (pytest). Senior-level depth includes memory management, "
        "the descriptor protocol, metaclasses, and async I/O design at scale.",
        "O*NET Technology Skills Database — Programming Languages",
    ),
    SeedDocument(
        "skill-distsys-001", "skill_taxonomy", "Distributed Systems",
        "Distributed systems skills cover designing software that runs across multiple networked machines "
        "while tolerating partial failure. Core concepts: the CAP theorem, consensus algorithms (Raft, Paxos), "
        "consistent hashing, idempotency and exactly-once vs at-least-once delivery semantics, leader election, "
        "distributed transactions (2-phase commit, sagas), and observability at scale (distributed tracing).",
        "ACM Computing Curricula — Distributed and Parallel Computing",
    ),
    SeedDocument(
        "skill-sql-001", "skill_taxonomy", "SQL",
        "SQL competency for data and backend roles spans: joins and set operations, window functions, "
        "query plan analysis (EXPLAIN/ANALYZE), indexing strategy (B-tree vs hash vs GIN), normalization vs "
        "denormalization tradeoffs, transaction isolation levels, and writing migrations safely against "
        "production-scale tables (online schema change patterns).",
        "O*NET Technology Skills Database — Database Management Systems",
    ),
    SeedDocument(
        "skill-react-001", "skill_taxonomy", "React",
        "React skill assessment covers component composition, the rendering lifecycle and reconciliation, "
        "hooks (useState, useEffect, useMemo, useCallback, custom hooks), state management patterns (Context, "
        "Redux, Zustand), performance optimization (memoization, virtualization, code-splitting), and testing "
        "with React Testing Library.",
        "O*NET Technology Skills Database — Web Frameworks",
    ),
    SeedDocument(
        "skill-leadership-001", "skill_taxonomy", "Technical Leadership",
        "Technical leadership at the senior/staff level is evaluated on: setting technical direction across "
        "teams, mentoring and growing engineers, driving cross-functional consensus on architecture decisions, "
        "managing technical debt against delivery pressure, and communicating tradeoffs to non-technical "
        "stakeholders.",
        "ESCO Skills Taxonomy — Management and Leadership Competencies",
    ),
    # --- Interview patterns -----------------------------------------------------
    SeedDocument(
        "pattern-star-001", "interview_pattern", "STAR behavioral answer structure",
        "The STAR method structures a behavioral answer as Situation (context), Task (your specific "
        "responsibility), Action (what you actually did, in detail), and Result (quantified outcome). "
        "Strong answers spend the most time on Action and always end with a measurable Result.",
        "Careerkundi Interview Methodology Guide",
    ),
    SeedDocument(
        "pattern-system-design-001", "interview_pattern", "System design interview structure",
        "A strong system design answer: (1) clarifies functional + non-functional requirements and scale "
        "targets, (2) sketches a high-level architecture before diving into any one component, (3) walks "
        "through data model and API contracts, (4) identifies bottlenecks and discusses tradeoffs explicitly "
        "(consistency vs availability, latency vs cost), and (5) addresses failure modes and monitoring.",
        "Careerkundi Interview Methodology Guide",
    ),
    SeedDocument(
        "pattern-followups-001", "interview_pattern", "Interviewer follow-up question strategy",
        "Interviewers commonly probe an initial answer with: 'What would you do differently with more time?', "
        "'How would this scale 10x?', 'What's the failure mode of your chosen approach?', and 'How did you "
        "validate your assumption was correct?' — strong candidates anticipate at least one of these.",
        "Careerkundi Interview Methodology Guide",
    ),
    # --- Learning resources -------------------------------------------------------
    SeedDocument(
        "resource-python-async-001", "learning_resource", "Python asyncio — official documentation",
        "The official CPython asyncio documentation covers event loops, coroutines, tasks, and "
        "synchronization primitives in depth, with runnable examples for producer/consumer and "
        "fan-out/fan-in patterns relevant to high-throughput pipeline design.",
        "https://docs.python.org/3/library/asyncio.html",
    ),
    SeedDocument(
        "resource-distsys-mit-001", "learning_resource", "MIT 6.824 Distributed Systems (course)",
        "MIT's open courseware distributed systems class covers Raft consensus, distributed transactions, "
        "and fault tolerance with hands-on Go labs implementing a replicated key-value store.",
        "https://pdos.csail.mit.edu/6.824/",
    ),
    SeedDocument(
        "resource-sql-perf-001", "learning_resource", "Use The Index, Luke! (SQL indexing guide)",
        "A free, vendor-agnostic guide to SQL indexing and query performance, covering B-tree internals, "
        "composite index column order, and common anti-patterns that defeat an index.",
        "https://use-the-index-luke.com/",
    ),
    SeedDocument(
        "resource-react-docs-001", "learning_resource", "react.dev — Official React Documentation",
        "The official React documentation's 'Learn' section walks through component thinking, hooks, and "
        "performance with interactive sandboxes for every concept.",
        "https://react.dev/learn",
    ),
    SeedDocument(
        "resource-system-design-primer-001", "learning_resource", "The System Design Primer (GitHub)",
        "A widely-used open-source repository organizing system design concepts (caching, load balancing, "
        "database scaling, message queues) with diagrams and curated further reading per topic.",
        "https://github.com/donnemartin/system-design-primer",
    ),
    # --- Career advice -------------------------------------------------------------
    SeedDocument(
        "advice-data-to-ds-001", "career_advice", "Data Analyst to Data Scientist transition",
        "The most common bridging skills between Data Analyst and Data Scientist roles are: statistical "
        "inference and hypothesis testing, Python/R for modeling (beyond SQL/Excel), and applied machine "
        "learning fundamentals (train/test methodology, overfitting, feature engineering).",
        "Careerkundi Career Transitions Knowledge Base",
    ),
    SeedDocument(
        "advice-resume-keywords-001", "career_advice", "ATS keyword matching",
        "Applicant Tracking Systems rank resumes primarily on exact and near-exact keyword overlap with the "
        "job description's required skills and title; bullet points that restate the JD's specific tools "
        "and responsibilities (rather than generic synonyms) score measurably higher.",
        "Careerkundi Resume Optimization Knowledge Base",
    ),
]
