import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

Finding = dict[str, str]


@dataclass(frozen=True)
class CoreSchemaValidator:
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve())

    def validate_payload(
        self,
        *,
        payload: Any,
        schema_name: str,
        source_path: Path,
    ) -> list[Finding]:
        schema_path = self._schema_path(schema_name)
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return [
                self._finding(
                    "error",
                    self._format(source_path, f"schema core inexistente {schema_name}"),
                )
            ]
        except json.JSONDecodeError as exc:
            return [
                self._finding(
                    "error",
                    self._format(source_path, f"schema core invalido {schema_name}: {exc.msg}"),
                )
            ]

        validator = Draft202012Validator(schema)
        findings: list[Finding] = []
        for error in sorted(validator.iter_errors(payload), key=lambda item: item.path):
            location = ".".join(str(part) for part in error.absolute_path)
            suffix = f"{location}: {error.message}" if location else error.message
            findings.append(
                self._finding(
                    "error",
                    self._format(source_path, f"{schema_name}: {suffix}"),
                )
            )
        return findings

    def _format(self, path: Path, message: str) -> str:
        try:
            label = path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            label = path.as_posix()
        return f"{label}: {message}"

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}

    def _schema_path(self, schema_name: str) -> Path:
        local_schema = self.root / "shared" / "schemas" / "core" / schema_name
        if local_schema.exists():
            return local_schema
        return Path(__file__).resolve().parents[2] / "shared" / "schemas" / "core" / schema_name
