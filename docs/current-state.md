# Current State

Fecha de actualizacion: 2026-08-15
Version declarada: 0.1.0 en `pyproject.toml`; `framework-agent` 0.1.0;
`growth-marketing-agent` 0.2.0.

## Implementado

- CLI `ariwalabs` con comandos:
  - `framework validate-repository`;
  - `agent run`;
  - `agent-registry list`;
  - `agent-registry show`;
  - `execution list`;
  - `execution resume`;
  - `handoff execute`.
- `FrameworkValidator` basico que valida existencia de `agent.yaml`, campos
  minimos, contexto compartido, skills y workflows declarados.
- `AgentRuntime` local basico que carga un agente y workflow, crea una ejecucion
  con estado `pending_human_approval` y la persiste como JSON.
- `JsonRepository` local para guardar/listar ejecuciones.
- `AuditLogger` local append-only en JSONL.
- Dos agentes definidos: Framework Agent y Growth & Marketing Agent.
- Skills declarativas en YAML para ambos agentes.
- Workflows declarativos en YAML para ambos agentes.
- Contexto compartido en `shared/context/`.
- Politica global en `shared/policies/global-agent-policy.yaml`.
- Output schemas estrictos para skills de Growth & Marketing y reportes del
  Framework Agent.
- Airtable Adapter HTTP desacoplado en `adapters/airtable/` con contrato,
  errores tipados, tablas permitidas, retries para rate-limit, idempotencia y
  auditoria sin secretos; incluye validacion de acceso via CLI.
- Diseno contractual de tablas Airtable para People, Organizations,
  TrainingPrograms, Cohorts, Enrollments, Campaigns, ContentItems, Events,
  Referrals, Opportunities, Approvals, AgentExecutions y Artifacts, con campos,
  relaciones, privacidad e idempotencia.
- Tablas Airtable del contrato creadas en la base configurada por `.env`,
  usando Metadata API e idempotencia por metadata.
- Contrato base para modelos en `adapters/models/`.
- Tests unitarios e integracion minimos.
- Workflow de GitHub Actions para ruff, mypy, pytest y validacion del framework.
- Entorno Python dev local preparado con `.venv`, instalacion editable y
  dependencias dev; Javier confirmo que las validaciones base corren
  correctamente.
- Dependencias de desarrollo declaran `types-PyYAML` para validar imports de
  `yaml` con `mypy --strict`.
- `SkillRegistry` valida ids, versiones, output schemas, tools, aprobaciones y
  ownership de skills.
- `HandoffRegistry` valida contratos estructurados de handoffs, incluyendo
  productor, consumidor, aprobacion, persistencia, errores e idempotencia.
- `WorkflowEngine` interpreta workflows locales con pasos `skill`, `parallel`,
  `condition`, `approval`, `action` y `workflow`; puede ejecutar skills reales
  mediante `SkillExecutor`/`ModelGateway`, usar fixtures `__skill_results__` o
  simular cuando no se inyecta executor.
- `ApprovalEngine` crea, lista, aprueba y rechaza approvals locales, actualiza
  ejecuciones relacionadas y audita decisiones.
- CLI `ariwalabs approval` permite listar approvals pendientes y aprobar o
  rechazar con razon registrada.
- `ArtifactManager` registra metadata de artifacts locales en
  `runtime/data/artifacts/` y audita creacion.
- `AuditLogger` escribe eventos JSONL canonicos con `event_id`, severidad,
  actor, correlacion, payload sanitizado y helpers para ejecuciones,
  validaciones, approvals, artifacts, errores y costos.
- `ModelGateway` enruta perfiles logicos `reasoning`, `generation`,
  `evaluation` y `fast_structured` hacia un `ModelAdapter`, con adapter falso
  local, errores tipados, auditoria y registro opcional de usage/costos.
- `OpenAIModelAdapter` implementa el contrato `ModelAdapter` usando Responses
  API con Structured Outputs, modelos configurables por perfil desde `.env`,
  validacion local contra JSON Schema y tests sin red mediante cliente
  inyectable.
- `ModelAdapterFactory` centraliza la seleccion de proveedor mediante
  `MODEL_PROVIDER`, soportando `fake` y `openai`.
- Structured Outputs recuperables: `ModelGateway.generate_structured()`
  normaliza salidas invalidas, incompletas, rechazadas o fallos de proveedor;
  `WorkflowEngine` pausa el flujo en `needs_structured_output_review` y
  `AgentRuntime` persiste `structured_output_error` sin crear approvals ni
  artifacts posteriores.
- Pruebas de regresion para Growth & Marketing con fixtures versionados de
  campana, bootcamp, journey y oportunidad.
