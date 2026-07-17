# ADR-001: VS Code y Python venv sin contenedores durante el MVP

Fecha: 2026-07-17
Estado: aceptada

## Contexto

El desarrollo inicial lo realiza Javier localmente con VS Code y Codex. El
objetivo es avanzar rapido en el framework sin overhead operacional.

## Decision

Durante el MVP se usara Python 3.12 con entorno virtual local. No se introducira
Docker ni contenedores.

## Alternativas

- Docker Compose local.
- Dev Containers.
- Entorno cloud desde el inicio.

## Consecuencias

- Menos complejidad inicial.
- Las instrucciones locales deben ser claras.
- La reproducibilidad depende de `pyproject.toml`, CI y documentacion.
