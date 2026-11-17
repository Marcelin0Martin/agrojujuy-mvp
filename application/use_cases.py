from dataclasses import dataclass
from typing import List, Optional
from domain.entities import (
    UsuarioEntity, ProductorEntity, ProfesionalEntity,
    TicketEntity, MensajeChatEntity, PostComunidadEntity, RespuestaComunidadEntity
)
from domain.ports import (
    RepositorioUsuario, RepositorioProductor, RepositorioProfesional,
    RepositorioTicket, RepositorioChat, RepositorioComunidad
)
from domain.rules import (
    validar_region,
    validar_matricula_ciapa,
    profesional_es_visible_para_productores,
    validar_acceso_chat_ticket,
    ESTADOS_TICKET,
)


@dataclass
class ResultadoOperacion:
    exito: bool
    mensaje: str
    datos: Optional[object] = None


class BuscarProfesionalesUseCase:
    def __init__(self, repo_profesional: RepositorioProfesional):
        self._repo = repo_profesional

    def ejecutar(self, region: Optional[str] = None, especialidad: Optional[str] = None) -> List[ProfesionalEntity]:
        return self._repo.listar_habilitados(region=region, especialidad=especialidad)


class CrearTicketAsistenciaUseCase:
    def __init__(self, repo_ticket: RepositorioTicket, repo_profesional: RepositorioProfesional):
        self._repo_ticket = repo_ticket
        self._repo_profesional = repo_profesional

    def ejecutar(self, productor_id: int, profesional_id: int, titulo: str, descripcion: str) -> ResultadoOperacion:
        profesional = self._repo_profesional.buscar_por_id(profesional_id)
        if not profesional:
            return ResultadoOperacion(exito=False, mensaje="El profesional no existe.")

        if not profesional_es_visible_para_productores(profesional.estado_validacion):
            return ResultadoOperacion(
                exito=False,
                mensaje="El profesional no se encuentra disponible para recibir solicitudes."
            )

        if not titulo.strip() or not descripcion.strip():
            return ResultadoOperacion(exito=False, mensaje="El título y la descripción son obligatorios.")

        ticket = TicketEntity(
            id=0,
            productor_id=productor_id,
            profesional_id=profesional_id,
            titulo=titulo.strip(),
            descripcion=descripcion.strip(),
            modalidad="DIRIGIDA",
            especialidad_requerida=profesional.especialidad,
            estado="Pendiente"
        )
        ticket_creado = self._repo_ticket.crear(ticket)
        return ResultadoOperacion(
            exito=True,
            mensaje="Solicitud dirigida enviada con éxito.",
            datos=ticket_creado
        )


class CrearSolicitudAbiertaUseCase:
    def __init__(self, repo_ticket: RepositorioTicket):
        self._repo_ticket = repo_ticket

    def ejecutar(
        self,
        productor_id: int,
        titulo: str,
        descripcion: str,
        especialidad_requerida: str = ""
    ) -> ResultadoOperacion:
        if not titulo.strip() or not descripcion.strip():
            return ResultadoOperacion(exito=False, mensaje="El título y la descripción del problema son obligatorios.")

        ticket = TicketEntity(
            id=0,
            productor_id=productor_id,
            profesional_id=None,
            titulo=titulo.strip(),
            descripcion=descripcion.strip(),
            modalidad="ABIERTA",
            especialidad_requerida=especialidad_requerida.strip(),
            estado="Pendiente"
        )
        ticket_creado = self._repo_ticket.crear(ticket)
        return ResultadoOperacion(
            exito=True,
            mensaje="Solicitud abierta publicada. Cualquier ingeniero habilitado podrá tomar tu caso.",
            datos=ticket_creado
        )


class TomarSolicitudAbiertaUseCase:
    def __init__(self, repo_ticket: RepositorioTicket, repo_profesional: RepositorioProfesional):
        self._repo_ticket = repo_ticket
        self._repo_profesional = repo_profesional

    def ejecutar(self, ticket_id: int, profesional_id: int) -> ResultadoOperacion:
        profesional = self._repo_profesional.buscar_por_id(profesional_id)
        if not profesional or not profesional_es_visible_para_productores(profesional.estado_validacion):
            return ResultadoOperacion(
                exito=False,
                mensaje="Solo profesionales habilitados por CIAPAJ pueden tomar solicitudes."
            )

        tomado = self._repo_ticket.tomar_solicitud_abierta(ticket_id, profesional_id)
        if not tomado:
            return ResultadoOperacion(
                exito=False,
                mensaje="Esta solicitud ya fue tomada por otro profesional o no está disponible."
            )
        return ResultadoOperacion(
            exito=True,
            mensaje="Has tomado la solicitud exitosamente. El caso quedó asignado y bloqueado para otros ingenieros."
        )


class CambiarEstadoTicketUseCase:
    def __init__(self, repo_ticket: RepositorioTicket):
        self._repo_ticket = repo_ticket

    def ejecutar(self, ticket_id: int, nuevo_estado: str) -> ResultadoOperacion:
        if nuevo_estado not in ESTADOS_TICKET:
            return ResultadoOperacion(exito=False, mensaje="Estado de ticket inválido.")
        self._repo_ticket.actualizar_estado(ticket_id, nuevo_estado)
        return ResultadoOperacion(exito=True, mensaje=f"Ticket actualizado a {nuevo_estado}.")


