# Resumen Visual - Arquitectura WGTB

## 🏗️ Arquitectura de Alto Nivel

```
┌────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND ANGULAR                              │
│                    (gtbwfront - TypeScript/Angular)                   │
│                                                                        │
│  ┌──────────────┬──────────────┬──────────────────────────────────┐   │
│  │  Core Module │ Shared Comp. │ Features (Task, Opportunity)    │   │
│  ├──────────────┼──────────────┼──────────────────────────────────┤   │
│  │ • Services   │ • Components │ • task-detail                   │   │
│  │ • Guards     │ • Pipes      │ • opportunity-detail            │   │
│  │ • Intercept. │ • Validators │ • dashboard                     │   │
│  │ • Adapters   │ • Models     │ • forms                         │   │
│  └──────────────┴──────────────┴──────────────────────────────────┘   │
│         ↑                                                              │
│         │ HTTP REST (JSON)                                            │
└─────────┼──────────────────────────────────────────────────────────────┘
          │
          │ ┌─────────────────────────────────────────────────────────────┐
          │ │              BACKEND JAVA/SPRING BOOT                      │
          │ │         (wgtbBackend - 3 módulos independientes)          │
          │ │                                                             │
          ▼ ▼                                                             │
    ┌─────────────┐   ┌──────────────┐   ┌──────────────┐              │
    │   APIBPM    │   │  APITABLE    │   │ APITEMPLATES │              │
    │             │   │              │   │              │              │
    │ ┌─────────┐ │   │ ┌──────────┐ │   │ ┌──────────┐ │              │
    │ │Listener │─┼───┼→│Listener  │─┼───┼→│Listener  │ │              │
    │ │  REST   │ │   │ │  REST    │ │   │ │  REST    │ │              │
    │ └────┬────┘ │   │ └──────┬───┘ │   │ └────┬─────┘ │              │
    │      │      │   │        │     │   │      │       │              │
    │ ┌────▼────┐ │   │ ┌──────▼──┐ │   │ ┌────▼─────┐ │              │
    │ │Application     │   │Application  │   │Application │              │
    │ │ Services  │ │   │ Services │ │   │ Services │ │              │
    │ └────┬────┘ │   │ └──────┬──┘ │   │ └────┬────┘ │              │
    │      │      │   │        │    │   │      │      │              │
    │ ┌────▼────┐ │   │ ┌──────▼──┐ │   │ ┌────▼────┐ │              │
    │ │Repository    │   │Repository   │   │Repository  │              │
    │ │(Data Access) │   │(Data Access)│   │(Data Access)              │
    │ └────┬────┘ │   │ └──────┬──┘ │   │ └────┬────┘ │              │
    │      │      │   │        │    │   │      │      │              │
    │ ┌────▼────┐ │   │ ┌──────▼──┐ │   │ ┌────▼────┐ │              │
    │ │  Domain    │   │  Domain    │   │  Domain    │              │
    │ │ Entities  │ │   │ Entities │ │   │ Entities │ │              │
    │ └──────────┘ │   │ └────────┘ │   │ └────────┘ │              │
    └─────────────┘   └──────────────┘   └──────────────┘              │
         │                  │                   │                      │
         │                  │                   │                      │
         ▼                  ▼                   ▼                      │
    ┌─────────────────────────────────────────────────────┐          │
    │              BASE DE DATOS (PostgreSQL)            │          │
    │                                                     │          │
    │ • business_data  • table       • template           │          │
    │ • task           • column      • section            │          │
    │ • comment        • column_val  • section_val        │          │
    │ • field          • select_val  •                    │          │
    │ • status_history                                    │          │
    └─────────────────────────────────────────────────────┘          │
                          │                                           │
    ┌─────────────────────┼──────────────────────────────────────┐   │
    │ SISTEMAS EXTERNOS    │                                    │   │
    │                      ▼                                    │   │
    │    ┌──────────────────────────┐                         │   │
    │    │  XBPM (Motor BPM)        │                         │   │
    │    │ - Orquesta procesos      │                         │   │
    │    │ - Gestiona tareas        │                         │   │
    │    │ - Define flujos          │                         │   │
    │    └──────────────────────────┘                         │   │
    │                                                          │   │
    │    ┌──────────────────────────┐                         │   │
    │    │  RDR (Data Registry)     │                         │   │
    │    │ - Datos terceros         │                         │   │
    │    │ - Tablas maestro         │                         │   │
    │    │ - Resoluciones           │                         │   │
    │    └──────────────────────────┘                         │   │
    └──────────────────────────────────────────────────────────────┘
```

