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
    `docs/architecture/19-airtable-tables.md`.
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

## P2 - Cerrado

Estado general: cerrado el 2026-08-10.

- Evaluacion independiente.
  - Estado: implementado el 2026-08-10 en `src/ariwalabs/evaluation_engine.py`,
    rubricas por agente y `AgentRuntime`.
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
  - Estado: implementado el 2026-08-10 en `src/ariwalabs/tool_gateway.py` e
    integrado con `SkillRegistry`.
  - Aceptacion: tools permitidas/prohibidas se resuelven centralmente.
  - Dependencias: Skill Registry y adapters.
- Context Engine.
  - Estado: implementado el 2026-08-10 en `src/ariwalabs/context_engine.py` e
    integrado con `AgentRuntime` y `FrameworkValidator`.
  - Aceptacion: compone contexto compartido por agente/workflow sin duplicacion.
  - Dependencias: catalogo de contexto.

## P3 - Cerrado

Estado general: cerrado para el alcance P3 el 2026-08-15.

- Separar Core Framework y AriwaLabs Training Pack.
  - Estado: implementado el 2026-08-15; existen manifests en
    `business_packs/`, `BusinessPackRegistry`, validacion de manifests, loaders
    con `business_pack_id`, CLI `--business-pack`, policies core/dominio
    separadas, rutas fisicas del pack AriwaLabs y un segundo pack minimo
    validable.
  - Aceptacion: loaders, validadores y runtime aceptan `business_pack_id`;
    policies core y policies de dominio estan separadas; existe un segundo pack
    minimo de ejemplo que valida reusabilidad del core.
  - Pendiente posterior: migrar referencias documentales historicas hacia rutas
    de pack y formalizar schemas comunes de core.
  - Dependencias: `ContextEngine`, `FrameworkValidator`, `SkillRegistry`,
    `HandoffRegistry`, `AgentRuntime` y `AgentRegistry`.
- Implementar Agent Registry.
  - Estado: implementado el 2026-08-15 como
    `src/ariwalabs/agent_registry.py`, integrado con `FrameworkValidator` y
    CLI `ariwalabs agent-registry`.
  - Aceptacion: existe un registro local gobernado que cataloga agentes,
    versiones, owner, estado de release, skills, workflows, schemas, rubricas,
    handoffs y politicas aplicables; se integra con `FrameworkValidator`; los
    releases sensibles requieren aprobacion de `company-director`; incluye tests
    unitarios e integracion.
  - Pendiente posterior: conectar release governance con approvals reales y
    decidir si se materializa/sincroniza el registro en Airtable.
  - Dependencias: separacion Core/Business Pack, `FrameworkValidator`,
    `SkillRegistry`, `HandoffRegistry`, `EvaluationEngine`, `ApprovalEngine`,
    `JsonRepository` y catalogo de agentes.
- Integrar ejecucion real de skills mediante Model Gateway.
  - Estado: implementado el 2026-08-15 mediante
    `src/ariwalabs/skill_executor.py`, `WorkflowEngine`, `AgentRuntime` y
    `ModelGateway`.
  - Aceptacion: el runtime carga prompt, schema, input y contexto compuesto;
    invoca `ModelGateway.generate_structured()` por skill; persiste resultados
    validados; mantiene el comportamiento recuperable para structured outputs.
  - Pendiente posterior: conectar tools reales de skills mediante Tool Gateway
    y calibrar prompts/outputs semanticos con provider real.
  - Dependencias: `ModelGateway`, prompts, schemas estrictos, `WorkflowEngine`,
    `ContextEngine` y `EvaluationEngine`.
- Sincronizar ejecuciones, approvals y artifacts hacia Airtable.
  - Estado: implementado el 2026-08-15 mediante
    `src/ariwalabs/airtable_sync.py` y CLI `ariwalabs airtable
    sync-execution`.
  - Aceptacion: ejecuciones, approvals y artifacts se pueden escribir como draft
    o estado gobernado en Airtable con idempotencia y auditoria, sin exponer
    secretos.
  - Pendiente posterior: decidir si la sincronizacion sera automatica despues
    de cada ejecucion o seguira como accion explicita gobernada; crear links
    Airtable entre registros si se requieren vistas relacionales.
  - Dependencias: `adapters/airtable/`, `ToolGateway`, `JsonRepository`,
    contrato de tablas y Approval Engine.
