---
id: DOM-HACK-001
type: spec
layer: domain
domain: AI Code Review
subdomain: Actors and Entities
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
  - id: ADR-001
    relation: constrained-by
  - id: ADR-002
    relation: constrained-by
  - id: ADR-003
    relation: constrained-by
  - id: ARCH-HACK-001
    relation: uses-data-from
tags:
  - domain
  - actores
  - entidades
  - quality-gate
  - override
  - human-in-the-loop
---

# DOM-HACK-001 — Actores y Entidades del Dominio HackIAdos

## Intent

Define los actores que participan en el sistema HackIAdos, las entidades que manipulan, y las reglas de negocio que gobiernan su comportamiento. Es el vocabulario compartido del dominio: cualquier spec de feature, rulebook o skill del agente debe ser coherente con las definiciones aquí establecidas.

---

## Definition

### Contexto

HackIAdos es un agente de revisión de código que actúa automáticamente sobre Pull Requests en GitHub Enterprise (BBVA interno). Su ciclo de vida fundamental es:

```
PR abierta/actualizada
        ↓
   Agente analiza diff
        ↓
   Aplica Rulebook(s)
        ↓
   Emite Quality Gate State (🔴 / 🟡 / 🟢)
        ↓
   Posta comentario en PR + actualiza Check Run
        ↓
   Notifica canal Google Chat del proyecto (si 🔴 o 🟡)
```

El principio rector es **"el agente propone y bloquea técnicamente; el humano corrige o autoriza"**. El agente actúa de forma autónoma sin aprobación humana previa, pero el merge está técnicamente controlado por el Quality Gate. Solo un actor con permisos explícitos puede desbloquear una PR en estado 🔴 de forma excepcional.

---

### Actores

#### ACT-001 — PR Author

**Quién es:** el desarrollador que abre o actualiza una Pull Request en un repositorio objetivo.

**Responsabilidades en el dominio:**
- Crea la PR que dispara el análisis del agente
- Recibe el comentario de resultado en su PR
- Corrige el código para resolver las violaciones 🔴 bloqueantes
- Puede optar por corregir o ignorar los avisos 🟡 (no bloquean)

**Interacción con el sistema:** pasiva — no invoca al agente directamente. El trigger es el evento de GitHub.

---

#### ACT-002 — Tech Lead / Reviewer

**Quién es:** el revisor técnico del equipo que hace code review de la PR además del agente.

**Responsabilidades en el dominio:**
- Revisa el análisis del agente como parte del proceso de revisión humana
- Puede ser designado como **Authorized Approver** (ver ACT-004), lo que le da permisos adicionales de desbloqueo
- Puede proporcionar feedback al **Rulebook Owner** si detecta que una regla genera falsos positivos recurrentes

**Relación con otros actores:** complementa al agente — el agente revisa cumplimiento de reglas, el Tech Lead revisa intención y diseño.

---

#### ACT-003 — Rulebook Owner

**Quién es:** Lourdes Pozo (rol formalizado en el equipo HackIAdos).

**Responsabilidades en el dominio:**
- Define y mantiene las reglas dentro de los Rulebooks (`rulebooks/*.md`)
- Revisa el comportamiento del agente para detectar falsos positivos o reglas mal calibradas
- Actualiza la severidad, descripción o auto-corrección de las reglas sin necesidad de redeployar el agente
- Valida que los Acceptance Criteria de los Rulebooks reflejan la realidad del codebase objetivo

**Interacción con el sistema:** actúa sobre los ficheros `.md` de Rulebook como artefactos de conocimiento versionados en el repositorio.

---

#### ACT-004 — Authorized Approver

**Quién es:** una persona (o lista de personas) cuyo **username de GitHub Enterprise** está explícitamente configurado como autorizado para desbloquear PRs en estado 🔴 por motivos de urgencia.

**Responsabilidades en el dominio:**
- Única figura autorizada para emitir un **Override Authorization** sobre una PR bloqueada
- Debe identificarse mediante su cuenta de GitHub Enterprise (el sistema verifica que el actor es uno de los configurados)
- La acción de desbloqueo queda registrada como **Override Authorization** con trazabilidad completa
- No puede delegar el permiso a otro usuario no configurado

**Configuración:** la lista de Authorized Approvers se define por repositorio (o por organización) como parte de la configuración del agente. Su modificación requiere acceso al fichero de configuración del agente — no es una acción en tiempo de ejecución.

**Restricción clave:** el override es una excepción de emergencia, no un mecanismo de bypass habitual. Cualquier uso queda registrado y es auditable.

---

#### ACT-005 — HackIAdos Agent

