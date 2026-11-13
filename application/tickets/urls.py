from django.urls import path
from .views import (
    BandejaProductorView,
    BandejaProfesionalView,
    SolicitarAsistenciaView,
    ChatTicketView,
    AceptarTicketView,
)

urlpatterns = [
    path('productor/solicitudes/', BandejaProductorView.as_view(), name='bandeja_productor'),
    path('profesional/trabajos/', BandejaProfesionalView.as_view(), name='bandeja_profesional'),
    path('solicitar/<int:profesional_id>/', SolicitarAsistenciaView.as_view(), name='solicitar_asistencia'),
    path('chat/<int:ticket_id>/', ChatTicketView.as_view(), name='chat_ticket'),
    path('aceptar/<int:ticket_id>/', AceptarTicketView.as_view(), name='aceptar_ticket'),
]
