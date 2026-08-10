# Implementacion: Model Gateway

Fecha: 2026-07-26

## Objetivo

Implementar el item P1 "Implementar Model Gateway" de
`docs/implementation-backlog.md`.

## Alcance

- Enrutar perfiles logicos de modelos.
- Mantener skills desacopladas de modelos concretos y proveedores.
- Agregar adapter falso local para tests sin red.
- Auditar requests, errores, usage y costos opcionales sin registrar prompts ni
  payloads completos.
- Validar `model_profile` en skills.
- No integrar OpenAI aun.

## Archivos modificados

- `src/ariwalabs/model_gateway.py`
- `src/ariwalabs/skill_registry.py`
- `adapters/models/base.py`
- `adapters/models/errors.py`
- `adapters/models/fake.py`
- `tests/unit/test_model_gateway.py`
- `tests/unit/test_skill_registry.py`
- `docs/architecture/model-gateway.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/2026-07-26-implementar-model-gateway.md`

## Pasos ejecutados

1. Se reviso ADR-004 y el contrato `ModelAdapter`.
   - Resultado: el gateway debe operar con perfiles logicos y no con modelos
     concretos.

2. Se agregaron errores tipados.
   - Resultado: existen errores para configuracion, perfil, proveedor y salida.

3. Se amplio `adapters/models/base.py`.
   - Resultado: se agrego alias `ModelResult` y se mantuvo la firma
     `generate`.

4. Se creo `adapters/models/fake.py`.
   - Resultado: adapter deterministico sin red para tests y desarrollo local.

5. Se creo `src/ariwalabs/model_gateway.py`.
   - Resultado: enruta perfiles soportados, valida requests/resultados, audita
     eventos y registra usage/costos opcionales.

6. Se integro validacion de perfiles en `SkillRegistry`.
   - Resultado: skills con `model_profile` desconocido quedan bloqueadas por el
     validador del framework.

7. Se agregaron tests unitarios.
   - Resultado: cubren perfil valido, perfil invalido, schema vacio, fallo de
     adapter, auditoria de usage/costo y skill con perfil invalido.

## Resultados de validacion

- `python3 -m compileall adapters/models src/ariwalabs/model_gateway.py src/ariwalabs/skill_registry.py tests/unit/test_model_gateway.py tests/unit/test_skill_registry.py`
  - Resultado: paso.

- Revision manual de lineas mayores a 100 caracteres en archivos tocados.
  - Resultado: paso; no se encontraron lineas mayores a 100 caracteres.

- `PYTHONPATH=src:. python3` con smoke test de `ModelGateway`.
  - Resultado: paso; retorno `draft reasoning`.

- `PYTHONPATH=src:. python3` con `FrameworkValidator`.
  - Resultado: paso; `{'status': 'passed', 'findings': []}`.

- `PYTHONPATH=src:. python3` ejecutando manualmente tests nuevos de Model
  Gateway y Skill Registry.
  - Resultado: paso.

## Validaciones pendientes

Los siguientes comandos deben ejecutarse desde la venv activa:

- `ariwalabs framework validate-repository --root .`
- `ruff check .`
- `mypy src`
- `pytest`

## Riesgos y deuda

- OpenAI real aun no esta integrado.
- Structured outputs estrictos siguen como item separado.
- El Workflow Engine aun simula skills y no invoca Model Gateway para ejecucion
  real de skills.

## Siguiente paso recomendado

Integrar modelos OpenAI mediante adapter configurable por `.env`.
