from datetime import timedelta
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.utils.html import escape
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy

import json
from collections import Counter
from django.views.generic import TemplateView
from .models import Productor, Profesional
from application.tickets.models import TicketAsistencia
from domain.rules import REGIONES_VALIDAS


from .models import CustomUser, Productor, Profesional, ConfiguracionSeguridad
from .forms import (
    RegistroProductorForm,
    RegistroProfesionalForm,
    PerfilProductorForm,
    PerfilProfesionalForm,
)
from application.use_cases import BuscarProfesionalesUseCase, ValidarProfesionalAdminUseCase
from infrastructure.adapters.repositories import DjangoProfesionalRepository
from domain.rules import REGIONES_VALIDAS, ESPECIALIDADES_VALIDAS


def _es_administrador(user) -> bool:
    return bool(
        user and user.is_authenticated and (
            user.role == 'ADMIN' or user.is_staff or user.is_superuser
        )
    )


class InicioView(TemplateView):
    template_name = 'users/inicio.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            effective_role = request.session.get('simulated_role') or request.user.role
            if effective_role == 'PROFESSIONAL':
                prof = getattr(request.user, 'perfil_profesional', None)
                if prof and prof.estado_validacion != 'Habilitado':
                    return redirect('espera_validacion')
                return redirect('bandeja_profesional')
            elif effective_role == 'PRODUCER':
                return redirect('buscador_profesionales')
            elif effective_role == 'ADMIN':
                return redirect('panel_admin_profesionales')
        return super().dispatch(request, *args, **kwargs)


class NosotrosView(TemplateView):
    """Apartado público institucional 'Nosotros' con mapa territorial interactivo de Jujuy."""
    template_name = 'users/nosotros.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        productores = list(Productor.objects.all())
        profesionales = list(Profesional.objects.filter(estado_validacion='Habilitado'))
        tickets = list(TicketAsistencia.objects.select_related('productor').all())

        descripciones_regiones = {
            'Puna': 'Altiplano jujeño: cultivos andinos, papa andina, quinua y ganadería de camélidos.',
            'Quebrada': 'Valles intermontanos: horticultura de altura, frutales de pepita y cultivos andinos.',
            'Valles': 'Zona templada central: tabaco, hortalizas intensivas, granos y forrajes.',
            'Yungas': 'Selva pedemontana subtropical: caña de azúcar, cítricos, banano y hortalizas primicia.',
        }

        datos_regiones = {}
        for region in REGIONES_VALIDAS:
            prods_region = [p for p in productores if p.region == region]
            profs_region = [pr for pr in profesionales if region in pr.get_zonas_list()]
            tickets_region = [t for t in tickets if t.productor.region == region]
            tickets_resueltos = [t for t in tickets_region if t.estado in ('Finalizado', 'Cerrado')]

            rubros = Counter(
                p.rubro_productivo.strip().capitalize()
                for p in prods_region if p.rubro_productivo
            )
            top_rubros = [r for r, _ in rubros.most_common(3)]

            datos_regiones[region] = {
                'nombre': region,
                'descripcion': descripciones_regiones.get(region, ''),
                'productores': len(prods_region),
                'profesionales': len(profs_region),
                'tickets_totales': len(tickets_region),
                'tickets_resueltos': len(tickets_resueltos),
                'top_rubros': top_rubros,
            }

        context['datos_regiones'] = datos_regiones
        context['total_productores'] = len(productores)
        context['total_profesionales'] = len(profesionales)
        return context

