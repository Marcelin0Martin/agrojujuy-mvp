from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import CustomUser, Productor, Profesional, ConfiguracionSeguridad


@admin.action(description="✅ Habilitar Profesionales seleccionados (Aprobación CIAPAJ)")
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
        'especialidad_propuesta',
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
        'usuario__username',
        'especialidad',
        'especialidad_propuesta',
    )
    actions = [habilitar_profesionales, suspender_profesionales]
    readonly_fields = ('fecha_solicitud', 'fecha_validacion')

    fieldsets = (
        ('Datos Institucionales CIAPAJ', {
            'fields': ('usuario', 'matricula_provincial', 'estado_validacion', 'fecha_solicitud', 'fecha_validacion')
        }),
        ('Información Técnica y Cobertura', {
            'fields': ('especialidad', 'especialidad_propuesta', 'zonas_cobertura', 'telefono', 'biografia')
        }),
    )

    def get_nombre_completo(self, obj):
        return f"{obj.usuario.first_name} {obj.usuario.last_name}"
    get_nombre_completo.short_description = "Profesional"

    def badge_estado(self, obj):
        if obj.estado_validacion == 'Habilitado':
            color = '#10B981'
            texto = 'Habilitado'
        elif obj.estado_validacion == 'Pendiente':
            color = '#C88A4B'
            texto = 'Pendiente de Revisión'
        else:
            color = '#EF4444'
            texto = 'Suspendido/Rechazado'

        return format_html(
            '<span style="background-color:{}; color:#ffffff; padding:4px 8px; border-radius:6px; font-weight:bold;">{}</span>',
            color,
            texto
        )
    badge_estado.short_description = "Estado de Validación"

    def acciones_rapidas(self, obj):
        if obj.estado_validacion == 'Pendiente':
            return format_html(
                '<a class="button" style="background-color:{}; color:white; padding:4px 8px; border-radius:6px; text-decoration:none;" href="/admin/users/profesional/{}/change/">{}</a>',
                '#173F32',
                obj.pk,
                'Revisar & Validar'
            )
        return "-"
    acciones_rapidas.short_description = "Acción"


class ProductorAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'dni', 'renspa', 'region', 'rubro_productivo', 'telefono', 'fecha_registro')
    list_filter = ('region',)
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__email', 'dni', 'renspa', 'rubro_productivo')

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
