import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { errorText } from "../api";
import { useAuth } from "../auth";
import { Alert, Field } from "../components/ui";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to={user.must_change_password ? "/cambiar-clave" : "/"} replace />;

  async function submit(e) {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      const u = await login(username.trim(), password);
      navigate(u.must_change_password ? "/cambiar-clave" : "/", { replace: true });
    } catch (err) {
      setError(err.status === 401 ? "Usuario o contraseña incorrectos." : errorText(err));
    } finally { setLoading(false); }
  }

  return (
    <div className="mx-auto mt-10 max-w-md px-4">
      <div className="mb-6 text-center">
        <img src="/icon-192.png" alt="" className="mx-auto mb-3 h-16 w-16 rounded-2xl" />
        <h1 className="text-2xl font-bold text-navy">Trazabilidad de Beneficios</h1>
        <p className="text-sm text-slate-500">Municipalidad de San Joaquín</p>
      </div>
      <form onSubmit={submit} className="card space-y-4">
        <Field label="Usuario"><input className="input" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus /></Field>
        <Field label="Contraseña"><input className="input" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></Field>
        <Alert>{error}</Alert>
        <button className="btn-primary w-full" disabled={loading}>{loading ? "Ingresando…" : "Ingresar"}</button>
        <p className="text-center text-xs text-slate-500">Las cuentas son entregadas por el municipio. No existe registro abierto.</p>
      </form>
    </div>
  );
}
