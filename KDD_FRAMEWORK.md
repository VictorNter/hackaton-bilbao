# KDD Framework — Referencia Operativa para HackIAdos

> **Qué es este fichero:** Resumen operativo del Knowledge-Driven Development (KDD v2) adaptado al proyecto HackIAdos.
> Léelo al inicio de cualquier sesión en la que vayas a crear o revisar specs.
> No es el framework completo — es lo que necesitas saber para trabajar.
> Última actualización: 04 Mayo 2026

---

## 1. Qué es KDD en una frase

Una metodología donde **las especificaciones son el artefacto principal** que guía el trabajo.
En lugar de documentación dispersa o conocimiento en la cabeza de las personas, cada decisión, regla de dominio y restricción arquitectónica vive como un fichero `.md` versionado, pequeño y legible por agentes IA.

**Versión del kit en uso:** KDD v2 (Bruzos, abril 2026).

---

## 2. Los tres tipos de artefacto

| Tipo | Para qué | Persiste | Ejemplos en este proyecto |
|------|----------|----------|--------------------------|
| **Knowledge** | Lo que el sistema *sabe* — conocimiento funcional y técnico | Sí — entre fases | Lógica del Quality Gate, actores, reglas del Rulebook |
| **Work** | Lo que el equipo *hace* — efímero, por fase | No — se archiva al terminar | Análisis de viabilidad, plan de implementación |
| **Governance** | Decisiones tomadas y por qué | Sí — referencia histórica | "Usamos GitHub App vs PAT", "Lenguaje del agente: X" |

---

## 3. Los tipos de spec y su ID

### Knowledge Artifacts (persistentes)

| Tipo | ID Pattern | Para qué |
|------|-----------|----------|
| Architecture | `ARCH-HACK-NNN` | Decisiones de tecnología, patrones, stack, integraciones |
| Domain | `DOM-HACK-NNN` | Actores, roles, entidades, reglas de negocio |
| Product | `PROD-HACK-NNN` | Flujos de usuario end-to-end, visión de producto |
| Feature | `FEAT-HACK-NNN` | Funcionalidad concreta, comportamientos, criterios de aceptación |
| Documentation | `DOC-HACK-NNN` | Guías, runbooks, referencia operativa |

### Work Artifacts (efímeros)

| Tipo | ID Pattern | Para qué |
|------|-----------|----------|
| WRK-SPEC | `WRK-SPEC-NNN` | Qué hay que cambiar y por qué |
| WRK-PLAN | `WRK-PLAN-NNN` | Cómo se va a implementar |
| WRK-TASK | `WRK-TASK-NNN` | Tarea atómica de implementación |

Jerarquía: `WRK-TASK → (parent) → WRK-PLAN → (parent) → WRK-SPEC`

### Governance Artifacts (bridge)

| Tipo | ID Pattern | Para qué | Lifecycle |
|------|-----------|----------|-----------|
| ADR | `ADR-NNN` | Decisión tomada — contexto, rationale y consecuencias | proposed → accepted → superseded |
| RFC | `RFC-NNN` | Propuesta de cambio antes de formalizar | draft → discussion → accepted / rejected |
| RULE | `RULE-NNN` | Restricción que debe enforcearse automáticamente en CI | active → deprecated |

> ⚠️ **RULE en HackIAdos:** cada entrada del Rulebook que supere la fase de validación se convierte en un `RULE-NNN`. Esto cierra el ciclo spec → agente → enforcement automático.

---

## 4. Anatomía de un spec — el frontmatter

Todo fichero `.md` empieza con este bloque YAML entre `---`. Es lo que permite al agente navegar sin leer todo.

### Para Knowledge y Work specs

