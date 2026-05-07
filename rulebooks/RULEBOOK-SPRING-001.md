---
id: DOC-HACK-001
type: spec
layer: documentation
domain: AI Code Review
subdomain: Spring Boot Rules
status: draft
confidence: low
version: "0.2.0"
created: 2026-05-04
updated: 2026-05-04
owner: victor-carmona
reviewers:
  - pablo-martinez
  - lourdes-pozo
dependencies:
  - id: ARCH-HACK-001
    relation: constrained-by
  - id: FEAT-HACK-001
    relation: constrained-by
  - id: FEAT-HACK-002
    relation: constrained-by
tags:
  - spring-boot
  - java
  - java-11
  - quality-gate
  - rulebook
  - hexagonal
  - wgtb
  - openapi
  - mapstruct
  - lombok
---

# RULEBOOK-SPRING-001 — Spring Boot / Java 11 (WGTB Backend)

## Intent

Define las reglas de calidad, arquitectura y estilo que el agente aplica al analizar diffs de Pull Requests del proyecto `WGTB-Backend-develop/wgtbBackend`. Las reglas están calibradas a los patrones reales del codebase: APIs en OpenAPI YML, listeners autogenerados, MapStruct, Lombok y arquitectura hexagonal.

## Definition

**Proyecto objetivo:** `com.bbva.wgtb:wgtbbackend` · Java 11 · Spring Boot (gestionado por NOVA) · JPA con Oracle · MapStruct 1.5.5 · Lombok 1.18.22 · Arquitectura hexagonal (ports & adapters).

**Stack de generación de código:** Los contratos API se definen en `src/main/resources/apis/*.yml` (Swagger 2.0). El generador KLTT-APIRestGenerator produce las interfaces `IRestListenerXxx` y las clases de excepción por endpoint. Los desarrolladores implementan esas interfaces en las clases `Listener*` de la capa `infrastructure/listener/`.

**Regla de Oro del Legacy (invariante):** el agente distingue entre código nuevo y código legacy modificado. Los fallos 🔴 Crítico de estilo/calidad bloquean en código nuevo pero se degradan a 🟡 Warning en legacy. Los fallos críticos de seguridad/arquitectura bloquean en ambos casos.

---

## 1. Arquitectura y Capas del Proyecto

### [RULE-SPR-001] Prohibición de acceso directo Listener → Repository

**Severidad:** 🔴 Crítico (seguridad/arquitectura)
**Aplica a:** Clases `Listener*` — código nuevo Y legacy si el salto de capa es introducido por el cambio
**Quality Gate:** 🔴 Rojo — bloquea merge en ambos contextos
**Descripción:** Las clases `Listener*` de la capa `infrastructure/listener/` solo pueden inyectar y llamar a interfaces de servicio (`IXxxService`). Nunca deben inyectar repositorios (`IXxxRepository` ni `XxxRepositoryJpa`) directamente. La lógica de acceso a datos es responsabilidad exclusiva de la capa `infrastructure/repository/`. Es la violación arquitectónica más grave del proyecto: la capa de entrada HTTP saltándose la capa de aplicación para acceder directamente a la persistencia.

**Ejemplo incorrecto:**
```java
@Slf4j
@Service
@RequiredArgsConstructor
public class ListenerApiBpm implements IRestListenerApibpm {

    private final IBusinessDataRepository businessDataRepository; // VIOLACIÓN: repo en Listener

    @Override
    public void assignTask(NovaMetadata novaMetadata, String taskId)
            throws Errors, AssignTaskException500, AssignTaskException404, AssignTaskException400 {
        businessDataRepository.findById(taskId); // acceso directo a datos desde el listener
    }
}
```

**Ejemplo correcto:**
```java
@Slf4j
@Service
@RequiredArgsConstructor
public class ListenerApiBpm implements IRestListenerApibpm {

    private final IServiceApiBpm service; // solo servicios de dominio/aplicación

    @Override
    public void assignTask(NovaMetadata novaMetadata, String taskId)
            throws Errors, AssignTaskException500, AssignTaskException404, AssignTaskException400 {
        try {
            this.service.assignTask(taskId);
        } catch (GenericException ex) {
            // ver RULE-SPR-008 para el patrón completo de manejo de errores
        }
    }
}
```

**Auto-corrección:**
```java
// 1. Eliminar la inyección del Repository del Listener
// 2. Identificar o crear el IXxxService correspondiente
// 3. Inyectar el Service mediante @RequiredArgsConstructor
// 4. Mover la lógica de acceso a datos al ServiceImpl correspondiente
```

---

### [RULE-SPR-002] Detección de God Objects en la capa de servicio

**Severidad:** 🟡 Warning (deuda técnica)
**Aplica a:** Clases `*ServiceImpl` nuevas o en las que se añadan responsabilidades adicionales
**Quality Gate:** 🟡 Amarillo — permite avance con notificación educativa
**Descripción:** Una clase `*ServiceImpl` con más de 10 métodos públicos de dominios funcionales distintos o más de 300 líneas se considera un God Object y viola el Principio de Responsabilidad Única. El proyecto ya separa por módulo (`apibpm`, `apitableservices`, `apitemplates`); dentro de cada módulo, los servicios deben seguir la misma separación por dominio funcional.

**Ejemplo incorrecto:**
```java
@Service
@RequiredArgsConstructor
public class ApiBpmServiceImpl implements IApiBpmService {
    // Gestiona BusinessData, Tasks, Comments, Fields, Users, Events... en una sola clase
    public BusinessData createOpportunity(...) { ... }
    public void assignTask(...) { ... }
    public Comment createComment(...) { ... }
    public void sendSignalEvent(...) { ... }
    public User getActualUser(...) { ... }
    // 10+ métodos de 5 dominios funcionales distintos
}
```

**Ejemplo correcto:**
```java
// Siguiendo el patrón del propio proyecto: un service por dominio funcional
@Service public class BusinessDataServiceImpl implements IBusinessDataService { ... } // oportunidades
@Service public class TaskServiceImpl implements ITaskService { ... }                 // tareas
@Service public class CommentServiceImpl implements ICommentService { ... }           // comentarios
@Service public class FieldServiceImpl implements IFieldService { ... }              // campos
```

**Auto-corrección:**
```java
// Identificar los grupos funcionales dentro del service (CRUD de una entidad = un service)
// Extraer cada grupo a su propio IXxxService + XxxServiceImpl
// Inyectar los services especializados donde se necesiten, respetando el grafo de dependencias
```

