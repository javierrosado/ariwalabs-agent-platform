# Implementacion: reanudar workflows despues de aprobaciones

Fecha: 2026-08-15

## Objetivo

Permitir que una ejecucion aprobada continue desde el checkpoint de approval sin
duplicar approvals, artifacts ni pasos previos.

## Alcance

- Agregar resume por checkpoint en `WorkflowEngine`.
- Agregar `AgentRuntime.resume(execution_id)`.
- Agregar CLI `ariwalabs execution resume <execution_id>`.
- Combinar pasos previos con pasos reanudados.
- Marcar el paso de approval como aprobado.
- Crear artifacts solo para acciones alcanzadas despues del checkpoint.

## Archivos modificados

- `src/ariwalabs/workflow_engine.py`
- `src/ariwalabs/runtime.py`
- `src/ariwalabs/cli.py`
- `tests/integration/test_growth_runtime.py`
- `tests/unit/test_approval_cli.py`
- `docs/architecture/11-workflow-engine.md`
- `docs/architecture/12-approval-engine.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/roadmap/implementation-roadmap.md`
- `README.md`
- `docs/session-log.md`

## Pasos ejecutados

1. Se agrego `resume_after_checkpoint` a `WorkflowEngine.run()`.
   - Resultado: el workflow puede continuar desde el paso posterior al approval
     aprobado.

2. Se agrego `AgentRuntime.resume()`.
   - Resultado: una ejecucion en `approved_pending_resume` se reanuda, combina
     pasos, recalcula evaluacion, actualiza estado y persiste el resultado.

3. Se agrego CLI.
   - Resultado: `ariwalabs execution resume <execution_id>` reanuda una
     ejecucion aprobada.

4. Se protegieron duplicados.
   - Resultado: el resume no crea nuevos approvals y solo crea artifacts para
     acciones posteriores al checkpoint.

## Riesgos y deuda

- El resume soporta checkpoints top-level del workflow actual.
- No ejecuta handoffs como transiciones reales todavia.
- El resume sigue siendo accion explicita; no se dispara automaticamente al
  aprobar desde CLI.
