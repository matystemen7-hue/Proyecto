import { useEffect, useState } from "react";
import { api, errorText } from "../api";
import { useAuth } from "../auth";
import { Alert, Badge, Field } from "../components/ui";

function Kpi({ label, value, tone }) {
  return (
    <div className="card">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${tone}`}>{Number(value ?? 0).toLocaleString("es-CL")}</p>
    </div>
  );
}

function Barra({ nombre, a, e }) {
  const pct = a ? Math.round((e / a) * 100) : 0;
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm"><span className="font-medium">{nombre}</span><span className="text-slate-500">{e}/{a} · {pct}%</span></div>
      <div className="h-2.5 rounded-full bg-slate-100"><div className="h-2.5 rounded-full bg-teal" style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

export default function Dashboard() {
  const { can } = useAuth();
  const [datos, setDatos] = useState(null);
  const [terr, setTerr] = useState([]);
  const [fTerr, setFTerr] = useState("");
  const [fTramo, setFTramo] = useState("");
  const [obs, setObs] = useState([]);
  const [compras, setCompras] = useState(null);
  const [demanda, setDemanda] = useState(null);
  const [msg, setMsg] = useState({ kind: "", text: "" });

  useEffect(() => { api.get("/territorios").then(setTerr).catch(() => {}); api.get("/beneficiarios/observados").then(setObs).catch(() => {}); }, []);
  useEffect(() => { if (can("compras")) api.get("/compras").then(setCompras).catch(() => {}); /* eslint-disable-next-line */ }, []);
  useEffect(() => {
    const p = new URLSearchParams();
    if (fTerr) p.set("territorio", fTerr);
    if (fTramo) p.set("tramo", fTramo);
    api.get(`/dashboard/demanda${fTerr ? `?territorio=${fTerr}` : ""}`).then(setDemanda).catch(() => {});
    api.get(`/dashboard/resumen${p.toString() ? `?${p}` : ""}`).then(setDatos).catch((e) => setMsg({ kind: "error", text: errorText(e) }));
  }, [fTerr, fTramo]);

  async function guardarCompras(e) {
    e.preventDefault();
    try {
      const body = Object.fromEntries(Object.entries(compras).map(([k, v]) => [k, Number(v) || 0]));
      setCompras(await api.put("/compras", body));
      setMsg({ kind: "ok", text: "Compras actualizadas." });
      setFTerr((x) => x); // refresca KPI
      const r = await api.get("/dashboard/resumen"); setDatos(r);
    } catch (err) { setMsg({ kind: "error", text: errorText(err) }); }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 className="text-xl font-bold text-navy">Dashboard municipal</h2>
        <div className="flex flex-wrap gap-2">
          <select className="input !w-44" value={fTerr} onChange={(e) => setFTerr(e.target.value)}>
            <option value="">Todos los territorios</option>{terr.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
          </select>
          <select className="input !w-36" value={fTramo} onChange={(e) => setFTramo(e.target.value)}>
            <option value="">Todas las edades</option><option value="0-3">0 a 3 años</option><option value="4-7">4 a 7 años</option><option value="8-10">8 a 10 años</option>
          </select>
          <button className="btn-ghost" onClick={() => api.download("/dashboard/exportar", "rendicion_contraloria.csv").catch((e) => setMsg({ kind: "error", text: errorText(e) }))}>Exportar CSV</button>
        </div>
      </div>
      <Alert kind={msg.kind}>{msg.text}</Alert>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Comprados" value={datos?.comprados} tone="text-navy" />
        <Kpi label="Asignados" value={datos?.asignados} tone="text-teal" />
        <Kpi label="Entregados" value={datos?.entregados} tone="text-emerald-600" />
        <Kpi label="Pendientes" value={datos?.pendientes} tone="text-accent" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card space-y-3"><h3 className="font-bold text-navy">Avance por territorio</h3>
          {datos?.por_territorio.map((t) => <Barra key={t.territorio} nombre={t.territorio} a={t.asignados} e={t.entregados} />)}
        </div>
        <div className="card space-y-3"><h3 className="font-bold text-navy">Avance por tramo de edad</h3>
          {datos?.por_tramo.map((t) => <Barra key={t.tramo} nombre={`${t.tramo} años`} a={t.asignados} e={t.entregados} />)}
          {compras && (
            <form onSubmit={guardarCompras} className="mt-4 space-y-2 border-t pt-3">
              <h4 className="text-sm font-semibold text-slate-700">Juguetes comprados por tramo</h4>
              <div className="grid grid-cols-3 gap-2">
                {["0-3", "4-7", "8-10"].map((k) => (
                  <Field key={k} label={k}><input className="input" type="number" min="0" value={compras[k] ?? 0} onChange={(e) => setCompras({ ...compras, [k]: e.target.value })} /></Field>
                ))}
              </div>
              <button className="btn-ghost">Guardar compras</button>
            </form>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="font-bold text-navy">Demanda por tramo y sexo</h3>
        <p className="mb-3 text-sm text-slate-600">Base para proyectar compras en futuras licitaciones ({demanda?.total_ninos ?? 0} niños/as distintos).</p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Tramo</th><th>Sexo</th><th>Asignados</th><th>Entregados</th><th>% de la demanda</th></tr></thead>
            <tbody>
              {demanda?.filas.map((f) => (
                <tr key={`${f.tramo}${f.sexo}`} className="border-t">
                  <td className="py-2">{f.tramo} años</td><td>{f.sexo === "F" ? "Niñas" : "Niños"}</td><td>{f.asignados}</td><td>{f.entregados}</td><td>{f.porcentaje}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3 className="mb-3 font-bold text-navy">Duplicados observados ({obs.length})</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Documento</th><th>Niño/a</th><th>JJVV</th><th>Justificación</th></tr></thead>
            <tbody>
              {obs.map((b) => (
                <tr key={b.id} className="border-t align-top">
                  <td className="py-2 font-mono text-xs">{b.tipo_doc} {b.numero_doc}</td><td>{b.nombres}</td>
                  <td>{b.jjvv_nombre}<div className="text-xs text-slate-500">{b.territorio}</div></td>
                  <td className="max-w-xs text-slate-600">{b.justificacion_duplicado}</td>
                </tr>
              ))}
              {obs.length === 0 && <tr><td colSpan={4} className="py-6 text-center text-slate-500">Sin duplicados observados.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
