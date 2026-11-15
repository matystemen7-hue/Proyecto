const API = (import.meta.env.VITE_API_URL || "http://localhost:8000/api").replace(/\/$/, "");
const KEY = "beneficios.session";

export class ApiError extends Error {
  constructor(status, data) {
    super(data?.detail || "Error de servidor");
    this.status = status;
    this.data = data || {};
    this.code = data?.code;
  }
}

export const session = {
  get() {
    try { return JSON.parse(sessionStorage.getItem(KEY)) || null; } catch { return null; }
  },
  set(v) { sessionStorage.setItem(KEY, JSON.stringify(v)); },
  clear() { sessionStorage.removeItem(KEY); },
};

async function refresh() {
  const s = session.get();
  if (!s?.refresh) return false;
  const res = await fetch(`${API}/auth/refresh`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh: s.refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  session.set({ ...s, access: data.access, refresh: data.refresh || s.refresh });
  return true;
}

async function request(path, { method = "GET", body, blob = false } = {}, retry = true) {
  const s = session.get();
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (s?.access) headers.Authorization = `Bearer ${s.access}`;
  let res;
  try {
    res = await fetch(`${API}${path}`, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError(0, { code: "network", detail: "Sin conexión con el servidor. Revise su Internet." });
  }
  if (res.status === 401 && retry && s?.refresh && path !== "/auth/login") {
    if (await refresh()) return request(path, { method, body, blob }, false);
    session.clear();
    window.dispatchEvent(new Event("session-expired"));
  }
  if (!res.ok) {
    let data = null;
    try { data = await res.json(); } catch { /* sin cuerpo JSON */ }
    throw new ApiError(res.status, data);
  }
  return blob ? res.blob() : res.status === 204 ? null : res.json();
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: "POST", body }),
  put: (p, body) => request(p, { method: "PUT", body }),
  async download(path, filename) {
    const blob = await request(path, { blob: true });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  },
};

// Convierte los errores de validación de DRF en un texto legible.
export function errorText(err) {
  if (!err) return "";
  const d = err.data || {};
  if (d.detail) return String(d.detail);
  const parts = Object.entries(d).filter(([k]) => k !== "code").map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : v}`);
  return parts.join(" · ") || err.message;
}
