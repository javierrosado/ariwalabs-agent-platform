# Handoff Catalog

## Framework Agent -> agentes registrados

- Trigger: onboarding, validacion o release de agente.
- Productor: Framework Agent.
- Consumidor: agente registrado o director.
- Input: definicion de agente, skills, workflows, schemas, politicas y pruebas.
- Output: reporte de validacion, version aprobada y restricciones aplicables.
- Precondiciones: estructura existente y validacion sin errores bloqueantes.
- Aprobacion: Javier para registro, breaking change o release.
- Persistencia: repositorio Git y futuro Agent Registry.
- Errores: schema faltante, skill inexistente, workflow invalido, politica
  incumplida.
- Idempotencia: version de agente y hash futuro del paquete validado.

## Growth & Marketing Agent -> Director

- Trigger: campana, bootcamp, oportunidad, reporte o cambio de programa.
- Productor: Growth & Marketing Agent.
- Consumidor: Javier.
- Input: request, contexto compartido, datos operacionales y restricciones.
- Output: recomendacion, artefactos, riesgos y solicitud de aprobacion.
- Precondiciones: claims con fuente, supuestos separados de hechos y riesgos
  explicitos.
- Aprobacion: obligatoria para acciones externas o comerciales.
- Persistencia: `runtime/data` actualmente; Airtable en MVP.
- Errores: informacion faltante, datos no autorizados, evidencia insuficiente.
- Idempotencia: `execution_id` actual; llave de solicitud pendiente.

## Growth & Marketing Agent -> Content Agent

- Trigger: brief de contenido aprobado o campana lista para piezas.
- Productor: Growth & Marketing Agent.
- Consumidor: Content Agent futuro.
- Input: audiencia, canal, formato, mensaje, CTA, fuentes, restricciones y fecha.
- Output: `content_brief_id` y paquete de produccion.
- Precondiciones: campana aprobada y brand compliance sin bloqueos.
- Aprobacion: Javier antes de publicacion externa.
- Persistencia: futuro `ContentItems` en Airtable y artefactos versionados.
- Errores: canal no permitido, claim sin fuente, falta de fecha o CTA.
- Idempotencia: `content_brief_id` estable.

## Growth & Marketing Agent -> Training Program Agent

- Trigger: necesidad de curso, nivel, bootcamp o ajuste curricular.
- Productor: Growth & Marketing Agent.
- Consumidor: Training Program Agent futuro.
- Input: nivel, segmento, problema, propuesta de valor, duracion, modalidad,
  resultados esperados y restricciones.
- Output: `training_brief_id` y requerimientos curriculares.
- Precondiciones: segmento y objetivo validados.
- Aprobacion: Javier para cambios en oferta.
- Persistencia: futuro `TrainingPrograms` y `Artifacts`.
- Errores: prerequisitos inconsistentes, duracion fuera de limite, promesa no
  validada.
- Idempotencia: `training_brief_id` por version.

## Growth & Marketing Agent -> Student Success Agent

- Trigger: alumno matriculado, cambio de estado o accion de comunidad.
- Productor: Growth & Marketing Agent.
- Consumidor: Student Success Agent futuro.
- Input: `person_id`, `enrollment_id`, `cohort_id`, estado, expectativas y datos
  autorizados.
- Output: plan de acompanamiento o evento de journey.
- Precondiciones: consentimiento para datos personales y matricula registrada.
- Aprobacion: segun politica para mensajes externos o uso de datos sensibles.
- Persistencia: futuro `People`, `Enrollments`, `Cohorts` y `AgentExecutions`.
- Errores: consentimiento ausente, datos incompletos, cohorte inexistente.
- Idempotencia: combinacion `person_id` + `enrollment_id` + evento.

## Growth & Marketing Agent -> Corporate Opportunity Agent

- Trigger: senal empresarial detectada con evidencia y aprobacion para registro.
- Productor: Growth & Marketing Agent.
- Consumidor: Corporate Opportunity Agent futuro.
- Input: alumno, organizacion, senales, evidencia, hipotesis, confianza y
  restricciones de contacto.
- Output: `opportunity_signal_id` o borrador de oportunidad.
- Precondiciones: empresa indicada voluntariamente y sin contacto externo.
- Aprobacion: Javier antes de registrar o escalar oportunidad.
- Persistencia: futuro `Opportunities`, `Organizations` y `Approvals`.
- Errores: evidencia insuficiente, datos no autorizados, conflicto de privacidad.
- Idempotencia: `opportunity_signal_id` derivado de fuente y fecha.

## Corporate Opportunity Agent -> Sales Proposal Agent

- Trigger: oportunidad corporativa aprobada para propuesta comercial.
- Productor: Corporate Opportunity Agent futuro.
- Consumidor: Sales Proposal Agent futuro.
- Input: oportunidad aprobada, problema, alcance hipotetico, restricciones,
  stakeholders autorizados y decision del director.
- Output: brief de propuesta comercial.
- Precondiciones: aprobacion explicita de Javier y datos autorizados.
- Aprobacion: Javier antes de contacto, envio o negociacion.
- Persistencia: futuro `Opportunities`, `Approvals` y `Artifacts`.
- Errores: falta de aprobacion, datos sensibles, alcance no validado.
- Idempotencia: `opportunity_id` + version de brief.
