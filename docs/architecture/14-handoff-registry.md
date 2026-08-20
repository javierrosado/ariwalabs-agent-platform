# Handoff Registry

Fecha: 2026-08-15

## Objetivo

Validar contratos estructurados de entregas entre agentes, el director y agentes
futuros, incluyendo aprobacion, persistencia, errores e idempotencia.

## Estado

Implementado en `src/ariwalabs/handoff_registry.py` para contratos y en
`src/ariwalabs/handoff_runtime.py` para ejecucion local gobernada.

## Reglas

- Los handoffs viven en `docs/handoffs/*.yaml`.
- Cada handoff requiere id, version, productor, consumidor, trigger, input,
  output, precondiciones, approval, persistencia, errores e idempotencia.
- La version debe usar formato `N.N.N`.
- Los productores deben ser agentes existentes o consumidores externos
  conocidos.
- Los handoffs sensibles requieren aprobacion por `company-director`.
- Las estrategias de idempotencia deben estar declaradas.
- La ejecucion de un handoff aprobado valida payloads requeridos, persiste una
  transicion versionada, aplica idempotencia y audita `duration_ms`.

## Componentes

- `src/ariwalabs/handoff_registry.py`: carga y validacion.
- `src/ariwalabs/handoff_runtime.py`: ejecucion local de transiciones.
- `src/ariwalabs/cli.py`: comando `ariwalabs handoff execute`.
- `docs/handoffs/growth-marketing-handoffs.yaml`: contratos estructurados.
- `docs/handoffs/growth-marketing-handoffs.md`: descripcion humana.
- `docs/handoff-catalog.md`: catalogo documental.
- `shared/schemas/handoff.schema.json`: schema comun futuro.
- `src/ariwalabs/framework_validator.py`: validacion integrada.
- `tests/unit/test_handoff_registry.py`: cobertura unitaria.
- `tests/unit/test_handoff_runtime.py`: cobertura de ejecucion e idempotencia.

## Implementacion relacionada

- [completar-validacion-handoffs.md](../implements/completar-validacion-handoffs.md)
- [ejecutar-handoffs-runtime.md](../implements/ejecutar-handoffs-runtime.md)

## Pendiente

- Validar contra `shared/schemas/handoff.schema.json`.
- Sincronizar handoffs aprobados con Agent Registry y Airtable cuando exista
  tabla operacional canonica.
