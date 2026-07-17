# ADR-007: Integraciones mediante adapters

Fecha: 2026-07-17
Estado: aceptada

## Contexto

El proyecto necesitara OpenAI, Airtable, WhatsApp, email, calendarios,
publicacion social y posiblemente Azure. Acoplar skills a proveedores haria
dificil validar, probar y gobernar.

## Decision

Todas las integraciones externas deben pasar por `adapters/` o por el futuro
Tool Gateway.

## Alternativas

- Llamadas directas desde skills.
- Integraciones ad hoc por workflow.
- Automatizaciones externas sin contrato versionado.

## Consecuencias

- Mejor testabilidad y menor acoplamiento.
- Los adapters deben tener contratos, errores tipados y mocks.
- Las tools permitidas/prohibidas deben validarse centralmente.
