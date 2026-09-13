"""STORY-005: the overlap count, and everything that must stop a run.

The count of findings named by exactly one role is the number the multi-agent
design is judged on. A counting bug would not fail loudly; it would quietly hand
the design the verdict it wanted. So the rules are tested against records built
by hand, where the right answer is known before the code runs.
"""

import json
from pathlib import Path

import pytest

from amigos import config as config_module, findings, jsonschema
from amigos.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "findings"


@pytest.fixture
def scratch_config(scratch_repo: Path):
    return config_module.load(root=scratch_repo)


def _record(role: str, *entries, story_id: str = "READY-001") -> dict:
    """A findings record from (section, dimension) pairs."""
    return {
        "schema_version": 1,
        "story_id": story_id,
        "role": role,
        "findings": [
            {"target_file": "intent.md", "target_section": section,
             "risk_dimension": dimension, "statement": f"{role} on {section}"}
            for section, dimension in entries
        ],
    }


def _write(directory: Path, payload: dict) -> Path:
    path = directory / f"{payload['role']}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _paths(directory: Path, *payloads: dict) -> dict[str, Path]:
    return {p["role"]: _write(directory, p) for p in payloads}


# --- the key ---------------------------------------------------------------

def test_the_same_section_and_dimension_is_one_finding(tmp_path):
    """STORY-005's third scenario: two roles naming the same thing count once."""
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", ("In Scope", "scope")),
        _record("qa", ("Success", "testability")),
    )
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    assert summary.total_findings == 3
    assert len(summary.keys) == 2
    assert summary.shared == 1
    assert summary.unique == 1
    assert summary.unique_by_role == {"product": 0, "dev": 0, "qa": 1}


def test_a_shared_finding_is_absent_from_the_unique_count(tmp_path):
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", ("In Scope", "scope")),
        _record("qa", ("In Scope", "scope")),
    )
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    key = summary.keys[0]
    assert key.shared is True
    assert key.roles == ("product", "dev", "qa")
    assert summary.unique == 0


def test_the_same_dimension_in_a_different_section_is_a_different_finding(tmp_path):
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", ("Out of Scope", "scope")),
        _record("qa", ("Success", "scope")),
    )
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    assert summary.unique == 3
    assert summary.shared == 0


def test_the_same_section_in_a_different_dimension_is_a_different_finding(tmp_path):
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", ("In Scope", "feasibility")),
        _record("qa", ("In Scope", "coverage")),
    )
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    assert summary.unique == 3


@pytest.mark.parametrize("written", ["In Scope", "in scope", "## In Scope",
                                     "IN  SCOPE", "  In   Scope  "])
def test_a_section_is_recognised_however_a_role_spells_it(tmp_path, written):
    """Roles that write the same heading differently have named the same section."""
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", (written, "scope")),
        _record("qa", ("Success", "coverage")),
    )
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    assert summary.shared == 1, written


def test_the_target_file_is_not_part_of_the_key(tmp_path):
    """Two roles looking at the same section from different files agree, not differ.

    Including the file would produce fewer collisions and a larger unique count,
    which is the number this milestone survives on. The contract's wording -
    'the same target section and the same risk dimension' - is taken literally.
    """
    product = _record("product", ("In Scope", "scope"))
    qa = _record("qa", ("In Scope", "scope"))
    qa["findings"][0]["target_file"] = "acceptance.feature"
    paths = _paths(tmp_path, product, _record("dev", ("Success", "coverage")), qa)
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    assert summary.shared == 1
    assert summary.unique == 1


def test_a_role_repeating_itself_does_not_inflate_its_unique_count(tmp_path):
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope"), ("In Scope", "scope")),
        _record("dev", ("Success", "coverage")),
        _record("qa", ("Problem", "ambiguity")),
    )
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    assert summary.total_findings == 4
    assert summary.unique_by_role["product"] == 1


def test_every_source_is_kept_so_a_wrong_merge_stays_visible(tmp_path):
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", ("In Scope", "scope")),
        _record("qa", ("In Scope", "scope")),
    )
    summary = findings.summarise("READY-001", findings.load_records("READY-001", paths))
    statements = [f.statement for f in summary.keys[0].sources]
    assert statements == ["product on In Scope", "dev on In Scope", "qa on In Scope"]