**Quién es:** el agente de IA automatizado que constituye el núcleo del sistema.

**Responsabilidades en el dominio:**
- Recibe eventos de PR (apertura, actualización) vía webhook de GitHub Enterprise
- Detecta el lenguaje/tecnología del diff y selecciona el Rulebook correspondiente
- Selecciona el modelo IA según la estrategia de routing definida en ADR-002
- Aplica las reglas del Rulebook sobre el diff
- Emite el Quality Gate State
- Posta comentarios en la PR con las violaciones detectadas y sus auto-correcciones
- Actualiza el Check Run de GitHub con el estado del Quality Gate
- Envía notificación al canal Google Chat del proyecto cuando el estado es 🔴 o 🟡
- Aprueba automáticamente la PR (GitHub Review) cuando el estado es 🟢

**Limitación explícita:** el agente nunca modifica código directamente. Solo propone auto-correcciones en los comentarios de la PR.

---

#### ACT-006 — Repo Admin / Platform Admin

**Quién es:** la persona responsable de configurar el agente en un repositorio o conjunto de repositorios de BBVA.

**Responsabilidades en el dominio:**
- Configura el webhook del repositorio para que los eventos de PR lleguen al agente
- Define qué Rulebooks aplican a ese repositorio (por tecnología detectada o configuración explícita)
- Configura la lista de Authorized Approvers (ACT-004) para ese repositorio
- Gestiona la integración con el mecanismo de autenticación elegido (GitHub App o PAT — ver ADR-003)

**Nota:** este rol puede recaer en el propio equipo HackIAdos durante la fase inicial del proyecto.

---

### Entidades

#### ENT-001 — Pull Request (PR)

**Qué es:** una solicitud de merge de una rama de trabajo en GitHub Enterprise. Es el artefacto principal que dispara y contiene el análisis del agente.

**Atributos relevantes para el dominio:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `prId` | String | Identificador único de la PR en el repositorio |
| `repositoryUrl` | String | URL del repositorio en GitHub Enterprise |
| `authorUsername` | String | Username del PR Author (ACT-001) |
| `headBranch` | String | Rama origen del cambio |
| `baseBranch` | String | Rama destino del merge |
| `status` | Enum | `open` \| `updated` \| `closed` \| `merged` |
| `qualityGateState` | ENT-005 | Estado actual del Quality Gate emitido por el agente |
| `overrideAuthorization` | ENT-008? | Presente si un Authorized Approver ha desbloqueado la PR |

**Ciclo de vida en el dominio:**
```
open / updated → [agente analiza] → qualityGateState asignado
     → 🔴 merge bloqueado hasta corrección o Override Authorization
     → 🟡 merge permitido con avisos
     → 🟢 PR aprobada automáticamente por el agente
```

---

#### ENT-002 — Diff

**Qué es:** el conjunto de cambios de código incluidos en una PR. El agente analiza el diff, no el código completo del repositorio.

**Atributos relevantes:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `files` | List\<FileDiff\> | Lista de ficheros modificados con sus cambios |
| `totalLinesChanged` | Integer | Líneas añadidas + eliminadas (determina nivel de modelo en ADR-002) |
| `touchesContractFiles` | Boolean | Si incluye cambios en `apis/*.yml` |
| `touchesListeners` | Boolean | Si incluye cambios en `infrastructure/listener/` |
| `modulesAffected` | List\<String\> | Módulos del proyecto tocados (`apibpm`, `apitableservices`, etc.) |
| `languagesDetected` | List\<String\> | Lenguajes detectados — determina qué Rulebook(s) cargar |

**Regla de clasificación de contexto (nuevo vs legacy):**
- Líneas marcadas con `+` en el diff pertenecen a **código nuevo** → se aplican todas las reglas en modo estricto
- Líneas que modifican un método o clase preexistente se clasifican como **legacy modificado** → reglas de estilo/calidad se degradan a warning (ver ENT-005 y `FEAT-HACK-002`)

---

#### ENT-003 — Violation

**Qué es:** una infracción de una regla del Rulebook detectada en el diff analizado.

**Atributos:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `ruleId` | String | ID de la regla infringida (ej. `RULE-SPR-001`) |
| `severity` | Enum | `CRITICAL_ARCH` \| `CRITICAL_QUALITY` \| `WARNING` \| `INFO` |
| `filePath` | String | Ruta del fichero donde se detecta la violación |
| `lineNumber` | Integer | Línea aproximada en el diff |
| `description` | String | Descripción contextualizada de la infracción |
| `codeContext` | Boolean | Si es código nuevo (`true`) o legacy modificado (`false`) |
| `suggestion` | ENT-004? | Auto-corrección propuesta (si la regla la incluye) |

