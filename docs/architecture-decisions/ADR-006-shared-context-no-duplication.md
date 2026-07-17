# ADR-006: Contexto compartido sin duplicacion

Fecha: 2026-07-17
Estado: aceptada

## Contexto

El contexto de empresa, oferta, audiencias y canales aplica a varios agentes y
puede cambiar con el tiempo.

## Decision

El contexto compartido vive en `shared/context/` y se referencia desde agentes.
No debe copiarse dentro de cada agente, prompt, skill o workflow.

## Alternativas

- Copiar contexto en cada prompt.
- Mantener contexto solo en documentacion libre.
- Guardar contexto en Airtable desde el inicio.

## Consecuencias

- Menos divergencia entre agentes.
- Se requiere Context Engine para componer contexto por ejecucion.
- Los cambios de contexto deben actualizar docs y pruebas afectadas.
