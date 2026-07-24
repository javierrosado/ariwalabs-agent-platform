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

El diagrama detallado de componentes y relaciones esta en
`docs/architecture/framework-overview.md`.

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

No se requieren contenedores durante la primera etapa. El proyecto requiere
Python 3.12, tal como queda definido en `pyproject.toml` y en el ADR-001.

Objetivo tecnico: preparar un entorno Python local, reproducible y alineado con
el MVP para ejecutar el CLI `ariwalabs`, validar el repositorio y probar agentes
sin Docker ni servicios externos.

Al terminar estos pasos se espera tener una `.venv` activa con Python 3.12, el
paquete instalado en modo editable con dependencias de desarrollo, el comando
`ariwalabs` disponible y capacidad de ejecutar la validacion del repositorio, una
campaña de ejemplo y la consulta de ejecuciones locales.

Paso 1: comprobar la version de Python que esta activa en la terminal. Esto
evita crear el entorno virtual con una version incompatible con el proyecto.

```bash
python --version
```

Si la version activa no es Python 3.12, elimina la venv anterior y creala con
un interprete 3.12.

Windows PowerShell:

Paso 2: recrear el entorno virtual en Windows con Python 3.12 y activarlo. Esto
aisla las dependencias del proyecto dentro de `.venv`.

```powershell
Remove-Item -Recurse -Force .venv
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

WSL/Linux:

Paso 2: recrear el entorno virtual en WSL/Linux con Python 3.12 y activarlo.
Esto aisla las dependencias del proyecto dentro de `.venv`.

```bash
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
```

Instalacion:

Paso 3: actualizar `pip` e instalar el paquete en modo editable con las
dependencias de desarrollo. Esto deja disponible el comando `ariwalabs` y las
herramientas de validacion local.

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Ejecutar validación del repositorio:

Paso 4: validar que las definiciones de agentes, skills, workflows y contexto
compartido cumplen las reglas basicas del framework.

```bash
ariwalabs framework validate-repository
```

Ejecutar campaña de ejemplo:

Paso 5: crear una ejecucion local usando un request de ejemplo. Esto permite
confirmar que el runtime puede cargar el agente, el workflow y persistir una
ejecucion pendiente de aprobacion humana.

```bash
ariwalabs agent run examples/requests/create-training-campaign.json
```

Listar ejecuciones:

Paso 6: revisar las ejecuciones locales guardadas por el runtime. Esto confirma
que la persistencia JSON local esta funcionando.

```bash
ariwalabs execution list
```

## 8. Flujo GitHub recomendado

Objetivo: asegurar que cada cambio tecnico quede versionado, revisable y
trazable en GitHub, que es la fuente de verdad del proyecto. Este flujo debe
usarse cada vez que se modifique codigo, agentes, skills, workflows, schemas,
prompts, politicas o documentacion relevante.

La idea es trabajar en ramas cortas, validar localmente antes de publicar y
dejar una revision explicita antes de integrar cambios a `main`.

```text
main
  +-- feature/framework-validation
  +-- feature/airtable-adapter
  +-- feature/model-gateway
