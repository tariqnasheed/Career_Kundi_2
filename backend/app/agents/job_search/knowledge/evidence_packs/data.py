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
        "Illustrative example: on a revenue dashboard, a data analyst could identify a many-to-many join inflating totals, add data-quality checks on source freshness, and compare query runtime before and after the change.",
    ],
    "interview_closings": [
        "In an interview, I would show that I can build reliable SQL analysis with sound joins, data quality controls, and performance awareness.",
    ],
    "contamination_terms": ["RCD", "allergen", "case law", "milk texture"],
}
