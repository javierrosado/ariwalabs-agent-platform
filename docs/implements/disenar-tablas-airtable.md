# Implementacion: Disenar tablas de Airtable

Fecha: 2026-07-26

## Objetivo

Implementar el item P1 "Disenar tablas de Airtable" de
`docs/implementation-backlog.md`.

## Alcance

- Definir campos, relaciones, claves externas, privacidad e idempotencia para
  las tablas Airtable del MVP.
- Alinear el catalogo ejecutable del adapter con el diseno documental.
- Agregar tests de contrato para tablas, campos de gobierno, privacidad y
  aprobaciones.
- No crear tablas reales en Airtable desde codigo.
- No conectar skills directamente con Airtable.

## Archivos modificados

- `docs/architecture/19-airtable-tables.md`
- `docs/architecture/18-airtable-adapter-contract.md`
- `adapters/airtable/schema.py`
- `tests/unit/test_airtable_schema.py`
- `tests/unit/test_airtable_adapter.py`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/disenar-tablas-airtable.md`

## Pasos ejecutados

1. Se reviso el estado actual, backlog, contexto de negocio y contrato del
   Airtable Adapter.
   - Resultado: el adapter existe, pero faltaba el modelo operacional completo.

2. Se revisaron handoffs y estructuras runtime.
   - Resultado: se identificaron campos fuente para `AgentExecutions`,
     `Approvals` y `Artifacts`.

3. Se creo `docs/architecture/19-airtable-tables.md`.
   - Resultado: contiene proposito, campos, tipos sugeridos, relaciones,
     privacidad e idempotencia para las 13 tablas del backlog.

4. Se actualizo `docs/architecture/18-airtable-adapter-contract.md`.
   - Resultado: el contrato apunta al diseno completo y al catalogo ejecutable
     en `adapters/airtable/schema.py`.

5. Se alineo `adapters/airtable/schema.py`.
   - Resultado: `AIRTABLE_TABLES` incluye campos requeridos mas estrictos,
     `privacy_fields` y `approval_fields`.

6. Se agregaron tests de contrato.
   - Resultado: validan que todas las tablas P1 esten declaradas, que tengan
     `Status`, `IdempotencyKey`, campos runtime, privacidad y aprobaciones.

7. Se ajustaron tests existentes del adapter.
   - Resultado: `AgentExecutions` usa los campos requeridos del nuevo contrato.

## Resultados de validacion

- `python3 -m compileall adapters tests/unit/test_airtable_adapter.py
  tests/unit/test_airtable_schema.py`
  - Resultado: paso.

- `PYTHONPATH=src:. python3` ejecutando manualmente tests de
  `test_airtable_schema.py`.
  - Resultado: paso.

- `PYTHONPATH=src:. python3` ejecutando manualmente tests contractuales del
  adapter.
  - Resultado: paso.

- Revision manual de lineas mayores a 100 caracteres en archivos tocados.
  - Resultado: paso; no se encontraron lineas sobre 100 caracteres.

## Validaciones pendientes

Los siguientes comandos deben ejecutarse desde la venv activa:

- `ariwalabs framework validate-repository --root .`
- `ruff check .`
- `mypy src`
- `pytest`

## Riesgos y deuda

- Las tablas reales aun deben crearse en Airtable.
- Las opciones exactas de single selects deben confirmarse en la base real.
- No existe sincronizacion runtime -> Airtable.
- La idempotencia end-to-end de workflows sigue pendiente.

## Siguiente paso recomendado

Implementar Model Gateway como siguiente bloque P1, manteniendo la creacion
fisica de tablas Airtable como tarea operacional guiada por el contrato.
