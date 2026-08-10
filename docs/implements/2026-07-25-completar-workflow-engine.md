# Implementacion: Workflow Engine

Fecha: 2026-07-25

## Objetivo

Completar el item P1 "Completar Workflow Engine" de
`docs/implementation-backlog.md`.

## Alcance

- Crear un motor local y deterministico para interpretar workflows YAML.
- Soportar pasos `skill`, `parallel`, `condition`, `approval`, `action` y
  `workflow`.
- Integrar el motor con `AgentRuntime`.
- Pausar ejecuciones en checkpoints de aprobacion humana.
- Simular skills y acciones internas sin llamar modelos, Airtable, WhatsApp,
  LinkedIn ni otros proveedores externos.

## Archivos modificados

- `src/ariwalabs/workflow_engine.py`
- `src/ariwalabs/runtime.py`
- `tests/unit/test_workflow_engine.py`
- `tests/integration/test_growth_runtime.py`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/2026-07-25-completar-workflow-engine.md`

## Pasos ejecutados

1. Se reviso el runtime actual.
   - Resultado: `AgentRuntime` solo cargaba la definicion del workflow y creaba
     una ejecucion en `pending_human_approval`.

2. Se revisaron los workflows existentes.
   - Resultado: se identificaron pasos `skill`, `parallel`, `condition`,
     `approval`, `action` y `workflow`.

3. Se creo `src/ariwalabs/workflow_engine.py`.
   - Resultado: el motor interpreta workflows de forma local y devuelve estado,
     pasos simulados, errores y aprobacion pendiente cuando corresponde.

4. Se integro `WorkflowEngine` con `AgentRuntime`.
   - Resultado: las ejecuciones guardan `workflow_execution` y derivan el
     estado principal desde el resultado del motor.

5. Se agregaron tests unitarios.
   - Resultado: `tests/unit/test_workflow_engine.py` cubre pausa por aprobacion,
     paralelismo simulado, condiciones cumplidas/no cumplidas, accion externa
     prohibida y aprobador invalido.

6. Se actualizo la prueba de integracion del runtime.
   - Resultado: ahora verifica que la ejecucion de una campana queda pausada en
     `approve_campaign`.

## Resultados de validacion

- `PYTHONPATH=src python3` ejecutando workflows de Growth:
  - `create-training-campaign`: `paused_for_approval`, checkpoint
    `approve_campaign`.
  - `plan-live-bootcamp`: `paused_for_approval`, checkpoint `approve_bootcamp`.
  - `detect-corporate-opportunity`: `paused_for_approval`, checkpoint
    `approve_opportunity_registration`.
  - `manage-student-growth-journey`: `completed` con condicion no cumplida.
  - `manage-student-growth-journey` con `eligible_for_referral`: `completed`
    con skill de referidos simulada.
  - `analyze-growth-funnel`: `paused_for_approval`, checkpoint
    `acknowledge_recommendations`.

- `PYTHONPATH=src python3` ejecutando `AgentRuntime` para
  `create-training-campaign`
  - Resultado: paso; estado principal `pending_human_approval` y
    `workflow_execution.status` igual a `paused_for_approval`.

- `python3 -m compileall src tests adapters`
  - Resultado: paso.

## Validaciones bloqueadas por entorno

Los siguientes comandos se intentaron, pero no estan disponibles en este shell:

- `ariwalabs framework validate-repository --root .`
- `ruff check .`
- `mypy src`
- `pytest`

## Riesgos y deuda

- Las skills se simulan; todavia no hay Model Gateway ni structured outputs en
  runtime.
- Las acciones internas se registran como simuladas; Artifact Manager y Approval
  Engine siguen pendientes.
- `parallel` se interpreta como ramas simuladas, no como concurrencia real.
- Las condiciones usan flags simples del input hasta que exista contrato
  canonico de condiciones.

## Siguiente paso recomendado

Implementar Approval Engine y CLI de aprobaciones para crear, listar, aprobar,
rechazar y auditar checkpoints.
