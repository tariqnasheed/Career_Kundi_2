/**
 * store/auth.ts
 * =============
 * Zustand auth store — the single source of truth for authentication state.
 *
 * What this file does:
 *   - Stores the current user object and JWT tokens (access + refresh)
 *   - Provides login / register / logout actions any component can call
 *   - On app boot, checks if a saved token exists and restores the session
 *   - Implements silent token refresh: when the access token expires (15 min),
 *     the refresh token (valid 7 days) automatically fetches a new pair
 *
 * Where it fits:
 *   - Imported by App.tsx (calls `init()` on mount)
 *   - Imported by any component that needs `useAuthStore().user`
 *   - The access token is also read by lib/api.ts's axios interceptor
 *     to attach `Authorization: Bearer <token>` to every API request
 *
 * How it connects:
 *   - Calls authApi from lib/api.ts for login/register/me/refresh
 *   - Tokens are persisted to localStorage so page refreshes don't log out
 *
 * Why Zustand?
 *   It's tiny (1.1kb), has zero boilerplate, and doesn't require wrapping
 *   the whole tree in a Provider. Any component can call `useAuthStore()`
 *   and get the same singleton state.
 */

import { create } from "zustand";
import { authApi } from "@/lib/api";
import type { UserRead } from "@/types/api";

// ---------------------------------------------------------------------------
// Interface — describes the shape of the auth store's state + actions
// ---------------------------------------------------------------------------
interface AuthState {
  /** The currently logged-in user's profile, or null if not authenticated. */
  user: UserRead | null;
  /** The short-lived JWT access token (15 min lifetime). */
  token: string | null;
  /** The long-lived JWT refresh token (7 day lifetime). */
  refreshToken: string | null;
  /** True while the initial session-restore call (/auth/me) is in flight. */
  isLoading: boolean;
  /** Convenience boolean: true when a valid user session exists. */
  isAuthenticated: boolean;

  /** Called once on app mount to restore session from localStorage. */
  init: () => Promise<void>;
  /** Log in with email + password, then fetch user profile. */
  login: (email: string, password: string) => Promise<void>;
  /** Register a new account, then auto-login. */
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  /** Clear all tokens and user data (client-side logout). */
  logout: () => void;
  /** Exchange the refresh token for a new access + refresh token pair. */
  silentRefresh: () => Promise<boolean>;
}

// ---------------------------------------------------------------------------
// localStorage keys — where we persist tokens across page refreshes
// ---------------------------------------------------------------------------
const ACCESS_TOKEN_KEY = "ck_access_token";
const REFRESH_TOKEN_KEY = "ck_refresh_token";

// ---------------------------------------------------------------------------
// Helper: safely read localStorage (avoids crashes in SSR/test contexts)
// ---------------------------------------------------------------------------
function safeGetItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    // localStorage is unavailable (SSR, some test environments)
    return null;
  }
}

// ---------------------------------------------------------------------------
// The Zustand store — created once, shared by every component that imports it
// ---------------------------------------------------------------------------
export const useAuthStore = create<AuthState>((set, get) => ({
  // --- Initial state -------------------------------------------------------
  // Note: we do NOT read localStorage here at module-import time (issue #16).
  // Instead, `init()` handles that safely after the component mounts.
  user: null,
  token: null,
  refreshToken: null,
  isLoading: true,
  isAuthenticated: false,

  // -------------------------------------------------------------------------
  // init — called once from App.tsx's useEffect on mount
  // -------------------------------------------------------------------------
  init: async () => {
    // Try to restore a session from a previously saved access token
    const token = safeGetItem(ACCESS_TOKEN_KEY);
    const refreshToken = safeGetItem(REFRESH_TOKEN_KEY);

    if (!token) {
      // No saved token → user needs to log in
      set({ isLoading: false, isAuthenticated: false });
      return;
    }

    try {
      // Verify the token is still valid by calling GET /auth/me
      const user = await authApi.me();
      set({ user, token, refreshToken, isLoading: false, isAuthenticated: true });
    } catch {
      // Token expired or invalid — try silent refresh before giving up
      if (refreshToken) {
        const refreshed = await get().silentRefresh();
        if (refreshed) return; // silentRefresh already called set()
      }
      // Refresh also failed — clear everything and show login
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      set({ user: null, token: null, refreshToken: null, isLoading: false, isAuthenticated: false });
    }
  },

  // -------------------------------------------------------------------------
  // login — exchange email + password for tokens, then fetch user profile
  // -------------------------------------------------------------------------
  login: async (email, password) => {
    // Call POST /auth/login → returns {access_token, refresh_token, token_type}
    const { access_token, refresh_token } = await authApi.login(email, password);

    // Persist both tokens so the session survives page refreshes
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

    // Fetch the full user profile now that we have a valid token
    const user = await authApi.me();
    set({ user, token: access_token, refreshToken: refresh_token, isAuthenticated: true });
  },

  // -------------------------------------------------------------------------
  // register — create account, then auto-login so the user lands on dashboard
  // -------------------------------------------------------------------------
  register: async (email, password, fullName) => {
    // Step 1: Create the account (POST /auth/register)
    await authApi.register({ email, password, full_name: fullName ?? "" });

    // Step 2: Immediately log in with the new credentials
    const { access_token, refresh_token } = await authApi.login(email, password);
    localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

    // Step 3: Fetch the user profile
    const user = await authApi.me();
    set({ user, token: access_token, refreshToken: refresh_token, isAuthenticated: true });
  },

  // -------------------------------------------------------------------------
  // logout — clear all state and tokens (and notify backend to blacklist)
  // -------------------------------------------------------------------------
  logout: async () => {
    const refreshToken = get().refreshToken ?? safeGetItem(REFRESH_TOKEN_KEY);
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch {
        // Ignore network errors on logout — we still want to clear local state
      }
    }
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    set({ user: null, token: null, refreshToken: null, isAuthenticated: false });
  },

  // -------------------------------------------------------------------------
  // silentRefresh — called when the access token expires (401 from API)
  // -------------------------------------------------------------------------
  silentRefresh: async () => {
    const currentRefreshToken = get().refreshToken ?? safeGetItem(REFRESH_TOKEN_KEY);
    if (!currentRefreshToken) return false;

    try {
      // POST /auth/refresh → exchange refresh token for a new pair
      // (This is called "token rotation" — old refresh token becomes invalid)
      const res = await authApi.refresh(currentRefreshToken);
      const { access_token, refresh_token } = res;

      localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

      const user = await authApi.me();
      set({ user, token: access_token, refreshToken: refresh_token, isLoading: false, isAuthenticated: true });
      return true;
    } catch {
      // Refresh token also expired or invalid — full logout
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      set({ user: null, token: null, refreshToken: null, isLoading: false, isAuthenticated: false });
      return false;
    }
  },
}));
