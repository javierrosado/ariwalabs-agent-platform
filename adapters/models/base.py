from typing import Any, Protocol

ModelResult = dict[str, Any]


class ModelAdapter(Protocol):
    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> ModelResult:
        ...
