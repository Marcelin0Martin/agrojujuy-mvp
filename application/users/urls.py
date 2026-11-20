from django.urls import path, reverse_lazy
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from .forms import AccessiblePasswordResetForm, AccessibleSetPasswordForm
from .views import (
    InicioView,
    NosotrosView,
    LoginPersonalizadoView,
    LoginAdminView,
    RegistroProductorView,
    RegistroProfesionalView,
    PantallaEsperaView,
    BuscadorProfesionalesView,
    VitrinaProfesionalView,
    PerfilProductorView,
    PerfilProfesionalView,
    NotificacionesView,
    marcar_notificacion_leida,
    PanelAdminProfesionalesView,
    CambiarEstadoProfesionalAdminView,
    validar_username_ajax,
    cambiar_rol_temporal,
)

urlpatterns = [
    path('', InicioView.as_view(), name='inicio'),
    path('nosotros/', NosotrosView.as_view(), name='nosotros'),
    path('login/', LoginPersonalizadoView.as_view(), name='login'),
    path('login/admin/', LoginAdminView.as_view(), name='login_admin'),
    path('logout/', LogoutView.as_view(next_page='inicio'), name='logout'),
    path('registro/productor/', RegistroProductorView.as_view(), name='registro_productor'),
    path('registro/profesional/', RegistroProfesionalView.as_view(), name='registro_profesional'),
    path('espera-validacion/', PantallaEsperaView.as_view(), name='espera_validacion'),
    path('buscador/', BuscadorProfesionalesView.as_view(), name='buscador_profesionales'),
    path('profesional/<int:pk>/', VitrinaProfesionalView.as_view(), name='vitrina_profesional'),
    path('perfil/productor/', PerfilProductorView.as_view(), name='perfil_productor'),
    path('perfil/profesional/', PerfilProfesionalView.as_view(), name='perfil_profesional'),
    path('notificaciones/', NotificacionesView.as_view(), name='notificaciones'),
    path('notificaciones/marcar-leida/', marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('panel-admin/profesionales/', PanelAdminProfesionalesView.as_view(), name='panel_admin_profesionales'),
    path('panel-admin/profesionales/<int:profesional_id>/estado/', CambiarEstadoProfesionalAdminView.as_view(), name='cambiar_estado_profesional_admin'),
    path('api/validar-username/', validar_username_ajax, name='validar_username_ajax'),
    path('cambiar-rol-temporal/', cambiar_rol_temporal, name='cambiar_rol_temporal'),

    # Flujo de Recuperación de Contraseña con Tokens de Un Solo Uso (OWASP ASVS L2)
    path(
        'password-reset/',
        PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            email_template_name='users/password_reset_email.html',
            form_class=AccessiblePasswordResetForm,
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/enviado/',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            form_class=AccessibleSetPasswordForm,
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/completado/',
        PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
