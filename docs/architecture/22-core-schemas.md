# Core Schemas

Fecha: 2026-08-21

## Objetivo

Definir contratos JSON Schema comunes para las entidades estructurales del Core
Framework sin acoplarlos al dominio AriwaLabs Training.

## Estado

Implementado para el alcance P4.1. Los contratos viven en
`shared/schemas/core/` y son aplicados por `CoreSchemaValidator` desde
registries y gestores runtime.

## Contratos

- `agent.schema.json`: estructura base de `agent.yaml`.
- `skill.schema.json`: estructura base de `skills/*/skill.yaml`.
- `workflow.schema.json`: estructura base de `workflows/*.yaml`.
- `business-pack.schema.json`: estructura base de `business_packs/*/pack.yaml`.
- `handoff.schema.json`: estructura base de archivos de handoffs.
- `approval.schema.json`: record local de approvals.
- `artifact.schema.json`: record local de artifacts.
- `common.schema.json`: definiciones comunes documentales para ids, versiones,
  roles, paths y perfiles de modelo.

## Regla de separacion

Los schemas validan estructura, tipos, enums y propiedades permitidas. Las
reglas que dependen del repositorio o del dominio siguen en Python:

- existencia de archivos declarados;
- ids duplicados;
- coincidencia de `agent.id` con carpeta;
- rutas permitidas de contexto;
- owner esperado por business pack;
- release governance;
- tools permitidas/prohibidas;
- bloqueo de acciones externas.

## Implementacion relacionada

- [formalizar-schemas-core.md](../implements/formalizar-schemas-core.md)
