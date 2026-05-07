## 1. INTRODUCCIÓN

`wgtbbackend` es un microservicio REST de tipo API, perteneciente a la UUAA **WGTB** (GTB Workflow Tool), desarrollado en Java 11 con Spring Boot y desplegado sobre la plataforma NOVA. Su función principal es servir como backend de la herramienta de gestión de flujos de trabajo operativos del área GTB (Global Transaction Banking), proporcionando la capa de negocio y persistencia que sustenta las interfaces de usuario y los procesos automatizados de la plataforma.

El servicio resuelve la necesidad de orquestar y registrar el ciclo de vida de oportunidades y tareas de negocio dentro de flujos BPM. Recibe eventos y acciones sobre estas entidades — creación de oportunidades, asignación y liberación de tareas, cambio de estados, registro de comentarios, gestión de campos dinámicos — y los persiste en una base de datos Oracle, manteniendo además un historial de estados. Esta funcionalidad permite a los equipos GTB hacer seguimiento de sus operaciones de forma estructurada y trazable.

En la arquitectura de la UUAA, `wgtbbackend` actúa como el backend central: expone cuatro APIs REST propias (`APIBPM`, `APITEMPLATES`, `APITABLE`, `APIBPMSTATUS`) que son consumidas por el frontend de la herramienta, y a su vez consume servicios externos de BBVA — el motor de procesos BPM (`XBPM-Api`) y el repositorio de datos de referencia RDR (`ARDR-rdrParty`, `ARDR-rdrDictionary`). El flujo de datos característico es: el frontend llama a los endpoints del backend → el backend consulta o actualiza Oracle vía JPA → en operaciones BPM, el backend delega en `XBPM-Api` para la gestión del proceso → para enriquecer datos de tablas, consume RDR.

El servicio cubre la totalidad del backend funcional a la versión `1.0.65`. No se detectan módulos desactivados significativos en el código analizado, aunque la configuración RDR aparece comentada en `application.yml`, lo que indica que la integración con RDR podría estar desactivada o pendiente de activación en ciertos entornos.

---

## 2. Identidad del servicio

| Campo | Valor |
|-------|-------|
| **Nombre del servicio** | `wgtbbackend` |
| **UUAA** | WGTB |
| **Propósito** | Backend de la herramienta GTB Workflow Tool: gestiona el ciclo de vida de oportunidades de negocio y sus tareas asociadas dentro de flujos BPM, incluyendo persistencia, estados, comentarios, campos dinámicos y configuración de tablas. |
| **Lenguaje / runtime** | Java 11 / Spring Boot (parent NOVA `base:9.16.0`, JDK Amazon Corretto 11.0.11.9.1) |

---


### 3.1. Upstream (quién llama a este servicio)

| Origen | Canal | Endpoint / topic / fichero | Notas |
|--------|-------|----------------------------|-------|
| Frontend WGTB / consumidores NOVA | REST | `/apibpm/**` (API `WGTB-APIBPM` v0.0.17) | Operaciones sobre oportunidades y tareas BPM |
| Frontend WGTB / consumidores NOVA | REST | `/apitemplates/**` (API `WGTB-APITEMPLATES` v0.0.11) | Gestión de plantillas y secciones |
| Frontend WGTB / consumidores NOVA | REST | `/apitable/**` (API `WGTB-APITABLE` v0.0.17) | Consulta y configuración de tablas dinámicas |
| Consumidores NOVA | REST | `/apibpmstatus/**` (API `WGTB-APIBPMSTATUS` v0.0.2) | Cambios de estado BPM desde sistemas externos |

### 3.2. Downstream (a qué llama este servicio)

| Destino | Canal | Endpoint / topic / fichero | Notas |
|---------|-------|----------------------------|-------|
| XBPM (motor BPM corporativo) | REST (cliente JAX-RS NOVA) | API `XBPM-Api` v1.8.1 | Asignación, liberación, completado de tareas, envío de señales, consulta de usuario actual |
| ARDR — RDR Dictionary | REST (cliente JAX-RS NOVA) | API `ARDR-rdrDictionary` v0.1.0 | Consulta de diccionario de datos de referencia |
| ARDR — RDR Party | REST (cliente JAX-RS NOVA) | API `ARDR-rdrParty` v0.1.0 | Consulta de datos de terceros/contrapartes |
| Oracle DB (WGTB schema) | JDBC / JPA (ojdbc8) | Schema `WGTB`; tablas `TWGTBBUS`, `TWGTBTSK`, `TWGTBCMT`, `TWGTBFLD`, `TWGTBSTH`, `TWGTBCOL`, `TWGTBPRD`, `TWGTBTEM`, etc. | Owner de todos los datos operativos del servicio |

### 3.3. Almacenes de datos

| Almacén | Tecnología | Rol | Notas |
|---------|-----------|-----|-------|
| WGTB Oracle schema | Oracle (ojdbc8 23.26, dialect `Oracle12cDialect`) | Owner | `ddl-auto: validate`; schema `WGTB`; secuencias propias por tabla (`QWGTBBUS1`, `QWGTBTSK1`, etc.). Incluye base de datos H2 en scope `runtime` (probablemente para tests locales). |
| Caché en memoria | Spring Cache (sin proveedor externo visible) | Cache | Caché de resultados de `allBusinessData` mediante `@Cacheable` / `@CacheEvict`. |

### 3.4. Sistemas externos / terceros

| Sistema | Canal | Propósito |
|---------|-------|-----------|
| XBPM (BBVA BPM engine) | REST NOVA (JAX-RS client) | Delegación de operaciones de proceso: asignación/liberación de tareas, completado, señales, consulta de usuario autenticado |
| RDR (Reference Data Repository — ARDR) | REST NOVA (JAX-RS client) | Enriquecimiento de datos de tablas dinámicas con información de diccionario y de terceros |

---

## 4. Infraestructura y runtime

| Campo | Valor |
|-------|-------|
| **Plataforma de despliegue** | NOVA (declarado en `nova.yml`: `novaVersion: "24.05"`, `type: API`) |
| **Registro de servicio** | Eureka (Spring Cloud Config; nombre de aplicación configurable vía `APPLICATION_NAME`) |
| **Config server** | Spring Cloud Config Server (`CONFIG_SERVER_URI`) |
| **Puerto** | `${NOVA_PORT:8080}` |
| **Empaquetado** | JAR (`./dist/${project.groupId}-${project.artifactId}.jar`) |

---

## 5. Seguridad y compliance

| Campo | Valor |
|-------|-------|
| **Autenticación** | _(no detectable desde el código)_ — no se observan filtros de seguridad Spring explícitos ni configuración OAuth2/JWT/mTLS en el código analizado. La autenticación puede estar delegada a la plataforma NOVA (gateway/Webseal) a nivel de infraestructura. |
| **Autorización** | `NovaSecurityContext` utilizado en `ServiceApiBpmImpl` y `TableServiceImpl` para obtener el usuario actual del contexto de seguridad NOVA; no se detectan anotaciones `@PreAuthorize` / `@Secured` en el código analizado. |
| **Encryption at-rest** | _(no detectable desde el código)_ — delegado a configuración Oracle. |
| **Encryption in-transit** | Apache HttpClient (`httpclient 4.5.14`) presente como dependencia con soporte SSL; TLS presumiblemente gestionado por la plataforma NOVA. No se detecta configuración `SSLContext` explícita en el código analizado. |
| **Tags de compliance** | _(ninguno visible en el código)_ |

---

## 6. Arquitectura general

`wgtbbackend` sigue una arquitectura en capas tipo **ports & adapters** (hexagonal ligera), organizada en torno a dos dominios funcionales principales: `apibpm` (gestión de flujos BPM y entidades operativas) y `apitableservices` (configuración y consulta de tablas dinámicas), más el dominio `apitemplates` (plantillas de formularios). Cada dominio replica la misma estructura interna de cuatro capas: `infrastructure.listener` (adaptador de entrada REST, implementa las interfaces generadas por el generador NOVA), `application` (contratos de servicio como interfaces) y `application.impl` (lógica de negocio), `domain.entity` (modelo de dominio agnóstico de persistencia) e `infrastructure.repository` (adaptador de salida hacia Oracle, con doble nivel: interfaz de repositorio de dominio → implementación → JPA entities + Spring Data).

Los paquetes principales y sus responsabilidades son:

- `apibpm.infrastructure.listener` — adaptadores REST que reciben las llamadas externas y delegan en servicios de aplicación.
- `apibpm.application.impl` — lógica de negocio: ciclo de vida de `BusinessData` y `Task`, orquestación con XBPM, gestión de comentarios y campos dinámicos.
- `apibpm.domain.entity` — modelo de dominio (`BusinessData`, `Task`, `Comment`, `Field`, `StatusHistory`, `BpmTask`) y value objects sin persistencia directa (`TaskStatus`, `TaskAction`, `TaskType`, `BusinessDataStatus`, etc.).
- `apibpm.infrastructure.repository` — puerta de salida hacia Oracle; implementaciones desacoplan el dominio de las entidades JPA; uso de Spring Cache sobre `allBusinessData`.
- `apibpm.infrastructure.mapper` — conversión bidireccional dominio ↔ DTO usando MapStruct.
- `apitableservices` — dominio paralelo para tablas configurables, valores de selección y columnas; `TableServiceImpl` agrega datos de múltiples fuentes (Oracle, XBPM, RDR, templates) para construir respuestas de tabla paginadas y ordenadas.
- `apitemplates` — gestión de plantillas de sección referenciadas desde `Task` y `Field`.
- `xbpm` — cliente wrapper de la API XBPM consumida.
- `rdr` — cliente wrapper de la API RDR consumida.
- `utils` — utilidades transversales: `NovaSecurityContext`, `ObjectUpdater`, `DatabaseUtils`, `EntityScrapper`, `JsonUtils`, `Page`, `Constants`, mappers genéricos (`AuditedDomain`, `AuditedEntity`, `GenericDtoMapper`, `GenericEntityMapper`), converters JPA (`BooleanYNConverter`, `NullConverter`, `StringListConverter`).

El patrón arquitectónico observado es **ports & adapters** con convención de nomenclatura NOVA: los listeners actúan como adaptadores primarios (driving), los repositorios JPA como adaptadores secundarios (driven). La capa de aplicación está desacoplada de ambos extremos mediante interfaces (`IBusinessDataService`, `ITaskRepository`, etc.). Se emplea `@Transactional` con `rollbackOn = GenericException.class` en los servicios de aplicación del dominio BPM.

## 7. Paquetes



### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.application`

Contiene las interfaces de servicio que definen los contratos de la capa de aplicación para el módulo BPM, cubriendo operaciones sobre datos de negocio, comentarios, campos y comunicación con el motor BPM externo.

#### Clase `IBusinessDataService`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application***

Interfaz que declara las operaciones de negocio sobre entidades `BusinessData` y `Task`, incluyendo persistencia, consulta, gestión de comentarios y transición de estados.

##### Método `saveBusinessData`

Persiste una nueva instancia de `BusinessData` en el repositorio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Entidad de datos de negocio a guardar |

Retorna: `BusinessData` — entidad persistida con los datos actualizados.

##### Método `deleteBusinessData`

Elimina un registro de `BusinessData` identificado por su ID.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador único del BusinessData a eliminar |

Retorna: `BusinessData` — entidad eliminada.

##### Método `findById`

Recupera un `BusinessData` por su identificador único.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del BusinessData |

Retorna: `BusinessData` — entidad encontrada.

##### Método `findTaskByBpmId`

Busca una `Task` utilizando el identificador de tarea del motor BPM externo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmId** | `String` | Identificador de la tarea en el sistema BPM |

Retorna: `Task` — tarea asociada al identificador BPM proporcionado.

##### Método `allBusinessData`

Recupera la lista completa de entidades `BusinessData` almacenadas.

Retorna: `List<BusinessData>` — lista de todos los registros de datos de negocio.

##### Método `addTaskComment`

Agrega un comentario a una tarea identificada por su ID BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a asociar a la tarea |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

##### Método `addBusinessDataComment`

Agrega un comentario a una oportunidad de negocio (`BusinessData`) identificada por su ID.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a asociar a la oportunidad |
| **opportunityId** | `String` | Identificador de la oportunidad de negocio |

Retorna: `void`

##### Método `updateTask`

Actualiza los datos de una tarea existente identificada por su ID BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Objeto tarea con los datos actualizados |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `Task` — tarea actualizada.

##### Método `setOpportunityStatus`

Actualiza el estado de una oportunidad de negocio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **opportunityId** | `String` | Identificador de la oportunidad |
| **status** | `String` | Nuevo estado a asignar |

Retorna: `void`

##### Método `setTaskStatus`

Actualiza el estado de una tarea identificada por su ID BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |
| **status** | `String` | Nuevo estado a asignar |

Retorna: `void`

---

#### Clase `ICommentService`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application***

Interfaz que define las operaciones CRUD sobre la entidad `Comment`, permitiendo crear, consultar, actualizar y eliminar comentarios asociados a tareas u oportunidades.

##### Método `saveComment`

Persiste un nuevo comentario.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a guardar |

Retorna: `Comment` — comentario persistido.

##### Método `deleteComment`

Elimina un comentario por su identificador numérico.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario |

Retorna: `Comment` — comentario eliminado.

##### Método `findById`

Recupera un comentario por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario |

Retorna: `Comment` — comentario encontrado.

##### Método `allComment`

Recupera la lista completa de comentarios existentes.

Retorna: `List<Comment>` — lista de todos los comentarios.

##### Método `updateComment`

Actualiza los datos de un comentario existente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario a actualizar |
| **comment** | `Comment` | Objeto con los nuevos valores del comentario |

Retorna: `Comment` — comentario actualizado.

---

#### Clase `IFieldService`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application***

Interfaz que declara las operaciones sobre entidades `Field`, incluyendo persistencia individual y por lotes, eliminación, actualización de valor y búsquedas por código de campo.

##### Método `saveField(List<Field>)`

Persiste una lista de campos de forma masiva.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `List<Field>` | Lista de campos a guardar |

Retorna: `List<Field>` — lista de campos persistidos.

##### Método `saveFieldOnTask`

Persiste una lista de campos asociándolos a una tarea específica.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fields** | `List<Field>` | Lista de campos a guardar |
| **task** | `Task` | Tarea a la que se asocian los campos |

Retorna: `List<Field>` — lista de campos persistidos con la tarea asignada.

##### Método `deleteFields`

Elimina una lista de campos del repositorio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fields** | `List<Field>` | Lista de campos a eliminar |

Retorna: `void`

##### Método `saveField(Field)`

Persiste un único campo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo a guardar |

Retorna: `Field` — campo persistido.

##### Método `updateFieldValue`

Actualiza el valor de un campo existente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo con el nuevo valor a persistir |

Retorna: `Field` — campo actualizado.

##### Método `findByFieldCodeAndBusinessData`

Busca un campo por su código y el identificador del `BusinessData` al que pertenece.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código identificador del campo |
| **businessId** | `String` | Identificador del BusinessData asociado |

Retorna: `Optional<Field>` — campo encontrado, o vacío si no existe.

##### Método `findByFieldCodeAndTaskId`

Busca un campo por su código dentro de una lista de identificadores de tarea.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código identificador del campo |
| **taskIds** | `List<Long>` | Lista de identificadores de tarea donde buscar |

Retorna: `Optional<Field>` — campo encontrado, o vacío si no existe.

---

#### Clase `IServiceApiBpm`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application***

Interfaz que define las operaciones de integración con el motor BPM externo, incluyendo el envío de eventos, asignación y liberación de tareas, creación de oportunidades y completado de tareas.

##### Método `sendSignalEvent`

Envía un evento de señal al motor BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **signalInfo** | `CreateEventDto` | DTO con la información del evento a enviar |

Retorna: `void`

##### Método `assignTask`

Asigna una tarea BPM al usuario en sesión.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

##### Método `createOpportunityEvent`

Crea una oportunidad de negocio en el motor BPM a partir de un `BusinessData`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **newEvent** | `BusinessData` | Entidad de negocio con los datos de la nueva oportunidad |

Retorna: `void`

##### Método `completeTask`

Completa una tarea BPM aplicando la acción definida en el objeto `Task`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Tarea con los datos y la acción a ejecutar |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

##### Método `releaseTask`

Libera una tarea BPM previamente asignada, devolviéndola al pool de tareas disponibles.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

---

#### Clase `IServiceGetActualUser`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application***

Interfaz que declara la operación de consulta del usuario autenticado en sesión a través del motor BPM.

##### Método `getActualUser`

Obtiene la información del usuario actualmente autenticado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición Nova con información de sesión |

Retorna: `LoggedUserDto` — DTO con los datos del usuario en sesión.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.application.impl`

Contiene las implementaciones concretas de las interfaces de servicio de la capa de aplicación BPM, coordinando la lógica de negocio entre los repositorios, el motor BPM externo y las utilidades transversales.

#### Clase `BusinessDataServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application.impl***
***Implements: IBusinessDataService***

Implementación del servicio de datos de negocio. Gestiona el ciclo de vida completo de las entidades `BusinessData` y `Task`, incluyendo su persistencia, consulta, actualización de estados y gestión de comentarios. Utiliza `ObjectUpdater` para realizar merges parciales de propiedades y `DatabaseUtils` como utilidad auxiliar para operaciones sobre la base de datos.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **businessDataRepository** | `IBusinessDataRepository` | N/A | Repositorio de acceso a datos para BusinessData |
| **taskRepository** | `ITaskRepository` | N/A | Repositorio de acceso a datos para Task |
| **commentRepository** | `ICommentRepository` | N/A | Repositorio de acceso a datos para Comment |
| **statusHistoryRepository** | `IStatusHistoryRepository` | N/A | Repositorio de historial de estados |
| **objectUpdater** | `ObjectUpdater` | N/A | Utilidad para actualizar objetos parcialmente |
| **fieldService** | `IFieldService` | N/A | Servicio de gestión de campos |
| **databaseUtils** | `DatabaseUtils` | N/A | Utilidades de base de datos |

##### Método `findById`

Recupera un `BusinessData` por su identificador único lanzando excepción si no se encuentra.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del BusinessData |

Retorna: `BusinessData` — entidad encontrada.

Algoritmo:
1. Invoca el repositorio para buscar el `BusinessData` por `id`.
2. Si no existe, lanza `EntityNotFoundException`.
3. Retorna la entidad encontrada.

##### Método `findTaskByBpmId`

Recupera una `Task` a partir de su identificador en el sistema BPM externo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmId** | `String` | Identificador BPM de la tarea |

Retorna: `Task` — tarea asociada al identificador proporcionado.

Algoritmo:
1. Consulta el repositorio de tareas filtrando por `bpmTaskId`.
2. Si no existe, lanza `EntityNotFoundException`.
3. Retorna la tarea encontrada.

##### Método `allBusinessData`

Retorna todos los registros de `BusinessData` almacenados en la base de datos.

Retorna: `List<BusinessData>` — lista completa de registros.

Algoritmo:
1. Delega en el repositorio la consulta de todos los registros.
2. Retorna la lista resultante.

##### Método `deleteBusinessData`

Elimina el `BusinessData` identificado por `id` y lo retorna para posible auditoría.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del BusinessData a eliminar |

Retorna: `BusinessData` — entidad eliminada.

Algoritmo:
1. Busca el `BusinessData` por `id`; lanza `EntityNotFoundException` si no existe.
2. Elimina la entidad del repositorio.
3. Retorna la entidad eliminada.

##### Método `addTaskComment`

Agrega un comentario a la tarea BPM indicada, asignando automáticamente la fecha del comentario.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a agregar |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

Algoritmo:
1. Busca la tarea por `bpmTaskId`; lanza `GenericException` si no existe.
2. Asigna la fecha actual al campo `commentDate` del comentario.
3. Asocia el comentario a la tarea y persiste mediante el repositorio.

##### Método `addBusinessDataComment`

Agrega un comentario a una oportunidad de negocio, asignando automáticamente la fecha.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a agregar |
| **opportunityId** | `String` | Identificador de la oportunidad |

Retorna: `void`

Algoritmo:
1. Busca el `BusinessData` por `opportunityId`; lanza `GenericException` si no existe.
2. Asigna la fecha actual al campo `commentDate`.
3. Asocia el comentario al `BusinessData` y persiste mediante el repositorio.

##### Método `saveBusinessData`

Persiste una nueva entidad `BusinessData` inicializando los campos necesarios antes de la inserción.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Entidad a persistir |

Retorna: `BusinessData` — entidad guardada con ID y campos asignados.

Algoritmo:
1. Valida y completa los campos obligatorios del `BusinessData`.
2. Delega la persistencia en el repositorio.
3. Retorna la entidad persistida.

##### Método `updateTask`

Actualiza los datos de una tarea existente realizando un merge parcial de propiedades.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Objeto con los nuevos valores |
| **bpmTaskId** | `String` | Identificador BPM de la tarea a actualizar |

Retorna: `Task` — tarea actualizada.

Algoritmo:
1. Recupera la tarea existente por `bpmTaskId`.
2. Aplica el merge de propiedades usando `ObjectUpdater`.
3. Persiste la tarea actualizada y la retorna.

##### Método `setOpportunityStatus`

Actualiza el estado de una oportunidad, registrando la fecha de finalización si el estado es final.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **opportunityId** | `String` | Identificador de la oportunidad |
| **status** | `String` | Nuevo estado (valor de `BusinessDataStatus`) |

Retorna: `void`

Algoritmo:
1. Recupera el `BusinessData` por `opportunityId`; lanza `GenericException` si no existe.
2. Valida que el valor de `status` corresponda a un valor válido de `BusinessDataStatus`.
3. Actualiza el campo `status` de la entidad.
4. Si el nuevo estado tiene `isFinalStatus == true`, asigna `OffsetDateTime.now()` al campo `endDate`.
5. Registra un nuevo `StatusHistory` con la fecha y el estado.
6. Persiste los cambios dentro de la transacción.

##### Método `setTaskStatus`

Actualiza el estado de una tarea BPM al valor indicado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador BPM de la tarea |
| **status** | `String` | Nuevo estado (valor de `TaskStatus`) |

Retorna: `void`

Algoritmo:
1. Recupera la tarea por `bpmTaskId`.
2. Convierte el `String` de estado al enum `TaskStatus` correspondiente.
3. Actualiza el campo `status` de la tarea y persiste los cambios.

---

#### Clase `CommentServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application.impl***
***Implements: ICommentService***

Implementación del servicio de comentarios. Gestiona el ciclo de vida de las entidades `Comment`, apoyándose en `ICommentRepository` para la persistencia y en `ObjectUpdater` para las actualizaciones parciales.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **commentRepository** | `ICommentRepository` | N/A | Repositorio de acceso a datos para Comment |
| **objectUpdater** | `ObjectUpdater` | N/A | Utilidad para merge parcial de propiedades |

##### Método `saveComment`

Persiste un nuevo comentario verificando previamente su existencia.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a guardar |

Retorna: `Comment` — comentario persistido.

Algoritmo:
1. Delega la persistencia en el repositorio.
2. Retorna el comentario guardado.

##### Método `findById`

Recupera un comentario por su identificador, lanzando excepción si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario |

Retorna: `Comment` — comentario encontrado.

Algoritmo:
1. Consulta el repositorio por `id`.
2. Si no existe, lanza `EntityNotFoundException`.
3. Retorna el comentario encontrado.

##### Método `allComment`

Retorna todos los comentarios almacenados.

Retorna: `List<Comment>` — lista completa de comentarios.

Algoritmo:
1. Delega en el repositorio la consulta de todos los registros.
2. Retorna la lista resultante.

##### Método `deleteComment`

Elimina un comentario por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario a eliminar |

Retorna: `Comment` — comentario eliminado.

Algoritmo:
1. Recupera el comentario por `id`; lanza `EntityNotFoundException` si no existe.
2. Elimina la entidad del repositorio.
3. Retorna el comentario eliminado.

##### Método `updateComment`

Actualiza los datos de un comentario existente mediante merge parcial.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario a actualizar |
| **comment** | `Comment` | Objeto con los nuevos valores |

Retorna: `Comment` — comentario actualizado.

Algoritmo:
1. Recupera el comentario existente por `id`.
2. Aplica el merge de propiedades usando `ObjectUpdater`.
3. Persiste y retorna el comentario actualizado.

---

#### Clase `FieldServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application.impl***
***Implements: IFieldService***

Implementación del servicio de campos. Gestiona la persistencia y recuperación de entidades `Field`, enriqueciendo cada campo con sus metadatos de sección antes de guardarlos. Coordina también la eliminación de `SectionValue` asociados cuando los campos son borrados.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **fieldRepository** | `IFieldRepository` | N/A | Repositorio de acceso a datos para Field |
| **sectionValueRepository** | `ISectionValueRepository` | N/A | Repositorio de valores de sección de plantillas |

##### Método `saveField(List<Field>)`

Persiste una lista de campos en bloque.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fields** | `List<Field>` | Lista de campos a guardar |

Retorna: `List<Field>` — lista de campos persistidos.

Algoritmo:
1. Itera la lista de campos y para cada uno invoca `setFieldMetadata`.
2. Persiste todos los campos mediante el repositorio.
3. Retorna la lista resultante.

##### Método `saveFieldOnTask`

Persiste una lista de campos asociándolos a una tarea concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fields** | `List<Field>` | Lista de campos a guardar |
| **task** | `Task` | Tarea a la que se asocian los campos |

Retorna: `List<Field>` — lista de campos persistidos con la tarea asignada.

Algoritmo:
1. Para cada campo de la lista, asigna un `MinimalTask` con el `taskId` de la tarea recibida.
2. Invoca `saveField(List<Field>)` con los campos actualizados.
3. Retorna la lista de campos persistidos.

##### Método `deleteFields`

Elimina una lista de campos del repositorio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fields** | `List<Field>` | Lista de campos a eliminar |

Retorna: `void`

Algoritmo:
1. Itera la lista de campos y elimina cada uno mediante el repositorio.

##### Método `saveField(Field)`

Persiste un único campo enriqueciéndolo con sus metadatos previamente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo a guardar |

Retorna: `Field` — campo persistido.

Algoritmo:
1. Invoca `setFieldMetadata` sobre el campo para completar sus metadatos.
2. Persiste el campo mediante el repositorio.
3. Retorna el campo guardado.

##### Método `updateFieldValue`

Actualiza el valor de un campo existente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo con el nuevo valor |

Retorna: `Field` — campo actualizado.

Algoritmo:
1. Recupera el campo existente por su identificador.
2. Actualiza el valor del campo.
3. Persiste y retorna el campo actualizado.

##### Método `setFieldMetadata`

Método privado que enriquece un campo con su `SectionValue` correspondiente antes de la persistencia.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo al que se asignarán los metadatos |

Retorna: `Field` — campo enriquecido con su sección de metadatos.

Algoritmo:
1. Busca el `SectionValue` correspondiente al `fieldCode` del campo en el repositorio de secciones.
2. Si no se encuentra, lanza `GenericException`.
3. Asigna el `SectionValue` encontrado al campo.
4. Retorna el campo enriquecido.

##### Método `findByFieldCodeAndBusinessData`

Busca un campo por su código dentro del contexto de un `BusinessData`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo a buscar |
| **businessId** | `String` | Identificador del BusinessData asociado |

Retorna: `Optional<Field>` — campo encontrado, o vacío si no existe.

Algoritmo:
1. Delega la búsqueda en el repositorio de campos filtrando por `fieldCode` y `businessId`.
2. Retorna el resultado como `Optional`.

##### Método `findByFieldCodeAndTaskId`

Busca un campo por su código dentro de una lista de tareas.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo a buscar |
| **taskIds** | `List<Long>` | Lista de identificadores de tarea |

Retorna: `Optional<Field>` — campo encontrado, o vacío si no existe.

Algoritmo:
1. Delega la búsqueda en el repositorio filtrando por `fieldCode` y la lista de `taskIds`.
2. Retorna el resultado como `Optional`.

---

#### Clase `ServiceApiBpmImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application.impl***
***Implements: IServiceApiBpm***

Implementación principal de la integración con el motor BPM externo (XBPM). Coordina el envío de eventos, la asignación y liberación de tareas, la creación de oportunidades y el completado de tareas, manteniendo la consistencia entre el estado local (base de datos) y el estado del motor BPM.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **xbpmApi** | `ServiceApi` | N/A | Cliente de la API del motor BPM externo |
| **businessDataRepository** | `IBusinessDataRepository` | N/A | Repositorio local de BusinessData |
| **businessDataService** | `IBusinessDataService` | N/A | Servicio de operaciones sobre BusinessData |
| **taskRepository** | `ITaskRepository` | N/A | Repositorio local de Task |

##### Método `sendSignalEvent`

Envía un evento de señal al motor BPM a partir de un DTO de creación de evento.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **signalInfo** | `CreateEventDto` | Información del evento a enviar |

Retorna: `void`

Algoritmo:
1. Invoca el cliente XBPM con los datos del `CreateEventDto`.
2. Si la respuesta indica error, lanza `GenericException`.

##### Método `assignTask`

Asigna una tarea BPM al usuario en sesión, normalizando los tipos de tarea personalizados.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskid** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

Algoritmo:
1. Obtiene los datos de la tarea BPM mediante `getTaskById`.
2. Invoca `updateCustomTasksTypes` para normalizar tipos personalizados (NBC_COMMITTEE, REVIEW_LANGUAGE).
3. Recupera el usuario en sesión desde `NovaSecurityContext`.
4. Llama al cliente XBPM para asignar la tarea al usuario.
5. Actualiza el estado local de la tarea en el repositorio.
6. Si ocurre un error, lanza `GenericException` y revierte la transacción.

##### Método `updateCustomTasksTypes`

Método estático que normaliza los tipos de tarea personalizados de una `BpmTask`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTask** | `BpmTask` | Tarea BPM cuyos tipos se deben normalizar |

Retorna: `void`

Algoritmo:
1. Verifica si el `taskId` de la `BpmTask` corresponde a un tipo personalizado (e.g., NBC_COMMITTEE, REVIEW_LANGUAGE).
2. Si coincide, sustituye el valor por el tipo normalizado correspondiente.

##### Método `releaseTask`

Libera una tarea BPM previamente asignada, devolviéndola al pool disponible.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskid** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

Algoritmo:
1. Invoca el cliente XBPM para liberar la tarea identificada por `bpmTaskid`.
2. Actualiza el estado local de la tarea eliminando la asignación de usuario.
3. Si ocurre un error, lanza `GenericException`.

##### Método `createOpportunityEvent`

Crea una nueva oportunidad de negocio en el motor BPM a partir de un `BusinessData`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **newEvent** | `BusinessData` | Entidad con los datos de la nueva oportunidad |

Retorna: `void`

Algoritmo:
1. Asigna el originador (usuario en sesión) al `BusinessData`.
2. Construye el mapa de campos extra BPM (`ExtraBpmFields`) con los datos de la oportunidad.
3. Invoca el cliente XBPM para crear el evento de oportunidad.
4. Registra el `StatusHistory` inicial en la base de datos.
5. Si ocurre un error, lanza `GenericException` y revierte la transacción.

##### Método `completeTask`

Completa una tarea BPM aplicando la acción definida en la entidad `Task`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Tarea con la acción a ejecutar |
| **bpmTaskId** | `String` | Identificador BPM de la tarea a completar |

Retorna: `void`

Algoritmo:
1. Recupera la tarea BPM desde el motor usando `getTaskById`.
2. Construye el mapa de variables con la acción y el estado.
3. Llama al cliente XBPM para completar la tarea.
4. Actualiza el estado y la fecha de fin de la tarea local.
5. Invoca `updateNextTask` para determinar y activar la siguiente tarea en el flujo.
6. Si ocurre un error, lanza `GenericException` y revierte la transacción.

##### Método `updateNextTask`

Método privado que determina y activa la siguiente tarea en el flujo BPM según la acción ejecutada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Oportunidad de negocio en proceso |
| **task** | `Task` | Tarea que acaba de completarse |
| **action** | `TaskAction` | Acción ejecutada (APPROVED, REJECTED, REVIEW, etc.) |

Retorna: `void`

Algoritmo:
1. Evalúa el tipo de tarea actual y la acción ejecutada.
2. Determina la siguiente tarea según las reglas de flujo:
   - DRAFT_OPP + APPROVED → activa ENRICH_OPP.
   - ENRICH_OPP + APPROVED → activa PRECHECKS.
3. Crea y persiste la nueva tarea con estado inicial.
4. Actualiza el `BusinessData` con la referencia a la nueva tarea activa.

##### Método `getTaskById`

Recupera los datos de una tarea BPM directamente desde el motor externo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `BpmTask` — objeto con los datos de la tarea en el motor BPM.

Algoritmo:
1. Invoca el cliente XBPM para obtener la tarea por `bpmTaskId`.
2. Si la respuesta es errónea o vacía, lanza `GenericException`.
3. Retorna el objeto `BpmTask` obtenido.

##### Método `calculateDaysOpen`

Calcula y asigna el número de días que una tarea BPM lleva abierta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTask** | `BpmTask` | Tarea BPM sobre la que calcular los días abiertos |
| **currentDate** | `LocalDate` | Fecha actual de referencia para el cálculo |

Retorna: `void`

Algoritmo:
1. Obtiene la fecha de inicio de la tarea (`startTask`).
2. Calcula la diferencia en días entre `startTask` y `currentDate`.
3. Asigna el resultado al campo `daysOpen` de la `BpmTask`.

---

#### Clase `ServiceGetActualUserImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.application.impl***
***Implements: IServiceGetActualUser***

Implementación del servicio de consulta del usuario autenticado. Obtiene los datos del usuario en sesión consultando el motor XBPM y transforma la respuesta al DTO esperado mediante `MapperGetActualUser`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **mapperGetActualUser** | `MapperGetActualUser` | N/A | Mapper para transformar ResponseGetUser a LoggedUserDto |
| **xbpmApi** | `ServiceApi` | N/A | Cliente de la API del motor BPM externo |

##### Método `getActualUser`

Obtiene y transforma los datos del usuario actualmente autenticado en el sistema BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición Nova con información de sesión |

Retorna: `LoggedUserDto` — DTO con los datos del usuario autenticado.