---

## 📊 Arquitectura de Capas (Hexagonal)

```
                          ┌─────────────┐
                          │  APLICACIÓN │
                          │ (Servicios) │
                          └──────┬──────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                                                         │
    │       ┌──────────────────────────────────────┐         │
    │       │      PUERTOS DE ENTRADA             │         │
    │       │  (REST Listeners - Inbound)         │         │
    │       │                                     │         │
    │       │  • HTTP Requests                   │         │
    │       │  • Mapeo DTO → Dominio             │         │
    │       │  • Validación                      │         │
    │       └──────────────────────────────────────┘         │
    │                     ▼                                  │
    │       ┌──────────────────────────────────────┐         │
    │       │      NUCLEO DE NEGOCIO              │         │
    │       │  (Domain Model)                     │         │
    │       │                                     │         │
    │       │  • Entidades                        │         │
    │       │  • Enums                            │         │
    │       │  • Lógica Dominio Pura              │         │
    │       │  • SIN dependencias externas        │         │
    │       └──────────────────────────────────────┘         │
    │                     ▲                                  │
    │       ┌──────────────────────────────────────┐         │
    │       │      PUERTOS DE SALIDA              │         │
    │       │  (Outbound Adapters)                │         │
    │       │                                     │         │
    │       │  • Repositories (BD)                │         │
    │       │  • XBPM Client                      │         │
    │       │  • RDR Client                       │         │
    │       │  • Mapeo Dominio → DTO              │         │
    │       └──────────────────────────────────────┘         │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Datos Típico

```
1. USUARIO INTERACTÚA
   │
   ▼
2. FRONTEND ENVÍA PETICIÓN HTTP
   POST /api/bpm/tasks/{id}
   Body: UpdateTaskDto { status: "COMPLETED", action: "APPROVED" }
   │
   ▼
3. BACKEND RECIBE EN LISTENER REST
   ListenerApiBpm.updateTask(UpdateTaskDto)
   │
   ├─→ Valida headers NOVA (usuario, seguridad)
   ├─→ Mapea DTO → Entidad Dominio
   │
   ▼
4. SERVICIO APLICA LÓGICA DE NEGOCIO
   ServiceApiBpmImpl.updateTask(Task)
   │
   ├─→ Valida reglas de negocio
   ├─→ Coordina múltiples repositorios
   ├─→ Maneja transacciones
   │
   ▼
5. REPOSITORIO PERSISTE
   TaskRepositoryImpl.saveTask(Task)
   │
   ├─→ Mapea Entidad Dominio → JPA
   ├─→ Spring Data ejecuta INSERT/UPDATE
   ├─→ Mapea resultado JPA → Dominio
   │
   ▼
6. SISTEMAS EXTERNOS NOTIFICADOS
   │
   ├─→ xbpm/ServiceApi.completeTask()
   │   └─→ Motor XBPM marca tarea como completa
   │
   └─→ StatusHistory registra auditoría
       └─→ BD guarda cambio de estado
           │
           ▼
7. RESPUESTA ENVIADA AL FRONTEND
   HTTP 200 OK
   Body: UpdatedTaskDto { taskId, status: "COMPLETED", ... }
   │
   ▼
8. FRONTEND ACTUALIZA UI
   TaskDetailComponent actualiza pantalla
   │
   ▼
