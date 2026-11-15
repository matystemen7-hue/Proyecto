import { useEffect, useState } from "react";
import { api, errorText } from "../api";
import { Alert, Badge } from "../components/ui";

const fmt = (iso) => new Date(iso).toLocaleString("es-CL", { timeZone: "America/Santiago" });

export default function Auditoria() {
  const [logs, setLogs] = useState([]);
  const [accion, setAccion] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/auditoria${accion ? `?accion=${encodeURIComponent(accion)}` : ""}`).then(setLogs).catch((e) => setErr(errorText(e)));
  }, [accion]);

  return (
    <div className="card space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div><h2 className="text-xl font-bold text-navy">Bitácora de auditoría</h2><p className="text-sm text-slate-600">Registro inmutable de acciones: no puede editarse ni borrarse.</p></div>
        <div className="flex gap-2">
          <select className="input !w-52" value={accion} onChange={(e) => setAccion(e.target.value)}>
            <option value="">Todas las acciones</option>
            {["LOGIN_OK", "LOGIN_FALLIDO", "USUARIO_CREADO", "CAMBIO_CLAVE", "BENEFICIARIO_CREADO", "INTENTO_DUPLICADO", "DUPLICADO_OBSERVADO", "ENTREGA_QR", "ENTREGA_SUBSIDIARIA", "ENTREGA_DUPLICADA_BLOQUEADA", "EXPORTACION_REPORTE"].map((a) => <option key={a}>{a}</option>)}
          </select>
          <button className="btn-ghost" onClick={() => api.download("/auditoria/exportar", "auditoria.csv").catch((e) => setErr(errorText(e)))}>Exportar CSV</button>
        </div>
      </div>
      <Alert>{err}</Alert>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Fecha y hora</th><th>Usuario</th><th>Acción</th><th>Detalle</th></tr></thead>
          <tbody>
            {logs.map((l, i) => (
              <tr key={i} className="border-t align-top">
                <td className="whitespace-nowrap py-2 text-xs">{fmt(l.timestamp)}</td><td>{l.usuario}</td>
                <td><Badge tone={l.accion.includes("FALLIDO") || l.accion.includes("BLOQUEADA") || l.accion.includes("DUPLICADO") ? "warn" : "navy"}>{l.accion}</Badge></td>
                <td className="max-w-md break-words font-mono text-xs text-slate-500">{JSON.stringify(l.detalle)}</td>
              </tr>
            ))}
            {logs.length === 0 && <tr><td colSpan={4} className="py-6 text-center text-slate-500">Sin eventos.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
