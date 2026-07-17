# ADR-009: WhatsApp mediante WhatsApp Business Platform, no WhatsApp Web

Fecha: 2026-07-17
Estado: aceptada

## Contexto

WhatsApp puede ser canal operativo para captacion y comunicacion, pero requiere
cumplir politicas, consentimiento y trazabilidad.

## Decision

Cuando se implemente, WhatsApp debe integrarse mediante WhatsApp Business
Platform, adapter o automatizacion gobernada. No se usara WhatsApp Web como
integracion automatizada.

## Alternativas

- Automatizar WhatsApp Web.
- Gestionar mensajes manualmente sin registro.
- Posponer WhatsApp indefinidamente.

## Consecuencias

- Mayor cumplimiento y estabilidad.
- Requiere consentimiento, templates, aprobaciones y auditoria.
- No forma parte del MVP inmediato.
