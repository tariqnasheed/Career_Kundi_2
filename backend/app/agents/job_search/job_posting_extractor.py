"""Job posting URL extraction for interview-pack generation (Iteration 004E-B).

Layered extraction: Schema.org JSON-LD JobPosting → OpenGraph/meta → HTML section
headings → light cleanup. Uses BeautifulSoup + httpx (existing dependencies).

Research note: many ATS and job boards expose JobPosting via application/ld+json;
see https://schema.org/JobPosting for field mapping.
"""

from __future__ import annotations

import html as html_module
import ipaddress
import json
import re
import socket
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_BULLET_LEN = 500
_MAX_REDIRECTS = 3
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB
_REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})
_NOISE_PATTERNS = (
    r"apply now",
    r"cookie",
    r"privacy policy",
    r"sign in",
    r"subscribe",
    r"accept all",
)

_SECTION_ALIASES: dict[str, str] = {
    "responsibilities": "responsibilities",
    "duties": "responsibilities",
    "what you will do": "responsibilities",
    "what you'll do": "responsibilities",
    "about the role": "responsibilities",
    "key responsibilities": "responsibilities",
    "requirements": "requirements",
    "minimum qualifications": "requirements",
    "basic qualifications": "requirements",
    "required qualifications": "requirements",
    "qualifications": "requirements",
    "preferred qualifications": "preferred_qualifications",
    "nice to have": "preferred_qualifications",
    "preferred skills": "preferred_qualifications",
    "skills": "skills",
    "tools": "tools",
    "software": "tools",
    "experience": "requirements",
    "education": "requirements",
    "benefits": "benefits",
    "about the company": "company_profile",
    "about us": "company_profile",
    "location": "location",
    "employment type": "employment_type",
}

_WARN_NO_JSON_LD = (
    "No Schema.org JobPosting JSON-LD was found; used readable page text fallback."
)
_WARN_PARTIAL = (
    "Only partial job details were extracted. Paste the full job description for stronger results."
)
_WARN_NO_USEFUL_INFO = (
    "No useful job posting information could be extracted from this link. "
    "Paste the full job description manually for stronger results."
)
_WARN_FETCH_FAILED_SAFE = (
    "The job posting URL could not be fetched safely. "
    "Paste the job description manually for stronger results."
)
_WARN_UNSAFE_REDIRECT = (
    "The job posting URL redirected to an unsafe location. "
    "Paste the job description manually for stronger results."
)
_WARN_RESPONSE_TOO_LARGE = (
    "The job posting page was too large to fetch safely. "
    "Paste the job description manually for stronger results."
)
_WARN_INVALID_URL = "Only http and https URLs are supported."


@dataclass
class JobPostingExtractionResult:
    source_url: str
    final_url: str | None = None
    title: str | None = None
    company_name: str | None = None
    company_profile: str | None = None
    description: str | None = None
    responsibilities: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    preferred_qualifications: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    location: str | None = None
    seniority: str | None = None
    employment_type: str | None = None
    date_posted: str | None = None
    valid_through: str | None = None
    salary_text: str | None = None
    extraction_confidence: str = "failed"
    extraction_methods: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_status: dict[str, str] = field(default_factory=dict)


def extraction_to_dict(result: JobPostingExtractionResult) -> dict[str, Any]:
    return asdict(result)


