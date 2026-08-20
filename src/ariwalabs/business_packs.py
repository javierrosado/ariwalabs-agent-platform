from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import load_yaml

Finding = dict[str, str]


@dataclass(frozen=True)
class BusinessPack:
    pack_id: str
    path: Path
    owner_role: str
    agent_paths: tuple[Path, ...]
    context_paths: tuple[Path, ...]
    policy_paths: tuple[Path, ...]
    handoff_paths: tuple[Path, ...]

    def agent_path(self, agent_id: str) -> Path:
        for path in self.agent_paths:
            agent_yaml = path / "agent.yaml"
            if path.name == agent_id and agent_yaml.exists():
                return path
            if agent_yaml.exists():
                payload = load_yaml(agent_yaml).get("agent", {})
                if payload.get("id") == agent_id:
                    return path
        msg = f"{self.pack_id}: agente no declarado {agent_id}"
        raise ValueError(msg)


class BusinessPackRegistry:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def default_agents_dir(self) -> Path:
        return self.root / "agents"

    def default_handoffs_dir(self) -> Path:
        return self.root / "docs" / "handoffs"

    def agent_dirs(self, business_pack_id: str | None = None) -> tuple[Path, ...]:
        if business_pack_id is None:
            agents_dir = self.default_agents_dir()
            if not agents_dir.exists():
                return ()
            return tuple(sorted(path for path in agents_dir.iterdir() if path.is_dir()))
        return self.load(business_pack_id).agent_paths

    def agent_path(self, agent_id: str, business_pack_id: str | None = None) -> Path:
        if business_pack_id is None:
            return self.root / "agents" / agent_id
        return self.load(business_pack_id).agent_path(agent_id)

    def handoff_files(self, business_pack_id: str | None = None) -> tuple[Path, ...]:
        if business_pack_id is None:
            docs_dir = self.default_handoffs_dir()
            if not docs_dir.exists():
                return ()
            return tuple(sorted(docs_dir.glob("*.yaml")))
        return tuple(path for path in self.load(business_pack_id).handoff_paths if path.suffix == ".yaml")

    def load(self, pack_id: str) -> BusinessPack:
        pack_path = self.root / "business_packs" / pack_id / "pack.yaml"
        if not pack_path.exists():
            msg = f"business pack inexistente {pack_id}"
            raise ValueError(msg)
        payload = load_yaml(pack_path).get("business_pack", {})
        if not isinstance(payload, dict):
            msg = f"{pack_path}: falta business_pack"
            raise TypeError(msg)
        assets = payload.get("domain_assets", {})
        if not isinstance(assets, dict):
            assets = {}
        return BusinessPack(
            pack_id=pack_id,
            path=pack_path.parent,
            owner_role=self._owner_role(payload),
            agent_paths=self._paths(assets.get("agents", [])),
            context_paths=self._paths(assets.get("context", [])),
            policy_paths=self._paths(assets.get("policies", [])),
            handoff_paths=self._paths(assets.get("handoffs", [])),
        )

    def validate_repository(self) -> list[Finding]:
        packs_dir = self.root / "business_packs"
        if not packs_dir.exists():
            return []
        findings: list[Finding] = []
        seen_ids: dict[str, Path] = {}
        for pack_yaml in sorted(packs_dir.glob("*/pack.yaml")):
            findings.extend(self._validate_pack(pack_yaml, seen_ids))
        return findings

    def _validate_pack(self, pack_yaml: Path, seen_ids: dict[str, Path]) -> list[Finding]:
        findings: list[Finding] = []
        payload = load_yaml(pack_yaml).get("business_pack")
        if not isinstance(payload, dict):
            return [self._finding("error", self._format(pack_yaml, "falta business_pack"))]
        pack_id = payload.get("id")
        if not isinstance(pack_id, str) or not pack_id:
            findings.append(self._finding("error", self._format(pack_yaml, "id requerido")))
        elif pack_id in seen_ids:
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        pack_yaml,
                        f"id duplicado {pack_id}; ya existe en {seen_ids[pack_id]}",
                    ),
                )
            )
        else:
            seen_ids[pack_id] = pack_yaml
        if pack_id and pack_yaml.parent.name != pack_id:
            findings.append(
                self._finding(
                    "error",
                    self._format(pack_yaml, f"carpeta debe llamarse {pack_id}"),
                )
            )
        for field in ("name", "version", "purpose"):
            if not isinstance(payload.get(field), str) or not payload.get(field):
                findings.append(
                    self._finding("error", self._format(pack_yaml, f"{field} requerido"))
                )
        if not self._owner_role(payload):
            findings.append(self._finding("error", self._format(pack_yaml, "owner_role requerido")))
        assets = payload.get("domain_assets")
        if not isinstance(assets, dict):
            findings.append(
                self._finding("error", self._format(pack_yaml, "domain_assets debe ser objeto"))
            )
            return findings
        for key in ("agents", "context", "policies", "handoffs"):
            findings.extend(self._validate_path_list(pack_yaml, assets, key))
        findings.extend(self._validate_agent_paths(pack_yaml, assets))
        return findings

    def _validate_agent_paths(self, pack_yaml: Path, assets: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        raw_values = assets.get("agents", [])
        if not isinstance(raw_values, list):
            return findings
        for value in raw_values:
            if not isinstance(value, str):
                continue
            agent_path = self.root / Path(value)
            if agent_path.exists() and not (agent_path / "agent.yaml").exists():
                findings.append(
                    self._finding(
                        "error",
                        self._format(pack_yaml, f"agente sin agent.yaml {value}"),
                    )
                )
        return findings

    def _validate_path_list(
        self,
        pack_yaml: Path,
        assets: dict[str, Any],
        key: str,
    ) -> list[Finding]:
        raw_values = assets.get(key, [])
        if not isinstance(raw_values, list):
            return [
                self._finding("error", self._format(pack_yaml, f"domain_assets.{key} debe ser lista"))
            ]
        findings: list[Finding] = []
        for value in raw_values:
            if not isinstance(value, str):
                findings.append(
                    self._finding(
                        "error",
                        self._format(pack_yaml, f"domain_assets.{key} contiene valor no string"),
                    )
                )
                continue
            rel_path = Path(value)
            if rel_path.is_absolute() or ".." in rel_path.parts:
                findings.append(
                    self._finding(
                        "error",
                        self._format(pack_yaml, f"ruta fuera del repositorio {value}"),
                    )
                )
                continue
            if not (self.root / rel_path).exists():
                findings.append(
                    self._finding("error", self._format(pack_yaml, f"ruta inexistente {value}"))
                )
        return findings

    def _paths(self, values: Any) -> tuple[Path, ...]:
        if not isinstance(values, list):
            return ()
        return tuple(self.root / Path(value) for value in values if isinstance(value, str))

    def _owner_role(self, payload: dict[str, Any]) -> str:
        owner_role = payload.get("owner_role", payload.get("owner"))
        return owner_role if isinstance(owner_role, str) else ""

    def _format(self, path: Path, message: str) -> str:
        return f"{path.relative_to(self.root).as_posix()}: {message}"

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
