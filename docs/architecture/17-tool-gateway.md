# Tool Gateway

Fecha: 2026-08-15

## Objetivo

Centralizar el catalogo de tools y validar que las skills solo declaren tools
permitidas por la politica del framework.

## Estado

Implementado como catalogo, validador y despachador gobernado en
`src/ariwalabs/tool_gateway.py`.

## Reglas

- Las skills pueden declarar `tools.allowed` y `tools.prohibited`.
- Una tool no puede estar simultaneamente permitida y prohibida.
- Las tools desconocidas bloquean la validacion.
- Las tools marcadas como no permitidas en skills no pueden aparecer en
  `tools.allowed`.
- Acciones externas como publicar, enviar mensajes o procesar pagos no pueden
  ejecutarse desde skills en el MVP.
- Las tools ejecutables validan contrato minimo de input/output.
- Las tools con `requires_approval=true` fallan con error tipado si no reciben
  aprobacion explicita.
- Las integraciones externas se ejecutan solo mediante adapters inyectados.
- Cada ejecucion audita inicio, fin, bloqueo por aprobacion y `duration_ms`.

## Catalogo actual

- `airtable-read`
- `airtable-write-draft`
- `artifact-create`
- `audit-append`
- `external-publish`
- `external-message`
- `payment`

## Componentes

- `src/ariwalabs/tool_gateway.py`: catalogo, resolucion y validacion.
- `src/ariwalabs/errors.py`: errores tipados de Tool Gateway.
- `src/ariwalabs/skill_registry.py`: integracion con validacion de skills.
- `adapters/airtable/`: adapter externo usado por `airtable-read` y
  `airtable-write-draft` cuando se inyecta explicitamente.
- `tests/unit/test_tool_gateway.py`: cobertura unitaria.

## Implementacion relacionada

- [tool-gateway.md](../implements/tool-gateway.md)
- [ejecutar-tools-tool-gateway.md](../implements/ejecutar-tools-tool-gateway.md)
- [implementar-airtable-adapter.md](../implements/implementar-airtable-adapter.md)

## Pendiente

- Invocar tools como pasos declarativos de workflows solo donde exista contrato
  explicito y politica de aprobacion.
- Ampliar catalogo de tools internas y externas sin permitir llamadas directas
  desde skills.
