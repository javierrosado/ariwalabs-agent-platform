# Implementacion: Structured Outputs recuperables

Fecha: 2026-08-08

## Objetivo

Implementar el item P1 "Structured outputs" con errores recuperables en Model
Gateway, Workflow Engine y runtime.

## Alcance

- Agregar un modo recuperable a Model Gateway.
- Normalizar salidas invalidas, incompletas, rechazadas y fallos de provider.
- Pausar workflows cuando una skill produce salida estructurada invalida.
- Persistir `structured_output_error` en ejecuciones.
- Evitar approvals y artifacts posteriores a un output invalido.
- Mantener `generate()` existente sin romper tests previos.

## Archivos modificados

- `src/ariwalabs/model_gateway.py`
- `src/ariwalabs/workflow_engine.py`
- `src/ariwalabs/runtime.py`
- `tests/unit/test_model_gateway.py`
- `tests/unit/test_workflow_engine.py`
- `tests/integration/test_growth_runtime.py`
- `docs/architecture/model-gateway.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`

## Pasos ejecutados

1. Se agrego `ModelGateway.generate_structured()`.
   - Resultado: `ModelOutputError` y `ModelProviderError` se convierten en
     resultados recuperables.

2. Se agregaron eventos auditables.
   - Resultado: existen `model.output.invalid` y
     `model.provider.failed_recoverable`.

3. Se extendio `WorkflowEngine`.
   - Resultado: al recibir estados recuperables para una skill, el workflow
     queda en `needs_structured_output_review`.

4. Se extendio `AgentRuntime`.
   - Resultado: persiste `structured_output_error` y no crea approvals ni
     artifacts posteriores.

5. Se agregaron tests de gateway, workflow y runtime.
   - Resultado: cubren output invalido, fallo de provider, incomplete y pausa
     recuperable del workflow.

6. Se actualizo documentacion y backlog.
   - Resultado: Structured Outputs quedo marcado como implementado.

## Resultados de validacion

- `.venv/Scripts/python.exe -m pytest` sobre Model Gateway, Workflow Engine y
  Growth runtime.
  - Resultado: paso con 17 tests.

- `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - Resultado: paso con `status=passed`.

- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 79 tests en la suite completa de ese momento.

- `git diff --check`
  - Resultado: paso.

## Validaciones bloqueadas por entorno

No aplico. Las validaciones se ejecutaron con `.venv/Scripts`.

## Riesgos y deuda

- El Workflow Engine aun recibe resultados de skill/modelo precomputados para
  simular fallos; falta integrar ejecucion real de skills mediante Model
  Gateway.
- No hay accion explicita de reintento/reanudacion tras revisar una salida
  estructurada fallida.

## Siguiente paso recomendado

Agregar pruebas de regresion para campana, bootcamp, journey y oportunidad.