---

### [RULE-SPR-003] Anotaciones de capa correctas en el proyecto WGTB

**Severidad:** 🔴 Crítico (estilo/calidad)
**Aplica a:** Clases nuevas — Warning educativo en legacy modificado
**Quality Gate:** 🔴 Rojo en código nuevo · 🟡 Amarillo en legacy modificado
**Descripción:** En el proyecto WGTB no existe `@RestController` escrito a mano: los controladores HTTP son generados por KLTT-APIRestGenerator. Las únicas anotaciones válidas para componentes de negocio son: `@Service` para Listeners, Services e implementaciones de repositorio; `@Repository` no se usa explícitamente en las interfaces JPA (Spring Data lo gestiona). Usar `@Component` o `@RestController` fuera del contexto generado es una violación.

**Mapeo de anotaciones en el proyecto:**

| Clase | Anotación correcta | Ejemplo |
|-------|--------------------|---------|
| Listener (entrada HTTP) | `@Service` + `@RequiredArgsConstructor` + `@Slf4j` | `ListenerApiBpm` |
| Service impl (aplicación/dominio) | `@Service` + `@RequiredArgsConstructor` | `BusinessDataServiceImpl` |
| Repository impl (persistencia) | `@Repository` + `@RequiredArgsConstructor` | `BusinessDataRepositoryImpl` |
| JPA repository interface | Sin anotación (Spring Data la gestiona) | `BusinessDataRepositoryJpa extends JpaRepository` |
| Mapper MapStruct | `@Mapper(componentModel = "spring")` | `MapperBusinessDataDto` |
| Utilidades transversales | `@Component` o `@Configuration` | `CacheConfig`, `FilterRegistration` |

**Ejemplo incorrecto:**
```java
@RestController               // VIOLACIÓN: los listeners no son RestControllers manuales
@RequestMapping("/api/bpm")
public class ListenerApiBpm implements IRestListenerApibpm { ... }

@Component                    // VIOLACIÓN: debe ser @Service
public class BusinessDataServiceImpl implements IBusinessDataService { ... }
```

**Ejemplo correcto:**
```java
@Slf4j
@Service
@RequiredArgsConstructor
public class ListenerApiBpm implements IRestListenerApibpm { ... }

@Service
@RequiredArgsConstructor
public class BusinessDataServiceImpl implements IBusinessDataService { ... }

@Repository
@RequiredArgsConstructor
public class BusinessDataRepositoryImpl implements IBusinessDataRepository { ... }
```

**Auto-corrección:**
```java
// Sustituir @RestController en Listeners por @Service + @Slf4j + @RequiredArgsConstructor
// Sustituir @Component en Services por @Service + @RequiredArgsConstructor
// Añadir @Repository a las implementaciones de repositorio (no a las interfaces JPA)
```

---

### [RULE-SPR-004] Inyección de dependencias por constructor con @RequiredArgsConstructor

**Severidad:** 🟡 Warning (deuda técnica)
**Aplica a:** Clases nuevas con inyección de dependencias — educativo en legacy modificado
**Quality Gate:** 🟡 Amarillo en ambos casos
**Descripción:** La inyección de dependencias debe realizarse mediante constructor. En este proyecto el patrón estándar es `@RequiredArgsConstructor` de Lombok sobre campos `final`, que genera el constructor automáticamente. Usar `@Autowired` en campos es incompatible con inmutabilidad y dificulta los tests unitarios con Mockito. No se debe añadir constructor explícito salvo necesidad de lógica de inicialización.

**Ejemplo incorrecto:**
```java
@Service
public class BusinessDataServiceImpl implements IBusinessDataService {

    @Autowired
    private IBusinessDataRepository businessDataRepository; // inyección por campo — VIOLACIÓN

    @Autowired
    private ITaskRepository taskRepository;
}
```

**Ejemplo correcto:**
```java
@Service
@RequiredArgsConstructor        // Lombok genera el constructor para todos los campos final
public class BusinessDataServiceImpl implements IBusinessDataService {

    private final IBusinessDataRepository businessDataRepository;
    private final ITaskRepository taskRepository;
    private final ICommentRepository commentRepository;
    private final ObjectUpdater objectUpdater;
}
```

**Auto-corrección:**
```java
// 1. Eliminar @Autowired de todos los campos
// 2. Añadir "final" a cada campo inyectado
// 3. Añadir @RequiredArgsConstructor a la clase
// 4. Eliminar constructores explícitos de inyección si existen (los reemplaza Lombok)
```

---

### [RULE-SPR-005] Patrón de tres capas en la infraestructura de repositorios

**Severidad:** 🔴 Crítico (seguridad/arquitectura)
**Aplica a:** Cualquier nuevo acceso a datos — bloquea en código nuevo y en legacy si introduce una capa nueva
**Quality Gate:** 🔴 Rojo — bloquea merge si se rompe la estructura de tres capas
**Descripción:** Todo acceso a base de datos debe seguir el patrón de tres capas del proyecto: (1) interfaz de dominio `IXxxRepository` en `infrastructure/repository/`; (2) implementación puente `XxxRepositoryImpl` (`@Repository`) que aplica caché y orquesta la JPA; (3) interfaz Spring Data `XxxRepositoryJpa` que extiende `JpaRepository`. No se permite el acceso directo a `XxxRepositoryJpa` desde servicios o listeners.

**Estructura de tres capas:**
```
infrastructure/repository/
├── IBusinessDataRepository.java         ← (1) interfaz de dominio — contrato sin JPA
├── impl/
│   └── BusinessDataRepositoryImpl.java  ← (2) @Repository — caché, mapeo JPA↔dominio
└── jpa/
    └── BusinessDataRepositoryJpa.java   ← (3) extends JpaRepository<BusinessDataJpa, String>
```

**Ejemplo incorrecto:**
```java
@Service
@RequiredArgsConstructor
public class BusinessDataServiceImpl implements IBusinessDataService {

    private final BusinessDataRepositoryJpa businessDataRepositoryJpa; // VIOLACIÓN: JPA directo en Service

    public BusinessData findById(String id) throws EntityNotFoundException {
        return businessDataRepositoryJpa.findById(id)                   // acceso JPA directo
                .map(businessDataMapper::toModel)
                .orElseThrow(() -> new EntityNotFoundException(id));
    }
}
```

