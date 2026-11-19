from django.db.models import Case, When, Value, IntegerField, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.contrib import messages

from .models import TicketAsistencia, MensajeTicket
from .forms import (
    CrearTicketForm,
    CrearSolicitudAbiertaForm,
    FinalizarTicketForm,
    MensajeChatForm,
)
from application.users.models import Productor, Profesional
from application.use_cases import (
    CrearTicketAsistenciaUseCase,
    CrearSolicitudAbiertaUseCase,
    TomarSolicitudAbiertaUseCase,
    CambiarEstadoTicketUseCase,
    FinalizarTrabajoTicketUseCase,
    ConfirmarRecepcionTicketUseCase,
    EnviarMensajeChatUseCase,
)
from infrastructure.adapters.repositories import (
    DjangoTicketRepository,
    DjangoProfesionalRepository,
    DjangoChatRepository,
)


def _obtener_o_crear_productor_para_usuario(user):
    prod = getattr(user, 'perfil_productor', None)
    if not prod and (user.role == 'PRODUCER' or user.is_admin_role()):
        prod, _ = Productor.objects.get_or_create(
            usuario=user,
            defaults={
                'region': 'Valles',
                'rubro_productivo': 'Producción General',
                'dni': '00000000',
                'renspa': '09.001.0.00000/00',
                'telefono': '+54 388 4000000',
                'direccion_finca': 'Finca Experimental',
            }
        )
    return prod


def _obtener_o_crear_profesional_para_usuario(user):
    prof = getattr(user, 'perfil_profesional', None)
    if not prof and (user.role == 'PROFESSIONAL' or user.is_admin_role()):
        prof, _ = Profesional.objects.get_or_create(
            usuario=user,
            defaults={
                'matricula_provincial': f"MP-AUTO-{user.id}/J",
                'especialidad': 'Agronomía General',
                'zonas_cobertura': 'Valles, Quebrada',
                'telefono': '+54 388 4000000',
                'estado_validacion': 'Habilitado',
            }
        )
    return prof


