# AriwaLabs Agent Platform

Plataforma local, versionada y gobernada para definir, validar y ejecutar
agentes. El repositorio esta evolucionando hacia dos capas:

- Core Framework: piezas reutilizables para cualquier negocio.
- Business Packs: activos de dominio para un negocio concreto.

El primer pack de dominio es `ariwalabs-training`, orientado a capacitaciones,
crecimiento, comunidad y oportunidades futuras de consultoria.

## 1. Estado actual

El core ya incluye runtime local, validadores, workflow engine, context engine,
model gateway, tool gateway, approval engine, evaluation engine, artifact
manager, auditoria y persistencia JSON local.

La separacion Core/Business Pack ya esta implementada para el alcance P3:

- manifests en `business_packs/`;
- `BusinessPackRegistry`;
- loaders principales con `business_pack_id` opcional;
- CLI `--business-pack` para validacion y ejecucion;
- pack real `business_packs/ariwalabs-training/` con agentes, contexto,
  policies y handoffs propios;
- pack minimo `business_packs/example-service/` con agente y workflow de prueba.

El backlog P3 esta implementado para el alcance actual: separacion
Core/Business Pack, Agent Registry, ejecucion real de skills via Model Gateway,
sincronizacion explicita con Airtable, reanudacion de workflows, Tool Gateway
ejecutable, Handoff Runtime, errores tipados y metricas de latencia.

## 2. Core Framework

El core debe mantenerse agnostico al negocio. No debe depender de AriwaLabs,
capacitaciones, alumnos, cohortes, referidos ni oportunidades corporativas.

Componentes core:

- `src/ariwalabs/runtime.py`
- `src/ariwalabs/agent_registry.py`
- `src/ariwalabs/business_packs.py`
- `src/ariwalabs/skill_registry.py`
- `src/ariwalabs/handoff_registry.py`
- `src/ariwalabs/handoff_runtime.py`
- `src/ariwalabs/workflow_engine.py`
- `src/ariwalabs/context_engine.py`
- `src/ariwalabs/skill_executor.py`
- `src/ariwalabs/model_gateway.py`
- `src/ariwalabs/tool_gateway.py`
- `src/ariwalabs/approval_engine.py`
- `src/ariwalabs/evaluation_engine.py`
- `src/ariwalabs/artifact_manager.py`
- `src/ariwalabs/audit.py`
- `src/ariwalabs/repository.py`
- `adapters/`

## 3. Business Packs

Los packs de dominio declaran agentes, contexto, policies, handoffs y activos
operacionales de un negocio concreto.

Packs actuales:

- `business_packs/ariwalabs-training/`: pack real de AriwaLabs.
- `business_packs/example-service/`: pack minimo para probar reusabilidad.

El pack AriwaLabs ya contiene copias fisicas de sus agentes, contexto, policies
y handoffs. Las rutas historicas `agents/`, `shared/` y `docs/handoffs/` se
mantienen para compatibilidad del modo default.

## 4. Agentes incluidos

### Framework Agent

Gobierna el ciclo de vida tecnico de agentes, skills, workflows, handoffs y
releases. No ejecuta tareas comerciales.

Ruta default: `agents/framework-agent/`
Ruta pack: `business_packs/ariwalabs-training/agents/framework-agent/`

### Growth & Marketing Agent

Gestiona crecimiento inicial para capacitaciones AriwaLabs: segmentacion,
propuesta de valor, campanas, contenido, bootcamps, journey, referidos,
analitica y deteccion de oportunidades.

Ruta default: `agents/growth-marketing-agent/`
Ruta pack: `business_packs/ariwalabs-training/agents/growth-marketing-agent/`

Este agente no publica, no compra publicidad, no contacta empresas y no registra
oportunidades corporativas sin aprobacion.

## 5. Arquitectura y backlog

Lectura recomendada:

1. `docs/architecture/01-framework-overview.md`
2. `docs/architecture/21-core-business-pack-separation.md`
3. `docs/current-state.md`
4. `docs/implementation-backlog.md`
5. `docs/roadmap/implementation-roadmap.md`

El backlog es la fuente operativa para el siguiente trabajo. El siguiente paso
previsto es definir el incremento posterior a P3: automatizacion gobernada de
tools/handoffs, persistencia operacional ampliada y calibracion de evaluaciones
por dominio.

