from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, Beneficiario, Compra, Entrega, JJVV, Territorio, Usuario

admin.site.register(Usuario, UserAdmin)
admin.site.register([Territorio, JJVV, Beneficiario, Entrega, Compra])


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "usuario", "accion", "recurso")

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
