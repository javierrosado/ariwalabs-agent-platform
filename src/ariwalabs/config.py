from pathlib import Path
from typing import Any
import yaml

def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}
