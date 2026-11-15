import os

from django.core.management.base import BaseCommand

from core.models import Compra, JJVV, Rol, Territorio, Usuario

TERRITORIOS = [f"Territorio {i}" for i in range(1, 8)]  # reemplazar por los nombres reales de los 7 territorios


class Command(BaseCommand):
    help = "Crea territorios, JJVV de ejemplo, compras y usuarios iniciales."

    def handle(self, *args, **opts):
        for nombre in TERRITORIOS:
            t, _ = Territorio.objects.get_or_create(nombre=nombre)
            for n in (1, 2):
                JJVV.objects.get_or_create(nombre=f"JJVV {t.id}-{n}", territorio=t)
        for tramo, cant in (("0-3", 4500), ("4-7", 5000), ("8-10", 4000)):
            Compra.objects.get_or_create(tramo=tramo, defaults={"cantidad": cant})

        admin_pass = os.environ.get("ADMIN_PASSWORD", "Admin.Muni2026!")
        for username, rol, jjvv in (("admin", Rol.SUPER_ADMIN, None), ("supervisor", Rol.SUPERVISOR_MUNI, None),
                                    ("jjvv1", Rol.REPRESENTANTE_JJVV, JJVV.objects.order_by("id").first())):
            if not Usuario.objects.filter(username=username).exists():
                u = Usuario(username=username, rol=rol, jjvv=jjvv, is_staff=(rol == Rol.SUPER_ADMIN),
                            is_superuser=(rol == Rol.SUPER_ADMIN))
                u.set_password(admin_pass)
                u.save()
                self.stdout.write(f"Usuario creado: {username} (clave: {admin_pass})")
        self.stdout.write(self.style.SUCCESS("Datos iniciales listos. Cambie las claves de demostración."))
