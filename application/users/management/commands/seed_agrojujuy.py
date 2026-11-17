import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from application.users.models import CustomUser, Productor, Profesional, ConfiguracionSeguridad
from application.tickets.models import TicketAsistencia, MensajeTicket
from application.community.models import PostComunidad, RespuestaComunidad
from domain.rules import REGIONES_VALIDAS, ESPECIALIDADES_VALIDAS


RUBROS_JUJUY = [
    'Papa Andina y Tubérculos',
    'Quinua y Maíces Nativos',
    'Hortalizas de Hoja y Tomate',
    'Tabaco Virginia',
    'Caña de Azúcar',
    'Cítricos y Frutas Tropicales',
    'Ganadería Bovina y Camélidos (Llamas)',
    'Legumbres y Porotos',
    'Floricultura',
    'Vid y Vinos de Altura',
]

TITULOS_TICKETS = [
    'Control de oruga cogollera en maíz',
    'Problemas de salinidad en suelo de riego',
    'Pudrición de raíz en plantines de pimiento',
    'Amarillamiento foliar y deficiencia de hierro',
    'Aparición de mosca blanca en tomate bajo cubierta',
    'Calibración de equipo de riego por goteo',
    'Plan nutricional para forraje de camélidos',
    'Enfermedad fúngica poscosecha en cítricos',
    'Tratamiento de pulgones en tabaco',
    'Manejo biológico de plagas en quinoa',
]

TITULOS_FORO = [
    '¿Qué variedades de papa resisten mejor las heladas en Quebrada?',
    'Experiencias con biofertilizantes caseros en Valles',
    'Consulta sobre costo y calidad de semillas certificadas en Jujuy',
    'Cosecha de agua de lluvia en la Puna: reservorios impermeabilizados',
    'Alerta temprana de mildiu tras lluvias recientes en Yungas',
    'Precios de referencia y canales de comercialización directa',
    'Control de caracoles y babosas en huertas familiares',
    'Rotación de cultivos con leguminosas para fijar nitrógeno',
    'Buenas prácticas agrícolas (BPA) exigidas para exportación',
    'Técnicas de poda en cítricos para maximizar rendimiento',
]