def _norm(text: str | None) -> str:
    if not text:
        return ""
    text = html_module.unescape(str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _dedupe_list(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _norm(item)
        if not text or len(text) > _MAX_BULLET_LEN:
            continue
        key = text.lower()
        if key in seen:
            continue
        if any(re.search(p, key) for p in _NOISE_PATTERNS):
            continue
        seen.add(key)
        out.append(text)
    return out


def _is_job_posting_type(value: Any) -> bool:
    if isinstance(value, str):
        return "JobPosting" in value
    if isinstance(value, list):
        return any(_is_job_posting_type(v) for v in value)
    return False


def _find_job_posting_object(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        for item in data:
            found = _find_job_posting_object(item)
            if found:
                return found
    elif isinstance(data, dict):
        if _is_job_posting_type(data.get("@type")):
            return data
        graph = data.get("@graph")
        if graph is not None:
            found = _find_job_posting_object(graph)
            if found:
                return found
        for value in data.values():
            if isinstance(value, (dict, list)):
                found = _find_job_posting_object(value)
                if found:
                    return found
    return None


def extract_json_ld_job_posting(html: str) -> dict[str, Any] | None:
    """Return the first Schema.org JobPosting object found in JSON-LD blocks."""
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", type=lambda t: t and "ld+json" in t.lower()):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        posting = _find_job_posting_object(data)
        if posting:
            return posting
    return None


def _org_name(org: Any) -> str | None:
    if isinstance(org, str):
        return _norm(org) or None
    if isinstance(org, dict):
        return _norm(org.get("name")) or None
    return None


def _org_description(org: Any) -> str | None:
    if isinstance(org, dict):
        return _norm(org.get("description") or org.get("employerOverview")) or None
    return None


def _location_text(loc: Any) -> str | None:
    if isinstance(loc, str):
        return _norm(loc) or None
    if isinstance(loc, dict):
        if loc.get("@type") == "Place" or "address" in loc:
            addr = loc.get("address")
            if isinstance(addr, dict):
                parts = [
                    addr.get("addressLocality"),
                    addr.get("addressRegion"),
                    addr.get("addressCountry"),
                ]
                joined = ", ".join(_norm(str(p)) for p in parts if p)
                return joined or None
            return _norm(str(addr)) or None
        return _norm(loc.get("name")) or None
    if isinstance(loc, list) and loc:
        return _location_text(loc[0])
    return None


def _salary_text(salary: Any) -> str | None:
    if isinstance(salary, dict):
        val = salary.get("value") or salary
        if isinstance(val, dict):
            min_v = val.get("minValue") or val.get("value")
            max_v = val.get("maxValue")
            unit = val.get("unitText") or salary.get("currency")
            if min_v and max_v:
                return _norm(f"{min_v} - {max_v} {unit or ''}")
            if min_v:
                return _norm(f"{min_v} {unit or ''}")
        return _norm(str(salary)) or None
    return _norm(str(salary)) if salary else None


def _list_from_field(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"[\n•;]", value)
        return _dedupe_list([p.lstrip("-* ").strip() for p in parts if p.strip()])
    if isinstance(value, list):
        items: list[str] = []
        for v in value:
            if isinstance(v, str):
                items.append(v)
            elif isinstance(v, dict):
                items.append(_norm(v.get("name") or v.get("description") or str(v)))
        return _dedupe_list(items)
    return []


def _map_json_ld_posting(posting: dict[str, Any]) -> dict[str, Any]:
    org = posting.get("hiringOrganization") or posting.get("employer")
    reqs = _list_from_field(posting.get("qualifications"))
    reqs.extend(_list_from_field(posting.get("experienceRequirements")))
    reqs.extend(_list_from_field(posting.get("educationRequirements")))
    preferred = _list_from_field(posting.get("preferredQualifications"))
    skills = _list_from_field(posting.get("skills"))
    responsibilities = _list_from_field(posting.get("responsibilities"))
    description = _norm(posting.get("description"))
    if not responsibilities and description:
        responsibilities = _split_description_bullets(description, "responsibilities")

    employment = posting.get("employmentType")
    if isinstance(employment, list):
        employment = ", ".join(str(e) for e in employment)
    employment = _norm(str(employment)) if employment else None

    return {
        "title": _norm(posting.get("title") or posting.get("name")) or None,
        "company_name": _org_name(org),
        "company_profile": _org_description(org),
        "description": description or None,
        "responsibilities": responsibilities,
        "requirements": _dedupe_list(reqs),
        "preferred_qualifications": preferred,
        "skills": skills,
        "location": _location_text(posting.get("jobLocation")),
        "employment_type": employment,
        "date_posted": _norm(str(posting.get("datePosted") or "")) or None,
        "valid_through": _norm(str(posting.get("validThrough") or "")) or None,
        "salary_text": _salary_text(posting.get("baseSalary") or posting.get("estimatedSalary")),
    }


def _meta_content(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return _norm(tag["content"]) or None
    return None


def _extract_meta_fallback(soup: BeautifulSoup) -> dict[str, Any]:
    title = _meta_content(soup, "og:title", "twitter:title") or (
        _norm(soup.title.string) if soup.title and soup.title.string else None
    )
    description = _meta_content(soup, "og:description", "description", "twitter:description")
    company = _meta_content(soup, "og:site_name")
    canonical = soup.find("link", rel=lambda r: r and "canonical" in r)
    return {
        "title": title,
        "company_name": company,
        "description": description,
        "canonical_url": canonical.get("href") if canonical else None,
    }


def _heading_key(text: str) -> str | None:
    lowered = _norm(text).lower().rstrip(":")
    matches: list[tuple[int, str]] = []
    for alias, key in _SECTION_ALIASES.items():
        if alias in lowered or lowered == alias:
            matches.append((len(alias), key))
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][1]


def _bullets_from_element(el) -> list[str]:
    items: list[str] = []
    for li in el.find_all("li"):
        text = _norm(li.get_text(" ", strip=True))
        if text:
            items.append(text)
    if not items:
        for p in el.find_all("p"):
            text = _norm(p.get_text(" ", strip=True))
            if text and len(text) > 20:
                items.append(text)
    return _dedupe_list(items)


def extract_job_sections_from_text(text: str) -> dict[str, list[str] | str]:
    """Detect labeled sections in plain text (headings followed by bullets or paragraphs)."""
    sections: dict[str, list[str]] = {
        "responsibilities": [],
        "requirements": [],
        "preferred_qualifications": [],
        "skills": [],
        "tools": [],
        "company_profile": [],
    }
    current_key: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            key = _heading_key(stripped.lstrip("#").strip())
            current_key = key
            continue
        if len(stripped) < 80 and stripped.endswith(":"):
            key = _heading_key(stripped)
            if key:
                current_key = key
                continue
        if len(stripped) < 60:
            key = _heading_key(stripped)
            if key:
                current_key = key
                continue
        bullet = stripped.lstrip("-•* ").strip()
        if not bullet or not current_key:
            continue
        if current_key == "company_profile":
            sections["company_profile"].append(bullet)
        elif current_key in sections:
            sections[current_key].append(bullet)
    for k, v in sections.items():
        sections[k] = _dedupe_list(v)  # type: ignore[assignment]
    return sections


def _extract_html_sections(soup: BeautifulSoup) -> dict[str, Any]:
    sections: dict[str, list[str]] = {
        "responsibilities": [],
        "requirements": [],
        "preferred_qualifications": [],
        "skills": [],
        "tools": [],
        "company_profile": [],
    }
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "strong", "b"]):
        key = _heading_key(heading.get_text(" ", strip=True))
        if not key:
            continue
        sibling = heading.find_next_sibling()
        collected: list[str] = []
        while sibling and sibling.name not in ("h1", "h2", "h3", "h4"):
            if sibling.name in ("ul", "ol"):
                collected.extend(_bullets_from_element(sibling))
            elif sibling.name == "p":
                text = _norm(sibling.get_text(" ", strip=True))
                if text:
                    collected.append(text)
            sibling = sibling.find_next_sibling()
        if key in sections and collected:
            sections[key].extend(collected)
    for k in list(sections.keys()):
        sections[k] = _dedupe_list(sections[k])
    return sections


def _split_description_bullets(description: str, kind: str) -> list[str]:
    """Pull bullet-like lines from a long description block."""
    items: list[str] = []
    for line in description.splitlines():
        text = line.strip().lstrip("-•* ")
        if len(text) < 15:
            continue
        if kind == "responsibilities" and any(
            w in text.lower() for w in ("responsible", "manage", "support", "develop", "lead", "build")
        ):
            items.append(text)
    return _dedupe_list(items)[:12]


def _readable_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)


