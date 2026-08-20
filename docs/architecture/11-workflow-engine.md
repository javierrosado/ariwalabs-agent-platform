# Workflow Engine

Fecha: 2026-08-15

## Objetivo

Interpretar workflows declarativos locales y producir un estado de ejecucion
auditable para el Agent Runtime.

## Estado

Implementado en `src/ariwalabs/workflow_engine.py`.

## Pasos soportados

- `skill`
- `parallel`
- `condition`
- `approval`
- `action`
- `workflow`

## Reglas

- Cada step debe tener exactamente un tipo, salvo condiciones que envuelven un
  step anidado.
- Las approvals solo pueden apuntar a `company-director`.
- Las acciones externas con terminos como publish, message, contact o payment
  quedan bloqueadas.
- Las acciones internas permitidas son un conjunto cerrado.
- Si una skill recibe un structured output recuperable, el workflow pausa en
  `needs_structured_output_review`.

## Componentes

- `src/ariwalabs/workflow_engine.py`: interprete de workflows.
- `agents/*/workflows/*.yaml`: definiciones declarativas.
- `src/ariwalabs/runtime.py`: caller principal.
- `tests/unit/test_workflow_engine.py`: cobertura unitaria.

## Implementacion relacionada

- [completar-workflow-engine.md](../implements/completar-workflow-engine.md)
- [structured-outputs-recuperables.md](../implements/structured-outputs-recuperables.md)
- [pruebas-regresion-growth.md](../implements/pruebas-regresion-growth.md)
- [ejecucion-real-skills-model-gateway.md](../implements/ejecucion-real-skills-model-gateway.md)

## Ejecucion de skills

`WorkflowEngine` acepta un `SkillExecutor` opcional. Cuando existe, cada paso
`skill` invoca `ModelGateway` a traves del executor. Si la request trae
`__skill_results__`, esos fixtures tienen precedencia para regresion. Si no hay
executor, el engine conserva el modo simulado para compatibilidad.

## Reanudacion

`WorkflowEngine.run()` acepta `resume_after_checkpoint`. Cuando se informa, el
engine localiza el approval top-level con ese checkpoint y ejecuta solo los
pasos posteriores. `AgentRuntime.resume()` combina esos pasos con la ejecucion
previa.

## Pendiente

- Formalizar el contrato canonico de workflow, condiciones y paralelismo.
- Mejorar errores tipados para runtime y CLI.
