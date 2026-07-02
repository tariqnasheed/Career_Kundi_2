"""
Substantive expert knowledge and direct interview answers per skill and role.

No interview-coaching meta-text — only real subject matter and the actual words
an expert would speak in the interview room.
"""

from __future__ import annotations

from app.agents.job_search.knowledge.normalize import normalize_key, title_case_skill

# ---------------------------------------------------------------------------
# Skill-level expert content (defaults)
# key = normalize_key(skill name)
# ---------------------------------------------------------------------------

_SKILL: dict[str, dict] = {}

def _s(
    definition: str,
    how_it_works: list[str],
    key_facts: list[str],
    teaching: str,
    explain: str,
    complex: str,
    *,
    standards: list[str] | None = None,
    pitfalls: list[str] | None = None,
    related: list[str] | None = None,
) -> dict:
    return {
        "definition": definition,
        "how_it_works": how_it_works,
        "key_facts": key_facts,
        "standards": standards or [],
        "teaching_body": teaching,
        "explain_answer": explain,
        "complex_answer": complex,
        "technical_pitfalls": pitfalls or [],
        "related_topics": related or [],
    }


# --- Electrical / construction trades ---------------------------------------

_SKILL["electrical_installation"] = _s(
    definition=(
        "Electrical installation is the physical work of designing, routing, connecting, and commissioning "
        "fixed wiring systems so they safely deliver electricity from the supply intake to points of use. "
        "It covers cable selection, containment, protective devices, earthing, bonding, circuit design "
        "(radial and ring final), and certification under applicable wiring regulations."
    ),
    how_it_works=[
        "Confirm scope against drawings and BS 7671 (IET Wiring Regulations); verify supply characteristics (TN-S, TN-C-S, TT).",
        "Install main earthing terminal, equipotential bonding to gas/water/oil where required, and circuit protective conductors.",
        "Route cables in appropriate zones, use correct cable types (e.g. 6242Y twin-and-earth for domestic ring/radial), and maintain derating for insulation/grouping.",
        "Terminate at accessories and consumer unit with correct polarity; label circuits clearly on the schedule.",
        "Commission: continuity of CPCs, insulation resistance (>1 MΩ at 500 V), polarity, earth fault loop impedance (Zs), and RCD operation where fitted.",
        "Issue Electrical Installation Certificate (EIC) or Minor Works Certificate with schedule of test results and handover documentation.",
    ],
    key_facts=[
        "BS 7671 18th Edition + Amendment 2 is the UK benchmark for design and verification.",
        "Maximum Zs values depend on protective device type and rating — must be verified on site.",
        "Ring final circuits: line, neutral, and CPC continuity; each leg typically ~1.67× ring length resistance.",
        "Part P (Building Regulations) may require notification for notifiable work in dwellings.",
        "Safe isolation: lock-off, prove dead with GS38-compliant voltage indicator on all conductors.",
    ],
    standards=["BS 7671 (IET Wiring Regulations)", "GS38 (test equipment)", "Part P Building Regulations", "Electricity at Work Regulations 1989"],
    teaching=(
        "Electrical installation is not simply 'running cables' — it is applying Ohm's law, adiabatic equation "
        "constraints, and disconnection times so that fault current is cleared before touch voltage becomes lethal. "
        "Every circuit has a design current (Ib), protective device rating (In), and maximum permitted Zs. "
        "Cable size follows from current-carrying capacity (Iz), voltage drop limits (typically 3% lighting, 5% other), "
        "and fault-withstand. Domestic work commonly uses 32 A ring finals on 2.5 mm² T&E for socket outlets and "
        "6 A lighting on 1.5 mm²; the consumer unit groups circuits under RCBOs or RCD-protected ways."
    ),
    explain=(
        "Electrical installation means building the fixed wiring that takes power from the meter or distribution board "
        "to sockets, lights, cookers, and equipment — safely and to code. You start with the supply type and earthing "
        "arrangement, then install bonding so all exposed metal stays at the same potential. Cables go in the correct "
        "zones with the right size for the load and the length — voltage drop matters on long runs. At the board you "
        "fit MCBs or RCBOs matched to the cable and load. Before energising you prove dead, then test continuity, "
        "insulation resistance, polarity, and earth loop impedance so fault disconnection happens within the required "
        "time — typically 0.4 s for final circuits. You finish with a certificate and test sheet so the building owner "
        "and inspector know the installation is compliant."
    ),
    complex=(
        "On a six-flat conversion from a single dwelling, the complex part was splitting one existing supply into "
        "sub-meters while keeping selectivity and RCD coordination. The original TN-C-S board had a 100 A main switch "
        "and mixed legacy circuits. I surveyed load per flat, designed six consumer units with 40 A main switches, "
        "type A 30 mA RCBOs on every circuit, and separate bonding per flat. During first fix we hit unexpected "
        "asbestos in the riser — work stopped, notified the client, and rerouted containment via an alternate route "
        "adding 12 m of trunking. On testing, flat 3's ring final showed high end-to-end resistance indicating a "
        "loose connection at a socket — we replaced the faulty accessory and re-tested. Final Zs on all circuits "
        "was below tabulated maxima; RCDs tripped at 18–24 ms on x1 test. Building Control signed off Part P and we "
        "issued six EICs plus the communal areas minor works certificate."
    ),
    pitfalls=[
        "Connecting CPC incorrectly on a ring — creates dangerous parallel paths and false continuity readings.",
        "Ignoring tabulated Zs after installing RCBOs with 30 mA — still must meet disconnection for line-earth faults.",
        "Working live without justification — illegal and unsafe; always isolate and prove dead.",
    ],
    related=["Earthing and bonding", "Cable sizing", "RCD types A vs AC", "Inspection and testing", "Part P notification"],
)

