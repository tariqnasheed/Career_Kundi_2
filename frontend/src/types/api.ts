/**
 * types/api.ts
 * ============
 * TypeScript interfaces mirroring the FastAPI Pydantic response schemas.
 * Keep these in lockstep with the backend schemas in `app/schemas/`.
 *
 * These are TYPE DECLARATIONS ONLY — no runtime logic here.
 */

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface UserRead {
  id: string;
  email: string;
  full_name: string;
  role: string;
  plan: string;
  is_email_verified: boolean;
  is_active: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Job Search
// ---------------------------------------------------------------------------

export interface SavedJobRead {
  id: string;
  source_url: string | null;
  source_site: string | null;
  import_method: string;
  status: "saved" | "applied" | "interviewing" | "offered" | "rejected";
  title: string;
  company_name: string | null;
  company_url: string | null;
  location: string | null;
  employment_type: string | null;
  is_remote: boolean | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  description_raw: string | null;
  responsibilities: string[];
  requirements: string[];
  benefits: string[];
  extracted_skills: ExtractedSkill[];
  company_profile: Record<string, unknown>;
  verification_status: "verified" | "partial" | "unverified";
  verification_sources: Record<string, unknown>[];
  match_score: number | null;
  interview_pack_confidence: number | null;
  interview_pack_generated_at: string | null;
  has_interview_pack: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExtractedSkill {
  skill: string;
  category?: "technical" | "soft" | "tool" | "domain";
  importance?: "critical" | "high" | "medium" | "nice-to-have";
}

/** Preview card from live web job discovery (not yet saved). */
export interface JobDiscoveryResult {
  title: string;
  company_name: string | null;
  location: string | null;
  employment_type: string | null;
  is_remote: boolean | null;
  snippet: string;
  source_url: string;
  source_site: string | null;
  salary_hint: string | null;
  verified: boolean;
}

export interface CompanyResearchSourceRead {
  url: string;
  source_type: string;
  title?: string | null;
  extracted_facts?: string[];
  confidence?: string;
}

export interface CompanyResearchRead {
  company_name?: string | null;
  company_domain?: string | null;
  official_website?: string | null;
  company_overview?: string | null;
  products_services?: string[];
  industries?: string[];
  markets?: string[];
  mission_or_values?: string[];
  company_size?: string | null;
  headquarters?: string | null;
  source_urls?: string[];
  sources?: CompanyResearchSourceRead[];
  research_confidence?: string;
  source_status?: Record<string, string>;
  warnings?: string[];
  research_methods?: string[];
}

export interface JobPostingExtractionRead {
  source_url: string;
  final_url?: string | null;
  title?: string | null;
  company_name?: string | null;
  company_profile?: string | null;
  description?: string | null;
  responsibilities?: string[];
  requirements?: string[];
  preferred_qualifications?: string[];
  tools?: string[];
  skills?: string[];
  location?: string | null;
  seniority?: string | null;
  employment_type?: string | null;
  date_posted?: string | null;
  valid_through?: string | null;
  salary_text?: string | null;
  extraction_confidence?: string;
  extraction_methods?: string[];
  warnings?: string[];
  source_status?: Record<string, string>;
}

export interface InterviewPackRead {
  job_id: string;
  questions: InterviewQuestion[];
  confidence_score: number | null;
  generated_at: string | null;
  role_slug?: string | null;
  role_overview?: RoleOverview | null;
  library_status?: "generated" | "library_reused" | "library_fallback" | "none";
  saved_documents?: string[];
  fallback_message?: string | null;
  from_library?: boolean;
  job_intelligence?: {
    completeness_score?: number;
    warnings?: string[];
    summary?: string;
    source_status?: Record<string, string>;
    source_ladder?: Record<string, string>;
  } | null;
  job_posting_extraction?: JobPostingExtractionRead | null;
  company_research?: CompanyResearchRead | null;
  coverage_audit?: Record<string, unknown> | null;
}

export interface SkillCluster {
  skill_name: string;
  questions: InterviewQuestion[];
}

export interface InterviewQuestion {
  question_id?: string | null;
  question: string;
  category: string;
  difficulty: "Easy" | "Medium" | "Hard" | "Expert";
  related_skills?: string[];
  model_answer: string;
  answer_explanation?: string;
  why_asked?: string;
  evaluation_criteria: string[];
  common_mistakes: string[];
  follow_up_questions: string[];
  estimated_answer_time_minutes: number;
  skill_tag?: string | null;
  study_material?: InterviewStudyMaterial;
  practice_tasks?: string[];
  revision_notes?: string[];
}

export interface InterviewStudyMaterial {
  overview: string;
  what_you_need_to_know_first?: string[];
  definitions: { term: string; definition: string }[];
  skill_explanations?: { skill: string; explanation: string }[];
  principles: string[];
  key_concepts: string[];
  step_by_step_breakdown?: string[];
  explanations: string[];
  practical_example?: string;
  common_mistakes?: string[];
  how_to_answer_better?: string[];
  practice_exercises?: string[];
  revision_notes?: string[];
  related_concepts?: string[];
  estimated_reading_time_minutes?: number | null;
  question_id?: string | null;
  question_text?: string | null;
  answer_summary?: string | null;
  source_items_used?: string[];
  source_types_used?: string[];
  source_priority_used?: string[];
  core_idea?: string | null;
  what_this_question_tests?: string | null;
  technical_or_workflow_skills_covered?: string[];
  key_definitions?: { term: string; definition: string }[];
  key_principles?: string[];
  step_by_step_method?: string[];
  beginner_explanation?: string | null;
  intermediate_explanation?: string | null;
  advanced_explanation?: string | null;
  interview_application?: string | null;
  likely_follow_ups?: string[];
  saved_material_insight?: string | null;
  document_library_insight?: string | null;
  model_insight?: string | null;
  web_or_company_source_insight?: string | null;
  source_status?: Record<string, string>;
  fallback_status?: string | null;
}

export interface RoleOverview {
  role_name: string;
  summary: string;
  responsibilities: string[];
  required_skills: string[];
  what_employers_expect: string[];
  skill_clusters: string[];
}

// ---------------------------------------------------------------------------
// CV Builder
// ---------------------------------------------------------------------------

export interface GeneratedCVRead {
  id: string;
  user_id: string;
  target_job_id: string | null;
  name: string;
  template: string;
  section_config: { section_id: string; enabled: boolean }[];
  rendered_content: Record<string, unknown>;
  export_format_last_used: string | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Career Roadmap
// ---------------------------------------------------------------------------

export interface RoadmapRead {
  id: string;
  user_id: string;
  target_role: string;
  pace: string;
  starting_skill_level: string | null;
  milestones: RoadmapMilestoneRead[];
  generation_confidence: number | null;
  generation_citations: Citation[];
  created_at: string;
  updated_at: string;
}

export interface RoadmapMilestoneRead {
  id: string;
  title: string;
  timeframe_label: string | null;
  order_index: number;
  skills: RoadmapSkillRead[];
}

export interface RoadmapSkillRead {
  id: string;
  skill_name: string;
  importance: string | null;
  estimated_hours: number | null;
  status: "not_started" | "in_progress" | "completed";
  resources: ResourceLink[];
  study_material: StudyMaterial | null;
  practice_activities: PracticeActivities | null;
  lateral_connections: string[];
  order_index: number;
}

export interface ResourceLink {
  title: string;
  url: string;
  resource_type: string;
  estimated_hours: number | null;
}

export interface StudyMaterial {
  overview: string;
  key_concepts: string[];
  estimated_reading_time_minutes: number;
}

export interface PracticeActivities {
  exercises: string[];
  project_idea: string;
  self_assessment_questions: string[];
}

// ---------------------------------------------------------------------------
// Chatbot
// ---------------------------------------------------------------------------

export interface ChatSessionRead {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  n: number;
  title: string;
  url: string;
}

export interface ChatMessageRead {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  intent: string | null;
  action_result: Record<string, unknown>;
  confidence_score: number | null;
  suggested_followups: string[];
  created_at: string;
  updated_at: string;
}

export interface ChatTurnResponse {
  user_message: ChatMessageRead;
  assistant_message: ChatMessageRead;
}

export interface AgentMemoryRead {
  id: string;
  namespace: string;
  key: string;
  value: Record<string, unknown>;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Profile
// ---------------------------------------------------------------------------

export interface ProfileRead {
  id: string;
  user_id: string;
  full_name?: string | null;
  email?: string | null;
  location?: string | null;
  summary?: string | null;
  experience?: any[];
  education?: any[];
  phone: string | null;
  professional_headline: string | null;
  bio_summary: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  address_city: string | null;
  address_country: string | null;
  interests: string[];
  completeness_score: number;
  skills: SkillRead[];
  work_experiences: WorkExperienceRead[];
  educations: EducationRead[];
  projects: ProjectRead[];
  certifications: CertificationRead[];
  custom_sections: CustomSectionRead[];
  created_at: string;
  updated_at: string;
}

export interface SkillRead {
  id: string;
  name: string;
  skill_type: "technical" | "soft";
  category: string | null;
  proficiency: string | null;
  order_index: number;
}

export interface WorkExperienceRead {
  id: string;
  job_title: string;
  company_name: string;
  location: string | null;
  employment_type: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description_bullets: string[];
  order_index: number;
}

export interface EducationRead {
  id: string;
  degree: string;
  field_of_study: string | null;
  institution: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  grade: string | null;
  order_index: number;
}

export interface ProjectRead {
  id: string;
  title: string;
  description: string | null;
  technologies: string[];
  project_url: string | null;
  role: string | null;
  order_index: number;
}

export interface CertificationRead {
  id: string;
  name: string;
  issuing_organization: string;
  issue_date: string | null;
  credential_url: string | null;
  order_index: number;
}

export interface CustomSectionRead {
  id: string;
  title: string;
  section_type: "list" | "free_text" | "tags";
  free_text_content: string | null;
  tags: string[];
  order_index: number;
}

// ---------------------------------------------------------------------------
// Shared error envelope
// ---------------------------------------------------------------------------

export interface ApiError {
  error: boolean;
  code: string;
  message: string;
  details: Record<string, unknown>;
}
