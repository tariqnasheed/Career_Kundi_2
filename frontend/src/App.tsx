/**
 * App.tsx – Root router
 *
 * Route hierarchy:
 *   /              → redirect to /dashboard (if auth) or /login
 *   /login         → LoginPage (public)
 *   /register      → RegisterPage (public)
 *   /              → AppShell (requires auth)
 *     /dashboard
 *     /jobs
 *     /interview-pack
 *     /cv-builder
 *     /roadmap
 *     /roadmaps (alias → same Roadmap page)
 *     /achievements
 *     /profile
 *     /settings
 *     /platform
 *     /passport
 *     /evidence
 *     /chatbot
 *
 * Auth guard: <PrivateRoute /> checks useAuthStore().isAuthenticated.
 * While `isLoading` is true (session restore in progress) it shows a
 * full-screen spinner so there's no redirect flicker.
 */

import { useEffect } from "react";
import { Routes, Route, Navigate, Outlet, useSearchParams } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { useAuthStore } from "./store/auth";
import { Spinner } from "./components/ui/Spinner";

/* ── Lazy page imports ──────────────────────────────────────────── */
import { lazy, Suspense } from "react";

const LandingPage      = lazy(() => import("./pages/LandingPage"));
const LoginPage        = lazy(() => import("./pages/LoginPage"));
const RegisterPage     = lazy(() => import("./pages/RegisterPage"));
const DashboardPage    = lazy(() => import("./pages/DashboardPage"));
const JobSearchPage    = lazy(() => import("./pages/JobSearchPage"));
const CVBuilderPage    = lazy(() => import("./pages/CVBuilderPage"));
const RoadmapPage      = lazy(() => import("./pages/RoadmapPage"));
const AchievementsPage = lazy(() => import("./pages/AchievementsPage"));
const ProfilePage      = lazy(() => import("./pages/ProfilePage"));
const SettingsPage     = lazy(() => import("./pages/SettingsPage"));
const PlatformPage     = lazy(() => import("./pages/PlatformPage"));
const PassportPage     = lazy(() => import("./features/passport/PassportPage"));
const EvidenceLibraryPage = lazy(() => import("./pages/EvidenceLibraryPage"));
const ChatbotPage      = lazy(() => import("./pages/ChatbotPage"));
const NotFoundPage     = lazy(() => import("./pages/NotFoundPage"));

/* ── Page loading fallback ──────────────────────────────────────── */
function PageSpinner() {
  return (
    <div style={{
      minHeight: "60vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}>
      <Spinner size="lg" />
    </div>
  );
}

/* ── Auth guard ─────────────────────────────────────────────────── */
function PrivateRoute() {
  const { isAuthenticated, isLoading } = useAuthStore();
  
  // 1. If we are still checking local storage to see if they are logged in, 
  //    show a spinner instead of redirecting them immediately.
  if (isLoading) return <PageSpinner />;
  
  // 2. If they are definitely NOT logged in, kick them out to the login page.
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  
  // 3. Otherwise, render whatever child route they requested.
  return <Outlet />;
}

/* ── Public-only guard (redirect logged-in users away) ──────────── */
function PublicRoute() {
  const { isAuthenticated, isLoading } = useAuthStore();
  if (isLoading) return <PageSpinner />;
  
  // If a logged-in user tries to visit the login page, redirect them to the dashboard.
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

/* ── Redirect legacy interview-pack URLs ─────────────────────────── */
function InterviewPackRedirect() {
  const [params] = useSearchParams();
  const jobId = params.get("jobId");
  return <Navigate to={jobId ? `/jobs?jobId=${jobId}` : "/jobs"} replace />;
}

/* ── Root App ───────────────────────────────────────────────────── */
export default function App() {
  // We call init() once when the app starts. This checks localStorage for 
  // saved tokens so the user doesn't have to log in again on every refresh.
  const init = useAuthStore((s) => s.init);
  useEffect(() => { init(); }, [init]);

  return (
    // Suspense handles the loading state while the lazy-loaded pages download.
    <Suspense fallback={<PageSpinner />}>
      <Routes>
        {/* Public routes — only accessible if you are NOT logged in */}
        <Route element={<PublicRoute />}>
          <Route path="/"         element={<LandingPage />} />
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* Private routes — only accessible if you ARE logged in.
            They are also wrapped in AppShell, which provides the sidebar and header. */}
        <Route element={<PrivateRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard"       element={<DashboardPage />} />
            <Route path="/jobs"            element={<JobSearchPage />} />
            <Route path="/interview-pack"  element={<InterviewPackRedirect />} />
            <Route path="/cv-builder"      element={<CVBuilderPage />} />
            <Route path="/roadmap"         element={<RoadmapPage />} />
            {/* Minimal alias — same page as /roadmap (ROAD-F1); plural IA remains planned */}
            <Route path="/roadmaps"        element={<RoadmapPage />} />
            <Route path="/achievements"    element={<AchievementsPage />} />
            <Route path="/profile"         element={<ProfilePage />} />
            <Route path="/settings"        element={<SettingsPage />} />
            <Route path="/platform"        element={<PlatformPage />} />
            <Route path="/passport"        element={<PassportPage />} />
            <Route path="/evidence"        element={<EvidenceLibraryPage />} />
            <Route path="/chatbot"         element={<ChatbotPage />} />
          </Route>
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
