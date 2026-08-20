# Airtable Adapter Contract

Fecha: 2026-07-25

## Alcance MVP

El adapter permite leer, crear drafts y actualizar drafts en tablas Airtable
permitidas. No reemplaza aun la persistencia local JSON del runtime y no es
invocado directamente por skills.

La sincronizacion operacional desde JSON local hacia Airtable se ejecuta con
`src/ariwalabs/airtable_sync.py` y el comando `ariwalabs airtable
sync-execution`.

El diseno operacional completo de tablas vive en
`docs/architecture/19-airtable-tables.md`. El catalogo ejecutable del adapter vive
en `adapters/airtable/schema.py` y debe mantenerse alineado con ese documento.

## Tablas permitidas

- `Approvals`
- `AgentExecutions`
- `Artifacts`
- `Campaigns`
- `Cohorts`
- `ContentItems`
- `Enrollments`
- `Events`
- `Opportunities`
- `Organizations`
- `People`
- `Referrals`
- `TrainingPrograms`

## Campos comunes

- `Status`: estado operacional del record.
- `IdempotencyKey`: clave opcional para evitar duplicados.
- `CreatedAt`: fecha operacional cuando el record proviene del runtime.
- `Source`: origen operacional cuando aplica.

## Operaciones

- `validate_access(table=None)`.
- `list_records(table, **filters)`.
- `create_draft(table, fields, idempotency_key=None)`.
- `update_draft(table, record_id, fields)`.
- `ariwalabs airtable sync-execution <execution_id>`.

## Reglas de gobierno

- Los secretos se leen desde `.env` o variables de entorno.
- `.env.example` no debe contener valores reales.
- Los logs no registran tokens ni headers de autorizacion.
- No existe borrado automatico en el MVP.
- Toda accion externa o comercial sensible sigue requiriendo aprobacion de
  `company-director`.

## Implementacion relacionada

- [implementar-airtable-adapter.md](../implements/implementar-airtable-adapter.md)
- [disenar-tablas-airtable.md](../implements/disenar-tablas-airtable.md)
- [crear-tablas-airtable.md](../implements/crear-tablas-airtable.md)
- [sincronizar-runtime-airtable.md](../implements/sincronizar-runtime-airtable.md)

## Pendiente

Confirmar opciones de single selects y decidir si la sincronizacion seguira
siendo accion CLI explicita o si se habilitara auto-sync gobernado desde
runtime.
