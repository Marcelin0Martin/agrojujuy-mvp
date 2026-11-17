import re
from typing import Optional

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
ESTADOS_TICKET = ['Pendiente', 'Aceptado', 'Finalizado', 'Cerrado']
MODALIDADES_TICKET = ['DIRIGIDA', 'ABIERTA']


def validar_region(region: str) -> bool:
    return region in REGIONES_VALIDAS


def validar_matricula_ciapa(matricula: str) -> bool:
    """
    Valida el número de matrícula provincial (CIAPAJ).
    Debe ser no vacía, alfanumérica limpia o con formato estándar de matrícula (ej. MP-1234, 1234/J, etc.)
    """
    if not matricula or not matricula.strip():
        return False
    limpio = matricula.strip()
    return bool(re.match(r'^[A-Za-z0-9\-\/]{3,20}$', limpio))


def validar_dni(dni: str) -> bool:
    """Valida que el DNI tenga entre 7 y 8 dígitos numéricos."""
    if not dni:
        return False
    return bool(re.match(r'^\d{7,8}$', dni.strip()))


def validar_renspa(renspa: str) -> bool:
    """
    Valida el número de RENSPA (Registro Nacional Sanitario de Productores Agropecuarios).
    Acepta formato estándar con puntos/guiones/barras o dígitos (ej. 09.001.0.00123/00 o código alfanumérico de 6 a 22 caracteres).
    """
    if not renspa:
        return False
    return bool(re.match(r'^[0-9\.\-\/A-Za-z]{6,22}$', renspa.strip()))


def validar_telefono(telefono: str) -> bool:
    """
    Valida el formato estricto de número telefónico:
    Permite prefijo +, espacios o guiones con entre 8 y 15 dígitos reales.
    """
    if not telefono or not telefono.strip():
        return False
    limpio = telefono.strip()
    if not re.match(r'^\+?[\d\s\-]{8,20}$', limpio):
        return False
    solo_digitos = re.sub(r'\D', '', limpio)
    return 8 <= len(solo_digitos) <= 15


def profesional_es_visible_para_productores(estado_validacion: str) -> bool:
    """
    Lógica de restricción del SDD:
    Si un profesional está 'Pendiente' o 'Suspendido', desaparece automáticamente del buscador.
    Solo 'Habilitado' es visible.
    """
    return estado_validacion == 'Habilitado'


def validar_acceso_chat_ticket(
    usuario_id: int,
    ticket_productor_user_id: int,
    ticket_profesional_user_id: Optional[int],
) -> bool:
    """
    El chat 1 a 1 de asistencia técnica solo puede ser visualizado y respondido por
    el productor solicitante o el profesional asignado.
    """
    participantes = [ticket_productor_user_id]
    if ticket_profesional_user_id is not None:
        participantes.append(ticket_profesional_user_id)
    return usuario_id in participantes