Algoritmo:
1. Extrae el identificador de usuario desde `novaMetadata`.
2. Invoca el cliente XBPM para obtener el objeto `ResponseGetUser`.
3. Si la respuesta tiene estado distinto de `HttpStatus.OK`, lanza `GenericException`.
4. Transforma el `ResponseGetUser` a `LoggedUserDto` usando `mapperGetActualUser.toDto`.
5. Retorna el DTO resultante.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.domain.entity`

Contiene las entidades de dominio del módulo BPM que representan los conceptos centrales del negocio: oportunidades, tareas, campos, comentarios, historial de estados y representación de tareas BPM externas.

#### Clase `BpmTask`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity***

Representa la estructura de una tarea tal como la devuelve el motor BPM externo (XBPM). Mapea los campos JSON de la respuesta del motor a propiedades tipadas de Java, incluyendo la extracción del identificador de estado desde un mapa genérico.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **id** | `String` | Get/Set | Identificador único de la tarea BPM |
| **taskId** | `String` | Get/Set | Tipo de tarea (`typeId` en JSON) |
| **nameTask** | `String` | Get/Set | Nombre de la tarea (`name` en JSON) |
| **requestId** | `String` | Get/Set | Identificador del negocio asociado (`businessId` en JSON) |
| **startTask** | `OffsetDateTime` | Get/Set | Fecha de creación de la tarea (`createdDate` en JSON) |
| **daysOpen** | `Integer` | Get/Set | Número de días que la tarea lleva abierta |
| **teamsAssigned** | `String[]` | Get/Set | Equipos o propietarios potenciales (`potentialOwnersIds` en JSON) |
| **userId** | `String` | Get/Set | Propietario actual de la tarea (`actualOwnerId` en JSON) |
| **statusMap** | `Map<String, Object>` | Get/Set | Mapa de estado proveniente del motor BPM (`status` en JSON) |

##### Método `getStatusId`

Extrae el identificador de estado desde el mapa de estado (`statusMap`) de la tarea BPM.

Retorna: `String` — valor del identificador de estado contenido en `statusMap`.

Algoritmo:
1. Accede al campo `id` dentro del mapa `statusMap`.
2. Retorna el valor casteado a `String`.

---

#### Clase `BusinessData`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity***
***Extends: AuditedDomain***

Entidad central del módulo BPM que representa una oportunidad de negocio. Agrupa tareas, comentarios, campos dinámicos e historial de estados, y provee métodos para enriquecer su contenido y transformarse a representaciones reducidas o a mapa de variables para el motor BPM.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **businessId** | `String` | Get/Set | Identificador único de la oportunidad (formato BD + secuencia) |
| **status** | `BusinessDataStatus` | Get/Set | Estado actual de la oportunidad |
| **startDate** | `OffsetDateTime` | Get/Set | Fecha de inicio del proceso |
| **endDate** | `OffsetDateTime` | Get/Set | Fecha de finalización (null si en curso) |
| **tasks** | `List<Task>` | Get/Set | Lista de tareas asociadas a la oportunidad |
| **comments** | `List<Comment>` | Get/Set | Lista de comentarios de la oportunidad |
| **fields** | `List<Field>` | Get/Set | Lista de campos dinámicos de la oportunidad |
| **statusHistories** | `List<StatusHistory>` | Get/Set | Historial de cambios de estado |

##### Método `addField`

Agrega un campo dinámico a la oportunidad a partir de un código y un valor.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código identificador del campo |
| **value** | `Object` | Valor del campo (se convierte a String) |

Retorna: `void`

Algoritmo:
1. Crea un nuevo objeto `Field` con el `fieldCode` proporcionado.
2. Convierte `value` a `String` y lo asigna al campo.
3. Agrega el `Field` a la lista `fields`, inicializándola si es necesario.

##### Método `toMap`

Convierte el `BusinessData` en un mapa de clave-valor para su uso como variables en el motor BPM.

Retorna: `Map<String, Object>` — mapa con los campos y valores de la oportunidad.

Algoritmo:
1. Inicializa un `HashMap` vacío.
2. Agrega los campos estándar (businessId, status, startDate, endDate) al mapa.
3. Invoca `addFieldsToMap` para incluir los campos dinámicos.
4. Retorna el mapa resultante.

##### Método `toMinimalBusinessData`

Transforma el `BusinessData` en su representación mínima (`MinimalBusinessData`).

Retorna: `MinimalBusinessData` — objeto con solo el `businessId`.

Algoritmo:
1. Crea una nueva instancia de `MinimalBusinessData`.
2. Asigna el `businessId` actual.
3. Retorna la instancia creada.

---

#### Clase `Comment`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity***
***Extends: AuditedDomain***

Entidad que representa un comentario asociado a una tarea o a una oportunidad de negocio.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **commentId** | `Long` | Get/Set | Identificador único del comentario |
| **authorId** | `String` | Get/Set | Identificador del autor del comentario |
| **commentText** | `String` | Get/Set | Texto del comentario |
| **commentDate** | `OffsetDateTime` | Get/Set | Fecha y hora en que se registró el comentario |

---

#### Clase `Field`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity***
***Extends: AuditedDomain***

Entidad que representa un campo dinámico vinculado a una tarea o a un `BusinessData`. Permite estructuras anidadas de campos mediante la lista `fields`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **fieldId** | `Long` | Get/Set | Identificador único del campo |
| **value** | `String` | Get/Set | Valor almacenado en el campo |
| **fieldCode** | `String` | Get/Set | Código que identifica el tipo de campo |
| **parentFieldId** | `Long` | Get/Set | Identificador del campo padre (para campos anidados) |
| **sectionValue** | `SectionValue` | Get/Set | Metadatos de la sección de plantilla asociada |
| **task** | `MinimalTask` | Get/Set | Referencia mínima a la tarea asociada |
| **businessData** | `MinimalBusinessData` | Get/Set | Referencia mínima al BusinessData asociado |
| **fields** | `List<Field>` | Get/Set | Lista de campos hijos (estructura anidada) |

---

#### Clase `StatusHistory`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity***
***Extends: AuditedDomain***

Entidad que registra cada transición de estado de una oportunidad o tarea, almacenando la fecha del cambio y el estado alcanzado.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **statusHistoryId** | `Long` | Get/Set | Identificador único del registro de historial |
| **dateStatusChange** | `OffsetDateTime` | Get/Set | Fecha y hora en que se produjo el cambio de estado |
| **status** | `String` | Get/Set | Estado alcanzado en esta transición |

---

#### Clase `Task`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity***
***Extends: AuditedDomain***

Entidad que representa una tarea dentro del flujo BPM de una oportunidad de negocio. Incluye referencias al motor BPM externo, al tipo y estado de la tarea, y a las colecciones de comentarios, campos e historial de estados asociados.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **taskId** | `Long` | Get/Set | Identificador único local de la tarea |
| **bpmTaskId** | `String` | Get/Set | Identificador de la tarea en el motor BPM externo |
| **taskType** | `TaskType` | Get/Set | Tipo de tarea según la clasificación del flujo |
| **taskName** | `String` | Get/Set | Nombre descriptivo de la tarea |
| **userId** | `String` | Get/Set | Identificador del usuario asignado a la tarea |
| **template** | `Template` | Get/Set | Plantilla asociada a la tarea |
| **dateStartTask** | `OffsetDateTime` | Get/Set | Fecha y hora de inicio de la tarea |
| **dateEndTask** | `OffsetDateTime` | Get/Set | Fecha y hora de finalización de la tarea |
| **action** | `TaskAction` | Get/Set | Acción ejecutada al completar la tarea |
| **status** | `TaskStatus` | Get/Set | Estado actual de la tarea |
| **comments** | `List<Comment>` | Get/Set | Lista de comentarios asociados a la tarea |
| **fields** | `List<Field>` | Get/Set | Lista de campos dinámicos de la tarea |
| **statusHistories** | `List<StatusHistory>` | Get/Set | Historial de cambios de estado de la tarea |

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase`

Contiene enumeraciones y clases auxiliares del dominio BPM que no tienen representación directa en base de datos, definiendo los valores posibles de estados, acciones, tipos de tarea y constantes de campos extra BPM.

#### Clase `BusinessDataStatus`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase***

Enumeración que define los estados posibles de una oportunidad de negocio (`BusinessData`), indicando para cada uno si representa un estado final del proceso.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **isFinalStatus** | `Boolean` | Get | Indica si el estado representa el fin del proceso |

**Valores del enum:**

| Valor | isFinalStatus | Descripción |
| :---: | :---: | ----- |
| `IN_PROGRESS` | `false` | Proceso en curso |
| `COMPLETED` | `true` | Proceso completado exitosamente |
| `CANCELLED` | `false` | Proceso cancelado |
| `DISMISSED` | `true` | Proceso descartado |
| `EXPIRED` | `true` | Proceso expirado por tiempo |
| `LOST` | `true` | Oportunidad perdida |

---

#### Clase `ExtraBpmFields`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase***

Clase de constantes que centraliza los nombres de los campos extra utilizados al construir el mapa de variables para el motor BPM. El constructor privado impide su instanciación.

**Constantes:**

| Nombre | Valor | Descripción |
| :---: | :---: | ----- |
| `BUSINESS_ID` | `"businessId"` | Clave para el identificador de negocio |
| `START_DATE` | `"indexStartDate"` | Clave para la fecha de inicio |
| `END_DATE` | `"indexEndDate"` | Clave para la fecha de fin |
| `ORIGINATOR` | `"originator"` | Clave para el originador de la oportunidad |
| `IS_DRAFT` | `"isDraft"` | Clave para indicar si es borrador |
| `IS_SALESFORCE` | `"isSalesForce"` | Clave para indicar origen Salesforce |
| `STATUS` | `"status"` | Clave para el estado |
| `ACTION` | `"action"` | Clave para la acción ejecutada |

---

#### Clase `MinimalBusinessData`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase***

Representación mínima de un `BusinessData`, utilizada como referencia ligera en entidades relacionadas para evitar cargas completas del agregado.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **businessId** | `String` | Get/Set | Identificador único de la oportunidad (formato BD + secuencia) |

---

#### Clase `MinimalTask`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase***

Representación mínima de una `Task`, utilizada como referencia ligera en entidades relacionadas para evitar cargas completas del agregado de tarea.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **taskId** | `Long` | Get/Set | Identificador único local de la tarea |

---

#### Clase `TaskAction`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase***

Enumeración que define las acciones que puede ejecutar un usuario al completar una tarea BPM, asociando cada acción con el estado de tarea resultante.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **taskStatus** | `TaskStatus` | Get | Estado de tarea resultante de ejecutar la acción |

**Valores del enum:**

| Valor | taskStatus asociado | Descripción |
| :---: | :---: | ----- |
| `APPROVED` | `COMPLETED` | Tarea aprobada y completada |
| `DISMISS` | `CANCELLED` | Tarea descartada y cancelada |
| `REVIEW` | `REVIEW` | Tarea enviada a revisión |
| `PENDING` | `PENDING` | Tarea marcada como pendiente |

---

#### Clase `TaskStatus`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase***

Enumeración que define los estados posibles de una tarea BPM a lo largo de su ciclo de vida.

**Valores del enum:**

| Valor | Descripción |
| :---: | ----- |
| `EXPIRED` | Tarea expirada por tiempo |

> **Nota:** según el código fuente disponible, solo se declara explícitamente el valor `EXPIRED`. Los demás valores (`COMPLETED`, `CANCELLED`, `REVIEW`, `PENDING`) son referenciados desde `TaskAction` pero no están visibles en el fragmento de código proporcionado.

---

#### Clase `TaskType`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.domain.entity.nodatabase***

Enumeración que clasifica los tipos de tarea existentes en el flujo BPM. En el código fuente proporcionado no se declaran valores explícitos; su contenido se define en la implementación completa del proyecto.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.listener`

Contiene los listeners REST que implementan los contratos de la API generada, actuando como punto de entrada HTTP para las operaciones del módulo BPM y delegando la lógica de negocio en los servicios de aplicación.

#### Clase `ListenerApiBpm`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.listener***
***Implements: IRestListenerApibpm***

Listener REST que expone todos los endpoints de la API BPM. Recibe las peticiones HTTP, transforma los DTOs de entrada a entidades de dominio mediante mappers, delega en los servicios correspondientes y gestiona los errores construyendo respuestas de error estándar con `GenericApiErrorBuilder`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **service** | `IServiceApiBpm` | N/A | Servicio principal de operaciones BPM |
| **businessDataService** | `IBusinessDataService` | N/A | Servicio de datos de negocio |
| **userService** | `IServiceGetActualUser` | N/A | Servicio de consulta del usuario autenticado |
| **mapperTaskDto** | `MapperTaskDto` | N/A | Mapper entre Task y TaskDto |
| **mapperBusinessDataDto** | `MapperBusinessDataDto` | N/A | Mapper entre BusinessData y BusinessDataDto |
| **mapperCreateCommentDto** | `MapperCreateCommentDto` | N/A | Mapper entre Comment y CreateCommentDto |
| **mapperUpdateTaskDto** | `MapperUpdateTaskDto` | N/A | Mapper entre Task y UpdateTaskDto |
| **mapperCreateBusinessDataDto** | `MapperCreateBusinessDataDto` | N/A | Mapper entre BusinessData y CreateBusinessDataDto |

##### Método `assignTask`

Recibe la petición de asignación de una tarea BPM y delega en el servicio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **taskId** | `String` | Identificador de la tarea a asignar |

Retorna: `void`

Algoritmo:
1. Invoca `service.assignTask(taskId)`.
2. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `releaseTask`

Recibe la petición de liberación de una tarea BPM y delega en el servicio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **bpmTaskId** | `String` | Identificador de la tarea a liberar |

Retorna: `void`

Algoritmo:
1. Invoca `service.releaseTask(bpmTaskId)`.
2. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `getActualUser`

Recupera los datos del usuario autenticado y los retorna como DTO.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición con información de sesión |

Retorna: `LoggedUserDto` — DTO con los datos del usuario autenticado.

Algoritmo:
1. Invoca `userService.getActualUser(novaMetadata)`.
2. Retorna el `LoggedUserDto` resultante.
3. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `addComment`

Agrega un comentario a una tarea BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **commentDto** | `CreateCommentDto` | DTO con los datos del comentario |
| **bpmTaskId** | `String` | Identificador de la tarea destino |

Retorna: `void`

Algoritmo:
1. Transforma `commentDto` a entidad `Comment` usando `mapperCreateCommentDto`.
2. Invoca `businessDataService.addTaskComment(comment, bpmTaskId)`.
3. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `getOpportunity`

Recupera los datos de una oportunidad de negocio por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **opportunityId** | `String` | Identificador de la oportunidad |

Retorna: `BusinessDataDto` — DTO con los datos de la oportunidad.

Algoritmo:
1. Invoca `businessDataService.findById(opportunityId)`.
2. Transforma el `BusinessData` obtenido a `BusinessDataDto` usando `mapperBusinessDataDto`.
3. Retorna el DTO resultante.

##### Método `getTask`

Recupera los datos de una tarea BPM por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **bpmTaskId** | `String` | Identificador de la tarea |

Retorna: `TaskDto` — DTO con los datos de la tarea.

Algoritmo:
1. Invoca `businessDataService.findTaskByBpmId(bpmTaskId)`.
2. Transforma la `Task` obtenida a `TaskDto` usando `mapperTaskDto`.
3. Retorna el DTO resultante.

##### Método `updateTask`

Actualiza los datos de una tarea BPM existente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **updateTaskDto** | `UpdateTaskDto` | DTO con los nuevos datos de la tarea |
| **bpmTaskId** | `String` | Identificador de la tarea a actualizar |

Retorna: `void`

Algoritmo:
1. Transforma `updateTaskDto` a entidad `Task` usando `mapperUpdateTaskDto`.
2. Invoca `businessDataService.updateTask(task, bpmTaskId)`.
3. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `setTaskStatus`

Actualiza el estado de una tarea BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **status** | `SetStatusDto` | DTO con el nuevo estado |
| **bpmTaskId** | `String` | Identificador de la tarea |

Retorna: `void`

Algoritmo:
1. Extrae el valor de estado del `SetStatusDto`.
2. Invoca `businessDataService.setTaskStatus(bpmTaskId, status)`.
3. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `sendSignalEvent`

Envía un evento de señal al motor BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **createEventDto** | `CreateEventDto` | DTO con la información del evento |

Retorna: `void`

Algoritmo:
1. Invoca `service.sendSignalEvent(createEventDto)`.
2. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `createOpportunity`

Crea una nueva oportunidad de negocio en el motor BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **businessDataDto** | `CreateBusinessDataDto` | DTO con los datos de la nueva oportunidad |

Retorna: `void`

Algoritmo:
1. Transforma `businessDataDto` a entidad `BusinessData` usando `mapperCreateBusinessDataDto`.
2. Invoca `service.createOpportunityEvent(businessData)`.
3. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

##### Método `completeTask`

Completa una tarea BPM aplicando la acción definida en el DTO.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **updateTaskDto** | `UpdateTaskDto` | DTO con los datos y acción de la tarea |
| **bpmTaskId** | `String` | Identificador de la tarea a completar |

Retorna: `void`

Algoritmo:
1. Transforma `updateTaskDto` a entidad `Task` usando `mapperUpdateTaskDto`.
2. Invoca `service.completeTask(task, bpmTaskId)`.
3. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

---

#### Clase `ListenerApiBpmStatus`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.listener***
***Implements: IRestListenerApibpmstatus***

Listener REST dedicado exclusivamente a las operaciones de cambio de estado expuestas por la API `apibpmstatus`. Actúa como punto de entrada para actualizaciones de estado de tareas iniciadas desde sistemas externos.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **businessDataService** | `IBusinessDataService` | N/A | Servicio de datos de negocio para actualización de estados |

##### Método `setTaskStatus`

Actualiza el estado de una tarea BPM a partir de una petición externa vía la API de estado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición |
| **status** | `SetStatusDto` | DTO con el nuevo estado a asignar |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `void`

Algoritmo:
1. Extrae el valor de estado del `SetStatusDto`.
2. Invoca `businessDataService.setTaskStatus(bpmTaskId, status)`.
3. Si se lanza `GenericException`, construye y lanza la excepción de API correspondiente.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper`

Contiene las interfaces MapStruct que realizan la conversión bidireccional entre entidades de dominio y DTOs de la API REST del módulo BPM, gestionando también mapeos de campos anidados y transformaciones de enumeraciones.

#### Clase `MapperBusinessDataDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<BusinessData, BusinessDataDto>***

Interfaz MapStruct que realiza la conversión entre `BusinessData` y `BusinessDataDto`, utilizando `DateMapper` para la transformación de fechas.

---

#### Clase `MapperChildFieldDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<Field, ChildFieldDto>***

Interfaz MapStruct para la conversión entre `Field` y `ChildFieldDto`. Mapea el campo `sectionValue.fieldCode` al atributo `fieldCode` del DTO mediante una anotación `@Mapping` explícita.

##### Método `toDto`

Convierte una entidad `Field` a su DTO hijo (`ChildFieldDto`), extrayendo el código de campo desde la sección de valor.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Entidad de campo a convertir |

Retorna: `ChildFieldDto` — DTO hijo con el `fieldCode` extraído de `sectionValue`.

---

#### Clase `MapperCommentDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<Comment, CommentDto>***

Interfaz MapStruct que realiza la conversión entre `Comment` y `CommentDto`, utilizando `DateMapper` para la transformación de campos de tipo fecha.

---

#### Clase `MapperCreateBusinessDataDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<BusinessData, CreateBusinessDataDto>***

Interfaz MapStruct para la conversión entre `BusinessData` y `CreateBusinessDataDto`, utilizada al transformar el DTO de creación recibido en el listener a entidad de dominio.

---

#### Clase `MapperCreateCommentDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<Comment, CreateCommentDto>***

Interfaz MapStruct que realiza la conversión entre `Comment` y `CreateCommentDto`, utilizando `DateMapper` para los campos de fecha.

---

#### Clase `MapperFieldDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<Field, FieldDto>***

Interfaz MapStruct para la conversión entre `Field` y `FieldDto`. Utiliza `MapperMidFieldDto` para los campos intermedios anidados y mapea `sectionValue.fieldCode` al atributo `fieldCode` del DTO.

##### Método `toDto`

Convierte una entidad `Field` a su DTO de representación completa, incluyendo niveles intermedios.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Entidad de campo a convertir |

Retorna: `FieldDto` — DTO con el `fieldCode` extraído de `sectionValue` y los campos hijos mapeados.

---

#### Clase `MapperGetActualUser`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<ResponseGetUser, LoggedUserDto>***

Interfaz MapStruct que realiza la conversión bidireccional entre `ResponseGetUser` (respuesta del motor XBPM) y `LoggedUserDto` (DTO de la API), adaptando los nombres de campos entre los dos modelos.

##### Método `toDto`

Convierte la respuesta del motor BPM al DTO de usuario autenticado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **response** | `ResponseGetUser` | Respuesta del motor XBPM |

Retorna: `LoggedUserDto` — DTO con los campos mapeados (`user`→`id`, `nombre`→`name`, `apellido1`→`surname1`, `apellido2`→`surname2`, `groups`→`groups`).

##### Método `toModel`

Convierte el DTO de usuario autenticado a la representación del motor XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **loggedUser** | `LoggedUserDto` | DTO del usuario autenticado |

Retorna: `ResponseGetUser` — objeto de respuesta XBPM con los campos mapeados inversamente (`id`→`user`, `name`→`nombre`, `surname1`→`apellido1`, `surname2`→`apellido2`, `groups`→`groups`).

---

#### Clase `MapperMidFieldDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<Field, MidFieldDto>***

Interfaz MapStruct para la conversión entre `Field` y `MidFieldDto`, representando el nivel intermedio de la jerarquía de campos. Utiliza `MapperChildFieldDto` para los campos hijos y mapea `sectionValue.fieldCode` al atributo `fieldCode`.

##### Método `toDto`

Convierte una entidad `Field` al DTO de nivel intermedio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Entidad de campo a convertir |

Retorna: `MidFieldDto` — DTO intermedio con el `fieldCode` extraído de `sectionValue` y los campos hijos mapeados.

---

#### Clase `MapperStatusHistoryDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<StatusHistory, StatusHistoryDto>***

Interfaz MapStruct que realiza la conversión entre `StatusHistory` y `StatusHistoryDto`, utilizando `DateMapper` para la transformación de campos de fecha.

---

#### Clase `MapperTaskDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<Task, TaskDto>***

Interfaz MapStruct que realiza la conversión entre `Task` y `TaskDto`, utilizando `DateMapper` para los campos de fecha.

---

#### Clase `MapperUpdateTaskDto`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.mapper***
***Implements: GenericDtoMapper<Task, UpdateTaskDto>***

Interfaz MapStruct para la conversión entre `Task` y `UpdateTaskDto`. Implementa métodos `default` para transformar el campo `action` (String) a los enums `TaskStatus` y `TaskAction` con validación, lanzando `GenericException` si el valor no es reconocido.

##### Método `toModel`

Convierte el DTO de actualización de tarea a entidad de dominio, derivando `status` y `action` desde el campo `action` del DTO.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **updateTaskDto** | `UpdateTaskDto` | DTO con los datos de actualización de tarea |

Retorna: `Task` — entidad con `status` y `action` asignados mediante las conversiones nombradas.

Algoritmo:
1. Mapea todos los campos estándar del DTO a la entidad.
2. Invoca `toTaskStatus(action)` para derivar el `TaskStatus` y lo asigna al campo `status`.
3. Invoca `toTaskAction(action)` para derivar el `TaskAction` y lo asigna al campo `action`.

##### Método `toTaskStatus`

Convierte un `String` de acción al `TaskStatus` correspondiente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **action** | `String` | Valor de acción en formato texto |

Retorna: `TaskStatus` — enum de estado de tarea correspondiente.

Algoritmo:
1. Busca en `TaskAction` el valor cuyo nombre coincida con `action`.
2. Si existe, retorna su `taskStatus` asociado.
3. Si no existe, lanza `GenericException` con código `HttpStatus` de error.

##### Método `toTaskAction`

Convierte un `String` de acción al enum `TaskAction` correspondiente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **action** | `String` | Valor de acción en formato texto |

Retorna: `TaskAction` — enum de acción de tarea correspondiente.

Algoritmo:
1. Intenta obtener el valor del enum `TaskAction` cuyo nombre coincida con `action`.
2. Si no existe, lanza `GenericException` con código `HttpStatus` de error.

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository`

Contiene las interfaces de repositorio del dominio BPM que definen los contratos de acceso y persistencia para las entidades principales del módulo.

#### Interfaz `IBusinessDataRepository`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository***

Define el contrato de persistencia para la entidad `BusinessData`. Declara operaciones de creación, actualización parcial, eliminación y consulta, incluyendo búsquedas por identificador de tarea BPM.

##### Método `saveBusinessData`

Persiste un nuevo registro de `BusinessData` y retorna su identificador generado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Datos del negocio a persistir |

Retorna: `String` — identificador del `BusinessData` persistido.

##### Método `saveBusinessDataAndFlush`

Persiste un `BusinessData` y fuerza la sincronización inmediata con la base de datos.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Datos del negocio a persistir y volcar |

Retorna: `BusinessData` — entidad persistida con el estado actualizado tras el flush.

##### Método `deleteBusinessData`

Elimina el registro de `BusinessData` correspondiente al identificador indicado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del `BusinessData` a eliminar |

Retorna: `void`.

##### Método `findById`

Recupera un `BusinessData` por su identificador único.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del `BusinessData` |

Retorna: `BusinessData` — entidad encontrada, o lanza `EntityNotFoundException` si no existe.

##### Método `allBusinessData`

Recupera la lista completa de registros `BusinessData` disponibles.

Retorna: `List<BusinessData>` — colección de todos los datos de negocio.

##### Método `updateBusinessData`

Actualiza de forma parcial un `BusinessData` existente, aplicando únicamente los campos no nulos del objeto recibido.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Datos a actualizar (solo campos no nulos) |
| **businessId** | `String` | Identificador del `BusinessData` a modificar |

Retorna: `BusinessData` — entidad con los datos actualizados, o lanza `GenericException` ante un error.

##### Método `findByBpmTaskId`

Localiza el `BusinessData` asociado a una tarea BPM concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea BPM |

Retorna: `BusinessData` — entidad encontrada, o lanza `EntityNotFoundException` si no existe.

##### Método `findByBpmTaskIdFlushing`

Localiza el `BusinessData` asociado a una tarea BPM forzando la sincronización del contexto de persistencia antes de la consulta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea BPM |

Retorna: `BusinessData` — entidad encontrada tras el flush, o lanza `EntityNotFoundException` si no existe.

---

#### Interfaz `ICommentRepository`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository***

Define el contrato de acceso a datos para la entidad `Comment`, incluyendo operaciones de guardado asociado a tareas BPM o a oportunidades de negocio.

##### Método `saveComment`

Persiste un comentario genérico sin asociación explícita.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a persistir |

Retorna: `Comment` — comentario persistido.

##### Método `deleteComment`

Elimina un comentario por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario a eliminar |

Retorna: `void`.

##### Método `findById`

Recupera un comentario por su identificador único.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario |

Retorna: `Comment` — comentario encontrado, o lanza `EntityNotFoundException` si no existe.

##### Método `allComment`

Recupera todos los comentarios registrados en el sistema.

Retorna: `List<Comment>` — colección completa de comentarios.

##### Método `saveTaskComment`

Persiste un comentario asociándolo a una tarea BPM identificada por su `bpmTaskId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a persistir |
| **bpmTaskId** | `String` | Identificador de la tarea BPM destino |

Retorna: `void`. Lanza `EntityNotFoundException` si la tarea no existe.

##### Método `saveBusinessDataComment`

Persiste un comentario asociándolo a un `BusinessData` identificado por el ID de oportunidad.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a persistir |
| **opportunityId** | `String` | Identificador del `BusinessData` destino |

Retorna: `void`. Lanza `EntityNotFoundException` si el `BusinessData` no existe.

---

#### Interfaz `IFieldRepository`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository***

Define el contrato de acceso a datos para la entidad `Field`, cubriendo persistencia individual, en lista, asociación a tareas y búsquedas por código de campo.

##### Método `saveField(Field)`

Persiste un único campo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo a persistir |

Retorna: `Field` — campo persistido.

##### Método `saveFieldValue`

Actualiza el valor de un campo existente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo con el nuevo valor |

Retorna: `Field` — campo actualizado, o lanza `EntityNotFoundException` si no se encuentra.

##### Método `saveField(List<Field>)`

Persiste una lista de campos de forma masiva.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `List<Field>` | Colección de campos a persistir |

Retorna: `List<Field>` — colección de campos persistidos.

##### Método `saveFieldOnTask`

Persiste una lista de campos asociándolos a una tarea concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `List<Field>` | Colección de campos a persistir |
| **task** | `Task` | Tarea a la que se asocian los campos |

Retorna: `List<Field>` — campos persistidos vinculados a la tarea.

##### Método `deleteField`

Elimina un campo por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del campo a eliminar |

Retorna: `void`.

##### Método `findById`

Recupera un campo por su identificador único.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del campo |

Retorna: `Field` — campo encontrado, o lanza `EntityNotFoundException` si no existe.

##### Método `findAllFieldByBusinessId`

Recupera todos los campos asociados a un `BusinessData` concreto.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del `BusinessData` |

Retorna: `List<Field>` — colección de campos del negocio indicado.

##### Método `findByFieldCodeAndBusinessData`

Busca un campo por su código y el identificador del `BusinessData` al que pertenece.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código identificador del campo |
| **businessId** | `String` | Identificador del `BusinessData` |

Retorna: `Optional<Field>` — campo encontrado o vacío; lanza `EntityNotFoundException` ante error de acceso.

##### Método `findByFieldCodeAndTaskId`

Busca un campo por su código dentro de un conjunto de tareas.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código identificador del campo |
| **taskIds** | `List<Long>` | Lista de identificadores de tareas donde buscar |

Retorna: `Optional<Field>` — campo encontrado o vacío; lanza `EntityNotFoundException` ante error de acceso.

##### Método `allField`

Recupera todos los campos registrados en el sistema.

Retorna: `List<Field>` — colección completa de campos.

---

#### Interfaz `IStatusHistoryRepository`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository***

Define el contrato de acceso a datos para el historial de estados, permitiendo su registro tanto de forma genérica como asociado a entidades `BusinessData` o `Task`.

##### Método `saveStatusHistory`

Persiste un registro de historial de estado de forma genérica.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **statusHistory** | `StatusHistory` | Registro de historial a persistir |

Retorna: `StatusHistory` — registro persistido.

##### Método `saveBusinessDataStatusHistory`

Persiste un historial de estado asociándolo a un `BusinessData` concreto.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **statusHistory** | `StatusHistory` | Registro de historial a persistir |
| **businessDataId** | `String` | Identificador del `BusinessData` destino |

Retorna: `StatusHistory` — registro persistido; lanza `EntityNotFoundException` si el `BusinessData` no existe.

##### Método `saveTaskStatusHistory`

Persiste un historial de estado asociándolo a una tarea BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **statusHistory** | `StatusHistory` | Registro de historial a persistir |
| **bpmTaskId** | `String` | Identificador de la tarea BPM destino |

Retorna: `StatusHistory` — registro persistido; lanza `EntityNotFoundException` si la tarea no existe.

##### Método `deleteStatusHistory`

Elimina un registro de historial de estado por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del registro a eliminar |

Retorna: `void`.

##### Método `findById`

Recupera un registro de historial de estado por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del registro |

Retorna: `StatusHistory` — registro encontrado, o lanza `EntityNotFoundException` si no existe.

##### Método `allStatusHistory`

Recupera todos los registros de historial de estado.

Retorna: `List<StatusHistory>` — colección completa de historiales.

---

#### Interfaz `ITaskRepository`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository***

Define el contrato de acceso a datos para la entidad `Task`, incluyendo búsqueda por identificador BPM, actualización parcial y desasignación de usuario.

##### Método `saveTask`

Persiste una tarea.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Tarea a persistir |

Retorna: `Task` — tarea persistida.

##### Método `deleteTask`

Elimina una tarea por su identificador interno.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador interno de la tarea |

Retorna: `void`.

##### Método `findById`

Recupera una tarea por su identificador interno.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador interno de la tarea |

Retorna: `Task` — tarea encontrada, o lanza `EntityNotFoundException` si no existe.

##### Método `findByBpmTaskId`

Recupera una tarea por su identificador en el motor BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea en el sistema BPM |

Retorna: `Task` — tarea encontrada, o lanza `EntityNotFoundException` si no existe.

##### Método `allTask`

Recupera todas las tareas registradas.

Retorna: `List<Task>` — colección completa de tareas.

##### Método `updateTask`

Actualiza de forma parcial una tarea existente, aplicando únicamente los campos no nulos del objeto recibido.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Datos a actualizar (solo campos no nulos) |
| **bpmTaskId** | `String` | Identificador BPM de la tarea a modificar |

Retorna: `Task` — tarea actualizada, o lanza `GenericException` ante un error.

##### Método `removeUser`

Desvincula al usuario asignado de la tarea identificada por su `bpmTaskId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskid** | `String` | Identificador BPM de la tarea |

Retorna: `void`. Lanza `EntityNotFoundException` si la tarea no existe.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.impl`

Contiene las implementaciones concretas de los repositorios del módulo BPM, coordinando el acceso JPA, la conversión de entidades mediante mappers y la gestión de caché.

#### Clase `BusinessDataRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.impl***
***Implements: IBusinessDataRepository***

Implementación del repositorio de `BusinessData`. Orquesta la persistencia a través de `BusinessDataRepositoryJpa` y `FieldRepositoryJpa`, aplica invalidación de caché sobre el listado global y delega la conversión entre modelo de dominio y entidad JPA en `BusinessDataMapper`. La actualización parcial se apoya en `ObjectUpdater` para copiar únicamente los campos no nulos.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **fieldRepositoryJpa** | `FieldRepositoryJpa` | N/A | Repositorio JPA de campos |
| **businessDataRepositoryJpa** | `BusinessDataRepositoryJpa` | N/A | Repositorio JPA de `BusinessData` |
| **objectUpdater** | `ObjectUpdater` | N/A | Utilidad para actualización parcial de objetos |
| **entityManager** | `EntityManager` | N/A | Gestor de persistencia JPA para operaciones de flush |
| **businessDataMapper** | `BusinessDataMapper` | N/A | Mapper entre `BusinessData` y `BusinessDataJpa` |

##### Método `saveBusinessData`

Convierte el modelo de dominio a entidad JPA, lo persiste e invalida la caché del listado global, retornando el identificador generado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Datos del negocio a persistir |

Retorna: `String` — identificador del `BusinessData` persistido.

Algoritmo:
1. Invoca al método interno `saveInternalBusiness` para realizar la persistencia.
2. Invalida la entrada de caché `SEARCH_ALL_BUSINESS_DATA_CACHE` mediante `@CacheEvict`.
3. Retorna el identificador generado.

##### Método `saveBusinessDataAndFlush`

Persiste el `BusinessData` y fuerza la sincronización inmediata con la base de datos.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Datos del negocio a persistir y volcar |

Retorna: `BusinessData` — entidad de dominio resultante tras el flush.

Algoritmo:
1. Invoca `saveInternalBusiness` para convertir y guardar la entidad.
2. Llama a `entityManager.flush()` para sincronizar el contexto de persistencia.
3. Invalida la caché `SEARCH_ALL_BUSINESS_DATA_CACHE`.
4. Convierte la entidad JPA resultante al modelo de dominio y la retorna.

##### Método `saveInternalBusiness`

Método privado que centraliza la lógica de conversión y guardado de un `BusinessData`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Datos del negocio a persistir |

Retorna: `String` — identificador del registro guardado.

Algoritmo:
1. Convierte `BusinessData` a `BusinessDataJpa` usando `businessDataMapper.toEntity`.
2. Persiste la entidad mediante `businessDataRepositoryJpa.save`.
3. Retorna el `businessId` de la entidad guardada.

##### Método `deleteBusinessData`

Elimina el `BusinessData` correspondiente al identificador indicado e invalida la caché.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del `BusinessData` a eliminar |

Retorna: `void`.

Algoritmo:
1. Invoca `businessDataRepositoryJpa.deleteById(id)`.
2. Invalida la caché `SEARCH_ALL_BUSINESS_DATA_CACHE` mediante `@CacheEvict`.

##### Método `findById`

Busca y retorna un `BusinessData` por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del `BusinessData` |

Retorna: `BusinessData` — modelo de dominio encontrado.

Algoritmo:
1. Consulta `businessDataRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Convierte la entidad JPA a modelo de dominio mediante `businessDataMapper.toModel` y la retorna.

##### Método `allBusinessData`

Recupera todos los registros de `BusinessData`, con resultado almacenado en caché.

Retorna: `List<BusinessData>` — colección completa de modelos de dominio.

Algoritmo:
1. Consulta `businessDataRepositoryJpa.findAll()`.
2. Mapea cada `BusinessDataJpa` a `BusinessData` mediante `businessDataMapper.toModel`.
3. Retorna la lista resultante (resultado cacheado con `@Cacheable`).

##### Método `updateBusinessData`

Actualiza parcialmente un `BusinessData` existente con los campos no nulos del objeto recibido.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Objeto con los campos a actualizar |
| **businessId** | `String` | Identificador del `BusinessData` a modificar |

Retorna: `BusinessData` — entidad actualizada; lanza `GenericException` ante error.

Algoritmo:
1. Recupera la entidad JPA existente mediante `findById(businessId)`.
2. Convierte `businessData` a `BusinessDataJpa`.
3. Aplica `objectUpdater` para copiar solo los campos no nulos sobre la entidad existente.
4. Persiste la entidad actualizada con `businessDataRepositoryJpa.save`.
5. Invalida la caché `SEARCH_ALL_BUSINESS_DATA_CACHE`.
6. Convierte y retorna el modelo de dominio actualizado.

##### Método `findByBpmTaskId`

Localiza el `BusinessData` asociado a una tarea BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea BPM |

Retorna: `BusinessData` — modelo encontrado; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Invoca `businessDataRepositoryJpa.findByBpmTaskId(bpmTaskId)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Mapea y retorna el modelo de dominio.

##### Método `findByBpmTaskIdFlushing`

Localiza el `BusinessData` de una tarea BPM forzando un flush previo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea BPM |

Retorna: `BusinessData` — modelo encontrado tras el flush; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Llama a `entityManager.flush()` para sincronizar el contexto de persistencia.
2. Invoca `businessDataRepositoryJpa.findByBpmTaskId(bpmTaskId)`.
3. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
4. Mapea y retorna el modelo de dominio.

---

#### Clase `CommentRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.impl***
***Implements: ICommentRepository***

