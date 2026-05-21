// Auth context: tracks the currently logged-in user.
// Login stores the user id in localStorage; the API client reads it from there.

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchMe } from "../api/endpoints";
import type { User } from "../types";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (user: User) => void;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount, if we have a user id stored, fetch the user.
  useEffect(() => {
    const userId = localStorage.getItem("skynet_user_id");
    if (!userId) {
      setLoading(false);
      return;
    }
    fetchMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("skynet_user_id");
      })
      .finally(() => setLoading(false));
  }, []);

  function login(u: User) {
    localStorage.setItem("skynet_user_id", String(u.id));
    setUser(u);
  }
  function logout() {
    localStorage.removeItem("skynet_user_id");
    setUser(null);
  }

  return <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
