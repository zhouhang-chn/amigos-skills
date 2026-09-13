import pytest

from amigos import jsonschema


def test_a_valid_instance_produces_no_errors():
    schema = {"type": "object", "required": ["a"], "properties": {"a": {"type": "string"}}}
    assert jsonschema.validate({"a": "x"}, schema) == []


def test_missing_required_key_is_reported():
    schema = {"type": "object", "required": ["a"]}
    assert "missing required key 'a'" in jsonschema.validate({}, schema)[0]


def test_additional_properties_false_rejects_extras():
    schema = {"type": "object", "properties": {"a": {}}, "additionalProperties": False}
    assert "unexpected key 'b'" in jsonschema.validate({"a": 1, "b": 2}, schema)[0]


def test_booleans_are_not_integers():
    assert jsonschema.validate(True, {"type": "integer"}) != []
    assert jsonschema.validate(1, {"type": "boolean"}) != []


def test_nullable_type_lists_are_honoured():
    assert jsonschema.validate(None, {"type": ["integer", "null"]}) == []
    assert jsonschema.validate("x", {"type": ["integer", "null"]}) != []


def test_array_items_are_checked():
    schema = {"type": "array", "items": {"type": "string"}}
    assert jsonschema.validate(["a", 1], schema) != []


def test_an_unimplemented_keyword_raises_rather_than_passing_silently():
    with pytest.raises(jsonschema.SchemaError):
        jsonschema.validate({}, {"type": "object", "patternProperties": {}})


def test_project_schemas_use_only_supported_keywords():
    for name in ("dor.schema.json", "state.schema.json"):
        jsonschema.validate({}, jsonschema.load_schema(name))
