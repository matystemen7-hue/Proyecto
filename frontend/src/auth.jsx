import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, session } from "./api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

// Capacidades por rol (espejo del RBAC del backend).
const PERMISOS = {
  SUPER_ADMIN: ["usuarios", "beneficiarios", "dashboard", "auditoria", "compras"],
  SUPERVISOR_MUNI: ["usuarios", "beneficiarios", "dashboard", "auditoria"],
  REPRESENTANTE_JJVV: ["beneficiarios", "entregas"],
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => session.get()?.usuario || null);

  const logout = useCallback(() => { session.clear(); setUser(null); }, []);

  useEffect(() => {
    window.addEventListener("session-expired", logout);
    return () => window.removeEventListener("session-expired", logout);
  }, [logout]);

  async function login(username, password) {
    const data = await api.post("/auth/login", { username, password });
    session.set({ access: data.access, refresh: data.refresh, usuario: data.usuario });
    setUser(data.usuario);
    return data.usuario;
  }

  function passwordChanged() {
    const s = session.get();
    const usuario = { ...s.usuario, must_change_password: false };
    session.set({ ...s, usuario });
    setUser(usuario);
  }

  const can = (permiso) => !!user && (PERMISOS[user.rol] || []).includes(permiso);
  return <AuthCtx.Provider value={{ user, login, logout, can, passwordChanged }}>{children}</AuthCtx.Provider>;
}
