# Airtable Tables

Fecha: 2026-07-26

## Objetivo

Definir el modelo operacional inicial de Airtable para AriwaLabs sin duplicar
contexto institucional, sin reemplazar aun la persistencia local JSON del
runtime y sin permitir llamadas directas desde skills.

## Reglas globales

- `company-director` es el unico aprobador durante el MVP.
- No guardar secretos, tokens, prompts completos ni archivos grandes.
- No guardar datos personales sin consentimiento o fuente autorizada.
- No registrar oportunidades corporativas activas sin aprobacion.
- No usar Airtable como fuente de verdad tecnica; GitHub mantiene agentes,
  prompts, schemas, politicas y documentacion.
- Las integraciones escriben mediante `adapters/` o futuro Tool Gateway.

## Implementacion relacionada

- [disenar-tablas-airtable.md](../implements/disenar-tablas-airtable.md)
- [crear-tablas-airtable.md](../implements/crear-tablas-airtable.md)
- [implementar-airtable-adapter.md](../implements/implementar-airtable-adapter.md)
- [sincronizar-runtime-airtable.md](../implements/sincronizar-runtime-airtable.md)

## Campos comunes

Todos los records operacionales deben incluir:

| Campo | Tipo Airtable | Regla |
| --- | --- | --- |
| `Status` | Single select | Estado operacional del record. |
| `IdempotencyKey` | Single line text | Requerido para escrituras automaticas. |
| `CreatedAt` | Date/time | Fecha de creacion desde runtime o adapter. |
| `Source` | Single select | Origen: `runtime`, `airtable_form`, `manual`, `import`. |
| `Notes` | Long text | Notas operativas no sensibles. |

Estados base:

- `Draft`
- `PendingApproval`
- `Approved`
- `Rejected`
- `Active`
- `Archived`

## AgentExecutions

Proposito: registrar ejecuciones de agentes y workflows.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `ExecutionId` | Single line text | Si | Llave externa `exec-*`. |
| `AgentId` | Single line text | Si | Id del agente. |
| `AgentVersion` | Single line text | Si | Version declarada del agente. |
| `WorkflowId` | Single line text | Si | Id del workflow. |
| `RequestedBy` | Single line text | Si | Normalmente `company-director`. |
| `Status` | Single select | Si | Estado de ejecucion. |
| `WorkflowStatus` | Single select | Si | Estado emitido por Workflow Engine. |
| `CreatedAt` | Date/time | Si | Fecha de ejecucion. |
| `InputSummary` | Long text | No | Resumen sanitizado, no payload completo sensible. |
| `Approval` | Link to Approvals | No | Approval principal, si existe. |
| `Artifacts` | Link to Artifacts | No | Artifacts producidos. |
| `IdempotencyKey` | Single line text | Si | `ExecutionId` inicialmente. |

Privacidad: no almacenar input completo si contiene datos personales o
comerciales sensibles.

## Approvals

Proposito: registrar aprobaciones humanas obligatorias.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `ApprovalId` | Single line text | Si | Llave externa `appr-*`. |
| `ExecutionId` | Single line text | Si | Ejecucion relacionada. |
| `AgentId` | Single line text | Si | Agente solicitante. |
| `WorkflowId` | Single line text | Si | Workflow solicitante. |
| `Checkpoint` | Single line text | Si | Checkpoint de aprobacion. |
| `Approver` | Single line text | Si | Debe ser `company-director`. |
| `Status` | Single select | Si | `PendingApproval`, `Approved`, `Rejected`. |
| `Decision` | Single select | No | `approved` o `rejected`. |
| `Reason` | Long text | No | Obligatorio al decidir. |
| `DecidedBy` | Single line text | No | Debe ser `company-director`. |
| `CreatedAt` | Date/time | Si | Fecha de solicitud. |
| `DecidedAt` | Date/time | No | Fecha de decision. |
| `IdempotencyKey` | Single line text | Si | `ApprovalId`. |

Privacidad: la razon debe ser suficiente para auditoria, sin secretos ni datos
personales innecesarios.

## Artifacts

Proposito: registrar metadata de artefactos generados por workflows.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `ArtifactId` | Single line text | Si | Llave externa `art-*`. |
| `ExecutionId` | Single line text | Si | Ejecucion productora. |
| `AgentId` | Single line text | Si | Agente productor. |
| `WorkflowId` | Single line text | Si | Workflow productor. |
| `ArtifactType` | Single select | Si | Tipo interno versionado. |
| `SourceAction` | Single line text | Si | Accion interna que lo produjo. |
| `Status` | Single select | Si | `Draft`, `PendingApproval`, `Approved`, etc. |
| `Version` | Single line text | Si | Version del artifact. |
| `CreatedAt` | Date/time | Si | Fecha de creacion. |
| `MetadataSummary` | Long text | No | Resumen sanitizado de metadata. |
| `IdempotencyKey` | Single line text | Si | `ArtifactId`. |

