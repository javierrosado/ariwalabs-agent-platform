from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from adapters.models.errors import ModelConfigError, ModelOutputError, ModelProviderError
from adapters.models.openai import OpenAIModelAdapter, OpenAIModelConfig
from ariwalabs.model_costs import ModelCostEstimator, ModelPrice


def test_openai_config_loads_models_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        (
            "OPENAI_API_KEY=test-key\n"
            "OPENAI_REASONING_MODEL=gpt-reasoning\n"
            "OPENAI_GENERATION_MODEL=gpt-generation\n"
            "OPENAI_EVALUATION_MODEL=gpt-evaluation\n"
            "OPENAI_FAST_MODEL=gpt-fast\n"
            "OPENAI_TIMEOUT_SECONDS=45"
        ),
        encoding="utf-8",
    )

    config = OpenAIModelConfig.from_environment(env_file=env_file, env={})

    assert config.api_key == "test-key"
    assert config.timeout_seconds == 45
    assert config.model_for_profile("reasoning") == "gpt-reasoning"
    assert config.model_for_profile("generation") == "gpt-generation"
    assert config.model_for_profile("evaluation") == "gpt-evaluation"
    assert config.model_for_profile("fast_structured") == "gpt-fast"


def test_openai_config_requires_api_key() -> None:
    try:
        OpenAIModelConfig.from_environment(
            env={"OPENAI_DEFAULT_MODEL": "gpt-test", "OPENAI_API_KEY": ""},
        )
    except ModelConfigError as exc:
        assert "OPENAI_API_KEY es obligatorio" in str(exc)
    else:
        raise AssertionError("config sin API key debio fallar")


def test_openai_config_uses_default_model_for_profile() -> None:
    config = OpenAIModelConfig.from_environment(
        env={"OPENAI_API_KEY": "test-key", "OPENAI_DEFAULT_MODEL": "gpt-default"},
    )

    assert config.model_for_profile("generation") == "gpt-default"


def test_openai_adapter_sends_strict_json_schema_request() -> None:
    client = FakeResponsesClient(
        response=SimpleNamespace(
            status="completed",
            output_text='{"summary": "ok"}',
            usage=SimpleNamespace(input_tokens=12, output_tokens=4),
        ),
    )
    adapter = OpenAIModelAdapter(
        config=OpenAIModelConfig(
            api_key="test-key",
            models_by_profile={"generation": "gpt-generation"},
        ),
        responses_client=client,
    )

    result = adapter.generate(
        profile="generation",
        system_prompt="System prompt.",
        payload={"objective": "draft"},
        output_schema={
            "title": "Sample Output",
            "type": "object",
            "additionalProperties": False,
            "required": ["summary"],
            "properties": {"summary": {"type": "string"}},
        },
    )

    assert result["status"] == "completed"
    assert result["provider"] == "openai"
    assert result["profile"] == "generation"
    assert result["model"] == "gpt-generation"
    assert result["content"] == {"summary": "ok"}
    assert result["usage"] == {"tokens_in": 12, "tokens_out": 4}
    assert client.last_request["model"] == "gpt-generation"
    assert client.last_request["instructions"] == "System prompt."
    assert client.last_request["input"] == '{"objective": "draft"}'
    text_format = client.last_request["text"]["format"]
    assert text_format["type"] == "json_schema"
    assert text_format["name"] == "Sample_Output"
    assert text_format["strict"] is True


def test_openai_adapter_estimates_cost_when_price_is_configured() -> None:
    client = FakeResponsesClient(
        response=SimpleNamespace(
            status="completed",
            output_text='{"summary": "ok"}',
            usage=SimpleNamespace(input_tokens=1000, output_tokens=500),
        ),
    )
    adapter = OpenAIModelAdapter(
        config=OpenAIModelConfig(
            api_key="test-key",
            models_by_profile={"generation": "gpt-test"},
        ),
        responses_client=client,
        cost_estimator=ModelCostEstimator(
            prices={
                "gpt-test": ModelPrice(
                    model="gpt-test",
                    input_per_1m=Decimal("2.00"),
                    output_per_1m=Decimal("12.00"),
                ),
            },
        ),
    )

    result = adapter.generate(
        profile="generation",
        system_prompt="System prompt.",
        payload={"objective": "draft"},
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["summary"],
            "properties": {"summary": {"type": "string"}},
        },
    )

    assert result["estimated_cost"]["amount"] == 0.008
    assert result["estimated_cost"]["pricing_unit"] == "per_1m_tokens"


def test_openai_adapter_parses_nested_output_text() -> None:
    client = FakeResponsesClient(
        response={
            "status": "completed",
            "output": [{"content": [{"text": '{"summary": "nested"}'}]}],
        },
    )
    adapter = OpenAIModelAdapter(
        config=OpenAIModelConfig(
            api_key="test-key",
            models_by_profile={"fast_structured": "gpt-fast"},
        ),
        responses_client=client,
    )

    result = adapter.generate(
        profile="fast_structured",
        system_prompt="System prompt.",
        payload={},
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["summary"],
            "properties": {"summary": {"type": "string"}},
        },
    )

    assert result["content"] == {"summary": "nested"}


def test_openai_adapter_rejects_schema_mismatch() -> None:
    adapter = OpenAIModelAdapter(
        config=OpenAIModelConfig(
            api_key="test-key",
            models_by_profile={"evaluation": "gpt-evaluation"},
        ),
        responses_client=FakeResponsesClient(
            response=SimpleNamespace(status="completed", output_text='{"extra": true}'),
        ),
    )

    try:
        adapter.generate(
            profile="evaluation",
            system_prompt="System prompt.",
            payload={},
            output_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["summary"],
                "properties": {"summary": {"type": "string"}},
            },
        )
    except ModelOutputError as exc:
        assert "did not match output_schema" in str(exc)
    else:
        raise AssertionError("schema mismatch debio fallar")


def test_openai_adapter_wraps_provider_failure() -> None:
    adapter = OpenAIModelAdapter(
        config=OpenAIModelConfig(
            api_key="test-key",
            models_by_profile={"reasoning": "gpt-reasoning"},
        ),
        responses_client=FailingResponsesClient(),
    )

    try:
        adapter.generate(
            profile="reasoning",
            system_prompt="System prompt.",
            payload={},
            output_schema={"type": "object"},
        )
    except ModelProviderError as exc:
        assert "OpenAI provider request failed" in str(exc)
    else:
        raise AssertionError("provider fallido debio fallar")


class FakeResponsesClient:
    def __init__(self, *, response: Any):
        self.response = response
        self.last_request: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> Any:
        self.last_request = kwargs
        return self.response


class FailingResponsesClient:
    def create(self, **kwargs: Any) -> Any:
        raise RuntimeError("provider exploded")