**Ejemplo correcto:**
```java
@Service
@RequiredArgsConstructor
public class BusinessDataServiceImpl implements IBusinessDataService {

    private final IBusinessDataRepository businessDataRepository; // interfaz de dominio

    public BusinessData findById(String id) throws EntityNotFoundException {
        return businessDataRepository.findById(id); // la impl gestiona JPA, caché y mapeo
    }
}
```

**Auto-corrección:**
```java
// Si el Service inyecta XxxRepositoryJpa:
//   1. Crear IXxxRepository con los métodos necesarios
//   2. Crear XxxRepositoryImpl que implemente la interfaz y delegue en XxxRepositoryJpa
//   3. Sustituir la dependencia en el Service por IXxxRepository
// Si el Listener inyecta XxxRepositoryJpa:
//   → Aplicar RULE-SPR-001 primero (el Listener no debe acceder a datos)
```

---

## 2. Convenciones de Naming del Proyecto

### [RULE-SPR-006] Convenciones de naming generales

**Severidad:** 🔴 Crítico (estilo/calidad) para clases · 🟡 Warning para métodos, variables y constantes
**Aplica a:** Código nuevo — Warning educativo en legacy modificado
**Quality Gate:** 🔴 Rojo (nombres de clase en código nuevo) · 🟡 Amarillo (resto de casos)
**Descripción:** PascalCase para clases e interfaces, camelCase para métodos y variables, UPPER_SNAKE_CASE para constantes `static final`. Los nombres genéricos sin contexto funcional (`process`, `handle`, `execute`, `data`, `info`, `obj`, `temp`) están prohibidos en código nuevo. Los nombres de métodos deben describir su acción: verbo + sustantivo (`findById`, `calcularDescuento`, `enviarNotificacion`).

**Ejemplo incorrecto:**
```java
public class businessDataService {               // VIOLACIÓN: debe ser PascalCase

    private static final int maxpedidos = 100;   // VIOLACIÓN: debe ser MAX_PEDIDOS

    public BusinessData Execute(String ID) {     // VIOLACIÓN: camelCase + nombre genérico
        String Info = "BUS";                     // VIOLACIÓN: nombre genérico
        return process(ID);
    }
}
```

**Ejemplo correcto:**
```java
public class BusinessDataServiceImpl {           // PascalCase

    private static final int MAX_BUSINESS_DATA = 100; // UPPER_SNAKE_CASE

    public BusinessData findByBusinessId(String businessId) { // camelCase + descriptivo
        final String prefix = "BUS";
        return buscarPorId(businessId);
    }
}
```

**Auto-corrección:**
```java
// Clases/Interfaces:  PascalCase        → BusinessDataServiceImpl, IBusinessDataRepository
// Métodos:            camelCase verbo   → findById, updateTask, setOpportunityStatus
// Variables:          camelCase         → businessDataStatus, fieldsToDelete
// Constantes:         UPPER_SNAKE_CASE  → MAX_REINTENTOS, TIMEOUT_MS, SEARCH_ALL_CACHE
// Nombres prohibidos: process, handle, execute, data, info, obj, temp, result (sin contexto)
```

---

### [RULE-SPR-007] Naming específico del proyecto WGTB

**Severidad:** 🔴 Crítico (estilo/calidad)
**Aplica a:** Clases nuevas — Warning en legacy modificado donde se añadan clases del mismo tipo
**Quality Gate:** 🔴 Rojo en código nuevo · 🟡 Amarillo en legacy modificado
**Descripción:** El proyecto WGTB impone sufijos y prefijos estrictos por tipo de artefacto. Cualquier clase nueva que no respete estas convenciones rompe la coherencia del codebase y dificulta la navegación. Estas convenciones son distintas a las convenciones genéricas de Java: son parte del contrato arquitectónico del equipo.

**Tabla de convenciones del proyecto:**

| Tipo de artefacto | Patrón | Ejemplo |
|-------------------|--------|---------|
| Interfaz de cualquier tipo | Prefijo `I` + PascalCase | `IBusinessDataService`, `IBusinessDataRepository` |
| Service implementation | PascalCase + `ServiceImpl` | `BusinessDataServiceImpl` |
| Repository implementation | PascalCase + `RepositoryImpl` | `BusinessDataRepositoryImpl` |
| JPA entity | PascalCase + `Jpa` | `BusinessDataJpa`, `TaskJpa` |
| Spring Data JPA interface | PascalCase + `RepositoryJpa` | `BusinessDataRepositoryJpa` |
| MapStruct mapper (DTO↔modelo) | `Mapper` + NombreDTO | `MapperBusinessDataDto`, `MapperTaskDto` |
| MapStruct mapper (JPA↔modelo) | PascalCase + `Mapper` | `BusinessDataMapper`, `TaskMapper` |
| Listener (entrada HTTP) | `Listener` + NombreApi | `ListenerApiBpm`, `ListenerApiTable` |
| Excepción de dominio | PascalCase + `Exception` | `EntityNotFoundException`, `XbpmException` |
| Tests | NombreClase + `Test` | `BusinessDataServiceImplTest` |

**Ejemplo incorrecto:**
```java
public class BizDataSvc implements IBizDataSvc { ... }    // VIOLACIÓN: sin Impl, abreviatura
public class DataRepo implements IDataRepo { ... }        // VIOLACIÓN: sin RepositoryImpl
public class BpmEntity { ... }                            // VIOLACIÓN: JPA sin sufijo Jpa
public interface MappearBusinessData { ... }              // VIOLACIÓN: Mapper debe ser prefijo
public class BpmController { ... }                        // VIOLACIÓN: Listener sin prefijo correcto
```

**Ejemplo correcto:**
```java
public class BusinessDataServiceImpl implements IBusinessDataService { ... }
public class BusinessDataRepositoryImpl implements IBusinessDataRepository { ... }
public class BusinessDataJpa { ... }
public interface MapperBusinessDataDto extends GenericDtoMapper<BusinessData, BusinessDataDto> { ... }
public class ListenerApiBpm implements IRestListenerApibpm { ... }
```

**Auto-corrección:**
```java
// Renombrar la clase y actualizar todas las referencias:
// - Interfaces: añadir prefijo I si no lo tiene
// - ServiceImpl/RepositoryImpl: comprobar que tienen el sufijo correcto
// - JPA: añadir sufijo Jpa si es una entidad de base de datos
// - Mappers: verificar que siguen el patrón Mapper* o *Mapper según el tipo
// Actualizar el import en todos los archivos que referencian la clase renombrada
```

