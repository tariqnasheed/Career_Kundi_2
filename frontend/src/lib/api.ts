/**
 * lib/api.ts
 * ==========
 * Typed API client for the Careerkundi backend. All HTTP communication with
 * `/api/v1/**` goes through this module — nowhere in the app calls `fetch`
 * or `axios` directly.
 *
 * Architecture:
 *   - A single `axios` instance with the base URL, JSON content-type, and
 *     request/response interceptors configured once.
 *   - The request interceptor attaches the JWT access token (from localStorage
 *     via `auth.ts`) to every authenticated request.
 *   - The response interceptor surfaces structured API errors (the backend's
 *     `{"error": true, "code": "...", "message": "..."}` envelope) as typed
 *     `ApiError` throws so calling code can `catch (e: ApiError)` cleanly.
 *
 * Every API function is typed end-to-end — the return type mirrors the
 * backend's Pydantic response schema exactly (see `types/api.ts`).
 */

import axios, { type AxiosInstance, type AxiosResponse } from "axios";
import type {
  TokenResponse,
  UserRead,
  JobDiscoveryResult,
  SavedJobRead,
  InterviewPackRead,
  GeneratedCVRead,
  RoadmapRead,
  ChatSessionRead,
  ChatMessageRead,
  ChatTurnResponse,
  AgentMemoryRead,
  ProfileRead,
  ApiError,
  PlatformSubjectRead,
  PlatformSubjectEnvelope,
  PlatformSubjectListEnvelope,
  PlatformGoalCreate,
  PlatformGoalRead,
  PlatformGoalEnvelope,
  PlatformGoalListEnvelope,
} from "@/types/api";
import {
  buildSavedJobSearchPageRequest,
  type SavedJobSearchPageParams,
  type SavedJobSearchPageRead,
} from "./savedJobSearchPageRequest";

// The base URL is injected at build time from the VITE_API_BASE_URL env var;
// in local development the Vite proxy rewrites /api → localhost:8000, so the
// value here is just the origin (or empty for same-origin proxy).
const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "") + "/api/v1";

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

// We create a custom "axios instance" instead of using global axios.
// This ensures every request uses the correct base URL and timeout without repeating ourselves.
const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,  // 30 s — long enough for pipeline-heavy endpoints
});

