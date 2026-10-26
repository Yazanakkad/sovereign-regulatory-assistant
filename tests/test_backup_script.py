"""Tests for deploy/backup/regassist-backup.sh, run against temporary directories."""

import fcntl
import hashlib
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "backup" / "regassist-backup.sh"
PREFIX = "regassist-"
SUFFIX = ".tar.gz"


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    (root / "srv/regassist/data/demo").mkdir(parents=True)
    (root / "srv/regassist/data/demo/file with space.txt").write_text("space test\n")
    (root / "etc/regassist").mkdir(parents=True)
    (root / "etc/regassist/regassist.env").write_text("REGASSIST_PORT=8000\n")
    return root


@pytest.fixture
def backup_dir(tmp_path: Path) -> Path:
    path = tmp_path / "backups"
    path.mkdir()
    return path


def run_backup(
    source_root: Path, backup_dir: Path, keep: str = "7"
) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": os.environ["PATH"],
        "REGASSIST_BACKUP_DIR": str(backup_dir),
        "REGASSIST_BACKUP_KEEP": keep,
        "REGASSIST_BACKUP_SOURCE_ROOT": str(source_root),
    }
    # Fixed script path, list arguments, no shell.
    return subprocess.run(  # noqa: S603
        ["/bin/bash", str(SCRIPT)], env=env, capture_output=True, text=True, check=False
    )


def archives(backup_dir: Path) -> set[str]:
    return {p.name for p in backup_dir.glob(f"{PREFIX}*{SUFFIX}")}


def make_fake_archive(backup_dir: Path, stamp: str) -> str:
    name = f"{PREFIX}{stamp}{SUFFIX}"
    (backup_dir / name).write_bytes(b"")
    (backup_dir / f"{name}.sha256").write_text(f"{'0' * 64}  {name}\n")
    return name


def test_creates_verified_private_archive_with_checksum(
    source_root: Path, backup_dir: Path
) -> None:
    result = run_backup(source_root, backup_dir)

    assert result.returncode == 0, result.stderr
    [name] = archives(backup_dir)
    archive = backup_dir / name
    expected, listed_name = (backup_dir / f"{name}.sha256").read_text().split()
    assert listed_name == name
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
    assert archive.stat().st_mode & 0o777 == 0o600
    with tarfile.open(archive) as tar:
        members = set(tar.getnames())
    assert "srv/regassist/data/demo/file with space.txt" in members
    assert "etc/regassist/regassist.env" in members
    assert not list(backup_dir.glob(".incoming.*"))
    assert "event=backup_done" in result.stderr


def test_retention_keeps_newest_and_never_prunes_the_new_archive(
    source_root: Path, backup_dir: Path
) -> None:
    # 2098/2099 simulate archives written while the clock was wrong (ADR-0010).
    fakes = {
        make_fake_archive(backup_dir, s)
        for s in ("20200101T000000Z", "20980101T000000Z", "20990101T000000Z")
    }

    result = run_backup(source_root, backup_dir, keep="2")

    assert result.returncode == 0, result.stderr
    remaining = archives(backup_dir)
    new = remaining - fakes
    assert len(new) == 1
    assert remaining == new | {f"{PREFIX}20990101T000000Z{SUFFIX}"}
    assert {p.name for p in backup_dir.glob("*.sha256")} == {f"{n}.sha256" for n in remaining}


@pytest.mark.parametrize("keep", ["0", "-1", "07", "abc"])
def test_invalid_keep_is_a_config_error(source_root: Path, backup_dir: Path, keep: str) -> None:
    result = run_backup(source_root, backup_dir, keep=keep)

    assert result.returncode == 2
    assert "event=config_error" in result.stderr
    assert archives(backup_dir) == set()


def test_failed_backup_prunes_nothing(source_root: Path, backup_dir: Path) -> None:
    fakes = {make_fake_archive(backup_dir, s) for s in ("20200101T000000Z", "20200102T000000Z")}
    shutil.rmtree(source_root / "etc/regassist")

    result = run_backup(source_root, backup_dir, keep="1")

    assert result.returncode == 1
    assert "event=source_missing" in result.stderr
    assert archives(backup_dir) == fakes
    assert not list(backup_dir.glob(".incoming.*"))


def test_concurrent_run_is_refused(source_root: Path, backup_dir: Path) -> None:
    with (backup_dir / ".lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = run_backup(source_root, backup_dir)

    assert result.returncode == 3
    assert "event=backup_skipped" in result.stderr
    assert archives(backup_dir) == set()


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read a mode-000 file")
def test_tool_failure_is_reported_as_exit_1(source_root: Path, backup_dir: Path) -> None:
    unreadable = source_root / "srv/regassist/data/demo/file with space.txt"
    unreadable.chmod(0o000)
    try:
        result = run_backup(source_root, backup_dir)
    finally:
        unreadable.chmod(0o600)  # let pytest delete tmp_path

    assert result.returncode == 1
    assert "event=backup_failed exit=1 cause_exit=2" in result.stderr
    assert "command=" in result.stderr
    assert archives(backup_dir) == set()
    assert not list(backup_dir.glob(".incoming.*"))
