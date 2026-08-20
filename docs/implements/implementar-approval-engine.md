# Implementacion: Approval Engine

Fecha: 2026-07-25

## Objetivo

Implementar el item P1 "Implementar Approval Engine" de
`docs/implementation-backlog.md`.

## Alcance

- Crear un motor local para crear, listar, aprobar y rechazar approvals.
- Persistir approvals en `runtime/data/approvals/`.
- Integrar la creacion de approvals con `AgentRuntime` cuando un workflow pausa
  en `paused_for_approval`.
- Actualizar la ejecucion relacionada cuando Javier aprueba o rechaza.
- Auditar creacion y decision de approvals.
- No reanudar workflows ni ejecutar acciones externas automaticamente.

## Archivos modificados

- `src/ariwalabs/approval_engine.py`
- `src/ariwalabs/runtime.py`
- `src/ariwalabs/repository.py`
- `tests/unit/test_approval_engine.py`
- `tests/integration/test_growth_runtime.py`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/implementar-approval-engine.md`

## Pasos ejecutados

1. Se reviso el runtime y el Workflow Engine.
   - Resultado: el runtime ya recibe `workflow_execution.approval` cuando el
     workflow pausa en un checkpoint.

2. Se agrego lectura de payloads al `JsonRepository`.
   - Resultado: `JsonRepository.load()` permite cargar approvals y ejecuciones
     existentes para actualizarlas.

3. Se creo `src/ariwalabs/approval_engine.py`.
   - Resultado: `ApprovalEngine` permite `create_pending`, `list_pending` y
     `decide`.

4. Se integro `ApprovalEngine` con `AgentRuntime`.
   - Resultado: cuando un workflow pausa por aprobacion, el runtime crea un
     approval pendiente y guarda `approval_id` dentro de la ejecucion.

5. Se agregaron tests unitarios.
   - Resultado: cubren creacion, listado, aprobacion, rechazo, decision sin
     razon, doble decision y decision por usuario distinto de
     `company-director`.

6. Se actualizo la prueba de integracion del runtime.
   - Resultado: verifica que una campana crea un approval pendiente asociado a
     la ejecucion.

## Resultados de validacion

- `PYTHONPATH=src python3` creando approval pendiente, listando pendientes y
  aprobando.
  - Resultado: paso; la ejecucion relacionada quedo en
    `approved_pending_resume`.

- `PYTHONPATH=src python3` ejecutando `AgentRuntime` para
  `create-training-campaign`.
  - Resultado: paso; estado principal `pending_human_approval` y approval con
    `approval_id` generado.

- `python3 -m compileall src tests adapters`
  - Resultado: paso.

- Revision manual de lineas mayores a 100 caracteres en `src/ariwalabs/*.py`,
  `tests/unit/*.py` y `tests/integration/*.py`.
  - Resultado: paso; no se encontraron lineas sobre 100 caracteres.

## Validaciones bloqueadas por entorno

Los siguientes comandos se intentaron, pero no estan disponibles en este shell:

- `ariwalabs framework validate-repository --root .`
- `ruff check .`
- `mypy src`
- `pytest`

## Riesgos y deuda

- Aprobar no reanuda workflows todavia; deja la ejecucion en
  `approved_pending_resume`.
- La CLI completa de aprobaciones sigue como item separado del backlog.
- Los approvals persisten en JSON local; Airtable se integrara despues mediante
  adapter.

## Siguiente paso recomendado

Implementar CLI de aprobaciones para que Javier pueda listar pendientes y
decidir con razon registrada desde `ariwalabs`.
