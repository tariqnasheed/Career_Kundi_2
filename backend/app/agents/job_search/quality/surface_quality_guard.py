"""Surface-quality defect detection (Iteration 004E-E2.2 + corrective pass)."""

from __future__ import annotations

import re
from typing import Any

from app.agents.job_search.quality.user_facing_text import iter_user_facing_text

_DUPLICATE_TOKEN_RE = re.compile(
    r"\b(\w+)\s+\1\b",
    re.I,
)

# Broken coaching conjugations produced by naive "I -> You could" rewrites, e.g.
# "You could would", "You could fixed", "You could can", "The team could delivered".
# The second-verb list is explicit past-tense/modal to avoid flagging legitimate
# base verbs ("you could exceed", "you could proceed").
_MALFORMED_COACHING_RE = re.compile(
    r"\b(?:you|they|the team|one|we)\s+(?:could|would|can|might|may|should)\s+"
    r"(?:would|will|can|could|might|should|"
    r"fixed|cut|built|ran|led|made|took|wrote|sent|kept|held|dealt|drove|met|"
    r"delivered|reviewed|added|verified|configured|deployed|tested|resolved|handled|"
    r"diagnosed|adjusted|rebuilt|inspected|validated|managed|improved|reduced|increased|"
    r"started|checked|confirmed|showed|applied|completed|created|designed|developed|launched)\b",
    re.I,
)

# Pseudo-definitions such as "Domain term for X work that must be applied correctly".
_PSEUDO_DEFINITION_RE = re.compile(
    r"\b(?:domain\s+)?term for [a-z][a-z ]*? work that must be applied correctly\b",
    re.I,
)

# Capitalisation/join artifacts mid-sentence: "publishing results For compliance",
# "while It directly addresses". Restricted to same-line context (no newline
# crossing) and to function words that are strong artifacts mid-sentence, to
# avoid flagging legitimate bullet/line boundaries.
_MIDSENTENCE_CAP_RE = re.compile(
    r"[a-z]+[ \t]+(?:For|It|While)[ \t]+[a-z]",
)

# Dangling participle fragments: "... using completed", "... System Design using applied".
_DANGLING_PARTICIPLE_RE = re.compile(
    r"\b(?:using|with|through|via|applied)\s+(?:completed|applied|created|reviewed|verified|configured)\s*(?:[.\n]|$)",
    re.I,
)

_ROLE_TAUTLOGY_RE = re.compile(
    r"\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+\1\b",
)

# Role/term tautology inside a definition: "For a Data Analyst, Data Analyst means…".
_DEFINITION_TAUTOLOGY_RE = re.compile(
    r"[Ff]or\s+[Aa]n?\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s*,\s*\1\b",
)

# Same tautology where the repeated role phrase is title-cased differently, so the
# case-sensitive backreference above misses it: "For a DevOps Engineer, Devops
# Engineer means…", "For an HR Assistant, Hr Assistant means…". This happens when a
# skill label equals the role (e.g. deterministic-random roles). The trailing
# "means" keeps ordinary prose ("For a while, while I waited") from matching, and it
# is counted/fixed separately from the exact-case regex to avoid double counting.
_DEFINITION_TAUTOLOGY_CI_RE = re.compile(
    r"([Ff]or\s+[Aa]n?)\s+([A-Za-z][A-Za-z]*(?:\s+[A-Za-z]+)*?)\s*,\s*"
    r"([A-Za-z][A-Za-z]*(?:\s+[A-Za-z]+)*?)\s+means\b",
)


def _definition_tautology_ci_matches(text: str) -> list["re.Match[str]"]:
    """Case-differing definition tautologies only (exact-case handled elsewhere)."""
    matches: list[re.Match[str]] = []
    for m in _DEFINITION_TAUTOLOGY_CI_RE.finditer(text):
        first, second = m.group(2).strip(), m.group(3).strip()
        if first != second and first.lower() == second.lower():
            matches.append(m)
    return matches

# Duplicated example lead-ins: "For example, illustrative example:", "e.g. for instance".
_EXAMPLE_LEADIN = (
    r"for example|for instance|illustrative example|illustrative scenario|"
    r"example scenario|as an example|e\.g\.|for e\.g\."
)
_DUPLICATE_LEADIN_RE = re.compile(
    rf"\b(?:{_EXAMPLE_LEADIN})\b[\s,:;.\-]+\b(?:{_EXAMPLE_LEADIN})\b",
    re.I,
)

