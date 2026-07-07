"""Deterministic claim-integrity checks (Iteration 004E-E2.2 + corrective pass).

Product rules (locked):
  * Feature access != evidence status. Evidence stays optional.
  * Explicit user-stated experience is trusted WITHOUT external evidence.
  * Job/opportunity data (posting description, responsibilities, requirements,
    company research, URL extraction) must NEVER establish personal biography.
  * Never invent employers, projects, tools, dates, metrics, percentages,
    outcomes, certifications, team sizes, or personal incidents.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from app.agents.job_search.quality.user_facing_text import iter_user_facing_text

ClaimSupportStatus = Literal[
    "claimed",
    "profile_supported",
    "evidence_backed",
    "verified",
    "assessment_demonstrated",
    "suggested",
    "unknown",
]

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Past-tense (and a few irregular) first-person action verbs signal a claimed
# personal *event* ("I fixed...", "I reviewed..."). Conditional/hypothetical
# framing ("I would...", "I could...") is intentionally NOT treated as a claim
# because it is an approved coaching construction.
_IRREGULAR_PAST = (
    "cut",
    "rebuilt",
    "built",
    "ran",
    "drove",
    "led",
    "oversaw",
    "made",
    "took",
    "wrote",
    "set",
    "saw",
    "sent",
    "kept",
    "held",
    "dealt",
    "spent",
    "won",
    "met",
    "brought",
    "taught",
    "rebuild",  # base forms occasionally emitted
    # Zero-inflection irregulars (same form as base) whose collective/first-person
    # use is a definite past event ("the team hit", "we put", "we shut").
    "hit",
    "put",
    "shut",
    "spread",
    "beat",
    "burst",
    "let",
    "quit",
    "split",
    "shed",
    "hurt",
    # Common irregular past-tense action verbs.
    "broke",
    "chose",
    "found",
    "gave",
    "went",
    "came",
    "got",
    "caught",
    "drew",
    "flew",
    "knew",
    "left",
    "lost",
    "paid",
    "sold",
    "spoke",
    "threw",
    "began",
)

_FIRST_PERSON_EVENT_RE = re.compile(
    r"\bI\s+(?:[a-z]+ed|" + "|".join(_IRREGULAR_PAST) + r")\b",
    re.I,
)

# Collective ("we"/"the team"/"our team"/"the crew"/"the squad") past-tense events
# presented as the user's own history.
_COLLECTIVE_EVENT_RE = re.compile(
    r"\b(?:we|our team|the team|the crew|the squad)\s+(?:[a-z]+ed|"
    + "|".join(_IRREGULAR_PAST)
    + r")\b",
    re.I,
)

# Any past-tense action verb (broad) — used ONLY in combination with strong
# episode/actor framing, never on its own.
_PAST_ACTION_RE = re.compile(
    r"\b(?:[a-z]{3,}ed|" + "|".join(_IRREGULAR_PAST) + r")\b",
    re.I,
)

# Episode-framing openers introduce a specific past work incident. On their own
# they are not a claim (generic advice can say "during a project, teams often…"),
# so they are only treated as a claim clause when paired with a past action or a
# concrete metric (see ``_clause_is_event``). Detection is NOT tied to a leading
# first-person "I".
_EPISODE_OPENER_RE = re.compile(
    r"\b(?:on\s+(?:an?|a\s+recent|a\s+previous|my\s+last)\s+assignment"
    r"|during\s+(?:a|an|the|one|my|our)\s+"
    r"(?:project|release|deployment|deploy|sprint|migration|incident|outage|rollout|"
    r"ward\s+round|round|shift|call|handover|hand-?off|audit|placement|rotation|"
    r"campaign|build|launch|go-?live|cut-?over|on-?call\s+shift)"
    r"|while\s+working\s+on"
    r"|while\s+(?:i|we)\s+(?:was|were)"
    r"|on\s+my\s+last\s+(?:project|shift|role|assignment|placement)"
    r"|in\s+(?:a|my)\s+previous\s+role"
    r"|in\s+my\s+last\s+role"
    r"|in\s+production\b)",
    re.I,
)

# Second-person HISTORICAL framing (definite past act attributed to the user),
# distinct from second-person coaching voice ("you would/should verify").
_SECOND_PERSON_HISTORICAL_RE = re.compile(
    r"\byou\s+(?:specifically|personally|previously|once|actually|already|even|"
    r"successfully|single-?handedly)\s+(?:[a-z]+ed|" + "|".join(_IRREGULAR_PAST) + r")\b",
    re.I,
)

# First-person responsibility/ownership framing ("my responsibility was…",
# "I was responsible for…").
_RESPONSIBILITY_RE = re.compile(
    r"\b(?:my|our)\s+(?:responsibility|role|job|task|remit|duty|brief)\s+"
    r"(?:was|were|had been|included|involved)\b"
    r"|\bI\s+was\s+(?:responsible|tasked|assigned|accountable|brought\s+in|hired)\b"
    r"|\bwe\s+were\s+(?:responsible|tasked|assigned|accountable)\b",
    re.I,
)

# Explicit fabricated-history phrasings.
_HISTORY_PHRASE_RE = re.compile(
    r"(?:in\s+(?:a\s+)?previous\s+[^.]{0,80}?\s+assignment"
    r"|in\s+my\s+[^.]{0,60}?\s+career"
    r"|in\s+my\s+previous\s+role"
    r"|during\s+a\s+(?:live\s+)?[^.]{0,60}?\s+assignment"
    r"|on\s+my\s+last\s+project"
    r"|i\s+have\s+\d+\s+years?)",
    re.I,
)

# "I have N years", "I have 5 years' experience" style numeric personal claims.
_HAS_YEARS_RE = re.compile(r"\bI\s+have\s+\d+\s+years?\b", re.I)

# STRONG numeric patterns are inherently achievement/change claims (before/after
# transitions, signed deltas, percentile drops, change-verb + number). They are
# flagged on their own (subject to support/hypothetical/standard checks) because
# they cannot plausibly be a neutral calculation spec or standard.
_STRONG_NUMERIC_PATTERNS = (
    re.compile(r"\bfrom\s+\d[\d,.]*\s*[a-z%]*\s+to\s+\d[\d,.]*\s*[a-z%]*", re.I),
    re.compile(r"\b\d+(?:\.\d+)?\s*%\s+to\s+\d+(?:\.\d+)?\s*%", re.I),
    re.compile(r"[+\-]\d+(?:\.\d+)?\s*%", re.I),
    re.compile(r"\b(?:p\d{2,3})\s+(?:dropped|fell|down|reduced|rose|climbed)\s+to\s+\d", re.I),
    re.compile(
        r"\b(?:cut|reduced|dropped|lowered|increased|grew|raised|boosted|improved|saved)\s+"
        r"(?:\w+\s+){0,4}?(?:to|by)\s+\d",
        re.I,
    ),
    # Result/outcome framing: a change-of-state verb landing on a concrete value
    # ("returned below 0.2%", "P95 dropped to 180 ms", "throughput rose to 5k").
    re.compile(
        r"\b(?:dropped|fell|rose|climbed|jumped|surged|declined|shrank|shrunk|"
        r"returned|recovered|stabili[sz]ed|landed|settled|came\s+in|held\s+at)\s+"
        r"(?:\w+\s+){0,3}?(?:to|at|below|under|above|around|near)\s+\d",
        re.I,
    ),
    # "down to 180 ms" / "up to 5,000 rows" bare directional result values.
    re.compile(r"\b(?:down|up)\s+to\s+\d[\d,.]*\s*(?:%|ms|milliseconds|seconds|secs|"
               r"minutes|mins|hours|hrs|days|weeks|months|k|m|bn|qps|rps|rows|"
               r"transactions|requests|users)\b", re.I),
)

# WEAK numeric patterns (bare percentage, bare duration, currency, headcount) are
# ambiguous: they may be a neutral calculation, question spec, or standard. They
# are flagged ONLY when the sentence also carries a real achievement/change verb
# or a first-person/collective personal-event framing.
_WEAK_NUMERIC_PATTERNS = (
    re.compile(r"\b\d+(?:\.\d+)?\s*%", re.I),
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:ms|milliseconds|seconds|secs|minutes|mins|hours|hrs|days|weeks|months)\b", re.I),
    re.compile(r"[£$€]\s?\d[\d,]*(?:\.\d+)?", re.I),
    re.compile(r"\b\d+\s+(?:people|employees|staff|team members|engineers|developers|reports|direct reports)\b", re.I),
    # Operational scale used as claimed event magnitude (throughput/volume). Weak:
    # only counts when the clause also carries achievement/personal-event framing.
    re.compile(r"\b\d[\d,.]*\s*(?:k|m|bn)?\s*(?:qps|rps|rows|transactions|records|requests|queries|tickets|users)\b", re.I),
)

# Real achievement/change markers (verbs). Deliberately excludes loose tokens
# like " to "/"from "/"cost"/"latency" that also occur in neutral calculation
# specs and question stems.
_ACHIEVEMENT_CONTEXT = (
    "improv",
    "reduc",
    "increas",
    "decreas",
    "cut ",
    "saved",
    "grew",
    "boost",
    "raised",
    "lowered",
    "dropped",
    "faster",
    "slower",
    "headcount",
    "managed",
    "delivered",
    "achieved",
    "shrank",
    "shortened",
    "throughput",
    "processed",
    "handled",
    "scaled",
    "time saved",
    "saved us",
)

# Tokens that mark a numeric as a legitimate standard / version / neutral value.
_STANDARD_NUMERIC_CONTEXT = (
    "1nf",
    "2nf",
    "3nf",
    "normal form",
    "ansi",
    "iso ",
    "iec ",
    "bs 7671",
    "version",
    "ohms",
    "voltage",
    "amp",
    "hz",
)

# Local (sentence-scoped) hypothetical / coaching markers. A marker only
# immunises the sentence it appears in — never the whole artifact.
_LOCAL_HYPOTHETICAL_MARKERS = (
    "hypothetical",
    "illustrative example",
    "illustrative scenario",
    "example scenario",
    "for practice",
    "a strong answer could",
    "a strong answer for",
    "if this reflects your real experience",
    "you could",
    "you would",
    "one could",
    "candidates could",
)


def _sentences(text: str) -> list[str]:
    if not text:
        return []
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


# Clause split for clause-appropriate hypothetical carve-outs. A hypothetical
# marker must immunise only the clause it appears in, so a later "hypothetical"
# clause cannot sanitise an earlier unsupported claim in the same sentence.
_CLAUSE_SPLIT_RE = re.compile(
    r"\s*(?:;|—|–|--)\s*|\s*,\s*(?=(?:though|although|whereas|however|but|while|yet|and|then)\b)"
    r"|\s+(?:though|although|whereas|however|but|while|yet)\s+",
    re.I,
)


def _clauses(sentence: str) -> list[str]:
    parts = [c.strip() for c in _CLAUSE_SPLIT_RE.split(sentence or "") if c and c.strip()]
    return parts or ([sentence.strip()] if sentence and sentence.strip() else [])


def _is_locally_hypothetical(text: str) -> bool:
    low = text.lower()
    return any(marker in low for marker in _LOCAL_HYPOTHETICAL_MARKERS)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def collect_user_claim_context(job: dict[str, Any]) -> dict[str, Any]:
    """Collect explicit USER/PERSONAL facts, kept strictly separate from
    OPPORTUNITY/JOB data.

    Personal sources (can establish biography): profile summary, work history,
    user-entered achievements, explicit personal-history fields.

    Job sources (must NOT establish biography): posting description, extracted
    responsibilities, requirements, extracted skills, company research, URL
    extraction. These may guide questions/study/coaching only.
    """
    achievements: list[str] = []
    for key in ("achievements", "key_achievements", "user_achievements"):
        val = job.get(key)
        if isinstance(val, list):
            achievements.extend(str(v).strip() for v in val if v)
        elif isinstance(val, str) and val.strip():
            achievements.append(val.strip())

    work_history: list[str] = []
    for exp in job.get("work_experiences") or job.get("work_experience") or []:
        if isinstance(exp, dict):
            parts = [exp.get("title"), exp.get("company"), exp.get("description")]
            work_history.append(" ".join(str(p) for p in parts if p))
        elif isinstance(exp, str):
            work_history.append(exp)

    profile_summary = str(
        job.get("profile_summary") or job.get("user_profile_summary") or ""
    ).strip()
    # Additional explicitly user-origin free-text fields, if the pipeline supplies them.
    for key in ("user_statement", "personal_statement", "user_experience_notes"):
        extra = str(job.get(key) or "").strip()
        if extra:
            profile_summary = f"{profile_summary} {extra}".strip()

    # --- OPPORTUNITY / JOB data (never personal biography) ---
    responsibilities = [
        str(r.get("text") if isinstance(r, dict) else r).strip()
        for r in (job.get("responsibilities") or [])
        if r
    ]
    requirements = [str(r).strip() for r in (job.get("requirements") or []) if r]
    skills = [
        str(s.get("skill") if isinstance(s, dict) else s).strip()
        for s in (job.get("extracted_skills") or [])
        if s
    ]
    description = str(job.get("description_raw") or "").strip()

    evidence_items: list[str] = []
    for key in ("evidence_items", "uploaded_evidence", "portfolio_items"):
        for item in job.get(key) or []:
            if isinstance(item, dict):
                evidence_items.append(str(item.get("label") or item.get("title") or item))
            else:
                evidence_items.append(str(item))

    # Personal-only blob: the ONLY text that can support first-person biography.
    explicit_blob = " ".join(
        filter(None, [profile_summary, " ".join(achievements), " ".join(work_history)])
    ).lower()

    # Broader context blob (used for question/study generation, NOT biography).
    user_context_blob = " ".join(
        filter(
            None,
            [
                explicit_blob,
                " ".join(responsibilities),
                " ".join(requirements),
                description,
            ],
        )
    ).lower()

    has_work_history = bool(work_history)
    has_profile_summary = bool(profile_summary)
    has_achievements = bool(achievements)
    has_evidence = bool(evidence_items)

    # CRITICAL: explicit personal experience derives ONLY from user/personal
    # sources. Job responsibilities + description must NEVER qualify.
    has_explicit_experience = any([has_work_history, has_profile_summary, has_achievements])

    # profile_supported requires MULTIPLE compatible USER records.
    personal_record_count = (
        len(work_history) + len(achievements) + (1 if has_profile_summary else 0)
    )

    return {
        "explicit_blob": explicit_blob,
        "user_context_blob": user_context_blob,
        "achievements": achievements,
        "work_history": work_history,
        "responsibilities": responsibilities,
        "requirements": requirements,
        "skills": skills,
        "evidence_items": evidence_items,
        "has_explicit_experience": has_explicit_experience,
        "personal_record_count": personal_record_count,
        "has_evidence": has_evidence,
        "job_thin": _is_job_thin(job),
    }


def _is_job_thin(job: dict[str, Any]) -> bool:
    if job.get("job_posting_extraction") or job.get("company_research"):
        return False
    if (job.get("responsibilities") or []) or (job.get("requirements") or []):
        return False
    if (job.get("extracted_skills") or []) or (job.get("description_raw") or "").strip():
        return False
    return bool((job.get("title") or "").strip())


def classify_claim_support(job: dict[str, Any], claim_text: str = "") -> ClaimSupportStatus:
    ctx = collect_user_claim_context(job)
    if ctx["has_evidence"]:
        # Uploaded evidence is evidence_backed — NOT automatically verified.
        return "evidence_backed"
    if ctx["has_explicit_experience"]:
        if ctx["personal_record_count"] >= 2:
            return "profile_supported"
        return "claimed"
    if claim_text:
        return "suggested"
    return "unknown"


# ---------------------------------------------------------------------------
# Support checks
# ---------------------------------------------------------------------------


def _content_words(text: str) -> list[str]:
    return re.findall(r"[a-z]{4,}", (text or "").lower())


def _sentence_supported_by_user(sentence: str, ctx: dict[str, Any]) -> bool:
    """A specific claim is supported only when its key content words appear in
    the PERSONAL blob (profile/achievements/work history)."""
    blob = ctx.get("explicit_blob") or ""
    if not blob:
        return False
    words = [w for w in _content_words(sentence) if w not in _STOPWORDS]
    if not words:
        return False
    hits = sum(1 for w in words if w in blob)
    # Require a meaningful overlap so a single incidental word cannot "support"
    # an otherwise invented anecdote.
    return hits >= max(2, len(set(words)) // 3)


def _numeric_supported_by_user(sentence: str, ctx: dict[str, Any]) -> bool:
    blob = ctx.get("explicit_blob") or ""
    if not blob:
        return False
    nums = re.findall(r"\d+(?:\.\d+)?", sentence.lower())
    if not nums:
        return False
    if not all(n in blob for n in nums):
        return False
    return _sentence_supported_by_user(sentence, ctx)


_STOPWORDS = {
    "with", "that", "this", "from", "have", "were", "would", "could", "your",
    "their", "them", "then", "than", "when", "what", "which", "will", "into",
    "about", "after", "before", "using", "used", "also", "such", "each", "some",
    "role", "work", "team", "example", "scenario", "answer", "question",
}


# ---------------------------------------------------------------------------
# Detection API
# ---------------------------------------------------------------------------


def _has_numeric_metric(text: str) -> bool:
    """A concrete metric appears (used to promote an episode opener into a claim)."""
    for pattern in _STRONG_NUMERIC_PATTERNS:
        if pattern.search(text):
            return True
    for pattern in _WEAK_NUMERIC_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _episode_clause_is_event(clause: str) -> bool:
    """An episode-framing opener only counts as a personal event when the clause
    also names a definite past action or a concrete metric."""
    if not _EPISODE_OPENER_RE.search(clause):
        return False
    return bool(_PAST_ACTION_RE.search(clause) or _has_numeric_metric(clause))


def detect_personal_claims(text: str) -> list[str]:
    """All personal-event phrases, ignoring support.

    Detection is semantic (actor framing, episode framing, tense/action, ownership
    framing) — NOT limited to sentences that literally begin with "I".
    """
    hits: list[str] = []
    for clause in _clauses(text or ""):
        hits += [m.group(0) for m in _FIRST_PERSON_EVENT_RE.finditer(clause)]
        hits += [m.group(0) for m in _COLLECTIVE_EVENT_RE.finditer(clause)]
        hits += [m.group(0) for m in _HISTORY_PHRASE_RE.finditer(clause)]
        hits += [m.group(0) for m in _SECOND_PERSON_HISTORICAL_RE.finditer(clause)]
        hits += [m.group(0) for m in _RESPONSIBILITY_RE.finditer(clause)]
        if _episode_clause_is_event(clause):
            m = _EPISODE_OPENER_RE.search(clause)
            if m:
                hits.append(m.group(0))
    return hits


def _clause_supported_by_user(clause: str, ctx: dict[str, Any]) -> bool:
    return _sentence_supported_by_user(clause, ctx)


def detect_unsupported_personal_claims(text: str, job: dict[str, Any]) -> list[str]:
    """Personal biography not supported by explicit user context.

    Having *some* real experience never authorises *unrelated* invented
    experience: each clause is judged on its own support, and a hypothetical
    marker only immunises the clause it appears in.
    """
    ctx = collect_user_claim_context(job)
    hits: list[str] = []
    for sentence in _sentences(text):
        for clause in _clauses(sentence):
            if _is_locally_hypothetical(clause):
                continue
            phrases = detect_personal_claims(clause)
            if not phrases:
                continue
            if ctx["has_explicit_experience"] and _clause_supported_by_user(clause, ctx):
                continue
            hits.extend(phrases)
    return hits


def _has_achievement_context(sentence: str) -> bool:
    low = sentence.lower()
    return bool(
        any(tok in low for tok in _ACHIEVEMENT_CONTEXT)
        or _FIRST_PERSON_EVENT_RE.search(sentence)
        or _COLLECTIVE_EVENT_RE.search(sentence)
        or _SECOND_PERSON_HISTORICAL_RE.search(sentence)
        or _RESPONSIBILITY_RE.search(sentence)
        or _episode_clause_is_event(sentence)
        or _HAS_YEARS_RE.search(sentence)
    )


def _numeric_matches_in_sentence(sentence: str) -> list[str]:
    """Return achievement-style numeric spans in a sentence.

    Strong patterns match on their own; weak (ambiguous) patterns require a real
    achievement/change or personal-event context so neutral calculation specs and
    question stems (e.g. "must handle X in 50 ms") are not flagged.
    """
    matched: list[str] = []
    for pattern in _STRONG_NUMERIC_PATTERNS:
        matched.extend(m.group(0).strip() for m in pattern.finditer(sentence))
    if _has_achievement_context(sentence):
        for pattern in _WEAK_NUMERIC_PATTERNS:
            matched.extend(m.group(0).strip() for m in pattern.finditer(sentence))
    return matched


def detect_unsupported_numeric_claims(text: str, job: dict[str, Any]) -> list[str]:
    ctx = collect_user_claim_context(job)
    hits: list[str] = []
    for sentence in _sentences(text):
        for clause in _clauses(sentence):
            low = clause.lower()
            if _is_locally_hypothetical(clause):
                continue
            if any(tok in low for tok in _STANDARD_NUMERIC_CONTEXT):
                continue
            matched = _numeric_matches_in_sentence(clause)
            if not matched:
                continue
            if _numeric_supported_by_user(clause, ctx):
                continue
            hits.extend(matched)
    return hits


# ---------------------------------------------------------------------------
# Safe coaching rewrite / sanitizer
# ---------------------------------------------------------------------------

# Ordered, grammar-safe first-person -> second-person coaching normalisations.
# Order matters: modal combinations are resolved before the bare-subject rule so
# we never produce "you could would" / "you could fixed".
_PRONOUN_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bI\s+would\b", re.I), "you could"),
    (re.compile(r"\bI\s+will\b", re.I), "you would"),
    (re.compile(r"\bI\s+can\b", re.I), "you can"),
    (re.compile(r"\bI\s+could\b", re.I), "you could"),
    (re.compile(r"\bI\s+might\b", re.I), "you might"),
    (re.compile(r"\bI\s+may\b", re.I), "you may"),
    (re.compile(r"\bI\s+should\b", re.I), "you should"),
    (re.compile(r"\bI\s+must\b", re.I), "you must"),
    (re.compile(r"\bI\s+have\b", re.I), "you have"),
    (re.compile(r"\bI\s+had\b", re.I), "you had"),
    (re.compile(r"\bI\s+am\b", re.I), "you are"),
    (re.compile(r"\bI'm\b", re.I), "you are"),
    (re.compile(r"\bI've\b", re.I), "you have"),
    (re.compile(r"\bI'd\b", re.I), "you would"),
    (re.compile(r"\bWe\s+would\b", re.I), "the team could"),
    (re.compile(r"\bWe\s+will\b", re.I), "the team would"),
    (re.compile(r"\bWe\s+can\b", re.I), "the team can"),
    # Bare subjects (present-tense method statements) become second person.
    (re.compile(r"\bI\s+", re.I), "you "),
    (re.compile(r"\bwe\s+", re.I), "the team "),
    (re.compile(r"\bmy\b", re.I), "your"),
    (re.compile(r"\bmine\b", re.I), "yours"),
    (re.compile(r"\bmyself\b", re.I), "yourself"),
)


def _normalise_to_coaching_voice(sentence: str) -> str:
    out = sentence
    for pattern, repl in _PRONOUN_RULES:
        out = pattern.sub(repl, out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    if out:
        out = out[0].upper() + out[1:]
    return out


def _sentence_is_fabricated_event(sentence: str, ctx: dict[str, Any]) -> bool:
    if _is_locally_hypothetical(sentence):
        return False
    if not (
        _FIRST_PERSON_EVENT_RE.search(sentence)
        or _COLLECTIVE_EVENT_RE.search(sentence)
        or _HISTORY_PHRASE_RE.search(sentence)
        or _SECOND_PERSON_HISTORICAL_RE.search(sentence)
        or _RESPONSIBILITY_RE.search(sentence)
        or _episode_clause_is_event(sentence)
        or _HAS_YEARS_RE.search(sentence)
    ):
        return False
    if ctx["has_explicit_experience"] and _sentence_supported_by_user(sentence, ctx):
        return False
    return True


def _sentence_has_unsupported_numeric(sentence: str, ctx: dict[str, Any]) -> bool:
    low = sentence.lower()
    if _is_locally_hypothetical(sentence):
        return False
    if any(tok in low for tok in _STANDARD_NUMERIC_CONTEXT):
        return False
    if not _numeric_matches_in_sentence(sentence):
        return False
    return not _numeric_supported_by_user(sentence, ctx)


def _indefinite_article(word: str) -> str:
    """Return 'a' or 'an' agreeing with the sound of the first word.

    Delegates to the surface-quality guard's shared vowel-sound / acronym heuristic
    so generated coaching lines never emit 'a Electrical Engineer', 'a HR Assistant',
    or 'an University'. Kept in sync with the surface audit that would otherwise flag
    the same string.
    """
    from app.agents.job_search.quality.surface_quality_guard import _word_needs_an

    return "an" if _word_needs_an(word or "") else "a"


def _hypothetical_example_line(job: dict[str, Any]) -> str:
    role = str(job.get("title") or "professional").strip()
    article = _indefinite_article(role)
    return (
        f"Hypothetical example: {article} {role} could describe a realistic situation, the method used, "
        f"the checks applied, and the outcome — using your own genuine experience where you have it."
    )


def rewrite_or_flag_unsupported_claims(
    text: str, job: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Sanitise unsupported biography/metrics into safe coaching/hypothetical text.

    Grammar-safe: drops fabricated event/metric sentences (rather than mechanically
    conjugating them) and normalises remaining first-person method statements into
    a clean second-person coaching voice.
    """
    original = text or ""
    ctx = collect_user_claim_context(job)
    personal_hits = detect_unsupported_personal_claims(original, job)
    numeric_hits = detect_unsupported_numeric_claims(original, job)

    if not personal_hits and not numeric_hits:
        meta = {
            "claim_support_status": classify_claim_support(job),
            "unsupported_personal_claim_count": 0,
            "unsupported_numeric_claim_count": 0,
            "rewritten_for_claim_integrity": False,
        }
        return original.strip(), meta

    kept: list[str] = []
    dropped_any = False
    for sentence in _sentences(original):
        if _sentence_is_fabricated_event(sentence, ctx) or _sentence_has_unsupported_numeric(
            sentence, ctx
        ):
            dropped_any = True
            continue
        # Remaining first-person method statements -> coaching voice.
        if _FIRST_PERSON_EVENT_RE.search(sentence) or re.search(r"\bI\b|\bwe\b|\bmy\b", sentence, re.I):
            kept.append(_normalise_to_coaching_voice(sentence))
        else:
            kept.append(sentence.strip())

    body = " ".join(s for s in kept if s).strip()
    if dropped_any:
        body = f"{body} {_hypothetical_example_line(job)}".strip() if body else _hypothetical_example_line(job)

    # Final safety sweep: no residual unsupported metric tokens.
    for phrase in detect_unsupported_numeric_claims(body, job):
        body = re.sub(re.escape(phrase), "a measurable improvement", body, flags=re.I)

    meta = {
        "claim_support_status": classify_claim_support(job),
        "unsupported_personal_claim_count": len(personal_hits),
        "unsupported_numeric_claim_count": len(numeric_hits),
        "rewritten_for_claim_integrity": body.strip() != original.strip(),
    }
    return body.strip(), meta


