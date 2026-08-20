# Implementacion: sincronizar runtime local hacia Airtable

Fecha: 2026-08-15

## Objetivo

Sincronizar ejecuciones, approvals y artifacts desde la persistencia JSON local
hacia Airtable usando el adapter existente, con idempotencia y auditoria.

## Alcance

- Crear `AirtableSync`.
- Mapear ejecuciones a `AgentExecutions`.
- Mapear approvals a `Approvals`.
- Mapear artifacts a `Artifacts`.
- Usar `AirtableHttpAdapter.create_draft()` con `IdempotencyKey`.
- Agregar comando CLI `ariwalabs airtable sync-execution`.
- Mantener la sincronizacion como accion explicita, no automatica.

## Archivos modificados

- `src/ariwalabs/airtable_sync.py`
- `src/ariwalabs/cli.py`
- `tests/unit/test_airtable_sync.py`
- `tests/unit/test_airtable_cli.py`
- `docs/architecture/18-airtable-adapter-contract.md`
- `docs/architecture/19-airtable-tables.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/roadmap/implementation-roadmap.md`
- `README.md`
- `docs/session-log.md`

## Pasos ejecutados

1. Se creo `AirtableSync`.
   - Resultado: sincroniza una ejecucion local y sus registros relacionados.

2. Se mapearon contratos Airtable.
   - Resultado: `AgentExecutions`, `Approvals` y `Artifacts` reciben campos
     requeridos del contrato documentado.

3. Se agrego idempotencia.
   - Resultado: cada escritura usa llaves `AgentExecutions:<execution_id>`,
     `Approvals:<approval_id>` y `Artifacts:<artifact_id>`.

4. Se agrego CLI.
   - Resultado: `ariwalabs airtable sync-execution <execution_id>` ejecuta la
     sincronizacion con credenciales de `.env`.

5. Se agregaron pruebas.
   - Resultado: se cubren mapeos, records relacionados, approvals decididos,
     campos requeridos y cableado CLI sin red.

## Riesgos y deuda

- La sincronizacion es explicita; aun no existe politica para auto-sync desde
  cada ejecucion del runtime.
- No se crean links Airtable entre records; se guardan llaves externas estables.
- La sincronizacion depende de que las tablas existan con campos compatibles.
