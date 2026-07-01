"""
data/seed_graph.py
======================
Seed data for the GraphRAG knowledge graph (app/tools/graph_rag.py).

Defines a small but real graph of roles, skills, industries, and learning
resources with typed edges, so graph traversal queries like "what skills
bridge Data Analyst to Data Scientist" or "what should I learn after SQL
for a Data Engineer track" have real structure to traverse from the moment
the platform boots — before any live O*NET/ESCO scraping has run.

Edge types
----------
requires       role -> skill        (role requires this skill)
prerequisite_of skill -> skill       (skill A should be learned before skill B)
bridges        skill -> role        (skill is a common bridge into this role)
resource_for   resource -> skill     (resource teaches this skill)
related_to     skill -> skill        (lateral / complementary skills)
in_industry    role -> industry      (role commonly found in this industry)
"""

ROLES = [
    "Data Analyst",
    "Data Scientist",
    "Data Engineer",
    "Backend Engineer",
    "Senior Backend Engineer",
    "Frontend Engineer",
    "DevOps Engineer",
    "Engineering Manager",
]

SKILLS = [
    "SQL",
    "Python",
    "Statistics",
    "Machine Learning",
    "Data Visualization",
    "ETL Pipelines",
    "Distributed Systems",
    "System Design",
    "REST API Design",
    "Docker",
    "Kubernetes",
    "CI/CD",
    "React",
    "TypeScript",
    "Technical Leadership",
    "Mentoring",
]

INDUSTRIES = ["Technology", "Finance", "Healthcare", "E-commerce"]

# (role, skill, importance)
ROLE_REQUIRES_SKILL = [
    ("Data Analyst", "SQL", "critical"),
    ("Data Analyst", "Data Visualization", "high"),
    ("Data Analyst", "Statistics", "medium"),
    ("Data Scientist", "Python", "critical"),
    ("Data Scientist", "Statistics", "critical"),
    ("Data Scientist", "Machine Learning", "critical"),
    ("Data Scientist", "SQL", "high"),
    ("Data Engineer", "SQL", "critical"),
    ("Data Engineer", "ETL Pipelines", "critical"),
    ("Data Engineer", "Python", "high"),
    ("Data Engineer", "Distributed Systems", "high"),
    ("Backend Engineer", "REST API Design", "critical"),
    ("Backend Engineer", "SQL", "high"),
    ("Backend Engineer", "Python", "high"),
    ("Senior Backend Engineer", "System Design", "critical"),
    ("Senior Backend Engineer", "Distributed Systems", "critical"),
    ("Senior Backend Engineer", "Technical Leadership", "high"),
    ("Frontend Engineer", "React", "critical"),
    ("Frontend Engineer", "TypeScript", "high"),
    ("DevOps Engineer", "Docker", "critical"),
    ("DevOps Engineer", "Kubernetes", "critical"),
    ("DevOps Engineer", "CI/CD", "high"),
    ("Engineering Manager", "Technical Leadership", "critical"),
    ("Engineering Manager", "Mentoring", "critical"),
]

# (skill_a, skill_b) skill_a is a prerequisite of skill_b
SKILL_PREREQUISITES = [
    ("SQL", "ETL Pipelines"),
    ("Python", "Machine Learning"),
    ("Statistics", "Machine Learning"),
    ("REST API Design", "System Design"),
    ("Distributed Systems", "System Design"),
    ("Docker", "Kubernetes"),
    ("React", "TypeScript"),
]

# (skill, target_role) — the skill is a common bridge INTO this role from an adjacent one
SKILL_BRIDGES_ROLE = [
    ("Statistics", "Data Scientist"),
    ("Machine Learning", "Data Scientist"),
    ("Python", "Data Scientist"),
    ("Distributed Systems", "Senior Backend Engineer"),
    ("System Design", "Senior Backend Engineer"),
    ("Technical Leadership", "Engineering Manager"),
]

# (skill_a, skill_b) lateral / complementary relationship
SKILL_RELATED = [
    ("SQL", "ETL Pipelines"),
    ("Docker", "CI/CD"),
    ("Kubernetes", "CI/CD"),
    ("System Design", "Distributed Systems"),
    ("Machine Learning", "Data Visualization"),
]

# (role, industry)
ROLE_IN_INDUSTRY = [
    ("Data Analyst", "Finance"),
    ("Data Analyst", "E-commerce"),
    ("Data Scientist", "Technology"),
    ("Data Scientist", "Healthcare"),
    ("Data Engineer", "Technology"),
    ("Backend Engineer", "Technology"),
    ("Backend Engineer", "E-commerce"),
    ("DevOps Engineer", "Technology"),
]
