/**
 * Curated popular job roles across educational streams — full-time careers
 * and part-time / odd-job listings for quick interview-pack & CV prep.
 */

import type { JobFormState } from "./jobForm";
import { formToSavePayload } from "./jobForm";

export type EmploymentCategory = "full_time" | "part_time_odd";

export interface EducationStream {
  id: string;
  label: string;
}

export interface PopularJobRole {
  id: string;
  title: string;
  streamId: string;
  category: EmploymentCategory;
  employment_type: string;
  experience_level: string;
  description: string;
  responsibilities: string[];
  requirements: string[];
  skills: string[];
}

export const EDUCATION_STREAMS: EducationStream[] = [
  { id: "engineering", label: "Engineering & Technology" },
  { id: "computer_science", label: "Computer Science & IT" },
  { id: "medicine", label: "Medicine & Healthcare" },
  { id: "nursing", label: "Nursing & Allied Health" },
  { id: "business", label: "Business & Management" },
  { id: "finance", label: "Finance & Accounting" },
  { id: "law", label: "Law & Legal Studies" },
  { id: "education", label: "Education & Teaching" },
  { id: "arts_media", label: "Arts, Design & Media" },
  { id: "science", label: "Science & Research" },
  { id: "hospitality", label: "Hospitality & Tourism" },
  { id: "retail_sales", label: "Retail & Sales" },
  { id: "construction", label: "Construction & Trades" },
  { id: "agriculture", label: "Agriculture & Environment" },
  { id: "social_sciences", label: "Social Sciences & Psychology" },
  { id: "public_service", label: "Public Service & Government" },
];

const PART_TIME_STREAMS: EducationStream[] = [
  { id: "gig_delivery", label: "Gig & Delivery" },
  { id: "retail_hospitality", label: "Retail & Hospitality" },
  { id: "tutoring", label: "Tutoring & Education Support" },
  { id: "creative_freelance", label: "Creative & Freelance" },
  { id: "care_community", label: "Care & Community" },
  { id: "admin_remote", label: "Admin & Remote Tasks" },
  { id: "events_seasonal", label: "Events & Seasonal" },
  { id: "odd_jobs", label: "Odd Jobs & Handyman" },
];

function role(
  id: string,
  title: string,
  streamId: string,
  category: EmploymentCategory,
  skills: string[],
  responsibilities: string[],
  requirements: string[],
  employment_type: string,
  experience_level: string,
): PopularJobRole {
  const typeLabel = category === "part_time_odd" ? "Part-time / gig" : "Full-time";
  return {
    id,
    title,
    streamId,
    category,
    employment_type,
    experience_level,
    skills,
    responsibilities,
    requirements,
    description: `${title} — ${typeLabel} role in ${streamId.replace(/_/g, " ")}. Typical duties include ${responsibilities.slice(0, 2).join("; ").toLowerCase()}.`,
  };
}

