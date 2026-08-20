# Architecture Alignment

Fecha: 2026-08-15

## Objetivo

Evaluar si `docs/architecture/01-framework-overview.md` esta alineado con lo
implementado actualmente en el repositorio.

## Veredicto

La arquitectura esta mayormente alineada con la implementacion actual, pero el
overview mezcla componentes ya implementados, componentes parciales y
componentes todavia conceptuales. La lectura correcta es que el diagrama
representa la arquitectura objetivo del framework local, no un inventario 100%
ejecutable.

## Implementacion relacionada

La evidencia historica de implementacion vive en `docs/implements/`. Para leer
la evolucion completa, empezar por los cierres P0/P1 y luego revisar las
implementaciones por componente:

- [cerrar-formalmente-p0.md](../implements/cerrar-formalmente-p0.md)
- [cerrar-formalmente-p1.md](../implements/cerrar-formalmente-p1.md)
- [implementar-skill-registry.md](../implements/implementar-skill-registry.md)
- [completar-workflow-engine.md](../implements/completar-workflow-engine.md)
- [implementar-approval-engine.md](../implements/implementar-approval-engine.md)
- [implementar-artifact-manager.md](../implements/implementar-artifact-manager.md)
- [implementar-audit-log-completo.md](../implements/implementar-audit-log-completo.md)
- [implementar-model-gateway.md](../implements/implementar-model-gateway.md)
- [context-engine.md](../implements/context-engine.md)
- [tool-gateway.md](../implements/tool-gateway.md)
- [evaluacion-independiente.md](../implements/evaluacion-independiente.md)

## Alineado

- `Agent Runtime` existe en `src/ariwalabs/runtime.py` y orquesta workflow,
  contexto, evaluacion, approvals, artifacts, auditoria e idempotencia.
- `Skill Registry` existe en `src/ariwalabs/skill_registry.py` y valida
  contratos declarativos de skills.
- `Workflow Engine` existe en `src/ariwalabs/workflow_engine.py` e interpreta
  pasos locales.
- `Context Engine` existe en `src/ariwalabs/context_engine.py` y compone
  contexto desde `shared/context/` y `shared/policies/`.
- `Model Gateway` existe en `src/ariwalabs/model_gateway.py` con perfiles
  logicos, adapters fake/OpenAI y structured outputs recuperables.
- `Tool Gateway` existe en `src/ariwalabs/tool_gateway.py` como catalogo y
  validador de tools declarativas.
- `Approval Engine` existe en `src/ariwalabs/approval_engine.py` con CLI para
  listar, aprobar y rechazar.
- `Evaluation Engine` existe en `src/ariwalabs/evaluation_engine.py` con
  rubricas por agente.
- `Artifact Manager` existe en `src/ariwalabs/artifact_manager.py`.
- `Audit` existe en `src/ariwalabs/audit.py` con eventos JSONL sanitizados.
- `Persistence` existe como `JsonRepository` local en
  `src/ariwalabs/repository.py`.
- `Airtable Adapter` existe en `adapters/airtable/` con contrato HTTP,
  errores tipados e idempotencia.
- `Model Adapter` existe en `adapters/models/`, incluyendo fake y OpenAI.
- Las politicas globales y el contexto compartido existen bajo `shared/`.
- Los agentes, skills, schemas, workflows y rubricas existen bajo `agents/`.
- Los handoffs existen bajo `docs/handoffs/` y se validan con
  `HandoffRegistry`.

## Parcial

- `Tool Gateway` gobierna catalogo y validacion, pero aun no despacha llamadas
  reales hacia adapters.
- `Workflow Engine` ejecuta skills mediante `SkillExecutor` y `ModelGateway`
  cuando el runtime provee executor; conserva fixtures `__skill_results__` y
  modo simulado para compatibilidad.
- `Context Engine` compone todo el contexto declarado por agente para el
  workflow; aun no selecciona subconjuntos por skill ni presupuesto de tokens.
- `Evaluation Engine` tiene rubricas base y evaluacion determinista; falta
  calibracion de criterios de dominio y uso productivo del evaluador de modelo.
- `Approval Engine` registra decisiones y `AgentRuntime.resume()` permite
  reanudar ejecuciones aprobadas desde el checkpoint correspondiente.
- `Persistence` es JSON local transitorio; Airtable ya puede recibir
  sincronizacion operacional explicita de ejecuciones, approvals y artifacts.
- `HandoffRegistry` valida contratos, pero no hay ejecucion runtime de
  handoffs entre agentes.

## Desalineado

- `Agent Registry` aparece en el diagrama como componente, pero no existe aun
  un modulo `src/ariwalabs/agent_registry.py`; el catalogo real sigue siendo la
  estructura versionada en `agents/`.
- El diagrama etiqueta el `Model Adapter` como "Proveedor de modelos futuro",
  pero ya hay adapters implementados en `adapters/models/`.
- El subgrafo del Growth & Marketing Agent muestra `handoffs/` dentro del
  agente; la implementacion actual ubica los contratos en `docs/handoffs/`.
- El ADR-002 aun dice que el checkout no contiene `.git`, mientras
  `docs/current-state.md` ya indica que existe `.git` y remote `origin`.

## Recomendacion

Mantener `01-framework-overview.md` como diagrama objetivo, pero ajustar sus
etiquetas para distinguir explicitamente `implementado`, `parcial` y `futuro`.
El siguiente incremento mas natural es reanudar workflows despues de approvals
o ejecutar tools reales mediante Tool Gateway.
