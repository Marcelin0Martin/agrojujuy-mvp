# Documentación UML — MVP AgroJujuy (Clean Architecture)

Documentación técnica generada a partir del código actual de las capas de **Dominio** (`domain/entities.py`, `domain/ports.py`, `domain/rules.py`), **Aplicación** (`application/use_cases.py`) e **Infraestructura** (`infrastructure/adapters/repositories.py`).

---

## 1. Diagrama de Casos de Uso

Representa las interacciones de los actores (**Productor**, **Profesional Agrario**, **Administrador CIAPAJ** y **Visitante Público**) con los módulos del sistema.

```mermaid
flowchart LR
    %% Actores
    Visitante(["👤 Visitante Público"])
    Productor(["🚜 Productor Agrícola"])
    Profesional(["🎓 Profesional Agrario"])
    Admin(["⚙️ Administrador CIAPAJ"])

    subgraph Sistema_AgroJujuy["Sistema AgroJujuy MVP"]
        direction TB

        subgraph Mod_Publico_Auth["Módulo de Registro, Seguridad y Acceso Público"]
            UC_Nosotros["Consultar Sección Nosotros"]
            UC_RegProd["Registrarse con Validación DNI y RENSPA"]
            UC_RegProf["Registrarse con Matrícula CIAPAJ y Múltiples Especialidades"]
            UC_AjaxUser["Validar Disponibilidad de Usuario en Tiempo Real (AJAX)"]
            UC_Espera["Visualizar Pantalla de Espera (24 a 48 hs)"]
            UC_PerfilProd["Editar Datos Operativos de Finca (Perfil Protegido)"]
            UC_PerfilProf["Editar Zonas y Contacto en Mi perfil CIAPAJ (Perfil Protegido)"]
        end

        subgraph Mod_Buscador["Módulo Buscador Inteligente y Vitrina"]
            UC_Buscar["Filtrar Profesionales Automáticamente por Región y Especialidad"]
            UC_PaginarProf["Navegar Perfiles Habilitados Paginados"]
            UC_Vitrina["Consultar Vitrina Digital Pública del Profesional"]
        end

        subgraph Mod_Tickets["Módulo de Solicitudes de Asistencia y Chat 1 a 1"]
            UC_SolDirigida["Enviar Solicitud Dirigida a Ingeniero Específico"]
            UC_SolAbierta["Publicar Solicitud Abierta a la Red CIAPAJ"]
            UC_TomarAbierta["Aceptar Solicitud y Bloquear Caso (select_for_update)"]
            UC_BandejaProf["Filtrar Bandeja de Trabajos (Pendientes Primero)"]
            UC_Chat["Dialogar en Canal Directo Privado (1 a 1)"]
            UC_Finalizar["Marcar Trabajo como Finalizado con Informe y Fecha"]
            UC_Confirmar["Confirmar Recepción Conforme del Trabajo"]
        end

        subgraph Mod_Comunidad["Módulo Foro / Muro Comunitario"]
            UC_VerForo["Explorar Resúmenes, Carrusel y Buscar por Palabras Clave"]
            UC_CrearPost["Publicar Problema, Idea o Consulta en el Muro"]
            UC_ResponderPost["Agregar Respuesta Técnica Anidada"]
        end

        subgraph Mod_Admin["Módulo de Administración Institucional (Django Admin)"]
            UC_AuditarMat["Cruzar y Validar Matrículas Provinciales CIAPAJ"]
            UC_Habilitar["Habilitar o Suspender Profesionales"]
            UC_SimularRol["Cambiar Rol Temporal en Header Global (Auditoría Visual)"]
        end
    end

    %% Relaciones Visitante
    Visitante --> UC_Nosotros
    Visitante --> UC_RegProd
    Visitante --> UC_RegProf
    Visitante --> UC_Buscar
    Visitante --> UC_Vitrina
    Visitante --> UC_VerForo

    %% Inclusión de validación AJAX en registros
    UC_RegProd -.->|"include"| UC_AjaxUser
    UC_RegProf -.->|"include"| UC_AjaxUser
    UC_RegProf -.->|"redirige si Pendiente"| UC_Espera

    %% Relaciones Productor
    Productor --> UC_Buscar
    Productor --> UC_PaginarProf
    Productor --> UC_Vitrina
    Productor --> UC_SolDirigida
    Productor --> UC_SolAbierta
    Productor --> UC_Chat
    Productor --> UC_Confirmar
    Productor --> UC_PerfilProd
    Productor --> UC_VerForo
    Productor --> UC_CrearPost
    Productor --> UC_ResponderPost

    %% Relaciones Profesional
    Profesional --> UC_BandejaProf
    Profesional --> UC_TomarAbierta
    Profesional --> UC_Chat
    Profesional --> UC_Finalizar
    Profesional --> UC_PerfilProf
    Profesional --> UC_VerForo
    Profesional --> UC_CrearPost
    Profesional --> UC_ResponderPost

    %% Relaciones Administrador
    Admin --> UC_AuditarMat
    Admin --> UC_Habilitar
    Admin --> UC_SimularRol
```

