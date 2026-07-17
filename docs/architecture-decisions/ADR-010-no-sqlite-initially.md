# ADR-010: No usar SQLite inicialmente

Fecha: 2026-07-17
Estado: aceptada

## Contexto

El MVP necesita evitar una doble fuente operacional entre base local y Airtable.
La persistencia JSON local solo sirve para trazas y ejecuciones durante el
esqueleto.

## Decision

No se usara SQLite inicialmente. Airtable sera el sistema operacional y JSON
local se mantendra como persistencia transitoria no versionada.

## Alternativas

- SQLite local para MVP.
- PostgreSQL desde el inicio.
- Solo archivos JSON.

## Consecuencias

- Menos migraciones tempranas.
- Airtable Adapter se vuelve prioridad.
- La persistencia local debe permanecer claramente limitada.
