import { Html5Qrcode, Html5QrcodeSupportedFormats } from "html5-qrcode";
import { useEffect, useRef } from "react";

// Lee el QR (frente) o el PDF417 (reverso) de la cédula con la cámara trasera.
// La cámara requiere HTTPS (Vercel lo entrega) o localhost.
export default function Scanner({ onScan, onError }) {
  const done = useRef(false);
  const elId = "lector-cedula";

  useEffect(() => {
    const scanner = new Html5Qrcode(elId, {
      formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE, Html5QrcodeSupportedFormats.PDF_417],
      verbose: false,
    });
    scanner
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 280, height: 200 } },
        (texto) => {
          if (done.current) return;
          done.current = true;
          onScan(texto);
        },
        () => {} // errores por frame sin código: se ignoran
      )
      .catch((e) => onError?.(String(e)));
    return () => {
      scanner.isScanning ? scanner.stop().then(() => scanner.clear()).catch(() => {}) : scanner.clear();
    };
    // eslint-disable-next-line
  }, []);

  return <div id={elId} className="overflow-hidden rounded-lg bg-black" style={{ minHeight: 220 }} />;
}
