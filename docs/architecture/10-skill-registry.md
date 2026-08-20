# Skill Registry

Fecha: 2026-08-15

## Objetivo

Validar que cada skill declarativa tenga contrato completo, versionado,
ownership correcto, perfil logico de modelo, output schema y tools gobernadas.

## Estado

Implementado en `src/ariwalabs/skill_registry.py`.

## Reglas

- Cada skill debe declarar `id`, `version`, `purpose`, `model_profile`,
  `approval_required` y `output_schema`.
- Los ids deben usar el prefijo del agente y el sufijo del slug de la skill.
- La version debe usar formato `N.N.N`.
- `model_profile` debe pertenecer a los perfiles soportados por Model Gateway.
- `output_schema` debe existir y ser JSON Schema valido.
- Las tools permitidas y prohibidas se validan mediante Tool Gateway.
- El owner del agente debe ser `company-director`.

## Componentes

- `src/ariwalabs/skill_registry.py`: carga y valida skills.
- `src/ariwalabs/model_profiles.py`: perfiles logicos soportados.
- `src/ariwalabs/tool_gateway.py`: catalogo y reglas de tools.
- `agents/*/skills/*/skill.yaml`: contratos de skills.
- `agents/*/schemas/*.schema.json`: schemas de salida.
- `tests/unit/test_skill_registry.py`: cobertura unitaria.

## Implementacion relacionada

- [completar-schemas-skills.md](../implements/completar-schemas-skills.md)
- [implementar-skill-registry.md](../implements/implementar-skill-registry.md)
- [ejecucion-real-skills-model-gateway.md](../implements/ejecucion-real-skills-model-gateway.md)
- [tool-gateway.md](../implements/tool-gateway.md)

## Ejecucion

Las skills se ejecutan desde `SkillExecutor`, que carga `skill.yaml`, prompt,
schema y contexto compuesto para invocar `ModelGateway.generate_structured()`.
Las skills siguen sin conocer OpenAI, Airtable ni adapters concretos.

## Pendiente

- Validar existencia y compatibilidad de prompts por skill.
- Ejecutar validaciones semanticas mas profundas contra workflows.
