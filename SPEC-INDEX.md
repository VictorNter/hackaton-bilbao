# SPEC-INDEX — hackIAdos

> **Proyecto:** HackIAdos — AI Code Reviewer & Quality Gate 2.0
> **Metodología:** KDD v2 · L1
> **Última actualización:** 04 Mayo 2026
> **Validador:** no ejecutado — repositorio en Fase 0

---

## Knowledge Artifacts

| ID | Fichero | Tipo | Estado | Confidence | Versión |
|----|---------|------|--------|------------|---------|
| ARCH-HACK-001 | `specs/architecture/ARCH-HACK-001-arquitectura-wgtb-backend.md` | architecture | draft | medium | 0.1.0 |
| DOC-HACK-001 | `rulebooks/RULEBOOK-SPRING-001.md` | documentation | draft | low | 0.2.0 |

---

## Governance Artifacts

| ID | Fichero | Estado | Confidence |
|----|---------|--------|------------|
| ADR-001 | `adrs/ADR-001-lenguaje-implementacion-agente.md` | accepted | medium |
| ADR-002 | `adrs/ADR-002-modelo-ia.md` | accepted | medium |
| ADR-003 | `adrs/ADR-003-github-app-vs-pat.md` | proposed | low |

---

## Work Artifacts

| Fichero | Estado |
|---------|--------|
| — | — |

---

## Rulebooks

| ID | Fichero | Tecnología | Estado |
|----|---------|-----------|--------|
| DOC-HACK-001 | `rulebooks/RULEBOOK-SPRING-001.md` | Java 11 / Spring Boot | 🟡 draft · v0.1.0 |

---

## Contexto de Dominio (no specs — fuentes primarias para Rulebooks)

| Fichero | Contenido | Usar para |
|---------|-----------|-----------|
| `KDD_Auditoria_WGTB_Backend.md` | Auditoría del backend WGTB | Fuente primaria → `RULEBOOK-SPRING-001` |
| `arquitectura/arquitectura_hexagonal_wgtb.md` | Arquitectura Hexagonal de WGTB | Reglas de estructura Spring Boot |
| `arquitectura/guia_desarrollo_wgtb.md` | Guía de desarrollo WGTB (convenciones, patrones) | Reglas de naming, DTOs, Mappers |
| `arquitectura/integraciones_modulos_wgtb.md` | Integración modulos + Frontend-Backend | Reglas Angular + integraciones |
| `promps/guia.md` | Guía de prompts (Pablo) | Diseño del prompt del agente revisor |

---

## Agent Skills

| Fichero | Estado | Activa en |
|---------|--------|-----------|
| `agents/code-reviewer/SKILL.md` | ⏳ Pendiente · tras specs en active | Fase 1 |

---

## Pendiente de crear — por prioridad

| Prioridad | ID | Fichero | Por qué |
|-----------|-----|---------|---------|
| ~~🔴~~ | ~~`ADR-001`~~ | ~~`adrs/ADR-001-lenguaje-implementacion-agente.md`~~ | ✅ Creado — accepted |
| ~~🔴~~ | ~~`ADR-002`~~ | ~~`adrs/ADR-002-modelo-ia.md`~~ | ✅ Creado — accepted |
| ~~🔴~~ | ~~`ADR-003`~~ | ~~`adrs/ADR-003-github-app-vs-pat.md`~~ | ✅ Creado — proposed (pendiente validación BBVA) |
| 🔴 | `ARCH-HACK-002` | `specs/architecture/ARCH-HACK-002-stack-agente-hackiados.md` | Stack técnico del agente HackIAdos — requiere ADR-001/002/003 |
| 🟡 | `DOM-HACK-001` | `specs/domain/DOM-HACK-001-actores-entidades.md` | Actores (PR author, reviewer…) y entidades (PR, diff, violation…) |
| 🟡 | `FEAT-HACK-001` | `specs/feature/FEAT-HACK-001-quality-gate-logic.md` | Lógica del semáforo 🟢🟡🔴 |
| 🟡 | `FEAT-HACK-002` | `specs/feature/FEAT-HACK-002-legacy-code-rule.md` | Regla de Oro del Legacy |
| ~~🟡~~ | ~~`RULEBOOK-SPRING-001`~~ | ~~`rulebooks/RULEBOOK-SPRING-001.md`~~ | ✅ Creado — `DOC-HACK-001` |
| 🟢 | `RULEBOOK-ANGULAR-001` | `rulebooks/RULEBOOK-ANGULAR-001-angular.md` | Segundo Rulebook — tras Spring Boot |

---

## Estado general

```
Total artefactos:  2 Knowledge + 3 Governance + 0 Work + 1 Rulebooks = 6
Errores:           0  ✅
Orphans:           0  ✅
Fase 0:            EN CURSO 🔵 — ADRs creados · ADR-003 pendiente validación BBVA
Siguiente acción:  Validar ADR-003 con plataforma BBVA → crear ARCH-HACK-002 (stack agente)
```
