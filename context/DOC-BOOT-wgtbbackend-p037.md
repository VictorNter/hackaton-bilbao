---
id: DOC-BOOT-wgtbbackend-p037
type: knowledge
layer: doc
title: Documentación Técnica P037 — wgtbBackend
status: draft
confidence: medium
version: '1.0'
owner: kdd-studio-plugin
domain: boot
dependencies: []
generated-by: kdd-studio
generated-at: '2026-05-06T16:49:41.049Z'
source: docs-tecnicos/P037-BOOT-wgtbbackend.md
---

# Documentación Técnica P037 — wgtbBackend

## Purpose

Documentación técnica P037 del servicio **wgtbBackend** (UUAA: BOOT), generada automáticamente a partir del análisis del código fuente.

## Definition

### Resumen

`wgtbbackend` es un microservicio REST de tipo API, perteneciente a la UUAA **WGTB** (GTB Workflow Tool), desarrollado en Java 11 con Spring Boot y desplegado sobre la plataforma NOVA. Su función principal es servir como backend de la herramienta de gestión de flujos de trabajo operativos del área GTB (Global Transaction Banking), proporcionando la capa de negocio y persistencia que sustenta las interfaces de usuario y los procesos automatizados de la plataforma. El servicio resuelve la necesidad de orquestar y registrar el ciclo de vida de oportunidades y tareas de negocio dentro de flujos BPM. Recibe eventos y acciones sobre estas entidades — creación de oportunidades, asignación y liberación de tareas, cambio de estados, registro de comentarios, gestión de campos dinámicos — y los persi

### Patrones detectados

- Factory
- Builder
- Hexagonal
- Ports & Adapters
- Repository

### Integraciones

- Oracle
- REST
- HTTP

## Evidence

- Fichero fuente: `docs-tecnicos/P037-BOOT-wgtbbackend.md`
- Generado por: kdd-studio (análisis automático de código Java)
- Fecha: 2026-05-06
