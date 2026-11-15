from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from core import rut as rutlib
from core.models import AuditLog, Beneficiario, Compra, JJVV, Rol, Territorio, Usuario

PWD = "Clave.Segura2026"


def mk_rut(body: str) -> str:
    return f"{body}-{rutlib.rut_dv(body)}"


def birth(years: int) -> str:
    return (date.today() - timedelta(days=365 * years + 30)).isoformat()


@pytest.fixture
def datos(db):
    t1, t2 = Territorio.objects.create(nombre="T1"), Territorio.objects.create(nombre="T2")
    j1, j2 = JJVV.objects.create(nombre="J1", territorio=t1), JJVV.objects.create(nombre="J2", territorio=t2)
    admin = Usuario.objects.create_user("admin", password=PWD, rol=Rol.SUPER_ADMIN)
    sup = Usuario.objects.create_user("sup", password=PWD, rol=Rol.SUPERVISOR_MUNI)
    r1 = Usuario.objects.create_user("r1", password=PWD, rol=Rol.REPRESENTANTE_JJVV, jjvv=j1)
    r2 = Usuario.objects.create_user("r2", password=PWD, rol=Rol.REPRESENTANTE_JJVV, jjvv=j2)
    for tr, c in (("0-3", 10), ("4-7", 10), ("8-10", 10)):
        Compra.objects.create(tramo=tr, cantidad=c)
    return dict(t1=t1, j1=j1, j2=j2, admin=admin, sup=sup, r1=r1, r2=r2)


