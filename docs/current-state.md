# Current State

Fecha de actualizacion: 2026-08-10
Version declarada: 0.1.0 en `pyproject.toml`; `framework-agent` 0.1.0;
`growth-marketing-agent` 0.2.0.

## Implementado

- CLI `ariwalabs` con comandos:
  - `framework validate-repository`;
  - `agent run`;
  - `execution list`.
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
  `condition`, `approval`, `action` y `workflow`, simulando ejecucion y pausando
  en aprobaciones humanas.
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

## Parcial

- Agent Registry: mencionado, pero no implementado como componente.
- Context Engine: existe carga de rutas declaradas, pero no hay seleccion ni
  composicion de contexto.
- Integracion controlada con ejecucion real de skills mediante Model Gateway.
- Tool Gateway: mencionado, pero no implementado.
- Evaluation Engine: mencionado, pero no implementado.
- Handoffs: existen contratos YAML versionados y validacion automatica basica.

## Stubs y deuda tecnica

- `shared/templates/` y `framework/` no contienen archivos.
- El checkout ya contiene `.git` y remote `origin` apuntando a
  `https://github.com/javierrosado/ariwalabs-agent-platform.git`.
- La validacion del framework usa `SkillRegistry` y `HandoffRegistry`, pero aun
  no comprueba existencia de prompts.
- Hay idempotencia en Airtable Adapter mediante `IdempotencyKey`; el runtime
  local ya evita duplicados por request, pero el indice JSON no es
  transaccional.
- No hay metricas de latencia.
- No hay manejo tipado de errores en runtime/CLI.
- Los tests de integracion escriben en `runtime/data`, que esta ignorado pero
  puede dejar artefactos locales.

## Integraciones pendientes

- Sincronizacion operacional desde runtime local hacia Airtable.
- Integracion controlada con ejecucion real de skills mediante Model Gateway.
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

- Forma exacta del Agent Registry.
- Contrato canonico para workflows, steps, condiciones y paralelismo.
- Modelo de persistencia local transitorio vs Airtable para ejecuciones.
- Vistas operativas de Airtable y sincronizacion desde runtime local.
- Politica de evaluacion y regresion para outputs de agentes.

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

## Siguiente objetivo recomendado

Continuar con P2: Evaluacion independiente, Tool Gateway o Context Engine.
