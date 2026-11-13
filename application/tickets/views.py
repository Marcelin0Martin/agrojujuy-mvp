from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, View
from django.contrib import messages
from django.urls import reverse

from .models import TicketAsistencia, MensajeTicket
from .forms import CrearTicketForm, MensajeChatForm
from application.users.models import Productor, Profesional
from application.use_cases import (
    CrearTicketAsistenciaUseCase,
    CambiarEstadoTicketUseCase,
    EnviarMensajeChatUseCase,
)
from infrastructure.adapters.repositories import (
    DjangoTicketRepository,
    DjangoProfesionalRepository,
    DjangoChatRepository,
)


class BandejaProductorView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/bandeja_productor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        productor = getattr(self.request.user, 'perfil_productor', None)
        if productor:
            # Acotado a las últimas 5 solicitudes según SDD
            context['tickets'] = TicketAsistencia.objects.filter(productor=productor).order_by('-fecha_creacion')[:5]
        else:
            context['tickets'] = []
        return context


class BandejaProfesionalView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/bandeja_profesional.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profesional = getattr(self.request.user, 'perfil_profesional', None)
        if profesional:
            # Acotado a las últimas 5 solicitudes/tickets según SDD
            context['tickets'] = TicketAsistencia.objects.filter(profesional=profesional).order_by('-fecha_creacion')[:5]
        else:
            context['tickets'] = []
        return context


class SolicitarAsistenciaView(LoginRequiredMixin, View):
    template_name = 'tickets/solicitar_ticket.html'

    def get(self, request, profesional_id):
        profesional = get_object_or_404(Profesional, id=profesional_id, estado_validacion='Habilitado')
        form = CrearTicketForm()
        return render(request, self.template_name, {'form': form, 'profesional': profesional})

    def post(self, request, profesional_id):
        profesional = get_object_or_404(Profesional, id=profesional_id, estado_validacion='Habilitado')
        productor = getattr(request.user, 'perfil_productor', None)
        if not productor:
            messages.error(request, "Solo los productores pueden solicitar asistencia técnica.")
            return redirect('buscador_profesionales')

        form = CrearTicketForm(request.POST)
        if form.is_valid():
            titulo = form.cleaned_data['titulo']
            descripcion = form.cleaned_data['descripcion']

            repo_ticket = DjangoTicketRepository()
            repo_prof = DjangoProfesionalRepository()
            use_case = CrearTicketAsistenciaUseCase(repo_ticket, repo_prof)
            res = use_case.ejecutar(
                productor_id=productor.id,
                profesional_id=profesional.id,
                titulo=titulo,
                descripcion=descripcion
            )
            if res.exito:
                messages.success(request, "¡Solicitud enviada! Se ha abierto el hilo de conversación técnica.")
                return redirect('chat_ticket', ticket_id=res.datos.id)
            else:
                messages.error(request, res.mensaje)

        return render(request, self.template_name, {'form': form, 'profesional': profesional})


class ChatTicketView(LoginRequiredMixin, View):
    template_name = 'tickets/chat_ticket.html'

    def get_ticket_y_validar(self, request, ticket_id):
        ticket = get_object_or_404(TicketAsistencia, id=ticket_id)
        # Validación de acceso al canal 1 a 1
        es_productor = (ticket.productor.usuario_id == request.user.id)
        es_profesional = (ticket.profesional.usuario_id == request.user.id)
        es_admin = (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser)

        if not (es_productor or es_profesional or es_admin):
            return None, ticket
        return ticket, ticket

    def get(self, request, ticket_id):
        ticket_valido, ticket = self.get_ticket_y_validar(request, ticket_id)
        if not ticket_valido:
            messages.error(request, "No tienes permiso para acceder a este canal privado de asistencia.")
            return redirect('inicio')

        mensajes = ticket.mensajes.all().order_by('fecha_envio')
        form = MensajeChatForm()
        return render(request, self.template_name, {
            'ticket': ticket,
            'mensajes': mensajes,
            'form': form,
            'es_productor': (ticket.productor.usuario_id == request.user.id),
            'es_profesional': (ticket.profesional.usuario_id == request.user.id),
        })

    def post(self, request, ticket_id):
        ticket_valido, ticket = self.get_ticket_y_validar(request, ticket_id)
        if not ticket_valido:
            messages.error(request, "No tienes permiso para acceder a este canal privado.")
            return redirect('inicio')

        form = MensajeChatForm(request.POST)
        if form.is_valid():
            contenido = form.cleaned_data['contenido']
            repo_chat = DjangoChatRepository()
            repo_ticket = DjangoTicketRepository()
            use_case = EnviarMensajeChatUseCase(repo_chat, repo_ticket)
            res = use_case.ejecutar(
                ticket_id=ticket.id,
                emisor_id=request.user.id,
                contenido=contenido,
                emisor_usuario_id=request.user.id,
                prod_uid=ticket.productor.usuario_id,
                prof_uid=ticket.profesional.usuario_id
            )
            if not res.exito:
                messages.error(request, res.mensaje)
        return redirect('chat_ticket', ticket_id=ticket.id)


class AceptarTicketView(LoginRequiredMixin, View):
    def post(self, request, ticket_id):
        profesional = getattr(request.user, 'perfil_profesional', None)
        ticket = get_object_or_404(TicketAsistencia, id=ticket_id)
        if profesional and ticket.profesional_id == profesional.id:
            repo_ticket = DjangoTicketRepository()
            use_case = CambiarEstadoTicketUseCase(repo_ticket)
            use_case.ejecutar(ticket.id, 'Aceptado')
            messages.success(request, f"Has aceptado la solicitud #{ticket.id}. Puedes continuar la conversación técnica.")
        return redirect('chat_ticket', ticket_id=ticket.id)
