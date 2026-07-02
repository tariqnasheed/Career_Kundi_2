from __future__ import annotations

TECHNOLOGY_PACK = {
    "domain_terms": [
        "IAM",
        "CloudWatch",
        "CloudTrail",
        "deployment pipeline",
        "rollback",
        "infrastructure as code",
        "CI/CD",
        "monitoring",
        "incident response",
    ],
    "verification_checks": [
        "check IAM permissions follow least privilege",
        "confirm deployment pipeline status",
        "review CloudWatch alarms and logs",
        "verify rollback plan before release",
        "confirm infrastructure changes are version-controlled",
    ],
    "safety_checks": [
        "avoid hard-coded secrets",
        "validate environment variables",
        "confirm monitoring and alerting coverage",
        "test rollback on a non-production environment",
    ],
    "common_mistakes": [
        "Deploying without a rollback plan.",
        "Using overly broad IAM permissions.",
        "Ignoring failed health checks after release.",
    ],
    "role_specific_examples": [
        "For example, during a production release, I verified IAM permissions, checked CloudWatch alarms, confirmed deployment pipeline status, rehearsed rollback, and reduced incident recovery time after a failed health check.",
    ],
    "interview_closings": [
        "In an interview, I would show that I can deliver reliable releases with observable pipelines, least-privilege access, and tested rollback plans.",
    ],
    "contamination_terms": ["contraindications", "case record trail", "milk texture", "BS 7671"],
}