## 6. Fuente de verdad

| Informacion | Fuente |
|---|---|
| Codigo, prompts, schemas y workflows | GitHub |
| Core framework | `src/ariwalabs/` |
| Business packs | `business_packs/` |
| Agentes default | `agents/` |
| Agentes por pack | `business_packs/*/agents/` |
| Contexto default | `shared/context/` |
| Contexto por pack | `business_packs/*/context/` |
| Politicas core | `framework/policies/` |
| Politicas por pack | `business_packs/*/policies/` |
| Handoffs default | `docs/handoffs/` |
| Handoffs por pack | `business_packs/*/handoffs/` |
| Arquitectura | `docs/architecture/` |
| Backlog | `docs/implementation-backlog.md` |
| Operacion de negocio inicial | Airtable |
| Trazabilidad local | `runtime/data/` |
| Secretos | `.env`, nunca GitHub |

## 7. Entorno local

No se usan contenedores durante el MVP. El proyecto usa Python 3.12 y entorno
virtual local.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

WSL/Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## 8. Comandos principales

Validar el repositorio completo:

```bash
ariwalabs framework validate-repository --root .
```

Validar usando el pack AriwaLabs:

```bash
ariwalabs framework validate-repository --root . --business-pack ariwalabs-training
```

Ejecutar un request de agente:

```bash
ariwalabs agent run examples/requests/create-training-campaign.json --root .
```

Ejecutar un request usando business pack:

```bash
ariwalabs agent run examples/requests/create-training-campaign.json --root . --business-pack ariwalabs-training
```

Listar ejecuciones locales:

```bash
ariwalabs execution list --root .
```

Listar approvals pendientes:

```bash
ariwalabs approval list --root .
```

Reanudar una ejecucion aprobada:

```bash
ariwalabs execution resume exec-<id> --root .
```

Validar Airtable sin imprimir secretos:

```bash
ariwalabs airtable validate-access --root . --env-file .env.example
```

Sincronizar una ejecucion local hacia Airtable:

```bash
ariwalabs airtable sync-execution exec-<id> --root . --env-file .env
```

Ejecutar un handoff aprobado desde payloads JSON:

```bash
ariwalabs handoff execute growth-marketing-to-director \
  --root . \
  --business-pack ariwalabs-training \
  --input runtime/data/handoff-input.json \
  --output runtime/data/handoff-output.json \
  --approved \
  --approval-id appr-<id>
```

Listar agentes registrados:

```bash
ariwalabs agent-registry list --root .
ariwalabs agent-registry list --root . --business-pack ariwalabs-training
```

Ver un agente registrado:

```bash
ariwalabs agent-registry show growth-marketing-agent --root . --business-pack ariwalabs-training
```

## 9. Validaciones antes de cerrar cambios

Ejecutar como minimo:

```bash
ariwalabs framework validate-repository --root .
ariwalabs framework validate-repository --root . --business-pack ariwalabs-training
ruff check .
mypy src
pytest
```

Para cambios documentales, tambien revisar enlaces/rutas internas de Markdown
cuando se renombren archivos.

## 10. Reglas no negociables

- Javier, `company-director`, es el unico operador y aprobador del MVP.
- GitHub es la fuente de verdad tecnica.
- No introducir Docker durante el MVP.
- No usar SQLite en el MVP.
- Los secretos viven en `.env` y no se versionan.
- Las skills usan perfiles logicos de modelo.
- Ninguna skill llama APIs externas directamente.
- Toda integracion pasa por `adapters/` o Tool Gateway.
- Toda accion externa, comercial, reputacional o de release requiere aprobacion.
- El Framework Agent gobierna agentes; no ejecuta tareas comerciales.

## 11. Siguiente trabajo

Definir el siguiente incremento posterior a P3, priorizando:

1. Automatizar invocaciones de Tool Gateway desde workflows solo con contrato y
   aprobacion aplicable.
2. Sincronizar handoffs con una tabla operacional canonica.
3. Calibrar rubricas y evaluaciones por business pack.

Cada incremento debe actualizar docs, backlog/current-state cuando aplique,
session log y pruebas.
