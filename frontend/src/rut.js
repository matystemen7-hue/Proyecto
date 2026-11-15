// Validación de RUT chileno (módulo 11) en el cliente. El backend la repite: es solo ayuda al usuario.
export function cleanRut(v) {
  return String(v || "").replace(/[^0-9kK]/g, "").toUpperCase();
}

export function rutDv(body) {
  let total = 0;
  let factor = 2;
  for (const d of [...body].reverse()) {
    total += Number(d) * factor;
    factor = factor === 7 ? 2 : factor + 1;
  }
  const rest = 11 - (total % 11);
  return rest === 11 ? "0" : rest === 10 ? "K" : String(rest);
}

export function isValidRut(v) {
  const c = cleanRut(v);
  if (c.length < 2 || !/^\d+$/.test(c.slice(0, -1))) return false;
  return rutDv(c.slice(0, -1)) === c.slice(-1);
}

export function formatRut(v) {
  const c = cleanRut(v);
  return c.length < 2 ? c : `${c.slice(0, -1)}-${c.slice(-1)}`;
}

export function isValidIpe(v) {
  return /^[0-9A-Za-z]{8,12}$/.test(String(v || "").trim());
}
