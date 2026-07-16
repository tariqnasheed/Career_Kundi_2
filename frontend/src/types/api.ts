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
  /** CVB-F2 gallery id when persisted; null on older CVs → UI defaults to minimal-corporate */
  studio_template_id?: string | null;
  section_config: CVSectionConfigItem[];
  rendered_content: Record<string, unknown>;
  export_format_last_used: string | null;
  created_at: string;
  updated_at: string;
}

/** Content section row or reserved `_studio` / `_taxonomy` meta rows. */
export interface CVSectionConfigItem {
  section_id: string;
  enabled: boolean;
  studio_template_id?: string;
  /** 0051-F8 advisory taxonomy fields when section_id === "_taxonomy" */
  target_role_text?: string | null;
  matched_role_id?: string | null;
  matched_skill_id?: string | null;
  normalized_text?: string | null;
  source?: TaxonomySourceType | string | null;
  confidence?: TaxonomyConfidenceLevel | string | null;
  explanation?: string | null;
  accepted_by_user?: boolean;
  kept_freeform?: boolean;
  matched_role_title?: string | null;
}

/** Optional Role Intelligence payload sent on CV generate/update (0051-F8). */
export interface CVTaxonomyMeta {
  target_role_text?: string | null;
  matched_role_id?: string | null;
  matched_skill_id?: string | null;
  normalized_text?: string | null;
  source?: TaxonomySourceType | string | null;
  confidence?: TaxonomyConfidenceLevel | string | null;
  explanation?: string | null;
  accepted_by_user?: boolean;
  kept_freeform?: boolean;
  matched_role_title?: string | null;
}

// ---------------------------------------------------------------------------
// Career Roadmap
// ---------------------------------------------------------------------------

/** Matches backend `RoadmapRead` — no roadmap-level status field; progress is skill-based. */
export interface RoadmapRead {
  id: string;
  /** Present on some clients historically; backend schema does not require it on read. */
  user_id?: string;
  target_role: string;
  pace: "fast" | "normal" | "thorough" | string;
  starting_skill_level: string | null;
  personalization_inputs?: Record<string, unknown> & {
    _taxonomy?: RoadmapTaxonomyMeta | null;
  };
  milestones: RoadmapMilestoneRead[];
  generation_confidence: number | null;
  generation_citations: Citation[];
  created_at: string;
  updated_at: string;
}

/** Optional Role Intelligence nested under personalization_inputs._taxonomy (0051-F10). */
export interface RoadmapTaxonomyMeta {
  target_role_text?: string | null;
  matched_role_id?: string | null;
  matched_skill_id?: string | null;
  normalized_text?: string | null;
  source?: TaxonomySourceType | string | null;
  confidence?: TaxonomyConfidenceLevel | string | null;
  explanation?: string | null;
  accepted_by_user?: boolean;
  kept_freeform?: boolean;
  suggested_skill_ids?: string[];
  suggested_skill_labels?: string[];
  matched_role_title?: string | null;
}

export interface RoadmapMilestoneRead {
  id: string;
  title: string;
  timeframe_label: string | null;
  order_index?: number;
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
  order_index?: number;
}

export interface ResourceLink {
  title: string;
  url: string | null;
  resource_type: string;
  estimated_hours?: number | null;
  source?: string | null;
  verified?: boolean;
}

export interface RoadmapKeyConcept {
  term: string;
  definition: string;
}

export interface StudyMaterial {
  overview: string;
  key_concepts: string[];
  estimated_reading_time_minutes?: number | null;
  // Enriched, Bloom-aligned learning content
  why_it_matters?: string;
  prerequisites?: string[];
  learning_objectives?: string[];
  beginner_explanation?: string;
  intermediate_explanation?: string;
  advanced_explanation?: string;
  concepts?: RoadmapKeyConcept[];
  worked_example?: string;
  common_mistakes?: string[];
  revision_notes?: string[];
}

export interface RoadmapFlashcard {
  front: string;
  back: string;
}

export interface RoadmapQuizQuestion {
  question: string;
  options: string[];
  answer_index: number;
  explanation?: string;
}

export interface RoadmapProject {
  title: string;
  brief: string;
  steps?: string[];
  deliverable?: string;
  difficulty?: "beginner" | "intermediate" | "advanced";
}

