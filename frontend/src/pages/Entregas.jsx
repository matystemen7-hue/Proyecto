import { lazy, Suspense, useEffect, useState } from "react";
import { api, errorText } from "../api";
import { Alert, Badge, Field, Modal } from "../components/ui";
import { formatRut, isValidRut } from "../rut";

// La librería del lector pesa bastante: se carga solo al abrir la cámara.
const Scanner = lazy(() => import("../components/Scanner"));

function EntregaModal({ benef, onClose, onDone }) {
  const [modo, setModo] = useState("qr");
  const [run, setRun] = useState("");
  const [obs, setObs] = useState("");
  const [msg, setMsg] = useState({ kind: "", text: "" });
  const [enviando, setEnviando] = useState(false);

  async function enviar(body) {
    setEnviando(true); setMsg({ kind: "", text: "" });
    try {
      await api.post("/entregas", { beneficiario: benef.id, ...body });
      onDone(`Entrega registrada para ${benef.nombres}.`);
    } catch (err) {
      setMsg({ kind: "error", text: errorText(err) });
      setEnviando(false);
    }
  }

  const porQr = (texto) => enviar({ tipo: "QR", qr_payload: texto });
  const manual = () => {
    if (!isValidRut(run)) return setMsg({ kind: "error", text: "RUN del tutor inválido." });
    enviar({ tipo: "QR", tutor_run: formatRut(run) });
  };
  const subsidiaria = () => {
    if (obs.trim().length < 10) return setMsg({ kind: "error", text: "La observación debe tener al menos 10 caracteres." });
    if (run && !isValidRut(run)) return setMsg({ kind: "error", text: "El RUN ingresado no es válido." });
    enviar({ tipo: "SUBSIDIARIA", observacion: obs.trim(), tutor_run: run ? formatRut(run) : "" });
  };

  const tabs = [["qr", "Escanear cédula"], ["manual", "Ingresar RUN"], ["subsidiaria", "Retiro subsidiario"]];
  return (
    <Modal title={`Entregar a ${benef.nombres}`} onClose={onClose}>
      <p className="mb-3 text-sm text-slate-600">{benef.tipo_doc} {benef.numero_doc} · Tramo {benef.tramo} · Tutor: {benef.tutor_nombre}</p>
      <div className="mb-4 flex gap-1 rounded-lg bg-slate-100 p-1">
        {tabs.map(([k, l]) => (
          <button key={k} className={`flex-1 rounded-md px-2 py-1.5 text-xs font-semibold ${modo === k ? "bg-white text-navy shadow" : "text-slate-600"}`} onClick={() => { setModo(k); setMsg({ kind: "", text: "" }); }}>{l}</button>
        ))}
      </div>

      {modo === "qr" && (
        <div className="space-y-3">
          <p className="text-sm text-slate-600">Apunte la cámara al código QR (frente) o al código de barras (reverso) de la cédula del tutor.</p>
          {!enviando && (
            <Suspense fallback={<p className="text-sm text-slate-500">Iniciando cámara…</p>}>
              <Scanner onScan={porQr} onError={(e) => setMsg({ kind: "error", text: `No se pudo usar la cámara: ${e}. Use "Ingresar RUN".` })} />
            </Suspense>
          )}
          {enviando && <Alert kind="ok">Procesando entrega…</Alert>}
        </div>
      )}
      {modo === "manual" && (
        <div className="space-y-3">
          <Field label="RUN del tutor"><input className="input" value={run} onChange={(e) => setRun(e.target.value)} placeholder="12345678-5" /></Field>
          <button className="btn-teal w-full" onClick={manual} disabled={enviando}>Confirmar entrega</button>
        </div>
      )}
      {modo === "subsidiaria" && (
        <div className="space-y-3">
          <Alert kind="warn">Use esta opción solo si el tutor no puede identificarse con RUN nacional. La JJVV asume la entrega como custodio.</Alert>
          <Field label="Observación fundamentada (obligatoria)"><textarea className="input" rows={3} value={obs} onChange={(e) => setObs(e.target.value)} placeholder="Ej.: Tutor extranjero sin RUN; retira la JJVV como custodio." /></Field>
          <Field label="RUN de quien retira (opcional)"><input className="input" value={run} onChange={(e) => setRun(e.target.value)} /></Field>
          <button className="btn-primary w-full" onClick={subsidiaria} disabled={enviando}>Registrar retiro subsidiario</button>
        </div>
      )}
      <div className="mt-3"><Alert kind={msg.kind}>{msg.text}</Alert></div>
    </Modal>
  );
}

export default function Entregas() {
  const [lista, setLista] = useState([]);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(null);
  const [msg, setMsg] = useState("");
  const [verEntregados, setVerEntregados] = useState(false);

  const cargar = () => api.get(`/beneficiarios${q ? `?q=${encodeURIComponent(q)}` : ""}`).then(setLista).catch(() => {});
  useEffect(() => { cargar(); /* eslint-disable-next-line */ }, [q]);

  const visibles = lista.filter((b) => verEntregados || !b.entregado);
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-navy">Entrega de regalos</h2>
          <p className="text-sm text-slate-600">Seleccione al niño/a y confirme la entrega con la cédula del tutor.</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-sm"><input type="checkbox" checked={verEntregados} onChange={(e) => setVerEntregados(e.target.checked)} /> Ver entregados</label>
          <input className="input !w-52" placeholder="Buscar por RUT / IPE" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>
      <Alert kind="ok">{msg}</Alert>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {visibles.map((b) => (
          <div key={b.id} className="card flex flex-col justify-between gap-3">
            <div>
              <p className="font-semibold">{b.nombres}</p>
              <p className="font-mono text-xs text-slate-500">{b.tipo_doc} {b.numero_doc}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                <Badge tone="navy">Tramo {b.tramo}</Badge>
                {b.estado === "OBSERVADO" && <Badge tone="warn">Observado</Badge>}
                {b.entregado && <Badge tone="ok">Entregado</Badge>}
              </div>
            </div>
            <button className="btn-teal" disabled={b.entregado} onClick={() => { setMsg(""); setSel(b); }}>{b.entregado ? "Ya entregado" : "Entregar"}</button>
          </div>
        ))}
        {visibles.length === 0 && <p className="col-span-full py-8 text-center text-slate-500">No hay niños/as pendientes de entrega.</p>}
      </div>
      {sel && <EntregaModal benef={sel} onClose={() => setSel(null)} onDone={(t) => { setSel(null); setMsg(t); cargar(); }} />}
    </div>
  );
}
