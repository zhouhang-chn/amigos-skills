"""Command line surface: ``amigos init | create | check | lint | status | gate | state | findings | hooks``."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from . import (__version__, config as config_module, dor, findings as findings_module,
               gate as gate_module, hooks, lint as lint_module, story)
from .gherkin import ParseError

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

DEFAULT_CONFIG = {
    "schema_version": 1,
    "stories_dir": ".amigos/stories",
    "lint": {"vague_words_extra": [], "vague_words_remove": []},
    "dor": {"min_primary": 1, "min_counterexamples": 2},
    "gate": {"exempt": list(config_module.DEFAULT_GATE_EXEMPT)},
}


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=None,
                        help="repository root (default: nearest ancestor holding .amigos/)")
    parser.add_argument("--stories-dir", type=Path, default=None,
                        help="override the configured stories directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="amigos",
        description="Contract-first development gate: a deterministic Definition of Ready.",
    )
    parser.add_argument("--version", action="version", version=f"amigos {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="create .amigos/ in this repository")
    init.add_argument("--root", type=Path, default=None, help="repository root")

    create = subparsers.add_parser("create", help="scaffold a story contract workspace")
    create.add_argument("story_id")
    _add_common(create)

    check = subparsers.add_parser("check", help="evaluate the Definition of Ready")
    check.add_argument("story_id")
    check.add_argument("--json", action="store_true", dest="as_json",
                       help="print the dor.json payload instead of a report")
    check.add_argument("--no-write", action="store_true",
                       help="evaluate without writing dor.json")
    _add_common(check)

    lint_cmd = subparsers.add_parser("lint", help="lint acceptance criteria")
    target = lint_cmd.add_mutually_exclusive_group(required=True)
    target.add_argument("story_id", nargs="?", help="story whose acceptance.feature to lint")
    target.add_argument("--file", type=Path, help="lint a feature file directly")
    lint_cmd.add_argument("--json", action="store_true", dest="as_json")
    _add_common(lint_cmd)

    status = subparsers.add_parser("status", help="summarise every story")
    _add_common(status)

    gate = subparsers.add_parser(
        "gate", help="decide whether a change to governed paths is permitted")
    gate.add_argument("--changed-file", action="append", default=[], dest="changed_files",
                      metavar="PATH", help="a changed path; repeatable")
    gate.add_argument("--staged", action="store_true",
                      help="take the changed paths from the git index")
    gate.add_argument("--story", default=None,
                      help="name the active story instead of resolving it")
    gate.add_argument("--json", action="store_true", dest="as_json")
    _add_common(gate)

    state = subparsers.add_parser(
        "state", help="record a lifecycle transition in state.json")
    state.add_argument("story_id")
    state.add_argument("--set", dest="declared", required=True,
                       metavar="STATE",
                       help=f"one of: {', '.join(story.DECLARABLE_STATES)}")
    state.add_argument("--note", default=None, help="why the transition happened")
    _add_common(state)

    found = subparsers.add_parser(
        "findings", help="file each role's findings record and count the overlap")
    found.add_argument("story_id")
    for role in findings_module.ROLES:
        found.add_argument(f"--{role}", type=Path, required=True, metavar="PATH",
                           help=f"the {role} agent's findings record")
    found.add_argument("--json", action="store_true", dest="as_json")
    found.add_argument("--no-write", action="store_true",
                       help="count without writing a run record")
    _add_common(found)

    hooks_cmd = subparsers.add_parser("hooks", help="install or inspect the git hook")
    hooks_cmd.add_argument("action", choices=["install", "uninstall", "status"])
    hooks_cmd.add_argument("--force", action="store_true",
                           help="overwrite a pre-commit hook amigos did not write")
    hooks_cmd.add_argument("--root", type=Path, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            return _init(args)
        if args.command == "hooks":
            return _hooks(args)
        cfg = config_module.load(root=args.root, stories_dir=args.stories_dir)
        if args.command == "create":
            return _create(cfg, args)
        if args.command == "check":
            return _check(cfg, args)
        if args.command == "lint":
            return _lint(cfg, args)
        if args.command == "status":
            return _status(cfg, args)
        if args.command == "gate":
            return _gate(cfg, args)
        if args.command == "state":
            return _state(cfg, args)
        if args.command == "findings":
            return _findings(cfg, args)
    except config_module.ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except story.StoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except dor.StructuralError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except ParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except findings_module.FindingsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except gate_module.GateUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_ERROR


def _init(args: argparse.Namespace) -> int:
    root = (args.root or Path.cwd()).resolve()
    amigos_dir = root / config_module.CONFIG_DIRNAME
    stories = amigos_dir / "stories"
    stories.mkdir(parents=True, exist_ok=True)
    config_path = amigos_dir / config_module.CONFIG_FILENAME
    if config_path.exists():
        print(f"{config_path}: already present, left unchanged")
    else:
        config_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
        print(f"{config_path}: created")
    print(f"{stories}: ready for stories")
    return EXIT_OK


def _create(cfg: config_module.Config, args: argparse.Namespace) -> int:
    directory = story.create(cfg, args.story_id)
    print(f"{directory}: scaffolded")
    for name in story.INPUT_FILES:
        print(f"  {name}")
    print("\nThe scaffold is not a contract. Fill it in, then run:")
    print(f"  amigos check {args.story_id}")
    return EXIT_OK


def _check(cfg: config_module.Config, args: argparse.Namespace) -> int:
    result = dor.evaluate(cfg, args.story_id)
    if not args.no_write:
        dor.write(result)
    if args.as_json:
        print(json.dumps(result.as_dict(), indent=2))
        return result.exit_code

    print(f"{result.story_id}: {result.state}")
    for name in dor.CHECK_NAMES:
        marker = "PASS" if result.checks[name] else "FAIL"
        print(f"  [{marker}] {name}")
    if result.failures:
        print()
        for failure in result.failures:
            print(f"  {failure.format()}")
    for warning in result.warnings:
        print(f"  {warning.format()}")
    if result.ready:
        print("\nready: true")
    else:
        print(f"\nready: false ({_reason(result)})")
    return result.exit_code


def _reason(result: dor.Result) -> str:
    if result.declared_state in story.WITHHOLDING_STATES:
        return f"state.json declares {result.declared_state}"
    failed = [n for n in dor.CHECK_NAMES if not result.checks[n]]
    return f"{len(failed)} check(s) failed: {', '.join(failed)}"


def _lint(cfg: config_module.Config, args: argparse.Namespace) -> int:
    if args.file is not None:
        path = args.file
    else:
        path = story.story_dir(cfg, args.story_id) / "acceptance.feature"
    if not path.is_file():
        print(f"error: {path}: not found", file=sys.stderr)
        return EXIT_ERROR

    findings = lint_module.lint_file(path, cfg)
    if args.as_json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding.format())
        if not findings:
            print(f"{path}: no findings")
    return EXIT_FINDINGS if lint_module.failures(findings) else EXIT_OK


def _status(cfg: config_module.Config, args: argparse.Namespace) -> int:
    if not cfg.stories_dir.is_dir():
        print(f"error: {cfg.stories_dir}: not found", file=sys.stderr)
        return EXIT_ERROR
    directories = sorted(d for d in cfg.stories_dir.iterdir() if d.is_dir())
    if not directories:
        print(f"{cfg.stories_dir}: no stories yet")
        return EXIT_OK

    worst = EXIT_OK
    width = max(len(d.name) for d in directories)
    for directory in directories:
        try:
            result = dor.evaluate(cfg, directory.name)
        except (dor.StructuralError, story.StoryError, ParseError) as exc:
            print(f"  {directory.name:<{width}}  error    {exc}")
            worst = EXIT_ERROR
            continue
        failed = [n for n in dor.CHECK_NAMES if not result.checks[n]]
        detail = "" if result.ready else f"  ({len(failed)} check(s) failed)" if failed else ""
        print(f"  {directory.name:<{width}}  {result.state:<15}{detail}")
        if not result.ready and worst == EXIT_OK:
            worst = EXIT_FINDINGS
    return worst


def _gate(cfg: config_module.Config, args: argparse.Namespace) -> int:
    if args.staged and args.changed_files:
        print("error: pass --staged or --changed-file, not both", file=sys.stderr)
        return EXIT_ERROR
    if args.staged:
        paths = gate_module.staged_paths(cfg.root)
    elif args.changed_files:
        paths = list(args.changed_files)
    else:
        paths = gate_module.working_tree_paths(cfg.root)

    decision = gate_module.decide(cfg, paths, override=args.story)

    if args.as_json:
        print(json.dumps(decision.as_dict(), indent=2))
        return decision.exit_code

    if decision.permitted:
        print(f"gate: permitted - {decision.reason}")
        return decision.exit_code

    print(f"gate: refused - {decision.reason}", file=sys.stderr)
    print(file=sys.stderr)
    print("governed paths in this change:", file=sys.stderr)
    for path in decision.governed[:20]:
        print(f"  {path}", file=sys.stderr)
    if len(decision.governed) > 20:
        print(f"  ... and {len(decision.governed) - 20} more", file=sys.stderr)
    print(file=sys.stderr)
    if decision.story_id is None:
        print("Set an active story with one of:", file=sys.stderr)
        print(f"  export {gate_module.ENV_VAR}=STORY-123", file=sys.stderr)
        print(f"  echo STORY-123 > .amigos/{gate_module.ACTIVE_FILE}", file=sys.stderr)
        print("  git switch -c story/STORY-123-short-description", file=sys.stderr)
    else:
        print(f"Make the story ready, then retry:", file=sys.stderr)
        print(f"  amigos check {decision.story_id}", file=sys.stderr)
    return decision.exit_code


def _hooks(args: argparse.Namespace) -> int:
    root = (args.root or Path.cwd()).resolve()
    if args.action == "install":
        return hooks.install(root, force=args.force)
    if args.action == "uninstall":
        return hooks.uninstall(root)
    return hooks.status(root)


def _state(cfg: config_module.Config, args: argparse.Namespace) -> int:
    directory = story.story_dir(cfg, args.story_id)
    if not directory.is_dir():
        print(f"error: {directory}: story not found", file=sys.stderr)
        return EXIT_ERROR
    before = story.read_state(directory).declared_state
    after = story.set_state(directory, args.declared, note=args.note)
    print(f"{args.story_id}: {before} -> {after.declared_state}")
    print(f"  {len(after.history)} entries in history")
    return EXIT_OK


def _findings(cfg: config_module.Config, args: argparse.Namespace) -> int:
    directory = story.story_dir(cfg, args.story_id)
    if not directory.is_dir():
        print(f"error: {directory}: story not found", file=sys.stderr)
        return EXIT_ERROR

    paths = {role: getattr(args, role) for role in findings_module.ROLES}
    records = findings_module.load_records(args.story_id, paths)
    summary = findings_module.summarise(args.story_id, records)

    run_directory = None
    if not args.no_write:
        run_directory = findings_module.write(cfg, summary, records)
        summary = dataclasses.replace(summary, run_id=run_directory.name)

    if args.as_json:
        print(json.dumps(summary.as_dict(), indent=2))
        return EXIT_OK

    print(f"{summary.story_id}: {summary.total_findings} findings, "
          f"{len(summary.keys)} distinct")
    width = max(len(role) for role in findings_module.ROLES)
    for role in findings_module.ROLES:
        print(f"  {role:<{width}}  {summary.findings_by_role[role]:>3} findings, "
              f"{summary.unique_by_role[role]:>3} named by no other role")
    print()
    print(f"  shared  {summary.shared:>3}")
    print(f"  unique  {summary.unique:>3}")
    if summary.split_added_nothing:
        print()
        print(findings_module.NOTHING_GAINED)
    if run_directory is not None:
        print()
        print(f"run record: {run_directory}")
    return EXIT_OK
