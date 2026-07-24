import argparse
import json
from pathlib import Path

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

    return 2

if __name__ == "__main__":
    raise SystemExit(main())
