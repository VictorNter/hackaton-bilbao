---
id: RULE-BOOT-dir-structure
type: governance
layer: rule
title: Estructura de directorios canónica para microservicios wgtb
status: active
confidence: low
version: 0.1.0
owner: platform
tags:
  - structure
  - conventions
  - onboarding
dependencies:
  - id: ARCH-BOOT-001
    type: constrained-by
generated-by: kdd-studio
generated-at: '2026-05-06T20:20:58.457Z'
source: (creación de specs)
---

# Estructura de directorios canónica para microservicios wgtb

## Purpose
Establece la estructura de directorios obligatoria para todos los microservicios que sigan el patrón wgtbBackend, garantizando que cada módulo funcional respete las tres capas de arquitectura hexagonal (application, domain, infrastructure) con sus subcarpetas canónicas.

## Definition
Todo módulo funcional bajo `src/main/java/com/bbva/<uuaa>/<servicio>/` debe seguir este árbol:

```
<módulo>/
  application/
    I<Nombre>Service.java        ← interfaz de servicio
    impl/
      <Nombre>ServiceImpl.java   ← implementación
  domain/
    entity/
      <Entidad>.java             ← entidades con persistencia
      nodatabase/
        <Tipo>.java              ← value objects / enums sin persistencia
  infrastructure/
    listener/
      Listener<Nombre>.java      ← entrada de mensajes/eventos
    mapper/
      <Nombre>DtoMapper.java     ← transformación DTO ↔ dominio
    repository/
      I<Nombre>Repository.java   ← interfaz de repositorio
      impl/
        <Nombre>RepositoryImpl.java
      jpa/
        <Nombre>Jpa.java
        <Nombre>RepositoryJpa.java
        mapper/
          <Nombre>Mapper.java
```

Carpetas transversales obligatorias en la raíz del servicio:
- `exception/` — jerarquía de excepciones propias
- `utils/` — utilidades compartidas (autentication, converter, jsonParser, mapper)
- `resources/apis/` — contratos OpenAPI de APIs publicadas
- `resources/consumed/` — contratos OpenAPI de APIs consumidas

El árbol de tests bajo `src/test/` debe replicar exactamente la estructura de `src/main/`, con sufijo `Test` en cada clase.

## Acceptance Criteria
- [ ] Cuando un PR introduce un módulo nuevo bajo `src/main/java/.../<servicio>/`, el pipeline rechaza el PR si alguna de las carpetas `application/`, `domain/entity/`, `infrastructure/` está ausente en ese módulo.
- [ ] Cuando un PR añade una clase de servicio en `application/` sin su interfaz `I<Nombre>Service.java` en el mismo paquete, el pipeline rechaza el PR.
- [ ] Cuando un PR añade una clase de repositorio en `infrastructure/repository/` sin la interfaz correspondiente `I<Nombre>Repository.java`, el pipeline rechaza el PR.
- [ ] Cuando un módulo nuevo no incluye subcarpeta `jpa/` bajo `infrastructure/repository/`, el pipeline emite un aviso de incumplimiento y bloquea el merge.
- [ ] Cuando en code review se detecta una clase de dominio con persistencia JPA fuera de `domain/entity/`, el revisor rechaza el PR indicando el criterio incumplido.
- [ ] Cuando en code review se detecta una clase de test cuyo paquete no replica el paquete de producción correspondiente, el revisor rechaza el PR.
- [ ] Cuando `src/main/resources/apis/` no contiene al menos un contrato OpenAPI para el módulo publicado, el pipeline rechaza el despliegue a entornos no locales.

## Evidence
| Type | Reference | Date | Confidence impact |
|------|-----------|------|-------------------|
| Árbol de directorios | wgtbBackend tree (aportado por usuario) | 2025-01-30 | Initial |
| Spec activa | ARCH-BOOT-001 | 2025-01-30 | Reused |

## Traceability
| Relation | Target | Description |
|----------|--------|-------------|
| constrained-by | ARCH-BOOT-001 | La arquitectura hexagonal del microservicio define las capas que esta regla hace cumplir |