def _compute_confidence(mapped: dict[str, Any], methods: list[str]) -> str:
    if "json_ld" in methods:
        if mapped.get("title") and mapped.get("description") and (
            mapped.get("responsibilities") or mapped.get("requirements")
        ):
            return "high"
        if mapped.get("title") and (mapped.get("description") or mapped.get("company_name")):
            return "medium"

    text_field_count = sum(
        1 for k in ("title", "description", "company_name", "location", "employment_type") if mapped.get(k)
    )
    list_item_count = sum(
        len(mapped.get(k) or [])
        for k in ("responsibilities", "requirements", "preferred_qualifications", "skills", "tools")
    )

    # HTML section extraction often has strong list signals even without title/meta.
    if list_item_count >= 4 or (list_item_count >= 2 and text_field_count >= 1):
        return "medium"
    if list_item_count > 0 or mapped.get("title") or mapped.get("description") or mapped.get("company_name"):
        return "low"
    return "failed"


def _build_source_status(methods: list[str]) -> dict[str, str]:
    return {
        "job_posting_url": "used",
        "json_ld": "used" if "json_ld" in methods else "available_not_used",
        "meta_tags": "used" if "meta" in methods else "available_not_used",
        "html_text": "used" if "html_sections" in methods else "available_not_used",
        "manual_fields": "merged",
    }


