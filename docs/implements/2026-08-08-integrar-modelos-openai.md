# Implementacion: Integrar modelos OpenAI

Fecha: 2026-08-08

## Objetivo

Implementar el item P1 "Integrar modelos OpenAI" mediante un adapter proveedor
separado, configurable por `.env` y desacoplado de skills.

## Alcance

- Agregar SDK OpenAI como dependencia.
- Crear `OpenAIModelAdapter` compatible con `ModelAdapter`.
- Leer API key, modelos por perfil y timeout desde `.env`.
- Usar Responses API con Structured Outputs y JSON Schema estricto.
- Validar localmente la respuesta contra el schema esperado.
- Probar sin red mediante cliente inyectable.
- No conectar skills directamente con OpenAI.

## Archivos modificados

- `.env.example`
- `pyproject.toml`
- `adapters/models/__init__.py`
- `adapters/models/openai.py`
- `tests/unit/test_openai_model_adapter.py`
- `docs/architecture/model-gateway.md`
- `docs/current-state.md`
- `docs/implementation-backlog.md`
- `docs/session-log.md`

## Pasos ejecutados

1. Se reviso la documentacion oficial de OpenAI sobre Structured Outputs.
   - Resultado: se decidio usar Responses API con `json_schema` y `strict`.

2. Se agrego `openai>=1.99.0` a `pyproject.toml`.
   - Resultado: el SDK queda instalado con `pip install -e ".[dev]"`.

3. Se amplio `.env.example`.
   - Resultado: quedaron placeholders para API key, modelos por perfil,
     modelo default y timeout.

4. Se creo `adapters/models/openai.py`.
   - Resultado: el adapter resuelve modelos por perfil, llama Responses API,
     parsea JSON, valida schema y normaliza usage.

5. Se agregaron tests unitarios sin red.
   - Resultado: cubren config, request con schema estricto, parsing, schema
     mismatch y fallo de provider.

6. Se actualizo la documentacion del Model Gateway y el backlog.
   - Resultado: OpenAI quedo marcado como implementado y Structured Outputs
     quedo inicialmente como parcial.

7. Se instalo la dependencia en la venv.
   - Resultado: `openai-2.53.0` quedo instalado en `.venv`.

8. Se ejecuto un smoke test real luego de agregar credito.
   - Resultado: OpenAI respondio correctamente con Structured Output para
     `fast_structured` usando `gpt-5.6-luna`.

## Resultados de validacion

- `.venv/Scripts/ariwalabs.exe framework validate-repository --root .`
  - Resultado: paso con `status=passed`.

- `.venv/Scripts/python.exe -m ruff check .`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m mypy src`
  - Resultado: paso.

- `.venv/Scripts/python.exe -m pytest`
  - Resultado: paso con 70 tests en la primera corrida de este bloque.

- `git diff --check`
  - Resultado: paso.

- Smoke test real OpenAI.
  - Resultado: paso con `status=completed`, `provider=openai`,
    `profile=fast_structured`, `model=gpt-5.6-luna` y usage reportado.

## Validaciones bloqueadas por entorno

Durante los primeros intentos, el smoke test real quedo bloqueado por billing:
OpenAI devolvio `credit_balance_exhausted`. Luego Javier agrego credito y el
smoke test paso.

## Riesgos y deuda

- El adapter real depende de saldo, permisos y disponibilidad de modelos en la
  cuenta/proyecto OpenAI.
- La ejecucion real de skills todavia no invoca Model Gateway de forma
  integrada.
- No existe politica versionada de precios/costos por modelo.

## Siguiente paso recomendado

Completar Structured Outputs recuperables a nivel runtime/workflows.
