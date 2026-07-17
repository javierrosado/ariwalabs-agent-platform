from typing import Protocol, Any

class ModelAdapter(Protocol):
    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        ...