export interface PracticeActivities {
  exercises: string[];
  project_idea?: string | null;
  self_assessment_questions: string[];
  // Enriched practice modalities
  flashcards?: RoadmapFlashcard[];
  quizzes?: RoadmapQuizQuestion[];
  projects?: RoadmapProject[];
  reflection_questions?: string[];
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
// Platform foundation (0050-PF8 / PF11)
// ---------------------------------------------------------------------------

export interface PlatformListMeta {
  count: number;
}

export interface PlatformSubjectRead {
  id: string;
  owner_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface PlatformSubjectEnvelope {
  data: PlatformSubjectRead;
}

export interface PlatformSubjectListEnvelope {
  data: PlatformSubjectRead[];
  meta: PlatformListMeta;
}

export interface PlatformGoalCreate {
  goal_kind: string;
  title: string;
  description?: string | null;
  status?: string;
}

export interface PlatformGoalRead {
  id: string;
  subject_id: string;
  goal_kind: string;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PlatformGoalEnvelope {
  data: PlatformGoalRead;
}

export interface PlatformGoalListEnvelope {
  data: PlatformGoalRead[];
  meta: PlatformListMeta;
}

// ---------------------------------------------------------------------------
// Taxonomy (0051-F5) — mirrors backend/app/schemas/taxonomy.py
// ---------------------------------------------------------------------------

export type TaxonomySourceType =
  | "user_provided"
  | "profile_supported"
  | "document_supported"
  | "job_description_supported"
  | "external_taxonomy_reference"
  | "model_inferred"
  | "fallback_default"
  | "unknown";

export type TaxonomyConfidenceLevel =
  | "verified"
  | "evidence_backed"
  | "profile_supported"
  | "suggested"
  | "inferred"
  | "default"
  | "unknown";

export type TaxonomyPathwayType =
  | "skill_gap"
  | "career_switch"
  | "graduate_launch"
  | "interview_preparation"
  | "job_application"
  | "study_education"
  | "professional_certification"
  | "public_sector"
  | "regional_readiness"
  | "portfolio_project"
  | "promotion_growth";

export interface TaxonomyHealthRead {
  available: boolean;
  catalog_name: string;
  domain_count: number;
  role_count: number;
  skill_count: number;
  pathway_type_count: number;
  external_dataset_ingestion: boolean;
}

export interface TaxonomyPathwayTypeRead {
  id: TaxonomyPathwayType | string;
  label: string;
  description: string | null;
}

export interface TaxonomyMatchRequest {
  input_text: string;
  source?: TaxonomySourceType | null;
  confidence?: TaxonomyConfidenceLevel | null;
}

export interface TaxonomyMatchRead {
  input_text: string;
  normalized_text: string;
  matched_role_id: string | null;
  matched_skill_id: string | null;
  source: TaxonomySourceType;
  confidence: TaxonomyConfidenceLevel;
  explanation: string;
}

export interface TaxonomyRoleRead {
  id: string;
  title: string;
  aliases: string[];
  description: string;
  common_skills: string[];
  related_roles: string[];
  source: TaxonomySourceType;
  confidence: TaxonomyConfidenceLevel;
}

export interface TaxonomySkillRead {
  id: string;
  label: string;
  aliases: string[];
  evidence_examples: string[];
  tool_examples: string[];
  source: TaxonomySourceType;
  confidence: TaxonomyConfidenceLevel;
}

export interface TaxonomyRoleSkillsRead {
  role_id: string;
  skills: TaxonomySkillRead[];
}

export interface TaxonomyRelatedRolesRead {
  role_id: string;
  related_roles: TaxonomyRoleRead[];
}

export interface TaxonomyErrorRead {
  message: string;
  code: string;
}

// ---------------------------------------------------------------------------
// Passport (0052-F3/F4) — mirrors backend/app/schemas/passport.py
// 0052-F7: Profile / CV Builder / Roadmap may consume PassportRead via passportApi.get only (no mutation clients).
// ---------------------------------------------------------------------------

export type PassportVisibility = "private";

export type PassportSectionKey =
  | "profile"
  | "experience"
  | "education"
  | "projects"
  | "skills"
  | "credentials"
  | "targets";

export type PassportTaxonomyKind = "role" | "skill";

export type PassportCredentialType =
  | "certification"
  | "license"
  | "course_certificate"
  | "education_award"
  | "professional_membership"
  | "other";

export type PassportSeniorityLevel =
  | "entry"
  | "junior"
  | "mid"
  | "senior"
  | "lead"
  | "principal"
  | "manager"
  | "director"
  | "executive"
  | "unknown";

export interface PassportRecordMetaRead {
  source_status: string;
  support_status: "not_provided" | "profile_supported" | string;
  verification_status: "unverified" | string;
}

export interface PassportTaxonomyReference {
  kind: PassportTaxonomyKind;
  input_text: string;
  normalized_text: string | null;
  taxonomy_id: string | null;
  source: TaxonomySourceType;
  confidence: TaxonomyConfidenceLevel;
  accepted_by_user: boolean;
}

export interface PassportSectionPreference {
  section: PassportSectionKey;
  order_index: number;
  enabled: boolean;
}

export interface PassportProfileRead {
  phone: string | null;
  date_of_birth: string | null;
  nationality: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  twitter_url: string | null;
  other_social_links: Record<string, unknown>[];
  address_city: string | null;
  address_state: string | null;
  address_country: string | null;
  photo_url: string | null;
  professional_headline: string | null;
  bio_summary: string | null;
  declaration_text: string | null;
  references_available_on_request: boolean;
  interests: string[];
  record_meta: PassportRecordMetaRead;
}

export interface PassportExperienceRead {
  id: string;
  created_at: string;
  updated_at: string;
  job_title: string;
  company_name: string;
  company_url: string | null;
  location: string | null;
  employment_type: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description_bullets: string[];
  order_index: number;
  role_taxonomy: PassportTaxonomyReference | null;
  record_meta: PassportRecordMetaRead;
}

export interface PassportEducationRead {
  id: string;
  created_at: string;
  updated_at: string;
  degree: string;
  field_of_study: string | null;
  institution: string;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  grade: string | null;
  description_bullets: string[];
  relevant_coursework: string[];
  order_index: number;
  record_meta: PassportRecordMetaRead;
}

export interface PassportProjectRead {
  id: string;
  created_at: string;
  updated_at: string;
  title: string;
  description: string | null;
  technologies: string[];
  project_url: string | null;
  start_date: string | null;
  end_date: string | null;
  role: string | null;
  key_achievements: string[];
  order_index: number;
  skill_taxonomy: PassportTaxonomyReference[];
  record_meta: PassportRecordMetaRead;
}

export interface PassportSkillRead {
  id: string;
  created_at: string;
  updated_at: string;
  name: string;
  skill_type: string;
  category: string | null;
  proficiency: string | null;
  order_index: number;
  taxonomy: PassportTaxonomyReference | null;
  record_meta: PassportRecordMetaRead;
}

export interface PassportCredentialRead {
  id: string;
  created_at: string;
  updated_at: string;
  credential_type: PassportCredentialType;
  name: string;
  issuing_organization: string;
  issue_date: string | null;
  expiry_date: string | null;
  credential_id: string | null;
  credential_url: string | null;
  order_index: number;
  record_meta: PassportRecordMetaRead;
}

export interface PassportTargetRead {
  id: string;
  created_at: string;
  updated_at: string;
  target_role_text: string;
  role_taxonomy: PassportTaxonomyReference | null;
  pathway_type: TaxonomyPathwayType | null;
  target_country: string | null;
  target_region: string | null;
  target_industry: string | null;
  target_seniority: PassportSeniorityLevel | null;
  time_horizon: string | null;
  priority: number;
  order_index: number;
  record_meta: PassportRecordMetaRead;
}

export interface PassportRead {
  id: string;
  subject_id: string | null;
  display_name: string | null;
  headline: string | null;
  summary: string | null;
  visibility: PassportVisibility | string;
  version: number;
  section_preferences: PassportSectionPreference[];
  profile: PassportProfileRead;
  experiences: PassportExperienceRead[];
  education: PassportEducationRead[];
  projects: PassportProjectRead[];
  skills: PassportSkillRead[];
  credentials: PassportCredentialRead[];
  targets: PassportTargetRead[];
  created_at: string;
  updated_at: string;
}

export interface PassportEnvelope {
  data: PassportRead;
}

// ---------------------------------------------------------------------------
// Passport mutation payloads (0052-F5) — Profile / Experience / Education only
// ---------------------------------------------------------------------------

export interface PassportProfilePatchRequest {
  expected_version: number;
  phone?: string | null;
  date_of_birth?: string | null;
  nationality?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
  twitter_url?: string | null;
  other_social_links?: Record<string, unknown>[] | null;
  address_city?: string | null;
  address_state?: string | null;
  address_country?: string | null;
  photo_url?: string | null;
  professional_headline?: string | null;
  bio_summary?: string | null;
  declaration_text?: string | null;
  references_available_on_request?: boolean | null;
  interests?: string[] | null;
}

export interface PassportExperienceCreateRequest {
  expected_version: number;
  job_title: string;
  company_name: string;
  company_url?: string | null;
  location?: string | null;
  employment_type?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  description_bullets?: string[];
  order_index?: number;
  role_taxonomy?: PassportTaxonomyReference | null;
}

export interface PassportExperiencePatchRequest {
  expected_version: number;
  job_title?: string | null;
  company_name?: string | null;
  company_url?: string | null;
  location?: string | null;
  employment_type?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean | null;
  description_bullets?: string[] | null;
  order_index?: number | null;
  role_taxonomy?: PassportTaxonomyReference | null;
}

export interface PassportEducationCreateRequest {
  expected_version: number;
  degree: string;
  field_of_study?: string | null;
  institution: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean;
  grade?: string | null;
  description_bullets?: string[];
  relevant_coursework?: string[];
  order_index?: number;
}

export interface PassportEducationPatchRequest {
  expected_version: number;
  degree?: string | null;
  field_of_study?: string | null;
  institution?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current?: boolean | null;
  grade?: string | null;
  description_bullets?: string[] | null;
  relevant_coursework?: string[] | null;
  order_index?: number | null;
}

export interface PassportReorderRequest {
  expected_version: number;
  ordered_ids: string[];
}

// ---------------------------------------------------------------------------
// Passport mutation payloads (0052-F6) — Projects / Skills / Credentials / Targets
// ---------------------------------------------------------------------------

export interface PassportProjectCreateRequest {
  expected_version: number;
  title: string;
  description?: string | null;
  technologies?: string[];
  project_url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  role?: string | null;
  key_achievements?: string[];
  order_index?: number;
  skill_taxonomy?: PassportTaxonomyReference[];
}

export interface PassportProjectPatchRequest {
  expected_version: number;
  title?: string | null;
  description?: string | null;
  technologies?: string[] | null;
  project_url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  role?: string | null;
  key_achievements?: string[] | null;
  order_index?: number | null;
  skill_taxonomy?: PassportTaxonomyReference[] | null;
}

export interface PassportSkillCreateRequest {
  expected_version: number;
  name: string;
  skill_type?: string;
  category?: string | null;
  proficiency?: string | null;
  order_index?: number;
  taxonomy?: PassportTaxonomyReference | null;
}

export interface PassportSkillPatchRequest {
  expected_version: number;
  name?: string | null;
  skill_type?: string | null;
  category?: string | null;
  proficiency?: string | null;
  order_index?: number | null;
  taxonomy?: PassportTaxonomyReference | null;
}

export interface PassportCredentialCreateRequest {
  expected_version: number;
  credential_type?: PassportCredentialType;
  name: string;
  issuing_organization: string;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
  order_index?: number;
}

export interface PassportCredentialPatchRequest {
  expected_version: number;
  credential_type?: PassportCredentialType | null;
  name?: string | null;
  issuing_organization?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
  order_index?: number | null;
}

export interface PassportTargetCreateRequest {
  expected_version: number;
  target_role_text: string;
  role_taxonomy?: PassportTaxonomyReference | null;
  pathway_type?: TaxonomyPathwayType | null;
  target_country?: string | null;
  target_region?: string | null;
  target_industry?: string | null;
  target_seniority?: PassportSeniorityLevel | null;
  time_horizon?: string | null;
  priority?: number;
  order_index?: number;
}

export interface PassportTargetPatchRequest {
  expected_version: number;
  target_role_text?: string | null;
  role_taxonomy?: PassportTaxonomyReference | null;
  pathway_type?: TaxonomyPathwayType | null;
  target_country?: string | null;
  target_region?: string | null;
  target_industry?: string | null;
  target_seniority?: PassportSeniorityLevel | null;
  time_horizon?: string | null;
  priority?: number | null;
  order_index?: number | null;
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
