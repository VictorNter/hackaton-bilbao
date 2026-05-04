# Documentación de Arquitectura - Proyecto WGTB

**Fecha de Generación**: 2026-04-20  
**Versión**: 1.0  
**Basado en Análisis de Código Fuente Actual**

---

## 📚 Índice de Documentos

Esta carpeta contiene documentación completa sobre la arquitectura, estructura e integración del proyecto WGTB.

### 1. **arquitectura_hexagonal_wgtb.md** ⭐ **COMIENZA AQUÍ**

📖 **Descripción**: Explicación detallada de cómo está implementada la Arquitectura Hexagonal en WGTB.

**Secciones**:
- Descripción general de la arquitectura
- Estructura de capas (Domain, Application, Infrastructure)
- Módulos principales (apibpm, apitableservices, apitemplates)
- Flujos de comunicación entre capas
- Patrones de implementación (inyección, transacciones, mapeos)
- Adaptadores y puertos (entrada/salida)
- Gestión de errores y excepciones

**Público Objetivo**: Desarrolladores nuevos, arquitectos, líderes técnicos

**Tiempo de Lectura**: 20-30 minutos

---

### 2. **integraciones_modulos_wgtb.md** 🔗

📖 **Descripción**: Cómo los tres módulos (apibpm, apitable, apitemplates) se comunican entre sí y con sistemas externos.

**Secciones**:
- Visión general de integraciones
- Flujos de integración detallados (creación de oportunidades, actualización de tareas, búsqueda en tablas)
- Dependencias entre módulos (matriz de dependencias)
- Interfaz Frontend-Backend
- Casos de uso principales

**Público Objetivo**: Desarrolladores que necesitan entender flujos complejos, líderes de módulos

**Tiempo de Lectura**: 25-35 minutos

---

### 3. **guia_desarrollo_wgtb.md** 🛠️

📖 **Descripción**: Guía práctica para desarrolladores que trabajan en el proyecto WGTB.

**Secciones**:
- Convenciones de nomenclatura (Java y TypeScript)
- Estructura de directorios best practices
- Patrones comunes de desarrollo
- Flujo de trabajo típico (paso a paso)
- Testing y validación
- Consideraciones de seguridad
- Troubleshooting común

**Público Objetivo**: Desarrolladores, líderes técnicos, QA

**Tiempo de Lectura**: 30-40 minutos

---

## 🎯 Cómo Usar Esta Documentación

### Para Diferentes Roles

#### 👨‍💼 **Gerente Técnico / Líder Arquitectura**
1. Lee: **arquitectura_hexagonal_wgtb.md** - Secciones "Descripción General" y "Módulos Principales"
2. Lee: **integraciones_modulos_wgtb.md** - Sección "Visión General"
3. Consulta: **guia_desarrollo_wgtb.md** - Sección "Convenciones"

#### 👨‍💻 **Desarrollador Nuevo**
1. Lee: **arquitectura_hexagonal_wgtb.md** - Completo
2. Lee: **guia_desarrollo_wgtb.md** - Completo
3. Lee: **integraciones_modulos_wgtb.md** - Según necesidad

#### 🔧 **Desarrollador Experimentado**
1. Lee: **guia_desarrollo_wgtb.md** - Secciones "Convenciones" y "Patrones Comunes"
2. Consulta: **arquitectura_hexagonal_wgtb.md** - Según necesidad
3. Consulta: **integraciones_modulos_wgtb.md** - Para flujos específicos

#### 🧪 **QA / Test Automation**
1. Lee: **integraciones_modulos_wgtb.md** - Sección "Casos de Uso"
2. Lee: **guia_desarrollo_wgtb.md** - Sección "Testing"
3. Consulta: **arquitectura_hexagonal_wgtb.md** - Para entender flujos

---

## 📋 Contenido Resumido

### arquitectura_hexagonal_wgtb.md

```
├─ Descripción General
│  └─ Patrón hexagonal con 3 módulos independientes
│
├─ Estructura de Capas
│  ├─ Domain (Entidades + Enums + Value Objects)
│  ├─ Application (Servicios + Interfaces)
│  └─ Infrastructure (REST Listeners + Repositories + Mappers)
│
├─ Módulos Principales
│  ├─ apibpm (Gestión BPM)
│  ├─ apitableservices (Tablas maestro)
│  └─ apitemplates (Plantillas formularios)
│
├─ Flujos de Comunicación
│  ├─ Obtener Tarea
│  ├─ Crear Oportunidad
│  └─ Actualizar Estado
│
├─ Patrones de Implementación
│  ├─ Inyección de Dependencias
│  ├─ Transacciones
│  ├─ Mapeo DTOs
│  ├─ Manejo de Excepciones
│  └─ Auditoría
│
├─ Adaptadores y Puertos
│  ├─ Entrada (REST Listeners)
│  └─ Salida (Repositorios, XBPM, RDR)
│
└─ Gestión de Errores
   ├─ Jerarquía de Excepciones
   ├─ Propagación de Errores
   └─ Respuestas Estandarizadas
```

