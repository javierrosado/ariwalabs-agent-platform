from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from adapters.models.base import ModelResult

from .business_packs import BusinessPackRegistry
from .config import load_yaml


class SkillModelGateway(Protocol):
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
        ...


@dataclass(frozen=True)
class SkillExecutionRequest:
    agent_id: str
    workflow_id: str
    skill_id: str
    business_pack_id: str | None
    request_input: dict[str, Any]
    composed_context: dict[str, Any]
    correlation_id: str | None = None


class SkillExecutor:
    def __init__(
        self,
        root: Path,
        *,
        model_gateway: SkillModelGateway,
        business_pack_id: str | None = None,
    ):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(self.root)
        self.model_gateway = model_gateway

    def execute(self, request: SkillExecutionRequest) -> ModelResult:
        skill_path = self._skill_path(
            agent_id=request.agent_id,
            skill_id=request.skill_id,
        )
        skill_config = self._skill_config(skill_path)
        model_profile = skill_config.get("model_profile")
        output_schema_ref = skill_config.get("output_schema")
        if not isinstance(model_profile, str):
            msg = f"{request.skill_id}: model_profile invalido"
            raise TypeError(msg)
        if not isinstance(output_schema_ref, str):
            msg = f"{request.skill_id}: output_schema invalido"
            raise TypeError(msg)
        output_schema = load_yaml((skill_path.parent / output_schema_ref).resolve())
        if not isinstance(output_schema, dict) or not output_schema:
            msg = f"{request.skill_id}: output_schema debe ser objeto"
            raise ValueError(msg)
        system_prompt = self._system_prompt(request.agent_id)
        return self.model_gateway.generate_structured(
            profile=model_profile,
            system_prompt=system_prompt,
            payload=self._payload(
                request=request,
                skill_config=skill_config,
                skill_slug=skill_path.parent.name,
            ),
            output_schema=output_schema,
            correlation_id=request.correlation_id,
            skill_id=request.skill_id,
        )

    def _skill_path(self, *, agent_id: str, skill_id: str) -> Path:
        agent_path = self.business_packs.agent_path(agent_id, self.business_pack_id)
        for skill_path in agent_path.glob("skills/*/skill.yaml"):
            skill = self._skill_config(skill_path)
            if skill.get("id") == skill_id:
                return skill_path
        msg = f"skill inexistente {skill_id}"
        raise ValueError(msg)

    def _skill_config(self, skill_path: Path) -> dict[str, Any]:
        payload = load_yaml(skill_path).get("skill")
        if not isinstance(payload, dict):
            msg = f"{skill_path.relative_to(self.root).as_posix()}: falta seccion skill"
            raise TypeError(msg)
        return payload

    def _system_prompt(self, agent_id: str) -> str:
        agent_path = self.business_packs.agent_path(agent_id, self.business_pack_id)
        prompt_path = agent_path / "prompts" / "system.md"
        if not prompt_path.exists():
            msg = f"{prompt_path.relative_to(self.root).as_posix()}: prompt inexistente"
            raise ValueError(msg)
        prompt = prompt_path.read_text(encoding="utf-8")
        if not prompt.strip():
            msg = f"{prompt_path.relative_to(self.root).as_posix()}: prompt vacio"
            raise ValueError(msg)
        return prompt

    def _payload(
        self,
        *,
        request: SkillExecutionRequest,
        skill_config: dict[str, Any],
        skill_slug: str,
    ) -> dict[str, Any]:
        return {
            "agent_id": request.agent_id,
            "workflow_id": request.workflow_id,
            "skill_id": request.skill_id,
            "skill_slug": skill_slug,
            "business_pack_id": request.business_pack_id,
            "request_input": request.request_input,
            "context": request.composed_context.get("data", {}),
            "context_sources": request.composed_context.get("source_paths", []),
            "skill": {
                "purpose": skill_config.get("purpose"),
                "approval_required": skill_config.get("approval_required"),
                "tools": skill_config.get("tools", {}),
            },
        }