def normalize_job_posting_extraction(
    source_url: str,
    *,
    final_url: str | None = None,
    mapped: dict[str, Any] | None = None,
    methods: list[str] | None = None,
    warnings: list[str] | None = None,
) -> JobPostingExtractionResult:
    mapped = mapped or {}
    methods = list(methods or [])
    warnings = list(warnings or [])
    confidence = _compute_confidence(mapped, methods)
    if confidence in ("low", "medium") and "json_ld" not in methods:
        if _WARN_NO_JSON_LD not in warnings:
            warnings.append(_WARN_NO_JSON_LD)
    if confidence in ("low", "medium") and _WARN_PARTIAL not in warnings:
        warnings.append(_WARN_PARTIAL)
    if confidence == "failed" and not warnings:
        warnings.append(_WARN_NO_USEFUL_INFO)
    elif confidence == "failed" and _WARN_PARTIAL in warnings and _WARN_NO_USEFUL_INFO not in warnings:
        warnings = [w for w in warnings if w != _WARN_PARTIAL]
        warnings.append(_WARN_NO_USEFUL_INFO)
    return JobPostingExtractionResult(
        source_url=source_url,
        final_url=final_url,
        title=mapped.get("title"),
        company_name=mapped.get("company_name"),
        company_profile=mapped.get("company_profile"),
        description=mapped.get("description"),
        responsibilities=list(mapped.get("responsibilities") or []),
        requirements=list(mapped.get("requirements") or []),
        preferred_qualifications=list(mapped.get("preferred_qualifications") or []),
        tools=list(mapped.get("tools") or []),
        skills=list(mapped.get("skills") or []),
        location=mapped.get("location"),
        seniority=mapped.get("seniority"),
        employment_type=mapped.get("employment_type"),
        date_posted=mapped.get("date_posted"),
        valid_through=mapped.get("valid_through"),
        salary_text=mapped.get("salary_text"),
        extraction_confidence=confidence,
        extraction_methods=methods,
        warnings=warnings,
        source_status=_build_source_status(methods),
    )


def extract_job_posting_from_html(html: str, source_url: str) -> JobPostingExtractionResult:
    """Extract job fields from HTML using layered strategy (no network)."""
    soup = BeautifulSoup(html, "lxml")
    methods: list[str] = []
    warnings: list[str] = []
    mapped: dict[str, Any] = {}

    posting = extract_json_ld_job_posting(html)
    if posting:
        methods.append("json_ld")
        mapped = _map_json_ld_posting(posting)

    meta = _extract_meta_fallback(soup)
    if meta.get("canonical_url"):
        mapped.setdefault("canonical_url", meta["canonical_url"])
    if not mapped.get("title") and meta.get("title"):
        methods.append("meta")
        mapped["title"] = meta["title"]
    if not mapped.get("description") and meta.get("description"):
        methods.append("meta")
        mapped["description"] = meta["description"]
    if not mapped.get("company_name") and meta.get("company_name"):
        methods.append("meta")
        mapped["company_name"] = meta["company_name"]

    html_sections = _extract_html_sections(BeautifulSoup(html, "lxml"))
    if any(html_sections.values()):
        methods.append("html_sections")
        for key, values in html_sections.items():
            if values and not mapped.get(key):
                mapped[key] = values
            elif values and isinstance(mapped.get(key), list):
                mapped[key] = _dedupe_list(list(mapped[key]) + values)

    if not any(html_sections.values()):
        plain = _readable_text(BeautifulSoup(html, "lxml"))
        text_sections = extract_job_sections_from_text(plain)
        if any(text_sections.values()):
            methods.append("html_sections")
            for key, values in text_sections.items():
                if values and not mapped.get(key):
                    mapped[key] = values

    if mapped.get("skills") and not mapped.get("tools"):
        toolish = [s for s in mapped["skills"] if any(t in s.lower() for t in ("excel", "sql", "python", "autocad"))]
        if toolish:
            mapped["tools"] = toolish

    final_url = meta.get("canonical_url") or source_url
    if isinstance(final_url, str) and not final_url.startswith("http"):
        final_url = urljoin(source_url, final_url)

    return normalize_job_posting_extraction(
        source_url,
        final_url=final_url,
        mapped=mapped,
        methods=methods,
        warnings=warnings,
    )


def _resolve_host_addresses(hostname: str) -> list[str]:
    """Resolve hostname to IP strings. Overridable in tests via monkeypatch."""
    results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    return list(dict.fromkeys(sockaddr[0] for *_, sockaddr in results))


