import { useEffect, useState } from "react";

import { api, type TokenResponse } from "../lib/api";

const STORAGE_KEY = "reliable-rag-auth";

interface AuthState {
  accessToken: string;
  username: string;
  role: string;
}

function readStoredAuth(): AuthState | null {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthState;
  } catch {
    sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    localStorage.removeItem(STORAGE_KEY);
    setAuth(readStoredAuth());
    setIsReady(true);
  }, []);

  const persistAuth = (response: TokenResponse) => {
    const nextState = {
      accessToken: response.access_token,
      username: response.username,
      role: response.role,
    };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
    setAuth(nextState);
  };

  const login = async (username: string, password: string) => {
    const response: TokenResponse = await api.login(username, password);
    persistAuth(response);
  };

  const register = async (username: string, fullName: string, password: string) => {
    const response: TokenResponse = await api.register(username, fullName, password);
    persistAuth(response);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_KEY);
    setAuth(null);
  };

  return {
    auth,
    isReady,
    isAuthenticated: Boolean(auth?.accessToken),
    login,
    register,
    logout,
  };
}