**Nota sobre severity y codeContext:** la severidad efectiva en el Quality Gate combina ambos campos. Una violación `CRITICAL_QUALITY` en `codeContext=false` (legacy) se trata como `WARNING` (ver Regla de Oro del Legacy en Reglas de Dominio).

---

#### ENT-004 — Suggestion (Auto-corrección)

**Qué es:** el bloque de código corregido que el agente propone como solución a una Violation. Se adjunta directamente en el comentario de la PR.

**Atributos:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `ruleId` | String | Regla que originó la sugerencia |
| `language` | String | Lenguaje del bloque de código (`java`, `yaml`) |
| `correctedCode` | String | Bloque de código con la corrección aplicada |
| `explanation` | String | Descripción breve de qué cambia y por qué |

**Restricción:** el agente solo propone — nunca aplica la auto-corrección directamente sobre el código del repositorio.

---

#### ENT-005 — Quality Gate State

**Qué es:** el resultado agregado del análisis de una PR. Es el estado del semáforo emitido por el agente tras procesar todas las Violations detectadas.

**Valores posibles:**

| Estado | Código | Condición | Acción del agente |
|--------|--------|-----------|------------------|
| 🟢 Verde | `GREEN` | Cero violaciones detectadas | Aprueba la PR automáticamente (GitHub Review Approve) |
| 🟡 Amarillo | `YELLOW` | Solo violaciones `WARNING` o `INFO` | Posta comentario educativo · merge permitido · notifica Google Chat |
| 🔴 Rojo | `RED` | Al menos una violación `CRITICAL` efectiva | Posta comentario bloqueante · bloquea merge via Check Run · notifica Google Chat |

**Regla de agregación:** el estado final es el peor estado individual detectado. Una sola violación `CRITICAL` efectiva convierte el resultado en 🔴 independientemente del resto.

---

#### ENT-006 — Rulebook

**Qué es:** el conjunto de reglas de calidad aplicables a una tecnología concreta. El agente carga el Rulebook correspondiente al lenguaje/framework detectado en el diff.

**Atributos:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `ruleBookId` | String | Identificador (ej. `DOC-HACK-001`) |
| `technology` | String | Stack al que aplica (`spring-boot`, `angular`) |
| `version` | String | Versión SemVer del Rulebook |
| `rules` | List\<ENT-007\> | Reglas contenidas |

**Selección de Rulebook:** si el diff toca ficheros Java/Spring Boot → `RULEBOOK-SPRING-001`. Si toca TypeScript/Angular → `RULEBOOK-ANGULAR-001`. Si toca ambos → se cargan ambos y las violaciones de cada uno se tratan de forma independiente.

---

#### ENT-007 — Rule

**Qué es:** una regla individual dentro de un Rulebook. Es la unidad mínima de evaluación del agente.

**Atributos:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `ruleId` | String | ID único (ej. `RULE-SPR-001`) |
| `name` | String | Nombre descriptivo |
| `severity` | Enum | `CRITICAL_ARCH` \| `CRITICAL_QUALITY` \| `WARNING` \| `INFO` |
| `appliesTo` | String | Ámbito de aplicación (código nuevo, legacy, ambos) |
| `qualityGateNewCode` | Enum | Estado que genera en código nuevo |
| `qualityGateLegacy` | Enum | Estado que genera en legacy modificado |

---

#### ENT-008 — Override Authorization

**Qué es:** el registro de una autorización excepcional emitida por un Authorized Approver para desbloquear una PR en estado 🔴 por motivo de urgencia.

**Atributos:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `prId` | String | PR sobre la que se aplica el override |
| `approverUsername` | String | Username de GitHub Enterprise del Authorized Approver |
| `timestamp` | DateTime | Momento exacto de la autorización |
| `justification` | String | Motivo declarado por el Authorized Approver (recomendado, no obligatorio en v1) |
| `violationsOverridden` | List\<String\> | IDs de las violaciones que quedan anuladas |

**Validación de identidad:** el sistema verifica que `approverUsername` pertenece a la lista de Authorized Approvers configurada para ese repositorio. Si no coincide, la autorización se rechaza.

**Trazabilidad:** cada Override Authorization queda registrada y es auditable. No se puede eliminar retroactivamente.

---

#### ENT-009 — PR Comment

**Qué es:** el comentario publicado por el agente en la PR con el resultado del análisis.

**Tipos de comentario:**

