import json
import sys

from app.services.workflow_service import parse_demo_message


def main() -> None:
    message = " ".join(sys.argv[1:]) or (
        "Hey @BizOpsBot, Acme Corp just reported that the login button isn't "
        "working on Chrome. This is pretty urgent because their team can't "
        "access the dashboard before tomorrow's board meeting. Can you create "
        "a ticket and assign it to Alex from Engineering?"
    )

    task = parse_demo_message(message)
    print(json.dumps(task.model_dump(), indent=2))


if __name__ == "__main__":
    main()
