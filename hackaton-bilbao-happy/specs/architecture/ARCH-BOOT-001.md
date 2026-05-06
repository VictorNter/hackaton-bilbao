---
id: ARCH-BOOT-001
type: knowledge
layer: architecture
title: Arquitectura del microservicio wgtbBackend
status: draft
confidence: low
version: 0.1.0
owner: pending
domain: platform
subdomain: Microservices
tags:
  - wgtbbackend
  - wgtb
  - gtb
  - spring-boot
  - hexagonal
  - nova
  - bpm
dependencies:
  - id: DOC-BOOT-wgtbbackend-p037
    type: extends
generated-by: kdd-studio
generated-at: '2026-05-06T19:46:37.316Z'
source: DOC-BOOT-wgtbbackend-p037.md
---

# Arquitectura del microservicio wgtbBackend

## Intent
Captura la identidad técnica, los patrones de diseño y las integraciones del
microservicio `wgtbBackend` (UUAA: WGTB), de manera que cualquier equipo que
extienda o integre el servicio disponga de una referencia arquitectónica estable.

## Definition

### Concept
`wgtbBackend` es un microservicio REST de tipo API perteneciente a la UUAA
**WGTB** (GTB Workflow Tool). Está desarrollado en **Java 11 con Spring Boot**
y desplegado sobre la plataforma **NOVA**. Actúa como backend de la herramienta
de gestión de flujos de trabajo operativos del área GTB (Global Transaction
Banking), proporcionando la capa de negocio y persistencia que sustenta las
interfaces de usuario y los procesos automatizados de la plataforma.

### Rules
1. El servicio orquesta y registra el ciclo de vida de oportunidades y tareas
   de negocio dentro de flujos BPM.
2. Las operaciones soportadas sobre entidades BPM incluyen, como mínimo:
   - Creación de oportunidades
   - Asignación y liberación de tareas
   - Cambio de estados
   - Registro de comentarios
   - Gestión de campos dinámicos
   _(El documento fuente está truncado; pueden existir operaciones adicionales —
   ver open_questions.)_
3. La arquitectura interna sigue el estilo **Hexagonal (Ports & Adapters)**,
   complementado con los patrones **Factory**, **Builder** y **Repository**.
4. La capa de persistencia usa **Oracle** como base de datos relacional.
5. La comunicación externa se realiza exclusivamente vía **REST/HTTP**.

### Constraints
- Plataforma de despliegue: NOVA (impone restricciones de runtime y
  configuración propias del estándar BBVA ONE).
- Lenguaje: Java 11 (LTS en el momento del análisis).

### Examples
- Un proceso BPM del área GTB crea una oportunidad → el servicio la persiste
  en Oracle y actualiza su estado a través de la API REST.
- Un usuario libera una tarea asignada → el evento llega por HTTP, el puerto
  de entrada lo recibe, el caso de uso lo procesa y el adaptador de
  persistencia actualiza Oracle.

## Acceptance Criteria
- [ ] El servicio expone una API REST que acepta operaciones de creación,
      asignación, liberación, cambio de estado, comentario y gestión de
      campos dinámicos sobre entidades BPM.
- [ ] La arquitectura interna es validable como hexagonal: lógica de negocio
      sin dependencias directas de infraestructura (Oracle, HTTP).
- [ ] El servicio arranca y despliega correctamente en la plataforma NOVA.
- [ ] La persistencia se realiza sobre Oracle sin acceso directo desde la capa
      de dominio (mediado por el patrón Repository).

## Evidence
| Type | Reference | Date | Confidence impact |
|------|-----------|------|-------------------|
| Document | DOC-BOOT-wgtbbackend-p037.md | 2026-05-06 | Initial → LOW |

## Traceability
| Relation | Target | Description |
|----------|--------|-------------|
| Source document | DOC-BOOT-wgtbbackend-p037.md | Incorporado en: 2026-05-06 |
| Extends | DOC-BOOT-wgtbbackend-p037 | Estructuración arquitectónica del DOC base |
