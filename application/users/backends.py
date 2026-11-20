from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import CustomUser, Profesional


class AgroJujuyAuthBackend(ModelBackend):
    """
    Authentication Backend personalizado para AgroJujuy:
    - Permite a usuarios con rol PROFESSIONAL iniciar sesión con su Número de Matrícula Provincial (CIAPAJ)
      y su contraseña (además de mantener soporte por username).
    - Permite a usuarios PRODUCER y ADMIN iniciar sesión con su nombre de usuario o correo electrónico
      y su contraseña.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        identificador = username.strip()
        user = None

        # 1. Intentar localizar profesional por Matrícula Provincial CIAPAJ
        profesional = Profesional.objects.select_related('usuario').filter(
            matricula_provincial__iexact=identificador
        ).first()
        if profesional and profesional.usuario.role == 'PROFESSIONAL':
            user = profesional.usuario

        # 2. Si no coincide con una matrícula, buscar por username o email
        if user is None:
            user = CustomUser.objects.filter(
                Q(username__iexact=identificador) | Q(email__iexact=identificador)
            ).first()

        if user is not None and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