```yaml
---
id: FEAT-HACK-001                        # ID único · patrón TYPE-AREA-NNN
type: spec                               # "spec" para Knowledge y Work artifacts
layer: feature                           # architecture | domain | product | feature | documentation
                                         # Para Work: work-spec | work-plan | work-task
domain: AI Code Review                   # dominio funcional del área
subdomain: Quality Gate                  # subdominio
status: draft                            # draft | active | deprecated (Knowledge)
                                         # draft | active | completed | archived (Work)
confidence: low                          # high | medium | low — solo en Knowledge specs
version: "0.1.0"                         # semver · siempre entre comillas
created: 2026-05-04
updated: 2026-05-04
owner: victor-carmona
reviewers:
  - pablo-martinez
  - lourdes-pozo
dependencies:
  - id: ARCH-HACK-001
    relation: implements                 # ver tabla de relaciones abajo
tags:
  - quality-gate
  - github-app
  - code-review
---
```

### Para Governance specs (ADR / RFC / RULE)

> ⚠️ **Diferencia crítica v2:** los ADRs usan `type: adr` y `layer: adr`, NO `type: spec`.

```yaml
---
id: ADR-001
type: adr                                # "adr" | "rfc" | "rule" — NO "spec"
layer: adr                               # debe coincidir con el type
status: accepted                         # proposed | accepted | superseded
confidence: high
version: "1.0.0"
created: 2026-05-04
updated: 2026-05-04
owner: victor-carmona
dependencies:
  - id: ARCH-HACK-001
    relation: depends-on
tags:
  - github-app
  - arquitectura
---
```

### Tabla de relaciones entre specs

| Relación | Cuándo usarla | Ejemplo en HackIAdos |
|----------|---------------|----------------------|
| `implements` | Este spec aplica un patrón del otro | FEAT-HACK-001 → ARCH-HACK-001 |
| `constrained-by` | Debe respetar restricciones del otro | DOM-HACK-001 → ARCH-HACK-001 |
| `extends` | Añade detalle al otro del mismo nivel | FEAT-HACK-003 → FEAT-HACK-001 |
| `uses-data-from` | Consume datos o entidades del otro | FEAT-HACK-001 → DOM-HACK-001 |
| `activates` | Solo Work: qué Knowledge cargar como contexto | WRK-TASK → FEAT-HACK-001 |
| `depends-on` | Solo Work: secuencia entre tareas | WRK-TASK-002 → WRK-TASK-001 |
| `parent` | Solo Work: jerarquía | WRK-TASK → WRK-PLAN |
| `supersedes` | Este spec reemplaza al anterior | ADR-003 → ADR-001 |

### Niveles de confidence

| Nivel | Significado | Cuándo usarlo |
|-------|-------------|---------------|
| `high` | Validado por los tres miembros del equipo | Tras revisión conjunta Víctor + Pablo + Lourdes |
| `medium` | Validado por al menos dos miembros | Cuando dos de los tres han revisado y dado OK |
| `low` | Capturado de conversación, pendiente validar | Primer borrador — empieza siempre aquí |

> **Regla práctica:** empieza siempre en `low`. Un spec `high` con `status: active` es el que el agente puede usar como contexto sin supervisión adicional.

---

## 5. Estructura de secciones del cuerpo

Después del frontmatter, cada spec sigue esta estructura. No todas las secciones son obligatorias en todos los tipos.

```markdown
## Intent
Qué define este spec y por qué existe. Una o dos frases.

## Definition
El contenido core. Varía según el tipo:
- Feature:      Contexto → Actores → Flujo → Modelo de datos → Fuera de alcance
- Domain:       Concepto → Actores/Entidades → Reglas → Restricciones
- Architecture: Context → Decision → Rationale → Consequences
- ADR:          Context → Decision → Rationale → Consequences

## Acceptance Criteria
- [ ] Criterio verificable 1
- [ ] Criterio verificable 2
(Para FEAT specs: formato Dado/Cuando/Entonces)

## Evidence
Qué valida este spec (revisiones, tests, sign-offs, referencias)

## Traceability
Links a otros specs, código, tests, ADRs
```

---

## 6. Estructura de carpetas del repositorio

