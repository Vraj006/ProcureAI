"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { usersApi } from "@/services/api/users";
import { TokenResponse, UserResponse } from "@/services/api/types";
import { apiClient } from "@/services/api/client";

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  login: (tokens: TokenResponse, userData: UserResponse) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    async function loadUser() {
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      if (token) {
        try {
          const userData = await usersApi.getMe();
          setUser(userData);
        } catch (error) {
          // 401 interceptor handles refresh. If gets here and fails, remove user
          setUser(null);
        }
      }
      setIsLoading(false);
    }
    loadUser();
  }, []);

  // Protected routing logic
  useEffect(() => {
    if (!isLoading) {
      const isPublicRoute = pathname === "/login" || pathname === "/register";
      if (!user && !isPublicRoute) {
        router.push("/login");
      } else if (user && isPublicRoute) {
        router.push("/dashboard");
      }
    }
  }, [user, isLoading, pathname, router]);

  const login = (tokens: TokenResponse, userData: UserResponse) => {
    localStorage.setItem("auth_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    apiClient.defaults.headers.common["Authorization"] = `Bearer ${tokens.access_token}`;
    setUser(userData);
    router.push("/dashboard");
  };

  const logout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("refresh_token");
    delete apiClient.defaults.headers.common["Authorization"];
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