| Tipo | Trigger | Contenido |
|------|---------|-----------|
| Bloqueante (🔴) | Quality Gate RED | Resumen de violaciones críticas + bloques de auto-corrección por cada una |
| Educativo (🟡) | Quality Gate YELLOW | Lista de warnings + sugerencias de mejora |
| Aprobación (🟢) | Quality Gate GREEN | Confirmación de cumplimiento 100% de reglas |
| Override confirmado | Override Authorization emitido | Registro de quién autorizó, cuándo y qué violaciones quedan anuladas |

**Formato:** Markdown estructurado (Víctor Carmona es el responsable del formatter de estos comentarios — ver `PROJECT_CONTEXT.md` sección 9).

---

#### ENT-010 — Check Run

**Qué es:** el estado técnico del Quality Gate registrado en GitHub Enterprise como un Check en la PR. Controla si el merge está permitido o bloqueado a nivel de plataforma.

**Estados:**

| Quality Gate | Check Run status | Merge permitido |
|-------------|-----------------|-----------------|
| 🟢 Verde | `success` | ✅ Sí |
| 🟡 Amarillo | `neutral` | ✅ Sí |
| 🔴 Rojo | `failure` | ❌ No (bloqueado por branch protection rules) |
| Override aplicado | `success` (forzado) | ✅ Sí (con registro de override) |

**Dependencia:** requiere que el repositorio tenga configurada una branch protection rule que exija el Check Run de HackIAdos. Sin esta configuración, el bloqueo 🔴 es informativo pero no técnicamente efectivo.

---

#### ENT-011 — Notification

**Qué es:** el mensaje enviado al canal de Google Chat del proyecto cuando el Quality Gate es 🔴 o 🟡.

**Atributos:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `trigger` | Enum | `RED` \| `YELLOW` |
| `prUrl` | String | URL de la PR en GitHub Enterprise |
| `authorUsername` | String | Username del PR Author |
| `qualityGateState` | ENT-005 | Estado emitido |
| `violationSummary` | String | Resumen de violaciones (número por severidad) |
| `channel` | ENT-012 | Canal destino |
| `timestamp` | DateTime | Momento del envío |

**Regla de envío:** 🟢 Verde **no genera notificación** — la aprobación automática en la PR es suficiente señal.

---

#### ENT-012 — Notification Channel

**Qué es:** el canal de Google Chat dedicado a las notificaciones de PR del proyecto. Es específico por proyecto y su único propósito es recibir alertas del agente.

**Atributos:**

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `channelId` | String | Identificador del canal en Google Chat |
| `projectName` | String | Proyecto al que pertenece |
| `webhookUrl` | String | URL del webhook de Google Chat (configurada por el Repo Admin) |
| `audience` | String | Equipo del proyecto (no usuarios individuales) |

---

#### ENT-013 — Webhook Event

**Qué es:** el evento recibido de GitHub Enterprise que dispara el ciclo de análisis del agente.

**Eventos relevantes:**

| Evento GitHub | Acción del agente |
|--------------|------------------|
| `pull_request.opened` | Inicia análisis completo |
| `pull_request.synchronize` | Re-analiza (nuevo commit pushed) |
| `pull_request.closed` | No analiza (PR cerrada sin merge) |
| `pull_request_review.submitted` | Si el reviewer es un Authorized Approver y la acción es `approve` sobre una PR en 🔴 → registra Override Authorization |

---

### Reglas de Dominio

#### RD-001 — Regla de Oro del Legacy (invariante)

El agente distingue obligatoriamente entre código nuevo y código legacy modificado en cada Violation detectada.

- **Código nuevo** (líneas `+` en un método o clase que no existía antes): se aplican todas las reglas en modo estricto. Las violaciones `CRITICAL` bloquean.
- **Legacy modificado** (líneas `+` en un método o clase preexistente): las violaciones `CRITICAL_QUALITY` se tratan como `WARNING` (no bloquean). Solo las violaciones `CRITICAL_ARCH` y los fallos de seguridad nuevos introducidos en ese cambio mantienen su carácter bloqueante.

Esta regla es invariante — ningún Rulebook puede desactivarla.

---

#### RD-002 — Agregación del Quality Gate

El Quality Gate State de una PR es el peor estado individual entre todas las Violations detectadas. Una sola Violation que resulta en 🔴 (tras aplicar RD-001) convierte todo el resultado en 🔴.

```
Violations efectivas → max(severidad efectiva) → Quality Gate State
```

No existe estado intermedio entre los tres: 🔴, 🟡 o 🟢.

---

#### RD-003 — Auto-aprobación en Verde

Cuando el Quality Gate es 🟢, el agente emite automáticamente un **GitHub Review Approval** en nombre de la integración HackIAdos. Ningún revisor humano necesita aprobar manualmente en este caso. El PR Author puede mergear directamente una vez que su Tech Lead (si aplica) haya completado su revisión humana.

