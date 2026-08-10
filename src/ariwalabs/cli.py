import argparse
import json
import sys
from pathlib import Path

from .approval_engine import ApprovalEngine
from .framework_validator import FrameworkValidator
from .repository import JsonRepository
from .runtime import AgentRuntime


def main() -> int:
    parser = argparse.ArgumentParser(prog="ariwalabs")
    sub = parser.add_subparsers(dest="command", required=True)

    framework = sub.add_parser("framework")
    framework_sub = framework.add_subparsers(dest="framework_command", required=True)
    validate = framework_sub.add_parser("validate-repository")
    validate.add_argument("--root", default=".")

    agent = sub.add_parser("agent")
    agent_sub = agent.add_subparsers(dest="agent_command", required=True)
    run = agent_sub.add_parser("run")
    run.add_argument("request")
    run.add_argument("--root", default=".")

    execution = sub.add_parser("execution")
    execution_sub = execution.add_subparsers(dest="execution_command", required=True)
    listing = execution_sub.add_parser("list")
    listing.add_argument("--root", default=".")

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

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "framework":
        result = FrameworkValidator(root).validate_repository()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1 if result["status"] == "blocked" else 0

    if args.command == "agent":
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        result = AgentRuntime(root).run(request)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.command == "execution":
        repo = JsonRepository(root / "runtime/data")
        for path in repo.list("executions"):
            print(path.name)
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
            result = AirtableHttpAdapter(config=config, root=root).validate_access(
                table=args.table,
            )
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


if __name__ == "__main__":
    raise SystemExit(main())
