from django.db import models
from application.users.models import Productor, Profesional, CustomUser


class TicketAsistencia(models.Model):
    MODALIDADES = (
        ('DIRIGIDA', 'Solicitud Dirigida a Ingeniero'),
        ('ABIERTA', 'Solicitud Abierta a la Comunidad de Ingenieros'),
    )

    ESTADOS = (
        ('Pendiente', 'Pendiente'),
        ('Aceptado', 'Aceptado'),
        ('Finalizado', 'Finalizado por Ingeniero'),
        ('Cerrado', 'Cerrado'),
    )

    productor = models.ForeignKey(Productor, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_recibidas'
    )
    modalidad = models.CharField(max_length=20, choices=MODALIDADES, default='DIRIGIDA')
    especialidad_requerida = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name="Especialidad Requerida"
    )
    titulo = models.CharField(max_length=200, verbose_name="Motivo / Consulta Técnica")
    descripcion = models.TextField(verbose_name="Detalle del problema agronómico")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    # Campos de finalización por el ingeniero y confirmación del productor
    descripcion_finalizacion = models.TextField(
        blank=True,
        default='',
        verbose_name="Informe / Descripción de Finalización"
    )
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    confirmado_por_productor = models.BooleanField(default=False, verbose_name="Recepción Confirmada por Productor")
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Ticket de Asistencia Técnica'
        verbose_name_plural = 'Tickets de Asistencia Técnica'
        ordering = ['-fecha_creacion']

    def __str__(self):
        prof_str = str(self.profesional) if self.profesional else "Abierta (Sin asignar)"
        return f"Ticket #{self.id} [{self.modalidad}]: {self.titulo} - {self.productor} -> {prof_str} [{self.estado}]"


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
