from django.db import models
from application.users.models import CustomUser


class PostComunidad(models.Model):
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posts_comunidad')
    titulo = models.CharField(max_length=200, verbose_name="Título del problema o idea")
    contenido = models.TextField(verbose_name="Publicación")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Publicación de Comunidad'
        verbose_name_plural = 'Publicaciones de Comunidad'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.titulo} - por {self.autor.get_full_name() or self.autor.username}"

    @property
    def total_respuestas(self):
        return self.respuestas.count()


class RespuestaComunidad(models.Model):
    post = models.ForeignKey(PostComunidad, on_delete=models.CASCADE, related_name='respuestas')
    autor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='respuestas_comunidad')
    contenido = models.TextField(verbose_name="Respuesta")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Respuesta de Comunidad'
        verbose_name_plural = 'Respuestas de Comunidad'
        ordering = ['fecha_creacion']

    def __str__(self):
        return f"Respuesta de {self.autor.username} en '{self.post.titulo}'"