_SKILL["testing"] = _s(  # electrical testing default for trades; overridden for software roles
    definition=(
        "Electrical testing and verification is the process of measuring an installation's safety and compliance "
        "after work is complete (or periodically during maintenance). It confirms conductors are correctly connected, "
        "insulation is intact, earth paths are effective, and protective devices will operate within required times."
    ),
    how_it_works=[
        "Visual inspection: correct devices, labelling, IP ratings, zones, and absence of damage before energising.",
        "Continuity of protective conductors (R1+R2 or r1+r2 method) — typically ≤1 Ω at the far end of final circuits.",
        "Continuity of ring final conductors: line, neutral, and CPC end-to-end readings within tolerance.",
        "Insulation resistance: 500 V DC between live conductors and earth; minimum 1 MΩ (often >>1 MΩ on new work).",
        "Polarity: switches in line conductor only; ES lampholders wired correctly; no reverse polarity at sockets.",
        "Earth fault loop impedance (Zs): measured at furthest point; compare to BS 7671 max Zs for the OCPD.",
        "RCD testing: no trip at ½×IΔn; trip at IΔn within 300 ms; at 5×IΔn within 40 ms (type-dependent).",
        "Record all results on schedule; issue certificate; explain any limitations or remedial work required.",
    ],
    key_facts=[
        "Test sequence matters — prove dead before continuity on dead tests; IR test with appliances disconnected.",
        "GS38 voltage indicators must be proved on a proving unit before and after use.",
        "Zs = Ze + (R1+R2); high Zs may require circuit redesign or different OCPD.",
        "PFC/PSCC measurement informs adequacy of breaking capacity at origin.",
    ],
    standards=["BS 7671 Part 6", "GS38", "IET Guidance Note 3 (Inspection & Testing)"],
    teaching=(
        "Verification separates a working installation from a safe one. Insulation breakdown, swapped neutrals, or "
        "high-Zs earth paths may not show until a fault occurs — testing finds them first. The electrician uses "
        "a multifunction tester (MFT) for most dead tests and live tests at the furthest point of each circuit. "
        "Results are compared against tabulated limits in BS 7671 — not guessed."
    ),
    explain=(
        "Testing an electrical installation means running a defined sequence of checks after installation or alteration. "
        "First I inspect visually — correct ratings, earthing present, no damage. Dead tests: continuity on CPCs and "
        "ring conductors, then insulation resistance at 500 V. After careful re-energisation I check polarity, then "
        "live tests — earth fault loop impedance at the end of each circuit and RCD trip times. Every reading goes "
        "on the schedule next to the maximum permitted value. If Zs is too high, the circuit doesn't get signed off "
        "until we fix the cause — often a loose connection, wrong cable size, or need for an RCBO. The certificate "
        "is the legal record that the installation was verified to BS 7671."
    ),
    complex=(
        "A commercial kitchen kept tripping a 30 mA RCD overnight with no appliances running. Initial suspicion was "
        "nuisance tripping from combined leakage. I split the circuit: insulation test showed 0.8 MΩ between neutral "
        "and earth on the combi oven circuit — below 1 MΩ minimum. Traced to heater element moisture ingress in the "
        "oven — not the wiring. Isolated the appliance, re-tested installation at >200 MΩ, fitted a dedicated RCBO "
        "for kitchen sockets separate from fixed equipment, and documented appliance repair before recommissioning. "
        "RCD x1 trip was 22 ms; Zs 0.85 Ω on a B32 MCB — well within limits. Documented root cause so the client "
        "knew wiring was sound but equipment needed service."
    ),
    pitfalls=[
        "Skipping dead tests and going straight to live Zs — misses open CPC faults.",
        "Not removing electronic equipment during IR tests — false low readings or damage to equipment.",
        "Recording Zs at the board only — must be at the furthest point of the circuit.",
    ],
    related=["Multifunction testers", "Ze and Zs", "RCD selectivity", "Periodic inspection (EICR)"],
)