class BandejaProductorView(LoginRequiredMixin, TemplateView):
    template_name = 'tickets/bandeja_productor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        productor = _obtener_o_crear_productor_para_usuario(self.request.user)
        filtro_estado = self.request.GET.get('estado', '').strip()

        if productor:
            qs = TicketAsistencia.objects.select_related('profesional', 'profesional__usuario').filter(
                productor=productor
            ).annotate(
                prioridad_estado=Case(
                    When(estado='Pendiente', then=Value(0)),
                    When(estado='Aceptado', then=Value(1)),
                    When(estado='Finalizado', then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            )
            if filtro_estado in ['Pendiente', 'Aceptado', 'Finalizado']:
                qs = qs.filter(estado=filtro_estado)
            context['tickets'] = qs.order_by('prioridad_estado', '-fecha_creacion')[:10]
        else:
            context['tickets'] = []

        context['filtro_estado'] = filtro_estado
        return context


class BandejaProfesionalView(LoginRequiredMixin, TemplateView):
    """
    Bandeja de Trabajos del Profesional:
    - Muestra las solicitudes dirigidas al ingeniero y las solicitudes abiertas disponibles.
    - Ordena mostrando los Pendientes primero y luego por fecha reciente.
    - Permite filtrar por 'Pendiente', 'Aceptado' o 'Finalizado'.
    """
    template_name = 'tickets/bandeja_profesional.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profesional = _obtener_o_crear_profesional_para_usuario(self.request.user)
        filtro_estado = self.request.GET.get('estado', '').strip()

        if profesional:
            qs = TicketAsistencia.objects.select_related(
                'productor', 'productor__usuario', 'profesional', 'profesional__usuario'
            ).filter(
                Q(profesional=profesional) |
                Q(modalidad='ABIERTA', estado='Pendiente', profesional__isnull=True)
            ).annotate(
                prioridad_estado=Case(
                    When(estado='Pendiente', then=Value(0)),
                    When(estado='Aceptado', then=Value(1)),
                    When(estado='Finalizado', then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            )
            if filtro_estado in ['Pendiente', 'Aceptado', 'Finalizado']:
                qs = qs.filter(estado=filtro_estado)

            context['tickets'] = qs.order_by('prioridad_estado', '-fecha_creacion')[:15]
            context['profesional'] = profesional
        else:
            context['tickets'] = []
            context['profesional'] = None

        context['filtro_estado'] = filtro_estado
        return context


class SolicitarAsistenciaView(LoginRequiredMixin, View):
    """Solicitud de asistencia técnica DIRIGIDA a un ingeniero específico."""
    template_name = 'tickets/solicitar_ticket.html'

    def get(self, request, profesional_id):
        profesional = get_object_or_404(Profesional, id=profesional_id, estado_validacion='Habilitado')
        form = CrearTicketForm()
        return render(request, self.template_name, {'form': form, 'profesional': profesional})

    def post(self, request, profesional_id):
        profesional = get_object_or_404(Profesional, id=profesional_id, estado_validacion='Habilitado')
        productor = _obtener_o_crear_productor_para_usuario(request.user)
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
                messages.success(request, "¡Solicitud dirigida enviada! Se ha abierto el hilo de conversación técnica.")
                return redirect('chat_ticket', ticket_id=res.datos.id)
            else:
                messages.error(request, res.mensaje)

        return render(request, self.template_name, {'form': form, 'profesional': profesional})


class SolicitarAsistenciaAbiertaView(LoginRequiredMixin, View):
    """
    Solicitud de asistencia técnica ABIERTA:
    Publica el problema para que cualquier ingeniero habilitado lo tome (bloqueándose una vez aceptado).
    """
    template_name = 'tickets/solicitar_ticket_abierto.html'

    def get(self, request):
        form = CrearSolicitudAbiertaForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        productor = _obtener_o_crear_productor_para_usuario(request.user)
        if not productor:
            messages.error(request, "Solo los productores pueden publicar solicitudes de asistencia.")
            return redirect('buscador_profesionales')

        form = CrearSolicitudAbiertaForm(request.POST)
        if form.is_valid():
            repo_ticket = DjangoTicketRepository()
            use_case = CrearSolicitudAbiertaUseCase(repo_ticket)
            res = use_case.ejecutar(
                productor_id=productor.id,
                titulo=form.cleaned_data['titulo'],
                descripcion=form.cleaned_data['descripcion'],
                especialidad_requerida=form.cleaned_data.get('especialidad_requerida', ''),
            )
            if res.exito:
                messages.success(request, res.mensaje)
                return redirect('bandeja_productor')
            messages.error(request, res.mensaje)

        return render(request, self.template_name, {'form': form})


class ChatTicketView(LoginRequiredMixin, View):
    template_name = 'tickets/chat_ticket.html'

    def get_ticket_y_validar(self, request, ticket_id):
        ticket = get_object_or_404(
            TicketAsistencia.objects.select_related(
                'productor', 'productor__usuario', 'profesional', 'profesional__usuario'
            ),
            id=ticket_id
        )
        es_productor = (ticket.productor.usuario_id == request.user.id)
        es_profesional = (ticket.profesional is not None and ticket.profesional.usuario_id == request.user.id)
        es_admin = (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser)
        es_abierta_disponible = (
            ticket.modalidad == 'ABIERTA' and
            ticket.estado == 'Pendiente' and
            ticket.profesional is None and
            (request.user.role == 'PROFESSIONAL' or es_admin)
        )

        if not (es_productor or es_profesional or es_admin or es_abierta_disponible):
            return None, ticket
        return ticket, ticket

    def get(self, request, ticket_id):
        ticket_valido, ticket = self.get_ticket_y_validar(request, ticket_id)
        if not ticket_valido:
            messages.error(request, "No tienes permiso para acceder a este canal privado de asistencia.")
            return redirect('inicio')

        from application.users.notifications import mark_ticket_messages_read
        mark_ticket_messages_read(request, ticket.id)
        mensajes = ticket.mensajes.select_related('emisor').all().order_by('fecha_envio')
        form = MensajeChatForm()
        finalizar_form = FinalizarTicketForm()
        return render(request, self.template_name, {
            'ticket': ticket,
            'mensajes': mensajes,
            'form': form,
            'finalizar_form': finalizar_form,
            'es_productor': (ticket.productor.usuario_id == request.user.id),
            'es_profesional': (ticket.profesional is not None and ticket.profesional.usuario_id == request.user.id),
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
            prof_uid = ticket.profesional.usuario_id if ticket.profesional else None
            res = use_case.ejecutar(
                ticket_id=ticket.id,
                emisor_id=request.user.id,
                contenido=contenido,
                emisor_usuario_id=request.user.id,
                prod_uid=ticket.productor.usuario_id,
                prof_uid=prof_uid
            )
            if not res.exito:
                messages.error(request, res.mensaje)
        return redirect('chat_ticket', ticket_id=ticket.id)


class AceptarTicketView(LoginRequiredMixin, View):
    """
    Permite a un ingeniero aceptar una solicitud dirigida o tomar una solicitud abierta
    (bloqueándola automáticamente para otros profesionales).
    """
    def post(self, request, ticket_id):
        profesional = _obtener_o_crear_profesional_para_usuario(request.user)
        ticket = get_object_or_404(TicketAsistencia, id=ticket_id)

        if not profesional:
            messages.error(request, "Debes contar con un perfil profesional para aceptar solicitudes.")
            return redirect('inicio')

        repo_ticket = DjangoTicketRepository()
        repo_prof = DjangoProfesionalRepository()
        use_case = TomarSolicitudAbiertaUseCase(repo_ticket, repo_prof)
        res = use_case.ejecutar(ticket.id, profesional.id)

        if res.exito:
            messages.success(request, res.mensaje)
            return redirect('chat_ticket', ticket_id=ticket.id)
        else:
            messages.error(request, res.mensaje)
            return redirect('bandeja_profesional')


class FinalizarTicketView(LoginRequiredMixin, View):
    """Permite al ingeniero marcar el trabajo como Finalizado con fecha y descripción técnica."""
    def post(self, request, ticket_id):
        profesional = _obtener_o_crear_profesional_para_usuario(request.user)
        ticket = get_object_or_404(TicketAsistencia, id=ticket_id)

        if not profesional:
            messages.error(request, "Acción reservada para el profesional asignado.")
            return redirect('inicio')

        descripcion_finalizacion = request.POST.get('descripcion_finalizacion', '').strip()
        repo_ticket = DjangoTicketRepository()
        use_case = FinalizarTrabajoTicketUseCase(repo_ticket)
        res = use_case.ejecutar(
            ticket_id=ticket.id,
            profesional_id=profesional.id,
            descripcion_finalizacion=descripcion_finalizacion
        )
        if res.exito:
            messages.success(request, res.mensaje)
        else:
            messages.error(request, res.mensaje)
        return redirect('chat_ticket', ticket_id=ticket.id)


class ConfirmarRecepcionView(LoginRequiredMixin, View):
    """Permite al productor confirmar la recepción conforme del trabajo finalizado."""
    def post(self, request, ticket_id):
        productor = _obtener_o_crear_productor_para_usuario(request.user)
        ticket = get_object_or_404(TicketAsistencia, id=ticket_id)

        if not productor:
            messages.error(request, "Solo el productor titular puede confirmar la recepción.")
            return redirect('inicio')

        repo_ticket = DjangoTicketRepository()
        use_case = ConfirmarRecepcionTicketUseCase(repo_ticket)
        res = use_case.ejecutar(ticket_id=ticket.id, productor_id=productor.id)
        if res.exito:
            messages.success(request, res.mensaje)
        else:
            messages.error(request, res.mensaje)

        next_url = request.POST.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect('chat_ticket', ticket_id=ticket.id)
