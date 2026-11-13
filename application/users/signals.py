from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, ConfiguracionSeguridad


@receiver(post_save, sender=CustomUser)
def inicializar_seguridad_usuario(sender, instance, created, **kwargs):
    if created:
        ConfiguracionSeguridad.objects.get_or_create(usuario=instance)
