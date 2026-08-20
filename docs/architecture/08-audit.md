# Audit

Fecha: 2026-08-15

## Objetivo

Mantener una traza append-only de eventos, decisiones, errores, validaciones,
artifacts y costos sin registrar secretos ni payloads sensibles completos.

## Estado

Implementado en `src/ariwalabs/audit.py`.

## Reglas

- Cada evento tiene `event_id`, timestamp UTC, tipo, severidad, actor,
  correlacion y payload sanitizado.
- Las claves sensibles se redactan.
- Los strings largos se truncan.
- La profundidad maxima del payload se limita para evitar logs excesivos.
- Los eventos se escriben en JSONL bajo `runtime/data/audit.jsonl`.
- Los eventos de ejecucion, requests de modelo, tools, handoffs y adapters
  registran `duration_ms` cuando aplica.

## Helpers

- `execution`
- `validation`
- `approval`
- `artifact`
- `error`
- `cost`

## Componentes

- `src/ariwalabs/audit.py`: logger canonico.
- `runtime/data/audit.jsonl`: salida local no versionada.
- `src/ariwalabs/runtime.py`: eventos de ejecucion.
- `src/ariwalabs/model_gateway.py`: eventos de modelo y costos.
- `src/ariwalabs/tool_gateway.py`: eventos de tools y bloqueo por aprobacion.
- `src/ariwalabs/handoff_runtime.py`: eventos de handoffs.
- `adapters/airtable/client.py`: eventos de requests Airtable.
- `src/ariwalabs/approval_engine.py`: eventos de aprobacion.
- `src/ariwalabs/artifact_manager.py`: eventos de artifacts.
- `tests/unit/test_audit.py`: cobertura unitaria.

## Implementacion relacionada

- [implementar-audit-log-completo.md](../implements/implementar-audit-log-completo.md)
- [implementar-approval-engine.md](../implements/implementar-approval-engine.md)
- [implementar-artifact-manager.md](../implements/implementar-artifact-manager.md)
- [metricas-costos-tokens.md](../implements/metricas-costos-tokens.md)
- [metricas-latencia.md](../implements/metricas-latencia.md)

## Pendiente

- Definir retencion y exportacion operacional.
- Unificar taxonomia completa de eventos cuando aumenten adapters y tools.
