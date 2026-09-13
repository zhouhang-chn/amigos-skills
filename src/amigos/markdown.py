"""Just enough Markdown to read a contract's sections.

A section is an ``##`` heading and the lines beneath it. A line is a
*placeholder* if it still carries scaffolding text, and placeholder lines count
as absent: a contract whose heading exists but whose body is untouched has not
been written, and 'the file exists' must not be enough to pass a check.
"""

from __future__ import annotations

import re
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\bTODO\b|<!--\s*amigos:placeholder\s*-->", re.IGNORECASE)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
_LIST_ITEM_RE = re.compile(r"^[-*+]\s+(.*)$")


def is_placeholder(line: str) -> bool:
    return bool(PLACEHOLDER_RE.search(line))


def sections(text: str) -> dict[str, list[tuple[int, str]]]:
    """Map each level-2 heading to its body lines as (line number, text) pairs.

    Headings are matched case-insensitively and stored lowercased. A deeper
    heading stays inside the section it sits under; a new ``##`` or ``#`` closes it.
    """
    result: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    for index, raw in enumerate(text.splitlines(), start=1):
        heading = _HEADING_RE.match(raw.strip())
        if heading and len(heading.group(1)) <= 2:
            current = heading.group(2).strip().lower() if len(heading.group(1)) == 2 else None
            if current is not None:
                result.setdefault(current, [])
            continue
        if current is not None:
            result[current].append((index, raw.rstrip()))
    return result


def sections_of(path: Path) -> dict[str, list[tuple[int, str]]]:
    return sections(path.read_text(encoding="utf-8"))


def content_lines(body: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Body lines that carry real content: non-blank and not a placeholder."""
    return [(n, t) for n, t in body if t.strip() and not is_placeholder(t)]


def list_items(body: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Bullet items that carry real content."""
    items: list[tuple[int, str]] = []
    for number, text in body:
        match = _LIST_ITEM_RE.match(text.strip())
        if match and match.group(1).strip() and not is_placeholder(text):
            items.append((number, match.group(1).strip()))
    return items