# Bounded repeated phrase around a connector: "performance for performance",
# "dashboard of dashboard". A small idiom allowlist prevents flagging legitimate
# repetition ("word for word", "like for like", "back to back", "day to day").
_REPEATED_PHRASE_RE = re.compile(
    r"\b(\w{4,})\s+(for|of|to|by|in|with)\s+\1\b",
    re.I,
)
_REPEATED_PHRASE_ALLOWED = frozenset(
    {
        "word for word",
        "like for like",
        "back to back",
        "face to face",
        "side by side",
        "hand to hand",
        "peer to peer",
        "toe to toe",
        "blow for blow",
        "step by step",
        "time after time",
        "year after year",
        "day after day",
        "case by case",
        "line by line",
        "end to end",
    }
)

# Pseudo-definitions that state nothing about the actual term.
_PSEUDO_DEFINITION_TEMPLATE_RE = re.compile(
    r"\bApplied\s+[A-Za-z][A-Za-z /&-]*?\s+terminology to define precisely and use correctly in context\b"
    r"|\bCore\s+[A-Za-z][A-Za-z /&-]*?\s+control used in professional practice\b"
    r"|\b\w+\s+means\s+Applied\b",
    re.I,
)

# Letters whose spoken name begins with a vowel sound (for acronym articles).
_VOWEL_SOUND_ACRONYM_LETTERS = frozenset("AEFHILMNORSX")
# Vowel-letter words that take "a" (consonant sound).
_CONSONANT_SOUND_PREFIXES = (
    "uni",
    "use",
    "user",
    "euro",
    "europ",
    "eulog",
    "ewe",
    "ubiq",
    "utili",
    "unil",
    "one",
    "once",
    "eu ",
)

_ARTICLE_A_RE = re.compile(r"\b([Aa])\s+([AaEeIiOo][A-Za-z]{2,})\b")


def _word_needs_an(word: str) -> bool:
    w = (word or "").strip()
    if not w:
        return False
    first = w.split()[0]
    low = first.lower()
    letters = re.sub(r"[^A-Za-z]", "", first)
    if letters and letters.isupper() and len(letters) <= 5:
        return letters[0] in _VOWEL_SOUND_ACRONYM_LETTERS
    if any(low.startswith(p) for p in _CONSONANT_SOUND_PREFIXES):
        return False
    return low[:1] in "aeiou"


def _article_agreement_defects(blob: str, role: str = "") -> int:
    count = 0
    for m in _ARTICLE_A_RE.finditer(blob):
        word = m.group(2)
        if _word_needs_an(word):
            count += 1
    if role:
        role_esc = re.escape(role)
        role_first = role.split()[0] if role.split() else role
        vowel_initial = role_first[:1].lower() in "aeiou"
        if _word_needs_an(role):
            # "a <role>" is wrong. The general A-rule already catches vowel-initial
            # role names, so only add the acronym/consonant-initial case it misses.
            if not vowel_initial:
                count += len(re.findall(rf"\ba\s+{role_esc}\b", blob))
        else:
            # role needs "a"; the general rule never inspects "an ...".
            count += len(re.findall(rf"\ban\s+{role_esc}\b", blob))
    return count


def _repeated_phrase_defects(blob: str) -> int:
    count = 0
    for m in _REPEATED_PHRASE_RE.finditer(blob):
        if m.group(0).lower() not in _REPEATED_PHRASE_ALLOWED:
            count += 1
    return count

_INCOMPLETE_CLAUSE_RE = re.compile(
    r"\b(?:using|when|involves|complete|during)\s*,\s*",
    re.I,
)

_MALFORMED_TEMPLATE_RE = re.compile(
    r"\b(?:default standards|therole-specific|name default|involves create|when create)\b",
    re.I,
)

_TAUTOLOGY_WORKFLOW_RE = re.compile(
    r"\bComplete\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+reliably\s+in\s+\1\s+work\b",
    re.I,
)

_MALFORMED_DEFINITION_RE = re.compile(
    r"\bdefinitions covered:\s*[^.]{0,40}\b(?:when|using|involves|complete)\b",
    re.I,
)

_BROKEN_USING_COMMA_RE = re.compile(r"\busing,\s", re.I)


_IRREGULAR_BASE = {
    "fixed": "fix",
    "cut": "cut",
    "built": "build",
    "ran": "run",
    "led": "lead",
    "made": "make",
    "took": "take",
    "wrote": "write",
    "delivered": "deliver",
    "reviewed": "review",
    "added": "add",
    "verified": "verify",
    "configured": "configure",
    "deployed": "deploy",
    "tested": "test",
    "resolved": "resolve",
    "handled": "handle",
    "diagnosed": "diagnose",
    "adjusted": "adjust",
    "rebuilt": "rebuild",
    "inspected": "inspect",
    "validated": "validate",
}