- Reanudar workflows despues de aprobaciones.
  - Estado: implementado el 2026-08-15 mediante `AgentRuntime.resume()`,
    `WorkflowEngine.run(resume_after_checkpoint=...)` y CLI `ariwalabs
    execution resume`.
  - Aceptacion: una ejecucion aprobada puede continuar desde el checkpoint
    aprobado sin duplicar approvals, artifacts ni acciones previas.
  - Pendiente posterior: decidir si el resume debe ejecutarse automaticamente
    despues de `approval decide --decision approved` o mantenerse como accion
    explicita gobernada.
  - Dependencias: `WorkflowEngine`, `ApprovalEngine`, idempotencia y
    persistencia de estado.
- Ejecutar tools mediante Tool Gateway.
  - Estado: implementado el 2026-08-15 mediante
    `src/ariwalabs/tool_gateway.py`.
  - Aceptacion: cada tool tiene contrato de input/output, reglas de approval,
    auditoria y adapter asociado; las acciones externas bloqueadas siguen sin
    ejecutarse desde skills.
  - Pendiente posterior: conectar invocaciones de tools desde workflows/skills
    solo cuando exista contrato explicito por accion y aprobacion aplicable.
  - Dependencias: `ToolGateway`, adapters, Audit y Approval Engine.
- Ejecutar handoffs en runtime.
  - Estado: implementado el 2026-08-15 mediante
    `src/ariwalabs/handoff_runtime.py` y CLI `ariwalabs handoff execute`.
  - Aceptacion: un handoff aprobado produce payload versionado, estado,
    idempotencia, auditoria y persistencia local/futura.
  - Pendiente posterior: sincronizar handoffs con Airtable/Agent Registry cuando
    exista tabla operacional canonica de handoffs.
  - Dependencias: `HandoffRegistry`, Agent Registry, Approval Engine y
    Persistence.
- Endurecer runtime y CLI con errores tipados.
  - Estado: implementado el 2026-08-15 mediante `src/ariwalabs/errors.py`,
    validaciones de entrada en `AgentRuntime` y respuestas JSON de CLI para
    errores del framework.
  - Aceptacion: errores de request invalida, agente inexistente, workflow
    inexistente, contexto invalido, schema invalido y persistencia tienen tipos
    claros y respuestas CLI consistentes.
  - Pendiente posterior: extender la taxonomia tipada a validadores,
    repositorio y adapters restantes.
  - Dependencias: `AgentRuntime`, `WorkflowEngine`, `ContextEngine` y CLI.
- Medir latencia.
  - Estado: implementado el 2026-08-15 en eventos de auditoria de runtime,
    requests de modelo, Tool Gateway, Handoff Runtime y Airtable Adapter.
  - Aceptacion: eventos de auditoria incluyen duracion para ejecuciones,
    requests de modelo, tools y adapters cuando aplique.
  - Pendiente posterior: agregar agregaciones/reportes operativos por workflow,
    skill, provider y adapter.
  - Dependencias: Audit, Model Gateway, Tool Gateway y adapters.

## P4 - Siguiente incremento post-P3

Estado general: priorizado el 2026-08-20; pendiente de implementacion paso a
paso.

- Formalizar schemas comunes del Core.
  - Estado: implementado el 2026-08-21 mediante `shared/schemas/core/` y
    `src/ariwalabs/schema_validator.py`.
  - Aceptacion: existen contratos canonicos versionados para agents, skills,
    workflows, approvals, artifacts, handoffs y business packs; los validadores
    usan esos contratos sin duplicar reglas de dominio.
  - Pendiente posterior: evaluar referencias multiarchivo reales desde
    `common.schema.json` cuando los contratos crezcan y migrar consumidores
    historicos de `shared/schemas/handoff.schema.json`.
  - Dependencias: `BusinessPackRegistry`, `AgentRegistry`, `SkillRegistry`,
    `HandoffRegistry`, `WorkflowEngine`, `ApprovalEngine` y `ArtifactManager`.
- Conectar Agent Registry con approvals reales.
  - Estado: pendiente.
  - Aceptacion: los cambios o releases sensibles de agentes generan approvals
    mediante `ApprovalEngine`; `company-director` conserva aprobacion
    obligatoria; CLI y auditoria muestran decision, razon y version afectada.
  - Dependencias: `AgentRegistry`, `ApprovalEngine`, `AuditLogger`,
    `JsonRepository` y schemas comunes del Core.
