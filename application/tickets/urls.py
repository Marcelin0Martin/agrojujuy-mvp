from django.urls import path
from .views import (
    BandejaProductorView,
    BandejaProfesionalView,
    SolicitarAsistenciaView,
    SolicitarAsistenciaAbiertaView,
    ChatTicketView,
    AceptarTicketView,
    FinalizarTicketView,
    ConfirmarRecepcionView,
)

urlpatterns = [
    path('productor/solicitudes/', BandejaProductorView.as_view(), name='bandeja_productor'),
    path('profesional/trabajos/', BandejaProfesionalView.as_view(), name='bandeja_profesional'),
    path('solicitar/<int:profesional_id>/', SolicitarAsistenciaView.as_view(), name='solicitar_asistencia'),
    path('solicitar-abierta/', SolicitarAsistenciaAbiertaView.as_view(), name='solicitar_asistencia_abierta'),
    path('chat/<int:ticket_id>/', ChatTicketView.as_view(), name='chat_ticket'),
    path('aceptar/<int:ticket_id>/', AceptarTicketView.as_view(), name='aceptar_ticket'),
    path('finalizar/<int:ticket_id>/', FinalizarTicketView.as_view(), name='finalizar_ticket'),
    path('confirmar/<int:ticket_id>/', ConfirmarRecepcionView.as_view(), name='confirmar_recepcion'),
]
