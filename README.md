# AgroJujuy - MVP (Sistema de Información Agrícola y Asistencia Técnica Provincial)

Proyecto desarrollado bajo **Clean Architecture / DDD** emulando la arquitectura de seguridad, roles, puertos, adaptadores y panel administrativo del repositorio de referencia institucional, con estricto apego al **Documento Maestro SDD (MANTRA)**.

---

## 🏛️ Estructura Arquitectónica (Clean Architecture / Hexagonal)

```text
Sistemas de informacion_MVP/
├── manage.py
├── config/                                # Configuración y entrada WSGI
│   ├── settings.py                        # Django 5.x, SQLite/PostgreSQL, Auth CustomUser, Validadores
│   ├── urls.py                            # Enrutamiento general y personalización Admin CIAPA
│   ├── wsgi.py
│   └── context_processors.py              # Contexto global para Header y Auditoría de Roles
├── domain/                                # Capa de Dominio puro (independiente de Django)
│   ├── entities.py                        # Entidades del negocio (Usuario, Productor, Profesional, Ticket, Chat, Post)
│   ├── rules.py                           # Reglas de negocio (visibilidad CIAPA, validación matrículas, regiones)
│   └── ports.py                           # Puertos / interfaces abstractas de repositorios
├── application/                           # Capa de Casos de Uso y Aplicaciones Django
│   ├── use_cases.py                       # Casos de uso (Búsqueda, Tickets, Chat 1 a 1, Muro, Aprobación CIAPA)
│   ├── users/                             # App de Usuarios, Productores y Profesionales CIAPA
│   │   ├── models.py                      # CustomUser (AbstractUser), Productor, Profesional, ConfigSeguridad
│   │   ├── forms.py                       # Formularios con validación de matrícula y seguridad
│   │   ├── views.py                       # Buscador inteligente, Vitrina digital, Onboarding, Auditoría
│   │   ├── admin.py                       # Panel institucional CIAPA con acciones masivas y badges
│   │   ├── signals.py                     # Inicialización de configuración de seguridad
│   │   ├── tests.py                       # Pruebas automatizadas de Clean Architecture
│   │   └── management/commands/
│   │       └── seed_agrojujuy.py          # Script automatizado de seeding volumétrico (Faker)
│   ├── tickets/                           # App de Asistencia Técnica y Chat Directo
│   │   ├── models.py                      # TicketAsistencia y MensajeTicket
│   │   ├── forms.py
│   │   ├── views.py                       # Bandejas acotadas (5 últimas) y canal 1 a 1
│   │   └── admin.py
│   └── community/                         # App de Foro Comunitario / Muro de Intercambio
│       ├── models.py                      # PostComunidad y RespuestaComunidad
│       ├── forms.py
│       ├── views.py                       # Muro público con respuestas anidadas y mockups publicitarios
│       └── admin.py
├── infrastructure/                        # Adaptadores de Infraestructura
│   └── adapters/
│       └── repositories.py                # Implementación Django ORM de los Puertos de Dominio
├── templates/                             # Plantillas HTML Mobile-First WCAG 2.1 AA
│   ├── base.html                          # Header global con selector de roles para auditoría
│   ├── users/                             # Login, registros, espera de validación, buscador, vitrina, perfiles
│   ├── tickets/                           # Bandejas de 5 solicitudes y chat directo
│   └── community/                         # Muro del foro agrario
└── static/
    └── css/
        └── styles.css                     # Estilos Inter, WCAG, alto contraste, paleta institucional
```

---

## 🎨 Paleta de Colores y Accesibilidad WCAG (Mobile-First)

- **Primary:** `#173F32` (Verde institucional profundo, texto sobre fondo claro, botones principales)
- **Secondary:** `#10B981` (Verde esmeralda para estados y botones; *prohibido para texto sobre fondo blanco según SDD*)
- **Tertiary:** `#C88A4B` (Ocre tierra andina para advertencias y llamadas secundarias)
- **Neutral:** `#6B7570` / `#2A332F` (Textos y bordes de alto contraste)
- **Background:** `#F6F8F6` (Fondo exterior optimizado para legibilidad bajo luz solar)
- **Tipografía:** `Inter` (sans-serif legible en pantallas móviles)

---

## ⚙️ Características Implementadas según SDD

1. **Header Global con Selector de Auditoría Temporal:**
   - Permite al Administrador alternar dinámicamente entre vista de **Productor**, **Profesional** y **Admin** para auditoría y prueba de bugs visuales sin alterar la base de datos.
2. **Seguridad y Django Auth:**
   - Sobrescritura de `AbstractUser` con campo `role` (`PRODUCER`, `PROFESSIONAL`, `ADMIN`).
   - Validadores estándar de contraseñas (mínimo 8 caracteres, alfanumérico).
   - Detección de fuerza bruta con bloqueo por 15 minutos tras 3 intentos erróneos.
3. **Gestión del Productor:**
   - **Buscador Inteligente:** Cuadrícula con filtros por Zona Geográfica (*Puna, Valles, Yungas, Quebrada*) y Especialidad agronómica.
   - **Bandeja de Solicitudes:** Historial acotado a las últimas 5 solicitudes enviadas.
   - **Chat Directo 1 a 1:** Hilo de comunicación técnica privado ligado a cada ticket.
   - **Autogestión de Perfil:** Edición de región y rubro productivo.
4. **Gestión del Profesional Agrario:**
   - **Onboarding con Matrícula Obligatoria:** Validación estricta de matrícula CIAPA.
   - **Pantalla de Espera (Bloqueo):** Redirección forzosa al registrarse con el mensaje: *"Perfil en revisión. El tiempo de validación institucional es de 24 a 48 horas"*.
   - **Vitrina Digital:** Perfil público accesible únicamente si el profesional está en estado **Habilitado**.
   - **Bandeja de Trabajos:** Historial acotado a las últimas 5 solicitudes recibidas.
   - **Autogestión de Perfil:** Actualización de especialidades, zonas de cobertura y contacto.
5. **Comunidad y Publicidad:**
   - **Muro Público:** Publicación de problemas e ideas con respuestas anidadas.
   - **Banners Estáticos (Mockup):** Espacios reservados de publicidad de agroinsumos en Buscador y Foro.
6. **Panel Institucional (Django Admin):**
   - Personalizado para CIAPA con badges de estado.
   - Acciones masivas de **Habilitar** y **Rechazar/Suspender**.
   - **Regla de restricción activa:** Los profesionales pendientes o suspendidos desaparecen automáticamente del buscador de productores.

---

## 🚀 Comandos Rápidos de Ejecución

### 1. Migraciones de Base de Datos
```bash
python manage.py migrate
```

### 2. Seeding Automatizado de Base de Datos
```bash
python manage.py seed_agrojujuy
```
Genera:
- Superusuario administrador: `admin` / `Admin1234!`
- **100 Productores** distribuidos en las 4 regiones.
- **100 Profesionales** (80% forzados a `Habilitado`, 20% en estado `Pendiente`).
- **5 Usuarios Inactivos / No Registrados**.
- **40 Publicaciones** en el foro comunitario con respuestas anidadas.
- **50 Tickets** de asistencia técnica con mensajes cruzados en chat 1 a 1.

### 3. Ejecutar Pruebas Automatizadas
```bash
python manage.py test application.users.tests
```

### 4. Iniciar el Servidor de Desarrollo
```bash
python manage.py runserver
```
Acceso a la plataforma: `http://127.0.0.1:8000/`  
Acceso al panel administrativo: `http://127.0.0.1:8000/admin/`
