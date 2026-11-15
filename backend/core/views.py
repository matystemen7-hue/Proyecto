import csv

from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import audit
from . import rut as rutlib
from .models import Beneficiario, Compra, Entrega, JJVV, Rol, Territorio, Usuario
from .permissions import requiere
from .serializers import (BeneficiarioSerializer, CambiarClaveSerializer, EntregaSerializer, JJVVSerializer,
                          LoginSerializer, TerritorioSerializer, UsuarioCrearSerializer, UsuarioListaSerializer)

TRAMOS = ["0-3", "4-7", "8-10"]


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = []
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        usuario = str(request.data.get("username", ""))[:150]
        try:
            response = super().post(request, *args, **kwargs)
        except Exception:  # credenciales inválidas (401) u otros errores: se audita y se re-lanza
            audit.log(usuario, "LOGIN_FALLIDO", "auth")
            raise
        audit.log(usuario, "LOGIN_OK", "auth")
        return response


class CambiarClaveView(APIView):
    allow_pending_password = True

    def post(self, request):
        ser = CambiarClaveSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = request.user
        user.set_password(ser.validated_data["clave_nueva"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        audit.log(user.username, "CAMBIO_CLAVE", "usuario", {"usuario_id": user.id})
        return Response({"detail": "Contraseña actualizada."})


class UsuariosView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("usuarios")]

    def get(self, request):
        return Response(UsuarioListaSerializer(Usuario.objects.all().order_by("id"), many=True).data)

    def post(self, request):
        ser = UsuarioCrearSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.save()
        audit.log(request.user.username, "USUARIO_CREADO", "usuario", {"usuario_id": user.id, "rol": user.rol})
        return Response(UsuarioListaSerializer(user).data, status=status.HTTP_201_CREATED)


class TerritoriosView(ListAPIView):
    queryset = Territorio.objects.all().order_by("id")
    serializer_class = TerritorioSerializer
    pagination_class = None


class JJVVListView(ListAPIView):
    serializer_class = JJVVSerializer
    pagination_class = None

    def get_queryset(self):
        qs = JJVV.objects.select_related("territorio").order_by("id")
        user = self.request.user
        return qs.filter(id=user.jjvv_id) if user.rol == Rol.REPRESENTANTE_JJVV else qs


def _scope(user, qs):
    """El Representante JJVV solo ve su propia JJVV."""
    return qs.filter(jjvv_id=user.jjvv_id) if user.rol == Rol.REPRESENTANTE_JJVV else qs


class BeneficiariosView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("beneficiarios")]

    def get(self, request):
        qs = _scope(request.user, Beneficiario.objects.select_related("jjvv__territorio", "entrega"))
        for param in ("estado", "tramo", "tipo_doc"):
            if request.query_params.get(param):
                qs = qs.filter(**{param: request.query_params[param]})
        if request.query_params.get("territorio"):
            qs = qs.filter(jjvv__territorio_id=request.query_params["territorio"])
        if request.query_params.get("q"):
            qs = qs.filter(numero_doc__icontains=request.query_params["q"].replace(".", ""))
        return Response(BeneficiarioSerializer(qs.order_by("-id")[:500], many=True).data)

    @transaction.atomic
    def post(self, request):
        ser = BeneficiarioSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = dict(ser.validated_data)
        justificacion = (data.pop("justificacion", "") or "").strip()
        user = request.user

        if user.rol == Rol.REPRESENTANTE_JJVV:
            jjvv = user.jjvv
        else:
            try:
                jjvv = JJVV.objects.get(pk=request.data.get("jjvv"))
            except (JJVV.DoesNotExist, ValueError, TypeError):
                return Response({"code": "invalid", "jjvv": "Indique una JJVV válida."}, status=400)

        previo = Beneficiario.objects.filter(tipo_doc=data["tipo_doc"], numero_doc=data["numero_doc"]).order_by("id").first()
        extra = {}
        if previo:
            # Duplicidad social: no se bloquea, pero exige justificación y queda OBSERVADO.
            if len(justificacion) < 10:
                audit.log(user.username, "INTENTO_DUPLICADO", "beneficiario",
                          {"numero_doc": data["numero_doc"], "jjvv_origen": previo.jjvv_id, "jjvv_intento": jjvv.id})
                return Response({"code": "DUPLICADO_REQUIERE_JUSTIFICACION",
                                 "detail": "El menor ya está registrado. Ingrese una justificación (mín. 10 caracteres).",
                                 "registrado_en": {"jjvv": previo.jjvv.nombre, "territorio": previo.jjvv.territorio.nombre}},
                                status=status.HTTP_409_CONFLICT)
            extra = {"estado": Beneficiario.Estado.OBSERVADO, "justificacion_duplicado": justificacion,
                     "duplicado_de": previo}
        benef = Beneficiario.objects.create(jjvv=jjvv, creado_por=user, **data, **extra)
        audit.log(user.username, "DUPLICADO_OBSERVADO" if previo else "BENEFICIARIO_CREADO", "beneficiario",
                  {"id": benef.id, "tipo_doc": benef.tipo_doc, "numero_doc": benef.numero_doc, "jjvv": jjvv.id})
        return Response(BeneficiarioSerializer(benef).data, status=status.HTTP_201_CREATED)


