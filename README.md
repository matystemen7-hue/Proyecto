# Sistema Municipal de Gestión y Trazabilidad de Beneficios

- `backend/`: API REST en Django + DRF (este archivo).
- `frontend/`: PWA en React (ver `frontend/README.md`).
- `render.yaml`: despliegue del backend en Render.

## Ejecutar en local
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # crea territorios, JJVV, compras y usuarios admin / supervisor / jjvv1
python manage.py runserver
python -m pytest -q               # 27 pruebas automáticas
```
Usuarios de demostración (clave `Admin.Muni2026!`, o la de `ADMIN_PASSWORD`): `admin`, `supervisor`, `jjvv1`. Cámbielas antes de presentar.

## Endpoints
| Método | Ruta | Función | Rol |
|---|---|---|---|
| POST | /api/auth/login | Devuelve JWT y `must_change_password` | Público |
| POST | /api/auth/cambiar-clave | Cambio de clave (obligatorio con clave temporal) | Autenticado |
| GET/POST | /api/usuarios | Lista / crea usuario con clave temporal | Admin, Supervisor |
| GET | /api/territorios · /api/jjvv | Catálogos | Autenticado |
| GET/POST | /api/beneficiarios | Lista / registra (RUT o IPE). Duplicado → 409 salvo `justificacion` → OBSERVADO | Admin, Sup., JJVV |
| GET | /api/beneficiarios/observados | Bandeja de duplicados | Admin, Supervisor |
| POST | /api/entregas | `tipo` QR (con `qr_payload` o `tutor_run`) o SUBSIDIARIA (con `observacion`) | JJVV |
| GET/PUT | /api/compras | Juguetes comprados por tramo | Admin |
| GET | /api/dashboard/resumen | Comprados, asignados, entregados, pendientes por territorio y tramo (`?territorio=&tramo=`) | Admin, Supervisor |
| GET | /api/dashboard/demanda | Demanda por tramo y sexo (proyección de compras) | Admin, Supervisor |
| GET | /api/dashboard/exportar | CSV de rendición | Admin, Supervisor |
| GET | /api/auditoria · /api/auditoria/exportar | Bitácora inmutable | Admin, Supervisor |
| GET | /api/health | Estado del servicio | Público |

Errores: `{"code": "...", "detail": "..."}`. Códigos clave: `PASSWORD_CHANGE_REQUIRED` (403), `DUPLICADO_REQUIERE_JUSTIFICACION` (409), `ENTREGA_DUPLICADA` (409), `CEDULA_ILEGIBLE` (400), `OBSERVACION_OBLIGATORIA` (400).

## Despliegue
- **PostgreSQL:** defina `DATABASE_URL`. Sin ella usa SQLite (solo desarrollo).
- **MongoDB Atlas:** defina `MONGO_URI`. Sin ella la auditoría se guarda en la tabla `AuditLog` (también inmutable).
- **Render:** suba el repositorio, use `render.yaml` y cargue las variables de `backend/.env.example`. Con `DEBUG=0` se fuerza HTTPS.
- Ajuste los nombres de los 7 territorios en `core/management/commands/seed_demo.py`.