def _to_base_verb(past: str) -> str:
    low = past.lower()
    if low in _IRREGULAR_BASE:
        return _IRREGULAR_BASE[low]
    if low.endswith("ied"):
        return low[:-3] + "y"
    if low.endswith("ed"):
        return low[:-2]
    return low


def audit_surface_quality(text: str, *, role: str = "") -> dict[str, Any]:
    blob = text or ""
    duplicate = len(_DUPLICATE_TOKEN_RE.findall(blob))
    role_tautology = len(_ROLE_TAUTLOGY_RE.findall(blob)) + len(_TAUTOLOGY_WORKFLOW_RE.findall(blob))
    role_tautology += len(_DEFINITION_TAUTOLOGY_RE.findall(blob))
    role_tautology += len(_definition_tautology_ci_matches(blob))
    if role:
        role_esc = re.escape(role)
        role_tautology += len(re.findall(rf"\b{role_esc}\s+{role_esc}\b", blob, re.I))
        role_tautology += len(re.findall(rf"\bnew\s+{role_esc}\s+role\b", blob, re.I))
    malformed_template = len(_MALFORMED_TEMPLATE_RE.findall(blob))
    incomplete_clause = len(_INCOMPLETE_CLAUSE_RE.findall(blob)) + len(_BROKEN_USING_COMMA_RE.findall(blob))
    incomplete_clause += len(_DANGLING_PARTICIPLE_RE.findall(blob))
    malformed_definition = len(_MALFORMED_DEFINITION_RE.findall(blob)) + len(
        _PSEUDO_DEFINITION_RE.findall(blob)
    )
    malformed_definition += len(_PSEUDO_DEFINITION_TEMPLATE_RE.findall(blob))
    malformed_coaching = len(_MALFORMED_COACHING_RE.findall(blob)) + len(
        _MIDSENTENCE_CAP_RE.findall(blob)
    )
    article_agreement = _article_agreement_defects(blob, role)
    duplicate_lead_in = len(_DUPLICATE_LEADIN_RE.findall(blob))
    repeated_phrase = _repeated_phrase_defects(blob)

    total = (
        duplicate
        + role_tautology
        + malformed_template
        + incomplete_clause
        + malformed_definition
        + malformed_coaching
        + article_agreement
        + duplicate_lead_in
        + repeated_phrase
    )
    return {
        "duplicate_token_defects": duplicate,
        "role_tautology_defects": role_tautology,
        "malformed_template_defects": malformed_template,
        "incomplete_clause_defects": incomplete_clause,
        "malformed_definition_defects": malformed_definition,
        "malformed_coaching_defects": malformed_coaching,
        "article_agreement_defects": article_agreement,
        "duplicate_lead_in_defects": duplicate_lead_in,
        "repeated_phrase_defects": repeated_phrase,
        "total_surface_quality_defects": total,
    }


