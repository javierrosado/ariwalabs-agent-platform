# ADR-004: Model Gateway con perfiles logicos

Fecha: 2026-07-17
Estado: aceptada

## Contexto

Las skills necesitan razonamiento, generacion, evaluacion y extraccion
estructurada, pero no deben depender de modelos concretos.

## Decision

El consumo de modelos se hara mediante Model Gateway y perfiles logicos como
`reasoning`, `generation`, `evaluation` y `fast_structured`.

## Alternativas

- Configurar modelo concreto dentro de cada skill.
- Llamar APIs de proveedor desde skills.
- Usar un unico modelo global.

## Consecuencias

- Se puede cambiar proveedor o modelo sin modificar skills.
- El gateway debe medir costo, tokens, errores y retries.
- Los schemas y structured outputs son requisito para produccion.
