# HackIAdos — Contexto del Proyecto para IA

> Fuente de verdad del proyecto HackIAdos: AI Code Reviewer & Quality Gate 2.0.
> Leer completo al inicio de cada sesión. Leer también: **KDD_FRAMEWORK.md**
> Última actualización: 04 Mayo 2026

---

## 1. EQUIPO

| Persona | Rol |
|---------|-----|
| **Víctor Carmona Torres** | Contextualización del agente · creación de formatters de markdown |
| **Pablo Martínez** | Prompt engineering (via Gemini) |
| **Lourdes Pozo** | TBD |

---

## 2. QUÉ ES HACKIADÓS

**HackIAdos: AI Code Reviewer & Quality Gate 2.0** es un agente de IA que actúa como revisor de código incansable para organizaciones con estándares estrictos (entorno BBVA / GitHub Enterprise interno).

**Objetivo principal:** garantizar la gobernanza técnica y la calidad del software de forma automática al detectar una Pull Request, sin frenar la productividad del equipo.

**Principio diferencial:** la IA distingue entre código nuevo (strictness total) y código legacy modificado (mejora incremental, sin bloqueos por deuda heredada).

---

## 3. ARQUITECTURA DE LA SOLUCIÓN

### 3.1 Estandarización Dinámica — El Libro de Reglas
- El agente se basa en **Rulebooks** (`.md` en `rulebooks/`) por tecnología
- **Stack objetivo revisado:** Java/Spring Boot (backend) · Angular (frontend)
- Arquitectura objetivo: **Hexagonal** (ports & adapters) — ver `arquitectura/`
- Cada regla tiene severidad: 🔴 Crítico / 🟡 Warning / 🔵 Info
- Los Rulebooks son versionados y actualizables sin redeployar el agente

### 3.2 Análisis al detectar una PR
- **Trigger:** Webhook de GitHub Enterprise (BBVA interno) al abrir/actualizar una Pull Request
- **Análisis:** diff → errores de tipado, lógica y complejidad ciclomática
- **Detección de contexto:** método/clase nuevo vs. código existente modificado
- **Motor IA:** Claude + GitHub Copilot Claude Agent

### 3.3 Quality Gate — Semáforo de Git

| Estado | Condición | Acción |
|--------|-----------|--------|
| 🟢 Verde | Cumple el 100% de las reglas | Sugiere aprobación automática |
| 🟡 Amarillo | Fallos menores o deuda técnica | Permite avance · notifica a Google Chat |
| 🔴 Rojo | Fallos críticos (seguridad / arquitectura) | Bloquea el merge · alerta urgente en Google Chat |

### 3.4 Auto-Corrección
El agente adjunta el **bloque de código corregido** directamente en el comentario de la PR.
Víctor gestiona los formatters que dan forma a estos comentarios en Markdown.

### 3.5 Regla de Oro: Manejo de Código Legacy

| Tipo de código | Tratamiento |
|----------------|-------------|
| **Métodos/Clases nuevas** | Aplicación estricta. Fallo = 🔴 Rojo (bloquea) |
| **Métodos existentes modificados** | Solo 🟡 Warnings + sugerencias educativas. No bloquea por deuda heredada |
| **Excepción** | Si el cambio legacy introduce un fallo crítico de seguridad *nuevo* → 🔴 Rojo |

---

## 4. INFRAESTRUCTURA Y STACK

| Componente | Tecnología | Estado |
|-----------|-----------|--------|
| Integración GitHub | **GitHub App** (Statuses, Check Runs, Comentarios) | ⏳ ADR-003 pendiente |
| Plataforma GitHub | **GitHub Enterprise** — entorno interno BBVA | Confirmado |
| Motor IA | **Claude + GitHub Copilot Claude Agent** | Confirmado |
| Prompt engineering | **Gemini** (tool usado por Pablo para diseño de prompts) | En uso |
| Distribución librería | **Artifactory** (DTOs, contratos API como librería interna) | ⏳ Por diseñar |
| Notificaciones | **Google Chat** (webhooks) | ⏳ Por diseñar |
| CI/CD y despliegue | **Jenkins** automatizado vía **NOVA** (plataforma interna BBVA) | Confirmado |
| Lenguaje del agente | TBD | ⏳ ADR-001 pendiente |

### Stack objetivo (código que revisa el agente)
| Capa | Tecnología | Patrón Arquitectónico |
|------|-----------|----------------------|
| Backend | Java / Spring Boot | Hexagonal (ports & adapters) |
| Frontend | Angular | TBD |

