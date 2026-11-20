from django.contrib.admin.sites import AdminSite
from django.test import TestCase, Client
from django.urls import reverse
from application.users.models import CustomUser, Productor, Profesional
from application.users.admin import ProfesionalAdmin
from application.tickets.models import TicketAsistencia
from application.community.models import PostComunidad
from domain.rules import (
    profesional_es_visible_para_productores,
    validar_matricula_ciapa,
    validar_region,
    validar_dni,
    validar_renspa,
    validar_telefono,
)
from application.use_cases import (
    BuscarProfesionalesUseCase,
    CrearTicketAsistenciaUseCase,
    CrearSolicitudAbiertaUseCase,
    ConvertirSolicitudAbiertaUseCase,
    CancelarTicketPendienteUseCase,
    TomarSolicitudAbiertaUseCase,
    FinalizarTrabajoTicketUseCase,
    ConfirmarRecepcionTicketUseCase,
    EnviarMensajeChatUseCase,
    ValidarProfesionalAdminUseCase,
)
from infrastructure.adapters.repositories import (
    DjangoProfesionalRepository,
    DjangoTicketRepository,
    DjangoChatRepository,
)


class AgroJujuyCleanArchitectureTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='AdminPassword123!',
            role='ADMIN'
        )

        self.prod_user = CustomUser.objects.create_user(
            username='prod_test',
            email='prod@test.com',
            password='ProdPassword123!',
            role='PRODUCER',
            first_name='Juan',
            last_name='Pérez'
        )
        self.productor = Productor.objects.create(
            usuario=self.prod_user,
            dni='35123456',
            renspa='09.001.0.12345/00',
            region='Quebrada',
            rubro_productivo='Cultivos Andinos',
            telefono='+54 388 4123456',
            direccion_finca='Finca Maimará'
        )

        self.prof_user1 = CustomUser.objects.create_user(
            username='ing_habilitado',
            email='ing1@test.com',
            password='IngPassword123!',
            role='PROFESSIONAL',
            first_name='Carlos',
            last_name='Gómez'
        )
        self.prof_habilitado = Profesional.objects.create(
            usuario=self.prof_user1,
            matricula_provincial='MP-1001/J',
            especialidad='Sanidad Vegetal y Plagas, Horticultura',
            zonas_cobertura='Quebrada, Puna',
            telefono='+54 388 4987654',
            estado_validacion='Habilitado'
        )

        self.prof_user2 = CustomUser.objects.create_user(
            username='ing_pendiente',
            email='ing2@test.com',
            password='IngPassword123!',
            role='PROFESSIONAL',
            first_name='Ana',
            last_name='Torres'
        )
        self.prof_pendiente = Profesional.objects.create(
            usuario=self.prof_user2,
            matricula_provincial='MP-1002/J',
            especialidad='Riego y Suelos',
            zonas_cobertura='Valles',
            telefono='+54 388 4554433',
            estado_validacion='Pendiente'
        )

        self.client = Client()

    def test_domain_rules_and_validators(self):
        self.assertTrue(profesional_es_visible_para_productores('Habilitado'))
        self.assertFalse(profesional_es_visible_para_productores('Pendiente'))
        self.assertFalse(profesional_es_visible_para_productores('Suspendido'))

        self.assertTrue(validar_matricula_ciapa('MP-1045/J'))
        self.assertFalse(validar_matricula_ciapa(''))
        self.assertTrue(validar_dni('35123456'))
        self.assertFalse(validar_dni('123'))
        self.assertTrue(validar_renspa('09.001.0.12345/00'))
        self.assertTrue(validar_telefono('+54 388 4123456'))
        self.assertFalse(validar_telefono('1234'))
        self.assertTrue(validar_region('Quebrada'))

    def test_admin_badge_estado_format_html_fix(self):
        site = AdminSite()
        model_admin = ProfesionalAdmin(Profesional, site)
        html_hab = model_admin.badge_estado(self.prof_habilitado)
        html_pend = model_admin.badge_estado(self.prof_pendiente)
        self.assertIn('#10B981', html_hab)
        self.assertIn('Habilitado', html_hab)
        self.assertIn('#C88A4B', html_pend)
        self.assertIn('Pendiente de Revisión', html_pend)

    def test_isolated_session_cookies_and_owasp_headers(self):
        self.client.login(username='prod_test', password='ProdPassword123!')
        res_web = self.client.get(reverse('buscador_profesionales'))
        self.assertEqual(res_web.status_code, 200)
        self.assertEqual(res_web['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(res_web['X-Frame-Options'], 'DENY')
        self.assertIn("default-src 'self'", res_web['Content-Security-Policy'])

    def test_public_pages_accessible_without_login(self):
        self.assertEqual(self.client.get(reverse('nosotros')).status_code, 200)
        self.assertEqual(self.client.get(reverse('buscador_profesionales')).status_code, 200)
        self.assertEqual(self.client.get(reverse('foro_comunidad')).status_code, 200)

    def test_buscador_does_not_load_all_by_default_and_paginates(self):
        """Verifica que el buscador no muestre toda la lista sin filtros y filtre al seleccionar región."""
        res_empty = self.client.get(reverse('buscador_profesionales'))
        self.assertEqual(len(res_empty.context['profesionales']), 0)
        self.assertFalse(res_empty.context['filtro_activo'])

        res_filtered = self.client.get(reverse('buscador_profesionales') + '?region=Quebrada')
        self.assertTrue(res_filtered.context['filtro_activo'])
        self.assertEqual(len(res_filtered.context['profesionales']), 1)

    def test_login_profesional_con_matricula_y_productor_tradicional(self):
        """
        Requerimiento 1:
        - Profesional inicia sesión ingresando su Número de Matrícula Provincial (MP-1001/J) y contraseña.
        - Productor y Admin mantienen login por usuario o correo electrónico.
        """
        res_prof = self.client.post(reverse('login'), {
            'username': 'MP-1001/J',
            'password': 'IngPassword123!',
        })
        self.assertEqual(res_prof.status_code, 302)
        self.assertEqual(res_prof.url, reverse('bandeja_profesional'))
        self.client.logout()

        res_prod = self.client.post(reverse('login'), {
            'username': 'prod_test',
            'password': 'ProdPassword123!',
        })
        self.assertEqual(res_prod.status_code, 302)
        self.assertEqual(res_prod.url, reverse('buscador_profesionales'))
        self.client.logout()

        res_prod_email = self.client.post(reverse('login'), {
            'username': 'prod@test.com',
            'password': 'ProdPassword123!',
        })
        self.assertEqual(res_prod_email.status_code, 302)

    def test_password_reset_flow_and_generic_anti_enumeration_message(self):
        """
        Iteración 3 - Requerimiento 2:
        - Flujo de recuperación de contraseña con mensaje genérico para evitar enumeración de cuentas.
        """
        res_get = self.client.get(reverse('password_reset'))
        self.assertEqual(res_get.status_code, 200)
        self.assertContains(res_get, 'autocomplete="email"')

        res_post = self.client.post(reverse('password_reset'), {'email': 'correo_inexistente@ejemplo.com'}, follow=True)
        self.assertEqual(res_post.status_code, 200)
        self.assertContains(res_post, 'Si el correo está registrado, recibirás instrucciones')

    def test_separacion_formulario_foro_y_mis_publicaciones(self):
        """
        Iteración 3 - Requerimiento 1:
        - Buscador del foro y filtro directo "Mis publicaciones".
        """
        PostComunidad.objects.create(
            autor=self.prod_user,
            titulo='Publicación del Productor Juan',
            contenido='Contenido de prueba de Juan.'
        )
        PostComunidad.objects.create(
            autor=self.prof_user1,
            titulo='Publicación del Ingeniero Carlos',
            contenido='Contenido técnico de Carlos.'
        )

        self.client.login(username='prod_test', password='ProdPassword123!')
        res_mis = self.client.get(reverse('foro_comunidad') + '?mis_publicaciones=1')
        self.assertEqual(res_mis.status_code, 200)
        self.assertContains(res_mis, 'Publicación del Productor Juan')
        self.assertNotContains(res_mis, 'Publicación del Ingeniero Carlos')

    def test_edicion_completa_perfil_profesional_exige_confirmar_matricula(self):
        """
        Iteración 3 - Requerimiento 4:
        - Permite al profesional editar nombre, apellido y correo SOLO si confirma su Número de Matrícula exacto.
        """
        self.client.login(username='MP-1001/J', password='IngPassword123!')

        # 1. Intentar cambiar nombre/correo SIN confirmar matrícula -> Debe fallar con error en confirmar_matricula
        res_sin_mat = self.client.post(reverse('perfil_profesional'), {
            'first_name': 'Carlos Alberto',
            'last_name': 'Gómez Quispe',
            'email': 'carlos.gomez.nuevo@ciapaj.org',
            'confirmar_matricula': '',
            'especialidades': ['Agroecología'],
            'zonas': ['Puna'],
            'telefono': '+54 388 5556677',
        })
        self.assertEqual(res_sin_mat.status_code, 200)
        self.assertContains(res_sin_mat, 'error_confirmar_matricula')
        self.prof_user1.refresh_from_db()
        self.assertEqual(self.prof_user1.first_name, 'Carlos')

        # 2. Cambiar nombre/correo CONFIRMANDO matrícula exacta -> Debe guardar con éxito
        res_con_mat = self.client.post(reverse('perfil_profesional'), {
            'first_name': 'Carlos Alberto',
            'last_name': 'Gómez Quispe',
            'email': 'carlos.gomez.nuevo@ciapaj.org',
            'confirmar_matricula': 'MP-1001/J',
            'especialidades': ['Agroecología', 'Cultivos Andinos'],
            'especialidad_propuesta': 'Sistemas Silvopastoriles',
            'zonas': ['Puna', 'Valles'],
            'telefono': '+54 388 5556677',
            'biografia': 'Especialista actualizado en agroecología andina.',
            'matricula_provincial': 'MP-HACK/J',
            'estado_validacion': 'Suspendido',
        })
        self.assertEqual(res_con_mat.status_code, 302)
        self.prof_user1.refresh_from_db()
        self.prof_habilitado.refresh_from_db()
        self.assertEqual(self.prof_user1.first_name, 'Carlos Alberto')
        self.assertEqual(self.prof_user1.last_name, 'Gómez Quispe')
        self.assertEqual(self.prof_user1.email, 'carlos.gomez.nuevo@ciapaj.org')
        self.assertEqual(self.prof_habilitado.especialidad, 'Agroecología, Cultivos Andinos')
        self.assertEqual(self.prof_habilitado.especialidad_propuesta, 'Sistemas Silvopastoriles')
        self.assertEqual(self.prof_habilitado.zonas_cobertura, 'Puna, Valles')
        self.assertEqual(self.prof_habilitado.matricula_provincial, 'MP-1001/J')

    def test_convertir_solicitud_dirigida_en_abierta_y_eliminar_pendiente(self):
        """
        Iteración 3 - Requerimiento 3:
        - Cuando una solicitud dirigida sigue pendiente, el productor puede convertirla en Abierta o eliminarla.
        """
        ticket = TicketAsistencia.objects.create(
            productor=self.productor,
            profesional=self.prof_habilitado,
            modalidad='DIRIGIDA',
            titulo='Plaga en cultivo de papa',
            descripcion='Sin respuesta del ingeniero asignado',
            estado='Pendiente'
        )

        self.client.login(username='prod_test', password='ProdPassword123!')

        # 1. Convertir en Solicitud Abierta
        res_conv = self.client.post(reverse('convertir_ticket_abierto', args=[ticket.id]))
        self.assertEqual(res_conv.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.modalidad, 'ABIERTA')
        self.assertIsNone(ticket.profesional)

        # 2. Eliminar / Cancelar solicitud pendiente
        res_del = self.client.post(reverse('eliminar_ticket_pendiente', args=[ticket.id]))
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(TicketAsistencia.objects.filter(id=ticket.id).exists())

    def test_chat_envio_ajax_y_ancla_scroll(self):
        """
        Iteración 3 - Requerimiento 4:
        - El envío de mensajes en el chat soporta Fetch/AJAX y redirección con ancla #ultimo-mensaje.
        """
        ticket = TicketAsistencia.objects.create(
            productor=self.productor,
            profesional=self.prof_habilitado,
            modalidad='DIRIGIDA',
            titulo='Consulta de riego',
            descripcion='Detalle',
            estado='Aceptado'
        )
        self.client.login(username='prod_test', password='ProdPassword123!')

        # Envío vía AJAX
        res_ajax = self.client.post(
            reverse('chat_ticket', args=[ticket.id]),
            {'contenido': 'Mensaje enviado sin perder scroll'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(res_ajax.status_code, 200)
        self.assertTrue(res_ajax.json()['exito'])
        self.assertEqual(res_ajax.json()['contenido'], 'Mensaje enviado sin perder scroll')

        # Envío tradicional (redirección con ancla #ultimo-mensaje)
        res_normal = self.client.post(
            reverse('chat_ticket', args=[ticket.id]),
            {'contenido': 'Segundo mensaje con ancla'}
        )
        self.assertEqual(res_normal.status_code, 302)
        self.assertTrue(res_normal.url.endswith('#ultimo-mensaje'))

    def test_panel_admin_web_alta_y_baja_profesionales(self):
        self.client.login(username='prod_test', password='ProdPassword123!')
        res_forbidden = self.client.get(reverse('panel_admin_profesionales'))
        self.assertEqual(res_forbidden.status_code, 403)
        self.client.logout()

        self.client.login(username='admin_test', password='AdminPassword123!')
        res_alta = self.client.post(
            reverse('cambiar_estado_profesional_admin', args=[self.prof_pendiente.id]),
            {'accion': 'alta'}
        )
        self.assertEqual(res_alta.status_code, 302)
        self.prof_pendiente.refresh_from_db()
        self.assertEqual(self.prof_pendiente.estado_validacion, 'Habilitado')

        res_baja = self.client.post(
            reverse('cambiar_estado_profesional_admin', args=[self.prof_habilitado.id]),
            {'accion': 'baja'}
        )
        self.assertEqual(res_baja.status_code, 302)
        self.prof_habilitado.refresh_from_db()
        self.assertEqual(self.prof_habilitado.estado_validacion, 'Suspendido')
        self.client.logout()

        self.client.login(username='MP-1001/J', password='IngPassword123!')
        res_bandeja = self.client.get(reverse('bandeja_profesional'))
        self.assertEqual(res_bandeja.status_code, 302)
        self.assertEqual(res_bandeja.url, reverse('espera_validacion'))

    def test_solicitud_abierta_locking_and_lifecycle_finalizacion_confirmacion(self):
        repo_ticket = DjangoTicketRepository()
        repo_prof = DjangoProfesionalRepository()

        uc_abierta = CrearSolicitudAbiertaUseCase(repo_ticket)
        res_crear = uc_abierta.ejecutar(
            productor_id=self.productor.id,
            titulo='Helada en cultivo de habas',
            descripcion='Necesito evaluación urgente tras helada en lote norte',
            especialidad_requerida='Cultivos Andinos'
        )
        self.assertTrue(res_crear.exito)
        ticket_id = res_crear.datos.id

        uc_tomar = TomarSolicitudAbiertaUseCase(repo_ticket, repo_prof)
        res_tomar1 = uc_tomar.ejecutar(ticket_id=ticket_id, profesional_id=self.prof_habilitado.id)
        self.assertTrue(res_tomar1.exito)

        otro_user = CustomUser.objects.create_user(username='ing_otro', password='IngPassword123!', role='PROFESSIONAL')
        otro_prof = Profesional.objects.create(
            usuario=otro_user,
            matricula_provincial='MP-1999/J',
            especialidad='Cultivos Andinos',
            zonas_cobertura='Quebrada',
            telefono='+54 388 4112233',
            estado_validacion='Habilitado'
        )
        res_tomar2 = uc_tomar.ejecutar(ticket_id=ticket_id, profesional_id=otro_prof.id)
        self.assertFalse(res_tomar2.exito)

        uc_finalizar = FinalizarTrabajoTicketUseCase(repo_ticket)
        res_fin = uc_finalizar.ejecutar(
            ticket_id=ticket_id,
            profesional_id=self.prof_habilitado.id,
            descripcion_finalizacion='Se aplicó bioestimulante foliar de aminoácidos y riego compensatorio.'
        )
        self.assertTrue(res_fin.exito)

        ticket_db = TicketAsistencia.objects.get(id=ticket_id)
        self.assertEqual(ticket_db.estado, 'Finalizado')
        self.assertIsNotNone(ticket_db.fecha_finalizacion)

        uc_confirmar = ConfirmarRecepcionTicketUseCase(repo_ticket)
        res_conf = uc_confirmar.ejecutar(ticket_id=ticket_id, productor_id=self.productor.id)
        self.assertTrue(res_conf.exito)
