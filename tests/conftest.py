import pytest

from clausemark import config


@pytest.fixture(autouse=True)
def use_temporary_folders(monkeypatch, tmp_path):
    """Tests never touch real uploads or traces."""
    monkeypatch.setattr(config, "UPLOADS_CORPUS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(config, "TRACES_FILE", str(tmp_path / "traces" / "asks.jsonl"))
    monkeypatch.setattr(config, "ACTIVE_SET", "sample")
