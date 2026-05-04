# HackIAdos: AI Code Reviewer & Quality Gate 2.0

> Repositorio de conocimiento del proyecto HackIAdos.
> Punto de entrada para cualquier sesión. Leer también: **PROJECT_CONTEXT.md** y **KDD_FRAMEWORK.md**

---

## Qué es este repositorio

Base de conocimiento estructurada siguiendo la metodología **KDD v2** (Knowledge-Driven Development).
Contiene las especificaciones funcionales, decisiones de arquitectura y guías operativas del agente
**HackIAdos**, un revisor de código IA con Quality Gate para entornos GitHub Enterprise.

---

## Ficheros clave

| Fichero | Para qué |
|---------|----------|
| [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) | Contexto del proyecto, equipo, stack, fases y estado actual — **leer siempre primero** |
| [KDD_FRAMEWORK.md](KDD_FRAMEWORK.md) | Reglas del juego: cómo se escriben y relacionan los specs |
| [SPEC-INDEX.md](SPEC-INDEX.md) | Catálogo global de artefactos con estado y confianza |

---

## Estructura del repositorio

```
hackIAdos/
├── PROJECT_CONTEXT.md          ← contexto vivo del proyecto
├── KDD_FRAMEWORK.md            ← referencia operativa KDD v2
├── SPEC-INDEX.md               ← catálogo global
│
├── specs/
│   ├── feature/                ← FEAT-HACK-NNN  comportamientos y criterios
│   ├── domain/                 ← DOM-HACK-NNN   actores, entidades, reglas
│   └── architecture/           ← ARCH-HACK-NNN  stack, patrones, decisiones técnicas
│
├── adrs/                       ← ADR-NNN  decisiones formalizadas
├── work/                       ← WRK-*    análisis y planes efímeros
├── rulebooks/                  ← Libros de Reglas por tecnología (Angular, Spring Boot…)
└── agents/
    └── code-reviewer/          ← SKILL.md del agente revisor
```

---

## Equipo

| Persona | Rol |
|---------|-----|
| Víctor Carmona Torres | — |
| Pablo Martínez | — |
| Lourdes Pozo | — |

---

## Estado actual

> Ver sección **Estado del Repositorio** en [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