const FULL_TIME_ROLES: PopularJobRole[] = [
  // Engineering
  role("ft-civil-eng", "Civil Engineer", "engineering", "full_time", ["AutoCAD", "Structural analysis", "Project management", "Site supervision"], ["Design infrastructure plans", "Oversee construction compliance", "Coordinate with contractors"], ["BEng Civil Engineering", "Professional accreditation", "2+ years site experience"], "Full-time", "Mid level (3–5 years)"),
  role("ft-mech-eng", "Mechanical Engineer", "engineering", "full_time", ["CAD", "Thermodynamics", "Manufacturing processes", "FEA"], ["Design mechanical systems", "Run simulations and tests", "Improve production efficiency"], ["Mechanical engineering degree", "CAD proficiency", "Problem-solving skills"], "Full-time", "Mid level (3–5 years)"),
  role("ft-electrical-eng", "Electrical Engineer", "engineering", "full_time", ["Circuit design", "PLC programming", "Power systems", "Safety standards"], ["Design electrical layouts", "Troubleshoot systems", "Ensure regulatory compliance"], ["Electrical engineering degree", "Licensed engineer preferred"], "Full-time", "Senior (5–8 years)"),
  role("ft-chemical-eng", "Chemical Engineer", "engineering", "full_time", ["Process design", "Hazmat safety", "Quality control", "Lab analysis"], ["Optimize chemical processes", "Monitor plant operations", "Document SOPs"], ["Chemical engineering degree", "Plant experience"], "Full-time", "Mid level (3–5 years)"),
  // CS & IT
  role("ft-software-eng", "Software Engineer", "computer_science", "full_time", ["JavaScript", "Python", "System design", "Git", "APIs"], ["Build and ship features", "Write tests and documentation", "Participate in code reviews"], ["CS degree or bootcamp", "2+ years development", "Strong problem solving"], "Full-time", "Mid level (3–5 years)"),
  role("ft-data-scientist", "Data Scientist", "computer_science", "full_time", ["Python", "SQL", "Machine learning", "Statistics", "Visualization"], ["Build predictive models", "Analyze business datasets", "Present insights to stakeholders"], ["Statistics or CS background", "ML project portfolio"], "Full-time", "Mid level (3–5 years)"),
  role("ft-cyber-analyst", "Cybersecurity Analyst", "computer_science", "full_time", ["SIEM", "Incident response", "Network security", "Risk assessment"], ["Monitor security alerts", "Investigate incidents", "Recommend hardening measures"], ["Security certifications", "IT operations experience"], "Full-time", "Mid level (3–5 years)"),
  role("ft-product-manager", "Product Manager (Tech)", "computer_science", "full_time", ["Roadmapping", "Agile", "User research", "Stakeholder management"], ["Define product vision", "Prioritize backlog", "Align engineering and design"], ["Product management experience", "Technical literacy"], "Full-time", "Senior (5–8 years)"),
  role("ft-devops", "DevOps Engineer", "computer_science", "full_time", ["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform"], ["Maintain deployment pipelines", "Improve system reliability", "Automate infrastructure"], ["Cloud platform experience", "Scripting skills"], "Full-time", "Senior (5–8 years)"),
  // Medicine
  role("ft-gp", "General Practitioner", "medicine", "full_time", ["Clinical diagnosis", "Patient care", "EMR systems", "Communication"], ["Consult patients", "Refer to specialists", "Maintain medical records"], ["Medical degree", "License to practice", "Residency completed"], "Full-time", "Senior (5–8 years)"),
  role("ft-pharmacist", "Clinical Pharmacist", "medicine", "full_time", ["Pharmacology", "Patient counseling", "Inventory management"], ["Dispense medications safely", "Advise on drug interactions", "Manage pharmacy operations"], ["Pharmacy degree", "Registered pharmacist"], "Full-time", "Mid level (3–5 years)"),
  role("ft-radiographer", "Radiographer", "medicine", "full_time", ["Medical imaging", "Radiation safety", "Patient positioning"], ["Operate imaging equipment", "Prepare patients for scans", "Collaborate with radiologists"], ["Radiography qualification", "Hospital experience"], "Full-time", "Mid level (3–5 years)"),
  // Nursing
  role("ft-registered-nurse", "Registered Nurse", "nursing", "full_time", ["Patient assessment", "Medication administration", "Care planning", "CPR"], ["Deliver bedside care", "Coordinate with physicians", "Document patient progress"], ["Nursing degree", "NMC registration", "Ward experience"], "Full-time", "Mid level (3–5 years)"),
  role("ft-physio", "Physiotherapist", "nursing", "full_time", ["Rehabilitation", "Manual therapy", "Exercise prescription"], ["Assess mobility needs", "Design treatment plans", "Track recovery outcomes"], ["Physiotherapy degree", "HCPC registered"], "Full-time", "Mid level (3–5 years)"),
  role("ft-occupational", "Occupational Therapist", "nursing", "full_time", ["ADL training", "Assistive technology", "Mental health support"], ["Support daily living skills", "Adapt environments for patients", "Work with multidisciplinary teams"], ["OT degree", "Clinical placement experience"], "Full-time", "Entry level (0–2 years)"),
  // Business
  role("ft-marketing-mgr", "Marketing Manager", "business", "full_time", ["Digital marketing", "Campaign strategy", "Analytics", "Brand management"], ["Plan marketing campaigns", "Manage budgets", "Report on KPIs"], ["Marketing degree or equivalent", "3+ years experience"], "Full-time", "Senior (5–8 years)"),
  role("ft-hr-bp", "HR Business Partner", "business", "full_time", ["Employee relations", "Talent acquisition", "HR policy", "Coaching"], ["Support people strategy", "Handle employee issues", "Partner with leadership"], ["HR certification", "Stakeholder management"], "Full-time", "Senior (5–8 years)"),
  role("ft-ops-mgr", "Operations Manager", "business", "full_time", ["Process improvement", "KPI tracking", "Team leadership", "Budgeting"], ["Optimize daily operations", "Lead operational teams", "Drive efficiency initiatives"], ["Operations or business degree", "Leadership experience"], "Full-time", "Senior (5–8 years)"),
  role("ft-consultant", "Management Consultant", "business", "full_time", ["Strategy", "Financial modelling", "Presentation", "Client management"], ["Analyze client problems", "Develop recommendations", "Facilitate workshops"], ["Top-tier analytical skills", "Consulting or industry experience"], "Full-time", "Mid level (3–5 years)"),
  // Finance
  role("ft-accountant", "Chartered Accountant", "finance", "full_time", ["Financial reporting", "Tax", "Audit", "Excel", "IFRS"], ["Prepare financial statements", "Support audits", "Advise on compliance"], ["Accounting qualification", "Practice experience"], "Full-time", "Mid level (3–5 years)"),
  role("ft-fin-analyst", "Financial Analyst", "finance", "full_time", ["Financial modelling", "Forecasting", "Excel", "Power BI"], ["Build financial models", "Analyze variances", "Support investment decisions"], ["Finance or economics degree", "Analytical mindset"], "Full-time", "Entry level (0–2 years)"),
  role("ft-investment", "Investment Analyst", "finance", "full_time", ["Equity research", "Valuation", "Market analysis", "Bloomberg"], ["Research securities", "Write investment memos", "Monitor portfolio risk"], ["Finance degree", "Strong numeracy"], "Full-time", "Entry level (0–2 years)"),
  // Law
  role("ft-solicitor", "Solicitor", "law", "full_time", ["Legal research", "Contract drafting", "Client advisory", "Litigation support"], ["Manage client cases", "Draft legal documents", "Represent clients where permitted"], ["Law degree", "Qualified solicitor"], "Full-time", "Mid level (3–5 years)"),
  role("ft-paralegal", "Paralegal", "law", "full_time", ["Case management", "Legal documentation", "E-discovery"], ["Support attorneys", "Organize case files", "Conduct legal research"], ["Paralegal certificate", "Attention to detail"], "Full-time", "Entry level (0–2 years)"),
  role("ft-compliance", "Compliance Officer", "law", "full_time", ["Regulatory compliance", "Risk assessment", "Policy writing"], ["Monitor regulatory changes", "Conduct internal audits", "Train staff on compliance"], ["Law or finance background", "Regulatory knowledge"], "Full-time", "Mid level (3–5 years)"),
  // Education
  role("ft-primary-teacher", "Primary School Teacher", "education", "full_time", ["Lesson planning", "Classroom management", "Safeguarding", "Assessment"], ["Teach core subjects", "Support pupil development", "Communicate with parents"], ["Teaching qualification", "DBS clearance"], "Full-time", "Mid level (3–5 years)"),
  role("ft-secondary-maths", "Secondary Maths Teacher", "education", "full_time", ["Mathematics curriculum", "Differentiated instruction", "Exam preparation"], ["Deliver maths lessons", "Mark and assess work", "Support extracurricular activities"], ["PGCE or equivalent", "Subject degree"], "Full-time", "Mid level (3–5 years)"),
  role("ft-lecturer", "University Lecturer", "education", "full_time", ["Research", "Academic writing", "Lecture delivery", "Mentoring"], ["Teach undergraduate modules", "Publish research", "Supervise dissertations"], ["PhD or masters with teaching exp", "Subject expertise"], "Full-time", "Senior (5–8 years)"),
  // Arts & Media
  role("ft-graphic-designer", "Graphic Designer", "arts_media", "full_time", ["Adobe Creative Suite", "Typography", "Brand identity", "UI basics"], ["Create visual assets", "Collaborate with marketing", "Maintain brand guidelines"], ["Design portfolio", "Creative degree preferred"], "Full-time", "Mid level (3–5 years)"),
  role("ft-journalist", "Journalist", "arts_media", "full_time", ["Reporting", "Interviewing", "Fact-checking", "Digital publishing"], ["Research and write stories", "Meet deadlines", "Engage audiences online"], ["Journalism degree or portfolio", "Strong writing"], "Full-time", "Mid level (3–5 years)"),
  role("ft-film-editor", "Video Editor", "arts_media", "full_time", ["Premiere Pro", "After Effects", "Storytelling", "Color grading"], ["Edit video content", "Sync audio and graphics", "Deliver final cuts"], ["Editing portfolio", "Production experience"], "Full-time", "Mid level (3–5 years)"),
  // Science
  role("ft-lab-scientist", "Laboratory Scientist", "science", "full_time", ["Lab techniques", "Data analysis", "Quality control", "Safety protocols"], ["Run experiments", "Record results accurately", "Maintain lab equipment"], ["Science degree", "Lab experience"], "Full-time", "Entry level (0–2 years)"),
  role("ft-biologist", "Research Biologist", "science", "full_time", ["Molecular biology", "PCR", "Scientific writing", "Statistics"], ["Design experiments", "Analyze biological data", "Publish findings"], ["Biology masters or PhD", "Research experience"], "Full-time", "Mid level (3–5 years)"),
  role("ft-environmental", "Environmental Scientist", "science", "full_time", ["Environmental impact assessment", "GIS", "Field sampling", "Regulations"], ["Assess environmental risks", "Prepare reports", "Support sustainability projects"], ["Environmental science degree", "Field work experience"], "Full-time", "Mid level (3–5 years)"),
  // Hospitality
  role("ft-hotel-mgr", "Hotel Manager", "hospitality", "full_time", ["Guest services", "Revenue management", "Team leadership", "Hospitality software"], ["Oversee daily hotel operations", "Ensure guest satisfaction", "Manage staff schedules"], ["Hospitality management degree", "Hotel experience"], "Full-time", "Senior (5–8 years)"),
  role("ft-chef", "Head Chef", "hospitality", "full_time", ["Menu development", "Food safety", "Kitchen management", "Cost control"], ["Lead kitchen brigade", "Maintain quality standards", "Manage inventory"], ["Culinary qualification", "Kitchen leadership"], "Full-time", "Senior (5–8 years)"),
  role("ft-travel-consult", "Travel Consultant", "hospitality", "full_time", ["Itinerary planning", "GDS systems", "Customer service", "Sales"], ["Book travel packages", "Advise clients on destinations", "Handle bookings and changes"], ["Travel industry experience", "Sales skills"], "Full-time", "Entry level (0–2 years)"),
  // Retail & Sales
  role("ft-store-mgr", "Retail Store Manager", "retail_sales", "full_time", ["Retail operations", "Merchandising", "Sales targets", "Staff training"], ["Hit sales KPIs", "Manage inventory", "Lead store team"], ["Retail management experience", "Customer focus"], "Full-time", "Mid level (3–5 years)"),
  role("ft-account-exec", "Account Executive", "retail_sales", "full_time", ["B2B sales", "CRM", "Negotiation", "Pipeline management"], ["Prospect new clients", "Close deals", "Maintain relationships"], ["Sales track record", "Communication skills"], "Full-time", "Mid level (3–5 years)"),
  role("ft-ecommerce", "E-commerce Manager", "retail_sales", "full_time", ["Shopify", "SEO", "Conversion optimization", "Analytics"], ["Grow online revenue", "Manage product listings", "Optimize checkout funnel"], ["Digital commerce experience", "Analytical skills"], "Full-time", "Mid level (3–5 years)"),
  // Construction
  role("ft-site-mgr", "Construction Site Manager", "construction", "full_time", ["Site safety", "Project scheduling", "Subcontractor coordination", "Blueprints"], ["Supervise construction sites", "Ensure health and safety", "Track project milestones"], ["Construction management", "CSCS card", "Site experience"], "Full-time", "Senior (5–8 years)"),
  role("ft-architect", "Architect", "construction", "full_time", ["AutoCAD", "Revit", "Building regulations", "Client presentations"], ["Develop architectural designs", "Coordinate with engineers", "Manage planning submissions"], ["Architecture degree", "ARB registered"], "Full-time", "Senior (5–8 years)"),
  role("ft-electrician", "Electrician", "construction", "full_time", ["Electrical installation", "Testing", "Wiring regulations", "Fault finding"], ["Install electrical systems", "Test and certify work", "Troubleshoot faults"], ["Electrician apprenticeship", "Qualified tradesperson"], "Full-time", "Mid level (3–5 years)"),
  // Agriculture
  role("ft-farm-mgr", "Farm Manager", "agriculture", "full_time", ["Crop management", "Livestock care", "Machinery operation", "Sustainability"], ["Plan planting cycles", "Manage farm workers", "Monitor yields and costs"], ["Agricultural degree or experience", "Practical farming skills"], "Full-time", "Mid level (3–5 years)"),
  role("ft-env-consultant", "Environmental Consultant", "agriculture", "full_time", ["Ecology", "Environmental law", "Report writing", "Field surveys"], ["Conduct site assessments", "Advise on sustainability", "Prepare compliance reports"], ["Environmental science background", "Consulting experience"], "Full-time", "Mid level (3–5 years)"),
  // Social sciences
  role("ft-social-worker", "Social Worker", "social_sciences", "full_time", ["Case management", "Safeguarding", "Counselling", "Multi-agency working"], ["Support vulnerable individuals", "Conduct assessments", "Develop care plans"], ["Social work degree", "Registered social worker"], "Full-time", "Mid level (3–5 years)"),
  role("ft-psychologist", "Clinical Psychologist", "social_sciences", "full_time", ["CBT", "Assessment", "Therapeutic interventions", "Ethics"], ["Deliver therapy sessions", "Conduct psychological assessments", "Maintain clinical records"], ["Doctorate in clinical psychology", "HCPC registered"], "Full-time", "Senior (5–8 years)"),
  role("ft-hr-advisor", "HR Advisor", "social_sciences", "full_time", ["Employee relations", "HR systems", "Policy guidance"], ["Answer HR queries", "Support recruitment", "Assist with disciplinary processes"], ["CIPD qualification", "HR experience"], "Full-time", "Mid level (3–5 years)"),
  // Public service
  role("ft-policy-officer", "Policy Officer", "public_service", "full_time", ["Policy analysis", "Stakeholder engagement", "Report writing", "Research"], ["Draft policy briefs", "Consult stakeholders", "Evaluate programme impact"], ["Public policy degree", "Government experience"], "Full-time", "Mid level (3–5 years)"),
  role("ft-civil-servant", "Civil Service Administrator", "public_service", "full_time", ["Administration", "Project support", "Data handling", "Communication"], ["Support departmental programmes", "Process applications", "Coordinate meetings"], ["Admin experience", "Security clearance may apply"], "Full-time", "Entry level (0–2 years)"),
  role("ft-emergency", "Emergency Services Coordinator", "public_service", "full_time", ["Incident coordination", "Radio communications", "Crisis management"], ["Coordinate emergency responses", "Log incidents", "Liaise with services"], ["Emergency services training", "Calm under pressure"], "Full-time", "Mid level (3–5 years)"),
];