def _is_unsafe_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def _validate_hostname(hostname: str) -> tuple[bool, str | None]:
    host = (hostname or "").lower().strip().rstrip(".")
    if not host:
        return False, _WARN_FETCH_FAILED_SAFE
    if host in {"localhost", "0.0.0.0"} or host.endswith(".local"):
        return False, _WARN_FETCH_FAILED_SAFE

    try:
        addr = ipaddress.ip_address(host.strip("[]"))
        if _is_unsafe_ip(addr):
            return False, _WARN_FETCH_FAILED_SAFE
        return True, None
    except ValueError:
        pass

    try:
        addresses = _resolve_host_addresses(host)
    except socket.gaierror:
        logger.warning("job_posting_dns_resolution_failed", hostname=host)
        return False, _WARN_FETCH_FAILED_SAFE

    if not addresses:
        return False, _WARN_FETCH_FAILED_SAFE

    for ip_str in addresses:
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, _WARN_FETCH_FAILED_SAFE
        if _is_unsafe_ip(addr):
            return False, _WARN_FETCH_FAILED_SAFE
    return True, None


def _is_safe_public_url(url: str, *, after_redirect: bool = False) -> tuple[bool, str | None]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        return False, _WARN_INVALID_URL
    host = parsed.hostname
    if not host:
        return False, _WARN_FETCH_FAILED_SAFE
    if parsed.username or parsed.password:
        return False, _WARN_FETCH_FAILED_SAFE
    safe, reason = _validate_hostname(host)
    if not safe:
        if after_redirect:
            return False, _WARN_UNSAFE_REDIRECT
        return False, reason
    return True, None


async def _read_limited_response_body(response: httpx.Response) -> tuple[str | None, str | None]:
    """Read response body up to _MAX_RESPONSE_BYTES. Returns (html, error_warning)."""
    content_length = response.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > _MAX_RESPONSE_BYTES:
                return None, _WARN_RESPONSE_TOO_LARGE
        except ValueError:
            pass

    chunks: list[bytes] = []
    total = 0
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > _MAX_RESPONSE_BYTES:
            return None, _WARN_RESPONSE_TOO_LARGE
        chunks.append(chunk)
    return b"".join(chunks).decode("utf-8", errors="replace"), None


async def _fetch_html_safely(url: str) -> tuple[str | None, str | None, list[str]]:
    """
    Fetch HTML with manual redirect handling, SSRF checks, and response size cap.
    Returns (html, final_url, warnings).
    """
    current_url = url.strip()
    warnings: list[str] = []

    async with httpx.AsyncClient(
        timeout=settings.scraper_timeout_ms / 1000,
        headers={"User-Agent": settings.scraper_user_agent},
        follow_redirects=False,
    ) as client:
        for redirect_hops in range(_MAX_REDIRECTS + 1):
            safe, reason = _is_safe_public_url(current_url, after_redirect=redirect_hops > 0)
            if not safe:
                return None, None, [reason or _WARN_FETCH_FAILED_SAFE]

            try:
                async with client.stream("GET", current_url) as response:
                    if response.status_code in _REDIRECT_STATUS_CODES:
                        if redirect_hops >= _MAX_REDIRECTS:
                            return None, None, [_WARN_FETCH_FAILED_SAFE]
                        location = response.headers.get("location")
                        if not location:
                            return None, None, [_WARN_FETCH_FAILED_SAFE]
                        current_url = urljoin(current_url, location.strip())
                        continue

                    if response.status_code >= 400:
                        response.raise_for_status()

                    html, size_warning = await _read_limited_response_body(response)
                    if size_warning:
                        return None, None, [size_warning]
                    return html, current_url, warnings
            except httpx.HTTPError as exc:
                logger.warning("job_posting_fetch_failed", url=current_url, error=str(exc))
                return None, None, [_WARN_FETCH_FAILED_SAFE]
            except Exception as exc:  # noqa: BLE001
                logger.warning("job_posting_fetch_failed", url=current_url, error=str(exc))
                return None, None, [_WARN_FETCH_FAILED_SAFE]

    return None, None, [_WARN_FETCH_FAILED_SAFE]


