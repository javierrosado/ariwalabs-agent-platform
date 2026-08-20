# Governance

Fecha: 2026-08-15

## Objetivo

Concentrar politicas, limites y bloqueos que mantienen el framework bajo
control humano, trazabilidad tecnica y separacion entre agentes, skills,
modelos e integraciones.

## Estado

Implementado de forma distribuida mediante politicas versionadas, validadores,
gateways y reglas del runtime. No existe un unico modulo `governance.py`.

## Reglas

- Javier, `company-director`, es el unico operador y aprobador.
- GitHub es la fuente de verdad tecnica.
- El MVP usa VS Code, Python venv local y ejecucion local; no Docker.
- Airtable es el sistema operacional inicial; no SQLite en el MVP.
- Los secretos viven en `.env` y no se versionan.
- Las skills usan perfiles logicos, no modelos concretos.
- Las skills no llaman APIs externas directamente.
- Toda integracion pasa por `adapters/` o Tool Gateway.
- El contexto empresarial vive en `shared/context/`.
- El Growth & Marketing Agent no publica, no envia mensajes externos, no compra
  publicidad, no contacta empresas y no registra oportunidades sin aprobacion.

## Componentes

- `AGENTS.md`: reglas operativas del repositorio.
- `shared/policies/global-agent-policy.yaml`: politica global versionada.
- `docs/architecture-decisions/`: ADRs aceptados.
- `src/ariwalabs/framework_validator.py`: validacion del repositorio.
- `src/ariwalabs/skill_registry.py`: contratos de skills.
- `src/ariwalabs/tool_gateway.py`: bloqueo de tools externas.
- `src/ariwalabs/approval_engine.py`: aprobacion humana.
- `src/ariwalabs/audit.py`: trazabilidad.

## Implementacion relacionada

- [cerrar-formalmente-p0.md](../implements/cerrar-formalmente-p0.md)
- [cerrar-formalmente-p1.md](../implements/cerrar-formalmente-p1.md)
- [implementar-approval-engine.md](../implements/implementar-approval-engine.md)
- [implementar-audit-log-completo.md](../implements/implementar-audit-log-completo.md)
- [tool-gateway.md](../implements/tool-gateway.md)

## Pendiente

- Centralizar mas reglas en validadores formales.
- Validar compatibilidad semantica entre policies, workflows y skills.
- Cubrir handoffs, herramientas, aprobaciones y prompts con validaciones mas
  profundas.