```

Por cada cambio:

1. Crear una rama desde `main`.
   Objetivo: aislar el cambio para que pueda revisarse sin mezclarlo con trabajo
   no relacionado.
   Como hacerlo: actualizar `main` y crear una rama descriptiva.

   ```bash
   git switch main
   git pull
   git switch -c feature/nombre-del-cambio
   ```

2. Modificar los archivos necesarios.
   Objetivo: mantener el alcance pequeno y alineado con la tarea, evitando
   refactors o cambios paralelos que dificulten la revision.
   Como hacerlo: editar solo los archivos relacionados con la tarea, revisar el
   alcance y confirmar los detalles del diff.

   ```bash
   git status --short
   git diff
   ```

3. Ejecutar validaciones locales.
   Objetivo: detectar errores de framework, estilo, tipado y comportamiento antes
   de publicar el cambio.
   Como hacerlo: con la `.venv` activa, ejecutar estos comandos desde la raiz del
   repositorio.

   ```bash
   ariwalabs framework validate-repository --root .
   ruff check .
   mypy src
   pytest
   ```

4. Corregir hallazgos de validacion.
   Objetivo: no avanzar a commit si el framework, el linter, el tipado o las
   pruebas reportan errores.
   Como hacerlo: leer la salida de cada comando, corregir los archivos afectados
   y repetir las validaciones hasta que pasen.

   ```bash
   ariwalabs framework validate-repository --root .
   ruff check .
   mypy src
   pytest
   ```

5. Crear un commit.
   Objetivo: guardar una unidad logica de cambio con un mensaje claro sobre lo
   que se modifico y por que.
   Como hacerlo: revisar el diff final, agregar solo los archivos del cambio y
   crear el commit.

   ```bash
   git status --short
   git diff
   git add <archivo>
   git commit -m "mensaje claro"
   ```

6. Hacer push de la rama.
   Objetivo: publicar el cambio en GitHub para conservar trazabilidad y permitir
   revision.
   Como hacerlo: subir la rama al remoto. La primera vez usa `-u`; despues basta
   `git push`.

   ```bash
   git push -u origin feature/nombre-del-cambio
   git push
   ```

7. Abrir un pull request.
   Objetivo: explicar el cambio, listar pruebas ejecutadas y dejar visible el
   impacto antes de integrarlo.
   Como hacerlo: abrir el PR en GitHub desde la rama publicada, completar
   resumen, archivos relevantes, pruebas ejecutadas, riesgos y pendientes.

   ```text
   Resumen:
   - Que cambio se hizo.

   Pruebas:
   - ariwalabs framework validate-repository --root .
   - ruff check .
   - mypy src
   - pytest

   Riesgos o pendientes:
   - Indicar si aplica.
   ```

8. Realizar revision propia.
   Objetivo: leer el diff completo, verificar que no hay secretos, archivos
   temporales, datos sensibles ni cambios fuera de alcance.
   Como hacerlo: revisar la pestana de cambios del PR o ejecutar estos comandos;
   confirmar que `.env`, credenciales y artefactos locales no estan incluidos.

   ```bash
   git status --short
   git diff main...HEAD
   ```

9. Hacer merge.
   Objetivo: integrar el cambio aprobado a `main` solo cuando las validaciones y
   la revision sean satisfactorias.
   Como hacerlo: usar el boton de merge en GitHub cuando el PR este aprobado y
   las validaciones esten en verde; despues actualizar el checkout local.

   ```bash
   git switch main
   git pull
   ```

## 9. Reglas de implementación

Objetivo: mantener el framework gobernable, auditable y seguro mientras crece.
Estas reglas deben usarse como checklist antes de implementar, durante la
revision del diff y antes de declarar listo un cambio.

1. No duplicar contexto dentro de agentes.
   Uso: referencia `shared/context/` desde agentes, prompts, skills o workflows.
   Objetivo: evitar que existan versiones contradictorias del contexto
   institucional.

2. No llamar directamente al proveedor de IA desde una skill.
   Uso: consume modelos mediante perfiles logicos y el Model Gateway.
   Objetivo: permitir cambiar proveedores o modelos sin reescribir skills.

3. No llamar directamente a Airtable desde una skill.
   Uso: encapsula cualquier lectura o escritura en `adapters/` o en el futuro
   Tool Gateway.
   Objetivo: centralizar permisos, errores, idempotencia y auditoria de datos.

4. Toda integracion debe pasar por un adapter/tool.
   Uso: crea o extiende contratos de integracion antes de conectar servicios
   externos.
   Objetivo: impedir APIs paralelas y mantener un punto controlado de acceso.

5. Todo output debe tener schema.
   Uso: define o actualiza JSON Schemas para respuestas de skills, handoffs y
   reportes.
   Objetivo: validar resultados automaticamente y reducir outputs ambiguos.

6. Todo workflow debe tener estados y aprobacion.
   Uso: declara checkpoints y estados de ejecucion, especialmente antes de
   acciones externas o comerciales.
   Objetivo: conservar control humano y trazabilidad del proceso.

7. Todo handoff debe tener contrato.
   Uso: documenta productor, consumidor, payload, aprobaciones, errores y
   persistencia esperada.
   Objetivo: que un agente pueda entregar trabajo a otro sin supuestos
   implicitos.

8. Toda ejecucion debe tener ID y version.
   Uso: registra identificadores estables para ejecuciones, artefactos y
   versiones de agente/workflow.
   Objetivo: poder auditar que version produjo cada resultado.

9. Todo release debe pasar por Framework Agent.
   Uso: ejecuta la revision tecnica del framework antes de declarar listo un
   agente, skill, workflow o contrato.
   Objetivo: bloquear cambios incompatibles antes de que afecten la operacion.

## 10. Prompts para Codex

Objetivo: usar prompts operativos versionados para pedir trabajo a Codex de
forma consistente. Los prompts en `prompts/codex` ayudan a cargar contexto,
mantener las reglas del repositorio y pedir entregables verificables.

Como deben usarse:

1. Abrir el prompt que corresponde a la tarea.
   Objetivo: elegir una instruccion base alineada con el tipo de cambio.

2. Reemplazar los placeholders como `<COMPONENT>`, `<AGENT_ID>` o `<SKILL_ID>`.
   Objetivo: convertir el prompt generico en una instruccion concreta.

3. Pegar el prompt en Codex junto con cualquier restriccion adicional.
   Objetivo: iniciar la tarea con contexto, alcance y criterios de validacion
   claros.

4. Revisar el plan, archivos propuestos y pruebas antes de aprobar cambios
   sensibles.
   Objetivo: conservar aprobacion humana y evitar impactos externos no deseados.

Prompts principales:

- `00-load-project-context.md`: usarlo al iniciar una sesion o antes de una
  tarea amplia. Sirve para que Codex lea contexto, politicas, agente afectado,
  riesgos, archivos y pruebas antes de modificar.
- `01-implement-framework-component.md`: usarlo para construir o mejorar piezas
  del framework, como runtime, validadores, gateways, auditoria o registries.
- `02-create-new-agent.md`: usarlo cuando se necesite definir un agente nuevo
  con `agent.yaml`, skills, workflows, schemas, handoffs, aprobaciones y pruebas.
- `03-create-new-skill.md`: usarlo para crear una skill nueva dentro de un
  agente existente, con input schema, output schema, permisos, errores y
  pruebas.
- `04-integrate-airtable.md`: usarlo cuando se implemente o amplie el Airtable
  Adapter. No debe usarse para llamar Airtable directamente desde una skill.
- `05-review-release.md`: usarlo antes de declarar listo un agente o release.
  Sirve para revisar definicion, contratos, politicas, pruebas, secretos y
  compatibilidad.

## 11. Limitaciones actuales

El repositorio incluye estructura, validadores, runtime local y persistencia
JSON. No incluye credenciales ni conexiones productivas con OpenAI, Airtable,
WhatsApp, LinkedIn o Azure. Los adapters contienen contratos y stubs seguros.
