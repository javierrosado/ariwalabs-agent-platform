# Implementacion: Agent Registry

Fecha: 2026-08-15

## Objetivo

Implementar un registro local y gobernado de agentes que funcione con el modo
default del repositorio y con business packs.

## Alcance

- Crear `src/ariwalabs/agent_registry.py`.
- Catalogar agentes por `business_pack_id`, version, owner, autonomia,
  contexto, policies, skills, workflows, rubricas y handoffs.
- Integrar el registry con `FrameworkValidator`.
- Agregar comandos CLI de consulta.
- Validar `ariwalabs-training` y `example-service`.

## Archivos modificados

- `src/ariwalabs/agent_registry.py`
- `src/ariwalabs/framework_validator.py`
- `src/ariwalabs/cli.py`
- `tests/unit/test_agent_registry.py`
- `docs/architecture/05-agent-registry.md`
- `docs/architecture/01-framework-overview.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/roadmap/implementation-roadmap.md`
- `README.md`
- `docs/session-log.md`

## Pasos ejecutados

1. Se creo `AgentRegistry`.
   - Resultado: el registry lista, muestra y valida agentes desde `agents/` o
     desde el pack indicado por `business_pack_id`.

2. Se definio `AgentRecord`.
   - Resultado: cada agente queda catalogado con version, owner, autonomia,
     rutas, contexto, policies, skills, workflows, handoffs y rubricas.

3. Se agrego validacion de contratos de agente.
   - Resultado: el registry detecta `agent.yaml` faltante, version invalida,
     owner incompatible con el pack, skills inexistentes, workflows
     inexistentes, contexto invalido y releases aprobados sin evidencia local.

4. Se integro con `FrameworkValidator`.
   - Resultado: la validacion del framework delega la validacion formal de
     agentes en `AgentRegistry`.

5. Se agrego CLI.
   - Resultado: existen `ariwalabs agent-registry list` y
     `ariwalabs agent-registry show`.

6. Se agregaron pruebas unitarias.
   - Resultado: quedan cubiertos modo default, `ariwalabs-training`,
     `example-service`, errores de contrato e integracion con validator.

## Resultados de validacion

- `.venv/Scripts/python.exe -m pytest tests/unit/test_agent_registry.py
  tests/unit/test_business_packs.py tests/unit/test_framework_validator.py`
  - Resultado: paso con 19 tests.
- `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - Resultado: paso.
- `.venv/Scripts/ariwalabs.exe agent-registry list --root .`
  - Resultado: lista agentes default.
- `.venv/Scripts/ariwalabs.exe agent-registry list --root . --business-pack
  ariwalabs-training`
  - Resultado: lista agentes del pack AriwaLabs.
- `.venv/Scripts/ariwalabs.exe agent-registry show growth-marketing-agent
  --root . --business-pack ariwalabs-training`
  - Resultado: muestra el agente Growth & Marketing desde el pack.
- `.venv/Scripts/ariwalabs.exe agent-registry list --root . --business-pack
  example-service`
  - Resultado: lista `service-ops-agent`.

## Riesgos y deuda

- El release governance queda como contrato local inicial; todavia no consume
  aprobaciones reales del `ApprovalEngine`.
- El registry no persiste un indice materializado; calcula el catalogo desde
  archivos versionados.
