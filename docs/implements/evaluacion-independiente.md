# Implementacion: Evaluacion independiente

Fecha: 2026-08-10

## Objetivo

Implementar el item P2 "Evaluacion independiente" para evaluar outputs de
skills con rubricas por skill y un evaluador separado de la generacion.

## Alcance

- Crear rubricas declarativas por skill para Framework Agent y Growth &
  Marketing Agent.
- Validar que cada skill tenga una rubrica registrada.
- Evaluar outputs de skills contra JSON Schema y criterios deterministas.
- Permitir evaluacion opcional mediante Model Gateway con perfil logico
  `evaluation`.
- Persistir el resultado independiente de evaluacion en ejecuciones nuevas.
- No cambiar el estado principal del workflow segun la evaluacion todavia.

## Archivos modificados

- `agents/framework-agent/evaluations/rubrics.yaml`
- `agents/growth-marketing-agent/evaluations/rubrics.yaml`
- `src/ariwalabs/evaluation_engine.py`
- `src/ariwalabs/framework_validator.py`
- `src/ariwalabs/runtime.py`
- `tests/unit/test_evaluation_engine.py`
- `tests/integration/test_growth_runtime.py`
- `docs/architecture/01-framework-overview.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/evaluacion-independiente.md`

## Pasos ejecutados

1. Se reviso el estado actual, backlog y ADR-004.
   - Resultado: se confirmo que la evaluacion debe usar el perfil logico
     `evaluation` mediante Model Gateway y no acoplar skills a modelos.

2. Se creo `src/ariwalabs/evaluation_engine.py`.
   - Resultado: existe `EvaluationEngine` con validacion de rubricas,
     evaluacion deterministica y hook opcional a Model Gateway.

3. Se agregaron rubricas por skill.
   - Resultado: Framework Agent y Growth & Marketing Agent tienen
     `evaluations/rubrics.yaml` con criterios por `skill_id`.

4. Se integro el engine con `FrameworkValidator`.
   - Resultado: la validacion del repositorio bloquea skills sin rubrica o
     rubricas invalidas.

5. Se integro el engine con `AgentRuntime`.
   - Resultado: las ejecuciones nuevas persisten `evaluation` separado del
     `workflow_execution`.

6. Se agregaron pruebas unitarias e integracion.
   - Resultado: cubren rubricas del repositorio, ausencia de rubricas,
     evaluacion deterministica, invocacion del evaluador separado, bloqueo por
     schema y persistencia runtime.

## Resultados de validacion

- `.venv/Scripts/python.exe -m pytest tests/unit/test_evaluation_engine.py \
  tests/unit/test_framework_validator.py tests/integration/test_growth_runtime.py`
  - Resultado: paso con 17 tests.

- `.venv/Scripts/python.exe -m ruff check src/ariwalabs/evaluation_engine.py \
  src/ariwalabs/framework_validator.py src/ariwalabs/runtime.py \
  tests/unit/test_evaluation_engine.py tests/unit/test_framework_validator.py \
  tests/integration/test_growth_runtime.py`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.

- `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - Resultado: paso con `status=passed`.

- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 115 tests.

- `git diff --check` acotado a los archivos tocados por Evaluacion
  independiente.
  - Resultado: paso.

## Validaciones bloqueadas por entorno

`git diff --check` completo sigue bloqueado por archivos generados en
`runtime/data/idempotency/`, fuera del cambio funcional de Evaluacion
independiente. Las validaciones focalizadas y la suite completa se ejecutaron
con `.venv/Scripts`.

## Riesgos y deuda

- Las rubricas iniciales son base y deben calibrarse por dominio/skill.
- La evaluacion independiente se persiste, pero aun no gobierna
  automaticamente el estado principal de la ejecucion.
- El runtime local no inyecta un Model Gateway productivo por defecto; la
  evaluacion por modelo queda disponible por inyeccion.

## Siguiente paso recomendado

Definir el siguiente incremento posterior a P2: integracion real de skills
mediante Model Gateway, sincronizacion operacional hacia Airtable o Agent
Registry.
