# AriwaLabs Training Pack

Fecha: 2026-08-15

## Objetivo

Declarar la frontera de dominio AriwaLabs Training con activos fisicos propios
para validacion y ejecucion mediante `business_pack_id`.

Este pack separa lo que pertenece al framework generico de lo que pertenece al
negocio de capacitaciones de AriwaLabs.

## Core framework reutilizable

El core generico esta compuesto por:

- `src/ariwalabs/runtime.py`
- `src/ariwalabs/skill_registry.py`
- `src/ariwalabs/handoff_registry.py`
- `src/ariwalabs/workflow_engine.py`
- `src/ariwalabs/context_engine.py`
- `src/ariwalabs/model_gateway.py`
- `src/ariwalabs/tool_gateway.py`
- `src/ariwalabs/approval_engine.py`
- `src/ariwalabs/evaluation_engine.py`
- `src/ariwalabs/artifact_manager.py`
- `src/ariwalabs/audit.py`
- `src/ariwalabs/repository.py`
- `adapters/`

## Activos de dominio AriwaLabs

El dominio AriwaLabs Training usa actualmente:

- `business_packs/ariwalabs-training/agents/growth-marketing-agent/`
- `business_packs/ariwalabs-training/agents/framework-agent/`
- `business_packs/ariwalabs-training/context/*.yaml`
- `business_packs/ariwalabs-training/policies/ariwalabs-training-policy.yaml`
- `business_packs/ariwalabs-training/handoffs/growth-marketing-handoffs.*`
- `framework/policies/core-agent-policy.yaml`
- `docs/architecture/19-airtable-tables.md`
- `adapters/airtable/schema.py`

## Estado

Este pack es un manifest activo para validacion y ejecucion mediante
`business_pack_id`. Sus activos reales viven dentro de
`business_packs/ariwalabs-training/`.

## Pendiente

- Implementar `Agent Registry` multipack.
- Migrar gradualmente referencias documentales historicas.