def cliente(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def nuevo_benef(c, numero=None, tipo="RUT", edad=5, **extra):
    numero = numero or mk_rut("25123456")
    body = {"tipo_doc": tipo, "numero_doc": numero, "nombres": "Ana Pérez", "fecha_nacimiento": birth(edad),
            "sexo": "F", "tutor_nombre": "María Pérez", "tutor_run": mk_rut("12345678"), **extra}
    return c.post("/api/beneficiarios", body, format="json")


# ---------- RUT / utilidades ----------
def test_rut_valido_e_invalido():
    assert rutlib.is_valid_rut("12.345.678-5")
    assert not rutlib.is_valid_rut("12.345.678-9")
    assert rutlib.is_valid_rut(mk_rut("7654321"))


def test_tramos_de_edad():
    assert [rutlib.tramo_for_age(a) for a in (0, 3, 4, 7, 8, 10, 11)] == ["0-3", "0-3", "4-7", "4-7", "8-10", "8-10", None]


def test_parse_cedula_qr_url():
    run = mk_rut("12345678")
    url = f"https://portal.sidiv.registrocivil.cl/docstatus?RUN={run}&type=CEDULA&serial=123&mrz=abc"
    assert rutlib.parse_cedula_payload(url) == run
    assert rutlib.parse_cedula_payload("basura") is None


# ---------- Módulo 1: autenticación ----------
def test_no_existe_autoregistro(db):
    c = APIClient()
    assert c.post("/api/usuarios", {"username": "x", "clave_temporal": "Abcdef123!"}, format="json").status_code == 401
    assert c.post("/api/registro", {}, format="json").status_code == 404


def test_login_y_clave_temporal_obliga_cambio(datos):
    adm = cliente(datos["admin"])
    r = adm.post("/api/usuarios", {"username": "nuevo", "rol": "REPRESENTANTE_JJVV", "jjvv": datos["j1"].id,
                                   "clave_temporal": "Temporal.2026"}, format="json")
    assert r.status_code == 201
    c = APIClient()
    login = c.post("/api/auth/login", {"username": "nuevo", "password": "Temporal.2026"}, format="json")
    assert login.status_code == 200 and login.data["usuario"]["must_change_password"] is True
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    bloqueado = c.get("/api/beneficiarios")
    assert bloqueado.status_code == 403 and bloqueado.data["code"] == "PASSWORD_CHANGE_REQUIRED"
    mala = c.post("/api/auth/cambiar-clave", {"clave_actual": "Temporal.2026", "clave_nueva": "123"}, format="json")
    assert mala.status_code == 400
    ok = c.post("/api/auth/cambiar-clave", {"clave_actual": "Temporal.2026", "clave_nueva": "Definitiva.2026x"}, format="json")
    assert ok.status_code == 200
    assert c.get("/api/beneficiarios").status_code == 200


def test_clave_se_guarda_con_bcrypt(datos):
    assert datos["admin"].password.startswith("bcrypt_sha256$")


def test_login_incorrecto(datos):
    assert APIClient().post("/api/auth/login", {"username": "admin", "password": "mala"}, format="json").status_code == 401


def test_rbac_usuarios(datos):
    assert cliente(datos["r1"]).get("/api/usuarios").status_code == 403
    sup = cliente(datos["sup"])
    r = sup.post("/api/usuarios", {"username": "otro", "rol": "SUPER_ADMIN", "clave_temporal": "Temporal.2026"}, format="json")
    assert r.status_code == 400  # el supervisor no crea administradores
    r = sup.post("/api/usuarios", {"username": "j3", "rol": "REPRESENTANTE_JJVV", "jjvv": datos["j1"].id,
                                   "clave_temporal": "Temporal.2026"}, format="json")
    assert r.status_code == 201


def test_rbac_dashboard_y_auditoria(datos):
    r1 = cliente(datos["r1"])
    for url in ("/api/dashboard/resumen", "/api/auditoria", "/api/beneficiarios/observados", "/api/compras"):
        assert r1.get(url).status_code == 403
    assert cliente(datos["sup"]).get("/api/dashboard/resumen").status_code == 200
    assert cliente(datos["sup"]).get("/api/compras").status_code == 403  # solo SUPER_ADMIN
    assert cliente(datos["admin"]).get("/api/compras").status_code == 200


# ---------- Módulo 2: beneficiarios ----------
def test_registro_con_rut_calcula_tramo(datos):
    r = nuevo_benef(cliente(datos["r1"]), edad=5)
    assert r.status_code == 201 and r.data["tramo"] == "4-7" and r.data["estado"] == "ACTIVO"


def test_registro_con_ipe(datos):
    r = nuevo_benef(cliente(datos["r1"]), numero="100200300", tipo="IPE", edad=2)
    assert r.status_code == 201 and r.data["tramo"] == "0-3"


def test_rut_invalido_e_ipe_invalido(datos):
    c = cliente(datos["r1"])
    assert nuevo_benef(c, numero="12345678-0").status_code == 400
    assert nuevo_benef(c, numero="12", tipo="IPE").status_code == 400


def test_edad_fuera_de_rango(datos):
    assert nuevo_benef(cliente(datos["r1"]), edad=14).status_code == 400


def test_duplicado_exige_justificacion_y_queda_observado(datos):
    r1, r2 = cliente(datos["r1"]), cliente(datos["r2"])
    assert nuevo_benef(r1).status_code == 201
    sin = nuevo_benef(r2)
    assert sin.status_code == 409 and sin.data["code"] == "DUPLICADO_REQUIERE_JUSTIFICACION"
    corta = nuevo_benef(r2, justificacion="corta")
    assert corta.status_code == 409
    ok = nuevo_benef(r2, justificacion="Familia se mudó de territorio en octubre")
    assert ok.status_code == 201 and ok.data["estado"] == "OBSERVADO" and ok.data["duplicado_de"]
    obs = cliente(datos["sup"]).get("/api/beneficiarios/observados")
    assert len(obs.data) == 1
    acciones = [a.accion for a in AuditLog.objects.all()]
    assert "INTENTO_DUPLICADO" in acciones and "DUPLICADO_OBSERVADO" in acciones


def test_jjvv_solo_ve_sus_beneficiarios(datos):
    nuevo_benef(cliente(datos["r1"]))
    assert len(cliente(datos["r1"]).get("/api/beneficiarios").data) == 1
    assert len(cliente(datos["r2"]).get("/api/beneficiarios").data) == 0
    assert len(cliente(datos["sup"]).get("/api/beneficiarios").data) == 1


# ---------- Módulo 3: entrega ----------
def test_entrega_por_qr_y_bloqueo_de_segunda(datos):
    c = cliente(datos["r1"])
    b = nuevo_benef(c).data
    qr = f"https://portal.sidiv.registrocivil.cl/docstatus?RUN={mk_rut('12345678')}&type=CEDULA"
    r = c.post("/api/entregas", {"beneficiario": b["id"], "tipo": "QR", "qr_payload": qr}, format="json")
    assert r.status_code == 201
    r2 = c.post("/api/entregas", {"beneficiario": b["id"], "tipo": "QR", "qr_payload": qr}, format="json")
    assert r2.status_code == 409 and r2.data["code"] == "ENTREGA_DUPLICADA"


def test_entrega_qr_ilegible(datos):
    c = cliente(datos["r1"])
    b = nuevo_benef(c).data
    r = c.post("/api/entregas", {"beneficiario": b["id"], "tipo": "QR", "qr_payload": "no-es-cedula"}, format="json")
    assert r.status_code == 400 and r.data["code"] == "CEDULA_ILEGIBLE"


def test_retiro_subsidiario_exige_observacion(datos):
    c = cliente(datos["r1"])
    b = nuevo_benef(c).data
    sin = c.post("/api/entregas", {"beneficiario": b["id"], "tipo": "SUBSIDIARIA"}, format="json")
    assert sin.status_code == 400 and sin.data["code"] == "OBSERVACION_OBLIGATORIA"
    ok = c.post("/api/entregas", {"beneficiario": b["id"], "tipo": "SUBSIDIARIA",
                                  "observacion": "Tutor extranjero sin RUN; retira la JJVV como custodio"}, format="json")
    assert ok.status_code == 201


def test_no_entrega_a_beneficiario_de_otra_jjvv(datos):
    b = nuevo_benef(cliente(datos["r1"])).data
    r = cliente(datos["r2"]).post("/api/entregas", {"beneficiario": b["id"], "tipo": "SUBSIDIARIA",
                                                    "observacion": "intento de entrega ajena"}, format="json")
    assert r.status_code == 403


def test_duplicado_observado_no_permite_doble_entrega(datos):
    b1 = nuevo_benef(cliente(datos["r1"])).data
    b2 = nuevo_benef(cliente(datos["r2"]), justificacion="Familia con domicilio en ambos territorios").data
    assert cliente(datos["r1"]).post("/api/entregas", {"beneficiario": b1["id"], "tipo": "SUBSIDIARIA",
                                                      "observacion": "retira la JJVV por custodia"}, format="json").status_code == 201
    r = cliente(datos["r2"]).post("/api/entregas", {"beneficiario": b2["id"], "tipo": "SUBSIDIARIA",
                                                    "observacion": "retira la JJVV por custodia"}, format="json")
    assert r.status_code == 409


def test_supervisor_no_registra_entregas(datos):
    assert cliente(datos["sup"]).post("/api/entregas", {}, format="json").status_code == 403


# ---------- Módulo 4: dashboard y auditoría ----------
def test_dashboard_cuenta_ninos_distintos(datos):
    r1, r2 = cliente(datos["r1"]), cliente(datos["r2"])
    b1 = nuevo_benef(r1, edad=1).data
    nuevo_benef(r1, numero=mk_rut("26000001"), edad=9)
    nuevo_benef(r2, justificacion="Duplicado con dos domicilios", edad=1)  # mismo niño: no suma
    r1.post("/api/entregas", {"beneficiario": b1["id"], "tipo": "SUBSIDIARIA", "observacion": "retiro por custodia JJVV"}, format="json")
    d = cliente(datos["sup"]).get("/api/dashboard/resumen").data
    assert (d["comprados"], d["asignados"], d["entregados"], d["pendientes"], d["observados"]) == (30, 2, 1, 1, 1)
    assert [x["tramo"] for x in d["por_tramo"]] == ["0-3", "4-7", "8-10"]
    assert d["por_tramo"][2]["asignados"] == 1
    filtrado = cliente(datos["sup"]).get(f"/api/dashboard/resumen?territorio={datos['t1'].id}").data
    assert filtrado["asignados"] == 2


def test_auditoria_listado_y_exportacion(datos):
    nuevo_benef(cliente(datos["r1"]))
    sup = cliente(datos["sup"])
    log = sup.get("/api/auditoria").data
    assert log and {"timestamp", "usuario", "accion"} <= set(log[0])
    csv = sup.get("/api/dashboard/exportar")
    assert csv.status_code == 200 and "text/csv" in csv["Content-Type"]
    assert sup.get("/api/auditoria/exportar").status_code == 200
    assert cliente(datos["r1"]).get("/api/auditoria").status_code == 403


def test_logs_son_inmutables(datos):
    nuevo_benef(cliente(datos["r1"]))
    entry = AuditLog.objects.first()
    with pytest.raises(PermissionError):
        entry.delete()
    entry.accion = "MANIPULADO"
    with pytest.raises(PermissionError):
        entry.save()


def test_login_queda_auditado(datos):
    APIClient().post("/api/auth/login", {"username": "admin", "password": PWD}, format="json")
    APIClient().post("/api/auth/login", {"username": "admin", "password": "mala"}, format="json")
    acciones = set(AuditLog.objects.values_list("accion", flat=True))
    assert {"LOGIN_OK", "LOGIN_FALLIDO"} <= acciones


def test_health(db):
    assert APIClient().get("/api/health").json() == {"status": "ok"}


def test_demanda_por_tramo_y_sexo(datos):
    c = cliente(datos["r1"])
    nuevo_benef(c, edad=1)  # niña 0-3
    nuevo_benef(c, numero=mk_rut("26000002"), edad=9, sexo="M")  # niño 8-10
    cliente(datos["r2"])
    nuevo_benef(cliente(datos["r2"]), edad=1, justificacion="Duplicado con dos domicilios")  # no suma
    d = cliente(datos["sup"]).get("/api/dashboard/demanda").data
    assert d["total_ninos"] == 2
    fila = {(f["tramo"], f["sexo"]): f for f in d["filas"]}
    assert fila[("0-3", "F")]["asignados"] == 1 and fila[("8-10", "M")]["asignados"] == 1
    assert fila[("0-3", "F")]["porcentaje"] == 50.0
    assert cliente(datos["r1"]).get("/api/dashboard/demanda").status_code == 403
