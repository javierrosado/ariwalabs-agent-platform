import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JsonRepository:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, category: str, entity_id: str, payload: dict[str, Any]) -> Path:
        folder = self.base_path / category
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{entity_id}.json"
        body = {
            "saved_at": datetime.now(UTC).isoformat(),
            "payload": payload,
        }
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, category: str, entity_id: str) -> dict[str, Any]:
        path = self.base_path / category / f"{entity_id}.json"
        body = json.loads(path.read_text(encoding="utf-8"))
        payload = body.get("payload", {})
        if not isinstance(payload, dict):
            msg = f"{category}/{entity_id}: payload invalido"
            raise TypeError(msg)
        return payload

    def exists(self, category: str, entity_id: str) -> bool:
        return (self.base_path / category / f"{entity_id}.json").exists()

    def list(self, category: str) -> list[Path]:
        folder = self.base_path / category
        return sorted(folder.glob("*.json")) if folder.exists() else []