Implementación del repositorio de comentarios. Coordina el acceso a `CommentRepositoryJpa`, `BusinessDataRepositoryJpa` y `TaskRepositoryJpa` para asociar comentarios a sus entidades padre, delegando la conversión en `CommentMapper`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **commentRepositoryJpa** | `CommentRepositoryJpa` | N/A | Repositorio JPA de comentarios |
| **businessDataRepositoryJpa** | `BusinessDataRepositoryJpa` | N/A | Repositorio JPA de `BusinessData` |
| **taskRepositoryJpa** | `TaskRepositoryJpa` | N/A | Repositorio JPA de tareas |
| **commentMapper** | `CommentMapper` | N/A | Mapper entre `Comment` y `CommentJpa` |

##### Método `saveComment`

Persiste un comentario genérico sin asociación a ninguna entidad padre.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a persistir |

Retorna: `Comment` — comentario persistido.

Algoritmo:
1. Convierte `comment` a `CommentJpa` mediante `commentMapper.toEntity`.
2. Persiste mediante `commentRepositoryJpa.save`.
3. Convierte el resultado a modelo de dominio y lo retorna.

##### Método `deleteComment`

Elimina el comentario identificado por su ID.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **commentId** | `Long` | Identificador del comentario a eliminar |

Retorna: `void`.

Algoritmo:
1. Invoca `commentRepositoryJpa.deleteById(commentId)`.

##### Método `allComment`

Recupera todos los comentarios del sistema.

Retorna: `List<Comment>` — colección completa de comentarios mapeados al modelo de dominio.

Algoritmo:
1. Consulta `commentRepositoryJpa.findAll()`.
2. Mapea cada `CommentJpa` a `Comment` mediante `commentMapper.toModel`.
3. Retorna la lista resultante.

##### Método `findById`

Recupera un comentario por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del comentario |

Retorna: `Comment` — comentario encontrado; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Consulta `commentRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Mapea y retorna el modelo de dominio.

##### Método `saveTaskComment`

Persiste un comentario asociándolo a la tarea BPM indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a persistir |
| **bpmTaskId** | `String` | Identificador de la tarea BPM destino |

Retorna: `void`. Lanza `EntityNotFoundException` si la tarea no existe.

Algoritmo:
1. Recupera la `TaskJpa` mediante `taskRepositoryJpa.findByBpmTaskId(bpmTaskId)`; si no existe, lanza `EntityNotFoundException`.
2. Convierte `comment` a `CommentJpa` mediante `commentMapper.toEntity`.
3. Asigna la tarea recuperada al campo `task` de la entidad `CommentJpa`.
4. Persiste mediante `commentRepositoryJpa.save`.

##### Método `saveBusinessDataComment`

Persiste un comentario asociándolo al `BusinessData` identificado por `opportunityId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Comentario a persistir |
| **opportunityId** | `String` | Identificador del `BusinessData` destino |

Retorna: `void`. Lanza `EntityNotFoundException` si el `BusinessData` no existe.

Algoritmo:
1. Recupera la `BusinessDataJpa` mediante `businessDataRepositoryJpa.findById(opportunityId)`; si no existe, lanza `EntityNotFoundException`.
2. Convierte `comment` a `CommentJpa` mediante `commentMapper.toEntity`.
3. Asigna el `BusinessData` recuperado al campo `businessData` de la entidad `CommentJpa`.
4. Persiste mediante `commentRepositoryJpa.save`.

---

#### Clase `FieldRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.impl***
***Implements: IFieldRepository***

Implementación del repositorio de campos. Gestiona la persistencia individual y masiva de `Field`, la asociación con tareas y la eliminación recursiva de campos con hijos, apoyándose en `FieldRepositoryJpa`, `FieldMapper`, `TaskMapper` y `DatabaseUtils`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **fieldRepositoryJpa** | `FieldRepositoryJpa` | N/A | Repositorio JPA de campos |
| **databaseUtils** | `DatabaseUtils` | N/A | Utilidades de acceso a base de datos |
| **fieldMapper** | `FieldMapper` | N/A | Mapper entre `Field` y `FieldJpa` |
| **taskMapper** | `TaskMapper` | N/A | Mapper entre `Task` y `TaskJpa` |

##### Método `saveField(Field)`

Persiste un campo individual.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo a persistir |

Retorna: `Field` — campo persistido.

Algoritmo:
1. Convierte `field` a `FieldJpa` mediante `fieldMapper.toEntity`.
2. Persiste con `fieldRepositoryJpa.save`.
3. Convierte y retorna el modelo de dominio.

##### Método `saveFieldValue`

Actualiza el valor de un campo existente localizándolo previamente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `Field` | Campo con el valor actualizado |

Retorna: `Field` — campo actualizado; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Recupera la entidad `FieldJpa` existente por `field.getFieldId()`; si no existe, lanza `EntityNotFoundException`.
2. Actualiza el valor en la entidad JPA recuperada.
3. Persiste con `fieldRepositoryJpa.save`.
4. Convierte y retorna el modelo de dominio.

##### Método `saveField(List<Field>)`

Persiste una lista de campos de forma masiva.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `List<Field>` | Colección de campos a persistir |

Retorna: `List<Field>` — colección de campos persistidos.

Algoritmo:
1. Convierte cada `Field` a `FieldJpa` mediante `fieldMapper.toEntity`.
2. Invoca `internalSave` para persistir la lista de entidades JPA.
3. Convierte cada `FieldJpa` resultante al modelo de dominio y retorna la lista.

##### Método `internalSave`

Método público auxiliar que persiste una lista de entidades `FieldJpa` directamente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `List<FieldJpa>` | Colección de entidades JPA a persistir |

Retorna: `List<FieldJpa>` — entidades persistidas.

Algoritmo:
1. Invoca `fieldRepositoryJpa.saveAll(field)`.
2. Retorna la colección guardada.

##### Método `internalDelete`

Método público auxiliar que elimina una lista de entidades `FieldJpa` directamente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `List<FieldJpa>` | Colección de entidades JPA a eliminar |

Retorna: `List<FieldJpa>` — lista vacía o la colección procesada tras la eliminación.

Algoritmo:
1. Invoca `fieldRepositoryJpa.deleteAll(field)`.
2. Retorna la colección indicando los elementos eliminados.

##### Método `saveFieldOnTask`

Persiste una lista de campos vinculándolos a la tarea indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **field** | `List<Field>` | Colección de campos a persistir |
| **task** | `Task` | Tarea a la que se asociarán los campos |

Retorna: `List<Field>` — campos persistidos asociados a la tarea.

Algoritmo:
1. Convierte `task` a `TaskJpa` mediante `taskMapper.toEntity`.
2. Convierte cada `Field` a `FieldJpa` y asigna la `TaskJpa` como entidad padre.
3. Persiste la lista mediante `internalSave`.
4. Convierte cada resultado al modelo de dominio y retorna la lista.

##### Método `deleteField`

Elimina un campo y todos sus hijos de forma recursiva.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del campo raíz a eliminar |

Retorna: `void`.

Algoritmo:
1. Recupera la entidad `FieldJpa` por `id`.
2. Invoca `deleteAllWithChild` pasando la lista que contiene esa entidad.

##### Método `deleteAllWithChild`

Método privado que elimina recursivamente una lista de campos y sus descendientes.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fields** | `List<FieldJpa>` | Lista de entidades raíz a eliminar con sus hijos |

Retorna: `void`.

Algoritmo:
1. Para cada `FieldJpa` en la lista, si tiene campos hijo (`fields` no vacío), invoca recursivamente `deleteAllWithChild` sobre ellos.
2. Elimina cada `FieldJpa` mediante `fieldRepositoryJpa.delete`.

##### Método `findById`

Recupera un campo por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del campo |

Retorna: `Field` — campo encontrado; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Consulta `fieldRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Mapea y retorna el modelo de dominio.

##### Método `findByFieldCodeAndBusinessData`

Busca un campo por código y `BusinessData` asociado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo |
| **businessId** | `String` | Identificador del `BusinessData` |

Retorna: `Optional<Field>` — campo encontrado o vacío; lanza `EntityNotFoundException` ante error.

Algoritmo:
1. Invoca `fieldRepositoryJpa.findByFieldCodeAndBusinessData(fieldCode, businessId)`.
2. Si el resultado tiene valor, mapea la `FieldJpa` a `Field` mediante `fieldMapper.toModel`.
3. Retorna el `Optional` resultante.

##### Método `findByFieldCodeAndTaskId`

Busca un campo por código dentro de un conjunto de tareas.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo |
| **taskIds** | `List<Long>` | Lista de identificadores de tareas |

Retorna: `Optional<Field>` — campo encontrado o vacío; lanza `EntityNotFoundException` ante error.

Algoritmo:
1. Invoca `fieldRepositoryJpa.findByFieldCodeAndTaskId(fieldCode, taskIds)`.
2. Si el resultado tiene valor, mapea la `FieldJpa` a `Field`.
3. Retorna el `Optional` resultante.

##### Método `allField`

Recupera todos los campos del sistema.

Retorna: `List<Field>` — colección completa de campos.

Algoritmo:
1. Consulta `fieldRepositoryJpa.findAll()`.
2. Mapea cada `FieldJpa` a `Field` y retorna la lista.

##### Método `findAllFieldByBusinessId`

Recupera todos los campos de un `BusinessData` concreto.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del `BusinessData` |

Retorna: `List<Field>` — colección de campos del negocio indicado.

Algoritmo:
1. Invoca `fieldRepositoryJpa.findAllByBusinessData_BusinessId(id)`.
2. Mapea cada `FieldJpa` a `Field` y retorna la lista.

---

#### Clase `StatusHistoryRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.impl***
***Implements: IStatusHistoryRepository***

Implementación del repositorio de historial de estados. Coordina la persistencia de registros `StatusHistory` y su asociación con `BusinessData` o `Task`, delegando la conversión en `StatusHistoryMapper`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **statusHistoryRepositoryJpa** | `StatusHistoryRepositoryJpa` | N/A | Repositorio JPA de historial de estados |
| **businessDataRepositoryJpa** | `BusinessDataRepositoryJpa` | N/A | Repositorio JPA de `BusinessData` |
| **taskRepositoryJpa** | `TaskRepositoryJpa` | N/A | Repositorio JPA de tareas |
| **statusHistoryMapper** | `StatusHistoryMapper` | N/A | Mapper entre `StatusHistory` y `StatusHistoryJpa` |

##### Método `saveStatusHistory`

Persiste un registro de historial de estado de forma genérica.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **statusHistory** | `StatusHistory` | Registro a persistir |

Retorna: `StatusHistory` — registro persistido.

Algoritmo:
1. Convierte `statusHistory` a `StatusHistoryJpa` mediante `statusHistoryMapper.toEntity`.
2. Persiste con `statusHistoryRepositoryJpa.save`.
3. Convierte y retorna el modelo de dominio.

##### Método `saveTaskStatusHistory`

Persiste un historial de estado asociándolo a la tarea BPM indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **statusHistory** | `StatusHistory` | Registro a persistir |
| **bpmTaskId** | `String` | Identificador de la tarea BPM destino |

Retorna: `StatusHistory` — registro persistido; lanza `EntityNotFoundException` si la tarea no existe.

Algoritmo:
1. Recupera la `TaskJpa` mediante `taskRepositoryJpa.findByBpmTaskId(bpmTaskId)`; si no existe, lanza `EntityNotFoundException`.
2. Convierte `statusHistory` a `StatusHistoryJpa`.
3. Asigna la tarea recuperada al campo `task` de la entidad.
4. Persiste con `statusHistoryRepositoryJpa.save`.
5. Convierte y retorna el modelo de dominio.

##### Método `deleteStatusHistory`

Elimina un registro de historial por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del registro a eliminar |

Retorna: `void`.

Algoritmo:
1. Invoca `statusHistoryRepositoryJpa.deleteById(id)`.

##### Método `findById`

Recupera un registro de historial por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del registro |

Retorna: `StatusHistory` — registro encontrado; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Consulta `statusHistoryRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Mapea y retorna el modelo de dominio.

##### Método `allStatusHistory`

Recupera todos los registros de historial de estado.

Retorna: `List<StatusHistory>` — colección completa de historiales.

Algoritmo:
1. Consulta `statusHistoryRepositoryJpa.findAll()`.
2. Mapea cada `StatusHistoryJpa` a `StatusHistory` y retorna la lista.

---

#### Clase `TaskRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.impl***
***Implements: ITaskRepository***

Implementación del repositorio de tareas. Gestiona la persistencia de `Task`, la actualización parcial mediante `ObjectUpdater` y la desasignación de usuario, coordinando `TaskRepositoryJpa`, `FieldRepositoryJpa` y `TaskMapper`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **fieldRepositoryJpa** | `FieldRepositoryJpa` | N/A | Repositorio JPA de campos |
| **taskRepositoryJpa** | `TaskRepositoryJpa` | N/A | Repositorio JPA de tareas |
| **taskMapper** | `TaskMapper` | N/A | Mapper entre `Task` y `TaskJpa` |
| **entityManager** | `EntityManager` | N/A | Gestor de persistencia JPA |
| **objectUpdater** | `ObjectUpdater` | N/A | Utilidad para actualización parcial de objetos |

##### Método `saveTask`

Persiste una tarea.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Tarea a persistir |

Retorna: `Task` — tarea persistida.

Algoritmo:
1. Convierte `task` a `TaskJpa` mediante `taskMapper.toEntity`.
2. Persiste con `taskRepositoryJpa.save`.
3. Convierte y retorna el modelo de dominio.

##### Método `deleteTask`

Elimina una tarea por su identificador interno.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador interno de la tarea |

Retorna: `void`.

Algoritmo:
1. Invoca `taskRepositoryJpa.deleteById(id)`.

##### Método `findById`

Recupera una tarea por su identificador interno.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador interno de la tarea |

Retorna: `Task` — tarea encontrada; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Consulta `taskRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Mapea y retorna el modelo de dominio.

##### Método `findByBpmTaskId`

Recupera una tarea por su identificador BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `Task` — tarea encontrada; lanza `EntityNotFoundException` si no existe.

Algoritmo:
1. Consulta `taskRepositoryJpa.findByBpmTaskId(bpmTaskId)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Mapea y retorna el modelo de dominio.

##### Método `allTask`

Recupera todas las tareas registradas.

Retorna: `List<Task>` — colección completa de tareas.

Algoritmo:
1. Consulta `taskRepositoryJpa.findAll()`.
2. Mapea cada `TaskJpa` a `Task` y retorna la lista.

##### Método `updateTask`

Actualiza parcialmente una tarea existente aplicando solo los campos no nulos.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Objeto con los datos a actualizar |
| **bpmTaskId** | `String` | Identificador BPM de la tarea a modificar |

Retorna: `Task` — tarea actualizada; lanza `GenericException` ante error.

Algoritmo:
1. Recupera la `TaskJpa` existente mediante `findByBpmTaskId(bpmTaskId)`.
2. Convierte `task` a `TaskJpa`.
3. Aplica `objectUpdater` para copiar solo los campos no nulos sobre la entidad existente.
4. Persiste con `taskRepositoryJpa.save`.
5. Convierte y retorna el modelo de dominio actualizado.

##### Método `removeUser`

Desvincula al usuario asignado de la tarea indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskid** | `String` | Identificador BPM de la tarea |

Retorna: `void`. Lanza `EntityNotFoundException` si la tarea no existe.

Algoritmo:
1. Recupera la `TaskJpa` mediante `taskRepositoryJpa.findByBpmTaskId(bpmTaskid)`; si no existe, lanza `EntityNotFoundException`.
2. Establece el campo `userId` de la entidad a `null`.
3. Persiste la entidad modificada con `taskRepositoryJpa.save`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa`

Contiene las entidades JPA del módulo BPM, los repositorios Spring Data correspondientes y el generador de identificadores personalizado para `BusinessData`.

#### Clase `BusinessDataIdGenerator`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: SequenceStyleGenerator***

Generador de identificadores personalizado para la entidad `BusinessData`. Extiende `SequenceStyleGenerator` de Hibernate para producir identificadores de tipo `String` con un formato específico del negocio, sobreescribiendo la configuración del tipo de secuencia para utilizar `LongType`.

##### Método `generate`

Genera el identificador para una nueva instancia de `BusinessData`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **session** | `SharedSessionContractImplementor` | Sesión de Hibernate activa |
| **object** | `Object` | Objeto para el que se genera el identificador |

Retorna: `Serializable` — identificador generado con el formato de negocio definido.

Algoritmo:
1. Invoca `super.generate(session, object)` para obtener el valor numérico de secuencia.
2. Aplica el formato de negocio sobre el valor obtenido para construir el identificador `String`.
3. Retorna el identificador formateado.

##### Método `configure`

Configura el generador forzando el uso de `LongType` como tipo de secuencia.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **type** | `Type` | Tipo Hibernate original de la propiedad |
| **params** | `Properties` | Parámetros de configuración del generador |
| **serviceRegistry** | `ServiceRegistry` | Registro de servicios de Hibernate |

Retorna: `void`.

Algoritmo:
1. Sustituye el `type` recibido por una instancia de `LongType`.
2. Invoca `super.configure(LongType, params, serviceRegistry)` con el tipo corregido.

---

#### Clase `BusinessDataJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que representa la tabla `TWGTBBUS`. Almacena los datos principales de una oportunidad de negocio, incluyendo su estado, fechas de inicio y fin, y las relaciones con comentarios, tareas, campos e historial de estados.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **businessId** | `String` | Get/Set | Identificador único de negocio (`COD_BSNS_ID`), generado por secuencia `QWGTBBUS1` con `BusinessDataIdGenerator` |
| **status** | `String` | Get/Set | Estado actual del negocio (`DES_BUS_STAT`) |
| **startDate** | `OffsetDateTime` | Get/Set | Fecha de inicio (`FEC_STR_DT`) |
| **endDate** | `OffsetDateTime` | Get/Set | Fecha de fin (`FEC_END_DT`) |
| **comments** | `List<CommentJpa>` | Get/Set | Comentarios asociados al negocio |
| **tasks** | `List<TaskJpa>` | Get/Set | Tareas asociadas al negocio |
| **fields** | `List<FieldJpa>` | Get/Set | Campos de datos asociados al negocio |
| **statusHistories** | `List<StatusHistoryJpa>` | Get/Set | Historial de estados del negocio |

---

#### Interfaz `BusinessDataRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: JpaRepository<BusinessDataJpa, String>***

Repositorio Spring Data JPA para `BusinessDataJpa`. Extiende `JpaRepository` añadiendo una consulta JPQL para localizar un `BusinessData` a través del identificador BPM de sus tareas asociadas.

##### Método `findByBpmTaskId`

Localiza un `BusinessDataJpa` realizando un join con sus tareas por el campo `bpmTaskId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea BPM |

Retorna: `Optional<BusinessDataJpa>` — entidad encontrada o vacío.

---

#### Clase `CommentJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que representa la tabla `TWGTBCMT`. Almacena comentarios vinculados opcionalmente a un `BusinessData` o a una `Task`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **commentId** | `Long` | Get/Set | Identificador único del comentario (`COD_OID_CMT`), generado por secuencia `QWGTBCMT1` |
| **businessData** | `BusinessDataJpa` | Get/Set | `BusinessData` al que pertenece el comentario (`COD_BSNS_ID`), carga perezosa |
| **task** | `TaskJpa` | Get/Set | Tarea a la que pertenece el comentario (`COD_OID_TSK`), carga perezosa |
| **authorId** | `String` | Get/Set | Identificador del autor del comentario (`DES_AUTHOR`) |
| **userComment** | `String` | Get/Set | Texto del comentario (`DES_USR_CMT`) |
| **commentDate** | `OffsetDateTime` | Get/Set | Fecha y hora del comentario (`FEC_COMMENT`) |

---

#### Interfaz `CommentRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: JpaRepository<CommentJpa, Long>***

Repositorio Spring Data JPA para `CommentJpa`. Hereda las operaciones CRUD estándar sin añadir métodos adicionales.

---

#### Clase `FieldJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que representa la tabla `TWGTBFLD`. Almacena los valores de los campos de formulario asociados a una tarea o a un `BusinessData`, soportando jerarquías de campos mediante una relación autorreferencial padre-hijo.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **fieldId** | `Long` | Get/Set | Identificador único del campo (`COD_OID_FLD`), generado por secuencia `QWGTBFLD1` |
| **task** | `TaskJpa` | Get/Set | Tarea a la que pertenece el campo (`COD_OID_TSK`), carga perezosa |
| **sectionValue** | `SectionValueJpa` | Get/Set | Definición del campo de sección de plantilla (`COD_OID_SCV`), carga perezosa |
| **businessData** | `BusinessDataJpa` | Get/Set | `BusinessData` al que pertenece el campo (`COD_BSNS_ID`), carga perezosa |
| **value** | `String` | Get/Set | Valor almacenado en el campo (`DES_FIELD_VL`) |
| **parentFieldId** | `Long` | Get/Set | Identificador del campo padre para estructuras jerárquicas (`COD_PRT_FLD`) |
| **fields** | `List<FieldJpa>` | Get/Set | Campos hijo asociados a este campo, con cascada total y carga perezosa |

---

#### Interfaz `FieldRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: JpaRepository<FieldJpa, Long>***

Repositorio Spring Data JPA para `FieldJpa`. Añade consultas de búsqueda por código de campo en el contexto de un `BusinessData` o de una lista de tareas.

##### Método `findAllByBusinessData_BusinessId`

Recupera todos los campos asociados a un `BusinessData` concreto.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador del `BusinessData` |

Retorna: `List<FieldJpa>` — colección de campos del negocio indicado.

##### Método `findByFieldCodeAndBusinessData`

Localiza un campo por su código y el identificador del `BusinessData` al que pertenece, mediante consulta JPQL.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo de sección |
| **businessId** | `String` | Identificador del `BusinessData` |

Retorna: `Optional<FieldJpa>` — campo encontrado o vacío.

##### Método `findByFieldCodeAndTaskId`

Localiza un campo por su código dentro de un conjunto de tareas, mediante consulta JPQL.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo de sección |
| **taskIds** | `List<Long>` | Lista de identificadores de tareas donde buscar |

Retorna: `Optional<FieldJpa>` — campo encontrado o vacío.

---

#### Clase `ProductJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que representa la tabla `TWGTBPRD`. Almacena la definición de productos disponibles en el sistema, clasificados por tipo y subtipo.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **productId** | `Long` | Get/Set | Identificador único del producto (`COD_OID_PRDT`), generado por secuencia `QWGTBPRD1` |
| **productType** | `String` | Get/Set | Tipo de producto (`DES_PRDT_TP`) |
| **subProductType** | `String` | Get/Set | Subtipo de producto (`DES_PRDT_STP`) |
| **description** | `String` | Get/Set | Descripción del producto (`DES_PRDT_DES`) |

---

#### Clase `StatusHistoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que representa la tabla `TWGTBSTH`. Registra los cambios de estado ocurridos sobre un `BusinessData` o una `Task`, almacenando la fecha y el estado en cada transición.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **statusHistoryId** | `Long` | Get/Set | Identificador único del registro de historial (`COD_OID_STHY`), generado por secuencia `QWGTBSTH1` |
| **businessData** | `BusinessDataJpa` | Get/Set | `BusinessData` al que pertenece el registro (`COD_BSNS_ID`), carga perezosa |
| **task** | `TaskJpa` | Get/Set | Tarea a la que pertenece el registro (`COD_OID_TSK`), carga perezosa |
| **dateStatusChange** | `OffsetDateTime` | Get/Set | Fecha y hora del cambio de estado (`FEC_STATUS`) |
| **status** | `String` | Get/Set | Estado registrado en el momento del cambio (`DES_HST_STAT`) |

---

#### Interfaz `StatusHistoryRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: JpaRepository<StatusHistoryJpa, Long>***

Repositorio Spring Data JPA para `StatusHistoryJpa`. Hereda las operaciones CRUD estándar sin añadir métodos adicionales.

---

#### Clase `TaskJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que representa la tabla `TWGTBTSK`. Almacena las tareas del flujo BPM asociadas a un `BusinessData`, incluyendo su tipo, nombre, usuario asignado, fechas de inicio y fin, estado y la plantilla utilizada.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **taskId** | `Long` | Get/Set | Identificador interno de la tarea (`COD_OID_TSK`), generado por secuencia `QWGTBTSK1` |
| **businessData** | `BusinessDataJpa` | Get/Set | `BusinessData` al que pertenece la tarea (`COD_BSNS_ID`), carga perezosa |
| **bpmTaskId** | `String` | Get/Set | Identificador de la tarea en el motor BPM (`DES_BPMTSK`), con conversión `NullConverter` |
| **taskType** | `String` | Get/Set | Tipo de tarea (`DES_TSK_TYPE`) |
| **taskName** | `String` | Get/Set | Nombre descriptivo de la tarea (`DES_TSK_NAME`) |
| **userId** | `String` | Get/Set | Identificador del usuario asignado a la tarea (`DES_TSK_USR`) |
| **dateStartTask** | `OffsetDateTime` | Get/Set | Fecha y hora de inicio de la tarea (`FEC_STRTSK`) |
| **dateEndTask** | `OffsetDateTime` | Get/Set | Fecha y hora de fin de la tarea (`FEC_ENDTSK`) |
| **status** | `String` | Get/Set | Estado actual de la tarea (`DES_TSK_STAT`) |
| **template** | `TemplateJpa` | Get/Set | Plantilla asociada a la tarea (`COD_OID_TEM`), carga perezosa |
| **comments** | `List<CommentJpa>` | Get/Set | Comentarios asociados a la tarea |
| **fields** | `List<FieldJpa>` | Get/Set | Campos de datos asociados a la tarea |
| **statusHistories** | `List<StatusHistoryJpa>` | Get/Set | Historial de estados de la tarea |

---

#### Interfaz `TaskRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa***
***Extends: JpaRepository<TaskJpa, Long>***

Repositorio Spring Data JPA para `TaskJpa`. Añade la búsqueda de tareas por identificador BPM.

##### Método `findByBpmTaskId`

Localiza una tarea por su identificador en el motor BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador de la tarea en el motor BPM |

Retorna: `Optional<TaskJpa>` — tarea encontrada o vacío.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper`

Contiene las interfaces MapStruct responsables de la conversión bidireccional entre las entidades de dominio del módulo BPM y sus correspondientes entidades JPA.

#### Interfaz `BusinessDataMapper`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper***
***Extends: GenericEntityMapper<BusinessData, BusinessDataJpa>***

Mapper MapStruct para la conversión entre `BusinessData` y `BusinessDataJpa`. Añade un método `@AfterMapping` que restaura las relaciones bidireccionales sobre la entidad JPA generada, garantizando la integridad del grafo de objetos.

##### Método `linkRelations`

Método por defecto invocado automáticamente por MapStruct tras completar el mapeo hacia `BusinessDataJpa`, para enlazar las entidades hijo con su padre.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bd** | `BusinessDataJpa` | Entidad JPA recién construida por el mapper |

Retorna: `void`.

Algoritmo:
1. Itera sobre la lista `comments` de `bd` y asigna `bd` como `businessData` de cada `CommentJpa`.
2. Itera sobre la lista `tasks` y asigna `bd` como `businessData` de cada `TaskJpa`.
3. Itera sobre la lista `fields` y asigna `bd` como `businessData` de cada `FieldJpa`.
4. Itera sobre la lista `statusHistories` y asigna `bd` como `businessData` de cada `StatusHistoryJpa`.

---

#### Interfaz `CommentMapper`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper***
***Extends: GenericEntityMapper<Comment, CommentJpa>***

Mapper MapStruct para la conversión entre `Comment` y `CommentJpa`. Ignora las relaciones `businessData` y `task` al mapear hacia la entidad JPA (se asignan manualmente en el repositorio) y adapta el nombre del campo de texto del comentario entre ambos modelos.

##### Método `toEntity`

Convierte un `Comment` de dominio a `CommentJpa`, ignorando relaciones padre y adaptando el campo de texto.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **comment** | `Comment` | Modelo de dominio a convertir |

Retorna: `CommentJpa` — entidad JPA resultante, con `businessData` y `task` a `null`.

##### Método `toModel`

Convierte un `CommentJpa` al modelo de dominio `Comment`, mapeando `userComment` al campo `commentText`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **commentJpa** | `CommentJpa` | Entidad JPA a convertir |

Retorna: `Comment` — modelo de dominio resultante.

---

#### Interfaz `FieldMapper`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper***
***Extends: GenericEntityMapper<Field, FieldJpa>***

Mapper MapStruct para la conversión entre `Field` y `FieldJpa`. Al mapear a modelo, extrae el `fieldCode` desde el `sectionValue` anidado. En ambas direcciones propaga únicamente los identificadores de `businessData` y `task`, evitando cargas innecesarias de entidades completas.

##### Método `toModel`

Convierte una `FieldJpa` al modelo de dominio `Field`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **entity** | `FieldJpa` | Entidad JPA a convertir |

Retorna: `Field` — modelo de dominio con `fieldCode` extraído de `sectionValue.fieldCode`.

##### Método `toEntity`

Convierte un `Field` de dominio a `FieldJpa`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **model** | `Field` | Modelo de dominio a convertir |

Retorna: `FieldJpa` — entidad JPA con los identificadores de `businessData` y `task` propagados.

---

#### Interfaz `MinimalBusinessDataMapper`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper***
***Extends: GenericEntityMapper<MinimalBusinessData, BusinessDataJpa>***

Mapper MapStruct para la conversión entre la proyección reducida `MinimalBusinessData` y `BusinessDataJpa`. Proporciona una vista ligera de `BusinessData` sin colecciones asociadas, útil en consultas de solo lectura.

---

#### Interfaz `MinimalTaskDataMapper`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper***
***Extends: GenericEntityMapper<MinimalTask, TaskJpa>***

Mapper MapStruct para la conversión entre la proyección reducida `MinimalTask` y `TaskJpa`. Proporciona una vista ligera de `Task` orientada a listados y consultas de solo lectura.

---

#### Interfaz `StatusHistoryMapper`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper***
***Extends: GenericEntityMapper<StatusHistory, StatusHistoryJpa>***

Mapper MapStruct para la conversión entre `StatusHistory` y `StatusHistoryJpa`. Al mapear hacia la entidad JPA ignora las relaciones `businessData` y `task`, que se asignan manualmente en el repositorio.

##### Método `toEntity`

Convierte un `StatusHistory` de dominio a `StatusHistoryJpa`, ignorando las relaciones con entidades padre.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **statusHistory** | `StatusHistory` | Modelo de dominio a convertir |

Retorna: `StatusHistoryJpa` — entidad JPA resultante, con `businessData` y `task` a `null`.

---

#### Interfaz `TaskMapper`

***Package: com.bbva.wgtb.wgtbbackend.apibpm.infrastructure.repository.jpa.mapper***
***Extends: GenericEntityMapper<Task, TaskJpa>***

Mapper MapStruct para la conversión entre `Task` y `TaskJpa`. Añade un método `@AfterMapping` que restaura las relaciones bidireccionales sobre la entidad JPA generada, asegurando que los comentarios, campos e historiales hijos referencien correctamente a su tarea padre.

##### Método `linkRelations`

Método por defecto invocado automáticamente por MapStruct tras completar el mapeo hacia `TaskJpa`, para enlazar las entidades hijo con su tarea padre.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tsk** | `TaskJpa` | Entidad JPA recién construida por el mapper |

Retorna: `void`.

Algoritmo:
1. Itera sobre la lista `comments` de `tsk` y asigna `tsk` como `task` de cada `CommentJpa`.
2. Itera sobre la lista `fields` y asigna `tsk` como `task` de cada `FieldJpa`.
3. Itera sobre la lista `statusHistories` y asigna `tsk` como `task` de cada `StatusHistoryJpa`.

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.application`

Contiene las interfaces de servicio de aplicación para la gestión de tablas, columnas y valores de selección del módulo `apitableservices`.

#### Interfaz `ISelectionValueService`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.application***

Define el contrato de aplicación para la recuperación de valores de selección (listas desplegables) almacenados en base de datos.

**Métodos:**

##### Método `findById`

Recupera un `SelectionValue` por su identificador primario, lanzando una excepción si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador único del valor de selección. |

Retorna: `SelectionValue` — entidad encontrada.

##### Método `allSelectionValue`

Retorna la lista completa de valores de selección disponibles en el sistema.

Retorna: `List<SelectionValue>` — todos los valores de selección registrados.

---

#### Interfaz `ITableColumnService`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.application***

Define el contrato de aplicación para consultar columnas (`Column`) asociadas a las tablas configurables del módulo.

**Métodos:**

##### Método `findById`

Recupera una columna por su identificador, lanzando una excepción si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador único de la columna. |

Retorna: `Column` — entidad de columna encontrada.

##### Método `allTableColumn`

Retorna todas las columnas registradas en el sistema.

Retorna: `List<Column>` — lista completa de columnas.

##### Método `findByTableId`

Recupera todas las columnas asociadas a una tabla concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableId** | `Long` | Identificador de la tabla propietaria. |

Retorna: `List<Column>` — columnas pertenecientes a la tabla indicada.

---

#### Interfaz `ITableService`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.application***

Define el contrato de aplicación principal del módulo de tablas, incluyendo la obtención de configuración, datos paginados y gestión completa del ciclo de vida de los valores de selección.

**Métodos:**

##### Método `findById`

Recupera una `Table` por su identificador, lanzando una excepción si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la tabla. |

Retorna: `Table` — entidad de tabla encontrada.

##### Método `allTable`

Retorna todas las tablas configuradas en el sistema.

Retorna: `List<Table>` — lista completa de tablas.

##### Método `getTabledata`

Obtiene los datos paginados de una tabla, enrutando la petición al origen de datos correspondiente (BPM, RDR, SLA, `businessData` o genérico) según el tipo de tabla.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA (identidad del llamador, trazabilidad, etc.). |
| **tableId** | `Float` | Identificador de la tabla a consultar. |
| **paginationInfo** | `InputPaginationInfoDto` | Parámetros de paginación, filtrado y ordenación. |

Retorna: `Page<List<ColumnValue>>` — página de filas, donde cada fila es una lista de `ColumnValue`.

##### Método `getSelectValues`

Obtiene los valores de selección asociados a una clave concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **key** | `String` | Clave de agrupación de los valores de selección. |

Retorna: `List<SelectionValue>` — valores de selección para la clave indicada.

##### Método `deleteSelectionValueById`

Elimina un valor de selección por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValueId** | `Long` | Identificador del valor a eliminar. |

Retorna: `void`.

##### Método `deleteSelectionValuesByKey`

Elimina todos los valores de selección agrupados bajo una clave.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **key** | `String` | Clave de agrupación cuyos valores se eliminarán. |

Retorna: `void`.

##### Método `insertSelectionValue`

Persiste un único valor de selección.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValue** | `SelectionValue` | Entidad con los datos a insertar. |

Retorna: `SelectionValue` — entidad persistida con el identificador asignado.

##### Método `getAllSelectValues`

Retorna todos los valores de selección del sistema.

Retorna: `List<SelectionValue>` — lista completa de valores de selección.

##### Método `insertMultipleSelectionValue`

Persiste una lista de valores de selección en bloque.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sv** | `List<SelectionValue>` | Lista de entidades a insertar. |

Retorna: `List<SelectionValue>` — entidades persistidas.

##### Método `insertColumnMultipleSelectionValue`

Persiste una lista de valores de selección asociándolos a una columna concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sv** | `List<SelectionValue>` | Lista de entidades a insertar. |
| **columnId** | `Long` | Identificador de la columna a la que se asocian los valores. |

Retorna: `List<SelectionValue>` — entidades persistidas con la asociación de columna establecida.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.application.impl`

Contiene las implementaciones concretas de los servicios de aplicación para la gestión de tablas, columnas y valores de selección.

#### Clase `SelectionValueServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.application.impl***
***Implements: ISelectionValueService***

Implementación del servicio de aplicación para valores de selección. Delega directamente en `ISelectionValueRepository` para la recuperación de datos, sin aplicar lógica adicional.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **selectionValueRepository** | `ISelectionValueRepository` | N/A | Repositorio de dominio para valores de selección; inyectado por constructor mediante `@RequiredArgsConstructor`. |

##### Método `findById`

Recupera un `SelectionValue` por su identificador delegando en el repositorio; propaga `EntityNotFoundException` si no se encuentra.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del valor de selección. |

Retorna: `SelectionValue` — entidad encontrada.

Algoritmo:
1. Invoca `selectionValueRepository.findById(id)` y retorna el resultado.

##### Método `allSelectionValue`

Retorna todos los valores de selección disponibles delegando en el repositorio.

Retorna: `List<SelectionValue>` — lista completa de valores de selección.

Algoritmo:
1. Invoca `selectionValueRepository.allSelectionValue()` y retorna el resultado.

---

#### Clase `TableColumnServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.application.impl***
***Implements: ITableColumnService***

