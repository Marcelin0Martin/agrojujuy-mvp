from django.urls import path
from .views import MuroComunidadView

urlpatterns = [
    path('muro/', MuroComunidadView.as_view(), name='foro_comunidad'),
]
