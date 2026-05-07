---
id: ADR-001
type: adr
layer: adr
status: accepted
confidence: medium
version: "1.0.0"
created: 2026-05-04
updated: 2026-05-04
owner: victor-carmona
dependencies: []
tags:
  - spring-boot
  - java-8
  - java-11
  - stack-agente
  - nova
---

# ADR-001 — Lenguaje e implementación del agente HackIAdos

## Context

HackIAdos necesita un lenguaje y framework de implementación para el agente revisor de código. El agente se desplegará en el ecosistema BBVA (plataforma NOVA, Jenkins) donde ya existe expertise en Java/Spring Boot — el propio proyecto WGTB que sirve de codebase objetivo está construido en este stack.

Se valoran dos consideraciones simultáneas:

1. **Familiaridad del equipo**: el equipo ya trabaja con Java y Spring Boot en el día a día.
2. **Compatibilidad de despliegue**: distintos entornos BBVA pueden estar corriendo Java 8 o Java 11. Se quiere dar soporte a ambos si es técnicamente viable sin coste de mantenimiento excesivo.

**Alternativas evaluadas:**

| Opción | Ventajas | Inconvenientes |
|--------|----------|----------------|
| Python | Ecosistema IA muy maduro, menos verboso | Sin expertise en el equipo, ajeno a NOVA/Jenkins BBVA |
| Node.js / TypeScript | Ligero, buen soporte async | Sin expertise en equipo, ajeno a NOVA |
| **Java + Spring Boot** | Expertise existente, integración natural con NOVA | Más verboso, arranque más lento |

---

## Decision

El agente HackIAdos se implementará en **Java con Spring Boot 2.7.x**, que es la única versión de Spring Boot que soporta simultáneamente Java 8 y Java 11 como target de compilación.

**Estructura de módulos Maven:**

Se adopta un proyecto **multi-módulo Maven** con un módulo por target de Java:

```
hackiados-agent/
├── pom.xml                        ← POM padre (Spring Boot 2.7.x, gestión de deps)
├── hackiados-agent-core/          ← Lógica común (Java 11 — módulo principal)
│   └── pom.xml                    ← maven.compiler.release=11
└── hackiados-agent-java8/         ← Módulo compatible Java 8 (sin APIs Java 11+)
    └── pom.xml                    ← maven.compiler.release=8
```

**Regla de decisión sobre qué módulo desplegar:**

| Entorno destino | Módulo a desplegar |
|-----------------|--------------------|
| Java 11 o superior | `hackiados-agent-core` |
| Java 8 | `hackiados-agent-java8` |
| Si un único artefacto es suficiente | `hackiados-agent-core` (Java 11) |

Si durante el desarrollo se constata que el módulo Java 8 añade deuda de mantenimiento sin uso real en BBVA, se descarta y se continúa únicamente con Java 11.

---

## Rationale

- **Spring Boot 2.7.x** es la última versión 2.x, la única que puede compilar a Java 8 y Java 11 desde el mismo POM padre. Spring Boot 3.x requiere Java 17 mínimo, lo que excluye ambos targets.
- **Multi-módulo Maven** permite compartir la lógica de negocio del agente (parseo de diffs, aplicación de reglas del Rulebook, formateo de comentarios) en `hackiados-agent-core` y restringir en `hackiados-agent-java8` únicamente el código que debe evitar APIs introducidas en Java 9–11 (`var`, `List.of`, `Map.copyOf`, `String::strip`, etc.).
- El **módulo Java 8 no usa ninguna API de Java 9+** — la verificación se puede automatizar en CI con el flag `--release 8` que el compilador rechaza cualquier API posterior.
- **Java 11 es el target principal**: el codebase objetivo (WGTB Backend) ya corre en Java 11 y el entorno NOVA donde se desplegará el agente es compatible con Java 11. El módulo Java 8 es un añadido opcional, no el camino por defecto.

---

## Consequences

**Positivo:**
- El equipo puede desarrollar sin curva de aprendizaje en un lenguaje nuevo.
- Despliegue natural sobre la plataforma NOVA y Jenkins existentes.
- Un único POM padre mantiene alineadas las versiones de dependencias de ambos módulos.
- Si el módulo Java 8 no es necesario, se elimina sin impacto en el módulo core.

**Negativo / Riesgos:**
- Spring Boot 2.7.x está en **EOL desde noviembre de 2023** (sin actualizaciones de seguridad en la rama OSS). Requiere evaluar soporte comercial o plan de migración a Spring Boot 3.x + Java 17 cuando el ecosistema BBVA lo permita.
- Mantener dos módulos con distinta compatibilidad de Java requiere disciplina: cualquier API Java 9+ en el módulo `java8` rompe la compilación.
- Si en el futuro se requiere Java 17 (Spring Boot 3.x, Jakarta EE), la migración será necesaria.

**Deuda técnica asumida:**
- Revisar viabilidad de actualización a Spring Boot 3.x + Java 17 en cuanto NOVA soporte ese target. Crear ADR de migración cuando proceda.