---

## 3. Patrones de Implementación

### [RULE-SPR-008] Manejo de excepciones en Listeners

**Severidad:** 🔴 Crítico (estilo/calidad)
**Aplica a:** Métodos nuevos en clases `Listener*` — Warning en métodos legacy modificados
**Quality Gate:** 🔴 Rojo en código nuevo · 🟡 Amarillo en legacy modificado
**Descripción:** Todo método de un Listener que llame a un service debe envolver la llamada en `try-catch` capturando `GenericException` y mapeando el `HttpStatus` a la excepción de API generada correspondiente (`XxxExceptionNNN`). La construcción de errores se realiza siempre mediante `GenericApiErrorBuilder`. No se permite lanzar directamente `RuntimeException` ni retornar `null` ante un error.

**Ejemplo incorrecto:**
```java
@Override
public void assignTask(NovaMetadata novaMetadata, String taskId)
        throws Errors, AssignTaskException500, AssignTaskException404, AssignTaskException400 {

    this.service.assignTask(taskId); // VIOLACIÓN: sin try-catch, GenericException no capturada
}
```

```java
@Override
public void assignTask(NovaMetadata novaMetadata, String taskId)
        throws Errors, AssignTaskException500, AssignTaskException404, AssignTaskException400 {
    try {
        this.service.assignTask(taskId);
    } catch (Exception ex) {
        throw new AssignTaskException500(null); // VIOLACIÓN: captura genérica + builder omitido
    }
}
```

**Ejemplo correcto:**
```java
@Override
public void assignTask(NovaMetadata novaMetadata, String taskId)
        throws Errors, AssignTaskException500, AssignTaskException404, AssignTaskException400 {
    try {
        this.service.assignTask(taskId);
    } catch (GenericException ex) {
        GenericApiErrorBuilder<APIError> apiErrorBuilder = GenericApiErrorBuilder.of(APIError.class);
        switch (ex.getCode()) {
            case NOT_FOUND:
                throw new AssignTaskException404(apiErrorBuilder.getFromGenericException(ex));
            case BAD_REQUEST:
                throw new AssignTaskException400(apiErrorBuilder.getFromGenericException(ex));
            default:
                log.error("Unexpected error assigning task: ", ex);
                throw new AssignTaskException500(apiErrorBuilder.getUnexpected());
        }
    } catch (Exception ex) {
        log.error("Unexpected error assigning task: ", ex);
        throw new AssignTaskException500(GenericApiErrorBuilder.of(APIError.class).getUnexpected());
    }
}
```

**Auto-corrección:**
```java
// Estructura obligatoria en cada método de Listener:
// try {
//     this.service.metodo(parametros);
// } catch (GenericException ex) {
//     GenericApiErrorBuilder<APIError> apiErrorBuilder = GenericApiErrorBuilder.of(APIError.class);
//     switch (ex.getCode()) {
//         case NOT_FOUND:    throw new XxxException404(apiErrorBuilder.getFromGenericException(ex));
//         case BAD_REQUEST:  throw new XxxException400(apiErrorBuilder.getFromGenericException(ex));
//         default:           log.error("..."); throw new XxxException500(apiErrorBuilder.getUnexpected());
//     }
// } catch (Exception ex) {
//     log.error("..."); throw new XxxException500(GenericApiErrorBuilder.of(APIError.class).getUnexpected());
// }
```

---

### [RULE-SPR-009] Optional vs excepción de dominio para ausencia de entidad

**Severidad:** 🟡 Warning (deuda técnica)
**Aplica a:** Métodos de servicio y repositorio nuevos que busquen una entidad por ID o criterio único
**Quality Gate:** 🟡 Amarillo — permite avance con sugerencia de consistencia
**Descripción:** El proyecto distingue dos semánticas de "ausencia": (1) si la ausencia es una condición de error esperada (se buscó algo que debe existir), el método lanza `EntityNotFoundException` con el identificador — este es el patrón predominante en los repositorios; (2) si la ausencia es un resultado válido del negocio, el método retorna `Optional<T>`. Está prohibido retornar `null` en cualquier caso.

**Regla de decisión:**

| Semántica | Patrón | Ejemplo del proyecto |
|-----------|--------|---------------------|
| "Debe existir, si no es un error" | lanzar `EntityNotFoundException` | `findById(String id) throws EntityNotFoundException` |
| "Puede o no existir (resultado válido)" | retornar `Optional<T>` | `findByFieldCodeAndBusinessData(...) returns Optional<Field>` |
| "Nunca retornar" | — prohibido — | `return null` |

**Ejemplo incorrecto:**
```java
// Retornar null — siempre prohibido
public BusinessData findById(String id) {
    return businessDataRepositoryJpa.findById(id).orElse(null); // VIOLACIÓN
}

// Retornar Optional cuando la semántica es "debe existir"
public Optional<BusinessData> findById(String id) { // VIOLACIÓN: confunde la semántica de negocio
    return businessDataRepositoryJpa.findById(id).map(businessDataMapper::toModel);
}
```

**Ejemplo correcto:**
```java
// Patrón 1: la entidad debe existir — lanzar excepción si no
public BusinessData findById(String id) throws EntityNotFoundException {
    return businessDataRepositoryJpa
            .findById(id)
            .map(businessDataMapper::toModel)
            .orElseThrow(() -> new EntityNotFoundException(id));
}

// Patrón 2: ausencia es resultado válido — retornar Optional
public Optional<Field> findByFieldCodeAndBusinessData(String fieldCode, String businessId)
        throws GenericException {
    return fieldRepositoryJpa.findByFieldCodeAndBusinessId(fieldCode, businessId)
            .map(fieldMapper::toModel);
}
```

**Auto-corrección:**
```java
// Decidir la semántica antes de implementar:
// ¿El caller espera que siempre exista? → throws EntityNotFoundException, sin Optional
// ¿El caller puede recibir "no encontrado" como respuesta válida? → Optional<T>, sin null
// En ningún caso: return null
```

---

### [RULE-SPR-010] Patrón MapStruct con GenericDtoMapper

