# Guía de Prompts para Entrenamiento y Auditoría de Agentes de IA

Este documento contiene los prompts optimizados para la generación de estándares, auditorías de código y estructuración de base de conocimiento (KDD).

---

## 1. Generación de Estándares de Código
**Objetivo:** Crear el manual de estilo para consulta de los agentes.

**Prompt:**
> Analiza mi proyecto actual y genera un archivo `docs/standards/coding-rules.md`. Este archivo debe detallar las reglas de oro del proyecto:
> - Obligatoriedad de tipado estricto en variables y funciones del frontend.
> - Límite de extensión: funciones de máximo 20-25 líneas.
> - Complejidad ciclomática: máximo 2 niveles de anidamiento (if/for).
> - Semántica: los nombres de métodos deben ser únicos y descriptivos.
> 
> Redacta el contenido en formato Markdown técnico y profesional.

---

## 2. Auditoría de Reactividad y Pipes (Angular/RxJS)
**Objetivo:** Identificar deuda técnica en flujos reactivos.

**Prompt:**
> Revisa los componentes y servicios de mi frontend. Genera un archivo `docs/analysis/reactive-patterns.md` donde identifiques:
> - Puntos donde se están usando Observables sin una desuscripción clara (falta de `takeUntil`, `unsubscribes` o `pipe async`).
> - Fragmentos de lógica repetida que podrían centralizarse en una 'Pipe' personalizada del framework.
> 
> Crea una tabla comparativa entre 'Código Actual' y 'Sugerencia de Mejora'.

---

## 3. Mapeo de Endpoints y Contratos de Datos
**Objetivo:** Definir la comunicación entre Frontend y Backend.

**Prompt:**
> Actúa como un arquitecto de software. Escanea las carpetas de servicios y modelos. Genera un archivo `docs/api/endpoints-contract.md` que liste todos los endpoints detectados, el tipo de dato que reciben (interfaces) y el que devuelven.

---

## 4. Análisis de Naming y Duplicidad
**Objetivo:** Evitar vicios de Clean Code y nombres genéricos.

**Prompt:**
> Analiza todos los métodos del proyecto. Genera un reporte en `docs/analysis/naming-audit.md` que liste:
> - Métodos con nombres duplicados en diferentes clases que hacen cosas distintas.
> - Métodos con nombres poco descriptivos (ej. 'data()', 'process()').
> 
> Propón nombres basados en Clean Code para cada caso encontrado.

---

## 5. Formato KDD (Knowledge Decomposition & Density)
**Objetivo:** Estructurar la documentación para arquitecturas KDD.

**Prompt:**
> Actúa como un Ingeniero de Conocimiento experto en arquitecturas KDD. Aplica una estructura KDD a todos los archivos .md de mi carpeta `/docs`.
> 
> Reglas de división:
> 1. **Atomicidad:** Cada archivo debe tratar un ÚNICO concepto técnico. Divídelo si es necesario.
> 2. **Densidad:** Elimina introducciones y texto de relleno. Contenido puramente técnico.
> 3. **Identificación:** Cada archivo debe incluir Metadatos (Tags, Contexto, Relacionado con).
> 4. **Jerarquía:** Organiza en `/standards`, `/api` y `/refactors`.

## 6. Testing
Analiza los archivos `.spec.ts` de la aplicación. Genera una guía en `docs/standards/testing-rules.md` que evalúe y estandarice:

- **Mocks vs Inyecciones Reales:** Verifica si las pruebas de los componentes están mockeando los servicios externos o si hacen llamadas reales/pesadas.
- **Casos de Uso Críticos:** Define que cada servicio debe tener, al menos, una prueba para el caso de éxito y otra para el `catchError`.
- Genera un ejemplo de un test unitario "perfecto" para un componente y un servicio basado en la pila tecnológica actual (Jasmine/Karma o Jest).