class Command(BaseCommand):
    help = "Genera la base de datos inicial de AgroJujuy según las especificaciones del Documento Maestro SDD"

    def handle(self, *args, **options):
        fake = Faker('es_ES')
        self.stdout.write(self.style.NOTICE("=== Iniciando Seeding de AgroJujuy ==="))

        # 1. Crear Superusuario / Admin
        admin_user, created = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@agrojujuy.gob.ar',
                'first_name': 'Administrador',
                'last_name': 'Institucional CIAPAJ',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('Admin1234!')
            admin_user.save()
            ConfiguracionSeguridad.objects.get_or_create(usuario=admin_user)
            self.stdout.write(self.style.SUCCESS("✔ Usuario Admin creado: 'admin' / 'Admin1234!'"))
        else:
            self.stdout.write("ℹ Usuario Admin ya existía.")

        # 2. Generar 100 Productores asignados aleatoriamente a las 4 regiones
        self.stdout.write("Generando 100 productores agrícolas con DNI y RENSPA...")
        productores_creados = []
        for i in range(1, 101):
            username = f"productor_{i:03d}"
            email = f"productor{i}@agrojujuy.test"
            first_name = fake.first_name()
            last_name = fake.last_name()
            user, u_created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'PRODUCER',
                }
            )
            if u_created:
                user.set_password('Productor1234!')
                user.save()
                ConfiguracionSeguridad.objects.get_or_create(usuario=user)

            region = random.choice(REGIONES_VALIDAS)
            rubro = random.choice(RUBROS_JUJUY)
            dni = str(25000000 + i * 137)
            renspa = f"09.{random.randint(1, 15):03d}.0.{10000 + i:05d}/00"
            prod, _ = Productor.objects.update_or_create(
                usuario=user,
                defaults={
                    'dni': dni,
                    'renspa': renspa,
                    'region': region,
                    'rubro_productivo': rubro,
                    'telefono': f"+54 388 {random.randint(4000000, 6999999)}",
                    'direccion_finca': f"Finca {fake.street_name()} s/n, {region}, Jujuy",
                }
            )
            productores_creados.append(prod)

        self.stdout.write(self.style.SUCCESS(f"✔ 100 Productores listos (distribuidos en {', '.join(REGIONES_VALIDAS)})."))

        # 3. Generar 100 Profesionales (80% Habilitados, 20% Pendientes)
        self.stdout.write("Generando 100 profesionales agrarios (80 Habilitados, 20 Pendientes)...")
        profesionales_creados = []
        profesionales_habilitados = []

        for i in range(1, 101):
            username = f"profesional_{i:03d}"
            email = f"ingeniero{i}@ciapaj-jujuy.test"
            first_name = fake.first_name()
            last_name = fake.last_name()
            user, u_created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'PROFESSIONAL',
                }
            )
            if u_created:
                user.set_password('Profesional1234!')
                user.save()
                ConfiguracionSeguridad.objects.get_or_create(usuario=user)

            matricula = f"MP-{1000 + i}/J"
            # Selección de 1 o 2 especialidades
            esps = random.sample(ESPECIALIDADES_VALIDAS, random.randint(1, 2))
            especialidad_str = ", ".join(esps)
            estado = "Habilitado" if i <= 80 else "Pendiente"

            num_zonas = random.randint(1, 3)
            zonas = ", ".join(random.sample(REGIONES_VALIDAS, num_zonas))

            prof, _ = Profesional.objects.update_or_create(
                usuario=user,
                defaults={
                    'matricula_provincial': matricula,
                    'especialidad': especialidad_str,
                    'zonas_cobertura': zonas,
                    'telefono': f"+54 388 {random.randint(4000000, 6999999)}",
                    'biografia': f"Ingeniero Agrónomo egresado de la FCA-UNJu con experiencia en {especialidad_str.lower()} en regiones {zonas}.",
                    'estado_validacion': estado,
                    'fecha_validacion': timezone.now() if estado == 'Habilitado' else None,
                }
            )
            profesionales_creados.append(prof)
            if estado == 'Habilitado':
                profesionales_habilitados.append(prof)

        self.stdout.write(self.style.SUCCESS("✔ 100 Profesionales listos (80 Habilitados, 20 Pendientes CIAPAJ)."))

        # 4. Generar 5 Usuarios No Registrados / Inactivos
        self.stdout.write("Generando 5 usuarios no registrados / inactivos...")
        for i in range(1, 6):
            username = f"inactivo_{i:02d}"
            email = f"inactivo{i}@test.com"
            user, u_created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'role': 'PRODUCER',
                    'is_active': False,
                }
            )
            if u_created:
                user.set_password('Inactivo1234!')
                user.save()
                ConfiguracionSeguridad.objects.get_or_create(usuario=user)
        self.stdout.write(self.style.SUCCESS("✔ 5 Usuarios inactivos/no registrados listos."))

        # 5. Generar 40 Posts en el foro de comunidad con respuestas anidadas
        self.stdout.write("Generando 40 publicaciones y respuestas en el foro comunitario...")
        todos_los_usuarios = list(CustomUser.objects.filter(is_active=True).exclude(username='admin'))
        for i in range(1, 41):
            autor = random.choice(todos_los_usuarios)
            titulo = random.choice(TITULOS_FORO) + f" (Caso #{i})"
            contenido = fake.paragraph(nb_sentences=4)
            post, p_created = PostComunidad.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'autor': autor,
                    'contenido': contenido,
                    'fecha_creacion': timezone.now() - timedelta(days=random.randint(1, 30)),
                }
            )
            if p_created:
                num_resp = random.randint(1, 3)
                for _ in range(num_resp):
                    resp_autor = random.choice(todos_los_usuarios)
                    RespuestaComunidad.objects.create(
                        post=post,
                        autor=resp_autor,
                        contenido=fake.sentence(nb_words=14),
                        fecha_creacion=post.fecha_creacion + timedelta(hours=random.randint(1, 48))
                    )
        self.stdout.write(self.style.SUCCESS("✔ 40 Posts en foro comunitario con respuestas anidadas creados."))

        # 6. Generar 50 Tickets de asistencia técnica (Dirigidos y Abiertos)
        self.stdout.write("Generando 50 tickets de asistencia con chats cruzados 1 a 1...")
        for i in range(1, 51):
            productor = random.choice(productores_creados)
            es_abierta = (i > 42)  # 8 solicitudes abiertas disponibles
            profesional = None if es_abierta else random.choice(profesionales_habilitados)
            modalidad = 'ABIERTA' if es_abierta else 'DIRIGIDA'
            titulo = random.choice(TITULOS_TICKETS) + f" - Finca #{random.randint(10, 99)}"
            estado = "Pendiente" if es_abierta else random.choice(["Pendiente", "Aceptado", "Finalizado"])

            ticket, t_created = TicketAsistencia.objects.get_or_create(
                productor=productor,
                titulo=titulo,
                defaults={
                    'profesional': profesional,
                    'modalidad': modalidad,
                    'especialidad_requerida': random.choice(ESPECIALIDADES_VALIDAS),
                    'descripcion': f"Consulta técnica solicitada por el productor sobre {titulo}. " + fake.text(max_nb_chars=180),
                    'estado': estado,
                    'descripcion_finalizacion': "Se realizó inspección en lote y ajuste de dosis fitosanitaria." if estado == 'Finalizado' else "",
                    'fecha_finalizacion': timezone.now() if estado == 'Finalizado' else None,
                    'fecha_creacion': timezone.now() - timedelta(days=random.randint(1, 20)),
                }
            )

            if t_created and profesional:
                MensajeTicket.objects.create(
                    ticket=ticket,
                    emisor=productor.usuario,
                    contenido=f"Hola Ing. {profesional.usuario.last_name}, solicito su orientación técnica: {ticket.descripcion}",
                    fecha_envio=ticket.fecha_creacion
                )
                if estado in ['Aceptado', 'Finalizado']:
                    MensajeTicket.objects.create(
                        ticket=ticket,
                        emisor=profesional.usuario,
                        contenido=f"Hola {productor.usuario.first_name}. Con gusto evalúo tu caso. Te recomiendo enviar fotos claras y suspender aplicaciones químicas hasta tener el diagnóstico.",
                        fecha_envio=ticket.fecha_creacion + timedelta(hours=random.randint(2, 24))
                    )

        self.stdout.write(self.style.SUCCESS("✔ 50 Tickets de asistencia técnica cruzados y mensajes de chat creados."))
        self.stdout.write(self.style.SUCCESS("=== Seeding Completado Exitosamente ==="))
