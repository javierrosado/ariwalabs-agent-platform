# Formalizar schemas comunes del Core

Fecha: 2026-08-21

## Objetivo

Implementar el item P4.1 para que los contratos estructurales del Core
Framework vivan en `shared/schemas/core/` y sean reutilizados por los
validadores/runtime sin duplicar reglas de dominio.

## Alcance implementado

- Se agrego `CoreSchemaValidator` en `src/ariwalabs/schema_validator.py`.
- Se crearon schemas core para agentes, skills, workflows, business packs,
  handoffs, approvals y artifacts.
- `BusinessPackRegistry`, `AgentRegistry`, `SkillRegistry` y `HandoffRegistry`
  validan estructura contra schemas core.
- `AgentRegistry` valida tambien los workflows declarados por cada agente.
- `ApprovalEngine` y `ArtifactManager` validan records locales antes de
  persistirlos.
- Las reglas semanticas existentes permanecen en los componentes Python.

## Decisiones

- Mantener `shared/schemas/handoff.schema.json` por compatibilidad historica y
  usar `shared/schemas/core/handoff.schema.json` como contrato core nuevo.
- No usar referencias externas entre schemas por ahora; `common.schema.json`
  documenta definiciones comunes y se evitara resolver referencias multiarchivo
  hasta que sea necesario.
- Permitir campos existentes del business pack como `core_framework`,
  `domain_boundaries`, `pending_extraction` y `domain_assets.operations`.

## Pruebas

- Tests focalizados de `CoreSchemaValidator`, Agent Registry, Skill Registry,
  Handoff Registry, Business Pack Registry, Approval Engine y Artifact Manager.
- Suite completa del protocolo al cierre del incremento.

## Siguiente paso

Continuar P4 con `Conectar Agent Registry con approvals reales`.
