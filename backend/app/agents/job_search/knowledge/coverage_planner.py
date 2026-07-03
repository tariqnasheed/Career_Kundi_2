"""Coverage planning layer — ensures interview packs meet minimum category/skill breadth."""

from __future__ import annotations

import re
from typing import Any

_TOOL_KEYWORDS = (
    "sql", "excel", "aws", "docker", "kubernetes", "python", "java", "tableau",
    "power bi", "git", "jenkins", "terraform", "ansible", "linux", "windows",
    "sap", "salesforce", "jira", "confluence", "autocad", "revit", "matlab",
    "r ", "spark", "snowflake", "databricks", "azure", "gcp", "ci/cd", "github",
)

_SAFETY_GOVERNANCE_KEYWORDS = (
    "safety", "compliance", "standard", "governance", "regulation", "haccp",
    "bs 7671", "iec", "hipaa", "gdpr", "mhra", "nice", "escalation", "risk",
    "allergen", "hygiene", "commissioning", "pharmacology", "prescribing",
)

_SIMPLE_ROLE_HINTS = (
    "barista", "cashier", "cleaner", "receptionist", "warehouse", "picker",
    "packer", "driver", "waiter", "waitress", "gardener", "housekeeper",
)

MIN_EXPORTABLE_PACK_QUESTIONS = 28
TARGET_PACK_QUESTIONS = 32

_CREATIVE_MEDIA_HINTS = (
    "journalist", "graphic designer", "video editor", "content writer", "copywriter",
    "photographer", "editor", "reporter", "broadcast", "media",
)
_CREATOR_TRENDING_HINTS = (
    "youtuber", "influencer", "podcaster", "social media creator", "content creator",
    "streamer", "esports", "vlogger", "creator",
)
_SPORTS_HINTS = (
    "footballer", "cricketer", "athlete", "coach", "fitness trainer", "personal trainer",
    "sports player", "sportsperson",
)

