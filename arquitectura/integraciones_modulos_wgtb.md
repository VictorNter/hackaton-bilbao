# Integraciones entre Módulos del Proyecto WGTB

## Tabla de Contenidos
1. [Visión General de Integraciones](#visión-general-de-integraciones)
2. [Flujos de Integración](#flujos-de-integración)
3. [Dependencias entre Módulos](#dependencias-entre-módulos)
4. [Interfaz Frontend - Backend](#interfaz-frontend---backend)
5. [Casos de Uso Principales](#casos-de-uso-principales)

---

## Visión General de Integraciones

El proyecto WGTB está organizado en tres módulos backend independientes que se comunican entre sí a través de interfaces bien definidas, y un frontend Angular que consume estos servicios a través de APIs REST generadas.

### Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    FRONTEND ANGULAR                             │
│           (app.module.ts, features, shared, core)               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Módulos API Generados:                               │   │
│  │  - ApibpmModule (api-bpm)                              │   │
│  │  - ApitableModule (api-table)                          │   │
│  │  - ApitemplatesModule (api-templates)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         │                                      │
└─────────────────────────┼──────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │ APIBPM   │      │ APITABLE │      │APITMPL   │
   │ Listener │      │ Listener │      │ Listener │
   └──────────┘      └──────────┘      └──────────┘
        │                 │                 │
        ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │ Services │      │ Services │      │ Services │
   │ (Appl)   │      │ (Appl)   │      │ (Appl)   │
   └──────────┘      └──────────┘      └──────────┘
        │                 │                 │
        ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │   BPM    │      │  TABLE   │      │TEMPLATE  │
   │Repository│      │Repository│      │Repository│
   └──────────┘      └──────────┘      └──────────┘
        │                 │                 │
        ▼                 ▼                 ▼
   ┌──────────┐      ┌──────────┐      ┌──────────┐
   │    BD    │      │    BD    │      │    BD    │
   └──────────┘      └──────────┘      └──────────┘
        │
        ├─→ XBPM Externo (ServiceApi)
        └─→ RDR Externo (RdrService)
```

---

## Flujos de Integración

### Flujo 1: Creación de Oportunidad (BusinessData) - Vista Completa

```
FRONTEND (Opportunity Detail Component)
    │
    ├─ El usuario carga la página de creación de oportunidad
    │
    └─→ HTTP POST /api/bpm/opportunities
        │
        ├─→ ApibpmModule genera la URL correcta
        ├─→ ProtocolService define el protocolo y headers
        └─→ ApibpmService envía petición HTTP
                │
                ▼
        BACKEND: ListenerApiBpm.createBusinessData(CreateBusinessDataDto)
            │
            ├─ Valida headers NOVA (usuario, metadatos)
            ├─ Mapea DTO → BusinessData (dominio)
            │
            └─→ ServiceApiBpmImpl.createOpportunityEvent(BusinessData)
                │
                ├─→ IBusinessDataRepository.saveBusinessData(businessData)
                │   │
                │   └─→ BusinessDataRepositoryImpl.saveBusinessData()
                │       ├─→ [MapStruct] BusinessData → BusinessDataJpa
                │       ├─→ [Spring Data] Persistir en BD
                │       └─→ [MapStruct] BusinessDataJpa → BusinessData
                │
                ├─→ xbpm/ServiceApi.sendEvent(businessData)
                │   └─→ XBPM EXTERNO: Motor BPM crea proceso
                │
                ├─→ IFieldRepository.saveField(fields)
                │   └─→ FieldRepositoryImpl persiste campos
                │
                └─→ Response HTTP 201 Created + BusinessDataDto
                    │
                    ├─ [MapStruct] BusinessData → BusinessDataDto
                    │
                    ▼
        FRONTEND: Observable recibe BusinessDataDto
            │
            └─→ TaskDetailComponent renderiza formulario
                └─→ Datos mostrados en UI
```

### Flujo 2: Actualización de Estado de Tarea - Sincronización BPM-DB

```
FRONTEND (Task Detail Component - Usuario completa tarea)
    │
    ├─ Usuario hace clic en "Aprobar"
    │
    └─→ HTTP PUT /api/bpm/tasks/{taskId}/status
        │
        ├─→ UpdateTaskDto: { status: "COMPLETED", action: "APPROVED" }
        │
        └─→ ApibpmService envía petición
                │
                ▼
        BACKEND: ListenerApiBpm.setTaskStatus(UpdateTaskDto)
            │
            ├─ Mapea DTO → Task (dominio)
            │
            └─→ ServiceApiBpmImpl.updateTaskStatus(task)
                │
                ├─→ Valida transición de estado (regla de negocio)
                │
                ├─→ ITaskRepository.saveTask(task)
                │   └─→ TaskRepositoryImpl persiste cambio
                │
                ├─→ IStatusHistoryRepository.saveStatusHistory(history)
                │   └─→ Registra auditoría del cambio
                │
                ├─→ xbpm/ServiceApi.completeTask(bpmTaskId, action)
                │   └─→ XBPM EXTERNO: Motor BPM marca tarea como completada
                │
                ├─→ Evalúa si hay siguiente tarea en el flujo
                │   │
                │   └─→ Si sí: ITaskRepository.saveTask(nextTask)
                │       └─→ Persiste próxima tarea
                │
                └─→ Response HTTP 200 OK + UpdatedTaskDto
                    │
                    ▼
        FRONTEND: Observable recibe UpdatedTaskDto
            │
            └─→ TaskDetailComponent actualiza UI
                └─→ Muestra siguiente tarea o resumen
```

### Flujo 3: Consulta de Datos de Tabla Maestro - Integración apitable

```
FRONTEND (Dashboard Component - Búsqueda avanzada)
    │
    ├─ Usuario abre modal de filtrado de tabla
    │
    └─→ HTTP GET /api/table/tables/{tableId}/data?filters=...
        │
        ├─→ InputPaginationInfoDto: { page: 1, size: 20, filters }
        │
        └─→ ApitableService envía petición
                │
                ▼
        BACKEND: ListenerApitable (generado - similar a ListenerApiBpm)
            │
            ├─ Mapea petición → parámetros dominio
            │
            └─→ ITableService.getTabledata(tableId, pagination)
                │
                ├─→ TableServiceImpl.getTabledata()
                │   │
                │   ├─→ ITableRepository.findById(tableId)
                │   │   └─→ Obtiene estructura de tabla
                │   │
                │   ├─→ RdrService.getTableData(tableId, filters)
                │   │   └─→ RDR EXTERNO: Consulta datos en RDR
                │   │       ├─→ RdrService.callDictionaryRdr()
                │   │       │   └─→ Resuelve IDs internos
                │   │       │
                │   │       └─→ RdrService.callPartyRdr()
                │   │           └─→ Obtiene datos completos
                │   │
                │   ├─→ Mapea datos RDR a ColumnValue[]
                │   │
                │   └─→ Aplica paginación y filtros
                │
                └─→ Response HTTP 200 OK + Page<List<ColumnValue>>
                    │
                    ▼
        FRONTEND: Observable recibe Page<ColumnValue[]>
            │
            └─→ TableComponent renderiza resultados
                └─→ Muestra filas paginadas con filtros
```

### Flujo 4: Carga de Plantillas de Formulario - Integración apitemplates

```
FRONTEND (Opportunity Detail Component - Renderiza formulario dinámico)
    │
    ├─ Componente necesita renderizar secciones de formulario
    │
    └─→ HTTP GET /api/templates/templates/{templateId}
        │
        └─→ ApitemplatesService envía petición
                │
                ▼
        BACKEND: ListenerApitemplates (generado)
            │
            ├─ Mapea DTO petición
            │
            └─→ ITemplateService.findById(templateId)
                │
                ├─→ TemplateServiceImpl.findById()
                │   │
                │   └─→ ITemplateRepository.findById(templateId)
                │       │
                │       ├─→ TemplateRepositoryImpl.findById()
                │       │   │
                │       │   ├─→ [MapStruct] TemplateJpa → Template
                │       │   │
                │       │   ├─→ ISectionService.findById(sectionId) [para cada sección]
                │       │   │   └─→ Obtiene detalles de secciones
                │       │   │
                │       │   └─→ Construye Template completo con secciones
                │       │
                │       └─→ Template con estructura hierárquica
                │
                └─→ Response HTTP 200 OK + TemplateDto
                    │
                    ├─ [MapStruct] Template → TemplateDto
                    │
                    ▼
        FRONTEND: Observable recibe TemplateDto
            │
            └─→ DetailTemplatesComponent renderiza dinámicamente
                │
                ├─ Para cada Section:
                │   └─→ DetailTemplatesComponent renderiza SectionComponent
                │       └─→ Renderiza campos dentro de cada sección
                │
                └─→ UI muestra formulario organizado por secciones
```

---

## Dependencias entre Módulos

### Dependencias de apibpm

```
apibpm (módulo de procesamiento BPM)
│
├─→ INTERNAS
│   ├─→ IFieldService (de application)
│   │   └─→ Para gestión de campos personalizados
│   │
│   ├─→ ICommentService (de application)
│   │   └─→ Para agregar comentarios a tareas
│   │
│   └─→ IStatusHistoryRepository (de infrastructure)
│       └─→ Para registrar cambios de estado
│
├─→ EXTERNAS (Servicios de otro módulo)
│   └─→ ISectionValueService (desde apitemplates)
│       └─→ Para mapear valores de secciones de plantillas
│           a campos de entidades
│
├─→ SISTEMAS EXTERNOS
│   ├─→ xbpm/ServiceApi (Motor BPM)
│   │   ├─→ sendEvent() - Crea procesos
│   │   ├─→ completeTask() - Cierra tareas
│   │   ├─→ getTaskInfo() - Obtiene info BPM
│   │   └─→ queryTasks() - Consulta tareas activas
│   │
│   └─→ rdr/RdrService (Registry Data Repository)
│       ├─→ getPartyData() - Obtiene datos de terceros
│       └─→ resolveDictionary() - Resuelve códigos
│
└─→ BASE DE DATOS
    └─→ Tablas: business_data, task, comment, field, status_history
```

### Dependencias de apitableservices

```
apitableservices (módulo de tablas maestro)
│
├─→ INTERNAS
│   ├─→ ITableService (application)
│   │   └─→ Servicio principal de tablas
│   │
│   ├─→ ITableColumnService (application)
│   │   └─→ Gestión de columnas
│   │
│   └─→ ISelectionValueService (application)
│       └─→ Valores para dropdowns/selecciones
│
├─→ EXTERNAS (Servicios de otro módulo)
│   └─→ Ninguna (módulo independiente)
│
├─→ SISTEMAS EXTERNOS
│   └─→ rdr/RdrService (Registry Data Repository)
│       ├─→ getTableData() - Obtiene datos de tablas RDR
│       ├─→ queryWithFilters() - Consulta con filtros
│       └─→ resolveDictionary() - Para resoluciones
│
└─→ BASE DE DATOS
    └─→ Tablas: table, column, column_value, selection_value
```

### Dependencias de apitemplates

```
apitemplates (módulo de plantillas)
│
├─→ INTERNAS
│   ├─→ ITemplateService (application)
│   │   └─→ Gestión de plantillas
│   │
│   ├─→ ISectionService (application)
│   │   └─→ Gestión de secciones
│   │
│   └─→ ISectionValueService (application)
│       └─→ Gestión de valores en secciones
│
├─→ EXTERNAS (Servicios de otro módulo)
│   └─→ apibpm/IFieldService
│       └─→ Los campos de BusinessData/Task pueden referenciar
│           secciones de plantillas (via Field.sectionValue)
│
├─→ SISTEMAS EXTERNOS
│   └─→ Ninguno directo
│
└─→ BASE DE DATOS
    └─→ Tablas: template, section, section_value
```

### Matriz de Dependencias

|  De \ A  | apibpm | apitable | apitemplates |
|----------|--------|----------|--------------|
| **apibpm** | ✓ (mismo módulo) | ✗ | ✓ (F.K. en Field.sectionValue) |
| **apitable** | ✗ | ✓ (mismo módulo) | ✗ |
| **apitemplates** | ✓ (ref. inversa) | ✗ | ✓ (mismo módulo) |

---

## Interfaz Frontend - Backend

### Arquitectura Frontend

```
FRONTEND ANGULAR (gtbwfront)
│
├─ app.module.ts
│   ├─ Importa ApibpmModule (api-bpm)
│   ├─ Importa ApitableModule (api-table)
│   ├─ Importa ApitemplatesModule (api-templates)
│   ├─ Importa CoreModule
│   └─ Importa SharedModule
│
├─ core/ (Servicios transversales)
│   ├─ services/
│   │   ├─ protocol.service.ts
│   │   │   ├─ getProtocol()
│   │   │   ├─ getNovaRequestConfig()
│   │   │   ├─ getNovaMetadata()
│   │   │   └─ ProtocolService inyecta ApibpmService, ApitableService, ApitemplatesService
│   │   │
│   │   ├─ user.service.ts
│   │   │   └─ getCurrentUser()
│   │   │
│   │   └─ icon-registry.service.ts
│   │       └─ Inicializa iconos de la aplicación
│   │
│   ├─ interceptors/
│   │   └─ error.interceptor.ts
│   │       └─ Captura errores HTTP globales
│   │
│   └─ adapters/
│       ├─ date-adapters.ts
│       └─ date-formats.ts
│
├─ features/ (Componentes de características)
│   ├─ opportunity-detail/
│   │   ├─ opportunity-detail.component.ts
│   │   │   └─ Inyecta ActivatedRoute para leer parámetros
│   │   ├─ opportunity-detail.module.ts
│   │   │   └─ Importa ApibpmModule para consumir BusinessData
│   │   └─ opportunity-detail-routing.module.ts
│   │
│   ├─ task-detail/
│   │   ├─ task-detail.component.ts
│   │   │   ├─ Inyecta ApibpmService
│   │   │   ├─ Inyecta TaskStatusService
│   │   │   └─ Maneja ciclo de vida de tarea
│   │   │
│   │   ├─ services/
│   │   │   ├─ task-status.service.ts
│   │   │   │   ├─ Gestiona estado local de tarea
│   │   │   │   ├─ Consume ApibpmService para obtener datos
│   │   │   │   └─ Usa BehaviorSubject para compartir estado
│   │   │   │
│   │   │   ├─ form.service.ts
│   │   │   │   └─ Gestiona estado de formularios dinámicos
│   │   │   │
│   │   │   ├─ masterData.service.ts
│   │   │   │   ├─ Consume ApitableService
│   │   │   │   └─ Cachea datos maestro
│   │   │   │
│   │   │   └─ search-RDR.service.ts
│   │   │       └─ Busca en Registry Data Repository
│   │   │
│   │   ├─ components/
│   │   │   └─ Renderiza secciones de plantillas
│   │   │
│   │   └─ models/
│   │       └─ Interfaces TypeScript del dominio
│   │
│   ├─ dashboard-tables/
│   │   ├─ Consume ApitableService
│   │   └─ Muestra tablas maestro con filtros
│   │
│   ├─ home/
│   │   └─ Landing page
│   │
│   └─ status-pages/
│       └─ Páginas especiales de estado
│
├─ shared/ (Componentes y servicios compartidos)
│   ├─ components/
│   │   ├─ detail-templates/ (CLAVE)
│   │   │   ├─ detail-templates.component.ts
│   │   │   └─ Renderiza dinámicamente secciones de plantillas
│   │   │       (Integración con apitemplates)
│   │   │
│   │   ├─ table/
│   │   │   ├─ Renderiza tablas genéricas
│   │   │   └─ Integración con apitableservices para datos
│   │   │
│   │   ├─ process-stepper/
│   │   │   └─ Muestra pasos del flujo BPM
│   │   │
│   │   ├─ comment-text-area/
│   │   │   └─ Componente para agregar comentarios
│   │   │
│   │   └─ logs-comments/
│   │       └─ Muestra historial de comentarios
│   │
│   ├─ models/
│   │   ├─ generic.model.ts
│   │   │   ├─ DynamicInterface (para datos dinámicos)
│   │   │   ├─ FormState
│   │   │   └─ FormDataStore
│   │   │
│   │   ├─ table.model.ts
│   │   ├─ log.model.ts
│   │   └─ process-step-dto.model.ts
│   │
│   ├─ enums/
│   │   ├─ taskStatus.enum.ts
│   │   ├─ taskType.enum.ts
│   │   └─ (Espejan enums del backend)
│   │
│   ├─ services/
│   │   ├─ confirmation.service.ts
│   │   │   └─ Servicio para mostrar confirmaciones
│   │   │
│   │   └─ (Servicios compartidos)
│   │
│   └─ shared.module.ts
│       └─ Declara todos los componentes y módulos Material
│
├─ utils/
│   └─ baseUri/
│       ├─ baseuri.factory.ts
│       └─ baseuri.injection.token.ts
│           └─ Inyecta URL base para APIs
│
└─ environments/
    ├─ environment.ts (desarrollo)
    └─ environment.prod.ts (producción)
```

### Flujo de Datos Frontend-Backend

```
Usuario interactúa con UI
    │
    ▼
Component Angular (task-detail.component.ts)
    │
    ├─ Inyecta ApibpmService (de api-bpm)
    │
    ▼
ApibpmService.getTask(taskId)
    │
    ├─ Construye URL: `${baseUri}/SHIVA/api/bpm/tasks/${taskId}`
    ├─ Usa NovaMetadata (headers)
    ├─ Usa NovaRequestConfig (protocolo)
    │
    ▼
HTTP GET /SHIVA/api/bpm/tasks/{taskId}
    │
    ├─ Header: X-Release: ${release}
    ├─ Header: X-User: ${user}
    └─ Otros headers NOVA
    │
    ▼
BACKEND: ListenerApiBpm.getTask()
    │
    ├─ Extrae usuario de contexto de seguridad NOVA
    ├─ Mapea DTO HTTP → Dominio
    │
    ▼
ServiceApiBpmImpl.getTask()
    │
    ├─ Lógica de negocio
    │
    ▼
TaskRepositoryImpl.findById()
    │
    ├─ [MapStruct] TaskJpa → Task
    │
    ▼
Base de Datos
    │
    ▼
Respuesta JSON (TaskDto)
    │
    ├─ [MapStruct] Task → TaskDto
    │
    ▼
HTTP 200 OK + TaskDto
    │
    ▼
Frontend: Observable<TaskDto>
    │
    ├─ ApibpmService devuelve Observable
    │
    ▼
Component suscribe con subscribe() o | async pipe
    │
    ▼
Task Status Service cachea datos en BehaviorSubject
    │
    ▼
DetailTemplatesComponent renderiza secciones
    │
    ▼
UI actualizada
```

---

## Casos de Uso Principales

### Caso 1: Crear Nueva Oportunidad de Negocio

**Actores**: Usuario del negocio, WGTB Frontend, WGTB Backend (apibpm), XBPM Externo

**Flujo**:

1. Usuario accede a `/WGTB/new-opportunity`
2. Carga `OpportunityDetailComponent`
3. Usuario rellena formulario (datos básicos)
4. Usuario hace clic en "Crear Oportunidad"
5. **Frontend**: Construye `CreateBusinessDataDto`
   ```typescript
   const businessData: CreateBusinessDataDto = {
       businessId: 'OPP-001',
       fields: [{ fieldCode: 'name', value: 'Mi Oportunidad' }]
   };
   ```
6. **Frontend**: `ApibpmService.createBusinessData(businessData)`
7. **Backend**: `ListenerApiBpm.createBusinessData()` recibe petición
8. **Backend**: `ServiceApiBpmImpl.createOpportunityEvent()`
   - Valida datos
   - `IBusinessDataRepository.saveBusinessData()` → Persiste en BD
   - `IFieldRepository.saveField()` → Persiste campos
   - `xbpm/ServiceApi.sendEvent()` → Notifica a XBPM
9. **XBPM**: Crea proceso y primera tarea
10. **Backend**: Retorna `HTTP 201 + BusinessDataDto`
11. **Frontend**: Redirecciona a `/WGTB/opportunity/{businessId}`
12. UI muestra formulario con siguiente tarea

---

### Caso 2: Completar Tarea en Flujo BPM

**Actores**: Usuario del negocio, Task Detail Component, TaskStatusService, WGTB Backend

**Flujo**:

1. Usuario abre detalle de tarea
2. `TaskDetailComponent` carga `task-detail.component.ts`
3. **Frontend**: `ApibpmService.getTask(bpmTaskId)`
4. **Backend**: Retorna `TaskDto` con datos de tarea y oportunidad
5. **Frontend**: `TaskStatusService.setSelectedTask()` cachea datos
6. UI renderiza:
   - **DetailTemplatesComponent**: Secciones de formulario (de apitemplates)
   - **LogsCommentsComponent**: Histórico de cambios
   - Botones de acciones (Aprobar, Rechazar, etc.)
7. Usuario completa campos del formulario
8. Usuario hace clic en "Aprobar"
9. **Frontend**: Construye `UpdateTaskDto`
   ```typescript
   const updateTask: UpdateTaskDto = {
       taskId: '12345',
       fields: [updated fields],
       action: 'APPROVED',
       status: 'COMPLETED'
   };
   ```
10. **Frontend**: `ApibpmService.updateTask(updateTask)`
11. **Backend**: `ListenerApiBpm.updateTask()`
12. **Backend**: `ServiceApiBpmImpl.updateTaskStatus()`
    - Valida transición de estado
    - `ITaskRepository.saveTask()` → Persiste cambio de estado
    - `IStatusHistoryRepository.saveStatusHistory()` → Registra auditoría
    - `xbpm/ServiceApi.completeTask()` → Notifica XBPM
    - Crea siguiente tarea si aplica
13. **Backend**: Retorna `HTTP 200 + UpdatedTaskDto`
14. **Frontend**: UI se actualiza automáticamente
    - Muestra siguiente tarea o resumen si flujo terminó

---

### Caso 3: Búsqueda en Tabla Maestro

**Actores**: Usuario, Dashboard Table Component, ApitableService, WGTB Backend (apitableservices)

**Flujo**:

1. Usuario accede a `/WGTB/dashboard`
2. Usuario abre filtro avanzado
3. Usuario busca en tabla "Clientes"
4. **Frontend**: Construye `InputPaginationInfoDto`
   ```typescript
   const pagination: InputPaginationInfoDto = {
       page: 1,
       size: 20,
       filters: [{ field: 'name', value: 'BBVA*' }]
   };
   ```
5. **Frontend**: `ApitableService.getTabledata(tableId, pagination)`
6. **Backend**: `TableServiceImpl.getTabledata()`
   - `ITableRepository.findById()` → Estructura de tabla
   - `RdrService.getTableData()` → Consulta RDR con filtros
     - Llama `ServiceRdrdictionary` → Resuelve IDs
     - Llama `ServiceRdrparty` → Obtiene datos completos
   - Mapea respuesta RDR a `List<ColumnValue>`
   - Aplica paginación
7. **Backend**: Retorna `Page<List<ColumnValue>>`
8. **Frontend**: `TableComponent` renderiza resultados
   - Cada fila es un `List<ColumnValue>`
   - Muestra columnas según estructura de tabla

---

### Caso 4: Renderizar Formulario Dinámico de Plantilla

**Actores**: UI Component, Template Service, Field Mapper

**Flujo**:

1. Tarea cargada tiene `fields` con `sectionValue` referencias
2. **Frontend**: Necesita renderizar formulario dinámico
3. **Frontend**: `ApitemplatesService.getTemplate(templateId)`
4. **Backend**: `TemplateServiceImpl.findById()`
   - `ITemplateRepository.findById()`
   - `ISectionService.findById()` para cada sección
   - Retorna estructura completa: `Template` con `Section[]`
5. **Backend**: Retorna `TemplateDto` con jerarquía
   ```json
   {
       "templateId": 1,
       "sections": [
           {
               "sectionId": 1,
               "name": "Información General",
               "sectionValues": [...]
           },
           {
               "sectionId": 2,
               "name": "Datos Adicionales",
               "sectionValues": [...]
           }
       ]
   }
   ```
6. **Frontend**: `DetailTemplatesComponent` itera sobre secciones
7. Para cada `SectionValue`, renderiza componente dinámico
   - Input text
   - Dropdown (datos de `apitableservices`)
   - Date picker
   - etc.
8. Usuario interactúa con campos
9. **Frontend**: Guarda valores en `FormDataStore`
10. Al completar tarea, envía valores al backend (como parte de `UpdateTaskDto`)

---

## Patrones de Comunicación

### Patrón 1: Service Pattern (Transaccional)

```
Frontend Component
    │
    └─→ ApibpmService.method(data)
        │
        ├─ Constructor HttpClient
        ├─ Construye URL
        ├─ Envía HTTP (GET/POST/PUT/DELETE)
        │
        └─→ Observable<ResponseDto>
            │
            └─→ Listener REST Backend
                │
                ├─ Mapea DTO → Dominio
                ├─ Llama Service (transaccional)
                ├─ Repository persiste
                │
                └─→ Mapea Dominio → DTO (respuesta)
                    │
                    └─→ HTTP Response
```

### Patrón 2: Cascading Service Calls (Orquestación)

```
Component A necesita datos de múltiples servicios
    │
    └─→ combineLatest([
        ApibpmService.getTask(),
        ApitableService.getTable(),
        ApitemplatesService.getTemplate()
    ])
    │
    ├─ Espera a que todos completen
    │
    └─→ Renderiza UI con datos combinados
```

### Patrón 3: State Management con BehaviorSubject

```
TaskStatusService
    │
    ├─ Guarda estado en BehaviorSubject
    ├─ selectedTaskData$: BehaviorSubject<DynamicInterface>
    │
    └─→ Components suscriben con .asObservable()
        │
        ├─ Si datos cambian → Notifica automáticamente
        └─ Múltiples componentes sincronizan estado
```

---

## Conclusiones

El proyecto WGTB implementa una arquitectura modular y escalable donde:

1. **Separación de Responsabilidades**: Cada módulo (apibpm, apitable, apitemplates) tiene responsabilidades claras
2. **Comunicación Aislada**: Los módulos se comunican a través de interfaces bien definidas
3. **Frontend Agnóstico**: El frontend Angular consume APIs REST de los módulos sin conocer su implementación interna
4. **Arquitectura Hexagonal**: La separación Domain-Application-Infrastructure garantiza testabilidad y mantenibilidad
5. **Escalabilidad**: Es fácil agregar nuevos módulos sin afectar los existentes


