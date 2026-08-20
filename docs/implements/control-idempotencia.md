# Implementacion: Control de idempotencia

Fecha: 2026-08-10

## Objetivo

Implementar el item P2 "Control de idempotencia" para que requests repetidos no
dupliquen approvals, opportunities ni artifacts.

## Alcance

- Agregar llaves de idempotencia por request/workflow.
- Permitir `idempotency_key` explicita en el request.
- Derivar una llave automatica cuando el request no trae llave explicita.
- Guardar un indice local transitorio en JSON.
- Reusar la ejecucion previa si llega el mismo request.
- Evitar duplicar approvals y artifacts en replays.
- Rechazar una misma llave usada con request distinto.
- No introducir SQLite, Docker ni integraciones externas nuevas.

## Archivos modificados

- `src/ariwalabs/idempotency.py`
- `src/ariwalabs/repository.py`
- `src/ariwalabs/runtime.py`
- `tests/unit/test_idempotency.py`
- `tests/integration/test_growth_runtime.py`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/control-idempotencia.md`

## Pasos ejecutados

1. Se reviso backlog, current-state, ADR-003, ADR-005, ADR-007 y ADR-010.
   - Resultado: la idempotencia debe vivir en runtime/adapters, mantener
     aprobacion humana y usar persistencia JSON local transitoria.

2. Se creo `src/ariwalabs/idempotency.py`.
   - Resultado: contiene calculo de huella canonica, llave automatica, id de
     almacenamiento seguro y replay de ejecucion.

3. Se agrego `JsonRepository.exists()`.
   - Resultado: el runtime puede consultar indices sin capturar excepciones de
     archivo inexistente.

4. Se integro idempotencia en `AgentRuntime`.
   - Resultado: antes de ejecutar workflow busca una ejecucion previa; si existe
     y coincide la huella, devuelve replay; si la llave entra en conflicto,
     falla con `IdempotencyConflictError`.

5. Se persiste metadata de idempotencia en la ejecucion.
   - Resultado: cada ejecucion nueva queda con `key`, `fingerprint` y
     `replayed=false`.

6. Se agregaron tests unitarios.
   - Resultado: cubren llave explicita, llave automatica estable y replay sin
     mutar la ejecucion original.

7. Se agregaron tests de integracion.
   - Resultado: campana repetida no duplica approval, journey repetido no
     duplica artifact y llave reutilizada con request distinto falla.

## Resultados de validacion

- `.venv/Scripts/python.exe -m pytest` sobre idempotencia y Growth runtime.
  - Resultado: paso con 9 tests.

- `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - Resultado: paso.

- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.

- `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - Resultado: paso con `status=passed`.

- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 90 tests.

## Validaciones bloqueadas por entorno

No aplico. Las validaciones focalizadas se ejecutaron con `.venv/Scripts`.

## Riesgos y deuda

- El indice local JSON no es transaccional; ejecuciones concurrentes podrian
  requerir locking o persistencia operacional en Airtable.
- La idempotencia local evita duplicados en runtime, pero la sincronizacion
  futura hacia Airtable debe respetar la misma llave.
- Opportunities reales aun no se crean porque el runtime sigue simulando actions
  internas.

## Siguiente paso recomendado

Continuar con P2: evaluacion independiente o metricas de costos/tokens.
