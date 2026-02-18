import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { tokenStorage } from "./storage";

interface AuthState {
  token: string | null;
  isAuthed: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => tokenStorage.get());

  const login = useCallback((newToken: string) => {
    tokenStorage.set(newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setToken(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      isAuthed: Boolean(token),
      login,
      logout,
    }),
    [token, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth должен использоваться внутри AuthProvider");
  }
  return ctx;
}