// ---------------------------------------------------------------------------
// Request Interceptor: Attach the JWT token
// ---------------------------------------------------------------------------
// Before any request leaves the browser, this function runs. It grabs the
// access token from localStorage and adds it to the headers. This is how the
// backend knows who you are on every request.
http.interceptors.request.use((config) => {
  const token = localStorage.getItem("ck_access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ---------------------------------------------------------------------------
// Response Interceptor: Error formatting
// ---------------------------------------------------------------------------
// When the backend replies, this function runs before your component sees the data.
// If the backend returned an error, we format it neatly into our `ApiError` type.
http.interceptors.response.use(
  (res: AxiosResponse) => res,
  (err) => {
    const data = err.response?.data;
    const apiError: ApiError = {
      error: true,
      code: data?.code ?? "UNKNOWN_ERROR",
      message: data?.message ?? err.message ?? "An unexpected error occurred.",
      details: data?.details ?? {},
    };
    return Promise.reject(apiError);
  }
);

// ---------------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------------

export const authApi = {
  /** Exchange email + password for a JWT access + refresh token pair. */
  login: async (email: string, password: string): Promise<TokenResponse> => {
    // The backend expects a JSON body with {email, password} fields
    // (see backend/app/schemas/user.py UserLogin model).
    const res = await http.post<TokenResponse>("/auth/login", { email, password });
    return res.data;
  },

  /** Register a new user. */
  register: async (payload: {
    email: string;
    password: string;
    full_name?: string;
  }): Promise<UserRead> => {
    const res = await http.post<UserRead>("/auth/register", payload);
    return res.data;
  },

  /** Fetch the currently authenticated user's profile. */
  me: async (): Promise<UserRead> => {
    const res = await http.get<UserRead>("/auth/me");
    return res.data;
  },

  /** Exchange a valid refresh token for a new access + refresh token pair. */
  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const res = await http.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return res.data;
  },

  /** Send refresh token to backend to be blacklisted. */
  logout: async (refreshToken: string): Promise<void> => {
    await http.post("/auth/logout", { refresh_token: refreshToken });
  },
};

// ---------------------------------------------------------------------------
// Job Search endpoints
// ---------------------------------------------------------------------------

export const jobApi = {
  /** Search live job postings on the web (Google Jobs / job boards). */
  discover: async (params: {
    q?: string;
    location?: string;
    employment_type?: string;
    remote?: boolean;
    salary_min?: number;
    experience_level?: string;
    date_posted?: string;
    url?: string;
  }): Promise<JobDiscoveryResult[]> => {
    const res = await http.post<JobDiscoveryResult[]>("/job-search/discover", params);
    return res.data;
  },

  /** Filter the user's saved jobs (local library). */
  searchSaved: async (params: {
    q?: string;
    location?: string;
    employment_type?: string;
    remote?: boolean;
    page?: number;
  }): Promise<SavedJobRead[]> => {
    const res = await http.get<SavedJobRead[]>("/job-search/search", { params });
    return res.data;
  },

  /** Search the user's saved jobs with exact server pagination metadata. */
  searchSavedPage: async (
    params: SavedJobSearchPageParams,
  ): Promise<SavedJobSearchPageRead> => {
    const request = buildSavedJobSearchPageRequest(
      params,
    );

    const res = await http.get<SavedJobSearchPageRead>(
      request.url,
      {
        params: request.params,
      },
    );

    return res.data;
  },

  /** @deprecated Alias for searchSaved — filters saved jobs only, not the live web. */
  search: async (params: {
    q?: string;
    location?: string;
    employment_type?: string;
    remote?: boolean;
    page?: number;
  }): Promise<SavedJobRead[]> => jobApi.searchSaved(params),

  /** Import a job from URL or pasted text (full enrichment pipeline). */
  parse: async (payload: { url?: string; pasted_text?: string }): Promise<SavedJobRead> => {
    const res = await http.post<SavedJobRead>("/job-search/parse", payload);
    return res.data;
  },

  /** @deprecated Use parse() — kept for backwards compatibility */
  importUrl: async (url: string): Promise<SavedJobRead> => {
    return jobApi.parse({ url });
  },

  /** List the user's saved jobs. */
  list: async (): Promise<SavedJobRead[]> => {
    const res = await http.get<SavedJobRead[]>("/job-search/");
    return res.data;
  },

  /** Get a single saved job. */
  get: async (id: string): Promise<SavedJobRead> => {
    const res = await http.get<SavedJobRead>(`/job-search/${id}`);
    return res.data;
  },

  /** Save a reviewed job manually (after editing extracted fields). */
  save: async (jobData: Record<string, unknown>): Promise<SavedJobRead> => {
    const res = await http.post<SavedJobRead>("/job-search/", jobData);
    return res.data;
  },

  /** Update an existing saved job's fields from the job form. */
  update: async (id: string, jobData: Record<string, unknown>): Promise<SavedJobRead> => {
    const res = await http.patch<SavedJobRead>(`/job-search/${id}`, jobData);
    return res.data;
  },

  /** Update job status (applied, interviewing, etc.). */
  updateStatus: async (id: string, status: SavedJobRead["status"]): Promise<SavedJobRead> => {
    const res = await http.patch<SavedJobRead>(`/job-search/${id}/status`, { status });
    return res.data;
  },

  /** Delete a saved job. */
  delete: async (id: string): Promise<void> => {
    await http.delete(`/job-search/${id}`);
  },

  /** Generate an interview pack for a saved job. */
  generateInterviewPack: async (
    jobId: string,
    options?: { focus_areas?: string[]; difficulty?: string; include_study_material?: boolean },
  ): Promise<InterviewPackRead> => {
    const res = await http.post<InterviewPackRead>(`/job-search/${jobId}/interview-pack`, {
      include_study_material: true,
      ...options,
    });
    return res.data;
  },

  /** Download interview pack PDF (full | study_material | questions_answers). */
  downloadInterviewPackPdf: async (
    jobId: string,
    format: "pdf" | "study_material" | "questions_answers" = "pdf",
  ): Promise<Blob> => {
    const param = format === "pdf" ? "pdf" : format;
    const res = await http.get(`/job-search/${jobId}/interview-pack/export`, {
      params: { format: param },
      responseType: "blob",
    });
    return res.data;
  },

  /** Get an existing interview pack. */
  getInterviewPack: async (jobId: string): Promise<InterviewPackRead | null> => {
    try {
      const res = await http.get<InterviewPackRead>(`/job-search/${jobId}/interview-pack`);
      return res.data;
    } catch {
      return null;
    }
  },
};

// ---------------------------------------------------------------------------
// CV Builder endpoints
// ---------------------------------------------------------------------------

export const cvApi = {
  /** List the user's generated CVs. */
  list: async (): Promise<GeneratedCVRead[]> => {
    const res = await http.get<GeneratedCVRead[]>("/cv-builder/");
    return res.data;
  },

  /** Generate a new CV from the user's profile. */
  generate: async (payload: {
    name?: string;
    target_job_id?: string;
    template?: string;
    section_ids?: string[];
    tone?: "concise" | "detailed" | "executive";
    generation_mode?: "profile" | "role_targeted";
    target_role_title?: string;
    target_role_description?: string;
  }): Promise<GeneratedCVRead> => {
    const res = await http.post<GeneratedCVRead>("/cv-builder/generate", payload);
    return res.data;
  },

  /** Fetch a single saved CV (includes rendered_content for preview). */
  get: async (cvId: string): Promise<GeneratedCVRead> => {
    const res = await http.get<GeneratedCVRead>(`/cv-builder/${cvId}`);
    return res.data;
  },

  /** Download a generated CV as PDF (or DOCX / Markdown) via the export route. */
  downloadPdf: async (
    cvId: string,
    format: "pdf" | "docx" | "markdown" = "pdf",
    options?: { templateId?: string },
  ): Promise<Blob> => {
    const res = await http.get(`/cv-builder/${cvId}/export`, {
      params: {
        format,
        ...(options?.templateId ? { template_id: options.templateId } : {}),
      },
      responseType: "blob",
    });
    return res.data;
  },

  /** Delete a generated CV. */
  delete: async (cvId: string): Promise<void> => {
    await http.delete(`/cv-builder/${cvId}`);
  },
};

// ---------------------------------------------------------------------------
// Career Roadmap endpoints
// ---------------------------------------------------------------------------

export const roadmapApi = {
  /** List all roadmaps for the current user. */
  list: async (): Promise<RoadmapRead[]> => {
    const res = await http.get<RoadmapRead[]>("/roadmap/");
    return res.data;
  },

  /** Get a single roadmap with milestones and skills. */
  get: async (id: string): Promise<RoadmapRead> => {
    const res = await http.get<RoadmapRead>(`/roadmap/${id}`);
    return res.data;
  },

  /** Generate a new roadmap for a target role. */
  generate: async (payload: {
    target_role: string;
    pace?: "fast" | "normal" | "thorough";
    starting_skill_level?: string;
    personalization_inputs?: Record<string, unknown>;
  }): Promise<RoadmapRead> => {
    const res = await http.post<RoadmapRead>("/roadmap/generate", payload);
    return res.data;
  },

  /** Regenerate an existing roadmap. */
  regenerate: async (id: string, payload: {
    target_role: string;
    pace?: string;
  }): Promise<RoadmapRead> => {
    const res = await http.post<RoadmapRead>(`/roadmap/${id}/regenerate`, payload);
    return res.data;
  },

  /** Update a skill's progress status. */
  updateSkillStatus: async (
    roadmapId: string,
    skillId: string,
    status: "not_started" | "in_progress" | "completed"
  ): Promise<void> => {
    await http.patch(`/roadmap/${roadmapId}/skills/${skillId}/status`, { status });
  },

  /** Refresh one skill's resources and study material. */
  refreshSkill: async (roadmapId: string, skillId: string) => {
    const res = await http.post(`/roadmap/${roadmapId}/skills/${skillId}/refresh`);
    return res.data;
  },

  /** Delete a roadmap. */
  delete: async (id: string): Promise<void> => {
    await http.delete(`/roadmap/${id}`);
  },
};

// ---------------------------------------------------------------------------
// Chatbot endpoints
// ---------------------------------------------------------------------------

export const chatbotApi = {
  /** List the user's chat sessions. */
  listSessions: async (): Promise<ChatSessionRead[]> => {
    const res = await http.get<ChatSessionRead[]>("/chatbot/sessions");
    return res.data;
  },

  /** Create a new chat session. */
  createSession: async (title?: string): Promise<ChatSessionRead> => {
    const res = await http.post<ChatSessionRead>("/chatbot/sessions", {
      title: title ?? "New conversation",
    });
    return res.data;
  },

  /** Get a session with its full message history. */
  getSession: async (id: string): Promise<ChatSessionRead & { messages: ChatMessageRead[] }> => {
    const res = await http.get<ChatSessionRead & { messages: ChatMessageRead[] }>(
      `/chatbot/sessions/${id}`
    );
    return res.data;
  },

  /** Delete a session. */
  deleteSession: async (id: string): Promise<void> => {
    await http.delete(`/chatbot/sessions/${id}`);
  },

  /** Send a user message and receive the assistant's reply. */
  sendMessage: async (sessionId: string, content: string): Promise<ChatTurnResponse> => {
    const res = await http.post<ChatTurnResponse>(
      `/chatbot/sessions/${sessionId}/messages`,
      { content }
    );
    return res.data;
  },

  /** Regenerate the assistant's reply for a given user message. */
  redoMessage: async (sessionId: string, messageId: string): Promise<ChatMessageRead> => {
    const res = await http.post<ChatMessageRead>(
      `/chatbot/sessions/${sessionId}/messages/${messageId}/redo`
    );
    return res.data;
  },

  /** List the user's long-term memory facts. */
  listMemory: async (): Promise<AgentMemoryRead[]> => {
    const res = await http.get<AgentMemoryRead[]>("/chatbot/memory");
    return res.data;
  },

  /** Delete a specific memory fact. */
  forgetMemory: async (namespace: string, key: string): Promise<void> => {
    await http.delete(`/chatbot/memory/${namespace}/${key}`);
  },
};

// ---------------------------------------------------------------------------
// Profile endpoints
// ---------------------------------------------------------------------------

export const profileApi = {
  get: async (): Promise<ProfileRead> => {
    const res = await http.get<ProfileRead>("/profile");
    return res.data;
  },
  update: async (data: Partial<ProfileRead>): Promise<ProfileRead> => {
    const res = await http.patch<ProfileRead>("/profile", data);
    return res.data;
  },
};

// ---------------------------------------------------------------------------
// Badge endpoints
// ---------------------------------------------------------------------------

export const badgeApi = {
  getAll: async () => {
    const res = await http.get("/badges/me");
    return res.data;
  },
  getEarned: async () => {
    const res = await http.get("/badges/me/earned");
    return res.data;
  },
  getPendingCelebrations: async () => {
    const res = await http.get("/badges/me/pending-celebrations");
    return res.data;
  },
  getStats: async () => {
    const res = await http.get("/badges/me/stats");
    return res.data;
  },
  dismissCelebration: async (badgeId: string) => {
    await http.post(`/badges/me/celebrations/${badgeId}/dismiss`);
  },
  getDefinitions: async () => {
    const res = await http.get("/badges/definitions");
    return res.data;
  },
  markJobOffer: async () => {
    const res = await http.post("/badges/me/mark-offer");
    return res.data;
  },
};

// ---------------------------------------------------------------------------
// Queue endpoints
// ---------------------------------------------------------------------------

export const queueApi = {
  enqueue: async (payload: { job_type: string; label?: string; input_params?: Record<string, unknown> }) => {
    const res = await http.post("/queue/jobs", payload);
    return res.data;
  },
  list: async () => {
    const res = await http.get("/queue/jobs");
    return res.data;
  },
  get: async (id: string) => {
    const res = await http.get(`/queue/jobs/${id}`);
    return res.data;
  },
  cancel: async (id: string) => {
    await http.delete(`/queue/jobs/${id}`);
  },
};

// ---------------------------------------------------------------------------
// Apply endpoints
// ---------------------------------------------------------------------------

export const applyApi = {
  extractUrl: async (url: string) => {
    const res = await http.post("/apply/extract-url", { url });
    return res.data;
  },
  startApply: async (jobId: string, payload: { cv_id?: string; cover_letter_requested?: boolean }) => {
    const res = await http.post(`/apply/jobs/${jobId}/apply`, payload);
    return res.data;
  },
  confirm: async (applicationId: string) => {
    const res = await http.patch(`/apply/applications/${applicationId}/confirm`);
    return res.data;
  },
  listApplications: async () => {
    const res = await http.get("/apply/applications");
    return res.data;
  },
};

// ---------------------------------------------------------------------------
// Platform foundation endpoints (0050-PF8 envelopes: { data } / { data, meta })
// ---------------------------------------------------------------------------

export const platformApi = {
  /** List Career Subjects owned by the authenticated user. */
  listPlatformSubjects: async (): Promise<PlatformSubjectRead[]> => {
    const res = await http.get<PlatformSubjectListEnvelope>("/platform/subjects");
    return res.data.data;
  },

  /** Create a Career Subject (no request body — ownership from auth). */
  createPlatformSubject: async (): Promise<PlatformSubjectRead> => {
    const res = await http.post<PlatformSubjectEnvelope>("/platform/subjects");
    return res.data.data;
  },

  /** Read one Career Subject by id. */
  getPlatformSubject: async (subjectId: string): Promise<PlatformSubjectRead> => {
    const res = await http.get<PlatformSubjectEnvelope>(`/platform/subjects/${subjectId}`);
    return res.data.data;
  },

  /** List Goals for an owned Career Subject. */
  listPlatformGoals: async (subjectId: string): Promise<PlatformGoalRead[]> => {
    const res = await http.get<PlatformGoalListEnvelope>(
      `/platform/subjects/${subjectId}/goals`,
    );
    return res.data.data;
  },

  /** Create a Goal under an owned Career Subject. */
  createPlatformGoal: async (
    subjectId: string,
    payload: PlatformGoalCreate,
  ): Promise<PlatformGoalRead> => {
    const res = await http.post<PlatformGoalEnvelope>(
      `/platform/subjects/${subjectId}/goals`,
      payload,
    );
    return res.data.data;
  },
};

export default http;