_SKILL["wiring_regulations"] = _s(
    definition=(
        "Wiring regulations — in the UK, BS 7671 (IET Wiring Regulations) — are the national standard for "
        "electrical design, erection, and verification of low-voltage installations. They translate statutory "
        "duties under the Electricity at Work Regulations into practical requirements for safety, disconnection, "
        "protection, and special locations."
    ),
    how_it_works=[
        "Apply the scope and fundamental principles (Chapter 13): protection against shock, thermal effects, overcurrent, fault current.",
        "Select appropriate devices: BS EN 60898 MCBs, BS EN 61009 RCBOs, correct curves (B, C, D) for load inrush.",
        "Design circuits meeting maximum disconnection times: 0.4 s final circuits, 5 s distribution, per Tables 41.1.",
        "Apply special location rules: bathrooms (Section 701), outdoor (714), agricultural — zones dictate IP and RCD.",
        "Document design assumptions; verify on site; issue certificates per Part 6.",
    ],
    key_facts=[
        "Regulations are non-statutory but compliance is the accepted way to meet legal duties.",
        "Amendment 2 introduced AFDD recommendations in some sleeping accommodation and updated RCD guidance.",
        "Prosumer's low-voltage electrical installations (PEI) covered for solar/storage integration.",
        "Cable references: 433.1 overload, 434 fault protection, 525 voltage drop.",
    ],
    standards=["BS 7671:2018+A2:2022", "Electricity at Work Regulations 1989", "Building Regulations Part P"],
    teaching=(
        "BS 7671 is structured in seven parts: scope, definitions, general characteristics, protection, selection and "
        "erection, inspection/testing, and special locations. The electrician doesn't memorise every table — but must "
        "know how to look up Iz, grouping factors, Zs maxima, and IP ratings. Compliance is demonstrated by design "
        "calculations plus test results, not assertions."
    ),
    explain=(
        "Wiring regulations — BS 7671 in the UK — tell us how to design and install electrical systems so people "
        "are protected from electric shock and fire. They define maximum disconnection times, when RCDs are required, "
        "how to size cables and protective devices, and special rules for bathrooms, gardens, and marinas. They're "
        "updated by the JPEL/64 committee; the current edition is 18th with Amendment 2. On site I work to the "
        "certified design or produce my own calculations for Ib, In, Iz, voltage drop, and Zs. Building Control and "
        "insurance surveys expect certificates that show we've met Part 6 verification — that's how regulations become "
        "auditable in practice."
    ),
    complex=(
        "A client wanted EV chargers on a TT supply with already-high Ze. Amendment 2 requires RCD protection and "
        "considers earth electrodes. I calculated that adding two 7.4 kW chargers would exceed existing demand; "
        "designed a sub-board with load management, type A RCDs for DC leakage, and separate earth electrode "
        "resistance test showing Ra < required value for the combined installation. Building Control queried Part P "
        "notification — we submitted via registered body with design PDF referencing BS 7671 Section 722 for EV "
        "and 542 for earthing. Post-install Zs on charger circuits was 0.62 Ω on C40 RCBOs; passed first inspection."
    ),
    pitfalls=["Applying outdated 17th Edition tables", "Ignoring special locations", "Mixing TN and TT earthing without design"],
    related=["Part P", "IET On-Site Guide", "Design current Ib", "Protective conductor sizing"],
)

_SKILL["fault_finding"] = _s(
    definition=(
        "Electrical fault finding is systematic diagnosis of failures in circuits or equipment — from intermittent "
        "tripping to dead circuits — using safe isolation, circuit knowledge, and measurement to locate root cause "
        "rather than replacing parts at random."
    ),
    how_it_works=[
        "Gather symptoms: what tripped, when, load connected, recent work, weather (RCD leakage).",
        "Safe isolation; prove dead; obtain single-line diagram or trace practically.",
        "Divide the circuit: test at board vs at midpoint — narrow fault location (half-split method).",
        "Measure: continuity for open circuits, IR for insulation faults, Zs for high loop impedance trips.",
        "For intermittent faults: monitor, wiggle test connections, thermal imaging under load where safe.",
        "Repair, re-test full sequence, document cause and remedy on job sheet.",
    ],
    key_facts=[
        "Nuisance RCD tripping often = cumulative appliance leakage approaching 30 mA.",
        "Intermittent MCB trips under load → loose termination or high resistance joint heating.",
        "Neutral-earth faults can cause RCD trips without obvious short circuit.",
    ],
    standards=["BS 7671", "Electricity at Work Regulations", "Safe isolation procedure"],
    teaching=(
        "Fault finding rewards method over guesswork. The half-split approach on a dead ring localises an open in "
        "log₂(n) steps. On live RCD issues, disconnect half the loads — if trip stops, fault is on disconnected side. "
        "Always distinguish installation faults from appliance faults before rewiring."
    ),
    explain=(
        "Fault finding means working logically from the symptom to the root cause. If an RCD trips, I ask whether it's "
        "immediate or under load, and if anything new was connected. I isolate safely, then divide — disconnect half "
        "the circuit loads and see if the problem persists. For a dead socket circuit I measure at the board: is there "
        "voltage? continuity on line and neutral? Often it's a tripped unnoticed RCBO or a loose connection at the "
        "last working accessory before the dead one. I fix it, then run the relevant tests again — not just flip the "
        "breaker and leave. Documentation protects you if the fault returns."
    ),
    complex=(
        "A shop had weekly Friday-night RCD trips closing tills. Pattern suggested heating timer plus Friday cleaning "
        "equipment. Logged trip times, correlated with 24-hour time switch energising trace heating on a roof de-icing "
        "cable with water ingress in a joint box. IR test on that branch: 0.3 MΩ. Replaced 4 m of damaged T&E in conduit, "
        "new IP66 junction, separated de-icing onto its own RCBO. No trips in eight weeks follow-up; saved the client "
        "from a full rewire quote another contractor had proposed."
    ),
    pitfalls=["Replacing RCD repeatedly without finding leakage source", "Working live to 'save time'", "Missing broken neutral on split-load board"],
    related=["RCD nuisance tripping", "Thermal imaging", "Circuit tracing", "Insulation breakdown"],
)

