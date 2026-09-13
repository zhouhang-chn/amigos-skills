from amigos import markdown

DOC = """# Intent

## User
A developer.

## In Scope
- One thing
-
- TODO another

## Out of Scope
- None

### Nested heading
Still inside Out of Scope.

## Empty
"""


def test_sections_are_lowercased_and_bodies_carry_line_numbers():
    found = markdown.sections(DOC)
    assert set(found) >= {"user", "in scope", "out of scope", "empty"}
    assert found["user"][0] == (4, "A developer.")


def test_deeper_heading_stays_inside_its_parent_section():
    found = markdown.sections(DOC)
    texts = [t for _, t in found["out of scope"]]
    assert "Still inside Out of Scope." in texts


def test_list_items_skip_placeholders_and_empty_bullets():
    items = markdown.list_items(markdown.sections(DOC)["in scope"])
    assert [t for _, t in items] == ["One thing"]


def test_explicit_none_counts_as_a_list_item():
    items = markdown.list_items(markdown.sections(DOC)["out of scope"])
    assert [t for _, t in items] == ["None"]


def test_empty_section_has_no_content_lines():
    assert markdown.content_lines(markdown.sections(DOC)["empty"]) == []


def test_placeholder_detection_is_word_bounded():
    assert markdown.is_placeholder("TODO: fill this in")
    assert markdown.is_placeholder("<!-- amigos:placeholder -->")
    assert not markdown.is_placeholder("The TODOs were resolved in TODOIST")
    assert not markdown.is_placeholder("A perfectly ordinary sentence.")
