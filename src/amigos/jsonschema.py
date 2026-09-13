"""A minimal JSON Schema checker covering the keywords this project's schemas use.

A dependency-free validator keeps the promise that the gate runs in any
repository with no install step. It supports exactly the keywords used by
``schemas/dor.schema.json`` and ``schemas/state.schema.json`` and raises on any
keyword it does not implement, so a schema cannot quietly go unchecked.
"""

from __future__ import annotations

import json
from pathlib import Path

SUPPORTED = {
    "$schema", "$id", "title", "description", "type", "required", "properties",
    "additionalProperties", "enum", "const", "items", "minimum", "minLength",
}

_TYPES: dict[str, type | tuple[type, ...]] = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "number": (int, float), "null": type(None),
}


class SchemaError(Exception):
    """The schema uses a keyword this checker does not implement."""


def validate(instance: object, schema: dict, path: str = "$") -> list[str]:
    """Return a list of human-readable violations; empty means valid."""
    unsupported = set(schema) - SUPPORTED
    if unsupported:
        raise SchemaError(f"{path}: unsupported schema keywords: {sorted(unsupported)}")

    errors: list[str] = []

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}, found {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")

    if "type" in schema:
        expected = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not _matches_type(instance, expected):
            errors.append(f"{path}: expected type {'|'.join(expected)}, found {_name(instance)}")
            return errors

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required key {key!r}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                errors.extend(validate(value, properties[key], f"{path}.{key}"))
            else:
                extra = schema.get("additionalProperties", True)
                if extra is False:
                    errors.append(f"{path}: unexpected key {key!r}")
                elif isinstance(extra, dict):
                    errors.extend(validate(value, extra, f"{path}.{key}"))

    if isinstance(instance, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(instance):
            errors.extend(validate(item, schema["items"], f"{path}[{i}]"))

    return errors


def _matches_type(instance: object, expected: list[str]) -> bool:
    for name in expected:
        if name == "integer":
            if isinstance(instance, int) and not isinstance(instance, bool):
                return True
        elif name == "boolean":
            if isinstance(instance, bool):
                return True
        elif name == "number":
            if isinstance(instance, (int, float)) and not isinstance(instance, bool):
                return True
        else:
            target = _TYPES.get(name)
            if target is not None and isinstance(instance, target):
                return True
    return False


def _name(instance: object) -> str:
    if isinstance(instance, bool):
        return "boolean"
    return {dict: "object", list: "array", str: "string", int: "integer",
            float: "number", type(None): "null"}.get(type(instance), type(instance).__name__)


def load_schema(name: str) -> dict:
    """Load one of this project's schemas by file name."""
    root = Path(__file__).resolve().parents[2] / "schemas"
    return json.loads((root / name).read_text(encoding="utf-8"))