# --- Software / technology ---------------------------------------------------

_SKILL["python"] = _s(
    definition=(
        "Python is a high-level, interpreted language with dynamic typing and automatic memory management. "
        "It emphasises readable syntax, rich standard library, and an ecosystem for web (FastAPI, Django), "
        "data (pandas, NumPy), ML (PyTorch, scikit-learn), and automation."
    ),
    how_it_works=[
        "Source (.py) compiles to bytecode (.pyc) executed by the CPython VM (stack-based interpreter).",
        "Objects are reference-counted with cyclic garbage collector for containers.",
        "Functions are first-class; decorators wrap callables; context managers use __enter__/__exit__.",
        "GIL serialises bytecode execution in threads — use multiprocessing or async I/O for parallelism.",
        "Package management via pip/uv; virtual environments isolate dependencies per project.",
    ],
    key_facts=[
        "list comprehensions and generators reduce memory vs eager lists.",
        "async/await for I/O-bound concurrency; threads blocked by GIL for CPU-bound work.",
        "Type hints (PEP 484) optional but improve tooling with mypy/pyright.",
        "Exceptions should be specific; EAFP (try/except) idiomatic over LBYL.",
    ],
    standards=["PEP 8 style", "PEP 20 Zen", "Semantic versioning for packages"],
    teaching=(
        "Python's data model is 'everything is an object' with dunder methods defining behaviour. "
        "Understanding mutability (list vs tuple), shallow copy, and iterator protocol explains most bugs. "
        "For production services, structure code in layers: routes → services → repositories, with explicit "
        "error types and logging context (structlog)."
    ),
    explain=(
        "Python is a language designed for clarity — indentation defines blocks, and the syntax reads almost like "
        "pseudocode. Code runs through an interpreter, so you iterate quickly without compile cycles. It has lists, "
        "dicts, sets, and generators built in, plus a massive library ecosystem. For a web API I'd use FastAPI or "
        "Django; for data work pandas and NumPy. Concurrency: asyncio for many network connections, multiprocessing "
        "for CPU-heavy work because of the GIL. I reach for Python when delivery speed, readability, and library "
        "availability matter — and when performance-critical inner loops can be pushed to C extensions or Rust."
    ),
    complex=(
        "We had a batch ETL job processing 40 GB nightly JSON that started exceeding its four-hour window. "
        "Profiling showed 70% time in json.loads and dict lookups. I refactored to ijson streaming parser, "
        "converted hot paths to PyArrow tables, and parallelised file shards with ProcessPoolExecutor — four "
        "workers on a 16-core box. Added idempotent writes with UPSERT on a staging table so retries were safe. "
        "Runtime dropped to 52 minutes; memory peak from 28 GB to 6 GB. Added Datadog timing on each stage so "
        "regression would alert if a vendor file format changed."
    ),
    pitfalls=["Mutable default arguments", "Not closing files/sessions", "CPU-bound code in threads expecting speedup"],
    related=["Virtual environments", "asyncio", "pandas", "Type hints"],
)

_SKILL["sql"] = _s(
    definition=(
        "SQL is the declarative language for defining, querying, and mutating relational data. "
        "Tables enforce schemas; ACID transactions coordinate concurrent writers; the optimiser "
        "chooses plans using indexes and statistics."
    ),
    how_it_works=[
        "DDL: CREATE TABLE with constraints (PRIMARY KEY, FOREIGN KEY, CHECK, UNIQUE).",
        "DML: INSERT, UPDATE, DELETE with WHERE predicates; JOIN combines rows across tables.",
        "Transactions: BEGIN … COMMIT/ROLLBACK; isolation levels trade consistency vs concurrency.",
        "Indexes (B-tree default): speed lookups but cost writes; EXPLAIN ANALYZE shows plan.",
        "Window functions (OVER PARTITION BY): rankings, running totals without self-joins.",
    ],
    key_facts=[
        "N+1 query problem: ORM loops causing thousands of round trips — fix with JOIN or prefetch.",
        "NULL semantics: NULL = NULL is unknown, use IS NULL.",
        "Covering indexes include all columns needed by query — index-only scan.",
    ],
    standards=["ANSI SQL", "PostgreSQL/MySQL dialect docs", "Normal forms (1NF–3NF)"],
    teaching=(
        "Relational algebra underpins SQL: selection (WHERE), projection (SELECT), join, grouping. "
        "Query performance comes from selective indexes, accurate statistics, and avoiding functions "
        "on indexed columns in predicates. Migrations must be backward-compatible in zero-downtime deploys."
    ),
    explain=(
        "SQL lets you work with structured data in tables using a declarative syntax — you describe what you want, "
        "not how to loop. SELECT with JOINs combines related entities; GROUP BY aggregates; window functions "
        "rank and compare rows without collapsing them. Transactions group changes atomically — either all commit "
        "or none. Indexes make lookups fast but must match query patterns. In production I always EXPLAIN critical "
        "queries, parameterise inputs against injection, and use migrations for schema changes."
    ),
    complex=(
        "Dashboard queries on a 120 M-row events table timed out at 90 s. EXPLAIN showed sequential scan — "
        "the filter was on created_at range but the composite index led with tenant_id from an ORM default. "
        "I added (tenant_id, created_at DESC) INCLUDE (metric_value), rewrote the query to force partition "
        "pruning on monthly tables, and materialised a nightly rollup for aggregates older than 30 days. "
        "P95 dropped to 180 ms; storage cost +4% for the index."
    ),
    pitfalls=["SELECT * in production", "Implicit conversions killing indexes", "Long transactions blocking vacuum"],
    related=["EXPLAIN ANALYZE", "Isolation levels", "ORM N+1", "Window functions"],
)

