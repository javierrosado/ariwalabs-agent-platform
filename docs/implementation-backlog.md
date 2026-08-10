# Implementation Backlog

## P0 - Cerrado

Estado general: cerrado el 2026-08-08.

- Preparar entorno Python dev local.
  - Estado: implementado el 2026-08-08; Javier confirmo que `.venv`,
    instalacion editable con dependencias dev y validaciones base corren
    correctamente.
  - Aceptacion: existe `.venv`, `pip install -e ".[dev]"` finaliza correctamente,
    y corren `ariwalabs`, `pytest`, `ruff` y `mypy`.
  - Dependencias: Python con `pip` o mecanismo equivalente de entorno virtual.
- Completar schemas de skills.
  - Estado: implementado el 2026-07-24 en
    `agents/*/schemas/*.schema.json`.
  - Aceptacion: cada output schema define campos requeridos, tipos, errores y
    `additionalProperties: false` donde corresponda.
  - Dependencias: contratos de outputs esperados por workflow.
- Implementar Skill Registry.
  - Estado: implementado el 2026-07-24 como `src/ariwalabs/skill_registry.py`.
  - Aceptacion: valida ids, versiones, schemas, tools, aprobaciones y ownership.
  - Dependencias: formato canonico de skill.
- Completar validacion de handoffs.
  - Estado: implementado el 2026-07-24 como `src/ariwalabs/handoff_registry.py`.
  - Aceptacion: contratos de productor/consumidor, aprobacion, persistencia,
    errores e idempotencia validados automaticamente.
  - Dependencias: `docs/handoff-catalog.md` y schema comun.

## P1 - Cerrado

Estado general: cerrado el 2026-08-08.

- Completar Workflow Engine.
  - Estado: implementado el 2026-07-25 como `src/ariwalabs/workflow_engine.py`.
  - Aceptacion: interpreta pasos, paralelismo, condiciones, acciones y estados.
  - Dependencias: Skill Registry, schemas y runtime de ejecucion.
- Implementar Approval Engine.
  - Estado: implementado el 2026-07-25 como `src/ariwalabs/approval_engine.py`.
  - Aceptacion: crea, lista, aprueba, rechaza y audita checkpoints.
  - Dependencias: CLI de aprobaciones y repositorio.
- Implementar CLI de aprobaciones.
  - Estado: implementado el 2026-07-25 en `src/ariwalabs/cli.py`.
  - Aceptacion: Javier puede ver pendientes y decidir con razon registrada.
  - Dependencias: Approval Engine.
- Implementar Artifact Manager.
  - Estado: implementado el 2026-07-25 como `src/ariwalabs/artifact_manager.py`.
  - Aceptacion: registra artefactos con metadata, origen, version y estado.
  - Dependencias: repositorio local y futura tabla `Artifacts`.
- Implementar Audit Log completo.
  - Estado: implementado el 2026-07-25 como `src/ariwalabs/audit.py`.
  - Aceptacion: eventos de ejecucion, validacion, approval, artifact, error y
    costos quedan en JSONL sin secretos.
  - Dependencias: runtime y gateways.
- Implementar Airtable Adapter.
  - Estado: implementado el 2026-07-25 en `adapters/airtable/`.
  - Aceptacion: read/create/update draft con errores tipados, retries,
    rate-limit handling e idempotencia.
  - Dependencias: diseno de tablas.
- Disenar tablas de Airtable.
  - Estado: implementado el 2026-07-26 en
    `docs/architecture/airtable-tables.md`.
  - Aceptacion: campos, relaciones, claves externas y reglas de privacidad para
    People, Organizations, TrainingPrograms, Cohorts, Enrollments, Campaigns,
    ContentItems, Events, Referrals, Opportunities, Approvals,
    AgentExecutions y Artifacts.
  - Dependencias: contexto de negocio y approvals.
- Implementar Model Gateway.
  - Estado: implementado el 2026-07-26 como `src/ariwalabs/model_gateway.py`.
  - Aceptacion: enruta perfiles `reasoning`, `generation`, `evaluation` y
    `fast_structured` sin acoplar skills a modelos.
  - Dependencias: contrato `ModelAdapter` y configuracion.
- Integrar modelos OpenAI.
  - Estado: implementado el 2026-08-08 en `adapters/models/openai.py`.
  - Aceptacion: provider configurable por `.env`, sin secretos en logs.
  - Dependencias: Model Gateway.
- Structured outputs.
  - Estado: implementado el 2026-08-08 en `ModelGateway`, `WorkflowEngine` y
    `AgentRuntime`.
  - Aceptacion: outputs validados contra JSON Schema y errores recuperables.
  - Dependencias: schemas estrictos y Model Gateway.
- Pruebas de regresion.
  - Estado: implementado el 2026-08-08 con fixtures en
    `tests/fixtures/regression/growth/`.
  - Aceptacion: fixtures para campana, bootcamp, journey y oportunidad.
  - Dependencias: Workflow Engine y schemas.

## P2 - Siguiente incremento

- Evaluacion independiente.
  - Aceptacion: rubricas por skill y evaluador separado de generacion.
  - Dependencias: Model Gateway y schemas.
- Control de idempotencia.
  - Estado: implementado el 2026-08-10 en `src/ariwalabs/idempotency.py` y
    `AgentRuntime`.
  - Aceptacion: requests repetidos no duplican approvals, opportunities ni
    artifacts.
  - Dependencias: llaves de idempotencia por workflow.
- Metricas de costos y tokens.
  - Estado: implementado el 2026-08-10 en `src/ariwalabs/model_costs.py`,
    `OpenAIModelAdapter` y `ModelGateway`.
  - Aceptacion: costo estimado por ejecucion, skill y perfil de modelo.
  - Dependencias: Model Gateway.
- Tool Gateway.
  - Aceptacion: tools permitidas/prohibidas se resuelven centralmente.
  - Dependencias: Skill Registry y adapters.
- Context Engine.
  - Aceptacion: compone contexto compartido por agente/workflow sin duplicacion.
  - Dependencias: catalogo de contexto.

## P3 - Futuro

- WhatsApp Business Platform mediante adapter.
- Email transaccional.
- Calendario Google o Microsoft.
- Publicacion social semimanual.
- Pasarela de pago.
- Azure o Microsoft Foundry.
- Nuevos agentes: Training Program, Student Success, Corporate Opportunity,
  Content, Sales Proposal, Project Delivery y Finance & Administration.
