# Metricas de latencia

Fecha: 2026-08-15

## Objetivo

Registrar duracion de operaciones relevantes del framework para diagnosticar
tiempos de ejecucion, modelo, tools, handoffs y adapters.

## Implementado

- `AgentRuntime` agrega `duration_ms` en eventos terminales de ejecucion,
  bloqueo, pausa, revision estructurada y reanudacion.
- `ModelGateway` agrega `duration_ms` en requests completados y fallidos.
- `ToolGateway` agrega `duration_ms` en ejecuciones completadas y fallidas.
- `HandoffRuntime` persiste y audita `duration_ms`.
- `AirtableHttpAdapter` audita `airtable.request.completed` con `duration_ms`
  y agrega duracion en errores remotos o rate-limit agotado.

## Archivos principales

- `src/ariwalabs/runtime.py`
- `src/ariwalabs/model_gateway.py`
- `src/ariwalabs/tool_gateway.py`
- `src/ariwalabs/handoff_runtime.py`
- `adapters/airtable/client.py`
- `tests/unit/test_model_gateway.py`
- `tests/unit/test_airtable_adapter.py`

## Validaciones

- `.venv/Scripts/python.exe -m pytest tests/unit/test_model_gateway.py tests/unit/test_airtable_adapter.py tests/unit/test_tool_gateway.py tests/unit/test_handoff_runtime.py`
- `.venv/Scripts/python.exe -m ruff check src/ariwalabs/model_gateway.py adapters/airtable/client.py src/ariwalabs/tool_gateway.py src/ariwalabs/handoff_runtime.py`

## Pendiente posterior

Agregar reportes agregados por workflow, skill, provider, adapter y business
pack.