**Severidad:** 🟡 Warning (deuda técnica)
**Aplica a:** Mappers nuevos entre capas (DTO↔modelo, JPA↔modelo) — educativo en mappers legacy modificados
**Quality Gate:** 🟡 Amarillo en ambos casos
**Descripción:** Todos los mappers entre capas deben implementarse con MapStruct, extendiendo la interfaz `GenericDtoMapper<Modelo, DTO>` o `GenericEntityMapper<Modelo, JPA>` según corresponda. La conversión manual entre objetos (bucles `for`, setters explícitos campo a campo en la capa de negocio) está prohibida cuando existe un mapper equivalente. Los mappers se declaran como interfaces con `@Mapper(componentModel = "spring")` y se inyectan normalmente por Spring.

**Ejemplo incorrecto:**
```java
// Conversión manual en el Service — VIOLACIÓN
public BusinessDataDto toDto(BusinessData model) {
    BusinessDataDto dto = new BusinessDataDto();
    dto.setBusinessId(model.getBusinessId());
    dto.setStatus(model.getStatus().name());
    dto.setStartDate(model.getStartDate());
    // ... 10 campos más mapeados manualmente
    return dto;
}
```

**Ejemplo correcto:**
```java
// Interfaz del mapper — solo declaración, MapStruct genera la implementación
@Mapper(
    componentModel = "spring",
    uses = {
        MapperTaskDto.class,
        MapperCommentDto.class,
        MapperFieldDto.class,
        DateMapper.class
    })
public interface MapperBusinessDataDto
        extends GenericDtoMapper<BusinessData, BusinessDataDto> {}

// Uso en el Listener (inyectado por Spring)
@Slf4j
@Service
@RequiredArgsConstructor
public class ListenerApiBpm implements IRestListenerApibpm {

    private final MapperBusinessDataDto mapperBusinessDataDto;

    @Override
    public BusinessDataDto getOpportunity(...) throws ... {
        BusinessData model = service.findById(id);
        return mapperBusinessDataDto.toDto(model);
    }
}
```

**Auto-corrección:**
```java
// 1. Crear la interfaz del mapper en infrastructure/mapper/ con @Mapper(componentModel = "spring")
// 2. Extender GenericDtoMapper<Modelo, DTO> o GenericEntityMapper<Modelo, Jpa>
// 3. Si hay conversiones especiales (fechas, enums), añadirlas como @Mapping o usar DateMapper
// 4. Eliminar el código de conversión manual del Service/Repository
// 5. Inyectar el mapper en la clase que lo necesita mediante @RequiredArgsConstructor
```

---

## 4. Calidad y Complejidad

### [RULE-SPR-011] Complejidad Ciclomática — máximo 10

**Severidad:** 🔴 Crítico (estilo/calidad)
**Aplica a:** Métodos nuevos — Warning educativo en métodos legacy modificados
**Quality Gate:** 🔴 Rojo en métodos nuevos con CC > 10 · 🟡 Amarillo en legacy modificado con CC > 10
**Descripción:** Ningún método debe superar complejidad ciclomática (CC) de 10. La CC se incrementa por cada punto de decisión: `if`, `else if`, `for`, `while`, `switch case`, `catch`, operadores `&&`/`||`, operador ternario. Cuando un método supera el límite, debe refactorizarse extrayendo ramas lógicas a métodos privados con nombre descriptivo del subdominio funcional que representan.

**Ejemplo incorrecto (CC ≈ 12):**
```java
@Override
public void setOpportunityStatus(String opportunityId, String status) throws GenericException {
    if (opportunityId == null) throw new GenericException(HttpStatus.BAD_REQUEST, "Id requerido"); // +1
    BusinessData bd = businessDataRepository.findById(opportunityId);
    if (bd == null) throw new EntityNotFoundException(opportunityId);                              // +1
    BusinessDataStatus newStatus;
    try {
        newStatus = BusinessDataStatus.valueOf(status);                                            // +1 (try)
    } catch (IllegalArgumentException e) {
        throw new GenericException(HttpStatus.BAD_REQUEST, "Estado inválido: " + status);
    }
    if (bd.getStatus() == newStatus) return;                                                       // +1
    if (newStatus == BusinessDataStatus.CLOSED) {                                                  // +1
        if (bd.getTasks() != null && !bd.getTasks().isEmpty()) {                                   // +1
            for (Task t : bd.getTasks()) {                                                         // +1
                if (t.getStatus() != TaskStatus.COMPLETED) {                                       // +1
                    if (t.getType() == TaskType.MANDATORY) {                                       // +1
                        throw new GenericException(HttpStatus.BAD_REQUEST, "Tarea pendiente");
                    }
                }
            }
        }
    }
    // más lógica...
}
```

**Ejemplo correcto:**
```java
@Override
public void setOpportunityStatus(String opportunityId, String status) throws GenericException {
    BusinessData bd = businessDataRepository.findById(opportunityId);
    BusinessDataStatus newStatus = parseStatus(status);
    if (bd.getStatus() == newStatus) return;
    if (newStatus == BusinessDataStatus.CLOSED) {
        validateNoMandatoryTasksPending(bd);
    }
    applyStatusChange(bd, newStatus);
}

private BusinessDataStatus parseStatus(String status) throws GenericException {
    try {
        return BusinessDataStatus.valueOf(status);
    } catch (IllegalArgumentException e) {
        throw new GenericException(HttpStatus.BAD_REQUEST, buildInvalidStatusMessage(status));
    }
}

private void validateNoMandatoryTasksPending(BusinessData bd) throws GenericException {
    boolean hasPendingMandatory = bd.getTasks() != null && bd.getTasks().stream()
            .filter(t -> t.getStatus() != TaskStatus.COMPLETED)
            .anyMatch(t -> t.getType() == TaskType.MANDATORY);
    if (hasPendingMandatory) {
        throw new GenericException(HttpStatus.BAD_REQUEST, "Existen tareas obligatorias pendientes");
    }
}
```

**Auto-corrección:**
```java
// Identificar las ramas if/else if principales → candidatas a métodos privados
// Extraer cada rama a un método privado con nombre que describe el subdominio (validar*, aplicar*, calcular*)
// Usar stream().anyMatch() / stream().allMatch() para sustituir bucles for con condiciones
// El método orquestador (CC baja) llama a métodos privados especializados (CC baja cada uno)
```

---

### [RULE-SPR-012] Longitud máxima de métodos — 25 líneas

