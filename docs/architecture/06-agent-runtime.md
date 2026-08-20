# Agent Runtime

Fecha: 2026-08-15

## Objetivo

Orquestar una ejecucion local de agente desde una request hasta su persistencia,
manteniendo control de contexto, workflow, evaluacion, approvals, artifacts,
auditoria e idempotencia.

## Estado

Implementado en `src/ariwalabs/runtime.py`.

## Reglas

- Carga `agent.yaml` y el workflow solicitado desde `agents/`.
- Valida request de entrada, agente y workflow con errores tipados.
- Compone contexto con `ContextEngine` antes de ejecutar el workflow.
- Aplica idempotencia por request para evitar duplicar ejecuciones, approvals y
  artifacts.
- Ejecuta el workflow con `WorkflowEngine`.
- Evalua resultados con `EvaluationEngine`.
- Crea approvals pendientes cuando el workflow pausa por aprobacion humana.
- Crea artifacts solo para acciones internas alcanzadas.
- Persiste ejecuciones en JSON local mediante `JsonRepository`.
- Audita inicio, creacion, finalizacion, bloqueo y revision de structured
  outputs con duracion en eventos terminales.
- Reanuda ejecuciones aprobadas desde el checkpoint correspondiente sin
  duplicar approvals ni artifacts previos.

## Componentes

- `src/ariwalabs/runtime.py`: orquestador principal.
- `src/ariwalabs/idempotency.py`: llaves, fingerprints y replay.
- `src/ariwalabs/repository.py`: persistencia JSON local.
- `src/ariwalabs/workflow_engine.py`: ejecucion declarativa de pasos.
- `src/ariwalabs/context_engine.py`: contexto compuesto.
- `src/ariwalabs/skill_executor.py`: ejecucion de skills mediante Model
  Gateway.
- `src/ariwalabs/evaluation_engine.py`: evaluacion posterior.
- `src/ariwalabs/approval_engine.py`: approvals pendientes.
- `src/ariwalabs/artifact_manager.py`: artifacts de acciones internas.
- `src/ariwalabs/audit.py`: eventos auditables.
- `src/ariwalabs/errors.py`: errores tipados del framework.

## Implementacion relacionada

- [completar-workflow-engine.md](../implements/completar-workflow-engine.md)
- [implementar-approval-engine.md](../implements/implementar-approval-engine.md)
- [implementar-artifact-manager.md](../implements/implementar-artifact-manager.md)
- [structured-outputs-recuperables.md](../implements/structured-outputs-recuperables.md)
- [control-idempotencia.md](../implements/control-idempotencia.md)
- [context-engine.md](../implements/context-engine.md)
- [evaluacion-independiente.md](../implements/evaluacion-independiente.md)
- [ejecucion-real-skills-model-gateway.md](../implements/ejecucion-real-skills-model-gateway.md)
- [sincronizar-runtime-airtable.md](../implements/sincronizar-runtime-airtable.md)
- [reanudar-workflows-aprobaciones.md](../implements/reanudar-workflows-aprobaciones.md)
- [errores-tipados-runtime-cli.md](../implements/errores-tipados-runtime-cli.md)
- [metricas-latencia.md](../implements/metricas-latencia.md)

## Pendiente

- Extender errores tipados a repositorio, validadores y adapters restantes.
- Decidir si la reanudacion se mantiene explicita o se dispara
  automaticamente al aprobar.