### integraciones_modulos_wgtb.md

```
├─ Visión General
│  └─ Diagrama arquitectura general
│
├─ Flujos de Integración
│  ├─ Crear Oportunidad (multipasos)
│  ├─ Actualizar Estado (sincronización BPM-DB)
│  ├─ Consultar Tabla Maestro (RDR)
│  └─ Cargar Plantillas
│
├─ Dependencias entre Módulos
│  ├─ apibpm: Servicios, Repositorios, Externos
│  ├─ apitableservices: Tablas, Valores
│  ├─ apitemplates: Plantillas, Secciones
│  └─ Matriz de Dependencias
│
├─ Interfaz Frontend-Backend
│  ├─ Arquitectura Frontend (modules, features, shared)
│  ├─ Flujo de Datos (Cliente → Backend → BD)
│  └─ Patrones HTTP
│
└─ Casos de Uso Principales
   ├─ Caso 1: Crear Oportunidad
   ├─ Caso 2: Completar Tarea
   ├─ Caso 3: Búsqueda en Tabla
   └─ Caso 4: Renderizar Formulario
```

### guia_desarrollo_wgtb.md

```
├─ Convenciones de Nomenclatura
│  ├─ Packages Java
│  ├─ Interfaces (I{Entidad}Service)
│  ├─ Implementaciones ({Entidad}ServiceImpl)
│  ├─ Componentes TypeScript
│  └─ Tabla de referencia rápida
│
├─ Estructura de Directorios
│  └─ Cómo agregar nuevo módulo (checklist)
│
├─ Patrones Comunes
│  ├─ Crear Servicio (con ejemplo completo)
│  ├─ Crear Repositorio (con ejemplo completo)
│  └─ Manejo de Errores (con ejemplo completo)
│
├─ Flujo de Trabajo
│  └─ Ejemplo paso a paso: Agregar nuevo campo
│
├─ Testing
│  ├─ Estructura de tests
│  ├─ Test unitario (con mocks)
│  └─ Test de integración
│
├─ Seguridad
│  ├─ Autenticación/Autorización
│  ├─ Validación de entrada
│  ├─ Prevención SQL Injection
│  └─ Datos sensibles
│
└─ Troubleshooting
   ├─ EntityNotFoundException
   ├─ LazyInitializationException
   ├─ DataIntegrityViolationException
   ├─ Mapper returns null
   └─ HTTP 404 inesperado
```

---

## 🔍 Búsqueda Rápida

### "¿Cómo...?"

| Pregunta | Documento | Sección |
|----------|-----------|---------|
| ¿Cómo funciona la Arquitectura Hexagonal? | `arquitectura_hexagonal_wgtb.md` | "Estructura de Capas" |
| ¿Cómo se comunican los módulos? | `integraciones_modulos_wgtb.md` | "Flujos de Integración" |
| ¿Cómo crear un servicio nuevo? | `guia_desarrollo_wgtb.md` | "Patrón 1: Crear Servicio" |
| ¿Cómo crear un repositorio nuevo? | `guia_desarrollo_wgtb.md` | "Patrón 2: Crear Repositorio" |
| ¿Cómo manejar errores? | `guia_desarrollo_wgtb.md` | "Patrón 3: Manejo de Errores" |
| ¿Cómo agregar un nuevo módulo? | `guia_desarrollo_wgtb.md` | "Estructura de Directorios" |
| ¿Qué convenciones seguir? | `guia_desarrollo_wgtb.md` | "Convenciones de Nomenclatura" |
| ¿Cómo escribir tests? | `guia_desarrollo_wgtb.md` | "Testing y Validación" |
| ¿Cómo resolver errores comunes? | `guia_desarrollo_wgtb.md` | "Troubleshooting Común" |

---

## 📦 Contenido Técnico por Aspecto

### Capa de Dominio
- 📄 `arquitectura_hexagonal_wgtb.md` - "Capa de Dominio"
- 📄 `guia_desarrollo_wgtb.md` - "Patrón 1: Crear Servicio"

### Capa de Aplicación
- 📄 `arquitectura_hexagonal_wgtb.md` - "Capa de Aplicación"
- 📄 `guia_desarrollo_wgtb.md` - "Patrón 2: Crear Repositorio"

