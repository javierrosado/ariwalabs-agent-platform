# Implementacion: completar schemas de skills

Fecha: 2026-07-24

## Objetivo

Completar el item P0 "Completar schemas de skills" de
`docs/implementation-backlog.md`.

## Alcance

- Endurecer los output schemas del Growth & Marketing Agent.
- Endurecer el schema de reportes del Framework Agent.
- Agregar validacion automatica basica de schemas declarados por skills.
- Mantener el contexto institucional en `shared/context/`.
- Mantener aprobacion humana obligatoria para campanas, bootcamps, referidos y
  oportunidades corporativas.
- No conectar skills directamente con Airtable, OpenAI, WhatsApp, LinkedIn ni
  otros proveedores externos.

## Archivos modificados

- `agents/framework-agent/schemas/framework-report.schema.json`
- `agents/growth-marketing-agent/schemas/audience-segmentation.schema.json`
- `agents/growth-marketing-agent/schemas/bootcamp-planning.schema.json`
- `agents/growth-marketing-agent/schemas/brand-compliance.schema.json`
- `agents/growth-marketing-agent/schemas/campaign-design.schema.json`
- `agents/growth-marketing-agent/schemas/content-planning.schema.json`
- `agents/growth-marketing-agent/schemas/corporate-opportunity-detection.schema.json`
- `agents/growth-marketing-agent/schemas/growth-analytics.schema.json`
- `agents/growth-marketing-agent/schemas/referral-program.schema.json`
- `agents/growth-marketing-agent/schemas/request-validation.schema.json`
- `agents/growth-marketing-agent/schemas/student-journey.schema.json`
- `agents/growth-marketing-agent/schemas/value-proposition.schema.json`
- `src/ariwalabs/framework_validator.py`
- `tests/unit/test_framework_validator.py`
- `docs/current-state.md`
- `docs/session-log.md`
- `docs/implements/completar-schemas-skills.md`

## Pasos ejecutados

1. Se reviso el estado Git del repositorio.
   - Resultado: rama `feature/fine-context` sincronizada con
     `origin/feature/fine-context` antes de iniciar cambios.

2. Se revisaron los contratos afectados.
   - `agents/growth-marketing-agent/agent.yaml`
   - `agents/growth-marketing-agent/skills/*/skill.yaml`
   - `agents/growth-marketing-agent/workflows/*.yaml`
   - `docs/handoff-catalog.md`
   - `docs/handoffs/growth-marketing-handoffs.md`
   - `shared/context/*.yaml`
   - `shared/policies/global-agent-policy.yaml`

3. Se reemplazaron los schemas permisivos del Growth & Marketing Agent.
   - Resultado: todos los schemas pasaron de `additionalProperties: true` sin
     campos requeridos a contratos con `required`, `properties`, tipos y
     `additionalProperties: false`.

4. Se endurecio `framework-report.schema.json`.
   - Resultado: `findings` ahora exige `severity`, `code`, `message`, `path`,
     `component`, `recommendation` y `blocking`.

5. Se agrego validacion de output schemas al `FrameworkValidator`.
   - Resultado: el validador comprueba existencia del schema declarado por cada
     skill, JSON parseable, `type: object`, `required`, `properties`,
     `additionalProperties: false` y presencia de `errors` o `findings`.

6. Se agregaron tests unitarios.
   - Resultado: hay pruebas para confirmar que el repositorio real no queda
     bloqueado por schemas y que un schema permisivo minimo si queda bloqueado.

## Resultados de validacion

- `python3 -m json.tool` sobre `agents/framework-agent/schemas/framework-report.schema.json`
  y `agents/growth-marketing-agent/schemas/*.schema.json`
  - Resultado: paso.

- `PYTHONPATH=src python3` ejecutando `FrameworkValidator(Path(".")).validate_repository()`
  - Resultado: paso con `{'status': 'passed', 'findings': []}`.

- `python3 -m compileall src tests adapters`
  - Resultado: paso.

- Prueba manual equivalente al caso unitario de schema permisivo.
  - Resultado: paso; el validador devolvio `status: blocked`.

- Revision manual de lineas mayores a 100 caracteres en
  `src/ariwalabs/framework_validator.py` y
  `tests/unit/test_framework_validator.py`
  - Resultado: paso; no se encontraron lineas sobre 100 caracteres.

## Validaciones bloqueadas por entorno

Los siguientes comandos se intentaron, pero no estan disponibles en el shell
actual:

- `ariwalabs framework validate-repository --root .`
  - Resultado: fallo, `/bin/bash: ariwalabs: command not found`.
- `ruff check .`
  - Resultado: fallo, `/bin/bash: ruff: command not found`.
- `mypy src`
  - Resultado: fallo, `/bin/bash: mypy: command not found`.
- `pytest`
  - Resultado: fallo, `/bin/bash: pytest: command not found`.

## Riesgos y deuda

- Los schemas ya son estrictos, pero todavia no existe un Workflow Engine que
  valide payloads entre pasos.
- El contrato comun de outputs esta repetido en cada schema; podria extraerse a
  `shared/schemas/` cuando se defina una politica de referencias compartidas.
- La validacion agregada es estructural; no valida todavia semantica completa de
  tools, approvals, handoffs ni compatibilidad entre workflows y schemas.

## Siguiente paso recomendado

Implementar el Skill Registry para centralizar validacion de ids, versiones,
schemas, tools, aprobaciones y ownership.