class ObservadosView(ListAPIView):
    permission_classes = [*APIView.permission_classes, requiere("dashboard")]
    serializer_class = BeneficiarioSerializer
    pagination_class = None

    def get_queryset(self):
        return Beneficiario.objects.filter(estado=Beneficiario.Estado.OBSERVADO).select_related("jjvv__territorio", "entrega").order_by("-id")


class EntregasView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("entregas")]

    @transaction.atomic
    def post(self, request):
        ser = EntregaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        benef = ser.validated_data["beneficiario"]
        user = request.user
        if benef.jjvv_id != user.jjvv_id:
            return Response({"code": "permission_denied", "detail": "El beneficiario pertenece a otra JJVV."}, status=403)
        # Un niño/a solo puede recibir un regalo, aunque tenga registros duplicados.
        ya = Entrega.objects.filter(beneficiario__tipo_doc=benef.tipo_doc, beneficiario__numero_doc=benef.numero_doc).first()
        if ya:
            audit.log(user.username, "ENTREGA_DUPLICADA_BLOQUEADA", "entrega", {"beneficiario": benef.id})
            return Response({"code": "ENTREGA_DUPLICADA", "detail": "Este niño/a ya recibió su regalo.",
                             "fecha_hora": ya.fecha_hora}, status=status.HTTP_409_CONFLICT)

        tipo = ser.validated_data["tipo"]
        observacion = (ser.validated_data.get("observacion") or "").strip()
        tutor_run = ser.validated_data.get("tutor_run", "")
        if tipo == Entrega.Tipo.QR:
            run = rutlib.parse_cedula_payload(ser.validated_data.get("qr_payload", "")) or (
                rutlib.format_rut(tutor_run) if tutor_run and rutlib.is_valid_rut(tutor_run) else None)
            if not run:
                return Response({"code": "CEDULA_ILEGIBLE", "detail": "No se pudo leer un RUN válido de la cédula."}, status=400)
            tutor_run = run
        else:
            if len(observacion) < 10:
                return Response({"code": "OBSERVACION_OBLIGATORIA",
                                 "detail": "El retiro subsidiario requiere una observación fundamentada (mín. 10 caracteres)."}, status=400)
            tutor_run = rutlib.format_rut(tutor_run) if tutor_run and rutlib.is_valid_rut(tutor_run) else ""
        entrega = Entrega.objects.create(beneficiario=benef, tipo=tipo, tutor_run=tutor_run, observacion=observacion, entregado_por=user)
        audit.log(user.username, "ENTREGA_SUBSIDIARIA" if tipo == Entrega.Tipo.SUBSIDIARIA else "ENTREGA_QR", "entrega",
                  {"beneficiario": benef.id, "tutor_run": tutor_run})
        return Response(EntregaSerializer(entrega).data, status=status.HTTP_201_CREATED)


class ComprasView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("compras")]

    def get(self, request):
        return Response({c.tramo: c.cantidad for c in Compra.objects.all()})

    def put(self, request):
        for tramo in TRAMOS:
            if tramo in request.data:
                Compra.objects.update_or_create(tramo=tramo, defaults={"cantidad": int(request.data[tramo])})
        audit.log(request.user.username, "COMPRAS_ACTUALIZADAS", "compra", dict(request.data))
        return self.get(request)


