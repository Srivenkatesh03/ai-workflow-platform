export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    if (window.location.port === "3000") {
      return "http://localhost:8000/api/v1";
    }
    return `${window.location.origin}/api/v1`;
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
}

export const API_BASE_URL = getApiBaseUrl();

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

// Simple global variable to prevent infinite loops during refresh
let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

function getStoredToken(key: string): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(key);
}

function setStoredToken(key: string, value: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, value);
}

function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("ai_workflow_access_token");
  window.localStorage.removeItem("ai_workflow_refresh_token");
  window.localStorage.removeItem("ai_workflow_user");
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const accessToken = getStoredToken("ai_workflow_access_token");
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  // Automatically inject access token if available and not auth endpoints
  if (accessToken && !path.startsWith("/auth/")) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const fetchOptions: RequestInit = {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, fetchOptions);

    if (response.status === 401 && !path.startsWith("/auth/")) {
      // Handle token expiration and refresh
      try {
        const newAccessToken = await handleTokenRefresh();
        
        // Retry the request with the new access token
        headers["Authorization"] = `Bearer ${newAccessToken}`;
        const retryResponse = await fetch(`${API_BASE_URL}${path}`, {
          ...fetchOptions,
          headers,
        });

        const retryPayload = await retryResponse.json();
        if (!retryResponse.ok) {
          throw new Error(retryPayload.message ?? "API request failed after refresh");
        }
        return retryPayload as T;
      } catch (refreshError) {
        clearStoredAuth();
        // Redirect to login on the client side if refresh fails
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        throw refreshError;
      }
    }

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message ?? "API request failed");
    }

    return payload as T;
  } catch (error) {
    throw error;
  }
}

async function handleTokenRefresh(): Promise<string> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  
  refreshPromise = (async () => {
    const refreshToken = getStoredToken("ai_workflow_refresh_token");
    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const payload = await response.json();
    if (!response.ok || !payload.success) {
      throw new Error(payload.message ?? "Failed to refresh token");
    }

    const data = payload.data;
    setStoredToken("ai_workflow_access_token", data.access_token);
    setStoredToken("ai_workflow_refresh_token", data.refresh_token);
    if (data.user) {
      setStoredToken("ai_workflow_user", JSON.stringify(data.user));
    }

    return data.access_token as string;
  })();

  try {
    const token = await refreshPromise;
    return token;
  } finally {
    isRefreshing = false;
    refreshPromise = null;
  }
}