Privacidad: no guardar contenido completo de artefactos grandes ni datos
personales sensibles.

## People

Proposito: personas prospecto, alumnos, egresados y miembros de comunidad.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `PersonId` | Single line text | Si | Llave externa estable. |
| `FullName` | Single line text | Si | Nombre operativo. |
| `Email` | Email | No | Solo con consentimiento o fuente autorizada. |
| `Phone` | Phone number | No | Solo con consentimiento. |
| `Segment` | Single select | Si | Segmento objetivo. |
| `LifecycleStage` | Single select | Si | Prospecto, alumno, egresado, comunidad. |
| `ConsentStatus` | Single select | Si | Estado de consentimiento. |
| `ConsentSource` | Single line text | No | Formulario, manual, evento, etc. |
| `Organization` | Link to Organizations | No | Empresa declarada voluntariamente. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Email normalizado o `PersonId`. |

Privacidad: no registrar empresa, telefono o email si no existe fuente
autorizada.

## Organizations

Proposito: empresas declaradas voluntariamente o prospectos corporativos.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `OrganizationId` | Single line text | Si | Llave externa estable. |
| `Name` | Single line text | Si | Nombre de organizacion. |
| `Industry` | Single select | No | Industria si fue proporcionada. |
| `Source` | Single select | Si | Origen autorizado. |
| `AuthorizedContactStatus` | Single select | Si | Si hay contacto autorizado. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Nombre normalizado + fuente. |

Privacidad: no inferir contactos ni claims empresariales sin evidencia.

## TrainingPrograms

Proposito: oferta formativa inicial y cambios aprobados.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `TrainingProgramId` | Single line text | Si | Llave externa estable. |
| `Name` | Single line text | Si | Nombre del programa. |
| `Level` | Single select | Si | Basico, Intermedio, Avanzado. |
| `PrerequisiteProgram` | Link to TrainingPrograms | No | Nivel anterior. |
| `MaxHours` | Number | Si | Maximo 48 por nivel. |
| `Modality` | Single select | Si | Hibrida inicialmente. |
| `PricePen` | Currency | Si | Precio referencial inicial. |
| `CertificateIncluded` | Checkbox | Si | Certificado incluido. |
| `Status` | Single select | Si | Estado operacional. |
| `Approval` | Link to Approvals | No | Requerido para cambios sensibles. |
| `IdempotencyKey` | Single line text | Si | Programa + version. |

Privacidad: no aplica a datos personales, pero no duplicar contexto fuente de
`shared/context`.

## Cohorts

Proposito: cohortes concretas de programas.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `CohortId` | Single line text | Si | Llave externa estable. |
| `TrainingProgram` | Link to TrainingPrograms | Si | Programa relacionado. |
| `Name` | Single line text | Si | Nombre operativo. |
| `StartDate` | Date | No | Fecha planificada. |
| `EndDate` | Date | No | Fecha planificada. |
| `Modality` | Single select | Si | Modalidad de cohorte. |
| `Capacity` | Number | No | Capacidad estimada. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Programa + nombre + fecha. |

## Enrollments

Proposito: relacion entre persona y cohorte/programa.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `EnrollmentId` | Single line text | Si | Llave externa estable. |
| `Person` | Link to People | Si | Persona matriculada. |
| `Cohort` | Link to Cohorts | Si | Cohorte relacionada. |
| `TrainingProgram` | Link to TrainingPrograms | Si | Programa relacionado. |
| `EnrollmentStatus` | Single select | Si | Prospecto, inscrito, activo, completado. |
| `ScholarshipStatus` | Single select | No | Estado de beca. |
| `Referral` | Link to Referrals | No | Referido relacionado. |
| `ConsentStatus` | Single select | Si | Consentimiento vigente. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Persona + cohorte. |

Privacidad: requiere consentimiento para contacto y seguimiento.

## Campaigns

Proposito: campanas de captacion o promocion.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `CampaignId` | Single line text | Si | Llave externa estable. |
| `Objective` | Long text | Si | Objetivo de campana. |
| `PrioritySegment` | Single select | Si | Segmento principal. |
| `BudgetCurrency` | Single line text | No | Moneda del presupuesto. |
| `BudgetMaximum` | Currency | No | Maximo aprobado o propuesto. |
| `Approval` | Link to Approvals | No | Requerido antes de publicar o gastar. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Objetivo + segmento + fecha. |

Gobierno: no publicar, contactar ni gastar sin approval.

## ContentItems

Proposito: briefs y piezas de contenido asociadas a campanas.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `ContentItemId` | Single line text | Si | Llave externa estable. |
| `Campaign` | Link to Campaigns | No | Campana origen. |
| `Channel` | Single select | Si | Canal propuesto. |
| `Format` | Single select | Si | Formato. |
| `MessageSummary` | Long text | Si | Resumen del mensaje. |
| `CallToAction` | Long text | Si | CTA aprobado o propuesto. |
| `Approval` | Link to Approvals | No | Requerido antes de publicacion. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Brief estable. |

