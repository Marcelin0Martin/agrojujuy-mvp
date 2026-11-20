from typing import List, Optional
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from domain.ports import (
    RepositorioUsuario, RepositorioProductor, RepositorioProfesional,
    RepositorioTicket, RepositorioChat, RepositorioComunidad
)
from domain.entities import (
    UsuarioEntity, ProductorEntity, ProfesionalEntity,
    TicketEntity, MensajeChatEntity, PostComunidadEntity, RespuestaComunidadEntity
)
from domain.rules import profesional_es_visible_para_productores
from application.users.models import CustomUser, Productor, Profesional
from application.tickets.models import TicketAsistencia, MensajeTicket
from application.community.models import PostComunidad, RespuestaComunidad


class DjangoUsuarioRepository(RepositorioUsuario):
    def buscar_por_id(self, user_id: int) -> Optional[UsuarioEntity]:
        try:
            u = CustomUser.objects.get(id=user_id)
            return UsuarioEntity(
                id=u.id,
                username=u.username,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
                is_active=u.is_active
            )
        except CustomUser.DoesNotExist:
            return None

    def buscar_por_username(self, username: str) -> Optional[UsuarioEntity]:
        try:
            u = CustomUser.objects.get(username=username)
            return UsuarioEntity(
                id=u.id,
                username=u.username,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
                is_active=u.is_active
            )
        except CustomUser.DoesNotExist:
            return None


class DjangoProductorRepository(RepositorioProductor):
    def buscar_por_usuario_id(self, usuario_id: int) -> Optional[ProductorEntity]:
        try:
            p = Productor.objects.get(usuario_id=usuario_id)
            return ProductorEntity(
                id=p.id,
                usuario_id=p.usuario_id,
                region=p.region,
                rubro_productivo=p.rubro_productivo,
                dni=p.dni,
                renspa=p.renspa,
                telefono=p.telefono,
                direccion_finca=p.direccion_finca
            )
        except Productor.DoesNotExist:
            return None

    def guardar(self, productor: ProductorEntity) -> ProductorEntity:
        p, _ = Productor.objects.update_or_create(
            id=productor.id if productor.id > 0 else None,
            defaults={
                'usuario_id': productor.usuario_id,
                'region': productor.region,
                'rubro_productivo': productor.rubro_productivo,
                'dni': productor.dni,
                'renspa': productor.renspa,
                'telefono': productor.telefono,
                'direccion_finca': productor.direccion_finca,
            }
        )
        productor.id = p.id
        return productor


class DjangoProfesionalRepository(RepositorioProfesional):
    def _to_entity(self, p: Profesional) -> ProfesionalEntity:
        nombre = p.usuario.get_full_name() or p.usuario.username
        return ProfesionalEntity(
            id=p.id,
            usuario_id=p.usuario_id,
            matricula_provincial=p.matricula_provincial,
            especialidad=p.especialidad,
            zonas_cobertura=p.get_zonas_list(),
            especialidades_lista=p.get_especialidades_list(),
            especialidad_propuesta=p.especialidad_propuesta,
            nombre_completo=nombre,
            telefono=p.telefono,
            biografia=p.biografia,
            estado_validacion=p.estado_validacion,
            fecha_solicitud=p.fecha_solicitud
        )

    def buscar_por_id(self, profesional_id: int) -> Optional[ProfesionalEntity]:
        try:
            p = Profesional.objects.select_related('usuario').get(id=profesional_id)
            return self._to_entity(p)
        except Profesional.DoesNotExist:
            return None

    def buscar_por_usuario_id(self, usuario_id: int) -> Optional[ProfesionalEntity]:
        try:
            p = Profesional.objects.select_related('usuario').get(usuario_id=usuario_id)
            return self._to_entity(p)
        except Profesional.DoesNotExist:
            return None

    def listar_habilitados(self, region: Optional[str] = None, especialidad: Optional[str] = None) -> List[ProfesionalEntity]:
        """
        Regla de negocio: Si un profesional está 'Pendiente' o 'Suspendido',
        desaparece automáticamente del buscador.
        Soporta múltiples especialidades y zonas.
        """
        qs = Profesional.objects.select_related('usuario').filter(estado_validacion='Habilitado')
        if region:
            qs = qs.filter(zonas_cobertura__icontains=region)
        if especialidad:
            qs = qs.filter(
                Q(especialidad__icontains=especialidad) |
                Q(especialidad_propuesta__icontains=especialidad)
            )

        resultado = []
        for p in qs:
            if profesional_es_visible_para_productores(p.estado_validacion):
                resultado.append(self._to_entity(p))
        return resultado

    def cambiar_estado(self, profesional_id: int, nuevo_estado: str) -> None:
        Profesional.objects.filter(id=profesional_id).update(estado_validacion=nuevo_estado)