# --- Chemical/process safety --------------------------------------------------

_SKILL["hazmat_safety"] = _s(
    definition=(
        "Hazmat safety in chemical engineering is the discipline of identifying, classifying, storing, "
        "handling, transferring, and disposing hazardous chemicals so acute and chronic harm is prevented "
        "to people, assets, and environment. It integrates process safety, occupational hygiene, and "
        "regulatory compliance (GHS/CLP, REACH, COSHH or OSHA equivalents)."
    ),
    how_it_works=[
        "Identify chemical inventory and classify hazards (flammable, toxic, corrosive, oxidizer, reactive) from SDS Section 2.",
        "Perform task-based risk assessment (exposure route, quantity, temperature/pressure, incompatibilities).",
        "Apply hierarchy of controls: elimination/substitution, enclosed transfer, local exhaust ventilation, then PPE.",
        "Implement storage segregation (acid/base, oxidizer/organic, cyanide/acid), secondary containment, and spill controls.",
        "Set operating limits and safeguards in SOPs: charging sequence, inerting, grounding/bonding, emergency shutdown criteria.",
        "Train personnel, run drills, and document incidents/near misses for corrective actions and MOC updates.",
    ],
    key_facts=[
        "SDS is operational data, not paperwork — incompatibility and first-aid sections drive controls.",
        "Many incidents come from mixing incompatible residues during cleaning/changeover, not core reaction steps.",
        "Grounding/bonding is mandatory when transferring flammable solvents to prevent static ignition.",
        "HAZOP + LOPA are standard methods to verify safeguards are adequate for credible deviations.",
        "Emergency response plans must specify spill class, isolation zone, and evacuation thresholds.",
    ],
    standards=["GHS/CLP classification", "REACH", "COSHH (UK) / OSHA HazCom", "HAZOP / LOPA process safety methods"],
    teaching=(
        "Hazmat safety is where chemical knowledge becomes operational discipline. The same solvent that is safe in a "
        "500 mL bottle can become an explosion risk in a 5,000 L transfer if ventilation, static control, and vapor "
        "management are not engineered correctly. Strong chemical engineers think in scenarios: loss of cooling, wrong "
        "line-up, overfill, incompatible clean-down residues, and delayed detection."
    ),
    explain=(
        "Hazmat safety means I treat every chemical operation as a controlled system, not a routine task. I start from SDS "
        "and process conditions, map incompatibilities, and define controls before anyone handles material. For solvent transfer "
        "I verify grounding, closed transfer where possible, ventilation, and ignition source control. I segregate storage by "
        "chemical compatibility, set spill containment, and ensure operators know immediate actions for exposure or release. "
        "At plant level I use HAZOP findings and incident learning to update SOPs and management-of-change records. That is how "
        "you prevent low-frequency, high-impact events while keeping production reliable."
    ),
    complex=(
        "At a specialty chemicals unit we had recurring near-miss vapor alarms during drum-to-reactor solvent charging. "
        "Investigation showed intermittent bonding clamp failure plus an operator shortcut opening vents early. I led a focused "
        "PHA: replaced manual charging with closed transfer using dry-break couplings, installed interlocked grounding verification, "
        "added LEL detector permissive on the charging step, and rewrote the SOP with a mandatory pre-charge checklist. We also "
        "segregated oxidizer drums to a separate bay with dedicated spill bund. In the next 12 months there were zero vapor alarms "
        "during charging and insurer audit findings closed without conditions."
    ),
    pitfalls=[
        "Treating SDS as documentation-only and not translating hazards into task controls.",
        "Ignoring chemical incompatibility during temporary storage or waste drum consolidation.",
        "Using PPE as the primary control when engineering controls are feasible.",
    ],
    related=["SDS interpretation", "HAZOP", "LOPA", "Incompatibility matrices", "Spill response planning"],
)

# --- Role-specific overrides (same skill, different field meaning) ------------

