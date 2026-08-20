from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .business_packs import BusinessPackRegistry
from .config import load_yaml

Finding = dict[str, str]

DEFAULT_ALLOWED_CONTEXT_ROOTS = (
    Path("framework/policies"),
    Path("shared/context"),
    Path("shared/policies"),
)


class ContextCompositionError(Exception):
    def __init__(self, findings: list[Finding]):
        self.findings = findings
        message = "; ".join(finding["message"] for finding in findings)
        super().__init__(message)


@dataclass(frozen=True)
class ContextSource:
    path: str
    key: str
    content: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "key": self.key,
            "content": self.content,
        }


@dataclass(frozen=True)
class ComposedContext:
    agent_id: str
    workflow_id: str
    sources: tuple[ContextSource, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "source_paths": tuple(source.path for source in self.sources),
            "sources": tuple(source.to_dict() for source in self.sources),
            "data": {source.key: source.content for source in self.sources},
        }


class ContextEngine:
    def __init__(self, root: Path, *, business_pack_id: str | None = None):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(self.root)

    def compose_for_agent_workflow(
        self,
        *,
        agent_id: str,
        workflow_id: str,
    ) -> ComposedContext:
        agent_path = self.business_packs.agent_path(
            agent_id,
            self.business_pack_id,
        ) / "agent.yaml"
        agent_payload = load_yaml(agent_path).get("agent", {})
        if not isinstance(agent_payload, dict):
            raise ContextCompositionError(
                [self._finding("error", f"{agent_id}: agent.yaml invalido")]
            )
        findings = self.validate_agent_context(agent_id=agent_id, agent_config=agent_payload)
        if findings:
            raise ContextCompositionError(findings)
        context_paths = self._context_paths(agent_payload.get("shared_context", []))
        return ComposedContext(
            agent_id=agent_id,
            workflow_id=workflow_id,
            sources=tuple(self._load_source(rel_path) for rel_path in context_paths),
        )

    def validate_agent_context(
        self,
        *,
        agent_id: str,
        agent_config: dict[str, Any],
    ) -> list[Finding]:
        raw_context = agent_config.get("shared_context", [])
        if raw_context in (None, []):
            return []
        if not isinstance(raw_context, list):
            return [self._finding("error", f"{agent_id}: shared_context debe ser lista")]

        findings: list[Finding] = []
        seen: set[str] = set()
        for value in raw_context:
            if not isinstance(value, str):
                findings.append(
                    self._finding("error", f"{agent_id}: shared_context contiene valor no string")
                )
                continue
            rel_path = Path(value)
            if value in seen:
                findings.append(
                    self._finding("error", f"{agent_id}: contexto duplicado {value}")
                )
            seen.add(value)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                findings.append(
                    self._finding("error", f"{agent_id}: contexto fuera del repositorio {value}")
                )
                continue
            if not self._is_allowed_context_path(rel_path):
                findings.append(
                    self._finding("error", f"{agent_id}: contexto fuera de rutas permitidas {value}")
                )
                continue
            full_path = self.root / rel_path
            if not full_path.exists():
                findings.append(self._finding("error", f"{agent_id}: contexto inexistente {value}"))
                continue
            if full_path.suffix not in {".yaml", ".yml"}:
                findings.append(self._finding("error", f"{agent_id}: contexto no YAML {value}"))
                continue
            try:
                payload = load_yaml(full_path)
            except yaml.YAMLError as exc:
                findings.append(
                    self._finding("error", f"{agent_id}: contexto YAML invalido {value}: {exc}")
                )
                continue
            if not payload:
                findings.append(self._finding("error", f"{agent_id}: contexto vacio {value}"))
            elif not isinstance(payload, dict):
                findings.append(
                    self._finding("error", f"{agent_id}: contexto debe ser objeto {value}")
                )
        return findings

    def _load_source(self, rel_path: Path) -> ContextSource:
        full_path = self.root / rel_path
        payload = load_yaml(full_path)
        return ContextSource(
            path=rel_path.as_posix(),
            key=self._source_key(rel_path, payload),
            content=payload,
        )

    def _context_paths(self, raw_context: Any) -> list[Path]:
        if not isinstance(raw_context, list):
            return []
        return [Path(value) for value in raw_context if isinstance(value, str)]

    def _source_key(self, rel_path: Path, payload: dict[str, Any]) -> str:
        if len(payload) == 1:
            only_key = next(iter(payload.keys()))
            if isinstance(only_key, str):
                return only_key
        return rel_path.stem.replace("-", "_")

    def _is_allowed_context_path(self, rel_path: Path) -> bool:
        return any(rel_path == root or rel_path.is_relative_to(root) for root in self._allowed_roots())

    def _allowed_roots(self) -> tuple[Path, ...]:
        roots = list(DEFAULT_ALLOWED_CONTEXT_ROOTS)
        if self.business_pack_id is not None:
            pack = self.business_packs.load(self.business_pack_id)
            roots.extend(self._relative_parents(pack.context_paths))
            roots.extend(self._relative_parents(pack.policy_paths))
        return tuple(dict.fromkeys(roots))

    def _relative_parents(self, paths: tuple[Path, ...]) -> list[Path]:
        parents: list[Path] = []
        for path in paths:
            try:
                parents.append(path.parent.relative_to(self.root))
            except ValueError:
                continue
        return parents

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
