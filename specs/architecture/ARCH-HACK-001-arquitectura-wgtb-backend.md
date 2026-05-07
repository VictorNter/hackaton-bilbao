---
id: ARCH-HACK-001
type: spec
layer: architecture
domain: AI Code Review
subdomain: Target Codebase Architecture
status: draft
confidence: medium
version: "0.1.0"
created: 2026-05-04
updated: 2026-05-04
owner: victor-carmona
reviewers:
  - pablo-martinez
  - lourdes-pozo
dependencies:
  - id: DOC-HACK-001
    relation: constrained-by
tags:
  - wgtb
  - spring-boot
  - java-11
  - hexagonal
  - openapi
  - mapstruct
  - oracle
  - nova
  - lombok
---

# ARCH-HACK-001 — Arquitectura del Backend WGTB

## Intent

Documenta la arquitectura técnica del proyecto WGTB Backend (`com.bbva.wgtb:wgtbbackend`), que es el codebase objetivo que el agente HackIAdos revisa. El agente necesita este contexto para interpretar correctamente los diffs de las PRs, aplicar las reglas de `RULEBOOK-SPRING-001` y distinguir violaciones arquitectónicas reales de código que simplemente sigue convenciones propias del proyecto.

---

## Definition

### Contexto

WGTB Backend es un servicio Spring Boot que implementa la gestión de procesos de negocio (BPM), servicios de tabla y plantillas para el entorno BBVA. Se despliega sobre la plataforma interna NOVA de BBVA mediante pipelines Jenkins. El artefacto Maven es `com.bbva.wgtb:wgtbbackend` y su estructura de código sigue **arquitectura hexagonal** (ports & adapters).

El proyecto utiliza **API-First**: los contratos de cada API se definen en ficheros OpenAPI/Swagger 2.0 (`.yml`) y el generador KLTT-APIRestGenerator produce automáticamente las interfaces de entrada HTTP y las clases de excepción por endpoint. Los desarrolladores **nunca escriben controllers HTTP a mano**.

---

### Stack Técnico

| Componente | Tecnología | Versión |
|-----------|-----------|---------|
| Lenguaje | Java | 11 |
| Framework principal | Spring Boot | Gestionado por `com.bbva.enoa.core:base:9.16.0` (NOVA) |
| Build | Maven | — |
| Base de datos | Oracle | ojdbc8 23.26.0.0.0 |
| ORM | Spring Data JPA / Hibernate | Gestionado por NOVA |
| Generación de código | KLTT-APIRestGenerator | Por versión de API |
| Mapping entre capas | MapStruct | 1.5.5.Final |
| Reducción de boilerplate | Lombok | 1.18.22 |
| Caché | Spring Cache (anotaciones) | Gestionado por NOVA |
| Clientes HTTP externos | Apache HttpClient | 4.5.14 |
| Testing | JUnit Jupiter + Mockito | Gestionado por NOVA |
| Despliegue | NOVA (plataforma interna BBVA) + Jenkins | — |
| Contrato de API propio | Swagger 2.0 en `.yml` | Por módulo |

---

### Estructura de módulos

El código fuente principal reside en `src/main/java/com/bbva/wgtb/wgtbbackend/` y se organiza en **tres módulos de negocio** y varios paquetes de soporte transversal:

```
com.bbva.wgtb.wgtbbackend/
│
├── apibpm/            ← Gestión de procesos BPM (oportunidades, tareas, comentarios, campos)
├── apitableservices/  ← Gestión de configuración de tablas y valores de selección
├── apitemplates/      ← Gestión de plantillas y secciones de formulario
│
├── exception/         ← Jerarquía de excepciones de dominio del proyecto
├── utils/             ← Utilidades transversales (caché, autenticación, mappers genéricos, AOP)
├── rdr/               ← Integración con servicio externo RDR (XML/XPath)
├── xbpm/              ← Clientes del API externo XBPM
└── Application.java   ← Punto de entrada Spring Boot
```

Los tres módulos de negocio (`apibpm`, `apitableservices`, `apitemplates`) comparten **exactamente la misma estructura interna de capas** descrita en la sección siguiente.

---

### Arquitectura Hexagonal por módulo

Cada módulo de negocio replica esta estructura de tres capas:

```
[modulo]/
├── application/                    ← Casos de uso y orquestación
│   ├── IXxxService.java            ← Interfaz del servicio (puerto de entrada)
│   └── impl/
│       └── XxxServiceImpl.java     ← Implementación con lógica de aplicación
│
├── domain/                         ← Modelo de negocio puro
│   └── entity/
│       ├── XxxEntity.java          ← Entidades del dominio (sin anotaciones JPA)
│       └── nodatabase/             ← Enums y objetos de valor sin persistencia
│
└── infrastructure/                 ← Adaptadores (entrada y salida)
    ├── listener/
    │   └── ListenerApiXxx.java     ← Adaptador HTTP de entrada (autogenerado parcialmente)
    ├── mapper/
    │   └── MapperXxxDto.java       ← MapStruct: DTO (API) ↔ modelo de dominio
    └── repository/
        ├── IXxxRepository.java     ← Puerto de salida (interfaz de dominio)
        ├── impl/
        │   └── XxxRepositoryImpl.java  ← @Repository: orquesta JPA + caché + mapeo
        └── jpa/
            ├── XxxJpa.java             ← Entidad JPA (@Entity, columnas Oracle)
            ├── XxxRepositoryJpa.java   ← Spring Data JPA (extends JpaRepository)
            └── XxxMapper.java          ← MapStruct: entidad JPA ↔ modelo de dominio
```

**Regla fundamental de la arquitectura:** la dependencia de capas es unidireccional. `application` puede llamar a `infrastructure` vía interfaces, `domain` no conoce ninguna capa. `infrastructure/listener` solo depende de `application`. El incumplimiento de esta regla es la violación más grave que puede detectar el agente.

---

### Flujo API-First: del contrato YML al listener

El ciclo completo desde la definición del contrato hasta la implementación es:

```
1. src/main/resources/apis/api-BPM.yml        ← Contrato OpenAPI 2.0 (escrito por el equipo)
         ↓  KLTT-APIRestGenerator
2. WGTB-APIBPM-server.spring.nova-generated   ← Artefacto Maven con código generado:
   ├── IRestListenerApibpm.java                    ← Interfaz que el listener debe implementar
   ├── AssignTaskException400.java                 ← Excepción tipada por endpoint y código HTTP
   ├── AssignTaskException404.java
   ├── AssignTaskException500.java
   └── [una excepción por endpoint × código HTTP]
         ↓  implementado por el desarrollador
3. infrastructure/listener/ListenerApiBpm.java  ← @Service que implementa IRestListenerApibpm
         ↓  delega en
4. application/impl/XxxServiceImpl.java         ← Lógica de negocio/aplicación
```

Los ficheros del paso 2 **nunca se modifican manualmente**: son el artefacto generado. Cualquier cambio de contrato se hace en el `.yml` y se regenera. Esta es la razón por la que no existe `@RestController` escrito a mano en el proyecto.

Los contratos de **APIs consumidas** (XBPM, RDR) siguen el mismo ciclo pero como clientes generados: `src/main/resources/consumed/*.yml` → artefacto cliente JAX-RS generado → inyectado en `rdr/` y `xbpm/`.

---

### Patrones de implementación establecidos

#### 1. Interface-first con convención de naming

Todo componente con implementación va acompañado de su interfaz. Las convenciones son estrictas y sirven como señal de navegación en el codebase:

| Artefacto | Convención | Ejemplo |
|-----------|-----------|---------|
| Interfaz de servicio | `I` + nombre | `IBusinessDataService` |
| Implementación de servicio | nombre + `ServiceImpl` | `BusinessDataServiceImpl` |
| Interfaz de repositorio | `I` + nombre | `IBusinessDataRepository` |
| Implementación de repositorio | nombre + `RepositoryImpl` | `BusinessDataRepositoryImpl` |
| Interfaz Spring Data JPA | nombre + `RepositoryJpa` | `BusinessDataRepositoryJpa` |
| Entidad JPA | nombre + `Jpa` | `BusinessDataJpa` |
| Mapper DTO↔modelo | `Mapper` + nombre DTO | `MapperBusinessDataDto` |
| Mapper JPA↔modelo | nombre + `Mapper` | `BusinessDataMapper` |
| Listener HTTP | `Listener` + nombre API | `ListenerApiBpm` |
| Excepción de dominio | nombre descriptivo + `Exception` | `EntityNotFoundException` |

#### 2. Inyección de dependencias

La inyección se realiza exclusivamente por constructor. El proyecto estandariza `@RequiredArgsConstructor` de Lombok sobre campos `final`, que genera el constructor automáticamente. No existe `@Autowired` en campos en el código nuevo.

```java
@Service
@RequiredArgsConstructor
public class BusinessDataServiceImpl implements IBusinessDataService {

    private final IBusinessDataRepository businessDataRepository;
    private final ITaskRepository taskRepository;
    private final ObjectUpdater objectUpdater;
    // Lombok genera: public BusinessDataServiceImpl(IBusinessDataRepository, ITaskRepository, ObjectUpdater)
}
```

#### 3. Repositorios en tres capas