# --- a run that gained nothing ---------------------------------------------

def test_a_run_where_every_finding_is_shared_says_so(tmp_path, capsys, scratch_repo):
    """STORY-005's fourth scenario. Silence here would be the design flattering itself."""
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", ("In Scope", "scope")),
        _record("qa", ("In Scope", "scope")),
    )
    code = main(["findings", "READY-001", "--root", str(scratch_repo),
                 *[arg for role, path in paths.items()
                   for arg in (f"--{role}", str(path))]])
    assert code == 0
    out = capsys.readouterr().out
    assert "unique    0" in out
    assert findings.NOTHING_GAINED in out

    summary = json.loads(next(scratch_repo.glob(".amigos/runs/READY-001/*/summary.json")).read_text())
    assert summary["unique"] == 0
    assert summary["split_added_nothing"] is True


# --- everything that stops a run -------------------------------------------

@pytest.mark.parametrize("role", findings.ROLES)
def test_an_empty_findings_record_stops_the_run(tmp_path, scratch_repo, role):
    """A role with nothing to say has not done its job; it has skipped it."""
    payloads = [_record(other, ("In Scope", "scope")) for other in findings.ROLES]
    for payload in payloads:
        if payload["role"] == role:
            payload["findings"] = []
    paths = _paths(tmp_path, *payloads)
    code = main(["findings", "READY-001", "--root", str(scratch_repo),
                 *[arg for r, path in paths.items() for arg in (f"--{r}", str(path))]])
    assert code == 2
    assert not (scratch_repo / ".amigos" / "runs").exists()


@pytest.mark.parametrize("role", findings.ROLES)
def test_a_missing_findings_record_stops_the_run(tmp_path, scratch_repo, role):
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    paths[role].unlink()
    code = main(["findings", "READY-001", "--root", str(scratch_repo),
                 *[arg for r, path in paths.items() for arg in (f"--{r}", str(path))]])
    assert code == 2
    assert not (scratch_repo / ".amigos" / "runs").exists()


def test_nothing_is_written_when_a_record_is_rejected(tmp_path, scratch_repo):
    """The contract's fifth scenario: no contract file, and no run record either."""
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    paths["qa"].write_text("{ not json", encoding="utf-8")
    before = sorted(p.name for p in (scratch_repo / ".amigos").iterdir())
    code = main(["findings", "READY-001", "--root", str(scratch_repo),
                 *[arg for r, path in paths.items() for arg in (f"--{r}", str(path))]])
    assert code == 2
    assert sorted(p.name for p in (scratch_repo / ".amigos").iterdir()) == before


def test_a_record_from_another_story_is_refused(tmp_path):
    paths = _paths(
        tmp_path,
        _record("product", ("In Scope", "scope")),
        _record("dev", ("In Scope", "scope")),
        _record("qa", ("In Scope", "scope"), story_id="BLOCKED-001"),
    )
    with pytest.raises(findings.FindingsError, match="belongs to story"):
        findings.load_records("READY-001", paths)


def test_a_record_supplied_as_the_wrong_role_is_refused(tmp_path):
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    swapped = {"product": paths["dev"], "dev": paths["product"], "qa": paths["qa"]}
    with pytest.raises(findings.FindingsError, match="declares role"):
        findings.load_records("READY-001", swapped)


def test_a_finding_claiming_another_role_is_refused(tmp_path):
    payload = _record("product", ("In Scope", "scope"))
    payload["findings"][0]["role"] = "qa"
    paths = _paths(tmp_path, payload,
                   _record("dev", ("Success", "coverage")),
                   _record("qa", ("Problem", "ambiguity")))
    with pytest.raises(findings.FindingsError, match="declares role 'qa' inside"):
        findings.load_records("READY-001", paths)


