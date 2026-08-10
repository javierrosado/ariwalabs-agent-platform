import json
from pathlib import Path
from typing import Any

from adapters.models.base import ModelResult
from adapters.models.errors import ModelOutputError, ModelProfileError, ModelProviderError
from adapters.models.fake import FakeModelAdapter
from ariwalabs.model_gateway import ModelGateway


def test_model_gateway_routes_supported_profile(tmp_path: Path) -> None:
    result = ModelGateway(adapter=FakeModelAdapter(), root=tmp_path).generate(
        profile="reasoning",
        system_prompt="System prompt.",
        payload={"objective": "test"},
        output_schema={"title": "sample", "type": "object"},
        correlation_id="exec-test",
    )

    assert result["status"] == "draft"
    assert result["profile"] == "reasoning"
    assert result["content"]["payload_keys"] == ["objective"]


def test_model_gateway_blocks_unknown_profile(tmp_path: Path) -> None:
    gateway = ModelGateway(adapter=FakeModelAdapter(), root=tmp_path)

    try:
        gateway.generate(
            profile="unknown",
            system_prompt="System prompt.",
            payload={},
            output_schema={"type": "object"},
        )
    except ModelProfileError as exc:
        assert "perfil de modelo no soportado" in str(exc)
    else:
        raise AssertionError("perfil desconocido debio fallar")


def test_model_gateway_blocks_empty_schema(tmp_path: Path) -> None:
    gateway = ModelGateway(adapter=FakeModelAdapter(), root=tmp_path)

    try:
        gateway.generate(
            profile="fast_structured",
            system_prompt="System prompt.",
            payload={},
            output_schema={},
        )
    except ModelOutputError as exc:
        assert "output_schema es obligatorio" in str(exc)
    else:
        raise AssertionError("schema vacio debio fallar")


def test_model_gateway_wraps_untyped_adapter_failure(tmp_path: Path) -> None:
    gateway = ModelGateway(adapter=FailingAdapter(), root=tmp_path)

    try:
        gateway.generate(
            profile="generation",
            system_prompt="System prompt.",
            payload={},
            output_schema={"type": "object"},
        )
    except ModelProviderError as exc:
        assert "adapter de modelo fallo" in str(exc)
    else:
        raise AssertionError("adapter fallido debio fallar")


def test_model_gateway_audits_usage_and_cost(tmp_path: Path) -> None:
    gateway = ModelGateway(adapter=UsageAdapter(), root=tmp_path)

    gateway.generate(
        profile="evaluation",
        system_prompt="System prompt.",
        payload={"secret": "should-not-leak"},
        output_schema={"title": "sample", "type": "object"},
        correlation_id="exec-test",
    )

    events = [
        json.loads(line)
        for line in (tmp_path / "runtime/data/audit.jsonl").read_text().splitlines()
    ]
    event_types = [event["event_type"] for event in events]

    assert "model.request.started" in event_types
    assert "model.request.completed" in event_types
    assert "model.cost.recorded" in event_types
    assert "should-not-leak" not in json.dumps(events)


def test_model_gateway_audits_cost_with_skill_id(tmp_path: Path) -> None:
    gateway = ModelGateway(adapter=UsageAdapter(), root=tmp_path)

    gateway.generate(
        profile="evaluation",
        system_prompt="System prompt.",
        payload={"objective": "review"},
        output_schema={"title": "sample", "type": "object"},
        correlation_id="exec-test",
        skill_id="growth-marketing.brand-compliance",
    )

    events = [
        json.loads(line)
        for line in (tmp_path / "runtime/data/audit.jsonl").read_text().splitlines()
    ]
    cost_event = next(
        event for event in events if event["event_type"] == "model.cost.recorded"
    )

    assert cost_event["payload"]["execution_id"] == "exec-test"
    assert cost_event["payload"]["logical_profile"] == "evaluation"
    assert cost_event["payload"]["metadata"]["skill_id"] == (
        "growth-marketing.brand-compliance"
    )


def test_model_gateway_returns_recoverable_invalid_output(tmp_path: Path) -> None:
    gateway = ModelGateway(adapter=InvalidOutputAdapter(), root=tmp_path)

    result = gateway.generate_structured(
        profile="fast_structured",
        system_prompt="System prompt.",
        payload={"secret": "should-not-leak"},
        output_schema={"title": "sample", "type": "object"},
        correlation_id="exec-test",
    )

    assert result["status"] == "invalid_output"
    assert result["content"] is None
    assert result["error"]["type"] == "ModelOutputError"
    assert result["error"]["retryable"] is True

    events = [
        json.loads(line)
        for line in (tmp_path / "runtime/data/audit.jsonl").read_text().splitlines()
    ]
    assert "model.output.invalid" in [event["event_type"] for event in events]
    assert "should-not-leak" not in json.dumps(events)


def test_model_gateway_returns_recoverable_provider_failure(tmp_path: Path) -> None:
    gateway = ModelGateway(adapter=FailingAdapter(), root=tmp_path)

    result = gateway.generate_structured(
        profile="generation",
        system_prompt="System prompt.",
        payload={},
        output_schema={"type": "object"},
        correlation_id="exec-test",
    )

    assert result["status"] == "provider_failed"
    assert result["error"]["type"] == "ModelProviderError"
    assert result["error"]["retryable"] is True


def test_model_gateway_normalizes_incomplete_response() -> None:
    result = ModelGateway(adapter=IncompleteAdapter()).generate_structured(
        profile="generation",
        system_prompt="System prompt.",
        payload={},
        output_schema={"type": "object"},
    )

    assert result["status"] == "incomplete"
    assert result["error"]["retryable"] is True


class FailingAdapter:
    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> ModelResult:
        raise RuntimeError("provider exploded")


class UsageAdapter:
    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> ModelResult:
        return {
            "status": "completed",
            "content": {"ok": True},
            "usage": {"tokens_in": 10, "tokens_out": 5},
            "estimated_cost": {"currency": "USD", "amount": 0.01},
        }


class InvalidOutputAdapter:
    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> ModelResult:
        raise ModelOutputError("schema mismatch")


class IncompleteAdapter:
    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> ModelResult:
        return {
            "status": "incomplete",
            "content": {},
            "usage": {"tokens_in": None, "tokens_out": None},
            "estimated_cost": None,
        }
