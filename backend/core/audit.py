"""Auditoría de solo agregado. MongoDB (NoSQL) si MONGO_URI existe; si no, tabla AuditLog."""
from datetime import datetime, timezone

from django.conf import settings

_client = None


def _mongo():
    global _client
    if _client is None:
        from pymongo import MongoClient
        _client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
    return _client[settings.MONGO_DB]["audit_logs"]


def log(usuario: str, accion: str, recurso: str = "", detalle: dict | None = None) -> None:
    detalle = detalle or {}
    if settings.MONGO_URI:
        try:
            _mongo().insert_one({"timestamp": datetime.now(timezone.utc), "usuario": usuario,
                                 "accion": accion, "recurso": recurso, "detalle": detalle})
            return
        except Exception:  # si Mongo cae, no se pierde el rastro
            detalle = {**detalle, "_respaldo": "mongo_no_disponible"}
    from .models import AuditLog
    AuditLog.objects.create(usuario=usuario, accion=accion, recurso=recurso, detalle=detalle)


def listar(limit: int = 200, accion: str | None = None):
    """Devuelve los eventos más recientes como lista de dicts."""
    if settings.MONGO_URI:
        try:
            query = {"accion": accion} if accion else {}
            docs = _mongo().find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)
            return [{**d, "timestamp": d["timestamp"].isoformat()} for d in docs]
        except Exception:
            pass
    from .models import AuditLog
    qs = AuditLog.objects.all().order_by("-timestamp")
    if accion:
        qs = qs.filter(accion=accion)
    return [{"timestamp": a.timestamp.isoformat(), "usuario": a.usuario, "accion": a.accion,
             "recurso": a.recurso, "detalle": a.detalle} for a in qs[:limit]]