---

#### RD-004 — Override restringido a Authorized Approvers

Solo los usuarios cuyo `username` de GitHub Enterprise esté explícitamente configurado en la lista de Authorized Approvers del repositorio pueden emitir un Override Authorization sobre una PR bloqueada en 🔴. Cualquier intento de override por un usuario no autorizado es rechazado silenciosamente o con mensaje de denegación.

El override es una medida de emergencia excepcional, no un mecanismo de bypass habitual. Toda autorización queda registrada como ENT-008 con trazabilidad completa e irrevocable.

---

#### RD-005 — Selección de Rulebook por tecnología

El agente detecta automáticamente el lenguaje/tecnología del diff y carga el Rulebook correspondiente. Si el diff toca múltiples tecnologías, se cargan múltiples Rulebooks y las violaciones de cada uno se evalúan de forma independiente.

Si no existe Rulebook para la tecnología detectada, el agente emite 🟢 con aviso de cobertura parcial (no bloquea por ausencia de reglas).

---

#### RD-006 — Notificación selectiva por estado

El agente envía notificación al Notification Channel del proyecto únicamente para los estados 🔴 y 🟡. El estado 🟢 no genera notificación externa — la aprobación automática en la PR es la señal suficiente.

---

#### RD-007 — Re-análisis en cada push

Cada vez que el PR Author hace un nuevo push a la rama de la PR (`pull_request.synchronize`), el agente re-ejecuta el análisis completo sobre el nuevo diff. El Quality Gate State se actualiza y el Check Run refleja el nuevo resultado. Los comentarios previos del agente no se eliminan — se añade un nuevo comentario con el resultado actualizado.

---

### Restricciones

| ID | Restricción |
|----|-------------|
| REST-001 | El agente nunca modifica código directamente en el repositorio |
| REST-002 | Solo los Authorized Approvers configurados pueden emitir Override Authorization |
| REST-003 | La lista de Authorized Approvers solo puede modificarse en la configuración del agente, no en tiempo de ejecución |
| REST-004 | Los Rulebooks son artefactos de conocimiento versionados — su modificación requiere actualizar la versión SemVer del fichero |
| REST-005 | La Regla de Oro del Legacy (RD-001) es invariante y no puede desactivarse por configuración |
| REST-006 | Un Override Authorization no puede eliminarse retroactivamente — es inmutable una vez emitido |
| REST-007 | El agente no analiza PRs cerradas ni ramas sin protección configurada para el Check Run |

---

## Acceptance Criteria

- [ ] El agente identifica correctamente al PR Author desde el evento de webhook
- [ ] El agente bloquea el merge (Check Run `failure`) cuando el Quality Gate es 🔴
- [ ] El agente aprueba automáticamente (GitHub Review Approve) cuando el Quality Gate es 🟢
- [ ] Cuando un Authorized Approver hace override, el Check Run cambia a `success` y se registra el ENT-008
- [ ] Un usuario no Authorized Approver no puede emitir override aunque sea Tech Lead
- [ ] El agente envía notificación al Notification Channel del proyecto cuando el estado es 🔴 o 🟡
- [ ] El agente NO envía notificación cuando el estado es 🟢
- [ ] Las violaciones en legacy modificado con severity `CRITICAL_QUALITY` se tratan como `WARNING` (RD-001)
- [ ] Las violaciones `CRITICAL_ARCH` bloquean tanto en código nuevo como en legacy modificado
- [ ] En cada nuevo push a la PR, el agente re-analiza y actualiza el Check Run

## Evidence

Derivado de conversaciones de diseño del equipo HackIAdos (mayo 2026). Los actores y reglas han sido validados con Víctor Carmona y Pablo Martínez. Confidence `medium`: diseño acordado pero pendiente de validación contra la implementación real.

## Traceability

- `ADR-001` — lenguaje de implementación del agente (Spring Boot / Java 11)
- `ADR-002` — estrategia de routing de modelo IA (Haiku / Sonnet / Opus)
- `ADR-003` — mecanismo de integración con GitHub Enterprise (pendiente decisión)
- `ARCH-HACK-001` — arquitectura del proyecto WGTB Backend (codebase objetivo)
- `DOC-HACK-001` (`rulebooks/RULEBOOK-SPRING-001.md`) — Rulebook que define las Rules (ENT-007)
- `FEAT-HACK-001` — lógica detallada del Quality Gate (pendiente de crear)
- `FEAT-HACK-002` — implementación de la Regla de Oro del Legacy (pendiente de crear)
