import json

import pytest

from amigos import config as config_module


def test_defaults_apply_without_a_config_file(tmp_path):
    (tmp_path / ".amigos").mkdir()
    cfg = config_module.load(root=tmp_path)
    assert cfg.source is None
    assert cfg.stories_dir == tmp_path / ".amigos" / "stories"
    assert (cfg.min_primary, cfg.min_counterexamples) == (1, 2)
    assert "correctly" in cfg.vague_words


def test_find_root_walks_up_to_the_amigos_directory(tmp_path):
    (tmp_path / ".amigos").mkdir()
    nested = tmp_path / "src" / "deep"
    nested.mkdir(parents=True)
    assert config_module.find_root(nested) == tmp_path.resolve()


def test_find_root_returns_none_outside_a_repository(tmp_path):
    assert config_module.find_root(tmp_path) is None


def test_stories_dir_override_beats_the_configured_value(tmp_path):
    (tmp_path / ".amigos").mkdir()
    (tmp_path / ".amigos" / "config.json").write_text('{"stories_dir": "configured"}')
    cfg = config_module.load(root=tmp_path, stories_dir=tmp_path / "override")
    assert cfg.stories_dir == tmp_path / "override"


def test_relative_stories_dir_resolves_against_the_root(tmp_path):
    (tmp_path / ".amigos").mkdir()
    (tmp_path / ".amigos" / "config.json").write_text('{"stories_dir": "elsewhere/stories"}')
    assert config_module.load(root=tmp_path).stories_dir == tmp_path / "elsewhere" / "stories"


def test_invalid_config_json_is_reported(tmp_path):
    (tmp_path / ".amigos").mkdir()
    (tmp_path / ".amigos" / "config.json").write_text("{not json")
    with pytest.raises(config_module.ConfigError) as excinfo:
        config_module.load(root=tmp_path)
    assert "invalid JSON" in str(excinfo.value)


def test_removing_a_word_does_not_disable_the_rule_set(tmp_path):
    (tmp_path / ".amigos").mkdir()
    (tmp_path / ".amigos" / "config.json").write_text(
        json.dumps({"lint": {"vague_words_remove": ["works", "good"]}}))
    cfg = config_module.load(root=tmp_path)
    assert "works" not in cfg.vague_words
    assert "correctly" in cfg.vague_words


def test_extending_the_vocabulary_does_not_duplicate_an_existing_entry(tmp_path):
    (tmp_path / ".amigos").mkdir()
    (tmp_path / ".amigos" / "config.json").write_text(
        json.dumps({"lint": {"vague_words_extra": ["Correct", "as designed"]}}))
    words = config_module.load(root=tmp_path).vague_words
    assert words.count("correct") == 1
    assert "as designed" in words