class LoginPersonalizadoView(BaseLoginView):
    template_name = 'users/login.html'

    def form_valid(self, form):
        user = form.get_user()
        tipo_acceso = (self.request.POST.get('tipo_acceso') or 'profesional').strip().lower()

        es_admin = user.role == 'ADMIN' or user.is_staff or user.is_superuser
        es_profesional = user.role == 'PROFESSIONAL'
        es_productor = user.role == 'PRODUCER'

        if tipo_acceso == 'profesional' and not es_profesional:
            if es_admin:
                messages.error(
                    self.request,
                    'Las cuentas de administrador deben ingresar por el apartado exclusivo «Acceso Administrador».'
                )
            else:
                messages.error(
                    self.request,
                    'Esta cuenta no corresponde a Ingreso Profesional. Seleccioná la pestaña «Productor» para ingresar.'
                )
            return redirect('login')

        if tipo_acceso == 'productor' and not es_productor:
            if es_admin:
                messages.error(
                    self.request,
                    'Las cuentas de administrador deben ingresar por el apartado exclusivo «Acceso Administrador».'
                )
            elif es_profesional:
                messages.error(
                    self.request,
                    'Esta cuenta corresponde a un Profesional Agrario. Seleccioná la pestaña «Ingreso Profesional» para ingresar.'
                )
            else:
                messages.error(
                    self.request,
                    'Esta cuenta no corresponde al perfil de Productor.'
                )
            return redirect('login')

        try:
            conf = ConfiguracionSeguridad.objects.get(usuario=user)
            if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                messages.error(
                    self.request,
                    'Cuenta bloqueada temporalmente por demasiados intentos fallidos. Intente más tarde.'
                )
                return redirect('login')
            conf.intentos_fallidos_login = 0
            conf.bloqueado_hasta = None
            conf.save()
        except ConfiguracionSeguridad.DoesNotExist:
            pass

        login(self.request, user)

        if es_profesional:
            prof = getattr(user, 'perfil_profesional', None)
            if prof and prof.estado_validacion != 'Habilitado':
                return redirect('espera_validacion')
            messages.success(self.request, f"¡Bienvenido Ing. {user.first_name or user.username}!")
            return redirect('bandeja_profesional')

        messages.success(self.request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")
        return redirect('buscador_profesionales')


class LoginAdminView(BaseLoginView):
    template_name = 'users/login_admin.html'

    def form_valid(self, form):
        user = form.get_user()
        es_admin = user.role == 'ADMIN' or user.is_staff or user.is_superuser

        if not es_admin:
            messages.error(
                self.request,
                'Acceso denegado. Esta pantalla es exclusiva para personal Administrador CIAPAJ.'
            )
            return redirect('login_admin')

        try:
            conf = ConfiguracionSeguridad.objects.get(usuario=user)
            if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                messages.error(
                    self.request,
                    'Cuenta bloqueada temporalmente por demasiados intentos fallidos. Intente más tarde.'
                )
                return redirect('login_admin')
            conf.intentos_fallidos_login = 0
            conf.bloqueado_hasta = None
            conf.save()
        except ConfiguracionSeguridad.DoesNotExist:
            pass

        login(self.request, user)
        messages.success(self.request, f"¡Bienvenido Administrador, {user.first_name or user.username}!")
        return redirect('panel_admin_profesionales')

class LoginPersonalizadoView(BaseLoginView):
    template_name = 'users/login.html'

    def form_valid(self, form):
        user = form.get_user()
        tipo_acceso = (self.request.POST.get('tipo_acceso') or 'profesional').strip().lower()

        es_admin = user.role == 'ADMIN' or user.is_staff or user.is_superuser
        es_profesional = user.role == 'PROFESSIONAL'
        es_productor = user.role == 'PRODUCER'

        if tipo_acceso == 'profesional' and not es_profesional:
            messages.error(
                self.request,
                'Esta cuenta no corresponde a Ingreso Profesional. Seleccioná la pestaña «Productor / Admin» para ingresar.'
            )
            return redirect('login')

        if tipo_acceso == 'productor' and not (es_productor or es_admin):
            messages.error(
                self.request,
                'Esta cuenta corresponde a un Profesional Agrario. Seleccioná la pestaña «Ingreso Profesional» para ingresar.'
            )
            return redirect('login')

        try:
            conf = ConfiguracionSeguridad.objects.get(usuario=user)
            if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                messages.error(
                    self.request,
                    'Cuenta bloqueada temporalmente por demasiados intentos fallidos. Intente más tarde.'
                )
                return redirect('login')
            conf.intentos_fallidos_login = 0
            conf.bloqueado_hasta = None
            conf.save()
        except ConfiguracionSeguridad.DoesNotExist:
            pass

        login(self.request, user)

        if es_profesional:
            prof = getattr(user, 'perfil_profesional', None)
            if prof and prof.estado_validacion != 'Habilitado':
                return redirect('espera_validacion')
            messages.success(self.request, f"¡Bienvenido Ing. {user.first_name or user.username}!")
            return redirect('bandeja_profesional')

        messages.success(self.request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")
        if es_admin:
            return redirect('panel_admin_profesionales')
        if es_productor:
            return redirect('buscador_profesionales')
        return redirect('inicio')

class RegistroProductorView(CreateView):
    form_class = RegistroProductorForm
    template_name = 'users/registro_productor.html'
    success_url = reverse_lazy('buscador_profesionales')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='application.users.backends.AgroJujuyAuthBackend')
        messages.success(
            self.request,
            f"¡Bienvenido {user.first_name}! Tu cuenta de productor agrícola fue creada con éxito."
        )
        return redirect(self.success_url)


class RegistroProfesionalView(CreateView):
    form_class = RegistroProfesionalForm
    template_name = 'users/registro_profesional.html'
    success_url = reverse_lazy('espera_validacion')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='application.users.backends.AgroJujuyAuthBackend')
        return redirect(self.success_url)


