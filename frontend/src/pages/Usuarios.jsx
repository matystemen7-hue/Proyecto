import { useEffect, useState } from "react";
import { api, errorText } from "../api";
import { useAuth } from "../auth";
import { Alert, Badge, Field } from "../components/ui";

const ROLES = { SUPER_ADMIN: "Administrador", SUPERVISOR_MUNI: "Supervisor", REPRESENTANTE_JJVV: "Representante JJVV" };
const vacio = { username: "", first_name: "", last_name: "", rol: "REPRESENTANTE_JJVV", jjvv: "", clave_temporal: "" };

export default function Usuarios() {
  const { user } = useAuth();
  const [lista, setLista] = useState([]);
  const [jjvv, setJjvv] = useState([]);
  const [form, setForm] = useState(vacio);
  const [msg, setMsg] = useState({ kind: "", text: "" });

  const cargar = () => api.get("/usuarios").then(setLista).catch((e) => setMsg({ kind: "error", text: errorText(e) }));
  useEffect(() => { cargar(); api.get("/jjvv").then(setJjvv).catch(() => {}); }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const rolesPermitidos = user.rol === "SUPER_ADMIN" ? Object.keys(ROLES) : ["REPRESENTANTE_JJVV"];

  async function crear(e) {
    e.preventDefault();
    setMsg({ kind: "", text: "" });
    try {
      const body = { ...form, jjvv: form.rol === "REPRESENTANTE_JJVV" ? Number(form.jjvv) || null : null };
      await api.post("/usuarios", body);
      setMsg({ kind: "ok", text: `Usuario ${form.username} creado. Deberá cambiar la clave temporal en su primer ingreso.` });
      setForm(vacio); cargar();
    } catch (err) { setMsg({ kind: "error", text: errorText(err) }); }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <form onSubmit={crear} className="card space-y-3 lg:col-span-2">
        <h2 className="text-lg font-bold text-navy">Crear usuario</h2>
        <Field label="Nombre de usuario"><input className="input" value={form.username} onChange={set("username")} required /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Nombre"><input className="input" value={form.first_name} onChange={set("first_name")} /></Field>
          <Field label="Apellido"><input className="input" value={form.last_name} onChange={set("last_name")} /></Field>
        </div>
        <Field label="Rol">
          <select className="input" value={form.rol} onChange={set("rol")}>{rolesPermitidos.map((r) => <option key={r} value={r}>{ROLES[r]}</option>)}</select>
        </Field>
        {form.rol === "REPRESENTANTE_JJVV" && (
          <Field label="Junta de Vecinos">
            <select className="input" value={form.jjvv} onChange={set("jjvv")} required>
              <option value="">Seleccione…</option>
              {jjvv.map((j) => <option key={j.id} value={j.id}>{j.nombre} · {j.territorio_nombre}</option>)}
            </select>
          </Field>
        )}
        <Field label="Clave temporal (mín. 8 caracteres)"><input className="input" value={form.clave_temporal} onChange={set("clave_temporal")} minLength={8} required /></Field>
        <Alert kind={msg.kind}>{msg.text}</Alert>
        <button className="btn-primary w-full">Crear usuario</button>
      </form>

      <div className="card lg:col-span-3">
        <h2 className="mb-3 text-lg font-bold text-navy">Usuarios ({lista.length})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Usuario</th><th>Rol</th><th>Estado</th></tr></thead>
            <tbody>
              {lista.map((u) => (
                <tr key={u.id} className="border-t">
                  <td className="py-2 font-medium">{u.username}</td>
                  <td>{ROLES[u.rol] || u.rol}</td>
                  <td>{u.must_change_password ? <Badge tone="warn">Clave temporal</Badge> : <Badge tone="ok">Activo</Badge>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
