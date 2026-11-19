from datetime import timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.utils.html import escape
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView
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
from application.use_cases import BuscarProfesionalesUseCase
from infrastructure.adapters.repositories import DjangoProfesionalRepository
from domain.rules import REGIONES_VALIDAS, ESPECIALIDADES_VALIDAS


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
                return redirect('buscador_profesionales')
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

        if user.role == 'PROFESSIONAL':
            prof = getattr(user, 'perfil_profesional', None)
            if prof and prof.estado_validacion != 'Habilitado':
                return redirect('espera_validacion')
            messages.success(self.request, f"¡Bienvenido Ing. {user.first_name or user.username}!")
            return redirect('bandeja_profesional')

        messages.success(self.request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")
        if user.role == 'PRODUCER':
            return redirect('buscador_profesionales')
        return redirect('inicio')

    def form_invalid(self, form):
        username = self.request.POST.get('username', '')
        if username:
            try:
                user = CustomUser.objects.get(username=username)
                conf, _ = ConfiguracionSeguridad.objects.get_or_create(usuario=user)
                if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                    messages.error(
                        self.request,
                        'Cuenta bloqueada por 15 minutos por exceso de intentos fallidos.'
                    )
                    return redirect('login')
                conf.intentos_fallidos_login += 1
                if conf.intentos_fallidos_login >= 3:
                    conf.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
                    conf.save()
                    messages.error(
                        self.request,
                        'Demasiados intentos fallidos. Tu cuenta ha sido bloqueada por 15 minutos.'
                    )
                    return redirect('login')
                conf.save()
            except CustomUser.DoesNotExist:
                pass
        return super().form_invalid(form)


class RegistroProductorView(CreateView):
    form_class = RegistroProductorForm
    template_name = 'users/registro_productor.html'
    success_url = reverse_lazy('buscador_profesionales')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
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
        login(self.request, user)
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
    """Vista 'Mi perfil CIAPAJ' sin errores 404 y con campos institucionales protegidos."""
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
        messages.success(self.request, "Tus zonas de cobertura, contacto y biografía en Mi perfil CIAPAJ han sido actualizados.")
        return super().form_valid(form)


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
    if not request.user.is_authenticated or not (
        request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser
    ):
        messages.error(request, "Acción exclusiva para administradores.")
        return redirect('inicio')

    nuevo_rol = request.POST.get('rol', '')
    if nuevo_rol in ['PRODUCER', 'PROFESSIONAL', 'ADMIN', 'RESET']:
        if nuevo_rol == 'RESET':
            request.session.pop('simulated_role', None)
            messages.info(request, "Restablecido al rol real de Administrador.")
            return redirect('buscador_profesionales')
        else:
            request.session['simulated_role'] = nuevo_rol
            messages.info(request, f"Modo de auditoría visual activado: simulando rol {nuevo_rol}.")
            if nuevo_rol == 'PROFESSIONAL':
                return redirect('bandeja_profesional')
            elif nuevo_rol == 'PRODUCER':
                return redirect('buscador_profesionales')

    return redirect('inicio')
