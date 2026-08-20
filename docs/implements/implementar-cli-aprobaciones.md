# Implementacion: CLI de aprobaciones

Fecha: 2026-07-25

## Objetivo

Implementar el item P1 "Implementar CLI de aprobaciones" de
`docs/implementation-backlog.md`.

## Alcance

- Exponer `ApprovalEngine` desde el CLI `ariwalabs`.
- Permitir listar approvals pendientes.
- Permitir aprobar o rechazar con razon registrada.
- Mantener `company-director` como unico decisor.
- No reanudar workflows ni ejecutar acciones externas automaticamente.

## Archivos modificados

- `src/ariwalabs/cli.py`
- `tests/unit/test_approval_cli.py`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/implementar-cli-aprobaciones.md`

## Comandos agregados

```bash
ariwalabs approval list --root .
ariwalabs approval decide <approval_id> --decision approved --reason "..." --root .
ariwalabs approval decide <approval_id> --decision rejected --reason "..." --root .
```

## Pasos ejecutados

1. Se reviso `src/ariwalabs/cli.py`.
   - Resultado: el CLI tenia comandos `framework`, `agent` y `execution`, pero
     no aprobaciones.

2. Se agrego el subcomando `approval`.
   - Resultado: `approval list` imprime approvals pendientes en JSON y
     `approval decide` llama `ApprovalEngine.decide()`.

3. Se agregaron tests unitarios.
   - Resultado: `tests/unit/test_approval_cli.py` cubre listado, aprobacion,
     rechazo, falta de `--reason` y decision invalida.

## Resultados de validacion

- `PYTHONPATH=src python3` ejecutando `ariwalabs approval list` via `main()`.
  - Resultado: paso; imprimio approval pendiente en JSON.

- `PYTHONPATH=src python3` ejecutando `ariwalabs approval decide ...`.
  - Resultado: paso; aprobo el approval y actualizo la ejecucion a
    `approved_pending_resume`.

- `python3 -m compileall src tests adapters`
  - Resultado: paso.

- Revision manual de lineas mayores a 100 caracteres en `src/ariwalabs/*.py`,
  `tests/unit/*.py` y `tests/integration/*.py`.
  - Resultado: paso; no se encontraron lineas sobre 100 caracteres.

## Validaciones bloqueadas por entorno

Los siguientes comandos se intentaron, pero no estan disponibles en este shell:

- `ariwalabs framework validate-repository --root .`
- `ruff check .`
- `mypy src`
- `pytest`

## Riesgos y deuda

- Aprobar desde CLI no reanuda workflows todavia; mantiene
  `approved_pending_resume`.
- No existe todavia comando para ver detalle de una ejecucion.
- La persistencia sigue siendo JSON local hasta implementar Airtable Adapter.

## Siguiente paso recomendado

Implementar Artifact Manager para registrar artefactos con metadata, origen,
version y estado.
