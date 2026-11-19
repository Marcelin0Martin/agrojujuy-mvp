from django.urls import path
from .views import MuroComunidadView, CrearPostComunidadView

urlpatterns = [
    path('muro/', MuroComunidadView.as_view(), name='foro_comunidad'),
    path('muro/nueva/', CrearPostComunidadView.as_view(), name='foro_nueva_consulta'),
]
