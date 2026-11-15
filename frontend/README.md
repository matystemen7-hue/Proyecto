# Frontend PWA — Trazabilidad de Beneficios (React + Vite + Tailwind)

## Local
```bash
cd frontend
cp .env.example .env     # VITE_API_URL=http://localhost:8000/api para desarrollo
npm install
npm run dev              # http://localhost:5173
npm test                 # pruebas de validación de RUT/IPE
npm run build            # genera dist/
```
El backend debe tener `CORS_ALLOWED_ORIGINS=http://localhost:5173` (valor por defecto).

## Pantallas
| Ruta | Rol | Función |
|---|---|---|
| /login | Público | Ingreso. No hay registro abierto |
| /cambiar-clave | Autenticado | Cambio obligatorio de clave temporal |
| /usuarios | Admin, Supervisor | Crear y listar usuarios |
| /beneficiarios | Admin, Supervisor, JJVV | Inscribir con RUT o IPE; justificación si hay duplicado |
| /entregas | JJVV | Escanear cédula (QR / PDF417), ingresar RUN o retiro subsidiario |
| /dashboard | Admin, Supervisor | Indicadores, filtros, duplicados observados, exportar CSV; el Admin edita compras |
| /auditoria | Admin, Supervisor | Bitácora y exportación |

## Despliegue en Vercel
1. Suba el repositorio y cree un proyecto en Vercel con *Root Directory* `frontend` (framework Vite).
2. Variable de entorno: `VITE_API_URL=https://su-api.onrender.com/api`.
3. En Render, agregue la URL de Vercel a `CORS_ALLOWED_ORIGINS`.
4. La cámara solo funciona en HTTPS (Vercel lo entrega) y con permiso del navegador.

## PWA
`public/manifest.webmanifest` y `public/sw.js` permiten "Agregar a la pantalla de inicio". El service worker solo guarda el shell; la API nunca se cachea.