**Severidad:** 🟡 Warning (deuda técnica)
**Aplica a:** Métodos nuevos — educativo en métodos legacy modificados donde se añadan líneas
**Quality Gate:** 🟡 Amarillo en ambos casos
**Descripción:** Un método no debe superar 25 líneas de código ejecutable (excluyendo comentarios y líneas en blanco). Métodos más largos acumulan múltiples responsabilidades y son difíciles de testear de forma unitaria. La excepción son los métodos de orquestación que coordinan subpasos ya extraídos a métodos privados — en ese caso el límite puede extenderse a 40 líneas si cada línea es una llamada a un método con nombre claro.

**Ejemplo incorrecto:**
```java
@Override
@Transactional(rollbackOn = GenericException.class)
public Task updateTask(Task task, String bpmTaskId) throws GenericException {
    Task found = taskRepository.findByBpmTaskId(bpmTaskId);
    if (task.getStatus() != null && !task.getStatus().equals(found.getStatus())) {
        found.setStatus(task.getStatus());
        found.getStatusHistories().add(new StatusHistory(null, OffsetDateTime.now(), task.getStatus().name()));
    }
    List<Field> fieldsToDelete = found.getFields().stream()
            .filter(f -> f.getFieldId() != null)
            .filter(f -> task.getFields().stream()
                    .noneMatch(tf -> tf.getFieldId() != null && tf.getFieldId().equals(f.getFieldId())))
            .collect(Collectors.toList());
    fieldService.deleteFields(fieldsToDelete);
    List<Field> existingFields = task.getFields().stream()
            .filter(f -> f.getFieldId() != null)
            .collect(Collectors.toList());
    if (!existingFields.isEmpty()) {
        fieldService.saveField(existingFields);
    }
    objectUpdater.update(found, task);
    found.setFields(List.of());
    Task saved = taskRepository.saveTask(found);
    List<Field> newFields = task.getFields().stream()
            .filter(f -> f.getFieldId() == null)
            .collect(Collectors.toList());
    newFields.forEach(f -> f.setTask(new MinimalTask(saved.getTaskId())));
    if (!newFields.isEmpty()) {
        fieldService.saveField(newFields);
    }
    databaseUtils.flushAndClearPersistenceContext();
    return findTaskByBpmId(bpmTaskId);
    // 35+ líneas ejecutables — VIOLACIÓN
}
```

**Ejemplo correcto:**
```java
@Override
@Transactional(rollbackOn = GenericException.class)
public Task updateTask(Task task, String bpmTaskId) throws GenericException {
    Task found = taskRepository.findByBpmTaskId(bpmTaskId);
    applyStatusChangeWithHistory(task, found);
    syncTaskFields(task, found);
    objectUpdater.update(found, task);
    found.setFields(List.of());
    Task saved = taskRepository.saveTask(found);
    persistNewFields(task.getFields(), saved.getTaskId());
    databaseUtils.flushAndClearPersistenceContext();
    return findTaskByBpmId(bpmTaskId);
}

private void applyStatusChangeWithHistory(Task incoming, Task existing) {
    if (incoming.getStatus() != null && !incoming.getStatus().equals(existing.getStatus())) {
        existing.setStatus(incoming.getStatus());
        existing.getStatusHistories()
                .add(new StatusHistory(null, OffsetDateTime.now(), incoming.getStatus().name()));
    }
}
```

**Auto-corrección:**
```java
// Identificar pasos lógicos distintos dentro del método (cada "comentario implícito" = candidato)
// Extraer cada paso a un método privado con nombre que describe la acción (applyX, validateX, syncX)
// El método principal queda como una secuencia de llamadas legibles en menos de 25 líneas
```

---

### [RULE-SPR-013] Profundidad máxima de anidamiento — 2 niveles

**Severidad:** 🟡 Warning (deuda técnica)
**Aplica a:** Métodos nuevos — educativo en métodos legacy modificados
**Quality Gate:** 🟡 Amarillo en ambos casos
**Descripción:** Los bloques de control (`if`, `for`, `while`, `try`) no deben anidarse más de 2 niveles de profundidad. El anidamiento profundo incrementa la complejidad cognitiva exponencialmente y es la principal causa de métodos ilegibles. La técnica de "guard clause" (retorno/excepción anticipada) y la extracción a métodos privados eliminan la mayoría de los niveles de anidamiento.

**Ejemplo incorrecto:**
```java
public void procesarCampos(BusinessData bd) throws GenericException {
    if (bd != null) {                                       // nivel 1
        if (bd.getTasks() != null) {                        // nivel 2
            for (Task task : bd.getTasks()) {               // nivel 3 — VIOLACIÓN
                if (task.getFields() != null) {             // nivel 4 — VIOLACIÓN
                    for (Field f : task.getFields()) {      // nivel 5 — VIOLACIÓN
                        if (f.getValue() != null) {
                            procesarValor(f.getValue());
                        }
                    }
                }
            }
        }
    }
}
```

**Ejemplo correcto:**
```java
public void procesarCampos(BusinessData bd) throws GenericException {
    if (bd == null || bd.getTasks() == null) return;     // guard clause — nivel 1 solo
    bd.getTasks().stream()
            .filter(t -> t.getFields() != null)
            .flatMap(t -> t.getFields().stream())
            .filter(f -> f.getValue() != null)
            .forEach(f -> procesarValor(f.getValue()));  // streams eliminan anidamiento
}
```

**Auto-corrección:**
```java
// Técnica 1 (guard clause): invertir la condición del if externo y retornar/lanzar temprano
// Técnica 2 (extracción): cada nivel de anidamiento > 2 es candidato a método privado
// Técnica 3 (streams): sustituir bucles for + if por stream().filter().map().forEach()
// Técnica 4 (Optional): encadenar .map().filter() en lugar de if anidados para nulos
```

---

## 5. Contratos OpenAPI y Versionado

### [RULE-SPR-014] Contratos API en YML con versionado SemVer

**Severidad:** 🔴 Crítico (seguridad/arquitectura)
**Aplica a:** Cualquier cambio en ficheros `src/main/resources/apis/*.yml` — código nuevo y legacy
**Quality Gate:** 🔴 Rojo — bloquea merge si se modifica el contrato sin actualizar la versión
**Descripción:** Los contratos API del proyecto se definen en los ficheros YML de `src/main/resources/apis/` (ej. `api-BPM.yml`, `api-TABLE.yml`). Cualquier cambio en estos ficheros debe ir acompañado del incremento de versión correcto en el campo `info.version` del YML y en la dependencia del artefacto generado en `pom.xml`. Se sigue Semantic Versioning estricto.

**Regla SemVer aplicada a contratos YML:**

