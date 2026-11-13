from django.contrib.auth.models import AbstractUser
from django.db import models


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
    region = models.CharField(max_length=50, choices=REGION_CHOICES)
    rubro_productivo = models.CharField(max_length=150, help_text="Ej: Papa andina, hortalizas, maíz, tabaco, cítricos")
    telefono = models.CharField(max_length=30, blank=True, default='')
    direccion_finca = models.CharField(max_length=255, blank=True, default='', verbose_name="Ubicación / Finca")
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
        verbose_name="Matrícula Provincial CIAPA",
        help_text="Número obligatorio de matrícula del Colegio de Ingenieros Agrónomos y Profesionales Afines"
    )
    especialidad = models.CharField(max_length=100, choices=ESPECIALIDADES_CHOICES, default='Agronomía General')
    zonas_cobertura = models.CharField(
        max_length=255,
        default='Valles, Yungas',
        help_text="Regiones de cobertura separadas por coma (Puna, Valles, Yungas, Quebrada)"
    )
    telefono = models.CharField(max_length=30, blank=True, default='')
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


class ConfiguracionSeguridad(models.Model):
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='configuracion_seguridad')
    intentos_fallidos_login = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Configuración de Seguridad'
        verbose_name_plural = 'Configuraciones de Seguridad'

    def __str__(self):
        return f"Seguridad de {self.usuario.username}"
