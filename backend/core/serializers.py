from datetime import date

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from . import rut as rutlib
from .models import Beneficiario, Entrega, JJVV, Rol, Territorio, Usuario


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["rol"] = user.rol
        token["jjvv"] = user.jjvv_id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["usuario"] = {"username": self.user.username, "rol": self.user.rol, "jjvv": self.user.jjvv_id,
                           "must_change_password": self.user.must_change_password}
        return data


class CambiarClaveSerializer(serializers.Serializer):
    clave_actual = serializers.CharField(write_only=True)
    clave_nueva = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["clave_actual"]):
            raise serializers.ValidationError({"clave_actual": "La clave actual no es correcta."})
        if attrs["clave_actual"] == attrs["clave_nueva"]:
            raise serializers.ValidationError({"clave_nueva": "La clave nueva debe ser distinta a la temporal."})
        validate_password(attrs["clave_nueva"], user)
        return attrs


class UsuarioCrearSerializer(serializers.ModelSerializer):
    clave_temporal = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ["id", "username", "first_name", "last_name", "email", "rol", "jjvv", "clave_temporal", "is_active"]
        read_only_fields = ["id", "is_active"]

    def validate(self, attrs):
        actor = self.context["request"].user
        rol = attrs.get("rol", Rol.REPRESENTANTE_JJVV)
        # El Supervisor no puede crear administradores ni otros supervisores.
        if actor.rol == Rol.SUPERVISOR_MUNI and rol != Rol.REPRESENTANTE_JJVV:
            raise serializers.ValidationError({"rol": "El Supervisor solo puede crear Representantes JJVV."})
        if rol == Rol.REPRESENTANTE_JJVV and not attrs.get("jjvv"):
            raise serializers.ValidationError({"jjvv": "Un Representante JJVV debe estar asociado a una JJVV."})
        return attrs

    def create(self, validated):
        clave = validated.pop("clave_temporal")
        user = Usuario(**validated)
        user.set_password(clave)
        user.must_change_password = True
        user.save()
        return user


class UsuarioListaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "username", "first_name", "last_name", "rol", "jjvv", "must_change_password", "is_active"]


class TerritorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Territorio
        fields = ["id", "nombre"]


class JJVVSerializer(serializers.ModelSerializer):
    territorio_nombre = serializers.CharField(source="territorio.nombre", read_only=True)

    class Meta:
        model = JJVV
        fields = ["id", "nombre", "territorio", "territorio_nombre"]


class BeneficiarioSerializer(serializers.ModelSerializer):
    territorio = serializers.CharField(source="jjvv.territorio.nombre", read_only=True)
    jjvv_nombre = serializers.CharField(source="jjvv.nombre", read_only=True)
    entregado = serializers.SerializerMethodField()
    justificacion = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Beneficiario
        fields = ["id", "tipo_doc", "numero_doc", "nombres", "fecha_nacimiento", "sexo", "tramo", "jjvv", "jjvv_nombre",
                  "territorio", "tutor_run", "tutor_nombre", "estado", "justificacion_duplicado", "justificacion",
                  "duplicado_de", "entregado", "creado_en"]
        read_only_fields = ["id", "tramo", "estado", "justificacion_duplicado", "duplicado_de", "creado_en", "jjvv"]

    def get_entregado(self, obj):
        return hasattr(obj, "entrega")

    def validate(self, attrs):
        tipo, numero = attrs["tipo_doc"], str(attrs["numero_doc"]).strip()
        if tipo == "RUT":
            if not rutlib.is_valid_rut(numero):
                raise serializers.ValidationError({"numero_doc": "RUT inválido (dígito verificador incorrecto)."})
            numero = rutlib.format_rut(numero)
        elif not rutlib.is_valid_ipe(numero):
            raise serializers.ValidationError({"numero_doc": "IPE inválido: use 8 a 12 caracteres alfanuméricos."})
        attrs["numero_doc"] = numero.upper()

        if attrs.get("tutor_run"):
            if not rutlib.is_valid_rut(attrs["tutor_run"]):
                raise serializers.ValidationError({"tutor_run": "RUN del tutor inválido."})
            attrs["tutor_run"] = rutlib.format_rut(attrs["tutor_run"])

        edad = rutlib.age_on(attrs["fecha_nacimiento"], date.today())
        tramo = rutlib.tramo_for_age(edad)
        if tramo is None:
            raise serializers.ValidationError({"fecha_nacimiento": "La edad debe estar entre 0 y 10 años."})
        attrs["tramo"] = tramo
        return attrs


class EntregaSerializer(serializers.ModelSerializer):
    qr_payload = serializers.CharField(write_only=True, required=False, allow_blank=True)
    beneficiario_nombre = serializers.CharField(source="beneficiario.nombres", read_only=True)

    class Meta:
        model = Entrega
        fields = ["id", "beneficiario", "beneficiario_nombre", "tipo", "tutor_run", "qr_payload", "observacion", "fecha_hora"]
        read_only_fields = ["id", "fecha_hora"]
        # La unicidad se controla en la vista para responder 409 ENTREGA_DUPLICADA y auditar el intento.
        extra_kwargs = {"beneficiario": {"validators": []}}
