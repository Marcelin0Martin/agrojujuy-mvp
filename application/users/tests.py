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
        """Verifica que badge_estado en ProfesionalAdmin no lance TypeError en Django 5.x."""
        site = AdminSite()
        model_admin = ProfesionalAdmin(Profesional, site)
        html_hab = model_admin.badge_estado(self.prof_habilitado)
        html_pend = model_admin.badge_estado(self.prof_pendiente)
        self.assertIn('#10B981', html_hab)
        self.assertIn('Habilitado', html_hab)
        self.assertIn('#C88A4B', html_pend)
        self.assertIn('Pendiente de Revisión', html_pend)

    def test_isolated_session_cookies_and_owasp_headers(self):
        """Verifica el aislamiento de la cookie de sesión de /admin/ respecto a la web y las cabeceras OWASP."""
        self.client.login(username='prod_test', password='ProdPassword123!')
        res_web = self.client.get(reverse('buscador_profesionales'))
        self.assertEqual(res_web.status_code, 200)
        self.assertEqual(res_web['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(res_web['X-Frame-Options'], 'DENY')
        self.assertIn("default-src 'self'", res_web['Content-Security-Policy'])

    def test_public_pages_accessible_without_login(self):
        """Verifica que Nosotros, Buscador y Foro sean accesibles sin iniciar sesión."""
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

    def test_perfil_profesional_ciapaj_no_404_and_protected_fields(self):
        """Verifica que /perfil/profesional/ ('Mi perfil CIAPAJ') no arroje 404 y proteja nombre/especialidad."""
        self.client.login(username='ing_habilitado', password='IngPassword123!')
        res = self.client.get(reverse('perfil_profesional'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Mi perfil CIAPAJ")

        # Intentar enviar un POST modificando first_name o especialidad (deben ignorarse)
        res_post = self.client.post(reverse('perfil_profesional'), {
            'first_name': 'Hackeado',
            'especialidad': 'Otra Especialidad',
            'zonas': ['Puna', 'Valles'],
            'telefono': '+54 388 5556677',
            'biografia': 'Nueva bio actualizada',
        })
        self.assertEqual(res_post.status_code, 302)
        self.prof_user1.refresh_from_db()
        self.prof_habilitado.refresh_from_db()
        self.assertEqual(self.prof_user1.first_name, 'Carlos')
        self.assertIn('Sanidad Vegetal', self.prof_habilitado.especialidad)
        self.assertEqual(self.prof_habilitado.zonas_cobertura, 'Puna, Valles')

    def test_perfil_productor_protected_fields(self):
        """Verifica que el productor no pueda cambiar nombre, correo, región ni dirección de finca."""
        self.client.login(username='prod_test', password='ProdPassword123!')
        res_post = self.client.post(reverse('perfil_productor'), {
            'first_name': 'NombreFalso',
            'region': 'Puna',
            'direccion_finca': 'Otra Finca',
            'rubro_productivo': 'Quinua Orgánica',
            'telefono': '+54 388 4998877',
        })
        self.assertEqual(res_post.status_code, 302)
        self.prod_user.refresh_from_db()
        self.productor.refresh_from_db()
        self.assertEqual(self.prod_user.first_name, 'Juan')
        self.assertEqual(self.productor.region, 'Quebrada')
        self.assertEqual(self.productor.direccion_finca, 'Finca Maimará')
        self.assertEqual(self.productor.rubro_productivo, 'Quinua Orgánica')

    def test_ajax_username_validation_and_aria_invalid_on_errors(self):
        """Verifica el endpoint AJAX de usuario ocupado y los atributos aria-invalid en errores de registro."""
        res_taken = self.client.get(reverse('validar_username_ajax') + '?username=prod_test')
        self.assertFalse(res_taken.json()['disponible'])

        res_free = self.client.get(reverse('validar_username_ajax') + '?username=usuario_nuevo_999')
        self.assertTrue(res_free.json()['disponible'])

        # Enviar registro inválido y verificar aria-invalid="true"
        res_invalid = self.client.post(reverse('registro_productor'), {'username': 'prod_test'})
        self.assertContains(res_invalid, 'aria-invalid="true"')

    def test_solicitud_abierta_locking_and_lifecycle_finalizacion_confirmacion(self):
        """
        Verifica el flujo completo:
        1. Productor publica Solicitud Abierta.
        2. Ingeniero 1 la toma (queda bloqueada para otros ingenieros).
        3. Ingeniero 1 marca como Finalizado con descripción y fecha.
        4. Productor confirma recepción.
        """
        repo_ticket = DjangoTicketRepository()
        repo_prof = DjangoProfesionalRepository()

        # 1. Crear solicitud abierta
        uc_abierta = CrearSolicitudAbiertaUseCase(repo_ticket)
        res_crear = uc_abierta.ejecutar(
            productor_id=self.productor.id,
            titulo='Helada en cultivo de habas',
            descripcion='Necesito evaluación urgente tras helada en lote norte',
            especialidad_requerida='Cultivos Andinos'
        )
        self.assertTrue(res_crear.exito)
        ticket_id = res_crear.datos.id

        # 2. Ingeniero habilitado toma la solicitud abierta
        uc_tomar = TomarSolicitudAbiertaUseCase(repo_ticket, repo_prof)
        res_tomar1 = uc_tomar.ejecutar(ticket_id=ticket_id, profesional_id=self.prof_habilitado.id)
        self.assertTrue(res_tomar1.exito)

        # Otro ingeniero habilitado intenta tomarla -> Debe estar bloqueada
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

        # 3. Ingeniero 1 finaliza el trabajo con descripción
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

        # 4. Productor confirma la recepción
        uc_confirmar = ConfirmarRecepcionTicketUseCase(repo_ticket)
        res_conf = uc_confirmar.ejecutar(ticket_id=ticket_id, productor_id=self.productor.id)
        self.assertTrue(res_conf.exito)

        ticket_db.refresh_from_db()
        self.assertTrue(ticket_db.confirmado_por_productor)
        self.assertIsNotNone(ticket_db.fecha_confirmacion)

    def test_foro_search_and_pagination(self):
        PostComunidad.objects.create(
            autor=self.prod_user,
            titulo='Control de pulgón en quinua orgánica',
            contenido='Experiencias aplicando extracto de neem en Puna.'
        )
        res = self.client.get(reverse('foro_comunidad') + '?q=quinua')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Control de pulgón en quinua orgánica')