9. USUARIO VE RESULTADO
```

---

## 📦 Estructura de Módulos

```
apibpm (API BPM)
├─ Responsabilidad: Gestión de procesos de negocio
├─ Entidades: BusinessData, Task, Comment, Field, StatusHistory
├─ Servicios: IServiceApiBpm, IBusinessDataService, IFieldService, ICommentService
├─ Externos: XBPM, RDR
└─ Tablas BD: business_data, task, comment, field, status_history

apitableservices (API Table Services)
├─ Responsabilidad: Gestión de tablas maestro
├─ Entidades: Table, Column, ColumnValue, SelectionValue
├─ Servicios: ITableService, ITableColumnService, ISelectionValueService
├─ Externos: RDR (Datos maestro)
└─ Tablas BD: table, column, column_value, selection_value

apitemplates (API Templates)
├─ Responsabilidad: Gestión de plantillas de formularios
├─ Entidades: Template, Section, SectionValue
├─ Servicios: ITemplateService, ISectionService, ISectionValueService
├─ Externos: Ninguno
└─ Tablas BD: template, section, section_value
```

---

## 🔌 Integraciones de Módulos

```
                apibpm
                  │ │
                  │ ├──────→ Referencia a apitemplates
                  │         (Field.sectionValue)
                  │
                  └──────→ Sistema Externo: XBPM
                  
                apitableservices
                  │
                  └──────→ Sistema Externo: RDR
                  
                apitemplates
                  │
                  └──→ (Independiente, referenciado por apibpm)
```

---

## 🔐 Capas de Seguridad

```
┌─────────────────────────────────────────────────┐
│  1. HTTP Headers Validation                    │
│     (NOVA Framework)                           │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  2. Authentication & Authorization              │
│     (NovaSecurityContext)                      │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  3. Input Validation                            │
│     (Listeners, Servicios)                     │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  4. Business Rules Validation                   │
│     (Servicios de Aplicación)                  │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  5. Database Constraints                        │
│     (Unique, FK, Check)                        │
└─────────────────────────────────────────────────┘
```

---

## 📋 Matriz de Módulos

| Aspecto | apibpm | apitable | apitemplates |
|---------|--------|----------|--------------|
| **Core** | BusinessData, Task | Table, Column | Template, Section |
| **Listeners** | ListenerApiBpm | ListenerApitable | ListenerApitemplates |
| **Servicios** | 5 | 3 | 3 |
| **Repositorios** | 5 | 3 | 3 |
| **BD Tables** | 5 | 4 | 3 |
| **Externos** | XBPM, RDR | RDR | - |
| **Dependencias** | - | - | apibpm (ref) |

---

## 🎯 Ciclo de Vida de una Oportunidad

```
CREAR
  │
  ├─→ HTTP POST /api/bpm/opportunities
  │   ├─→ ListenerApiBpm.createBusinessData()
  │   ├─→ ServiceApiBpmImpl.createOpportunityEvent()
  │   ├─→ IBusinessDataRepository.save()
  │   ├─→ xbpm/ServiceApi.sendEvent() → XBPM crea proceso
  │   └─→ Retorna HTTP 201 + BusinessDataDto
  │
  ├─→ BD: INSERT INTO business_data (status = IN_PROGRESS)
  │
  ▼
PRIMERA TAREA CREADA
  │
  ├─→ XBPM crea primera tarea
  │
  ├─→ HTTP GET /api/bpm/tasks/{taskId}
  │   ├─→ ListenerApiBpm.getTask()
  │   ├─→ ServiceApiBpmImpl.getTask()
  │   ├─→ ITaskRepository.findById()
  │   └─→ Retorna HTTP 200 + TaskDto
  │
  ▼
USUARIO COMPLETA TAREA
  │
  ├─→ HTTP PUT /api/bpm/tasks/{taskId}
  │   ├─→ ListenerApiBpm.updateTask()
  │   ├─→ ServiceApiBpmImpl.updateTask()
  │   ├─→ ITaskRepository.save()
  │   ├─→ IStatusHistoryRepository.save() → Registra cambio
  │   ├─→ xbpm/ServiceApi.completeTask() → XBPM completa tarea
  │   └─→ Retorna HTTP 200 + UpdatedTaskDto
  │
  ├─→ BD: UPDATE task SET status = COMPLETED
  ├─→ BD: INSERT INTO status_history (registro de cambio)
  │
  ▼
