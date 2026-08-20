# AriwaLabs Agent Platform

## Mision del repositorio

Este repositorio contiene la plataforma local, versionada y gobernada para
definir, validar y ejecutar agentes de AriwaLabs. La meta inicial es madurar un
framework multiagente para capacitacion en IA y, luego, consultoria derivada de
la comunidad formada por esas capacitaciones.

## Reglas no negociables

- Javier, `company-director`, es el unico operador y aprobador.
- GitHub debe ser la fuente de verdad tecnica; este checkout debe mantenerse
  bajo control de versiones.
- El MVP usa VS Code, Python venv local y ejecucion local. No introducir Docker.
- Airtable sera el sistema operacional inicial. No usar SQLite en el MVP.
- Los secretos viven en `.env`; nunca deben versionarse.
- Los modelos se consumen por perfiles logicos mediante Model Gateway.
- Ninguna skill debe acoplarse a un modelo concreto.
- Ninguna skill llama directamente a Airtable, OpenAI, WhatsApp, LinkedIn u otra
  API externa.
- Toda integracion pasa por `adapters/` o por el futuro Tool Gateway.
- El contexto empresarial default vive en `shared/context/`; el contexto de
  cada business pack vive en `business_packs/<pack>/context/`. No duplicarlo
  dentro de prompts, skills o workflows.
- El Framework Agent gobierna agentes; no ejecuta tareas comerciales.
- El Growth & Marketing Agent no publica, no envia mensajes externos, no compra
  publicidad, no contacta empresas y no registra oportunidades sin aprobacion.

## Lectura obligatoria antes de cualquier tarea

1. Leer este archivo.
2. Leer `docs/current-state.md`.
3. Leer `docs/project-context.md`.
4. Leer el ADR relacionado en `docs/architecture-decisions/`.
5. Leer el agente, skill, workflow, schema, adapter o componente afectado.
6. Revisar `docs/implementation-backlog.md`.
7. Declarar archivos a tocar y pruebas a ejecutar.

## Que leer segun la tarea

- Contexto de negocio: `docs/project-context.md`, `shared/context/*.yaml`.
- Politicas: `framework/policies/core-agent-policy.yaml`,
  `business_packs/*/policies/*.yaml` y compatibilidad historica en
  `shared/policies/global-agent-policy.yaml`.
- Estado real y deuda: `docs/current-state.md`, `docs/implementation-backlog.md`.
- Arquitectura: `docs/architecture/01-framework-overview.md` y ADRs.
- Business packs: `business_packs/*/pack.yaml` y docs del pack.
- Agentes: `docs/agent-catalog.md`, `agents/*/agent.yaml`.
- Skills: `agents/<agent>/skills/*/skill.yaml` y schemas del agente.
- Workflows: `agents/<agent>/workflows/*.yaml`.
- Handoffs: `docs/handoff-catalog.md`, `docs/handoffs/`.
- Runtime y CLI: `src/ariwalabs/`.
- Integraciones: `adapters/` y docs del adapter correspondiente.
- Prompts operativos: `prompts/codex/`.
- Validacion: `tests/`, `.github/workflows/validate.yml`, `.vscode/tasks.json`.

## Rutas principales

- `src/ariwalabs/`: CLI, runtime, validador, auditoria y persistencia local.
- `agents/`: definiciones, prompts, skills, schemas y workflows de agentes.
- `shared/context/`: fuente de verdad empresarial compartida del modo default.
- `shared/policies/`: reglas globales historicas del modo default.
- `framework/policies/`: politicas core reutilizables.
- `business_packs/*/context/`: contexto de dominio por pack.
- `business_packs/*/policies/`: politicas de dominio por pack.
- `shared/schemas/`: contratos comunes futuros.
- `shared/templates/`: plantillas comunes futuras.
- `adapters/`: contratos de integraciones externas.
- `business_packs/`: manifests y documentacion de dominios reutilizables.
- `docs/`: contexto persistente, arquitectura, decisiones, estado y backlog.
- `examples/`: requests de ejemplo.
- `tests/`: pruebas unitarias e integracion.
- `runtime/`: datos locales no versionados.

## Protocolo antes de modificar codigo

- Confirmar el alcance contra documentacion y codigo real.
- Identificar si el cambio toca framework, agente, skill, workflow, schema,
  adapter, prompt o docs.
- Revisar contratos existentes y evitar crear APIs paralelas.
- Mantener aprobacion humana cuando exista impacto externo o comercial.
- Evitar refactors amplios si la tarea no los requiere.

## Protocolo despues de modificar codigo

- Ejecutar, como minimo:

```bash
ariwalabs framework validate-repository --root .
ruff check .
mypy src
pytest
```

- Actualizar documentacion afectada.
- Actualizar `docs/current-state.md` si cambia el estado real.
- Anadir una entrada append-only en `docs/session-log.md`.
- Reportar deuda tecnica, riesgos y siguiente paso recomendado.

## Politica de aprobaciones

Toda accion externa, publicacion, mensaje, presupuesto, registro de oportunidad,
uso de nombre de cliente, despliegue productivo o release requiere aprobacion de
Javier. El runtime actual conserva las ejecuciones en estado
`pending_human_approval`; el Approval Engine completo aun no esta implementado.

## Validaciones actuales

La validacion existente comprueba presencia basica de agentes, contexto, skills
y workflows declarados. Todavia no valida contratos completos, schemas
detallados, handoffs, herramientas, aprobaciones ni compatibilidad semantica.
