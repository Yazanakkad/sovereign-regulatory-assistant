"""Tests for the placeholder HTTP server."""

import json
import logging
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest

from regassist.server import (
    Config,
    JsonFormatter,
    journal_stream_attached,
    load_config,
    make_server,
)

ARABIC = "\u0645\u0631\u062d\u0628\u0627"  # "marhaba"


def test_load_config_defaults() -> None:
    assert load_config({}) == Config(host="127.0.0.1", port=8000)


def test_load_config_reads_environment() -> None:
    env = {"REGASSIST_HOST": "::1", "REGASSIST_PORT": "9000"}
    assert load_config(env) == Config(host="::1", port=9000)


@pytest.mark.parametrize("raw", ["abc", "0", "65536"])
def test_load_config_rejects_bad_port(raw: str) -> None:
    with pytest.raises(ValueError, match="REGASSIST_PORT"):
        load_config({"REGASSIST_PORT": raw})


def test_json_formatter_keeps_fields_and_arabic() -> None:
    record = logging.makeLogRecord(
        {"name": "regassist", "levelname": "INFO", "msg": ARABIC, "fields": {"port": 8000}}
    )
    line = JsonFormatter().format(record)
    data = json.loads(line)
    assert data["msg"] == ARABIC
    assert data["port"] == 8000
    assert data["level"] == "info"
    assert ARABIC in line  # written as UTF-8, not \u escapes


@pytest.fixture
def base_url() -> Iterator[str]:
    server = make_server(Config(host="127.0.0.1", port=0))  # port 0: the OS picks a free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join()


def test_health_returns_ok(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/health", timeout=5) as resp:  # noqa: S310
        assert resp.status == 200
        assert resp.headers["Content-Type"] == "application/json"
        assert resp.headers["Server"] == "regassist"
        assert json.loads(resp.read())["status"] == "ok"


def test_unknown_path_returns_404(base_url: str) -> None:
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(f"{base_url}/nope", timeout=5)  # noqa: S310
    assert excinfo.value.code == 404
    excinfo.value.close()


def test_json_formatter_syslog_prefix_maps_level() -> None:
    record = logging.makeLogRecord(
        {"name": "regassist", "levelno": logging.ERROR, "levelname": "ERROR", "msg": "boom"}
    )
    assert JsonFormatter(syslog_prefix=True).format(record).startswith("<3>{")
    assert JsonFormatter().format(record).startswith("{")


@pytest.mark.parametrize(("env", "expected"), [({"JOURNAL_STREAM": "8:1234"}, True), ({}, False)])
def test_journal_stream_detection(env: dict[str, str], expected: bool) -> None:
    assert journal_stream_attached(env) is expected
