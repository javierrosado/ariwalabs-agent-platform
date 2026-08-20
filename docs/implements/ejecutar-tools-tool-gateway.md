# Ejecutar tools mediante Tool Gateway

Fecha: 2026-08-15

## Objetivo

Convertir `ToolGateway` de catalogo declarativo a puerta ejecutable gobernada,
sin permitir que las skills llamen APIs externas directamente.

## Implementado

- Se agregaron contratos de input/output al catalogo de tools.
- Se agrego `ToolExecutionRequest` y `ToolExecutionResult`.
- `audit-append` y `artifact-create` ejecutan acciones internas locales.
- `airtable-read` y `airtable-write-draft` despachan hacia adapter Airtable
  inyectado.
- `airtable-write-draft` requiere aprobacion explicita.
- Acciones externas bloqueadas siguen fuera de `tools.allowed` para skills.
- Cada ejecucion audita inicio, fin, bloqueo por aprobacion y `duration_ms`.

## Archivos principales

- `src/ariwalabs/tool_gateway.py`
- `src/ariwalabs/errors.py`
- `tests/unit/test_tool_gateway.py`

## Validaciones

- `.venv/Scripts/python.exe -m pytest tests/unit/test_tool_gateway.py`
- `.venv/Scripts/python.exe -m ruff check src/ariwalabs/tool_gateway.py tests/unit/test_tool_gateway.py src/ariwalabs/errors.py`

## Pendiente posterior

Invocar tools desde workflows o skills solo cuando exista un contrato explicito
por accion, approval aplicable y adapter configurado.