- Definir politica de automatizacion gobernada para resume, sync y tools.
  - Estado: pendiente.
  - Aceptacion: existe una politica documentada y validada que define que
    acciones siguen siendo CLI explicitas y cuales pueden ejecutarse
    automaticamente despues de approvals; toda accion externa mantiene bloqueo
    sin aprobacion de Javier.
  - Dependencias: `ApprovalEngine`, `AgentRuntime.resume()`,
    `airtable_sync`, `ToolGateway`, politicas core y politicas de pack.
- Integrar invocaciones de Tool Gateway desde workflows/skills.
  - Estado: pendiente.
  - Aceptacion: workflows y/o skills pueden invocar tools gobernadas solo cuando
    exista contrato explicito de input/output, approval, auditoria, adapter e
    idempotencia; las acciones externas prohibidas siguen bloqueadas.
  - Dependencias: politica de automatizacion gobernada, `ToolGateway`,
    `WorkflowEngine`, `SkillExecutor`, adapters y `ApprovalEngine`.
- Completar sincronizacion operacional Airtable.
  - Estado: pendiente.
  - Aceptacion: `AgentExecutions`, `Approvals` y `Artifacts` quedan enlazados
    relacionalmente en Airtable cuando aplique; existen vistas operativas para
    Javier; se decide si los handoffs requieren tabla canonica propia.
  - Dependencias: `airtable_sync`, contrato de tablas Airtable,
    `HandoffRuntime`, `ApprovalEngine` y `JsonRepository`.
- Calibrar prompts, outputs y rubricas con provider real.
  - Estado: pendiente.
  - Aceptacion: Growth & Marketing Agent ejecuta workflows principales con
    OpenAI real sobre datos controlados; prompts, schemas y rubricas se ajustan
    con fixtures de regresion; no se registran secretos ni datos sensibles en
    auditoria.
  - Dependencias: `ModelGateway`, `OpenAIModelAdapter`, `SkillExecutor`,
    `EvaluationEngine`, fixtures Growth y `.env` local.
- Extender errores tipados a validadores, repositorio y adapters.
  - Estado: pendiente.
  - Aceptacion: validadores, persistencia local y adapters devuelven errores
    tipados del framework; CLI expone respuestas JSON estables y auditables para
    fallos de validacion, persistencia e integracion.
  - Dependencias: `errors.py`, `FrameworkValidator`, registries,
    `JsonRepository`, adapters y CLI.
- Agregar reportes operativos de observabilidad.
  - Estado: pendiente.
  - Aceptacion: existen agregaciones locales por workflow, skill, provider,
    adapter, tokens, costo y latencia; los reportes se generan sin exponer
    secretos ni payloads sensibles.
  - Dependencias: `AuditLogger`, metricas de costos/tokens, latencia auditada y
    CLI.
- Corregir deuda documental post-P3.
  - Estado: pendiente.
  - Aceptacion: documentos de arquitectura, current-state y roadmap no contienen
    pendientes ya implementados; referencias historicas se migran gradualmente a
    rutas de business pack sin romper compatibilidad del modo default.
  - Dependencias: `docs/architecture/`, `docs/current-state.md`,
    `docs/roadmap/implementation-roadmap.md`, `business_packs/` y rutas
    historicas `agents/`, `shared/`, `docs/handoffs/`.
- Evaluar primera integracion externa posterior.
  - Estado: futuro.
  - Aceptacion: se elige la primera integracion entre WhatsApp Business
    Platform, email transaccional o calendario; existe ADR con riesgos,
    aprobaciones, adapter requerido, datos tratados y criterio de no accion
    externa sin Javier.
  - Dependencias: politica de automatizacion gobernada, Tool Gateway,
    Approval Engine, adapters y contexto operacional de AriwaLabs.
- Evaluar nuevos agentes de dominio.
  - Estado: futuro.
  - Aceptacion: no se inicia un agente nuevo hasta que Growth & Marketing Agent
    ejecute workflows principales con skills reales o fixtures aprobados,
    genere artifacts conformes, registre approvals, sincronice ejecuciones
    relevantes con Airtable y pase regresion.
  - Dependencias: cierre de los items operativos P4 y criterio de roadmap para
    nuevos agentes.
