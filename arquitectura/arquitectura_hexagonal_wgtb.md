# Arquitectura Hexagonal del Proyecto WGTB

## Índice
1. [Descripción General](#descripción-general)
2. [Estructura de Capas](#estructura-de-capas)
3. [Módulos Principales](#módulos-principales)
4. [Flujo de Comunicación](#flujo-de-comunicación)
5. [Patrones de Implementación](#patrones-de-implementación)
6. [Adaptadores y Puertos](#adaptadores-y-puertos)
7. [Gestión de Errores](#gestión-de-errores)

---

## Descripción General

El proyecto WGTB implementa **Arquitectura Hexagonal (Ports & Adapters)** mediante una estructura modular basada en tres módulos independientes:

- **apibpm**: Gestión de procesos de negocio (Business Process Management)
- **apitableservices**: Servicios de tablas de datos
- **apitemplates**: Gestión de plantillas de formularios

Cada módulo sigue el mismo patrón hexagonal: **Application → Infrastructure → Domain**, con separación clara entre la lógica de negocio y los adaptadores externos.

---

## Estructura de Capas

### Estructura General por Módulo

```
src/main/java/com/bbva/wgtb/wgtbbackend/{modulo}/
├── application/        (Servicios de aplicación - Puertos internos)
├── domain/            (Entidades de dominio - Núcleo del negocio)
├── infrastructure/    (Adaptadores - Persistencia, REST, mapeos)
```

### 1. **Capa de Dominio (Domain)**

**Ubicación**: `{modulo}/domain/`

**Responsabilidad**: Contiene la lógica de negocio pura e independiente de cualquier framework.

**Componentes principales**:

#### a) **Entidades de Dominio** (`domain/entity/`)
Son objetos que representan conceptos del negocio:

| Entidad | Descripción | Ubicación |
|---------|-------------|-----------|
| **Task** | Representa una tarea en el flujo BPM con ciclo de vida completo | `apibpm/domain/entity/Task.java` |
| **BusinessData** | Oportunidad de negocio central, contiene tareas, comentarios y campos | `apibpm/domain/entity/BusinessData.java` |
| **Comment** | Comentarios en tareas y oportunidades para auditoría | `apibpm/domain/entity/Comment.java` |
| **Field** | Campos personalizados de datos en tareas y oportunidades | `apibpm/domain/entity/Field.java` |
| **StatusHistory** | Historial de cambios de estado de tareas y oportunidades | `apibpm/domain/entity/StatusHistory.java` |
| **Table** | Tabla de datos maestros | `apitableservices/domain/entity/Table.java` |
| **Column** | Columna de una tabla maestro | `apitableservices/domain/entity/Column.java` |
| **Template** | Plantilla de formulario reutilizable | `apitemplates/domain/entity/Template.java` |
| **Section** | Sección lógica dentro de una plantilla | `apitemplates/domain/entity/Section.java` |

**Características de las entidades**:
- Extienden de `AuditedDomain` para incluir auditoría automática (usuario, fecha de modificación)
- Contienen solo atributos y métodos de dominio, sin dependencias a frameworks
- Utilizan **enums de dominio** para valores constantes

#### b) **Enums de Dominio** (`domain/entity/nodatabase/`)
Valores de enumeración que representan estados y conceptos clave:

| Enum | Propósito | Valores Típicos |
|------|----------|-----------------|
| **BusinessDataStatus** | Estados de una oportunidad | `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `DISMISSED` |
| **TaskStatus** | Estados de una tarea | `NOT_CREATED`, `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `REVIEW`, `CANCELLED` |
| **TaskType** | Tipos de tareas en el flujo | `DRAFT_OPP`, `ENRICH_OPP`, `VALIDATE_OPP`, etc. |
| **TaskAction** | Acciones ejecutadas al completar una tarea | `APPROVED`, `REJECTED`, `RESUBMIT` |

**Ejemplo de Enum**:
```java
@Getter
@AllArgsConstructor
public enum BusinessDataStatus {
    IN_PROGRESS(false),      // Oportunidad en proceso
    COMPLETED(true),         // Finalizada exitosamente
    CANCELLED(false),        // Cancelada
    DISMISSED(true);         // Descartada (estado final)
    
    private final boolean isFinalStatus;
}
```

#### c) **Entidades de Valor (No Persistidas)** (`domain/entity/nodatabase/`)
Clases simples que agrupan información sin persistencia en BD:

- `MinimalBusinessData`: Referencia mínima a BusinessData
- `MinimalTask`: Referencia mínima a Task
- `ExtraBpmFields`: Campos adicionales del motor BPM

---

### 2. **Capa de Aplicación (Application)**

**Ubicación**: `{modulo}/application/`

**Responsabilidad**: Define contratos de servicios (interfaces) que implementan la lógica de negocio. Actúan como **puertos** en la arquitectura hexagonal.

**Estructura**:
```
application/
├── I{Entidad}Service.java        (Interfaces - Puertos de entrada)
├── impl/
│   └── {Entidad}ServiceImpl.java  (Implementaciones de servicios)
```

#### Servicios por Módulo:

**Módulo apibpm**:
| Interfaz | Implementación | Responsabilidad |
|----------|----------------|-----------------|
| `IServiceApiBpm` | `ServiceApiBpmImpl` | Operaciones principales: asignar tareas, crear oportunidades, enviar eventos |
| `IBusinessDataService` | `BusinessDataServiceImpl` | Gestión CRUD de BusinessData, tareas, comentarios |
| `IFieldService` | `FieldServiceImpl` | Gestión de campos personalizados |
| `ICommentService` | `CommentServiceImpl` | Gestión de comentarios |
| `IServiceGetActualUser` | `ServiceGetActualUserImpl` | Obtener usuario autenticado actual |

**Módulo apitableservices**:
| Interfaz | Implementación | Responsabilidad |
|----------|----------------|-----------------|
| `ITableService` | `TableServiceImpl` | Consulta de tablas maestro y datos |
| `ITableColumnService` | `TableColumnServiceImpl` | Gestión de columnas de tablas |
| `ISelectionValueService` | `SelectionValueServiceImpl` | Valores de selección para dropdowns |

**Módulo apitemplates**:
| Interfaz | Implementación | Responsabilidad |
|----------|----------------|-----------------|
| `ISectionService` | `SectionServiceImpl` | Gestión de secciones de plantillas |
| `ISectionValueService` | `SectionValueServiceImpl` | Valores de secciones |
| `ITemplateService` | `TemplateServiceImpl` | Gestión de plantillas |

#### Características de los Servicios:
- **Inyección de dependencias**: Reciben repositorios como dependencias
- **Transacciones**: Anotadas con `@Transactional` para garantizar consistencia
- **Manejo de excepciones**: Lanzan `GenericException` con códigos HTTP
- **Lógica de negocio**: Implementan reglas de negocio no presentes en las entidades

**Ejemplo de Servicio**:
```java
@Service
@RequiredArgsConstructor
@Transactional
public class BusinessDataServiceImpl implements IBusinessDataService {
    
    private final IBusinessDataRepository businessDataRepository;
    private final ITaskRepository taskRepository;
    private final ICommentRepository commentRepository;
    
    @Override
    public BusinessData saveBusinessData(BusinessData businessData) throws GenericException {
        // Lógica de negocio
        return businessDataRepository.saveBusinessData(businessData);
    }
    
    @Override
    public void addTaskComment(Comment comment, String bpmTaskId) throws GenericException {
        Task task = taskRepository.findByBpmTaskId(bpmTaskId);
        task.addComment(comment);
        taskRepository.saveTask(task);
    }
}
```

---

### 3. **Capa de Infraestructura (Infrastructure)**

**Ubicación**: `{modulo}/infrastructure/`

**Responsabilidad**: Implementa los **adaptadores** que conectan la aplicación con sistemas externos (BD, APIs, etc).

**Estructura**:
```
infrastructure/
├── listener/                    (Adaptador REST entrante)
├── repository/                  (Adaptador de persistencia)
│   ├── I{Entidad}Repository.java        (Interfaz - Puerto de salida)
│   ├── impl/                             (Implementaciones de repositorios)
│   └── jpa/                              (Mapeos JPA-Entidades)
├── mapper/                      (Mapeos DTO ↔ Entidades)
└── (listener extra)
```

#### a) **Adaptador REST (Listener)**

**Componente**: `infrastructure/listener/Listener{Modulo}.java`

**Responsabilidad**: Es el **puerto de entrada** (Adapter entrante) que recibe peticiones HTTP REST.

**Flujo**:
```
HTTP Request → Listener (REST Adapter) → Service (Aplicación) → Repository → BD
```

**Implementación**:
- Anotada con `@Service` y `@RequiredArgsConstructor` (inyección de Spring)
- Implementa interfaz generada por NOVA: `IRestListener{Modulo}`
- Mapea DTOs HTTP a entidades de dominio
- Convierte excepciones a respuestas HTTP

**Ejemplo (ListenerApiBpm)**:
```java
@Service
@RequiredArgsConstructor
public class ListenerApiBpm implements IRestListenerApibpm {
    
    private final IServiceApiBpm service;
    private final IBusinessDataService businessDataService;
    private final MapperTaskDto mapperTaskDto;
    
    @Override
    public assignTask(String bpmTaskId) throws GetTaskException404 {
        try {
            service.assignTask(bpmTaskId);
            return Response.ok().build();
        } catch (GenericException e) {
            throw new GetTaskException404(e.getMessage());
        }
    }
}
```

#### b) **Adaptador de Persistencia (Repository)**

**Componentes**:
- `infrastructure/repository/I{Entidad}Repository.java` - Interfaz (Puerto de salida)
- `infrastructure/repository/impl/{Entidad}RepositoryImpl.java` - Implementación
- `infrastructure/repository/jpa/{Entidad}RepositoryJpa.java` - Acceso a BD con Spring Data JPA

**Flujo de Persistencia**:
```
Servicio → I{Entidad}Repository (interfaz)
         ↓
         {Entidad}RepositoryImpl (implementación con mapeo)
         ↓
         {Entidad}Jpa (entidad JPA)
         ↓
         {Entidad}RepositoryJpa (Spring Data JPA)
         ↓
         Base de Datos
```

**Ejemplo (TaskRepository)**:
```
Domain Entity (Task) 
    ↓↑ [TaskMapper]
JPA Entity (TaskJpa)
    ↓↑ [Spring Data]
Database Table (task)
```

**Capas del Repositorio**:

| Capa | Ubicación | Responsabilidad |
|------|-----------|-----------------|
| **Interfaz Repository** | `repository/ITaskRepository.java` | Contrato de operaciones CRUD |
| **Impl Repository** | `repository/impl/TaskRepositoryImpl.java` | Orquesta mappeo y llamadas JPA |
| **Mapper** | `repository/jpa/mapper/TaskMapper.java` | Convierte Task ↔ TaskJpa (MapStruct) |
| **JPA Repository** | `repository/jpa/TaskRepositoryJpa.java` | Spring Data JPA (consultas SQL) |
| **JPA Entity** | `repository/jpa/TaskJpa.java` | Entidad persistible con anotaciones JPA |

**Implementación**:
```java
@Repository
@RequiredArgsConstructor
public class TaskRepositoryImpl implements ITaskRepository {
    
    private final TaskRepositoryJpa taskRepositoryJpa;
    private final TaskMapper taskMapper;  // MapStruct
    
    @Override
    public Task saveTask(Task task) {
        // Dominio → JPA
        TaskJpa taskJpa = taskMapper.toEntity(task);
        
        // Persistir
        TaskJpa savedJpa = taskRepositoryJpa.save(taskJpa);
        
        // JPA → Dominio
        return taskMapper.toModel(savedJpa);
    }
    
    @Override
    public Task findById(Long id) throws EntityNotFoundException {
        TaskJpa taskJpa = taskRepositoryJpa.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("Task not found"));
        return taskMapper.toModel(taskJpa);
    }
}
```

#### c) **Mappers (DTO ↔ Entidades)**

**Ubicación**: 
- REST Mappers: `infrastructure/mapper/Mapper{DtoName}.java`
- JPA Mappers: `infrastructure/repository/jpa/mapper/{EntityName}Mapper.java`

**Tecnología**: MapStruct (mapeo automático por anotaciones)

**Tipos de Mappers**:

**REST Mappers** (Listener):
```
{DtoName}Dto (generado por APIRestGenerator)
    ↑↓ [MapStruct]
Domain Entity
```

Ejemplos:
- `MapperTaskDto`: TaskDto ↔ Task
- `MapperBusinessDataDto`: BusinessDataDto ↔ BusinessData
- `MapperCreateCommentDto`: CreateCommentDto ↔ Comment
- `MapperUpdateTaskDto`: UpdateTaskDto ↔ Task

**Implementación**:
```java
@Mapper(
    componentModel = "spring",
    uses = {
        MapperCommentDto.class,
        MapperFieldDto.class,
        MapperStatusHistoryDto.class,
        DateMapper.class
    })
public interface MapperTaskDto extends GenericDtoMapper<Task, TaskDto> {}
```

**JPA Mappers** (Repository):
```java
@Mapper(componentModel = "spring")
public interface TaskMapper {
    
    @Mapping(target = "id", source = "taskId")
    TaskJpa toEntity(Task domain);
    
    @Mapping(target = "taskId", source = "id")
    Task toModel(TaskJpa entity);
}
```

---

## Módulos Principales

### 1. Módulo **apibpm** (API BPM)

**Propósito**: Gestión del ciclo de vida de procesos de negocio y tareas.

**Entidades Principales**:
- `BusinessData`: Oportunidad de negocio (concepto central)
- `Task`: Tarea del flujo
- `Comment`: Comentarios de auditoría
- `Field`: Datos personalizados
- `StatusHistory`: Historial de cambios

**Servicios Principales**:
- `IServiceApiBpm`: Operaciones BPM (asignar, enviar eventos)
- `IBusinessDataService`: CRUD de oportunidades y tareas
- `IFieldService`: Gestión de campos personalizados
- `ICommentService`: Gestión de comentarios

**Adaptadores Externos**:
- **XBPM**: Motor de procesos externo (via `xbpm/ServiceApi.java`)
- **RDR**: Registry Data Repository (via `rdr/RdrService.java`)
- **Base de Datos**: Persistencia de datos

**Listeners**:
- `ListenerApiBpm`: Endpoints REST principales
- `ListenerApiBpmStatus`: Endpoints de gestión de estado

---

### 2. Módulo **apitableservices** (API Table Services)

**Propósito**: Gestión de tablas maestro de datos.

**Entidades Principales**:
- `Table`: Tabla de datos
- `Column`: Columna de tabla
- `ColumnValue`: Valor de celda
- `SelectionValue`: Valores para dropdowns

**Servicios Principales**:
- `ITableService`: Consulta de tablas y datos
- `ITableColumnService`: Gestión de columnas
- `ISelectionValueService`: Valores de selección

**Características**:
- Soporta paginación
- Integración con RDR para obtener datos externos
- Filtrado de datos

---

### 3. Módulo **apitemplates** (API Templates)

**Propósito**: Gestión de plantillas de formularios reutilizables.

**Entidades Principales**:
- `Template`: Plantilla de formulario
- `Section`: Sección lógica de plantilla
- `SectionValue`: Valores de sección

**Servicios Principales**:
- `ISectionService`: Gestión de secciones
- `ISectionValueService`: Gestión de valores
- `ITemplateService`: Gestión de plantillas

**Características**:
- Reutilización de plantillas
- Organización visual de campos

---

## Flujo de Comunicación

### Flujo 1: Petición HTTP para obtener una Tarea

```
┌─────────────────────────────────────────────────────────────────┐
│ Cliente HTTP                                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ ADAPTER ENTRANTE: ListenerApiBpm (infrastructure/listener)      │
│ - Recibe HTTP GET /tasks/{id}                                   │
│ - Valida headers NOVA (metadatos, usuario, etc)                │
│ - Mapea DTOs HTTP → Entidades Dominio                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ APLICACIÓN: BusinessDataServiceImpl (application/impl)           │
│ - Ejecuta lógica de negocio                                     │
│ - Valida reglas de negocio                                      │
│ - Coordina repositorios                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ ADAPTER SALIDA: TaskRepositoryImpl (infrastructure/repository)   │
│ - Consulta interfaz ITaskRepository                             │
│ - Mapea Entidades Dominio → Entidades JPA                       │
│ - Ejecuta consultas via Spring Data JPA                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ DOMINIO: Entidad Task (domain/entity)                           │
│ - Datos persistidos (sin lógica externa)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Base de Datos                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Flujo 2: Crear Oportunidad de Negocio (Multipasos)

```
HTTP POST /opportunities
    ↓
ListenerApiBpm.createBusinessData()
    ↓ [Mapper: CreateBusinessDataDto → BusinessData]
    ↓
ServiceApiBpmImpl.createOpportunityEvent()
    ├─→ IBusinessDataRepository.saveBusinessData()
    │   ├─→ [Mapper: BusinessData → BusinessDataJpa]
    │   └─→ BD: INSERT
    │
    ├─→ ServiceApi (XBPM).sendEvent()
    │   └─→ Motor BPM Externo (envía evento de inicio)
    │
    └─→ ListenerApiBpm devuelve respuesta
        ↓ [Mapper: BusinessData → BusinessDataDto]
        ↓
HTTP 201 Created + BusinessDataDto
```

### Flujo 3: Actualizar Estado de Tarea

```
HTTP PUT /tasks/{id}/status
    ↓
ListenerApiBpm.setTaskStatus()
    ↓ [Mapper: SetStatusDto → Task]
    ↓
ServiceApiBpmImpl.updateTaskStatus()
    │
    ├─→ Valida transición de estado
    │
    ├─→ ITaskRepository.saveTask(task)
    │   ├─→ [Mapper: Task → TaskJpa]
    │   └─→ BD: UPDATE task SET status = ?
    │
    ├─→ IStatusHistoryRepository.saveStatusHistory()
    │   └─→ BD: INSERT INTO status_history (registra cambio)
    │
    ├─→ ServiceApi (XBPM).updateTaskStatus()
    │   └─→ Motor BPM: notifica cambio de estado
    │
    └─→ Response HTTP 200 OK
```

---

## Patrones de Implementación

### 1. **Inyección de Dependencias**

Todos los servicios usan **constructor injection** con `@RequiredArgsConstructor`:

```java
@Service
@RequiredArgsConstructor
public class BusinessDataServiceImpl implements IBusinessDataService {
    
    private final IBusinessDataRepository businessDataRepository;
    private final ITaskRepository taskRepository;
    private final ICommentRepository commentRepository;
    
    // Las dependencias se inyectan en el constructor automáticamente
}
```

**Ventajas**:
- Inmutabilidad de dependencias
- Testeo más sencillo (mock de dependencias)
- Claridad de dependencias

### 2. **Transacciones**

Las operaciones que modifican datos son **transaccionales**:

```java
@Transactional
public void updateTask(Task task) throws GenericException {
    taskRepository.saveTask(task);
    statusHistoryRepository.saveStatusHistory(history);
    // Si algo falla, ambos cambios se revierten
}
```

**Comportamiento**:
- Si todo tiene éxito → COMMIT
- Si hay excepción → ROLLBACK automático

### 3. **Mapeo de DTOs**

Separación entre **DTOs de API** (generados por APIRestGenerator) y **entidades de dominio**:

```
HTTP Layer (DTOs)  ←→ [Mapper] ←→ Domain Layer (Entities)
TaskDto                           Task
CreateTaskDto                     Task
UpdateTaskDto                     Task
```

**Ventajas**:
- DTOs pueden cambiar sin afectar dominio
- Validación separada
- Seguridad (no expone todas las entidades)

### 4. **Manejo de Excepciones con Códigos HTTP**

Las excepciones llevan códigos HTTP implícitos:

```java
public interface ITaskRepository {
    Task findById(Long id) throws EntityNotFoundException;  // HTTP 404
}
```

El Listener mapea a respuestas HTTP:

```java
try {
    Task task = businessDataService.findById(id);
} catch (EntityNotFoundException e) {
    throw new GetTaskException404(e.getMessage());  // HTTP 404
} catch (GenericException e) {
    // Mapear según e.getCode() a excepción HTTP
}
```

### 5. **Modelo de Auditoría**

Las entidades extienden `AuditedDomain` para auditoría automática:

```java
public class AuditedDomain {
    
    @CreationTimestamp
    private OffsetDateTime createdDate;
    
    private String user;  // Del contexto de seguridad Nova
    
    // Se rellenan automáticamente en constructor
    public AuditedDomain() {
        this.user = NovaSecurityContext.getAuthentication().getUser();
        this.createdDate = OffsetDateTime.now();
    }
}
```

Todas las entidades (Task, BusinessData, Comment, Field, etc.) heredan esto.

---

## Adaptadores y Puertos

### Puertos de Entrada (Inbound Adapters)

| Tipo | Ubicación | Función |
|------|-----------|---------|
| **REST Listener** | `infrastructure/listener/Listener{Modulo}.java` | Recibe peticiones HTTP |
| | Implementa `IRestListener{Modulo}` generada | Genera respuestas HTTP |

**Ejemplo**:
```java
@Service
public class ListenerApiBpm implements IRestListenerApibpm {
    
    @Override
    public assignTask(String bpmTaskId) {
        // Recibe petición HTTP
        service.assignTask(bpmTaskId);
        // Devuelve respuesta
    }
}
```

### Puertos de Salida (Outbound Adapters)

| Tipo | Ubicación | Propósito |
|------|-----------|----------|
| **Repository (BD)** | `infrastructure/repository/impl/{Entidad}RepositoryImpl.java` | Persistencia de datos |
| **XBPM Client** | `xbpm/ServiceApi.java` | Comunicación con motor BPM externo |
| **RDR Client** | `rdr/RdrService.java` | Consulta Registry Data Repository |
| **Mappers** | `infrastructure/mapper/` y `infrastructure/repository/jpa/mapper/` | Transformación de datos |

**Patrón Común**:
```
Aplicación → Interfaz (Puerto) → Implementación (Adaptador) → Sistema Externo
           ITaskRepository     TaskRepositoryImpl      TaskRepositoryJpa → BD
                              
           ServiceApiBpm       xbpm/ServiceApi        → XBPM Externo

           IFieldService      FieldServiceImpl         → Lógica + Repositorio → BD
```

---

## Gestión de Errores

### Jerarquía de Excepciones

```
java.lang.Exception
    │
    └─ GenericException (base con HttpStatus)
        │
        ├─ EntityNotFoundException (HTTP 404)
        ├─ AuthenticationException (HTTP 401)
        ├─ EntityAlreadyExistsException
        ├─ XbpmException (errores del motor BPM)
        └─ RdrException (errores del servicio RDR)
```

### Propagación de Errores

**Desde la BD**:
```java
// Repository intenta recuperar entidad
Task task = taskRepositoryJpa.findById(id)
    .orElseThrow(() -> 
        new EntityNotFoundException(HttpStatus.NOT_FOUND, "Task not found")
    );
```

**En el Listener**:
```java
try {
    Task task = businessDataService.findById(taskId);
    return mapperTaskDto.map(task);
} catch (EntityNotFoundException e) {
    throw new GetTaskException404(e.getMessage());  // HTTP 404
} catch (GenericException e) {
    throw mapToRestException(e);  // Mapea según código HTTP
}
```

### Respuesta de Error Estandarizada

```java
// GenericApiErrorBuilder construye respuesta error estándar
{
    "code": "NOT_FOUND",
    "message": "Task not found",
    "httpStatus": 404,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Resumen Conceptual

### Capas y Responsabilidades

| Capa | Ubicación | Responsabilidad | Acceso |
|------|-----------|-----------------|--------|
| **Adaptadores Entrantes** | `infrastructure/listener/` | Reciben HTTP, mapean DTOs | Público (HTTP) |
| **Servicios (Application)** | `application/impl/` | Lógica de negocio | Solo desde Listener/Tests |
| **Entidades (Domain)** | `domain/entity/` | Datos + lógica de dominio puro | Desde Application/Infrastructure |
| **Adaptadores Salida** | `infrastructure/repository/` | Persistencia, comunicación externa | Desde Application |
| **Mappers** | `infrastructure/mapper/`, `repository/jpa/mapper/` | DTO ↔ Entidad | Desde Listener/Repository |

### Aislamiento de Responsabilidades

```
┌──────────────────────────────────────────────────────────┐
│ CAPA DE PRESENTACIÓN                                     │
│ HTTP REST Listener (Adaptador Entrante)                  │
│ └─ Mapea DTOs → Entidades                               │
│ └─ Maneja excepciones → HTTP                            │
└──────────┬───────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│ CAPA DE APLICACIÓN                                       │
│ Servicios (@Service)                                    │
│ └─ Orquesta repositorios                               │
│ └─ Implementa lógica de negocio                        │
│ └─ Coordina transacciones                              │
└──────────┬───────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│ CAPA DE DOMINIO                                          │
│ Entidades de Negocio (Entities)                         │
│ └─ Task, BusinessData, Comment, Field, etc.            │
│ └─ Lógica pura de dominio                              │
│ └─ Sin dependencias a frameworks                        │
└──────────┬───────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│ CAPA DE INFRAESTRUCTURA                                  │
│ Repositorios (Adaptadores de Salida)                    │
│ └─ Mapean Entidades → JPA                              │
│ └─ Ejecutan consultas a BD                             │
│                                                         │
│ Clientes Externos                                       │
│ └─ XBPM (Motor BPM)                                    │
│ └─ RDR (Registry Data Repository)                      │
│ └─ BD (Persistencia)                                   │
└──────────────────────────────────────────────────────────┘
```

### Flujo de Datos Típico

```
Cliente
  ↓
HTTP Request (DTO)
  ↓
Listener.method(Dto) 
  ├─ Mapea: Dto → Entity (dominio)
  ├─ Llama Service.operation(Entity)
  │   ├─ Lógica de negocio
  │   ├─ Llama Repository.method(Entity)
  │   │   ├─ Mapea: Entity → JpaEntity
  │   │   ├─ Ejecuta consulta SQL
  │   │   ├─ Mapea: JpaEntity → Entity
  │   │   └─ Retorna Entity
  │   └─ Retorna Entity
  ├─ Mapea: Entity → Dto
  └─ HTTP Response (Dto)
```

---

## Notas Importantes

1. **Sin Generación de Código Manual**: Los listeners y algunos servicios están generados por **KLTT-APIRestGenerator** (visible en encabezado de archivos). Estos no deben editarse manualmente.

2. **Configuración NOVA**: El proyecto utiliza frameworks NOVA para:
   - Generación de clientes REST
   - Manejo de metadatos
   - Autenticación y seguridad

3. **Separated DTOs**: Los DTOs se generan separadamente en paquete `com.bbva.wgtb.apirestgen.*` y se utilizan para comunicación HTTP, nunca entran en la lógica de dominio.

4. **Patrones de Cache**: La aplicación tiene `@EnableCaching` en `Application.java`, pero el mapeo específico está en configuración no mostrada aquí.

5. **Auditoría Integrada**: Todos los cambios quedan registrados automáticamente (usuario, fecha) mediante `AuditedDomain` y `StatusHistory`.

