import re
from typing import List

REGIONES_VALIDAS = ['Puna', 'Valles', 'Yungas', 'Quebrada']

ESPECIALIDADES_VALIDAS = [
    'Agronomía General',
    'Riego y Suelos',
    'Sanidad Vegetal y Plagas',
    'Horticultura',
    'Fruticultura',
    'Producción Ganadera y Forrajes',
    'Agroecología',
    'Cultivos Andinos',
]

ROLES_VALIDOS = ['PRODUCER', 'PROFESSIONAL', 'ADMIN']
ESTADOS_PROFESIONAL = ['Pendiente', 'Habilitado', 'Suspendido']
ESTADOS_TICKET = ['Pendiente', 'Aceptado', 'Cerrado']


def validar_region(region: str) -> bool:
    return region in REGIONES_VALIDAS


def validar_matricula_ciapa(matricula: str) -> bool:
    """
    Valida el número de matrícula provincial (CIAPA).
    Debe ser no vacía, alfanumérica limpia o con formato estándar de matrícula (ej. MP-1234, 1234/J, etc.)
    """
    if not matricula or not matricula.strip():
        return False
    limpio = matricula.strip()
    return bool(re.match(r'^[A-Za-z0-9\-\/]{3,20}$', limpio))


def profesional_es_visible_para_productores(estado_validacion: str) -> bool:
    """
    Lógica de restricción del SDD:
    Si un profesional está 'Pendiente' o 'Suspendido', desaparece automáticamente del buscador.
    Solo 'Habilitado' es visible.
    """
    return estado_validacion == 'Habilitado'


def validar_acceso_chat_ticket(usuario_id: int, ticket_productor_user_id: int, ticket_profesional_user_id: int) -> bool:
    """
    El chat 1 a 1 de asistencia técnica solo puede ser visualizado y respondido por
    el productor solicitante o el profesional asignado (o un administrador).
    """
    return usuario_id in [ticket_productor_user_id, ticket_profesional_user_id]