### Capa de Infraestructura
- 📄 `arquitectura_hexagonal_wgtb.md` - "Capa de Infraestructura"
- 📄 `integraciones_modulos_wgtb.md` - "Interfaz Frontend-Backend"

### Persistencia y BD
- 📄 `guia_desarrollo_wgtb.md` - "Patrón 2: Crear Repositorio"
- 📄 `guia_desarrollo_wgtb.md` - "Flujo de Trabajo Típico"

### Frontend Angular
- 📄 `integraciones_modulos_wgtb.md` - "Interfaz Frontend-Backend"
- 📄 `integraciones_modulos_wgtb.md` - "Casos de Uso"

### Errores y Seguridad
- 📄 `arquitectura_hexagonal_wgtb.md` - "Gestión de Errores"
- 📄 `guia_desarrollo_wgtb.md` - "Consideraciones de Seguridad"
- 📄 `guia_desarrollo_wgtb.md` - "Troubleshooting Común"

---

## 💡 Conceptos Clave

### Términos Importantes

| Término | Explicación | Ver |
|---------|-------------|-----|
| **Hexagonal Architecture** | Patrón que aísla dominio de infraestructura | `arquitectura_hexagonal_wgtb.md` |
| **Puerto (Port)** | Interface que define contrato de entrada/salida | `arquitectura_hexagonal_wgtb.md` - "Adaptadores" |
| **Adaptador (Adapter)** | Implementación que conecta puertos con sistemas externos | `arquitectura_hexagonal_wgtb.md` - "Adaptadores" |
| **DTO (Data Transfer Object)** | Objeto para transferencia HTTP, separado de dominio | `guia_desarrollo_wgtb.md` - "Patrón 4" |
| **Mapper** | Convierte DTO ↔ Entidad usando MapStruct | `arquitectura_hexagonal_wgtb.md` - "Mappers" |
| **Repository** | Adaptador de persistencia (patrón Data Access) | `guia_desarrollo_wgtb.md` - "Patrón 2" |
| **Entidad de Dominio** | Objeto puro de negocio sin dependencias externas | `arquitectura_hexagonal_wgtb.md` - "Capa de Dominio" |
| **AuditedDomain** | Base class que proporciona auditoría automática | `arquitectura_hexagonal_wgtb.md` - "Modelo de Auditoría" |

---

## 📚 Referencias Externas

### Libros Recomendados
- "Implementing Domain-Driven Design" - Vaughn Vernon
- "Clean Architecture" - Robert C. Martin
- "Domain-Driven Design" - Eric Evans

### Patrones
- Hexagonal Architecture: https://en.wikipedia.org/wiki/Hexagonal_architecture
- Spring Data: https://spring.io/projects/spring-data
- MapStruct: https://mapstruct.org/
- JPA/Hibernate: https://hibernate.org/orm/

---

## 🔄 Evolución de la Documentación

Esta documentación fue generada analizando el código fuente actual del proyecto WGTB.

### Cómo Mantenerla Actualizada

1. **Cuando agregas un nuevo módulo**: Actualiza `integraciones_modulos_wgtb.md` y `guia_desarrollo_wgtb.md`
2. **Cuando cambias convenciones**: Actualiza `guia_desarrollo_wgtb.md`
3. **Cuando cambias arquitectura**: Actualiza `arquitectura_hexagonal_wgtb.md`
4. **Cuando agregas patrón importante**: Actualiza `guia_desarrollo_wgtb.md`

---

## ❓ Preguntas Frecuentes

**P: ¿Por qué hay 3 módulos separados?**  
R: Para separación de responsabilidades y escalabilidad independiente. Ver `integraciones_modulos_wgtb.md` - "Visión General".

**P: ¿Dónde va el nuevo código?**  
R: Depends - Domain/Application/Infrastructure. Ver `arquitectura_hexagonal_wgtb.md` - "Estructura de Capas".

**P: ¿Cuándo crear un nuevo módulo?**  
R: Cuando tienes dominio completamente separado. Ver `guia_desarrollo_wgtb.md` - "Estructura de Directorios".

**P: ¿Cómo debuggear errores?**  
R: Ver `guia_desarrollo_wgtb.md` - "Troubleshooting Común".

---

## 📞 Soporte

Para preguntas sobre esta documentación:
1. Consulta los archivos .md relevantes
2. Busca en "¿Cómo...?" table anterior
3. Revisa "Troubleshooting Común"

---

**Última actualización**: 2026-04-20  
**Versión de análisis**: Basado en código fuente actual de WGTB


