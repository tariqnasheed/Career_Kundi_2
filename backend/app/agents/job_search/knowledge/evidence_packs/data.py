from __future__ import annotations

DATA_PACK = {
    "domain_terms": [
        "joins",
        "aggregation",
        "data quality",
        "query performance",
        "schema design",
        "normalisation",
        "indexing",
        "data lineage",
    ],
    "verification_checks": [
        "validate source data completeness and freshness",
        "check join keys and cardinality assumptions",
        "review query execution plans for performance",
        "confirm aggregation logic against business definitions",
    ],
    "safety_checks": [
        "mask or restrict sensitive fields",
        "document data quality exceptions",
        "validate outputs against control totals",
    ],
    "common_mistakes": [
        "Joining tables without understanding cardinality.",
        "Reporting aggregates without handling nulls consistently.",
        "Shipping dashboards without data quality checks.",
    ],
    "role_specific_examples": [
        "For example, on a revenue dashboard, I fixed a many-to-many join inflating totals, added data quality checks on source freshness, and cut query runtime from 48 seconds to 6 seconds.",
    ],
    "interview_closings": [
        "In an interview, I would show that I can build reliable SQL analysis with sound joins, data quality controls, and performance awareness.",
    ],
    "contamination_terms": ["RCD", "allergen", "case law", "milk texture"],
}
