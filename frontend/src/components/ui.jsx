export function Alert({ kind = "error", children }) {
  if (!children) return null;
  const styles = { error: "bg-red-50 text-red-800 ring-red-200", ok: "bg-emerald-50 text-emerald-800 ring-emerald-200", warn: "bg-amber-50 text-amber-900 ring-amber-200" };
  return <div role="alert" className={`rounded-lg px-3 py-2.5 text-sm ring-1 ${styles[kind]}`}>{children}</div>;
}

export function Badge({ children, tone = "slate" }) {
  const tones = { slate: "bg-slate-100 text-slate-700", ok: "bg-emerald-100 text-emerald-800", warn: "bg-amber-100 text-amber-900", navy: "bg-navy/10 text-navy" };
  return <span className={`badge ${tones[tone]}`}>{children}</span>;
}

export function Field({ label, children }) {
  return <label className="block"><span className="label">{label}</span>{children}</label>;
}

export function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4" onClick={onClose}>
      <div className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-5 sm:rounded-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-bold text-navy">{title}</h2>
          <button className="text-2xl leading-none text-slate-500" aria-label="Cerrar" onClick={onClose}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}
