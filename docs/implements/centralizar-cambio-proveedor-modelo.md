# Implementacion: Centralizar cambio de proveedor y modelo

Fecha: 2026-08-08

## Objetivo

Documentar e implementar donde se cambian modelos y proveedores para que las
skills sigan usando perfiles logicos y no nombres de modelos concretos.

## Alcance

- Agregar `MODEL_PROVIDER` como seleccion central de proveedor.
- Crear una factory de adapters de modelo.
- Documentar cambio de modelo OpenAI, cambio de proveedor soportado y alta de
  proveedor nuevo.
- Agregar comentarios de uso a `.env` sin exponer secretos.
- Mantener `fake` como provider local por defecto.

## Archivos modificados

- `.env`
- `.env.example`
- `adapters/models/factory.py`
- `tests/unit/test_model_adapter_factory.py`
- `docs/architecture/15-model-gateway.md`
- `docs/current-state.md`
- `docs/session-log.md`

## Pasos ejecutados

1. Se agrego `MODEL_PROVIDER=fake` a `.env.example`.
   - Resultado: el provider local sin red queda documentado como default.

2. Se creo `adapters/models/factory.py`.
   - Resultado: `create_model_adapter()` selecciona `fake` u `openai` desde
     `.env` o variables de entorno.

3. Se agregaron tests de factory.
   - Resultado: cubren default fake, provider OpenAI, provider desconocido y
     precedencia de variables de entorno sobre `.env`.

4. Se actualizo `docs/architecture/15-model-gateway.md`.
   - Resultado: quedo documentado como cambiar modelo, cambiar proveedor y
     agregar proveedores nuevos.

5. Se agregaron comentarios a `.env`.
   - Resultado: el archivo local explica `MODEL_PROVIDER`, uso de OpenAI,
     modelos por perfil y variables Airtable sin modificar secretos reales.

6. Se actualizo `current-state` y session log.
   - Resultado: la factory quedo registrada como componente implementado.

## Resultados de validacion

- `.venv/Scripts/python.exe -m pytest` sobre factory, OpenAI adapter y Model
  Gateway.
  - Resultado: paso con 16 tests.

- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 74 tests en la suite completa de ese momento.

- `git diff --check`
  - Resultado: paso.

## Validaciones bloqueadas por entorno

No aplico. Las validaciones se ejecutaron con `.venv/Scripts`.

## Riesgos y deuda

- La factory solo soporta `fake` y `openai`; futuros providers deben registrarse
  explicitamente.
- Aun no hay Tool Gateway ni politica central de permisos para tools de modelo.

## Siguiente paso recomendado

Implementar Structured Outputs recuperables para que errores de modelo no rompan
el runtime ni avancen workflows con datos invalidos.
