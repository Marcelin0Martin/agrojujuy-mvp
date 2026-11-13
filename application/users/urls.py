from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    InicioView,
    LoginPersonalizadoView,
    RegistroProductorView,
    RegistroProfesionalView,
    PantallaEsperaView,
    BuscadorProfesionalesView,
    VitrinaProfesionalView,
    PerfilProductorView,
    PerfilProfesionalView,
    cambiar_rol_temporal,
)

urlpatterns = [
    path('', InicioView.as_view(), name='inicio'),
    path('login/', LoginPersonalizadoView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='inicio'), name='logout'),
    path('registro/productor/', RegistroProductorView.as_view(), name='registro_productor'),
    path('registro/profesional/', RegistroProfesionalView.as_view(), name='registro_profesional'),
    path('espera-validacion/', PantallaEsperaView.as_view(), name='espera_validacion'),
    path('buscador/', BuscadorProfesionalesView.as_view(), name='buscador_profesionales'),
    path('profesional/<int:pk>/', VitrinaProfesionalView.as_view(), name='vitrina_profesional'),
    path('perfil/productor/', PerfilProductorView.as_view(), name='perfil_productor'),
    path('perfil/profesional/', PerfilProfesionalView.as_view(), name='perfil_profesional'),
    path('cambiar-rol-temporal/', cambiar_rol_temporal, name='cambiar_rol_temporal'),
]
