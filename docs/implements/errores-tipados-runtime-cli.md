# Errores tipados en runtime y CLI

Fecha: 2026-08-15

## Objetivo

Hacer que fallos esperados del framework tengan tipos claros y que la CLI los
reporte como JSON consistente.

## Implementado

- Se agrego `src/ariwalabs/errors.py` con errores base del framework.
- `AgentRuntime.run()` valida request, agente y workflow antes de ejecutar.
- `AgentRuntime.resume()` usa errores tipados para estados no reanudables.
- Tool Gateway y Handoff Runtime usan errores tipados para approval requerido,
  tool/handoff inexistente y payload invalido.
- CLI traduce `AriwaLabsError` a respuesta JSON con `status`, `error_type` y
  `message` en comandos de agente, ejecucion y handoff.

## Archivos principales

- `src/ariwalabs/errors.py`
- `src/ariwalabs/runtime.py`
- `src/ariwalabs/tool_gateway.py`
- `src/ariwalabs/handoff_runtime.py`
- `src/ariwalabs/cli.py`
- `tests/integration/test_growth_runtime.py`

## Validaciones

- `.venv/Scripts/python.exe -m pytest tests/integration/test_growth_runtime.py tests/unit/test_approval_cli.py`
- `.venv/Scripts/python.exe -m ruff check src/ariwalabs/runtime.py src/ariwalabs/cli.py src/ariwalabs/errors.py`

## Pendiente posterior

Extender la taxonomia a validadores, repositorio y adapters restantes, evitando
mezclar errores de dominio con excepciones genericas.