def fix_surface_quality_defects(text: str, *, role: str = "") -> str:
    out = text or ""
    out = _DUPLICATE_TOKEN_RE.sub(r"\1", out)
    if role:
        out = re.sub(rf"\b{re.escape(role)}\s+role\b", role, out, flags=re.I)
        out = re.sub(rf"\bnew\s+{re.escape(role)}\s+role\b", role, out, flags=re.I)
        out = re.sub(rf"\b{re.escape(role)}\s+{re.escape(role)}\b", role, out, flags=re.I)
    out = re.sub(r"\bstrengths in\s+would\b", "strengths would", out, flags=re.I)
    out = re.sub(r"\btherole-specific\b", "the role-specific", out, flags=re.I)
    out = re.sub(r"\bthe the\b", "the", out, flags=re.I)
    out = re.sub(r"\bwork work\b", "work", out, flags=re.I)
    out = re.sub(r"\binvolves create\b", "involves creating", out, flags=re.I)
    out = re.sub(r"\bwhen create\b", "when creating", out, flags=re.I)
    out = re.sub(r"\busing,\s*$", "using documented methods.", out, flags=re.M)
    out = re.sub(r"\busing,\s+", "using ", out, flags=re.I)
    out = re.sub(r"\bname default standards\b", "named standards", out, flags=re.I)
    out = re.sub(r"\bdefault standards\b", "applicable standards", out, flags=re.I)
    # Repair naive coaching conjugations ("you could would" -> "you could").
    out = re.sub(
        r"\b(you|they|we|one|the team)\s+(?:could|would)\s+(?:would|will)\b",
        r"\1 could",
        out,
        flags=re.I,
    )
    out = re.sub(r"\b(you|they|we|one|the team)\s+could\s+can\b", r"\1 can", out, flags=re.I)
    # "<subj> could <pasttense>" -> reduce to base verb after the modal.
    out = re.sub(
        r"\b(you|they|we|one|the team)\s+could\s+"
        r"(fixed|cut|built|ran|led|made|took|wrote|delivered|reviewed|added|verified|"
        r"configured|deployed|tested|resolved|handled|diagnosed|adjusted|rebuilt|inspected|validated)\b",
        lambda m: f"{m.group(1)} could {_to_base_verb(m.group(2))}",
        out,
        flags=re.I,
    )
    # Mid-sentence capitalisation join artifacts (same-line only).
    out = re.sub(r"([a-z]+)[ \t]+For[ \t]+([a-z])", r"\1 for \2", out)
    out = re.sub(r"([a-z]+)[ \t]+It[ \t]+([a-z])", r"\1 it \2", out)
    out = re.sub(r"\bwhile It\b", "while it", out)
    out = _TAUTOLOGY_WORKFLOW_RE.sub(
        lambda m: f"Complete {m.group(1)} work reliably with traceable checkpoints",
        out,
    )
    # Definition tautology: "For a Data Analyst, Data Analyst means" -> drop the repeat.
    out = _DEFINITION_TAUTOLOGY_RE.sub(lambda m: f"For a {m.group(1)}, this", out)
    # Case-differing variant: "For a DevOps Engineer, Devops Engineer means" -> "…, this means".
    def _fix_def_taut_ci(m: "re.Match[str]") -> str:
        first, second = m.group(2).strip(), m.group(3).strip()
        if first != second and first.lower() == second.lower():
            return f"{m.group(1)} {m.group(2)}, this means"
        return m.group(0)
    out = _DEFINITION_TAUTOLOGY_CI_RE.sub(_fix_def_taut_ci, out)
    # Duplicated example lead-ins: keep the first only, with clean punctuation.
    out = re.sub(
        rf"\b({_EXAMPLE_LEADIN})\b[\s,:;.\-]+(?:{_EXAMPLE_LEADIN})\b[\s,:;.\-]*",
        lambda m: f"{m.group(1).rstrip(' ,:;.-')}, ",
        out,
        flags=re.I,
    )
    # Bounded repeated phrase around a connector ("performance for performance").
    def _dedupe_repeat(m: "re.Match[str]") -> str:
        if m.group(0).lower() in _REPEATED_PHRASE_ALLOWED:
            return m.group(0)
        return m.group(1)
    out = _REPEATED_PHRASE_RE.sub(_dedupe_repeat, out)
    # Article agreement for obvious a/an errors.
    def _fix_article(m: "re.Match[str]") -> str:
        art, word = m.group(1), m.group(2)
        if _word_needs_an(word):
            return f"{'An' if art == 'A' else 'an'} {word}"
        return m.group(0)
    out = _ARTICLE_A_RE.sub(_fix_article, out)
    if role:
        role_esc = re.escape(role)
        if _word_needs_an(role):
            out = re.sub(rf"\bA\s+{role_esc}\b", f"An {role}", out)
            out = re.sub(rf"\ba\s+{role_esc}\b", f"an {role}", out)
        else:
            out = re.sub(rf"\bAn\s+{role_esc}\b", f"A {role}", out)
            out = re.sub(rf"\ban\s+{role_esc}\b", f"a {role}", out)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()


def audit_pack_surface_quality(questions: list[dict[str, Any]], *, role: str) -> dict[str, Any]:
    totals = {
        "duplicate_token_defects": 0,
        "role_tautology_defects": 0,
        "malformed_template_defects": 0,
        "incomplete_clause_defects": 0,
        "malformed_definition_defects": 0,
        "malformed_coaching_defects": 0,
        "article_agreement_defects": 0,
        "duplicate_lead_in_defects": 0,
        "repeated_phrase_defects": 0,
        "total_surface_quality_defects": 0,
    }
    for q in questions:
        # Scan ALL user-facing prose recursively (nested lists/dicts/extensions).
        for blob in iter_user_facing_text(q):
            audit = audit_surface_quality(blob, role=role)
            for key in totals:
                totals[key] += audit.get(key, 0)
    return totals