const PART_TIME_ROLES: PopularJobRole[] = [
  role("pt-delivery", "Food Delivery Driver", "gig_delivery", "part_time_odd", ["Navigation", "Customer service", "Time management"], ["Pick up and deliver orders", "Follow app routing", "Maintain delivery standards"], ["Valid driving license", "Smartphone", "Flexible availability"], "Part-time / Gig", "Entry level (0–2 years)"),
  role("pt-rideshare", "Rideshare Driver", "gig_delivery", "part_time_odd", ["Safe driving", "Navigation", "Customer service"], ["Transport passengers", "Maintain vehicle cleanliness", "Follow platform policies"], ["Driving license", "Background check", "Own vehicle"], "Gig", "Entry level (0–2 years)"),
  role("pt-courier", "Parcel Courier", "gig_delivery", "part_time_odd", ["Route planning", "Package handling", "Punctuality"], ["Deliver parcels on schedule", "Scan packages", "Report issues"], ["Driving license", "Physical fitness"], "Part-time", "Entry level (0–2 years)"),
  role("pt-barista", "Barista", "retail_hospitality", "part_time_odd", ["Coffee preparation", "Cash handling", "Customer service"], ["Prepare drinks to standard", "Operate POS", "Keep workspace clean"], ["Hospitality experience helpful", "Friendly manner"], "Part-time", "Entry level (0–2 years)"),
  role("pt-retail", "Retail Sales Associate", "retail_hospitality", "part_time_odd", ["Customer service", "Merchandising", "POS systems"], ["Assist shoppers", "Restock shelves", "Process transactions"], ["Retail experience preferred", "Weekend availability"], "Part-time", "Entry level (0–2 years)"),
  role("pt-waiter", "Waiter / Waitress", "retail_hospitality", "part_time_odd", ["Table service", "Order taking", "Upselling"], ["Serve guests", "Take orders accurately", "Handle payments"], ["Food service experience", "Team player"], "Part-time", "Entry level (0–2 years)"),
  role("pt-kitchen", "Kitchen Porter", "retail_hospitality", "part_time_odd", ["Food hygiene", "Cleaning", "Kitchen support"], ["Wash dishes and equipment", "Support chefs", "Maintain hygiene standards"], ["Food hygiene certificate helpful"], "Part-time", "Entry level (0–2 years)"),
  role("pt-tutor-maths", "Private Maths Tutor", "tutoring", "part_time_odd", ["Mathematics", "Lesson planning", "Patience", "Communication"], ["Tutor students 1:1 or small groups", "Prepare practice materials", "Track progress"], ["Strong maths grades", "DBS check", "Teaching aptitude"], "Part-time", "Entry level (0–2 years)"),
  role("pt-tutor-english", "English Language Tutor", "tutoring", "part_time_odd", ["English", "ESL", "Communication", "Lesson planning"], ["Teach reading and writing", "Support exam preparation", "Give constructive feedback"], ["English qualification", "Tutoring experience"], "Part-time", "Entry level (0–2 years)"),
  role("pt-teaching-asst", "Teaching Assistant", "tutoring", "part_time_odd", ["Classroom support", "Safeguarding", "Behaviour management"], ["Support lead teacher", "Help pupils with tasks", "Supervise activities"], ["DBS clearance", "Experience with children"], "Part-time", "Entry level (0–2 years)"),
  role("pt-freelance-design", "Freelance Graphic Designer", "creative_freelance", "part_time_odd", ["Illustrator", "Photoshop", "Branding", "Client communication"], ["Deliver design projects", "Revise based on feedback", "Meet deadlines"], ["Portfolio", "Self-employed setup"], "Freelance", "Mid level (3–5 years)"),
  role("pt-content-writer", "Freelance Content Writer", "creative_freelance", "part_time_odd", ["Copywriting", "SEO", "Research", "Editing"], ["Write blog posts and web copy", "Optimize for SEO", "Meet client briefs"], ["Writing samples", "Reliable internet"], "Freelance", "Entry level (0–2 years)"),
  role("pt-photographer", "Event Photographer", "creative_freelance", "part_time_odd", ["Photography", "Lightroom", "Client relations"], ["Shoot events", "Edit and deliver photos", "Manage bookings"], ["Camera equipment", "Portfolio"], "Freelance / Gig", "Mid level (3–5 years)"),
  role("pt-care-assistant", "Care Assistant", "care_community", "part_time_odd", ["Personal care", "Empathy", "Safeguarding", "Medication prompts"], ["Support daily living", "Accompany clients", "Report concerns"], ["Care certificate helpful", "DBS check"], "Part-time", "Entry level (0–2 years)"),
  role("pt-babysitter", "Babysitter / Nanny", "care_community", "part_time_odd", ["Childcare", "First aid", "Reliability"], ["Supervise children", "Follow routines", "Communicate with parents"], ["Childcare experience", "References", "DBS"], "Part-time", "Entry level (0–2 years)"),
  role("pt-dog-walker", "Dog Walker / Pet Sitter", "care_community", "part_time_odd", ["Animal care", "Reliability", "Communication"], ["Walk dogs safely", "Feed and check on pets", "Send updates to owners"], ["Animal experience", "Insurance recommended"], "Gig", "Entry level (0–2 years)"),
  role("pt-data-entry", "Data Entry Clerk", "admin_remote", "part_time_odd", ["Typing", "Excel", "Attention to detail", "Accuracy"], ["Enter data into systems", "Verify records", "Meet daily targets"], ["Fast typing", "Basic computer skills"], "Part-time / Remote", "Entry level (0–2 years)"),
  role("pt-virtual-asst", "Virtual Assistant", "admin_remote", "part_time_odd", ["Email management", "Scheduling", "Microsoft Office", "Communication"], ["Manage calendars", "Handle admin tasks", "Coordinate meetings"], ["Remote work experience", "Organized"], "Part-time / Remote", "Entry level (0–2 years)"),
  role("pt-transcription", "Transcriptionist", "admin_remote", "part_time_odd", ["Typing", "Listening", "Grammar", "Confidentiality"], ["Transcribe audio accurately", "Format documents", "Meet deadlines"], ["Fast typing WPM", "Headphones"], "Freelance / Remote", "Entry level (0–2 years)"),
  role("pt-event-staff", "Event Staff", "events_seasonal", "part_time_odd", ["Customer service", "Teamwork", "Stamina"], ["Register attendees", "Direct guests", "Support event logistics"], ["Flexible hours", "Smart appearance"], "Casual / Seasonal", "Entry level (0–2 years)"),
  role("pt-promoter", "Brand Promoter", "events_seasonal", "part_time_odd", ["Sales", "Communication", "Product knowledge"], ["Promote products at events", "Engage passers-by", "Distribute samples"], ["Outgoing personality", "Weekend availability"], "Casual", "Entry level (0–2 years)"),
  role("pt-warehouse", "Warehouse Picker / Packer", "events_seasonal", "part_time_odd", ["Order picking", "Physical fitness", "Accuracy"], ["Pick and pack orders", "Operate handheld scanners", "Meet pick rates"], ["Warehouse experience helpful", "Safety boots"], "Part-time / Shift", "Entry level (0–2 years)"),
  role("pt-handyman", "Handyman / Odd Jobs", "odd_jobs", "part_time_odd", ["Basic repairs", "Painting", "Assembly", "Tool use"], ["Complete small home repairs", "Assemble furniture", "Quote for jobs"], ["Practical skills", "Own tools", "Reliable transport"], "Gig / Self-employed", "Mid level (3–5 years)"),
  role("pt-cleaner", "Domestic Cleaner", "odd_jobs", "part_time_odd", ["Cleaning", "Time management", "Trustworthiness"], ["Clean homes or offices", "Follow checklists", "Bring supplies if required"], ["Cleaning experience", "References"], "Part-time", "Entry level (0–2 years)"),
  role("pt-gardener", "Gardener / Landscaping Helper", "odd_jobs", "part_time_odd", ["Gardening", "Physical work", "Tool use"], ["Mow lawns and trim hedges", "Clear garden waste", "Maintain outdoor spaces"], ["Outdoor work experience", "Own transport helpful"], "Part-time / Seasonal", "Entry level (0–2 years)"),
  role("pt-mover", "Removal / Moving Helper", "odd_jobs", "part_time_odd", ["Heavy lifting", "Teamwork", "Care with belongings"], ["Load and unload vans", "Protect furniture", "Follow move schedules"], ["Physical fitness", "Reliable"], "Casual / Gig", "Entry level (0–2 years)"),
  role("pt-call-center", "Call Center Agent (Part-time)", "admin_remote", "part_time_odd", ["Phone manner", "CRM", "Problem solving"], ["Handle inbound calls", "Log interactions", "Follow scripts"], ["Clear communication", "Headset", "Shift flexibility"], "Part-time", "Entry level (0–2 years)"),
];