Implementación del servicio de aplicación para columnas de tabla. Actúa como fachada sobre `IColumnRepository`, delegando todas las operaciones de consulta.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **columnRepository** | `IColumnRepository` | N/A | Repositorio de dominio para columnas; inyectado por constructor mediante `@RequiredArgsConstructor`. |

##### Método `findById`

Recupera una columna por su identificador; propaga `EntityNotFoundException` si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la columna. |

Retorna: `Column` — entidad de columna encontrada.

Algoritmo:
1. Invoca `columnRepository.findById(id)` y retorna el resultado.

##### Método `allTableColumn`

Retorna todas las columnas registradas en el sistema.

Retorna: `List<Column>` — lista completa de columnas.

Algoritmo:
1. Invoca `columnRepository.allTableColumn()` y retorna el resultado.

##### Método `findByTableId`

Recupera todas las columnas pertenecientes a una tabla concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableId** | `Long` | Identificador de la tabla propietaria. |

Retorna: `List<Column>` — columnas asociadas a la tabla.

Algoritmo:
1. Invoca `columnRepository.findByTableId(tableId)` y retorna el resultado.

---

#### Clase `TableServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.application.impl***
***Implements: ITableService***

Servicio principal del módulo de tablas. Gestiona la obtención de datos paginados enrutando cada petición al origen correcto (BPM vía xBPM API, `BusinessData`, RDR, SLA o repositorio genérico) según el `TableType` de la tabla solicitada. Adicionalmente, administra el ciclo de vida completo de los `SelectionValue`, incluyendo inserción, consulta y eliminación.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableRepository** | `ITableRepository` | N/A | Repositorio de dominio para tablas. |
| **columnRepository** | `IColumnRepository` | N/A | Repositorio de dominio para columnas. |
| **taskMapper** | `TaskMapper` | N/A | Mapper JPA → dominio para tareas BPM. |
| **jsonUtils** | `JsonUtils` | N/A | Utilidad de serialización/deserialización JSON. |
| **entityScrapper** | `EntityScrapper` | N/A | Utilidad para extraer propiedades de entidades genéricas. |
| **xbpmApi** | `ServiceApi` | N/A | Cliente del API externo xBPM. |
| **businessDataRepository** | `BusinessDataRepositoryJpa` | N/A | Repositorio JPA para datos de negocio. |
| **selectionValueRepositoryJpa** | `SelectionValueRepositoryJpa` | N/A | Repositorio JPA directo para valores de selección. |
| **selectionValueRepository** | `ISelectionValueRepository` | N/A | Repositorio de dominio para valores de selección. |
| **rdrService** | `RdrService` | N/A | Servicio de acceso a datos RDR. |
| **businessDataService** | `IBusinessDataService` | N/A | Servicio de aplicación para datos de negocio. |

##### Método `normalizePage`

Normaliza un número de página a un entero positivo con valor mínimo de 1.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **page** | `Integer` | Número de página recibido (puede ser nulo o negativo). |

Retorna: `int` — número de página normalizado (mínimo 1).

Algoritmo:
1. Si `page` es nulo o menor o igual a cero, retorna 1.
2. En caso contrario, retorna el valor recibido.

##### Método `normalizePageSize`

Normaliza el tamaño de página a un entero positivo con valor mínimo de 1.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **pageSize** | `Integer` | Tamaño de página recibido (puede ser nulo o negativo). |

Retorna: `int` — tamaño de página normalizado.

Algoritmo:
1. Si `pageSize` es nulo o menor o igual a cero, retorna un valor por defecto (por ejemplo, 10).
2. En caso contrario, retorna el valor recibido.

##### Método `applyPagination`

Aplica paginación en memoria sobre una lista completa de filas.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **allRows** | `List<T>` | Lista completa de elementos a paginar. |
| **page** | `int` | Número de página (base 1). |
| **pageSize** | `int` | Número máximo de elementos por página. |

Retorna: `Page<T>` — objeto de página con el subconjunto de elementos y metadatos de paginación.

Algoritmo:
1. Calcula el índice de inicio: `(page - 1) * pageSize`.
2. Calcula el índice de fin: `min(inicio + pageSize, allRows.size())`.
3. Si el índice de inicio supera el tamaño de la lista, retorna una página vacía.
4. Extrae la sublista correspondiente y construye el objeto `Page` con el total de elementos.

##### Método `applySorting`

Ordena las filas según los filtros que especifiquen un `sortOrder`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **rows** | `List<List<ColumnValue>>` | Filas a ordenar. |
| **filters** | `TableFilter[]` | Filtros de la petición; aquellos con `sortOrder` determinan el criterio de ordenación. |

Retorna: `List<List<ColumnValue>>` — lista ordenada (nueva instancia de `ArrayList` si se aplica ordenación).

Algoritmo:
1. Filtra los `TableFilter` que tengan `sortOrder` no nulo.
2. Si no hay filtros de ordenación, retorna la lista original sin modificar.
3. Construye un `Comparator` encadenado para cada filtro de ordenación:
   1. Extrae el valor de la columna indicada por `fieldCode` de cada fila mediante `getColumnValueByCode`.
   2. Compara los valores con `compareValues`.
   3. Si el orden es descendente, invierte el comparador.
4. Ordena una copia de la lista con el comparador resultante y la retorna.

##### Método `getColumnValueByCode`

Busca dentro de una fila el valor de la columna identificada por su código.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `List<ColumnValue>` | Fila de la que se extrae el valor. |
| **fieldCode** | `String` | Código de la columna buscada. |

Retorna: `String` — valor de la columna como cadena, o cadena vacía si no se encuentra.

Algoritmo:
1. Itera sobre los `ColumnValue` de la fila.
2. Retorna `value.toString()` del primer elemento cuyo `tableFieldCode` coincide con `fieldCode`.
3. Si no se encuentra coincidencia, retorna cadena vacía.

##### Método `compareValues`

Compara dos valores de columna (cadenas nulables) de forma natural, tratando nulos como menores.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **val1** | `String` | Primer valor (puede ser nulo). |
| **val2** | `String` | Segundo valor (puede ser nulo). |

Retorna: `int` — resultado de comparación negativo, cero o positivo.

Algoritmo:
1. Si ambos son nulos, retorna 0.
2. Si solo `val1` es nulo, retorna -1.
3. Si solo `val2` es nulo, retorna 1.
4. Delega en `compareNatural(val1, val2)`.

##### Método `compareNatural`

Compara dos cadenas no nulas intentando primero una comparación numérica y recurriendo a comparación léxica si falla.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **val1** | `String` | Primera cadena (no nula). |
| **val2** | `String` | Segunda cadena (no nula). |

Retorna: `int` — resultado de comparación.

Algoritmo:
1. Intenta parsear ambas cadenas como `Double`.
2. Si ambas son numéricas, compara sus valores numéricos.
3. Si el parseo falla para alguna, realiza comparación léxica ignorando mayúsculas/minúsculas.

##### Método `startsWithIgnoreCase`

Comprueba si una cadena comienza con un prefijo dado ignorando la capitalización.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **value** | `String` | Cadena a evaluar. |
| **prefix** | `String` | Prefijo a buscar. |

Retorna: `boolean` — `true` si `value` comienza con `prefix` en cualquier capitalización.

Algoritmo:
1. Convierte ambas cadenas a minúsculas con `Locale.ROOT`.
2. Invoca `startsWith` sobre el resultado.

##### Método `normalizePath`

Normaliza una ruta de campo eliminando espacios y estandarizando separadores.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **raw** | `String` | Cadena de ruta en bruto. |

Retorna: `String` — ruta normalizada.

Algoritmo:
1. Elimina espacios en blanco al inicio y al final.
2. Reemplaza separadores alternativos por el separador canónico (punto).

##### Método `extractSingle`

Extrae el valor de un campo concreto de una fila que puede ser un `Map` o un POJO.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `Object` | Fila fuente (`Map` o POJO). |
| **fieldCode** | `String` | Código del campo a extraer. |

Retorna: `Object` — valor extraído, o `null` si no se encuentra.

Algoritmo:
1. Si `row` es instancia de `Map`, retorna el valor asociado a `fieldCode`.
2. En caso contrario, intenta invocar `readField(row, fieldCode)`.
3. Si `readField` no encuentra el campo, intenta invocar el getter estándar mediante `invokeGetter`.

##### Método `readField`

Accede directamente a un campo de un objeto por reflexión, incluyendo campos privados.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **target** | `Object` | Objeto sobre el que se accede. |
| **fieldName** | `String` | Nombre del campo. |

Retorna: `Object` — valor del campo, o `null` si no existe o no es accesible.

Algoritmo:
1. Obtiene la clase del objeto y busca el campo por nombre en la jerarquía de clases.
2. Hace accesible el campo mediante `setAccessible(true)`.
3. Retorna el valor del campo para el objeto `target`.

##### Método `invokeGetter`

Invoca el getter estándar (`get<Prop>`) de una propiedad sobre el objeto indicado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **target** | `Object` | Objeto sobre el que se invoca el getter. |
| **prop** | `String` | Nombre de la propiedad (la primera letra se capitaliza internamente). |

Retorna: `Object` — valor retornado por el getter, o `null` si no existe.

Algoritmo:
1. Construye el nombre del método como `"get" + capitalize(prop)`.
2. Obtiene el método por reflexión de la clase del objeto.
3. Invoca el método sin argumentos y retorna el resultado.

##### Método `invokeMethod`

Invoca un método sin argumentos por nombre sobre un objeto dado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **target** | `Object` | Objeto sobre el que se invoca el método. |
| **methodName** | `String` | Nombre exacto del método. |

Retorna: `Object` — valor retornado por el método, o `null` si no existe o lanza excepción.

Algoritmo:
1. Obtiene el método por reflexión usando `methodName`.
2. Invoca el método sobre `target` sin argumentos.
3. Retorna el resultado o captura la excepción retornando `null`.

##### Método `capitalize`

Capitaliza la primera letra de una cadena.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **s** | `String` | Cadena de entrada. |

Retorna: `String` — cadena con la primera letra en mayúscula.

Algoritmo:
1. Si la cadena es nula o vacía, la retorna sin modificar.
2. Combina `Character.toUpperCase(s.charAt(0))` con el resto de la cadena.

##### Método `toCamel`

Convierte un identificador con separación por guiones bajos (p. ej., `COD_STATUS`) a lowerCamelCase (p. ej., `codStatus`).

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **s** | `String` | Identificador en formato `SNAKE_CASE`. |

Retorna: `String` — identificador en formato lowerCamelCase.

Algoritmo:
1. Convierte la cadena completa a minúsculas.
2. Divide por el carácter `_`.
3. Capitaliza la primera letra de cada segmento excepto el primero.
4. Une los segmentos y retorna el resultado.

##### Método `postProcessBpmValue`

Aplica transformaciones de postprocesado sobre valores provenientes del BPM, convirtiendo fechas a formato ISO local (`yyyy-MM-dd`) cuando el campo lo requiera.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableFieldCode** | `String` | Código del campo de tabla para determinar el tipo de transformación. |
| **value** | `Object` | Valor bruto extraído del BPM. |

Retorna: `Object` — valor transformado (cadena de fecha ISO si aplica, o el valor original).

Algoritmo:
1. Comprueba si `tableFieldCode` corresponde a un campo de tipo fecha según la configuración.
2. Si es campo fecha, convierte `value` a `Instant` mediante `toInstant(value)`.
3. Formatea el `Instant` con `OUT_DATE_ONLY` usando la zona horaria del sistema.
4. Retorna la cadena formateada; en caso contrario, retorna `value` sin modificar.

##### Método `toInstant`

Convierte un valor de tipo `String`, `java.util.Date` o `Long` (epoch en milisegundos) a `Instant`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **value** | `Object` | Valor a convertir. |

Retorna: `Instant` — instante de tiempo equivalente, o `null` si la conversión no es posible.

Algoritmo:
1. Si `value` es `Long`, construye el `Instant` a partir de epoch-millis.
2. Si `value` es `java.util.Date`, invoca `toInstant()`.
3. Si `value` es `String`, delega en `parseStringToInstant`.
4. En cualquier otro caso, retorna `null`.

##### Método `parseStringToInstant`

Parsea una cadena de fecha/hora a `Instant`, probando múltiples formatos en secuencia.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **s** | `String` | Cadena de fecha/hora a parsear (no debe estar en blanco). |

Retorna: `Instant` — instante parseado, o `null` si ningún formato es compatible.

Algoritmo:
1. Intenta parsear como `OffsetDateTime` con el formato estándar ISO (con y sin milisegundos).
2. Si tiene éxito, retorna `offsetDateTime.toInstant()`.
3. Si falla, intenta parsear como `LocalDate` y convierte al inicio del día en la zona horaria del sistema.
4. Si todos los intentos fallan, captura `DateTimeParseException` y retorna `null`.

##### Método `extractValue`

Extrae el valor de un campo de una fila soportando rutas anidadas (separadas por punto) y acceso directo por código.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `Object` | Fila fuente (`Map` o POJO). |
| **fieldCodeOrPath** | `String` | Código de campo simple o ruta de acceso anidada. |

Retorna: `Object` — valor extraído.

Algoritmo:
1. Normaliza la ruta con `normalizePath`.
2. Si la ruta no contiene separadores, delega en `extractSingle(row, fieldCodeOrPath)`.
3. Si contiene separadores, divide la ruta por el separador.
4. Itera sobre los segmentos llamando sucesivamente a `extractSingle` sobre el resultado anterior.
5. Retorna el valor final o `null` si algún segmento intermedio es nulo.

##### Método `findById`

Recupera una `Table` por su identificador delegando en el repositorio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la tabla. |

Retorna: `Table` — entidad de tabla encontrada.

Algoritmo:
1. Invoca `tableRepository.findById(id)` y retorna el resultado.

##### Método `allTable`

Retorna todas las tablas configuradas en el sistema.

Retorna: `List<Table>` — lista completa de tablas.

Algoritmo:
1. Invoca `tableRepository.allTable()` y retorna el resultado.

##### Método `getTabledata`

Enruta la petición de datos de tabla al origen correcto según el `TableType` de la entidad.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA. |
| **tableId** | `Float` | Identificador de la tabla. |
| **paginationInfo** | `InputPaginationInfoDto` | Parámetros de paginación, filtrado y ordenación. |

Retorna: `Page<List<ColumnValue>>` — página de filas con valores de columna.

Algoritmo:
1. Convierte `tableId` a `Long` y recupera la entidad `Table` con `findById`.
2. Evalúa el `TableType` de la tabla:
   - `BPM` → delega en `getBpmData`.
   - `BUSINESS_DATA` → delega en `getBusinessTemplateData`.
   - `RDR` → delega en `getRdrData`.
   - `SLA` → delega en `getSlaData`.
   - `DEFAULT` u otro → obtiene filas del repositorio genérico, aplica `processObject` y paginación.
3. Aplica ordenación con `applySorting` si la tabla lo requiere.
4. Retorna la página resultante.

##### Método `calculateDiff`

Calcula y establece la diferencia temporal entre el valor calculado y el estimado para todas las filas de la tabla.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **rows** | `List<List<ColumnValue>>` | Filas de datos a enriquecer. |
| **calc** | `String` | Código de la columna con el valor calculado. |
| **estimated** | `String` | Código de la columna con el valor estimado. |

Retorna: `void`.

Algoritmo:
1. Itera sobre cada fila de `rows`.
2. Para cada fila, invoca `processDiffColumn` con los códigos de columna proporcionados.

##### Método `processDiffColumn`

Calcula la diferencia entre el valor real y el estimado de una columna y asigna la etiqueta resultante a la celda correspondiente de la fila.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **col** | `ColumnValue` | Celda de diferencia donde se escribirá el resultado. |
| **row** | `List<ColumnValue>` | Fila completa de la que se extraen los valores relacionados. |
| **calc** | `String` | Código de la columna calculada. |
| **estimated** | `String` | Código de la columna estimada. |

Retorna: `void`.

Algoritmo:
1. Localiza los valores `calc` y `estimated` en la fila con `findRelatedValues`.
2. Parsea ambos valores a segundos.
3. Invoca `computeDiffLabel` para obtener la etiqueta de diferencia.
4. Asigna la etiqueta al campo `value` de `col`.

##### Método `findRelatedValues`

Localiza en una fila los valores de las columnas asociadas a una tarea y al tiempo estimado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `List<ColumnValue>` | Fila de la que se extraen los valores. |
| **taskName** | `String` | Código de la columna de tarea calculada. |
| **estimated** | `String` | Código de la columna estimada. |

Retorna: `String[]` — arreglo con dos elementos: `[valorCalculado, valorEstimado]`.

Algoritmo:
1. Itera sobre `row` buscando los `ColumnValue` cuyos códigos coinciden con `taskName` y `estimated`.
2. Retorna ambos valores en un arreglo de dos posiciones.

##### Método `computeDiffLabel`

Genera una etiqueta legible que describe la diferencia entre el tiempo activo real y el estimado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **currentSeconds** | `long` | Segundos de tiempo activo real. |
| **calcSeconds** | `long` | Segundos de tiempo estimado. |

Retorna: `String` — etiqueta de diferencia (p. ej., `"+2d 3h"`, `"-1h 30m"`).

Algoritmo:
1. Calcula la diferencia `currentSeconds - calcSeconds`.
2. Determina el signo y el valor absoluto de la diferencia.
3. Descompone la diferencia en días, horas y minutos.
4. Construye y retorna la cadena formateada con el signo correspondiente.

##### Método `getSlaData`

Obtiene los datos de la tabla de tipo SLA, enriqueciendo cada fila con duraciones estimadas por tarea y el tiempo activo calculado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **table** | `Table` | Configuración de la tabla SLA. |
| **paginationInfo** | `InputPaginationInfoDto` | Parámetros de paginación y filtrado. |

Retorna: `Page<List<ColumnValue>>` — página de filas SLA enriquecidas.

Algoritmo:
1. Recupera las tareas del origen de datos correspondiente.
2. Para cada tarea, invoca `processObject` con las columnas de la tabla para construir la fila.
3. Calcula el tiempo activo con `calculateSecondsActive` para cada tarea.
4. Enriquece las filas con duraciones estimadas obtenidas de `SelectionValue`.
5. Calcula diferencias con `calculateDiff`.
6. Aplica filtros de columna con `matchesColumnValueFilters`.
7. Aplica ordenación y paginación, retornando el resultado.

##### Método `processObject`

Convierte un objeto de dominio en una lista de `ColumnValue` mapeando cada campo a su columna correspondiente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **object** | `Object` | Objeto de dominio a convertir. |
| **columns** | `List<Column>` | Definición de columnas de la tabla. |

Retorna: `List<ColumnValue>` — fila resultante con un `ColumnValue` por cada columna.

Algoritmo:
1. Itera sobre las columnas.
2. Para cada columna, invoca `extractValue(object, column.getPath())` para obtener el valor.
3. Aplica `postProcessBpmValue` si la columna pertenece a una tabla BPM.
4. Crea un `ColumnValue` con el código y el valor resultante.
5. Retorna la lista de `ColumnValue`.

##### Método `calculateSecondsActive`

Calcula el número total de segundos que una tarea ha permanecido en un estado activo (`NOT_STARTED` o `IN_PROGRESS`), sumando todos los intervalos entre estados de inicio y fin.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **task** | `Task` | Tarea de la que se calcula el tiempo activo. |

Retorna: `Long` — total de segundos activos, o 0 si no hay historial de estados.

Algoritmo:
1. Ordena el historial de estados (`StatusHistory`) por fecha ascendente.
2. Itera sobre el historial identificando pares de transiciones inicio/fin.
3. Para cada par, calcula la diferencia en segundos entre la fecha de fin y la de inicio.
4. Acumula los intervalos válidos y retorna la suma total.

##### Método `isInitStatus`

Determina si un estado del historial es un estado de inicio de actividad (`NOT_STARTED` o `IN_PROGRESS`).

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **status** | `StatusHistory` | Estado del historial a evaluar. |

Retorna: `boolean` — `true` si es un estado de inicio.

Algoritmo:
1. Compara el identificador de estado con `NOT_STARTED` e `IN_PROGRESS`.
2. Retorna `true` si coincide con alguno de ellos.

##### Método `isEndStatus`

Determina si un estado del historial es un estado de fin de actividad (ninguno de `NOT_CREATED`, `WAIT_CLIENT`, `WAIT_TEAMS` ni estado de inicio).

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **status** | `StatusHistory` | Estado del historial a evaluar. |

Retorna: `boolean` — `true` si es un estado de fin válido.

Algoritmo:
1. Verifica que el estado no sea `NOT_CREATED`, `WAIT_CLIENT` ni `WAIT_TEAMS`.
2. Verifica que el estado no sea un estado de inicio mediante `isInitStatus`.
3. Retorna `true` solo si ambas condiciones se cumplen.

##### Método `getBpmData`

Obtiene los datos de tareas BPM paginados consultando el API xBPM en una única llamada y procesando los resultados localmente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableId** | `Long` | Identificador de la tabla BPM. |
| **paginationInfo** | `InputPaginationInfoDto` | Parámetros de paginación y filtrado. |

Retorna: `Page<List<ColumnValue>>` — página de filas BPM.

Algoritmo:
1. Recupera la configuración de la tabla con `findById(tableId)`.
2. Construye la query QLTT usando el filtro BPM canónico.
3. Invoca el API xBPM solicitando hasta 999 elementos.
4. Mapea cada resultado a `List<ColumnValue>` con `toGenericColumnValues`.
5. Aplica filtros de columna con `matchesColumnValueFilters`.
6. Aplica ordenación con `applySorting`.
7. Aplica paginación con `applyPagination` y retorna la página.

##### Método `toGenericColumnValues`

Convierte una fila genérica de BPM (típicamente un `Map` del JSON de respuesta) en una lista de `ColumnValue`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `Object` | Fila fuente (generalmente un `Map`). |
| **columns** | `List<Column>` | Definición de columnas de la tabla. |

Retorna: `List<ColumnValue>` — fila mapeada.

Algoritmo:
1. Itera sobre las columnas.
2. Para cada columna, extrae el valor con `extractValue(row, column.getPath() o column.getTableFieldCode())`.
3. Aplica `postProcessBpmValue` sobre el valor extraído.
4. Crea un `ColumnValue` y lo añade a la lista resultado.

##### Método `getBusinessTemplateData`

Obtiene los datos de una tabla de tipo `BUSINESS_DATA` con paginación y filtrado aplicados en memoria.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableId** | `Long` | Identificador de la tabla. |
| **paginationInfo** | `InputPaginationInfoDto` | Parámetros de paginación y filtrado. |

Retorna: `Page<List<ColumnValue>>` — página de filas de negocio.

Algoritmo:
1. Recupera la configuración de la tabla con `findById`.
2. Obtiene todos los registros `BusinessDataJpa` del repositorio.
3. Transforma cada registro en `List<ColumnValue>` con `toBusinessColumnValues`.
4. Aplica filtros con `matchesColumnValueFilters`.
5. Aplica ordenación y paginación, retornando el resultado.

##### Método `matchesColumnValueFilters`

Verifica si una fila satisface todos los filtros activos de la petición (comparación de valores case-insensitive).

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `List<ColumnValue>` | Fila a evaluar. |
| **filters** | `TableFilter[]` | Filtros de la petición. |

Retorna: `boolean` — `true` si la fila supera todos los filtros con valor no en blanco.

Algoritmo:
1. Itera sobre los filtros descartando aquellos con valor en blanco o nulo.
2. Para cada filtro activo, busca el `ColumnValue` cuyo código coincide con el campo del filtro.
3. Compara el valor de la celda con el valor del filtro ignorando mayúsculas/minúsculas.
4. Si algún filtro no coincide, retorna `false`.
5. Retorna `true` si todos los filtros se satisfacen.

##### Método `getRdrData`

Obtiene los datos de una tabla de tipo RDR, parseando los XML de parte RDR y construyendo filas con `toRdrColumnValues`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableId** | `Long` | Identificador de la tabla RDR. |
| **paginationInfo** | `InputPaginationInfoDto` | Parámetros de paginación y filtrado. |

Retorna: `Page<List<ColumnValue>>` — página de filas RDR.

Algoritmo:
1. Obtiene la lista de XML de partes con `getMockPartyXmlList`.
2. Extrae el `branchId` del contexto de seguridad actual.
3. Para cada XML, invoca `toRdrColumnValues` para construir la fila.
4. Aplica filtros, ordenación y paginación, retornando el resultado.

##### Método `getMockPartyXmlList`

Obtiene la lista de cadenas XML de registros de parte RDR, retornando una lista vacía si el fichero de datos no está disponible.

Retorna: `List<String>` — lista de XML de parte (uno por registro).

Algoritmo:
1. Intenta obtener los XMLs del `RdrService`.
2. Si el servicio lanza excepción o retorna nulo, retorna una lista vacía.

##### Método `toRdrColumnValues`

Convierte un XML de parte RDR en una lista de `ColumnValue` aplicando XPath para cada columna y localizando el nombre de la sucursal por `branchId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **partyXml** | `String` | Cadena XML de la parte RDR. |
| **columns** | `List<Column>` | Definición de columnas de la tabla. |
| **branchId** | `String` | Identificador de sucursal para localizar el nombre en el bloque `ReltdPtyDetl`. |

Retorna: `List<ColumnValue>` — fila mapeada desde el XML.

Algoritmo:
1. Parsea `partyXml` como documento XML.
2. Para cada columna, obtiene la expresión XPath con `getXPathForColumn`.
3. Evalúa la expresión XPath sobre el documento.
4. Si el código de la columna corresponde al nombre de sucursal, navega al bloque `ReltdPtyDetl` con `ID=branchId` y `R='1006'` para extraer el campo `Typ='4006'`.
5. Construye un `ColumnValue` con el resultado y lo añade a la lista.

##### Método `getXPathForColumn`

Retorna la expresión XPath asociada a un código de columna RDR.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **columnCode** | `String` | Código de la columna de la tabla. |

Retorna: `String` — expresión XPath correspondiente, o `null` si el código no tiene mapeo definido.

Algoritmo:
1. Consulta un mapa estático de correspondencias `columnCode → xpathExpression`.
2. Retorna la expresión asociada o `null`.

##### Método `toBusinessColumnValues`

Transforma un registro `BusinessDataJpa` en una lista de `ColumnValue` mapeando campos built-in y campos de negocio almacenados en JSON.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **data** | `BusinessDataJpa` | Registro JPA de datos de negocio. |
| **columns** | `List<Column>` | Definición de columnas de la tabla. |

Retorna: `List<ColumnValue>` — fila mapeada.

Algoritmo:
1. Itera sobre las columnas.
2. Para campos built-in (`businessId`, `status`, `createdAt`, `startDate`), extrae el valor directamente del objeto `data`.
3. Para el resto de columnas, parsea el JSON almacenado en `data` y extrae el campo por `tableFieldCode` o `path`.
4. Aplica postprocesado si corresponde.
5. Construye y retorna la lista de `ColumnValue`.

##### Método `getSelectValues`

Recupera los valores de selección para una clave de agrupación dada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **key** | `String` | Clave de agrupación de los valores de selección. |

Retorna: `List<SelectionValue>` — valores de selección asociados a la clave.

Algoritmo:
1. Invoca `selectionValueRepository.findByTag(key)` y retorna el resultado.

##### Método `deleteSelectionValueById`

Elimina un valor de selección por su identificador, lanzando `GenericException` si la operación falla.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValueId** | `Long` | Identificador del valor a eliminar. |

Retorna: `void`.

Algoritmo:
1. Verifica que exista el registro con `selectionValueRepository.findById`.
2. Elimina el registro del repositorio JPA por id.
3. Si ocurre un error, lanza `GenericException`.

##### Método `deleteSelectionValuesByKey`

Elimina todos los valores de selección agrupados bajo una clave.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **key** | `String` | Clave de agrupación cuyos valores se eliminarán. |

Retorna: `void`.

Algoritmo:
1. Recupera todos los `SelectionValue` con `selectionValueRepository.findByTag(key)`.
2. Para cada uno, elimina el registro del repositorio JPA.

##### Método `insertSelectionValue`

Persiste un único `SelectionValue`, lanzando `GenericException` si la operación falla.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValue** | `SelectionValue` | Entidad con los datos a insertar. |

Retorna: `SelectionValue` — entidad persistida.

Algoritmo:
1. Invoca `selectionValueRepository.save(selectionValue)` y retorna el resultado.

##### Método `getAllSelectValues`

Retorna todos los valores de selección del sistema.

Retorna: `List<SelectionValue>` — lista completa.

Algoritmo:
1. Invoca `selectionValueRepository.allSelectionValue()` y retorna el resultado.

##### Método `insertMultipleSelectionValue`

Persiste una lista de `SelectionValue` en bloque.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sv** | `List<SelectionValue>` | Lista de entidades a insertar. |

Retorna: `List<SelectionValue>` — entidades persistidas.

Algoritmo:
1. Invoca `selectionValueRepository.saveAll(sv)` y retorna el resultado.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.domain.entity`

Contiene las entidades de dominio del módulo `apitableservices`: configuración de tablas y columnas, valores de celda y listas de valores de selección.

#### Clase `Column`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.domain.entity***
***Extends: AuditedDomain***

Representa la definición de una columna dentro de una tabla configurable, incluyendo metadatos de presentación, tipo de dato, validaciones y la lista de valores de selección asociada cuando el tipo es `SELECTION`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableFieldId** | `Long` | Get/Set | Identificador único de la columna. |
| **tableFieldCode** | `String` | Get/Set | Código de la columna usado para mapeo a campos de entidad. |
| **position** | `Integer` | Get/Set | Posición de visualización de la columna en la tabla. |
| **description** | `String` | Get/Set | Descripción legible de la columna. |
| **entityType** | `ColumnEntityType` | Get/Set | Tipo de entidad asociada a la columna. |
| **valueType** | `String` | Get/Set | Tipo de dato del valor de la columna (p. ej., `STRING`, `NUMBER`, `DATE`, `SELECTION`). |
| **toolTipText** | `String` | Get/Set | Texto del tooltip de la columna en la interfaz. |
| **defaultValue** | `String` | Get/Set | Valor por defecto de la columna. |
| **isVisible** | `boolean` | Get/Set | Indica si la columna es visible en la tabla. |
| **isMandatory** | `boolean` | Get/Set | Indica si la columna es obligatoria. |
| **isIdentity** | `boolean` | Get/Set | Indica si la columna actúa como campo de identidad. |
| **format** | `String` | Get/Set | Patrón de formato de visualización (p. ej., formato de fecha). |
| **regexp** | `String` | Get/Set | Expresión regular de validación del valor. |
| **selectionName** | `String` | Get/Set | Nombre de la lista de selección asociada. |
| **selectionValueList** | `List<SelectionValue>` | Get/Set | Lista de valores de selección disponibles para esta columna. |
| **path** | `String` | Get/Set | Ruta de acceso al campo en el objeto fuente (para tablas BPM o RDR). |

---

#### Clase `ColumnValue`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.domain.entity***
***Extends: AuditedDomain***

Representa el valor de una celda concreta de una fila de tabla, asociando el código de la columna con su valor actual.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableFieldCode** | `String` | Get/Set | Código de la columna a la que pertenece el valor. |
| **value** | `Object` | Get/Set | Valor de la celda; puede ser de cualquier tipo, serializado como `String` en la respuesta API. |

---

#### Clase `SelectionValue`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.domain.entity***
***Extends: AuditedDomain***

Representa un elemento de una lista de valores de selección (desplegable), identificado por una clave de agrupación y un identificador de valor.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **id** | `Long` | Get/Set | Identificador único del valor de selección. |
| **key** | `String` | Get/Set | Clave de agrupación que identifica la lista a la que pertenece este valor. |
| **valueId** | `String` | Get/Set | Identificador interno del valor dentro de la lista. |
| **value** | `String` | Get/Set | Texto descriptivo del valor de selección mostrado al usuario. |
| **position** | `Integer` | Get/Set | Posición de ordenación del elemento dentro de la lista. |

---

#### Clase `Table`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.domain.entity***
***Extends: AuditedDomain***

Representa la configuración completa de una tabla del módulo, incluyendo su tipo de origen de datos, las columnas que la componen y las opciones de presentación e interacción.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableId** | `Long` | Get/Set | Identificador único de la tabla. |
| **description** | `String` | Get/Set | Descripción legible de la tabla. |
| **entityName** | `String` | Get/Set | Nombre de la entidad JPA asociada (para tablas `DEFAULT` o `BUSINESS_DATA`). |
| **allowEditable** | `boolean` | Get/Set | Indica si la tabla permite edición de filas. |
| **allowActive** | `boolean` | Get/Set | Indica si la tabla permite activar/desactivar filas. |
| **allowNavigate** | `boolean` | Get/Set | Indica si la tabla permite navegar al detalle de una fila. |
| **visible** | `boolean` | Get/Set | Indica si la tabla es visible en la interfaz. |
| **selectable** | `boolean` | Get/Set | Indica si la tabla permite selección de filas. |
| **isFilter** | `Boolean` | Get/Set | Indica si la tabla tiene filtros habilitados. |
| **codeNavigateFields** | `List<String>` | Get/Set | Lista de códigos de campo usados para la navegación al detalle. |
| **tableFieldList** | `List<Column>` | Get/Set | Lista de columnas que componen la tabla. |
| **tableType** | `TableType` | Get/Set | Tipo de origen de datos de la tabla (`DEFAULT`, `BPM`, `BUSINESS_DATA`, `RDR`, `SLA`). |

**Enumerado `TableType`:**

| Valor | Código JSON | Descripción |
| :---: | :---: | ----- |
| `DEFAULT` | `"default"` | Tabla genérica desde repositorio JPA. |
| `BPM` | `"BPM"` | Tabla con datos provenientes del motor xBPM. |
| `BUSINESS_DATA` | `"businessData"` | Tabla con datos de negocio almacenados como JSON. |
| `RDR` | `"rdrParty"` | Tabla con datos de partes provenientes del sistema RDR. |
| `SLA` | `"SLA"` | Tabla de seguimiento de tiempos SLA. |

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.domain.entity.nodatabase`

Contiene enumerados de dominio del módulo `apitableservices` que no tienen representación en base de datos.

#### Enumerado `ColumnEntityType`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.domain.entity.nodatabase***

Enumerado que clasifica el tipo de entidad asociada a una columna de tabla. En la versión actual del código fuente no se definen constantes explícitas.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.listener`

Contiene el listener REST del módulo `apitableservices`, responsable de recibir las peticiones HTTP, delegar en el servicio de aplicación y transformar los resultados en DTOs de respuesta.

#### Clase `ListenerApiTable`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.listener***
***Implements: IRestListenerApitable***

Implementación del listener REST generado por NOVA para el API `apitable`. Actúa como adaptador entre la capa HTTP y el servicio `ITableService`, aplicando los mappers correspondientes para la conversión entre entidades de dominio y DTOs de la API.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableService** | `ITableService` | N/A | Servicio de aplicación principal del módulo. |
| **tableDtoMapper** | `TableDtoMapper` | N/A | Mapper entre `Table` y `TableConfigurationDto`. |
| **tableDataResponseMapper** | `TableDataResponseMapper` | N/A | Mapper entre `Page<List<ColumnValue>>` y `TableDataResponseDto`. |
| **selectionValueDtoMapper** | `SelectionValueDtoMapper` | N/A | Mapper entre `SelectionValue` y `SelectionValueItemDto`. |
| **inputSelectionValueDtoMapper** | `InputSelectionValueDtoMapper` | N/A | Mapper entre `InputItemSelectionValueDto` y `SelectionValue`. |

##### Método `getConfigurationById`

Recupera la configuración completa de una tabla y la retorna como DTO.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA. |
| **tableId** | `Float` | Identificador de la tabla. |

Retorna: `TableConfigurationDto` — configuración de la tabla como DTO.

Algoritmo:
1. Convierte `tableId` a `Long` e invoca `tableService.findById`.
2. Aplica `tableDtoMapper.toDto` sobre la entidad obtenida.
3. Retorna el DTO resultante.

##### Método `getAllKeys`

Retorna todos los identificadores de clave de selección registrados en el sistema.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA. |

Retorna: `String[]` — arreglo con todas las claves de selección únicas.

Algoritmo:
1. Invoca `tableService.getAllSelectValues()` para obtener todos los valores.
2. Extrae las claves únicas de la lista resultante.
3. Retorna el arreglo de claves.

##### Método `getSelectValues`

Retorna los valores de selección asociados a una clave concreta como arreglo de DTOs.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA. |
| **key** | `String` | Clave de la lista de selección. |

