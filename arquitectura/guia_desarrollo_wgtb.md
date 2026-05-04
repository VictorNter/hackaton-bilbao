# Guía de Desarrollo y Convenciones en WGTB

## Tabla de Contenidos
1. [Convenciones de Nomenclatura](#convenciones-de-nomenclatura)
2. [Estructura de Directorios - Best Practices](#estructura-de-directorios---best-practices)
3. [Patrones Comunes de Desarrollo](#patrones-comunes-de-desarrollo)
4. [Flujo de Trabajo Típico](#flujo-de-trabajo-típico)
5. [Testing y Validación](#testing-y-validación)
6. [Consideraciones de Seguridad](#consideraciones-de-seguridad)
7. [Troubleshooting Común](#troubleshooting-común)

---

## Convenciones de Nomenclatura

### Backend Java - Packages

```
com.bbva.wgtb.wgtbbackend.
│
├─ {modulo}/                              # apibpm, apitableservices, apitemplates
│
├─ {modulo}/domain/
│   ├─ entity/                            # Entidades persistibles
│   │   ├─ {EntidadPrincipal}.java       # ej: Task.java, BusinessData.java
│   │   ├─ {Entidad}.java                # ej: Comment.java, Field.java
│   │   └─ nodatabase/
│   │       ├─ {Enum}Status.java         # ej: TaskStatus.java
│   │       ├─ {Enum}Type.java           # ej: TaskType.java
│   │       └─ {Enum}Action.java         # ej: TaskAction.java
│   │
│   └─ Regla: Las entidades NO tienen sufijo "Entity"
│
├─ {modulo}/application/
│   ├─ I{Entidad}Service.java            # Interfaz (ej: ITaskService.java)
│   └─ impl/
│       └─ {Entidad}ServiceImpl.java      # Implementación
│
│   Regla: Los servicios comienzan con "I" para interfaz
│
├─ {modulo}/infrastructure/
│   ├─ listener/
│   │   └─ Listener{Modulo}.java         # ej: ListenerApiBpm.java
│   │
│   ├─ repository/
│   │   ├─ I{Entidad}Repository.java     # Interfaz (ej: ITaskRepository.java)
│   │   ├─ impl/
│   │   │   └─ {Entidad}RepositoryImpl.java
│   │   └─ jpa/
│   │       ├─ {Entidad}RepositoryJpa.java
│   │       ├─ {Entidad}Jpa.java         # Entidad JPA
│   │       └─ mapper/
│   │           └─ {Entidad}Mapper.java  # MapStruct mapper
│   │
│   └─ mapper/
│       └─ Mapper{Dto}.java              # ej: MapperTaskDto.java
│
├─ exception/
│   ├─ GenericException.java             # Base con HttpStatus
│   ├─ EntityNotFoundException.java       # HTTP 404
│   ├─ AuthenticationException.java       # HTTP 401
│   ├─ XbpmException.java                # Errores BPM
│   └─ RdrException.java                 # Errores RDR
│
├─ xbpm/
│   ├─ ServiceApi.java                   # Cliente XBPM
│   └─ ConfigApi.java                    # Configuración
│
├─ rdr/
│   ├─ RdrService.java                   # Servicio RDR
│   ├─ ServiceRdrdictionary.java         # Llamadas diccionario
│   └─ ServiceRdrparty.java              # Llamadas party
│
└─ utils/
    ├─ mapper/
    │   ├─ AuditedDomain.java            # Base con auditoría
    │   └─ GenericDtoMapper.java         # Interface MapStruct
    └─ Constants.java                    # Constantes globales
```

### Convenciones Específicas

| Tipo | Patrón | Ejemplo | Notas |
|------|--------|---------|-------|
| **Interfaz de Servicio** | `I{Entidad}Service` | `ITaskService.java` | Comienza con "I" |
| **Implementación Servicio** | `{Entidad}ServiceImpl` | `TaskServiceImpl.java` | Sufijo "Impl" |
| **Interfaz Repository** | `I{Entidad}Repository` | `ITaskRepository.java` | Comienza con "I" |
| **Impl Repository** | `{Entidad}RepositoryImpl` | `TaskRepositoryImpl.java` | En `/impl/` |
| **Entidad JPA** | `{Entidad}Jpa` | `TaskJpa.java` | En `/jpa/` |
| **Mapper JPA** | `{Entidad}Mapper` | `TaskMapper.java` | En `/jpa/mapper/` |
| **Mapper DTO** | `Mapper{Dto}` | `MapperTaskDto.java` | En `/mapper/` |
| **Listener REST** | `Listener{Modulo}` | `ListenerApiBpm.java` | En `/listener/` |
| **Enum Status** | `{Concepto}Status` | `TaskStatus.java` | Valores finales: UPPERCASE_WITH_UNDERSCORES |
| **Enum Type** | `{Concepto}Type` | `TaskType.java` | Valores finales: UPPERCASE_WITH_UNDERSCORES |
| **Excepción Custom** | `{Concepto}Exception` | `XbpmException.java` | Extiende GenericException |

### Frontend TypeScript/Angular

```
src/app/
│
├─ core/
│   ├─ services/
│   │   └─ {caracteristica}.service.ts       # ej: user.service.ts
│   ├─ interceptors/
│   │   └─ {tipo}.interceptor.ts             # ej: error.interceptor.ts
│   ├─ guards/
│   │   └─ {tipo}.guard.ts                   # ej: auth.guard.ts
│   └─ adapters/
│       └─ {tipo}-adapters.ts                # ej: date-adapters.ts
│
├─ features/
│   └─ {feature}/
│       ├─ {feature}-routing.module.ts
│       ├─ {feature}.component.ts            # Componente principal
│       ├─ {feature}.module.ts
│       ├─ services/
│       │   └─ {feature}.service.ts
│       ├─ components/
│       │   └─ sub-{feature}.component.ts
│       └─ models/
│           └─ {feature}.model.ts
│
├─ shared/
│   ├─ components/
│   │   └─ {nombre}/
│   │       ├─ {nombre}.component.ts
│   │       ├─ {nombre}.component.html
│   │       └─ {nombre}.component.scss
│   ├─ services/
│   │   └─ {caracteristica}.service.ts
│   ├─ models/
│   │   └─ {dominio}.model.ts
│   ├─ pipes/
│   │   └─ {transformacion}.pipe.ts
│   ├─ validators/
│   │   └─ {validacion}.validator.ts
│   └─ enums/
│       └─ {concepto}.enum.ts
│
└─ utils/
    ├─ {helper}.ts                          # Funciones helper
    └─ constants/
        └─ {dominio}.constants.ts
```

**Convenciones TypeScript/Angular**:

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| **Interfaz** | `I{Concepto}` | `ITask.ts` |
| **Tipo** | `{Concepto}Type` | `TaskStatusType.ts` |
| **Enum** | `{Concepto}Enum` | `TaskStatusEnum.ts` |
| **Service** | `{Concepto}Service` | `TaskService.ts` |
| **Component** | `{Concepto}Component` | `TaskDetailComponent.ts` |
| **Pipe** | `{Transformacion}Pipe` | `StatusDisplayPipe.ts` |
| **Guard** | `{Tipo}Guard` | `AuthGuard.ts` |
| **Interceptor** | `{Tipo}Interceptor` | `ErrorInterceptor.ts` |
| **Directive** | `appHighlight` (kebab-case) | `app-highlight.directive.ts` |

---

## Estructura de Directorios - Best Practices

### Cómo Agregar Nuevo Módulo Backend

Si necesitas crear un nuevo módulo (ej: `apireporting`):

```
src/main/java/com/bbva/wgtb/wgtbbackend/apireporting/
│
├─ domain/
│   ├─ entity/
│   │   ├─ Report.java
│   │   ├─ ReportTemplate.java
│   │   └─ nodatabase/
│   │       ├─ ReportStatus.java
│   │       └─ ReportFormat.java
│   │
│   └─ valor de objeto/
│       └─ ReportMetadata.java
│
├─ application/
│   ├─ IReportService.java
│   ├─ IReportTemplateService.java
│   └─ impl/
│       ├─ ReportServiceImpl.java
│       └─ ReportTemplateServiceImpl.java
│
├─ infrastructure/
│   ├─ listener/
│   │   └─ ListenerApireporting.java
│   ├─ repository/
│   │   ├─ IReportRepository.java
│   │   ├─ IReportTemplateRepository.java
│   │   ├─ impl/
│   │   │   ├─ ReportRepositoryImpl.java
│   │   │   └─ ReportTemplateRepositoryImpl.java
│   │   └─ jpa/
│   │       ├─ ReportJpa.java
│   │       ├─ ReportRepositoryJpa.java
│   │       ├─ mapper/
│   │       │   └─ ReportMapper.java
│   │       └─ ...
│   └─ mapper/
│       ├─ MapperReportDto.java
│       └─ MapperCreateReportDto.java
│
└─ (Archivos de configuración si es necesario)
```

### Checklist para Nuevo Módulo

- [ ] Crear carpeta `{modulo}` en `src/main/java/com/bbva/wgtb/wgtbbackend/`
- [ ] Crear estructura `domain/`, `application/`, `infrastructure/`
- [ ] Crear entidades de dominio en `domain/entity/`
- [ ] Crear enums en `domain/entity/nodatabase/`
- [ ] Crear interfaces de servicio en `application/`
- [ ] Crear implementaciones en `application/impl/`
- [ ] Crear interfaces de repositorio en `infrastructure/repository/`
- [ ] Crear implementaciones de repositorio en `infrastructure/repository/impl/`
- [ ] Crear mappers JPA en `infrastructure/repository/jpa/mapper/`
- [ ] Crear entidades JPA en `infrastructure/repository/jpa/`
- [ ] Crear listener REST en `infrastructure/listener/`
- [ ] Crear mappers DTO en `infrastructure/mapper/`
- [ ] Crear excepciones custom si es necesario
- [ ] Generar DTOs con APIRestGenerator
- [ ] Agregar tests unitarios

---

## Patrones Comunes de Desarrollo

### Patrón 1: Crear Nuevo Servicio

```java
// 1. Crear interfaz (application/I{Entidad}Service.java)
public interface INewService {
    
    /**
     * Documentación de JavaDoc detallada
     * @param param descripción del parámetro
     * @return descripción del retorno
     * @throws GenericException descripción de errores
     */
    Result doSomething(Input param) throws GenericException;
}

// 2. Crear implementación (application/impl/{Entidad}ServiceImpl.java)
@Service
@RequiredArgsConstructor                    // Inyección Lombok
@Slf4j                                      // Logger
@Transactional                              // Transaccionalidad
public class NewServiceImpl implements INewService {
    
    // Inyectar repositorios necesarios
    private final INewRepository repository;
    private final IOtherRepository otherRepository;
    
    @Override
    public Result doSomething(Input param) throws GenericException {
        try {
            // 1. Validaciones de entrada
            if (param == null) {
                throw new GenericException(
                    HttpStatus.BAD_REQUEST,
                    "Param cannot be null"
                );
            }
            
            // 2. Lógica de negocio
            Entity entity = repository.findById(param.getId());
            entity.setProperty(param.getValue());
            
            // 3. Persistencia
            Entity saved = repository.save(entity);
            
            // 4. Auditoría (automática via AuditedDomain)
            
            // 5. Retornar resultado
            return new Result(saved);
            
        } catch (EntityNotFoundException e) {
            log.error("Entity not found: {}", param.getId(), e);
            throw new GenericException(HttpStatus.NOT_FOUND, e.getMessage());
        } catch (Exception e) {
            log.error("Unexpected error in doSomething", e);
            throw new GenericException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
        }
    }
}
```

### Patrón 2: Crear Nuevo Repositorio

```java
// 1. Crear interfaz (infrastructure/repository/I{Entidad}Repository.java)
public interface INewRepository {
    
    /**
     * Guarda o actualiza una entidad.
     * @param entity la entidad a guardar
     * @return entidad guardada con ID
     * @throws EntityNotFoundException si hay error de integridad
     */
    Entity save(Entity entity) throws EntityNotFoundException;
    
    /**
     * Obtiene una entidad por ID.
     * @param id identificador único
     * @return entidad encontrada
     * @throws EntityNotFoundException si no existe
     */
    Entity findById(Long id) throws EntityNotFoundException;
    
    /**
     * Obtiene todas las entidades.
     * @return lista completa
     */
    List<Entity> findAll();
    
    /**
     * Elimina una entidad por ID.
     * @param id identificador único
     */
    void delete(Long id);
}

// 2. Crear implementación (infrastructure/repository/impl/{Entidad}RepositoryImpl.java)
@Repository
@RequiredArgsConstructor
public class NewRepositoryImpl implements INewRepository {
    
    private final NewRepositoryJpa jpaRepository;
    private final NewMapper mapper;  // MapStruct
    
    @Override
    public Entity save(Entity entity) throws EntityNotFoundException {
        try {
            // 1. Mapear dominio → JPA
            NewJpa jpa = mapper.toEntity(entity);
            
            // 2. Persistir
            NewJpa savedJpa = jpaRepository.save(jpa);
            
            // 3. Mapear JPA → dominio
            return mapper.toModel(savedJpa);
            
        } catch (DataIntegrityViolationException e) {
            log.error("Data integrity error", e);
            throw new EntityNotFoundException("Entity save failed");
        }
    }
    
    @Override
    public Entity findById(Long id) throws EntityNotFoundException {
        NewJpa jpa = jpaRepository.findById(id)
            .orElseThrow(() -> {
                log.warn("Entity not found: {}", id);
                return new EntityNotFoundException("Entity not found");
            });
        return mapper.toModel(jpa);
    }
    
    @Override
    public List<Entity> findAll() {
        return jpaRepository.findAll()
            .stream()
            .map(mapper::toModel)
            .collect(Collectors.toList());
    }
    
    @Override
    public void delete(Long id) {
        jpaRepository.deleteById(id);
    }
}

// 3. Crear Mapper (infrastructure/repository/jpa/mapper/NewMapper.java)
@Mapper(componentModel = "spring")
public interface NewMapper {
    
    @Mapping(target = "id", source = "entityId")
    NewJpa toEntity(Entity domain);
    
    @Mapping(target = "entityId", source = "id")
    Entity toModel(NewJpa jpa);
}

// 4. Crear Entidad JPA (infrastructure/repository/jpa/NewJpa.java)
@Entity
@Table(name = "new_entities")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class NewJpa {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false)
    private String name;
    
    @Column
    private LocalDateTime createdDate;
    
    // Relaciones JPA si es necesario
    @ManyToOne
    @JoinColumn(name = "parent_id")
    private ParentJpa parent;
}

// 5. Crear Repository JPA (infrastructure/repository/jpa/NewRepositoryJpa.java)
@Repository
public interface NewRepositoryJpa extends JpaRepository<NewJpa, Long> {
    
    // Métodos personalizados si es necesario
    Optional<NewJpa> findByName(String name);
}
```

### Patrón 3: Manejo de Errores

```java
// En Servicio
try {
    // Operación que puede fallar
    Entity entity = repository.findById(id);
    
} catch (EntityNotFoundException e) {
    // HTTP 404 - Recurso no existe
    log.warn("Resource not found: {}", id);
    throw new GenericException(HttpStatus.NOT_FOUND, "Resource not found");
    
} catch (DataIntegrityViolationException e) {
    // HTTP 400 - Datos inválidos
    log.error("Data integrity violation", e);
    throw new GenericException(HttpStatus.BAD_REQUEST, "Invalid data");
    
} catch (Exception e) {
    // HTTP 500 - Error interno
    log.error("Unexpected error", e);
    throw new GenericException(HttpStatus.INTERNAL_SERVER_ERROR, "Internal error");
}

// En Listener REST
@Override
public ResponseEntity<?> getEntity(Long id) throws GetEntityException404 {
    try {
        Entity entity = service.getEntity(id);
        return ResponseEntity.ok(mapperEntityDto.map(entity));
        
    } catch (EntityNotFoundException e) {
        throw new GetEntityException404(e.getMessage());  // HTTP 404
        
    } catch (GenericException e) {
        // Mapear según código HTTP
        return ResponseEntity
            .status(e.getCode())
            .body(GenericApiErrorBuilder.build(e));
    }
}
```

### Patrón 4: Mapeo DTO ↔ Entidad

```java
// DTOs (generados por APIRestGenerator - NO editar manualmente)
public class CreateTaskDto {
    private String taskName;
    private String description;
    // Getters/Setters generados
}

public class TaskDto {
    private Long taskId;
    private String taskName;
    private String description;
    private List<CommentDto> comments;
    // Getters/Setters generados
}

// Mapper REST (infrastructure/mapper/MapperTaskDto.java)
@Mapper(
    componentModel = "spring",
    uses = {
        MapperCommentDto.class,
        DateMapper.class
    })
public interface MapperTaskDto extends GenericDtoMapper<Task, TaskDto> {
    
    // Mappings automáticos por convención
    // Task.taskId ↔ TaskDto.taskId
    // Task.comments ↔ TaskDto.comments (usa MapperCommentDto)
}

// Mapper para DTO de creación
@Mapper(componentModel = "spring")
public interface MapperCreateTaskDto extends GenericDtoMapper<Task, CreateTaskDto> {
    
    @Mapping(target = "taskId", ignore = true)  // Se genera en backend
    @Mapping(target = "status", constant = "NOT_CREATED")
    Task toModel(CreateTaskDto dto);
}
```

---

## Flujo de Trabajo Típico

### Trabajar en Desarrollo

**Escenario**: Agregar nuevo campo a una tarea BPM

#### 1. Actualizar Entidad de Dominio

```java
// domain/entity/Task.java
@Getter
@Setter
public class Task extends AuditedDomain {
    // ... campos existentes ...
    
    /** Nuevo campo para prioridad */
    private Integer priority;
    
    // Getter/Setter automático con Lombok
}
```

#### 2. Actualizar Entidad JPA

```java
// infrastructure/repository/jpa/TaskJpa.java
@Entity
@Table(name = "task")
public class TaskJpa {
    // ... campos existentes ...
    
    @Column
    private Integer priority;  // Nuevo campo
}
```

#### 3. Agregar Migración de Base de Datos

```sql
-- src/main/resources/db/migration/V{VERSION}__Add_priority_to_task.sql
ALTER TABLE task ADD COLUMN priority INT DEFAULT 0;
CREATE INDEX idx_task_priority ON task(priority);
```

#### 4. Actualizar Mapper JPA

```java
// infrastructure/repository/jpa/mapper/TaskMapper.java
@Mapper(componentModel = "spring")
public interface TaskMapper {
    
    @Mapping(target = "priority", source = "priority")
    TaskJpa toEntity(Task domain);
    
    @Mapping(target = "priority", source = "priority")
    Task toModel(TaskJpa jpa);
}
```

#### 5. Actualizar DTO (si aplica)

Generar con APIRestGenerator:
```yaml
# en especificación OpenAPI
Task:
  properties:
    priority:
      type: integer
      description: "Prioridad de la tarea"
```

#### 6. Pruebas Unitarias

```java
@RunWith(SpringRunner.class)
@SpringBootTest
public class TaskRepositoryTest {
    
    @Autowired
    private TaskRepository repository;
    
    @Test
    public void testSaveTaskWithPriority() throws Exception {
        // Arrange
        Task task = new Task();
        task.setPriority(5);
        
        // Act
        Task saved = repository.save(task);
        
        // Assert
        assertNotNull(saved.getTaskId());
        assertEquals(5, saved.getPriority().intValue());
    }
}
```

#### 7. Deploy a DEV/TEST

```bash
# Compilar y ejecutar tests
mvn clean test

# Empaquetar
mvn clean package

# Deploy a DEV
# (Proceso específico del proyecto)
```

---

## Testing y Validación

### Estructura de Tests

```
src/test/java/com/bbva/wgtb/wgtbbackend/
│
├─ {modulo}/
│   ├─ application/
│   │   └─ {Entidad}ServiceTest.java
│   ├─ infrastructure/
│   │   ├─ repository/
│   │   │   └─ {Entidad}RepositoryTest.java
│   │   └─ listener/
│   │       └─ Listener{Modulo}Test.java
│   └─ domain/
│       └─ entity/
│           └─ {Entidad}Test.java
│
└─ {modulo}/resources/
    └─ test_data.json
```

### Test Unitario - Servicio

```java
@RunWith(SpringRunner.class)
@SpringBootTest
public class BusinessDataServiceTest {
    
    @Autowired
    private IBusinessDataService service;
    
    @MockBean
    private IBusinessDataRepository repository;
    
    @Before
    public void setUp() {
        // Inicialización de mocks
    }
    
    @Test
    public void testCreateBusinessData_Success() throws Exception {
        // Arrange
        BusinessData input = new BusinessData();
        input.setBusinessId("OPP-001");
        
        BusinessData expected = new BusinessData();
        expected.setBusinessId("OPP-001");
        expected.setStatus(BusinessDataStatus.IN_PROGRESS);
        
        Mockito.when(repository.saveBusinessData(input))
            .thenReturn(expected);
        
        // Act
        BusinessData result = service.saveBusinessData(input);
        
        // Assert
        assertNotNull(result);
        assertEquals("OPP-001", result.getBusinessId());
        assertEquals(BusinessDataStatus.IN_PROGRESS, result.getStatus());
        
        // Verify
        Mockito.verify(repository).saveBusinessData(input);
    }
    
    @Test
    public void testCreateBusinessData_NullInput() throws Exception {
        // Arrange - N/A
        
        // Act & Assert
        assertThrows(GenericException.class, 
            () -> service.saveBusinessData(null));
    }
}
```

### Test de Integración

```java
@RunWith(SpringRunner.class)
@SpringBootTest
@Transactional
public class BusinessDataRepositoryIntegrationTest {
    
    @Autowired
    private IBusinessDataRepository repository;
    
    @Autowired
    private TestEntityManager em;
    
    @Test
    public void testSaveAndFetch() throws Exception {
        // Arrange
        BusinessData bd = new BusinessData();
        bd.setBusinessId("OPP-TEST");
        bd.setStatus(BusinessDataStatus.IN_PROGRESS);
        
        // Act
        String savedId = repository.saveBusinessData(bd);
        em.flush();
        em.clear();
        
        BusinessData fetched = repository.findById(savedId);
        
        // Assert
        assertNotNull(fetched);
        assertEquals("OPP-TEST", fetched.getBusinessId());
        assertEquals(BusinessDataStatus.IN_PROGRESS, fetched.getStatus());
    }
}
```

---

## Consideraciones de Seguridad

### 1. Autenticación y Autorización

```java
// El contexto de seguridad NOVA se propaga automáticamente
public class AuditedDomain {
    
    public AuditedDomain() {
        this.user = NovaSecurityContext.getAuthentication()
            .getUser();  // ← Obtiene usuario del contexto seguro
    }
}
```

**Verificar**: Que `NovaSecurityContext` esté siempre disponible en requests

### 2. Validación de Entrada

```java
@Service
public class TaskServiceImpl {
    
    public Task updateTask(Task task) throws GenericException {
        // Validar campos obligatorios
        if (task == null || task.getTaskId() == null) {
            throw new GenericException(
                HttpStatus.BAD_REQUEST,
                "Task or taskId cannot be null"
            );
        }
        
        // Validar enums
        if (task.getStatus() == null) {
            throw new GenericException(
                HttpStatus.BAD_REQUEST,
                "Status is required"
            );
        }
        
        // Validar transiciones de estado
        if (!isValidTransition(task.getStatus())) {
            throw new GenericException(
                HttpStatus.BAD_REQUEST,
                "Invalid status transition"
            );
        }
        
        // Proceder con seguridad
        return repository.save(task);
    }
}
```

### 3. Inyección SQL Preventiva

- **Usar PreparedStatements** (Spring Data JPA lo hace automáticamente)
- **NO concatenar strings** en queries
- **Usar @Query con nombrados**:

```java
@Repository
public interface TaskRepositoryJpa extends JpaRepository<TaskJpa, Long> {
    
    // ✓ BIEN: Parámetro nombrado
    @Query("SELECT t FROM TaskJpa t WHERE t.bpmTaskId = :bpmId")
    Optional<TaskJpa> findByBpmId(@Param("bpmId") String bpmId);
    
    // ✗ MAL: Concatenación (NO hacer)
    // String query = "SELECT * FROM task WHERE bpmTaskId = '" + id + "'";
}
```

### 4. Manejo de Datos Sensibles

```java
// NO loguear datos sensibles
log.error("Password: {}", password);  // ✗ MAL

// Loguear de forma segura
log.error("Authentication failed for user: {}", username);  // ✓ BIEN

// En excepciones
throw new GenericException(
    HttpStatus.UNAUTHORIZED,
    "Invalid credentials"  // No revelar detalles
);
```

---

## Troubleshooting Común

### Problema 1: "EntityNotFoundException: Entity not found"

**Causa**: Intentando acceder a una entidad que no existe

**Solución**:

```java
// Agregar logs antes de la búsqueda
log.debug("Searching for task with ID: {}", taskId);

try {
    Task task = repository.findById(taskId);
} catch (EntityNotFoundException e) {
    // Loguear contexto
    log.error("Task {} not found. Available tasks: {}", 
        taskId, getAllTaskIds());
    throw e;
}

// Verificar base de datos
SELECT * FROM task WHERE task_id = ?;
```

### Problema 2: "LazyInitializationException"

**Causa**: Accediendo a colecciones no inicializadas fuera de la transacción

**Solución**:

```java
// ✗ MAL
@Override
public BusinessData findById(String id) {
    return repository.findById(id);  // Sin transacción
}
// Luego acceder a tasks causa: LazyInitializationException

// ✓ BIEN
@Override
@Transactional(readOnly = true)
public BusinessData findById(String id) {
    BusinessData bd = repository.findById(id);
    // Cargar colecciones dentro de la transacción
    bd.getTasks().size();
    return bd;
}

// O usar @Fetch(EAGER) en la entidad
@ManyToOne(fetch = FetchType.EAGER)
private List<Task> tasks;
```

### Problema 3: "DataIntegrityViolationException"

**Causa**: Violación de restricciones de BD (unique, FK, etc.)

**Solución**:

```java
try {
    repository.save(entity);
} catch (DataIntegrityViolationException e) {
    log.error("Constraint violation", e);
    
    // Identificar tipo de violación
    if (e.getMessage().contains("unique")) {
        throw new GenericException(
            HttpStatus.CONFLICT,
            "Entity already exists"
        );
    }
    if (e.getMessage().contains("foreign key")) {
        throw new GenericException(
            HttpStatus.BAD_REQUEST,
            "Invalid reference"
        );
    }
    
    throw new GenericException(
        HttpStatus.INTERNAL_SERVER_ERROR,
        "Database error"
    );
}
```

### Problema 4: "Mapper returns null"

**Causa**: MapStruct mapper no tiene mapping para algunos campos

**Solución**:

```java
// Verificar que mapper está correctamente anotado
@Mapper(componentModel = "spring")  // ← Importante
public interface TaskMapper {
    
    // Especificar mappings explícitos si es necesario
    @Mapping(target = "taskId", source = "id")
    @Mapping(target = "status", source = "status")
    Task toModel(TaskJpa jpa);
}

// En test, verificar que bean está siendo inyectado
@Autowired
private TaskMapper mapper;  // ← Debe estar disponible

@Test
public void testMapper() {
    TaskJpa jpa = new TaskJpa();
    jpa.setId(1L);
    jpa.setStatus("ACTIVE");
    
    Task task = mapper.toModel(jpa);
    
    assertNotNull(task);  // Si es null, mapper no fue inyectado
    assertEquals(1L, task.getTaskId().longValue());
}
```

### Problema 5: "HTTP 404 cuando el recurso existe"

**Causa**: Listener no está mapeando correctamente el camino

**Solución**:

```java
// Verificar anotación @Path en Listener
@Service
@RequiredArgsConstructor
public class ListenerApiBpm implements IRestListenerApibpm {
    
    // La interfaz IRestListenerApibpm tiene @Path
    @Override
    @GET
    @Path("/tasks/{id}")  // ← Debe coincidir con petición
    public TaskDto getTask(@PathParam("id") String id) 
        throws GetTaskException404 {
        // ...
    }
}

// Verificar URL completa
// Esperado: /api/bpm/tasks/{id}
// Actual: http://localhost:8080/SHIVA/api/bpm/tasks/123
```

---

## Conclusión

El proyecto WGTB mantiene convenciones claras y patrones consistentes que facilitan:

1. **Onboarding**: Nuevos desarrolladores entienden la estructura rápidamente
2. **Mantenibilidad**: Código predecible y consistente
3. **Escalabilidad**: Fácil agregar nuevas características
4. **Testabilidad**: Arquitectura bien separada favorece tests

**Recuerda**: Si algo no está aquí, consulta el código existente como referencia de estilo.


