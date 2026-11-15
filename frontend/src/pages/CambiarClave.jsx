import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api, errorText } from "../api";
import { useAuth } from "../auth";
import { Alert, Field } from "../components/ui";

export default function CambiarClave() {
  const { user, passwordChanged, logout } = useAuth();
  const navigate = useNavigate();
  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");
  const [repite, setRepite] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!user) return <Navigate to="/login" replace />;

  async function submit(e) {
    e.preventDefault();
    setError("");
    if (nueva !== repite) return setError("Las contraseñas nuevas no coinciden.");
    if (nueva.length < 8) return setError("La contraseña debe tener al menos 8 caracteres.");
    setLoading(true);
    try {
      await api.post("/auth/cambiar-clave", { clave_actual: actual, clave_nueva: nueva });
      passwordChanged();
      navigate("/", { replace: true });
    } catch (err) { setError(errorText(err)); } finally { setLoading(false); }
  }

  return (
    <div className="mx-auto mt-10 max-w-md px-4">
      <h1 className="mb-1 text-2xl font-bold text-navy">Cambie su contraseña</h1>
      <p className="mb-4 text-sm text-slate-600">
        {user.must_change_password ? "Su cuenta tiene una contraseña temporal. Debe reemplazarla para continuar." : "Actualice su contraseña."}
      </p>
      <form onSubmit={submit} className="card space-y-4">
        <Field label="Contraseña actual (temporal)"><input className="input" type="password" autoComplete="current-password" value={actual} onChange={(e) => setActual(e.target.value)} required /></Field>
        <Field label="Contraseña nueva"><input className="input" type="password" autoComplete="new-password" value={nueva} onChange={(e) => setNueva(e.target.value)} required /></Field>
        <Field label="Repita la contraseña nueva"><input className="input" type="password" autoComplete="new-password" value={repite} onChange={(e) => setRepite(e.target.value)} required /></Field>
        <Alert>{error}</Alert>
        <div className="flex gap-2">
          <button className="btn-primary flex-1" disabled={loading}>{loading ? "Guardando…" : "Guardar contraseña"}</button>
          <button type="button" className="btn-ghost" onClick={() => { logout(); navigate("/login"); }}>Salir</button>
        </div>
      </form>
    </div>
  );
}
