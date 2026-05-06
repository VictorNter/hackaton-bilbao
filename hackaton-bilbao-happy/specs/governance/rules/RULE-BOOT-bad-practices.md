---
id: RULE-BOOT-bad-practices
type: governance
layer: rule
title: Malas prácticas prohibidas en microservicios wgtb
status: active
confidence: low
version: 0.1.0
owner: pending
tags:
  - quality
  - best-practices
  - microservices
dependencies:
  - id: ARCH-BOOT-001
    type: constrained-by
  - id: RULE-BOOT-dir-structure
    type: constrained-by
generated-by: kdd-studio
generated-at: '2026-05-06T20:53:47.402Z'
source: (creación de specs)
---

# Malas prácticas prohibidas en microservicios wgtb

## Purpose
Establece los antipatrones prohibidos en el desarrollo de microservicios wgtb, clasificados por severidad (grave, medio, leve), para que los equipos puedan identificarlos durante revisión de código, diseño técnico y auditorías de calidad.

## Definition
Las malas prácticas se agrupan en seis áreas funcionales. La severidad indica el impacto potencial en producción y la urgencia de corrección:

- **Grave**: compromete seguridad, disponibilidad o integridad de datos. Bloquea el merge.
- **Medio**: degrada mantenibilidad, observabilidad o resiliencia. Requiere issue creado antes del merge.
- **Leve**: reduce legibilidad o consistencia. Se corrige en la misma iteración si es posible.

---

### 1. Diseño de API / contratos

| Severidad | Antipatrón |
|-----------|-----------|
| 🔴 Grave | Romper el contrato de una API pública sin versionar (eliminar campos, cambiar tipos) sin previo aviso ni período de deprecación. |
| 🔴 Grave | Devolver códigos HTTP incorrectos de forma sistemática (p. ej. 200 en errores, 500 para validaciones de negocio). |
| 🟡 Medio | No documentar los endpoints en OpenAPI / Swagger antes de su entrega. |
| 🟡 Medio | Diseñar endpoints que mezclan responsabilidades (p. ej. un POST que crea y también consulta). |
| 🟢 Leve | Usar nombres de campos inconsistentes entre endpoints del mismo servicio (camelCase vs snake_case). |
| 🟢 Leve | No incluir paginación en endpoints que devuelven colecciones potencialmente grandes. |

---

### 2. Gestión de errores

| Severidad | Antipatrón |
|-----------|-----------|
| 🔴 Grave | Silenciar excepciones con bloques `catch` vacíos o que solo hacen `log` y continúan como si no hubiera pasado nada. |
| 🔴 Grave | Propagar stack traces completos al cliente en respuestas de error de producción. |
| 🟡 Medio | No distinguir entre errores recuperables (reintentar) y no recuperables (fallar rápido). |
| 🟡 Medio | Lanzar excepciones genéricas (`Exception`, `Error`) en lugar de tipos de error de dominio. |
| 🟢 Leve | Mensajes de error sin contexto suficiente para diagnosticar el problema (p. ej. `"Error interno"`). |
| 🟢 Leve | No incluir un `correlationId` en la respuesta de error para trazabilidad. |

---

### 3. Seguridad básica (secretos, autenticación)

| Severidad | Antipatrón |
|-----------|-----------|
| 🔴 Grave | Hardcodear credenciales, tokens o claves en el código fuente o en ficheros de configuración versionados. |
| 🔴 Grave | No validar ni sanitizar la entrada del usuario antes de usarla en queries, comandos o respuestas. |
| 🔴 Grave | Exponer endpoints autenticados sin verificación real del token (p. ej. aceptar cualquier JWT sin validar firma). |
| 🟡 Medio | Usar algoritmos de cifrado o hashing obsoletos (MD5, SHA-1, DES). |
| 🟡 Medio | Confiar en cabeceras controladas por el cliente para decisiones de autorización (p. ej. `X-User-Role`). |
| 🟢 Leve | No establecer tiempo de expiración en tokens de sesión o JWT. |
| 🟢 Leve | Devolver información de versión del framework o servidor en cabeceras de respuesta. |

