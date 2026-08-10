# Airtable Adapter

## Variables

- `AIRTABLE_TOKEN`
- `AIRTABLE_BASE_ID`

Los valores reales deben vivir en `.env` o en variables de entorno del proceso.
`.env.example` solo debe contener nombres de variables sin secretos.

## Tablas previstas

People, Organizations, TrainingPrograms, Cohorts, Enrollments, Campaigns,
ContentItems, Events, Referrals, Opportunities, Approvals, AgentExecutions,
Artifacts.

No implementar borrado automático en el MVP.

## Operaciones MVP

- `validate_access(table=None)`: valida credenciales y acceso a la base usando
  metadata; si se indica tabla, valida lectura no destructiva de esa tabla.
- `list_records(table, **filters)`: lista records de tablas permitidas usando
  filtros convertidos a `filterByFormula`.
- `create_draft(table, fields, idempotency_key=None)`: crea un record en estado
  `Draft`; si se entrega `idempotency_key`, busca primero por
  `IdempotencyKey`.
- `update_draft(table, record_id, fields)`: actualiza un record existente.

## Gobierno

- Las skills no llaman Airtable directamente.
- El adapter no publica, no envia mensajes externos y no aprueba acciones.
- Las decisiones comerciales siguen pasando por aprobacion humana.
- Los eventos del adapter se auditan sin registrar token ni headers de
  autorizacion.

## Errores tipados

- `AirtableConfigError`
- `AirtableTableError`
- `AirtableRemoteError`
- `AirtableRateLimitError`
- `AirtableIdempotencyError`

## Validacion de acceso

Desde la CLI local:

```bash
ariwalabs airtable validate-access --root . --env-file .env.example
```

Si el token no tiene permisos de metadata, se puede validar una tabla concreta:

```bash
ariwalabs airtable validate-access --root . --env-file .env.example --table Artifacts
```

La salida no incluye `AIRTABLE_TOKEN`.

## Crear tablas del contrato

El script `scripts/create_airtable_tables.py` crea las tablas y campos faltantes
desde `adapters/airtable/schema.py` usando Metadata API. Es idempotente: primero
lee metadata y luego crea solo lo faltante.

Modo simulacion:

```bash
PYTHONPATH=src:. python3 scripts/create_airtable_tables.py --root . --env-file .env --dry-run
```

Ejecucion real:

```bash
PYTHONPATH=src:. python3 scripts/create_airtable_tables.py --root . --env-file .env
```