class DjangoTicketRepository(RepositorioTicket):
    def _to_entity(self, t: TicketAsistencia) -> TicketEntity:
        return TicketEntity(
            id=t.id,
            productor_id=t.productor_id,
            profesional_id=t.profesional_id,
            titulo=t.titulo,
            descripcion=t.descripcion,
            modalidad=t.modalidad,
            especialidad_requerida=t.especialidad_requerida,
            estado=t.estado,
            fecha_creacion=t.fecha_creacion,
            descripcion_finalizacion=t.descripcion_finalizacion,
            fecha_finalizacion=t.fecha_finalizacion,
            confirmado_por_productor=t.confirmado_por_productor,
            fecha_confirmacion=t.fecha_confirmacion,
        )

    def crear(self, ticket: TicketEntity) -> TicketEntity:
        t = TicketAsistencia.objects.create(
            productor_id=ticket.productor_id,
            profesional_id=ticket.profesional_id,
            titulo=ticket.titulo,
            descripcion=ticket.descripcion,
            modalidad=ticket.modalidad,
            especialidad_requerida=ticket.especialidad_requerida,
            estado=ticket.estado
        )
        return self._to_entity(t)

    def buscar_por_id(self, ticket_id: int) -> Optional[TicketEntity]:
        try:
            t = TicketAsistencia.objects.get(id=ticket_id)
            return self._to_entity(t)
        except TicketAsistencia.DoesNotExist:
            return None

    def listar_ultimos_por_productor(self, productor_id: int, limite: int = 5) -> List[TicketEntity]:
        qs = TicketAsistencia.objects.filter(productor_id=productor_id).order_by('-fecha_creacion')[:limite]
        return [self._to_entity(t) for t in qs]

    def listar_ultimos_por_profesional(self, profesional_id: int, limite: int = 5) -> List[TicketEntity]:
        qs = TicketAsistencia.objects.filter(profesional_id=profesional_id).order_by('-fecha_creacion')[:limite]
        return [self._to_entity(t) for t in qs]

    def actualizar_estado(self, ticket_id: int, nuevo_estado: str) -> None:
        TicketAsistencia.objects.filter(id=ticket_id).update(estado=nuevo_estado)

    def tomar_solicitud_abierta(self, ticket_id: int, profesional_id: int) -> bool:
        with transaction.atomic():
            try:
                t = TicketAsistencia.objects.select_for_update().get(id=ticket_id)
                if t.estado != 'Pendiente' or (t.profesional_id is not None and t.profesional_id != profesional_id):
                    return False
                t.profesional_id = profesional_id
                t.estado = 'Aceptado'
                t.save(update_fields=['profesional_id', 'estado', 'fecha_actualizacion'])
                return True
            except TicketAsistencia.DoesNotExist:
                return False

    def convertir_a_abierta(self, ticket_id: int) -> None:
        TicketAsistencia.objects.filter(id=ticket_id, estado='Pendiente').update(
            modalidad='ABIERTA',
            profesional=None,
            fecha_actualizacion=timezone.now()
        )

    def eliminar_pendiente(self, ticket_id: int) -> None:
        TicketAsistencia.objects.filter(id=ticket_id, estado='Pendiente').delete()

    def finalizar_trabajo(self, ticket_id: int, descripcion_finalizacion: str) -> None:
        TicketAsistencia.objects.filter(id=ticket_id).update(
            estado='Finalizado',
            descripcion_finalizacion=descripcion_finalizacion,
            fecha_finalizacion=timezone.now()
        )

    def confirmar_recepcion_productor(self, ticket_id: int) -> None:
        TicketAsistencia.objects.filter(id=ticket_id).update(
            confirmado_por_productor=True,
            fecha_confirmacion=timezone.now()
        )


class DjangoChatRepository(RepositorioChat):
    def enviar_mensaje(self, mensaje: MensajeChatEntity) -> MensajeChatEntity:
        m = MensajeTicket.objects.create(
            ticket_id=mensaje.ticket_id,
            emisor_id=mensaje.emisor_id,
            contenido=mensaje.contenido
        )
        mensaje.id = m.id
        mensaje.fecha_envio = m.fecha_envio
        return mensaje

    def listar_mensajes_por_ticket(self, ticket_id: int) -> List[MensajeChatEntity]:
        qs = MensajeTicket.objects.filter(ticket_id=ticket_id).order_by('fecha_envio')
        return [
            MensajeChatEntity(
                id=m.id,
                ticket_id=m.ticket_id,
                emisor_id=m.emisor_id,
                contenido=m.contenido,
                fecha_envio=m.fecha_envio
            ) for m in qs
        ]


class DjangoComunidadRepository(RepositorioComunidad):
    def listar_posts(self) -> List[PostComunidadEntity]:
        qs = PostComunidad.objects.all().order_by('-fecha_creacion')
        return [
            PostComunidadEntity(
                id=p.id,
                autor_id=p.autor_id,
                titulo=p.titulo,
                contenido=p.contenido,
                fecha_creacion=p.fecha_creacion,
                respuestas_count=p.respuestas.count()
            ) for p in qs
        ]

    def crear_post(self, post: PostComunidadEntity) -> PostComunidadEntity:
        p = PostComunidad.objects.create(
            autor_id=post.autor_id,
            titulo=post.titulo,
            contenido=post.contenido
        )
        post.id = p.id
        post.fecha_creacion = p.fecha_creacion
        return post

    def agregar_respuesta(self, respuesta: RespuestaComunidadEntity) -> RespuestaComunidadEntity:
        r = RespuestaComunidad.objects.create(
            post_id=respuesta.post_id,
            autor_id=respuesta.autor_id,
            contenido=respuesta.contenido
        )
        respuesta.id = r.id
        respuesta.fecha_creacion = r.fecha_creacion
        return respuesta

    def listar_respuestas(self, post_id: int) -> List[RespuestaComunidadEntity]:
        qs = RespuestaComunidad.objects.filter(post_id=post_id).order_by('fecha_creacion')
        return [
            RespuestaComunidadEntity(
                id=r.id,
                post_id=r.post_id,
                autor_id=r.autor_id,
                contenido=r.contenido,
                fecha_creacion=r.fecha_creacion
            ) for r in qs
        ]
