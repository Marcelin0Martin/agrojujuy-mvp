from django.contrib import admin
from .models import TicketAsistencia, MensajeTicket


class MensajeTicketInline(admin.TabularInline):
    model = MensajeTicket
    extra = 0
    readonly_fields = ('emisor', 'contenido', 'fecha_envio')


class TicketAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'productor', 'profesional', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'productor__usuario__username', 'profesional__usuario__username')
    inlines = [MensajeTicketInline]


admin.site.register(TicketAsistencia, TicketAsistenciaAdmin)
admin.site.register(MensajeTicket)
