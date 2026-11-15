from django.http import JsonResponse
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health", health),
    path("auth/login", views.LoginView.as_view()),
    path("auth/refresh", TokenRefreshView.as_view()),
    path("auth/cambiar-clave", views.CambiarClaveView.as_view()),
    path("usuarios", views.UsuariosView.as_view()),
    path("territorios", views.TerritoriosView.as_view()),
    path("jjvv", views.JJVVListView.as_view()),
    path("beneficiarios", views.BeneficiariosView.as_view()),
    path("beneficiarios/observados", views.ObservadosView.as_view()),
    path("entregas", views.EntregasView.as_view()),
    path("compras", views.ComprasView.as_view()),
    path("dashboard/resumen", views.DashboardView.as_view()),
    path("dashboard/demanda", views.DemandaView.as_view()),
    path("dashboard/exportar", views.DashboardExportView.as_view()),
    path("auditoria", views.AuditoriaView.as_view()),
    path("auditoria/exportar", views.AuditoriaExportView.as_view()),
]
