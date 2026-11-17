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
    dni: str = ""
    renspa: str = ""
    telefono: str = ""
    direccion_finca: str = ""


@dataclass
class ProfesionalEntity:
    id: int
    usuario_id: int
    matricula_provincial: str
    especialidad: str
    zonas_cobertura: List[str] = field(default_factory=list)
    especialidades_lista: List[str] = field(default_factory=list)
    especialidad_propuesta: str = ""
    nombre_completo: str = ""
    telefono: str = ""
    biografia: str = ""
    estado_validacion: str = "Pendiente"  # 'Pendiente', 'Habilitado', 'Suspendido'
    fecha_solicitud: Optional[datetime] = None


@dataclass
class TicketEntity:
    id: int
    productor_id: int
    profesional_id: Optional[int]
    titulo: str
    descripcion: str
    modalidad: str = "DIRIGIDA"  # 'DIRIGIDA', 'ABIERTA'
    especialidad_requerida: str = ""
    estado: str = "Pendiente"  # 'Pendiente', 'Aceptado', 'Finalizado', 'Cerrado'
    fecha_creacion: Optional[datetime] = None
    descripcion_finalizacion: str = ""
    fecha_finalizacion: Optional[datetime] = None
    confirmado_por_productor: bool = False
    fecha_confirmacion: Optional[datetime] = None


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
