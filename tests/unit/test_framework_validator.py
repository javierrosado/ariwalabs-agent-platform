from pathlib import Path
from ariwalabs.framework_validator import FrameworkValidator

def test_repository_is_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    result = FrameworkValidator(root).validate_repository()
    assert result["status"] != "blocked", result
