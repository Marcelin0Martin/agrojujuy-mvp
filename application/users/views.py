from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy

from .models import CustomUser, Productor, Profesional, ConfiguracionSeguridad
from .forms import RegistroProductorForm, RegistroProfesionalForm, PerfilProductorForm, PerfilProfesionalForm
from application.use_cases import BuscarProfesionalesUseCase
from infrastructure.adapters.repositories import DjangoProfesionalRepository
from domain.rules import REGIONES_VALIDAS, ESPECIALIDADES_VALIDAS


class InicioView(TemplateView):
    template_name = 'users/inicio.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Check effective role (simulated by admin or real)
            effective_role = request.session.get('simulated_role', request.user.role)
            if effective_role == 'PROFESSIONAL':
                prof = getattr(request.user, 'perfil_profesional', None)
                if prof and prof.estado_validacion != 'Habilitado':
                    return redirect('espera_validacion')
                return redirect('bandeja_profesional')
            elif effective_role == 'ADMIN':
                return redirect('/admin/')
            return redirect('buscador_profesionales')
        return super().dispatch(request, *args, **kwargs)


class LoginPersonalizadoView(BaseLoginView):
    template_name = 'users/login.html'

    def form_valid(self, form):
        user = form.get_user()
        try:
            conf = ConfiguracionSeguridad.objects.get(usuario=user)
            if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                messages.error(self.request, 'Cuenta bloqueada temporalmente por demasiados intentos fallidos. Intente más tarde.')
                return redirect('login')
            conf.intentos_fallidos_login = 0
            conf.bloqueado_hasta = None
            conf.save()
        except ConfiguracionSeguridad.DoesNotExist:
            pass

        # Check if professional is in pending status
        if user.role == 'PROFESSIONAL':
            prof = getattr(user, 'perfil_profesional', None)
            if prof and prof.estado_validacion != 'Habilitado':
                login(self.request, user)
                return redirect('espera_validacion')

        messages.success(self.request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        username = self.request.POST.get('username', '')
        if username:
            try:
                user = CustomUser.objects.get(username=username)
                conf, _ = ConfiguracionSeguridad.objects.get_or_create(usuario=user)
                if conf.bloqueado_hasta and conf.bloqueado_hasta > timezone.now():
                    messages.error(self.request, 'Cuenta bloqueada por 15 minutos por exceso de intentos fallidos.')
                    return redirect('login')
                conf.intentos_fallidos_login += 1
                if conf.intentos_fallidos_login >= 3:
                    conf.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
                    conf.save()
                    messages.error(self.request, 'Demasiados intentos fallidos. Tu cuenta ha sido bloqueada por 15 minutos.')
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
        messages.success(self.request, f"¡Bienvenido {user.first_name}! Tu cuenta de productor agrícola fue creada con éxito.")
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


class BuscadorProfesionalesView(LoginRequiredMixin, TemplateView):
    template_name = 'users/buscador_profesionales.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        region = self.request.GET.get('region', '')
        especialidad = self.request.GET.get('especialidad', '')

        repo = DjangoProfesionalRepository()
        use_case = BuscarProfesionalesUseCase(repo)

        # Filters are applied through clean architecture use case
        profesionales = use_case.ejecutar(
            region=region if region else None,
            especialidad=especialidad if especialidad else None
        )

        context['profesionales'] = profesionales
        context['regiones'] = REGIONES_VALIDAS
        context['especialidades'] = ESPECIALIDADES_VALIDAS
        context['filtro_region'] = region
        context['filtro_especialidad'] = especialidad
        return context


class VitrinaProfesionalView(LoginRequiredMixin, DetailView):
    model = Profesional
    template_name = 'users/vitrina_profesional.html'
    context_object_name = 'profesional'

    def get_queryset(self):
        # Restriction logic: only 'Habilitado' is visible
        return Profesional.objects.filter(estado_validacion='Habilitado')


class PerfilProductorView(LoginRequiredMixin, UpdateView):
    model = Productor
    form_class = PerfilProductorForm
    template_name = 'users/perfil_productor.html'
    success_url = reverse_lazy('perfil_productor')

    def get_object(self, queryset=None):
        return get_object_or_404(Productor, usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Tus datos de productor y finca han sido actualizados.")
        return super().form_valid(form)


class PerfilProfesionalView(LoginRequiredMixin, UpdateView):
    model = Profesional
    form_class = PerfilProfesionalForm
    template_name = 'users/perfil_profesional.html'
    success_url = reverse_lazy('perfil_profesional')

    def get_object(self, queryset=None):
        return get_object_or_404(Profesional, usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Tus datos profesionales y zonas de cobertura han sido actualizados.")
        return super().form_valid(form)


def cambiar_rol_temporal(request):
    """
    Header Global Requirement:
    'Debe incluir un selector de estado temporal que permita al Administrador
    cambiar entre roles para auditoría y reporte de bugs visuales.'
    """
    if not request.user.is_authenticated or not (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Acción exclusiva para administradores.")
        return redirect('inicio')

    nuevo_rol = request.POST.get('rol', '')
    if nuevo_rol in ['PRODUCER', 'PROFESSIONAL', 'ADMIN', 'RESET']:
        if nuevo_rol == 'RESET':
            request.session.pop('simulated_role', None)
            messages.info(request, "Restablecido al rol real de Administrador.")
        else:
            request.session['simulated_role'] = nuevo_rol
            messages.info(request, f"Modo de auditoría visual activado: simulando rol {nuevo_rol}.")

    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
    return redirect(next_url)