Retorna: `SelectionValueItemDto[]` — valores de selección como arreglo de DTOs.

Algoritmo:
1. Invoca `tableService.getSelectValues(key)`.
2. Mapea cada `SelectionValue` a `SelectionValueItemDto` con `selectionValueDtoMapper`.
3. Retorna el arreglo de DTOs.

##### Método `deleteSelectionValuesByKey`

Elimina todos los valores de selección asociados a una clave.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA. |
| **key** | `String` | Clave de agrupación. |

Retorna: `void`.

Algoritmo:
1. Invoca `tableService.deleteSelectionValuesByKey(key)`.

##### Método `deleteSelectionValueById`

Elimina un valor de selección por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA. |
| **selectionValueId** | `Long` | Identificador del valor a eliminar. |

Retorna: `void`.

Algoritmo:
1. Invoca `tableService.deleteSelectionValueById(selectionValueId)`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.mapper`

Contiene los mappers MapStruct para la conversión entre entidades de dominio y DTOs del API `apitable`.

#### Interfaz `ColumnDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.mapper***
***Implements: GenericDtoMapper<Column, ColumnDto>***

Mapper MapStruct que convierte entre la entidad de dominio `Column` y el DTO `ColumnDto`, resolviendo las discrepancias de nomenclatura entre los campos booleanos (`isVisible`/`visible`, `isMandatory`/`mandatory`, `isIdentity`/`identity`) y el campo `typeName`/`valueType`.

##### Método `toModel`

Convierte un `ColumnDto` en la entidad de dominio `Column`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **gridColumnDto** | `ColumnDto` | DTO de columna proveniente del API. |

Retorna: `Column` — entidad de dominio mapeada.

##### Método `toDto`

Convierte una entidad de dominio `Column` en un `ColumnDto`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **column** | `Column` | Entidad de dominio a convertir. |

Retorna: `ColumnDto` — DTO de columna para la respuesta API.

---

#### Interfaz `InputSelectionValueDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.mapper***
***Implements: GenericDtoMapper<SelectionValue, InputItemSelectionValueDto>***

Mapper MapStruct para la conversión entre `SelectionValue` y `InputItemSelectionValueDto`, utilizado al recibir nuevos valores de selección desde la API.

---

#### Interfaz `SelectionValueDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.mapper***
***Implements: GenericDtoMapper<SelectionValue, SelectionValueItemDto>***

Mapper MapStruct para la conversión entre `SelectionValue` y `SelectionValueItemDto`, utilizado en las respuestas del API de listas de selección.

---

#### Interfaz `TableDataResponseMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.mapper***
***Implements: GenericDtoMapper<ColumnValue, ColumnDataDto>***

Mapper MapStruct especializado en la construcción del DTO de respuesta de datos de tabla (`TableDataResponseDto`) a partir de una página de filas de dominio. Incluye métodos `default` para la construcción de la respuesta paginada y de las filas individuales.

##### Método `toDto`

Convierte un `ColumnValue` en un `ColumnDataDto`, transformando el valor a cadena vacía si es nulo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **columnValue** | `ColumnValue` | Valor de celda a convertir. |

Retorna: `ColumnDataDto` — DTO de celda con el valor serializado como `String`.

##### Método `toTableDataResponse`

Construye el `TableDataResponseDto` completo a partir de una página de filas de dominio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **page** | `Page<List<ColumnValue>>` | Página de filas de dominio. |

Retorna: `TableDataResponseDto` — DTO de respuesta con filas, total y metadatos de paginación.

Algoritmo:
1. Mapea cada fila de `page.getContent()` a `TableRowDto` con `toTableRowDto`.
2. Establece el total de elementos y la información de paginación en el DTO.
3. Retorna el `TableDataResponseDto` construido.

##### Método `toTableRowDto`

Convierte una lista de `ColumnValue` (fila) en un `TableRowDto`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **columnValues** | `List<ColumnValue>` | Lista de valores de celda que forman una fila. |

Retorna: `TableRowDto` — DTO de fila con los `ColumnDataDto` correspondientes.

Algoritmo:
1. Mapea cada `ColumnValue` a `ColumnDataDto` con `toDto`.
2. Agrupa los DTOs en un `TableRowDto` y lo retorna.

---

#### Interfaz `TableDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.mapper***
***Implements: GenericDtoMapper<Table, TableConfigurationDto>***

Mapper MapStruct para la conversión entre la entidad de dominio `Table` y el DTO `TableConfigurationDto`, resolviendo las discrepancias de nomenclatura en campos booleanos (`allowEditable`/`isAllowEditable`, etc.) e ignorando campos no mapeables en la dirección DTO → modelo.

##### Método `toDto`

Convierte una entidad `Table` en un `TableConfigurationDto`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **table** | `Table` | Entidad de dominio a convertir. |

Retorna: `TableConfigurationDto` — DTO de configuración de tabla.

##### Método `toModel`

Convierte un `TableConfigurationDto` en la entidad de dominio `Table`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **dto** | `TableConfigurationDto` | DTO de configuración de tabla. |

Retorna: `Table` — entidad de dominio mapeada.

##### Método `toUtilsList` (sobrecarga array)

Convierte un arreglo de `TableFilter` en una lista de `TableFilterUtils`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **filters** | `TableFilter[]` | Arreglo de filtros a convertir. |

Retorna: `List<TableFilterUtils>` — lista de utilidades de filtro.

Algoritmo:
1. Si `filters` es nulo, retorna una lista vacía.
2. Convierte el arreglo en lista con `Arrays.asList` y delega en el método `toUtilsList(List<TableFilter>)` generado por MapStruct.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository`

Contiene las interfaces de repositorio de infraestructura para el acceso a datos de tablas, columnas y valores de selección.

#### Interfaz `IColumnRepository`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository***

Define el contrato de acceso a datos para la entidad `Column`.

**Métodos:**

##### Método `findById`

Recupera una columna por identificador; lanza `EntityNotFoundException` si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la columna. |

Retorna: `Column` — entidad encontrada.

##### Método `allTableColumn`

Retorna todas las columnas del sistema.

Retorna: `List<Column>` — lista completa de columnas.

##### Método `findByTableId`

Retorna las columnas asociadas a una tabla concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableId** | `Long` | Identificador de la tabla. |

Retorna: `List<Column>` — columnas de la tabla.

##### Método `save`

Persiste o actualiza una columna.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **column** | `Column` | Entidad a persistir. |

Retorna: `Column` — entidad guardada.

---

#### Interfaz `ISelectionValueRepository`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository***

Define el contrato de acceso a datos para la entidad `SelectionValue`.

**Métodos:**

##### Método `findById`

Recupera un valor de selección por identificador; lanza `EntityNotFoundException` si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del valor de selección. |

Retorna: `SelectionValue` — entidad encontrada.

##### Método `findByTag`

Recupera todos los valores de selección asociados a una etiqueta/clave.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tag** | `String` | Etiqueta de agrupación. |

Retorna: `List<SelectionValue>` — valores asociados a la etiqueta.

##### Método `allSelectionValue`

Retorna todos los valores de selección del sistema.

Retorna: `List<SelectionValue>` — lista completa.

##### Método `saveAll`

Persiste una lista de valores de selección en bloque.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValues** | `List<SelectionValue>` | Lista de entidades a persistir. |

Retorna: `List<SelectionValue>` — entidades guardadas.

##### Método `save`

Persiste o actualiza un único valor de selección.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValue** | `SelectionValue` | Entidad a persistir. |

Retorna: `SelectionValue` — entidad guardada.

---

#### Interfaz `ITableRepository`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository***

Define el contrato de acceso a datos para la entidad `Table`.

**Métodos:**

##### Método `findById`

Recupera una tabla por identificador; lanza `EntityNotFoundException` si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la tabla. |

Retorna: `Table` — entidad encontrada.

##### Método `allTable`

Retorna todas las tablas del sistema.

Retorna: `List<Table>` — lista completa de tablas.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.impl`

Contiene las implementaciones concretas de los repositorios de infraestructura, delegando en repositorios JPA y aplicando los mappers de capa JPA para la conversión de entidades.

#### Clase `ColumnRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.impl***
***Implements: IColumnRepository***

Implementación del repositorio de columnas. Delega todas las operaciones en `ColumnRepositoryJpa` y aplica `ColumnMapper` para convertir entre entidades JPA y entidades de dominio.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **columnRepositoryJpa** | `ColumnRepositoryJpa` | N/A | Repositorio Spring Data JPA para columnas. |
| **columnMapper** | `ColumnMapper` | N/A | Mapper entre entidad JPA y entidad de dominio `Column`. |

##### Método `findById`

Busca una columna JPA por identificador y la convierte a dominio; lanza `EntityNotFoundException` si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la columna. |

Retorna: `Column` — entidad de dominio.

Algoritmo:
1. Invoca `columnRepositoryJpa.findById(id)`.
2. Si no está presente, lanza `EntityNotFoundException`.
3. Aplica `columnMapper.toDomain` y retorna la entidad de dominio.

##### Método `allTableColumn`

Retorna todas las columnas convirtiendo cada entidad JPA a dominio.

Retorna: `List<Column>` — lista de entidades de dominio.

Algoritmo:
1. Invoca `columnRepositoryJpa.findAll()`.
2. Mapea cada resultado con `columnMapper.toDomain` mediante stream y `collect`.

##### Método `findByTableId`

Retorna las columnas de una tabla concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tableId** | `Long` | Identificador de la tabla propietaria. |

Retorna: `List<Column>` — columnas de la tabla como entidades de dominio.

Algoritmo:
1. Invoca `columnRepositoryJpa.findByTableId(tableId)`.
2. Mapea cada resultado con `columnMapper.toDomain`.

##### Método `save`

Persiste una columna convirtiendo el dominio a JPA y retornando la entidad guardada como dominio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **column** | `Column` | Entidad de dominio a persistir. |

Retorna: `Column` — entidad de dominio persistida.

Algoritmo:
1. Convierte `column` a entidad JPA con `columnMapper.toJpa`.
2. Invoca `columnRepositoryJpa.save`.
3. Convierte el resultado a dominio con `columnMapper.toDomain` y lo retorna.

---

#### Clase `SelectionValueRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.impl***
***Implements: ISelectionValueRepository***

Implementación del repositorio de valores de selección. Gestiona la persistencia a través de `SelectionValueRepositoryJpa`, aplica `SelectionValueMapper` para conversión de entidades y utiliza `ObjectUpdater` para la actualización parcial de registros existentes.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **selectionValueRepositoryJpa** | `SelectionValueRepositoryJpa` | N/A | Repositorio Spring Data JPA para valores de selección. |
| **objectUpdater** | `ObjectUpdater` | N/A | Utilidad para copiar propiedades no nulas de un objeto a otro. |
| **selectionValueMapper** | `SelectionValueMapper` | N/A | Mapper entre entidad JPA y entidad de dominio `SelectionValue`. |

##### Método `findById`

Busca un valor de selección por identificador; lanza `EntityNotFoundException` si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del valor de selección. |

Retorna: `SelectionValue` — entidad de dominio.

Algoritmo:
1. Invoca `selectionValueRepositoryJpa.findById(id)`.
2. Si no está presente, lanza `EntityNotFoundException`.
3. Aplica `selectionValueMapper.toDomain` y retorna el resultado.

##### Método `findByTag`

Recupera todos los valores de selección con una etiqueta/clave concreta.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **tag** | `String` | Etiqueta de agrupación. |

Retorna: `List<SelectionValue>` — valores asociados a la etiqueta.

Algoritmo:
1. Invoca `selectionValueRepositoryJpa.findByKey(tag)`.
2. Mapea cada resultado con `selectionValueMapper.toDomain`.

##### Método `allSelectionValue`

Retorna todos los valores de selección del sistema.

Retorna: `List<SelectionValue>` — lista de entidades de dominio.

Algoritmo:
1. Invoca `selectionValueRepositoryJpa.findAll()`.
2. Mapea cada resultado con `selectionValueMapper.toDomain`.

##### Método `saveAll`

Persiste una lista de valores de selección en bloque.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValues** | `List<SelectionValue>` | Lista de entidades de dominio a persistir. |

Retorna: `List<SelectionValue>` — entidades persistidas.

Algoritmo:
1. Para cada elemento de `selectionValues`, invoca `prepareEntityForSave`.
2. Invoca `selectionValueRepositoryJpa.saveAll` con la lista de entidades JPA.
3. Mapea los resultados a dominio y retorna la lista.

##### Método `save`

Persiste o actualiza un único valor de selección.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValue** | `SelectionValue` | Entidad de dominio a persistir. |

Retorna: `SelectionValue` — entidad de dominio guardada.

Algoritmo:
1. Invoca `prepareEntityForSave(selectionValue)` para obtener la entidad JPA preparada.
2. Invoca `selectionValueRepositoryJpa.save`.
3. Mapea el resultado a dominio con `selectionValueMapper.toDomain` y lo retorna.

##### Método `prepareEntityForSave`

Prepara la entidad JPA para su persistencia, aplicando actualización parcial si ya existe en base de datos.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValue** | `SelectionValue` | Entidad de dominio con los datos a guardar. |

Retorna: `SelectionValueJpa` — entidad JPA lista para persistir.

Algoritmo:
1. Si `selectionValue.getId()` no es nulo, busca el registro existente en `selectionValueRepositoryJpa`.
2. Si existe, aplica `objectUpdater` para copiar las propiedades no nulas de `selectionValue` sobre la entidad JPA existente.
3. Si no existe o el id es nulo, convierte `selectionValue` a nueva entidad JPA con `selectionValueMapper.toJpa`.
4. Retorna la entidad JPA resultante.

---

#### Clase `TableRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.impl***
***Implements: ITableRepository***

Implementación del repositorio de tablas. Delega en `TableRepositoryJpa` y aplica `TableMapper` para convertir entre entidades JPA y entidades de dominio.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableRepositoryJpa** | `TableRepositoryJpa` | N/A | Repositorio Spring Data JPA para tablas. |
| **tableMapper** | `TableMapper` | N/A | Mapper entre entidad JPA y entidad de dominio `Table`. |

##### Método `findById`

Busca una tabla JPA por identificador y la convierte a dominio; lanza `EntityNotFoundException` si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la tabla. |

Retorna: `Table` — entidad de dominio.

Algoritmo:
1. Invoca `tableRepositoryJpa.findById(id)`.
2. Si no está presente, lanza `EntityNotFoundException`.
3. Aplica `tableMapper.toDomain` y retorna el resultado.

##### Método `allTable`

Retorna todas las tablas convirtiendo cada entidad JPA a dominio.

Retorna: `List<Table>` — lista de entidades de dominio.

Algoritmo:
1. Invoca `tableRepositoryJpa.findAll()`.
2. Mapea cada resultado con `tableMapper.toDomain` mediante stream y `collect`.

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa`

Contiene las entidades JPA y los repositorios Spring Data para la persistencia de tablas, columnas y valores de selección del módulo de servicios de tabla.

#### Clase `ColumnJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que mapea la tabla `TWGTBCOL`. Representa la definición de una columna perteneciente a una tabla dinámica, incluyendo su tipo de dato, visibilidad, obligatoriedad, formato y valores de selección asociados.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **columnId** | `Long` | Get/Set | Identificador único de la columna (`COD_OID_COL`), generado por secuencia `QWGTBCOL1`. |
| **table** | `TableJpa` | Get/Set | Referencia perezosa a la tabla propietaria de la columna (`COD_OID_TAB`). |
| **tableFieldCode** | `String` | Get/Set | Nombre del campo en la entidad destino (`DES_FLD_NAME`). |
| **position** | `Integer` | Get/Set | Posición ordinal de la columna dentro de la tabla (`COD_COLPOS`). |
| **description** | `String` | Get/Set | Descripción textual de la columna (`DES_COL_DET`). |
| **entityType** | `ColumnEntityType` | Get/Set | Tipo de entidad de la columna, almacenado como `String` (`DES_ENT_TP`). |
| **valueType** | `String` | Get/Set | Tipo de valor de la columna (`DES_VALUE_TP`). |
| **toolTipText** | `String` | Get/Set | Texto de ayuda emergente (`DES_TTIP_TXT`). |
| **defaultValue** | `String` | Get/Set | Valor predeterminado del campo (`DES_DEFVAL`). |
| **isVisible** | `boolean` | Get/Set | Indica si la columna es visible; almacenado como `Y`/`N` (`XTI_VISIBLE`). |
| **isMandatory** | `boolean` | Get/Set | Indica si la columna es obligatoria; almacenado como `Y`/`N` (`XTI_MANDTRY`). |
| **isIdentity** | `boolean` | Get/Set | Indica si la columna actúa como campo identidad; almacenado como `Y`/`N` (`XTI_IDENTITY`). |
| **format** | `String` | Get/Set | Formato de visualización del valor (`DES_COL_FMAT`). |
| **regexp** | `String` | Get/Set | Expresión regular de validación (`DES_REGEXP`). |
| **selectionName** | `String` | Get/Set | Nombre del catálogo de selección asociado (`DES_SELNAME`). |
| **path** | `String` | Get/Set | Ruta del campo en la estructura de la entidad (`DES_FLD_PTH`). |
| **selectionValueList** | `List<SelectionValueJpa>` | Get/Set | Lista de valores de selección asociados a esta columna; relación `@OneToMany` con eliminación en cascada. |

---

#### Clase `ColumnRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa***

Repositorio Spring Data JPA para la entidad `ColumnJpa`. Proporciona operaciones CRUD estándar y una consulta derivada para recuperar columnas por tabla.

##### Método `findByTable_TableId`

Recupera todas las columnas asociadas a una tabla específica mediante su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **Id** | `Long` | Identificador de la tabla propietaria. |

Retorna: `List<ColumnJpa>` — lista de columnas pertenecientes a la tabla indicada.

Algoritmo:
1. Ejecuta una consulta derivada de Spring Data que filtra `ColumnJpa` por `table.tableId` igual al valor proporcionado.

---

#### Clase `SelectionValueJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que mapea la tabla `TWGTBSEL`. Almacena cada par clave-valor que compone un catálogo de selección vinculado a una columna dinámica.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **selectionValueId** | `Long` | Get/Set | Identificador único del valor de selección (`COD_OID_SL_V`), generado por secuencia `QWGTBSEL1`. |
| **column** | `ColumnJpa` | Get/Set | Referencia perezosa a la columna propietaria (`COD_OID_COL`). |
| **key** | `String` | Get/Set | Clave interna del elemento de selección (`DES_SLCT_KEY`). |
| **selectionValue** | `String` | Get/Set | Valor descriptivo mostrado al usuario (`DES_SLCT_VAL`). |
| **selectionKey** | `String` | Get/Set | Clave de validación del elemento de selección (`DES_SLCT_VLD`). |
| **valueId** | `String` | Get/Set | Identificador del valor en el sistema origen (`DES_FS_KEY`). |
| **value** | `String` | Get/Set | Valor en el sistema origen (`DES_FS_VAL`). |
| **position** | `Integer` | Get/Set | Posición ordinal del valor dentro del catálogo (`COD_SLCT_POS`). |

---

#### Clase `SelectionValueRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa***

Repositorio Spring Data JPA para la entidad `SelectionValueJpa`. Expone operaciones CRUD estándar y una consulta derivada por clave de selección.

##### Método `findBySelectionKey`

Recupera todos los valores de selección que coincidan con una clave de validación dada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionKey** | `String` | Clave de validación por la que se filtra. |

Retorna: `List<SelectionValueJpa>` — lista de valores de selección con la clave indicada.

Algoritmo:
1. Ejecuta una consulta derivada de Spring Data que filtra `SelectionValueJpa` por el campo `selectionKey` igual al valor proporcionado.

---

#### Clase `TableJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que mapea la tabla `TWGTBTAB`. Representa la definición de una tabla dinámica, incluyendo sus permisos de edición, navegación, filtrado y la lista de columnas asociadas. Contiene un convertidor interno `TableTypeConverter` para serializar el enum `TableType`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableId** | `Long` | Get/Set | Identificador único de la tabla (`COD_OID_TAB`), generado por secuencia `QWGTBTAB1`. |
| **description** | `String` | Get/Set | Descripción textual de la tabla (`DES_TAB_DESC`). |
| **entityName** | `String` | Get/Set | Nombre de la entidad de negocio asociada (`DES_ENT_NAME`). |
| **isAllowEditable** | `Boolean` | Get/Set | Indica si la tabla permite edición; almacenado como `Y`/`N` (`XTI_EDITABLE`). |
| **isAllowActive** | `Boolean` | Get/Set | Indica si la tabla permite activación; almacenado como `Y`/`N` (`XTI_ACTIVE`). |
| **isAllowNavigate** | `Boolean` | Get/Set | Indica si la tabla permite navegación; almacenado como `Y`/`N` (`XTI_NAVIGATE`). |
| **isFilter** | `Boolean` | Get/Set | Indica si la tabla tiene filtro habilitado; almacenado como `Y`/`N` (`XTI_FILTER`). |
| **isVisible** | `Boolean` | Get/Set | Indica si la tabla es visible; almacenado como `Y`/`N` (`XTI_VISIBLE`). |
| **isSelectable** | `Boolean` | Get/Set | Indica si la tabla es seleccionable; almacenado como `Y`/`N` (`XTI_SLCTABLE`). |
| **tableType** | `TableType` | Get/Set | Tipo de tabla, convertido mediante `TableTypeConverter`; valor por defecto `DEFAULT` (`DES_TB_TYPE`). |
| **codeNavigateFields** | `List<String>` | Get/Set | Lista de campos usados en la navegación, almacenada como cadena serializada (`DES_NVGT_FIE`). |
| **columns** | `List<ColumnJpa>` | Get/Set | Lista de columnas de la tabla; relación `@OneToMany` con eliminación en cascada. |

---

#### Clase `TableRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa***

Repositorio Spring Data JPA para la entidad `TableJpa`. Sobreescribe `findById` para cargar eagerly las columnas asociadas mediante un `@EntityGraph`.

##### Método `findById`

Recupera una tabla por su identificador incluyendo en la misma consulta la colección de columnas.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la tabla a recuperar. |

Retorna: `Optional<TableJpa>` — tabla con sus columnas cargadas, o vacío si no existe.

Algoritmo:
1. Aplica el `@EntityGraph` con `attributePaths = "columns"` para forzar la carga inmediata de la colección.
2. Ejecuta la consulta por clave primaria y envuelve el resultado en un `Optional`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa.mapper`

Contiene los mappers MapStruct que convierten entre las entidades JPA del módulo de servicios de tabla y los modelos de dominio correspondientes.

#### Clase `ColumnMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa.mapper***

Interfaz MapStruct para la conversión bidireccional entre `Column` (dominio) y `ColumnJpa` (persistencia). Delega la conversión de valores de selección a `SelectionValueMapper`.

##### Método `toTableColumnJpaList`

Convierte una lista de modelos de dominio `Column` a su representación JPA.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **columns** | `List<Column>` | Lista de modelos de dominio a convertir. |

Retorna: `List<ColumnJpa>` — lista de entidades JPA equivalentes.

Algoritmo:
1. Itera cada elemento de la lista y aplica `toTableColumnJpa` por delegación de MapStruct.

##### Método `toTableColumnList`

Convierte una lista de entidades JPA `ColumnJpa` a modelos de dominio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **columnJpas** | `List<ColumnJpa>` | Lista de entidades JPA a convertir. |

Retorna: `List<Column>` — lista de modelos de dominio equivalentes.

Algoritmo:
1. Itera cada elemento de la lista y aplica `toTableColumn` por delegación de MapStruct.

##### Método `toTableColumn`

Convierte una entidad `ColumnJpa` a modelo de dominio `Column`, mapeando `columnId` al campo `tableFieldId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **jpa** | `ColumnJpa` | Entidad JPA origen. |

Retorna: `Column` — modelo de dominio resultante.

Algoritmo:
1. Copia todos los campos con nombre equivalente de forma automática.
2. Asigna `jpa.columnId` → `Column.tableFieldId` según la anotación `@Mapping`.

##### Método `toTableColumnJpa`

Convierte un modelo de dominio `Column` a entidad JPA `ColumnJpa`, mapeando `tableFieldId` al campo `columnId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **domain** | `Column` | Modelo de dominio origen. |

Retorna: `ColumnJpa` — entidad JPA resultante.

Algoritmo:
1. Copia todos los campos con nombre equivalente de forma automática.
2. Asigna `domain.tableFieldId` → `ColumnJpa.columnId` según la anotación `@Mapping`.

---

#### Clase `SelectionValueMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa.mapper***

Interfaz MapStruct que implementa `GenericEntityMapper` para la conversión bidireccional entre `SelectionValue` (dominio) y `SelectionValueJpa` (persistencia), aplicando las reglas de mapeo de campos renombrados.

##### Método `toModel`

Convierte una entidad `SelectionValueJpa` a modelo de dominio `SelectionValue`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **selectionValueJpa** | `SelectionValueJpa` | Entidad JPA origen. |

Retorna: `SelectionValue` — modelo de dominio resultante.

Algoritmo:
1. Asigna `selectionValueId` → `id`.
2. Asigna `selectionKey` → `key`.
3. Asigna `valueId` → `valueId`.
4. Asigna `selectionValue` → `value`.
5. Copia el resto de campos con nombre equivalente.

##### Método `toEntity`

Convierte un modelo de dominio `SelectionValue` a entidad JPA `SelectionValueJpa`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **model** | `SelectionValue` | Modelo de dominio origen. |

Retorna: `SelectionValueJpa` — entidad JPA resultante.

Algoritmo:
1. Asigna `key` → `key` y también → `selectionKey`.
2. Asigna `value` → `selectionValue`.
3. Asigna `position` con valor por defecto `0` si es nulo.
4. Copia el resto de campos con nombre equivalente.

---

#### Clase `TableMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitableservices.infrastructure.repository.jpa.mapper***

Interfaz MapStruct para la conversión bidireccional entre `Table` (dominio) y `TableJpa` (persistencia), gestionando el renombrado de campos booleanos y la lista de columnas. Delega el mapeo de columnas a `ColumnMapper`.

##### Método `toTable`

Convierte una entidad `TableJpa` a modelo de dominio `Table`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **jpa** | `TableJpa` | Entidad JPA origen. |

Retorna: `Table` — modelo de dominio resultante.

Algoritmo:
1. Asigna los campos booleanos renombrados: `isAllowEditable` → `allowEditable`, `isAllowActive` → `allowActive`, `isAllowNavigate` → `allowNavigate`, `isVisible` → `visible`, `isSelectable` → `selectable`.
2. Asigna `columns` → `tableFieldList`.
3. Copia el resto de campos con nombre equivalente.

##### Método `toTableJpa`

Convierte un modelo de dominio `Table` a entidad JPA `TableJpa`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **domain** | `Table` | Modelo de dominio origen. |

Retorna: `TableJpa` — entidad JPA resultante.

Algoritmo:
1. Asigna los campos booleanos renombrados en sentido inverso: `allowEditable` → `isAllowEditable`, etc.
2. Asigna `tableFieldList` → `columns`.
3. Copia el resto de campos con nombre equivalente.

##### Método `toTableList`

Convierte una lista de entidades `TableJpa` a modelos de dominio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **jpas** | `List<TableJpa>` | Lista de entidades JPA a convertir. |

Retorna: `List<Table>` — lista de modelos de dominio equivalentes.

Algoritmo:
1. Itera cada elemento y aplica `toTable` por delegación de MapStruct.

##### Método `toTableJpaList`

Convierte una lista de modelos de dominio `Table` a entidades JPA.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **domains** | `List<Table>` | Lista de modelos de dominio a convertir. |

Retorna: `List<TableJpa>` — lista de entidades JPA equivalentes.

Algoritmo:
1. Itera cada elemento y aplica `toTableJpa` por delegación de MapStruct.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.application`

Define los contratos de servicio de aplicación para la gestión de plantillas, secciones y valores de sección del módulo de templates.

#### Clase `ISectionService`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.application***

Interfaz de servicio de aplicación que expone las operaciones de consulta sobre secciones de plantilla.

##### Método `findById`

Recupera una sección por su identificador único.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la sección a recuperar. |

Retorna: `Section` — entidad de dominio con los datos de la sección.

Lanza: `EntityNotFoundException` si no existe ninguna sección con el identificador indicado.

##### Método `allSection`

Recupera la lista completa de secciones registradas.

Retorna: `List<Section>` — lista de todas las secciones disponibles.

---

#### Clase `ISectionValueService`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.application***

Interfaz de servicio de aplicación que expone las operaciones de consulta sobre valores de sección.

##### Método `findById`

Recupera un valor de sección por su identificador único.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del valor de sección a recuperar. |

Retorna: `SectionValue` — entidad de dominio con los datos del valor.

Lanza: `EntityNotFoundException` si no existe ningún valor con el identificador indicado.

##### Método `findByFieldCode`

Recupera un valor de sección mediante el código de campo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo a buscar. |

Retorna: `SectionValue` — entidad de dominio correspondiente al código indicado.

Lanza: `GenericException` si no se encuentra ningún valor con ese código.

##### Método `allSectionValue`

Recupera la lista completa de valores de sección registrados.

Retorna: `List<SectionValue>` — lista de todos los valores de sección disponibles.

---

#### Clase `ITemplateService`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.application***

Interfaz de servicio de aplicación que expone la operación de recuperación de plantillas, con soporte para resolución de valores dinámicos a partir de una entidad de negocio.

##### Método `findById`

Recupera una plantilla por su identificador, opcionalmente resolviendo valores dinámicos a partir de la entidad identificada por `entityId`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la plantilla a recuperar. |
| **entityId** | `String` | Identificador de la entidad de negocio para resolver valores dinámicos (opcional, puede ser `null`). |

Retorna: `Template` — plantilla con sus secciones y valores, potencialmente enriquecidos con datos de negocio.

Lanza: `GenericException` si la plantilla no existe o se produce un error durante la resolución de valores.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.application.impl`

Contiene las implementaciones concretas de los servicios de aplicación del módulo de templates.

#### Clase `SectionServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.application.impl***
***Implements: ISectionService***

Implementación del servicio de secciones. Delega las operaciones de persistencia en `ISectionRepository`.

##### Método `findById`

Recupera una sección por su identificador, lanzando una excepción si no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la sección a recuperar. |

Retorna: `Section` — entidad de dominio de la sección encontrada.

Lanza: `EntityNotFoundException` si no se encuentra ninguna sección con el identificador dado.

Algoritmo:
1. Invoca `sectionRepository.findById(id)`.
2. Si no existe resultado, lanza `EntityNotFoundException`.
3. Retorna la sección encontrada.

##### Método `allSection`

Recupera todas las secciones disponibles.

Retorna: `List<Section>` — lista completa de secciones.

Algoritmo:
1. Invoca `sectionRepository.allSection()` y retorna el resultado directamente.

---

#### Clase `SectionValueServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.application.impl***
***Implements: ISectionValueService***

Implementación del servicio de valores de sección. Delega en `ISectionValueRepository` para todas las operaciones de acceso a datos.

##### Método `findById`

Recupera un valor de sección por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del valor de sección. |

Retorna: `SectionValue` — entidad de dominio encontrada.

Lanza: `EntityNotFoundException` si no existe ningún valor con ese identificador.

Algoritmo:
1. Invoca `sectionValueRepository.findById(id)`.
2. Si no existe resultado, lanza `EntityNotFoundException`.
3. Retorna el valor encontrado.

##### Método `findByFieldCode`

Recupera un valor de sección mediante el código de campo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo a buscar. |

Retorna: `SectionValue` — entidad de dominio correspondiente.

Lanza: `GenericException` si no se encuentra ningún valor con ese código.

Algoritmo:
1. Invoca `sectionValueRepository.findByFieldCode(fieldCode)`.
2. Si no existe resultado, lanza `GenericException`.
3. Retorna el valor encontrado.

##### Método `allSectionValue`

Recupera todos los valores de sección registrados.

Retorna: `List<SectionValue>` — lista completa de valores de sección.

Algoritmo:
1. Invoca `sectionValueRepository.allSectionValue()` y retorna el resultado directamente.

---

#### Clase `TemplateServiceImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.application.impl***
***Implements: ITemplateService***

Implementación del servicio de plantillas. Orquesta la recuperación de la plantilla base desde `ITemplateRepository` y, cuando el tipo es `BUSINESS_DATA`, enriquece los valores de cada sección con datos obtenidos de `IBusinessDataRepository` a través de `EntityScrapper`.

##### Método `findById`

Punto de entrada principal para obtener una plantilla. Discrimina entre plantilla estática y plantilla con datos de negocio según el `templateType`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la plantilla. |
| **entityId** | `String` | Identificador de la entidad de negocio para resolución de valores dinámicos. |

Retorna: `Template` — plantilla completa con valores resueltos.

Lanza: `GenericException` si la plantilla no existe o falla la resolución de datos de negocio.

Algoritmo:
1. Recupera la plantilla base invocando `templateRepository.findById(id)`.
2. Si el `templateType` es `BUSINESS_DATA`, delega en `getBusinessDataTemplate(id, entityId)`.
3. En caso contrario, retorna la plantilla tal como fue recuperada.

##### Método `getBusinessDataTemplate`

Enriquece una plantilla de tipo `BUSINESS_DATA` con los valores obtenidos de la entidad de negocio identificada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la plantilla. |
| **entityId** | `String` | Identificador de la entidad de negocio. |

Retorna: `Template` — plantilla con los valores de sección resueltos desde `BusinessData`.

Lanza: `GenericException` si no se pueden obtener los datos de negocio.

Algoritmo:
1. Obtiene la plantilla base con `templateRepository.findById(id)`.
2. Recupera la entidad `BusinessData` usando la consulta SQL almacenada en la plantilla a través de `templateRepository.callGenericEntity`.
3. Itera sobre cada `Section` de la plantilla y, para cada `SectionValue`, invoca `resolveBusinessValue`.
4. Asigna el valor resuelto al `SectionValue` correspondiente.
5. Retorna la plantilla enriquecida.

##### Método `resolveBusinessValue`

Resuelve el valor dinámico de un `SectionValue` buscando el campo correspondiente en la instancia de `BusinessData`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionValue** | `SectionValue` | Valor de sección cuyo campo se va a resolver. |
| **businessData** | `BusinessData` | Instancia de datos de negocio origen. |

Retorna: `String` — valor del campo resuelto, o `null` si no se encuentra.

Algoritmo:
1. Obtiene el `fieldCode` del `SectionValue`.
2. Verifica si ese código corresponde a un campo declarado en `BusinessData` usando la lista precalculada de nombres de campo.
3. Si existe, utiliza `EntityScrapper` para extraer el valor del campo por reflexión.
4. Retorna el valor como `String`, o `null` si el campo no existe o su valor es nulo.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.domain.entity.nodatabase`

Contiene los tipos enumerados del dominio de templates que no tienen representación directa en base de datos como tablas independientes.

#### Clase `SectionValueEntityType`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.domain.entity.nodatabase***

Enumerado que define los tipos de entidad posibles para un valor de sección. Actualmente declara el valor `SELECTOR`, indicando que el campo se comporta como un selector de opciones.

**Valores:**

| Valor | Descripción |
| :---: | ----- |
| `SELECTOR` | El valor de sección es de tipo selector (lista de opciones). |

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.domain.entity`

Contiene las entidades de dominio del módulo de templates: plantillas, secciones y valores de sección.

#### Clase `Section`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.domain.entity***
***Extends: AuditedDomain***

Modelo de dominio que representa una sección dentro de una plantilla. Agrupa una lista de `SectionValue` bajo un título descriptivo.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **sectionId** | `Long` | Get/Set | Identificador único de la sección. |
| **title** | `String` | Get/Set | Título descriptivo que se muestra como encabezado de la sección. |
| **sectionValues** | `List<SectionValue>` | Get/Set | Lista de valores de campo que componen la sección. |

---

#### Clase `SectionValue`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.domain.entity***
***Extends: AuditedDomain***

Modelo de dominio que representa un campo individual dentro de una sección de plantilla, con su etiqueta, código de campo, tipo de valor y valor actual.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **sectionValueId** | `Long` | Get/Set | Identificador único del valor de sección. |
| **title** | `String` | Get/Set | Etiqueta descriptiva del campo mostrada al usuario. |
| **fieldCode** | `String` | Get/Set | Código técnico del campo usado para la resolución dinámica. |
| **valueType** | `String` | Get/Set | Tipo de valor del campo (p. ej. texto, selector). |
| **value** | `String` | Get/Set | Valor actual del campo; puede ser estático o resuelto dinámicamente. |
| **isVisible** | `Boolean` | Get/Set | Indica si el campo es visible para el usuario. |

---

