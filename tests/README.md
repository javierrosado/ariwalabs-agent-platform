# Tests

## Objetivo

La carpeta `tests/` protege el comportamiento tecnico del Core Framework y de
los Business Packs. Su objetivo es detectar regresiones en validacion,
ejecucion local, aprobaciones, integraciones gobernadas, auditoria,
idempotencia y contratos de agentes antes de mover cambios a GitHub.

## Tipos de test

- Unitarios: prueban componentes aislados como registries, gateways, engines,
  adapters, auditoria, repositorio e idempotencia.
- Integracion local: ejecutan flujos completos del runtime con agentes,
  workflows, skills, approvals, artifacts y evaluacion.
- Regresion: usan fixtures versionados para verificar que casos clave de
  Growth & Marketing siguen produciendo estados y contratos esperados.
- CLI: validan comandos `ariwalabs` y salidas JSON para errores o resultados
  operativos.
- Adapter contract tests: validan contratos de integraciones sin depender de
  red real, usando transports o clientes falsos.

## Convenciones

- Los tests no deben usar secretos reales.
- Las pruebas con integraciones externas deben inyectar adapters falsos o
  transports controlados.
- Los tests pueden escribir en `runtime/data/`; esa ruta es local y no debe
  versionarse.
- Cuando se agregue un componente de arquitectura, debe existir al menos una
  prueba unitaria o de integracion que cubra su contrato principal.

## Comandos

```bash
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m mypy src
```
