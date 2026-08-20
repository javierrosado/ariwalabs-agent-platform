# Evaluation Engine

Fecha: 2026-08-15

## Objetivo

Evaluar outputs de skills de forma separada de la generacion, usando rubricas
versionadas por agente y validaciones deterministas.

## Estado

Implementado en `src/ariwalabs/evaluation_engine.py`.

## Reglas

- Cada agente debe tener `evaluations/rubrics.yaml`.
- Debe existir una rubrica por cada `skill_id` declarado.
- Las rubricas deben tener version, `min_score` y criterios ponderados.
- La evaluacion determinista revisa schema, errores, approvals y politicas.
- Opcionalmente puede invocar un evaluador mediante Model Gateway con perfil
  `evaluation`.

## Componentes

- `src/ariwalabs/evaluation_engine.py`: validacion y evaluacion.
- `agents/*/evaluations/rubrics.yaml`: rubricas versionadas.
- `agents/*/schemas/*.schema.json`: contratos usados para evaluar outputs.
- `src/ariwalabs/runtime.py`: persistencia de `evaluation` por ejecucion.
- `src/ariwalabs/framework_validator.py`: validacion integrada.
- `tests/unit/test_evaluation_engine.py`: cobertura unitaria.

## Implementacion relacionada

- [evaluacion-independiente.md](../implements/evaluacion-independiente.md)
- [completar-schemas-skills.md](../implements/completar-schemas-skills.md)

## Eventos auditados

- `evaluation.workflow.started`
- `evaluation.workflow.completed`

## Pendiente

- Calibrar criterios especificos por dominio.
- Usar evaluacion de modelo en runtime productivo.
- Registrar metricas historicas de calidad por skill y version.
