# Implementacion: Tool Gateway

Fecha: 2026-08-10

## Objetivo

Implementar el item P2 "Tool Gateway" para que las tools permitidas y
prohibidas por skill se resuelvan y validen desde un componente central.

## Alcance

- Crear un catalogo central de tools declarativas.
- Distinguir tools internas, tools via adapter y acciones externas bloqueadas.
- Validar tools desconocidas, solapamientos entre allowed/prohibited y acciones
  externas declaradas indebidamente como permitidas.
- Integrar la validacion central con `SkillRegistry`.
- No ejecutar tools reales ni despachar llamadas a adapters en runtime.

## Archivos modificados

- `src/ariwalabs/tool_gateway.py`
- `src/ariwalabs/skill_registry.py`
- `tests/unit/test_tool_gateway.py`
- `tests/unit/test_skill_registry.py`
- `docs/architecture/01-framework-overview.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/tool-gateway.md`

## Pasos ejecutados

1. Se reviso el estado actual, backlog, contexto del proyecto y ADRs de
   integraciones, Airtable, human-in-the-loop y persistencia local.
   - Resultado: se confirmo que Tool Gateway debia resolver el control central
     de declaraciones de tools sin introducir Docker, SQLite ni llamadas
     directas desde skills.

2. Se creo `src/ariwalabs/tool_gateway.py`.
   - Resultado: existe `ToolGateway` con catalogo central, metadata de tools y
     resolucion de allowed/prohibited.

3. Se movieron las reglas de tools fuera de `SkillRegistry`.
   - Resultado: `SkillRegistry` sigue cargando skills y delega la validacion de
     tools al gateway.

4. Se agregaron pruebas unitarias.
   - Resultado: cubren tools conocidas, tools desconocidas, solapamiento,
     acciones externas prohibidas como allowed y metadata resuelta del catalogo.

5. Se actualizo documentacion de estado y backlog.
   - Resultado: Tool Gateway queda marcado como implementado en P2, con deuda
     explicita sobre ejecucion real de tools/adapters.

## Resultados de validacion

- `.venv/Scripts/python.exe -m pytest tests/unit/test_tool_gateway.py \
  tests/unit/test_skill_registry.py tests/unit/test_framework_validator.py`
  - Resultado: paso con 14 tests.

- `.venv/Scripts/python.exe -m ruff check src/ariwalabs/tool_gateway.py \
  src/ariwalabs/skill_registry.py tests/unit/test_tool_gateway.py \
  tests/unit/test_skill_registry.py`
  - Resultado: paso.

- `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - Resultado: paso con `status=passed`.

- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 103 tests.

## Validaciones bloqueadas por entorno

`git diff --check` completo quedo bloqueado por archivos generados previamente
en `runtime/data/idempotency/`, que no forman parte de esta implementacion.
Se ejecuto `git diff --check` acotado a los archivos tocados por Tool Gateway.

## Riesgos y deuda

- Tool Gateway todavia no ejecuta tools ni despacha hacia adapters.
- El catalogo es estatico en codigo; en una etapa posterior podria moverse a un
  contrato versionado si crece el numero de integraciones.
- La autorizacion runtime por ejecucion queda pendiente hasta conectar skills
  reales con Model Gateway y adapters.

## Siguiente paso recomendado

Ejecutar la suite completa del protocolo y continuar con P2: evaluacion
independiente o Context Engine.