async def fetch_and_extract_job_posting_url(url: str) -> JobPostingExtractionResult:
    """Fetch a job posting URL and extract fields. Returns warnings on failure — never raises."""
    safe, reason = _is_safe_public_url(url)
    if not safe:
        return normalize_job_posting_extraction(
            url,
            warnings=[reason or _WARN_FETCH_FAILED_SAFE],
        )

    html, final_url, fetch_warnings = await _fetch_html_safely(url)
    if html is None:
        return normalize_job_posting_extraction(
            url,
            warnings=fetch_warnings or [_WARN_FETCH_FAILED_SAFE],
        )

    result = extract_job_posting_from_html(html, url)
    if final_url and final_url != url:
        safe_final, _ = _is_safe_public_url(final_url, after_redirect=True)
        result.final_url = final_url if safe_final else None
    else:
        result.final_url = final_url
    if fetch_warnings:
        result.warnings = list(dict.fromkeys(result.warnings + fetch_warnings))
    return result


def _user_has_text(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return len(value) > 0
    return bool(value)


def merge_extraction_into_job_snapshot(
    job: dict[str, Any],
    extraction: JobPostingExtractionResult,
) -> dict[str, Any]:
    """Merge extracted URL fields into job snapshot. User-provided fields win."""
    merged = dict(job)
    merged["source_url"] = merged.get("source_url") or extraction.source_url

    if not _user_has_text(merged.get("title")) or merged.get("title") == "Untitled Role":
        if extraction.title:
            merged["title"] = extraction.title

    if not _user_has_text(merged.get("company_name")) and extraction.company_name:
        merged["company_name"] = extraction.company_name

    if not _user_has_text(merged.get("location")) and extraction.location:
        merged["location"] = extraction.location

    if not _user_has_text(merged.get("employment_type")) and extraction.employment_type:
        merged["employment_type"] = extraction.employment_type

    if not _user_has_text(merged.get("description_raw")) and extraction.description:
        merged["description_raw"] = extraction.description

    merged["responsibilities"] = _merge_string_lists(
        merged.get("responsibilities") or [],
        extraction.responsibilities,
    )
    merged["requirements"] = _merge_string_lists(
        merged.get("requirements") or [],
        extraction.requirements + extraction.preferred_qualifications,
    )

    existing_skills = merged.get("extracted_skills") or []
    skill_names = {
        (s.get("skill") if isinstance(s, dict) else str(s)).lower()
        for s in existing_skills
        if s
    }
    for skill in extraction.skills:
        if skill.lower() not in skill_names:
            existing_skills.append({"skill": skill, "importance": "high"})
            skill_names.add(skill.lower())
    for tool in extraction.tools:
        if tool.lower() not in skill_names:
            existing_skills.append({"skill": tool, "importance": "high", "category": "tool"})
            skill_names.add(tool.lower())
    merged["extracted_skills"] = existing_skills

    cp = dict(merged.get("company_profile") or {})
    if not _user_has_text(cp.get("summary")) and extraction.company_profile:
        cp["summary"] = extraction.company_profile
    merged["company_profile"] = cp

    summary_parts = [
        extraction.title,
        extraction.company_name,
        extraction.description,
        " ".join(extraction.responsibilities),
        " ".join(extraction.requirements),
    ]
    merged["extracted_link_content"] = _norm(" ".join(p for p in summary_parts if p)) or None
    merged["job_posting_extraction"] = extraction_to_dict(extraction)
    return merged


def _merge_string_lists(user_items: list[Any], extracted: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in user_items:
        text = item.get("text") if isinstance(item, dict) else str(item)
        text = _norm(text)
        if text and text.lower() not in seen:
            seen.add(text.lower())
            out.append(text)
    for item in extracted:
        text = _norm(item)
        if text and text.lower() not in seen:
            seen.add(text.lower())
            out.append(text)
    return out


async def enrich_job_snapshot_from_posting_url(
    job: dict[str, Any],
    url: str | None = None,
    *,
    html: str | None = None,
) -> tuple[dict[str, Any], JobPostingExtractionResult | None]:
    """
    Extract from URL (live fetch) or pre-supplied HTML (tests), then merge into job snapshot.
    """
    posting_url = _norm(url or job.get("source_url") or job.get("job_posting_url") or "")
    if not posting_url:
        return job, None

    if html is not None:
        extraction = extract_job_posting_from_html(html, posting_url)
    else:
        extraction = await fetch_and_extract_job_posting_url(posting_url)

    if extraction.extraction_confidence == "failed" and not extraction.description:
        merged = dict(job)
        merged["source_url"] = merged.get("source_url") or posting_url
        merged["job_posting_extraction"] = extraction_to_dict(extraction)
        return merged, extraction

    merged = merge_extraction_into_job_snapshot(job, extraction)
    return merged, extraction
