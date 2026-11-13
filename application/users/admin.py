from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import CustomUser, Productor, Profesional, ConfiguracionSeguridad


@admin.action(description="✅ Habilitar Profesionales seleccionados (Aprobación CIAPA)")
def habilitar_profesionales(modeladmin, request, queryset):
    actualizados = queryset.update(estado_validacion='Habilitado', fecha_validacion=timezone.now())
    modeladmin.message_user(
        request,
        f"Se habilitaron {actualizados} profesionales correctamente. Ahora son visibles para los productores."
    )


@admin.action(description="⛔ Rechazar / Suspender Profesionales seleccionados")
def suspender_profesionales(modeladmin, request, queryset):
    actualizados = queryset.update(estado_validacion='Suspendido')
    modeladmin.message_user(
        request,
        f"Se suspendieron/rechazaron {actualizados} profesionales. Han sido retirados del buscador público."
    )


class ProfesionalAdmin(admin.ModelAdmin):
    list_display = (
        'matricula_provincial',
        'get_nombre_completo',
        'especialidad',
        'zonas_cobertura',
        'telefono',
        'badge_estado',
        'fecha_solicitud',
        'acciones_rapidas',
    )
    list_filter = ('estado_validacion', 'especialidad')
    search_fields = (
        'matricula_provincial',
        'usuario__first_name',
        'usuario__last_name',
        'usuario__email',
        'usuario__username'
    )
    actions = [habilitar_profesionales, suspender_profesionales]
    readonly_fields = ('fecha_solicitud', 'fecha_validacion')

    fieldsets = (
        ('Datos Institucionales CIAPA', {
            'fields': ('usuario', 'matricula_provincial', 'estado_validacion', 'fecha_solicitud', 'fecha_validacion')
        }),
        ('Información Técnica y Cobertura', {
            'fields': ('especialidad', 'zonas_cobertura', 'telefono', 'biografia')
        }),
    )

    def get_nombre_completo(self, obj):
        return f"{obj.usuario.first_name} {obj.usuario.last_name}"
    get_nombre_completo.short_description = "Profesional"

    def badge_estado(self, obj):
        if obj.estado_validacion == 'Habilitado':
            return format_html('<span style="background-color:#10B981; color:#ffffff; padding:4px 8px; border-radius:4px; font-weight:bold;">Habilitado</span>')
        elif obj.estado_validacion == 'Pendiente':
            return format_html('<span style="background-color:#C88A4B; color:#ffffff; padding:4px 8px; border-radius:4px; font-weight:bold;">Pendiente de Revisión</span>')
        else:
            return format_html('<span style="background-color:#EF4444; color:#ffffff; padding:4px 8px; border-radius:4px; font-weight:bold;">Suspendido/Rechazado</span>')
    badge_estado.short_description = "Estado de Validación"

    def acciones_rapidas(self, obj):
        if obj.estado_validacion == 'Pendiente':
            return format_html(
                '<a class="button" style="background-color:#173F32; color:white; padding:3px 6px; border-radius:3px; text-decoration:none;" href="/admin/users/profesional/{}/change/">Revisar & Validar</a>',
                obj.pk
            )
        return "-"
    acciones_rapidas.short_description = "Acción"


class ProductorAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'region', 'rubro_productivo', 'telefono', 'fecha_registro')
    list_filter = ('region',)
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__email', 'rubro_productivo')

    def get_nombre_completo(self, obj):
        return f"{obj.usuario.first_name} {obj.usuario.last_name}"
    get_nombre_completo.short_description = "Productor"


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Productor, ProductorAdmin)
admin.site.register(Profesional, ProfesionalAdmin)
admin.site.register(ConfiguracionSeguridad)