---

## 2. Diagrama de Clases (Capa de Dominio)

Enfocado estrictamente en las entidades de negocio definidas en `domain/entities.py` y las reglas/puertos de `domain/rules.py` y `domain/ports.py`.

```mermaid
classDiagram
    direction TB

    class UsuarioEntity {
        +int id
        +str username
        +str email
        +str first_name
        +str last_name
        +str role
        +bool is_active
    }

    class ProductorEntity {
        +int id
        +int usuario_id
        +str region
        +str rubro_productivo
        +str dni
        +str renspa
        +str telefono
        +str direccion_finca
    }

    class ProfesionalEntity {
        +int id
        +int usuario_id
        +str matricula_provincial
        +str especialidad
        +List~str~ zonas_cobertura
        +List~str~ especialidades_lista
        +str especialidad_propuesta
        +str nombre_completo
        +str telefono
        +str biografia
        +str estado_validacion
        +datetime fecha_solicitud
    }

    class TicketEntity {
        +int id
        +int productor_id
        +Optional~int~ profesional_id
        +str titulo
        +str descripcion
        +str modalidad
        +str especialidad_requerida
        +str estado
        +datetime fecha_creacion
        +str descripcion_finalizacion
        +Optional~datetime~ fecha_finalizacion
        +bool confirmado_por_productor
        +Optional~datetime~ fecha_confirmacion
    }

    class MensajeChatEntity {
        +int id
        +int ticket_id
        +int emisor_id
        +str contenido
        +datetime fecha_envio
    }

    class PostComunidadEntity {
        +int id
        +int autor_id
        +str titulo
        +str contenido
        +datetime fecha_creacion
        +int respuestas_count
    }

    class RespuestaComunidadEntity {
        +int id
        +int post_id
        +int autor_id
        +str contenido
        +datetime fecha_creacion
    }

    %% Relaciones de Dominio
    UsuarioEntity "1" -- "0..1" ProductorEntity : "posee perfil productor"
    UsuarioEntity "1" -- "0..1" ProfesionalEntity : "posee perfil profesional"
    ProductorEntity "1" --> "0..*" TicketEntity : "crea solicitud (DIRIGIDA / ABIERTA)"
    ProfesionalEntity "0..1" --> "0..*" TicketEntity : "atiende y finaliza"
    TicketEntity "1" *-- "0..*" MensajeChatEntity : "contiene hilo 1 a 1"
    UsuarioEntity "1" --> "0..*" MensajeChatEntity : "emite mensaje"
    UsuarioEntity "1" --> "0..*" PostComunidadEntity : "publica en muro"
    PostComunidadEntity "1" *-- "0..*" RespuestaComunidadEntity : "anida respuestas"
    UsuarioEntity "1" --> "0..*" RespuestaComunidadEntity : "responde"
```

---

## 3. Diagrama de Secuencia (Ciclo de Solicitud Abierta hasta Cierre y Confirmación)

Detalla el flujo completo a través de las capas de la arquitectura hexagonal desde que el **Productor** publica una **Solicitud Abierta** hasta que un **Profesional** habilitado la acepta/bloquea, la marca como **Finalizada** y el **Productor** confirma su recepción.