```
hackIAdos/
├── PROJECT_CONTEXT.md              ← contexto del proyecto · siempre actualizado
├── KDD_FRAMEWORK.md                ← este fichero
├── SPEC-INDEX.md                   ← catálogo global con estado y dependencias
├── README.md                       ← punto de entrada
│
├── specs/
│   ├── feature/                    ← FEAT-HACK-NNN
│   │   (Quality Gate logic, auto-corrección, webhook handling, notificaciones…)
│   ├── domain/                     ← DOM-HACK-NNN
│   │   (Actores: PR author, reviewer, tech lead; entidades: PR, diff, violation, suggestion…)
│   └── architecture/               ← ARCH-HACK-NNN
│       (GitHub App, Artifactory, stack del agente, modelo IA, integración Google Chat…)
│
├── adrs/                           ← ADR-NNN
│   (Lenguaje del agente, modelo IA elegido, estrategia legacy code, GitHub App vs PAT…)
│
├── work/                           ← WRK-* (efímeros)
│
├── rulebooks/                      ← Libros de Reglas por tecnología
│   (RULEBOOK-ANGULAR-001.md, RULEBOOK-SPRING-001.md…)
│
└── agents/
    └── code-reviewer/
        └── SKILL.md                ← skill del agente revisor (tras specs en active)
```

---

## 7. Rulebooks — especificidad de HackIAdos

Los **Rulebooks** son ficheros `.md` en `rulebooks/` que el agente carga como contexto al analizar una PR.
Son Knowledge artifacts de tipo `documentation` con frontmatter estándar.

**Estructura de una regla dentro de un Rulebook:**

```markdown
### [RULE-ANG-001] Nombre de componentes en PascalCase
**Severidad:** 🔴 Crítico
**Aplica a:** Clases nuevas — NO aplica a modificaciones de clases existentes
**Quality Gate:** Rojo si falla en código nuevo. Warning si falla en legacy modificado.
**Descripción:** ...
**Ejemplo incorrecto:** ...
**Ejemplo correcto:** ...
**Auto-corrección:** [bloque de código corregido para adjuntar en la PR]
```

**Tabla de severidades:**

| Severidad | Quality Gate | Código Nuevo | Legacy Modificado |
|-----------|-------------|--------------|-------------------|
| 🔴 Crítico (seguridad/arquitectura) | Rojo — bloquea merge | Bloquea | Bloquea si es fallo nuevo |
| 🔴 Crítico (estilo/calidad) | Rojo — bloquea merge | Bloquea | Warning — no bloquea |
| 🟡 Warning (deuda técnica) | Amarillo — permite avance | Sí | Sí (educativo) |
| 🔵 Info | Verde — sugerencia | Sí | Sí |

> **Regla de Oro del Legacy:** si el desarrollador toca un método existente, la IA aplica Warnings educativos.
> Solo bloquea si el cambio introduce un fallo crítico de seguridad nuevo (no heredado).

---

## 8. Reglas de trabajo

**Regla 1 — Una sesión, un objetivo.**
Cada sesión tiene un objetivo claro antes de empezar. Ejemplos: *"Escribir ADR-001 sobre elección de lenguaje"*, *"Definir FEAT-HACK-001 Quality Gate logic"*. No mezclar estrategia con ejecución.

**Regla 2 — Cada sesión termina con un `.md` commiteado.**
Si la conversación no produce un fichero que va al repositorio, la sesión no ha valido. El fichero es el "guardar". El historial del chat no lo es.

**Regla 3 — PROJECT_CONTEXT.md es un fichero vivo.**
Cada vez que se toma una decisión relevante, se actualiza PROJECT_CONTEXT.md. Es lo primero que cualquier agente lee en cada sesión nueva.

**Regla 4 — La Regla de Oro del Legacy es invariante.**
Todo spec, feature y rulebook deben documentar explícitamente el comportamiento diferencial para código nuevo vs. código legacy modificado. Es la invariante más crítica del sistema.

---

## 9. Orden de trabajo — estado actual (Mayo 2026)

