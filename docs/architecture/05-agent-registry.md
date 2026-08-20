# Agent Registry

Fecha: 2026-08-15

## Objetivo

Mantener un catalogo gobernado de agentes, versiones, owners, estado de release
y compatibilidad con skills, workflows, schemas, handoffs y politicas.

## Estado

Implementado como `src/ariwalabs/agent_registry.py`.

Actualmente el registro carga agentes desde:

- `agents/<agent>/agent.yaml`
- `business_packs/<pack>/agents/<agent>/agent.yaml`
- handoffs versionados en `docs/handoffs/` o
  `business_packs/<pack>/handoffs/`
- GitHub como fuente de verdad tecnica

## Reglas

- Javier, `company-director`, debe seguir siendo el unico owner y aprobador en
  el MVP.
- El registro no debe ejecutar tareas comerciales.
- Las versiones de agentes deben ser trazables en Git.
- El registro debe validar que skills, workflows, schemas, rubricas, contexto y
  handoffs declarados existan y sean compatibles.
- Un release de agente requiere aprobacion humana.

## Componentes relacionados

- `agents/*/agent.yaml`: definicion actual de agentes.
- `business_packs/*/agents/*/agent.yaml`: definiciones por pack.
- `src/ariwalabs/agent_registry.py`: catalogo gobernado de agentes.
- `src/ariwalabs/framework_validator.py`: orquestacion de validacion del
  repositorio.
- `src/ariwalabs/skill_registry.py`: validacion de skills.
- `src/ariwalabs/handoff_registry.py`: validacion de handoffs.
- `src/ariwalabs/evaluation_engine.py`: validacion de rubricas.
- `docs/agent-catalog.md`: catalogo documental.

## Implementacion relacionada

- [implementar-agent-registry.md](../implements/implementar-agent-registry.md)

- [implementar-skill-registry.md](../implements/implementar-skill-registry.md)
- [completar-validacion-handoffs.md](../implements/completar-validacion-handoffs.md)
- [evaluacion-independiente.md](../implements/evaluacion-independiente.md)

## Pendiente

- Conectar release governance con aprobaciones reales del `ApprovalEngine`.
- Decidir si la persistencia futura del registro se sincronizara a Airtable.
