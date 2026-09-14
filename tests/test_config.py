"""Tests for Settings.data_root resolution (BRAINY_DATA_DIR / NEXUS_DATA_DIR / cross-platform default)."""

from pathlib import Path

import pytest

from brainy import config


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure each test starts with neither env var set, and reset the cached
    Settings singleton so changes take effect."""
    monkeypatch.delenv("BRAINY_DATA_DIR", raising=False)
    monkeypatch.delenv("NEXUS_DATA_DIR", raising=False)
    config.reset_settings()
    yield
    config.reset_settings()


def test_default_data_root_is_cross_platform_when_no_env_set():
    """Without any override, the root must be ~/.brainy/data - not a
    hardcoded, machine-specific path."""
    settings = config.Settings(_env_file=None)
    assert settings.data_root == Path.home() / ".brainy" / "data"


def test_brainy_data_dir_takes_priority(monkeypatch, tmp_path):
    preferred = tmp_path / "brainy-priority-test"
    legacy = tmp_path / "should-be-ignored"
    monkeypatch.setenv("BRAINY_DATA_DIR", str(preferred))
    monkeypatch.setenv("NEXUS_DATA_DIR", str(legacy))
    settings = config.Settings(_env_file=None)
    assert settings.data_root == preferred


def test_nexus_data_dir_still_works_as_legacy_fallback(monkeypatch, tmp_path):
    legacy = tmp_path / "nexus-legacy-test"
    monkeypatch.setenv("NEXUS_DATA_DIR", str(legacy))
    settings = config.Settings(_env_file=None)
    assert settings.data_root == legacy


def test_relative_brainy_data_dir_is_rejected(monkeypatch):
    monkeypatch.setenv("BRAINY_DATA_DIR", "relative/path")
    with pytest.raises(Exception):
        config.Settings(_env_file=None)


def test_relative_nexus_data_dir_is_rejected(monkeypatch):
    monkeypatch.setenv("NEXUS_DATA_DIR", "relative/path")
    with pytest.raises(Exception):
        config.Settings(_env_file=None)
