#!/usr/bin/env python3
"""Claude Code PreToolUse adapter for the repository gate.

Reads the hook payload on stdin, asks `amigos gate` about the file the tool is
about to write, and denies the call when the gate refuses. It holds no rules of
its own; the decision belongs to src/amigos/gate.py.

Wire it up in .claude/settings.json:

    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Edit|Write|NotebookEdit",
            "hooks": [
              {
                "type": "command",
                "command": "python3 \\"$CLAUDE_PROJECT_DIR/integrations/claude-code/gate_hook.py\\""
              }
            ]
          }
        ]
      }
    }
"""

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from amigos import config as config_module, gate  # noqa: E402


def allow() -> None:
    sys.exit(0)


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        allow()  # Not a payload we understand; the pre-commit hook is the backstop.

    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        allow()

    root = Path(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or REPO)
    try:
        cfg = config_module.load(root=config_module.find_root(root) or root)
    except config_module.ConfigError as exc:
        deny(f"amigos gate could not read its configuration: {exc}")

    try:
        relative = str(Path(file_path).resolve().relative_to(cfg.root))
    except ValueError:
        allow()  # Outside the repository, so outside the contract.

    decision = gate.decide(cfg, [relative])
    if decision.permitted:
        allow()

    deny(
        f"Blocked by the amigos repository gate: {decision.reason}.\n\n"
        f"{relative} is a governed path. Contract-first development means the "
        "acceptance contract has to be ready before implementation starts.\n\n"
        "Either make the story ready (amigos check <STORY-ID>), or work on the "
        "contract itself under .amigos/ and docs/, which are not governed."
    )


if __name__ == "__main__":
    main()