export const ALL_POPULAR_ROLES = [...FULL_TIME_ROLES, ...PART_TIME_ROLES];

export function getStreamsForCategory(category: EmploymentCategory): EducationStream[] {
  return category === "full_time" ? EDUCATION_STREAMS : PART_TIME_STREAMS;
}

export function getRolesForStream(streamId: string, category: EmploymentCategory): PopularJobRole[] {
  return ALL_POPULAR_ROLES.filter((r) => r.streamId === streamId && r.category === category);
}

export function popularRoleToForm(role: PopularJobRole): JobFormState {
  return {
    title: role.title,
    company_name: "",
    company_url: "",
    location: "Flexible / Various",
    employment_type: role.employment_type,
    experience_level: role.experience_level,
    is_remote: role.category === "part_time_odd" && role.streamId === "admin_remote",
    salary_min: "",
    salary_max: "",
    salary_currency: "GBP",
    source_url: "",
    description_raw: role.description,
    responsibilities: role.responsibilities.join("\n"),
    requirements: role.requirements.join("\n"),
    benefits: role.category === "part_time_odd" ? "Flexible hours\nImmediate start" : "Professional development\nPension scheme",
    skills: role.skills.join(", "),
  };
}


export function savePayloadFromPopularRole(form: JobFormState): Record<string, unknown> {
  return { ...formToSavePayload(form), import_method: "popular_role" };
}
