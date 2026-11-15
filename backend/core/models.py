from django.contrib.auth.models import AbstractUser
from django.db import models


class Territorio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.nombre


class JJVV(models.Model):
    nombre = models.CharField(max_length=120)
    territorio = models.ForeignKey(Territorio, on_delete=models.PROTECT, related_name="juntas")

    class Meta:
        unique_together = ("nombre", "territorio")

    def __str__(self):
        return self.nombre


class Rol(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Administrador Municipal"
    SUPERVISOR_MUNI = "SUPERVISOR_MUNI", "Supervisor Municipal"
    REPRESENTANTE_JJVV = "REPRESENTANTE_JJVV", "Representante JJVV"


# Permisos por rol (RBAC). Un rol nuevo (p. ej. REPRESENTANTE_JARDIN) se agrega aquí
# y en Rol, sin tocar las vistas.
PERMISOS = {
    Rol.SUPER_ADMIN: {"usuarios", "beneficiarios", "dashboard", "auditoria", "compras"},
    Rol.SUPERVISOR_MUNI: {"usuarios", "beneficiarios", "dashboard", "auditoria"},
    Rol.REPRESENTANTE_JJVV: {"beneficiarios", "entregas"},
}


class Usuario(AbstractUser):
    rol = models.CharField(max_length=30, choices=Rol.choices, default=Rol.REPRESENTANTE_JJVV)
    jjvv = models.ForeignKey(JJVV, null=True, blank=True, on_delete=models.PROTECT, related_name="usuarios")
    must_change_password = models.BooleanField(default=False)

    def tiene_permiso(self, permiso: str) -> bool:
        return permiso in PERMISOS.get(self.rol, set())


class Sexo(models.TextChoices):
    NINA = "F", "Niña"
    NINO = "M", "Niño"


class Beneficiario(models.Model):
    class TipoDoc(models.TextChoices):
        RUT = "RUT", "RUT"
        IPE = "IPE", "IPE"

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        OBSERVADO = "OBSERVADO", "Observado"

    tipo_doc = models.CharField(max_length=3, choices=TipoDoc.choices)
    numero_doc = models.CharField(max_length=20, db_index=True)
    nombres = models.CharField(max_length=120)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    tramo = models.CharField(max_length=5)
    jjvv = models.ForeignKey(JJVV, on_delete=models.PROTECT, related_name="beneficiarios")
    tutor_run = models.CharField(max_length=12, blank=True)
    tutor_nombre = models.CharField(max_length=120)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ACTIVO)
    justificacion_duplicado = models.TextField(blank=True)
    duplicado_de = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="duplicados")
    creado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="beneficiarios_creados")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["tipo_doc", "numero_doc"])]


class Entrega(models.Model):
    class Tipo(models.TextChoices):
        QR = "QR", "Escaneo de cédula"
        SUBSIDIARIA = "SUBSIDIARIA", "Retiro subsidiario JJVV"

    beneficiario = models.OneToOneField(Beneficiario, on_delete=models.PROTECT, related_name="entrega")
    tipo = models.CharField(max_length=12, choices=Tipo.choices)
    tutor_run = models.CharField(max_length=12, blank=True)
    observacion = models.TextField(blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    entregado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="entregas")


class Compra(models.Model):
    """Juguetes comprados por tramo de edad (licitación en Mercado Público)."""
    tramo = models.CharField(max_length=5, unique=True)
    cantidad = models.PositiveIntegerField(default=0)


class AuditLog(models.Model):
    """Bitácora inmutable (respaldo relacional cuando no hay MongoDB)."""
    timestamp = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150)
    accion = models.CharField(max_length=60)
    recurso = models.CharField(max_length=60, blank=True)
    detalle = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Los logs de auditoría son inmutables.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Los logs de auditoría son inmutables.")