class FinalizarTrabajoTicketUseCase:
    def __init__(self, repo_ticket: RepositorioTicket):
        self._repo_ticket = repo_ticket

    def ejecutar(self, ticket_id: int, profesional_id: int, descripcion_finalizacion: str) -> ResultadoOperacion:
        ticket = self._repo_ticket.buscar_por_id(ticket_id)
        if not ticket:
            return ResultadoOperacion(exito=False, mensaje="El ticket no existe.")
        if ticket.profesional_id != profesional_id:
            return ResultadoOperacion(exito=False, mensaje="No tienes permiso para finalizar este ticket.")
        if ticket.estado != "Aceptado":
            return ResultadoOperacion(exito=False, mensaje="Solo se pueden finalizar trabajos en estado Aceptado.")
        if not descripcion_finalizacion or not descripcion_finalizacion.strip():
            return ResultadoOperacion(
                exito=False,
                mensaje="Debes ingresar una descripción o informe técnico de finalización."
            )

        self._repo_ticket.finalizar_trabajo(ticket_id, descripcion_finalizacion.strip())
        return ResultadoOperacion(
            exito=True,
            mensaje="Trabajo marcado como Finalizado. Pendiente de confirmación de recepción por el productor."
        )


class ConfirmarRecepcionTicketUseCase:
    def __init__(self, repo_ticket: RepositorioTicket):
        self._repo_ticket = repo_ticket

    def ejecutar(self, ticket_id: int, productor_id: int) -> ResultadoOperacion:
        ticket = self._repo_ticket.buscar_por_id(ticket_id)
        if not ticket:
            return ResultadoOperacion(exito=False, mensaje="El ticket no existe.")
        if ticket.productor_id != productor_id:
            return ResultadoOperacion(exito=False, mensaje="Solo el productor titular puede confirmar la recepción.")
        if ticket.estado != "Finalizado":
            return ResultadoOperacion(exito=False, mensaje="El trabajo aún no ha sido marcado como finalizado por el ingeniero.")

        self._repo_ticket.confirmar_recepcion_productor(ticket_id)
        return ResultadoOperacion(
            exito=True,
            mensaje="Has confirmado la recepción conforme del trabajo técnico."
        )


class EnviarMensajeChatUseCase:
    def __init__(self, repo_chat: RepositorioChat, repo_ticket: RepositorioTicket):
        self._repo_chat = repo_chat
        self._repo_ticket = repo_ticket

    def ejecutar(
        self,
        ticket_id: int,
        emisor_id: int,
        contenido: str,
        emisor_usuario_id: int,
        prod_uid: int,
        prof_uid: Optional[int],
    ) -> ResultadoOperacion:
        if not validar_acceso_chat_ticket(emisor_usuario_id, prod_uid, prof_uid):
            return ResultadoOperacion(exito=False, mensaje="No tienes autorización para participar en este chat.")

        if not contenido or not contenido.strip():
            return ResultadoOperacion(exito=False, mensaje="El mensaje no puede estar vacío.")

        mensaje = MensajeChatEntity(
            id=0,
            ticket_id=ticket_id,
            emisor_id=emisor_id,
            contenido=contenido.strip()
        )
        creado = self._repo_chat.enviar_mensaje(mensaje)
        return ResultadoOperacion(exito=True, mensaje="Mensaje enviado.", datos=creado)


class PublicarEnComunidadUseCase:
    def __init__(self, repo_comunidad: RepositorioComunidad):
        self._repo_comunidad = repo_comunidad

    def ejecutar(self, autor_id: int, titulo: str, contenido: str) -> ResultadoOperacion:
        if not titulo.strip() or not contenido.strip():
            return ResultadoOperacion(exito=False, mensaje="El título y contenido del post son obligatorios.")

        post = PostComunidadEntity(
            id=0,
            autor_id=autor_id,
            titulo=titulo.strip(),
            contenido=contenido.strip()
        )
        post_creado = self._repo_comunidad.crear_post(post)
        return ResultadoOperacion(exito=True, mensaje="Publicación creada en el muro comunitario.", datos=post_creado)


class ResponderPostComunidadUseCase:
    def __init__(self, repo_comunidad: RepositorioComunidad):
        self._repo_comunidad = repo_comunidad

    def ejecutar(self, post_id: int, autor_id: int, contenido: str) -> ResultadoOperacion:
        if not contenido.strip():
            return ResultadoOperacion(exito=False, mensaje="La respuesta no puede estar vacía.")

        respuesta = RespuestaComunidadEntity(
            id=0,
            post_id=post_id,
            autor_id=autor_id,
            contenido=contenido.strip()
        )
        resp_creada = self._repo_comunidad.agregar_respuesta(respuesta)
        return ResultadoOperacion(exito=True, mensaje="Respuesta agregada con éxito.", datos=resp_creada)


class ValidarProfesionalAdminUseCase:
    def __init__(self, repo_profesional: RepositorioProfesional):
        self._repo = repo_profesional

    def habilitar(self, profesional_id: int) -> ResultadoOperacion:
        self._repo.cambiar_estado(profesional_id, "Habilitado")
        return ResultadoOperacion(exito=True, mensaje="Profesional habilitado institucionalmente.")

    def rechazar_o_suspender(self, profesional_id: int) -> ResultadoOperacion:
        self._repo.cambiar_estado(profesional_id, "Suspendido")
        return ResultadoOperacion(exito=True, mensaje="Profesional suspendido / rechazado.")