def test_a_story_that_does_not_exist_is_refused(tmp_path, scratch_repo):
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope"), story_id="NOPE-001")
                               for r in findings.ROLES])
    code = main(["findings", "NOPE-001", "--root", str(scratch_repo),
                 *[arg for r, path in paths.items() for arg in (f"--{r}", str(path))]])
    assert code == 2


# --- the run record --------------------------------------------------------

def test_the_run_record_holds_one_findings_record_per_role(tmp_path, scratch_config):
    """STORY-005's second scenario."""
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    records = findings.load_records("READY-001", paths)
    summary = findings.summarise("READY-001", records)
    directory = findings.write(scratch_config, summary, records)
    filed = sorted(p.name for p in (directory / "findings").iterdir())
    assert filed == ["dev.json", "product.json", "qa.json"]
    assert (directory / "summary.json").is_file()


def test_every_filed_finding_names_its_role(tmp_path, scratch_config):
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    records = findings.load_records("READY-001", paths)
    directory = findings.write(
        scratch_config, findings.summarise("READY-001", records), records)
    for role in findings.ROLES:
        payload = json.loads((directory / "findings" / f"{role}.json").read_text())
        assert [f["role"] for f in payload["findings"]] == [role]


def test_the_run_record_lands_outside_the_story_directory(tmp_path, scratch_config):
    """The story directory is the specification; a run record is evidence about a run."""
    from amigos import story
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    records = findings.load_records("READY-001", paths)
    findings.write(scratch_config, findings.summarise("READY-001", records), records)
    directory = scratch_config.story_dir("READY-001")
    allowed = {*story.INPUT_FILES, "dor.json"}
    assert {p.name for p in directory.iterdir()} <= allowed
    assert findings.runs_dir(scratch_config).is_dir()


def test_the_summary_satisfies_its_schema(tmp_path, scratch_config):
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    records = findings.load_records("READY-001", paths)
    directory = findings.write(
        scratch_config, findings.summarise("READY-001", records), records)
    payload = json.loads((directory / "summary.json").read_text())
    schema = jsonschema.load_schema(findings.SUMMARY_SCHEMA)
    assert jsonschema.validate(payload, schema) == []


def test_runs_accumulate_rather_than_overwrite(tmp_path, scratch_config):
    """A count that survives only until the next run cannot be compared to anything."""
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    records = findings.load_records("READY-001", paths)
    first = findings.write(scratch_config, findings.summarise("READY-001", records), records)
    second = findings.write(scratch_config, findings.summarise("READY-001", records), records)
    assert first != second
    assert len(list(first.parent.iterdir())) == 2


def test_the_summary_names_the_directory_it_is_in(tmp_path, scratch_config):
    """Two runs inside one second must not both claim the same run id."""
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    records = findings.load_records("READY-001", paths)
    summary = findings.summarise("READY-001", records)
    for _ in range(2):
        directory = findings.write(scratch_config, summary, records)
        payload = json.loads((directory / "summary.json").read_text())
        assert payload["run_id"] == directory.name


def test_no_write_counts_without_leaving_a_record(tmp_path, scratch_repo):
    paths = _paths(tmp_path, *[_record(r, ("In Scope", "scope")) for r in findings.ROLES])
    code = main(["findings", "READY-001", "--root", str(scratch_repo), "--no-write",
                 *[arg for r, path in paths.items() for arg in (f"--{r}", str(path))]])
    assert code == 0
    assert not (scratch_repo / ".amigos" / "runs").exists()


# --- the fixture corpus ----------------------------------------------------

def test_the_fixture_records_count_the_way_they_were_built(scratch_repo, capsys):
    """Six distinct findings across three roles: two shared, four named once."""
    code = main(["findings", "READY-001", "--root", str(scratch_repo), "--json",
                 "--no-write",
                 "--product", str(FIXTURES / "product.json"),
                 "--dev", str(FIXTURES / "dev.json"),
                 "--qa", str(FIXTURES / "qa.json")])
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["total_findings"] == 9
    assert summary["distinct_findings"] == 6
    assert summary["shared"] == 2
    assert summary["unique"] == 4
    assert summary["unique_by_role"] == {"product": 1, "dev": 2, "qa": 1}
    assert summary["split_added_nothing"] is False
