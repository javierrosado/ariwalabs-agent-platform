# Ejecutar handoffs en runtime

Fecha: 2026-08-15

## Objetivo

Materializar handoffs aprobados como transiciones versionadas entre productor y
consumidor, usando los contratos YAML ya validados por `HandoffRegistry`.

## Implementado

- `HandoffRegistry` expone `list_handoffs()` y `get_handoff()`.
- `HandoffRuntime` valida `input_payload` y `output_payload` contra campos
  requeridos del contrato.
- Los handoffs que requieren aprobacion fallan con error tipado si no reciben
  `approved=True`.
- Cada handoff persistido incluye version, productor, consumidor, trigger,
  approval, contrato, payloads, idempotencia, estado y `duration_ms`.
- La persistencia local usa `runtime/data/handoffs/`.
- El CLI agrega `ariwalabs handoff execute`.

## Archivos principales

- `src/ariwalabs/handoff_registry.py`
- `src/ariwalabs/handoff_runtime.py`
- `src/ariwalabs/cli.py`
- `tests/unit/test_handoff_runtime.py`

## Validaciones

- `.venv/Scripts/python.exe -m pytest tests/unit/test_handoff_registry.py tests/unit/test_handoff_runtime.py`
- `.venv/Scripts/python.exe -m ruff check src/ariwalabs/handoff_registry.py src/ariwalabs/handoff_runtime.py src/ariwalabs/cli.py tests/unit/test_handoff_runtime.py`

## Pendiente posterior

Definir una tabla operacional canonica para handoffs y sincronizar transiciones
aprobadas hacia Airtable/Agent Registry.
