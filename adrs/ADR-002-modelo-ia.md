---
id: ADR-002
type: adr
layer: adr
status: accepted
confidence: medium
version: "1.0.0"
created: 2026-05-04
updated: 2026-05-04
owner: victor-carmona
dependencies:
  - id: ADR-001
    relation: depends-on
tags:
  - modelo-ia
  - claude
  - tokens
  - routing
  - haiku
  - sonnet
  - opus
  - stack-agente
---

# ADR-002 — Selección y estrategia de routing del modelo IA

## Context

HackIAdos necesita un modelo de lenguaje para analizar diffs de PRs y aplicar las reglas del Rulebook. El coste de tokens es una restricción real: el agente se ejecutará en cada PR abierta o actualizada en los repositorios BBVA objetivo, lo que puede suponer decenas de invocaciones diarias.

Los modelos disponibles en la familia Claude (mayo 2026) son:

| Modelo | ID | Capacidad | Coste relativo |
|--------|-----|-----------|----------------|
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Rápido, tareas simples | 🟢 Bajo |
| Sonnet 4.6 | `claude-sonnet-4-6` | Balanceado, análisis complejos | 🟡 Medio |
| Opus 4.7 | `claude-opus-4-7` | Máxima capacidad | 🔴 Alto |

No todas las PRs tienen la misma complejidad: una PR de 30 líneas que renombra variables no requiere el mismo poder de análisis que una PR de 600 líneas que toca tres módulos y modifica contratos YML.

---

## Decision

**Modelo base:** `claude-sonnet-4-6` — es el modelo por defecto para cualquier análisis que no encaje en los criterios de los otros dos niveles.

Se adopta una **estrategia de routing dinámico de tres niveles** basada en el tamaño del diff, los ficheros tocados y la señal de riesgo detectada en el análisis de triage:

### Nivel 1 — Triage rápido (Haiku)

**Modelo:** `claude-haiku-4-5-20251001`

**Condición de activación:**
- Diff con menos de 150 líneas cambiadas **y**
- Ningún fichero `apis/*.yml` modificado **y**
- Ningún fichero `infrastructure/listener/` o `domain/` en el diff

**Checks que ejecuta:**
- Reglas de naming (RULE-SPR-006, RULE-SPR-007)
- Detección de `@Autowired` en campos (RULE-SPR-004)
- Longitud de métodos y anidamiento obvio (RULE-SPR-012, RULE-SPR-013)

**Resultado:**
- Si Haiku no detecta ninguna violación → 🟢 Verde directo (coste mínimo)
- Si Haiku detecta alguna violación o incertidumbre → escalar a Sonnet (Nivel 2)

---

### Nivel 2 — Análisis estándar (Sonnet) — **por defecto**

**Modelo:** `claude-sonnet-4-6`

**Condición de activación:**
- Diff entre 150 y 500 líneas, **o**
- Toca ficheros `apis/*.yml`, **o**
- Toca `infrastructure/listener/` o `application/impl/`, **o**
- Haiku (Nivel 1) ha escalado el análisis

**Checks que ejecuta:** todas las reglas de `RULEBOOK-SPRING-001` (RULE-SPR-001 a RULE-SPR-015)

**Resultado:** emite el estado del Quality Gate (🔴 / 🟡 / 🟢) con comentario detallado en la PR

---

### Nivel 3 — Análisis profundo (Sonnet en contexto ampliado)

**Modelo:** `claude-sonnet-4-6` (mismo modelo, distinta estrategia de contexto)

**Condición de activación:**
- Diff con más de 500 líneas cambiadas, **o**
- Modifica ficheros en más de un módulo (`apibpm` + `apitableservices` o `apitemplates`), **o**
- Modifica simultáneamente un contrato YML y su listener asociado

**Diferencia respecto al Nivel 2:**
- Se carga `ARCH-HACK-001` (arquitectura del proyecto) como contexto adicional
- El análisis se divide en pasadas: primero los ficheros de contrato YML, luego los de implementación
- Si Sonnet expresa incertidumbre en su output sobre una violación arquitectónica → escalar puntualmente a `claude-opus-4-7` solo para ese fragmento

> **Nota sobre Opus:** Opus queda reservado exclusivamente como escalado puntual en el Nivel 3. No es un nivel habitual de operación. El objetivo es que Sonnet resuelva el 95%+ de los análisis.

---

### Resumen del routing

```
PR recibida
     │
     ▼
¿Diff < 150 líneas Y sin YML Y sin listener/domain?
     │ SÍ                          │ NO
     ▼                             ▼
  HAIKU                        SONNET (estándar)
     │                             │
¿Violación o incertidumbre?   ¿Diff > 500 líneas o
     │ SÍ        │ NO         multi-módulo o YML+listener?
     ▼           ▼                 │ SÍ
  SONNET     🟢 Verde         SONNET (contexto ampliado)
(estándar)                         │
                              ¿Incertidumbre arquitectónica?
                                   │ SÍ (puntual)
                                   ▼
                               OPUS (fragmento concreto)
```

---

## Rationale

- **Sonnet 4.6 como eje central**: ofrece el equilibrio óptimo entre capacidad de razonamiento sobre código y coste de tokens. Es suficiente para el 90%+ de las PRs del día a día.
- **Haiku en el triage**: el 40-50% de las PRs en proyectos activos son cambios pequeños (renombrados, ajustes de configuración, correcciones de nombres). Resolverlos con Haiku reduce el coste total del sistema de forma significativa sin sacrificar calidad en esos casos simples.
- **No usar Opus como nivel estándar**: Opus es 5-10x más caro que Sonnet por token. Para code review la diferencia de calidad no justifica ese coste en el análisis habitual. Solo aporta valor en casos de alta ambigüedad arquitectónica.
- **Routing basado en señales objetivas** (líneas cambiadas, ficheros tocados): evita subjetividad y permite ajustar los umbrales fácilmente cuando haya datos reales de uso.
- **Sonnet en Nivel 3 en lugar de Opus**: antes de escalar a Opus, se mejora el resultado de Sonnet ampliando el contexto cargado (ARCH-HACK-001 + división de análisis en pasadas). Esto suele ser suficiente.

---

## Consequences

**Positivo:**
- Coste de tokens reducido en un ~40-50% estimado respecto a usar Sonnet para todo, gracias al triage con Haiku.
- Los umbrales de routing (150 líneas, 500 líneas) son configurables sin redeployar el agente — basta con actualizar una variable de configuración.
- El sistema es extensible: cuando exista `RULEBOOK-ANGULAR-001`, el routing detecta el lenguaje del diff y carga el Rulebook correspondiente con el mismo mecanismo.

**Negativo / Riesgos:**
- Los umbrales iniciales (150/500 líneas) son estimaciones — necesitan calibración con datos reales de PRs del proyecto WGTB.
- Un diff pequeño puede esconder una violación arquitectónica grave (ej. 5 líneas que añaden una inyección directa de repositorio en un listener). El triage de Haiku debe detectar esa señal y escalar; si no lo hace, es un falso negativo.
- La lógica de routing añade complejidad al orquestador del agente.

**Pendiente de validar:**
- Umbrales de escalado ajustados a la distribución real de tamaño de PRs en los repos BBVA objetivo.
- Coste mensual real una vez el agente esté en producción con los tres niveles activos.
- Si Haiku es suficiente para los checks de Nivel 1 o necesita reemplazarse por Sonnet en algunos casos de naming complejo.
