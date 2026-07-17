# Implementation Backlog

## P0 - Bloqueante

- Preparar entorno Python dev local.
  - Aceptacion: existe `.venv`, `pip install -e ".[dev]"` finaliza correctamente,
    y corren `ariwalabs`, `pytest`, `ruff` y `mypy`.
  - Dependencias: Python con `pip` o mecanismo equivalente de entorno virtual.
- Completar schemas de skills.
  - Aceptacion: cada output schema define campos requeridos, tipos, errores y
    `additionalProperties: false` donde corresponda.
  - Dependencias: contratos de outputs esperados por workflow.
- Implementar Skill Registry.
  - Aceptacion: valida ids, versiones, schemas, tools, aprobaciones y ownership.
  - Dependencias: formato canonico de skill.
- Completar validacion de handoffs.
  - Aceptacion: contratos de productor/consumidor, aprobacion, persistencia,
    errores e idempotencia validados automaticamente.
  - Dependencias: `docs/handoff-catalog.md` y schema comun.

## P1 - Necesario para MVP

- Completar Workflow Engine.
  - Aceptacion: interpreta pasos, paralelismo, condiciones, acciones y estados.
  - Dependencias: Skill Registry, schemas y runtime de ejecucion.
- Implementar Approval Engine.
  - Aceptacion: crea, lista, aprueba, rechaza y audita checkpoints.
  - Dependencias: CLI de aprobaciones y repositorio.
- Implementar CLI de aprobaciones.
  - Aceptacion: Javier puede ver pendientes y decidir con razon registrada.
  - Dependencias: Approval Engine.
- Implementar Artifact Manager.
  - Aceptacion: registra artefactos con metadata, origen, version y estado.
  - Dependencias: repositorio local y futura tabla `Artifacts`.
- Implementar Audit Log completo.
  - Aceptacion: eventos de ejecucion, validacion, approval, artifact, error y
    costos quedan en JSONL sin secretos.
  - Dependencias: runtime y gateways.
- Implementar Airtable Adapter.
  - Aceptacion: read/create/update draft con errores tipados, retries,
    rate-limit handling e idempotencia.
  - Dependencias: diseno de tablas.
- Disenar tablas de Airtable.
  - Aceptacion: campos, relaciones, claves externas y reglas de privacidad para
    People, Organizations, TrainingPrograms, Cohorts, Enrollments, Campaigns,
    ContentItems, Events, Referrals, Opportunities, Approvals,
    AgentExecutions y Artifacts.
  - Dependencias: contexto de negocio y approvals.
- Implementar Model Gateway.
  - Aceptacion: enruta perfiles `reasoning`, `generation`, `evaluation` y
    `fast_structured` sin acoplar skills a modelos.
  - Dependencias: contrato `ModelAdapter` y configuracion.
- Integrar modelos OpenAI.
  - Aceptacion: provider configurable por `.env`, sin secretos en logs.
  - Dependencias: Model Gateway.
- Structured outputs.
  - Aceptacion: outputs validados contra JSON Schema y errores recuperables.
  - Dependencias: schemas estrictos y Model Gateway.
- Pruebas de regresion.
  - Aceptacion: fixtures para campana, bootcamp, journey y oportunidad.
  - Dependencias: Workflow Engine y schemas.

## P2 - Siguiente incremento

- Evaluacion independiente.
  - Aceptacion: rubricas por skill y evaluador separado de generacion.
  - Dependencias: Model Gateway y schemas.
- Control de idempotencia.
  - Aceptacion: requests repetidos no duplican approvals, opportunities ni
    artifacts.
  - Dependencias: llaves de idempotencia por workflow.
- Metricas de costos y tokens.
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