- Backlog P1 "Necesario para MVP" cerrado formalmente el 2026-08-08.
- Control de idempotencia end-to-end local: `AgentRuntime` calcula o recibe
  `idempotency_key`, guarda un indice transitorio JSON y reusa la ejecucion
  existente para evitar duplicar approvals y artifacts.
- Metricas de tokens y costos: Model Gateway audita tokens por ejecucion,
  perfil y skill opcional; `OpenAIModelAdapter` estima costos cuando existen
  tarifas configuradas por modelo en `.env`.
- `ToolGateway` centraliza el catalogo de tools declarativas, resuelve tools
  permitidas/prohibidas y valida que las skills no permitan acciones externas
  bloqueadas.
- `ContextEngine` compone contexto compartido por agente/workflow desde
  `shared/context/` y `shared/policies/`, valida rutas permitidas y persiste el
  contexto compuesto en ejecuciones nuevas.
- `EvaluationEngine` valida rubricas declarativas por skill, evalua outputs de
  skills contra schemas y criterios deterministas, y puede invocar un evaluador
  separado mediante Model Gateway con perfil logico `evaluation`.
- Backlog P2 "Siguiente incremento" cerrado formalmente el 2026-08-10.
- Separacion Core Framework / Business Packs con manifests en
  `business_packs/`, `BusinessPackRegistry`, validacion de manifests,
  `business_pack_id` opcional en Framework Validator, Agent Runtime, Context
  Engine, Skill Registry, Handoff Registry, Workflow Engine y Evaluation
  Engine, CLI `--business-pack`, policies core/dominio separadas, rutas fisicas
  del pack AriwaLabs y pack minimo `example-service` validable.
- `AgentRegistry` local en `src/ariwalabs/agent_registry.py`, integrado con
  `FrameworkValidator` y CLI, cataloga agentes por modo default o
  `business_pack_id` con version, owner, estado de release, skills, workflows,
  contexto, policies, handoffs y rubricas.
- Ejecucion real de skills mediante `src/ariwalabs/skill_executor.py` y
  `ModelGateway`: el runtime carga prompt, output schema, input y contexto
  compuesto por skill, invoca `generate_structured()` y persiste `model_result`
  en la ejecucion.
- Sincronizacion operacional explicita hacia Airtable mediante
  `src/ariwalabs/airtable_sync.py` y CLI `ariwalabs airtable sync-execution`,
  cubriendo `AgentExecutions`, `Approvals` y `Artifacts` con idempotencia y
  auditoria.
- Reanudacion explicita de workflows aprobados mediante `AgentRuntime.resume()`
  y CLI `ariwalabs execution resume`, continuando desde el checkpoint aprobado
  sin duplicar approvals ni artifacts previos.
- `ToolGateway` ejecutable para tools gobernadas: `audit-append`,
  `artifact-create`, `airtable-read` y `airtable-write-draft` con contratos de
  input/output, auditoria, latencia, bloqueo por aprobacion y adapters
  inyectados; acciones externas como publicar, enviar mensajes o pagos siguen
  bloqueadas para skills.
- `HandoffRuntime` ejecuta handoffs aprobados desde contratos YAML, valida
  payloads requeridos, persiste transiciones versionadas en JSON local, aplica
  idempotencia, registra aprobacion asociada y audita duracion.
- Errores tipados del framework en `src/ariwalabs/errors.py` para requests
  invalidos, agente inexistente, workflow inexistente, Tool Gateway y Handoff
  Runtime; CLI traduce errores del framework a JSON estable con
  `status=failed`.
- Metricas de latencia en eventos de auditoria de ejecucion, requests de
  modelo, tools, handoffs y requests Airtable.

## Parcial

- Reusabilidad multi-negocio: existe frontera implementada, manifests de
  business packs, loaders parametrizables, Agent Registry multipack y pack de
  ejemplo validable.
- Handoffs: ya se pueden ejecutar localmente; queda pendiente sincronizacion
  operacional futura con Airtable/Agent Registry cuando se defina tabla
  canonica.

## Stubs y deuda tecnica

- `shared/templates/` y `framework/` quedan reservados con `.gitkeep`.
- Las rutas historicas `agents/`, `shared/` y `docs/handoffs/` se mantienen
  para compatibilidad del modo default aunque AriwaLabs Training ya tiene
  activos fisicos propios dentro del pack.
- El checkout ya contiene `.git` y remote `origin` apuntando a
  `https://github.com/javierrosado/ariwalabs-agent-platform.git`.
- La validacion del framework usa `SkillRegistry` y `HandoffRegistry`, pero aun
  no comprueba existencia de prompts.
- `ContextEngine` aun no selecciona subconjuntos por skill ni presupuestos de
  tokens; compone todo el contexto declarado por agente para el workflow.
- `EvaluationEngine` aun usa rubricas base estaticas; falta calibrar criterios
  especificos por dominio y usar evaluacion de modelo en runtime productivo.
