"""Command line surface: ``amigos init | create | check | lint | status``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, config as config_module, dor, lint as lint_module, story
from .gherkin import ParseError

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

DEFAULT_CONFIG = {
    "schema_version": 1,
    "stories_dir": ".amigos/stories",
    "lint": {"vague_words_extra": [], "vague_words_remove": []},
    "dor": {"min_primary": 1, "min_counterexamples": 2},
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

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            return _init(args)
        cfg = config_module.load(root=args.root, stories_dir=args.stories_dir)
        if args.command == "create":
            return _create(cfg, args)
        if args.command == "check":
            return _check(cfg, args)
        if args.command == "lint":
            return _lint(cfg, args)
        if args.command == "status":
            return _status(cfg, args)
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
