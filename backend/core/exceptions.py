from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler


def handler(exc, context):
    """Respuestas de error uniformes: {"code": ..., "detail": ...}."""
    response = exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict) and "code" not in response.data:
        code = getattr(exc, "default_code", "error")
        detail = response.data.get("detail")
        if isinstance(detail, ErrorDetail) and detail.code:
            code = detail.code
        response.data = {"code": str(code), **response.data}
    return response
