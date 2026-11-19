from django.db.models import Q
from django.urls import reverse
from application.tickets.models import MensajeTicket
from application.community.models import RespuestaComunidad


def get_user_session_key(user):
    return f"agrojujuy_read_notifs_{user.id}"


def get_read_notification_ids(request):
    if not request.user.is_authenticated:
        return set()
    key = get_user_session_key(request.user)
    return set(request.session.get(key, []))


def mark_notifications_as_read(request, notif_ids):
    if not request.user.is_authenticated:
        return
    key = get_user_session_key(request.user)
    current = list(request.session.get(key, []))
    current_set = set(current)
    for nid in notif_ids:
        if nid not in current_set:
            current.append(nid)
            current_set.add(nid)
    # Mantener un tamaño liviano en sesión por usuario
    request.session[key] = current[-500:]
    request.session.modified = True


def mark_ticket_messages_read(request, ticket_id):
    if not request.user.is_authenticated:
        return
    msg_ids = MensajeTicket.objects.filter(
        ticket_id=ticket_id
    ).exclude(emisor=request.user).values_list('id', flat=True)
    mark_notifications_as_read(request, [f"chat_{mid}" for mid in msg_ids])


def obtener_notificaciones_usuario(request, limit=50):
    """
    Construye las notificaciones del usuario autenticado consultando directamente
    las entidades existentes del DER (MensajeTicket y RespuestaComunidad),
    sin alterar el esquema de base de datos ni agregar nuevas tablas.

    Asegura estricta privacidad e introspección por rol:
    - ADMIN: Rol institucional y de auditoría; no recibe alertas privadas de tickets ni hilos ajenos.
    - PRODUCER: Únicamente alertas de sus propios tickets como productor y sus temas del foro.
    - PROFESSIONAL: Únicamente alertas de los tickets formalmente asignados a su matrícula y sus temas del foro.
    """
    if not request.user.is_authenticated:
        return [], 0

    user = request.user
    effective_role = request.session.get('simulated_role') or getattr(user, 'role', None)

    # El rol Administrador es institucional y de auditoría; cada mensaje y consulta es estrictamente
    # personal y privado para los usuarios directos (productor o profesional asignado).
    if effective_role == 'ADMIN' or (user.role == 'ADMIN' and not request.session.get('simulated_role')):
        return [], 0

    read_ids = get_read_notification_ids(request)
    notificaciones = []

    # 1. Mensajes recibidos en conversaciones de Chat 1 a 1 (aislados estrictamente al usuario)
    if effective_role == 'PRODUCER':
        chat_filter = Q(ticket__productor__usuario=user)
    elif effective_role == 'PROFESSIONAL':
        chat_filter = Q(ticket__profesional__usuario=user)
    else:
        chat_filter = Q(ticket__productor__usuario=user) | Q(ticket__profesional__usuario=user)

    mensajes_chat = (
        MensajeTicket.objects.select_related('ticket', 'emisor')
        .filter(chat_filter)
        .exclude(emisor=user)
        .order_by('-fecha_envio')[:limit]
    )

    for msg in mensajes_chat:
        nid = f"chat_{msg.id}"
        autor_nombre = msg.emisor.get_full_name() or msg.emisor.username
        rol_label = "Ingeniero CIAPAJ" if msg.emisor.role == 'PROFESSIONAL' else (
            "Productor" if msg.emisor.role == 'PRODUCER' else "Administrador"
        )
        notificaciones.append({
            'id': nid,
            'tipo': 'chat',
            'tipo_label': 'Mensaje de Chat 1 a 1',
            'titulo': f"Mensaje en Consulta #{msg.ticket_id}: {msg.ticket.titulo}",
            'autor': autor_nombre,
            'autor_rol': rol_label,
            'extracto': msg.contenido,
            'fecha': msg.fecha_envio,
            'url': reverse('chat_ticket', args=[msg.ticket_id]),
            'leida': nid in read_ids,
        })

    # 2. Comentarios recibidos en hilos del Foro Comunitario (creados o participados por el usuario)
    respuestas_foro = (
        RespuestaComunidad.objects.select_related('post', 'autor')
        .filter(
            Q(post__autor=user) | Q(post__respuestas__autor=user)
        )
        .exclude(autor=user)
        .distinct()
        .order_by('-fecha_creacion')[:limit]
    )

    for resp in respuestas_foro:
        nid = f"foro_{resp.id}"
        autor_nombre = resp.autor.get_full_name() or resp.autor.username
        rol_label = "Ingeniero CIAPAJ" if resp.autor.role == 'PROFESSIONAL' else (
            "Productor" if resp.autor.role == 'PRODUCER' else "Administrador"
        )
        notificaciones.append({
            'id': nid,
            'tipo': 'foro',
            'tipo_label': 'Comentario en el Foro',
            'titulo': f"Nuevo comentario en: {resp.post.titulo}",
            'autor': autor_nombre,
            'autor_rol': rol_label,
            'extracto': resp.contenido,
            'fecha': resp.fecha_creacion,
            'url': f"{reverse('foro_comunidad')}#post-{resp.post_id}",
            'leida': nid in read_ids,
        })

    notificaciones.sort(key=lambda x: x['fecha'], reverse=True)
    notificaciones = notificaciones[:limit]
    unread_count = sum(1 for n in notificaciones if not n['leida'])
    return notificaciones, unread_count