_ROLE_SKILL_OVERRIDES: dict[str, dict[str, dict]] = {
    "software_engineer": {
        "testing": _s(
            definition=(
                "Software testing verifies that code meets requirements and does not regress. "
                "Levels include unit (isolated functions), integration (modules together), "
                "contract (API boundaries), and end-to-end (user journeys)."
            ),
            how_it_works=[
                "Write failing test describing expected behaviour (TDD optional but valuable).",
                "Unit-test pure logic with mocks/stubs for I/O boundaries.",
                "Integration tests use real DB in containers; reset state between tests.",
                "CI pipeline runs tests on every PR; block merge on failure.",
                "Measure coverage but prioritise critical paths over percentage vanity.",
            ],
            key_facts=["Test pyramid: many unit, fewer integration, minimal E2E", "Flaky tests erode trust — quarantine and fix", "Property-based testing finds edge cases"],
            teaching="Testing is how teams move fast without breaking production. Good tests document intent and fail for the right reason.",
            explain=(
                "Software testing means automatically checking that code behaves correctly. Unit tests cover single "
                "functions with mocked dependencies — fast and precise. Integration tests hit real databases and "
                "HTTP layers. E2E tests simulate users in a browser — slower but catch wiring bugs. In CI every "
                "commit runs the suite; flaky tests get fixed immediately. I aim for high confidence on payment, "
                "auth, and data mutation paths — not 100% line coverage on UI glue."
            ),
            complex=(
                "Payments service had intermittent double-charge reports — 0.02% of transactions. Logs showed "
                "duplicate webhook delivery from the provider. I added idempotency keys stored in Redis with "
                "24-hour TTL, wrote property tests for the handler, and simulated duplicate POSTs in integration "
                "tests. Incidents went to zero in six weeks; added alerting on idempotency collision rate."
            ),
            pitfalls=["Testing implementation not behaviour", "Shared mutable test state", "Sleep-based timing in E2E"],
            related=["TDD", "Mocking", "Test containers", "Contract testing"],
        ),
    },
    "devops_engineer": {
        "testing": _s(
            definition="In DevOps, testing extends to infrastructure validation — policy as code, smoke tests post-deploy, chaos experiments, and pipeline gates.",
            how_it_works=["Terraform plan in CI", "OPA/Sentinel policy checks", "Post-deploy smoke against staging", "Canary analysis before full rollout"],
            key_facts=["Shift-left security scanning", "Immutable artifacts", "Rollback tested regularly"],
            teaching="DevOps testing validates that systems are deployable, secure, and observable — not only that application unit tests pass.",
            explain="We test infrastructure the same way we test apps: plan/apply dry runs, policy checks blocking public S3 buckets, and automated smoke tests after each deploy.",
            complex="A bad Terraform module passed unit tests but opened SG 0.0.0.0/0 in prod — we added OPA rules and tfsec in CI; blocked 12 similar PRs in the next quarter.",
            pitfalls=["Manual prod changes bypassing pipeline", "Untested rollback paths"],
            related=["CI/CD", "Policy as code", "Canary deploys"],
        ),
    },
}

def _infer_profile(skill_t: str, role: str, duty: str, domain: str) -> str:
    text = f"{skill_t} {role} {duty}".lower()
    if any(k in text for k in ("hazmat", "process design", "lab", "chemical", "safety", "qc", "gmp")):
        return "chemical_process"
    if any(k in text for k in ("policy", "administration", "civil service", "report writing", "case management")):
        return "public_admin"
    if any(k in text for k in ("lesson", "teaching", "classroom", "curriculum", "tutor", "lecturer")):
        return "education"
    if any(k in text for k in ("patient", "clinical", "pharmac", "radi", "diagnosis", "care")):
        return "healthcare"
    if any(k in text for k in ("finance", "valuation", "tax", "ifrs", "audit", "legal", "compliance")):
        return "finance_legal"
    if any(k in text for k in ("sales", "crm", "marketing", "seo", "brand", "e-commerce")):
        return "commercial"
    if any(k in text for k in ("driver", "courier", "route", "warehouse", "navigation", "delivery")):
        return "logistics"
    if any(k in text for k in ("hospitality", "kitchen", "food", "barista", "guest", "restaurant")):
        return "hospitality"
    return domain