SIGUIENTE TAREA (si aplica)
  │
  ├─→ XBPM crea siguiente tarea
  ├─→ ServiceApiBpmImpl crea Task en BD
  └─→ Usuario ve nueva tarea
  │
  ▼
ÚLTIMA TAREA COMPLETADA
  │
  ├─→ HTTP PUT /api/bpm/opportunities/{oppId}/status
  │   └─→ Cambia status a COMPLETED
  │
  ├─→ BD: UPDATE business_data SET status = COMPLETED
  │
  ▼
OPORTUNIDAD FINALIZADA ✓
```

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| **Backend** | Spring Boot | 2.x |
| **ORM** | Hibernate/JPA | 5.x |
| **BD** | PostgreSQL | 12+ |
| **BD Migrations** | Flyway | 7.x |
| **Mapeo** | MapStruct | 1.x |
| **Inyección** | Spring DI | - |
| **REST** | Spring MVC | - |
| **Seguridad** | NOVA Framework | - |
| **Frontend** | Angular | 12+ |
| **UI Components** | Material Design | - |
| **Build** | Maven | 3.x |

---

## 📈 Escalabilidad

```
Dentro de un Módulo (ej: apibpm)
  ├─ Agregar nuevas Entidades → Nueva carpeta en domain/entity/
  ├─ Agregar nuevos Servicios → Nueva interfaz + impl
  ├─ Agregar nuevos Repositorios → Nueva interfaz + impl + JPA
  └─ Extensible sin afectar otros módulos

Entre Módulos
  ├─ Los módulos son independientes
  ├─ Comunicación solo a través de interfaces
  ├─ Fácil agregar nuevos módulos
  └─ Sin dependencias circulares

Externos
  ├─ XBPM: A través de ServiceApi
  ├─ RDR: A través de RdrService
  └─ Fácil reemplazar sin cambiar código interno
```

---

## 🐛 Puntos de Error Comunes

```
Error: EntityNotFoundException
└─ Revisar: ¿Existe el ID en BD?

Error: LazyInitializationException
└─ Revisar: ¿Se accede a colección fuera de transacción?

Error: DataIntegrityViolationException
└─ Revisar: ¿Cumple restricciones de BD? (unique, FK)

Error: NullPointerException en Mapper
└─ Revisar: ¿Mapper está inyectado? ¿El mapper tiene @Mapper?

Error: HTTP 404 Inesperado
└─ Revisar: ¿El @Path del listener es correcto?

Error: HTTP 500 en createBusinessData
└─ Revisar: ¿XBPM está disponible? ¿Credenciales RDR?
```

---

## 📊 Diagrama ER Simplificado

```
business_data (opportunities)
    │
    ├──→ task (tareas del flujo)
    │     │
    │     ├──→ comment (comentarios en tarea)
    │     │
    │     ├──→ field (campos personalizados)
    │     │     │
    │     │     └──→ section_value (referencia a plantilla)
    │     │
    │     └──→ status_history (auditoría de cambios)
    │
    ├──→ comment (comentarios en oportunidad)
    │
    ├──→ field (campos personalizados)
    │     │
    │     └──→ section_value (referencia a plantilla)
    │
    └──→ status_history (auditoría de cambios)

(Tablas independientes)
table
    └──→ column
         └──→ column_value (datos de tabla)
         └──→ selection_value (opciones dropdown)

template
    └──→ section
         └──→ section_value (valores de sección)
```

---

## 📝 Notas Importantes

- **SIN Generación Manual**: Listeners generados por KLTT-APIRestGenerator
- **Auditoría Automática**: Todos los cambios quedan registrados
- **Transacciones**: Coordina múltiples operaciones de BD
- **Mapeo Automático**: MapStruct maneja conversiones
- **Escalable**: Fácil agregar nuevas funcionalidades
- **Testeable**: Separación clara de responsabilidades

---

**Última actualización**: 2026-04-20