_ARCHETYPE_LEGACY_TYPES = frozenset(
    {
        "ethics",
        "portfolio",
        "audience_research",
        "story_planning",
        "production_workflow",
        "platform_tools",
        "publishing_schedule",
        "analytics_kpi",
        "brand_safety",
        "copyright",
        "crisis_reputation",
        "editor_feedback",
        "quality_review",
        "content_niche",
        "training_discipline",
        "match_preparation",
        "teamwork_sports",
        "sportsmanship",
        "recovery_awareness",
        "coaching_feedback",
        "content_planning",
        "community_management",
        "monetization_awareness",
        "filming_recording",
        "thumbnail_hooks",
        "workflow_process",
        "stakeholder_communication",
        "growth_seniority",
    }
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _is_simple_role(title: str) -> bool:
    t = _norm(title)
    return any(h in t for h in _SIMPLE_ROLE_HINTS)


def _skills_from_job(job: dict) -> list[str]:
    skills: list[str] = []
    for s in job.get("extracted_skills") or []:
        name = s.get("skill") if isinstance(s, dict) else s
        if name:
            skills.append(str(name))
    for req in job.get("requirements") or []:
        text = req.get("text") if isinstance(req, dict) else req
        if text and str(text) not in skills:
            skills.append(str(text))
    return list(dict.fromkeys(skills))


def _responsibilities(job: dict) -> list[str]:
    out: list[str] = []
    for r in job.get("responsibilities") or []:
        text = r.get("text") if isinstance(r, dict) else r
        if text:
            out.append(str(text))
    return out


def _question_blob(questions: list[dict]) -> str:
    return " ".join(_norm(q.get("question", "")) for q in questions)


def _categories(questions: list[dict]) -> set[str]:
    return {str(q.get("category") or "") for q in questions}


def _question_types(questions: list[dict]) -> set[str]:
    return {str(q.get("question_type") or "") for q in questions if q.get("question_type")}


def _count_category(questions: list[dict], category: str) -> int:
    return sum(1 for q in questions if q.get("category") == category)


def _has_type_or_marker(questions: list[dict], qtype: str, markers: tuple[str, ...] = ()) -> bool:
    blob = _question_blob(questions)
    if any(q.get("question_type") == qtype for q in questions):
        return True
    return any(m in blob for m in markers)


def _responsibility_covered(resp: str, questions: list[dict]) -> bool:
    key = _norm(resp)[:40]
    for q in questions:
        qtext = _norm(q.get("question", ""))
        if key[:20] in qtext or _norm(resp)[:25] in qtext:
            return True
        if "this role involves" in qtext and key[:15] in qtext:
            return True
    return False


def _skill_covered(skill: str, questions: list[dict]) -> bool:
    sk = _norm(skill)
    for q in questions:
        if sk in _norm(q.get("skill_tag") or ""):
            return True
        if sk in _norm(q.get("question", "")):
            return True
        if sk in _norm(" ".join(q.get("related_skills") or [])):
            return True
    return False


def _tool_skills(skills: list[str]) -> list[str]:
    found: list[str] = []
    for skill in skills:
        sk = _norm(skill)
        if any(t in sk for t in _TOOL_KEYWORDS):
            found.append(skill)
    return found


def _needs_safety_question(job: dict, skills: list[str]) -> bool:
    blob = _norm(" ".join(_responsibilities(job) + skills + (job.get("requirements") or [])))
    return any(k in blob for k in _SAFETY_GOVERNANCE_KEYWORDS)


def _seniority_label(job: dict, difficulty: str) -> tuple[str, str]:
    seniority = (job.get("experience_level") or job.get("seniority") or "").lower()
    if difficulty == "entry" or "entry" in seniority or "0–2" in seniority:
        return "junior", "entry-level"
    if difficulty == "senior" or "senior" in seniority or "lead" in seniority or "8+" in seniority:
        return "senior", "senior/lead"
    return "mid", "mid-level"


def _hr_motivation_question(job: dict) -> str:
    role = job.get("title") or "this role"
    role_l = _norm(role)
    skills = ", ".join(_skills_from_job(job)[:4])

    if "data analyst" in role_l:
        return (
            f"Why do you want this {role} role, and how would you turn messy operational data into "
            f"trusted SQL queries, dashboards, and KPI reporting with clear data quality checks "
            f"that stakeholders can act on?"
        )
    if "electrical engineer" in role_l:
        return (
            f"Why are you pursuing this {role} role, and how would you deliver safe, compliant electrical work "
            f"across load calculations, cable sizing, commissioning, and site coordination?"
        )
    if "clinical pharmacist" in role_l or "pharmacist" in role_l:
        return (
            f"Why do you want this {role} role, and how would you contribute to medicines optimisation through "
            f"medication review, prescribing safety checks, patient counselling, and clinical governance?"
        )
    if "barista" in role_l:
        return (
            f"Why do you want this {role} role, and how would you keep drink quality, hygiene, allergen control, "
            f"and customer service consistent during busy rush periods?"
        )
    if "devops" in role_l:
        return (
            f"Why are you interested in this {role} role, and how would you improve reliable deployments, "
            f"monitoring, incident response, and secure infrastructure automation using tools such as {skills}?"
        )
    return (
        f"Why do you want this {role} role, and which strengths in {skills} would help you deliver "
        f"the responsibilities listed in this posting from the first month?"
    )


def build_hr_questions(job: dict) -> list[dict]:
    role = job.get("title") or "this role"
    return [
        {
            "category": "hr",
            "question": _hr_motivation_question(job),
            "why_asked": "HR screen — role-specific motivation, domain fit, and communication clarity.",
            "ideal_answer_points": [
                "Links motivation to specific responsibilities in the posting",
                "Highlights 2–3 relevant strengths with brief evidence",
                "Shows realistic understanding of day-to-day work",
            ],
            "question_type": "hr_motivation",
            "skill_tag": None,
        },
        {
            "category": "hr",
            "question": (
                f"What salary expectations and notice period do you have for a {role} role, "
                f"and what employment arrangement works best for you?"
            ),
            "why_asked": "HR screen — practical hiring logistics and expectation alignment.",
            "ideal_answer_points": [
                "States a researched salary range or flexibility",
                "Confirms notice period honestly",
                "Mentions work pattern preferences if relevant (remote, shifts, contract)",
            ],
            "question_type": "hr_logistics",
            "skill_tag": None,
        },
        {
            "category": "hr",
            "question": (
                f"How do you handle feedback, performance reviews, and professional development "
                f"in a {role} career?"
            ),
            "why_asked": "HR screen — growth mindset and workplace professionalism.",
            "ideal_answer_points": [
                "Concrete example of acting on feedback",
                "How you track development goals",
                "How you balance autonomy with manager guidance",
            ],
            "question_type": "hr_development",
            "skill_tag": None,
        },
    ]


def build_daily_routine_questions(job: dict) -> list[dict]:
    role = job.get("title") or "this role"
    resp = _responsibilities(job)
    primary = resp[0] if resp else "core duties"
    return [
        {
            "category": "daily_routine",
            "question": (
                f"Walk me through a typical working day as a {role}, from start-of-shift "
                f"briefing through handover or close-down."
            ),
            "why_asked": "Tests practical understanding of daily workflow and prioritisation.",
            "ideal_answer_points": [
                "Opening checks and planning",
                "Core task sequence with realistic timing",
                "Communication, documentation, and handover",
            ],
            "question_type": "daily_routine",
            "skill_tag": role,
        },
        {
            "category": "daily_routine",
            "question": (
                f"On your first day as a {role}, how would you prioritise tasks related to "
                f"{primary.lower()} while learning team processes?"
            ),
            "why_asked": "Day-one readiness and structured onboarding approach.",
            "ideal_answer_points": [
                "Observe before acting on safety-critical work",
                "Clarify priorities with supervisor",
                "Document learning and early wins",
            ],
            "question_type": "day_one",
            "skill_tag": role,
        },
    ]


def build_seniority_questions(job: dict, difficulty: str) -> list[dict]:
    role = job.get("title") or "this role"
    tier, label = _seniority_label(job, difficulty)
    if tier == "junior":
        return [
            {
                "category": "role_specific",
                "question": (
                    f"As a junior {role}, how would you handle a task you have not done before "
                    f"while still meeting quality and safety expectations?"
                ),
                "why_asked": "Junior-tier probe — learning speed, escalation, and quality discipline.",
                "ideal_answer_points": ["Ask for guidance early", "Follow standard procedure", "Verify before sign-off"],
                "question_type": "seniority",
                "skill_tag": None,
            },
        ]
    if tier == "senior":
        return [
            {
                "category": "role_specific",
                "question": (
                    f"As a senior {role}, describe how you would mentor juniors, review their work, "
                    f"and still deliver on your own technical responsibilities."
                ),
                "why_asked": "Senior-tier probe — leadership, delegation, and technical ownership.",
                "ideal_answer_points": ["Structured review criteria", "Coaching without micromanaging", "Own delivery"],
                "question_type": "seniority",
                "skill_tag": None,
            },
        ]
    return [
        {
            "category": "role_specific",
            "question": (
                f"At mid-level as a {role}, how do you balance independent delivery with "
                f"supporting colleagues and escalating risks appropriately?"
            ),
            "why_asked": "Mid-tier probe — autonomy, collaboration, and judgement.",
            "ideal_answer_points": ["Clear ownership boundaries", "When to escalate", "Evidence-based decisions"],
            "question_type": "seniority",
            "skill_tag": None,
        },
    ]


def build_case_study_questions(job: dict, skills: list[str]) -> list[dict]:
    role = job.get("title") or "this role"
    skill = skills[0] if skills else role
    simple = _is_simple_role(role)
    if simple:
        return [
            {
                "category": "technical",
                "question": (
                    f"During a busy rush as a {role}, drink quality drops and customer complaints rise. "
                    f"Walk me through how you diagnose and fix the issue using {skill} practices."
                ),
                "why_asked": "Practical case — operational problem-solving under pressure.",
                "ideal_answer_points": ["Immediate containment", "Root cause checks", "Prevention steps"],
                "question_type": "case_study",
                "skill_tag": skill,
            },
        ]
    return [
        {
            "category": "technical",
            "question": (
                f"Case study: You join as {role} and inherit a backlog affecting "
                f"{skill.lower() if skills else 'core delivery'}. Stakeholders want fast fixes; "
                f"compliance requires thorough verification. How do you plan the first two weeks?"
            ),
            "why_asked": "Case-study probe — prioritisation, stakeholder management, and technical judgement.",
            "ideal_answer_points": ["Triage criteria", "Quick wins vs structural fixes", "Communication plan"],
            "question_type": "case_study",
            "skill_tag": skill,
        },
        {
            "category": "technical",
            "question": (
                f"Practical task: Outline the steps you would take to complete a representative "
                f"{skill} assignment in this {role} role, including checks before sign-off."
            ),
            "why_asked": "Practical-task probe — hands-on method and verification discipline.",
            "ideal_answer_points": ["Preparation", "Execution sequence", "Verification and documentation"],
            "question_type": "practical_task",
            "skill_tag": skill,
        },
    ]


def build_scenario_questions(job: dict, skills: list[str]) -> list[dict]:
    role = job.get("title") or "this role"
    skill = skills[0] if skills else "core work"
    return [
        {
            "category": "technical",
            "question": (
                f"Scenario: A critical issue appears during {skill.lower()} work in your {role} shift. "
                f"Deadlines are tight and a senior is unavailable. What do you do?"
            ),
            "why_asked": "Scenario/problem-solving under ambiguity and time pressure.",
            "ideal_answer_points": ["Assess risk first", "Contain and communicate", "Document and escalate"],
            "question_type": "scenario",
            "skill_tag": skill,
        },
        {
            "category": "technical",
            "question": (
                f"Describe how you would solve a recurring quality problem affecting "
                f"{skill.lower()} outputs in {role} work, including metrics you would track."
            ),
            "why_asked": "Problem-solving with measurement and continuous improvement.",
            "ideal_answer_points": ["Define the defect", "Root cause", "Corrective action with metrics"],
            "question_type": "problem_solving",
            "skill_tag": skill,
        },
    ]


def build_tool_questions(job: dict, tools: list[str]) -> list[dict]:
    role = job.get("title") or "this role"
    out: list[dict] = []
    for tool in tools[:2]:
        out.append(
            {
                "category": "technical",
                "question": (
                    f"Which {tool} features or workflows do you use most as a {role}, "
                    f"and how do you verify outputs before sharing with stakeholders?"
                ),
                "why_asked": "Tool/software depth — practical proficiency, not buzzwords.",
                "ideal_answer_points": [
                    f"Named {tool} capabilities used in real work",
                    "Verification or testing approach",
                    "Common pitfalls avoided",
                ],
                "question_type": "tools",
                "skill_tag": tool,
            }
        )
    return out


def build_standards_questions(job: dict, skills: list[str]) -> list[dict]:
    role = job.get("title") or "this role"
    skill = skills[0] if skills else role
    family_blob = _norm(" ".join(_responsibilities(job) + skills))
    focus = "safety and compliance"
    if any(k in family_blob for k in ("pharmac", "clinical", "patient", "medication")):
        focus = "clinical governance and patient safety"
    elif any(k in family_blob for k in ("electrical", "commissioning", "cable")):
        focus = "electrical safety and applicable standards (e.g. BS 7671)"
    elif any(k in family_blob for k in ("haccp", "allergen", "hygiene", "food")):
        focus = "food hygiene, allergen control, and HACCP"
    elif any(k in family_blob for k in ("security", "incident", "aws", "kubernetes")):
        focus = "security controls and incident response standards"
    return [
        {
            "category": "technical",
            "question": (
                f"How do you apply {focus} standards in day-to-day {role} work involving "
                f"{skill.lower()}?"
            ),
            "why_asked": "Standards/safety/governance — non-negotiable professional requirements.",
            "ideal_answer_points": ["Named standard or policy", "When to stop work", "Documentation and escalation"],
            "question_type": "standards",
            "skill_tag": skill,
        },
    ]


def build_responsibility_questions(job: dict, existing: list[dict]) -> list[dict]:
    out: list[dict] = []
    for resp in _responsibilities(job):
        if _responsibility_covered(resp, existing + out):
            continue
        out.append(
            {
                "category": "role_specific",
                "question": (
                    f"This role involves '{resp}'. How have you delivered this responsibility "
                    f"in past work, and what would you do differently next time?"
                ),
                "why_asked": "Responsibility-specific evidence — ties posting duties to candidate experience.",
                "ideal_answer_points": ["Specific past example", "Personal actions", "Measurable outcome"],
                "question_type": "responsibility",
                "skill_tag": None,
            }
        )
    return out


def build_skill_gap_questions(job: dict, skills: list[str], existing: list[dict]) -> list[dict]:
    role = job.get("title") or "this role"
    out: list[dict] = []
    for skill in skills:
        if _skill_covered(skill, existing + out):
            continue
        out.append(
            {
                "category": "technical",
                "question": (
                    f"Explain how you apply {skill} in {role} work, including one method you trust "
                    f"and one mistake you actively avoid."
                ),
                "why_asked": f"Skill-specific depth for {skill}.",
                "ideal_answer_points": ["Clear method", "Realistic example", "Verification step"],
                "question_type": "explain",
                "skill_tag": skill,
            }
        )
    return out


def detect_coverage_archetype(job: dict) -> str | None:
    """Classify roles that need creative/media, creator/trending, or sports coverage packs."""
    title = _norm(job.get("title") or "")
    blob = f"{title} {_norm(' '.join(_skills_from_job(job)))}"
    if any(h in blob for h in _CREATOR_TRENDING_HINTS):
        return "creator_trending"
    if any(h in blob for h in _CREATIVE_MEDIA_HINTS):
        return "creative_media"
    if any(h in blob for h in _SPORTS_HINTS):
        return "sports"
    return None


def is_archetype_legacy_question_type(question_type: str | None) -> bool:
    return (question_type or "") in _ARCHETYPE_LEGACY_TYPES


def _archetype_question(
    *,
    role: str,
    category: str,
    question_type: str,
    question: str,
    why: str,
    skill_tag: str | None = None,
) -> dict:
    return {
        "category": category,
        "question": question,
        "why_asked": why,
        "ideal_answer_points": ["Concrete method", "Role-specific example", "Quality or ethics check"],
        "question_type": question_type,
        "skill_tag": skill_tag,
        "skip_skill_card": True,
    }


def build_creative_media_questions(job: dict) -> list[dict]:
    role = job.get("title") or "this role"
    skills = ", ".join(_skills_from_job(job)[:3]) or "core editorial skills"
    return [
        _archetype_question(
            role=role,
            category="behavioral",
            question_type="ethics",
            question=(
                f"Describe a time as a {role} when source verification or editorial ethics "
                f"changed what you could publish."
            ),
            why="Ethics and accuracy under deadline pressure.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="story_planning",
            question=(
                f"How do you plan a {role} story from initial tip to publish-ready copy, "
                f"including research, interviews, and fact-checking?"
            ),
            why="Research and story-planning workflow.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="audience_research",
            question=(
                f"How do you decide which stories matter to your audience as a {role}, "
                f"and how do you measure engagement after publication?"
            ),
            why="Audience understanding and post-publish review.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="production_workflow",
            question=(
                f"Walk me through your production workflow as a {role} — drafting, editing, "
                f"legal/sub-editing checks, and CMS publishing."
            ),
            why="Production workflow and deadline management.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="platform_tools",
            question=f"Which tools or platforms do you rely on most as a {role} ({skills}), and how do you verify outputs?",
            why="Tools/platforms depth without buzzwords.",
            skill_tag=_skills_from_job(job)[0] if _skills_from_job(job) else None,
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="editor_feedback",
            question=(
                f"Tell me about a difficult editor or stakeholder feedback round in {role} work "
                f"and how you incorporated it without losing accuracy."
            ),
            why="Stakeholder/editor feedback handling.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="portfolio",
            question=f"What would you include in a {role} portfolio to show range, accuracy, and deadline discipline?",
            why="Portfolio and evidence of craft.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="quality_review",
            question=(
                f"How do you run a final quality review on {role} work before publication, "
                f"including headline, quotes, and image rights?"
            ),
            why="Quality review and sign-off discipline.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="practical_task",
            question=(
                f"Practical task: You receive a late-breaking lead as a {role}. Outline your first hour "
                f"including verification, outreach, and deadline planning."
            ),
            why="Practical task under time pressure.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="case_study",
            question=(
                f"Case study: A controversial story risks defamation complaints. How would you handle "
                f"verification, escalation, and publication decisions as a {role}?"
            ),
            why="Case-study judgement for media risk.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="copyright",
            question=f"How do you manage copyright, attribution, and image rights in {role} publishing?",
            why="Copyright and rights awareness.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="growth_seniority",
            question=(
                f"How has your {role} craft evolved from early assignments to more complex beats, "
                f"and what do you still deliberately practise?"
            ),
            why="Seniority and growth variation.",
        ),
    ]


def build_creator_trending_questions(job: dict) -> list[dict]:
    role = job.get("title") or "this role"
    return [
        _archetype_question(
            role=role,
            category="behavioral",
            question_type="content_niche",
            question=f"How did you choose your content niche as a {role}, and how do you keep it credible as you grow?",
            why="Niche and audience positioning.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="content_planning",
            question=f"Describe your content planning process as a {role} — ideas, calendar, scripting, and batching.",
            why="Content planning and scheduling discipline.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="filming_recording",
            question=f"Walk me through your filming/recording and editing workflow as a {role} from setup to export.",
            why="Production workflow.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="thumbnail_hooks",
            question=f"How do you develop thumbnails, titles, and hooks as a {role} without misleading the audience?",
            why="Hooks and packaging with integrity.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="publishing_schedule",
            question=f"How do you set and protect a publishing schedule as a {role} during busy or low-motivation periods?",
            why="Publishing cadence and consistency.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="analytics_kpi",
            question=f"Which analytics or KPIs do you track as a {role}, and how do you turn them into better content decisions?",
            why="Analytics and performance review.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="community_management",
            question=f"How do you manage community comments and DMs as a {role} during a viral spike?",
            why="Community management under pressure.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="brand_safety",
            question=f"What brand-safety checks do you run before accepting sponsorships or posting as a {role}?",
            why="Brand safety and reputation.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="monetization_awareness",
            question=f"How do you balance monetization and audience trust as a {role}?",
            why="Sponsorship/monetization awareness.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="copyright",
            question=f"How do you handle music, footage, and asset rights before publishing as a {role}?",
            why="Copyright clearance.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="crisis_reputation",
            question=f"Describe how you would respond to a reputation crisis or platform-policy warning as a {role}.",
            why="Crisis/reputation handling.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="platform_tools",
            question=f"Which platforms and creator tools do you use most as a {role}, and how do you quality-check each upload?",
            why="Platform/tool proficiency.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="practical_task",
            question=f"Practical task: Plan a seven-day content series as a {role} for a new audience segment.",
            why="Practical planning task.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="case_study",
            question=f"Case study: A sponsored video underperforms and attracts negative comments. What do you do as a {role}?",
            why="Case-study response under pressure.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="growth_seniority",
            question=f"How has your {role} approach changed as your audience grew, and what would you do differently at 10x scale?",
            why="Growth/seniority variation.",
        ),
    ]


def build_sports_questions(job: dict) -> list[dict]:
    role = job.get("title") or "this role"
    return [
        _archetype_question(
            role=role,
            category="behavioral",
            question_type="training_discipline",
            question=f"Describe your training discipline as a {role} during a congested fixture or competition period.",
            why="Training discipline without unsafe advice.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="match_preparation",
            question=f"How do you prepare for match or game day as a {role}, including review, communication, and routines?",
            why="Match/game preparation.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="teamwork_sports",
            question=f"Give an example of effective teamwork or on-field communication from your {role} experience.",
            why="Teamwork under competitive pressure.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="coaching_feedback",
            question=f"How do you receive and apply coaching feedback as a {role}?",
            why="Coaching feedback and improvement.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="recovery_awareness",
            question=f"How do you balance training load, sleep, and recovery as a {role} without ignoring medical guidance?",
            why="Recovery awareness — safe, non-medical framing.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="sportsmanship",
            question=f"Describe a moment where sportsmanship or ethics mattered in your {role} career.",
            why="Ethics/sportsmanship.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="practical_task",
            question=f"Practical task: Design a one-week preparation plan as a {role} before an important match or event.",
            why="Practical preparation task.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="case_study",
            question=f"Case study: You notice a performance slump mid-season as a {role}. How do you diagnose and respond?",
            why="Scenario/problem-solving.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="growth_seniority",
            question=f"How has your role as a {role} evolved from early career to more senior expectations?",
            why="Seniority/growth variation.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="workflow_process",
            question=f"What performance metrics or review habits do you use as a {role} to improve week to week?",
            why="Performance review habits.",
        ),
    ]


def build_field_agnostic_floor_questions(job: dict, *, round_index: int = 0) -> list[dict]:
    """Field-agnostic supplemental questions when packs still fall below the coverage floor."""
    role = job.get("title") or "this role"
    skills = _skills_from_job(job)
    skill = skills[round_index % len(skills)] if skills else role
    templates = [
        _archetype_question(
            role=role,
            category="behavioral",
            question_type="workflow_process",
            question=f"Describe how you organise daily priorities as a {role} when deadlines and quality both matter.",
            why="Daily workflow and prioritisation.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="stakeholder_communication",
            question=f"How do you communicate progress and risks to stakeholders or managers in {role} work?",
            why="Communication and stakeholder management.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="quality_review",
            question=f"What quality checks do you never skip in {role} work involving {skill}?",
            why="Quality control discipline.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="practical_task",
            question=f"Practical task: Outline how you would complete a representative {skill} assignment as a {role}.",
            why="Practical task depth.",
            skill_tag=skill,
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="case_study",
            question=f"Case study: A {role} deliverable fails review at the last minute. How do you respond?",
            why="Problem-solving under pressure.",
        ),
        _archetype_question(
            role=role,
            category="technical",
            question_type="growth_seniority",
            question=f"How would a senior {role} mentor someone struggling with {skill.lower()} fundamentals?",
            why="Growth and seniority perspective.",
        ),
    ]
    start = (round_index * 2) % len(templates)
    return templates[start : start + 3]


def build_archetype_coverage_questions(job: dict, archetype: str | None = None) -> list[dict]:
    archetype = archetype or detect_coverage_archetype(job)
    if archetype == "creative_media":
        return build_creative_media_questions(job)
    if archetype == "creator_trending":
        return build_creator_trending_questions(job)
    if archetype == "sports":
        return build_sports_questions(job)
    return []


def build_coverage_floor_questions(
    job: dict,
    *,
    archetype: str | None,
    round_index: int,
    existing: list[dict],
) -> list[dict]:
    """Additional non-duplicate questions for exportable coverage floor rounds."""
    pool: list[dict] = []
    if archetype:
        pool.extend(build_archetype_coverage_questions(job, archetype))
    pool.extend(build_field_agnostic_floor_questions(job, round_index=round_index))
    pool.extend(build_scenario_questions(job, _skills_from_job(job)))
    pool.extend(build_case_study_questions(job, _skills_from_job(job)))

    out: list[dict] = []
    seen = {_norm(q.get("question", ""))[:80] for q in existing}
    for q in pool:
        key = _norm(q.get("question", ""))[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(q)
    return out[:6]


def apply_coverage_plan(
    job: dict,
    questions: list[dict],
    *,
    difficulty: str = "auto",
) -> list[dict]:
    """
    Append supplemental questions until minimum coverage targets are met.
    Does not remove or rewrite existing questions.
    """
    skills = _skills_from_job(job)
    tools = _tool_skills(skills)
    simple = _is_simple_role(job.get("title") or "")
    supplemental: list[dict] = []

    if _count_category(questions, "hr") < 2:
        supplemental.extend(build_hr_questions(job)[: max(0, 2 - _count_category(questions, "hr"))])

    if _count_category(questions, "daily_routine") < 1:
        supplemental.extend(build_daily_routine_questions(job)[:1])

    if not _has_type_or_marker(questions, "seniority", ("junior", "senior", "mid-level", "lead")):
        supplemental.extend(build_seniority_questions(job, difficulty))

    scenario_count = sum(
        1 for q in questions
        if q.get("question_type") in {"scenario", "problem_solving", "complex_problem"}
        or "scenario" in _norm(q.get("question", ""))
    )
    if scenario_count < 2:
        supplemental.extend(build_scenario_questions(job, skills)[: max(0, 2 - scenario_count)])

    if not _has_type_or_marker(questions, "case_study", ("case study", "practical task")):
        supplemental.extend(build_case_study_questions(job, skills)[:1 if simple else 2])

    if tools and not _has_type_or_marker(questions, "tools", tuple(_TOOL_KEYWORDS)):
        supplemental.extend(build_tool_questions(job, tools)[:1])

    if _needs_safety_question(job, skills) and not _has_type_or_marker(
        questions, "standards", ("standard", "safety", "compliance", "governance", "haccp")
    ):
        supplemental.extend(build_standards_questions(job, skills))

    supplemental.extend(build_responsibility_questions(job, questions + supplemental))
    supplemental.extend(build_skill_gap_questions(job, skills, questions + supplemental))

    archetype = detect_coverage_archetype(job)
    if archetype:
        supplemental.extend(build_archetype_coverage_questions(job, archetype))

    return questions + supplemental
