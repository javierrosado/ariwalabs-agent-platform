import argparse
import json
import sys
from pathlib import Path

from .agent_registry import AgentRegistry
from .airtable_sync import AirtableSync
from .approval_engine import ApprovalEngine
from .errors import AriwaLabsError
from .framework_validator import FrameworkValidator
from .handoff_runtime import HandoffExecutionRequest, HandoffRuntime
from .repository import JsonRepository
from .runtime import AgentRuntime


def main() -> int:
    parser = argparse.ArgumentParser(prog="ariwalabs")
    sub = parser.add_subparsers(dest="command", required=True)

    framework = sub.add_parser("framework")
    framework_sub = framework.add_subparsers(dest="framework_command", required=True)
    validate = framework_sub.add_parser("validate-repository")
    validate.add_argument("--root", default=".")
    validate.add_argument("--business-pack")

    agent = sub.add_parser("agent")
    agent_sub = agent.add_subparsers(dest="agent_command", required=True)
    run = agent_sub.add_parser("run")
    run.add_argument("request")
    run.add_argument("--root", default=".")
    run.add_argument("--business-pack")

    agent_registry = sub.add_parser("agent-registry")
    agent_registry_sub = agent_registry.add_subparsers(
        dest="agent_registry_command",
        required=True,
    )
    agent_registry_list = agent_registry_sub.add_parser("list")
    agent_registry_list.add_argument("--root", default=".")
    agent_registry_list.add_argument("--business-pack")
    agent_registry_show = agent_registry_sub.add_parser("show")
    agent_registry_show.add_argument("agent_id")
    agent_registry_show.add_argument("--root", default=".")
    agent_registry_show.add_argument("--business-pack")

    execution = sub.add_parser("execution")
    execution_sub = execution.add_subparsers(dest="execution_command", required=True)
    listing = execution_sub.add_parser("list")
    listing.add_argument("--root", default=".")
    resume = execution_sub.add_parser("resume")
    resume.add_argument("execution_id")
    resume.add_argument("--root", default=".")

    handoff = sub.add_parser("handoff")
    handoff_sub = handoff.add_subparsers(dest="handoff_command", required=True)
    handoff_execute = handoff_sub.add_parser("execute")
    handoff_execute.add_argument("handoff_id")
    handoff_execute.add_argument("--input", required=True)
    handoff_execute.add_argument("--output", required=True)
    handoff_execute.add_argument("--root", default=".")
    handoff_execute.add_argument("--business-pack")
    handoff_execute.add_argument("--approved", action="store_true")
    handoff_execute.add_argument("--approval-id")
    handoff_execute.add_argument("--idempotency-key")
    handoff_execute.add_argument("--actor", default="company-director")
    handoff_execute.add_argument("--correlation-id")

    approval = sub.add_parser("approval")
    approval_sub = approval.add_subparsers(dest="approval_command", required=True)
    approval_list = approval_sub.add_parser("list")
    approval_list.add_argument("--root", default=".")
    approval_decide = approval_sub.add_parser("decide")
    approval_decide.add_argument("approval_id")
    approval_decide.add_argument("--decision", choices=["approved", "rejected"], required=True)
    approval_decide.add_argument("--reason", required=True)
    approval_decide.add_argument("--root", default=".")

    airtable = sub.add_parser("airtable")
    airtable_sub = airtable.add_subparsers(dest="airtable_command", required=True)
    validate_access = airtable_sub.add_parser("validate-access")
    validate_access.add_argument("--root", default=".")
    validate_access.add_argument("--env-file", default=".env.example")
    validate_access.add_argument("--table")
    sync_execution = airtable_sub.add_parser("sync-execution")
    sync_execution.add_argument("execution_id")
    sync_execution.add_argument("--root", default=".")
    sync_execution.add_argument("--env-file", default=".env")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "framework":
        result = FrameworkValidator(
            root,
            business_pack_id=args.business_pack,
        ).validate_repository()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result["status"] == "blocked" else 0

    if args.command == "agent":
        try:
            request = json.loads(Path(args.request).read_text(encoding="utf-8"))
            result = AgentRuntime(root, business_pack_id=args.business_pack).run(request)
        except AriwaLabsError as exc:
            print(json.dumps(_error_response(exc), indent=2, ensure_ascii=False))
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "agent-registry":
        registry = AgentRegistry(root, business_pack_id=args.business_pack)
        if args.agent_registry_command == "list":
            result = {"agents": registry.list_agents()}
        else:
            result = registry.get_agent(args.agent_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "execution":
        if args.execution_command == "list":
            repo = JsonRepository(root / "runtime/data")
            for path in repo.list("executions"):
                print(path.name)
        else:
            try:
                result = AgentRuntime(root).resume(args.execution_id)
            except AriwaLabsError as exc:
                print(json.dumps(_error_response(exc), indent=2, ensure_ascii=False))
                return 1
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "handoff":
        try:
            result = HandoffRuntime(
                root,
                business_pack_id=args.business_pack,
            ).execute(
                HandoffExecutionRequest(
                    handoff_id=args.handoff_id,
                    input_payload=json.loads(Path(args.input).read_text(encoding="utf-8")),
                    output_payload=json.loads(Path(args.output).read_text(encoding="utf-8")),
                    actor=args.actor,
                    correlation_id=args.correlation_id,
                    approved=args.approved,
                    approval_id=args.approval_id,
                    idempotency_key=args.idempotency_key,
                )
            )
        except AriwaLabsError as exc:
            print(json.dumps(_error_response(exc), indent=2, ensure_ascii=False))
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "approval":
        engine = ApprovalEngine(root)
        if args.approval_command == "list":
            pending_approvals = engine.list_pending()
            print(json.dumps(pending_approvals, indent=2, ensure_ascii=False))
            return 0
        decided_approval = engine.decide(
            approval_id=args.approval_id,
            decision=args.decision,
            reason=args.reason,
            decided_by="company-director",
        )
        print(json.dumps(decided_approval, indent=2, ensure_ascii=False))
        return 0

    if args.command == "airtable":
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from adapters.airtable.client import AirtableConfig, AirtableHttpAdapter
        from adapters.airtable.errors import AirtableAdapterError

        try:
            config = AirtableConfig.from_environment(
                root=root,
                env_file=root / args.env_file,
            )
            adapter = AirtableHttpAdapter(config=config, root=root)
            if args.airtable_command == "validate-access":
                result = adapter.validate_access(table=args.table)
            else:
                result = AirtableSync(root, adapter=adapter).sync_execution(args.execution_id)
        except AirtableAdapterError as exc:
            result = {
                "status": "failed",
                "error_type": exc.__class__.__name__,
                "message": str(exc),
                "suggestion": (
                    "Si el token no tiene permiso de metadata, reintenta con "
                    "`--table <tabla_existente>` o agrega permisos de schema "
                    "al token de Airtable."
                ),
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    return 2


def _error_response(exc: AriwaLabsError) -> dict[str, str]:
    return {
        "status": "failed",
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }


if __name__ == "__main__":
    raise SystemExit(main())
