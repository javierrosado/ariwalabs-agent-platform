# Agent Catalog

## Framework Agent

- Ruta: `agents/framework-agent/`.
- Version: 0.1.0.
- Dominio: gobierno tecnico de la plataforma.
- Alcance: validar, registrar, gobernar y preparar releases de agentes, skills,
  workflows y handoffs.
- Inputs: definiciones de agentes, skills, workflows, schemas, handoffs,
  politicas, pruebas y evidencias de release.
- Outputs: reportes de validacion y decision de release.
- Skills:
  - `framework.validate-agent-definition`
  - `framework.register-agent`
  - `framework.validate-skill-contract`
  - `framework.validate-workflow`
  - `framework.validate-handoff`
  - `framework.release-agent`
- Workflows:
  - `validate-repository`
  - `onboard-agent`
  - `release-agent`
- Aprobaciones: release de agente, breaking changes y despliegues productivos.
- Limites: no ejecuta campanas, no publica, no modifica datos de negocio.
- Handoffs: entrega agentes validados y reportes de release.
- Madurez: declarativo con validador basico; registries y validacion profunda
  pendientes.

## Growth & Marketing Agent

- Ruta: `agents/growth-marketing-agent/`.
- Version: 0.2.0.
- Dominio: crecimiento, marketing y transicion capacitacion-consultoria.
- Alcance: solicitudes, segmentacion, propuesta de valor, campanas, contenido,
  bootcamps, journey, referidos, senales empresariales, analytics y marca.
- Inputs: requests del director, contexto compartido, datos operacionales
  futuros desde Airtable, restricciones y politicas.
- Outputs: estrategias, briefs, calendarios, planes de bootcamp, reportes de
  embudo, borradores de oportunidad y solicitudes de aprobacion.
- Skills:
  - `growth-marketing.request-validation`
  - `growth-marketing.audience-segmentation`
  - `growth-marketing.value-proposition`
  - `growth-marketing.campaign-design`
  - `growth-marketing.content-planning`
  - `growth-marketing.bootcamp-planning`
  - `growth-marketing.student-journey`
  - `growth-marketing.referral-program`
  - `growth-marketing.corporate-opportunity-detection`
  - `growth-marketing.growth-analytics`
  - `growth-marketing.brand-compliance`
- Workflows:
  - `create-training-campaign`
  - `plan-live-bootcamp`
  - `manage-student-growth-journey`
  - `detect-corporate-opportunity`
  - `analyze-growth-funnel`
- Aprobaciones: campanas, bootcamps, publicaciones externas, cambios de
  referidos y registro de oportunidades corporativas.
- Limites: no publica, no envia mensajes externos, no contacta empresas, no
  compra publicidad, no inventa claims, metricas ni casos de exito.
- Handoffs: Director, Content Agent, Training Program Agent, Student Success
  Agent y Corporate Opportunity Agent.
- Madurez: definicion funcional y workflows declarativos; ejecucion real de
  skills, schemas estrictos y persistencia Airtable pendientes.

## Agentes futuros previstos

Estos agentes estan previstos, pero no deben implementarse todavia.

- Training Program Agent: disenio curricular, niveles, temarios, rubricas y
  materiales.
- Student Success Agent: onboarding, avance, retencion, satisfaccion y comunidad.
- Corporate Opportunity Agent: calificacion de senales empresariales aprobadas.
- Content Agent: produccion asistida de piezas a partir de briefs aprobados.
- Sales Proposal Agent: propuestas comerciales para oportunidades aprobadas.
- Project Delivery Agent: delivery de proyectos de consultoria.
- Finance & Administration Agent: pagos, becas, facturacion y administracion.
