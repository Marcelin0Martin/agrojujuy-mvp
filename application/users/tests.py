from django.test import TestCase, Client
from django.urls import reverse
from application.users.models import CustomUser, Productor, Profesional
from application.tickets.models import TicketAsistencia, MensajeTicket
from application.community.models import PostComunidad, RespuestaComunidad
from domain.rules import (
    profesional_es_visible_para_productores,
    validar_matricula_ciapa,
    validar_region,
)
from domain.entities import ProfesionalEntity
from domain.ports import RepositorioProfesional
from application.use_cases import (
    BuscarProfesionalesUseCase,
    CrearTicketAsistenciaUseCase,
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
        # Admin
        self.admin_user = CustomUser.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='AdminPassword123!',
            role='ADMIN'
        )

        # Productor
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
            region='Quebrada',
            rubro_productivo='Cultivos Andinos',
            telefono='3881234567'
        )

        # Profesional Habilitado
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
            especialidad='Sanidad Vegetal y Plagas',
            zonas_cobertura='Quebrada, Puna',
            telefono='3889876543',
            estado_validacion='Habilitado'
        )

        # Profesional Pendiente
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
            telefono='3885554433',
            estado_validacion='Pendiente'
        )

        self.client = Client()

    def test_domain_rules(self):
        self.assertTrue(profesional_es_visible_para_productores('Habilitado'))
        self.assertFalse(profesional_es_visible_para_productores('Pendiente'))
        self.assertFalse(profesional_es_visible_para_productores('Suspendido'))

        self.assertTrue(validar_matricula_ciapa('MP-1045/J'))
        self.assertTrue(validar_matricula_ciapa('1234'))
        self.assertFalse(validar_matricula_ciapa(''))
        self.assertFalse(validar_matricula_ciapa('invalid@#$%'))

        self.assertTrue(validar_region('Quebrada'))
        self.assertFalse(validar_region('Patagonia'))

    def test_buscador_profesionales_use_case_restriction(self):
        repo = DjangoProfesionalRepository()
        use_case = BuscarProfesionalesUseCase(repo)

        # Debe retornar solo el habilitado
        resultados = use_case.ejecutar()
        ids = [p.id for p in resultados]
        self.assertIn(self.prof_habilitado.id, ids)
        self.assertNotIn(self.prof_pendiente.id, ids)

        # Filtro por region Quebrada
        res_quebrada = use_case.ejecutar(region='Quebrada')
        self.assertEqual(len(res_quebrada), 1)
        self.assertEqual(res_quebrada[0].id, self.prof_habilitado.id)

        # Filtro por region Valles (el profesional de valles está pendiente, por lo que debe devolver 0)
        res_valles = use_case.ejecutar(region='Valles')
        self.assertEqual(len(res_valles), 0)

    def test_solicitar_ticket_use_case(self):
        repo_ticket = DjangoTicketRepository()
        repo_prof = DjangoProfesionalRepository()
        use_case = CrearTicketAsistenciaUseCase(repo_ticket, repo_prof)

        # Intento de ticket a profesional pendiente -> Debe fallar
        res_fallo = use_case.ejecutar(
            productor_id=self.productor.id,
            profesional_id=self.prof_pendiente.id,
            titulo='Consulta Suelos',
            descripcion='Detalle del problema'
        )
        self.assertFalse(res_fallo.exito)

        # Intento de ticket a profesional habilitado -> Debe tener éxito
        res_exito = use_case.ejecutar(
            productor_id=self.productor.id,
            profesional_id=self.prof_habilitado.id,
            titulo='Plaga en maíz',
            descripcion='Tengo oruga cogollera en lote 2'
        )
        self.assertTrue(res_exito.exito)
        self.assertIsNotNone(res_exito.datos.id)

    def test_chat_ticket_access_and_messaging(self):
        ticket = TicketAsistencia.objects.create(
            productor=self.productor,
            profesional=self.prof_habilitado,
            titulo='Consulta Directa',
            descripcion='Detalle',
            estado='Pendiente'
        )

        repo_chat = DjangoChatRepository()
        repo_ticket = DjangoTicketRepository()
        use_case = EnviarMensajeChatUseCase(repo_chat, repo_ticket)

        # Mensaje enviado por el productor
        res_msg = use_case.ejecutar(
            ticket_id=ticket.id,
            emisor_id=self.prod_user.id,
            contenido='Buenas tardes Ing., ¿pudo revisar el caso?',
            emisor_usuario_id=self.prod_user.id,
            prod_uid=self.prod_user.id,
            prof_uid=self.prof_user1.id
        )
        self.assertTrue(res_msg.exito)

        # Mensaje enviado por un tercero no autorizado -> Debe fallar
        tercero = CustomUser.objects.create_user(username='hacker', password='Password123!')
        res_invalido = use_case.ejecutar(
            ticket_id=ticket.id,
            emisor_id=tercero.id,
            contenido='Intrusión no autorizada',
            emisor_usuario_id=tercero.id,
            prod_uid=self.prod_user.id,
            prof_uid=self.prof_user1.id
        )
        self.assertFalse(res_invalido.exito)

    def test_pantalla_espera_profesional_pendiente(self):
        self.client.login(username='ing_pendiente', password='IngPassword123!')
        response = self.client.get(reverse('inicio'), follow=True)
        self.assertContains(response, "Perfil en revisión. El tiempo de validación institucional es de 24 a 48 horas")

    def test_admin_habilitar_profesional_use_case(self):
        repo_prof = DjangoProfesionalRepository()
        use_case_admin = ValidarProfesionalAdminUseCase(repo_prof)
        res = use_case_admin.habilitar(self.prof_pendiente.id)
        self.assertTrue(res.exito)

        self.prof_pendiente.refresh_from_db()
        self.assertEqual(self.prof_pendiente.estado_validacion, 'Habilitado')

        # Ahora debe ser visible en el buscador
        use_case_buscar = BuscarProfesionalesUseCase(repo_prof)
        res_valles = use_case_buscar.ejecutar(region='Valles')
        self.assertEqual(len(res_valles), 1)
