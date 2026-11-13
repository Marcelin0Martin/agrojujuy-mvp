from django.db import models
from application.users.models import Productor, Profesional, CustomUser


class TicketAsistencia(models.Model):
    ESTADOS = (
        ('Pendiente', 'Pendiente'),
        ('Aceptado', 'Aceptado'),
        ('Cerrado', 'Cerrado'),
    )

    productor = models.ForeignKey(Productor, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    profesional = models.ForeignKey(Profesional, on_delete=models.CASCADE, related_name='solicitudes_recibidas')
    titulo = models.CharField(max_length=200, verbose_name="Motivo / Consulta Técnica")
    descripcion = models.TextField(verbose_name="Detalle del problema agronómico")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ticket de Asistencia Técnica'
        verbose_name_plural = 'Tickets de Asistencia Técnica'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Ticket #{self.id}: {self.titulo} - {self.productor} -> {self.profesional} [{self.estado}]"


class MensajeTicket(models.Model):
    ticket = models.ForeignKey(TicketAsistencia, on_delete=models.CASCADE, related_name='mensajes')
    emisor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mensajes_enviados')
    contenido = models.TextField(verbose_name="Mensaje")
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensaje de Chat Directo'
        verbose_name_plural = 'Mensajes de Chat Directo'
        ordering = ['fecha_envio']

    def __str__(self):
        return f"Mensaje de {self.emisor.username} en Ticket #{self.ticket_id}"
