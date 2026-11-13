from dataclasses import dataclass
from typing import List, Optional, Tuple
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
    validar_acceso_chat_ticket
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
        # El repositorio ya asegura retornar solo Habilitados
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
            return ResultadoOperacion(exito=False, mensaje="El profesional no se encuentra disponible para recibir solicitudes.")

        if not titulo.strip() or not descripcion.strip():
            return ResultadoOperacion(exito=False, mensaje="El título y la descripción son obligatorios.")

        ticket = TicketEntity(
            id=0,
            productor_id=productor_id,
            profesional_id=profesional_id,
            titulo=titulo.strip(),
            descripcion=descripcion.strip(),
            estado="Pendiente"
        )
        ticket_creado = self._repo_ticket.crear(ticket)
        return ResultadoOperacion(exito=True, mensaje="Solicitud de asistencia enviada con éxito.", datos=ticket_creado)


class CambiarEstadoTicketUseCase:
    def __init__(self, repo_ticket: RepositorioTicket):
        self._repo_ticket = repo_ticket

    def ejecutar(self, ticket_id: int, nuevo_estado: str) -> ResultadoOperacion:
        if nuevo_estado not in ["Pendiente", "Aceptado", "Cerrado"]:
            return ResultadoOperacion(exito=False, mensaje="Estado de ticket inválido.")
        self._repo_ticket.actualizar_estado(ticket_id, nuevo_estado)
        return ResultadoOperacion(exito=True, mensaje=f"Ticket actualizado a {nuevo_estado}.")


class EnviarMensajeChatUseCase:
    def __init__(self, repo_chat: RepositorioChat, repo_ticket: RepositorioTicket):
        self._repo_chat = repo_chat
        self._repo_ticket = repo_ticket

    def ejecutar(self, ticket_id: int, emisor_id: int, contenido: str, emisor_usuario_id: int, prod_uid: int, prof_uid: int) -> ResultadoOperacion:
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
