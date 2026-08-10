# Implementacion: Skill Registry

Fecha: 2026-07-24

## Objetivo

Implementar el item P0 "Implementar Skill Registry" de
`docs/implementation-backlog.md`.

## Alcance

- Crear un componente `SkillRegistry` dentro de `src/ariwalabs/`.
- Centralizar la validacion de ids, versiones, schemas, tools, aprobaciones y
  ownership de skills.
- Integrar el registry con `FrameworkValidator`.
- Mantener las integraciones externas desacopladas: ninguna skill llama
  directamente a Airtable, OpenAI, WhatsApp, LinkedIn ni otro proveedor.
- Mantener aprobacion humana obligatoria para skills de impacto comercial.

## Archivos modificados

- `src/ariwalabs/skill_registry.py`
- `src/ariwalabs/framework_validator.py`
- `tests/unit/test_skill_registry.py`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/2026-07-24-completar-schemas-skills.md`
- `docs/implements/2026-07-24-implementar-skill-registry.md`

## Pasos ejecutados

1. Se reviso el estado Git del repositorio.
   - Resultado: la rama `feature/fine-context` tenia cambios abiertos del item
     anterior de schemas.

2. Se revisaron los contratos existentes.
   - `src/ariwalabs/framework_validator.py`
   - `tests/unit/test_framework_validator.py`
   - `agents/*/agent.yaml`
   - `agents/*/skills/*/skill.yaml`
   - `shared/policies/global-agent-policy.yaml`

3. Se creo `src/ariwalabs/skill_registry.py`.
   - Resultado: el registry carga skills desde `agents/*/skills/*/skill.yaml`
     y construye registros internos con agente, owner, approvals, slug, id,
     version, schema, approvals y tools.

4. Se agregaron validaciones del registry.
   - Resultado: valida seccion `skill`, campos requeridos, tipo de campos,
     ids duplicados, convencion de ids, version `N.N.N`, tools permitidas y
     prohibidas, tools bloqueadas en `allowed`, skills sensibles con
     aprobacion y output schemas estrictos.

5. Se integro el registry con `FrameworkValidator`.
   - Resultado: `FrameworkValidator.validate_repository()` conserva validacion
     de estructura de agentes y delega validacion de skills/schemas al
     `SkillRegistry`.

6. Se agregaron tests unitarios.
   - Resultado: `tests/unit/test_skill_registry.py` cubre repositorio real,
     mismatch entre carpeta e id, tool prohibida en `allowed` y skill sensible
     sin aprobacion.

## Resultados de validacion

- `PYTHONPATH=src python3` ejecutando `SkillRegistry(Path(".")).validate_repository()`
  - Resultado: paso con `[]`.

- `PYTHONPATH=src python3` ejecutando `FrameworkValidator(Path(".")).validate_repository()`
  - Resultado: paso con `{'status': 'passed', 'findings': []}`.

- Simulacion manual de skill con id distinto al slug de carpeta.
  - Resultado: paso; el registry reporto `id debe terminar con sample-skill`.

- Simulacion manual de tool prohibida en `tools.allowed`.
  - Resultado: paso; el registry reporto `tools prohibidas en allowed`.

- Simulacion manual de skill sensible sin aprobacion.
  - Resultado: paso; el registry reporto `skill sensible requiere aprobacion`.

- `python3 -m compileall src tests adapters`
  - Resultado: paso.

- Revision manual de lineas mayores a 100 caracteres en `src/ariwalabs/*.py` y
  `tests/unit/*.py`
  - Resultado: paso; no se encontraron lineas sobre 100 caracteres.

- `git diff --check`
  - Resultado: paso.

## Validaciones bloqueadas por entorno

Los siguientes comandos se intentaron, pero no estan disponibles en este shell:

- `ariwalabs framework validate-repository --root .`
  - Resultado: fallo, `/bin/bash: ariwalabs: command not found`.
- `ruff check .`
  - Resultado: fallo, `/bin/bash: ruff: command not found`.
- `mypy src`
  - Resultado: fallo, `/bin/bash: mypy: command not found`.
- `pytest`
  - Resultado: fallo, `/bin/bash: pytest: command not found`.

## Riesgos y deuda

- La validacion de tools es todavia estructural y por nombres reservados; el
  Tool Gateway aun no existe.
- La compatibilidad semantica entre workflow steps y schemas queda pendiente
  para Workflow Engine.
- Las approvals se validan a nivel de presencia en `agent.yaml`, pero el
  Approval Engine completo sigue pendiente.

## Siguiente paso recomendado

Completar validacion de handoffs con contratos de productor/consumidor,
aprobacion, persistencia, errores e idempotencia.
