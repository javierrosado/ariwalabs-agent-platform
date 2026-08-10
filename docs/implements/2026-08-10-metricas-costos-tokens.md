# Implementacion: Metricas de costos y tokens

Fecha: 2026-08-10

## Objetivo

Implementar el item P2 "Metricas de costos y tokens" para estimar costo por
ejecucion, perfil logico y skill cuando existan tarifas configuradas por modelo.

## Alcance

- Auditar tokens de entrada y salida devueltos por adapters de modelo.
- Calcular costo estimado cuando existan tarifas configuradas.
- Mantener precios fuera del codigo para evitar valores desactualizados.
- Registrar `skill_id` opcional en eventos de Model Gateway.
- Soportar estimaciones para OpenAI sin acoplar skills al proveedor.
- No implementar latencia ni facturacion oficial.

## Archivos modificados

- `.env`
- `.env.example`
- `src/ariwalabs/model_costs.py`
- `src/ariwalabs/model_gateway.py`
- `adapters/models/openai.py`
- `adapters/models/factory.py`
- `tests/unit/test_model_costs.py`
- `tests/unit/test_model_gateway.py`
- `tests/unit/test_openai_model_adapter.py`
- `docs/architecture/model-gateway.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`
- `docs/implements/2026-08-10-metricas-costos-tokens.md`

## Pasos ejecutados

1. Se reviso documentacion oficial de OpenAI pricing.
   - Resultado: se confirmo que los precios son por tokens de entrada/salida y
     se publican por 1M tokens.

2. Se creo `src/ariwalabs/model_costs.py`.
   - Resultado: existe `ModelCostEstimator` con tarifas configurables por
     modelo, moneda, input por 1M y output por 1M.

3. Se extendio `OpenAIModelAdapter`.
   - Resultado: calcula `estimated_cost` cuando el provider devuelve usage y
     hay tarifa configurada para el modelo.

4. Se extendio `ModelGateway`.
   - Resultado: `generate()` y `generate_structured()` aceptan `skill_id`
     opcional y lo auditan en metadata de requests/costos.

5. Se extendio la factory de modelos.
   - Resultado: al crear OpenAI adapter tambien inyecta el estimador de costos
     construido desde `.env`.

6. Se actualizaron `.env.example` y `.env`.
   - Resultado: quedaron variables opcionales de tarifa para Luna y Terra,
     vacias por defecto.

7. Se agregaron tests unitarios.
   - Resultado: cubren calculo de costo, ausencia de tarifa, carga desde env,
     placeholders vacios, config parcial invalida, adapter OpenAI y auditoria
     con `skill_id`.

## Resultados de validacion

- `.venv/Scripts/python.exe -m pytest` sobre costos, gateway, OpenAI adapter y
  factory.
  - Resultado: paso con 26 tests.

- `.venv/Scripts/python.exe -m ruff check` sobre archivos tocados.
  - Resultado: paso.

- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.

- `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - Resultado: paso con `status=passed`.

- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 97 tests.

## Validaciones bloqueadas por entorno

No aplico. Las validaciones focalizadas se ejecutaron con `.venv/Scripts`.

## Riesgos y deuda

- Las estimaciones dependen de tarifas configuradas manualmente; si OpenAI
  cambia precios, `.env` debe actualizarse.
- No se implemento latencia por request/modelo.
- La ejecucion real de skills mediante Model Gateway sigue pendiente, por lo
  que `skill_id` aun se usa como metadata opcional preparada para esa etapa.

## Siguiente paso recomendado

Continuar con P2: evaluacion independiente, Tool Gateway o Context Engine.
