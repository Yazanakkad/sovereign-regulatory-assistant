"""Smoke tests: the package installs, imports, and its entry point runs."""

import pytest

import regassist


def test_version_is_set() -> None:
    assert regassist.__version__


def test_main_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    regassist.main()
    assert capsys.readouterr().out.strip() == f"regassist {regassist.__version__}"
