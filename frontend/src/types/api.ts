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
  user_id: string;
  title: string;
  company_name: string;
  location: string | null;
  employment_type: string | null;
  salary_range: string | null;
  job_description: string | null;
  source_url: string | null;
  status: "saved" | "applied" | "interviewing" | "offered" | "rejected";
  match_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface InterviewPackRead {
  id: string;
  job_id: string;
  skill_clusters: SkillCluster[];
  generation_confidence: number | null;
  generation_citations: Citation[];
  created_at: string;
  updated_at: string;
}

export interface SkillCluster {
  skill_name: string;
  questions: InterviewQuestion[];
}

export interface InterviewQuestion {
  question: string;
  category: string;
  difficulty: "Easy" | "Medium" | "Hard" | "Expert";
  model_answer: string;
  evaluation_criteria: string[];
  common_mistakes: string[];
  follow_up_questions: string[];
  estimated_answer_time_minutes: number;
}

// ---------------------------------------------------------------------------
// CV Builder
// ---------------------------------------------------------------------------

export interface GeneratedCVRead {
  id: string;
  user_id: string;
  name: string;
  template: string;
  enabled_sections: string[];
  target_job_title: string | null;
  target_company: string | null;
  generation_confidence: number | null;
  pdf_url: string | null;
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
