from django.contrib import admin
from django.urls import path, include
from application.community.views import CrearPostComunidadView

# Personalización del Admin Institucional CIAPAJ
admin.site.site_header = "AgroJujuy - Panel Institucional y Auditoría CIAPAJ"
admin.site.site_title = "AgroJujuy Admin"
admin.site.index_title = "Control Institucional de Profesionales y Productores"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('application.users.urls')),
    path('tickets/', include('application.tickets.urls')),
    path('comunidad/', include('application.community.urls')),
    path('foro/nueva/', CrearPostComunidadView.as_view(), name='foro_nueva'),
]