El acceso a datos siempre pasa por tres niveles:

- **`IXxxRepository`** (dominio): contrato sin tecnología de persistencia, recibe y devuelve objetos de dominio.
- **`XxxRepositoryImpl`** (`@Repository`): puente entre dominio e infraestructura JPA. Aplica `@Cacheable`/`@CacheEvict`, convierte entidades JPA a modelos de dominio con MapStruct, y orquesta operaciones complejas de persistencia.
- **`XxxRepositoryJpa`** (`extends JpaRepository<XxxJpa, ID>`): interfaz Spring Data. Spring genera la implementación. Contiene solo métodos de consulta JPA.

Un servicio solo puede inyectar `IXxxRepository`. Nunca `XxxRepositoryJpa` directamente.

#### 4. Manejo de excepciones

El proyecto tiene dos niveles de excepción:

**Nivel dominio** — jerarquía propia del proyecto:
```
Exception
└── GenericException (base: tiene HttpStatus code)
    ├── EntityNotFoundException    (NOT_FOUND)
    ├── EntityAlreadyExistsException
    ├── AuthenticationException
    ├── XbpmException              (errores del servicio externo XBPM)
    └── RdrException               (errores del servicio externo RDR)
```

**Nivel API** — generadas por KLTT, una por endpoint × código HTTP:
```
AssignTaskException400   (BAD_REQUEST)
AssignTaskException404   (NOT_FOUND)
AssignTaskException500   (INTERNAL_SERVER_ERROR)
[una terna por cada operación del YML]
```

El listener captura `GenericException` y mapea su `HttpStatus` a la excepción de API correspondiente mediante `GenericApiErrorBuilder`:

```java
try {
    this.service.assignTask(taskId);
} catch (GenericException ex) {
    GenericApiErrorBuilder<APIError> builder = GenericApiErrorBuilder.of(APIError.class);
    switch (ex.getCode()) {
        case NOT_FOUND:  throw new AssignTaskException404(builder.getFromGenericException(ex));
        case BAD_REQUEST: throw new AssignTaskException400(builder.getFromGenericException(ex));
        default: throw new AssignTaskException500(builder.getUnexpected());
    }
} catch (Exception ex) {
    throw new AssignTaskException500(GenericApiErrorBuilder.of(APIError.class).getUnexpected());
}
```

#### 5. Mapping con MapStruct

Las conversiones entre capas se implementan con MapStruct, extendiendo interfaces genéricas del proyecto:

```java
// DTO (API) ↔ Modelo de dominio
public interface GenericDtoMapper<M, D> {
    M toModel(D dto) throws GenericException;
    D toDto(M model) throws GenericException;
    List<M> toModelList(List<D> dtoList) throws GenericException;
    List<D> toDtoList(List<M> modelList) throws GenericException;
}

// Implementación: solo declaración, MapStruct genera el cuerpo
@Mapper(componentModel = "spring", uses = { MapperTaskDto.class, DateMapper.class })
public interface MapperBusinessDataDto
        extends GenericDtoMapper<BusinessData, BusinessDataDto> {}
```

La conversión manual campo a campo está prohibida cuando existe el mapper equivalente.

#### 6. Entidades JPA y convenciones Oracle

Las entidades JPA tienen el sufijo `Jpa` y siguen las convenciones de Oracle:
- Nombres de tabla: `UPPERCASE` (`@Table(name = "TWGTBBUS")`)
- Nombres de columna: `UPPERCASE_CON_UNDERSCORES` (`@Column(name = "COD_BSNS_ID")`)
- IDs generados: secuencias Oracle con generadores personalizados (`@GenericGenerator`)
- Campos de auditoría: heredados de `AuditedEntity` (base class del proyecto)

Los modelos de dominio en `domain/entity/` **no tienen anotaciones JPA**. Son POJOs con Lombok (`@Getter`, `@Setter`, `@AllArgsConstructor`, `@NoArgsConstructor`, `@FieldNameConstants`).

#### 7. Ausencia de valor: excepción vs Optional

El proyecto convive con dos semánticas de "no encontrado":

| Semántica | Patrón | Ejemplo en el proyecto |
|-----------|--------|----------------------|
| La entidad **debe** existir; su ausencia es un error | lanzar `EntityNotFoundException` | `BusinessDataRepositoryImpl.findById` |
| La entidad **puede** o no existir; es un resultado válido | retornar `Optional<T>` | `FieldServiceImpl.findByFieldCodeAndBusinessData` |

Retornar `null` está prohibido en ambos casos.

---

### Infraestructura y despliegue