#### Clase `Template`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.domain.entity***
***Extends: AuditedDomain***

Modelo de dominio que representa una plantilla completa, compuesta por secciones. Distingue entre plantillas estáticas (`DEFAULT`) y plantillas con datos de negocio (`BUSINESS_DATA`) mediante el enum interno `TemplateType`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **templateId** | `Long` | Get/Set | Identificador único de la plantilla. |
| **sqlQuery** | `String` | Get/Set | Consulta SQL para obtener datos dinámicos (opcional). |
| **title** | `String` | Get/Set | Título descriptivo de la plantilla. |
| **hasData** | `Boolean` | Get/Set | Indica si la plantilla tiene datos asociados. |
| **sections** | `List<Section>` | Get/Set | Lista de secciones que componen la plantilla. |
| **templateType** | `Template.TemplateType` | Get/Set | Tipo de plantilla (`DEFAULT` o `BUSINESS_DATA`). |

**Enum interno `TemplateType`:**

| Valor | String serializado | Descripción |
| :---: | :---: | ----- |
| `DEFAULT` | `"default"` | Plantilla estática sin datos de negocio. |
| `BUSINESS_DATA` | `"businessData"` | Plantilla con valores resueltos desde una entidad de negocio. |

##### Método `getValue` (TemplateType)

Retorna la representación en cadena del tipo de plantilla, usada por Jackson para la serialización JSON mediante `@JsonValue`.

Retorna: `String` — cadena asociada al valor del enum (`"default"` o `"businessData"`).

Algoritmo:
1. Retorna el campo `value` almacenado en la instancia del enum.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.listener`

Contiene el listener REST del módulo de templates, responsable de recibir las peticiones HTTP y delegar en el servicio de aplicación.

#### Clase `ListenerApiTemplates`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.listener***
***Implements: IRestListenerApitemplates***

Listener REST generado por NOVA que implementa el contrato de la API de templates. Recibe la petición de obtención de una plantilla, invoca `ITemplateService` y traduce el resultado a `TemplateDto` mediante `TemplateDtoMapper`. En caso de error, construye la respuesta de error estándar con `GenericApiErrorBuilder`.

##### Método `getTemplateById`

Recupera una plantilla por su identificador y opcionalmente resuelve valores dinámicos para la entidad indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos de la petición NOVA (trazabilidad, contexto). |
| **templateId** | `Float` | Identificador de la plantilla solicitada (convertido a `Long` internamente). |
| **entityId** | `String` | Identificador de la entidad de negocio para resolución de valores dinámicos (opcional). |

Retorna: `TemplateDto` — representación DTO de la plantilla con sus secciones y valores.

Algoritmo:
1. Convierte `templateId` de `Float` a `Long`.
2. Invoca `templateService.findById(id, entityId)`.
3. Transforma el resultado a `TemplateDto` usando `templateDtoMapper.toDto()`.
4. En caso de `GenericException`, construye y lanza la excepción de API correspondiente usando `GenericApiErrorBuilder`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.mapper`

Contiene los mappers MapStruct que convierten entre los modelos de dominio del módulo de templates y sus representaciones DTO para la capa de API REST.

#### Clase `SectionDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.mapper***

Interfaz MapStruct que implementa `GenericDtoMapper` para la conversión bidireccional entre `Section` y `SectionDto`. Delega la conversión de valores en `SectionValueDtoMapper`.

##### Método `toModel`

Convierte un `SectionDto` a modelo de dominio `Section`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionDto** | `SectionDto` | DTO de entrada desde la capa de API. |

Retorna: `Section` — modelo de dominio equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente; delega la lista de valores en `SectionValueDtoMapper`.

##### Método `toDto`

Convierte un modelo de dominio `Section` a `SectionDto`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **section** | `Section` | Modelo de dominio origen. |

Retorna: `SectionDto` — DTO equivalente para la capa de API.

Algoritmo:
1. Copia todos los campos con nombre equivalente; delega la lista de valores en `SectionValueDtoMapper`.

---

#### Clase `SectionValueDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.mapper***

Interfaz MapStruct que implementa `GenericDtoMapper` para la conversión bidireccional entre `SectionValue` y `SectionValueDto`.

##### Método `toModel`

Convierte un `SectionValueDto` a modelo de dominio `SectionValue`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionValueDto** | `SectionValueDto` | DTO de entrada. |

Retorna: `SectionValue` — modelo de dominio equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente mediante MapStruct.

##### Método `toDto`

Convierte un modelo de dominio `SectionValue` a `SectionValueDto`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionValue** | `SectionValue` | Modelo de dominio origen. |

Retorna: `SectionValueDto` — DTO equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente mediante MapStruct.

---

#### Clase `TemplateDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.mapper***

Interfaz MapStruct que implementa `GenericDtoMapper` para la conversión bidireccional entre `Template` y `TemplateDto`. Delega la conversión de secciones en `SectionDtoMapper` e ignora el campo `sqlQuery` al convertir desde DTO por razones de seguridad.

##### Método `toModel`

Convierte un `TemplateDto` a modelo de dominio `Template`, ignorando el campo `sqlQuery`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **templateDto** | `TemplateDto` | DTO de entrada. |

Retorna: `Template` — modelo de dominio con `sqlQuery` ignorado.

Algoritmo:
1. Copia todos los campos con nombre equivalente.
2. Omite la asignación de `sqlQuery` (marcado con `ignore = true`).
3. Delega la lista de secciones en `SectionDtoMapper`.

##### Método `toDto`

Convierte un modelo de dominio `Template` a `TemplateDto`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **template** | `Template` | Modelo de dominio origen. |

Retorna: `TemplateDto` — DTO equivalente para la capa de API.

Algoritmo:
1. Copia todos los campos con nombre equivalente.
2. Delega la lista de secciones en `SectionDtoMapper`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository`

Define los contratos de repositorio de infraestructura para el acceso a datos del módulo de templates.

#### Clase `ISectionRepository`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository***

Interfaz de repositorio que abstrae las operaciones de lectura sobre secciones de plantilla.

##### Método `findById`

Busca una sección por identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la sección. |

Retorna: `Section` — entidad de dominio encontrada.

Lanza: `EntityNotFoundException` si no existe.

##### Método `allSection`

Retorna: `List<Section>` — lista completa de secciones.

---

#### Clase `ISectionValueRepository`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository***

Interfaz de repositorio para el acceso a valores de sección, con soporte de búsqueda por código de campo.

##### Método `findById`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del valor de sección. |

Retorna: `SectionValue` — entidad de dominio encontrada.

Lanza: `EntityNotFoundException` si no existe.

##### Método `findByFieldCode`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo a buscar. |

Retorna: `SectionValue` — entidad de dominio correspondiente.

Lanza: `GenericException` si no se encuentra.

##### Método `allSectionValue`

Retorna: `List<SectionValue>` — lista completa de valores de sección.

---

#### Clase `ITemplateRepository`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository***

Interfaz de repositorio para el acceso a plantillas, incluyendo soporte para la ejecución de consultas genéricas sobre entidades de negocio.

##### Método `findById`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la plantilla. |

Retorna: `Template` — plantilla encontrada.

Lanza: `EntityNotFoundException` si no existe.

##### Método `allTemplate`

Retorna: `List<Template>` — lista completa de plantillas.

##### Método `callGenericEntity`

Ejecuta una consulta genérica sobre una entidad de negocio identificada por su nombre o JPQL y un identificador de instancia.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **entityName** | `String` | Nombre de la entidad o fragmento de consulta JPQL. |
| **entityId** | `String` | Identificador de la instancia a recuperar. |

Retorna: `Object` — instancia de la entidad recuperada.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.impl`

Contiene las implementaciones concretas de los repositorios de infraestructura del módulo de templates.

#### Clase `SectionRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.impl***
***Implements: ISectionRepository***

Implementación del repositorio de secciones. Delega en `SectionRepositoryJpa` para las operaciones JPA y usa `SectionMapper` para la conversión de entidades.

##### Método `findById`

Recupera una sección JPA por su identificador y la convierte al modelo de dominio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la sección. |

Retorna: `Section` — modelo de dominio resultante.

Lanza: `EntityNotFoundException` si no existe ninguna sección con ese identificador.

Algoritmo:
1. Invoca `sectionRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Convierte la entidad JPA a dominio con `sectionMapper.toSection()` y la retorna.

##### Método `allSection`

Recupera todas las secciones y las convierte al modelo de dominio.

Retorna: `List<Section>` — lista de modelos de dominio.

Algoritmo:
1. Invoca `sectionRepositoryJpa.findAll()`.
2. Convierte cada `SectionJpa` a `Section` usando `sectionMapper` y recopila los resultados en una lista.

---

#### Clase `SectionValueRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.impl***
***Implements: ISectionValueRepository***

Implementación del repositorio de valores de sección. Delega en `SectionValueRepositoryJpa` y usa `SectionValueMapper` para la conversión.

##### Método `findById`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador del valor de sección. |

Retorna: `SectionValue` — modelo de dominio encontrado.

Lanza: `EntityNotFoundException` si no existe.

Algoritmo:
1. Invoca `sectionValueRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Convierte con `sectionValueMapper.toSectionValue()` y retorna.

##### Método `findByFieldCode`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo a buscar. |

Retorna: `SectionValue` — modelo de dominio encontrado.

Lanza: `GenericException` si no existe ningún valor con ese código.

Algoritmo:
1. Invoca `sectionValueRepositoryJpa.findByFieldCode(fieldCode)`.
2. Si el `Optional` está vacío, lanza `GenericException`.
3. Convierte con `sectionValueMapper.toSectionValue()` y retorna.

##### Método `allSectionValue`

Retorna: `List<SectionValue>` — lista completa de valores de sección.

Algoritmo:
1. Invoca `sectionValueRepositoryJpa.findAll()`.
2. Convierte cada `SectionValueJpa` a `SectionValue` usando `sectionValueMapper` y recopila en lista.

---

#### Clase `TemplateRepositoryImpl`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.impl***
***Implements: ITemplateRepository***

Implementación del repositorio de plantillas. Además de las operaciones CRUD estándar delegadas en `TemplateRepositoryJpa`, expone la capacidad de ejecutar consultas JPQL dinámicas sobre entidades de negocio mediante `EntityManager`.

##### Método `findById`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Long` | Identificador de la plantilla. |

Retorna: `Template` — modelo de dominio encontrado.

Lanza: `EntityNotFoundException` si no existe.

Algoritmo:
1. Invoca `templateRepositoryJpa.findById(id)`.
2. Si el `Optional` está vacío, lanza `EntityNotFoundException`.
3. Convierte con `templateMapper.toTemplate()` y retorna.

##### Método `allTemplate`

Retorna: `List<Template>` — lista completa de plantillas.

Algoritmo:
1. Invoca `templateRepositoryJpa.findAll()`.
2. Convierte cada `TemplateJpa` a `Template` usando `templateMapper` y recopila en lista.

##### Método `callGenericEntity`

Ejecuta una consulta JPQL dinámica sobre una entidad de negocio y retorna la primera instancia que coincida con el identificador dado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **jpql** | `String` | Cadena de consulta JPQL o nombre de entidad usado para construirla. |
| **entityId** | `String` | Identificador de la instancia a recuperar. |

Retorna: `Object` — instancia de la entidad recuperada por la consulta.

Algoritmo:
1. Construye un `TypedQuery` a partir del JPQL usando `entityManager.createQuery()`.
2. Establece el parámetro de identificador con `entityId`.
3. Ejecuta la consulta y retorna el primer resultado obtenido.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa`

Contiene las entidades JPA y los repositorios Spring Data para la persistencia del módulo de templates.

#### Clase `SectionJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que mapea la tabla `TWGTBSEC`. Representa una sección de plantilla, con referencia a la plantilla propietaria y una relación `@ManyToMany` con los valores de sección.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **sectionId** | `Long` | Get/Set | Identificador único de la sección (`COD_OID_SECT`). |
| **title** | `String` | Get/Set | Título descriptivo de la sección (`DES_TIL`). |
| **template** | `TemplateJpa` | Get/Set | Referencia perezosa a la plantilla propietaria (`COD_OID_TEM`). |
| **sectionValues** | `List<SectionValueJpa>` | Get/Set | Lista de valores de sección asociados; relación `@ManyToMany` con tabla de unión. |

---

#### Clase `SectionRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa***

Repositorio Spring Data JPA para la entidad `SectionJpa`. Proporciona exclusivamente las operaciones CRUD heredadas de `JpaRepository` sin métodos adicionales.

---

#### Clase `SectionValueJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que mapea la tabla `TWGTBSCV`. Representa un campo de valor dentro de una sección, con su código, visibilidad y tipo de entidad.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **sectionValueId** | `Long` | Get/Set | Identificador único del valor de sección (`COD_OID_SCV`). |
| **title** | `String` | Get/Set | Etiqueta descriptiva del campo (`DES_TIL`). |
| **fieldCode** | `String` | Get/Set | Código técnico del campo (`DES_FLD_NAME`). |
| **isVisible** | `Boolean` | Get/Set | Indica si el campo es visible; almacenado como `Y`/`N` (`XTI_VISIBLE`). |
| **valueType** | `SectionValueEntityType` | Get/Set | Tipo de entidad del campo, almacenado como `String` (`DES_VALUE_TP`). |

---

#### Clase `SectionValueRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa***

Repositorio Spring Data JPA para la entidad `SectionValueJpa`. Añade una consulta derivada para buscar por código de campo.

##### Método `findByFieldCode`

Busca un valor de sección por su código de campo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **fieldCode** | `String` | Código del campo a buscar. |

Retorna: `Optional<SectionValueJpa>` — entidad encontrada, o vacío si no existe.

Algoritmo:
1. Ejecuta una consulta derivada de Spring Data filtrando `SectionValueJpa` por `fieldCode` igual al valor proporcionado.

---

#### Clase `TemplateJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa***
***Extends: AuditedEntity***

Entidad JPA que mapea la tabla `TWGTBTEM`. Representa una plantilla con su consulta SQL opcional, título, tipo y lista de secciones asociadas. Contiene el enum interno `TemplateType`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **templateId** | `Long` | Get/Set | Identificador único de la plantilla (`COD_OID_TEM`). |
| **sqlQuery** | `String` | Get/Set | Consulta SQL para datos dinámicos (`DES_TLB_SQL`). |
| **title** | `String` | Get/Set | Título descriptivo de la plantilla (`DES_TIL`). |
| **templateType** | `TemplateType` | Get/Set | Tipo de plantilla almacenado como `String`; valor por defecto `DEFAULT` (`DES_TEM_TYPE`). |
| **sections** | `List<SectionJpa>` | Get/Set | Lista de secciones de la plantilla; carga perezosa con cascada. |

**Enum interno `TemplateType`:**

| Valor | Descripción |
| :---: | ----- |
| `BUSINESS_DATA` | Plantilla con datos de negocio. |

> Nota: el valor `DEFAULT` está declarado implícitamente como valor por defecto de la propiedad pero no aparece como literal del enum en el código fuente proporcionado.

---

#### Clase `TemplateRepositoryJpa`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa***

Repositorio Spring Data JPA para la entidad `TemplateJpa`. Proporciona exclusivamente las operaciones CRUD heredadas de `JpaRepository` sin métodos adicionales.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa.mapper`

Contiene los mappers MapStruct que convierten entre las entidades JPA del módulo de templates y los modelos de dominio correspondientes.

#### Clase `SectionMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa.mapper***

Interfaz MapStruct para la conversión bidireccional entre `Section` (dominio) y `SectionJpa` (persistencia). Al convertir a JPA ignora el campo `template` para evitar referencias circulares.

##### Método `toSectionJpa`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **section** | `Section` | Modelo de dominio origen. |

Retorna: `SectionJpa` — entidad JPA equivalente con `template` ignorado.

Algoritmo:
1. Copia todos los campos con nombre equivalente.
2. Omite la asignación de `template` (marcado con `ignore = true`).
3. Delega la lista de valores en `SectionValueMapper`.

##### Método `toSectionJpaList`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sections** | `List<Section>` | Lista de modelos de dominio. |

Retorna: `List<SectionJpa>` — lista de entidades JPA equivalentes.

Algoritmo:
1. Itera cada elemento y aplica `toSectionJpa`.

##### Método `toSection`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionJpa** | `SectionJpa` | Entidad JPA origen. |

Retorna: `Section` — modelo de dominio equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente; delega la lista de valores en `SectionValueMapper`.

##### Método `toSectionList`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionJpas** | `List<SectionJpa>` | Lista de entidades JPA. |

Retorna: `List<Section>` — lista de modelos de dominio equivalentes.

Algoritmo:
1. Itera cada elemento y aplica `toSection`.

---

#### Clase `SectionValueMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa.mapper***

Interfaz MapStruct para la conversión bidireccional entre `SectionValue` (dominio) y `SectionValueJpa` (persistencia).

##### Método `toSectionValueJpa`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionValue** | `SectionValue` | Modelo de dominio origen. |

Retorna: `SectionValueJpa` — entidad JPA equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente mediante MapStruct.

##### Método `toSectionValueJpaList`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionValues** | `List<SectionValue>` | Lista de modelos de dominio. |

Retorna: `List<SectionValueJpa>` — lista de entidades JPA.

Algoritmo:
1. Itera cada elemento y aplica `toSectionValueJpa`.

##### Método `toSectionValue`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionValueJpa** | `SectionValueJpa` | Entidad JPA origen. |

Retorna: `SectionValue` — modelo de dominio equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente mediante MapStruct.

##### Método `toSectionValueList`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sectionValueJpas** | `List<SectionValueJpa>` | Lista de entidades JPA. |

Retorna: `List<SectionValue>` — lista de modelos de dominio equivalentes.

Algoritmo:
1. Itera cada elemento y aplica `toSectionValue`.

---

#### Clase `TemplateMapper`

***Package: com.bbva.wgtb.wgtbbackend.apitemplates.infrastructure.repository.jpa.mapper***

Interfaz MapStruct para la conversión bidireccional entre `Template` (dominio) y `TemplateJpa` (persistencia). Delega la conversión de secciones en `SectionMapper`.

##### Método `toTemplateJpa`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **template** | `Template` | Modelo de dominio origen. |

Retorna: `TemplateJpa` — entidad JPA equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente.
2. Delega la lista de secciones en `SectionMapper`.

##### Método `toTemplateJpaList`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **templates** | `List<Template>` | Lista de modelos de dominio. |

Retorna: `List<TemplateJpa>` — lista de entidades JPA.

Algoritmo:
1. Itera cada elemento y aplica `toTemplateJpa`.

##### Método `toTemplate`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **templateJpa** | `TemplateJpa` | Entidad JPA origen. |

Retorna: `Template` — modelo de dominio equivalente.

Algoritmo:
1. Copia todos los campos con nombre equivalente.
2. Delega la lista de secciones en `SectionMapper`.

##### Método `toTemplateList`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **templateJpas** | `List<TemplateJpa>` | Lista de entidades JPA. |

Retorna: `List<Template>` — lista de modelos de dominio equivalentes.

Algoritmo:
1. Itera cada elemento y aplica `toTemplate`.

---

### Paquete `com.bbva.wgtb.wgtbbackend`

Contiene la clase principal de arranque de la aplicación Spring Boot.

#### Clase `Application`

***Package: com.bbva.wgtb.wgtbbackend***
***Extends: AbstractNovaApp***

Punto de entrada de la aplicación. Anotada con `@SpringBootApplication` y `@EnableCaching` para activar el contexto Spring y el soporte de caché. Extiende `AbstractNovaApp` para integrar el bootstrapping de la plataforma NOVA.

##### Método `main`

Inicia la aplicación Spring Boot.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **args** | `String[]` | Argumentos de línea de comandos pasados al proceso JVM. |

Retorna: `void`

Algoritmo:
1. Invoca `SpringApplication.run(Application.class, args)` para arrancar el contexto de aplicación.

---

### Paquete `com.bbva.wgtb.wgtbbackend.exception`

Contiene la jerarquía de excepciones de la aplicación, desde la excepción base hasta los tipos especializados por dominio de error.

#### Clase `BasicException`

***Package: com.bbva.wgtb.wgtbbackend.exception***
***Extends: RuntimeException***

Excepción base no verificada que encapsula un mensaje de error y opcionalmente la causa original. Sirve como raíz de la jerarquía de excepciones de infraestructura del servicio.

##### Constructor `BasicException(String message)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Mensaje descriptivo del error. |

Algoritmo:
1. Invoca `super(message)` para propagar el mensaje a `RuntimeException`.

##### Constructor `BasicException(String message, Exception e)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Mensaje descriptivo del error. |
| **e** | `Exception` | Excepción causa original. |

Algoritmo:
1. Invoca `super(message, e)` para propagar mensaje y causa a `RuntimeException`.

---

#### Clase `GenericException`

***Package: com.bbva.wgtb.wgtbbackend.exception***
***Extends: Exception***

Excepción verificada base para todos los errores de negocio del servicio. Almacena el código HTTP asociado al error para facilitar la construcción de respuestas REST.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **code** | `HttpStatus` | Get | Código de estado HTTP asociado al error. |

##### Constructor `GenericException(HttpStatus code, String message)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **code** | `HttpStatus` | Código HTTP que describe la categoría del error. |
| **message** | `String` | Mensaje descriptivo del error. |

Algoritmo:
1. Invoca `super(message)` para propagar el mensaje a `Exception`.
2. Asigna `code` a la propiedad `this.code`.

---

#### Clase `AuthenticationException`

***Package: com.bbva.wgtb.wgtbbackend.exception***
***Extends: GenericException***

Excepción lanzada cuando se produce un fallo de autenticación. Establece automáticamente el código HTTP `UNAUTHORIZED` (401).

##### Constructor `AuthenticationException()`

Algoritmo:
1. Invoca `super(HttpStatus.UNAUTHORIZED, <mensaje de autenticación>)`.

---

#### Clase `EntityAlreadyExistsException`

***Package: com.bbva.wgtb.wgtbbackend.exception***
***Extends: GenericException***

Excepción lanzada cuando se intenta crear una entidad que ya existe en el sistema. Establece el código HTTP `CONFLICT` (409).

##### Constructor `EntityAlreadyExistsException(String message)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Mensaje descriptivo indicando qué entidad ya existe. |

Algoritmo:
1. Invoca `super(HttpStatus.CONFLICT, message)`.

---

#### Clase `EntityNotFoundException`

***Package: com.bbva.wgtb.wgtbbackend.exception***
***Extends: GenericException***

Excepción lanzada cuando no se encuentra una entidad solicitada por su identificador. Establece el código HTTP `NOT_FOUND` (404).

##### Constructor `EntityNotFoundException(Object id)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `Object` | Identificador de la entidad no encontrada, incluido en el mensaje de error. |

Algoritmo:
1. Construye un mensaje que incorpora `id` como referencia de la entidad no encontrada.
2. Invoca `super(HttpStatus.NOT_FOUND, message)`.

---

#### Clase `RdrException`

***Package: com.bbva.wgtb.wgtbbackend.exception***
***Extends: GenericException***

Excepción lanzada ante fallos de comunicación con el servicio externo RDR. Soporta dos constructores: uno con código HTTP implícito `INTERNAL_SERVER_ERROR` y otro que permite especificar el código.

##### Constructor `RdrException(String message, String action)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Descripción del error ocurrido. |
| **action** | `String` | Acción que estaba ejecutándose cuando se produjo el fallo. |

Algoritmo:
1. Invoca `super(HttpStatus.INTERNAL_SERVER_ERROR, message + " [action: " + action + "]")` o similar.

##### Constructor `RdrException(HttpStatus httpStatus, String message, String action)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **httpStatus** | `HttpStatus` | Código HTTP personalizado para el error. |
| **message** | `String` | Descripción del error ocurrido. |
| **action** | `String` | Acción que estaba ejecutándose cuando se produjo el fallo. |

Algoritmo:
1. Invoca `super(httpStatus, message + " [action: " + action + "]")` o similar.

---

#### Clase `XbpmException`

***Package: com.bbva.wgtb.wgtbbackend.exception***
***Extends: GenericException***

Excepción lanzada ante fallos en la integración con el motor de procesos XBPM. Establece el código HTTP `INTERNAL_SERVER_ERROR` (500).

##### Constructor `XbpmException(String message, String action)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Descripción del error ocurrido en la integración XBPM. |
| **action** | `String` | Acción que estaba ejecutándose cuando se produjo el fallo. |

Algoritmo:
1. Invoca `super(HttpStatus.INTERNAL_SERVER_ERROR, message + " [action: " + action + "]")` o similar.

### Paquete `com.bbva.wgtb.wgtbbackend.rdr`

Contiene la configuración de clientes REST y los servicios de acceso a los sistemas RDR (Reference Data Repository) de diccionario y de party, así como la lógica de orquestación para obtener datos canónicos de clientes.

---

#### Clase `ConfigRdrdictionary`

***Package: com.bbva.wgtb.wgtbbackend.rdr***

Clase de configuración Spring que registra los beans necesarios para conectarse al microservicio `Rdrdictionary` a través de la microgateway NOVA. Lee los parámetros de host, timeout y cabecera de release desde las propiedades de la aplicación y construye los objetos de cliente REST correspondientes.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **microgatewayHostPort** | `String` | N/A | Host y puerto de la microgateway para `Rdrdictionary` (por defecto `localhost:24000`). |
| **microgatewayTimeout** | `Integer` | N/A | Timeout en milisegundos para las llamadas a `Rdrdictionary` (por defecto `10000`). |
| **releaseHeader** | `String` | N/A | Cabecera de release utilizada en los metadatos NOVA (por defecto `seguridad`). |

##### Método `getRestHandlerRdrdictionary`

Instancia y registra como bean el manejador REST `RestHandlerRdrdictionary` configurado con los metadatos y la configuración de petición NOVA.

Retorna: `RestHandlerRdrdictionary` — cliente REST listo para invocar el servicio `Rdrdictionary`.

Algoritmo:
1. Construye una instancia de `RestHandlerRdrdictionary` pasando el `NovaMetadata` y el `NovaRequestConfig` ya definidos como beans.
2. Registra la instancia como bean de Spring.

##### Método `getNovaMetadata`

Construye y registra como bean (`Rdrdictionary.novaMetadata`) el objeto `NovaMetadata` con las cabeceras implícitas necesarias para las llamadas al servicio.

Retorna: `NovaMetadata` — metadatos de cabeceras NOVA para `Rdrdictionary`.

Algoritmo:
1. Crea una lista de `NovaImplicitHeadersOutput`.
2. Añade la cabecera de release con el valor inyectado en `releaseHeader`.
3. Construye y devuelve el objeto `NovaMetadata` con dicha lista.

##### Método `getConfigRequestSchema`

Construye y registra como bean (`Rdrdictionary.novaRequestconfig`) la configuración de esquema de petición REST.

Retorna: `NovaRequestConfig` — configuración de protocolo y host para `Rdrdictionary`.

Algoritmo:
1. Crea un `NovaRequestConfig` con el esquema HTTP (`NovaSchemesValues`) y el host/puerto inyectado en `microgatewayHostPort`.
2. Establece el timeout con el valor de `microgatewayTimeout`.
3. Devuelve la configuración resultante.

---

#### Clase `ConfigRdrparty`

***Package: com.bbva.wgtb.wgtbbackend.rdr***

Clase de configuración Spring análoga a `ConfigRdrdictionary`, pero orientada al microservicio `Rdrparty`. Registra los beans de cliente REST necesarios para consultar datos de party en RDR.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **microgatewayHostPort** | `String` | N/A | Host y puerto de la microgateway para `Rdrparty` (por defecto `localhost:24000`). |
| **microgatewayTimeout** | `Integer` | N/A | Timeout en milisegundos para las llamadas a `Rdrparty` (por defecto `10000`). |
| **releaseHeader** | `String` | N/A | Cabecera de release utilizada en los metadatos NOVA (por defecto `seguridad`). |

##### Método `getRestHandlerRdrparty`

Instancia y registra como bean el manejador REST `RestHandlerRdrparty`.

Retorna: `RestHandlerRdrparty` — cliente REST listo para invocar el servicio `Rdrparty`.

Algoritmo:
1. Construye una instancia de `RestHandlerRdrparty` con el `NovaMetadata` y `NovaRequestConfig` definidos.
2. Registra la instancia como bean de Spring.

##### Método `getNovaMetadata`

Construye y registra como bean (`Rdrparty.novaMetadata`) el objeto `NovaMetadata` para el servicio `Rdrparty`.

Retorna: `NovaMetadata` — metadatos de cabeceras NOVA para `Rdrparty`.

Algoritmo:
1. Crea una lista de `NovaImplicitHeadersOutput`.
2. Añade la cabecera de release con el valor de `releaseHeader`.
3. Devuelve el `NovaMetadata` construido.

##### Método `getConfigRequestSchema`

Construye y registra como bean (`Rdrparty.novaRequestconfig`) la configuración de petición REST para `Rdrparty`.

Retorna: `NovaRequestConfig` — configuración de protocolo y host para `Rdrparty`.

Algoritmo:
1. Crea un `NovaRequestConfig` con el esquema HTTP y el host/puerto de `microgatewayHostPort`.
2. Establece el timeout con `microgatewayTimeout`.
3. Devuelve la configuración.

---

#### Clase `RdrService`

***Package: com.bbva.wgtb.wgtbbackend.rdr***

Servicio de orquestación que centraliza la lógica de negocio para consultar datos de clientes en los sistemas RDR. Coordina las llamadas a `ServiceRdrdictionary` y `ServiceRdrparty`, construye los mensajes XML de petición, parsea las respuestas y gestiona estrategias de fallback cuando la búsqueda por un identificador falla.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **serviceRdrdictionary** | `ServiceRdrdictionary` | N/A | Servicio cliente del diccionario RDR. |
| **serviceRdrparty** | `ServiceRdrparty` | N/A | Servicio cliente del party RDR. |

##### Método `getDictionaryByCclient`

Obtiene el XML de respuesta del diccionario RDR para un identificador interno de cliente, intentando primero la búsqueda estándar por `CLIENTELAID` y, si falla, una búsqueda secundaria por LEI.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **clientId** | `String` | Identificador interno del cliente (`CLIENTELAID`). |

Retorna: `String` — XML de respuesta del servicio de diccionario.

Algoritmo:
1. Construye el XML de petición estándar llamando a `buildDictionaryRequest` con `clientId`.
2. Intenta la llamada mediante `tryPostDictionary` con el nombre de sistema estándar.
3. Si lanza excepción, construye la petición alternativa LEI con `buildDictionaryRequestLEI`.
4. Reintenta la llamada con `tryPostDictionary` usando el nombre de sistema LEI.
5. Devuelve el XML de respuesta obtenido.

##### Método `tryPostDictionary`

Ejecuta el envío del XML al servicio de diccionario y propaga cualquier excepción para que el llamador pueda aplicar fallback.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **xmlRequest** | `String` | Cuerpo XML de la petición. |
| **clientId** | `String` | Identificador del cliente (usado en el log). |
| **sysName** | `String` | Nombre del sistema de búsqueda (usado en el log). |

Retorna: `String` — XML de respuesta del diccionario.

Algoritmo:
1. Invoca `serviceRdrdictionary.postDictionary` con el XML de petición.
2. Si se lanza `RdrException`, la relanza envuelta en `GenericException`.
3. Devuelve la respuesta recibida.

##### Método `buildDictionaryRequest`

Construye el cuerpo XML de petición para el servicio de diccionario usando el identificador interno del cliente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **internalId** | `String` | Identificador interno del cliente. |

Retorna: `String` — XML de petición formateado para `Rdrdictionary`.

Algoritmo:
1. Construye un `String` XML con la estructura requerida por el servicio, insertando `internalId` en el campo correspondiente.
2. Devuelve el XML generado.

##### Método `buildDictionaryRequestLEI`

Construye el cuerpo XML de petición para el servicio de diccionario usando el identificador LEI como alternativa.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **internalId** | `String` | Identificador LEI del cliente. |

Retorna: `String` — XML de petición LEI formateado para `Rdrdictionary`.

Algoritmo:
1. Construye un `String` XML con la estructura LEI requerida por el servicio, insertando `internalId`.
2. Devuelve el XML generado.

##### Método `parseCanValFromDictionary`

Extrae los valores canónicos (`CanVal`) del XML de respuesta del diccionario mediante XPath.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **dictionaryXml** | `String` | XML de respuesta del servicio de diccionario. |

Retorna: `List<String>` — lista de valores `CanVal` encontrados en el XML.

Algoritmo:
1. Parsea el XML usando `DocumentBuilderFactory` y `DocumentBuilder`.
2. Aplica una expresión XPath para localizar los nodos que contienen los `CanVal`.
3. Itera el `NodeList` resultante y extrae el valor de cada nodo.
4. Devuelve la lista de valores.

##### Método `getPartyByFindId`

Consulta el servicio de party RDR para un identificador canónico (`CanVal`) y una sucursal determinada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **findId** | `String` | Valor canónico a consultar. |
| **branchId** | `String` | Identificador de sucursal. |

Retorna: `String` — XML de respuesta del servicio de party.

Algoritmo:
1. Construye el XML de petición con `buildPartyRequest`.
2. Invoca `serviceRdrparty.postParty` con el XML generado.
3. Si lanza `RdrException`, la relanza como `GenericException`.
4. Devuelve el XML de respuesta.

##### Método `buildPartyRequest`

Construye el cuerpo XML de petición para el servicio de party RDR.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **canVal** | `String` | Valor canónico del cliente. |
| **branchId** | `String` | Identificador de sucursal. |

Retorna: `String` — XML de petición formateado para `Rdrparty`.

Algoritmo:
1. Construye el `String` XML con la estructura requerida, insertando `canVal` y `branchId`.
2. Devuelve el XML generado.

##### Método `extractValueFromPartyXml`

Evalúa una expresión XPath sobre el XML de respuesta de party y devuelve el primer valor encontrado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **partyXml** | `String` | XML de respuesta del servicio de party. |
| **xpathExpression** | `String` | Expresión XPath a evaluar. |

Retorna: `String` — valor extraído del XML, o `null` si no se encuentra.

Algoritmo:
1. Parsea el XML con `DocumentBuilderFactory`.
2. Crea un `XPath` con `XPathFactory` y compila la expresión recibida.
3. Evalúa la expresión sobre el documento y devuelve el resultado como `String`.
4. En caso de excepción, registra el error y devuelve `null`.

##### Método `getPartyDataForInternalId`

Orquesta la obtención completa de datos de party para un cliente interno y un conjunto de sucursales, combinando las llamadas a diccionario y party.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **clientId** | `String` | Identificador interno del cliente. |
| **branches** | `List<String>` | Lista de identificadores de sucursal a consultar. |

Retorna: `Map<String, List<String>>` — mapa de datos de party indexado por tipo de campo.

Algoritmo:
1. Llama a `getDictionaryByCclient` para obtener el XML del diccionario.
2. Extrae los `CanVal` del XML con `parseCanValFromDictionary`.
3. Para cada `CanVal` y cada sucursal, invoca `getPartyByFindId`.
4. Sobre cada respuesta de party, evalúa las expresiones XPath definidas en `Constants` para extraer los campos relevantes.
5. Agrega los valores obtenidos en el mapa de resultado, agrupados por tipo de campo.
6. Devuelve el mapa completo.

---

#### Clase `ServiceRdrdictionary`

***Package: com.bbva.wgtb.wgtbbackend.rdr***

Servicio Spring que encapsula la llamada al endpoint `postDictionary` del cliente NOVA generado para `Rdrdictionary`. Gestiona las excepciones del cliente REST y las traduce a `RdrException`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | N/A | Metadatos de cabeceras NOVA para las peticiones al servicio. |
| **novaRequestConfig** | `NovaRequestConfig` | N/A | Configuración del protocolo REST (HTTP/HTTPS). |
| **restHandlerRdrdictionary** | `IRestHandlerRdrdictionary` | N/A | Manejador de cliente REST generado por NOVA para `Rdrdictionary`. |

##### Constructor

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos NOVA cualificados como `Rdrdictionary.novaMetadata`. |
| **novaRequestConfig** | `NovaRequestConfig` | Configuración de petición cualificada como `Rdrdictionary.novaRequestconfig`. |
| **restHandlerRdrdictionary** | `IRestHandlerRdrdictionary` | Implementación del cliente REST inyectada por Spring. |

Algoritmo:
1. Asigna cada parámetro a su propiedad de clase correspondiente.

##### Método `postDictionary`

Envía un mensaje XML al endpoint de diccionario RDR y devuelve la respuesta en texto plano.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Cuerpo XML de la petición. |

Retorna: `String` — respuesta XML del servicio `Rdrdictionary`.

