# Implementacion: ejecucion real de skills mediante Model Gateway

Fecha: 2026-08-15

## Objetivo

Conectar la ejecucion de pasos `skill` del workflow con `ModelGateway`, usando
prompts, schemas, perfiles logicos y contexto compuesto sin acoplar skills a un
proveedor concreto.

## Alcance

- Crear `SkillExecutor`.
- Resolver skill, prompt y output schema desde modo default o business pack.
- Inyectar `SkillExecutor` en `WorkflowEngine`.
- Crear `ModelGateway` desde `AgentRuntime` usando `adapters.models.factory`.
- Mantener fixtures `__skill_results__` como override para regresion.
- Hacer que `FakeModelAdapter` genere contenido minimo compatible con schemas
  estrictos.

## Archivos modificados

- `src/ariwalabs/skill_executor.py`
- `src/ariwalabs/workflow_engine.py`
- `src/ariwalabs/runtime.py`
- `adapters/models/fake.py`
- `tests/unit/test_skill_executor.py`
- `tests/integration/test_growth_runtime.py`
- `docs/architecture/10-skill-registry.md`
- `docs/architecture/11-workflow-engine.md`
- `docs/architecture/15-model-gateway.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/roadmap/implementation-roadmap.md`
- `README.md`
- `docs/session-log.md`

## Pasos ejecutados

1. Se creo `SkillExecutor`.
   - Resultado: carga `skill.yaml`, prompt de sistema, output schema y contexto
     compuesto para invocar `ModelGateway.generate_structured()`.

2. Se integro `WorkflowEngine` con executor opcional.
   - Resultado: los pasos `skill` ejecutan modelo cuando hay executor, usan
     fixtures `__skill_results__` cuando se inyectan, o simulan si no hay
     executor para compatibilidad.

3. Se integro `AgentRuntime`.
   - Resultado: el runtime crea un `ModelGateway` con provider configurado por
     `.env`; por defecto usa `FakeModelAdapter`.

4. Se reforzo `FakeModelAdapter`.
   - Resultado: genera contenido minimo compatible con schemas estrictos,
     permitiendo ejecuciones locales sin red.

5. Se agregaron pruebas.
   - Resultado: se cubre ejecucion default, ejecucion por business pack,
     precedencia de fixtures, prompt faltante y persistencia de `model_result`
     en runtime.

## Riesgos y deuda

- El adapter fake genera contenido estructuralmente valido, pero no semantico.
- La ejecucion de tools declaradas por skills sigue pendiente; aun no se
  despacha hacia adapters desde Tool Gateway.
- El resume posterior a approvals sigue pendiente.
