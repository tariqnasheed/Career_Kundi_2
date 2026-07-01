"""
agents/job_extractor/mock_data.py
====================================
Realistic mock page text and field extraction, keyed on URL domain
and keyword hints in the URL path/query string.

Used when settings.llm_mode == "mock" so the pipeline runs end-to-end
without real HTTP requests or LLM calls.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _path_keywords(url: str) -> str:
    try:
        return urlparse(url).path.lower()
    except Exception:
        return ""


def fake_page_text(url: str) -> str:
    """Return a realistic-looking scraped page text for the given URL."""
    domain = _domain(url)
    path = _path_keywords(url)

    # Generic tech-company job posting template, customised by URL hints
    role_hint = "Software Engineer"
    if "senior" in path or "sr" in path:
        role_hint = "Senior Software Engineer"
    elif "lead" in path or "principal" in path:
        role_hint = "Principal Engineer"
    elif "data" in path:
        role_hint = "Data Engineer"
    elif "product" in path:
        role_hint = "Product Manager"
    elif "design" in path:
        role_hint = "UX/UI Designer"
    elif "devops" in path or "sre" in path or "platform" in path:
        role_hint = "Platform Engineer (SRE)"
    elif "ml" in path or "machine" in path or "ai" in path:
        role_hint = "Machine Learning Engineer"

    company = domain.split(".")[0].capitalize() if domain else "TechCorp"

    return f"""
{company} Careers | {role_hint}

About {company}
{company} is a fast-growing technology company building the next generation of developer tooling.
We serve over 50,000 teams across 120 countries and are backed by leading venture capital firms.

Job Title: {role_hint}
Location: London, UK (Hybrid — 3 days in office)
Employment Type: Full-time, Permanent
Salary: £80,000 – £110,000 per year + equity + benefits
Posted: 2 weeks ago

About the Role
We're looking for a talented {role_hint} to join our engineering team. You'll work on
high-impact problems, collaborating with a team of world-class engineers to design, build,
and ship features used by millions of developers.

Responsibilities
- Design, develop, and maintain scalable backend services in Python and Go
- Collaborate with product and design teams to define technical requirements
- Review code, mentor junior engineers, and contribute to engineering best practices
- Participate in on-call rotation and help improve system reliability
- Write clear technical documentation and RFCs

Requirements
- 4+ years of professional software engineering experience
- Strong proficiency in Python or Go (or both)
- Experience with distributed systems and microservices architecture
- Familiarity with cloud platforms (AWS, GCP, or Azure)
- Excellent communication skills and ability to work in a remote-first team

Nice to Have
- Experience with Kubernetes and container orchestration
- Contributions to open-source projects
- Experience in a high-growth startup environment

Benefits
- Competitive salary and equity package
- 30 days annual leave + bank holidays
- Private health insurance (including dental and vision)
- £2,000 annual learning & development budget
- Home office setup allowance
- Regular team off-sites

How to Apply
Please apply via our careers portal. We review every application within 5 business days.
""".strip()


def extract_fields_from_text(raw_text: str, url: str) -> dict:
    """
    Pattern-match the fake page text to return structured fields.
    In live mode this would be an LLM call with a JSON schema.
    """
    domain = _domain(url)
    company = domain.split(".")[0].capitalize() if domain else "TechCorp"

    # Title
    title_match = re.search(r"Job Title:\s*(.+)", raw_text)
    title = title_match.group(1).strip() if title_match else "Software Engineer"

    # Location
    loc_match = re.search(r"Location:\s*(.+)", raw_text)
    location = loc_match.group(1).strip() if loc_match else "London, UK (Hybrid)"

    # Employment type
    emp_match = re.search(r"Employment Type:\s*(.+)", raw_text)
    employment_type = emp_match.group(1).strip() if emp_match else "Full-time"

    # Remote
    is_remote = "remote" in raw_text.lower() or "hybrid" in raw_text.lower()

    # Salary
    sal_match = re.search(r"Salary:\s*£?([\d,]+)\s*[–\-]+\s*£?([\d,]+)", raw_text)
    salary_min = float(sal_match.group(1).replace(",", "")) if sal_match else None
    salary_max = float(sal_match.group(2).replace(",", "")) if sal_match else None
    salary_currency = "GBP" if sal_match else None

    # Description
    desc_start = raw_text.find("About the Role")
    description_raw = raw_text[desc_start:desc_start + 800].strip() if desc_start > 0 else raw_text[:500]

    # Parse list sections
    def _extract_list_section(text: str, header: str) -> list[str]:
        pattern = re.compile(rf"{header}\n((?:- .+\n?)+)", re.IGNORECASE)
        m = pattern.search(text)
        if not m:
            return []
        lines = m.group(1).strip().split("\n")
        return [ln.lstrip("- ").strip() for ln in lines if ln.strip()]

    responsibilities = _extract_list_section(raw_text, "Responsibilities")
    requirements     = _extract_list_section(raw_text, "Requirements")
    benefits         = _extract_list_section(raw_text, "Benefits")

    return {
        "title": title,
        "company_name": company,
        "location": location,
        "employment_type": employment_type,
        "is_remote": is_remote,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "salary_currency": salary_currency,
        "description_raw": description_raw,
        "responsibilities": responsibilities or [
            "Build and ship scalable backend services",
            "Collaborate with cross-functional teams",
            "Participate in code reviews",
        ],
        "requirements": requirements or [
            "4+ years software engineering experience",
            "Strong Python or Go skills",
            "Distributed systems knowledge",
        ],
        "benefits": benefits or [
            "Competitive salary + equity",
            "30 days holiday",
            "Learning budget",
        ],
        "source_url": url,
    }
