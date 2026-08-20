# Implementacion: separar core framework y business pack

Fecha: 2026-08-15

## Objetivo

Separar el framework generico reutilizable del dominio AriwaLabs Training con
activos fisicos de pack, policies core/dominio separadas y compatibilidad con
las rutas historicas del modo default.

## Alcance

- Crear manifests de business packs.
- Crear rutas fisicas de dominio en `business_packs/ariwalabs-training/`.
- Separar policies core y policies AriwaLabs.
- Implementar `BusinessPackRegistry`.
- Parametrizar loaders principales con `business_pack_id`.
- Crear pack minimo no AriwaLabs validable.
- Documentar la frontera core vs dominio.
- Actualizar arquitectura, estado y backlog.
- Mantener intacta la ejecucion actual del runtime por defecto.

## Archivos modificados

- `business_packs/ariwalabs-training/pack.yaml`
- `business_packs/ariwalabs-training/README.md`
- `business_packs/example-service/pack.yaml`
- `business_packs/example-service/README.md`
- `src/ariwalabs/business_packs.py`
- `src/ariwalabs/framework_validator.py`
- `src/ariwalabs/runtime.py`
- `src/ariwalabs/context_engine.py`
- `src/ariwalabs/workflow_engine.py`
- `src/ariwalabs/skill_registry.py`
- `src/ariwalabs/handoff_registry.py`
- `src/ariwalabs/evaluation_engine.py`
- `src/ariwalabs/cli.py`
- `tests/unit/test_business_packs.py`
- `docs/architecture/21-core-business-pack-separation.md`
- `docs/architecture/01-framework-overview.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/separar-core-business-pack.md`

## Pasos ejecutados

1. Se reviso el estado real del framework, backlog y arquitectura.
   - Resultado: se confirmo que el core tecnico es reusable, pero los activos
     de dominio siguen mezclados en `agents/`, `shared/` y docs operativos.

2. Se creo `business_packs/ariwalabs-training/pack.yaml`.
   - Resultado: el pack declara agentes, contexto, policies, handoffs y
     operaciones Airtable especificas del dominio.

3. Se creo `business_packs/ariwalabs-training/README.md`.
   - Resultado: queda documentado que el pack referencia activos historicos por
     compatibilidad.

4. Se creo `src/ariwalabs/business_packs.py`.
   - Resultado: existe `BusinessPackRegistry` para validar manifests y resolver
     rutas de agentes y handoffs por `business_pack_id`.

5. Se parametrizaron loaders principales.
   - Resultado: Framework Validator, Agent Runtime, Context Engine, Skill
     Registry, Handoff Registry, Workflow Engine y Evaluation Engine aceptan
     `business_pack_id` opcional.

6. Se agrego `--business-pack` a la CLI.
   - Resultado: `ariwalabs framework validate-repository` y `ariwalabs agent
     run` pueden operar contra un pack declarado.

7. Se creo `business_packs/example-service/`.
   - Resultado: existe un segundo pack minimo no AriwaLabs para comprobar que
     el core valida manifests independientes.

8. Se creo `docs/architecture/21-core-business-pack-separation.md`.
   - Resultado: la arquitectura distingue Core Framework y Business Pack.

9. Se actualizo estado, backlog, roadmap y session log.
   - Resultado: la separacion inicial queda registrada y los pendientes de
     parametrizacion quedan explicitados.

## Resultados de validacion

- `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - Resultado: paso con `status=passed`.
- Parseo YAML de `business_packs/ariwalabs-training/pack.yaml`.
  - Resultado: paso; `business_pack.id` es `ariwalabs-training`.
- `git diff --check` acotado a archivos tocados.
  - Resultado: paso.
- `.venv/Scripts/python.exe -m pytest tests/unit/test_business_packs.py`
  - Resultado: paso.
- `.venv/Scripts/ariwalabs.exe framework validate-repository --root . --business-pack ariwalabs-training`
  - Resultado: paso con `status=passed`.
- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.
- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.
- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 119 tests.
- Validacion local de Markdown y enlaces/rutas internas.
  - Resultado: paso.

## Riesgos y deuda

- La policy global sigue mezclando reglas core y reglas AriwaLabs.
- Los activos reales de AriwaLabs siguen en rutas historicas y solo son
  referenciados por el pack.