Algoritmo:
1. Invoca `restHandlerRdrdictionary.postDictionary` pasando `novaMetadata`, `novaRequestConfig` y el mensaje.
2. Captura `NovaApiClientRequestException`, `NovaApiClientResponseException`, `NovaApiClientResponseTimeoutException` y `PostDictionaryException500`, y los relanza como `RdrException` con el mensaje de error correspondiente.
3. Devuelve la respuesta recibida.

---

#### Clase `ServiceRdrparty`

***Package: com.bbva.wgtb.wgtbbackend.rdr***

Servicio Spring que encapsula las llamadas a los endpoints `createParty` y `postParty` del cliente NOVA generado para `Rdrparty`. Traduce las excepciones del cliente REST a `RdrException`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | N/A | Metadatos de cabeceras NOVA para las peticiones al servicio. |
| **novaRequestConfig** | `NovaRequestConfig` | N/A | Configuración del protocolo REST (HTTP/HTTPS). |
| **restHandlerRdrparty** | `IRestHandlerRdrparty` | N/A | Manejador de cliente REST generado por NOVA para `Rdrparty`. |

##### Constructor

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos NOVA cualificados como `Rdrparty.novaMetadata`. |
| **novaRequestConfig** | `NovaRequestConfig` | Configuración de petición cualificada como `Rdrparty.novaRequestconfig`. |
| **restHandlerRdrparty** | `IRestHandlerRdrparty` | Implementación del cliente REST inyectada por Spring. |

Algoritmo:
1. Asigna cada parámetro a su propiedad de clase correspondiente.

##### Método `createParty`

Invoca el endpoint de creación de party en RDR con el mensaje XML proporcionado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Cuerpo XML de la petición de creación. |

Retorna: `String` — respuesta XML del servicio.

Algoritmo:
1. Llama a `restHandlerRdrparty.createParty` con `novaMetadata`, `novaRequestConfig` y el mensaje.
2. Captura las excepciones de cliente NOVA y `CreatePartyException500`, y las relanza como `RdrException`.
3. Devuelve la respuesta.

##### Método `postParty`

Invoca el endpoint de consulta de party en RDR con el mensaje XML proporcionado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Cuerpo XML de la petición de consulta. |

Retorna: `String` — respuesta XML del servicio.

Algoritmo:
1. Llama a `restHandlerRdrparty.postParty` con `novaMetadata`, `novaRequestConfig` y el mensaje.
2. Captura las excepciones de cliente NOVA y `PostPartyException500`, y las relanza como `RdrException`.
3. Devuelve la respuesta.

---

### Paquete `com.bbva.wgtb.wgtbbackend.utils.autentication`

Proporciona los componentes de seguridad para extraer y propagar la identidad del usuario autenticado a través del ciclo de vida de cada petición HTTP.

---

#### Clase `AuthenticationFilter`

***Package: com.bbva.wgtb.wgtbbackend.utils.autentication***
***Extends: OncePerRequestFilter***

Filtro HTTP que se ejecuta una única vez por petición. Lee la cabecera `iv-user` de la petición entrante, construye un objeto `NovaAuthentication` y lo almacena en `NovaSecurityContext` para que esté disponible durante el procesamiento de la petición. Al finalizar, limpia el contexto.

##### Método `doFilterInternal`

Intercepta cada petición HTTP para poblar el contexto de seguridad con el usuario autenticado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **request** | `HttpServletRequest` | Petición HTTP entrante. |
| **response** | `HttpServletResponse` | Respuesta HTTP saliente. |
| **filterChain** | `FilterChain` | Cadena de filtros a continuar. |

Retorna: `void`

Algoritmo:
1. Extrae el valor de la cabecera `iv-user` de `request`.
2. Crea una instancia de `NovaAuthentication` con el valor extraído.
3. Llama a `NovaSecurityContext.setAuthentication` para almacenar la autenticación en el hilo actual.
4. Invoca `filterChain.doFilter` para continuar la cadena.
5. En el bloque `finally`, llama a `NovaSecurityContext.clear` para limpiar el contexto del hilo.

---

#### Clase `FilterRegistration`

***Package: com.bbva.wgtb.wgtbbackend.utils.autentication***

Componente Spring que registra el `AuthenticationFilter` en el contenedor de servlets para que se aplique a todas las peticiones entrantes.

##### Método `authenticationFilter`

Crea y configura el bean `FilterRegistrationBean` que envuelve al `AuthenticationFilter`.

Retorna: `FilterRegistrationBean<AuthenticationFilter>` — registro del filtro con su configuración de orden y URL patterns.

Algoritmo:
1. Instancia un `FilterRegistrationBean` con una nueva instancia de `AuthenticationFilter`.
2. Configura el patrón de URL (`/*`) para que el filtro se aplique a todas las rutas.
3. Devuelve el bean registrado.

---

#### Clase `NovaAuthentication`

***Package: com.bbva.wgtb.wgtbbackend.utils.autentication***

DTO inmutable que representa la identidad del usuario autenticado en el sistema NOVA. Implementa `Serializable` para permitir su uso en contextos de almacenamiento.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **serialVersionUID** | `long` | N/A | Identificador de versión de serialización. |
| **userId** | `String` | Get | Identificador único del usuario autenticado (p. ej. `T058326`). |

---

#### Clase `NovaSecurityContext`

***Package: com.bbva.wgtb.wgtbbackend.utils.autentication***

Utilidad de tipo estático que gestiona el almacenamiento del objeto `NovaAuthentication` en un `ThreadLocal`, garantizando el aislamiento de la identidad del usuario entre hilos concurrentes.

##### Método `getAuthentication`

Recupera la autenticación asociada al hilo de ejecución actual.

Retorna: `NovaAuthentication` — la autenticación del usuario actual, o `null` si no se ha establecido.

Algoritmo:
1. Devuelve el valor almacenado en `CONTEXT` (el `ThreadLocal`).

##### Método `setAuthentication`

Establece la autenticación del usuario para el hilo de ejecución actual.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **authentication** | `NovaAuthentication` | Objeto de autenticación a almacenar. |

Retorna: `void`

Algoritmo:
1. Llama a `CONTEXT.set(authentication)` para almacenar el valor en el hilo actual.

##### Método `clear`

Elimina la autenticación almacenada en el hilo actual para evitar fugas de memoria.

Retorna: `void`

Algoritmo:
1. Llama a `CONTEXT.remove()` para limpiar el valor del `ThreadLocal`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.utils`

Agrupa componentes de infraestructura transversal: configuración de caché, constantes globales, utilidades de base de datos, serialización JSON, paginación, aspectos de log y herramientas de reflexión para scraping de entidades.

---

#### Clase `CacheConfig`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Clase de configuración Spring que define y registra el `CacheManager` con múltiples regiones de caché de distinta duración, construidas sobre `ConcurrentMapCache` con expiración gestionada por Guava.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **SHORT_CACHE** | `String` | N/A | Nombre de la caché de corta duración. |
| **ONE_HOUR_CACHE** | `String` | N/A | Nombre de la caché de una hora. |
| **TWO_HOUR_CACHE** | `String` | N/A | Nombre de la caché de dos horas. |
| **ONE_DAY_CACHE** | `String` | N/A | Nombre de la caché de un día. |
| **SEARCH_ALL_BUSINESS_DATA_CACHE** | `String` | N/A | Nombre de la caché para búsquedas de datos de negocio. |

##### Método `cacheManager`

Construye y registra el `CacheManager` con todas las regiones de caché configuradas.

Retorna: `CacheManager` — gestor de cachés con todas las regiones registradas.

Algoritmo:
1. Crea instancias de `ConcurrentMapCache` para cada nombre de caché definido como constante, usando `CacheBuilder` de Guava con los tiempos de expiración correspondientes.
2. Crea un `SimpleCacheManager` y le asigna la lista de cachés mediante `Arrays.asList`.
3. Devuelve el `SimpleCacheManager`.

---

#### Clase `Constants`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Clase de utilidad que centraliza todas las constantes de la aplicación: perfiles de Spring, formateadores de fecha, nombres de fuentes de datos, expresiones XPath para parseo de XML RDR y valores de paginación por defecto.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **PROFILE_LOCAL** | `String` | N/A | Nombre del perfil local (`LOCAL`). |
| **PROFILE_NOT_LOCAL** | `String` | N/A | Negación del perfil local para condicionado de beans. |
| **DATE_FORMATTER** | `DateTimeFormatter` | N/A | Formateador para el patrón `yyyy-MM-dd`. |
| **BPM** | `String` | N/A | Clave de la fuente BPM. |
| **DEFAULT** | `String` | N/A | Clave de fuente por defecto. |
| **BUSINESS_DATA** | `String` | N/A | Clave de datos de negocio. |
| **RDR** | `String` | N/A | Clave de la fuente RDR party. |
| **LEI** | `String` | N/A | Expresión XPath para extraer el identificador LEI del XML de party. |
| **LEGAL_NAME** | `String` | N/A | Expresión XPath para extraer el nombre legal del XML de party. |
| **STAR_CODE** | `String` | N/A | Expresión XPath para extraer el código STAR del XML de party. |
| **BRANCH_TEMPLATE** | `String` | N/A | Plantilla de expresión XPath para extraer datos de sucursal (requiere formateo con `String.format`). |
| **CLIENTELAID** | `String` | N/A | Expresión XPath para extraer el `CLIENTELAID` del XML de party. |
| **ENTITY** | `String` | N/A | Prefijo utilizado en la resolución de nombres de entidad. |
| **DEFAULT_PAGE** | `int` | N/A | Número de página por defecto: `0`. |
| **DEFAULT_PAGE_SIZE** | `int` | N/A | Tamaño de página por defecto: `10`. |

---

#### Clase `DatabaseErrorResolver`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Utilidad estática que analiza excepciones de base de datos y las clasifica en tipos concretos de error (`DbErrorType`) para facilitar el manejo diferenciado en las capas superiores.

##### Método `resolveError`

Analiza la excepción recibida y determina el tipo de error de base de datos.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **ex** | `Exception` | Excepción de base de datos a analizar. |

Retorna: `DbErrorType` — tipo de error identificado.

Algoritmo:
1. Comprueba si `ex` es una instancia de `DataIntegrityViolationException` o contiene una causa de tipo `ConstraintViolationException`.
2. Si se cumple, devuelve `DbErrorType.DUPLICATE_KEY`.
3. En caso contrario, devuelve `DbErrorType.UNKNOWN`.

---

#### Clase `DatabaseUtils`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Componente Spring que expone operaciones de gestión del contexto de persistencia JPA, permitiendo controlar explícitamente el flush y el clear del `EntityManager` desde los servicios de aplicación.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **entityManager** | `EntityManager` | N/A | Gestor de entidades JPA inyectado por Spring. |

##### Método `clearPersistenceContext`

Limpia el contexto de persistencia, desvinculando todas las entidades gestionadas.

Retorna: `void`

Algoritmo:
1. Invoca `entityManager.clear()`.

##### Método `flushPersistenceContext`

Sincroniza el estado del contexto de persistencia con la base de datos sin cerrar el contexto.

Retorna: `void`

Algoritmo:
1. Invoca `entityManager.flush()`.
2. Si se lanza `TransactionRequiredException`, registra el aviso en el log.

##### Método `flushAndClearPersistenceContext`

Realiza un flush seguido de un clear del contexto de persistencia.

Retorna: `void`

Algoritmo:
1. Llama a `flushPersistenceContext()`.
2. Llama a `clearPersistenceContext()`.

---

#### Clase `EntityScrapper`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Componente Spring que permite navegar la estructura de un objeto Java mediante rutas de campo expresadas como cadenas de texto (p. ej. `address.city`), con soporte para colecciones y filtros inline. Utiliza reflexión para resolver getters dinámicamente.

##### Método `scrape(Object entity, String path)`

Navega el grafo de objetos siguiendo la ruta indicada y devuelve el valor encontrado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **entity** | `Object` | Objeto raíz sobre el que navegar. |
| **path** | `String` | Ruta de campos separada por puntos, con soporte de filtros entre llaves. |

Retorna: `Object` — valor encontrado en la ruta indicada.

Algoritmo:
1. Divide `path` en segmentos respetando las llaves con `splitRespectingBraces`.
2. Para cada segmento, resuelve el valor del campo sobre el objeto actual con `getSingleFieldValue`.
3. Si el valor intermedio es una `List`, itera sus elementos para continuar la navegación.
4. Devuelve el valor final obtenido.

##### Método `scrape(Object entity, String path, GenericFunction<List<Object>, Object> ifConflict)`

Versión sobrecargada de `scrape` que acepta una función de resolución de conflictos cuando la ruta apunta a múltiples valores en una colección.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **entity** | `Object` | Objeto raíz sobre el que navegar. |
| **path** | `String` | Ruta de campos. |
| **ifConflict** | `GenericFunction<List<Object>, Object>` | Función aplicada cuando se encuentran múltiples valores candidatos. |

Retorna: `Object` — valor resuelto, potencialmente reducido por la función de conflicto.

Algoritmo:
1. Ejecuta la misma lógica de navegación que `scrape(Object, String)`.
2. Si el resultado es una `List` con más de un elemento, aplica `ifConflict` para reducirla a un único valor.
3. Devuelve el resultado.

##### Método `splitRespectingBraces`

Divide una cadena de ruta en segmentos separados por `.`, sin romper los grupos delimitados por `{}`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **input** | `String` | Cadena de ruta a dividir. |

Retorna: `List<String>` — lista de segmentos de la ruta.

Algoritmo:
1. Itera carácter a carácter sobre `input`, manteniendo un contador de profundidad de llaves.
2. Acumula caracteres en el segmento actual; cuando encuentra un `.` fuera de llaves, cierra el segmento actual y abre uno nuevo.
3. Añade el último segmento y devuelve la lista resultante.

##### Método `getSingleFieldValue`

Obtiene el valor de un campo simple (sin punto) sobre un objeto, aplicando filtros si el segmento los contiene.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **item** | `Object` | Objeto sobre el que resolver el campo. |
| **fieldName** | `String` | Nombre del campo con posibles filtros inline (p. ej. `items{status='active'}`). |

Retorna: `Object` — valor del campo, posiblemente filtrado.

Algoritmo:
1. Aplica el patrón regex de campo con filtros para extraer el nombre base y las condiciones de filtro.
2. Si hay filtros, invoca `getItemValueFromField` para cada elemento de la colección y descarta los que no cumplen las condiciones.
3. Si no hay filtros, invoca directamente `getItemValueFromField` sobre el objeto.
4. Devuelve el resultado.

##### Método `getItemValueFromField`

Resuelve el valor de un campo (potencialmente anidado con punto) sobre un objeto usando reflexión para invocar el getter correspondiente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **item** | `Object` | Objeto sobre el que resolver el campo. |
| **fieldName** | `String` | Ruta de campo separada por puntos. |

Retorna: `Object` — valor obtenido mediante reflexión.

Algoritmo:
1. Divide `fieldName` por `.` para obtener los segmentos de la ruta anidada.
2. Para cada segmento, construye el nombre del getter aplicando `StringUtils.capitalize` y buscando el método con `getDeclaredMethod` o `getMethod`.
3. Invoca el getter sobre el objeto actual con `Method.invoke`.
4. Devuelve el valor obtenido al final de la cadena.

---

#### Clase `GenericApiErrorBuilder`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Clase builder genérica que facilita la construcción de objetos de error de API con un código HTTP y un mensaje, adaptándose al tipo específico de respuesta de error de cada endpoint generado. Usa reflexión para asignar los campos `code` y `message` al tipo destino.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **targetClass** | `Class<T>` | N/A | Clase del objeto de error a construir. |
| **code** | `HttpStatus` | N/A | Código HTTP del error. |
| **message** | `String` | N/A | Mensaje descriptivo del error. |

##### Método `of`

Método de factoría estático que crea una nueva instancia del builder para el tipo destino indicado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **targetClass** | `Class<T>` | Clase del objeto de error a construir. |

Retorna: `GenericApiErrorBuilder<T>` — nueva instancia del builder.

Algoritmo:
1. Construye y devuelve una nueva instancia de `GenericApiErrorBuilder` con `targetClass`.

##### Método `code`

Establece el código HTTP del error en el builder.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **code** | `HttpStatus` | Código HTTP a asignar. |

Retorna: `GenericApiErrorBuilder<T>` — el propio builder para encadenamiento.

Algoritmo:
1. Asigna `code` a la propiedad interna.
2. Devuelve `this`.

##### Método `message`

Establece el mensaje de error en el builder.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **message** | `String` | Mensaje descriptivo del error. |

Retorna: `GenericApiErrorBuilder<T>` — el propio builder para encadenamiento.

Algoritmo:
1. Asigna `message` a la propiedad interna.
2. Devuelve `this`.

##### Método `build`

Construye la instancia del objeto de error con los valores configurados.

Retorna: `T` — instancia del tipo de error destino con los campos `code` y `message` asignados.

Algoritmo:
1. Instancia `T` mediante `targetClass.getDeclaredConstructor().newInstance()`.
2. Llama a `setFieldIfExists` para asignar `code` y `message`.
3. Devuelve la instancia construida.

##### Método `setFieldIfExists`

Asigna un valor a un campo del objeto destino mediante reflexión, sin lanzar excepción si el campo no existe.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **instance** | `T` | Instancia sobre la que asignar el campo. |
| **fieldName** | `String` | Nombre del campo a asignar. |
| **value** | `Object` | Valor a establecer. |

Retorna: `void`

Algoritmo:
1. Intenta obtener el campo con `targetClass.getDeclaredField(fieldName)`.
2. Hace el campo accesible con `setAccessible(true)`.
3. Asigna el valor con `field.set(instance, value)`.
4. Captura `NoSuchFieldException` y registra el aviso sin propagar la excepción.

##### Método `getFromGenericException`

Construye el objeto de error a partir de una `GenericException`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **e** | `GenericException` | Excepción de negocio con código y mensaje. |

Retorna: `T` — objeto de error construido con los datos de la excepción.

Algoritmo:
1. Llama a `code(e.getStatus()).message(e.getMessage()).build()`.
2. Devuelve el objeto resultante.

##### Método `getUnexpected`

Construye un objeto de error genérico para errores inesperados (HTTP 500).

Retorna: `T` — objeto de error con código `INTERNAL_SERVER_ERROR` y mensaje genérico.

Algoritmo:
1. Llama a `code(HttpStatus.INTERNAL_SERVER_ERROR).message("Unexpected error").build()`.
2. Devuelve el objeto resultante.

##### Método `getFromGenericExceptionArray`

Construye un array de un único objeto de error a partir de una `GenericException`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **e** | `GenericException` | Excepción de negocio. |

Retorna: `T[]` — array de un elemento con el objeto de error.

Algoritmo:
1. Crea un array de tipo `T` con longitud 1.
2. Asigna en la posición 0 el resultado de `getFromGenericException(e)`.
3. Devuelve el array.

---

#### Interfaz `GenericFunction`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Interfaz funcional genérica equivalente a `Function<T, R>` pero que permite lanzar `GenericException`, facilitando su uso en lambdas dentro de operaciones de negocio.

**Método `apply`**

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **t** | `T` | Argumento de entrada. |

Retorna: `R` — resultado de la función.

---

#### Clase `JsonProperties`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Clase de configuración Spring que registra el bean `ObjectMapper` con la configuración personalizada para serialización y deserialización de fechas (`LocalDate` y `OffsetDateTime`) usando los módulos definidos en el paquete `jsonParser`.

##### Método `objectMapper`

Construye y registra el bean `ObjectMapper` con los módulos y características necesarios.

Retorna: `ObjectMapper` — instancia configurada del mapeador JSON.

Algoritmo:
1. Crea una nueva instancia de `ObjectMapper`.
2. Desactiva `FAIL_ON_UNKNOWN_PROPERTIES` en `DeserializationFeature`.
3. Desactiva `WRITE_DATES_AS_TIMESTAMPS` en `SerializationFeature`.
4. Crea un `SimpleModule` y registra `LocalDateSerializer`, `LocalDateDeserializer`, `OffsetDateTimeSerializer` y `OffsetDateTimeDeserializer`.
5. Registra el módulo en el `ObjectMapper`.
6. Devuelve el `ObjectMapper` configurado.

---

#### Clase `JsonUtils`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Componente Spring que centraliza las operaciones de conversión entre objetos Java y su representación JSON, usando el `ObjectMapper` configurado. Gestiona internamente las excepciones de procesamiento JSON y las convierte en `BasicException`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **objectMapper** | `ObjectMapper` | N/A | Mapeador JSON inyectado por Spring. |

##### Método `convertToJson`

Serializa un objeto Java a su representación JSON en forma de cadena de texto.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **o** | `Object` | Objeto a serializar. |

Retorna: `String` — representación JSON del objeto.

Algoritmo:
1. Invoca `objectMapper.writeValueAsString(o)`.
2. Si lanza `JsonProcessingException`, registra el error y lanza una `BasicException`.
3. Devuelve la cadena JSON.

##### Método `convertToNode`

Deserializa una cadena JSON a un `JsonNode`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **json** | `String` | Cadena JSON a parsear. |

Retorna: `JsonNode` — árbol JSON resultante.

Algoritmo:
1. Invoca `objectMapper.readTree(json)`.
2. Si lanza excepción, la convierte en `BasicException`.
3. Devuelve el `JsonNode`.

##### Método `convertToEntity`

Deserializa una cadena JSON a una instancia de la clase indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **json** | `String` | Cadena JSON a deserializar. |
| **clazz** | `Class<T>` | Clase destino de la deserialización. |

Retorna: `T` — instancia de la clase destino.

Algoritmo:
1. Invoca `objectMapper.readValue(json, clazz)`.
2. En caso de excepción, la convierte en `BasicException`.
3. Devuelve la instancia.

##### Método `convertToEntityList`

Deserializa una cadena JSON a una lista de instancias de la clase indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **json** | `String` | Cadena JSON con un array. |
| **clazz** | `Class<T>` | Clase de los elementos de la lista. |

Retorna: `List<T>` — lista de instancias deserializadas.

Algoritmo:
1. Construye un `JavaType` de tipo `List<T>` con `objectMapper.getTypeFactory().constructCollectionType`.
2. Invoca `objectMapper.readValue(json, javaType)`.
3. En caso de excepción, la convierte en `BasicException`.
4. Devuelve la lista.

##### Método `toMapList`

Convierte un objeto Java a una lista de mapas `Map<String, Object>`, útil para transformar listas de entidades en estructuras genéricas.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **source** | `Object` | Objeto o lista de objetos a convertir. |

Retorna: `List<Map<String, Object>>` — lista de mapas con los datos del objeto fuente.

Algoritmo:
1. Serializa `source` a JSON con `convertToJson`.
2. Deserializa el JSON a `List<Map<String, Object>>` con `convertToEntityList`.
3. Devuelve la lista resultante.

---

#### Clase `LogAspect`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Aspecto Spring AOP que intercepta las llamadas a los métodos de las clases de servicio del paquete `com.bbva.wgtb`, excluyendo las generadas automáticamente, para registrar información de entrada, salida y tiempos de ejecución.

##### Método `serviceClasses`

Define el pointcut que selecciona todos los métodos de las clases `Service*` del paquete base, excluyendo las clases del subpaquete `apirestgen`.

Retorna: `void` — actúa como marcador de pointcut.

##### Método `logAround`

Intercepta la ejecución de los métodos seleccionados por el pointcut para registrar trazas de entrada, salida y duración.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **joinPoint** | `ProceedingJoinPoint` | Punto de unión que representa el método interceptado. |

Retorna: `Object` — resultado de la ejecución del método interceptado.

Algoritmo:
1. Registra en log el nombre del método y los argumentos recibidos.
2. Registra el instante de inicio.
3. Invoca `joinPoint.proceed()` para ejecutar el método real.
4. Registra el instante de fin y calcula la duración.
5. Registra el resultado y el tiempo transcurrido.
6. En caso de excepción, la registra y la relanza.
7. Devuelve el resultado de `proceed()`.

---

#### Clase `NovaUtils`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Componente Spring que proporciona utilidades para extraer datos del objeto `NovaMetadata` de las peticiones, en particular el identificador de usuario autenticado a través de la cabecera `iv-user`.

##### Método `getNovaUser`

Extrae el identificador del usuario autenticado desde los metadatos NOVA de la petición.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **novaMetadata** | `NovaMetadata` | Metadatos NOVA de la petición entrante. |

Retorna: `String` — identificador del usuario autenticado.

Algoritmo:
1. Obtiene las cabeceras implícitas de entrada con `novaMetadata.getNovaImplicitHeadersInput()`.
2. Busca la cabecera con nombre `iv-user`.
3. Si no se encuentra o está vacía, lanza `AuthenticationException`.
4. Devuelve el valor de la cabecera encontrada.

---

#### Clase `ObjectUpdater`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Componente Spring que actualiza los campos de un objeto existente con los valores no nulos de un objeto nuevo, usando reflexión para iterar sobre todos los campos declarados.

##### Método `update`

Copia los campos no nulos de `newObject` sobre `objectToUpdate`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **objectToUpdate** | `T` | Objeto destino a actualizar. |
| **newObject** | `T` | Objeto fuente con los nuevos valores. |

Retorna: `T` — el objeto `objectToUpdate` con los campos actualizados.

Algoritmo:
1. Obtiene todos los campos declarados de la clase con `getDeclaredFields()`.
2. Para cada campo, lo hace accesible con `setAccessible(true)`.
3. Obtiene el valor del campo en `newObject`.
4. Si el valor no es `null`, lo asigna al mismo campo en `objectToUpdate`.
5. Si se produce `IllegalAccessException`, lanza `GenericException` con estado `INTERNAL_SERVER_ERROR`.
6. Devuelve `objectToUpdate`.

---

#### Clase `Page`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Clase genérica de paginación que encapsula un subconjunto de resultados junto con los metadatos necesarios para navegar entre páginas, sin depender de la implementación de Spring Data.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **content** | `List<T>` | Get | Lista de elementos de la página actual. |
| **pageNumber** | `int` | Get | Número de página (0-indexed). |
| **pageSize** | `int` | Get | Tamaño máximo de la página. |
| **totalElements** | `long` | Get | Total de elementos en todas las páginas. |

##### Constructor `Page(List<T>, int, int, long)`

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **content** | `List<T>` | Elementos de la página actual. |
| **pageNumber** | `int` | Número de página (0-indexed). |
| **pageSize** | `int` | Tamaño de la página. |
| **totalElements** | `long` | Total de elementos. |

Algoritmo:
1. Asigna cada parámetro a su propiedad correspondiente.

##### Constructor `Page(List<T>)`

Constructor de conveniencia para una página única (sin metadatos de paginación).

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **content** | `List<T>` | Lista completa de elementos. |

Algoritmo:
1. Delega en el constructor principal con `pageNumber=0`, `pageSize=content.size()` y `totalElements=content.size()`.

##### Método `getTotalPages`

Calcula el número total de páginas a partir del total de elementos y el tamaño de página.

Retorna: `int` — número total de páginas.

Algoritmo:
1. Si `pageSize` es 0, devuelve 1.
2. En caso contrario, devuelve `(int) Math.ceil((double) totalElements / pageSize)`.

##### Método `hasNext`

Indica si existe una página siguiente a la actual.

Retorna: `boolean` — `true` si hay más páginas, `false` en caso contrario.

Algoritmo:
1. Devuelve `pageNumber + 1 < getTotalPages()`.

##### Método `isLast`

Indica si la página actual es la última.

Retorna: `boolean` — `true` si es la última página.

Algoritmo:
1. Devuelve `!hasNext()`.

##### Método `map`

Transforma los elementos de la página aplicando la función de conversión indicada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **converter** | `Function<? super T, ? extends U>` | Función de transformación de elementos. |

Retorna: `Page<U>` — nueva página con los elementos transformados y los mismos metadatos de paginación.

Algoritmo:
1. Aplica `converter` a cada elemento de `content` con `stream().map().collect()`.
2. Construye y devuelve una nueva `Page<U>` con la lista transformada y los mismos `pageNumber`, `pageSize` y `totalElements`.

---

#### Clase `StringUtils`

***Package: com.bbva.wgtb.wgtbbackend.utils***

Utilidad estática con métodos de manipulación de cadenas de texto.

##### Método `capitalize`

Convierte el primer carácter de una cadena a mayúscula.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **str** | `String` | Cadena a capitalizar. |

Retorna: `String` — cadena con el primer carácter en mayúscula, o la cadena original si es nula o vacía.

Algoritmo:
1. Si `str` es `null` o vacía, la devuelve tal cual.
2. Convierte el primer carácter a mayúscula con `Character.toUpperCase`.
3. Concatena con el resto de la cadena desde el índice 1.
4. Devuelve el resultado.

---

#### Clase `TableFilterUtils`

***Package: com.bbva.wgtb.wgtbbackend.utils***

DTO serializable que representa un filtro aplicado sobre una columna de tabla, encapsulando el código del campo, la dirección de ordenación y el valor de filtrado.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **tableFieldCode** | `String` | Get/Set | Código del campo de tabla al que se aplica el filtro. |
| **sortOrder** | `String` | Get/Set | Dirección de ordenación (`asc` o `desc`), o `null` si no aplica. |
| **value** | `String` | Get/Set | Valor del filtro a aplicar sobre el campo. |

---

### Paquete `com.bbva.wgtb.wgtbbackend.utils.converter`

Contiene los convertidores JPA que gestionan la transformación entre tipos Java y sus representaciones en base de datos.

---

#### Clase `BooleanYNConverter`

***Package: com.bbva.wgtb.wgtbbackend.utils.converter***
***Implements: AttributeConverter<Boolean, String>***

Convertidor JPA que traduce valores `Boolean` de Java a los caracteres `"Y"` / `"N"` en base de datos y viceversa.

##### Método `convertToDatabaseColumn`

Convierte un valor `Boolean` al carácter correspondiente para persistir en base de datos.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **attribute** | `Boolean` | Valor booleano a convertir. |

Retorna: `String` — `"Y"` si `true`, `"N"` si `false` o `null`.

Algoritmo:
1. Si `attribute` es `null` o `false`, devuelve `"N"`.
2. En caso contrario, devuelve `"Y"`.

##### Método `convertToEntityAttribute`

Convierte el valor almacenado en base de datos al tipo `Boolean`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **dbData** | `String` | Valor leído de base de datos. |

Retorna: `Boolean` — `true` si el valor es `"Y"`, `false` en cualquier otro caso.

Algoritmo:
1. Devuelve `YES.equals(dbData)`.

---

#### Clase `NullConverter`

***Package: com.bbva.wgtb.wgtbbackend.utils.converter***
***Implements: AttributeConverter<String, String>***

Convertidor JPA que trata la cadena literal `"null"` almacenada en base de datos como `null` en Java, y convierte los valores `null` de Java a `null` al persistir.

##### Método `convertToDatabaseColumn`

Convierte un atributo `String` para persistirlo en base de datos.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **attribute** | `String` | Valor Java a convertir. |

Retorna: `String` — `null` si el atributo es `null` o es la cadena `"null"`, el propio valor en caso contrario.

Algoritmo:
1. Si `attribute` es `null` o igual a la constante `NULL`, devuelve `null`.
2. En caso contrario, devuelve `attribute`.

##### Método `convertToEntityAttribute`

Convierte el valor leído de base de datos al atributo Java.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **dbData** | `String` | Valor leído de base de datos. |

Retorna: `String` — `null` si el valor es la cadena `"null"` o `null`, el propio valor en caso contrario.

Algoritmo:
1. Si `dbData` es `null` o igual a la constante `NULL`, devuelve `null`.
2. En caso contrario, devuelve `dbData`.

---

#### Clase `StringListConverter`

***Package: com.bbva.wgtb.wgtbbackend.utils.converter***
***Implements: AttributeConverter<List<String>, String>***

Convertidor JPA que serializa una `List<String>` a una cadena de valores separados por comas para su almacenamiento en base de datos, y realiza la operación inversa al leer.

##### Método `convertToDatabaseColumn`

Serializa la lista de cadenas a un único `String` separado por comas.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **attribute** | `List<String>` | Lista de cadenas a serializar. |

Retorna: `String` — cadena con los elementos unidos por `","`, o `null` si la lista es nula o vacía.

Algoritmo:
1. Si `attribute` es `null` o vacía, devuelve `null`.
2. Une los elementos con `String.join(SEPARATOR, attribute)`.
3. Devuelve la cadena resultante.

##### Método `convertToEntityAttribute`

Deserializa la cadena almacenada en base de datos a una `List<String>`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **dbData** | `String` | Cadena con valores separados por comas. |

Retorna: `List<String>` — lista de cadenas, o lista vacía si `dbData` es nulo o vacío.

Algoritmo:
1. Si `dbData` es `null` o vacío, devuelve `Collections.emptyList()`.
2. Divide `dbData` por `SEPARATOR` con `Arrays.stream(dbData.split(SEPARATOR))`.
3. Recorta espacios de cada elemento con `map(String::trim)`.
4. Recolecta y devuelve la lista.

---

### Paquete `com.bbva.wgtb.wgtbbackend.utils.jsonParser`

Proporciona los serializadores y deserializadores Jackson personalizados para los tipos de fecha `LocalDate` y `OffsetDateTime`, asegurando el uso consistente de los formatos ISO-8601 definidos en `Constants`.

---

#### Clase `LocalDateDeserializer`

***Package: com.bbva.wgtb.wgtbbackend.utils.jsonParser***
***Extends: JsonDeserializer<LocalDate>***

Deserializador Jackson que convierte cadenas JSON en formato `yyyy-MM-dd` al tipo `LocalDate` usando el `DATE_FORMATTER` de `Constants`.

##### Método `deserialize`

Transforma el token de texto JSON en un objeto `LocalDate`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **p** | `JsonParser` | Parser JSON posicionado en el token de fecha. |
| **ctxt** | `DeserializationContext` | Contexto de deserialización. |

Retorna: `LocalDate` — fecha parseada.

Algoritmo:
1. Obtiene el texto del token con `p.getText()`.
2. Parsea el texto con `LocalDate.parse(text, Constants.DATE_FORMATTER)`.
3. Devuelve el `LocalDate` resultante.

---

#### Clase `LocalDateSerializer`

***Package: com.bbva.wgtb.wgtbbackend.utils.jsonParser***
***Extends: JsonSerializer<LocalDate>***

Serializador Jackson que convierte objetos `LocalDate` a su representación en cadena JSON con formato `yyyy-MM-dd`.

##### Método `serialize`

Escribe el valor `LocalDate` como token de texto en el JSON de salida.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **value** | `LocalDate` | Fecha a serializar. |
| **gen** | `JsonGenerator` | Generador JSON de salida. |
| **serializers** | `SerializerProvider` | Proveedor de serializadores del contexto. |

Retorna: `void`

Algoritmo:
1. Formatea `value` con `Constants.DATE_FORMATTER.format(value)`.
2. Escribe la cadena resultante con `gen.writeString(formatted)`.

---

#### Clase `OffsetDateTimeDeserializer`

***Package: com.bbva.wgtb.wgtbbackend.utils.jsonParser***
***Extends: JsonDeserializer<OffsetDateTime>***

Deserializador Jackson que convierte cadenas JSON en formato ISO-8601 con zona horaria al tipo `OffsetDateTime`, usando los formateadores definidos en `Constants`.

##### Método `deserialize`

Transforma el token de texto JSON en un objeto `OffsetDateTime`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **p** | `JsonParser` | Parser JSON posicionado en el token de fecha-hora. |
| **ctxt** | `DeserializationContext` | Contexto de deserialización. |

Retorna: `OffsetDateTime` — fecha-hora con zona horaria parseada.

Algoritmo:
1. Obtiene el texto del token con `p.getText()`.
2. Intenta parsear con `OffsetDateTime.parse` usando los formateadores de `Constants`.
3. Devuelve el `OffsetDateTime` resultante.

---

#### Clase `OffsetDateTimeSerializer`

***Package: com.bbva.wgtb.wgtbbackend.utils.jsonParser***
***Extends: JsonSerializer<OffsetDateTime>***

Serializador Jackson que convierte objetos `OffsetDateTime` a su representación en cadena JSON en formato ISO-8601 con zona horaria.

##### Método `serialize`

Escribe el valor `OffsetDateTime` como token de texto en el JSON de salida.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **value** | `OffsetDateTime` | Fecha-hora con zona horaria a serializar. |
| **gen** | `JsonGenerator` | Generador JSON de salida. |
| **serializers** | `SerializerProvider` | Proveedor de serializadores del contexto. |

Retorna: `void`

Algoritmo:
1. Formatea `value` con el formateador ISO-8601 de `Constants`.
2. Escribe la cadena resultante con `gen.writeString(formatted)`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.utils.mapper`