Gobierno: no publicar automaticamente desde Airtable.

## Events

Proposito: clases, sesiones, webinars y eventos de comunidad.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `EventId` | Single line text | Si | Llave externa estable. |
| `EventType` | Single select | Si | Clase, webinar, comunidad, reunion. |
| `Cohort` | Link to Cohorts | No | Cohorte relacionada. |
| `TrainingProgram` | Link to TrainingPrograms | No | Programa relacionado. |
| `StartsAt` | Date/time | No | Fecha y hora. |
| `Channel` | Single select | No | Canal o modalidad. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Tipo + fecha + cohorte. |

## Referrals

Proposito: seguimiento del programa de referidos.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `ReferralId` | Single line text | Si | Llave externa estable. |
| `ReferrerPerson` | Link to People | Si | Persona que refiere. |
| `ReferredPerson` | Link to People | No | Persona referida si esta autorizada. |
| `TrainingProgram` | Link to TrainingPrograms | No | Programa relacionado. |
| `ReferralStatus` | Single select | Si | Nuevo, contactable, convertido, cerrado. |
| `ConsentStatus` | Single select | Si | Consentimiento del referido. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Referidor + referido + programa. |

Privacidad: no contactar referidos sin consentimiento o base autorizada.

## Opportunities

Proposito: oportunidades corporativas potenciales derivadas de evidencia y
aprobacion.

| Campo | Tipo Airtable | Requerido | Regla |
| --- | --- | --- | --- |
| `OpportunityId` | Single line text | Si | Llave externa estable. |
| `Organization` | Link to Organizations | Si | Organizacion relacionada. |
| `SourcePerson` | Link to People | No | Alumno/fuente si esta autorizado. |
| `SignalSummary` | Long text | Si | Senal con evidencia. |
| `EvidenceSummary` | Long text | Si | Evidencia sanitizada. |
| `Hypothesis` | Long text | Si | Hipotesis separada de hechos. |
| `Confidence` | Single select | Si | Baja, media, alta. |
| `Approval` | Link to Approvals | Si | Requerido para registro activo. |
| `ContactRestrictions` | Long text | Si | Restricciones vigentes. |
| `Status` | Single select | Si | Estado operacional. |
| `IdempotencyKey` | Single line text | Si | Senal + organizacion + fecha. |

Gobierno: no contactar empresas ni registrar oportunidad activa sin aprobacion.

## Relaciones iniciales

- `AgentExecutions` 1:N `Approvals`.
- `AgentExecutions` 1:N `Artifacts`.
- `Approvals` N:1 `AgentExecutions`.
- `Artifacts` N:1 `AgentExecutions`.
- `People` N:1 `Organizations`.
- `People` 1:N `Enrollments`.
- `TrainingPrograms` 1:N `Cohorts`.
- `Cohorts` 1:N `Enrollments`.
- `Campaigns` 1:N `ContentItems`.
- `People` 1:N `Referrals` como referidor.
- `Organizations` 1:N `Opportunities`.
- `Approvals` 1:N `Opportunities`, `Campaigns`, `ContentItems` y
  `TrainingPrograms`.

## Mapeo desde runtime local

| Runtime JSON | Airtable |
| --- | --- |
| `execution_id` | `AgentExecutions.ExecutionId` |
| `agent_id` | `AgentExecutions.AgentId` |
| `agent_version` | `AgentExecutions.AgentVersion` |
| `workflow_id` | `AgentExecutions.WorkflowId` |
| `requested_by` | `AgentExecutions.RequestedBy` |
| `status` | `AgentExecutions.Status` |
| `workflow_execution.status` | `AgentExecutions.WorkflowStatus` |
| `approval.approval_id` | `Approvals.ApprovalId` |
| `artifact_id` | `Artifacts.ArtifactId` |

## Idempotencia inicial

- `AgentExecutions`: `ExecutionId`.
- `Approvals`: `ApprovalId`.
- `Artifacts`: `ArtifactId`.
- `People`: email normalizado si existe; si no, `PersonId`.
- `Organizations`: nombre normalizado + fuente.
- `TrainingPrograms`: programa + version.
- `Cohorts`: programa + nombre + fecha.
- `Enrollments`: persona + cohorte.
- `Campaigns`: objetivo + segmento + fecha.
- `ContentItems`: content brief id estable.
- `Events`: tipo + fecha + cohorte.
- `Referrals`: referidor + referido + programa.
- `Opportunities`: senal + organizacion + fecha.

## Pendiente de implementacion

- Confirmar nombres exactos de single selects en la base real.
- Decidir si se agregan links Airtable entre `AgentExecutions`, `Approvals` y
  `Artifacts` o se mantienen solo llaves externas.
- Definir vistas operativas para Javier.
