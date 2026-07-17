# Framework Overview

## Componentes

| Componente | Responsabilidad |
|---|---|
| Agent Registry | Catálogo y versiones de agentes |
| Skill Registry | Catálogo y contratos de skills |
| Workflow Engine | Secuencia, paralelo, condiciones y estados |
| Context Engine | Carga selectiva del contexto compartido |
| Model Gateway | Enrutamiento de perfiles de modelos |
| Tool Gateway | Acceso controlado a plataformas externas |
| Approval Engine | Pausas y decisiones humanas |
| Evaluation Engine | Validación determinística y por rúbrica |
| Artifact Manager | Registro de entregables |
| Audit | Registro de eventos |
| Governance | Políticas y bloqueos |
| Persistence | Repositorios intercambiables |

## Principio principal

La memoria y la operación pertenecen al framework, no a un agente concreto.