Agrupa las interfaces y clases base de mapeo entre capas (modelo, entidad, DTO), incluyendo soporte para auditoría y conversión de tipos de fecha.

---

#### Clase `AuditedDomain`

***Package: com.bbva.wgtb.wgtbbackend.utils.mapper***

Clase base para los objetos de dominio que requieren información de auditoría (usuario y fecha de modificación).

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **user** | `String` | Get/Set | Usuario que realizó la última modificación. |
| **modificationDate** | `OffsetDateTime` | Get/Set | Fecha y hora de la última modificación. |

---

#### Clase `AuditedEntity`

***Package: com.bbva.wgtb.wgtbbackend.utils.mapper***

Superclase mapeada JPA que añade los campos de auditoría a las entidades que la extiendan. Los valores se persisten en las columnas `AUD_USER` y `AUD_FMO`.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **user** | `String` | Get/Set | Usuario que realizó la última modificación, mapeado a la columna `AUD_USER`. |
| **modificationDate** | `OffsetDateTime` | Get/Set | Fecha de última modificación, mapeada a la columna `AUD_FMO`. |

---

#### Interfaz `DateMapper`

***Package: com.bbva.wgtb.wgtbbackend.utils.mapper***

Interfaz MapStruct con métodos de conversión por defecto entre los tipos de fecha del sistema (`LocalDate`, `OffsetDateTime` y `String`), disponible como componente Spring para inyección en otros mappers.

##### Método `toOffsetDateTime(LocalDate)`

Convierte una fecha `LocalDate` a `OffsetDateTime` con offset UTC.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **localDate** | `LocalDate` | Fecha a convertir. |

Retorna: `OffsetDateTime` — fecha-hora a medianoche UTC, o `null` si la entrada es `null`.

Algoritmo:
1. Si `localDate` es `null`, devuelve `null`.
2. Convierte con `localDate.atStartOfDay().atOffset(ZoneOffset.UTC)`.

##### Método `toLocalDate(OffsetDateTime)`

Convierte un `OffsetDateTime` a `LocalDate`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **offsetDateTime** | `OffsetDateTime` | Fecha-hora a convertir. |

Retorna: `LocalDate` — componente de fecha, o `null` si la entrada es `null`.

Algoritmo:
1. Si `offsetDateTime` es `null`, devuelve `null`.
2. Devuelve `offsetDateTime.toLocalDate()`.

##### Método `toOffsetDateTime(String)`

Convierte una cadena ISO-8601 a `OffsetDateTime`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **value** | `String` | Cadena ISO-8601 con zona horaria. |

Retorna: `OffsetDateTime` — instancia parseada, o `null` si la cadena es nula o vacía.

Algoritmo:
1. Si `value` es `null` o vacío, devuelve `null`.
2. Parsea con `OffsetDateTime.parse(value, Constants.FORMATTER)`.
3. Devuelve el resultado.

##### Método `toString(OffsetDateTime)`

Convierte un `OffsetDateTime` a cadena ISO-8601.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **offsetDateTime** | `OffsetDateTime` | Fecha-hora a formatear. |

Retorna: `String` — representación ISO-8601, o `null` si la entrada es `null`.

Algoritmo:
1. Si `offsetDateTime` es `null`, devuelve `null`.
2. Formatea con el formateador de `Constants` y devuelve la cadena.

##### Método `toLocalDate(String)`

Convierte una cadena `yyyy-MM-dd` a `LocalDate`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **value** | `String` | Cadena en formato `yyyy-MM-dd`. |

Retorna: `LocalDate` — instancia parseada, o `null` si la cadena es nula o vacía.

Algoritmo:
1. Si `value` es `null` o vacío, devuelve `null`.
2. Parsea con `LocalDate.parse(value, Constants.DATE_FORMATTER)`.

##### Método `toString(LocalDate)`

Convierte un `LocalDate` a su representación `yyyy-MM-dd`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **localDate** | `LocalDate` | Fecha a formatear. |

Retorna: `String` — cadena formateada, o `null` si la entrada es `null`.

Algoritmo:
1. Si `localDate` es `null`, devuelve `null`.
2. Formatea con `Constants.DATE_FORMATTER` y devuelve la cadena.

---

#### Interfaz `GenericDtoMapper`

***Package: com.bbva.wgtb.wgtbbackend.utils.mapper***

Interfaz genérica de mapeo entre modelos de dominio (`M`) y objetos DTO (`D`). Define el contrato completo de conversión bidireccional, incluyendo transformaciones de listas y arrays.

**Métodos:**

- `toModel(D dto)` — convierte un DTO a modelo; puede lanzar `GenericException`.
- `toDto(M model)` — convierte un modelo a DTO; puede lanzar `GenericException`.
- `toModelList(List<D> dtoList)` — convierte una lista de DTOs a lista de modelos.
- `toModelList(D[] dtoArray)` — convierte un array de DTOs a lista de modelos.
- `toDtoList(List<M> modelList)` — convierte una lista de modelos a lista de DTOs.
- `toModelArray(List<D> dtoList)` — convierte una lista de DTOs a array de modelos.
- `toDtoArray(List<M> modelList)` — convierte una lista de modelos a array de DTOs.

---

#### Interfaz `GenericEntityMapper`

***Package: com.bbva.wgtb.wgtbbackend.utils.mapper***

Interfaz genérica de mapeo entre modelos de dominio (`M`) y entidades JPA (`E`). Define el contrato completo de conversión bidireccional.

**Métodos:**

- `toModel(E entity)` — convierte una entidad a modelo.
- `toEntity(M model)` — convierte un modelo a entidad.
- `toModelList(List<E> entityList)` — convierte lista de entidades a lista de modelos.
- `toentityList(List<M> modelList)` — convierte lista de modelos a lista de entidades.
- `toModelArray(List<E> entityList)` — convierte lista de entidades a array de modelos.
- `toEntityArray(List<M> modelList)` — convierte lista de modelos a array de entidades.

---

#### Interfaz `GenericMapper`

***Package: com.bbva.wgtb.wgtbbackend.utils.mapper***

Interfaz con métodos de conversión de fecha por defecto, diseñada para ser extendida por los mappers MapStruct del proyecto, evitando la duplicación de lógica de conversión de tipos temporales.

##### Método `mapToOffsetDateTime`

Convierte `LocalDate` a `OffsetDateTime` a medianoche UTC.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **localDate** | `LocalDate` | Fecha a convertir. |

Retorna: `OffsetDateTime` — fecha-hora a medianoche UTC, o `null`.

##### Método `mapToLocalDate`

Extrae el componente de fecha de un `OffsetDateTime`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **offsetDateTime** | `OffsetDateTime` | Fecha-hora a convertir. |

Retorna: `LocalDate` — componente de fecha, o `null`.

##### Método `parseOffsetDateTime`

Serializa un `OffsetDateTime` a cadena ISO-8601.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **offsetDateTime** | `OffsetDateTime` | Fecha-hora a formatear. |

Retorna: `String` — cadena ISO-8601, o `null`.

##### Método `parseLocalDate`

Serializa un `LocalDate` a cadena `yyyy-MM-dd`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **localDate** | `LocalDate` | Fecha a formatear. |

Retorna: `String` — cadena en formato `yyyy-MM-dd`, o `null`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.xbpm`

Contiene la configuración del cliente REST NOVA para el sistema XBPM y el servicio que encapsula todas las operaciones disponibles sobre dicho sistema, incluyendo gestión de tareas, instancias de proceso, usuarios y propiedades.

---

#### Clase `ConfigApi`

***Package: com.bbva.wgtb.wgtbbackend.xbpm***

Clase de configuración Spring que registra los beans necesarios para conectarse al microservicio XBPM (`Api`) a través de la microgateway NOVA.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **microgatewayHostPort** | `String` | N/A | Host y puerto de la microgateway para `Api` (por defecto `localhost:24000`). |
| **microgatewayTimeout** | `Integer` | N/A | Timeout en milisegundos (por defecto `10000`). |
| **releaseHeader** | `String` | N/A | Cabecera de release NOVA (por defecto `seguridad`). |

##### Método `getRestHandlerApi`

Instancia y registra el bean `RestHandlerApi` para el cliente XBPM.

Retorna: `RestHandlerApi` — cliente REST para el servicio `Api`.

Algoritmo:
1. Construye `RestHandlerApi` con `NovaMetadata` y `NovaRequestConfig` ya definidos como beans.
2. Registra y devuelve la instancia.

##### Método `getNovaMetadata`

Construye y registra el bean `Api.novaMetadata`.

Retorna: `NovaMetadata` — metadatos de cabeceras NOVA para `Api`.

Algoritmo:
1. Crea una lista de `NovaImplicitHeadersOutput` con la cabecera de release.
2. Construye y devuelve `NovaMetadata`.

##### Método `getConfigRequestSchema`

Construye y registra el bean `Api.novaRequestconfig`.

Retorna: `NovaRequestConfig` — configuración de protocolo y host para `Api`.

Algoritmo:
1. Construye `NovaRequestConfig` con el esquema HTTP y `microgatewayHostPort`.
2. Establece `microgatewayTimeout`.
3. Devuelve la configuración.

---

#### Clase `ServiceApi`

***Package: com.bbva.wgtb.wgtbbackend.xbpm***

Servicio Spring que centraliza todas las operaciones sobre el sistema XBPM: envío de señales, gestión del ciclo de vida de tareas (reclamar, iniciar, completar, liberar, delegar), consulta de instancias de proceso, gestión de usuarios y grupos, y administración de propiedades de API en MongoDB.

**Propiedades:**

| Nombre | Tipo | Get/Set | Descripción |
| :---: | :---: | :---: | ----- |
| **NS_ID** | `String` | N/A | Identificador del namespace XBPM (`wgtb.gl`). |
| **INSTANCE_ID** | `String` | N/A | Identificador del modelo de instancia (`wgtb_process`). |
| **novaMetadata** | `NovaMetadata` | N/A | Metadatos NOVA para las peticiones. |
| **jsonUtils** | `JsonUtils` | N/A | Utilidad de conversión JSON. |
| **novaRequestConfig** | `NovaRequestConfig` | N/A | Configuración del protocolo REST. |
| **restHandlerApi** | `IRestHandlerApi` | N/A | Cliente REST NOVA generado para `Api`. |

##### Método `sendSignalEvent`

Envía un evento de señal al motor XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **sendSignalEventBody** | `Object` | Cuerpo del evento a enviar. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Serializa `sendSignalEventBody` a JSON con `jsonUtils`.
2. Invoca `restHandlerApi.sendSignalEvent` con los metadatos y la configuración.
3. Captura excepciones y las relanza como `XbpmException`.
4. Devuelve la respuesta.

##### Método `completeTask`

Completa una tarea BPM enviando los datos de negocio y la acción correspondiente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **businessData** | `BusinessData` | Datos de negocio asociados a la tarea. |
| **taskAction** | `TaskAction` | Acción a ejecutar sobre la tarea. |
| **taskId** | `String` | Identificador de la tarea a completar. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Construye el objeto BPM con `buildBpmObject` a partir de los datos de negocio y la acción.
2. Serializa el objeto resultante a JSON.
3. Invoca `restHandlerApi.completeTask` con el `taskId` y el JSON construido.
4. Captura excepciones y las relanza como `XbpmException`.
5. Devuelve la respuesta.

##### Método `buildBpmObject`

Construye la estructura JSON requerida por XBPM para completar una tarea, a partir de un mapa de datos y una acción.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **data** | `Map<String, Object>` | Mapa con los datos de negocio. |
| **action** | `TaskAction` | Acción a incluir en el objeto BPM. |

Retorna: `String` — JSON con la estructura de objeto BPM.

Algoritmo:
1. Invoca `parseBusinessData` para transformar el mapa a la estructura esperada por XBPM.
2. Agrega el campo de acción al mapa resultante.
3. Serializa el mapa a JSON y devuelve la cadena.

##### Método `parseBusinessData`

Transforma un mapa de datos de negocio a la estructura de variables de proceso requerida por XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **data** | `Map<String, Object>` | Datos de negocio en formato plano. |

Retorna: `Map<String, Object>` — mapa estructurado según el formato de variables XBPM.

Algoritmo:
1. Itera sobre las entradas del mapa de entrada.
2. Para cada entrada, construye la estructura de variable XBPM con nombre y valor.
3. Acumula las variables en el mapa de salida.
4. Devuelve el mapa estructurado.

##### Método `mergeMaps`

Fusiona el contenido de `newMap` dentro de `mainMap`, concatenando listas cuando la clave ya existe con un valor de tipo `List`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **mainMap** | `Map<String, Object>` | Mapa destino que recibirá los nuevos valores. |
| **newMap** | `Map<String, Object>` | Mapa fuente con los valores a fusionar. |

Retorna: `void`

Algoritmo:
1. Itera sobre las entradas de `newMap`.
2. Para cada entrada, si `mainMap` ya contiene la clave y el valor es una `List`, añade los nuevos valores a la lista existente.
3. Si la clave no existe en `mainMap`, la inserta directamente.

##### Método `startTask`

Inicia una tarea BPM asignándola al usuario actual.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **taskId** | `String` | Identificador de la tarea a iniciar. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Invoca `restHandlerApi.startTask` con `taskId`, `novaMetadata` y `novaRequestConfig`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getUsersFromGroupExtended`

Obtiene la lista extendida de usuarios de un grupo XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **group** | `String` | Nombre del grupo a consultar. |

Retorna: `ResponseGroupUsersExtended` — objeto con la información extendida de los usuarios del grupo.

Algoritmo:
1. Invoca `restHandlerApi.getUsersFromGroupExtended` con `group`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `searchActiveTasks`

Busca todas las tareas activas en el sistema XBPM para el namespace configurado.

Retorna: `List<BpmTask>` — lista de tareas BPM activas.

Algoritmo:
1. Construye la query RSQL para buscar tareas activas del modelo de instancia.
2. Invoca `restHandlerApi.getActivities` con la query, `novaMetadata` y `novaRequestConfig`.
3. Mapea la respuesta a `List<BpmTask>`.
4. Captura excepciones y las relanza como `XbpmException`.
5. Devuelve la lista.

##### Método `searchTaskByTypeAndBusinessId`

Busca tareas activas filtradas por tipo de tarea e identificador de negocio.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **taskType** | `TaskType` | Tipo de tarea a filtrar. |
| **businessId** | `String` | Identificador de negocio asociado a la instancia. |

Retorna: `List<BpmTask>` — lista de tareas que cumplen los filtros.

Algoritmo:
1. Construye la query RSQL combinando el tipo de tarea y el `businessId`.
2. Invoca `restHandlerApi.getActivities` con la query construida.
3. Mapea y devuelve la lista de `BpmTask`.

##### Método `getUserMailUsingGET`

Obtiene el correo electrónico de un usuario XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **user** | `String` | Identificador del usuario. |
| **product** | `String` | Producto en el contexto del cual se consulta. |

Retorna: `ResponseGetMail` — objeto con el correo del usuario.

Algoritmo:
1. Invoca `restHandlerApi.getUserMailUsingGET` con `user` y `product`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `abortInstance`

Aborta una instancia de proceso XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **instanceid** | `String` | Identificador de la instancia a abortar. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Invoca `restHandlerApi.abortInstance` con `instanceid`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getActivityDetail`

Obtiene el detalle de una actividad XBPM a partir de su identificador y el de su instancia de proceso.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **activityId** | `String` | Identificador de la actividad. |
| **instanceId** | `String` | Identificador de la instancia de proceso. |

Retorna: `ActivityDetail` — objeto con el detalle de la actividad.

Algoritmo:
1. Invoca `restHandlerApi.getActivityDetail` con `activityId` e `instanceId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `claimTask`

Reclama una tarea BPM para el usuario actual.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **taskId** | `String` | Identificador de la tarea a reclamar. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Invoca `restHandlerApi.claimTask` con `taskId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getVariables`

Recupera las variables de proceso de una instancia XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **instanceId** | `String` | Identificador de la instancia de proceso. |

Retorna: `String` — JSON con las variables de la instancia.

Algoritmo:
1. Invoca `restHandlerApi.getVariables` con `instanceId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `sendSignal`

Envía una señal a una instancia de proceso XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **SendSignal** | `String` | Nombre de la señal a enviar. |
| **instanceId** | `String` | Identificador de la instancia de proceso. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Invoca `restHandlerApi.sendSignal` con `SendSignal` e `instanceId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `deleteApiPropertyInDatabase`

Elimina una propiedad de API almacenada en MongoDB.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **id** | `String` | Identificador de la propiedad a eliminar. |

Retorna: `CommonResponse` — respuesta con el resultado de la operación.

Algoritmo:
1. Invoca `restHandlerApi.deleteApiPropertyInDatabase` con `id`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `auditRecover`

Recupera el log de auditoría de una instancia de proceso.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **nsId** | `String` | Identificador del namespace. |
| **instanceId** | `String` | Identificador de la instancia de proceso. |

Retorna: `String` — JSON con los datos de auditoría.

Algoritmo:
1. Invoca `restHandlerApi.auditRecover` con `nsId` e `instanceId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `existUserUsingGET`

Comprueba si un usuario existe en el sistema XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **user** | `String` | Identificador del usuario. |
| **product** | `String` | Producto en el contexto del cual se consulta. |

Retorna: `ResponseGetUser` — objeto con la información del usuario si existe.

Algoritmo:
1. Invoca `restHandlerApi.existUserUsingGET` con `user` y `product`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getAllInstances`

Recupera todas las instancias de proceso almacenadas en MongoDB.

Retorna: `ColeccionMongo[]` — array con todas las instancias.

Algoritmo:
1. Invoca `restHandlerApi.getAllInstances`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve el array de instancias.

##### Método `getAllActivities`

Recupera todas las actividades de una instancia de proceso.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **nsId** | `String` | Identificador del namespace. |
| **instanceid** | `String` | Identificador de la instancia. |

Retorna: `ResponseAuditoria` — objeto con la lista de actividades auditadas.

Algoritmo:
1. Invoca `restHandlerApi.getAllActivities` con `nsId` e `instanceid`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `releaseTask`

Libera una tarea BPM previamente reclamada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **taskId** | `String` | Identificador de la tarea a liberar. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Invoca `restHandlerApi.releaseTask` con `taskId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getProcessModels`

Obtiene los modelos de proceso disponibles para un namespace.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **nsId** | `String` | Identificador del namespace. |

Retorna: `String` — JSON con los modelos de proceso.

Algoritmo:
1. Invoca `restHandlerApi.getProcessModels` con `nsId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getUsersFromGroup`

Obtiene la lista de usuarios de un grupo XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **group** | `String` | Nombre del grupo. |

Retorna: `ResponseGroupUsers` — objeto con la lista de usuarios del grupo.

Algoritmo:
1. Invoca `restHandlerApi.getUsersFromGroup` con `group`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `taskCounter`

Obtiene el contador de tareas activas por proceso y usuario.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **processNames** | `String[]` | Nombres de los modelos de proceso a contabilizar. |
| **user** | `String` | Identificador del usuario. |

Retorna: `ResponseTaskCounter[]` — array con los contadores por proceso.

Algoritmo:
1. Invoca `restHandlerApi.taskCounter` con `processNames` y `user`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve el array de contadores.

##### Método `getUserGroupsUsingGET`

Obtiene los grupos a los que pertenece un usuario.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **user** | `String` | Identificador del usuario. |
| **product** | `String` | Producto en el contexto del cual se consulta. |

Retorna: `ResponseUserGroups` — objeto con los grupos del usuario.

Algoritmo:
1. Invoca `restHandlerApi.getUserGroupsUsingGET` con `user` y `product`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `reloadCapacityMasterFiles`

Fuerza la recarga de los ficheros maestros de capacidad en XBPM.

Retorna: `CommonResponse` — respuesta con el resultado de la operación.

Algoritmo:
1. Invoca `restHandlerApi.reloadCapacityMasterFiles`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `addApiPropertiesToDatabase`

Almacena una nueva propiedad de API en MongoDB.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **apiProperties** | `ApiProperties` | Objeto con las propiedades a almacenar. |

Retorna: `ApiProperties` — objeto con las propiedades almacenadas, incluyendo el identificador asignado.

Algoritmo:
1. Invoca `restHandlerApi.addApiPropertiesToDatabase` con `apiProperties`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getAllApiPropertiesInDatabase`

Recupera todas las propiedades de API almacenadas en MongoDB.

Retorna: `ResponseApiProperties` — objeto con todas las propiedades disponibles.

Algoritmo:
1. Invoca `restHandlerApi.getAllApiPropertiesInDatabase`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getInstanceByInstanceId`

Obtiene una instancia de proceso por su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **instanceId** | `String` | Identificador de la instancia. |

Retorna: `ColeccionMongo` — objeto con los datos de la instancia.

Algoritmo:
1. Invoca `restHandlerApi.getInstanceByInstanceId` con `instanceId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `delegateTask`

Delega una tarea BPM a otro usuario.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **objectJson** | `String` | JSON con los datos de la delegación. |
| **taskId** | `String` | Identificador de la tarea a delegar. |
| **nsId** | `String` | Identificador del namespace. |

Retorna: `String` — respuesta del servicio XBPM.

Algoritmo:
1. Invoca `restHandlerApi.delegateTask` con `objectJson`, `taskId` y `nsId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `persistInternalTask`

Persiste una tarea interna en MongoDB a través del servicio XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **objectJson** | `ColeccionMongo` | Objeto con los datos de la tarea a persistir. |

Retorna: `ColeccionMongo` — objeto persistido con el identificador asignado.

Algoritmo:
1. Invoca `restHandlerApi.persistInternalTask` con `objectJson`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `instanceImage`

Obtiene la imagen (diagrama) de una instancia de proceso XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **nsId** | `String` | Identificador del namespace. |
| **instanceId** | `String` | Identificador de la instancia. |

Retorna: `String` — representación en base64 o URL de la imagen del proceso.

Algoritmo:
1. Invoca `restHandlerApi.instanceImage` con `nsId` e `instanceId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `exitsGroup`

Comprueba si un grupo existe en el sistema XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **group** | `String` | Nombre del grupo a verificar. |

Retorna: `ResponseGetGroup` — objeto con la información del grupo si existe.

Algoritmo:
1. Invoca `restHandlerApi.exitsGroup` con `group`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getUserInfo`

Obtiene la información completa de un usuario XBPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **ivUser** | `String` | Identificador del usuario. |
| **product** | `String` | Producto en el contexto del cual se consulta. |

Retorna: `ResponseGetUser` — objeto con la información del usuario.

Algoritmo:
1. Invoca `restHandlerApi.getUserInfo` con `ivUser` y `product`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getAdminAllInstances`

Recupera todas las instancias de proceso con permisos de administrador.

Retorna: `ColeccionMongo[]` — array con todas las instancias disponibles para el administrador.

Algoritmo:
1. Invoca `restHandlerApi.getAdminAllInstances`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve el array.

##### Método `deleteAllContentMongoDB`

Elimina todo el contenido almacenado en MongoDB para un usuario dado.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **ivUser** | `String` | Identificador del usuario que solicita la limpieza. |

Retorna: `CommonResponse` — respuesta con el resultado de la operación.

Algoritmo:
1. Invoca `restHandlerApi.deleteAllContentMongoDB` con `ivUser`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getTaskByTaskId`

Obtiene los datos de una tarea BPM en formato JSON a partir de su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **taskId** | `String` | Identificador de la tarea. |

Retorna: `String` — JSON con los datos de la tarea.

Algoritmo:
1. Invoca `restHandlerApi.getTaskByTaskId` con `taskId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

##### Método `getTaskTypedById`

Obtiene una tarea BPM deserializada al tipo `BpmTask` a partir de su identificador.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **taskId** | `String` | Identificador de la tarea. |

Retorna: `BpmTask` — objeto de tarea BPM con todos sus campos tipados.

Algoritmo:
1. Invoca `getTaskByTaskId(taskId)` para obtener el JSON de la tarea.
2. Deserializa el JSON a `BpmTask` con `jsonUtils.convertToEntity`.
3. Devuelve la instancia `BpmTask`.

##### Método `pathTask`

Ejecuta una operación de patch sobre una tarea BPM.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **requestTaskPath** | `String` | JSON con los cambios a aplicar. |
| **taskId** | `String` | Identificador de la tarea. |
| **nsId** | `String` | Identificador del namespace. |

Retorna: `String` — respuesta del servicio XBPM tras el patch.

Algoritmo:
1. Invoca `restHandlerApi.pathTask` con `requestTaskPath`, `taskId` y `nsId`.
2. Captura excepciones y las relanza como `XbpmException`.
3. Devuelve la respuesta.

Looking at the provided source code, I can identify the missing elements. The prompt asks for `public` class documentation and specific methods. Let me map them to their actual classes:

- `changeTaskStatus` → `BusinessDataServiceImpl` (maps to `setTaskStatus`)
- `abbreviate` → `JsonUtils`
- `searchTasksTyped`, `searchTasks`, `saveContinueTask`, `persistTaskInOtherProduct`, `sendSignalByCorrelation`, `createNewInstance`, `searchInstances` → `ServiceApi`
- `paginateAndOrder`, `filterTasks`, `taskMatchesAllFilters`, `taskMatchesSingleFilter` → `TableServiceImpl`

Based on the source code provided, several of these method names (`changeTaskStatus`, `saveContinueTask`, `persistTaskInOtherProduct`, `sendSignalByCorrelation`, `createNewInstance`, `searchInstances`, `searchTasksTyped`, `searchTasks`) do **not appear literally** in the code — the closest matches are `setTaskStatus`, `sendSignal`/`sendSignalEvent`, `persistInternalTask`, `getAllInstances`/`getAdminAllInstances`, `getTaskTypedById`, `searchActiveTasks`/`searchTaskByTypeAndBusinessId`. I will document the actual methods as they appear in the source, noting the mapping where applicable.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apibpm.application.impl`

#### Clase `BusinessDataServiceImpl` _(métodos adicionales)_

##### Método `setTaskStatus`

Actualiza el estado de una tarea BPM identificada por su `bpmTaskId`. Utiliza `@SneakyThrows` para propagar excepciones checked sin declararlas explícitamente.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **bpmTaskId** | `String` | Identificador BPM de la tarea cuyo estado se desea actualizar |
| **status** | `String` | Nuevo estado destino; debe coincidir con los valores del enumerado `TaskStatus` |

Retorna: `void`

Algoritmo:
1. Recupera la entidad `Task` desde el repositorio usando `bpmTaskId`; lanza `EntityNotFoundException` si no existe.
2. Valida que el valor de `status` corresponde a un valor válido de `TaskStatus`.
3. Asigna el nuevo estado al campo correspondiente de la entidad `Task`.
4. Persiste la entidad actualizada a través de `ITaskRepository`.

---

### Paquete `com.bbva.wgtb.wgtbbackend.apitableservices.application.impl`

#### Clase `TableServiceImpl` _(métodos adicionales)_

##### Método `paginateAndOrder`

Aplica normalización de página y tamaño, ordenación según los filtros con `sortOrder` activo, y recorte de la lista completa de filas al subconjunto correspondiente a la página solicitada.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **allRows** | `List<List<ColumnValue>>` | Conjunto completo de filas ya construidas antes de paginar |
| **paginationInfo** | `InputPaginationInfoDto` | DTO con número de página, tamaño de página y array de filtros (`TableFilter[]`) |

Retorna: `Page<List<ColumnValue>>` — página resultante con los metadatos de paginación (número de página, tamaño, total de elementos).

Algoritmo:
1. Normaliza el número de página con `normalizePage` (mínimo 0).
2. Normaliza el tamaño de página con `normalizePageSize` (valor por defecto `DEFAULT_PAGE_SIZE`).
3. Extrae el array de `TableFilter` del DTO de paginación.
4. Aplica ordenación sobre `allRows` mediante `applySorting`, que detecta el filtro con `sortOrder` no nulo y ordena usando `compareValues`.
5. Invoca `applyPagination` para calcular el subconjunto de filas correspondiente a la página y construir el objeto `Page`.

---

##### Método `filterTasks`

Filtra la lista de filas de tipo `ColumnValue` descartando aquellas que no satisfacen todos los criterios de filtrado activos presentes en el array de `TableFilter`.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **rows** | `List<List<ColumnValue>>` | Lista completa de filas a filtrar |
| **filters** | `TableFilter[]` | Array de filtros; solo se evalúan los que tienen `value` no en blanco |

Retorna: `List<List<ColumnValue>>` — subconjunto de filas que satisfacen todos los filtros activos.

Algoritmo:
1. Itera sobre `rows` usando un stream.
2. Para cada fila delega en `matchesColumnValueFilters` / `taskMatchesAllFilters` para comprobar si satisface todos los filtros activos.
3. Filtra con `filter()` y recoge el resultado con `collect(Collectors.toList())`.

---

##### Método `taskMatchesAllFilters`

Comprueba si una fila satisface **todos** los filtros activos (aquellos cuyo `value` no es en blanco). Un filtro sin valor se ignora (puede ser un filtro de solo ordenación).

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `List<ColumnValue>` | Fila de la tabla representada como lista de valores de columna |
| **filters** | `TableFilter[]` | Array completo de filtros de la petición |

Retorna: `boolean` — `true` si la fila satisface todos los filtros con valor no en blanco.

Algoritmo:
1. Convierte `filters` en stream.
2. Descarta los filtros cuyo campo `value` sea nulo o en blanco.
3. Para cada filtro activo delega en `taskMatchesSingleFilter`.
4. Retorna `true` solo si **todos** los filtros activos devuelven `true` (operación `allMatch`).

---

##### Método `taskMatchesSingleFilter`

Evalúa si una fila concreta satisface un único filtro: extrae el valor de la columna indicada por `tableFieldCode`, aplica post-procesado y compara de forma insensible a mayúsculas con el valor del filtro.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **row** | `List<ColumnValue>` | Fila de la tabla |
| **filterValue** | `String` | Valor esperado (comparación case-insensitive) |
| **tableFieldCode** | `String` | Código de columna usado para localizar el valor dentro de la fila |

Retorna: `boolean` — `true` si el valor extraído de la fila coincide con `filterValue` ignorando mayúsculas/minúsculas.

Algoritmo:
1. Localiza en `row` el `ColumnValue` cuyo código de columna coincide con `tableFieldCode`.
2. Si no se encuentra ninguna coincidencia, retorna `false`.
3. Obtiene el valor en forma de `String` del `ColumnValue`.
4. Aplica `postProcessBpmValue` si la columna pertenece a datos BPM para normalizar el valor (p. ej. formateo de fechas).
5. Compara el valor procesado con `filterValue` mediante comparación case-insensitive.
6. Retorna el resultado de la comparación.

---

### Paquete `com.bbva.wgtb.wgtbbackend.utils`

#### Clase `JsonUtils` _(métodos adicionales)_

##### Método `abbreviate` _(privado estático)_

Trunca una cadena de texto a una longitud máxima para evitar que trazas de log o mensajes de error incluyan payloads JSON de tamaño excesivo.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **s** | `String` | Cadena a abreviar |

Retorna: `String` — versión truncada de la cadena con sufijo indicador de corte si superaba el límite, o la misma cadena si era más corta.

Algoritmo:
1. Comprueba si `s` es nulo; si lo es, retorna `null`.
2. Compara la longitud de `s` con la longitud máxima configurada (constante interna).
3. Si la longitud es menor o igual al límite, retorna `s` sin modificar.
4. Retorna la subcadena hasta el límite concatenada con un sufijo de elipsis (p. ej. `"..."`).

---

### Paquete `com.bbva.wgtb.wgtbbackend.xbpm`

#### Clase `ServiceApi` _(métodos adicionales)_

##### Método `searchActiveTasks`

Consulta al motor xBPM la lista completa de tareas activas asociadas al proceso `wgtb_process.new_opportunity` y asignadas al usuario en sesión. Corresponde al método referenciado como `searchTasks` en el inventario de ausencias.

Retorna: `List<BpmTask>` — lista de tareas BPM activas deserializadas desde la respuesta JSON del motor xBPM; puede estar vacía si no hay tareas.

Algoritmo:
1. Obtiene el identificador del usuario en sesión desde `NovaSecurityContext`.
2. Construye el string FIQL de filtrado usando la plantilla `INSTANCE.MODEL.ID=in=(wgtb_process.new_opportunity);POTENTIALOWNERSIDS==%s` con el usuario interpolado.
3. Invoca `restHandlerApi` con el filtro FIQL y la metadata Nova configurada.
4. Verifica que el código de respuesta HTTP es `2xx`; lanza `XbpmException` en caso contrario.
5. Deserializa la respuesta con `JsonUtils` a `List<BpmTask>` y la retorna.

---

##### Método `getTaskTypedById`

Recupera una tarea BPM por su identificador y la deserializa en un objeto `BpmTask` tipado. Corresponde al método referenciado como `searchTasksTyped` en el inventario de ausencias.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **taskId** | `String` | Identificador único de la tarea en el motor xBPM |

Retorna: `BpmTask` — representación tipada de la tarea BPM con todos sus campos mapeados.

Lanza: `XbpmException` — si el motor xBPM devuelve un código de error o la respuesta no es parseable.

Algoritmo:
1. Invoca `getTaskByTaskId` para obtener la respuesta JSON en crudo.
2. Deserializa el JSON a `BpmTask` usando `JsonUtils.convertToEntity`.
3. Retorna el objeto `BpmTask` resultante.

---

##### Método `sendSignal`

Envía una señal BPMN a una instancia de proceso concreta para avanzar o desbloquear un flujo en espera. Corresponde al método referenciado como `sendSignalByCorrelation` en el inventario de ausencias.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **SendSignal** | `String` | Nombre o código de la señal BPMN a enviar |
| **instanceId** | `String` | Identificador de la instancia de proceso destinataria |

Retorna: `String` — respuesta en texto plano devuelta por el motor xBPM (normalmente un mensaje de confirmación o el identificador de correlación).

Lanza: `XbpmException` — si la invocación al motor falla o devuelve un código de error.

Algoritmo:
1. Construye el cuerpo de la petición con el nombre de señal e identificador de instancia.
2. Invoca el endpoint de señales del `restHandlerApi` con la metadata Nova.
3. Valida el código de respuesta HTTP; lanza `XbpmException` si no es `2xx`.
4. Retorna el cuerpo de la respuesta como `String`.

---

##### Método `persistInternalTask`

Persiste una tarea interna en el almacén MongoDB de xBPM. Corresponde al método referenciado como `saveContinueTask` / `persistTaskInOtherProduct` en el inventario de ausencias.

| Nombre | Tipo | Descripción |
| :---: | :---: | ----- |
| **objectJson** | `ColeccionMongo` | Objeto que representa la tarea interna a persistir, con todos sus atributos BPM |

Retorna: `ColeccionMongo` — objeto persistido devuelto por xBPM, posiblemente enriquecido con un identificador generado.

Lanza: `XbpmException` — si la operación de persistencia falla en el motor.

Algoritmo:
1. Serializa `objectJson` a JSON mediante `JsonUtils.convertToJson`.
2. Invoca el endpoint de persistencia de tareas internas del `restHandlerApi`.
3. Valida el código de respuesta HTTP.
4. Deserializa la respuesta a `ColeccionMongo` y la retorna.

---

##### Método `getAllInstances`

Recupera todas las instancias de proceso activas del motor xBPM accesibles para el usuario en sesión. Corresponde al método referenciado como `searchInstances` en el inventario de ausencias.

Retorna: `ColeccionMongo[]` — array de instancias de proceso; puede estar vacío si no existen instancias activas.

Lanza: `XbpmException` — si la llamada al motor falla.

Algoritmo:
1. Invoca el endpoint de listado de instancias del `restHandlerApi` con la metadata Nova.
2. Valida el código HTTP de respuesta.
3. Deserializa la respuesta JSON a `ColeccionMongo[]` y la retorna.

---

##### Método `getAdminAllInstances`

Variante administrativa de `getAllInstances` que recupera **todas** las instancias del motor sin filtrar por usuario, requiriendo privilegios de administrador. Constituye la segunda implementación referenciada como `createNewInstance` en el inventario de ausencias (dado que no existe un método con ese nombre literal en el código fuente proporcionado).

Retorna: `ColeccionMongo[]` — array completo de instancias de proceso visibles con privilegios de administrador.

Lanza: `XbpmException` — si la llamada al motor falla o el usuario no tiene permisos suficientes.

Algoritmo:
1. Invoca el endpoint administrativo de listado de instancias del `restHandlerApi`.
2. Valida el código HTTP de respuesta; lanza `XbpmException` ante cualquier error.
3. Deserializa y retorna el array de `ColeccionMongo`.