import tomllib
from pathlib import Path

from skylinee_harness import __version__


def test_package_version_matches_project_metadata() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["version"] == __version__