- Hay idempotencia en Airtable Adapter mediante `IdempotencyKey`; la
  sincronizacion operacional usa llaves externas por ejecucion, approval y
  artifact. El indice JSON local del runtime no es transaccional.
- Los tests de integracion escriben en `runtime/data`, que esta ignorado pero
  puede dejar artefactos locales.

## Integraciones pendientes

- WhatsApp Business Platform.
- Email transaccional.
- Calendarios.
- Publicacion social semimanual.
- Pasarela de pago.
- Azure o Microsoft Foundry.

## Riesgos

- La documentacion de arquitectura puede leerse como implementacion completa,
  aunque varios componentes son aun disenio.
- Los schemas genericos no protegen contra outputs incompletos o ambiguos.
- La trazabilidad en GitHub depende de mantener commits y pushes despues de los
  cambios relevantes.
- La integracion OpenAI real todavia debe cuidar que prompts, payloads sensibles
  y secretos no se registren en auditoria.
- El runtime puede aceptar requests invalidos hasta fallar por excepcion.

## Decisiones pendientes

- Conectar release governance del Agent Registry con approvals reales.
- Contrato canonico para workflows, steps, condiciones y paralelismo.
- Modelo de persistencia local transitorio vs Airtable para ejecuciones.
- Vistas operativas de Airtable y sincronizacion desde runtime local.
- Politica de evaluacion y regresion para outputs de agentes.
- Politica de automatizacion: decidir si tools/handoffs se ejecutaran solo via
  CLI o tambien como pasos declarativos del workflow.

## Validaciones ejecutadas en esta sesion

- Javier confirmo el 2026-08-08 que las validaciones base se ejecutaron
  correctamente desde el entorno dev local:
  - `ariwalabs framework validate-repository --root .`
  - `ruff check .`
  - `mypy src`
  - `pytest`
- Con esto queda cerrado el bloqueo P0 de preparacion del entorno Python local.
- Para la integracion OpenAI se ejecuto el 2026-08-08:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - `git diff --check`
  - Resultado: paso; `pytest` reporto 70 tests.
- Para Structured Outputs recuperables se ejecuto el 2026-08-08:
  - `.venv/Scripts/python.exe -m pytest` sobre Model Gateway, Workflow Engine
    y Growth runtime.
  - `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso; el set focalizado reporto 17 tests.
- Suite completa posterior:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso; `pytest` reporto 79 tests.
- Para pruebas de regresion Growth se ejecuto el 2026-08-08:
  - `.venv/Scripts/python.exe -m pytest tests/integration/test_growth_regression.py`
  - `.venv/Scripts/python.exe -m ruff check tests/integration/test_growth_regression.py`
  - Validacion portable de JSON en `tests/fixtures/regression/growth/`.
  - `.venv/Scripts/python.exe -m mypy src`
  - `git diff --check`
  - Resultado: paso; el set nuevo reporto 5 tests.
- Suite completa posterior:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso; `pytest` reporto 84 tests.
- Para control de idempotencia se ejecuto el 2026-08-10:
  - `.venv/Scripts/python.exe -m pytest` sobre idempotencia y Growth runtime.
  - `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso; el set focalizado reporto 9 tests.
- Suite completa posterior:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso; `pytest` reporto 90 tests.
- Para metricas de costos y tokens se ejecuto el 2026-08-10:
  - `.venv/Scripts/python.exe -m pytest` sobre costos, gateway, OpenAI adapter
    y factory.
  - `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso; el set focalizado reporto 26 tests.
- Suite completa posterior:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso; `pytest` reporto 97 tests.
- Para Tool Gateway se ejecuto el 2026-08-10:
  - `.venv/Scripts/python.exe -m pytest` sobre Tool Gateway, Skill Registry y
    Framework Validator.
  - `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - Resultado: paso; el set focalizado reporto 14 tests.
- Suite completa posterior:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso; `pytest` reporto 103 tests.
- Para Context Engine se ejecuto el 2026-08-10:
  - `.venv/Scripts/python.exe -m pytest` sobre Context Engine, Framework
    Validator y Growth runtime.
  - `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso; el set focalizado reporto 15 tests.
- Suite completa posterior:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso; `pytest` reporto 109 tests.
- Para Evaluacion independiente se ejecuto el 2026-08-10:
  - `.venv/Scripts/python.exe -m pytest` sobre Evaluation Engine, Framework
    Validator y Growth runtime.
  - `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso; el set focalizado reporto 17 tests.
- Suite completa posterior:
  - `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - `.venv/Scripts/python.exe -m ruff check .`
  - `.venv/Scripts/python.exe -m mypy src`
  - `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso; `pytest` reporto 115 tests.

## Siguiente objetivo recomendado

Continuar P3 con reanudacion de workflows despues de approvals o ejecucion de
tools reales mediante Tool Gateway.