def _profile_scaffold(profile: str, skill_t: str, role: str, duty: str) -> dict:
    if profile == "chemical_process":
        return {
            "standards": ["GHS/CLP", "REACH/COSHH", "HAZOP", "MOC"],
            "steps": [
                f"Define process intent and chemical inventory affecting {duty.lower()}.",
                "Review SDS hazards, incompatibilities, and exposure routes for each substance.",
                "Set control strategy: substitution, containment, ventilation, interlocks, PPE.",
                "Validate safeguards with HAZOP action closure and operator training.",
                "Monitor incidents/near misses and update SOPs under MOC governance.",
            ],
            "facts": [
                "Incompatibility control is as important as reactor design for incident prevention.",
                "SDS sections 2, 8, and 10 are operationally critical for safe handling.",
                "Process safety requires layered safeguards, not single-point controls.",
            ],
            "example": (
                f"In a {role} assignment on {duty.lower()}, I found solvent transfer relied on manual venting with no "
                "ground verification. I redesigned the step with closed transfer, bonding interlock, and LEL permissive; "
                "alarm excursions dropped to zero over the next campaign."
            ),
        }
    if profile == "public_admin":
        return {
            "standards": ["Data protection policy", "Records retention schedule", "Service-level targets"],
            "steps": [
                "Translate policy into a concrete workflow with eligibility rules and deadlines.",
                "Create a complete case record trail: intake, decision evidence, approvals, and correspondence.",
                "Run QA checks on completeness, lawful basis, and timeliness before closure.",
                "Escalate exceptions early with written risk/impact notes.",
                "Track cycle-time and rework rate to improve process reliability.",
            ],
            "facts": [
                "Most service delays come from incomplete case data and unclear ownership.",
                "Auditability matters as much as speed in public-facing administration.",
                "Clear decision logs reduce appeals and repeat contacts.",
            ],
            "example": (
                f"As {role}, I redesigned the {duty.lower()} workflow with mandatory data fields and decision templates; "
                "average processing time dropped 24% and audit queries reduced by half."
            ),
        }
    if profile == "education":
        return {
            "standards": ["Curriculum outcomes", "Safeguarding policy", "Assessment policy"],
            "steps": [
                "Map lesson objective to curriculum standard and success criteria.",
                "Diagnose baseline understanding with a short formative check.",
                "Deliver scaffolded instruction with differentiated tasks.",
                "Assess understanding in-class and adapt pacing immediately.",
                "Record attainment evidence and next-step intervention.",
            ],
            "facts": [
                "Formative assessment has larger impact than one-off summative testing.",
                "Differentiation is about access route, not lower expectations.",
                "Safeguarding responsibilities apply during every teaching activity.",
            ],
            "example": (
                f"In a {role} class, I used hinge questions to detect misconceptions mid-lesson and regrouped learners "
                "on the spot; attainment on exit tasks improved from 43% to 79%."
            ),
        }
    if profile == "healthcare":
        return {
            "standards": ["Clinical guideline pathway", "Medication safety checks", "SBAR handover"],
            "steps": [
                "Assess patient baseline and immediate risk flags.",
                "Apply protocol-driven intervention and verify contraindications.",
                "Document observations and response to treatment in real time.",
                "Escalate deterioration using structured handover (SBAR).",
                "Review outcomes and update care plan with MDT input.",
            ],
            "facts": [
                "Early escalation prevents preventable deterioration.",
                "Medication errors often occur at transition points and handovers.",
                "Documentation quality is directly linked to continuity of care.",
            ],
            "example": (
                f"On shift as {role}, I identified a subtle deterioration pattern, escalated with SBAR, and intervention "
                "was initiated within minutes, preventing critical care transfer."
            ),
        }
    if profile == "finance_legal":
        return {
            "standards": ["Applicable statutory framework", "Internal control policy", "Audit trail requirements"],
            "steps": [
                "Define scope, materiality threshold, and governing framework.",
                "Gather and reconcile source documents against assertions.",
                "Test assumptions and perform variance/sensitivity analysis.",
                "Document recommendations with risk disclosure and alternatives.",
                "Archive defensible working papers for audit/legal review.",
            ],
            "facts": [
                "Materiality drives prioritization of review effort.",
                "Defensible documentation is essential for auditability.",
                "Professional skepticism reduces avoidable compliance failures.",
            ],
            "example": (
                f"As {role}, I challenged a key assumption in the {duty.lower()} file, identified a hidden risk exposure, "
                "and updated the recommendation before sign-off."
            ),
        }
    if profile == "commercial":
        return {
            "standards": ["Campaign KPI framework", "CRM hygiene policy", "Conversion measurement model"],
            "steps": [
                "Define ICP/audience segment and objective metric (pipeline, ROAS, conversion).",
                "Design offer/message variant and channel plan.",
                "Instrument tracking (UTM, attribution, CRM stage rules).",
                "Run controlled test and analyze cohort performance.",
                "Scale winning variant and archive learnings.",
            ],
            "facts": [
                "Measurement design quality determines campaign learning quality.",
                "Lead quality matters more than top-of-funnel volume.",
                "Consistency between messaging and landing experience lifts conversion.",
            ],
            "example": (
                f"In {role}, I rebuilt the {duty.lower()} funnel with tighter audience segmentation and experiment design; "
                "qualified lead rate improved by 31% in one quarter."
            ),
        }
    if profile == "logistics":
        return {
            "standards": ["Route compliance policy", "Vehicle/asset safety checks", "Proof-of-delivery controls"],
            "steps": [
                "Plan route with constraints: time windows, capacity, and risk points.",
                "Perform pre-shift safety and documentation checks.",
                "Execute deliveries with scan/PoD discipline and exception logging.",
                "Handle disruptions with dynamic rerouting and customer updates.",
                "Reconcile manifests and incident reports end of shift.",
            ],
            "facts": [
                "On-time performance depends on exception handling, not only route planning.",
                "Proof-of-delivery integrity reduces disputes and write-offs.",
                "Pre-shift checks prevent high-cost roadside failures.",
            ],
            "example": (
                f"As {role}, I re-sequenced high-risk stops and improved live exception reporting; first-attempt "
                "delivery success increased while overtime hours dropped."
            ),
        }
    if profile == "hospitality":
        return {
            "standards": ["HACCP", "Service SOPs", "Allergen controls"],
            "steps": [
                "Set up station readiness, prep levels, and hygiene controls pre-service.",
                "Execute service SOP with quality checks at pass/dispatch.",
                "Manage guest communication and recovery when delays occur.",
                "Track waste, yield, and peak-period throughput.",
                "Close with sanitation, stock reconciliation, and handover notes.",
            ],
            "facts": [
                "Service recovery quality predicts repeat business better than perfect service rates.",
                "Allergen communication failures are high-severity operational risks.",
                "Prep discipline is the strongest predictor of peak-hour consistency.",
            ],
            "example": (
                f"During peak as {role}, I adjusted prep cadence and station allocation for {duty.lower()}; "
                "ticket times stabilized and complaint rate decreased materially."
            ),
        }
    # Domain-driven default
    return {
        "standards": [],
        "steps": [
            f"Clarify required outcome, constraints, and stakeholders for {duty.lower()}.",
            f"Apply {skill_t} using documented procedures and intermediate quality checks.",
            "Validate output against acceptance criteria and applicable standards.",
            "Record decisions and handover notes for traceability.",
            "Review result and improve process for next cycle.",
        ],
        "facts": [
            "Outcome quality improves when assumptions are explicit and testable.",
            "Traceability prevents repeated failures in handoffs.",
            "Risk controls must be integrated into normal workflow, not bolted on later.",
        ],
        "example": (
            f"In {role}, I applied {skill_t} to stabilize {duty.lower()} under constraints, documented the control points, "
            "and reduced rework through structured verification."
        ),
    }