class PantallaEsperaView(LoginRequiredMixin, TemplateView):
    template_name = 'users/espera_validacion.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prof = getattr(self.request.user, 'perfil_profesional', None)
        context['profesional'] = prof
        return context


class BuscadorProfesionalesView(TemplateView):
    """
    Buscador Inteligente accesible públicamente y para productores:
    - No carga toda la lista de ingenieros por defecto al entrar sin filtros.
    - Aplica filtros automáticamente al seleccionar Zona Geográfica o Especialidad.
    - Implementa paginación de 10 perfiles por página.
    """
    template_name = 'users/buscador_profesionales.html'
    PER_PAGE = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        region = self.request.GET.get('region', '').strip()
        especialidad = self.request.GET.get('especialidad', '').strip()
        mostrar_todos = self.request.GET.get('mostrar', '').strip() == 'todos'
        page_number = self.request.GET.get('page', 1)

        filtro_activo = bool(region or especialidad or mostrar_todos)

        if filtro_activo:
            repo = DjangoProfesionalRepository()
            use_case = BuscarProfesionalesUseCase(repo)
            resultados = use_case.ejecutar(
                region=region if region else None,
                especialidad=especialidad if especialidad else None
            )
            paginator = Paginator(resultados, self.PER_PAGE)
            page_obj = paginator.get_page(page_number)
            profesionales_paginados = list(page_obj.object_list)
            total_resultados = paginator.count
        else:
            page_obj = None
            profesionales_paginados = []
            total_resultados = 0

        context['profesionales'] = profesionales_paginados
        context['page_obj'] = page_obj
        context['total_resultados'] = total_resultados
        context['filtro_activo'] = filtro_activo
        context['regiones'] = REGIONES_VALIDAS
        context['especialidades'] = ESPECIALIDADES_VALIDAS
        context['filtro_region'] = region
        context['filtro_especialidad'] = especialidad
        return context


class VitrinaProfesionalView(DetailView):
    """Vitrina digital pública de profesionales habilitados por CIAPAJ."""
    model = Profesional
    template_name = 'users/vitrina_profesional.html'
    context_object_name = 'profesional'

    def get_queryset(self):
        return Profesional.objects.select_related('usuario').filter(estado_validacion='Habilitado')


class PerfilProductorView(LoginRequiredMixin, UpdateView):
    model = Productor
    form_class = PerfilProductorForm
    template_name = 'users/perfil_productor.html'
    success_url = reverse_lazy('perfil_productor')

    def get_object(self, queryset=None):
        productor, _ = Productor.objects.get_or_create(
            usuario=self.request.user,
            defaults={
                'region': 'Valles',
                'rubro_productivo': 'Producción General',
                'dni': '00000000',
                'renspa': '09.001.0.00000/00',
                'telefono': '+54 388 4000000',
                'direccion_finca': 'Sin especificar',
            }
        )
        return productor

    def form_valid(self, form):
        messages.success(self.request, "Tus datos operativos de productor han sido actualizados.")
        return super().form_valid(form)


class PerfilProfesionalView(LoginRequiredMixin, UpdateView):
    """
    Vista 'Mi perfil CIAPAJ' (/perfil/profesional/):
    Permite modificar nombre, apellido, correo electrónico, teléfono,
    especialidades, zonas de cobertura y resumen profesional con validación de matrícula en servidor.
    """
    model = Profesional
    form_class = PerfilProfesionalForm
    template_name = 'users/perfil_profesional.html'
    success_url = reverse_lazy('perfil_profesional')

    def get_object(self, queryset=None):
        profesional, _ = Profesional.objects.get_or_create(
            usuario=self.request.user,
            defaults={
                'matricula_provincial': f"MP-TEMP-{self.request.user.id}/J",
                'especialidad': 'Agronomía General',
                'zonas_cobertura': 'Valles',
                'telefono': '+54 388 4000000',
                'estado_validacion': 'Habilitado' if self.request.user.is_admin_role() else 'Pendiente',
            }
        )
        return profesional

    def form_valid(self, form):
        messages.success(
            self.request,
            "Tus datos personales y profesionales en Mi perfil CIAPAJ han sido actualizados correctamente."
        )
        return super().form_valid(form)


