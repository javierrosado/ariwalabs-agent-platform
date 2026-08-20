# Model Adapter

Fecha: 2026-08-15

## Objetivo

Aislar proveedores de modelos detras de un contrato comun para que Model
Gateway pueda cambiar de proveedor o modelo sin modificar agents, skills,
prompts, workflows ni schemas.

## Estado

Implementado en `adapters/models/`.

## Reglas

- Cada adapter implementa el protocolo `ModelAdapter`.
- La seleccion de proveedor se resuelve con `MODEL_PROVIDER`.
- Los modelos concretos se configuran por perfil logico.
- Los secretos se leen desde `.env` o variables de entorno.
- Los adapters no deben auditar secretos, prompts completos ni payloads
  sensibles.
- Las pruebas de adapters reales deben evitar red usando cliente inyectable.

## Proveedores soportados

- `fake`: adapter local deterministico.
- `openai`: adapter real para OpenAI Responses API con Structured Outputs.

## Componentes

- `adapters/models/base.py`: protocolo `ModelAdapter`.
- `adapters/models/factory.py`: seleccion central de provider.
- `adapters/models/fake.py`: provider local sin red.
- `adapters/models/openai.py`: provider OpenAI.
- `adapters/models/errors.py`: errores tipados.
- `src/ariwalabs/model_gateway.py`: consumidor principal.
- `tests/unit/test_model_adapter_factory.py`: cobertura de factory.
- `tests/unit/test_openai_model_adapter.py`: cobertura OpenAI sin red.

## Implementacion relacionada

- [implementar-model-gateway.md](../implements/implementar-model-gateway.md)
- [centralizar-cambio-proveedor-modelo.md](../implements/centralizar-cambio-proveedor-modelo.md)
- [integrar-modelos-openai.md](../implements/integrar-modelos-openai.md)
- [metricas-costos-tokens.md](../implements/metricas-costos-tokens.md)

## Pendiente

- Agregar nuevos providers solo cuando exista una necesidad concreta.
- Completar latencia y reintentos por provider.
- Revisar periodicamente variables de configuracion y pricing.