---

### 4. Calidad de código (acoplamiento, duplicación, complejidad)

| Severidad | Antipatrón |
|-----------|-----------|
| 🔴 Grave | Lógica de negocio crítica sin cobertura de tests unitarios (umbral mínimo definido en `RULE-QUALITY-COVERAGE-001`). |
| 🟡 Medio | Clases o funciones con más de una responsabilidad clara (violación de SRP). |
| 🟡 Medio | Copiar y pegar bloques de código en lugar de extraer funciones o módulos compartidos. |
| 🟡 Medio | Dependencias circulares entre módulos internos del servicio. |
| 🟡 Medio | Funciones con más de 4 parámetros sin agrupar en objeto de configuración. |
| 🟢 Leve | Código comentado ("dead code") dejado en el repositorio sin propósito documentado. |
| 🟢 Leve | Nombres de variables de un solo carácter fuera de contextos de iteración trivial. |
| 🟢 Leve | Números mágicos sin constante nombrada. |

---

### 5. Observabilidad (logs, trazas)

| Severidad | Antipatrón |
|-----------|-----------|
| 🔴 Grave | No loguear eventos de negocio críticos (inicio/fin de transacciones, fallos de integración con sistemas externos). |
| 🟡 Medio | Loguear datos sensibles (PII, credenciales, tokens) en cualquier nivel. |
| 🟡 Medio | Usar `System.out.println` o equivalente en lugar del sistema de logging estructurado del servicio. |
| 🟡 Medio | No propagar el `correlationId` / `traceId` en llamadas a servicios externos. |
| 🟢 Leve | Logs sin nivel de severidad explícito (`DEBUG`, `INFO`, `WARN`, `ERROR`). |
| 🟢 Leve | Logs que no incluyen el contexto de la operación (p. ej. qué entidad se estaba procesando). |

---

### 6. Gestión de dependencias

| Severidad | Antipatrón |
|-----------|-----------|
| 🔴 Grave | Incluir dependencias con vulnerabilidades conocidas de severidad alta o crítica (CVE). |
| 🟡 Medio | No fijar versiones exactas de dependencias transitivas en servicios de producción (usar rangos `^` o `~` sin lockfile). |
| 🟡 Medio | Añadir dependencias de propósito general cuando ya existe una librería aprobada en el stack del proyecto. |
| 🟢 Leve | Dependencias declaradas en el manifiesto que ya no se usan en el código. |
| 🟢 Leve | No separar dependencias de desarrollo de las de producción en el manifiesto. |

## Acceptance Criteria
- [ ] El pipeline de CI rechaza cualquier merge que contenga credenciales hardcodeadas detectadas por análisis estático.
- [ ] El pipeline de CI rechaza cualquier merge con cobertura de tests por debajo del umbral definido en `RULE-QUALITY-COVERAGE-001`.
- [ ] Toda revisión de código verifica explícitamente los antipatrones de severidad **grave** antes de aprobar.
- [ ] Los antipatrones de severidad **medio** generan un issue de seguimiento antes de que el merge sea aprobado.
- [ ] Los antipatrones de severidad **leve** quedan registrados como comentarios en el PR y se corrigen en la misma iteración si el esfuerzo es menor de 30 minutos.

## Evidence
| Type | Reference | Date | Confidence impact |
|------|-----------|------|-------------------|
| Spec activo | ARCH-BOOT-001 | 2025-01-31 | Context |
| Spec activo | RULE-BOOT-dir-structure | 2025-01-31 | Context |
| Conocimiento experto | OWASP Top 10, SANS CWE Top 25 | 2025-01-31 | Initial |

## Traceability
| Relation | Target | Description |
|----------|--------|-------------|
| constrained-by | ARCH-BOOT-001 | Arquitectura base del microservicio que estas reglas protegen |
| constrained-by | RULE-BOOT-dir-structure | Estructura canónica con la que estas prácticas deben ser consistentes |