def _resumen(territorio=None, tramo=None):
    base = Beneficiario.objects.all()
    if territorio:
        base = base.filter(jjvv__territorio_id=territorio)
    if tramo:
        base = base.filter(tramo=tramo)
    # Asignados = niños distintos (un duplicado observado no suma otro juguete).
    asignados_qs = base.values("tipo_doc", "numero_doc").distinct()
    asignados = asignados_qs.count()
    entregas = Entrega.objects.filter(beneficiario__in=base)
    entregados = entregas.count()
    comprados = sum(c.cantidad for c in Compra.objects.all() if not tramo or c.tramo == tramo)
    por_territorio = []
    for t in Territorio.objects.order_by("id"):
        if territorio and str(t.id) != str(territorio):
            continue
        b = base.filter(jjvv__territorio=t)
        a = b.values("tipo_doc", "numero_doc").distinct().count()
        e = Entrega.objects.filter(beneficiario__in=b).count()
        por_territorio.append({"territorio": t.nombre, "asignados": a, "entregados": e, "pendientes": a - e})
    por_tramo = []
    for tr in TRAMOS:
        if tramo and tr != tramo:
            continue
        b = base.filter(tramo=tr)
        a = b.values("tipo_doc", "numero_doc").distinct().count()
        e = Entrega.objects.filter(beneficiario__in=b).count()
        por_tramo.append({"tramo": tr, "asignados": a, "entregados": e, "pendientes": a - e})
    return {"comprados": comprados, "asignados": asignados, "entregados": entregados, "pendientes": asignados - entregados,
            "observados": base.filter(estado=Beneficiario.Estado.OBSERVADO).count(),
            "por_territorio": por_territorio, "por_tramo": por_tramo}


class DashboardView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("dashboard")]

    def get(self, request):
        return Response(_resumen(request.query_params.get("territorio"), request.query_params.get("tramo")))


class DemandaView(APIView):
    """Perfil de demanda por tramo y sexo: base para proyectar compras en futuras licitaciones."""
    permission_classes = [*APIView.permission_classes, requiere("dashboard")]

    def get(self, request):
        qs = Beneficiario.objects.select_related("entrega").order_by("id")
        if request.query_params.get("territorio"):
            qs = qs.filter(jjvv__territorio_id=request.query_params["territorio"])
        ninos = {}
        for b in qs:  # un niño con duplicados cuenta una sola vez
            ninos.setdefault((b.tipo_doc, b.numero_doc), []).append(b)
        filas = {(t, x): {"tramo": t, "sexo": x, "asignados": 0, "entregados": 0} for t in TRAMOS for x in ("F", "M")}
        for registros in ninos.values():
            b = registros[0]
            fila = filas[(b.tramo, b.sexo)]
            fila["asignados"] += 1
            fila["entregados"] += any(hasattr(r, "entrega") for r in registros)
        total = sum(f["asignados"] for f in filas.values())
        data = []
        for f in filas.values():
            data.append({**f, "porcentaje": round(100 * f["asignados"] / total, 1) if total else 0})
        return Response({"total_ninos": total, "filas": data})


class DashboardExportView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("dashboard")]

    def get(self, request):
        data = _resumen()
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="rendicion_contraloria.csv"'
        resp.write("\ufeff")
        w = csv.writer(resp)
        w.writerow(["Territorio", "Asignados", "Entregados", "Pendientes"])
        for r in data["por_territorio"]:
            w.writerow([r["territorio"], r["asignados"], r["entregados"], r["pendientes"]])
        w.writerow([])
        w.writerow(["Tramo", "Asignados", "Entregados", "Pendientes"])
        for r in data["por_tramo"]:
            w.writerow([r["tramo"], r["asignados"], r["entregados"], r["pendientes"]])
        w.writerow([])
        w.writerow(["Comprados", data["comprados"]])
        audit.log(request.user.username, "EXPORTACION_REPORTE", "dashboard")
        return resp


class AuditoriaView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("auditoria")]

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 200)), 1000)
        return Response(audit.listar(limit, request.query_params.get("accion")))


class AuditoriaExportView(APIView):
    permission_classes = [*APIView.permission_classes, requiere("auditoria")]

    def get(self, request):
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="auditoria.csv"'
        resp.write("\ufeff")
        w = csv.writer(resp)
        w.writerow(["timestamp", "usuario", "accion", "recurso", "detalle"])
        for e in audit.listar(1000):
            w.writerow([e["timestamp"], e["usuario"], e["accion"], e["recurso"], e["detalle"]])
        audit.log(request.user.username, "EXPORTACION_AUDITORIA", "auditoria")
        return resp
