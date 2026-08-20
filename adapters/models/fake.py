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
        content = self._fake_content(payload=payload, output_schema=output_schema)
        return {
            "status": "draft",
            "profile": profile,
            "content": content,
            "usage": {
                "tokens_in": None,
                "tokens_out": None,
            },
            "estimated_cost": None,
        }

    def _fake_content(
        self,
        *,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        required = output_schema.get("required")
        properties = output_schema.get("properties")
        if not isinstance(required, list) or not isinstance(properties, dict):
            return {
                "summary": "fake model response",
                "payload_keys": sorted(payload),
                "schema_title": output_schema.get("title"),
            }
        return {
            field: self._fake_value(
                schema=properties.get(field, {}),
                root_schema=output_schema,
            )
            for field in required
            if isinstance(field, str)
        }

    def _fake_value(self, *, schema: Any, root_schema: dict[str, Any]) -> Any:
        if not isinstance(schema, dict):
            return None
        if "const" in schema:
            return schema["const"]
        ref = schema.get("$ref")
        if isinstance(ref, str):
            return self._fake_value(schema=self._resolve_ref(ref, root_schema), root_schema=root_schema)
        enum = schema.get("enum")
        if isinstance(enum, list) and enum:
            return enum[0]
        schema_type = schema.get("type")
        if isinstance(schema_type, list):
            if "null" in schema_type:
                return None
            schema_type = schema_type[0] if schema_type else None
        if schema_type == "object":
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            if not isinstance(required, list) or not isinstance(properties, dict):
                return {}
            return {
                field: self._fake_value(
                    schema=properties.get(field, {}),
                    root_schema=root_schema,
                )
                for field in required
                if isinstance(field, str)
            }
        if schema_type == "array":
            return []
        if schema_type == "boolean":
            return False
        if schema_type in {"integer", "number"}:
            return 0
        if schema_type == "string":
            return "fake model response"
        return None

    def _resolve_ref(self, ref: str, root_schema: dict[str, Any]) -> Any:
        if not ref.startswith("#/"):
            return {}
        current: Any = root_schema
        for part in ref.removeprefix("#/").split("/"):
            if not isinstance(current, dict):
                return {}
            current = current.get(part, {})
        return current
