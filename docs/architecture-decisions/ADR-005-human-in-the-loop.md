# ADR-005: Human-in-the-loop obligatorio

Fecha: 2026-07-17
Estado: aceptada

## Contexto

Los agentes pueden generar campanas, briefs, recomendaciones y oportunidades que
impactan reputacion, privacidad, presupuesto o relaciones comerciales.

## Decision

Javier debe aprobar toda accion externa, release, publicacion, mensaje,
presupuesto, uso de nombre de cliente, cambio comercial sensible y registro de
oportunidad corporativa.

## Alternativas

- Automatizar publicaciones y contactos.
- Permitir aprobaciones por varios operadores desde el MVP.
- Aprobar solo por convencion manual sin registro.

## Consecuencias

- El Approval Engine y su CLI son componentes criticos.
- Las ejecuciones deben poder pausar y reanudarse.
- Toda decision debe quedar auditada.
