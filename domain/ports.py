from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import (
    UsuarioEntity, ProductorEntity, ProfesionalEntity,
    TicketEntity, MensajeChatEntity, PostComunidadEntity, RespuestaComunidadEntity
)


class RepositorioUsuario(ABC):
    @abstractmethod
    def buscar_por_id(self, user_id: int) -> Optional[UsuarioEntity]:
        ...

    @abstractmethod
    def buscar_por_username(self, username: str) -> Optional[UsuarioEntity]:
        ...


class RepositorioProductor(ABC):
    @abstractmethod
    def buscar_por_usuario_id(self, usuario_id: int) -> Optional[ProductorEntity]:
        ...

    @abstractmethod
    def guardar(self, productor: ProductorEntity) -> ProductorEntity:
        ...


class RepositorioProfesional(ABC):
    @abstractmethod
    def buscar_por_id(self, profesional_id: int) -> Optional[ProfesionalEntity]:
        ...

    @abstractmethod
    def buscar_por_usuario_id(self, usuario_id: int) -> Optional[ProfesionalEntity]:
        ...

    @abstractmethod
    def listar_habilitados(self, region: Optional[str] = None, especialidad: Optional[str] = None) -> List[ProfesionalEntity]:
        ...

    @abstractmethod
    def cambiar_estado(self, profesional_id: int, nuevo_estado: str) -> None:
        ...


class RepositorioTicket(ABC):
    @abstractmethod
    def crear(self, ticket: TicketEntity) -> TicketEntity:
        ...

    @abstractmethod
    def buscar_por_id(self, ticket_id: int) -> Optional[TicketEntity]:
        ...

    @abstractmethod
    def listar_ultimos_por_productor(self, productor_id: int, limite: int = 5) -> List[TicketEntity]:
        ...

    @abstractmethod
    def listar_ultimos_por_profesional(self, profesional_id: int, limite: int = 5) -> List[TicketEntity]:
        ...

    @abstractmethod
    def actualizar_estado(self, ticket_id: int, nuevo_estado: str) -> None:
        ...

    @abstractmethod
    def tomar_solicitud_abierta(self, ticket_id: int, profesional_id: int) -> bool:
        ...

    @abstractmethod
    def finalizar_trabajo(self, ticket_id: int, descripcion_finalizacion: str) -> None:
        ...

    @abstractmethod
    def confirmar_recepcion_productor(self, ticket_id: int) -> None:
        ...


class RepositorioChat(ABC):
    @abstractmethod
    def enviar_mensaje(self, mensaje: MensajeChatEntity) -> MensajeChatEntity:
        ...

    @abstractmethod
    def listar_mensajes_por_ticket(self, ticket_id: int) -> List[MensajeChatEntity]:
        ...


class RepositorioComunidad(ABC):
    @abstractmethod
    def listar_posts(self) -> List[PostComunidadEntity]:
        ...

    @abstractmethod
    def crear_post(self, post: PostComunidadEntity) -> PostComunidadEntity:
        ...

    @abstractmethod
    def agregar_respuesta(self, respuesta: RespuestaComunidadEntity) -> RespuestaComunidadEntity:
        ...

    @abstractmethod
    def listar_respuestas(self, post_id: int) -> List[RespuestaComunidadEntity]:
        ...
