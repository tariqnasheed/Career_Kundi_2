"""
services/job_discovery.py
=============================
Discover live job postings from the web via SerpAPI (Google Jobs / organic
search). Used by the Job Search page's top discovery panel — distinct from
`GET /job-search/search` which only filters the user's already-saved jobs.

Mock mode returns realistic, query-aware listings so the UI can be exercised
without a SerpAPI key.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Well-known job boards — used to label source badges in the UI.
_JOB_BOARD_HOSTS = {
    "linkedin.com": "LinkedIn",
    "indeed.com": "Indeed",
    "glassdoor.com": "Glassdoor",
    "greenhouse.io": "Greenhouse",
    "lever.co": "Lever",
    "workday.com": "Workday",
    "jobs.lever.co": "Lever",
    "boards.greenhouse.io": "Greenhouse",
    "wellfound.com": "Wellfound",
    "angel.co": "AngelList",
    "monster.com": "Monster",
    "ziprecruiter.com": "ZipRecruiter",
}


def _source_site(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    for pattern, label in _JOB_BOARD_HOSTS.items():
        if pattern in host:
            return label
    return host.split(".")[0].capitalize() if host else "Web"


def _build_query(
    q: str | None,
    location: str | None,
    employment_type: str | None,
    remote: bool | None,
    experience_level: str | None,
) -> str:
    parts: list[str] = []
    if q and q.strip():
        parts.append(q.strip())
    else:
        parts.append("jobs")
    if location and location.strip():
        parts.append(f"in {location.strip()}")
    if remote is True:
        parts.append("remote")
    elif remote is False:
        parts.append("on-site")
    if employment_type and employment_type.strip():
        parts.append(employment_type.strip())
    if experience_level and experience_level.strip():
        parts.append(experience_level.strip())
    return " ".join(parts)


def _parse_title_company(title: str) -> tuple[str, str | None]:
    """Best-effort split of search result titles like 'Role - Company | LinkedIn'."""
    cleaned = re.sub(r"\s*[\|·]\s*(LinkedIn|Indeed|Glassdoor|Monster).*$", "", title, flags=re.I)
    for sep in (" - ", " – ", " | ", " at "):
        if sep in cleaned:
            left, right = cleaned.split(sep, 1)
            if len(left) > 2 and len(right) > 1:
                return left.strip(), right.strip()
    return cleaned.strip() or title, None


def _mock_discover(
    q: str | None,
    location: str | None,
    employment_type: str | None,
    remote: bool | None,
    url: str | None,
) -> list[dict]:
    """Deterministic mock listings shaped like live discovery results."""
    if url and url.strip():
        host = urlparse(url.strip()).netloc or "company.com"
        slug = urlparse(url.strip()).path.rstrip("/").split("/")[-1].replace("-", " ").title()
        return [{
            "title": slug or "Imported Role",
            "company_name": host.replace("www.", "").split(".")[0].capitalize(),
            "location": location or ("Remote" if remote else "London, UK"),
            "employment_type": employment_type or "Full-time",
            "is_remote": remote,
            "snippet": f"Job posting discovered at {host}. Click 'Use this job' to extract full details for interview prep and CV tailoring.",
            "source_url": url.strip(),
            "source_site": _source_site(url.strip()),
            "salary_hint": None,
            "verified": False,
        }]

    role = (q or "Software Engineer").strip()
    loc = location or ("Remote" if remote else "London, UK")
    companies = ["Stripe", "Monzo", "Revolut", "Deliveroo", "Bloomberg", "Google", "Meta", "Amazon"]
    results: list[dict] = []
    for i, company in enumerate(companies[:6]):
        title = role if i == 0 else f"{role} {'(Senior)' if i % 2 else ''}".strip()
        results.append({
            "title": title,
            "company_name": company,
            "location": loc,
            "employment_type": employment_type or ("Contract" if i == 3 else "Full-time"),
            "is_remote": remote if remote is not None else (i % 3 == 0),
            "snippet": (
                f"{company} is hiring a {title} in {loc}. "
                f"Requirements include relevant experience with technologies mentioned in your search. "
                f"[mock listing — configure SERPAPI_KEY for live web results]"
            ),
            "source_url": f"https://careers.example.com/{company.lower()}/{role.lower().replace(' ', '-')}-{i + 1}",
            "source_site": ["LinkedIn", "Indeed", "Glassdoor", "Greenhouse"][i % 4],
            "salary_hint": f"£{(60 + i * 8)}k – £{(85 + i * 10)}k" if i % 2 == 0 else None,
            "verified": False,
        })
    return results


async def _live_google_jobs(query: str, location: str | None) -> list[dict]:
    """SerpAPI Google Jobs engine."""
    params: dict = {
        "engine": "google_jobs",
        "q": query,
        "api_key": settings.serpapi_key,
        "hl": "en",
    }
    if location:
        params["location"] = location

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()

    results: list[dict] = []
    for item in data.get("jobs_results", [])[:15]:
        apply_link = ""
        for opt in item.get("apply_options") or []:
            if opt.get("link"):
                apply_link = opt["link"]
                break
        source_url = apply_link or item.get("share_link") or item.get("apply_link") or ""
        if not source_url:
            continue
        detected = item.get("detected_extensions") or {}
        results.append({
            "title": item.get("title") or "Untitled Role",
            "company_name": item.get("company_name"),
            "location": item.get("location"),
            "employment_type": detected.get("schedule_type") or item.get("schedule_type"),
            "is_remote": "remote" in (item.get("location") or "").lower() or detected.get("work_from_home"),
            "snippet": (item.get("description") or "")[:400],
            "source_url": source_url,
            "source_site": _source_site(source_url),
            "salary_hint": detected.get("salary") or item.get("salary"),
            "verified": True,
        })
    return results


async def _live_organic_jobs(query: str) -> list[dict]:
    """Fallback: organic Google search scoped to major job boards."""
    scoped = f'{query} (site:linkedin.com/jobs OR site:indeed.com OR site:glassdoor.com)'
    params = {
        "engine": "google",
        "q": scoped,
        "api_key": settings.serpapi_key,
        "num": 10,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()

    results: list[dict] = []
    for item in data.get("organic_results", [])[:10]:
        url = item.get("link", "")
        if not url:
            continue
        title, company = _parse_title_company(item.get("title", ""))
        results.append({
            "title": title,
            "company_name": company,
            "location": None,
            "employment_type": None,
            "is_remote": "remote" in (item.get("snippet") or "").lower(),
            "snippet": item.get("snippet") or "",
            "source_url": url,
            "source_site": _source_site(url),
            "salary_hint": None,
            "verified": True,
        })
    return results


async def discover_jobs(
    *,
    q: str | None = None,
    location: str | None = None,
    employment_type: str | None = None,
    remote: bool | None = None,
    experience_level: str | None = None,
    url: str | None = None,
) -> list[dict]:
    """
    Return job discovery hits from the public web. If `url` is set, return a
    single preview card for that posting (full extraction happens on parse).
    """
    if url and url.strip():
        if settings.search_mode != "live":
            return _mock_discover(q, location, employment_type, remote, url)
        return [{
            "title": urlparse(url.strip()).path.rstrip("/").split("/")[-1].replace("-", " ").title() or "Job posting",
            "company_name": urlparse(url.strip()).netloc.replace("www.", "").split(".")[0].capitalize(),
            "location": location,
            "employment_type": employment_type,
            "is_remote": remote,
            "snippet": f"Direct job URL from {_source_site(url.strip())}. Use 'Use this job' to extract the full posting.",
            "source_url": url.strip(),
            "source_site": _source_site(url.strip()),
            "salary_hint": None,
            "verified": True,
        }]

    query = _build_query(q, location, employment_type, remote, experience_level)

    if settings.search_mode != "live":
        logger.info("job_discovery_mock", query=query)
        return _mock_discover(q, location, employment_type, remote, None)

    try:
        results = await _live_google_jobs(query, location)
        if not results:
            results = await _live_organic_jobs(query)
        logger.info("job_discovery_live", query=query, count=len(results))
        return results
    except Exception as exc:
        logger.warning("job_discovery_failed", error=str(exc), query=query)
        return _mock_discover(q, location, employment_type, remote, None)