class PanelAdminProfesionalesView(LoginRequiredMixin, TemplateView):
    """
    Panel de Administración Web (Frontend) para el rol ADMIN:
    Permite gestionar el Alta (Habilitar) y Baja (Suspender/Desactivar) de profesionales
    sin obligar al administrador a entrar al /admin/ nativo de Django.
    """
    template_name = 'users/panel_admin_profesionales.html'
    PER_PAGE = 15

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not _es_administrador(request.user):
            messages.error(request, "Acceso denegado. Esta sección es exclusiva para Administradores Institucionales.")
            return HttpResponseForbidden("Acceso denegado: Se requieren permisos de Administrador.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filtro_estado = self.request.GET.get('estado', '').strip()
        busqueda = self.request.GET.get('q', '').strip()
        page_number = self.request.GET.get('page', 1)

        qs = Profesional.objects.select_related('usuario').annotate(
            orden_estado=Case(
                When(estado_validacion='Pendiente', then=Value(0)),
                When(estado_validacion='Habilitado', then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        ).order_by('orden_estado', '-fecha_solicitud')

        if filtro_estado in ['Pendiente', 'Habilitado', 'Suspendido']:
            qs = qs.filter(estado_validacion=filtro_estado)

        if busqueda:
            qs = qs.filter(
                Q(matricula_provincial__icontains=busqueda) |
                Q(usuario__first_name__icontains=busqueda) |
                Q(usuario__last_name__icontains=busqueda) |
                Q(usuario__email__icontains=busqueda) |
                Q(especialidad__icontains=busqueda) |
                Q(especialidad_propuesta__icontains=busqueda)
            )

        paginator = Paginator(qs, self.PER_PAGE)
        page_obj = paginator.get_page(page_number)

        context['profesionales'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['filtro_estado'] = filtro_estado
        context['busqueda'] = busqueda
        context['total_pendientes'] = Profesional.objects.filter(estado_validacion='Pendiente').count()
        context['total_habilitados'] = Profesional.objects.filter(estado_validacion='Habilitado').count()
        context['total_suspendidos'] = Profesional.objects.filter(estado_validacion='Suspendido').count()
        return context


class CambiarEstadoProfesionalAdminView(LoginRequiredMixin, View):
    """
    Ejecuta el Alta (Habilitar) o Baja (Suspender/Desactivar) de un profesional mediante POST
    con token CSRF y verificación estricta de permisos de administrador en backend.
    """

    def post(self, request, profesional_id):
        if not _es_administrador(request.user):
            return HttpResponseForbidden("Acceso denegado: Se requieren permisos de Administrador.")

        profesional = get_object_or_404(Profesional.objects.select_related('usuario'), id=profesional_id)
        accion = request.POST.get('accion', '').strip()

        repo = DjangoProfesionalRepository()
        use_case = ValidarProfesionalAdminUseCase(repo)

        if accion == 'alta':
            use_case.habilitar(profesional.id)
            Profesional.objects.filter(id=profesional.id).update(fecha_validacion=timezone.now())
            messages.success(
                request,
                f"✅ Alta institucional confirmada: Ing. {profesional.usuario.get_full_name() or profesional.usuario.username} "
                f"(Mat. {profesional.matricula_provincial}) ahora está Habilitado y visible en el buscador."
            )
        elif accion == 'baja':
            use_case.rechazar_o_suspender(profesional.id)
            messages.warning(
                request,
                f"⛔ Baja aplicada: Ing. {profesional.usuario.get_full_name() or profesional.usuario.username} "
                f"(Mat. {profesional.matricula_provincial}) fue suspendido. Ya no aparece en el buscador y su bandeja de trabajos quedó restringida."
            )
        else:
            messages.error(request, "Acción administrativa no válida.")

        return redirect('panel_admin_profesionales')


def validar_username_ajax(request):
    """
    Validación en tiempo real (AJAX / HTMX) para avisar si el nombre de usuario ya está ocupado.
    Soporta respuesta JSON y fragmento HTML accesible (HX-Request).
    """
    username = request.GET.get('username', '').strip()
    is_htmx = request.headers.get('HX-Request') == 'true'

    if not username:
        if is_htmx:
            return HttpResponse('')
        return JsonResponse({'disponible': None, 'mensaje': ''})

    if len(username) < 3:
        msg = "El nombre de usuario debe tener al menos 3 caracteres."
        if is_htmx:
            return HttpResponse(f'<span class="text-warning-msg" role="status">{escape(msg)}</span>')
        return JsonResponse({'disponible': False, 'mensaje': msg})

    ocupado = CustomUser.objects.filter(username__iexact=username).exists()
    if ocupado:
        msg = f"El nombre de usuario «{username}» ya está ocupado. Por favor elige otro."
        if is_htmx:
            return HttpResponse(f'<span class="text-error-msg" role="alert">⛔ {escape(msg)}</span>')
        return JsonResponse({'disponible': False, 'mensaje': msg})

    msg = f"El nombre de usuario «{username}» está disponible."
    if is_htmx:
        return HttpResponse(f'<span class="text-success-msg" role="status">✔ {escape(msg)}</span>')
    return JsonResponse({'disponible': True, 'mensaje': msg})


def cambiar_rol_temporal(request):
    """
    Header Global Requirement:
    Permite al Administrador cambiar entre roles para auditoría y reporte de bugs visuales.
    Redirige automáticamente a la vista correspondiente al rol seleccionado.
    """
    if not _es_administrador(request.user):
        messages.error(request, "Acción exclusiva para administradores.")
        return redirect('inicio')

    nuevo_rol = request.POST.get('rol', '')
    if nuevo_rol in ['PRODUCER', 'PROFESSIONAL', 'ADMIN', 'RESET']:
        if nuevo_rol == 'RESET':
            request.session.pop('simulated_role', None)
            messages.info(request, "Restablecido al rol real de Administrador.")
            return redirect('panel_admin_profesionales')
        else:
            request.session['simulated_role'] = nuevo_rol
            messages.info(request, f"Modo de auditoría visual activado: simulando rol {nuevo_rol}.")
            if nuevo_rol == 'PROFESSIONAL':
                return redirect('bandeja_profesional')
            elif nuevo_rol == 'PRODUCER':
                return redirect('buscador_profesionales')
            elif nuevo_rol == 'ADMIN':
                return redirect('panel_admin_profesionales')

    return redirect('inicio')


class NotificacionesView(LoginRequiredMixin, TemplateView):
    """
    Centro de Notificaciones unificado:
    Muestra mensajes nuevos en chats 1 a 1 y comentarios nuevos en hilos del foro
    sin alterar el DER del proyecto.
    """
    template_name = 'users/notificaciones.html'

    def get_context_data(self, **kwargs):
        from .notifications import obtener_notificaciones_usuario
        context = super().get_context_data(**kwargs)
        filtro = self.request.GET.get('tipo', '').strip()
        notificaciones, unread_count = obtener_notificaciones_usuario(self.request)
        if filtro in ('chat', 'foro'):
            notificaciones_filtradas = [n for n in notificaciones if n['tipo'] == filtro]
        elif filtro == 'no_leidas':
            notificaciones_filtradas = [n for n in notificaciones if not n['leida']]
        else:
            notificaciones_filtradas = notificaciones

        context['notificaciones'] = notificaciones_filtradas
        context['total_notificaciones'] = len(notificaciones)
        context['unread_count'] = unread_count
        context['filtro_actual'] = filtro
        return context


def marcar_notificacion_leida(request):
    """Marca una o todas las notificaciones como leídas y redirige al destino."""
    from .notifications import obtener_notificaciones_usuario, mark_notifications_as_read

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        notif_id = request.POST.get('notif_id', '').strip()
        next_url = request.POST.get('next', '').strip()
        if notif_id == 'ALL':
            notificaciones, _ = obtener_notificaciones_usuario(request)
            mark_notifications_as_read(request, [n['id'] for n in notificaciones])
            messages.success(request, "Todas las notificaciones fueron marcadas como leídas.")
            return redirect('notificaciones')
        elif notif_id:
            mark_notifications_as_read(request, [notif_id])
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('notificaciones')

    return redirect('notificaciones')