> Ver carpeta `arquitectura/` para análisis completo del proyecto WGTB (codebase objetivo).
> Ver `KDD_Auditoria_WGTB_Backend.md` para auditoría del backend que informará el primer Rulebook.

---

## 5. FASES DEL PROYECTO

| Fase | Descripción | Estado |
|------|-------------|--------|
| **Fase 0** | Base de conocimiento KDD — specs, ADRs, arquitectura | 🔵 EN CURSO — Mayo 2026 |
| **Fase 1** | MVP: webhook → análisis → Quality Gate 🟢🟡🔴 | ⏳ Pendiente |
| **Fase 2** | Auto-corrección: código sugerido en comentarios de PR | ⏳ Pendiente |
| **Fase 3** | Rulebooks dinámicos: carga por tecnología detectada | ⏳ Pendiente |
| **Fase 4** | Distribución como librería interna en Artifactory | ⏳ Pendiente |

**Principio:** El agente propone — el equipo valida — el agente ejecuta. Siempre Human-in-the-loop.

---

## 6. ORDEN DE RULEBOOKS

| # | Rulebook | Tecnología | Justificación |
|---|----------|-----------|---------------|
| 1 | `RULEBOOK-SPRING-001.md` | Java / Spring Boot | Backend primero · fuente: `KDD_Auditoria_WGTB_Backend.md` |
| 2 | `RULEBOOK-ANGULAR-001.md` | Angular | Frontend después · fuente: `arquitectura/integraciones_modulos_wgtb.md` |

---

## 7. ESTADO DEL REPOSITORIO — 04/05/2026

```
hackIAdos/
├── PROJECT_CONTEXT.md              ✅ actualizado · 04/05/2026
├── KDD_FRAMEWORK.md                ✅ creado · 04/05/2026
├── SPEC-INDEX.md                   ✅ creado · 04/05/2026
├── README.md                       ✅ creado · 04/05/2026
├── KDD_Auditoria_WGTB_Backend.md   ✅ presente · fuente para RULEBOOK-SPRING-001
│
├── arquitectura/                   ✅ presente · análisis del codebase WGTB
│   ├── arquitectura_hexagonal_wgtb.md
│   ├── guia_desarrollo_wgtb.md
│   ├── integraciones_modulos_wgtb.md
│   └── README_DOCUMENTACION.md
│
├── promps/                         ✅ presente · trabajo de Pablo (prompt engineering)
│   └── guia.md
│
├── specs/
│   ├── feature/                    ⏳ vacío
│   ├── domain/                     ⏳ vacío
│   ├── architecture/               ⏳ vacío
│   └── legacy/                     ⏳ vacío
│
├── adrs/                           ⏳ vacío · ADR-001/002/003 pendientes
├── work/                           ⏳ vacío
├── rulebooks/                      ⏳ vacío · RULEBOOK-SPRING-001 es el siguiente paso
└── agents/
    └── code-reviewer/              ⏳ vacío · SKILL.md tras specs en active
```

---

## 8. PREGUNTAS ABIERTAS — REQUIEREN RESPUESTA DEL EQUIPO

| # | Pregunta | Por qué es crítica |
|---|----------|--------------------|
| 1 | ¿Cuál es el **lenguaje de implementación del agente** en sí? ¿Spring Boot también, o Python/Node.js? | Desbloquea ADR-001 y ARCH-HACK-001 |
| 2 | ¿Cuál es el **rol de Lourdes Pozo** en el proyecto? | Para asignar owners y saber quién valida qué |

---

## 9. INSTRUCCIONES PARA LA IA

- Respuestas directas sin preámbulo. Orientadas a acción.
- Una sesión = un objetivo = un fichero `.md` commiteado al final.
- Preguntar ANTES de generar si falta información. No desperdiciar tokens.
- Actualizar PROJECT_CONTEXT.md y SPEC-INDEX.md al cerrar cada sesión.
- La **Regla de Oro del Legacy** (sección 3.5) es invariante — reflejarla siempre.
- Al escribir el RULEBOOK-SPRING-001, usar `KDD_Auditoria_WGTB_Backend.md` y `arquitectura/` como fuente primaria.
- Los formatters de markdown de los comentarios de PR son responsabilidad de Víctor — consultarle antes de definir el formato de output del agente.
- Cuando una decisión se tome en conversación, formalizarla como ADR. No dejar decisiones sin doc.