| Prioridad | Fichero | Tipo | Estado | Desbloquea |
|-----------|---------|------|--------|------------|
| 🔴 Alta | ADRs iniciales (lenguaje agente, modelo IA, GitHub App vs PAT) | ADR | ⏳ Pendiente | Arrancar architecture specs |
| 🔴 Alta | `ARCH-HACK-001` stack técnico del agente | Architecture | ⏳ Pendiente | Todo lo demás |
| 🟡 Media | `DOM-HACK-001` actores y entidades | Domain | ⏳ Pendiente | Feature specs |
| 🟡 Media | `FEAT-HACK-001` Quality Gate logic (Green/Yellow/Red) | Feature | ⏳ Pendiente | Agent SKILL |
| 🟡 Media | `FEAT-HACK-002` Legacy Code Rule (Regla de Oro) | Feature | ⏳ Pendiente | Rulebooks |
| 🟡 Media | Primer Rulebook (`RULEBOOK-ANGULAR-001` o `RULEBOOK-SPRING-001`) | Documentation | ⏳ Pendiente | Validación del sistema |
| 🟢 Baja | `agents/code-reviewer/SKILL.md` | Agent skill | ⏳ Pendiente | Tras specs en status: active |

---

## 10. Niveles de adopción KDD — dónde estáis

| Nivel | Nombre | Qué implica | Estado |
|-------|--------|-------------|--------|
| **L1** | Document | Escribir specs en Markdown con frontmatter YAML | ← **Aquí ahora** |
| **L2** | Validate | Ejecutar `spec-graph validate` en CI | Próximo |
| **L3** | Automate | Generar boilerplate desde specs | Futuro |
| **L4** | Generate | Agentes consumen specs como contexto para revisar PRs | Objetivo del proyecto |
| **L5** | Orchestrate | Agentes activan conocimiento automáticamente vía webhook | Objetivo 2027+ |

---

## 11. Cómo usa el agente los specs — activación contextual

El agente no lee todos los ficheros. El flujo al recibir un webhook de PR es:

1. Lee `SPEC-INDEX.md` para localizar specs relevantes
2. Detecta el lenguaje/stack del diff → carga el Rulebook correspondiente
3. Carga specs de `activates` del Work artifact activo (activación explícita)
4. Expande transitivamente por el grafo de dependencias
5. Filtra los deprecated
6. Ajusta al presupuesto de contexto según el tipo de análisis

**Presupuesto de contexto:**

| Tipo de análisis | Specs que carga |
|------------------|----------------|
| PR pequeña (< 200 líneas) | 2–5 specs + 1 Rulebook |
| PR mediana (200–500 líneas) | 3–7 specs + 1–2 Rulebooks |
| PR grande (> 500 líneas) | 5–10 specs + Rulebooks relevantes |

**Regla de oro:** 5 specs enfocados > 20 specs relacionados vagamente.

---

## 12. Herramientas de KDD v2

### CLI spec-graph

```bash
# Validar integridad — ejecutar antes de cada sesión
node spec-graph.mjs --specs ./specs validate

# Ver métricas del repositorio
node spec-graph.mjs --specs ./specs stats

# Impacto de cambiar un spec
node spec-graph.mjs --specs ./specs impact FEAT-HACK-001

# Encontrar specs sin conexiones (posible dependencia olvidada)
node spec-graph.mjs --specs ./specs orphans

# Filtrar specs por criterio
node spec-graph.mjs --specs ./specs filter --confidence low --status draft
```

### Plugin para Claude Code (`kdd-toolkit/`)

| Comando | Qué hace |
|---------|----------|
| `/kdd:spec-validate` | Valida integridad del repositorio — refs rotas, ciclos, frontmatter incompleto |
| `/kdd:spec-impact FEAT-HACK-001` | Qué specs se ven afectados si cambias ese spec |
| `/kdd:spec-context "quality gate"` | Encuentra specs relevantes para una tarea en lenguaje natural |
| `/kdd:spec-create "spec de Quality Gate"` | Crea un spec desde lenguaje natural |
| `/kdd:spec-consolidate WRK-SPEC-001` | Captura conocimiento tras terminar un trabajo |

---

*Mantener vivo: actualizar la sección 9 (orden de trabajo) conforme avance el proyecto.*
