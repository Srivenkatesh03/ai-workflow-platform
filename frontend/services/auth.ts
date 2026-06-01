import { apiRequest } from "@/services/api";
import type { ApiResponse, AuthTokens, AuthUser } from "@/types/auth";

const ACCESS_TOKEN_KEY = "ai_workflow_access_token";
const REFRESH_TOKEN_KEY = "ai_workflow_refresh_token";
const USER_KEY = "ai_workflow_user";

export async function login(email: string, password: string): Promise<AuthTokens> {
  const response = await apiRequest<ApiResponse<AuthTokens>>("/auth/login", {
    method: "POST",
    body: { email, password }
  });
  persistAuth(response.data);
  return response.data;
}

export async function register(name: string, email: string, password: string): Promise<AuthTokens> {
  const response = await apiRequest<ApiResponse<AuthTokens>>("/auth/register", {
    method: "POST",
    body: { name, email, password }
  });
  persistAuth(response.data);
  return response.data;
}

export function persistAuth(tokens: AuthTokens): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(tokens.user));
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") {
    return null;
  }
  const rawUser = window.localStorage.getItem(USER_KEY);
  return rawUser ? (JSON.parse(rawUser) as AuthUser) : null;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function clearAuth(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

