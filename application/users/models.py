from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


telefono_validator = RegexValidator(
    regex=r'^\+?[\d\s\-]{8,20}$',
    message="Ingrese un número de teléfono válido (entre 8 y 15 dígitos, puede incluir +, espacios o guiones)."
)

dni_validator = RegexValidator(
    regex=r'^\d{7,8}$',
    message="El DNI debe contener entre 7 y 8 dígitos numéricos sin puntos."
)

renspa_validator = RegexValidator(
    regex=r'^[0-9\.\-\/A-Za-z]{6,22}$',
    message="Ingrese un número de RENSPA válido (ej: 09.001.0.00123/00 o código de 6 a 22 caracteres)."
)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('PRODUCER', 'Productor'),
        ('PROFESSIONAL', 'Profesional'),
        ('ADMIN', 'Administrador'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PRODUCER')

    def is_producer(self):
        return self.role == 'PRODUCER'

    def is_professional(self):
        return self.role == 'PROFESSIONAL'

    def is_admin_role(self):
        return self.role == 'ADMIN' or self.is_superuser


class Productor(models.Model):
    REGION_CHOICES = (
        ('Puna', 'Puna'),
        ('Valles', 'Valles'),
        ('Yungas', 'Yungas'),
        ('Quebrada', 'Quebrada'),
    )

    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='perfil_productor')
    dni = models.CharField(
        max_length=10,
        default='',
        blank=True,
        validators=[dni_validator],
        verbose_name="DNI del Productor",
        help_text="Documento Nacional de Identidad (7 u 8 dígitos)"
    )
    renspa = models.CharField(
        max_length=30,
        default='',
        blank=True,
        validators=[renspa_validator],
        verbose_name="Número de RENSPA",
        help_text="Registro Nacional Sanitario de Productores Agropecuarios"
    )
    region = models.CharField(max_length=50, choices=REGION_CHOICES)
    rubro_productivo = models.CharField(
        max_length=150,
        help_text="Ej: Papa andina, hortalizas, maíz, tabaco, cítricos"
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        default='',
        validators=[telefono_validator]
    )
    direccion_finca = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Ubicación / Finca"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Productor Agrícola'
        verbose_name_plural = 'Productores Agrícolas'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.region})"


class Profesional(models.Model):
    ESTADO_VALIDACION_CHOICES = (
        ('Pendiente', 'Pendiente de Validación'),
        ('Habilitado', 'Habilitado Institucionalmente'),
        ('Suspendido', 'Rechazado / Suspendido'),
    )

    ESPECIALIDADES_CHOICES = (
        ('Agronomía General', 'Agronomía General'),
        ('Riego y Suelos', 'Riego y Suelos'),
        ('Sanidad Vegetal y Plagas', 'Sanidad Vegetal y Plagas'),
        ('Horticultura', 'Horticultura'),
        ('Fruticultura', 'Fruticultura'),
        ('Producción Ganadera y Forrajes', 'Producción Ganadera y Forrajes'),
        ('Agroecología', 'Agroecología'),
        ('Cultivos Andinos', 'Cultivos Andinos'),
    )

    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='perfil_profesional')
    matricula_provincial = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Matrícula Provincial CIAPAJ",
        help_text="Número obligatorio de matrícula del Colegio de Ingenieros Agrónomos y Profesionales Afines de Jujuy"
    )
    especialidad = models.CharField(
        max_length=500,
        default='Agronomía General',
        verbose_name="Especialidades Agronómicas",
        help_text="Una o más especialidades separadas por coma"
    )
    especialidad_propuesta = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name="Especialidad Propuesta",
        help_text="Nueva especialidad propuesta durante el registro"
    )
    zonas_cobertura = models.CharField(
        max_length=255,
        default='Valles, Yungas',
        help_text="Regiones de cobertura separadas por coma (Puna, Valles, Yungas, Quebrada)"
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        default='',
        validators=[telefono_validator]
    )
    biografia = models.TextField(blank=True, default='', verbose_name="Perfil Profesional / Trayectoria")
    estado_validacion = models.CharField(
        max_length=30,
        choices=ESTADO_VALIDACION_CHOICES,
        default='Pendiente',
        help_text="Control institucional del Colegio/Admin"
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_validacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Profesional Agrario'
        verbose_name_plural = 'Profesionales Agrarios'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Ing. {self.usuario.get_full_name() or self.usuario.username} - Mat. {self.matricula_provincial} [{self.estado_validacion}]"

    def esta_habilitado(self):
        return self.estado_validacion == 'Habilitado'

    def get_zonas_list(self):
        return [z.strip() for z in self.zonas_cobertura.split(',') if z.strip()]

    def get_especialidades_list(self):
        items = [e.strip() for e in self.especialidad.split(',') if e.strip()]
        if self.especialidad_propuesta and self.especialidad_propuesta.strip() not in items:
            items.append(self.especialidad_propuesta.strip())
        return items


class ConfiguracionSeguridad(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='configuracion_seguridad')
    intentos_fallidos_login = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Configuración de Seguridad'
        verbose_name_plural = 'Configuraciones de Seguridad'

    def __str__(self):
        return f"Seguridad de {self.usuario.username}"
