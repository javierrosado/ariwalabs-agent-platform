# ADR-003: Airtable como sistema operacional inicial

Fecha: 2026-07-17
Estado: aceptada

## Contexto

AriwaLabs necesita operar personas, organizaciones, cohortes, campanas,
referidos, oportunidades, aprobaciones, ejecuciones y artefactos sin construir
una app administrativa completa al inicio.

## Decision

Airtable sera el sistema operacional inicial del MVP.

## Alternativas

- SQLite local.
- PostgreSQL.
- Google Sheets.
- CRM dedicado desde el inicio.

## Consecuencias

- Se requiere Airtable Adapter desacoplado.
- Las skills no pueden llamar Airtable directamente.
- Hay que disenar tablas, relaciones, permisos, idempotencia y privacidad.