| Aspecto | Detalle |
|---------|---------|
| Plataforma de despliegue | NOVA (plataforma interna BBVA) |
| CI/CD | Jenkins automatizado vía NOVA |
| Base de datos | Oracle — conexión mediante `ojdbc8`, naming en UPPERCASE |
| Caché | Spring Cache con `@Cacheable` y `@CacheEvict` en `XxxRepositoryImpl` |
| Autenticación | Filtro NOVA (`AuthenticationFilter`, `NovaAuthentication`, `NovaSecurityContext`) |
| Logging | `@Slf4j` de Lombok en listeners y servicios que requieren trazabilidad |
| AOP | `LogAspect` para logging transversal |
| APIs externas consumidas | XBPM (JAX-RS, clientes generados) · RDR Party y RDR Dictionary (JAX-RS, XML/XPath) |
| Configuración por entorno | `application.yml` (base) + `application-LOCAL.yml` (perfil local) + `bootstrap.yml` |
| Empaquetado | JAR con directorio de salida `./dist` |
| Configuración del compilador | Maven Compiler Plugin 3.8.1, source/target Java 11, annotation processors: MapStruct + Lombok + Lombok-MapStruct binding |

---

### Módulos de negocio: responsabilidades

| Módulo | Package | API de entrada | Responsabilidad |
|--------|---------|---------------|-----------------|
| `apibpm` | `apibpm/` | `api-BPM.yml` v0.0.17, `api-BPM-STATUS.yml` v0.0.2 | Gestión del ciclo de vida de procesos BPM: oportunidades (`BusinessData`), tareas (`Task`), comentarios (`Comment`), campos dinámicos (`Field`) e historial de estados (`StatusHistory`) |
| `apitableservices` | `apitableservices/` | `api-TABLE.yml` v0.0.17 | Configuración de tablas de datos, columnas y valores de selección |
| `apitemplates` | `apitemplates/` | `api-TEMPLATES.yml` v0.0.11 | Gestión de plantillas de formulario y sus secciones |

---

### Cobertura de tests

El proyecto mantiene una batería de tests unitarios que cubre todas las capas. La cobertura aproximada es de 92 ficheros de test, usando:
- **JUnit Jupiter** (JUnit 5) para la estructura de tests
- **Mockito** + `mockito-junit-jupiter` para mocking de dependencias
- **bean-matchers** para tests de getters/setters en entidades y DTOs
- **Hamcrest** para aserciones expresivas

Los tests de listener verifican el mapeo correcto de `GenericException` a excepciones de API. Los tests de servicio verifican la lógica de negocio con repositorios mockeados. Los tests de repositorio verifican el comportamiento de caché y mapeo JPA.

---

## Acceptance Criteria

- [ ] El agente es capaz de identificar a qué capa pertenece cualquier clase del proyecto por su nombre y ubicación en el paquete
- [ ] El agente distingue entre código autogenerado por KLTT (no modificable) e implementación manual (revisable)
- [ ] El agente entiende que la ausencia de `@RestController` es correcta en este proyecto
- [ ] El agente aplica las reglas de `RULEBOOK-SPRING-001` con conocimiento de la estructura de capas real del proyecto
- [ ] El agente identifica correctamente un cambio en `apis/*.yml` como cambio de contrato sujeto a RULE-SPR-014 y RULE-SPR-015
- [ ] El agente no marca como violación el uso de `@Service` en las clases `Listener*` (es el patrón correcto del proyecto)

## Evidence

Derivado de análisis directo del codebase `WGTB-Backend-develop/wgtbBackend/src` en Mayo 2026. Ficheros analizados: `pom.xml`, `ListenerApiBpm.java`, `BusinessDataServiceImpl.java`, `BusinessDataRepositoryImpl.java`, `BusinessDataJpa.java`, `MapperBusinessDataDto.java`, `GenericDtoMapper.java`, `GenericException.java`, `api-BPM.yml`, `api-TABLE.yml`, `application.yml`. Confidence `medium`: análisis de código sin validación explícita del equipo de desarrollo de WGTB.

## Traceability

- `KDD_Auditoria_WGTB_Backend.md` — auditoría operativa del backend que motivó este spec
- `arquitectura/arquitectura_hexagonal_wgtb.md` — análisis de la arquitectura hexagonal del proyecto
- `arquitectura/guia_desarrollo_wgtb.md` — guía de desarrollo y convenciones del proyecto
- `arquitectura/integraciones_modulos_wgtb.md` — detalle de integraciones entre módulos
- `DOC-HACK-001` (`rulebooks/RULEBOOK-SPRING-001.md`) — reglas de calidad derivadas de esta arquitectura
- `WGTB-Backend-develop/wgtbBackend/src` — fuente primaria del análisis