| Tipo de cambio | Versión | Ejemplo |
|---------------|---------|---------|
| Añadir endpoint nuevo | MINOR `0.0.17 → 0.1.0` | Nuevo `GET /opportunity/search` |
| Añadir campo opcional en request/response | MINOR | `optional: true` en el YML |
| Cambiar tipo de un campo existente | MAJOR `0.0.17 → 1.0.0` | `string → integer` en el schema |
| Eliminar un endpoint o campo | MAJOR | Eliminar `POST /event/` |
| Renombrar un campo en el schema | MAJOR | `taskId → id` en el schema |
| Cambiar método HTTP de un endpoint | MAJOR | `POST → PUT` |

**Ejemplo incorrecto:**
```yaml
# api-BPM.yml — info.version sigue en 0.0.17 tras un cambio breaking
info:
  version: "0.0.17"   # VIOLACIÓN: versión no actualizada tras cambio de tipo en schema

definitions:
  Task:
    properties:
      status:
        type: integer   # CAMBIO BREAKING: era "type: string" — requiere MAJOR bump
```

**Ejemplo correcto:**
```yaml
# api-BPM.yml — versión actualizada a 1.0.0 por cambio breaking
info:
  version: "1.0.0"    # MAJOR bump por cambio de tipo breaking

definitions:
  Task:
    properties:
      status:
        type: integer
```

```xml
<!-- pom.xml — dependencia actualizada con la nueva versión generada -->
<dependency>
    <groupId>WGTB-APIBPM-server.spring.nova-generated</groupId>
    <version>1.0.0</version>
</dependency>
```

**Auto-corrección:**
```yaml
# 1. Determinar si el cambio es MINOR (no rompe) o MAJOR (rompe compatibilidad)
# 2. Actualizar info.version en el fichero .yml
# 3. Actualizar la versión de la dependencia generada en pom.xml
# 4. Si MAJOR: crear plan de migración y comunicar a equipos consumidores del artefacto generado
# 5. Actualizar el CHANGELOG.md del proyecto con descripción del cambio de contrato
```

---

### [RULE-SPR-015] Prohibición de eliminar o renombrar elementos del contrato YML sin versión MAJOR

**Severidad:** 🔴 Crítico (seguridad/arquitectura)
**Aplica a:** Ficheros `src/main/resources/apis/*.yml` — código nuevo y legacy
**Quality Gate:** 🔴 Rojo — bloquea merge independientemente del contexto (nuevo o legacy)
**Descripción:** Eliminar o renombrar un endpoint, un parámetro o un campo del schema en los ficheros YML es un cambio breaking que rompe todos los clientes del artefacto generado. Está terminantemente prohibido sin un incremento de versión MAJOR. La estrategia preferida para campos que se quieren eliminar es deprecarlos primero con `x-deprecated: true` y eliminarlos en la siguiente versión MAJOR tras el periodo de migración.

**Ejemplo incorrecto:**
```yaml
# api-BPM.yml — versión 0.0.17 — campo eliminado sin bump MAJOR — VIOLACIÓN
definitions:
  Task:
    properties:
      # bpmTaskId eliminado silenciosamente — rompe a los clientes que lo consumen
      status:
        type: string
      assignee:
        type: string
```

**Ejemplo correcto (estrategia de deprecación — MINOR primero):**
```yaml
# api-BPM.yml — versión 0.1.0 — campo marcado como deprecated
info:
  version: "0.1.0"
definitions:
  Task:
    properties:
      bpmTaskId:
        type: string
        x-deprecated: true          # señal para los consumidores: migrar antes del MAJOR
        description: "Deprecated: use taskId instead"
      taskId:
        type: string
        description: "New identifier field, replaces bpmTaskId"
      status:
        type: string
```

```yaml
# api-BPM.yml — versión 1.0.0 — campo deprecated eliminado tras periodo de migración
info:
  version: "1.0.0"
definitions:
  Task:
    properties:
      taskId:
        type: string
      status:
        type: string
```

**Auto-corrección:**
```yaml
# NO eliminar el campo/endpoint directamente
# Paso 1: marcar con x-deprecated: true y añadir el nuevo elemento (bump MINOR)
# Paso 2: comunicar a los equipos consumidores con fecha límite de migración
# Paso 3: confirmar que todos los consumidores han migrado
# Paso 4: eliminar el elemento deprecated en la siguiente versión MAJOR
```

---

## 6. Semáforo de Calidad (Quality Gate)

El agente emite uno de los tres estados al finalizar el análisis. El estado final es el peor estado individual detectado.

### Estado 🔴 Rojo — Bloqueado

El merge queda bloqueado. Cambios obligatorios antes de continuar.

**Condiciones que activan el estado ROJO:**
- Cualquier Listener que inyecte un Repository directamente (RULE-SPR-001)
- Service/Listener sin anotación correcta en código nuevo (RULE-SPR-003)
- Repository que no siga el patrón de tres capas en código nuevo (RULE-SPR-005)
- Clase nueva que no respete el naming del proyecto (I+prefijo, +Impl, +Jpa, etc.) (RULE-SPR-007)
- Método de Listener sin try-catch + GenericApiErrorBuilder en código nuevo (RULE-SPR-008)
- Retorno de `null` en cualquier método de Service o Repository (RULE-SPR-009)
- Método nuevo con complejidad ciclomática > 10 (RULE-SPR-011)
- Cambio en `apis/*.yml` sin actualizar `info.version` conforme a SemVer (RULE-SPR-014)
- Eliminación o renombrado de elemento en `apis/*.yml` sin versión MAJOR (RULE-SPR-015)

**Acción del agente:** comentario bloqueante en la PR con la regla infringida, fragmento de código incorrecto y bloque de auto-corrección sugerido.

---

### Estado 🟡 Amarillo — Aviso

El merge está permitido. El agente notifica con sugerencias educativas sin bloquear.

**Condiciones que activan el estado AMARILLO:**
- God Object detectado en Service nuevo o existente modificado (RULE-SPR-002)
- Anotaciones de capa incorrectas en código legacy modificado (RULE-SPR-003)
- Inyección por `@Autowired` en lugar de `@RequiredArgsConstructor` (RULE-SPR-004)
- Naming del proyecto incorrecto en código legacy modificado (RULE-SPR-007)
- try-catch incompleto en Listeners legacy modificados (RULE-SPR-008)
- Uso de `Optional` donde la semántica requiere excepción de dominio, o viceversa (RULE-SPR-009)
- Conversión manual en lugar de MapStruct (RULE-SPR-010)
- Método legacy modificado con complejidad ciclomática > 10 (RULE-SPR-011)
- Método nuevo o modificado con más de 25 líneas ejecutables (RULE-SPR-012)
- Anidamiento mayor de 2 niveles en código nuevo o modificado (RULE-SPR-013)
- Naming general incorrecto (camelCase, UPPER_SNAKE_CASE) en métodos/variables (RULE-SPR-006)

