import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const ROL = { SUPER_ADMIN: "Administrador", SUPERVISOR_MUNI: "Supervisor", REPRESENTANTE_JJVV: "Representante JJVV" };

export default function Layout() {
  const { user, can, logout } = useAuth();
  const navigate = useNavigate();
  const links = [
    ["/dashboard", "Dashboard", "dashboard"],
    ["/beneficiarios", "Beneficiarios", "beneficiarios"],
    ["/entregas", "Entregas", "entregas"],
    ["/usuarios", "Usuarios", "usuarios"],
    ["/auditoria", "Auditoría", "auditoria"],
  ].filter(([, , p]) => can(p));

  return (
    <div className="min-h-screen pb-10">
      {user && !user.must_change_password && (
        <header className="bg-navy text-white">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-3">
            <div>
              <p className="text-base font-bold leading-tight">Trazabilidad de Beneficios</p>
              <p className="text-xs text-slate-300">Municipalidad de San Joaquín</p>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <span className="hidden sm:inline">{user.username} · {ROL[user.rol] || user.rol}</span>
              <button className="btn-ghost !px-3 !py-1.5 !text-navy" onClick={() => { logout(); navigate("/login"); }}>Salir</button>
            </div>
          </div>
          <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-3 pb-2">
            {links.map(([to, label]) => (
              <NavLink key={to} to={to}
                className={({ isActive }) => `whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium ${isActive ? "bg-teal text-white" : "text-slate-200 hover:bg-white/10"}`}>
                {label}
              </NavLink>
            ))}
          </nav>
        </header>
      )}
      <main className="mx-auto max-w-6xl px-4 py-6"><Outlet /></main>
    </div>
  );
}
