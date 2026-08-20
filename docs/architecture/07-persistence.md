# Persistence

Fecha: 2026-08-15

## Objetivo

Persistir ejecuciones, approvals, artifacts, idempotencia y auditoria durante el
MVP local, manteniendo claro que Airtable sera el sistema operacional inicial.

## Estado

Implementado como persistencia JSON local transitoria en
`src/ariwalabs/repository.py`.

## Reglas

- No usar SQLite en el MVP.
- Los datos locales de runtime viven bajo `runtime/data/`.
- `runtime/` no debe tratarse como fuente de verdad tecnica.
- Airtable es el destino operacional previsto para entidades de negocio.
- Los secretos no se persisten en JSON ni en audit.

## Categorias actuales

- `executions`
- `approvals`
- `artifacts`
- `idempotency`
- `audit.jsonl`

## Componentes

- `src/ariwalabs/repository.py`: repositorio JSON local.
- `src/ariwalabs/runtime.py`: persistencia de ejecuciones.
- `src/ariwalabs/approval_engine.py`: persistencia de approvals.
- `src/ariwalabs/artifact_manager.py`: persistencia de artifacts.
- `src/ariwalabs/idempotency.py`: registros de idempotencia.
- `adapters/airtable/`: sistema operacional futuro/externo.
- `docs/architecture/19-airtable-tables.md`: contrato de tablas.

## Implementacion relacionada

- [implementar-approval-engine.md](../implements/implementar-approval-engine.md)
- [implementar-artifact-manager.md](../implements/implementar-artifact-manager.md)
- [control-idempotencia.md](../implements/control-idempotencia.md)
- [disenar-tablas-airtable.md](../implements/disenar-tablas-airtable.md)
- [crear-tablas-airtable.md](../implements/crear-tablas-airtable.md)
- [sincronizar-runtime-airtable.md](../implements/sincronizar-runtime-airtable.md)

## Pendiente

- Persistencia transaccional o mecanismo mas robusto para idempotencia.
- Politicas de limpieza de datos locales.
