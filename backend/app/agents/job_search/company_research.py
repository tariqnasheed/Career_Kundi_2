"""Company profile and source-cited web research for interview packs (Iteration 004E-C).

Layered extraction: user-provided profile → job posting derived context →
Schema.org Organization JSON-LD → OpenGraph/meta → HTML section headings.

Reuses safe URL fetch from job_posting_extractor (SSRF, redirect, size cap).
"""

from __future__ import annotations

import html as html_module
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.agents.job_search.job_posting_extractor import (
    _fetch_html_safely,
    _is_safe_public_url,
    _norm,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_FACT_LEN = 500
_MAX_OVERVIEW_LEN = 1200

_ORG_TYPE_MARKERS = (
    "Organization",
    "Corporation",
    "LocalBusiness",
    "EducationalOrganization",
    "NGO",
    "NonprofitOrganization",
    "GovernmentOrganization",
    "NewsMediaOrganization",
    "SportsOrganization",
    "WorkersUnion",
    "CollegeOrUniversity",
    "School",
    "Airline",
    "Consortium",
)

_SECTION_ALIASES: dict[str, str] = {
    "about": "overview",
    "about us": "overview",
    "who we are": "overview",
    "what we do": "overview",
    "our story": "overview",
    "products": "products_services",
    "services": "products_services",
    "solutions": "products_services",
    "what we offer": "products_services",
    "industries": "industries",
    "industry": "industries",
    "markets": "markets",
    "customers": "markets",
    "mission": "mission_or_values",
    "values": "mission_or_values",
    "our mission": "mission_or_values",
}

_NOISE_PATTERNS = (
    r"cookie",
    r"privacy policy",
    r"sign in",
    r"subscribe",
    r"accept all",
    r"all rights reserved",
)

_WARN_NO_OFFICIAL = (
    "No official company profile source was available. Company-specific questions may be limited."
)
_WARN_PARTIAL = "Only partial company context was extracted from available sources."
_WARN_UNAVAILABLE = (
    "Company research was unavailable; generation will rely on user-provided job details and local fallback."
)
_WARN_FETCH_FAILED = (
    "The company profile page could not be fetched safely. "
    "Provide company details manually for stronger results."
)


@dataclass
class CompanyResearchSource:
    url: str
    source_type: str
    title: str | None
    extracted_facts: list[str]
    confidence: str


@dataclass
class CompanyResearchResult:
    company_name: str | None = None
    company_domain: str | None = None
    official_website: str | None = None
    company_overview: str | None = None
    products_services: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    markets: list[str] = field(default_factory=list)
    mission_or_values: list[str] = field(default_factory=list)
    company_size: str | None = None
    headquarters: str | None = None
    source_urls: list[str] = field(default_factory=list)
    sources: list[CompanyResearchSource] = field(default_factory=list)
    research_confidence: str = "unavailable"
    source_status: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    research_methods: list[str] = field(default_factory=list)


def research_to_dict(result: CompanyResearchResult) -> dict[str, Any]:
    data = asdict(result)
    data["sources"] = [asdict(s) for s in result.sources]
    return data


def _dedupe_list(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _norm(item)
        if not text or len(text) > _MAX_FACT_LEN:
            continue
        key = text.lower()
        if key in seen:
            continue
        if any(re.search(p, key) for p in _NOISE_PATTERNS):
            continue
        seen.add(key)
        out.append(text)
    return out


def _dedupe_urls(urls: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for url in urls:
        u = (url or "").strip()
        if not u or not u.startswith(("http://", "https://")):
            continue
        if u.lower() in seen:
            continue
        seen.add(u.lower())
        out.append(u)
    return out


def _is_organization_type(value: Any) -> bool:
    if isinstance(value, str):
        if any(marker in value for marker in _ORG_TYPE_MARKERS):
            return True
        return value.endswith("Organization")
    if isinstance(value, list):
        return any(_is_organization_type(v) for v in value)
    return False


def _find_organization_object(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        for item in data:
            found = _find_organization_object(item)
            if found:
                return found
    elif isinstance(data, dict):
        if _is_organization_type(data.get("@type")):
            return data
        graph = data.get("@graph")
        if graph is not None:
            found = _find_organization_object(graph)
            if found:
                return found
        for value in data.values():
            if isinstance(value, (dict, list)):
                found = _find_organization_object(value)
                if found:
                    return found
    return None


def extract_json_ld_organization(html: str) -> dict[str, Any] | None:
    """Return the first Schema.org Organization-like object found in JSON-LD blocks."""
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
        org = _find_organization_object(data)
        if org:
            return org
    return None


def _address_text(addr: Any) -> str | None:
    if isinstance(addr, str):
        return _norm(addr) or None
    if not isinstance(addr, dict):
        return None
    parts = [
        addr.get("streetAddress"),
        addr.get("addressLocality"),
        addr.get("addressRegion"),
        addr.get("postalCode"),
        addr.get("addressCountry"),
    ]
    text = _norm(", ".join(str(p) for p in parts if p))
    return text or None


def _location_text(loc: Any) -> str | None:
    if isinstance(loc, str):
        return _norm(loc) or None
    if isinstance(loc, dict):
        if loc.get("name"):
            return _norm(str(loc["name"])) or None
        return _address_text(loc.get("address") or loc)
    if isinstance(loc, list) and loc:
        return _location_text(loc[0])
    return None


def _offer_items(org: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for key in ("makesOffer", "hasOfferCatalog", "brand"):
        value = org.get(key)
        if isinstance(value, str):
            items.append(value)
        elif isinstance(value, dict):
            name = value.get("name") or value.get("description")
            if name:
                items.append(str(name))
            for offer in value.get("itemListElement") or value.get("offers") or []:
                if isinstance(offer, dict):
                    label = offer.get("name") or offer.get("itemOffered")
                    if isinstance(label, dict):
                        label = label.get("name")
                    if label:
                        items.append(str(label))
                elif isinstance(offer, str):
                    items.append(offer)
        elif isinstance(value, list):
            for entry in value:
                if isinstance(entry, str):
                    items.append(entry)
                elif isinstance(entry, dict):
                    label = entry.get("name") or entry.get("description")
                    if label:
                        items.append(str(label))
    return _dedupe_list(items)


def _same_as_urls(org: dict[str, Any]) -> list[str]:
    same_as = org.get("sameAs")
    if isinstance(same_as, str):
        return [same_as] if same_as.startswith("http") else []
    if isinstance(same_as, list):
        return [u for u in same_as if isinstance(u, str) and u.startswith("http")]
    return []


def _keywords_list(org: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for key in ("keywords", "knowsAbout", "industry"):
        value = org.get(key)
        if isinstance(value, str):
            items.extend(re.split(r"[,;|]", value))
        elif isinstance(value, list):
            for entry in value:
                if isinstance(entry, str):
                    items.append(entry)
                elif isinstance(entry, dict) and entry.get("name"):
                    items.append(str(entry["name"]))
    return _dedupe_list(items)


def _map_organization_json_ld(org: dict[str, Any]) -> dict[str, Any]:
    name = _norm(org.get("legalName") or org.get("name") or "")
    overview = _norm(org.get("description") or "")
    if len(overview) > _MAX_OVERVIEW_LEN:
        overview = overview[:_MAX_OVERVIEW_LEN].rsplit(" ", 1)[0] + "…"
    website = org.get("url")
    if isinstance(website, str) and not website.startswith("http"):
        website = None
    hq = _location_text(org.get("location")) or _location_text(org.get("foundingLocation"))
    area = org.get("areaServed")
    markets: list[str] = []
    if isinstance(area, str):
        markets.append(area)
    elif isinstance(area, list):
        for entry in area:
            if isinstance(entry, str):
                markets.append(entry)
            elif isinstance(entry, dict) and entry.get("name"):
                markets.append(str(entry["name"]))
    employees = org.get("numberOfEmployees")
    size: str | None = None
    if isinstance(employees, (str, int)):
        size = str(employees)
    elif isinstance(employees, dict) and employees.get("value"):
        size = str(employees["value"])
    return {
        "company_name": name or None,
        "company_overview": overview or None,
        "official_website": website if isinstance(website, str) else None,
        "products_services": _offer_items(org),
        "industries": _keywords_list(org),
        "markets": _dedupe_list(markets),
        "headquarters": hq,
        "company_size": size,
        "source_urls": _same_as_urls(org),
    }


def _extract_meta(soup: BeautifulSoup) -> dict[str, str | None]:
    title_tag = soup.find("title")
    title = _norm(title_tag.get_text()) if title_tag else None
    og_title = og_desc = meta_desc = canonical = None
    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").lower()
        content = meta.get("content")
        if not content:
            continue
        if prop in ("og:title", "twitter:title") and not og_title:
            og_title = _norm(content)
        elif prop in ("og:description", "twitter:description", "description") and not meta_desc:
            meta_desc = _norm(content)
        elif prop == "og:description" and not og_desc:
            og_desc = _norm(content)
    link = soup.find("link", rel=lambda r: r and "canonical" in str(r).lower())
    if link and link.get("href"):
        canonical = link["href"].strip()
    return {
        "title": title,
        "og_title": og_title,
        "og_description": og_desc or meta_desc,
        "meta_description": meta_desc,
        "canonical_url": canonical,
    }


def _readable_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    return _norm(soup.get_text(separator="\n"))


def _section_key(heading: str) -> str | None:
    lowered = _norm(heading).lower().rstrip(":")
    return _SECTION_ALIASES.get(lowered)


def extract_company_sections_from_text(text: str) -> dict[str, list[str]]:
    """Extract company facts grouped by section from plain text."""
    sections: dict[str, list[str]] = {
        "overview": [],
        "products_services": [],
        "industries": [],
        "markets": [],
        "mission_or_values": [],
    }
    current_key: str | None = None
    for raw_line in text.splitlines():
        line = _norm(raw_line)
        if not line:
            continue
        if len(line) < 80 and (line.isupper() or line.endswith(":") or line.istitle()):
            key = _section_key(line.rstrip(":"))
            if key:
                current_key = key
                continue
        if current_key and len(line) <= _MAX_FACT_LEN:
            if line.startswith(("-", "•", "*")):
                line = _norm(line.lstrip("-•* "))
            sections[current_key].append(line)
    for key in sections:
        sections[key] = _dedupe_list(sections[key])[:8]
    return sections


def _extract_html_sections(soup: BeautifulSoup) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "overview": [],
        "products_services": [],
        "industries": [],
        "markets": [],
        "mission_or_values": [],
    }
    current_key: str | None = None
    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        tag = element.name or ""
        text = _norm(element.get_text())
        if not text:
            continue
        if tag in ("h1", "h2", "h3", "h4"):
            key = _section_key(text)
            if key:
                current_key = key
            continue
        if current_key and tag in ("p", "li"):
            if len(text) <= _MAX_FACT_LEN:
                sections[current_key].append(text)
    for key in sections:
        sections[key] = _dedupe_list(sections[key])[:8]
    return sections


def _has_useful_context(result: CompanyResearchResult) -> bool:
    return bool(
        result.company_overview
        or result.products_services
        or result.industries
        or result.markets
        or result.mission_or_values
        or result.headquarters
    )


def _compute_confidence(result: CompanyResearchResult, methods: list[str]) -> str:
    if not _has_useful_context(result):
        return "unavailable"
    if "json_ld_organization" in methods and (
        result.company_overview or result.products_services or result.industries
    ):
        return "high"
    if "user_provided" in methods and _has_useful_context(result):
        if "html_sections" in methods or "json_ld_organization" in methods:
            return "high"
        return "medium"
    if "html_sections" in methods:
        return "medium"
    if "meta_fallback" in methods or "job_posting_derived" in methods:
        return "low"
    return "low"


def _build_warnings(result: CompanyResearchResult, methods: list[str]) -> list[str]:
    warnings: list[str] = []
    if result.research_confidence == "unavailable":
        warnings.append(_WARN_UNAVAILABLE)
    elif result.research_confidence in ("low", "medium") and "company_page" not in methods:
        if _WARN_NO_OFFICIAL not in warnings:
            warnings.append(_WARN_NO_OFFICIAL)
    elif result.research_confidence == "low":
        warnings.append(_WARN_PARTIAL)
    elif result.research_confidence == "medium" and "json_ld_organization" not in methods:
        warnings.append(_WARN_PARTIAL)
    seen: set[str] = set()
    unique: list[str] = []
    for w in warnings + result.warnings:
        if w and w not in seen:
            seen.add(w)
            unique.append(w)
    return unique


def _result_from_mapped(
    mapped: dict[str, Any],
    *,
    source_url: str,
    methods: list[str],
    warnings: list[str],
    source_type: str,
    title: str | None = None,
) -> CompanyResearchResult:
    facts: list[str] = []
    if mapped.get("company_overview"):
        facts.append(str(mapped["company_overview"]))
    facts.extend(mapped.get("products_services") or [])
    facts.extend(mapped.get("industries") or [])
    source = CompanyResearchSource(
        url=source_url,
        source_type=source_type,
        title=title,
        extracted_facts=facts[:12],
        confidence="low",
    )
    urls = _dedupe_urls([source_url] + list(mapped.get("source_urls") or []))
    result = CompanyResearchResult(
        company_name=mapped.get("company_name"),
        company_domain=urlparse(source_url).hostname if source_url else None,
        official_website=mapped.get("official_website") or source_url,
        company_overview=mapped.get("company_overview"),
        products_services=list(mapped.get("products_services") or []),
        industries=list(mapped.get("industries") or []),
        markets=list(mapped.get("markets") or []),
        mission_or_values=list(mapped.get("mission_or_values") or []),
        company_size=mapped.get("company_size"),
        headquarters=mapped.get("headquarters"),
        source_urls=urls,
        sources=[source],
        research_methods=list(methods),
        warnings=list(warnings),
    )
    result.research_confidence = _compute_confidence(result, methods)
    result.warnings = _build_warnings(result, methods)
    if result.sources:
        result.sources[0].confidence = result.research_confidence
    return result


def extract_company_from_html(
    html: str,
    source_url: str,
    company_name: str | None = None,
) -> CompanyResearchResult:
    """Extract company context from HTML using JSON-LD, meta, and section fallbacks."""
    soup = BeautifulSoup(html, "lxml")
    methods: list[str] = []
    warnings: list[str] = []
    mapped: dict[str, Any] = {
        "company_name": company_name,
        "products_services": [],
        "industries": [],
        "markets": [],
        "mission_or_values": [],
        "source_urls": [],
    }

    org = extract_json_ld_organization(html)
    meta = _extract_meta(soup)
    title = meta.get("og_title") or meta.get("title")

    if org:
        methods.append("json_ld_organization")
        ld_mapped = _map_organization_json_ld(org)
        for key, value in ld_mapped.items():
            if key == "source_urls" and value:
                mapped["source_urls"] = _dedupe_urls(list(mapped["source_urls"]) + list(value))
            elif value and not mapped.get(key):
                mapped[key] = value
            elif key in ("products_services", "industries", "markets") and value:
                mapped[key] = _dedupe_list(list(mapped.get(key) or []) + list(value))

    html_sections = _extract_html_sections(soup)
    if any(html_sections.values()):
        methods.append("html_sections")
        if not mapped.get("company_overview") and html_sections["overview"]:
            mapped["company_overview"] = " ".join(html_sections["overview"][:2])
            if len(mapped["company_overview"]) > _MAX_OVERVIEW_LEN:
                mapped["company_overview"] = mapped["company_overview"][:_MAX_OVERVIEW_LEN]
        for key in ("products_services", "industries", "markets", "mission_or_values"):
            if html_sections.get(key):
                mapped[key] = _dedupe_list(list(mapped.get(key) or []) + html_sections[key])

    if not any(html_sections.values()):
        plain = _readable_text(soup)
        text_sections = extract_company_sections_from_text(plain)
        if any(text_sections.values()):
            methods.append("html_sections")
            if not mapped.get("company_overview") and text_sections["overview"]:
                mapped["company_overview"] = " ".join(text_sections["overview"][:2])
            for key in ("products_services", "industries", "markets", "mission_or_values"):
                if text_sections.get(key):
                    mapped[key] = _dedupe_list(list(mapped.get(key) or []) + text_sections[key])

    meta_used = False
    if not mapped.get("company_overview"):
        desc = meta.get("og_description") or meta.get("meta_description")
        if desc and len(desc) > 40:
            mapped["company_overview"] = desc[:_MAX_OVERVIEW_LEN]
            methods.append("meta_fallback")
            meta_used = True
    if not mapped.get("company_name"):
        name_candidate = meta.get("og_title") or meta.get("title")
        if name_candidate and len(name_candidate) < 120:
            mapped["company_name"] = name_candidate
            if meta_used or not methods:
                methods.append("meta_fallback")

    canonical = meta.get("canonical_url")
    if isinstance(canonical, str) and canonical.startswith("http"):
        mapped["source_urls"] = _dedupe_urls(list(mapped.get("source_urls") or []) + [canonical])
        if not mapped.get("official_website"):
            mapped["official_website"] = canonical

    if not methods:
        warnings.append(_WARN_UNAVAILABLE)

    return _result_from_mapped(
        mapped,
        source_url=source_url,
        methods=methods,
        warnings=warnings,
        source_type="company_page",
        title=title if isinstance(title, str) else None,
    )


def merge_company_research(
    primary: CompanyResearchResult,
    secondary: CompanyResearchResult,
) -> CompanyResearchResult:
    """Merge research results. Primary scalar fields win; lists are combined."""
    merged = CompanyResearchResult(
        company_name=primary.company_name or secondary.company_name,
        company_domain=primary.company_domain or secondary.company_domain,
        official_website=primary.official_website or secondary.official_website,
        company_overview=primary.company_overview or secondary.company_overview,
        products_services=_dedupe_list(primary.products_services + secondary.products_services),
        industries=_dedupe_list(primary.industries + secondary.industries),
        markets=_dedupe_list(primary.markets + secondary.markets),
        mission_or_values=_dedupe_list(primary.mission_or_values + secondary.mission_or_values),
        company_size=primary.company_size or secondary.company_size,
        headquarters=primary.headquarters or secondary.headquarters,
        source_urls=_dedupe_urls(primary.source_urls + secondary.source_urls),
        sources=primary.sources + secondary.sources,
        research_methods=list(dict.fromkeys(primary.research_methods + secondary.research_methods)),
        warnings=list(dict.fromkeys(primary.warnings + secondary.warnings)),
        source_status=dict(primary.source_status),
    )
    merged.research_confidence = _compute_confidence(merged, merged.research_methods)
    merged.warnings = _build_warnings(merged, merged.research_methods)
    return merged


def _user_has_text(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return any(_user_has_text(v) for v in value.values())
    return bool(value)


def build_company_research_from_job_snapshot(job: dict[str, Any]) -> CompanyResearchResult:
    """Layers 1–2: user-provided profile and job-posting-derived company context."""
    methods: list[str] = []
    warnings: list[str] = []
    source_urls: list[str] = []
    source_status: dict[str, str] = {
        "user_company_profile": "thin",
        "job_posting_company_profile": "not_present",
        "company_page": "not_present",
        "company_research_urls": "none",
        "model_knowledge": "disabled",
        "document_library": "not_checked",
        "local_fallback": "available",
    }

    company_name = _norm(job.get("company_name") or "") or None
    company_url = _norm(job.get("company_url") or "") or None
    if company_url:
        source_urls.append(company_url)

    overview: str | None = None
    products: list[str] = []
    industries: list[str] = []
    markets: list[str] = []
    mission: list[str] = []
    headquarters: str | None = None

    cp = job.get("company_profile") if isinstance(job.get("company_profile"), dict) else {}
    user_signal = False
    if _user_has_text(cp.get("summary") or cp.get("description")):
        overview = _norm(str(cp.get("summary") or cp.get("description")))
        user_signal = True
    if _user_has_text(cp.get("products_services") or cp.get("products") or cp.get("services")):
        raw = str(cp.get("products_services") or cp.get("products") or cp.get("services"))
        products = _dedupe_list(re.split(r"[,;|]", raw))
        user_signal = True
    if _user_has_text(cp.get("industry") or cp.get("domain")):
        industries = _dedupe_list([str(cp.get("industry") or cp.get("domain"))])
        user_signal = True
    if _user_has_text(cp.get("scope") or cp.get("market")):
        markets = _dedupe_list([str(cp.get("scope") or cp.get("market"))])
        user_signal = True
    if _user_has_text(cp.get("headquarters") or cp.get("location")):
        headquarters = _norm(str(cp.get("headquarters") or cp.get("location")))
        user_signal = True
    if _user_has_text(cp.get("mission") or cp.get("values")):
        mission = _dedupe_list([str(cp.get("mission") or cp.get("values"))])
        user_signal = True

    if user_signal:
        methods.append("user_provided")
        source_status["user_company_profile"] = "used"

    extraction = job.get("job_posting_extraction")
    posting_used = False
    if isinstance(extraction, dict):
        if not company_name and extraction.get("company_name"):
            company_name = _norm(str(extraction["company_name"])) or None
        if not overview and extraction.get("company_profile"):
            overview = _norm(str(extraction["company_profile"]))
            posting_used = True
        posting_url = extraction.get("final_url") or extraction.get("source_url")
        if isinstance(posting_url, str) and posting_url.startswith("http"):
            source_urls.append(posting_url)
        source_status["job_posting_company_profile"] = "used" if posting_used else "available_not_used"
    else:
        source_status["job_posting_company_profile"] = "not_present"

    domain = urlparse(company_url).hostname if company_url else None
    result = CompanyResearchResult(
        company_name=company_name,
        company_domain=domain,
        official_website=company_url,
        company_overview=overview,
        products_services=products,
        industries=industries,
        markets=markets,
        mission_or_values=mission,
        headquarters=headquarters,
        source_urls=_dedupe_urls(source_urls),
        research_methods=methods,
        warnings=warnings,
        source_status=source_status,
    )
    if result.source_urls:
        source_status["company_research_urls"] = "captured"
        result.source_status = source_status
    result.research_confidence = _compute_confidence(result, methods)
    result.warnings = _build_warnings(result, methods)
    return result


async def fetch_and_research_company_url(
    url: str,
    company_name: str | None = None,
) -> CompanyResearchResult:
    """Fetch a company profile URL and extract fields. Never raises."""
    safe, reason = _is_safe_public_url(url)
    if not safe:
        return CompanyResearchResult(
            official_website=url,
            source_urls=[url] if url.startswith("http") else [],
            warnings=[reason or _WARN_FETCH_FAILED],
            research_confidence="unavailable",
            source_status={
                "user_company_profile": "thin",
                "job_posting_company_profile": "not_present",
                "company_page": "failed",
                "company_research_urls": "captured" if url.startswith("http") else "none",
                "model_knowledge": "disabled",
                "document_library": "not_checked",
                "local_fallback": "available",
            },
        )

    html, final_url, fetch_warnings = await _fetch_html_safely(url)
    if html is None:
        return CompanyResearchResult(
            official_website=url,
            source_urls=[url],
            warnings=fetch_warnings or [_WARN_FETCH_FAILED],
            research_confidence="unavailable",
            source_status={
                "user_company_profile": "thin",
                "job_posting_company_profile": "not_present",
                "company_page": "failed",
                "company_research_urls": "captured",
                "model_knowledge": "disabled",
                "document_library": "not_checked",
                "local_fallback": "available",
            },
        )

    page_url = final_url or url
    page_result = extract_company_from_html(html, page_url, company_name)
    if fetch_warnings:
        page_result.warnings = list(dict.fromkeys(page_result.warnings + fetch_warnings))
    page_result.source_status["company_page"] = "used"
    page_result.source_status.setdefault("model_knowledge", "disabled")
    page_result.source_status.setdefault("document_library", "not_checked")
    page_result.source_status.setdefault("local_fallback", "available")
    if page_result.source_urls:
        page_result.source_status["company_research_urls"] = "captured"
    page_result.research_methods = list(
        dict.fromkeys(page_result.research_methods + ["company_page"])
    )
    page_result.research_confidence = _compute_confidence(page_result, page_result.research_methods)
    page_result.warnings = _build_warnings(page_result, page_result.research_methods)
    return page_result


def merge_company_research_into_job_snapshot(
    job: dict[str, Any],
    research: CompanyResearchResult,
) -> dict[str, Any]:
    """Merge company research into job snapshot. User-provided fields always win."""
    merged = dict(job)
    cp = dict(merged.get("company_profile") or {})

    if not _user_has_text(cp.get("summary")) and research.company_overview:
        cp["summary"] = research.company_overview
    if not _user_has_text(cp.get("products_services") or cp.get("products")) and research.products_services:
        cp["products_services"] = ", ".join(research.products_services)
    if not _user_has_text(cp.get("industry") or cp.get("domain")) and research.industries:
        cp["industry"] = ", ".join(research.industries)
    if not _user_has_text(cp.get("scope") or cp.get("market")) and research.markets:
        cp["scope"] = ", ".join(research.markets)
    if not _user_has_text(cp.get("headquarters") or cp.get("location")) and research.headquarters:
        cp["headquarters"] = research.headquarters
    if not _user_has_text(cp.get("mission")) and research.mission_or_values:
        cp["mission"] = "; ".join(research.mission_or_values[:3])

    merged["company_profile"] = cp
    if not _user_has_text(merged.get("company_name")) and research.company_name:
        merged["company_name"] = research.company_name
    if not _user_has_text(merged.get("company_url")) and research.official_website:
        merged["company_url"] = research.official_website
    merged["company_research"] = research_to_dict(research)
    return merged


async def enrich_job_snapshot_with_company_research(
    job: dict[str, Any],
    *,
    company_url: str | None = None,
    fetch_company_page: bool = True,
) -> tuple[dict[str, Any], CompanyResearchResult]:
    """Run layers 1–4 company research and merge into the job snapshot."""
    base = build_company_research_from_job_snapshot(job)
    target_url = _norm(company_url or job.get("company_url") or "") or None

    if fetch_company_page and target_url:
        page_result = await fetch_and_research_company_url(
            target_url,
            company_name=job.get("company_name") or base.company_name,
        )
        combined = merge_company_research(base, page_result)
        combined.source_status = dict(base.source_status)
        if page_result.source_status.get("company_page") == "used":
            combined.source_status["company_page"] = "used"
        elif page_result.source_status.get("company_page") == "failed":
            combined.source_status["company_page"] = "failed"
        if combined.source_urls:
            combined.source_status["company_research_urls"] = "captured"
        combined.research_confidence = _compute_confidence(combined, combined.research_methods)
        combined.warnings = _build_warnings(combined, combined.research_methods)
        research = combined
    else:
        research = base

    merged = merge_company_research_into_job_snapshot(job, research)
    return merged, research
