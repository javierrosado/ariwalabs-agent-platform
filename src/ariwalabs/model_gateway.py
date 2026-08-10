from pathlib import Path
from typing import Any
from uuid import uuid4

from adapters.models.base import ModelAdapter, ModelResult
from adapters.models.errors import (
    ModelGatewayError,
    ModelOutputError,
    ModelProfileError,
    ModelProviderError,
)

from .audit import AuditLogger
from .model_profiles import SUPPORTED_MODEL_PROFILES


class ModelGateway:
    def __init__(self, *, adapter: ModelAdapter, root: Path | None = None):
        self.adapter = adapter
        audit_root = root or Path(".")
        self.audit = AuditLogger(audit_root / "runtime/data/audit.jsonl")

    def generate(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
        correlation_id: str | None = None,
        skill_id: str | None = None,
    ) -> ModelResult:
        request_id = f"model-{uuid4().hex[:12]}"
        self._validate_request(
            profile=profile,
            system_prompt=system_prompt,
            payload=payload,
            output_schema=output_schema,
        )
        self.audit.append(
            "model.request.started",
            {
                "request_id": request_id,
                "profile": profile,
                "payload_keys": sorted(payload),
                "schema_title": output_schema.get("title"),
                "skill_id": skill_id,
            },
            correlation_id=correlation_id or request_id,
        )
        try:
            result = self.adapter.generate(
                profile=profile,
                system_prompt=system_prompt,
                payload=payload,
                output_schema=output_schema,
            )
        except ModelGatewayError:
            self.audit.error(
                "model.request.failed",
                error_type="ModelGatewayError",
                message="adapter failure",
                correlation_id=correlation_id or request_id,
                metadata={"request_id": request_id, "profile": profile},
            )
            raise
        except Exception as exc:
            self.audit.error(
                "model.request.failed",
                error_type=exc.__class__.__name__,
                message=str(exc),
                correlation_id=correlation_id or request_id,
                metadata={"request_id": request_id, "profile": profile},
            )
            msg = "adapter de modelo fallo"
            raise ModelProviderError(msg) from exc

        self._validate_result(result)
        self.audit.append(
            "model.request.completed",
            {
                "request_id": request_id,
                "profile": profile,
                "status": result.get("status"),
                "has_usage": isinstance(result.get("usage"), dict),
                "has_estimated_cost": isinstance(result.get("estimated_cost"), dict),
                "skill_id": skill_id,
            },
            correlation_id=correlation_id or request_id,
        )
        self._audit_cost(
            request_id=request_id,
            profile=profile,
            result=result,
            correlation_id=correlation_id or request_id,
            skill_id=skill_id,
        )
        return result

    def generate_structured(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
        correlation_id: str | None = None,
        skill_id: str | None = None,
    ) -> ModelResult:
        try:
            result = self.generate(
                profile=profile,
                system_prompt=system_prompt,
                payload=payload,
                output_schema=output_schema,
                correlation_id=correlation_id,
                skill_id=skill_id,
            )
        except ModelOutputError as exc:
            return self._recoverable_result(
                profile=profile,
                status="invalid_output",
                error_type=exc.__class__.__name__,
                message=str(exc),
                retryable=True,
                correlation_id=correlation_id,
                skill_id=skill_id,
            )
        except ModelProviderError as exc:
            return self._recoverable_result(
                profile=profile,
                status="provider_failed",
                error_type=exc.__class__.__name__,
                message=str(exc),
                retryable=True,
                correlation_id=correlation_id,
                skill_id=skill_id,
            )
        if result.get("status") in {"refused", "incomplete"}:
            status = str(result["status"])
            return {
                **result,
                "error": {
                    "type": "ModelOutputError",
                    "message": f"modelo retorno estado {status}",
                    "retryable": status == "incomplete",
                },
            }
        return {**result, "error": None}

    def _validate_request(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
    ) -> None:
        if profile not in SUPPORTED_MODEL_PROFILES:
            msg = f"perfil de modelo no soportado: {profile}"
            raise ModelProfileError(msg)
        if not system_prompt.strip():
            msg = "system_prompt es obligatorio"
            raise ValueError(msg)
        if not isinstance(payload, dict):
            msg = "payload debe ser dict"
            raise TypeError(msg)
        if not isinstance(output_schema, dict):
            msg = "output_schema debe ser dict"
            raise TypeError(msg)
        if not output_schema:
            msg = "output_schema es obligatorio"
            raise ModelOutputError(msg)

    def _validate_result(self, result: ModelResult) -> None:
        if not isinstance(result, dict):
            msg = "resultado de modelo debe ser dict"
            raise TypeError(msg)
        if not isinstance(result.get("status"), str):
            msg = "resultado de modelo requiere status string"
            raise ModelOutputError(msg)
        if "content" not in result:
            msg = "resultado de modelo requiere content"
            raise ModelOutputError(msg)

    def _audit_cost(
        self,
        *,
        request_id: str,
        profile: str,
        result: ModelResult,
        correlation_id: str,
        skill_id: str | None,
    ) -> None:
        usage = result.get("usage")
        estimated_cost = result.get("estimated_cost")
        if not isinstance(usage, dict) and not isinstance(estimated_cost, dict):
            return
        tokens_in = usage.get("tokens_in") if isinstance(usage, dict) else None
        tokens_out = usage.get("tokens_out") if isinstance(usage, dict) else None
        self.audit.cost(
            "model.cost.recorded",
            execution_id=correlation_id,
            logical_profile=profile,
            tokens_in=tokens_in if isinstance(tokens_in, int) else None,
            tokens_out=tokens_out if isinstance(tokens_out, int) else None,
            estimated_cost=estimated_cost if isinstance(estimated_cost, dict) else None,
            metadata={"request_id": request_id, "skill_id": skill_id},
        )

    def _recoverable_result(
        self,
        *,
        profile: str,
        status: str,
        error_type: str,
        message: str,
        retryable: bool,
        correlation_id: str | None,
        skill_id: str | None,
    ) -> ModelResult:
        event_type = (
            "model.output.invalid"
            if status == "invalid_output"
            else "model.provider.failed_recoverable"
        )
        self.audit.append(
            event_type,
            {
                "profile": profile,
                "status": status,
                "error": {
                    "type": error_type,
                    "message": message,
                    "retryable": retryable,
                },
                "skill_id": skill_id,
            },
            severity="warning",
            correlation_id=correlation_id,
        )
        return {
            "status": status,
            "profile": profile,
            "content": None,
            "usage": {"tokens_in": None, "tokens_out": None},
            "estimated_cost": None,
            "error": {
                "type": error_type,
                "message": message,
                "retryable": retryable,
            },
        }
