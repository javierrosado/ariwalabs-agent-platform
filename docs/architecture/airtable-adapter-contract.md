# Airtable Adapter Contract

Fecha: 2026-07-25

## Alcance MVP

El adapter permite leer, crear drafts y actualizar drafts en tablas Airtable
permitidas. No reemplaza aun la persistencia local JSON del runtime y no es
invocado directamente por skills.

El diseno operacional completo de tablas vive en
`docs/architecture/airtable-tables.md`. El catalogo ejecutable del adapter vive
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

## Reglas de gobierno

- Los secretos se leen desde `.env` o variables de entorno.
- `.env.example` no debe contener valores reales.
- Los logs no registran tokens ni headers de autorizacion.
- No existe borrado automatico en el MVP.
- Toda accion externa o comercial sensible sigue requiriendo aprobacion de
  `company-director`.

## Pendiente

Crear las tablas reales en Airtable, confirmar opciones de single selects e
implementar sincronizacion controlada desde runtime local hacia Airtable.
