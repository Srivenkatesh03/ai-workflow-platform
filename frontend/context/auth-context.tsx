"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { login as authLogin, register as authRegister, clearAuth, getStoredUser } from "@/services/auth";
import { apiRequest } from "@/services/api";
import type { AuthUser } from "@/types/auth";
import type { ApiResponse } from "@/types/auth";

type AuthContextType = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  checkSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const PUBLIC_ROUTES = ["/login", "/register"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  async function checkSession() {
    try {
      const stored = getStoredUser();
      if (!stored) {
        setUser(null);
        setLoading(false);
        return;
      }

      // Verify the token by calling /users/me
      const response = await apiRequest<ApiResponse<AuthUser>>("/users/me");
      if (response.success && response.data) {
        setUser(response.data);
      } else {
        setUser(stored); // fallback to stored if API succeeded but structure differed
      }
    } catch (error) {
      console.error("Session verification failed, logging out:", error);
      clearAuth();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    checkSession();
  }, []);

  // Handle route protection
  useEffect(() => {
    if (loading) return;

    const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

    if (!user && !isPublicRoute) {
      router.replace("/login");
    } else if (user && isPublicRoute) {
      router.replace("/");
    }
  }, [user, loading, pathname, router]);

  async function login(email: string, password: string) {
    setLoading(true);
    try {
      const tokens = await authLogin(email, password);
      setUser(tokens.user);
      router.push("/");
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  }

  async function register(name: string, email: string, password: string) {
    setLoading(true);
    try {
      const tokens = await authRegister(name, email, password);
      setUser(tokens.user);
      router.push("/");
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearAuth();
    setUser(null);
    router.push("/login");
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    checkSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
