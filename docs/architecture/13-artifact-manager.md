# Artifact Manager

Fecha: 2026-08-15

## Objetivo

Registrar metadata de entregables generados por acciones internas del workflow,
sin publicar ni ejecutar acciones externas.

## Estado

Implementado en `src/ariwalabs/artifact_manager.py`.

## Reglas

- Todo artifact requiere `execution_id`, `agent_id`, `workflow_id`,
  `artifact_type` y `source_action`.
- Los estados validos son `draft`, `pending_approval`, `approved`, `rejected` y
  `archived`.
- El runtime crea artifacts solo para acciones internas alcanzadas.
- La metadata puede incluir approval asociado, checkpoint y si requiere
  aprobacion.
- La creacion de artifacts se audita.

## Componentes

- `src/ariwalabs/artifact_manager.py`: registro y listado de artifacts.
- `src/ariwalabs/runtime.py`: mapeo de acciones internas a tipos de artifact.
- `src/ariwalabs/repository.py`: persistencia JSON local.
- `src/ariwalabs/audit.py`: evento `artifact.created`.
- `tests/unit/test_artifact_manager.py`: cobertura unitaria.

## Implementacion relacionada

- [implementar-artifact-manager.md](../implements/implementar-artifact-manager.md)

## Pendiente

- Persistir contenido de artifacts con contrato mas rico.
- Sincronizar metadata hacia Airtable.
- Soportar versionado y promocion formal de estado.