def _generate_fallback(skill: str, role_title: str, responsibility: str | None) -> dict:
    """Produce substantive content when no curated entry exists."""
    from app.agents.job_search.knowledge.domains import classify_skill_domain, get_domain_foundation

    skill_t = title_case_skill(skill)
    duty = responsibility or "core professional duties"
    role = role_title or "Professional"
    domain = classify_skill_domain(skill, role_title)
    foundation = get_domain_foundation(domain)

    profile = _infer_profile(skill_t, role, duty, domain)
    scaffold = _profile_scaffold(profile, skill_t, role, duty)

    # Intentionally avoid reusing cached skill text, because older generated caches
    # can reintroduce generic language. Fallback content must be generated fresh.
    if profile == "chemical_process":
        definition = (
            f"{skill_t} in chemical engineering is the controlled application of chemistry, process safety, "
            f"and regulatory compliance to {duty.lower()} without creating unacceptable fire, toxicity, "
            "reactivity, or environmental release risk."
        )
    elif profile == "public_admin":
        definition = (
            f"{skill_t} in public administration is the design and execution of auditable workflows that "
            f"deliver {duty.lower()} lawfully, on time, and with complete records."
        )
    elif profile == "education":
        definition = (
            f"{skill_t} in education is the structured practice of turning curriculum goals into measurable "
            "learning outcomes through instruction, assessment, and safeguarding."
        )
    elif profile == "healthcare":
        definition = (
            f"{skill_t} in healthcare is the clinically governed practice of delivering interventions that "
            "improve patient outcomes while maintaining safety, consent, and continuity of care."
        )
    elif profile == "finance_legal":
        definition = (
            f"{skill_t} in legal/financial work is the evidence-based application of statutory rules and "
            "professional judgment to produce defensible decisions."
        )
    elif profile == "commercial":
        definition = (
            f"{skill_t} in commercial functions is the disciplined execution of market-facing activities "
            "that improve qualified demand, conversion quality, and customer value."
        )
    elif profile == "logistics":
        definition = (
            f"{skill_t} in logistics is the operational control of routing, handoffs, and proof-of-delivery "
            "to meet service windows safely and efficiently."
        )
    elif profile == "hospitality":
        definition = (
            f"{skill_t} in hospitality is the repeatable delivery of safe, high-quality service under "
            "time pressure, with hygiene and guest-experience controls."
        )
    else:
        definition = (
            f"{skill_t} is the body of knowledge, tools, standards, and verified procedures that "
            f"{role} professionals apply when performing {duty.lower()}."
        )

    how_it_works = scaffold["steps"]
    key_facts = scaffold["facts"][:5]
    teaching = (
        f"{definition} In {role} practice, {skill_t} directly supports {duty.lower()}. "
        f"{foundation['field_intro']} Operational excellence requires explicit controls, measurable checks, "
        "and documented decision points."
    )

    explain = (
        f"In this {role} context, {skill_t} starts with {how_it_works[0].lower()} "
        f"and continues through {how_it_works[1].lower() if len(how_it_works) > 1 else 'verification controls'}. "
        f"The critical discipline is evidence: {key_facts[0].lower() if key_facts else 'verify controls before execution'}. "
        f"When conditions change, I revalidate assumptions before proceeding — that is how {duty.lower()} stays reliable "
        f"under real operational constraints."
    )

    complex = scaffold["example"]

    return {
        "definition": definition,
        "how_it_works": how_it_works,
        "key_facts": key_facts,
        "standards": scaffold["standards"],
        "teaching_body": teaching,
        "explain_answer": explain,
        "complex_answer": complex,
        "technical_pitfalls": [
            f"Executing {skill_t} without validating prerequisites and constraints.",
            "Relying on habit instead of current procedures and controls.",
            "Incomplete records that break traceability and handover.",
        ],
        "related_topics": [skill_t, *scaffold["facts"][:2], domain.replace("_", " ")],
    }


def resolve_expert_content(skill: str, role_title: str | None = None, responsibility: str | None = None) -> dict:
    """Return substantive expert content for skill, with role overrides."""
    sk = normalize_key(skill)
    role_k = normalize_key(role_title or "")

    if role_k in _ROLE_SKILL_OVERRIDES and sk in _ROLE_SKILL_OVERRIDES[role_k]:
        return _ROLE_SKILL_OVERRIDES[role_k][sk]

    if sk in _SKILL:
        content = dict(_SKILL[sk])
        # Personalise complex answer with role if generic
        if role_title and role_k:
            content["complex_answer"] = content["complex_answer"].replace("On a", f"As {role_title}, on a", 1) if content["complex_answer"].startswith("On a") else content["complex_answer"]
        return content

    return _generate_fallback(skill, role_title or "Professional", responsibility)


def list_curated_skills() -> list[str]:
    return list(_SKILL.keys())