```mermaid
sequenceDiagram
    autonumber
    actor Prod as Productor Agrícola
    actor Prof as Profesional Agrario (CIAPAJ)
    participant View as Vistas Django (application/tickets/views.py)
    participant UC as Casos de Uso (application/use_cases.py)
    participant Rules as Reglas de Dominio (domain/rules.py)
    participant Repo as DjangoTicketRepository (infrastructure/adapters)
    participant DB as Base de Datos (TicketAsistencia)

    %% Fase 1: Publicación de Solicitud Abierta
    rect rgb(232, 240, 236)
        Note over Prod,DB: 1. Publicación de Solicitud Abierta
        Prod->>View: POST /tickets/solicitar-abierta/ (título, descripción, especialidad)
        View->>UC: CrearSolicitudAbiertaUseCase.ejecutar(productor_id, titulo, descripcion, esp)
        UC->>Repo: crear(TicketEntity[modalidad="ABIERTA", profesional_id=None, estado="Pendiente"])
        Repo->>DB: INSERT TicketAsistencia (profesional=NULL, modalidad='ABIERTA', estado='Pendiente')
        DB-->>Repo: Ticket creado (id)
        Repo-->>UC: TicketEntity
        UC-->>View: ResultadoOperacion(exito=True)
        View-->>Prod: Redirige a Bandeja de Solicitudes con alerta de éxito
    end

    %% Fase 2: Visualización y Aceptación con Bloqueo Atómico
    rect rgb(254, 243, 199)
        Note over Prof,DB: 2. Aceptación y Bloqueo Atómico por Profesional Habilitado
        Prof->>View: GET /tickets/profesional/trabajos/?estado=Pendiente
        View->>DB: SELECT tickets (Pendientes primero, incluye ABIERTA sin asignar)
        DB-->>View: Lista de solicitudes disponibles
        View-->>Prof: Renderiza Bandeja de Trabajos

        Prof->>View: POST /tickets/aceptar/{ticket_id}/
        View->>UC: TomarSolicitudAbiertaUseCase.ejecutar(ticket_id, profesional_id)
        UC->>Rules: profesional_es_visible_para_productores(estado_validacion)
        Rules-->>UC: True (Estado == "Habilitado")
        UC->>Repo: tomar_solicitud_abierta(ticket_id, profesional_id)
        Repo->>DB: BEGIN ATOMIC + SELECT ... FOR UPDATE (ticket_id)
        alt Solicitud aún libre (estado == 'Pendiente' y profesional IS NULL)
            Repo->>DB: UPDATE profesional_id = prof.id, estado = 'Aceptado'
            DB-->>Repo: Commit exitoso
            Repo-->>UC: True (Caso asignado y bloqueado para otros ingenieros)
            UC-->>View: ResultadoOperacion(exito=True)
            View-->>Prof: Redirige al Canal de Chat 1 a 1 (/tickets/chat/{ticket_id}/)
        else Ya fue tomada por otro ingeniero
            DB-->>Repo: Rollback / Sin cambios
            Repo-->>UC: False
            UC-->>View: ResultadoOperacion(exito=False, "Ya fue tomada por otro profesional")
            View-->>Prof: Muestra alerta de conflicto en Bandeja
        end
    end

    %% Fase 3: Intercambio en Chat 1 a 1 y Finalización por el Profesional
    rect rgb(236, 253, 245)
        Note over Prod,DB: 3. Cierre Técnico (Finalización por el Ingeniero)
        Prof->>View: POST /tickets/finalizar/{ticket_id}/ (descripcion_finalizacion)
        View->>UC: FinalizarTrabajoTicketUseCase.ejecutar(ticket_id, profesional_id, descripcion)
        UC->>Repo: buscar_por_id(ticket_id)
        Repo-->>UC: TicketEntity (estado="Aceptado", profesional_id=prof.id)
        UC->>Repo: finalizar_trabajo(ticket_id, descripcion_finalizacion)
        Repo->>DB: UPDATE estado='Finalizado', descripcion_finalizacion, fecha_finalizacion=now()
        DB-->>Repo: OK
        Repo-->>UC: Confirmado
        UC-->>View: ResultadoOperacion(exito=True)
        View-->>Prof: Actualiza vista de Chat con Informe de Finalización
    end

    %% Fase 4: Confirmación de Recepción por el Productor
    rect rgb(246, 248, 246)
        Note over Prod,DB: 4. Confirmación de Recepción por el Productor
        Prod->>View: POST /tickets/confirmar/{ticket_id}/
        View->>UC: ConfirmarRecepcionTicketUseCase.ejecutar(ticket_id, productor_id)
        UC->>Repo: buscar_por_id(ticket_id)
        Repo-->>UC: TicketEntity (estado="Finalizado", productor_id=prod.id)
        UC->>Repo: confirmar_recepcion_productor(ticket_id)
        Repo->>DB: UPDATE confirmado_por_productor=True, fecha_confirmacion=now()
        DB-->>Repo: OK
        Repo-->>UC: Confirmado
        UC-->>View: ResultadoOperacion(exito=True)
        View-->>Prod: Muestra insignia "Recepción Confirmada"
    end
```
