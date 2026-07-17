# Prompt: integrar Airtable

Implementa el Airtable Adapter sin acoplarlo a una skill.

Requisitos:

- configuración por variables de entorno;
- tablas configurables;
- operaciones read/create/update limitadas;
- retries con backoff;
- manejo de rate limits;
- idempotencia;
- logs sin datos sensibles;
- mocks para pruebas;
- errores tipados;
- documentación de campos;
- no almacenar secretos en GitHub.

Tablas iniciales:

People, Organizations, TrainingPrograms, Cohorts, Enrollments, Campaigns,
ContentItems, Events, Referrals, Opportunities, Approvals, AgentExecutions,
Artifacts.
