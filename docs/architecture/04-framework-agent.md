# Framework Agent

Fecha: 2026-08-15

## Objetivo

Gobernar definiciones de agentes, validaciones, releases y contratos del
framework sin ejecutar tareas comerciales.

## Estado

Definido declarativamente en `agents/framework-agent/` y ejecutable por el
runtime local como agente del repositorio.

## Reglas

- No ejecuta tareas comerciales.
- Opera sobre agentes, skills, workflows, schemas, handoffs y releases.
- Sus acciones sensibles requieren aprobacion de `company-director`.
- Usa contexto y politicas compartidas desde `shared/`.

## Componentes

- `agents/framework-agent/agent.yaml`: definicion del agente.
- `agents/framework-agent/skills/*/skill.yaml`: skills declarativas.
- `agents/framework-agent/workflows/*.yaml`: workflows de onboarding,
  validacion y release.
- `agents/framework-agent/schemas/framework-report.schema.json`: schema de
  reporte.
- `agents/framework-agent/evaluations/rubrics.yaml`: rubricas.
- `src/ariwalabs/framework_validator.py`: validador usado por CLI.
- `src/ariwalabs/runtime.py`: ejecucion local.

## Implementacion relacionada

- [completar-schemas-skills.md](../implements/completar-schemas-skills.md)
- [implementar-skill-registry.md](../implements/implementar-skill-registry.md)
- [completar-validacion-handoffs.md](../implements/completar-validacion-handoffs.md)
- [completar-workflow-engine.md](../implements/completar-workflow-engine.md)
- [evaluacion-independiente.md](../implements/evaluacion-independiente.md)

## Pendiente

- Conectar sus skills a ejecucion real mediante Model Gateway.
- Integrarlo con un Agent Registry formal.
- Completar flujo de release con aprobacion y reanudacion.
