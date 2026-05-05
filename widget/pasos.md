# Guía de Implementación: Agente IA de Control de Calidad en GitLab

Este documento detalla el proceso completo para integrar un agente de Inteligencia Artificial propio dentro del flujo de CI/CD de GitLab. El objetivo es que la IA revise el código de las **Merge Requests (MR)** basándose en reglas predefinidas en archivos `.md` y reporte los errores visualmente usando el **Widget de Code Quality** de GitLab.

---

## 1. Arquitectura del Sistema

El flujo de trabajo no requiere servidores externos (es 100% *Serverless* usando los Runners de GitLab):

1.  **Trigger:** Un desarrollador crea o actualiza una Merge Request.
2.  **Contexto:** El pipeline de GitLab extrae las diferencias de código (`git diff`) y lee tus reglas de negocio (archivos `.md`).
3.  **Análisis:** Un script en Python invoca a tu Agente IA pasándole el contexto.
4.  **Formateo:** El script transforma la respuesta de la IA al formato JSON de "Code Quality" que exige GitLab.
5.  **Visualización:** GitLab lee el JSON y muestra un Widget interactivo en la MR, marcando las líneas con errores.



---

## 2. Preparación del Entorno

### A. Estructura de Archivos Recomendada
Organiza tu repositorio de la siguiente manera para mantener el orden:

```text
/
├── .gitlab-ci.yml              # Configuración del pipeline
├── rules/                      # Carpeta con tus reglas para la IA
│   ├── convenciones_codigo.md
│   ├── seguridad.md
│   └── arquitectura.md
├── scripts/
│   └── orquestador_ia.py       # Script puente entre GitLab y tu Agente
└── requirements_agent.txt      # Dependencias (ej: openai, langchain, etc.)
```

---

## 3. Configuración del Pipeline GitLab

### B. Archivo `.gitlab-ci.yml`

[Contenido del archivo de configuración aquí]

---

## 4. Script Orquestador en Python

[Contenido del script aquí]

---

## 5. Visualización y Resultados

Una vez que el pipeline finalice con éxito, GitLab transformará el JSON en los siguientes elementos visuales dentro de la Merge Request:

- **Widget Resumen:** Justo encima del botón de Merge, aparecerá un panel que indica si el Code Quality ha mejorado o degradado. Al expandirlo, se listan los errores.
- **Pestaña Code Quality:** Una pestaña dedicada en la MR con el detalle de todos los hallazgos, su ubicación y severidad.
- **Anotaciones In-Line:** En la pestaña "Changes" de la MR, aparecerá un icono de advertencia junto a la línea exacta de código señalada por la IA.

---

## 6. Recomendaciones de Prompting para la IA

Para que tu agente funcione de manera óptima, instrúyelo con las siguientes directrices:

- **Estricto con las reglas:** "Si el código analizado NO viola explícitamente ninguna de las reglas proporcionadas en los archivos .md, devuelve una lista vacía. No apliques criterios subjetivos externos."
- **Precisión en líneas:** "Identifica la línea del error basándote estrictamente en los encabezados del Git Diff (ej. `@@ -10,5 +10,6 @@`)."
- **Salida Estructurada:** Exige a la IA que responda siempre en un formato JSON puro (o un esquema que tu script de Python pueda parsear) que incluya: archivo, línea, mensaje y severidad.