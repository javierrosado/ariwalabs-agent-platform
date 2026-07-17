# ADR-002: GitHub como fuente de verdad tecnica

Fecha: 2026-07-17
Estado: aceptada

## Contexto

El framework, agentes, prompts, schemas, politicas, pruebas y documentacion
deben sobrevivir entre sesiones y quedar auditables.

## Decision

GitHub sera la fuente de verdad tecnica del proyecto. Los cambios deben pasar
por validaciones locales y, cuando corresponda, pull request.

## Alternativas

- Mantener contexto solo en conversaciones.
- Usar documentos externos como fuente primaria.
- Guardar decisiones en herramientas operacionales.

## Consecuencias

- La memoria durable vive en archivos del repositorio.
- El checkout debe estar bajo Git; actualmente esta ruta no contiene `.git`.
- Secretos y datos sensibles quedan fuera de Git.
