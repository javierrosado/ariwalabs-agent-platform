from typing import Any

from .base import ModelResult


class FakeModelAdapter:
    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> ModelResult:
        return {
            "status": "draft",
            "profile": profile,
            "content": {
                "summary": "fake model response",
                "payload_keys": sorted(payload),
                "schema_title": output_schema.get("title"),
                "system_prompt_length": len(system_prompt),
            },
            "usage": {
                "tokens_in": None,
                "tokens_out": None,
            },
            "estimated_cost": None,
        }
