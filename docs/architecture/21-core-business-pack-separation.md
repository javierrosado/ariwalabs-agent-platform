# Core And Business Pack Separation

Fecha: 2026-08-15

## Objetivo

Separar la arquitectura en dos capas:

- Core Framework: componentes reutilizables para cualquier negocio.
- Business Pack: activos de dominio de un negocio concreto.

## Estado

Implementado para el alcance P3. Existen manifests en `business_packs/`,
`BusinessPackRegistry`, validacion de manifests, loaders con `business_pack_id`
opcional y CLI `--business-pack`. AriwaLabs Training ya tiene agentes, contexto,
policies y handoffs dentro de `business_packs/ariwalabs-training/`. Las rutas
historicas `agents/`, `shared/` y `docs/handoffs/` siguen disponibles como modo
default compatible.

## Core Framework

El core no debe depender de AriwaLabs, capacitaciones, alumnos, cohortes,
campanas, referidos ni oportunidades corporativas.

Componentes core:

- Agent Runtime
- Agent Registry futuro
- Skill Registry
- Handoff Registry
- Workflow Engine
- Context Engine
- Model Gateway
- Model Adapter
- Tool Gateway
- Approval Engine
- Evaluation Engine
- Artifact Manager
- Audit
- Persistence
- Adapter contracts

## AriwaLabs Training Pack

El dominio AriwaLabs Training agrupa:

- Growth & Marketing Agent.
- Contexto institucional y oferta formativa.
- Audiencias objetivo.
- Politicas comerciales especificas.
- Handoffs de Growth y futuros agentes de training/consultoria.
- Tablas Airtable operacionales para capacitacion, cohortes, referidos y
  oportunidades.

## Reglas

- El core puede validar contratos genericos, pero no debe conocer reglas de
  negocio especificas.
- El pack puede declarar reglas de negocio, agents, schemas, workflows,
  handoffs y tablas operacionales.
- Los adapters siguen viviendo fuera del pack, salvo configuraciones o schemas
  de dominio.
- `company-director` debe convertirse gradualmente en rol configurable por pack.

## Implementacion relacionada

- [separar-core-business-pack.md](../implements/separar-core-business-pack.md)

## Pendiente

- Crear schemas comunes de core para agents, skills, workflows, approvals y
  artifacts.
- Implementar Agent Registry con soporte para `business_pack_id`.
- Migrar gradualmente referencias documentales historicas hacia rutas de pack.
