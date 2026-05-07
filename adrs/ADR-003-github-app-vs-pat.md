---
id: ADR-003
type: adr
layer: adr
status: proposed
confidence: low
version: "0.1.0"
created: 2026-05-04
updated: 2026-05-04
owner: victor-carmona
dependencies:
  - id: ADR-001
    relation: depends-on
tags:
  - github
  - github-enterprise
  - autenticacion
  - webhook
  - bbva
  - integracion
---

# ADR-003 — Mecanismo de integración con GitHub Enterprise (BBVA)

## Context

HackIAdos necesita dos capacidades sobre GitHub Enterprise interno de BBVA:

1. **Escuchar eventos**: recibir notificación cuando se abre o actualiza una Pull Request (webhook).
2. **Actuar sobre PRs**: publicar comentarios con el resultado del análisis y actualizar el estado del Quality Gate (Check Run o Status).

GitHub Enterprise admite varios mecanismos de autenticación e integración. Cada uno tiene implicaciones distintas en términos de permisos, viabilidad dentro del ecosistema BBVA y complejidad de setup.

**Restricción crítica:** la viabilidad de cada opción depende de lo que BBVA permita en su instancia de GitHub Enterprise. Esta decisión **no puede tomarse solo desde el equipo de HackIAdos** — requiere validación con el equipo de plataforma / seguridad de BBVA.

---

## Opciones evaluadas

### Opción A — GitHub App

Una GitHub App es una integración de primera clase en GitHub. Se instala a nivel de organización o repositorio y actúa con su propia identidad (no la de un usuario).

**Cómo funciona:**
- Se registra la App en GitHub Enterprise (requiere permisos de administrador de organización)
- La App recibe webhooks firmados con su secret
- Se autentica con JWT + Installation Token (rotación automática cada hora)
- Actúa con los permisos granulares configurados en la App (Pull Requests: Read & Write, Checks: Write)

**Ventajas:**
- Identidad propia (los comentarios aparecen como "HackIAdos Bot", no como un usuario real)
- Permisos granulares — solo accede a lo que necesita
- Tokens de corta duración (más seguro)
- Escalable a múltiples repositorios y organizaciones sin crear nuevas credenciales
- Es el mecanismo recomendado por GitHub para integraciones de CI/CD

**Inconvenientes:**
- Requiere aprobación de administrador de organización en GitHub Enterprise BBVA
- Setup más complejo (registro de App, gestión de private key, JWT generation)
- Puede estar restringida o requerir proceso de aprobación formal en BBVA

---

### Opción B — Personal Access Token (PAT) clásico

Un PAT clásico vincula el acceso a la cuenta de un usuario (o cuenta de servicio).

**Cómo funciona:**
- Se crea un PAT en la cuenta de un usuario de servicio (`hackiados-bot@bbva.com` o similar)
- El agente usa el PAT en la cabecera `Authorization: token <PAT>` para todas las llamadas a la API
- Los webhooks se configuran manualmente en cada repositorio con un secret propio

**Ventajas:**
- Setup simple — solo necesita un token y acceso a la configuración del repositorio
- No requiere aprobación de administrador de organización (solo del dueño del repositorio)
- Familiar para cualquier equipo que ya use GitHub API

**Inconvenientes:**
- El token está vinculado a un usuario: si ese usuario se va o su cuenta se desactiva, el agente deja de funcionar
- Permisos poco granulares (repo scope da acceso a mucho más de lo necesario)
- Tokens de larga duración (riesgo de seguridad si se filtran)
- En BBVA puede haber políticas que prohíban PATs con acceso a repos de organización

---

### Opción C — Fine-Grained PAT (PAT de nueva generación)

Similar al PAT clásico pero con control de permisos por repositorio y tipo de recurso.

**Ventajas frente al PAT clásico:**
- Permisos granulares similares a GitHub App (solo Pull Requests y Checks)
- Scope limitado a repositorios específicos
- Tokens con fecha de expiración configurable

**Inconvenientes:**
- Sigue estando vinculado a un usuario
- Disponibilidad en GitHub Enterprise depende de la versión instalada en BBVA
- No recibe webhooks directamente (sigue siendo el agente quien los configura)

---

### Opción D — OAuth App

Una OAuth App permite actuar en nombre de un usuario que ha dado consentimiento.

**Descartada:** no aplica para un agente automatizado sin interacción de usuario. No es viable para este caso de uso.

---

## Tabla comparativa

| Criterio | GitHub App | PAT clásico | Fine-Grained PAT |
|----------|-----------|-------------|-----------------|
| Identidad propia (no vinculada a usuario) | ✅ | ❌ | ❌ |
| Permisos granulares | ✅ | ❌ | ✅ |
| Tokens de corta duración | ✅ | ❌ | Configurable |
| Requiere aprobación admin org | ✅ (necesario) | ❌ | ❌ |
| Complejidad de setup | Alta | Baja | Media |
| Recomendado por GitHub para bots | ✅ | ❌ | Parcialmente |
| Disponibilidad en GHE BBVA | A validar | Probable | A validar (depende versión GHE) |

---

## Decision

**Pendiente — estado: proposed.**

La decisión está bloqueada por la validación con el equipo de plataforma/seguridad de BBVA. Se establece el siguiente orden de preferencia técnica:

1. **GitHub App** — opción ideal si BBVA permite su instalación
2. **Fine-Grained PAT** — alternativa si GitHub App no es viable pero la versión de GHE la soporta
3. **PAT clásico sobre cuenta de servicio** — fallback si ninguna de las anteriores es viable

**Preguntas que debe responder el equipo de plataforma BBVA antes de cerrar este ADR:**

- [ ] ¿Permite la instancia de GitHub Enterprise de BBVA la creación e instalación de GitHub Apps a nivel de organización?
- [ ] ¿Existe un proceso de aprobación formal para registrar una GitHub App en el entorno interno?
- [ ] ¿Qué versión de GitHub Enterprise está instalada? (relevante para Fine-Grained PATs)
- [ ] ¿Hay cuentas de servicio (`service accounts`) disponibles para vincular un PAT si fuera necesario?
- [ ] ¿Existen restricciones de seguridad sobre el uso de webhooks con endpoints externos?

---

## Rationale

La preferencia técnica es **GitHub App** porque:
- Es el único mecanismo que no vincula el agente a la identidad de un empleado de BBVA
- Los tokens de instalación (1h de TTL) eliminan el riesgo de credenciales de larga duración filtradas
- Permite operar sobre múltiples repositorios y organizaciones sin multiplicar credenciales
- Es el camino que GitHub recomienda para integraciones automatizadas de CI/CD

Sin embargo, la viabilidad dentro de BBVA es determinante. Si no es posible, el Fine-Grained PAT sobre una cuenta de servicio es el compromiso más razonable.

---

## Consequences

**Si se elige GitHub App:**
- Requiere proceso formal de aprobación con el equipo de plataforma BBVA
- El agente recibe webhooks firmados — mayor seguridad en la verificación de eventos
- Setup inicial más costoso, pero mantenimiento mínimo (rotación automática de tokens)

**Si se elige Fine-Grained PAT o PAT clásico:**
- Setup inmediato sin bloqueos burocráticos
- El agente queda vinculado a una cuenta de usuario/servicio — plan de contingencia necesario si esa cuenta cambia
- Requiere política de rotación manual de tokens cada N meses

**Pendiente de actualizar:**
- Cambiar `status: proposed` → `status: accepted` una vez validada la opción con BBVA
- Incrementar `version` a `1.0.0` y actualizar `confidence` a `high` o `medium` según la certeza de la decisión final
