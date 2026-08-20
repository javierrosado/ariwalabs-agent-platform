# Approval Engine

Fecha: 2026-08-15

## Objetivo

Registrar checkpoints de aprobacion humana y decisiones de Javier antes de
cualquier accion externa, comercial, reputacional o de release.

## Estado

Implementado en `src/ariwalabs/approval_engine.py` con comandos CLI.

## Reglas

- El unico aprobador valido en el MVP es `company-director`.
- Las decisiones validas son `approved` y `rejected`.
- Toda decision requiere una razon no vacia.
- Las decisiones actualizan la ejecucion relacionada.
- Una decision `approved` deja la ejecucion en `approved_pending_resume`; la
  continuacion se ejecuta explicitamente con `ariwalabs execution resume`.
- Toda creacion y decision se audita.

## Componentes

- `src/ariwalabs/approval_engine.py`: creacion, listado y decision.
- `src/ariwalabs/cli.py`: comandos `ariwalabs approval list` y
  `ariwalabs approval decide`.
- `src/ariwalabs/repository.py`: persistencia local de approvals.
- `src/ariwalabs/audit.py`: eventos de approval.
- `tests/unit/test_approval_engine.py`: cobertura unitaria.
- `tests/unit/test_approval_cli.py`: cobertura CLI.

## Implementacion relacionada

- [implementar-approval-engine.md](../implements/implementar-approval-engine.md)
- [implementar-cli-aprobaciones.md](../implements/implementar-cli-aprobaciones.md)
- [reanudar-workflows-aprobaciones.md](../implements/reanudar-workflows-aprobaciones.md)

## Estados relacionados

- `pending`
- `approved`
- `rejected`
- `approved_pending_resume`

## Pendiente

- Decidir si el resume sera automatico o seguira como accion explicita.
- Mejorar filtros y vistas operativas para pendientes.
