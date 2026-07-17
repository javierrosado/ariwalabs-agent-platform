# AriwaLabs Agent Platform

Plataforma local y versionada para desarrollar, ejecutar y gobernar agentes
especializados de AriwaLabs desde VS Code y Codex.

## 1. Objetivo

Construir una plataforma multiagente incremental en la que:

- Javier sea el único operador y aprobador.
- GitHub sea la fuente de verdad técnica.
- Airtable sea el sistema operacional inicial.
- Los modelos OpenAI se consuman mediante perfiles lógicos.
- Cada agente comparta contexto institucional sin duplicarlo.
- Skills, workflows, contratos, handoffs y aprobaciones queden versionados.
- Ningún agente publique, contacte o comprometa presupuesto sin aprobación.

## 2. Agentes incluidos

### Framework Agent

Gobierna el ciclo de vida técnico de los agentes.

Responsabilidades:

- validar definiciones de agentes;
- validar contratos de skills;
- validar workflows;
- validar handoffs;
- registrar agentes;
- generar reportes de cumplimiento;
- preparar releases;
- bloquear cambios incompatibles.

No ejecuta tareas de marketing ni de negocio.

### Growth & Marketing Agent

Gestiona el crecimiento inicial de AriwaLabs mediante capacitaciones.

Responsabilidades:

- segmentación;
- propuesta de valor;
- diseño de campañas;
- planificación de contenido;
- bootcamps;
- recorrido del alumno;
- referidos;
- detección de señales empresariales;
- analítica de crecimiento;
- cumplimiento de marca.

No publica, no compra publicidad, no contacta empresas y no registra
oportunidades corporativas sin aprobación.

## 3. Arquitectura

```text
Director
  |
  +-- CLI / VS Code
         |
         +-- Framework Agent
         |      +-- valida agentes, skills, workflows y handoffs
         |
         +-- Agent Runtime
                +-- Context Engine
                +-- Workflow Engine
                +-- Model Gateway
                +-- Tool Gateway
                +-- Approval Engine
                +-- Evaluation Engine
                +-- Artifact Manager
                +-- Audit
                |
                +-- Growth & Marketing Agent
                       +-- Skills
                       +-- Workflows
                       +-- Handoffs
```

## 4. Fuente de verdad por tipo de información

| Información | Fuente |
|---|---|
| Código, prompts, schemas y workflows | GitHub |
| Contexto institucional | `shared/context` |
| Políticas | `shared/policies` |
| Operación de negocio | Airtable |
| Artefactos grandes | Local inicialmente; Drive/Blob después |
| Trazabilidad técnica | JSON local inicialmente |
| Secretos | `.env`, nunca GitHub |

## 5. Handoffs

### Framework Agent -> Growth & Marketing Agent

El Framework Agent entrega:

- definición validada;
- versión aprobada;
- skills registradas;
- workflows validados;
- políticas aplicables;
- reporte de release.

### Growth & Marketing Agent -> Director

Entrega:

- estrategia;
- campañas;
- calendarios;
- briefs;
- riesgos;
- métricas;
- solicitudes de aprobación;
- oportunidades potenciales.

### Growth & Marketing Agent -> futuros agentes

- `Training Program Agent`: brief de curso, audiencia y propuesta de valor.
- `Student Success Agent`: alumno matriculado y journey inicial.
- `Corporate Opportunity Agent`: señal empresarial aprobada.
- `Content Agent`: brief de contenido aprobado.
- `Sales Proposal Agent`: oportunidad corporativa aprobada.

Los contratos de handoff se documentan en `docs/handoffs`.

## 6. Roadmap

### Fase 0 - Base local

- VS Code.
- Python virtual environment.
- GitHub.
- contexto compartido;
- Framework Agent;
- Growth & Marketing Agent;
- CLI;
- JSON local;
- pruebas.

### Fase 1 - Airtable

- diseñar base AriwaLabs Operations;
- implementar Airtable Adapter;
- tablas People, Organizations, Programs, Cohorts, Campaigns, ContentItems,
  Events, Referrals, Opportunities, Approvals, AgentExecutions y Artifacts;
- lectura y escritura controlada;
- aprobaciones persistentes.

### Fase 2 - Model Gateway

- conectar modelos OpenAI;
- perfiles `reasoning`, `generation`, `evaluation`, `fast_structured`;
- structured outputs;
- reintentos;
- límites;
- costos;
- pruebas con modelos simulados y reales.

### Fase 3 - Growth Agent productivo

- campaña completa;
- calendario;
- bootcamp;
- journey;
- referidos;
- analytics;
- aprobaciones;
- artefactos.

### Fase 4 - Integraciones

- Airtable Forms;
- email transaccional;
- WhatsApp Business Platform;
- calendario;
- publicación social semimanual;
- LinkedIn inicialmente manual.

### Fase 5 - Segundo agente

Implementar `Training Program Agent` sobre la misma base.

### Fase 6 - Cloud

- Azure OpenAI o Microsoft Foundry;
- almacenamiento de artefactos;
- Application Insights;
- despliegue controlado.

## 7. Entorno local

No se requieren contenedores durante la primera etapa.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instalación:

```bash
pip install -e ".[dev]"
```

Ejecutar validación del repositorio:

```bash
ariwalabs framework validate-repository
```

Ejecutar campaña de ejemplo:

```bash
ariwalabs agent run examples/requests/create-training-campaign.json
```

Listar ejecuciones:

```bash
ariwalabs execution list
```

## 8. Flujo GitHub recomendado

```text
main
  +-- feature/framework-validation
  +-- feature/airtable-adapter
  +-- feature/model-gateway
```

Por cada cambio:

1. crear rama;
2. modificar;
3. ejecutar `ruff`, `mypy` y `pytest`;
4. ejecutar validación del Framework Agent;
5. commit;
6. push;
7. pull request;
8. revisión propia;
9. merge.

## 9. Reglas de implementación

- No duplicar contexto dentro de agentes.
- No llamar directamente al proveedor de IA desde una skill.
- No llamar directamente a Airtable desde una skill.
- Toda integración debe pasar por un adapter/tool.
- Todo output debe tener schema.
- Todo workflow debe tener estados y aprobación.
- Todo handoff debe tener contrato.
- Toda ejecución debe tener ID y versión.
- Todo release debe pasar por Framework Agent.

## 10. Prompts para Codex

Revisar `prompts/codex`.

Prompts principales:

- `00-load-project-context.md`
- `01-implement-framework-component.md`
- `02-create-new-agent.md`
- `03-create-new-skill.md`
- `04-integrate-airtable.md`
- `05-review-release.md`

## 11. Limitaciones actuales

El repositorio incluye estructura, validadores, runtime local y persistencia
JSON. No incluye credenciales ni conexiones productivas con OpenAI, Airtable,
WhatsApp, LinkedIn o Azure. Los adapters contienen contratos y stubs seguros.
