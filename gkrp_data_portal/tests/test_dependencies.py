"""requirements.txt must mirror pyproject [project].dependencies."""

from __future__ import annotations

import tomllib
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def test_requirements_match_pyproject():
    with (_ROOT / "pyproject.toml").open("rb") as fh:
        declared = tomllib.load(fh)["project"]["dependencies"]
    pinned = [
        line.strip()
        for line in (_ROOT / "requirements.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert sorted(pinned) == sorted(declared)
