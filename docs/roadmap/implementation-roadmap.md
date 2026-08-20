# Roadmap de implementacion

Fecha de actualizacion: 2026-08-15

## Norte arquitectonico

Separar el Core Framework reutilizable de los Business Packs de dominio. El
primer pack activo es `ariwalabs-training`; `example-service` valida que el
core puede operar con un dominio no AriwaLabs.

## Fase 1 - Frontera Core / Business Pack

Estado: implementado para el alcance P3.

- Mantener documentada la frontera Core Framework vs AriwaLabs Training Pack.
- Usar `business_packs/ariwalabs-training/pack.yaml` como manifest de dominio.
- Validar manifests con `BusinessPackRegistry`.
- Usar `business_pack_id` en loaders, runtime y CLI.
- Separar policies core de policies AriwaLabs.
- Resolver agentes, contexto, policies y handoffs desde rutas fisicas de pack.
- Validar `example-service` como pack minimo no AriwaLabs.

## Fase 2 - Agent Registry multipack

Estado: implementado para el alcance P3.

- Implementar `src/ariwalabs/agent_registry.py`.
- Registrar agentes por `business_pack_id`, version, owner y estado de release.
- Validar skills, workflows, schemas, rubricas, contexto, policies y handoffs.
- Integrar con `FrameworkValidator`.
- Preparar governance local para releases sensibles.

## Fase 3 - Reanudacion de approvals

Estado: implementado para el alcance P3.

- Continuar ejecuciones en `approved_pending_resume`.
- Reanudar desde checkpoint sin duplicar approvals, artifacts ni acciones.
- Auditar la decision y la reanudacion.
- Mantener resume como accion CLI explicita.

## Fase 4 - Skills reales via Model Gateway

Estado: implementado para el alcance P3.

- Cargar prompt, schema, input y contexto compuesto por skill.
- Invocar `ModelGateway.generate_structured()`.
- Persistir outputs validados.
- Mantener pausa recuperable para structured outputs invalidos, incompletos o
  rechazados.
- Mantener fixtures `__skill_results__` para regresion.

## Fase 5 - Tool Gateway ejecutable

Estado: implementado para el alcance P3.

- Definir contrato input/output por tool.
- Despachar tools hacia adapters permitidos.
- Bloquear acciones externas no autorizadas.
- Auditar ejecuciones de tools con duracion.

## Fase 6 - Sincronizacion operacional Airtable

Estado: implementado para el alcance P3.

- Sincronizar `AgentExecutions`, `Approvals` y `Artifacts`.
- Mantener idempotencia.
- No exponer secretos ni payloads sensibles.
- Confirmar vistas operativas para Javier.
- Mantener la sincronizacion como accion CLI explicita.

## Fase 7 - Handoffs en runtime

Estado: implementado para el alcance P3.

- Ejecutar handoffs aprobados como transiciones versionadas.
- Persistir payload, estado, errores e idempotencia.
- Conectar con futura persistencia operacional cuando exista tabla canonica.

## Fase 8 - Robustez y observabilidad

Estado: implementado para el alcance P3.

- Errores tipados en runtime y CLI.
- Latencia por ejecucion, modelo, tool y adapter.
- Criterios de evaluacion calibrados por dominio.

## Fase 9 - Integraciones futuras

Estado: futuro.

- WhatsApp Business Platform.
- Email transaccional.
- Calendario Google o Microsoft.
- Publicacion social semimanual.
- Pasarela de pago.
- Azure o Microsoft Foundry.

## Criterio para crear nuevos agentes

No iniciar nuevos agentes de dominio hasta que Growth & Marketing Agent:

- ejecute workflows principales con skills reales o fixtures aprobados;
- genere artifacts conformes;
- registre aprobaciones;
- sincronice ejecuciones relevantes con Airtable;
- pase pruebas de regresion;
- tenga rubricas internas calibradas.
