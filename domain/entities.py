from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class UsuarioEntity:
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str  # 'PRODUCER', 'PROFESSIONAL', 'ADMIN'
    is_active: bool = True


@dataclass
class ProductorEntity:
    id: int
    usuario_id: int
    region: str  # 'Puna', 'Valles', 'Yungas', 'Quebrada'
    rubro_productivo: str
    telefono: str = ""
    direccion_finca: str = ""


@dataclass
class ProfesionalEntity:
    id: int
    usuario_id: int
    matricula_provincial: str
    especialidad: str
    zonas_cobertura: List[str] = field(default_factory=list)
    telefono: str = ""
    biografia: str = ""
    estado_validacion: str = "Pendiente"  # 'Pendiente', 'Habilitado', 'Suspendido'
    fecha_solicitud: Optional[datetime] = None


@dataclass
class TicketEntity:
    id: int
    productor_id: int
    profesional_id: int
    titulo: str
    descripcion: str
    estado: str = "Pendiente"  # 'Pendiente', 'Aceptado', 'Cerrado'
    fecha_creacion: Optional[datetime] = None


@dataclass
class MensajeChatEntity:
    id: int
    ticket_id: int
    emisor_id: int
    contenido: str
    fecha_envio: Optional[datetime] = None


@dataclass
class PostComunidadEntity:
    id: int
    autor_id: int
    titulo: str
    contenido: str
    fecha_creacion: Optional[datetime] = None
    respuestas_count: int = 0


@dataclass
class RespuestaComunidadEntity:
    id: int
    post_id: int
    autor_id: int
    contenido: str
    fecha_creacion: Optional[datetime] = None
