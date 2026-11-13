from django.contrib import admin
from django.urls import path, include

# Personalización del Admin Institucional CIAPA
admin.site.site_header = "AgroJujuy - Panel Institucional y Auditoría CIAPA"
admin.site.site_title = "AgroJujuy Admin"
admin.site.index_title = "Control Institucional de Profesionales y Productores"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('application.users.urls')),
    path('tickets/', include('application.tickets.urls')),
    path('comunidad/', include('application.community.urls')),
]