# ---------------------------------------------------------------------------
# Auditing
# ---------------------------------------------------------------------------


# Phrases that assert the posting captured specific facts (its listed duties,
# skills, or "what you read"). They are legitimate ONLY when the job genuinely
# carries those captured facts. On a title-only / thin input there is nothing
# captured, so these are fabricated posting claims (Defect Class E).
_CAPTURED_FACT_CLAIM_MARKERS: tuple[str, ...] = (
    "skills listed",
    "listed responsibilities",
    "responsibilities listed",
    "duties listed",
    "listed duties",
    "posting centres on",
    "posting centers on",
    "based on what you've read",
    "based on what you have read",
    "what you have read",
    "what you've read",
    "as listed in the posting",
    "listed in the job description",
)


def detect_unsupported_captured_fact_claims(text: str, job: dict[str, Any]) -> list[str]:
    """Captured-posting-fact claims that no captured evidence supports.

    Only fires when the job is thin (no responsibilities / skills / description
    were actually captured). A rich posting that genuinely lists duties and
    skills may reference them.
    """
    ctx = collect_user_claim_context(job)
    if not ctx.get("job_thin"):
        return []
    low = (text or "").lower()
    return [m for m in _CAPTURED_FACT_CLAIM_MARKERS if m in low]


def audit_claim_integrity(text: str, job: dict[str, Any]) -> dict[str, Any]:
    personal = detect_unsupported_personal_claims(text, job)
    numeric = detect_unsupported_numeric_claims(text, job)
    captured_fact = detect_unsupported_captured_fact_claims(text, job)
    ctx = collect_user_claim_context(job)
    thin_violations = 0
    if ctx["job_thin"]:
        thin_violations += len(personal) + len(numeric) + len(captured_fact)
    return {
        "claim_support_status": classify_claim_support(job),
        "unsupported_personal_claim_count": len(personal),
        "unsupported_numeric_claim_count": len(numeric),
        "unsupported_captured_fact_claim_count": len(captured_fact),
        "thin_input_specificity_violation_count": thin_violations,
        "unsupported_personal_claims": personal[:5],
        "unsupported_numeric_claims": numeric[:5],
        "unsupported_captured_fact_claims": captured_fact[:5],
    }


def audit_pack_claim_integrity(
    questions: list[dict[str, Any]], job: dict[str, Any]
) -> dict[str, Any]:
    """Recursively audit ALL user-facing text in each question (model answer,
    answer explanation, study material, nested lists/dicts/extensions)."""
    personal = numeric = thin = 0
    personal_examples: list[str] = []
    numeric_examples: list[str] = []
    for q in questions:
        for blob in iter_user_facing_text(q):
            audit = audit_claim_integrity(blob, job)
            personal += audit["unsupported_personal_claim_count"]
            numeric += audit["unsupported_numeric_claim_count"]
            thin += audit["thin_input_specificity_violation_count"]
            if audit["unsupported_personal_claims"] and len(personal_examples) < 8:
                personal_examples.extend(audit["unsupported_personal_claims"])
            if audit["unsupported_numeric_claims"] and len(numeric_examples) < 8:
                numeric_examples.extend(audit["unsupported_numeric_claims"])
    return {
        "unsupported_personal_claim_count": personal,
        "unsupported_numeric_claim_count": numeric,
        "thin_input_specificity_violation_count": thin,
        "unsupported_personal_claim_examples": personal_examples[:8],
        "unsupported_numeric_claim_examples": numeric_examples[:8],
    }
