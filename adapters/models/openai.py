import json
import os
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from ariwalabs.model_costs import ModelCostEstimator
from ariwalabs.model_profiles import SUPPORTED_MODEL_PROFILES

from .base import ModelResult
from .errors import ModelConfigError, ModelOutputError, ModelProviderError

DEFAULT_TIMEOUT_SECONDS = 30


class OpenAIResponsesClient(Protocol):
    def create(self, **kwargs: Any) -> Any:
        ...


@dataclass(frozen=True)
class OpenAIModelConfig:
    api_key: str
    models_by_profile: dict[str, str]
    default_model: str | None = None
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_key", self.api_key.strip())
        normalized_models = {
            profile: model.strip()
            for profile, model in self.models_by_profile.items()
            if model.strip()
        }
        object.__setattr__(self, "models_by_profile", normalized_models)
        if self.default_model is not None:
            object.__setattr__(self, "default_model", self.default_model.strip() or None)
        if not self.api_key:
            msg = "OPENAI_API_KEY es obligatorio"
            raise ModelConfigError(msg)
        if not normalized_models and self.default_model is None:
            msg = "al menos un modelo OpenAI por perfil o OPENAI_DEFAULT_MODEL es obligatorio"
            raise ModelConfigError(msg)

    @classmethod
    def from_environment(
        cls,
        *,
        root: Path | None = None,
        env_file: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> "OpenAIModelConfig":
        values = dict(os.environ if env is None else env)
        config_file = env_file
        if config_file is None and root is not None:
            config_file = root / ".env"
        if config_file is not None:
            values = {**_load_env_file(config_file), **values}

        return cls(
            api_key=values.get("OPENAI_API_KEY", ""),
            default_model=values.get("OPENAI_DEFAULT_MODEL"),
            timeout_seconds=_int_value(
                values.get("OPENAI_TIMEOUT_SECONDS"),
                default=DEFAULT_TIMEOUT_SECONDS,
            ),
            models_by_profile={
                "reasoning": values.get("OPENAI_REASONING_MODEL", ""),
                "generation": values.get("OPENAI_GENERATION_MODEL", ""),
                "evaluation": values.get("OPENAI_EVALUATION_MODEL", ""),
                "fast_structured": values.get("OPENAI_FAST_MODEL", ""),
            },
        )

    def model_for_profile(self, profile: str) -> str:
        if profile not in SUPPORTED_MODEL_PROFILES:
            msg = f"perfil de modelo no soportado: {profile}"
            raise ModelConfigError(msg)
        model = self.models_by_profile.get(profile) or self.default_model
        if model is None:
            msg = f"modelo OpenAI no configurado para perfil {profile}"
            raise ModelConfigError(msg)
        return model


class OpenAIModelAdapter:
    def __init__(
        self,
        *,
        config: OpenAIModelConfig,
        responses_client: OpenAIResponsesClient | None = None,
        cost_estimator: ModelCostEstimator | None = None,
    ):
        self.config = config
        self.responses_client = responses_client or _default_responses_client(config)
        self.cost_estimator = cost_estimator or ModelCostEstimator.from_environment()

    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> ModelResult:
        model = self.config.model_for_profile(profile)
        schema_name = _schema_name(output_schema, profile)
        try:
            response = self.responses_client.create(
                model=model,
                instructions=system_prompt,
                input=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": output_schema,
                        "strict": True,
                    },
                },
            )
        except Exception as exc:
            msg = "OpenAI provider request failed"
            raise ModelProviderError(msg) from exc

        content = _parse_response_content(response)
        _validate_content(content=content, output_schema=output_schema)

        usage = _response_usage(response)
        return {
            "status": _response_status(response),
            "provider": "openai",
            "profile": profile,
            "model": model,
            "content": content,
            "usage": usage,
            "estimated_cost": self.cost_estimator.estimate(
                model=model,
                tokens_in=usage["tokens_in"],
                tokens_out=usage["tokens_out"],
            ),
        }


def _default_responses_client(config: OpenAIModelConfig) -> OpenAIResponsesClient:
    try:
        openai_module = import_module("openai")
    except ImportError as exc:
        msg = "openai SDK no esta instalado"
        raise ModelConfigError(msg) from exc
    client = openai_module.OpenAI(api_key=config.api_key, timeout=config.timeout_seconds)
    return cast(OpenAIResponsesClient, client.responses)


def _parse_response_content(response: Any) -> dict[str, Any]:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return _parse_json_object(output_text)

    output = _value(response, "output")
    if isinstance(output, list):
        for item in output:
            content = _value(item, "content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                text = _value(content_item, "text")
                if isinstance(text, str) and text.strip():
                    return _parse_json_object(text)

    msg = "OpenAI response did not contain JSON output"
    raise ModelOutputError(msg)


def _validate_content(
    *,
    content: dict[str, Any],
    output_schema: dict[str, Any],
) -> None:
    try:
        jsonschema = import_module("jsonschema")
        jsonschema.validate(instance=content, schema=output_schema)
    except Exception as exc:
        msg = "OpenAI response did not match output_schema"
        raise ModelOutputError(msg) from exc


def _parse_json_object(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = "OpenAI response was not valid JSON"
        raise ModelOutputError(msg) from exc
    if not isinstance(parsed, dict):
        msg = "OpenAI response JSON must be an object"
        raise ModelOutputError(msg)
    return parsed


def _response_status(response: Any) -> str:
    status = _value(response, "status")
    return status if isinstance(status, str) and status else "completed"


def _response_usage(response: Any) -> dict[str, int | None]:
    usage = _value(response, "usage")
    if usage is None:
        return {"tokens_in": None, "tokens_out": None}
    input_tokens = _value(usage, "input_tokens")
    output_tokens = _value(usage, "output_tokens")
    return {
        "tokens_in": input_tokens if isinstance(input_tokens, int) else None,
        "tokens_out": output_tokens if isinstance(output_tokens, int) else None,
    }


def _schema_name(output_schema: dict[str, Any], profile: str) -> str:
    title = output_schema.get("title")
    base = title if isinstance(title, str) and title.strip() else f"{profile}_output"
    safe = "".join(char if char.isalnum() else "_" for char in base)
    return safe.strip("_") or f"{profile}_output"


def _value(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _int_value(raw: str | None, *, default: int) -> int:
    if raw is None or not raw.strip():
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        msg = "OPENAI_TIMEOUT_SECONDS debe ser entero"
        raise ModelConfigError(msg) from exc
    if parsed <= 0:
        msg = "OPENAI_TIMEOUT_SECONDS debe ser positivo"
        raise ModelConfigError(msg)
    return parsed


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
