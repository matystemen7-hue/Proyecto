from rest_framework.permissions import BasePermission


class NoPendingPasswordChange(BasePermission):
    """Intercepta al usuario con clave temporal: solo puede cambiarla."""
    code = "PASSWORD_CHANGE_REQUIRED"
    message = "Debe cambiar su contraseña temporal antes de continuar."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return True  # lo resuelve IsAuthenticated
        if getattr(view, "allow_pending_password", False):
            return True
        return not user.must_change_password


def requiere(permiso: str):
    """Fábrica de permisos RBAC por capacidad."""
    class _Perm(BasePermission):
        message = "Su rol no tiene permiso para esta acción."

        def has_permission(self, request, view):
            return bool(request.user and request.user.is_authenticated and request.user.tiene_permiso(permiso))
    _Perm.__name__ = f"Requiere_{permiso}"
    return _Perm
