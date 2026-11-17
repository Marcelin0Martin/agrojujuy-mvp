# AgroJujuy — MVP (Iteración 2: Refactorización UI/UX, Accesibilidad WCAG 2.1 AA y Seguridad OWASP)

Proyecto desarrollado bajo **Clean Architecture / DDD** siguiendo el **Documento Maestro SDD (MANTRA)** y la guía transversal de **Accesibilidad (WCAG 2.1 Nivel AA) y Seguridad (OWASP Top 10:2025 / ASVS 5.0 Nivel 2)**.

---

## 0. Mapeo del Proyecto (Sección 0 — `SKILL.md`)

| Elemento | Definición en AgroJujuy MVP | Ubicación / Referencia |
|---|---|---|
| **Stack y framework** | Python 3.10+, Django 5.2, Plantillas SSR con HTML5 semántico, CSS moderno (sistema de diseño propio compatible con utilidades Tailwind), JS progresivo (Fetch/AJAX) | `manage.py`, `config/settings.py` |
| **Convenciones** | Clean Architecture / Hexagonal: `domain` (entidades, reglas, puertos), `application` (casos de uso y apps `users`, `tickets`, `community`), `infrastructure` (adaptadores ORM) | `domain/`, `application/`, `infrastructure/` |
| **Tokens de diseño** | Paleta oficial SDD (`#173F32`, `#10B981`, `#C88A4B`, `#6B7570`, `#F6F8F6`), sombras suaves, radios `rounded-xl`/`rounded-2xl`, tipografía `Inter` | `static/css/styles.css` |
| **Punto único de salida / persistencia** | Puertos en `domain/ports.py` implementados exclusivamente en `infrastructure/adapters/repositories.py` | `infrastructure/adapters/repositories.py` |
| **Utilidades transversales** | `IsolatedSessionMiddleware` (aislamiento de sesión `/admin/` vs web), `OWASPSecurityHeadersMiddleware` (CSP, HSTS/nosniff/Frame-Options), `AccessibleFormMixin` (`aria-invalid` y `aria-describedby`) | `config/middleware.py`, `application/users/forms.py` |
| **Comandos de verificación** | Chequeo de sistema Django y suite de pruebas unitarias/integración | `python manage.py check`, `python manage.py test application.users.tests` |
| **Infraestructura y cabeceras** | Cabeceras HTTP de seguridad inyectadas por middleware (`Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, `X-Frame-Options: DENY`) | `config/middleware.py` |
| **Navegadores y lectores soportados** | Chrome, Firefox, Edge, Safari; soporte de teclado completo, Skip Link (`#main-content`), regiones `aria-live="polite"` y `role="alert"` para NVDA / VoiceOver / TalkBack | `templates/base.html` |

---

## 🚀 Novedades de la Iteración 2

1. **Refactorización UI/UX ("Taste" — Emil Kowalski) y Accesibilidad WCAG 2.1 AA:**
   - Esquinas redondeadas (`rounded-xl`, `rounded-2xl`), sombras suaves multicapa (`shadow-sm`, `shadow-md`), espaciados amplios (`p-6`, `gap-4`/`gap-6`) y micro-interacciones que respetan `@media (prefers-reduced-motion: reduce)`.
   - Skip link accesible al recibir foco, indicador `:focus-visible` de alto contraste (`3px solid #C88A4B`), jerarquía semántica de encabezados y contraste mínimo ≥ 4.5:1.
   - Apartado público **"Nosotros"** (`/nosotros/`) y acceso libre de lectura para visitantes al **Buscador** y al **Foro Comunitario** sin requerir inicio de sesión.

2. **Corrección de Bugs Críticos:**
   - **Django Admin (`application/users/admin.py`):** Corregido `TypeError: args or kwargs must be provided` en `badge_estado` pasando `color` y `texto` como argumentos posicionales a `format_html`.
   - **Aislamiento de Sesiones (`config/middleware.py`):** Separada la cookie de sesión del panel `/admin/` (`agrojujuy_admin_sessionid`, path `/admin/`) respecto a la web principal (`agrojujuy_web_sessionid`, path `/`).
   - **Ruta `/perfil/profesional/` ("Mi perfil CIAPAJ") y Ruteo por Rol:** Eliminado el error 404 asegurando la resolución del perfil y corrigiendo el redireccionamiento del Profesional directamente a su **Bandeja de Trabajos**.
   - **Errores de Formulario Accesibles:** Implementado `AccessibleFormMixin` y plantillas con `aria-invalid="true"`, `aria-describedby` y mensajes `role="alert"` debajo de cada campo con error.

3. **Lógica de Negocio y Modelos:**
   - **Productor:** Añadidos campos `dni` y `renspa` con validadores nativos. Perfil protegido en edición (nombre, apellido, correo, DNI, RENSPA, región y dirección de finca bloqueados contra edición autónoma).
   - **Profesional:** Selección de múltiples especialidades agronómicas y campo para proponer una nueva especialidad en el registro. Perfil protegido en edición (nombre, apellido, correo, matrícula y especialidad bloqueados).
   - **Validaciones:** Endpoint AJAX en tiempo real (`/api/validar-username/`) para alertar si el nombre de usuario está ocupado y `RegexValidator` estricto para teléfonos.

4. **Navegación y Funcionalidad:**
   - **Buscador Inteligente:** Estado limpio inicial (no carga toda la lista sin filtros), aplicación automática de filtros al elegir región o especialidad, y paginación de 10 perfiles por página.
   - **Solicitudes Dirigidas y Abiertas:** Nueva modalidad **Abierta** (`/tickets/solicitar-abierta/`) que cualquier ingeniero habilitado puede tomar, bloqueándose atómicamente con `select_for_update()`.
   - **Bandeja del Profesional y Ciclo de Cierre:** Filtros por estado (`Pendiente`, `Aceptado`, `Finalizado`), ordenamiento con **Pendientes primero**, cierre técnico por el ingeniero con fecha y descripción (`FinalizarTicketView`), y confirmación de recepción por el productor (`ConfirmarRecepcionView`).
   - **Foro / Muro Comunitario:** Tarjetas con resumen breve desplegable bajo demanda, barra de búsqueda por palabras clave (`?q=`), carrusel accesible de destacados y paginación.
