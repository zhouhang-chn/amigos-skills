"""Installing the git pre-commit adapter.

The hook holds no rules. It calls the same decision function as every other
adapter and passes the exit code through, so there is exactly one implementation
of the rule.

The interpreter and the package location are resolved at install time and baked
into the hook. A hook that depends on `amigos` being on `PATH`, or on the gated
repository being the amigos-skills checkout, works in exactly one repository —
which is the one place a gate is least needed.
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = "# installed by amigos-skills"

TEMPLATE = '''#!{python}
{marker}
# Refuses a commit that touches governed paths without a ready story.
# Inspect with: amigos hooks status
# Remove with:  amigos hooks uninstall
import sys

sys.path.insert(0, {package_parent!r})

from amigos.cli import main

sys.exit(main(["gate", "--staged"]))
'''

OK = 0
PROBLEM = 2


def hook_path(root: Path) -> Path:
    return root / ".git" / "hooks" / "pre-commit"


def _package_parent() -> str:
    """The directory to put on sys.path so ``import amigos`` resolves."""
    return str(Path(__file__).resolve().parents[1])


def render() -> str:
    return TEMPLATE.format(
        python=sys.executable, marker=MARKER, package_parent=_package_parent()
    )


def _is_ours(path: Path) -> bool:
    return path.is_file() and MARKER in path.read_text(encoding="utf-8", errors="replace")


def install(root: Path, force: bool = False) -> int:
    path = hook_path(root)
    if not path.parent.is_dir():
        print(f"error: {path.parent}: not a git repository")
        return PROBLEM
    if path.exists() and not _is_ours(path) and not force:
        print(f"error: {path}: a pre-commit hook is already installed and amigos "
              "did not write it; refusing to overwrite it")
        print("       re-run with --force to replace it")
        return PROBLEM
    path.write_text(render(), encoding="utf-8")
    path.chmod(0o755)
    print(f"{path}: installed")
    return OK


def uninstall(root: Path) -> int:
    path = hook_path(root)
    if not path.exists():
        print(f"{path}: not present")
        return OK
    if not _is_ours(path):
        print(f"error: {path}: amigos did not write this hook; leaving it alone")
        return PROBLEM
    path.unlink()
    print(f"{path}: removed")
    return OK


def status(root: Path) -> int:
    path = hook_path(root)
    if not path.exists():
        print(f"{path}: not installed")
    elif _is_ours(path):
        print(f"{path}: installed by amigos")
    else:
        print(f"{path}: present, written by something else")
    return OK