---

### Estado 🟢 Verde — Limpio

Cero violaciones 🔴 y cero violaciones 🟡 detectadas en el diff analizado.

**Acción del agente:** aprobación automática sugerida con comentario de confirmación.

---

### Tabla resumen de reglas y estados

| Regla | Descripción breve | Código nuevo | Legacy modificado |
|-------|------------------|--------------|------------------|
| RULE-SPR-001 | Listener → Repository directo | 🔴 Rojo | 🔴 Rojo |
| RULE-SPR-002 | God Object en Services | 🟡 Amarillo | 🟡 Amarillo |
| RULE-SPR-003 | Anotaciones de capa incorrectas | 🔴 Rojo | 🟡 Amarillo |
| RULE-SPR-004 | @Autowired en lugar de @RequiredArgsConstructor | 🟡 Amarillo | 🟡 Amarillo |
| RULE-SPR-005 | Patrón tres capas en repositorios roto | 🔴 Rojo | 🔴 Rojo |
| RULE-SPR-006 | Naming general (PascalCase/camelCase/UPPER_SNAKE) | 🔴 Rojo (clase) / 🟡 resto | 🟡 Amarillo |
| RULE-SPR-007 | Naming del proyecto (I+, +Impl, +Jpa, Mapper+, Listener+) | 🔴 Rojo | 🟡 Amarillo |
| RULE-SPR-008 | Listener sin try-catch + GenericApiErrorBuilder | 🔴 Rojo | 🟡 Amarillo |
| RULE-SPR-009 | Retorno null / Optional vs excepción de dominio | 🔴 Rojo (null) / 🟡 (semántica) | 🔴 Rojo (null) / 🟡 (semántica) |
| RULE-SPR-010 | Conversión manual en lugar de MapStruct | 🟡 Amarillo | 🟡 Amarillo |
| RULE-SPR-011 | Complejidad ciclomática > 10 | 🔴 Rojo | 🟡 Amarillo |
| RULE-SPR-012 | Método > 25 líneas ejecutables | 🟡 Amarillo | 🟡 Amarillo |
| RULE-SPR-013 | Anidamiento > 2 niveles | 🟡 Amarillo | 🟡 Amarillo |
| RULE-SPR-014 | Cambio en YML sin bump SemVer | 🔴 Rojo | 🔴 Rojo |
| RULE-SPR-015 | Eliminar/renombrar en YML sin MAJOR | 🔴 Rojo | 🔴 Rojo |

---

## Acceptance Criteria

- [ ] Dado un diff con un `ListenerApiBpm` que inyecta `IBusinessDataRepository` → el agente emite 🔴 Rojo con referencia a RULE-SPR-001
- [ ] Dado un diff con un método `assignTask` sin `try-catch` + `GenericApiErrorBuilder` en código nuevo → el agente emite 🔴 Rojo con referencia a RULE-SPR-008
- [ ] Dado un diff con una clase `taskService` (minúscula) → el agente emite 🔴 Rojo con referencia a RULE-SPR-006
- [ ] Dado un diff con una interfaz `BusinessDataService` (sin prefijo I) → el agente emite 🔴 Rojo con referencia a RULE-SPR-007
- [ ] Dado un diff que modifica `api-BPM.yml` cambiando el tipo de un campo sin actualizar `info.version` → el agente emite 🔴 Rojo con referencia a RULE-SPR-014
- [ ] Dado un diff que elimina un campo de `api-BPM.yml` sin MAJOR bump → el agente emite 🔴 Rojo con referencia a RULE-SPR-015
- [ ] Dado un método nuevo con CC = 12 → el agente emite 🔴 Rojo con referencia a RULE-SPR-011 y bloque de refactorización
- [ ] Dado un método legacy modificado con CC = 15 → el agente emite 🟡 Amarillo (no bloquea)
- [ ] Dado un diff con `@Autowired` en campo → el agente emite 🟡 Amarillo con referencia a RULE-SPR-004
- [ ] Dado un diff sin ninguna violación → el agente emite 🟢 Verde con sugerencia de aprobación automática
- [ ] La Regla de Oro del Legacy se aplica: fallos 🔴 de estilo/calidad se degradan a 🟡 en código legacy modificado
- [ ] RULE-SPR-001, RULE-SPR-005, RULE-SPR-009 (retorno null), RULE-SPR-014 y RULE-SPR-015 emiten 🔴 tanto en nuevo como en legacy (no se degradan)

## Evidence

Pendiente de primera ejecución del agente contra una PR real del proyecto `WGTB-Backend-develop/wgtbBackend`. Las reglas se han derivado del análisis directo del codebase (estructura de clases, patrones de inyección, listeners, mappers, YMLs de API y pom.xml). Versión 0.2.0: reglas calibradas al patrón real del proyecto (0.1.0 contenía reglas genéricas de Spring Boot no aplicables a WGTB).

## Traceability

- `KDD_Auditoria_WGTB_Backend.md` — fuente primaria: mapeo WGTB, criterios de severidad, KDD workflow
- `arquitectura/arquitectura_hexagonal_wgtb.md` — referencia de arquitectura hexagonal del proyecto WGTB
- `arquitectura/guia_desarrollo_wgtb.md` — guía de desarrollo, convenciones y patrones del proyecto
- `PROJECT_CONTEXT.md` — contexto del proyecto, Regla de Oro del Legacy y tabla del Quality Gate
- `WGTB-Backend-develop/wgtbBackend/src` — codebase analizado directamente para calibrar las reglas (v0.2.0)
- `FEAT-HACK-001` — lógica del semáforo 🟢🟡🔴 (pendiente de crear)
- `FEAT-HACK-002` — Regla de Oro del Legacy — comportamiento diferencial nuevo vs. legacy (pendiente de crear)
- `ARCH-HACK-001` — arquitectura del proyecto WGTB Backend (ver traceability de este spec)
- `ARCH-HACK-002` — stack técnico del agente HackIAdos (pendiente de crear)
