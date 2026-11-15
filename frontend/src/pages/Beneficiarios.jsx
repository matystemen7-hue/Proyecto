import { useEffect, useState } from "react";
import { api, errorText } from "../api";
import { useAuth } from "../auth";
import { formatRut, isValidIpe, isValidRut } from "../rut";
import { Alert, Badge, Field } from "../components/ui";

const hoy = new Date();
const maxFecha = hoy.toISOString().slice(0, 10);
const minFecha = new Date(hoy.getFullYear() - 11, hoy.getMonth(), hoy.getDate()).toISOString().slice(0, 10);
const vacio = { tipo_doc: "RUT", numero_doc: "", nombres: "", fecha_nacimiento: "", sexo: "F", tutor_nombre: "", tutor_run: "", jjvv: "", justificacion: "" };

export default function Beneficiarios() {
  const { user } = useAuth();
  const esJJVV = user.rol === "REPRESENTANTE_JJVV";
  const [lista, setLista] = useState([]);
  const [jjvv, setJjvv] = useState([]);
  const [form, setForm] = useState(vacio);
  const [dup, setDup] = useState(null); // datos del 409 por duplicado
  const [msg, setMsg] = useState({ kind: "", text: "" });
  const [q, setQ] = useState("");

  const cargar = () => api.get(`/beneficiarios${q ? `?q=${encodeURIComponent(q)}` : ""}`).then(setLista).catch((e) => setMsg({ kind: "error", text: errorText(e) }));
  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [q]);
  useEffect(() => { api.get("/jjvv").then(setJjvv).catch(() => {}); }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function guardar(e) {
    e.preventDefault();
    setMsg({ kind: "", text: "" });
    const docOk = form.tipo_doc === "RUT" ? isValidRut(form.numero_doc) : isValidIpe(form.numero_doc);
    if (!docOk) return setMsg({ kind: "error", text: form.tipo_doc === "RUT" ? "El RUT no es válido (revise el dígito verificador)." : "El IPE debe tener entre 8 y 12 caracteres alfanuméricos." });
    if (form.tutor_run && !isValidRut(form.tutor_run)) return setMsg({ kind: "error", text: "El RUN del tutor no es válido." });
    const body = { ...form, jjvv: esJJVV ? undefined : Number(form.jjvv) || null };
    if (form.tipo_doc === "RUT") body.numero_doc = formatRut(form.numero_doc);
    if (form.tutor_run) body.tutor_run = formatRut(form.tutor_run);
    if (!dup) delete body.justificacion;
    try {
      const r = await api.post("/beneficiarios", body);
      setMsg({ kind: r.estado === "OBSERVADO" ? "warn" : "ok", text: r.estado === "OBSERVADO" ? `Registrado como OBSERVADO. Tramo ${r.tramo}.` : `Registrado correctamente. Tramo ${r.tramo}.` });
      setForm(vacio); setDup(null); cargar();
    } catch (err) {
      if (err.code === "DUPLICADO_REQUIERE_JUSTIFICACION") setDup(err.data);
      else setMsg({ kind: "error", text: errorText(err) });
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <form onSubmit={guardar} className="card space-y-3 lg:col-span-2">
        <h2 className="text-lg font-bold text-navy">Inscribir niño/a</h2>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Documento">
            <select className="input" value={form.tipo_doc} onChange={set("tipo_doc")}><option value="RUT">RUT</option><option value="IPE">IPE</option></select>
          </Field>
          <div className="col-span-2"><Field label={form.tipo_doc === "RUT" ? "RUT (con guion)" : "IPE"}>
            <input className="input" value={form.numero_doc} onChange={set("numero_doc")} placeholder={form.tipo_doc === "RUT" ? "12345678-5" : "100200300"} required /></Field></div>
        </div>
        <Field label="Nombres y apellidos"><input className="input" value={form.nombres} onChange={set("nombres")} required /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Fecha de nacimiento"><input className="input" type="date" min={minFecha} max={maxFecha} value={form.fecha_nacimiento} onChange={set("fecha_nacimiento")} required /></Field>
          <Field label="Sexo"><select className="input" value={form.sexo} onChange={set("sexo")}><option value="F">Niña</option><option value="M">Niño</option></select></Field>
        </div>
        <Field label="Nombre del tutor"><input className="input" value={form.tutor_nombre} onChange={set("tutor_nombre")} required /></Field>
        <Field label="RUN del tutor (opcional)"><input className="input" value={form.tutor_run} onChange={set("tutor_run")} placeholder="12345678-5" /></Field>
        {!esJJVV && (
          <Field label="Junta de Vecinos">
            <select className="input" value={form.jjvv} onChange={set("jjvv")} required>
              <option value="">Seleccione…</option>
              {jjvv.map((j) => <option key={j.id} value={j.id}>{j.nombre} · {j.territorio_nombre}</option>)}
            </select>
          </Field>
        )}
        {dup && (
          <div className="space-y-2 rounded-lg bg-amber-50 p-3 ring-1 ring-amber-200">
            <p className="text-sm font-semibold text-amber-900">Este niño/a ya está inscrito{dup.registrado_en ? ` en ${dup.registrado_en.jjvv} (${dup.registrado_en.territorio})` : ""}.</p>
            <p className="text-xs text-amber-900">Puede registrarlo igualmente indicando una justificación. Quedará como OBSERVADO para revisión municipal.</p>
            <textarea className="input" rows={3} minLength={10} required placeholder="Justificación (mín. 10 caracteres)" value={form.justificacion} onChange={set("justificacion")} />
          </div>
        )}
        <Alert kind={msg.kind}>{msg.text}</Alert>
        <button className="btn-primary w-full">{dup ? "Registrar con justificación" : "Inscribir"}</button>
      </form>

      <div className="card lg:col-span-3">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-bold text-navy">Inscritos ({lista.length})</h2>
          <input className="input !w-48" placeholder="Buscar por RUT / IPE" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Documento</th><th>Nombre</th><th>Tramo</th><th>Estado</th></tr></thead>
            <tbody>
              {lista.map((b) => (
                <tr key={b.id} className="border-t">
                  <td className="py-2 font-mono text-xs">{b.tipo_doc} {b.numero_doc}</td>
                  <td>{b.nombres}<div className="text-xs text-slate-500">{b.jjvv_nombre} · {b.territorio}</div></td>
                  <td>{b.tramo}</td>
                  <td className="space-x-1">
                    {b.estado === "OBSERVADO" ? <Badge tone="warn">Observado</Badge> : <Badge tone="navy">Activo</Badge>}
                    {b.entregado && <Badge tone="ok">Entregado</Badge>}
                  </td>
                </tr>
              ))}
              {lista.length === 0 && <tr><td colSpan={4} className="py-6 text-center text-slate-500">Sin registros.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
