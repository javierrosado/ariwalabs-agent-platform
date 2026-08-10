# Model Gateway

Fecha: 2026-08-08

## Objetivo

Centralizar el consumo de modelos mediante perfiles logicos para que agents y
skills no dependan de proveedores ni modelos concretos.

## Perfiles soportados

- `reasoning`: razonamiento y planificacion.
- `generation`: generacion de contenido o briefs.
- `evaluation`: revision, compliance y evaluacion.
- `fast_structured`: extraccion o respuestas estructuradas rapidas.

## Reglas

- Las skills declaran `model_profile`, no nombres de modelos.
- El gateway llama un `ModelAdapter`; las skills no llaman proveedores.
- El proveedor se resuelve centralmente con `MODEL_PROVIDER`; no se decide en
  skills, prompts ni workflows.
- Los prompts completos, payloads sensibles, tokens y secretos no se auditan.
- Usage y costos se auditan solo cuando el adapter los devuelve.
- OpenAI se integra mediante un adapter separado en `adapters/models/openai.py`.
- El adapter OpenAI usa Responses API con Structured Outputs y JSON Schema
  estricto, de acuerdo con la documentacion oficial de OpenAI.

## Cambio de proveedor o modelo

### Cambiar solo el modelo OpenAI

Editar `.env` y ajustar los modelos por perfil logico:

- `OPENAI_REASONING_MODEL`
- `OPENAI_GENERATION_MODEL`
- `OPENAI_EVALUATION_MODEL`
- `OPENAI_FAST_MODEL`
- `OPENAI_DEFAULT_MODEL`

No se modifican skills, prompts, workflows ni schemas solo por cambiar el
modelo. Si el nuevo modelo requiere ajustes de comportamiento, esos cambios se
tratan como trabajo de prompting o evaluacion separado.

### Cambiar de proveedor soportado

Editar `.env`:

- `MODEL_PROVIDER=fake`: adapter deterministico local, sin red.
- `MODEL_PROVIDER=openai`: adapter real OpenAI.

Cada proveedor mantiene sus propias variables. Para OpenAI se usan las variables
de la seccion siguiente.

### Agregar un proveedor nuevo

1. Crear `adapters/models/<provider>.py`.
2. Implementar el protocolo `ModelAdapter` declarado en
   `adapters/models/base.py`.
3. Resolver modelos por perfiles logicos, no por skills.
4. Leer secretos y configuracion desde `.env` o variables de entorno.
5. Normalizar la respuesta al contrato `ModelResult`.
6. No auditar secretos, prompts completos ni payloads sensibles.
7. Registrar el provider en `adapters/models/factory.py`.
8. Agregar tests unitarios sin red usando cliente o transporte inyectable.
9. Actualizar `.env.example`, esta documentacion, `current-state`, backlog y
   session log.

## Configuracion OpenAI

- `MODEL_PROVIDER`: `fake` u `openai`; por defecto documentado `fake`.
- `OPENAI_API_KEY`: secreto obligatorio para usar el provider real.
- `OPENAI_REASONING_MODEL`: modelo para `reasoning`.
- `OPENAI_GENERATION_MODEL`: modelo para `generation`.
- `OPENAI_EVALUATION_MODEL`: modelo para `evaluation`.
- `OPENAI_FAST_MODEL`: modelo para `fast_structured`.
- `OPENAI_DEFAULT_MODEL`: fallback opcional para perfiles sin modelo dedicado.
- `OPENAI_TIMEOUT_SECONDS`: timeout opcional; por defecto 30 segundos.

Los valores viven en `.env` o variables de entorno. `.env.example` solo contiene
placeholders.

## Costos y tokens

OpenAI factura tokens de entrada y salida segun la tarifa del modelo, expresada
por 1M tokens en la documentacion oficial de pricing. El repositorio no guarda
precios hardcodeados porque cambian con el tiempo.

Las estimaciones locales se habilitan configurando tarifas por modelo:

- `MODEL_COST_CURRENCY`: moneda para estimaciones; por defecto `USD`.
- `MODEL_COST_GPT_5_6_LUNA_INPUT_PER_1M`
- `MODEL_COST_GPT_5_6_LUNA_OUTPUT_PER_1M`
- `MODEL_COST_GPT_5_6_TERRA_INPUT_PER_1M`
- `MODEL_COST_GPT_5_6_TERRA_OUTPUT_PER_1M`

Si una tarifa esta vacia, el sistema audita tokens pero deja
`estimated_cost=null`. Si ambas tarifas de un modelo estan configuradas, el
adapter calcula `input_amount`, `output_amount` y `amount`.

Los eventos `model.cost.recorded` incluyen:

- `execution_id`: correlacion de ejecucion.
- `logical_profile`: perfil logico usado.
- `tokens_in` y `tokens_out`.
- `estimated_cost`: costo estimado si hay tarifa configurada.
- `metadata.skill_id`: skill asociada cuando el caller la informa.

## Componentes

- `src/ariwalabs/model_gateway.py`: gateway principal y perfiles soportados.
- `src/ariwalabs/model_costs.py`: estimador configurable de costos por modelo.
- `adapters/models/base.py`: contrato `ModelAdapter`.
- `adapters/models/factory.py`: seleccion central de provider desde `.env`.
- `adapters/models/fake.py`: adapter deterministico local sin red.
- `adapters/models/openai.py`: adapter real para OpenAI, configurable por `.env`
  y probado mediante cliente inyectable sin red.
- `adapters/models/errors.py`: errores tipados del gateway.

## Eventos auditados

- `model.request.started`
- `model.request.completed`
- `model.request.failed`
- `model.cost.recorded`
- `model.output.invalid`
- `model.provider.failed_recoverable`

## Structured Outputs recuperables

`ModelGateway.generate_structured()` envuelve `generate()` y convierte fallos de
salida estructurada en resultados recuperables:

- `invalid_output`: el proveedor respondio, pero el JSON no valido contra el
  schema esperado.
- `provider_failed`: el proveedor fallo de forma recuperable.
- `incomplete`: el proveedor reporto salida incompleta.
- `refused`: el proveedor rechazo la respuesta.

Cuando un workflow recibe uno de esos estados para una skill, el paso queda como
`failed_recoverable`, el workflow queda en
`needs_structured_output_review`, no avanza a approvals/actions posteriores y el
runtime persiste `structured_output_error` en la ejecucion.

## Pendiente

- Integracion controlada con ejecucion real de skills.
- Latencia por request/modelo.
- Acciones explicitas de reintento/reanudacion tras revisar un Structured
  Output fallido.
