"""Validación de RUT chileno (módulo 11), IPE y lectura de la cédula del tutor."""
import re
from datetime import date


def clean_rut(value: str) -> str:
    return re.sub(r"[^0-9kK]", "", str(value or "")).upper()


def rut_dv(body: str) -> str:
    total, factor = 0, 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = 2 if factor == 7 else factor + 1
    rest = 11 - (total % 11)
    return "0" if rest == 11 else "K" if rest == 10 else str(rest)


def is_valid_rut(value: str) -> bool:
    cleaned = clean_rut(value)
    if len(cleaned) < 2 or not cleaned[:-1].isdigit():
        return False
    return rut_dv(cleaned[:-1]) == cleaned[-1]


def format_rut(value: str) -> str:
    cleaned = clean_rut(value)
    return f"{cleaned[:-1]}-{cleaned[-1]}"


def is_valid_ipe(value: str) -> bool:
    """IPE (Identificador Provisorio Escolar): código alfanumérico de 8 a 12 caracteres."""
    return bool(re.fullmatch(r"[0-9A-Za-z]{8,12}", str(value or "").strip()))


_RUN_PARAM = re.compile(r"RUN=([0-9.]+-?[0-9kK])", re.IGNORECASE)
_RUN_ANY = re.compile(r"\b(\d{1,2}\.?\d{3}\.?\d{3}-?[0-9kK])\b")


def parse_cedula_payload(payload: str):
    """Extrae el RUN del contenido del QR (URL del Registro Civil) o del PDF417 de la cédula."""
    if not payload:
        return None
    for pattern in (_RUN_PARAM, _RUN_ANY):
        match = pattern.search(payload)
        if match and is_valid_rut(match.group(1)):
            return format_rut(match.group(1))
    return None


def tramo_for_age(age: int):
    if 0 <= age <= 3:
        return "0-3"
    if 4 <= age <= 7:
        return "4-7"
    if 8 <= age <= 10:
        return "8-10"
    return None


def age_on(birth: date, ref: date) -> int:
    return ref.year - birth.year - ((ref.month, ref.day) < (birth.month, birth.day))
