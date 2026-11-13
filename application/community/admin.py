from django.contrib import admin
from .models import PostComunidad, RespuestaComunidad


class RespuestaInline(admin.TabularInline):
    model = RespuestaComunidad
    extra = 0


class PostComunidadAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'autor', 'fecha_creacion', 'total_respuestas')
    search_fields = ('titulo', 'contenido', 'autor__username', 'autor__first_name')
    inlines = [RespuestaInline]


admin.site.register(PostComunidad, PostComunidadAdmin)
admin.site.register(RespuestaComunidad)
