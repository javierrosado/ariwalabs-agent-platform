from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import json

class JsonRepository:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, category: str, entity_id: str, payload: dict[str, Any]) -> Path:
        folder = self.base_path / category
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{entity_id}.json"
        body = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def list(self, category: str) -> list[Path]:
        folder = self.base_path / category
        return sorted(folder.glob("*.json")) if folder.exists() else []
