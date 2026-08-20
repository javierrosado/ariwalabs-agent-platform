# Context Engine

Fecha: 2026-08-15

## Objetivo

Componer contexto empresarial compartido por agente y workflow sin duplicarlo en
agentes, prompts, skills ni workflows.

## Estado

Implementado en `src/ariwalabs/context_engine.py`.

## Reglas

- El contexto debe declararse como rutas en `agent.yaml`.
- Solo se permiten fuentes bajo `shared/context/` y `shared/policies/`.
- No se permiten rutas absolutas ni rutas con `..`.
- Las fuentes deben ser YAML no vacio y con objeto raiz.
- El contexto compuesto se persiste dentro de ejecuciones nuevas.

## Componentes

- `src/ariwalabs/context_engine.py`: composicion y validacion.
- `shared/context/*.yaml`: contexto empresarial compartido.
- `shared/policies/global-agent-policy.yaml`: politica global.
- `agents/*/agent.yaml`: declaracion de `shared_context`.
- `src/ariwalabs/framework_validator.py`: validacion integrada.
- `src/ariwalabs/runtime.py`: persistencia del contexto compuesto.
- `tests/unit/test_context_engine.py`: cobertura unitaria.

## Implementacion relacionada

- [context-engine.md](../implements/context-engine.md)

## Pendiente

- Seleccionar subconjuntos de contexto por skill.
- Incorporar presupuesto de tokens.
- Versionar snapshots de contexto con mayor granularidad.
